from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from multilang.services import contextual_morphology
from multilang.settings import Settings


def _document(text):
    word = SimpleNamespace(text=text, lemma="go", upos="VERB", feats=None)
    token = SimpleNamespace(text=text, start_char=0, end_char=len(text), words=[word])
    return SimpleNamespace(sentences=[SimpleNamespace(tokens=[token])])


def test_language_profile_selection_reaches_verified_loading_without_changing_other_languages(
    tmp_path, monkeypatch
):
    status_calls, load_calls = [], []

    def status(language, root, **kwargs):
        status_calls.append((language, root, kwargs))
        return {"available": True, "backend": "stanza", "manifest_sha256": "a" * 64}

    def loader(language, root, **kwargs):
        load_calls.append((language, root, kwargs))
        return _document

    monkeypatch.setattr(contextual_morphology, "model_status", status)
    monkeypatch.setattr(contextual_morphology, "load_stanza_pipeline", loader)
    profiles = {"en": "balanced"}
    service = contextual_morphology.LocalContextualMorphologyService(
        model_root=tmp_path, model_profiles=profiles, threads=2
    )
    profiles["en"] = "accurate"

    assert service.analyze("en", "went").status == "complete"
    assert service.analyze("de", "ging").status == "complete"
    assert status_calls == [("en", tmp_path, {"profile": "balanced"}), ("de", tmp_path, {})]
    assert load_calls == [
        ("en", tmp_path, {"profile": "balanced", "threads": 2}),
        ("de", tmp_path, {"threads": 2}),
    ]


def test_legacy_analyzer_keeps_two_argument_loading_seam(tmp_path, monkeypatch):
    monkeypatch.setattr(
        contextual_morphology,
        "model_status",
        lambda language, root: {"available": True, "backend": "stanza"},
    )
    monkeypatch.setattr(
        contextual_morphology, "load_stanza_pipeline", lambda language, root: _document
    )
    result = contextual_morphology.LocalContextualMorphologyService(model_root=tmp_path).analyze(
        "en", "went"
    )
    assert result.status == "complete"


@pytest.mark.parametrize(
    "profiles", [{"unknown": "balanced"}, {"la": "fast"}, {"ko": "accurate"}, {"en": "other"}]
)
def test_invalid_model_profiles_are_rejected_by_settings(profiles):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, native_language_model_profiles=profiles)


def test_language_profiles_can_be_configured_in_environment(monkeypatch):
    monkeypatch.setenv("MULTILANG_NATIVE_LANGUAGE_MODEL_PROFILES", '{"en":"balanced","de":"accurate"}')
    settings = Settings(_env_file=None)
    assert settings.model_dump().get("native_language_model_profiles") == {
        "en": "balanced",
        "de": "accurate",
    }


@pytest.mark.parametrize("threads", [0, 9, True])
def test_analyzer_rejects_invalid_thread_budgets(threads):
    with pytest.raises(ValueError, match="threads"):
        contextual_morphology.LocalContextualMorphologyService(
            model_root=Path("unused"), threads=threads
        )


def test_native_runtime_uses_configured_language_profiles(tmp_path, monkeypatch):
    from sqlalchemy.orm import Session

    from multilang.native_runtime import build_native_facade

    captured = {}

    class Analyzer:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(contextual_morphology, "LocalContextualMorphologyService", Analyzer)
    settings = Settings(
        _env_file=None,
        native_language_models_dir=tmp_path / "models",
        native_evidence_dir=tmp_path / "evidence",
        native_contextual_bindings_dir=tmp_path / "bindings",
        native_language_model_profiles={"en": "balanced"},
    )
    with Session() as session:
        build_native_facade(session, settings)
    assert captured.get("model_profiles") == {"en": "balanced"}
    assert captured["model_root"] == tmp_path / "models"
