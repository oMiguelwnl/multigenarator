import hashlib
import io
import json
import sys
from types import SimpleNamespace

import pytest

from multilang.services import language_models as models


def registry_fixture():
    fast = {"tokenize": "combined", "pos": "combined_charlm", "lemma": "combined_nocharlm"}
    accurate = {**fast, "pos": "combined_electra-large"}
    entry = {"packages": {"default": fast, "default_accurate": accurate}}
    payloads = {}
    for kind, names in {
        "tokenize": ["combined"],
        "pos": ["combined_nocharlm", "combined_charlm", "combined_electra-large"],
        "lemma": ["combined_nocharlm"],
        "forward_charlm": ["news"],
    }.items():
        entry[kind] = {}
        for name in names:
            relative = f"en/{kind}/{name}.pt"
            payloads[relative] = relative.encode()
            entry[kind][name] = {"md5": hashlib.md5(payloads[relative]).hexdigest()}
    entry["pos"]["combined_charlm"]["dependencies"] = [
        {"model": "forward_charlm", "package": "news"}
    ]
    return {"en": entry}, payloads


def install_fixture(tmp_path, monkeypatch):
    registry, payloads = registry_fixture()
    content = json.dumps(registry).encode()
    monkeypatch.setattr(models, "STANZA_RESOURCES_SHA256", hashlib.sha256(content).hexdigest())
    monkeypatch.setattr(models, "urlopen", lambda *a, **kw: io.BytesIO(content))
    monkeypatch.setattr(models.importlib.metadata, "version", lambda name: "1.14.0")

    def download(**kwargs):
        root = __import__("pathlib").Path(kwargs["model_dir"])
        for relative in models._required_models(registry, "en", kwargs["processors"]):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payloads[relative])

    monkeypatch.setitem(
        sys.modules, "stanza", SimpleNamespace(__version__="1.14.0", download=download)
    )
    return registry, payloads


def test_profile_selection_preserves_fast_and_uses_actual_defaults():
    registry, _ = registry_fixture()
    assert models.stanza_processors(registry, "en")["pos"] == "combined_nocharlm"
    assert models.stanza_processors(registry, "en", profile="balanced")["pos"] == "combined_charlm"
    assert (
        models.stanza_processors(registry, "en", profile="accurate")["pos"]
        == "combined_electra-large"
    )
    del registry["en"]["packages"]["default_accurate"]
    with pytest.raises(ValueError, match="unsupported|available"):
        models.stanza_processors(registry, "en", profile="accurate")


@pytest.mark.parametrize("profile", ["balanced", "accurate"])
def test_native_profiles_explicitly_unsupported(tmp_path, profile):
    assert models.model_status("ko", tmp_path, profile=profile)["reason"] == "unsupported_profile"
    with pytest.raises(ValueError, match="unsupported"):
        models.prepare_model("ja", tmp_path, profile=profile)


def test_preparation_isolates_exact_inventory_and_preserves_fast(tmp_path, monkeypatch):
    install_fixture(tmp_path, monkeypatch)
    models.prepare_model("en", tmp_path)
    old = (tmp_path / "en.manifest.json").read_bytes()
    before = models.model_status("en", tmp_path)
    models.prepare_model("en", tmp_path, profile="balanced")
    assert (tmp_path / "en.manifest.json").read_bytes() == old
    assert models.model_status("en", tmp_path) == before
    manifest = models.verify_model_manifest(tmp_path / "en.balanced.manifest.json")
    assert manifest["profile"] == "balanced"
    assert "en/pos/combined_nocharlm.pt" not in manifest["files"]
    assert "en/forward_charlm/news.pt" in manifest["files"]
    models.prepare_model("en", tmp_path)
    assert (tmp_path / "en.manifest.json").read_bytes() == old
    inventory = models.available_model_profiles("en", tmp_path)
    assert inventory["profiles"]["balanced"]["available"]
    assert inventory["profiles"]["accurate"]["supported"]
    assert not inventory["profiles"]["accurate"]["available"]


def test_alternate_manifest_cannot_be_used_as_fast(tmp_path, monkeypatch):
    install_fixture(tmp_path, monkeypatch)
    models.prepare_model("en", tmp_path, profile="balanced")
    (tmp_path / "en.manifest.json").write_bytes(
        (tmp_path / "en.balanced.manifest.json").read_bytes()
    )
    assert not models.model_status("en", tmp_path)["available"]


def test_failed_preparation_never_publishes_manifest(tmp_path, monkeypatch):
    install_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(sys.modules["stanza"], "download", lambda **kwargs: None)
    with pytest.raises((OSError, ValueError)):
        models.prepare_model("en", tmp_path, profile="balanced")
    assert not (tmp_path / "en.balanced.manifest.json").exists()


def test_status_reports_registry_unsupported_profile_without_fallback(tmp_path, monkeypatch):
    registry, _ = install_fixture(tmp_path, monkeypatch)
    del registry["en"]["packages"]["default_accurate"]
    content = json.dumps(registry).encode()
    (tmp_path / "resources.json").write_bytes(content)
    monkeypatch.setattr(models, "STANZA_RESOURCES_SHA256", hashlib.sha256(content).hexdigest())
    status = models.model_status("en", tmp_path, profile="accurate")
    assert status["profile"] == "accurate"
    assert status["reason"] == "unsupported_profile"


def test_identity_lemma_is_a_processor_without_a_downloadable_model():
    registry, _ = registry_fixture()
    registry["en"]["packages"]["default"]["lemma"] = "identity"
    selected = models.stanza_processors(registry, "en", profile="balanced")
    assert selected["lemma"] == "identity"
    assert not any("/lemma/" in path for path in models._required_models(registry, "en", selected))


def test_existing_conflicting_artifact_is_not_repaired_or_published(tmp_path, monkeypatch):
    install_fixture(tmp_path, monkeypatch)
    target = tmp_path / "en" / "pos" / "combined_charlm.pt"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"conflict")
    with pytest.raises(ValueError, match="conflicts"):
        models.prepare_model("en", tmp_path, profile="balanced")
    assert target.read_bytes() == b"conflict"
    assert not (tmp_path / "en.balanced.manifest.json").exists()


def test_profile_pipeline_receives_sealed_local_cache_and_no_download(tmp_path, monkeypatch):
    install_fixture(tmp_path, monkeypatch)
    models.prepare_model("en", tmp_path, profile="balanced")
    calls = []
    cache = object()
    from multilang.services import transformer_artifacts

    monkeypatch.setattr(transformer_artifacts, "local_foundation_cache", lambda *a: cache)
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(set_num_threads=lambda value: None))
    monkeypatch.setitem(
        sys.modules,
        "stanza.pipeline.core",
        SimpleNamespace(DownloadMethod=SimpleNamespace(NONE="none")),
    )
    monkeypatch.setattr(
        sys.modules["stanza"], "Pipeline", lambda **kwargs: calls.append(kwargs), raising=False
    )
    models.load_stanza_pipeline("en", tmp_path, profile="balanced", threads=2)
    assert calls[0]["foundation_cache"] is cache
    assert calls[0]["download_method"] == "none"
    assert calls[0]["processors"]["pos"] == "combined_charlm"
    assert calls[0]["package"] is None


@pytest.mark.parametrize("missing_package", ["transformers", "sentencepiece"])
def test_verified_transformer_status_requires_runtime_packages(
    tmp_path, monkeypatch, missing_package
):
    registry, _ = install_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(models, "_read_registry", lambda root: registry)
    manifest = {
        "language": "en",
        "model_language": "en",
        "package_version": "1.14.0",
        "processors": {"pos": "combined_electra-large"},
        "external_dependencies": [{"repo_id": "google/electra-large-discriminator"}],
    }
    monkeypatch.setattr(models, "verify_model_manifest", lambda path: manifest)

    def version(package):
        if package == missing_package:
            raise models.importlib.metadata.PackageNotFoundError(package)
        return "1.14.0"

    monkeypatch.setattr(models.importlib.metadata, "version", version)
    status = models.model_status("en", tmp_path, profile="accurate")
    assert status["available"] is False
    assert status["reason"] == "transformer_runtime_missing"


def test_transformer_preparation_rejects_missing_runtime_before_large_download(
    tmp_path, monkeypatch
):
    install_fixture(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(sys.modules["stanza"], "download", lambda **kwargs: calls.append(kwargs))

    def version(package):
        if package == "transformers":
            raise models.importlib.metadata.PackageNotFoundError(package)
        return "1.14.0"

    monkeypatch.setattr(models.importlib.metadata, "version", version)
    with pytest.raises(ValueError, match="transformer runtime"):
        models.prepare_model("en", tmp_path, profile="accurate")
    assert calls == []
