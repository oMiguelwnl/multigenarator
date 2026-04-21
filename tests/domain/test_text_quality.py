"""Contract tests for persisted text-quality records."""

from __future__ import annotations

from multilang.domain.text_quality import (
    ConfidenceLabel,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationFlag,
    ValidationFlagCode,
    ValidationStatus,
)


def make_record(**overrides: object) -> TextQualityRecord:
    payload: dict[str, object] = {
        "job_id": "job-123",
        "item_key": "item-1",
        "lexical_candidate_id": "lex-123",
        "example_sentence": "Eu corro no parque todos os dias.",
        "translation_text": "I run in the park every day.",
        "generation_status": TextGenerationStatus.GENERATED,
        "validation_status": ValidationStatus.PASSED,
        "review_status": ReviewStatus.ACCEPTED,
        "repair_attempt_count": 0,
        "confidence_score": 0.94,
        "confidence_label": ConfidenceLabel.HIGH,
        "validation_flags": [],
        "review_reason": None,
        "sentence_provenance": TextProvenance(
            source="generator",
            provider="openai",
            model="gpt-4.1-mini",
            version="2026-04-21",
            metadata={"prompt_version": "sentence-v1"},
        ),
        "translation_provenance": TextProvenance(
            source="translator",
            provider="deepl",
            model="api",
            version="v2",
            metadata={"glossary": "disabled"},
        ),
    }
    payload.update(overrides)
    return TextQualityRecord(**payload)


def test_text_quality_record_keeps_sentence_and_translation_provenance() -> None:
    record = make_record()

    assert record.example_sentence == "Eu corro no parque todos os dias."
    assert record.translation_text == "I run in the park every day."
    assert record.sentence_provenance.source == "generator"
    assert record.sentence_provenance.metadata["prompt_version"] == "sentence-v1"
    assert record.translation_provenance.source == "translator"
    assert record.translation_provenance.provider == "deepl"


def test_validation_flags_are_machine_readable() -> None:
    flags = [
        ValidationFlag(code=ValidationFlagCode.MISSING_TARGET_LEMMA, detail="lemma not present"),
        ValidationFlag(code=ValidationFlagCode.SENTENCE_TOO_LONG, detail="17 tokens over limit"),
        ValidationFlag(code=ValidationFlagCode.BANNED_PATTERN, detail="contains placeholder text"),
        ValidationFlag(code=ValidationFlagCode.TRANSLATION_MISMATCH, detail="translation drops tense"),
        ValidationFlag(code=ValidationFlagCode.LOW_CONFIDENCE, detail="judge requested review"),
    ]

    record = make_record(
        validation_status=ValidationStatus.FAILED,
        review_status=ReviewStatus.REVIEW_REQUIRED,
        validation_flags=flags,
        review_reason="validation failed after repair",
    )

    assert [flag.code for flag in record.validation_flags] == [
        ValidationFlagCode.MISSING_TARGET_LEMMA,
        ValidationFlagCode.SENTENCE_TOO_LONG,
        ValidationFlagCode.BANNED_PATTERN,
        ValidationFlagCode.TRANSLATION_MISMATCH,
        ValidationFlagCode.LOW_CONFIDENCE,
    ]
    assert all(flag.detail for flag in record.validation_flags)


def test_status_helpers_model_generate_validate_repair_review_flow() -> None:
    pending = make_record(
        generation_status=TextGenerationStatus.PENDING,
        validation_status=ValidationStatus.PENDING,
        review_status=ReviewStatus.NOT_REVIEWED,
    )
    failed_once = make_record(
        generation_status=TextGenerationStatus.REPAIRED,
        validation_status=ValidationStatus.FAILED,
        review_status=ReviewStatus.NOT_REVIEWED,
        repair_attempt_count=1,
    )
    accepted = make_record()

    assert pending.stage_flow == "generate"
    assert pending.can_attempt_repair() is True
    assert failed_once.stage_flow == "review"
    assert failed_once.can_attempt_repair() is False
    assert failed_once.requires_review is True
    assert accepted.stage_flow == "complete"
    assert accepted.requires_review is False
