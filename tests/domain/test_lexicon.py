"""Contract tests for lexical candidate domain models."""

from __future__ import annotations

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import (
    DeckLanguagePolicy,
    DefinitionRecord,
    GroundingStatus,
    LexicalCardCandidate,
    LexicalProvenance,
    PronunciationRecord,
    policy_for_language,
)


def test_candidate_keeps_submitted_and_lemma_values() -> None:
    candidate = LexicalCardCandidate(
        submitted_form="hablarse",
        display_form="hablarse",
        lemma="hablar",
        lemma_key="es:hablar",
        frequency_rank=42,
        frequency_level=1,
        definitions_html="to speak",
        definition_language="en",
        ipa="/aˈβlaɾ/",
        translation_target_language="en",
        grounding_status=GroundingStatus.GROUNDED,
        warning_code=None,
        warning_detail=None,
        provenance=LexicalProvenance(
            source="manual",
            definition=DefinitionRecord(source="manual", value="to speak"),
            pronunciation=PronunciationRecord(source="manual", value="/aˈβlaɾ/"),
        ),
    )

    assert candidate.submitted_form == "hablarse"
    assert candidate.display_form == "hablarse"
    assert candidate.lemma == "hablar"
    assert candidate.lemma_key == "es:hablar"


def test_policy_for_english_targets_portuguese_definition_and_translation() -> None:
    english_policy = policy_for_language(SupportedLanguage.EN)
    french_policy = policy_for_language(SupportedLanguage.FR)

    assert english_policy == DeckLanguagePolicy(
        deck_language=SupportedLanguage.EN,
        definition_language="pt",
        translation_target_language="pt",
    )
    assert french_policy.definition_language == "en"
    assert french_policy.translation_target_language == "en"


def test_candidate_models_pending_state_without_fabricated_ipa() -> None:
    candidate = LexicalCardCandidate(
        submitted_form="onde quer que",
        display_form="onde quer que",
        lemma="onde quer que",
        lemma_key="pt:onde-quer-que",
        frequency_rank=None,
        frequency_level=None,
        definitions_html="wherever",
        definition_language="en",
        ipa=None,
        translation_target_language="en",
        grounding_status=GroundingStatus.PENDING,
        warning_code="missing-ipa",
        warning_detail="No authoritative pronunciation found.",
        provenance=LexicalProvenance(
            source="user-input",
            definition=DefinitionRecord(source="fallback", value="wherever", fallback_used=True),
            pronunciation=PronunciationRecord(source="missing", value=None, authoritative=False),
        ),
    )

    assert candidate.ipa is None
    assert candidate.grounding_status is GroundingStatus.PENDING
    assert candidate.warning_code == "missing-ipa"
    assert candidate.provenance.pronunciation is not None
    assert candidate.provenance.pronunciation.authoritative is False
