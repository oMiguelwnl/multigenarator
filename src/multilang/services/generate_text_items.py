"""Coordinate generated text validation, single repair, and review routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from multilang.domain.jobs import JobStage, SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.text_quality import (
    ReviewStatus,
    TextGenerationStatus,
    TextQualityRecord,
    ValidationStatus,
)
from multilang.services.text_generation import (
    GeneratedTextBundle,
    SentenceGenerationFallback,
    SentenceGenerationResult,
    TextGenerationService,
)
from multilang.services.text_validation import TextValidationResult, TextValidationService


class TatoebaSentenceSource(Protocol):
    def select_sentence(
        self,
        *,
        display_form: str,
        lemma: str,
        target_language: str,
        translation_target_language: str,
        candidates: list[Any],
    ) -> SentenceGenerationResult | None: ...


@dataclass(slots=True)
class GenerateTextItemsResult:
    processed_items: int = 0
    accepted_items: int = 0
    review_required_items: int = 0


class GenerateTextItemsService:
    """Run generate -> validate -> repair once -> persist for pending text items."""

    def __init__(
        self,
        *,
        job_repository: Any,
        lexical_repository: Any,
        text_repository: Any,
        text_generation_service: TextGenerationService,
        text_validation_service: TextValidationService,
        tatoeba_sentence_source: TatoebaSentenceSource,
    ) -> None:
        self.job_repository = job_repository
        self.lexical_repository = lexical_repository
        self.text_repository = text_repository
        self.text_generation_service = text_generation_service
        self.text_validation_service = text_validation_service
        self.tatoeba_sentence_source = tatoeba_sentence_source

    def execute(
        self,
        *,
        job_id: str,
        deck_language: SupportedLanguage,
    ) -> GenerateTextItemsResult:
        result = GenerateTextItemsResult()

        for persisted_candidate in self.text_repository.list_generation_candidates(job_id):
            candidate_id = getattr(persisted_candidate, "id")
            item_key = getattr(persisted_candidate, "item_key")
            lexical_candidate = self._to_candidate(persisted_candidate)

            generated_bundle = self.text_generation_service.generate_bundle(
                candidate=lexical_candidate,
                deck_language=deck_language,
            )
            validation = self._validate_bundle(bundle=generated_bundle, candidate=lexical_candidate)
            generation_status = TextGenerationStatus.GENERATED
            repair_attempt_count = 0

            # Single repair attempt only.
            if validation.validation_status is ValidationStatus.FAILED:
                repair_attempt_count = 1
                generation_status = TextGenerationStatus.REPAIRED
                generated_bundle, validation = self._attempt_tatoeba_repair(
                    candidate=lexical_candidate,
                    deck_language=deck_language,
                    generated_bundle=generated_bundle,
                    validation=validation,
                )

            record = self._build_record(
                job_id=job_id,
                item_key=item_key,
                lexical_candidate_id=candidate_id,
                bundle=generated_bundle,
                validation=validation,
                generation_status=generation_status,
                repair_attempt_count=repair_attempt_count,
            )
            self.text_repository.upsert_text_record(record)
            self.job_repository.record_item_success(
                job_id,
                item_key=item_key,
                completed_stage=JobStage.GENERATE_TEXT,
            )

            result.processed_items += 1
            if record.review_status is ReviewStatus.ACCEPTED:
                result.accepted_items += 1
            else:
                result.review_required_items += 1

        return result

    def _validate_bundle(
        self,
        *,
        bundle: GeneratedTextBundle,
        candidate: LexicalCardCandidate,
    ) -> TextValidationResult:
        return self.text_validation_service.validate(
            sentence=bundle.sentence,
            translation=bundle.translation,
            display_form=candidate.display_form,
            lemma=candidate.lemma,
            definitions_html=candidate.definitions_html,
        )

    def _build_record(
        self,
        *,
        job_id: str,
        item_key: str,
        lexical_candidate_id: str,
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
            job_id=job_id,
            item_key=item_key,
            lexical_candidate_id=lexical_candidate_id,
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

    def _attempt_tatoeba_repair(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        generated_bundle: GeneratedTextBundle,
        validation: TextValidationResult,
    ) -> tuple[GeneratedTextBundle, TextValidationResult]:
        fallback_sentence = self.tatoeba_sentence_source.select_sentence(
            display_form=candidate.display_form,
            lemma=candidate.lemma,
            target_language=deck_language.value,
            translation_target_language=candidate.translation_target_language,
            candidates=[],
        )
        if fallback_sentence is None:
            return generated_bundle, validation

        repaired_bundle = self.text_generation_service.generate_bundle_from_fallback(
            candidate=candidate,
            deck_language=deck_language,
            fallback=SentenceGenerationFallback(sentence_result=fallback_sentence),
        )
        repaired_validation = self._validate_bundle(bundle=repaired_bundle, candidate=candidate)
        return repaired_bundle, repaired_validation

    def _to_candidate(self, persisted_candidate: Any) -> LexicalCardCandidate:
        if hasattr(persisted_candidate, "candidate"):
            return getattr(persisted_candidate, "candidate")

        return LexicalCardCandidate(
            submitted_form=getattr(persisted_candidate, "submitted_form"),
            display_form=getattr(persisted_candidate, "display_form"),
            lemma=getattr(persisted_candidate, "lemma"),
            lemma_key=getattr(persisted_candidate, "lemma_key"),
            frequency_rank=getattr(persisted_candidate, "frequency_rank"),
            frequency_level=getattr(persisted_candidate, "frequency_level"),
            definitions_html=getattr(persisted_candidate, "definitions_html"),
            definition_language=getattr(persisted_candidate, "definition_language"),
            ipa=getattr(persisted_candidate, "ipa"),
            translation_target_language=getattr(persisted_candidate, "translation_target_language"),
            grounding_status=GroundingStatus(getattr(persisted_candidate, "grounding_status")),
            warning_code=getattr(persisted_candidate, "warning_code"),
            warning_detail=getattr(persisted_candidate, "warning_detail"),
            provenance=LexicalProvenance.model_validate(getattr(persisted_candidate, "provenance")),
        )


__all__ = ["GenerateTextItemsResult", "GenerateTextItemsService"]
