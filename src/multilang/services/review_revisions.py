"""Pure append-only field revision transition service.

This module intentionally keeps provider calls, SQL, file publication, and history
deletion out of scope. It models the atomic command semantics that later storage
plans can persist.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Final

from pydantic import ValidationError

from multilang.domain.review import (
    AILinguisticReviewEvidence,
    AudioPublicationReservation,
    AudioPublicationStatus,
    AudioPublicationTransition,
    AudioReviewEvidence,
    FieldDependencyBinding,
    FieldPointer,
    FieldRevision,
    GeneratorMetadata,
    HashBinding,
    PrivateDisplaySelector,
    ReviewAccessAction,
    ReviewAccessEvent,
    ReviewDecision,
    ReviewField,
    ReviewInspectSelector,
    ReviewListSelector,
    ReviewStatus,
    ReviewTransitionAction,
    ReviewTransitionEvent,
    RevisionCreationEvidence,
    canonical_command_sha256,
    derive_audio_final_path,
)


_SENTENCE_DEPENDENT_FIELDS: Final = (ReviewField.TRANSLATION, ReviewField.SENTENCE_AUDIO)


class ReviewRevisionError(Exception):
    """Base class for review revision service failures."""


class ReviewCommandConflict(ReviewRevisionError):
    """The same stable request identity was reused for a different command."""


class ReviewCASConflict(ReviewRevisionError):
    """A compare-and-set expectation did not match current pointer/reservation state."""


class ReviewValidationError(ReviewRevisionError):
    """A command supplied evidence or identities that cannot be accepted."""


@dataclass(frozen=True)
class ReviewOperationResult:
    event: ReviewTransitionEvent
    revision: FieldRevision | None = None
    pointer: FieldPointer | None = None
    decision: ReviewDecision | None = None
    stale_decisions: tuple[ReviewDecision, ...] = ()
    replayed: bool = False


@dataclass(frozen=True)
class ReviewAccessResult:
    event: ReviewAccessEvent
    rows: tuple[dict[str, object], ...] = ()
    metadata: dict[str, object] | None = None
    value: object | None = None
    released_after_event_id: str | None = None
    replayed: bool = False


@dataclass(frozen=True)
class AudioPublicationResult:
    reservation: AudioPublicationReservation
    transition: AudioPublicationTransition
    pointer: FieldPointer | None = None
    replayed: bool = False


@dataclass(frozen=True)
class _PublicationState:
    reservation: AudioPublicationReservation
    status: AudioPublicationStatus
    artifact_sha256: str | None = None


class ReviewRevisionService:
    """In-memory append-only model of field revision review transitions."""

    def __init__(self) -> None:
        self.revisions: dict[str, FieldRevision] = {}
        self.pointers: dict[tuple[str, str, ReviewField], FieldPointer] = {}
        self.decisions: list[ReviewDecision] = []
        self.transition_events: list[ReviewTransitionEvent] = []
        self.access_events: list[ReviewAccessEvent] = []
        self.audio_transitions: list[AudioPublicationTransition] = []
        self.provider_call_count = 0

        self._access_results: dict[tuple[str, str, ReviewAccessAction], tuple[str, ReviewAccessResult]] = {}
        self._command_results: dict[tuple[str, str, str], tuple[str, object]] = {}
        self._publication_states: dict[str, _PublicationState] = {}
        self._publication_revision_paths: dict[tuple[str, str, ReviewField, str], str] = {}
        self._publication_path_revisions: dict[str, tuple[str, str, ReviewField, str]] = {}
        self._clock_tick = 0
        self._lock = Lock()

    @property
    def committed_access_event_ids(self) -> tuple[str, ...]:
        return tuple(event.event_id for event in self.access_events)

    def latest_decision(self, revision_id: str) -> ReviewDecision | None:
        for decision in reversed(self.decisions):
            if decision.revision_id == revision_id:
                return decision
        return None

    def create_candidate(
        self,
        *,
        actor_id: str,
        request_id: str,
        action: str | ReviewTransitionAction,
        job_id: str,
        item_id: str,
        field: ReviewField,
        payload: dict[str, Any],
        source_hashes: tuple[HashBinding, ...],
        dependency_hashes: tuple[FieldDependencyBinding, ...] = (),
        expected_base_revision_id: str | None,
        expected_pointer_version: int,
    ) -> ReviewOperationResult:
        field = ReviewField(field)
        action_enum = self._candidate_action(action)
        payload_hash = canonical_command_sha256(payload)
        command_sha256 = canonical_command_sha256(
            {
                "action": action_enum.value,
                "job_id": job_id,
                "item_id": item_id,
                "field": field.value,
                "payload_hash": payload_hash,
                "source_hashes": source_hashes,
                "dependency_hashes": dependency_hashes,
                "expected_base_revision_id": expected_base_revision_id,
                "expected_pointer_version": expected_pointer_version,
            }
        )

        with self._lock:
            replay = self._command_replay(actor_id, request_id, action_enum.value, command_sha256)
            if replay is not None:
                return replay

            pointer = self._pointer(job_id, item_id, field)
            self._require_pointer(pointer, expected_pointer_version, expected_base_revision_id)
            revision_no = self._next_revision_no(job_id, item_id, field)
            revision_id = self._safe_id("rev", job_id, item_id, field.value, revision_no)
            now = self._now()
            revision = FieldRevision(
                job_id=job_id,
                item_id=item_id,
                field=field,
                revision_id=revision_id,
                revision_no=revision_no,
                content_hash=payload_hash,
                payload=payload,
                source_hashes=source_hashes,
                dependency_hashes=dependency_hashes,
                generator=GeneratorMetadata(
                    generator_id=actor_id,
                    generator_version="1",
                    route_id="offline-review-revisions",
                    request_sha256=command_sha256,
                ),
                creation_evidence=RevisionCreationEvidence(
                    actor_type="local_user" if action_enum is ReviewTransitionAction.EDIT_TO_NEW_CANDIDATE else "generator",
                    actor_id=actor_id,
                    source_kind="edited" if action_enum is ReviewTransitionAction.EDIT_TO_NEW_CANDIDATE else "generated",
                    created_at=now,
                    evidence_sha256=command_sha256,
                ),
                initial_status=ReviewStatus.REVIEW_REQUIRED,
                created_at=now,
            )
            updated_pointer = FieldPointer(
                job_id=job_id,
                item_id=item_id,
                field=field,
                candidate_revision_id=revision.revision_id,
                candidate_content_hash=revision.content_hash,
                approved_revision_id=pointer.approved_revision_id,
                approved_content_hash=pointer.approved_content_hash,
                version=pointer.version + 1,
            )
            event = self._transition_event(
                action=action_enum,
                actor_id=actor_id,
                request_id=request_id,
                command_sha256=command_sha256,
                job_id=job_id,
                item_id=item_id,
                field=field,
                before_revision_id=pointer.candidate_revision_id,
                before_content_hash=pointer.candidate_content_hash,
                after_revision_id=revision.revision_id,
                after_content_hash=revision.content_hash,
                before_pointer_version=pointer.version,
                after_pointer_version=updated_pointer.version,
                reason_code="none",
            )
            self.revisions[revision.revision_id] = revision
            self.pointers[self._pointer_key(job_id, item_id, field)] = updated_pointer
            self.transition_events.append(event)
            result = ReviewOperationResult(event=event, revision=revision, pointer=updated_pointer)
            self._store_command_result(actor_id, request_id, action_enum.value, command_sha256, result)
            return result

    def approve_revision(
        self,
        *,
        actor_id: str,
        request_id: str,
        job_id: str,
        item_id: str,
        field: ReviewField,
        revision_id: str,
        revision_no: int,
        content_hash: str,
        expected_pointer_version: int,
        evidence: AILinguisticReviewEvidence | AudioReviewEvidence,
    ) -> ReviewOperationResult:
        field = ReviewField(field)
        command_sha256 = canonical_command_sha256(
            {
                "action": ReviewTransitionAction.APPROVE.value,
                "job_id": job_id,
                "item_id": item_id,
                "field": field.value,
                "revision_id": revision_id,
                "revision_no": revision_no,
                "content_hash": content_hash,
                "expected_pointer_version": expected_pointer_version,
                "evidence": evidence,
            }
        )
        with self._lock:
            replay = self._command_replay(actor_id, request_id, ReviewTransitionAction.APPROVE.value, command_sha256)
            if replay is not None:
                return replay

            pointer = self._pointer(job_id, item_id, field)
            self._require_pointer(pointer, expected_pointer_version, revision_id)
            revision = self._exact_revision(job_id, item_id, field, revision_id, revision_no, content_hash)
            if getattr(evidence, "source_kind", "production") != "production":
                raise ReviewValidationError("synthetic evidence cannot be accepted")
            now = self._now()
            try:
                decision = ReviewDecision(
                    decision_id=self._safe_id("decision", command_sha256, revision_id),
                    job_id=job_id,
                    item_id=item_id,
                    field=field,
                    revision_id=revision.revision_id,
                    revision_no=revision.revision_no,
                    content_hash=revision.content_hash,
                    status=ReviewStatus.ACCEPTED,
                    actor_type="ai_model" if isinstance(evidence, AILinguisticReviewEvidence) else "system",
                    actor_id=actor_id,
                    policy_sha256=evidence.policy_sha256,
                    evidence=evidence,
                    reason_code="none",
                    created_at=now,
                )
            except (TypeError, ValueError, ValidationError) as exc:
                raise ReviewValidationError(str(exc)) from exc

            previous_approved_hash = pointer.approved_content_hash
            updated_pointer = FieldPointer(
                job_id=job_id,
                item_id=item_id,
                field=field,
                candidate_revision_id=pointer.candidate_revision_id,
                candidate_content_hash=pointer.candidate_content_hash,
                approved_revision_id=revision.revision_id,
                approved_content_hash=revision.content_hash,
                version=pointer.version + 1,
            )
            event = self._transition_event(
                action=ReviewTransitionAction.APPROVE,
                actor_id=actor_id,
                request_id=request_id,
                command_sha256=command_sha256,
                job_id=job_id,
                item_id=item_id,
                field=field,
                before_revision_id=pointer.approved_revision_id,
                before_content_hash=pointer.approved_content_hash,
                after_revision_id=revision.revision_id,
                after_content_hash=revision.content_hash,
                before_pointer_version=pointer.version,
                after_pointer_version=updated_pointer.version,
                reason_code="none",
            )
            self.pointers[self._pointer_key(job_id, item_id, field)] = updated_pointer
            self.decisions.append(decision)
            self.transition_events.append(event)
            stale_decisions: tuple[ReviewDecision, ...] = ()
            if (
                field is ReviewField.SENTENCE
                and previous_approved_hash is not None
                and previous_approved_hash != revision.content_hash
            ):
                stale_decisions = self._stale_dependents_locked(
                    actor_id=actor_id,
                    request_id=request_id,
                    command_sha256=command_sha256,
                    job_id=job_id,
                    item_id=item_id,
                    source_field=ReviewField.SENTENCE,
                    source_content_hash=previous_approved_hash,
                    reason_code="source-sentence-changed",
                    allowed_fields=_SENTENCE_DEPENDENT_FIELDS,
                )
            result = ReviewOperationResult(
                event=event,
                revision=revision,
                pointer=updated_pointer,
                decision=decision,
                stale_decisions=stale_decisions,
            )
            self._store_command_result(actor_id, request_id, ReviewTransitionAction.APPROVE.value, command_sha256, result)
            return result

    def reject_revision(
        self,
        *,
        actor_id: str,
        request_id: str,
        job_id: str,
        item_id: str,
        field: ReviewField,
        revision_id: str,
        revision_no: int,
        content_hash: str,
        expected_pointer_version: int,
        reason_code: str,
    ) -> ReviewOperationResult:
        field = ReviewField(field)
        command_sha256 = canonical_command_sha256(
            {
                "action": ReviewTransitionAction.REJECT.value,
                "job_id": job_id,
                "item_id": item_id,
                "field": field.value,
                "revision_id": revision_id,
                "revision_no": revision_no,
                "content_hash": content_hash,
                "expected_pointer_version": expected_pointer_version,
                "reason_code": reason_code,
            }
        )
        with self._lock:
            replay = self._command_replay(actor_id, request_id, ReviewTransitionAction.REJECT.value, command_sha256)
            if replay is not None:
                return replay
            pointer = self._pointer(job_id, item_id, field)
            self._require_pointer(pointer, expected_pointer_version, revision_id)
            revision = self._exact_revision(job_id, item_id, field, revision_id, revision_no, content_hash)
            decision = ReviewDecision(
                decision_id=self._safe_id("decision", command_sha256, revision_id),
                job_id=job_id,
                item_id=item_id,
                field=field,
                revision_id=revision.revision_id,
                revision_no=revision.revision_no,
                content_hash=revision.content_hash,
                status=ReviewStatus.REJECTED,
                actor_type="local_user",
                actor_id=actor_id,
                policy_sha256="0" * 64,
                evidence=None,
                reason_code=reason_code,
                created_at=self._now(),
            )
            event = self._transition_event(
                action=ReviewTransitionAction.REJECT,
                actor_id=actor_id,
                request_id=request_id,
                command_sha256=command_sha256,
                job_id=job_id,
                item_id=item_id,
                field=field,
                before_revision_id=revision.revision_id,
                before_content_hash=revision.content_hash,
                after_revision_id=pointer.approved_revision_id,
                after_content_hash=pointer.approved_content_hash,
                before_pointer_version=pointer.version,
                after_pointer_version=pointer.version,
                reason_code=reason_code,
            )
            self.decisions.append(decision)
            self.transition_events.append(event)
            result = ReviewOperationResult(event=event, revision=revision, pointer=pointer, decision=decision)
            self._store_command_result(actor_id, request_id, ReviewTransitionAction.REJECT.value, command_sha256, result)
            return result

    def list_fields(
        self,
        *,
        actor_id: str,
        request_id: str,
        selector: ReviewListSelector,
    ) -> ReviewAccessResult:
        command_sha256 = canonical_command_sha256(
            {"action": ReviewAccessAction.LIST.value, "selector": selector}
        )
        with self._lock:
            replay = self._access_replay(actor_id, request_id, ReviewAccessAction.LIST, command_sha256)
            if replay is not None:
                return replay
            rows = tuple(
                row
                for row in self._list_rows(selector)
                if row["status"] in {status.value for status in selector.statuses}
            )
            result_hash = canonical_command_sha256(rows)
            event = self._access_event(
                actor_id=actor_id,
                request_id=request_id,
                action=ReviewAccessAction.LIST,
                command_sha256=command_sha256,
                result_hash=result_hash,
                result_count=len(rows),
            )
            self.access_events.append(event)
            result = ReviewAccessResult(event=event, rows=rows, released_after_event_id=event.event_id)
            self._store_access_result(actor_id, request_id, ReviewAccessAction.LIST, command_sha256, result)
            return result

    def inspect_field(
        self,
        *,
        actor_id: str,
        request_id: str,
        selector: ReviewInspectSelector,
    ) -> ReviewAccessResult:
        command_sha256 = canonical_command_sha256(
            {"action": ReviewAccessAction.INSPECT.value, "selector": selector}
        )
        with self._lock:
            replay = self._access_replay(actor_id, request_id, ReviewAccessAction.INSPECT, command_sha256)
            if replay is not None:
                return replay
            revision = self._revision_for_selector(selector)
            pointer = self._pointer(selector.job_id, selector.item_id, selector.field)
            if pointer.version != selector.pointer_version:
                raise ReviewCASConflict("pointer version mismatch")
            metadata: dict[str, object] = {
                "job_id": revision.job_id,
                "item_id": revision.item_id,
                "field": revision.field.value,
                "revision_id": revision.revision_id,
                "revision_no": revision.revision_no,
                "content_hash": revision.content_hash,
                "source_hashes": tuple(binding.model_dump(mode="json") for binding in revision.source_hashes),
                "dependency_hashes": tuple(binding.model_dump(mode="json") for binding in revision.dependency_hashes),
                "status": self._revision_status(revision).value,
                "pointer_version": pointer.version,
            }
            event = self._access_event(
                actor_id=actor_id,
                request_id=request_id,
                action=ReviewAccessAction.INSPECT,
                command_sha256=command_sha256,
                result_hash=canonical_command_sha256(metadata),
                result_count=1,
            )
            self.access_events.append(event)
            result = ReviewAccessResult(event=event, metadata=metadata, released_after_event_id=event.event_id)
            self._store_access_result(actor_id, request_id, ReviewAccessAction.INSPECT, command_sha256, result)
            return result

    def private_display_revision(
        self,
        *,
        actor_id: str,
        request_id: str,
        selector: PrivateDisplaySelector,
    ) -> ReviewAccessResult:
        command_sha256 = canonical_command_sha256(
            {"action": ReviewAccessAction.PRIVATE_DISPLAY.value, "selector": selector}
        )
        with self._lock:
            replay = self._access_replay(actor_id, request_id, ReviewAccessAction.PRIVATE_DISPLAY, command_sha256)
            if replay is not None:
                return replay
            revision = self._revision_for_selector(selector)
            pointer = self._pointer(selector.job_id, selector.item_id, selector.field)
            if pointer.version != selector.pointer_version:
                raise ReviewCASConflict("pointer version mismatch")
            event = self._access_event(
                actor_id=actor_id,
                request_id=request_id,
                action=ReviewAccessAction.PRIVATE_DISPLAY,
                command_sha256=command_sha256,
                result_hash=canonical_command_sha256(
                    {
                        "job_id": revision.job_id,
                        "item_id": revision.item_id,
                        "field": revision.field.value,
                        "revision_id": revision.revision_id,
                        "content_hash": revision.content_hash,
                    }
                ),
                result_count=1,
            )
            self.access_events.append(event)
            result = ReviewAccessResult(
                event=event,
                value=revision.payload,
                released_after_event_id=event.event_id,
            )
            self._store_access_result(actor_id, request_id, ReviewAccessAction.PRIVATE_DISPLAY, command_sha256, result)
            return result

    def record_bridge_decision(
        self,
        *,
        actor_id: str,
        request_id: str,
        job_id: str,
        item_id: str,
        proposal_id: str,
        base_revision_id: str,
        expected_base_revision_id: str,
        prerequisite_concept_ids: tuple[str, ...],
    ) -> ReviewOperationResult:
        if base_revision_id != expected_base_revision_id:
            raise ReviewCASConflict("expected base revision mismatch")
        return self._proposal_decision(
            actor_id=actor_id,
            request_id=request_id,
            job_id=job_id,
            item_id=item_id,
            action=ReviewTransitionAction.BRIDGE,
            proposal_id=proposal_id,
            base_revision_id=base_revision_id,
            reason_code="bridge-selected",
            extra={"prerequisite_concept_ids": prerequisite_concept_ids},
        )

    def record_defer_decision(
        self,
        *,
        actor_id: str,
        request_id: str,
        job_id: str,
        item_id: str,
        proposal_id: str,
        base_revision_id: str,
        expected_base_revision_id: str,
        reason_code: str,
    ) -> ReviewOperationResult:
        if base_revision_id != expected_base_revision_id:
            raise ReviewCASConflict("expected base revision mismatch")
        return self._proposal_decision(
            actor_id=actor_id,
            request_id=request_id,
            job_id=job_id,
            item_id=item_id,
            action=ReviewTransitionAction.DEFER,
            proposal_id=proposal_id,
            base_revision_id=base_revision_id,
            reason_code=reason_code,
            extra={},
        )

    def mark_declared_dependents_stale(
        self,
        *,
        actor_id: str,
        request_id: str,
        job_id: str,
        item_id: str,
        source_field: ReviewField,
        source_content_hash: str,
        reason_code: str,
    ) -> ReviewOperationResult:
        source_field = ReviewField(source_field)
        command_sha256 = canonical_command_sha256(
            {
                "action": ReviewTransitionAction.STALE_DEPENDENT.value,
                "job_id": job_id,
                "item_id": item_id,
                "source_field": source_field.value,
                "source_content_hash": source_content_hash,
                "reason_code": reason_code,
            }
        )
        with self._lock:
            replay = self._command_replay(actor_id, request_id, ReviewTransitionAction.STALE_DEPENDENT.value, command_sha256)
            if replay is not None:
                return replay
            stale_decisions = self._stale_dependents_locked(
                actor_id=actor_id,
                request_id=request_id,
                command_sha256=command_sha256,
                job_id=job_id,
                item_id=item_id,
                source_field=source_field,
                source_content_hash=source_content_hash,
                reason_code=reason_code,
                allowed_fields=None,
            )
            event = self._transition_event(
                action=ReviewTransitionAction.STALE_DEPENDENT,
                actor_id=actor_id,
                request_id=request_id,
                command_sha256=command_sha256,
                job_id=job_id,
                item_id=item_id,
                field=source_field,
                before_revision_id=None,
                before_content_hash=source_content_hash,
                after_revision_id=None,
                after_content_hash=None,
                before_pointer_version=0,
                after_pointer_version=0,
                reason_code=reason_code,
            )
            self.transition_events.append(event)
            result = ReviewOperationResult(event=event, stale_decisions=stale_decisions)
            self._store_command_result(actor_id, request_id, ReviewTransitionAction.STALE_DEPENDENT.value, command_sha256, result)
            return result

    def reserve_audio_publication(
        self,
        *,
        actor_id: str,
        request_id: str,
        job_id: str,
        item_id: str,
        field: ReviewField,
        revision_id: str,
        revision_no: int,
        revision_content_hash: str,
        request_sha256: str,
        profile_extension: str,
        authority_sha256: str,
        root_prestate_sha256: str,
    ) -> AudioPublicationResult:
        field = ReviewField(field)
        final_path = derive_audio_final_path(
            field=field,
            item_id=item_id,
            revision_id=revision_id,
            request_sha256=request_sha256,
            profile_extension=profile_extension,
        )
        command_sha256 = canonical_command_sha256(
            {
                "action": ReviewTransitionAction.AUDIO_RESERVED.value,
                "job_id": job_id,
                "item_id": item_id,
                "field": field.value,
                "revision_id": revision_id,
                "revision_no": revision_no,
                "revision_content_hash": revision_content_hash,
                "request_sha256": request_sha256,
                "profile_extension": profile_extension,
                "authority_sha256": authority_sha256,
                "root_prestate_sha256": root_prestate_sha256,
                "final_path": final_path,
            }
        )
        with self._lock:
            replay = self._command_replay(actor_id, request_id, ReviewTransitionAction.AUDIO_RESERVED.value, command_sha256)
            if replay is not None:
                return replay
            self._exact_revision(job_id, item_id, field, revision_id, revision_no, revision_content_hash)
            revision_key = (job_id, item_id, field, revision_id)
            existing_path = self._publication_revision_paths.get(revision_key)
            if existing_path is not None and existing_path != final_path:
                raise ReviewCASConflict("one final path is allowed per revision")
            existing_revision = self._publication_path_revisions.get(final_path)
            if existing_revision is not None and existing_revision != revision_key:
                raise ReviewCASConflict("one revision is allowed per final path")
            reservation = AudioPublicationReservation(
                reservation_id=self._safe_id("reservation", command_sha256, revision_id),
                job_id=job_id,
                item_id=item_id,
                field=field,
                revision_id=revision_id,
                revision_no=revision_no,
                revision_content_hash=revision_content_hash,
                request_sha256=request_sha256,
                profile_extension=profile_extension,
                final_path=final_path,
                authority_sha256=authority_sha256,
                root_prestate_sha256=root_prestate_sha256,
                version=1,
                reserved_at=self._now(),
            )
            transition = AudioPublicationTransition(
                transition_id=self._safe_id("pub", command_sha256, AudioPublicationStatus.RESERVED.value),
                reservation_id=reservation.reservation_id,
                status=AudioPublicationStatus.RESERVED,
                from_version=0,
                to_version=1,
                final_path=reservation.final_path,
                artifact_sha256=None,
                evidence_sha256=command_sha256,
                reason_code="none",
                occurred_at=self._now(),
            )
            self._publication_revision_paths[revision_key] = final_path
            self._publication_path_revisions[final_path] = revision_key
            self._publication_states[reservation.reservation_id] = _PublicationState(
                reservation=reservation,
                status=AudioPublicationStatus.RESERVED,
            )
            self.audio_transitions.append(transition)
            result = AudioPublicationResult(reservation=reservation, transition=transition)
            self._store_command_result(actor_id, request_id, ReviewTransitionAction.AUDIO_RESERVED.value, command_sha256, result)
            return result

    def transition_audio_publication(
        self,
        *,
        actor_id: str,
        request_id: str,
        reservation_id: str,
        expected_version: int,
        status: AudioPublicationStatus,
        artifact_sha256: str | None = None,
        evidence_sha256: str,
    ) -> AudioPublicationResult:
        status = AudioPublicationStatus(status)
        action = self._audio_action(status)
        command_sha256 = canonical_command_sha256(
            {
                "action": action.value,
                "reservation_id": reservation_id,
                "expected_version": expected_version,
                "status": status.value,
                "artifact_sha256": artifact_sha256,
                "evidence_sha256": evidence_sha256,
            }
        )
        with self._lock:
            replay = self._command_replay(actor_id, request_id, action.value, command_sha256)
            if replay is not None:
                return replay
            state = self._publication_state(reservation_id)
            self._require_publication_version(state, expected_version)
            self._require_publication_order(state.status, status)
            reservation = state.reservation.model_copy(update={"version": expected_version + 1})
            transition = AudioPublicationTransition(
                transition_id=self._safe_id("pub", command_sha256, status.value),
                reservation_id=reservation_id,
                status=status,
                from_version=expected_version,
                to_version=reservation.version,
                final_path=state.reservation.final_path,
                artifact_sha256=artifact_sha256,
                evidence_sha256=evidence_sha256,
                reason_code="none" if status not in {AudioPublicationStatus.FAILED_UNKNOWN, AudioPublicationStatus.BLOCKED_MISMATCH} else status.value,
                occurred_at=self._now(),
            )
            self._publication_states[reservation_id] = _PublicationState(
                reservation=reservation,
                status=status,
                artifact_sha256=artifact_sha256 or state.artifact_sha256,
            )
            self.audio_transitions.append(transition)
            result = AudioPublicationResult(reservation=reservation, transition=transition)
            self._store_command_result(actor_id, request_id, action.value, command_sha256, result)
            return result

    def finalize_audio_publication(
        self,
        *,
        actor_id: str,
        request_id: str,
        reservation_id: str,
        expected_version: int,
        artifact_sha256: str,
        evidence_sha256: str,
        expected_pointer_version: int,
    ) -> AudioPublicationResult:
        command_sha256 = canonical_command_sha256(
            {
                "action": ReviewTransitionAction.AUDIO_FINALIZED.value,
                "reservation_id": reservation_id,
                "expected_version": expected_version,
                "artifact_sha256": artifact_sha256,
                "evidence_sha256": evidence_sha256,
                "expected_pointer_version": expected_pointer_version,
            }
        )
        with self._lock:
            replay = self._command_replay(actor_id, request_id, ReviewTransitionAction.AUDIO_FINALIZED.value, command_sha256)
            if replay is not None:
                return replay
            state = self._publication_state(reservation_id)
            self._require_publication_version(state, expected_version)
            if state.status is not AudioPublicationStatus.PUBLISHED:
                raise ReviewCASConflict("audio reservation must be published before finalization")
            if state.artifact_sha256 != artifact_sha256:
                raise ReviewCASConflict("published artifact hash mismatch")
            reservation = state.reservation
            pointer = self._pointer(reservation.job_id, reservation.item_id, reservation.field)
            if pointer.version != expected_pointer_version:
                raise ReviewCASConflict("pointer version mismatch")
            updated_pointer = FieldPointer(
                job_id=reservation.job_id,
                item_id=reservation.item_id,
                field=reservation.field,
                candidate_revision_id=reservation.revision_id,
                candidate_content_hash=reservation.revision_content_hash,
                approved_revision_id=pointer.approved_revision_id,
                approved_content_hash=pointer.approved_content_hash,
                version=pointer.version if pointer.candidate_revision_id == reservation.revision_id else pointer.version + 1,
            )
            updated_reservation = reservation.model_copy(update={"version": expected_version + 1})
            transition = AudioPublicationTransition(
                transition_id=self._safe_id("pub", command_sha256, AudioPublicationStatus.FINALIZED.value),
                reservation_id=reservation_id,
                status=AudioPublicationStatus.FINALIZED,
                from_version=expected_version,
                to_version=updated_reservation.version,
                final_path=reservation.final_path,
                artifact_sha256=artifact_sha256,
                evidence_sha256=evidence_sha256,
                reason_code="none",
                occurred_at=self._now(),
            )
            self.pointers[self._pointer_key(reservation.job_id, reservation.item_id, reservation.field)] = updated_pointer
            self._publication_states[reservation_id] = _PublicationState(
                reservation=updated_reservation,
                status=AudioPublicationStatus.FINALIZED,
                artifact_sha256=artifact_sha256,
            )
            self.audio_transitions.append(transition)
            result = AudioPublicationResult(
                reservation=updated_reservation,
                transition=transition,
                pointer=updated_pointer,
            )
            self._store_command_result(actor_id, request_id, ReviewTransitionAction.AUDIO_FINALIZED.value, command_sha256, result)
            return result

    def _candidate_action(self, action: str | ReviewTransitionAction) -> ReviewTransitionAction:
        if isinstance(action, ReviewTransitionAction):
            action_enum = action
        else:
            action_enum = ReviewTransitionAction(action)
        if action_enum not in {
            ReviewTransitionAction.CREATE_CANDIDATE,
            ReviewTransitionAction.VALIDATED_GENERATION_RESULT,
            ReviewTransitionAction.EDIT_TO_NEW_CANDIDATE,
            ReviewTransitionAction.REGENERATE_FIELD,
        }:
            raise ReviewValidationError("action does not create a candidate")
        return action_enum

    def _pointer_key(self, job_id: str, item_id: str, field: ReviewField) -> tuple[str, str, ReviewField]:
        return (job_id, item_id, ReviewField(field))

    def _pointer(self, job_id: str, item_id: str, field: ReviewField) -> FieldPointer:
        key = self._pointer_key(job_id, item_id, field)
        return self.pointers.get(
            key,
            FieldPointer(job_id=job_id, item_id=item_id, field=field, version=0),
        )

    def _require_pointer(
        self,
        pointer: FieldPointer,
        expected_version: int,
        expected_base_revision_id: str | None,
    ) -> None:
        if pointer.version != expected_version:
            raise ReviewCASConflict("pointer version mismatch")
        if pointer.candidate_revision_id != expected_base_revision_id:
            raise ReviewCASConflict("expected base revision mismatch")

    def _exact_revision(
        self,
        job_id: str,
        item_id: str,
        field: ReviewField,
        revision_id: str,
        revision_no: int,
        content_hash: str,
    ) -> FieldRevision:
        revision = self.revisions.get(revision_id)
        if revision is None:
            raise ReviewCASConflict("revision missing")
        if (
            revision.job_id != job_id
            or revision.item_id != item_id
            or revision.field is not field
            or revision.revision_no != revision_no
            or revision.content_hash != content_hash
        ):
            raise ReviewCASConflict("revision identity mismatch")
        return revision

    def _next_revision_no(self, job_id: str, item_id: str, field: ReviewField) -> int:
        return 1 + max(
            (
                revision.revision_no
                for revision in self.revisions.values()
                if revision.job_id == job_id and revision.item_id == item_id and revision.field is field
            ),
            default=0,
        )

    def _list_rows(self, selector: ReviewListSelector) -> tuple[dict[str, object], ...]:
        rows: list[dict[str, object]] = []
        for (job_id, item_id, field), pointer in sorted(
            self.pointers.items(), key=lambda item: (item[0][0], item[0][1], item[0][2].value)
        ):
            if job_id != selector.job_id or field not in selector.fields:
                continue
            revision_id = pointer.candidate_revision_id or pointer.approved_revision_id
            if revision_id is None:
                continue
            rows.append(
                {
                    "job_id": job_id,
                    "item_id": item_id,
                    "field": field.value,
                    "candidate_revision_id": pointer.candidate_revision_id,
                    "approved_revision_id": pointer.approved_revision_id,
                    "status": self._revision_status(self.revisions[revision_id]).value,
                    "pointer_version": pointer.version,
                }
            )
        return tuple(rows)

    def _revision_status(self, revision: FieldRevision) -> ReviewStatus:
        latest = self.latest_decision(revision.revision_id)
        if latest is None:
            return revision.initial_status
        return latest.status

    def _revision_for_selector(self, selector: ReviewInspectSelector) -> FieldRevision:
        revision = self.revisions.get(selector.revision_id)
        if revision is None:
            raise ReviewCASConflict("revision missing")
        if revision.job_id != selector.job_id or revision.item_id != selector.item_id or revision.field is not selector.field:
            raise ReviewCASConflict("revision identity mismatch")
        return revision

    def _stale_dependents_locked(
        self,
        *,
        actor_id: str,
        request_id: str,
        command_sha256: str,
        job_id: str,
        item_id: str,
        source_field: ReviewField,
        source_content_hash: str,
        reason_code: str,
        allowed_fields: tuple[ReviewField, ...] | None,
    ) -> tuple[ReviewDecision, ...]:
        stale_decisions: list[ReviewDecision] = []
        for pointer in tuple(self.pointers.values()):
            if pointer.job_id != job_id or pointer.item_id != item_id or pointer.approved_revision_id is None:
                continue
            if allowed_fields is not None and pointer.field not in allowed_fields:
                continue
            revision = self.revisions[pointer.approved_revision_id]
            if self._revision_status(revision) is ReviewStatus.STALE:
                continue
            matching_dependency = next(
                (
                    dependency
                    for dependency in revision.dependency_hashes
                    if dependency.source_field is source_field
                    and dependency.source_content_hash == source_content_hash
                ),
                None,
            )
            if matching_dependency is None:
                continue
            decision = ReviewDecision(
                decision_id=self._safe_id("decision", command_sha256, revision.revision_id, reason_code),
                job_id=revision.job_id,
                item_id=revision.item_id,
                field=revision.field,
                revision_id=revision.revision_id,
                revision_no=revision.revision_no,
                content_hash=revision.content_hash,
                status=ReviewStatus.STALE,
                actor_type="system",
                actor_id=actor_id,
                policy_sha256="0" * 64,
                evidence=None,
                reason_code=reason_code,
                dependency_binding=matching_dependency,
                created_at=self._now(),
            )
            event = self._transition_event(
                action=ReviewTransitionAction.STALE_DEPENDENT,
                actor_id=actor_id,
                request_id=request_id,
                command_sha256=command_sha256,
                job_id=revision.job_id,
                item_id=revision.item_id,
                field=revision.field,
                before_revision_id=revision.revision_id,
                before_content_hash=revision.content_hash,
                after_revision_id=revision.revision_id,
                after_content_hash=revision.content_hash,
                before_pointer_version=pointer.version,
                after_pointer_version=pointer.version,
                reason_code=reason_code,
            )
            self.decisions.append(decision)
            self.transition_events.append(event)
            stale_decisions.append(decision)
        return tuple(stale_decisions)

    def _proposal_decision(
        self,
        *,
        actor_id: str,
        request_id: str,
        job_id: str,
        item_id: str,
        action: ReviewTransitionAction,
        proposal_id: str,
        base_revision_id: str,
        reason_code: str,
        extra: dict[str, object],
    ) -> ReviewOperationResult:
        command_sha256 = canonical_command_sha256(
            {
                "action": action.value,
                "job_id": job_id,
                "item_id": item_id,
                "proposal_id": proposal_id,
                "base_revision_id": base_revision_id,
                "reason_code": reason_code,
                **extra,
            }
        )
        with self._lock:
            replay = self._command_replay(actor_id, request_id, action.value, command_sha256)
            if replay is not None:
                return replay
            if base_revision_id not in self.revisions:
                raise ReviewCASConflict("base revision missing")
            event = self._transition_event(
                action=action,
                actor_id=actor_id,
                request_id=request_id,
                command_sha256=command_sha256,
                job_id=job_id,
                item_id=item_id,
                field=None,
                before_revision_id=base_revision_id,
                before_content_hash=self.revisions[base_revision_id].content_hash,
                after_revision_id=base_revision_id,
                after_content_hash=self.revisions[base_revision_id].content_hash,
                before_pointer_version=0,
                after_pointer_version=0,
                reason_code=reason_code,
            )
            self.transition_events.append(event)
            result = ReviewOperationResult(event=event)
            self._store_command_result(actor_id, request_id, action.value, command_sha256, result)
            return result

    def _publication_state(self, reservation_id: str) -> _PublicationState:
        state = self._publication_states.get(reservation_id)
        if state is None:
            raise ReviewCASConflict("audio reservation missing")
        return state

    def _require_publication_version(self, state: _PublicationState, expected_version: int) -> None:
        if state.reservation.version != expected_version:
            raise ReviewCASConflict("audio reservation version mismatch")

    def _require_publication_order(
        self,
        current: AudioPublicationStatus,
        requested: AudioPublicationStatus,
    ) -> None:
        allowed = {
            AudioPublicationStatus.RESERVED: {
                AudioPublicationStatus.STAGED,
                AudioPublicationStatus.FAILED_UNKNOWN,
                AudioPublicationStatus.BLOCKED_MISMATCH,
            },
            AudioPublicationStatus.STAGED: {
                AudioPublicationStatus.PUBLISHED,
                AudioPublicationStatus.FAILED_UNKNOWN,
                AudioPublicationStatus.BLOCKED_MISMATCH,
            },
            AudioPublicationStatus.PUBLISHED: {
                AudioPublicationStatus.FINALIZED,
                AudioPublicationStatus.FAILED_UNKNOWN,
                AudioPublicationStatus.BLOCKED_MISMATCH,
            },
        }
        if requested not in allowed.get(current, set()):
            raise ReviewCASConflict("audio publication transition order invalid")

    def _audio_action(self, status: AudioPublicationStatus) -> ReviewTransitionAction:
        mapping = {
            AudioPublicationStatus.STAGED: ReviewTransitionAction.AUDIO_STAGED,
            AudioPublicationStatus.PUBLISHED: ReviewTransitionAction.AUDIO_PUBLISHED,
            AudioPublicationStatus.FINALIZED: ReviewTransitionAction.AUDIO_FINALIZED,
            AudioPublicationStatus.FAILED_UNKNOWN: ReviewTransitionAction.AUDIO_PUBLISHED,
            AudioPublicationStatus.BLOCKED_MISMATCH: ReviewTransitionAction.AUDIO_PUBLISHED,
        }
        if status is AudioPublicationStatus.RESERVED:
            raise ReviewValidationError("use reserve_audio_publication for reservation")
        return mapping[status]

    def _command_replay(
        self,
        actor_id: str,
        request_id: str,
        action: str,
        command_sha256: str,
    ) -> object | None:
        stable_key = (actor_id, request_id, action)
        previous = self._command_results.get(stable_key)
        if previous is None:
            return None
        previous_hash, result = previous
        if previous_hash != command_sha256:
            raise ReviewCommandConflict("stable command identity reused with different command hash")
        return replace(result, replayed=True)

    def _store_command_result(
        self,
        actor_id: str,
        request_id: str,
        action: str,
        command_sha256: str,
        result: object,
    ) -> None:
        self._command_results[(actor_id, request_id, action)] = (command_sha256, result)

    def _access_replay(
        self,
        actor_id: str,
        request_id: str,
        action: ReviewAccessAction,
        command_sha256: str,
    ) -> ReviewAccessResult | None:
        stable_key = (actor_id, request_id, action)
        previous = self._access_results.get(stable_key)
        if previous is None:
            return None
        previous_hash, result = previous
        if previous_hash != command_sha256:
            raise ReviewCommandConflict("stable access identity reused with different command hash")
        return replace(result, replayed=True)

    def _store_access_result(
        self,
        actor_id: str,
        request_id: str,
        action: ReviewAccessAction,
        command_sha256: str,
        result: ReviewAccessResult,
    ) -> None:
        self._access_results[(actor_id, request_id, action)] = (command_sha256, result)

    def _access_event(
        self,
        *,
        actor_id: str,
        request_id: str,
        action: ReviewAccessAction,
        command_sha256: str,
        result_hash: str,
        result_count: int,
    ) -> ReviewAccessEvent:
        return ReviewAccessEvent(
            event_id=self._safe_id("access", actor_id, request_id, action.value, command_sha256),
            actor_id=actor_id,
            request_id=request_id,
            action=action,
            command_sha256=command_sha256,
            result_id=self._safe_id("result", command_sha256, result_hash),
            result_hash=result_hash,
            result_count=result_count,
            occurred_at=self._now(),
        )

    def _transition_event(
        self,
        *,
        action: ReviewTransitionAction,
        actor_id: str,
        request_id: str,
        command_sha256: str,
        job_id: str,
        item_id: str,
        field: ReviewField | None,
        before_revision_id: str | None,
        before_content_hash: str | None,
        after_revision_id: str | None,
        after_content_hash: str | None,
        before_pointer_version: int,
        after_pointer_version: int,
        reason_code: str,
    ) -> ReviewTransitionEvent:
        return ReviewTransitionEvent(
            event_id=self._safe_id("event", action.value, command_sha256, len(self.transition_events)),
            job_id=job_id,
            item_id=item_id,
            field=field,
            action=action,
            actor_id=actor_id,
            request_id=request_id,
            command_sha256=command_sha256,
            before_revision_id=before_revision_id,
            before_content_hash=before_content_hash,
            after_revision_id=after_revision_id,
            after_content_hash=after_content_hash,
            before_pointer_version=before_pointer_version,
            after_pointer_version=after_pointer_version,
            reason_code=reason_code,
            occurred_at=self._now(),
        )

    def _safe_id(self, prefix: str, *parts: object) -> str:
        return f"{prefix}-{canonical_command_sha256(parts)[:24]}"

    def _now(self) -> str:
        value = datetime(2026, 8, 30, 12, 0, 0) + timedelta(seconds=self._clock_tick)
        self._clock_tick += 1
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")


__all__ = [
    "AudioPublicationResult",
    "ReviewAccessResult",
    "ReviewCASConflict",
    "ReviewCommandConflict",
    "ReviewOperationResult",
    "ReviewRevisionError",
    "ReviewRevisionService",
    "ReviewValidationError",
]
