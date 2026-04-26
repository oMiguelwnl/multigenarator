"""Regenerate one persisted text row against stable job and item identity."""

from __future__ import annotations

from multilang.domain.jobs import JobStage, SupportedLanguage
from multilang.domain.text_quality import ReviewStatus, TextGenerationStatus, TextQualityRecord, ValidationStatus
from multilang.services.generate_text_items import GenerateTextItemsService
from multilang.services.text_generation import GeneratedTextBundle
from multilang.services.text_validation import TextValidationResult


class RegenerateTextItemService:
    """Rerun generate -> validate -> repair for one persisted text item."""

    def __init__(
        self,
        *,
        job_repository: object,
        lexical_repository: object,
        text_repository: object,
        text_generation_service: object,
        text_validation_service: object,
    ) -> None:
        self.job_repository = job_repository
        self.lexical_repository = lexical_repository
        self.text_repository = text_repository
        self.text_generation_service = text_generation_service
        self.text_validation_service = text_validation_service

    def execute(
        self,
        *,
        job_id: str,
        item_key: str,
        deck_language: SupportedLanguage,
    ) -> TextQualityRecord:
        existing_record = self.text_repository.get_text_record(job_id, item_key)
        if existing_record is None:
            raise ValueError(f"unknown text record for job {job_id!r} item {item_key!r}")

        persisted_candidate = self.lexical_repository.get_candidate_for_item(job_id, item_key)
        if persisted_candidate is None:
            raise ValueError(f"unknown lexical candidate for job {job_id!r} item {item_key!r}")

        candidate = GenerateTextItemsService._to_candidate(self, persisted_candidate)
        seen_sentences = GenerateTextItemsService._normalize_sentences(
            self.text_repository.list_example_sentences_for_job(job_id, exclude_item_key=item_key)
        )
        generated_bundle = self.text_generation_service.generate_bundle(
            candidate=candidate,
            deck_language=deck_language,
        )
        validation = self._validate_bundle(
            bundle=generated_bundle,
            candidate=candidate,
            seen_sentences=seen_sentences,
        )
        generation_status = TextGenerationStatus.GENERATED
        repair_attempt_count = 0

        if validation.validation_status is ValidationStatus.FAILED:
            repair_attempt_count = 1
            generation_status = TextGenerationStatus.REPAIRED
            generated_bundle = self.text_generation_service.generate_bundle(
                candidate=candidate,
                deck_language=deck_language,
            )
            validation = self._validate_bundle(
                bundle=generated_bundle,
                candidate=candidate,
                seen_sentences=seen_sentences,
            )

        regenerated_record = self._build_record(
            existing_record=existing_record,
            bundle=generated_bundle,
            validation=validation,
            generation_status=generation_status,
            repair_attempt_count=repair_attempt_count,
        )
        saved_record = self.text_repository.upsert_text_record(regenerated_record)
        self.job_repository.record_item_success(
            job_id,
            item_key=item_key,
            completed_stage=JobStage.GENERATE_TEXT,
        )
        return saved_record

    def _validate_bundle(
        self,
        *,
        bundle: GeneratedTextBundle,
        candidate: object,
        seen_sentences: set[str] | None = None,
    ) -> TextValidationResult:
        return self.text_validation_service.validate(
            sentence=bundle.sentence,
            translation=bundle.translation,
            display_form=getattr(candidate, "display_form"),
            lemma=getattr(candidate, "lemma"),
            definitions_html=getattr(candidate, "definitions_html"),
            disallowed_sentence_texts=set(seen_sentences or set()),
        )

    def _build_record(
        self,
        *,
        existing_record: TextQualityRecord,
        bundle: GeneratedTextBundle,
        validation: TextValidationResult,
        generation_status: TextGenerationStatus,
        repair_attempt_count: int,
    ) -> TextQualityRecord:
        review_status = (
            ReviewStatus.ACCEPTED
            if validation.validation_status is ValidationStatus.PASSED
            else ReviewStatus.REVIEW_REQUIRED
        )
        review_reason = None
        if review_status is ReviewStatus.REVIEW_REQUIRED and validation.validation_flags:
            review_reason = validation.validation_flags[0].code.value

        return TextQualityRecord(
            job_id=existing_record.job_id,
            item_key=existing_record.item_key,
            lexical_candidate_id=existing_record.lexical_candidate_id,
            example_sentence=bundle.sentence.text,
            translation_text=bundle.translation.text,
            generation_status=generation_status,
            validation_status=validation.validation_status,
            review_status=review_status,
            repair_attempt_count=repair_attempt_count,
            confidence_score=validation.confidence_score,
            confidence_label=validation.confidence_label,
            validation_flags=validation.validation_flags,
            review_reason=review_reason,
            sentence_provenance=bundle.sentence.provenance,
            translation_provenance=bundle.translation.provenance,
        )


__all__ = ["RegenerateTextItemService"]
