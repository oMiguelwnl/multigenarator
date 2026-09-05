"""Korean grammar bundle construction and strict graph validation."""

from __future__ import annotations

from enum import Enum
from graphlib import CycleError, TopologicalSorter
from typing import Callable, Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from multilang.domain.korean import KoreanConcept
from multilang.domain.korean_grammar import (
    KOREAN_GRAMMAR_CATEGORIES,
    KOREAN_GRAMMAR_SOURCE_KIND,
    KoreanGrammarBootstrapEntry,
    KoreanGrammarBundle,
    KoreanGrammarEntry,
    Phase31GrammarRootBinding,
    build_bundle_sha256,
    build_member_hashes,
    korean_grammar_canonical_json_sha256,
)
from multilang.services.korean_foundation_snapshot import (
    resolve_active_korean_foundation_snapshot,
)


_MAX_IDS: Final = 512


class KoreanGrammarReasonCode(str, Enum):
    """Content-free Korean grammar validation failures."""

    PHASE31_NOT_ACTIVE = "phase31_not_active"
    PHASE31_HASH_DRIFT = "phase31_hash_drift"
    CONCEPT_COLLISION = "concept_collision"
    UNKNOWN_CONCEPT = "unknown_concept"
    CONCEPT_CYCLE = "concept_cycle"
    FORWARD_DEPENDENCY = "forward_dependency"
    INCOMPLETE_CLOSURE = "incomplete_closure"
    STRICT_POLICY_REQUIRED = "strict_policy_required"
    TARGET_NOT_OBSERVED = "target_not_observed"
    REPEATED_TARGET = "repeated_target"
    UNKNOWN_PREREQUISITE = "unknown_prerequisite"
    EXACTLY_ONE_UNKNOWN_REQUIRED = "exactly_one_unknown_required"
    SERIALIZED_UNKNOWN_MISMATCH = "serialized_unknown_mismatch"
    BROAD_TARGET_CATEGORY = "broad_target_category"


class KoreanGrammarError(ValueError):
    """A controlled grammar failure that never includes source content."""

    def __init__(self, reason_code: KoreanGrammarReasonCode) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code.value)


class _FrozenServiceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class KoreanGrammarValidationResult(_FrozenServiceModel):
    """Recomputed grammar graph and production readiness result."""

    ready_state: Literal["blocked", "learner_ready"]
    imported_known_concept_ids: tuple[str, ...] = Field(default=(), max_length=_MAX_IDS)
    admitted_bootstrap_concept_ids: tuple[str, ...] = Field(default=(), max_length=_MAX_IDS)
    admitted_grammar_concept_ids: tuple[str, ...] = Field(default=(), max_length=_MAX_IDS)
    known_concept_ids: tuple[str, ...] = Field(default=(), max_length=_MAX_IDS)
    blocked_reason_codes: tuple[str, ...] = Field(default=(), max_length=_MAX_IDS)


def _raise(reason_code: KoreanGrammarReasonCode) -> None:
    raise KoreanGrammarError(reason_code)


def _sha256_or_fail(value: object) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        _raise(KoreanGrammarReasonCode.PHASE31_HASH_DRIFT)
    return value


def _concept_registry_member_sha256(snapshot: object) -> str:
    for member in getattr(snapshot, "members", ()):
        if getattr(member, "role", None) == "concept_registry":
            return _sha256_or_fail(getattr(member, "sha256", None))
    _raise(KoreanGrammarReasonCode.PHASE31_HASH_DRIFT)


def _with_content_hash(payload: dict[str, object]) -> dict[str, object]:
    result = dict(payload)
    result["content_hash"] = korean_grammar_canonical_json_sha256(result)
    return result


def _phase31_binding_from_snapshot(
    snapshot: object,
) -> tuple[Phase31GrammarRootBinding, tuple[KoreanConcept, ...]]:
    source_kind = getattr(snapshot, "source_kind", KOREAN_GRAMMAR_SOURCE_KIND)
    if source_kind != KOREAN_GRAMMAR_SOURCE_KIND:
        _raise(KoreanGrammarReasonCode.PHASE31_NOT_ACTIVE)

    registry = getattr(snapshot, "concept_registry", None)
    concepts = tuple(getattr(registry, "concepts", ()))
    if not concepts:
        _raise(KoreanGrammarReasonCode.PHASE31_HASH_DRIFT)
    imported_concepts = tuple(
        KoreanConcept.model_validate(concept.model_dump(mode="python"))
        if isinstance(concept, BaseModel)
        else KoreanConcept.model_validate(concept)
        for concept in concepts
    )
    payload = _with_content_hash(
        {
            "source_kind": KOREAN_GRAMMAR_SOURCE_KIND,
            "bundle_sha256": _sha256_or_fail(getattr(snapshot, "bundle_sha256", None)),
            "receipt_sha256": _sha256_or_fail(getattr(snapshot, "receipt_sha256", None)),
            "snapshot_manifest_sha256": _sha256_or_fail(
                getattr(snapshot, "snapshot_manifest_sha256", None)
            ),
            "snapshot_root_sha256": _sha256_or_fail(
                getattr(snapshot, "snapshot_root_sha256", None)
            ),
            "concept_registry_member_sha256": _concept_registry_member_sha256(snapshot),
            "imported_concept_ids": [concept.id for concept in imported_concepts],
        }
    )
    return Phase31GrammarRootBinding(**payload), imported_concepts


def _ensure_ordered_sequences(
    entries: tuple[KoreanGrammarBootstrapEntry | KoreanGrammarEntry, ...],
) -> None:
    sequences = tuple(entry.sequence for entry in entries)
    if sequences != tuple(sorted(sequences)) or len(sequences) != len(set(sequences)):
        _raise(KoreanGrammarReasonCode.FORWARD_DEPENDENCY)


def _overlay_concepts(
    *,
    imported_concepts: tuple[KoreanConcept, ...],
    lexical_bootstrap: tuple[KoreanGrammarBootstrapEntry, ...],
    grammar_entries: tuple[KoreanGrammarEntry, ...],
) -> tuple[KoreanConcept, ...]:
    imported_ids = {concept.id for concept in imported_concepts}
    overlay_ids = [
        *(entry.target_concept_id for entry in lexical_bootstrap),
        *(entry.target_concept_id for entry in grammar_entries),
    ]
    if len(overlay_ids) != len(set(overlay_ids)) or imported_ids & set(overlay_ids):
        _raise(KoreanGrammarReasonCode.CONCEPT_COLLISION)

    base_sequence = max(concept.sequence for concept in imported_concepts)
    concepts: list[KoreanConcept] = []
    for offset, entry in enumerate(lexical_bootstrap, start=1):
        concepts.append(
            KoreanConcept(
                id=entry.target_concept_id,
                domain="lexicon",
                prerequisite_ids=entry.prerequisite_concept_ids,
                sequence=base_sequence + offset,
            )
        )
    for offset, entry in enumerate(grammar_entries, start=len(lexical_bootstrap) + 1):
        if entry.category_id not in KOREAN_GRAMMAR_CATEGORIES:
            _raise(KoreanGrammarReasonCode.BROAD_TARGET_CATEGORY)
        concepts.append(
            KoreanConcept(
                id=entry.target_concept_id,
                domain="grammar",
                prerequisite_ids=entry.evidence.prerequisite_concept_ids,
                sequence=base_sequence + offset,
            )
        )
    return tuple(concepts)


def _validate_graph_closure(
    *,
    imported_concepts: tuple[KoreanConcept, ...],
    overlay_concepts: tuple[KoreanConcept, ...],
) -> None:
    concepts = (*imported_concepts, *overlay_concepts)
    concept_by_id = {concept.id: concept for concept in concepts}
    for concept in overlay_concepts:
        for predecessor in concept.prerequisite_ids:
            if predecessor not in concept_by_id:
                if predecessor.startswith("grammar:"):
                    _raise(KoreanGrammarReasonCode.FORWARD_DEPENDENCY)
                _raise(KoreanGrammarReasonCode.UNKNOWN_CONCEPT)

    graph = {concept.id: set(concept.prerequisite_ids) for concept in concepts}
    try:
        tuple(TopologicalSorter(graph).static_order())
    except CycleError as exc:
        raise KoreanGrammarError(KoreanGrammarReasonCode.CONCEPT_CYCLE) from exc

    for concept in overlay_concepts:
        for predecessor in concept.prerequisite_ids:
            if concept_by_id[predecessor].sequence >= concept.sequence:
                _raise(KoreanGrammarReasonCode.FORWARD_DEPENDENCY)

    ancestor_cache: dict[str, set[str]] = {}

    def ancestors(concept_id: str) -> set[str]:
        if concept_id in ancestor_cache:
            return ancestor_cache[concept_id]
        result: set[str] = set()
        for predecessor in graph[concept_id]:
            result.add(predecessor)
            result.update(ancestors(predecessor))
        ancestor_cache[concept_id] = result
        return result

    for concept in overlay_concepts:
        if set(concept.prerequisite_ids) != ancestors(concept.id):
            _raise(KoreanGrammarReasonCode.INCOMPLETE_CLOSURE)


def _strict_result(bundle: KoreanGrammarBundle) -> KoreanGrammarValidationResult:
    imported_ids = tuple(concept.id for concept in bundle.imported_concepts)
    known_order = list(imported_ids)
    known = set(imported_ids)
    all_declared_ids = {
        *(concept.id for concept in bundle.imported_concepts),
        *(concept.id for concept in bundle.overlay_concepts),
    }
    admitted_bootstrap: list[str] = []
    admitted_grammar: list[str] = []

    for entry in bundle.lexical_bootstrap:
        if not set(entry.prerequisite_concept_ids) <= known:
            _raise(KoreanGrammarReasonCode.UNKNOWN_PREREQUISITE)
        recomputed_unknown = tuple(
            concept_id for concept_id in entry.observed_concept_ids if concept_id not in known
        )
        if recomputed_unknown != (entry.target_concept_id,):
            _raise(KoreanGrammarReasonCode.EXACTLY_ONE_UNKNOWN_REQUIRED)
        known.add(entry.target_concept_id)
        known_order.append(entry.target_concept_id)
        admitted_bootstrap.append(entry.target_concept_id)

    for entry in bundle.grammar_entries:
        evidence = entry.evidence
        target_id = evidence.target_concept_id
        if entry.category_id not in KOREAN_GRAMMAR_CATEGORIES:
            _raise(KoreanGrammarReasonCode.BROAD_TARGET_CATEGORY)
        if evidence.policy != "strict":
            _raise(KoreanGrammarReasonCode.STRICT_POLICY_REQUIRED)
        if target_id not in evidence.observed_concept_ids:
            _raise(KoreanGrammarReasonCode.TARGET_NOT_OBSERVED)
        if target_id in known:
            _raise(KoreanGrammarReasonCode.REPEATED_TARGET)
        missing_prerequisites = set(evidence.prerequisite_concept_ids) - all_declared_ids
        if missing_prerequisites:
            _raise(KoreanGrammarReasonCode.UNKNOWN_PREREQUISITE)
        if not set(evidence.prerequisite_concept_ids) <= known:
            _raise(KoreanGrammarReasonCode.FORWARD_DEPENDENCY)
        recomputed_unknown = tuple(
            concept_id for concept_id in evidence.observed_concept_ids if concept_id not in known
        )
        if recomputed_unknown != (target_id,):
            _raise(KoreanGrammarReasonCode.EXACTLY_ONE_UNKNOWN_REQUIRED)
        if tuple(evidence.unknown_concept_ids) != recomputed_unknown:
            _raise(KoreanGrammarReasonCode.SERIALIZED_UNKNOWN_MISMATCH)
        known.add(target_id)
        known_order.append(target_id)
        admitted_grammar.append(target_id)

    return KoreanGrammarValidationResult(
        ready_state="learner_ready",
        imported_known_concept_ids=imported_ids,
        admitted_bootstrap_concept_ids=tuple(admitted_bootstrap),
        admitted_grammar_concept_ids=tuple(admitted_grammar),
        known_concept_ids=tuple(known_order),
        blocked_reason_codes=(),
    )


def _production_blockers(bundle: KoreanGrammarBundle) -> tuple[str, ...]:
    reasons: list[str] = []
    for entry in bundle.lexical_bootstrap:
        if entry.source_binding.synthetic:
            reasons.append("synthetic_source")
        if not entry.source_binding.source_backed:
            reasons.append("missing_source")
        if not entry.source_binding.license_decision.startswith("approved"):
            reasons.append("missing_license")
    for entry in bundle.grammar_entries:
        if entry.ready_state != "learner_ready":
            reasons.append("entry_not_learner_ready")
        if entry.source_binding.synthetic:
            reasons.append("synthetic_source")
        if not entry.source_binding.license_decision.startswith("approved"):
            reasons.append("missing_license")
        if entry.review_binding.consensus_status != "ai_review_passed":
            reasons.append("missing_review")
        media_ready = (
            entry.word_media_binding.integrity_status == "passed"
            and entry.sentence_media_binding.integrity_status == "passed"
            and entry.word_media_binding.acoustic_review_status
            in {"ai_acoustic_review_passed", "automated_integrity_passed"}
            and entry.sentence_media_binding.acoustic_review_status
            in {"ai_acoustic_review_passed", "automated_integrity_passed"}
        )
        if not media_ready:
            reasons.append("missing_media")
    return tuple(sorted(set(reasons)))


def validate_korean_grammar_strict_graph(
    bundle: KoreanGrammarBundle,
) -> KoreanGrammarValidationResult:
    """Recompute ordered bootstrap and strict grammar unknowns from known state."""

    strict = _strict_result(bundle)
    blockers = _production_blockers(bundle)
    if not blockers:
        return strict
    return strict.model_copy(
        update={"ready_state": "blocked", "blocked_reason_codes": blockers}
    )


def validate_korean_grammar_production_readiness(
    bundle: KoreanGrammarBundle,
) -> KoreanGrammarValidationResult:
    """Return fail-closed production readiness after deterministic graph validation."""

    return validate_korean_grammar_strict_graph(bundle)


class KoreanGrammarBundleBuilder:
    """Build one grammar bundle from a single resolved active Phase 31 snapshot."""

    def __init__(
        self,
        *,
        active_snapshot_resolver: Callable[[], object] = resolve_active_korean_foundation_snapshot,
    ) -> None:
        self._active_snapshot_resolver = active_snapshot_resolver

    def build_bundle(
        self,
        *,
        lexical_bootstrap: tuple[KoreanGrammarBootstrapEntry, ...],
        grammar_entries: tuple[KoreanGrammarEntry, ...],
    ) -> KoreanGrammarBundle:
        snapshot = self._active_snapshot_resolver()
        phase31_binding, imported_concepts = _phase31_binding_from_snapshot(snapshot)
        _ensure_ordered_sequences(lexical_bootstrap)
        _ensure_ordered_sequences(grammar_entries)
        overlay_concepts = _overlay_concepts(
            imported_concepts=imported_concepts,
            lexical_bootstrap=lexical_bootstrap,
            grammar_entries=grammar_entries,
        )
        _validate_graph_closure(
            imported_concepts=imported_concepts,
            overlay_concepts=overlay_concepts,
        )
        member_hashes = build_member_hashes(
            phase31_binding=phase31_binding,
            imported_concepts=imported_concepts,
            overlay_concepts=overlay_concepts,
            lexical_bootstrap=lexical_bootstrap,
            grammar_entries=grammar_entries,
        )
        payload = {
            "schema_version": "korean-grammar-bundle-v1",
            "language": "ko",
            "phase31_binding": phase31_binding,
            "imported_concepts": imported_concepts,
            "overlay_concepts": overlay_concepts,
            "lexical_bootstrap": lexical_bootstrap,
            "grammar_entries": grammar_entries,
            "member_hashes": member_hashes,
        }
        bundle = KoreanGrammarBundle(
            **payload,
            bundle_sha256=build_bundle_sha256(
                {
                    **payload,
                    "phase31_binding": phase31_binding.model_dump(mode="json"),
                    "imported_concepts": [
                        concept.model_dump(mode="json") for concept in imported_concepts
                    ],
                    "overlay_concepts": [
                        concept.model_dump(mode="json") for concept in overlay_concepts
                    ],
                    "lexical_bootstrap": [
                        entry.model_dump(mode="json", by_alias=True)
                        for entry in lexical_bootstrap
                    ],
                    "grammar_entries": [
                        entry.model_dump(mode="json", by_alias=True)
                        for entry in grammar_entries
                    ],
                }
            ),
        )
        _strict_result(bundle)
        return bundle


__all__ = [
    "KoreanGrammarBundleBuilder",
    "KoreanGrammarError",
    "KoreanGrammarReasonCode",
    "KoreanGrammarValidationResult",
    "validate_korean_grammar_production_readiness",
    "validate_korean_grammar_strict_graph",
]
