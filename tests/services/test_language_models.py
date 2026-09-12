import hashlib
import json

import pytest


def test_language_model_selection_covers_modern_languages_without_latin():
    from multilang.domain.jobs import SupportedLanguage
    from multilang.services.language_models import model_spec

    for language in SupportedLanguage:
        if language.value == 'la':
            with pytest.raises(ValueError, match='Latin'):
                model_spec('la')
        else:
            spec = model_spec(language.value)
            assert spec.language == language.value
    assert model_spec('ko').backend == 'kiwi'
    assert model_spec('ja').backend == 'fugashi'
    assert model_spec('zh').backend == 'stanza'
    assert model_spec('zh').model_language == 'zh-hans'
    assert model_spec('nb').model_language == 'nb'


def test_lightweight_packages_require_real_registry_entries():
    from multilang.services.language_models import stanza_processors

    registry = {'en': {'packages': {'default': {'tokenize':'combined','mwt':'combined',
                    'pos':'combined_charlm','lemma':'combined_nocharlm'}},
                    'tokenize': {'combined': {}}, 'mwt': {'combined': {}},
                    'pos': {'combined_charlm': {}, 'combined_nocharlm': {}},
                    'lemma': {'combined_nocharlm': {}}}}
    processors = stanza_processors(registry, 'en')
    assert processors == {'tokenize':'combined','mwt':'combined',
                          'pos':'combined_nocharlm','lemma':'combined_nocharlm'}
    registry['en']['pos'] = {}
    with pytest.raises(ValueError, match='available'):
        stanza_processors(registry, 'en')


def test_model_manifest_checks_bytes_before_model_loading(tmp_path, monkeypatch):
    from multilang.services import language_models

    processors = {name: 'test' for name in ['tokenize', 'pos', 'lemma']}
    files = {}
    entry = {'packages': {'default': processors}}
    for name in processors:
        model = tmp_path/'en'/name/'test.pt'
        model.parent.mkdir(parents=True)
        model.write_bytes(b'model fixture')
        files[model.relative_to(tmp_path).as_posix()] = hashlib.sha256(model.read_bytes()).hexdigest()
        entry[name] = {'test': {'md5': hashlib.md5(model.read_bytes()).hexdigest()}}
    resource = tmp_path/'resources.json'
    resource.write_text(json.dumps({'en': entry}))
    files['resources.json'] = hashlib.sha256(resource.read_bytes()).hexdigest()
    monkeypatch.setattr(language_models, 'STANZA_RESOURCES_SHA256', files['resources.json'])
    manifest = {'language':'en', 'backend':'stanza', 'model_language':'en', 'package_version':'1.14.0',
                'resource_version':'1.10.0', 'processors': processors, 'files': files, 'qualified':False}
    path = tmp_path / 'en.manifest.json'
    path.write_text(json.dumps(manifest))
    assert language_models.verify_model_manifest(path)['files'] == manifest['files']
    model.write_bytes(b'tampered model')
    with pytest.raises(ValueError, match='checksum'):
        language_models.verify_model_manifest(path)


def test_model_manifest_rejects_escape_and_links(tmp_path):
    from multilang.services.language_models import verify_model_manifest

    path = tmp_path / 'en.manifest.json'
    path.write_text(json.dumps({'files': {'../outside.pt':'0'*64}}))
    with pytest.raises(ValueError, match='path'):
        verify_model_manifest(path)


def test_model_packages_are_fingerprinted_from_actual_artifacts(tmp_path, monkeypatch):
    import importlib.metadata
    from types import SimpleNamespace

    from multilang.services.language_models import package_artifact_fingerprint

    artifact = tmp_path / 'dictionary.dic'
    artifact.write_bytes(b'original dictionary')
    package = SimpleNamespace(files=['dictionary.dic', 'package.py'],
                              locate_file=lambda name: tmp_path / name)
    monkeypatch.setattr(importlib.metadata, 'distribution', lambda name: package)
    first = package_artifact_fingerprint('test')
    artifact.write_bytes(b'changed dictionary')
    assert package_artifact_fingerprint('test') != first


def test_dictionary_runtime_configuration_participates_in_fingerprint(tmp_path, monkeypatch):
    import importlib.metadata
    from types import SimpleNamespace

    from multilang.services.language_models import package_artifact_fingerprint

    (tmp_path/'sys.dic').write_bytes(b'dictionary')
    config = tmp_path/'dicrc'
    config.write_text('cost-factor = 700')
    package = SimpleNamespace(files=['sys.dic', 'dicrc'], locate_file=lambda name: tmp_path/name)
    monkeypatch.setattr(importlib.metadata, 'distribution', lambda name: package)
    before = package_artifact_fingerprint('test')
    config.write_text('cost-factor = 1')
    assert package_artifact_fingerprint('test') != before


def test_model_registry_is_pinned_before_any_download(tmp_path, monkeypatch):
    import io
    import sys
    from types import SimpleNamespace

    from multilang.services import language_models

    monkeypatch.setitem(sys.modules, 'stanza', SimpleNamespace())
    monkeypatch.setattr(language_models, 'urlopen', lambda *a, **kw: io.BytesIO(b'{}'))
    with pytest.raises(ValueError, match='registry checksum'):
        language_models.prepare_model('en', tmp_path)
    assert not (tmp_path/'resources.json').exists()


def test_manifest_cannot_omit_pinned_registry_and_required_models(tmp_path):
    from multilang.services.language_models import verify_model_manifest

    unrelated = tmp_path/'unrelated.txt'
    unrelated.write_bytes(b'not a model')
    path = tmp_path/'en.manifest.json'
    path.write_text(json.dumps({'language': 'en', 'backend': 'stanza', 'model_language': 'en',
        'package_version': '1.14.0', 'resource_version': 'not-the-pinned-version',
        'processors': {'tokenize': 'unverified'}, 'qualified': False,
        'files': {'unrelated.txt': hashlib.sha256(unrelated.read_bytes()).hexdigest()}}))
    with pytest.raises(ValueError, match='pinned|registry|manifest'):
        verify_model_manifest(path)


@pytest.mark.parametrize('relative', ['en', 'en/pos'])
def test_model_download_preflight_rejects_nested_symlinks(tmp_path, monkeypatch, relative):
    import io
    import sys
    from types import SimpleNamespace

    from multilang.services import language_models

    root = tmp_path/'models'
    root.mkdir()
    outside = tmp_path/'outside'
    outside.mkdir()
    target = root/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(outside, target_is_directory=True)
    processors = {name: 'test' for name in ['tokenize', 'pos', 'lemma']}
    entry = {'packages': {'default': processors},
             **{name: {'test': {'md5': 'a'*32}} for name in processors}}
    content = json.dumps({'en': entry}).encode()
    monkeypatch.setattr(language_models, 'STANZA_RESOURCES_SHA256', hashlib.sha256(content).hexdigest())
    monkeypatch.setattr(language_models, 'urlopen', lambda *a, **kw: io.BytesIO(content))
    called = []
    monkeypatch.setitem(sys.modules, 'stanza', SimpleNamespace(download=lambda **kw: called.append(kw)))
    with pytest.raises(ValueError, match='symlink'):
        language_models.prepare_model('en', root)
    assert not called
    assert not list(outside.iterdir())
