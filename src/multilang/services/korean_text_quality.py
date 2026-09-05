"""Deterministic Korean text-quality gates and adaptive prefix evidence."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
import re
from typing import Any, Literal

from multilang.domain.korean import (
    KOREAN_TEXT_QUALITY_POLICY_VERSION,
    KoreanAnalyzerFingerprint,
    KoreanFrequencyEntry,
    KoreanLexicalIdentity,
    KoreanMatchResult,
    KoreanMatchStatus,
    KoreanTextError,
    canonical_json_sha256,
    canonicalize_korean,
    korean_lexical_concept_id,
)
from multilang.domain.text_quality import (
    KOREAN_ADAPTIVE_EVIDENCE_POLICY_VERSION,
    KoreanAdaptiveIPlusOneEvidence,
    KoreanTextSelectionEvidence,
)
from multilang.services.korean_foundation_snapshot import (
    resolve_active_korean_foundation_snapshot,
    verify_active_korean_foundation_snapshot_provenance,
)
from multilang.services.korean_morphology import KiwiKoreanMorphologyService
from multilang.services.text_validation import detect_language_mismatch, looks_like_invalid_translation

_HEX = frozenset("0123456789abcdef")
_SELECTOR_VERSION = "korean-text-quality-selector-v1"
_SCORER_VERSION = "adaptive-i-plus-one-v1"
_UNSAFE_MARKUP_RE = re.compile(r"<[^>]+>|&lt;\s*/?\s*[a-z!]", re.IGNORECASE)
_ENGLISH_LEAKAGE_TOKENS = {
    "and",
    "are",
    "from",
    "go",
    "goes",
    "is",
    "school",
    "student",
    "the",
    "to",
    "today",
    "with",
}


@dataclass(frozen=True, slots=True)
class KoreanKnownPrefixEvidence:
    """Path-free known-state prefix bound to Phase 31 and frozen ranks."""

    target_rank: int
    foundation_concept_ids: tuple[str, ...]
    lexical_concept_ids: tuple[str, ...]
    known_concept_ids: tuple[str, ...]
    known_concept_count: int
    known_prefix_sha256: str
    phase31_pointer_locator_sha256: str
    phase31_pointer_content_sha256: str
    phase31_validation_receipt_sha256: str
    phase31_snapshot_manifest_sha256: str
    phase31_snapshot_root_sha256: str
    frequency_bundle_locator_sha256: str
    frequency_bundle_content_sha256: str


@dataclass(frozen=True, slots=True)
class KoreanTextQualityEvaluation:
    """Candidate selection outcome; machine evidence never means approval."""

    selectable: bool
    hard_gate_codes: tuple[str, ...]
    adaptive_evidence: KoreanAdaptiveIPlusOneEvidence | None
    selection_evidence: KoreanTextSelectionEvidence | None
    score_components: dict[str, float]
    review_status: Literal["review_required"] = "review_required"


@dataclass(frozen=True, slots=True)
class KoreanTextCandidate:
    """One provider/generated Korean sentence candidate with stable provider ordinal."""

    sentence_text: str
    translation_text: str
    observed_concept_ids: tuple[str, ...]
    candidate_sha256: str
    ordinal: int
    intended_sense_id: str | None = None
    register_exception_evidence_sha256: str | None = None


class KoreanTextQualityService:
    """Build Korean frozen-prefix evidence and gate candidates before scoring."""

    def __init__(
        self,
        *,
        active_snapshot_resolver: Callable[[], object] = resolve_active_korean_foundation_snapshot,
        active_provenance_verifier: Callable[..., object] = verify_active_korean_foundation_snapshot_provenance,
        korean_matcher: object | None = None,
    ) -> None:
        self._active_snapshot_resolver = active_snapshot_resolver
        self._active_provenance_verifier = active_provenance_verifier
        self._korean_matcher = korean_matcher or KiwiKoreanMorphologyService()

    def known_prefix(
        self,
        *,
        target_rank: int,
        frequency_entries: Iterable[KoreanFrequencyEntry],
        expected_phase31_receipt_sha256: str,
        phase31_pointer_locator_sha256: str,
        phase31_pointer_content_sha256: str,
        frequency_bundle_locator_sha256: str,
        frequency_bundle_content_sha256: str,
    ) -> KoreanKnownPrefixEvidence:
        if target_rank < 1:
            raise ValueError("target_rank must be positive")
        expected_phase31_receipt_sha256 = _sha256(expected_phase31_receipt_sha256, field_name="phase31 receipt")
        phase31_pointer_locator_sha256 = _sha256(phase31_pointer_locator_sha256, field_name="phase31 pointer locator")
        phase31_pointer_content_sha256 = _sha256(phase31_pointer_content_sha256, field_name="phase31 pointer content")
        frequency_bundle_locator_sha256 = _sha256(frequency_bundle_locator_sha256, field_name="frequency bundle locator")
        frequency_bundle_content_sha256 = _sha256(frequency_bundle_content_sha256, field_name="frequency bundle content")

        snapshot = self._active_snapshot_resolver()
        if getattr(snapshot, "receipt_sha256", None) != expected_phase31_receipt_sha256:
            raise ValueError("Phase 31 active receipt drift")
        self._active_provenance_verifier(expected_receipt_sha256=expected_phase31_receipt_sha256)
        phase31_snapshot_manifest_sha256 = _sha256(
            getattr(snapshot, "snapshot_manifest_sha256", None),
            field_name="phase31 snapshot manifest",
        )
        phase31_snapshot_root_sha256 = _sha256(
            getattr(snapshot, "snapshot_root_sha256", None),
            field_name="phase31 snapshot root",
        )

        entries = tuple(KoreanFrequencyEntry.model_validate(entry.model_dump(mode="python")) for entry in frequency_entries)
        prior_entries = tuple(sorted((entry for entry in entries if entry.final_rank < target_rank), key=lambda entry: entry.final_rank))
        expected_ranks = tuple(range(1, target_rank))
        actual_ranks = tuple(entry.final_rank for entry in prior_entries)
        if actual_ranks != expected_ranks:
            raise ValueError("missing lower Korean frequency rank")
        if any(entry.bundle_sha256 != frequency_bundle_content_sha256 for entry in prior_entries):
            raise ValueError("Korean frequency bundle authority drift")

        foundation_concept_ids = _foundation_concept_ids(snapshot)
        lexical_concept_ids = tuple(korean_lexical_concept_id(entry.lexical_identity) for entry in prior_entries)
        known_concept_ids = tuple(sorted((*foundation_concept_ids, *lexical_concept_ids)))
        if len(known_concept_ids) != len(set(known_concept_ids)):
            raise ValueError("duplicate Korean known concept")
        payload = {
            "policy_version": KOREAN_TEXT_QUALITY_POLICY_VERSION,
            "target_rank": target_rank,
            "foundation_concept_ids": foundation_concept_ids,
            "lexical_concept_ids": lexical_concept_ids,
            "known_concept_ids": known_concept_ids,
            "phase31_pointer_locator_sha256": phase31_pointer_locator_sha256,
            "phase31_pointer_content_sha256": phase31_pointer_content_sha256,
            "phase31_validation_receipt_sha256": expected_phase31_receipt_sha256,
            "phase31_snapshot_manifest_sha256": phase31_snapshot_manifest_sha256,
            "phase31_snapshot_root_sha256": phase31_snapshot_root_sha256,
            "frequency_bundle_locator_sha256": frequency_bundle_locator_sha256,
            "frequency_bundle_content_sha256": frequency_bundle_content_sha256,
        }
        return KoreanKnownPrefixEvidence(
            target_rank=target_rank,
            foundation_concept_ids=foundation_concept_ids,
            lexical_concept_ids=lexical_concept_ids,
            known_concept_ids=known_concept_ids,
            known_concept_count=len(known_concept_ids),
            known_prefix_sha256=canonical_json_sha256(payload),
            phase31_pointer_locator_sha256=phase31_pointer_locator_sha256,
            phase31_pointer_content_sha256=phase31_pointer_content_sha256,
            phase31_validation_receipt_sha256=expected_phase31_receipt_sha256,
            phase31_snapshot_manifest_sha256=phase31_snapshot_manifest_sha256,
            phase31_snapshot_root_sha256=phase31_snapshot_root_sha256,
            frequency_bundle_locator_sha256=frequency_bundle_locator_sha256,
            frequency_bundle_content_sha256=frequency_bundle_content_sha256,
        )

    def build_adaptive_evidence(
        self,
        *,
        prefix: KoreanKnownPrefixEvidence,
        target_entry: KoreanFrequencyEntry,
        observed_concept_ids: Iterable[str],
        candidate_sha256: str,
        selected_ordinal: int,
        hard_gate_codes: Iterable[str] = (),
        score_components: dict[str, float] | None = None,
    ) -> KoreanAdaptiveIPlusOneEvidence:
        candidate_sha256 = _sha256(candidate_sha256, field_name="candidate")
        target_entry = KoreanFrequencyEntry.model_validate(target_entry.model_dump(mode="python"))
        target_concept_id = korean_lexical_concept_id(target_entry.lexical_identity)
        observed = _safe_unique_sorted(observed_concept_ids, field_name="observed concepts")
        if target_concept_id not in observed:
            raise ValueError("observed Korean concepts must include the target")
        incidental = tuple(
            concept_id
            for concept_id in observed
            if concept_id not in set(prefix.known_concept_ids) and concept_id != target_concept_id
        )
        components = score_components or {
            "known_concept_count": float(prefix.known_concept_count),
            "incidental_concept_count": float(len(incidental)),
        }
        return KoreanAdaptiveIPlusOneEvidence(
            known_prefix_sha256=prefix.known_prefix_sha256,
            known_concept_ids=prefix.known_concept_ids,
            known_concept_count=prefix.known_concept_count,
            phase31_pointer_locator_sha256=prefix.phase31_pointer_locator_sha256,
            phase31_pointer_content_sha256=prefix.phase31_pointer_content_sha256,
            phase31_validation_receipt_sha256=prefix.phase31_validation_receipt_sha256,
            phase31_snapshot_manifest_sha256=prefix.phase31_snapshot_manifest_sha256,
            phase31_snapshot_root_sha256=prefix.phase31_snapshot_root_sha256,
            frequency_bundle_locator_sha256=prefix.frequency_bundle_locator_sha256,
            frequency_bundle_content_sha256=prefix.frequency_bundle_content_sha256,
            candidate_sha256=candidate_sha256,
            selected_ordinal=selected_ordinal,
            hard_gate_codes=tuple(hard_gate_codes),
            score_components=components,
            policy_version=KOREAN_ADAPTIVE_EVIDENCE_POLICY_VERSION,
            target_concept_id=target_concept_id,
            observed_concept_ids=observed,
            incidental_concept_ids=incidental,
            scorer_version=_SCORER_VERSION,
        )

    def evaluate_candidate(
        self,
        *,
        target_entry: KoreanFrequencyEntry,
        target_rank: int,
        frequency_entries: Iterable[KoreanFrequencyEntry],
        sentence_text: str,
        translation_text: str,
        observed_concept_ids: Iterable[str],
        candidate_sha256: str,
        selected_ordinal: int,
        expected_phase31_receipt_sha256: str,
        phase31_pointer_locator_sha256: str,
        phase31_pointer_content_sha256: str,
        frequency_bundle_locator_sha256: str,
        frequency_bundle_content_sha256: str,
        intended_sense_id: str | None = None,
        register_exception_evidence_sha256: str | None = None,
    ) -> KoreanTextQualityEvaluation:
        target_entry = KoreanFrequencyEntry.model_validate(target_entry.model_dump(mode="python"))
        candidate_sha256 = _sha256(candidate_sha256, field_name="candidate")
        gate_codes = self._hard_gate_codes(
            target_identity=target_entry.lexical_identity,
            sentence_text=sentence_text,
            translation_text=translation_text,
            intended_sense_id=intended_sense_id,
            register_exception_evidence_sha256=register_exception_evidence_sha256,
        )
        candidate_set_sha256 = canonical_json_sha256(
            {
                "candidate_sha256": candidate_sha256,
                "selected_ordinal": selected_ordinal,
                "policy_version": KOREAN_TEXT_QUALITY_POLICY_VERSION,
            }
        )
        if gate_codes:
            return KoreanTextQualityEvaluation(
                selectable=False,
                hard_gate_codes=gate_codes,
                adaptive_evidence=None,
                selection_evidence=KoreanTextSelectionEvidence(
                    candidate_set_sha256=candidate_set_sha256,
                    selected_candidate_sha256=candidate_sha256,
                    selected_ordinal=selected_ordinal,
                    initial_candidate_count=1,
                    repair_attempt_count=0,
                    hard_gate_status="failed",
                    selector_version=_SELECTOR_VERSION,
                ),
                score_components={},
            )

        prefix = self.known_prefix(
            target_rank=target_rank,
            frequency_entries=frequency_entries,
            expected_phase31_receipt_sha256=expected_phase31_receipt_sha256,
            phase31_pointer_locator_sha256=phase31_pointer_locator_sha256,
            phase31_pointer_content_sha256=phase31_pointer_content_sha256,
            frequency_bundle_locator_sha256=frequency_bundle_locator_sha256,
            frequency_bundle_content_sha256=frequency_bundle_content_sha256,
        )
        score_components = {
            "known_concept_count": float(prefix.known_concept_count),
            "incidental_concept_count": float(
                len(
                    set(_safe_unique_sorted(observed_concept_ids, field_name="observed concepts"))
                    - set(prefix.known_concept_ids)
                    - {korean_lexical_concept_id(target_entry.lexical_identity)}
                )
            ),
        }
        adaptive_evidence = self.build_adaptive_evidence(
            prefix=prefix,
            target_entry=target_entry,
            observed_concept_ids=observed_concept_ids,
            candidate_sha256=candidate_sha256,
            selected_ordinal=selected_ordinal,
            score_components=score_components,
        )
        return KoreanTextQualityEvaluation(
            selectable=True,
            hard_gate_codes=(),
            adaptive_evidence=adaptive_evidence,
            selection_evidence=KoreanTextSelectionEvidence(
                candidate_set_sha256=candidate_set_sha256,
                selected_candidate_sha256=candidate_sha256,
                selected_ordinal=selected_ordinal,
                initial_candidate_count=1,
                repair_attempt_count=0,
                hard_gate_status="passed",
                selector_version=_SELECTOR_VERSION,
            ),
            score_components=score_components,
        )

    def select_best_candidate(
        self,
        *,
        target_entry: KoreanFrequencyEntry,
        target_rank: int,
        frequency_entries: Iterable[KoreanFrequencyEntry],
        candidates: Iterable[KoreanTextCandidate],
        expected_phase31_receipt_sha256: str,
        phase31_pointer_locator_sha256: str,
        phase31_pointer_content_sha256: str,
        frequency_bundle_locator_sha256: str,
        frequency_bundle_content_sha256: str,
    ) -> KoreanTextQualityEvaluation:
        candidate_items = tuple(candidates)
        if not candidate_items:
            raise ValueError("Korean candidate set must not be empty")
        candidate_set_sha256 = _candidate_set_sha256(candidate_items)
        frequency_entries = tuple(frequency_entries)
        evaluated: list[tuple[KoreanTextCandidate, KoreanTextQualityEvaluation]] = []
        for candidate in candidate_items:
            if candidate.ordinal < 1:
                raise ValueError("candidate ordinal must be positive")
            evaluated.append(
                (
                    candidate,
                    self.evaluate_candidate(
                        target_entry=target_entry,
                        target_rank=target_rank,
                        frequency_entries=frequency_entries,
                        sentence_text=candidate.sentence_text,
                        translation_text=candidate.translation_text,
                        observed_concept_ids=candidate.observed_concept_ids,
                        candidate_sha256=candidate.candidate_sha256,
                        selected_ordinal=candidate.ordinal,
                        expected_phase31_receipt_sha256=expected_phase31_receipt_sha256,
                        phase31_pointer_locator_sha256=phase31_pointer_locator_sha256,
                        phase31_pointer_content_sha256=phase31_pointer_content_sha256,
                        frequency_bundle_locator_sha256=frequency_bundle_locator_sha256,
                        frequency_bundle_content_sha256=frequency_bundle_content_sha256,
                        intended_sense_id=candidate.intended_sense_id,
                        register_exception_evidence_sha256=candidate.register_exception_evidence_sha256,
                    ),
                )
            )
        selectable = tuple(
            (candidate, evaluation)
            for candidate, evaluation in evaluated
            if evaluation.selectable and evaluation.adaptive_evidence is not None
        )
        if not selectable:
            candidate, evaluation = evaluated[0]
            selection_evidence = KoreanTextSelectionEvidence(
                candidate_set_sha256=candidate_set_sha256,
                selected_candidate_sha256=_sha256(candidate.candidate_sha256, field_name="candidate"),
                selected_ordinal=candidate.ordinal,
                initial_candidate_count=len(candidate_items),
                repair_attempt_count=0,
                hard_gate_status="failed",
                selector_version=_SELECTOR_VERSION,
            )
            return replace(evaluation, selection_evidence=selection_evidence)

        candidate, evaluation = min(
            selectable,
            key=lambda item: (
                float(item[1].score_components.get("incidental_concept_count", 0.0)),
                _sha256(item[0].candidate_sha256, field_name="candidate"),
                item[0].ordinal,
            ),
        )
        selection_evidence = KoreanTextSelectionEvidence(
            candidate_set_sha256=candidate_set_sha256,
            selected_candidate_sha256=_sha256(candidate.candidate_sha256, field_name="candidate"),
            selected_ordinal=candidate.ordinal,
            initial_candidate_count=len(candidate_items),
            repair_attempt_count=0,
            hard_gate_status="passed",
            selector_version=_SELECTOR_VERSION,
        )
        return replace(evaluation, selection_evidence=selection_evidence)

    def _hard_gate_codes(
        self,
        *,
        target_identity: KoreanLexicalIdentity,
        sentence_text: str,
        translation_text: str,
        intended_sense_id: str | None,
        register_exception_evidence_sha256: str | None,
    ) -> tuple[str, ...]:
        gates: list[str] = []
        try:
            canonical_sentence = canonicalize_korean(sentence_text)
        except KoreanTextError:
            canonical_sentence = ""
            gates.append("nfc_or_script")
        else:
            if canonical_sentence != sentence_text:
                gates.append("nfc_or_script")
            if detect_language_mismatch(canonical_sentence, expected_language="ko") is not None:
                gates.append("language")

        normalized_translation = " ".join(str(translation_text or "").split())
        if _contains_unsafe_markup(normalized_translation):
            gates.append("unsafe_markup")
        if _looks_like_english_leakage(normalized_translation):
            gates.append("english_leakage")
        if _looks_like_isolated_translation(normalized_translation):
            gates.append("isolated_word_translation")
        if (
            not normalized_translation
            or normalized_translation == canonical_sentence
            or looks_like_invalid_translation(normalized_translation)
        ):
            gates.append("translation_consistency")
        if intended_sense_id is not None and intended_sense_id != target_identity.sense_id:
            gates.append("source_sense_mismatch")
        if register_exception_evidence_sha256 is not None:
            _sha256(register_exception_evidence_sha256, field_name="register exception evidence")
        elif _violates_default_korean_register(canonical_sentence):
            gates.append("register_policy")
        if _looks_like_korean_template(canonical_sentence):
            gates.append("template_naturalness")

        match_gate = self._selected_morphology_gate(canonical_sentence, target_identity)
        if match_gate is not None:
            gates.append(match_gate)
        return tuple(dict.fromkeys(gates))

    def _selected_morphology_gate(
        self,
        sentence_text: str,
        target_identity: KoreanLexicalIdentity,
    ) -> str | None:
        matcher = self._korean_matcher
        try:
            active_fingerprint = getattr(matcher, "fingerprint")
            if not isinstance(active_fingerprint, KoreanAnalyzerFingerprint):
                raise TypeError("invalid fingerprint")
            active_fingerprint = KoreanAnalyzerFingerprint.model_validate(active_fingerprint.model_dump(mode="python"))
            identity = KoreanLexicalIdentity.model_validate(target_identity.model_dump(mode="python"))
        except (AttributeError, TypeError, ValueError):
            return "selected_morphology_inconclusive"
        if identity.analyzer_fingerprint != active_fingerprint:
            return "selected_morphology_inconclusive"
        try:
            raw_result = matcher.match_target(sentence_text, identity)
            result = KoreanMatchResult.model_validate(raw_result.model_dump(mode="python"))
        except Exception:
            return "selected_morphology_inconclusive"
        if result.analyzer_fingerprint != active_fingerprint:
            return "selected_morphology_inconclusive"
        if result.status is KoreanMatchStatus.MATCHED:
            return None
        if result.status is KoreanMatchStatus.MISMATCH:
            return "selected_morphology_mismatch"
        return "selected_morphology_inconclusive"


def _foundation_concept_ids(snapshot: object) -> tuple[str, ...]:
    registry = getattr(snapshot, "concept_registry", None)
    concepts = tuple(getattr(registry, "concepts", ()) or ())
    if not concepts:
        raise ValueError("Phase 31 active snapshot has no concepts")
    ordered = tuple(sorted(concepts, key=lambda concept: getattr(concept, "sequence", 0)))
    ids = tuple(_safe_identifier(getattr(concept, "id", None), field_name="foundation concept") for concept in ordered)
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate Korean known concept")
    return ids


def _safe_unique_sorted(values: Iterable[str], *, field_name: str) -> tuple[str, ...]:
    ids = tuple(_safe_identifier(value, field_name=field_name) for value in values)
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate {field_name}")
    return tuple(sorted(ids))


def _candidate_set_sha256(candidates: tuple[KoreanTextCandidate, ...]) -> str:
    return canonical_json_sha256(
        {
            "policy_version": KOREAN_TEXT_QUALITY_POLICY_VERSION,
            "candidates": tuple(
                sorted(
                    (
                        {
                            "candidate_sha256": _sha256(candidate.candidate_sha256, field_name="candidate"),
                            "ordinal": candidate.ordinal,
                        }
                        for candidate in candidates
                    ),
                    key=lambda item: (item["candidate_sha256"], item["ordinal"]),
                )
            ),
        }
    )


def _safe_identifier(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a safe identifier")
    normalized = value.strip()
    if not normalized or normalized != value or len(normalized) > 160:
        raise ValueError(f"{field_name} must be a safe identifier")
    if any(not (character.isascii() and (character.isalnum() or character in "._:-")) for character in normalized):
        raise ValueError(f"{field_name} must be a safe identifier")
    return normalized


def _sha256(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _violates_default_korean_register(sentence_text: str) -> bool:
    formal_markers = ("습니다", "습니까", "합니다", "합니까", "했습니다", "하였습니다")
    plain_markers = ("한다", "했다", "이다")
    return any(marker in sentence_text for marker in (*formal_markers, *plain_markers))


def _looks_like_korean_template(sentence_text: str) -> bool:
    normalized = " ".join(sentence_text.split())
    return normalized.startswith(("이 문장", "예문", "다음 문장")) or "사용합니다" in normalized or "사용해요" in normalized


def _contains_unsafe_markup(value: str) -> bool:
    return bool(_UNSAFE_MARKUP_RE.search(value))


def _looks_like_english_leakage(value: str) -> bool:
    tokens = re.findall(r"[A-Za-z]+", value.casefold())
    return len(set(tokens) & _ENGLISH_LEAKAGE_TOKENS) >= 2


def _looks_like_isolated_translation(value: str) -> bool:
    tokens = re.findall(r"[\wÀ-ÿ]+", value, flags=re.UNICODE)
    return len(tokens) == 1


__all__ = [
    "KoreanKnownPrefixEvidence",
    "KoreanTextCandidate",
    "KoreanTextQualityEvaluation",
    "KoreanTextQualityService",
]
