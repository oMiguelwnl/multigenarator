"""Offline seams for orchestration tests; real NLP has separate model tests."""

from multilang.services.language_identifier import CorpusLanguageIdentifier, LanguageDetectionResult
from multilang.services.morphology import OptionalStanzaMorphologicalAnalyzer
from multilang.services.text_validation import TextValidationService


def use_mechanical_text_validation(monkeypatch):
    """Exercise fallback mechanics; dedicated validation tests cover NLP evidence."""
    monkeypatch.setenv("MULTILANG_FORBID_NETWORK", "1")
    monkeypatch.setenv("MULTILANG_FORBID_PROVIDERS", "1")
    # These tests cover orchestration with synthetic meanings. The exact-pair
    # definition judge and production wiring have their own offline regressions.
    original_init = TextValidationService.__init__

    def mechanical_init(self, *args, **kwargs):
        kwargs["require_definition_consistency"] = False
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(TextValidationService, "__init__", mechanical_init)
    monkeypatch.setattr(OptionalStanzaMorphologicalAnalyzer, "_pipeline_for", lambda *_: None)
    monkeypatch.setattr(
        CorpusLanguageIdentifier, "detect",
        lambda *_args, **_kwargs: LanguageDetectionResult(
            detected_language=None, confidence=0.0, reliable=False,
            provider="offline-orchestration-fixture", detail="corpus checks covered by validation tests",
        ),
    )
