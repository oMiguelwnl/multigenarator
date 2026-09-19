import hashlib
import json
import sys
from types import SimpleNamespace

import pytest


def dependency_fixture(tmp_path):
    repo = "google/electra-large-discriminator"
    revision = "a" * 40
    base = f"transformers/{hashlib.sha256(repo.encode()).hexdigest()}/{revision}"
    files = {}
    for name in ["config.json", "tokenizer_config.json", "vocab.txt", "model.safetensors"]:
        path = tmp_path / base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"{}" if name.endswith(".json") else b"fixture")
        files[f"{base}/{name}"] = hashlib.sha256(path.read_bytes()).hexdigest()
    dependency = {"repo_id": repo, "revision": revision, "files": files}
    manifest = {
        "model_language": "en",
        "processors": {"pos": "combined_electra-large"},
        "external_dependencies": [dependency],
        "files": files,
    }
    return manifest, tmp_path / base


def test_transformer_dependency_is_bound_to_trusted_repo_revision_and_files(tmp_path):
    from multilang.services.transformer_artifacts import verify_dependencies

    manifest, _ = dependency_fixture(tmp_path)
    assert verify_dependencies(manifest, tmp_path) == manifest["files"]
    manifest["external_dependencies"][0]["repo_id"] = "untrusted/custom-code"
    with pytest.raises(ValueError, match="dependency|trusted"):
        verify_dependencies(manifest, tmp_path)


def test_transformer_dependency_rejects_unmanifested_local_configuration(tmp_path):
    from multilang.services.transformer_artifacts import verify_dependencies

    manifest, local = dependency_fixture(tmp_path)
    (local / "added_tokens.json").write_text("{}")
    with pytest.raises(ValueError, match="inventory"):
        verify_dependencies(manifest, tmp_path)


def test_transformer_cache_uses_only_verified_local_path_without_remote_code(tmp_path, monkeypatch):
    from multilang.services.transformer_artifacts import local_foundation_cache

    manifest, local = dependency_fixture(tmp_path)
    calls = []

    def load(path, **kwargs):
        calls.append((path, kwargs))
        return SimpleNamespace()

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(
            AutoModel=SimpleNamespace(from_pretrained=load),
            AutoTokenizer=SimpleNamespace(from_pretrained=load),
        ),
    )
    cache = local_foundation_cache(manifest, tmp_path)
    assert len(calls) == 2
    assert all(path == str(local) for path, kwargs in calls)
    assert all(
        kwargs["local_files_only"] and kwargs["trust_remote_code"] is False for _, kwargs in calls
    )
    assert cache.load_bert("google/electra-large-discriminator")[0] is not None
    with pytest.raises(ValueError, match="unverified"):
        cache.load_bert("untrusted/repo")


def test_transformer_cache_detects_tampering_before_transformers_import(tmp_path, monkeypatch):
    from multilang.services.transformer_artifacts import local_foundation_cache

    manifest, local = dependency_fixture(tmp_path)
    (local / "config.json").write_text('{"changed":true}')
    monkeypatch.setitem(sys.modules, "transformers", None)
    with pytest.raises(ValueError, match="checksum"):
        local_foundation_cache(manifest, tmp_path)


@pytest.mark.parametrize("unrelated_manifest", [None, b"{}", b"malformed json"])
def test_transformer_snapshot_download_pins_revision_and_file_hashes(
    tmp_path, monkeypatch, unrelated_manifest
):
    from multilang.services import transformer_artifacts as artifacts

    if unrelated_manifest is not None:
        (tmp_path / "aa.manifest.json").write_bytes(unrelated_manifest)
    revision = "a" * 40
    calls = []

    def fetch(url, maximum):
        calls.append(url)
        if "/api/models/" in url:
            return json.dumps(
                {
                    "sha": revision,
                    "siblings": [
                        {"rfilename": n}
                        for n in [
                            "config.json",
                            "tokenizer_config.json",
                            "vocab.txt",
                            "model.safetensors",
                            "evil.py",
                        ]
                    ],
                }
            ).encode()
        return b"{}" if url.endswith(".json") else b"fixture"

    monkeypatch.setattr(artifacts, "_fetch", fetch)
    manifest = {"model_language": "en", "processors": {"pos": "combined_electra-large"}}
    monkeypatch.setattr(artifacts, "_validate_checkpoint", lambda *a: None)
    dependencies = artifacts.prepare_dependencies(manifest, tmp_path, existing_root=tmp_path)
    assert dependencies[0]["revision"] == revision
    assert all("/resolve/" + revision + "/" in url for url in calls[1:])
    assert not any("evil.py" in url for url in calls)
    manifest.update(external_dependencies=dependencies, files=dependencies[0]["files"])
    assert artifacts.verify_dependencies(manifest, tmp_path)


@pytest.mark.parametrize(
    ("language", "package", "repo"),
    [
        ("da", "ddt_scandibert", "vesteinn/ScandiBERT"),
        ("fi", "tdt_bert", "TurkuNLP/bert-base-finnish-cased-v1"),
    ],
)
def test_supported_danish_and_finnish_transformer_dependencies(language, package, repo):
    from multilang.services.transformer_artifacts import _expected

    assert _expected({"model_language": language, "processors": {"pos": package}}) == [repo]
