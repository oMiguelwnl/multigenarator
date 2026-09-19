import hashlib
import json

import pytest
from typer.testing import CliRunner

from multilang.settings import Settings
from multilang.vocabulary_cli import create_vocabulary_app


def test_prepare_model_command_forwards_explicit_profile(tmp_path, monkeypatch):
    from multilang import vocabulary_cli

    calls = []

    def prepare(language, root, **kwargs):
        calls.append((language, root, kwargs))
        return {"available": True}

    monkeypatch.setattr(vocabulary_cli, "prepare_model", prepare)
    result = CliRunner().invoke(
        create_vocabulary_app(settings=Settings(_env_file=None)),
        ["prepare-model", "en", "--root", str(tmp_path), "--profile", "balanced"],
    )
    assert result.exit_code == 0, result.output
    assert calls == [("en", tmp_path, {"profile": "balanced"})]


def test_models_command_uses_per_language_configuration(tmp_path, monkeypatch):
    from multilang import vocabulary_cli

    calls = []

    def status(language, root, **kwargs):
        calls.append((language, root, kwargs))
        return {"available": False, "reason": "not_prepared"}

    monkeypatch.setattr(vocabulary_cli, "model_status", status)
    settings = Settings(_env_file=None, native_language_model_profiles={"en": "accurate"})
    result = CliRunner().invoke(
        create_vocabulary_app(settings=settings), ["models", "--language", "en", "--root", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    assert calls == [("en", tmp_path, {"profile": "accurate"})]


def test_analyze_command_uses_configured_model_profiles(tmp_path, monkeypatch):
    from multilang.services import contextual_morphology

    calls = []

    class Analyzer:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        def analyze(self, language, text):
            return contextual_morphology.ContextualAnalysis(
                language=language,
                sentence_sha256=contextual_morphology.sentence_hash(text),
                model_fingerprint="a" * 64,
                status="unavailable",
                reason="model_missing_or_drifted",
            )

    monkeypatch.setattr(contextual_morphology, "LocalContextualMorphologyService", Analyzer)
    path = tmp_path / "text.txt"
    path.write_text("went")
    settings = Settings(
        _env_file=None,
        native_language_models_dir=tmp_path / "models",
        native_language_model_profiles={"en": "balanced"},
    )
    result = CliRunner().invoke(create_vocabulary_app(settings=settings), ["analyze", "en", str(path)])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == "unavailable"
    assert calls[0].get("model_profiles") == {"en": "balanced"}


def test_explicit_fast_profile_overrides_configuration(tmp_path, monkeypatch):
    from multilang import vocabulary_cli

    calls = []
    monkeypatch.setattr(
        vocabulary_cli, "model_status",
        lambda language, root, **kwargs: calls.append(kwargs) or {"available": False},
    )
    app = create_vocabulary_app(
        settings=Settings(_env_file=None, native_language_model_profiles={"en": "accurate"})
    )
    result = CliRunner().invoke(app, ["models", "--language", "en", "--profile", "fast"])
    assert result.exit_code == 0, result.output
    assert calls == [{}]


def test_model_options_lists_available_profiles_without_preparing(tmp_path, monkeypatch):
    from multilang.services import language_models

    calls = []
    catalog = {"language": "en", "profiles": {"fast": {"supported": True}}}
    monkeypatch.setattr(
        language_models, "available_model_profiles",
        lambda language, root: calls.append((language, root)) or catalog,
    )
    result = CliRunner().invoke(
        create_vocabulary_app(settings=Settings(_env_file=None)),
        ["model-options", "--language", "en", "--root", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == [catalog]
    assert calls == [("en", tmp_path)]


def comparison_input(tmp_path):
    return {
        "model_root": str(tmp_path / "models"),
        "datasets": [{"language": "en", "corpus": str(tmp_path / "dev.conllu"),
                      "corpus_sha256": "a" * 64, "split": "dev"}],
        "profiles": ["fast", "balanced"],
        "max_sentences": 20,
        "timeout_seconds": 30,
        "threads": 1,
    }


def test_compare_models_validates_hashed_request_and_delegates(tmp_path, monkeypatch):
    from multilang.services import model_comparison

    calls = []

    def compare(request, *, output):
        calls.append((request, output))
        return {"qualification": False, "activation": False}

    monkeypatch.setattr(model_comparison, "compare_models", compare)
    request = tmp_path / "request.json"
    request.write_text(json.dumps(comparison_input(tmp_path)))
    digest = hashlib.sha256(request.read_bytes()).hexdigest()
    app = create_vocabulary_app(settings=Settings(_env_file=None))
    args = ["compare-models", str(request), digest, str(tmp_path / "report")]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {"qualification": False, "activation": False}
    assert isinstance(calls[0][0], model_comparison.ModelComparisonRequest)
    assert calls[0][1] == tmp_path / "report"
    args[2] = "0" * 64
    assert CliRunner().invoke(app, args).exit_code == 1
    assert len(calls) == 1


@pytest.mark.parametrize("invalid", ["duplicate", "too_large", "unknown_field"])
def test_compare_models_rejects_ambiguous_or_unbounded_input(tmp_path, monkeypatch, invalid):
    from multilang.services import model_comparison

    calls = []
    monkeypatch.setattr(model_comparison, "compare_models", lambda *a, **k: calls.append(a))
    payload = json.dumps(comparison_input(tmp_path))
    if invalid == "duplicate":
        payload = payload[:-1] + ', "threads": 2}'
    elif invalid == "too_large":
        payload += " " * (1024**2)
    else:
        payload = payload[:-1] + ', "download_missing": true}'
    request = tmp_path / "request.json"
    request.write_text(payload)
    result = CliRunner().invoke(
        create_vocabulary_app(settings=Settings(_env_file=None)),
        ["compare-models", str(request), hashlib.sha256(request.read_bytes()).hexdigest(),
         str(tmp_path / "report")],
    )
    assert result.exit_code == 1
    assert calls == []


@pytest.mark.parametrize("command", ["observe-corpus", "observe-training"])
def test_qualification_observations_use_selected_model(tmp_path, monkeypatch, command):
    from multilang.services import contextual_morphology, qualification_observations

    calls = []
    monkeypatch.setattr(
        contextual_morphology, "LocalContextualMorphologyService",
        lambda **kwargs: calls.append(kwargs),
    )
    for function in ("observe_document_corpus", "observe_training_corpus"):
        monkeypatch.setattr(qualification_observations, function, lambda *a, **k: {})
    receipt = tmp_path / "receipt.json"
    receipt.write_text("{}")
    args = ["qualification", command, str(tmp_path / "corpus"), "a" * 64]
    if command == "observe-training":
        args.extend(["en", str(receipt), hashlib.sha256(receipt.read_bytes()).hexdigest()])
    args.append(str(tmp_path / "observations.json"))
    result = CliRunner().invoke(
        create_vocabulary_app(settings=Settings(
            _env_file=None, native_language_model_profiles={"en": "balanced"}
        )), args,
    )
    assert result.exit_code == 0, result.output
    assert calls[0].get("model_profiles") == {"en": "balanced"}
