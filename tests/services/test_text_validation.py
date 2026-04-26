"""Tests for deterministic Phase 3 text validation."""

from __future__ import annotations

from multilang.domain.text_quality import ConfidenceLabel, ValidationFlagCode, ValidationStatus
from multilang.services.text_generation import GeneratedSentence, GeneratedTranslation
from multilang.services.text_validation import TextValidationService


def build_service() -> TextValidationService:
    return TextValidationService()


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
