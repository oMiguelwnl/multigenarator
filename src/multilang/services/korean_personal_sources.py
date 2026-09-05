"""Fail-closed Korean personal-source resolution and decisions."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal, Protocol

from pydantic import ValidationError

from multilang.domain.korean import KoreanTextError, canonical_json_sha256, canonicalize_korean
from multilang.domain.personal_sources import (
    KoreanPersonalSourceIdentitySelection,
    KoreanPersonalSourceResolutionFailure,
    KoreanPersonalSourceResolutionOutcome,
    KoreanPersonalSourceReviewReason,
    PersonalSourceAdaptiveEvidence,
    PersonalSourceDecisionCommand,
    PersonalSourceDecisionReason,
    PersonalSourcePreparedItem,
    PersonalSourcePreparationStatus,
    PersonalSourcePrerequisiteDecision,
    PersonalSourcePrerequisiteProposal,
    PersonalSourceRow,
)


KOREAN_PERSONAL_PREREQUISITE_POLICY_VERSION = "korean-personal-adaptive-prereq-v1"
_KOREAN_PERSONAL_PREREQUISITE_ASSESSOR = "korean-personal-prerequisite-assessor-v1"


class KoreanPersonalSourceResolver(Protocol):
    """Injected Phase 30-style resolver/source selector."""

    def resolve(self, submitted_form: str) -> object:
        """Return a source-backed selection or controlled failure."""


class KoreanPersonalSourceService:
    """Resolve ordered Korean custom rows without heuristic fallback."""

    def __init__(self, *, resolver: KoreanPersonalSourceResolver) -> None:
        self._resolver = resolver

    def resolve_rows(
        self,
        rows: Iterable[PersonalSourceRow],
    ) -> tuple[KoreanPersonalSourceResolutionOutcome, ...]:
        outcomes: list[KoreanPersonalSourceResolutionOutcome] = []
        for row in sorted(tuple(rows), key=lambda item: item.input_position):
            if row.duplicate_of_position is not None:
                outcomes.append(
                    self._needs_review(row, reason_code="duplicate_of_existing", status="duplicate")
                )
                continue
            if not self._valid_korean_surface(row.display_form):
                outcomes.append(self._needs_review(row, reason_code="invalid_text"))
                continue
            try:
                resolved = self._resolver.resolve(row.display_form)
            except Exception:  # pragma: no cover - defensive content-free boundary
                outcomes.append(self._needs_review(row, reason_code="resolver_error"))
                continue
            outcomes.append(self._outcome_from_resolver(row, resolved))
        return tuple(outcomes)

    def assess_prerequisites(
        self,
        outcome: KoreanPersonalSourceResolutionOutcome,
        *,
        observed_concept_ids: Iterable[str],
        prerequisite_concept_ids: Iterable[str],
        known_concept_ids: Iterable[str],
        threshold: int = 2,
        policy_version: str = KOREAN_PERSONAL_PREREQUISITE_POLICY_VERSION,
    ) -> PersonalSourcePrerequisiteProposal:
        observed = tuple(observed_concept_ids)
        prerequisites = tuple(prerequisite_concept_ids)
        known = tuple(known_concept_ids)
        known_set = set(known)
        unknown = tuple(concept_id for concept_id in prerequisites if concept_id not in known_set)
        policy_hash = _prerequisite_policy_hash(
            policy_version=policy_version,
            threshold=threshold,
        )
        if outcome.resolution_status != "resolved":
            reason_codes = ("unresolved_identity",)
            status = "needs_review"
            available_decisions = ("needs_review",)
        elif len(unknown) > threshold:
            reason_codes = ("excessive_prerequisites",)
            status = "requires_decision"
            available_decisions = ("bridge", "defer")
        else:
            reason_codes = ("within_threshold",)
            status = "ready"
            available_decisions = ()

        evidence = PersonalSourceAdaptiveEvidence(
            observed_concept_ids=observed,
            prerequisite_concept_ids=prerequisites,
            known_concept_ids=known,
            unknown_prerequisite_concept_ids=unknown,
            novelty_count=len(unknown),
            threshold=threshold,
            policy_version=policy_version,
            policy_hash=policy_hash,
            reason_codes=reason_codes,
        )
        proposal_id = _proposal_id(
            outcome=outcome,
            evidence=evidence,
            status=status,
            available_decisions=available_decisions,
        )
        return PersonalSourcePrerequisiteProposal(
            proposal_id=proposal_id,
            input_position=outcome.row.input_position,
            row_item_key=outcome.row.stable_item_key,
            status=status,
            evidence=evidence,
            available_decisions=available_decisions,
        )

    def record_prerequisite_decision(
        self,
        proposal: PersonalSourcePrerequisiteProposal,
        command: PersonalSourceDecisionCommand,
    ) -> PersonalSourcePrerequisiteDecision:
        if (
            command.input_position != proposal.input_position
            or command.row_item_key != proposal.row_item_key
        ):
            return _needs_review_decision(proposal, reason_code="dependency_drift")
        if command.expected_policy_hash != proposal.evidence.policy_hash:
            return _needs_review_decision(proposal, reason_code="policy_drift")
        if command.expected_prerequisite_concept_ids != proposal.evidence.prerequisite_concept_ids:
            return _needs_review_decision(proposal, reason_code="dependency_drift")
        if command.expected_proposal_id != proposal.proposal_id:
            return _needs_review_decision(proposal, reason_code="dependency_drift")
        if proposal.status == "needs_review":
            return _needs_review_decision(proposal, reason_code="unresolved_identity")
        if proposal.status == "ready":
            return _needs_review_decision(proposal, reason_code="no_decision_required")
        if command.decision == "defer":
            return _decision_from_command(proposal, command, reason_code="operator_defer")

        reviewed = set(command.reviewed_prerequisite_ids)
        required = set(proposal.evidence.unknown_prerequisite_concept_ids)
        if reviewed != required:
            return _needs_review_decision(proposal, reason_code="invalid_bridge")
        return _decision_from_command(proposal, command, reason_code="operator_bridge")

    def project_preparation_order(
        self,
        outcomes: Iterable[KoreanPersonalSourceResolutionOutcome],
        *,
        decisions: Iterable[PersonalSourcePrerequisiteDecision],
    ) -> tuple[PersonalSourcePreparedItem, ...]:
        decision_by_row = {
            (decision.input_position, decision.row_item_key): decision
            for decision in decisions
        }
        prepared: list[PersonalSourcePreparedItem] = []
        for outcome in sorted(tuple(outcomes), key=lambda item: item.row.input_position):
            row = outcome.row
            decision = decision_by_row.get((row.input_position, row.stable_item_key))
            if decision is not None and decision.decision == "bridge":
                for reference_id in decision.reviewed_prerequisite_ids:
                    prepared.append(
                        PersonalSourcePreparedItem(
                            kind="bridge_reference",
                            input_position=row.input_position,
                            row_item_key=row.stable_item_key,
                            preparation_status="bridge_reference",
                            bridge_reference_id=reference_id,
                        )
                    )
            prepared.append(
                PersonalSourcePreparedItem(
                    kind="user_row",
                    input_position=row.input_position,
                    row_item_key=row.stable_item_key,
                    preparation_status=_preparation_status(outcome, decision),
                )
            )
        return tuple(prepared)

    def _outcome_from_resolver(
        self,
        row: PersonalSourceRow,
        resolved: object,
    ) -> KoreanPersonalSourceResolutionOutcome:
        failure = self._resolution_failure(resolved)
        if failure is not None:
            return self._needs_review(row, reason_code=failure.reason_code)

        if self._has_non_consensus_marker(resolved):
            return self._needs_review(row, reason_code="non_consensus")

        try:
            selection = KoreanPersonalSourceIdentitySelection.model_validate(resolved)
        except ValidationError:
            return self._needs_review(row, reason_code="malformed_identity")

        if not selection.top_two_consensus or not selection.source_consensus:
            return self._needs_review(row, reason_code="non_consensus")
        if selection.lexical_identity.analyzer_fingerprint != selection.analyzer_fingerprint:
            return self._needs_review(row, reason_code="fingerprint_drift")
        if selection.lexical_identity.canonical_nfc != row.display_form:
            return self._needs_review(row, reason_code="malformed_identity")

        return KoreanPersonalSourceResolutionOutcome(
            row=row,
            resolution_status="resolved",
            lexical_identity=selection.lexical_identity,
            identity_evidence=selection.identity_evidence(),
        )

    def _resolution_failure(
        self,
        resolved: object,
    ) -> KoreanPersonalSourceResolutionFailure | None:
        if isinstance(resolved, KoreanPersonalSourceResolutionFailure):
            return resolved
        if isinstance(resolved, dict) and resolved.get("status") in {
            "ambiguous",
            "invalid",
            "oov",
            "unavailable",
        }:
            try:
                return KoreanPersonalSourceResolutionFailure.model_validate(resolved)
            except ValidationError:
                return KoreanPersonalSourceResolutionFailure(
                    status="invalid",
                    reason_code="malformed_identity",
                )
        return None

    def _has_non_consensus_marker(self, resolved: object) -> bool:
        if isinstance(resolved, dict):
            return (
                resolved.get("top_two_consensus") is False
                or resolved.get("source_consensus") is False
            )
        top_two = getattr(resolved, "top_two_consensus", None)
        source = getattr(resolved, "source_consensus", None)
        return top_two is False or source is False

    def _needs_review(
        self,
        row: PersonalSourceRow,
        *,
        reason_code: KoreanPersonalSourceReviewReason,
        status: Literal["needs_review", "duplicate"] = "needs_review",
    ) -> KoreanPersonalSourceResolutionOutcome:
        return KoreanPersonalSourceResolutionOutcome(
            row=row,
            resolution_status=status,
            review_reason_code=reason_code,
        )

    def _valid_korean_surface(self, value: str) -> bool:
        try:
            canonical = canonicalize_korean(value)
        except KoreanTextError:
            return False
        return canonical == value and any(_is_hangul(character) for character in value)


def _is_hangul(character: str) -> bool:
    code_point = ord(character)
    return (
        0xAC00 <= code_point <= 0xD7A3
        or 0x1100 <= code_point <= 0x11FF
        or 0xA960 <= code_point <= 0xA97F
        or 0xD7B0 <= code_point <= 0xD7FF
    )


def _prerequisite_policy_hash(*, policy_version: str, threshold: int) -> str:
    return canonical_json_sha256(
        {
            "assessor": _KOREAN_PERSONAL_PREREQUISITE_ASSESSOR,
            "policy_version": policy_version,
            "threshold": threshold,
        }
    )


def _proposal_id(
    *,
    outcome: KoreanPersonalSourceResolutionOutcome,
    evidence: PersonalSourceAdaptiveEvidence,
    status: str,
    available_decisions: tuple[str, ...],
) -> str:
    return canonical_json_sha256(
        {
            "kind": "personal-source-prerequisite-proposal-v1",
            "input_position": outcome.row.input_position,
            "row_item_key": outcome.row.stable_item_key,
            "resolution_status": outcome.resolution_status,
            "status": status,
            "available_decisions": available_decisions,
            "evidence": evidence.model_dump(mode="json"),
        }
    )


def _decision_id(
    *,
    proposal: PersonalSourcePrerequisiteProposal,
    decision: str,
    reviewed_prerequisite_ids: tuple[str, ...],
    reason_code: str,
) -> str:
    return canonical_json_sha256(
        {
            "kind": "personal-source-prerequisite-decision-v1",
            "proposal_id": proposal.proposal_id,
            "input_position": proposal.input_position,
            "row_item_key": proposal.row_item_key,
            "policy_hash": proposal.evidence.policy_hash,
            "prerequisite_concept_ids": proposal.evidence.prerequisite_concept_ids,
            "decision": decision,
            "reviewed_prerequisite_ids": reviewed_prerequisite_ids,
            "reason_code": reason_code,
        }
    )


def _needs_review_decision(
    proposal: PersonalSourcePrerequisiteProposal,
    *,
    reason_code: PersonalSourceDecisionReason,
) -> PersonalSourcePrerequisiteDecision:
    return PersonalSourcePrerequisiteDecision(
        decision_id=_decision_id(
            proposal=proposal,
            decision="needs_review",
            reviewed_prerequisite_ids=(),
            reason_code=reason_code,
        ),
        input_position=proposal.input_position,
        row_item_key=proposal.row_item_key,
        proposal_id=proposal.proposal_id,
        policy_hash=proposal.evidence.policy_hash,
        prerequisite_concept_ids=proposal.evidence.prerequisite_concept_ids,
        decision="needs_review",
        reviewed_prerequisite_ids=(),
        reason_code=reason_code,
        blocks_current_preparation=True,
    )


def _decision_from_command(
    proposal: PersonalSourcePrerequisiteProposal,
    command: PersonalSourceDecisionCommand,
    *,
    reason_code: PersonalSourceDecisionReason,
) -> PersonalSourcePrerequisiteDecision:
    reviewed_prerequisite_ids = command.reviewed_prerequisite_ids
    return PersonalSourcePrerequisiteDecision(
        decision_id=_decision_id(
            proposal=proposal,
            decision=command.decision,
            reviewed_prerequisite_ids=reviewed_prerequisite_ids,
            reason_code=reason_code,
        ),
        input_position=proposal.input_position,
        row_item_key=proposal.row_item_key,
        proposal_id=proposal.proposal_id,
        policy_hash=proposal.evidence.policy_hash,
        prerequisite_concept_ids=proposal.evidence.prerequisite_concept_ids,
        decision=command.decision,
        reviewed_prerequisite_ids=reviewed_prerequisite_ids,
        reason_code=reason_code,
        blocks_current_preparation=command.decision != "bridge",
    )


def _preparation_status(
    outcome: KoreanPersonalSourceResolutionOutcome,
    decision: PersonalSourcePrerequisiteDecision | None,
) -> PersonalSourcePreparationStatus:
    if outcome.resolution_status == "duplicate":
        return "duplicate"
    if outcome.resolution_status == "needs_review":
        return "needs_review"
    if decision is None:
        return "ready"
    if decision.decision == "bridge":
        return "ready"
    if decision.decision == "defer":
        return "deferred"
    return "needs_review"


__all__ = [
    "KOREAN_PERSONAL_PREREQUISITE_POLICY_VERSION",
    "KoreanPersonalSourceResolver",
    "KoreanPersonalSourceService",
]
