"""Contract tests for lexical candidate domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanSignatureItem,
)
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
    korean_policy = policy_for_language(SupportedLanguage.KO)
    french_policy = policy_for_language(SupportedLanguage.FR)

    assert english_policy == DeckLanguagePolicy(
        deck_language=SupportedLanguage.EN,
        definition_language="pt",
        translation_target_language="pt",
    )
    assert korean_policy == DeckLanguagePolicy(
        deck_language=SupportedLanguage.KO,
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


def test_candidate_round_trips_complete_korean_identity() -> None:
    identity = _korean_identity()

    candidate = LexicalCardCandidate(
        submitted_form="학교",
        display_form="학교",
        lemma="학교",
        lemma_key=identity.lexical_key,
        definitions_html="escola",
        definition_language="pt",
        translation_target_language="pt",
        grounding_status=GroundingStatus.GROUNDED,
        provenance=LexicalProvenance(source="reviewed-fixture"),
        korean_identity=identity,
    )

    restored = LexicalCardCandidate.model_validate(candidate.model_dump(mode="json"))

    assert restored.korean_identity == identity
    assert restored.korean_identity is not None
    assert restored.korean_identity.analyzer_fingerprint == identity.analyzer_fingerprint
    assert restored.korean_identity.morpheme_signature == identity.morpheme_signature


@pytest.mark.parametrize(
    ("lemma", "lemma_key"),
    [
        ("학원", None),
        (None, "ko:not-the-source-identity-key"),
    ],
)
def test_candidate_rejects_korean_identity_lemma_or_key_mismatch(
    lemma: str | None,
    lemma_key: str | None,
) -> None:
    identity = _korean_identity()

    with pytest.raises(ValidationError, match="Korean identity"):
        LexicalCardCandidate(
            submitted_form="학교",
            display_form="학교",
            lemma=lemma or identity.lemma,
            lemma_key=lemma_key or identity.lexical_key,
            definitions_html="escola",
            definition_language="pt",
            translation_target_language="pt",
            grounding_status=GroundingStatus.GROUNDED,
            provenance=LexicalProvenance(source="reviewed-fixture"),
            korean_identity=identity,
        )


def _korean_identity() -> KoreanLexicalIdentity:
    return KoreanLexicalIdentity(
        submitted_form="학교",
        canonical_nfc="학교",
        lemma="학교",
        part_of_speech="NNG",
        sense_id="fixture-school-1",
        register="neutral",
        morpheme_signature=(KoreanSignatureItem(form="학교", pos="NNG"),),
        analyzer_fingerprint=KoreanAnalyzerFingerprint(
            analyzer_name="kiwi",
            analyzer_package_version="0.23.2",
            model_package_version="0.23.0",
            model_type="cong",
            enabled_dialects="standard",
            num_workers=1,
            integrate_allomorph=True,
            top_n=2,
            split_complex=False,
            compatible_jamo=False,
            normalize_coda=False,
            z_coda=False,
            typos=None,
            oov_handling="chr",
            policy_version="kiwi-top2-consensus-v1",
        ),
        status="resolved",
    )
