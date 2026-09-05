"""Tests for deterministic Phase 3 text validation."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanMatchResult,
    KoreanMatchStatus,
    KoreanReasonCode,
    KoreanSignatureItem,
)
from multilang.domain.text_quality import ConfidenceLabel, ValidationFlagCode, ValidationStatus
from multilang.services.language_identifier import LanguageDetectionResult
from multilang.services.morphology import MorphologyValidationResult
from multilang.services.text_generation import GeneratedSentence, GeneratedTranslation
from multilang.services.text_validation import TextValidationService, detect_language_mismatch


def build_service() -> TextValidationService:
    return TextValidationService()


class FakeLanguageIdentifier:
    def __init__(self, detected_language: str | None, *, reliable: bool = True) -> None:
        self.detected_language = detected_language
        self.reliable = reliable

    def detect(self, value: str, *, expected_language: str | None = None) -> LanguageDetectionResult:
        return LanguageDetectionResult(
            detected_language=self.detected_language,
            confidence=0.97,
            reliable=self.reliable,
            provider="fake-language-id",
            detail="test detector",
        )


class FakeMorphologicalAnalyzer:
    def __init__(self, result: MorphologyValidationResult) -> None:
        self.result = result
        self.call_count = 0

    def contains_target_lemma(
        self,
        *,
        sentence_text: str,
        target_language: str,
        display_form: str,
        lemma: str,
    ) -> MorphologyValidationResult:
        self.call_count += 1
        return self.result


class FakeKoreanMatcher:
    def __init__(
        self,
        *,
        fingerprint: KoreanAnalyzerFingerprint,
        result: object,
    ) -> None:
        self.fingerprint = fingerprint
        self.result = result
        self.calls: list[tuple[str, KoreanLexicalIdentity]] = []

    def match_target(
        self,
        sentence_text: str,
        target: KoreanLexicalIdentity,
    ) -> object:
        self.calls.append((sentence_text, target))
        return self.result


class ForbiddenLanguageIdentifier:
    def detect(self, value: str, *, expected_language: str | None = None) -> LanguageDetectionResult:
        raise AssertionError("generic language identification must not run for Korean")


def build_korean_fingerprint(
    *, analyzer_package_version: str = "0.23.2"
) -> KoreanAnalyzerFingerprint:
    return KoreanAnalyzerFingerprint(
        analyzer_name="kiwi",
        analyzer_package_version=analyzer_package_version,
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
    )


def build_korean_identity(
    *, fingerprint: KoreanAnalyzerFingerprint | None = None
) -> KoreanLexicalIdentity:
    return KoreanLexicalIdentity(
        submitted_form="먹다",
        canonical_nfc="먹다",
        lemma="먹다",
        part_of_speech="VV",
        sense_id="reviewed:eat:1",
        register="standard",
        morpheme_signature=(KoreanSignatureItem(form="먹", pos="VV"),),
        analyzer_fingerprint=fingerprint or build_korean_fingerprint(),
        status="resolved",
    )


def build_korean_match_result(
    status: KoreanMatchStatus,
    *,
    fingerprint: KoreanAnalyzerFingerprint,
) -> KoreanMatchResult:
    reason_codes = {
        KoreanMatchStatus.MATCHED: KoreanReasonCode.CONSENSUS_MATCH,
        KoreanMatchStatus.MISMATCH: KoreanReasonCode.NO_SIGNATURE_MATCH,
        KoreanMatchStatus.AMBIGUOUS: KoreanReasonCode.ANALYSIS_DISAGREEMENT,
        KoreanMatchStatus.OOV: KoreanReasonCode.OOV_TOKEN,
        KoreanMatchStatus.UNAVAILABLE: KoreanReasonCode.ANALYZER_RUNTIME_ERROR,
        KoreanMatchStatus.MISSING: KoreanReasonCode.MISSING_IDENTITY,
        KoreanMatchStatus.FINGERPRINT_MISMATCH: KoreanReasonCode.FINGERPRINT_MISMATCH,
        KoreanMatchStatus.INVALID: KoreanReasonCode.INVALID_SIGNATURE,
    }
    alternative_matches = {
        KoreanMatchStatus.MATCHED: (True, True),
        KoreanMatchStatus.MISMATCH: (False, False),
        KoreanMatchStatus.AMBIGUOUS: (True, False),
    }.get(status, ())
    return KoreanMatchResult(
        status=status,
        reason_code=reason_codes[status],
        analyzer_fingerprint=fingerprint,
        alternative_matches=alternative_matches,
    )


def build_sentence(*, text: str, target_language: str = "en") -> GeneratedSentence:
    return GeneratedSentence(
        text=text,
        target_language=target_language,
        intended_sense="habit",
        uncertainty_notes=[],
        provenance={"source": "test"},
    )


def build_translation(*, text: str, target_language: str = "pt") -> GeneratedTranslation:
    return GeneratedTranslation(
        text=text,
        target_language=target_language,
        provenance={"source": "test"},
    )


def test_validation_fails_when_sentence_omits_target_form() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="They practice every morning before class."),
        translation=build_translation(text="Eles praticam todas as manhãs antes da aula."),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.MISSING_TARGET_LEMMA in {flag.code for flag in result.validation_flags}
    assert result.confidence_label is ConfidenceLabel.LOW


def test_validation_rejects_non_learner_friendly_or_placeholder_text() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="TODO wash wash wash wash wash wash wash wash wash wash wash wash wash."),
        translation=build_translation(text="Lavar."),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
    )

    codes = {flag.code for flag in result.validation_flags}
    assert ValidationFlagCode.BANNED_PATTERN in codes
    assert ValidationFlagCode.SENTENCE_TOO_LONG in codes
    assert result.validation_status is ValidationStatus.FAILED


def test_validation_flags_translation_copied_from_definition() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="I wash the cup after breakfast every day."),
        translation=build_translation(text="to wash"),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
    )

    assert ValidationFlagCode.TRANSLATION_MISMATCH in {flag.code for flag in result.validation_flags}
    assert result.validation_status is ValidationStatus.FAILED


def test_validation_rejects_isolated_word_translation_for_multi_token_sentence() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="Он хочет достичь цели завтра.", target_language="ru"),
        translation=build_translation(text="to achieve", target_language="en"),
        display_form="дости́чь",
        lemma="достичь",
        definitions_html="verb: to achieve, to attain, to reach",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.TRANSLATION_MISMATCH in {flag.code for flag in result.validation_flags}


def test_validation_allows_full_sentence_translation_for_multi_token_sentence() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="Он хочет достичь цели завтра.", target_language="ru"),
        translation=build_translation(text="He wants to achieve the goal tomorrow.", target_language="en"),
        display_form="дости́чь",
        lemma="достичь",
        definitions_html="verb: to achieve, to attain, to reach",
    )

    assert result.validation_status is ValidationStatus.PASSED
    assert ValidationFlagCode.TRANSLATION_MISMATCH not in {flag.code for flag in result.validation_flags}


def test_validation_rejects_hollow_support_verb_templates() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="I use wash every day."),
        translation=build_translation(text="Eu uso wash todos os dias."),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
    )

    assert ValidationFlagCode.BANNED_PATTERN in {flag.code for flag in result.validation_flags}
    assert result.validation_status is ValidationStatus.FAILED


def test_validation_rejects_generic_meta_sentences() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="The word alpha is useful in daily life."),
        translation=build_translation(text="A palavra alpha é útil no dia a dia."),
        display_form="alpha",
        lemma="alpha",
        definitions_html="definition for alpha",
    )

    assert ValidationFlagCode.BANNED_PATTERN in {flag.code for flag in result.validation_flags}
    assert result.validation_status is ValidationStatus.FAILED


def test_validation_rejects_title_cased_target_form_in_middle_of_sentence() -> None:
    result = build_service().validate(
        sentence=build_sentence(
            text="Des voisins discutent Remercia pendant le dîner.",
            target_language="fr",
        ),
        translation=build_translation(text="translation omitted", target_language="fr"),
        display_form="remercier",
        lemma="remercier",
        definitions_html="verb: to thank someone",
        require_translation=False,
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.BANNED_PATTERN in {flag.code for flag in result.validation_flags}


def test_validation_downgrades_confidence_for_risky_but_valid_text() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="I wash the cup at home."),
        translation=build_translation(text="Eu lavo a xícara em casa."),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
        uncertainty_notes=["model unsure about phrasing"],
    )

    assert result.validation_status is ValidationStatus.PASSED
    assert result.confidence_label is ConfidenceLabel.MEDIUM
    assert result.confidence_score < 0.8


def test_validation_accepts_inflected_spanish_reflexive_forms() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="Yo me lavo antes de dormir.", target_language="es"),
        translation=build_translation(text="I wash myself before sleeping.", target_language="en"),
        display_form="lavarse",
        lemma="lavar",
        definitions_html="to wash oneself",
    )

    assert result.validation_status is ValidationStatus.PASSED
    assert ValidationFlagCode.MISSING_TARGET_LEMMA not in {flag.code for flag in result.validation_flags}


def test_validation_accepts_inflected_german_verb_forms() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="Ich mache jeden Tag Sport.", target_language="de"),
        translation=build_translation(text="I exercise every day.", target_language="en"),
        display_form="machen",
        lemma="machen",
        definitions_html="to do",
    )

    assert result.validation_status is ValidationStatus.PASSED
    assert ValidationFlagCode.MISSING_TARGET_LEMMA not in {flag.code for flag in result.validation_flags}


def test_validation_accepts_no_space_japanese_sentence() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="学校に行く。", target_language="ja"),
        translation=build_translation(text="I go to school.", target_language="en"),
        display_form="学校",
        lemma="学校",
        definitions_html="noun: school",
    )

    assert result.validation_status is ValidationStatus.PASSED
    codes = {flag.code for flag in result.validation_flags}
    assert ValidationFlagCode.MISSING_TARGET_LEMMA not in codes
    assert ValidationFlagCode.SENTENCE_TOO_SHORT not in codes


def test_validation_rejects_non_japanese_sentence_for_japanese_target() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="Friends discuss school during lunch.", target_language="ja"),
        translation=build_translation(text="Amigos conversam sobre a escola no almoço."),
        display_form="学校",
        lemma="学校",
        definitions_html="noun: school",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.LANGUAGE_MISMATCH in {flag.code for flag in result.validation_flags}


def test_validation_accepts_unspaced_simplified_mandarin_with_target() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="我每天去中国银行。", target_language="zh"),
        translation=build_translation(text="I go to the Bank of China every day.", target_language="en"),
        display_form="中国",
        lemma="中国",
        definitions_html="proper noun: China",
    )

    assert result.validation_status is ValidationStatus.PASSED
    codes = {flag.code for flag in result.validation_flags}
    assert ValidationFlagCode.MISSING_TARGET_LEMMA not in codes
    assert ValidationFlagCode.SENTENCE_TOO_SHORT not in codes
    assert ValidationFlagCode.LANGUAGE_MISMATCH not in codes


def test_validation_rejects_mandarin_sentence_without_target_substring() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="我每天阅读中文报纸。", target_language="zh"),
        translation=build_translation(text="I read a Chinese newspaper every day.", target_language="en"),
        display_form="银行",
        lemma="银行",
        definitions_html="noun: bank",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.MISSING_TARGET_LEMMA in {flag.code for flag in result.validation_flags}


def test_validation_rejects_traditional_primary_mandarin_sentence() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="我每天去中國銀行。", target_language="zh"),
        translation=build_translation(text="I go to the Bank of China every day.", target_language="en"),
        display_form="中國",
        lemma="中國",
        definitions_html="proper noun: China",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.LANGUAGE_MISMATCH in {flag.code for flag in result.validation_flags}


def test_validation_rejects_japanese_or_latin_for_mandarin_target() -> None:
    for text in ("私は銀行へ行きます。", "I visit 中国 every day."):
        result = build_service().validate(
            sentence=build_sentence(text=text, target_language="zh"),
            translation=build_translation(text="I visit the bank every day.", target_language="en"),
            display_form="银行",
            lemma="银行",
            definitions_html="noun: bank",
        )

        assert result.validation_status is ValidationStatus.FAILED
        assert ValidationFlagCode.LANGUAGE_MISMATCH in {flag.code for flag in result.validation_flags}


def test_validation_rejects_question_form_fallback_sentences() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="Do you wash at home?"),
        translation=build_translation(text="Você lava em casa?"),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.BANNED_PATTERN in {flag.code for flag in result.validation_flags}


def test_validation_rejects_short_command_like_fallback_sentences() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="Wash the cup!"),
        translation=build_translation(text="Lave a xícara!"),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
    )

    assert result.validation_status is ValidationStatus.FAILED
    codes = {flag.code for flag in result.validation_flags}
    assert ValidationFlagCode.BANNED_PATTERN in codes
    assert ValidationFlagCode.SENTENCE_TOO_SHORT in codes


def test_validation_rejects_short_command_like_fallback_sentences_without_exclamation() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="Wash the cup now."),
        translation=build_translation(text="Lave a xícara agora."),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.BANNED_PATTERN in {flag.code for flag in result.validation_flags}


def test_validation_allows_short_danish_declarative_starting_with_pronoun_target() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="Det regner meget i dag.", target_language="da"),
        translation=build_translation(text="It is raining a lot today.", target_language="en"),
        display_form="det",
        lemma="det",
        definitions_html="pronoun: it<br>pronoun: that",
    )

    assert result.validation_status is ValidationStatus.PASSED
    assert ValidationFlagCode.BANNED_PATTERN not in {flag.code for flag in result.validation_flags}


def test_validation_requires_translation_to_pass_for_otherwise_valid_fallback_sentence() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="I wash the cup at home."),
        translation=build_translation(text="I wash the cup at home."),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.TRANSLATION_MISMATCH in {flag.code for flag in result.validation_flags}


def test_validation_rejects_duplicate_sentence_within_job() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="I wash the cup at home."),
        translation=build_translation(text="Eu lavo a xícara em casa."),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
        disallowed_sentence_texts={"i wash the cup at home"},
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.DUPLICATE_SENTENCE in {flag.code for flag in result.validation_flags}


def test_validation_uses_configurable_highlight_min_sentence_tokens() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="Readers quietly revisit wash pages."),
        translation=build_translation(text="translation omitted by highlight export"),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
        require_translation=False,
        min_sentence_tokens=6,
        max_sentence_tokens=16,
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.SENTENCE_TOO_SHORT in {flag.code for flag in result.validation_flags}


def test_validation_preserves_default_frequency_sentence_maximum() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="I wash the old ceramic cup at home before breakfast every single morning."),
        translation=build_translation(text="Eu lavo a xícara antiga de cerâmica em casa antes do café."),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.SENTENCE_TOO_LONG in {flag.code for flag in result.validation_flags}


def test_validation_rejects_provider_error_page_translation() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="My mamy dobre połączenia kolejowe.", target_language="pl"),
        translation=build_translation(
            text="Error 500 (Server Error)!!1500.That's an error.There was an error. Please try again later.That's all we know.",
            target_language="en",
        ),
        display_form="połączenia",
        lemma="połączenia",
        definitions_html="noun: connections",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.TRANSLATION_MISMATCH in {flag.code for flag in result.validation_flags}


def test_validation_rejects_sentence_in_wrong_language() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="The committee is ready for the meeting.", target_language="pl"),
        translation=build_translation(text="The committee is ready for the meeting.", target_language="en"),
        display_form="komisja",
        lemma="komisja",
        definitions_html="noun: committee",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.LANGUAGE_MISMATCH in {flag.code for flag in result.validation_flags}


def test_validation_rejects_translation_in_wrong_language() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="To jest dobra komisja.", target_language="pl"),
        translation=build_translation(text="O gato esta na casa.", target_language="en"),
        display_form="komisja",
        lemma="komisja",
        definitions_html="noun: committee",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.LANGUAGE_MISMATCH in {flag.code for flag in result.validation_flags}


def test_validation_uses_injected_language_identifier_for_wrong_language() -> None:
    result = TextValidationService(
        language_identifier=FakeLanguageIdentifier("es"),
    ).validate(
        sentence=build_sentence(text="I wash the cup at home.", target_language="en"),
        translation=build_translation(text="Eu lavo a xícara em casa.", target_language="pt"),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.LANGUAGE_MISMATCH in {flag.code for flag in result.validation_flags}


def test_validation_accepts_target_lemma_from_morphological_analyzer() -> None:
    result = TextValidationService(
        morphological_analyzer=FakeMorphologicalAnalyzer(
            MorphologyValidationResult(matched=True, reliable=True, provider="fake-morph", detail="lemma match")
        ),
    ).validate(
        sentence=build_sentence(text="He went home after lunch today."),
        translation=build_translation(text="Ele foi para casa depois do almoço."),
        display_form="go",
        lemma="go",
        definitions_html="verb: to go",
    )

    assert result.validation_status is ValidationStatus.PASSED
    assert ValidationFlagCode.MISSING_TARGET_LEMMA not in {flag.code for flag in result.validation_flags}


def test_validation_rejects_false_positive_when_morphology_disagrees() -> None:
    result = TextValidationService(
        morphological_analyzer=FakeMorphologicalAnalyzer(
            MorphologyValidationResult(matched=False, reliable=True, provider="fake-morph", detail="lemma absent")
        ),
    ).validate(
        sentence=build_sentence(text="The washer is in the room."),
        translation=build_translation(text="A lavadora está na sala."),
        display_form="wash",
        lemma="wash",
        definitions_html="verb: to wash",
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.MORPHOLOGY_MISMATCH in {flag.code for flag in result.validation_flags}


def test_validation_rejects_html_quota_captcha_and_blocked_translation_text() -> None:
    for bad_translation in (
        "<html><body>Server Error</body></html>",
        "Quota for this billing period has been exceeded",
        "Please complete the captcha to continue",
        "Your request was temporarily blocked",
    ):
        result = build_service().validate(
            sentence=build_sentence(text="I wash the cup at home."),
            translation=build_translation(text=bad_translation),
            display_form="wash",
            lemma="wash",
            definitions_html="to wash",
        )
        assert result.validation_status is ValidationStatus.FAILED
        assert ValidationFlagCode.TRANSLATION_MISMATCH in {flag.code for flag in result.validation_flags}


def test_validation_accepts_configurable_highlight_max_sentence_tokens() -> None:
    result = build_service().validate(
        sentence=build_sentence(text="Readers wash the old cup carefully after the quiet morning chapter ends."),
        translation=build_translation(text="translation omitted by highlight export"),
        display_form="wash",
        lemma="wash",
        definitions_html="to wash",
        require_translation=False,
        min_sentence_tokens=6,
        max_sentence_tokens=16,
    )

    assert result.validation_status is ValidationStatus.PASSED
    assert ValidationFlagCode.SENTENCE_TOO_LONG not in {flag.code for flag in result.validation_flags}


def test_korean_matched_identity_accepts_inflection_without_generic_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import multilang.services.text_validation as validation_module

    fingerprint = build_korean_fingerprint()
    identity = build_korean_identity(fingerprint=fingerprint)
    matcher = FakeKoreanMatcher(
        fingerprint=fingerprint,
        result=build_korean_match_result(
            KoreanMatchStatus.MATCHED,
            fingerprint=fingerprint,
        ),
    )
    generic_analyzer = FakeMorphologicalAnalyzer(
        MorphologyValidationResult(
            matched=True,
            reliable=True,
            provider="forbidden-generic-morphology",
            detail="must not run",
        )
    )

    def forbidden_path(*args: object, **kwargs: object) -> object:
        raise AssertionError("Japanese, Mandarin, generic key, suffix, or heuristic path ran")

    monkeypatch.setattr(validation_module, "_japanese_contains_target", forbidden_path)
    monkeypatch.setattr(validation_module, "_mandarin_contains_target", forbidden_path)
    monkeypatch.setattr(validation_module, "_match_keys", forbidden_path)
    monkeypatch.setattr(validation_module, "_derive_matchable_forms", forbidden_path)

    sentence_text = "저는 오늘 집에서 맛있는 밥을 먹었어요."
    result = TextValidationService(
        language_identifier=ForbiddenLanguageIdentifier(),
        morphological_analyzer=generic_analyzer,
        korean_matcher=matcher,
    ).validate(
        sentence=build_sentence(text=sentence_text, target_language="ko"),
        translation=build_translation(text="translation omitted"),
        display_form="먹다",
        lemma="먹다",
        definitions_html="comer",
        korean_identity=identity,
        require_translation=False,
    )

    assert result.validation_status is ValidationStatus.PASSED
    assert result.validation_flags == []
    assert matcher.calls == [(sentence_text, identity)]
    assert generic_analyzer.call_count == 0


@pytest.mark.parametrize(
    "status",
    [
        KoreanMatchStatus.MISMATCH,
        KoreanMatchStatus.AMBIGUOUS,
        KoreanMatchStatus.OOV,
        KoreanMatchStatus.UNAVAILABLE,
        KoreanMatchStatus.MISSING,
        KoreanMatchStatus.FINGERPRINT_MISMATCH,
        KoreanMatchStatus.INVALID,
    ],
)
def test_korean_non_matched_statuses_fail_with_content_free_morphology_detail(
    status: KoreanMatchStatus,
) -> None:
    fingerprint = build_korean_fingerprint()
    identity = build_korean_identity(fingerprint=fingerprint)
    matcher = FakeKoreanMatcher(
        fingerprint=fingerprint,
        result=build_korean_match_result(status, fingerprint=fingerprint),
    )
    sentence_text = "저는 오늘 집에서 맛있는 밥을 먹었어요."

    result = TextValidationService(korean_matcher=matcher).validate(
        sentence=build_sentence(text=sentence_text, target_language="ko"),
        translation=build_translation(text="translation omitted"),
        display_form="먹다",
        lemma="먹다",
        definitions_html="comer",
        korean_identity=identity,
        require_translation=False,
    )

    morphology_flags = [
        flag
        for flag in result.validation_flags
        if flag.code is ValidationFlagCode.MORPHOLOGY_MISMATCH
    ]
    assert result.validation_status is ValidationStatus.FAILED
    assert len(morphology_flags) == 1
    assert status.value in morphology_flags[0].detail
    assert sentence_text not in morphology_flags[0].detail
    assert identity.lemma not in morphology_flags[0].detail
    assert identity.sense_id not in morphology_flags[0].detail


@pytest.mark.parametrize(
    ("status", "projection"),
    [
        (KoreanMatchStatus.MISMATCH, "mismatch"),
        (KoreanMatchStatus.AMBIGUOUS, "inconclusive"),
        (KoreanMatchStatus.OOV, "inconclusive"),
        (KoreanMatchStatus.UNAVAILABLE, "inconclusive"),
        (KoreanMatchStatus.INVALID, "inconclusive"),
    ],
)
def test_korean_selected_kiwi_mismatch_and_inconclusive_projection_is_explicit(
    status: KoreanMatchStatus,
    projection: str,
) -> None:
    fingerprint = build_korean_fingerprint()
    identity = build_korean_identity(fingerprint=fingerprint)
    matcher = FakeKoreanMatcher(
        fingerprint=fingerprint,
        result=build_korean_match_result(status, fingerprint=fingerprint),
    )

    result = TextValidationService(korean_matcher=matcher).validate(
        sentence=build_sentence(
            text="저는 오늘 집에서 맛있는 밥을 먹었어요.",
            target_language="ko",
        ),
        translation=build_translation(text="translation omitted"),
        display_form="먹다",
        lemma="먹다",
        definitions_html="comer",
        korean_identity=identity,
        require_translation=False,
    )

    morphology_detail = next(
        flag.detail
        for flag in result.validation_flags
        if flag.code is ValidationFlagCode.MORPHOLOGY_MISMATCH
    )
    assert result.validation_status is ValidationStatus.FAILED
    assert f"projection={projection}" in morphology_detail
    assert "저는" not in morphology_detail
    assert identity.sense_id not in morphology_detail


@pytest.mark.parametrize("identity_kind", ["missing", "malformed"])
def test_korean_missing_or_malformed_identity_fails_before_matcher(
    identity_kind: str,
) -> None:
    fingerprint = build_korean_fingerprint()
    valid_identity = build_korean_identity(fingerprint=fingerprint)
    identity = (
        None
        if identity_kind == "missing"
        else valid_identity.model_copy(update={"morpheme_signature": ()})
    )
    matcher = FakeKoreanMatcher(
        fingerprint=fingerprint,
        result=build_korean_match_result(
            KoreanMatchStatus.MATCHED,
            fingerprint=fingerprint,
        ),
    )

    result = TextValidationService(korean_matcher=matcher).validate(
        sentence=build_sentence(
            text="저는 오늘 집에서 맛있는 밥을 먹었어요.",
            target_language="ko",
        ),
        translation=build_translation(text="translation omitted"),
        display_form="먹다",
        lemma="먹다",
        definitions_html="comer",
        korean_identity=identity,
        require_translation=False,
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.MORPHOLOGY_MISMATCH in {
        flag.code for flag in result.validation_flags
    }
    assert matcher.calls == []


def test_korean_persisted_fingerprint_drift_fails_before_matcher() -> None:
    active_fingerprint = build_korean_fingerprint()
    persisted_fingerprint = build_korean_fingerprint(analyzer_package_version="0.23.1")
    identity = build_korean_identity(fingerprint=persisted_fingerprint)
    matcher = FakeKoreanMatcher(
        fingerprint=active_fingerprint,
        result=build_korean_match_result(
            KoreanMatchStatus.MATCHED,
            fingerprint=active_fingerprint,
        ),
    )

    result = TextValidationService(korean_matcher=matcher).validate(
        sentence=build_sentence(
            text="저는 오늘 집에서 맛있는 밥을 먹었어요.",
            target_language="ko",
        ),
        translation=build_translation(text="translation omitted"),
        display_form="먹다",
        lemma="먹다",
        definitions_html="comer",
        korean_identity=identity,
        require_translation=False,
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert matcher.calls == []
    morphology_detail = next(
        flag.detail
        for flag in result.validation_flags
        if flag.code is ValidationFlagCode.MORPHOLOGY_MISMATCH
    )
    assert "fingerprint-mismatch" in morphology_detail
    assert "0.23.1" not in morphology_detail
    assert "0.23.2" not in morphology_detail


@pytest.mark.parametrize("result_kind", ["untyped", "drifted"])
def test_korean_only_typed_matched_result_with_equal_fingerprint_passes(
    result_kind: str,
) -> None:
    fingerprint = build_korean_fingerprint()
    identity = build_korean_identity(fingerprint=fingerprint)
    if result_kind == "untyped":
        match_result: object = SimpleNamespace(
            status=KoreanMatchStatus.MATCHED,
            analyzer_fingerprint=fingerprint,
        )
    else:
        match_result = build_korean_match_result(
            KoreanMatchStatus.MATCHED,
            fingerprint=build_korean_fingerprint(analyzer_package_version="0.23.1"),
        )
    matcher = FakeKoreanMatcher(fingerprint=fingerprint, result=match_result)

    result = TextValidationService(korean_matcher=matcher).validate(
        sentence=build_sentence(
            text="저는 오늘 집에서 맛있는 밥을 먹었어요.",
            target_language="ko",
        ),
        translation=build_translation(text="translation omitted"),
        display_form="먹다",
        lemma="먹다",
        definitions_html="comer",
        korean_identity=identity,
        require_translation=False,
    )

    assert result.validation_status is ValidationStatus.FAILED
    assert ValidationFlagCode.MORPHOLOGY_MISMATCH in {
        flag.code for flag in result.validation_flags
    }


def test_korean_language_check_accepts_modern_hangul_without_generic_identifier() -> None:
    assert (
        detect_language_mismatch(
            "저는 오늘 집에서 밥을 먹었어요.",
            expected_language="ko",
            language_identifier=ForbiddenLanguageIdentifier(),
        )
        is None
    )


@pytest.mark.parametrize(
    "unsafe_text",
    [
        "학교ㄱ",
        "Friends eat lunch together.",
        "私は学校で昼ご飯を食べます。",
        "我每天在学校吃午饭。",
    ],
)
def test_korean_language_check_rejects_forbidden_or_non_korean_text_without_echo(
    unsafe_text: str,
) -> None:
    detail = detect_language_mismatch(
        unsafe_text,
        expected_language="ko",
        language_identifier=ForbiddenLanguageIdentifier(),
    )

    assert detail is not None
    assert unsafe_text not in detail


def test_korean_language_check_rejects_non_nfc_hangul_without_echo() -> None:
    unsafe_text = "학교에서 밥을 먹었어요."

    detail = detect_language_mismatch(
        unsafe_text,
        expected_language="ko",
        language_identifier=ForbiddenLanguageIdentifier(),
    )

    assert detail is not None
    assert "non-canonical" in detail
    assert unsafe_text not in detail
