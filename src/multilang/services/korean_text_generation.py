"""Bounded Korean text-generation selector shared by batch and item regeneration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Literal

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import LexicalCardCandidate
from multilang.domain.text_quality import TextGenerationStatus, TextQualityRecord, ValidationStatus
from multilang.services.text_generation import (
    GeneratedTextBundle,
    KoreanSelectorAttemptContext,
)
from multilang.services.text_validation import TextValidationResult

KOREAN_TEXT_GENERATION_SELECTOR_VERSION = "korean-text-generation-selector-v1"


ValidateBundle = Callable[..., TextValidationResult]


@dataclass(frozen=True, slots=True)
class KoreanTextGenerationHistoryEntry:
    stage: Literal["initial", "repair"]
    ordinal: int
    candidate_sha256: str
    validation_status: ValidationStatus
    rejection_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class KoreanTextGenerationHistory:
    selector_version: str
    attempts: tuple[KoreanTextGenerationHistoryEntry, ...]

    @property
    def initial_candidate_count(self) -> int:
        return sum(1 for attempt in self.attempts if attempt.stage == "initial")

    @property
    def repair_attempt_count(self) -> int:
        return sum(1 for attempt in self.attempts if attempt.stage == "repair")


@dataclass(frozen=True, slots=True)
class KoreanTextGenerationSelection:
    bundle: GeneratedTextBundle
    validation: TextValidationResult
    generation_status: TextGenerationStatus
    repair_attempt_count: int
    history: KoreanTextGenerationHistory


@dataclass(frozen=True, slots=True)
class _EvaluatedAttempt:
    bundle: GeneratedTextBundle
    validation: TextValidationResult
    history_entry: KoreanTextGenerationHistoryEntry


class KoreanTextGenerationSelector:
    """Generate exactly two initial Korean candidates and at most one repair."""

    def __init__(
        self,
        *,
        text_generation_service: object,
        validate_bundle: ValidateBundle,
    ) -> None:
        self._text_generation_service = text_generation_service
        self._validate_bundle = validate_bundle

    def select(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        source_type: str | None,
        highlight_context: str | None,
        seen_sentences: set[str],
        job_id: str,
        item_key: str,
        rate_limiter: object | None = None,
        remaining_repair_budget: int = 1,
        existing_history: KoreanTextGenerationHistory | None = None,
    ) -> KoreanTextGenerationSelection:
        if deck_language is not SupportedLanguage.KO:
            raise ValueError("Korean selector only handles Korean generation")
        if candidate.korean_identity is None:
            raise ValueError("Korean selector requires a persisted Korean identity")

        if existing_history is not None and existing_history.initial_candidate_count >= 2:
            if existing_history.repair_attempt_count >= 1 or remaining_repair_budget < 1:
                raise ValueError("Korean selector repair budget exhausted")
            repair = self._generate_attempt(
                candidate=candidate,
                deck_language=deck_language,
                source_type=source_type,
                highlight_context=highlight_context,
                seen_sentences=seen_sentences,
                job_id=job_id,
                item_key=item_key,
                rate_limiter=rate_limiter,
                stage="repair",
                ordinal=3,
                rejected_candidate_sha256s=tuple(
                    attempt.candidate_sha256
                    for attempt in existing_history.attempts
                    if attempt.stage == "initial"
                ),
                rejection_codes=_combined_history_rejection_codes(existing_history),
            )
            history = KoreanTextGenerationHistory(
                selector_version=KOREAN_TEXT_GENERATION_SELECTOR_VERSION,
                attempts=(*existing_history.attempts, repair.history_entry),
            )
            return KoreanTextGenerationSelection(
                bundle=repair.bundle,
                validation=repair.validation,
                generation_status=TextGenerationStatus.REPAIRED,
                repair_attempt_count=history.repair_attempt_count,
                history=history,
            )

        attempts = [
            self._generate_attempt(
                candidate=candidate,
                deck_language=deck_language,
                source_type=source_type,
                highlight_context=highlight_context,
                seen_sentences=seen_sentences,
                job_id=job_id,
                item_key=item_key,
                rate_limiter=rate_limiter,
                stage="initial",
                ordinal=1,
                rejected_candidate_sha256s=(),
                rejection_codes=(),
            ),
            self._generate_attempt(
                candidate=candidate,
                deck_language=deck_language,
                source_type=source_type,
                highlight_context=highlight_context,
                seen_sentences=seen_sentences,
                job_id=job_id,
                item_key=item_key,
                rate_limiter=rate_limiter,
                stage="initial",
                ordinal=2,
                rejected_candidate_sha256s=(),
                rejection_codes=(),
            ),
        ]
        passed_initial = _best_passed_attempt(attempts)
        if passed_initial is not None:
            return KoreanTextGenerationSelection(
                bundle=passed_initial.bundle,
                validation=passed_initial.validation,
                generation_status=TextGenerationStatus.GENERATED,
                repair_attempt_count=0,
                history=KoreanTextGenerationHistory(
                    selector_version=KOREAN_TEXT_GENERATION_SELECTOR_VERSION,
                    attempts=tuple(attempt.history_entry for attempt in attempts),
                ),
            )

        if remaining_repair_budget > 0:
            repair = self._generate_attempt(
                candidate=candidate,
                deck_language=deck_language,
                source_type=source_type,
                highlight_context=highlight_context,
                seen_sentences=seen_sentences,
                job_id=job_id,
                item_key=item_key,
                rate_limiter=rate_limiter,
                stage="repair",
                ordinal=3,
                rejected_candidate_sha256s=tuple(attempt.history_entry.candidate_sha256 for attempt in attempts),
                rejection_codes=_combined_rejection_codes(attempts),
            )
            attempts.append(repair)
            return KoreanTextGenerationSelection(
                bundle=repair.bundle,
                validation=repair.validation,
                generation_status=TextGenerationStatus.REPAIRED,
                repair_attempt_count=1,
                history=KoreanTextGenerationHistory(
                    selector_version=KOREAN_TEXT_GENERATION_SELECTOR_VERSION,
                    attempts=tuple(attempt.history_entry for attempt in attempts),
                ),
            )

        failed = _best_failed_attempt(attempts)
        return KoreanTextGenerationSelection(
            bundle=failed.bundle,
            validation=failed.validation,
            generation_status=TextGenerationStatus.GENERATED,
            repair_attempt_count=0,
            history=KoreanTextGenerationHistory(
                selector_version=KOREAN_TEXT_GENERATION_SELECTOR_VERSION,
                attempts=tuple(attempt.history_entry for attempt in attempts),
            ),
        )

    def _generate_attempt(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        source_type: str | None,
        highlight_context: str | None,
        seen_sentences: set[str],
        job_id: str,
        item_key: str,
        rate_limiter: object | None,
        stage: Literal["initial", "repair"],
        ordinal: int,
        rejected_candidate_sha256s: tuple[str, ...],
        rejection_codes: tuple[str, ...],
    ) -> _EvaluatedAttempt:
        context = KoreanSelectorAttemptContext(
            stage=stage,
            ordinal=ordinal,
            cache_identity=_attempt_cache_identity(
                job_id=job_id,
                item_key=item_key,
                stage=stage,
                ordinal=ordinal,
                rejected_candidate_sha256s=rejected_candidate_sha256s,
                rejection_codes=rejection_codes,
            ),
            rejected_candidate_sha256s=rejected_candidate_sha256s,
            rejection_codes=rejection_codes,
        )
        bundle = self._text_generation_service.generate_bundle(
            candidate=candidate,
            deck_language=deck_language,
            source_type=source_type,
            highlight_context=highlight_context,
            rate_limiter=rate_limiter,
            job_id=job_id,
            korean_selector_attempt=context,
        )
        validation = self._validate_bundle(
            bundle=bundle,
            candidate=candidate,
            seen_sentences=seen_sentences,
            source_type=source_type,
            deck_language=deck_language,
        )
        entry = KoreanTextGenerationHistoryEntry(
            stage=stage,
            ordinal=ordinal,
            candidate_sha256=_candidate_sha256(bundle, candidate=candidate),
            validation_status=validation.validation_status,
            rejection_codes=_rejection_codes(validation),
        )
        return _EvaluatedAttempt(bundle=bundle, validation=validation, history_entry=entry)


def _best_passed_attempt(attempts: list[_EvaluatedAttempt]) -> _EvaluatedAttempt | None:
    passed = [attempt for attempt in attempts if attempt.validation.validation_status is ValidationStatus.PASSED]
    if not passed:
        return None
    return min(
        passed,
        key=lambda attempt: (
            -float(attempt.validation.confidence_score or 0.0),
            attempt.history_entry.candidate_sha256,
            attempt.history_entry.ordinal,
        ),
    )


def _best_failed_attempt(attempts: list[_EvaluatedAttempt]) -> _EvaluatedAttempt:
    return min(
        attempts,
        key=lambda attempt: (
            -float(attempt.validation.confidence_score or 0.0),
            attempt.history_entry.candidate_sha256,
            attempt.history_entry.ordinal,
        ),
    )


def _combined_rejection_codes(attempts: list[_EvaluatedAttempt]) -> tuple[str, ...]:
    codes: list[str] = []
    for attempt in attempts:
        for code in attempt.history_entry.rejection_codes:
            if code not in codes:
                codes.append(code)
    return tuple(codes)


def _combined_history_rejection_codes(history: KoreanTextGenerationHistory) -> tuple[str, ...]:
    codes: list[str] = []
    for attempt in history.attempts:
        for code in attempt.rejection_codes:
            if code not in codes:
                codes.append(code)
    return tuple(codes)


def _rejection_codes(validation: TextValidationResult) -> tuple[str, ...]:
    if validation.validation_status is ValidationStatus.PASSED:
        return ()
    codes = tuple(dict.fromkeys(flag.code.value for flag in validation.validation_flags))
    return codes or ("low_confidence",)


def _candidate_sha256(bundle: GeneratedTextBundle, *, candidate: LexicalCardCandidate) -> str:
    identity = candidate.korean_identity
    payload = {
        "selector_version": KOREAN_TEXT_GENERATION_SELECTOR_VERSION,
        "identity_sha256": sha256(
            json.dumps(
                identity.model_dump(mode="json") if identity is not None else None,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        "sentence_sha256": sha256(bundle.sentence.text.encode("utf-8")).hexdigest(),
        "translation_sha256": sha256(bundle.translation.text.encode("utf-8")).hexdigest(),
        "translation_target_language": bundle.translation.target_language,
    }
    return _stable_sha256(payload)


def _attempt_cache_identity(
    *,
    job_id: str,
    item_key: str,
    stage: str,
    ordinal: int,
    rejected_candidate_sha256s: tuple[str, ...],
    rejection_codes: tuple[str, ...],
) -> str:
    return _stable_sha256(
        {
            "selector_version": KOREAN_TEXT_GENERATION_SELECTOR_VERSION,
            "job_id": job_id,
            "item_key": item_key,
            "stage": stage,
            "ordinal": ordinal,
            "rejected_candidate_sha256s": rejected_candidate_sha256s,
            "rejection_codes": rejection_codes,
        }
    )


def _stable_sha256(payload: Any) -> str:
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def korean_selector_history_to_metadata(history: KoreanTextGenerationHistory) -> dict[str, Any]:
    return {
        "selector_version": history.selector_version,
        "initial_candidate_count": history.initial_candidate_count,
        "repair_attempt_count": history.repair_attempt_count,
        "attempts": [
            {
                "stage": attempt.stage,
                "ordinal": attempt.ordinal,
                "candidate_sha256": attempt.candidate_sha256,
                "validation_status": attempt.validation_status.value,
                "rejection_codes": list(attempt.rejection_codes),
            }
            for attempt in history.attempts
        ],
    }


def korean_selector_history_from_record(record: object | None) -> KoreanTextGenerationHistory | None:
    if record is None:
        return None
    provenance = getattr(record, "sentence_provenance", None)
    metadata = getattr(provenance, "metadata", {}) or {}
    raw_history = metadata.get("korean_selector_history") if isinstance(metadata, dict) else None
    if raw_history is None:
        return None
    if not isinstance(raw_history, dict):
        raise ValueError("Korean selector history must be structured metadata")
    raw_attempts = raw_history.get("attempts")
    if not isinstance(raw_attempts, list):
        raise ValueError("Korean selector history attempts must be structured metadata")
    attempts: list[KoreanTextGenerationHistoryEntry] = []
    for raw_attempt in raw_attempts:
        if not isinstance(raw_attempt, dict):
            raise ValueError("Korean selector history attempt must be structured metadata")
        attempts.append(
            KoreanTextGenerationHistoryEntry(
                stage=_history_stage(raw_attempt.get("stage")),
                ordinal=int(raw_attempt.get("ordinal")),
                candidate_sha256=_history_hash(raw_attempt.get("candidate_sha256")),
                validation_status=ValidationStatus(str(raw_attempt.get("validation_status"))),
                rejection_codes=tuple(str(code) for code in raw_attempt.get("rejection_codes", ())),
            )
        )
    history = KoreanTextGenerationHistory(
        selector_version=str(raw_history.get("selector_version") or KOREAN_TEXT_GENERATION_SELECTOR_VERSION),
        attempts=tuple(attempts),
    )
    if history.initial_candidate_count > 2 or history.repair_attempt_count > 1:
        raise ValueError("Korean selector history exceeds bounded 2+1 contract")
    return history


def with_korean_selector_history(
    record: TextQualityRecord,
    history: KoreanTextGenerationHistory,
) -> TextQualityRecord:
    provenance = record.sentence_provenance
    metadata = dict(provenance.metadata or {})
    metadata["korean_selector_history"] = korean_selector_history_to_metadata(history)
    return record.model_copy(
        update={
            "sentence_provenance": provenance.model_copy(update={"metadata": metadata})
        }
    )


def _history_stage(value: object) -> Literal["initial", "repair"]:
    if value in {"initial", "repair"}:
        return value  # type: ignore[return-value]
    raise ValueError("Korean selector history stage must be initial or repair")


def _history_hash(value: object) -> str:
    if isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value):
        return value
    raise ValueError("Korean selector history hash must be lowercase SHA-256")


__all__ = [
    "KOREAN_TEXT_GENERATION_SELECTOR_VERSION",
    "KoreanTextGenerationHistory",
    "KoreanTextGenerationHistoryEntry",
    "KoreanTextGenerationSelection",
    "KoreanTextGenerationSelector",
    "korean_selector_history_from_record",
    "korean_selector_history_to_metadata",
    "with_korean_selector_history",
]
