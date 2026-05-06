"""Coordinate generated text validation, single repair, and review routing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

from multilang.domain.jobs import JobStage, SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.source_profiles import get_source_profile
from multilang.security.redaction import redact_sensitive_text
from multilang.domain.text_quality import (
    ConfidenceLabel,
    ReviewStatus,
    TextGenerationStatus,
    TextQualityRecord,
    ValidationFlag,
    ValidationFlagCode,
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
    ) -> SentenceGenerationResult | None: ...


@dataclass(slots=True)
class GenerateTextItemsResult:
    processed_items: int = 0
    accepted_items: int = 0
    review_required_items: int = 0


class GenerateTextItemsService:
    """Run generate -> validate -> AI retry -> Tatoeba fallback -> persist."""

    _sentence_token_re = re.compile(r"\b[\w'-]+\b", re.UNICODE)

    def __init__(
        self,
        *,
        job_repository: Any,
        lexical_repository: Any,
        text_repository: Any,
        text_generation_service: TextGenerationService,
        text_validation_service: TextValidationService,
        tatoeba_sentence_source: TatoebaSentenceSource,
        highlight_import_repository: Any | None = None,
    ) -> None:
        self.job_repository = job_repository
        self.lexical_repository = lexical_repository
        self.text_repository = text_repository
        self.text_generation_service = text_generation_service
        self.text_validation_service = text_validation_service
        self.tatoeba_sentence_source = tatoeba_sentence_source
        self.highlight_import_repository = highlight_import_repository

    def execute(
        self,
        *,
        job_id: str,
        deck_language: SupportedLanguage,
    ) -> GenerateTextItemsResult:
        result = GenerateTextItemsResult()
        seen_sentences = self._normalize_sentences(self.text_repository.list_example_sentences_for_job(job_id))

        for persisted_candidate in self.text_repository.list_generation_candidates(job_id):
            candidate_id = getattr(persisted_candidate, "id")
            item_key = getattr(persisted_candidate, "item_key")
            lexical_candidate = self._to_candidate(persisted_candidate)
            source_type = self._resolve_source_type(
                getattr(persisted_candidate, "source_type", None),
                candidate=lexical_candidate,
            )
            highlight_context = self._build_highlight_context(
                job_id=job_id,
                source_type=source_type,
                candidate=lexical_candidate,
            )

            generated_bundle = self.text_generation_service.generate_bundle(
                candidate=lexical_candidate,
                deck_language=deck_language,
                source_type=source_type,
                highlight_context=highlight_context,
            )
            validation = self._validate_bundle(
                bundle=generated_bundle,
                candidate=lexical_candidate,
                seen_sentences=seen_sentences,
                source_type=source_type,
                deck_language=deck_language,
            )
            generation_status = TextGenerationStatus.GENERATED
            repair_attempt_count = 0

            if validation.validation_status is ValidationStatus.FAILED:
                generation_status = TextGenerationStatus.REPAIRED
                generated_bundle, validation, repair_attempt_count = self._attempt_repair_chain(
                    candidate=lexical_candidate,
                    deck_language=deck_language,
                    generated_bundle=generated_bundle,
                    validation=validation,
                    seen_sentences=seen_sentences,
                    source_type=source_type,
                    highlight_context=highlight_context,
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
            normalized_sentence = self._normalize_sentence_text(record.example_sentence)
            if normalized_sentence:
                seen_sentences.add(normalized_sentence)
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
        seen_sentences: set[str] | None = None,
        source_type: str | None = None,
        deck_language: SupportedLanguage,
    ) -> TextValidationResult:
        source_profile = get_source_profile(self._resolve_source_type(source_type, candidate=candidate))
        validation = self.text_validation_service.validate(
            sentence=bundle.sentence,
            translation=bundle.translation,
            display_form=candidate.display_form,
            lemma=candidate.lemma,
            definitions_html=candidate.definitions_html,
            disallowed_sentence_texts=set(seen_sentences or set()),
            require_translation=(
                source_profile.requires_translation_validation
                and candidate.translation_target_language != deck_language.value
            ),
            min_sentence_tokens=source_profile.min_sentence_tokens,
            max_sentence_tokens=source_profile.max_sentence_tokens,
        )
        return _gate_frequency_local_templates(
            validation=validation,
            bundle=bundle,
            source_type=source_profile.source_type,
            deck_language=deck_language,
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

    def _attempt_repair_chain(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        generated_bundle: GeneratedTextBundle,
        validation: TextValidationResult,
        seen_sentences: set[str],
        source_type: str | None,
        highlight_context: str | None = None,
    ) -> tuple[GeneratedTextBundle, TextValidationResult, int]:
        retry_bundle = self.text_generation_service.generate_bundle(
            candidate=candidate,
            deck_language=deck_language,
            source_type=source_type,
            highlight_context=highlight_context,
        )
        retry_validation = self._validate_bundle(
            bundle=retry_bundle,
            candidate=candidate,
            seen_sentences=seen_sentences,
            source_type=source_type,
            deck_language=deck_language,
        )
        if retry_validation.validation_status is ValidationStatus.PASSED:
            return retry_bundle, retry_validation, 1

        fallback_bundle, fallback_validation = self._attempt_tatoeba_repair(
            candidate=candidate,
            deck_language=deck_language,
            generated_bundle=retry_bundle,
            validation=retry_validation,
            seen_sentences=seen_sentences,
            source_type=source_type,
            highlight_context=highlight_context,
        )
        fallback_used = fallback_bundle is not retry_bundle
        return fallback_bundle, fallback_validation, 2 if fallback_used else 1

    def _attempt_tatoeba_repair(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        generated_bundle: GeneratedTextBundle,
        validation: TextValidationResult,
        seen_sentences: set[str],
        source_type: str | None,
        highlight_context: str | None = None,
    ) -> tuple[GeneratedTextBundle, TextValidationResult]:
        fallback_sentence = self.tatoeba_sentence_source.select_sentence(
            display_form=candidate.display_form,
            lemma=candidate.lemma,
            target_language=deck_language.value,
            translation_target_language=candidate.translation_target_language,
        )
        if fallback_sentence is None:
            return generated_bundle, validation

        repaired_bundle = self.text_generation_service.generate_bundle_from_fallback(
            candidate=candidate,
            deck_language=deck_language,
            fallback=SentenceGenerationFallback(sentence_result=fallback_sentence),
            source_type=source_type,
            highlight_context=highlight_context,
        )
        repaired_validation = self._validate_bundle(
            bundle=repaired_bundle,
            candidate=candidate,
            seen_sentences=seen_sentences,
            source_type=source_type,
            deck_language=deck_language,
        )
        return repaired_bundle, repaired_validation

    @staticmethod
    def _normalize_sentence_text(value: str | None) -> str:
        if value is None:
            return ""
        return " ".join(GenerateTextItemsService._sentence_token_re.findall(value.casefold()))

    @classmethod
    def _normalize_sentences(cls, values: list[str]) -> set[str]:
        return {
            normalized
            for value in values
            if (normalized := cls._normalize_sentence_text(value))
        }

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

    @staticmethod
    def _resolve_source_type(source_type: str | None, *, candidate: LexicalCardCandidate) -> str:
        if source_type:
            return source_type
        if candidate.frequency_rank is not None or candidate.frequency_level is not None:
            return "frequency"
        return "word-list"

    def _build_highlight_context(
        self,
        *,
        job_id: str,
        source_type: str,
        candidate: LexicalCardCandidate,
    ) -> str | None:
        if source_type != "kindle-highlights" or self.highlight_import_repository is None:
            return None
        highlight_id = _provenance_note_value(candidate.provenance.notes, "first_highlight_id")
        if not highlight_id:
            return None
        record = self.highlight_import_repository.get_private_record(job_id, highlight_id)
        if record is None:
            return None
        normalized_text = str(getattr(record, "normalized_text", "") or "").strip()
        if not normalized_text:
            return None
        redacted = redact_sensitive_text(normalized_text)
        return _bounded_context_snippet(
            redacted,
            display_form=candidate.display_form,
            lemma=candidate.lemma,
        )


def _provenance_note_value(notes: list[str], key: str) -> str | None:
    prefix = f"{key}="
    for note in notes:
        if note.startswith(prefix):
            value = note.removeprefix(prefix).strip()
            if value:
                return value
    return None


def _bounded_context_snippet(text: str, *, display_form: str, lemma: str, max_tokens: int = 24) -> str:
    tokens = GenerateTextItemsService._sentence_token_re.findall(text)
    if not tokens:
        return ""
    match_keys = {display_form.casefold(), lemma.casefold()}
    center = 0
    for index, token in enumerate(tokens):
        if token.casefold() in match_keys:
            center = index
            break
    half_window = max_tokens // 2
    start = max(0, center - half_window)
    end = min(len(tokens), start + max_tokens)
    start = max(0, end - max_tokens)
    return " ".join(tokens[start:end])


def _gate_frequency_local_templates(
    *,
    validation: TextValidationResult,
    bundle: GeneratedTextBundle,
    source_type: str | None,
    deck_language: SupportedLanguage,
) -> TextValidationResult:
    if (
        source_type != "frequency"
        or deck_language is SupportedLanguage.EN
        or not _uses_generic_local_text(bundle)
    ):
        return validation

    flags = [
        *validation.validation_flags,
        ValidationFlag(
            code=ValidationFlagCode.BANNED_PATTERN,
            detail="frequency decks must not accept generic local text templates as learner-facing content",
        ),
    ]
    return validation.model_copy(
        update={
            "validation_status": ValidationStatus.FAILED,
            "validation_flags": flags,
            "confidence_score": min(validation.confidence_score, 0.45),
            "confidence_label": ConfidenceLabel.LOW,
        }
    )


def _uses_generic_local_text(bundle: GeneratedTextBundle) -> bool:
    return _is_generic_local_provenance(bundle.sentence.provenance) or _is_generic_local_provenance(
        bundle.translation.provenance
    )


def _is_generic_local_provenance(provenance: object) -> bool:
    provider = getattr(provenance, "provider", None)
    source = getattr(provenance, "source", None)
    metadata = getattr(provenance, "metadata", {}) or {}
    template_kind = str(metadata.get("template_kind") or "")
    local_source = str(metadata.get("source") or "")

    is_local = provider == "local" or source == "local" or local_source.startswith("runtime-local")
    if not is_local:
        return False
    return not template_kind.startswith("curated:")


__all__ = ["GenerateTextItemsResult", "GenerateTextItemsService"]
