"""SQLAlchemy repository for review revisions and audio publication state."""

from __future__ import annotations

from hashlib import sha256
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from multilang.db.models import (
    AudioPublicationReservationModel,
    AudioPublicationTransitionModel,
    AudioRevisionEvidenceModel,
    GenerationJob,
    ReviewAccessEventModel,
    ReviewCurrentPointerModel,
    ReviewDecisionModel,
    ReviewFieldRevisionModel,
)
from multilang.domain.korean import canonical_json_sha256


class ReviewRepositoryConflict(ValueError):
    """A stable request identity or immutable row was reused with changed content."""


class ReviewRepositoryCASConflict(ValueError):
    """A pointer or reservation version expectation was stale."""


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReviewRevisionRecord(_Record):
    revision_id: str
    job_id: str
    item_id: str
    field_name: str
    revision_no: int = Field(ge=1)
    value_sha256: str

    @field_validator("value_sha256")
    @classmethod
    def value_hash_must_be_hex(cls, value: str) -> str:
        _require_sha256(value, "value_sha256")
        return value


class ReviewMutationResult(_Record):
    revision: ReviewRevisionRecord
    pointer_version: int
    pointer_status: str
    replayed: bool = False


class ReviewAccessEventRecord(_Record):
    event_id: str
    action: str
    command_sha256: str
    result_id_sha256: str
    result_hash_count: int


class ReviewAccessResult(_Record):
    event: ReviewAccessEventRecord
    rows: tuple[dict[str, object], ...]
    replayed: bool = False


class AudioReservationRecord(_Record):
    reservation_id: str
    job_id: str
    item_id: str
    field_name: str
    field_revision_id: str
    final_path: str
    state: str
    version: int


class AudioTransitionRecord(_Record):
    reservation_id: str
    state: str
    version: int


class AudioEvidenceRecord(_Record):
    reservation_id: str
    state: str
    artifact_sha256: str


class ReviewRepository:
    """Repository boundary for exact review CAS and content-free access events."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_candidate_revision(
        self,
        *,
        actor_id: str,
        request_id: str,
        job_id: str,
        item_id: str,
        field_name: str,
        value_sha256: str,
        generator_id: str,
        generator_version: str,
        route_id: str | None,
        expected_pointer_version: int,
    ) -> ReviewMutationResult:
        _require_sha256(value_sha256, "value_sha256")
        command_sha256 = _command_sha256(
            "create_candidate_revision",
            actor_id=actor_id,
            request_id=request_id,
            job_id=job_id,
            item_id=item_id,
            field_name=field_name,
            value_sha256=value_sha256,
            generator_id=generator_id,
            generator_version=generator_version,
            route_id=route_id,
            expected_pointer_version=expected_pointer_version,
        )
        revision_id = _stable_id("rev", command_sha256)
        replay = self._candidate_replay(
            revision_id=revision_id,
            job_id=job_id,
            item_id=item_id,
            field_name=field_name,
            value_sha256=value_sha256,
        )
        if replay is not None:
            return replay.model_copy(update={"replayed": True})

        pointer = self._pointer(job_id, item_id, field_name)
        current_version = pointer.pointer_version if pointer is not None else 0
        if current_version != expected_pointer_version:
            if pointer is not None and pointer.review_status == "needs_review":
                raise ReviewRepositoryConflict("candidate command conflicts with current revision")
            raise ReviewRepositoryCASConflict("review pointer version conflict")
        revision_no = self._next_revision_no(job_id, item_id, field_name)
        revision = ReviewFieldRevisionModel(
            id=revision_id,
            job_id=job_id,
            item_id=item_id,
            field_name=field_name,
            revision_no=revision_no,
            value_sha256=value_sha256,
            generator_id=generator_id,
            generator_version=generator_version,
            route_id=route_id,
            previous_revision_sha256=None,
        )
        self.session.add(revision)
        if pointer is None:
            pointer = ReviewCurrentPointerModel(
                id=_stable_id("ptr", _command_sha256("pointer", job_id=job_id, item_id=item_id, field_name=field_name)),
                job_id=job_id,
                item_id=item_id,
                field_name=field_name,
                current_revision_id=revision_id,
                pointer_version=1,
                review_status="needs_review",
            )
            self.session.add(pointer)
        else:
            pointer.current_revision_id = revision_id
            pointer.pointer_version = expected_pointer_version + 1
            pointer.review_status = "needs_review"
            self.session.add(pointer)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            replay_after_conflict = self._candidate_replay(
                revision_id=revision_id,
                job_id=job_id,
                item_id=item_id,
                field_name=field_name,
                value_sha256=value_sha256,
            )
            if replay_after_conflict is not None:
                return replay_after_conflict.model_copy(update={"replayed": True})
            raise ReviewRepositoryConflict("candidate revision conflict") from exc
        return ReviewMutationResult(
            revision=_revision_record(revision),
            pointer_version=pointer.pointer_version,
            pointer_status=pointer.review_status,
        )

    def approve_revision(
        self,
        *,
        actor_id: str,
        request_id: str,
        job_id: str,
        item_id: str,
        field_name: str,
        revision_id: str,
        expected_pointer_version: int,
        decision_sha256: str,
        reason_code: str,
    ) -> ReviewMutationResult:
        _require_sha256(decision_sha256, "decision_sha256")
        pointer = self._pointer(job_id, item_id, field_name)
        if pointer is None or pointer.pointer_version != expected_pointer_version:
            raise ReviewRepositoryCASConflict("review pointer version conflict")
        revision = self._revision(job_id, item_id, field_name, revision_id)
        decision_revision = self._next_decision_revision(revision_id)
        self.session.add(
            ReviewDecisionModel(
                id=_stable_id(
                    "dec",
                    _command_sha256(
                        "approve_revision",
                        actor_id=actor_id,
                        request_id=request_id,
                        revision_id=revision_id,
                        decision_sha256=decision_sha256,
                    ),
                ),
                job_id=job_id,
                item_id=item_id,
                field_name=field_name,
                revision_id=revision_id,
                decision_revision=decision_revision,
                review_status="approved",
                reviewer_id_sha256=None,
                decision_sha256=decision_sha256,
                reason_code=reason_code,
            )
        )
        pointer.review_status = "approved"
        pointer.pointer_version = expected_pointer_version + 1
        self.session.add(pointer)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ReviewRepositoryConflict("review decision conflict") from exc
        return ReviewMutationResult(
            revision=_revision_record(revision),
            pointer_version=pointer.pointer_version,
            pointer_status=pointer.review_status,
        )

    def list_fields_with_audit(
        self,
        *,
        actor_id: str,
        request_id: str,
        job_id: str,
        fields: tuple[str, ...],
        statuses: tuple[str, ...],
        source_types: tuple[str, ...],
        policy_sha256: str,
        snapshot_sha256: str,
    ) -> ReviewAccessResult:
        _require_sha256(policy_sha256, "policy_sha256")
        _require_sha256(snapshot_sha256, "snapshot_sha256")
        command_sha256 = _command_sha256(
            "list_fields",
            job_id=job_id,
            fields=fields,
            statuses=statuses,
            source_types=source_types,
            policy_sha256=policy_sha256,
            snapshot_sha256=snapshot_sha256,
        )
        existing = self.session.scalar(
            select(ReviewAccessEventModel).where(
                ReviewAccessEventModel.actor_id == actor_id,
                ReviewAccessEventModel.request_id == request_id,
                ReviewAccessEventModel.action == "list",
            )
        )
        if existing is not None:
            if existing.command_sha256 != command_sha256:
                raise ReviewRepositoryConflict("review access command hash conflict")
            return ReviewAccessResult(
                event=_access_event_record(existing),
                rows=self._safe_field_rows(job_id, fields, statuses, source_types),
                replayed=True,
            )

        rows = self._safe_field_rows(job_id, fields, statuses, source_types)
        result_id_sha256 = canonical_json_sha256({"rows": rows})
        event = ReviewAccessEventModel(
            id=_stable_id("acc", _command_sha256("access", actor_id=actor_id, request_id=request_id, action="list")),
            actor_id=actor_id,
            request_id=request_id,
            action="list",
            command_sha256=command_sha256,
            result_id_sha256=result_id_sha256,
            result_hash_count=len(rows),
            policy_sha256=policy_sha256,
            snapshot_sha256=snapshot_sha256,
        )
        self.session.add(event)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ReviewRepositoryConflict("review access event conflict") from exc
        return ReviewAccessResult(event=_access_event_record(event), rows=rows)

    def reserve_audio_publication(
        self,
        *,
        job_id: str,
        item_id: str,
        field_name: str,
        field_revision_id: str,
        request_sha256: str,
        final_path: str,
        authority_sha256: str,
        root_prestate_sha256: str,
        expected_pointer_version: int,
    ) -> AudioReservationRecord:
        for name, value in {
            "request_sha256": request_sha256,
            "authority_sha256": authority_sha256,
            "root_prestate_sha256": root_prestate_sha256,
        }.items():
            _require_sha256(value, name)
        pointer = self._pointer(job_id, item_id, field_name)
        if pointer is None or pointer.pointer_version != expected_pointer_version:
            raise ReviewRepositoryCASConflict("audio reservation pointer version conflict")
        if pointer.current_revision_id != field_revision_id:
            raise ReviewRepositoryCASConflict("audio reservation revision conflict")
        final_path_sha256 = _text_sha256(final_path)
        existing = self.session.scalar(
            select(AudioPublicationReservationModel).where(
                AudioPublicationReservationModel.field_revision_id == field_revision_id
            )
        )
        if existing is not None:
            if _reservation_payload(existing) == {
                "job_id": job_id,
                "item_id": item_id,
                "field_name": field_name,
                "field_revision_id": field_revision_id,
                "request_sha256": request_sha256,
                "final_path": final_path,
                "final_path_sha256": final_path_sha256,
                "authority_sha256": authority_sha256,
                "root_prestate_sha256": root_prestate_sha256,
                "expected_pointer_version": expected_pointer_version,
            }:
                return _reservation_record(existing)
            raise ReviewRepositoryConflict("audio reservation identity conflict")
        reservation = AudioPublicationReservationModel(
            id=_stable_id(
                "res",
                _command_sha256(
                    "reserve_audio_publication",
                    field_revision_id=field_revision_id,
                    request_sha256=request_sha256,
                    final_path_sha256=final_path_sha256,
                ),
            ),
            job_id=job_id,
            item_id=item_id,
            field_name=field_name,
            field_revision_id=field_revision_id,
            request_sha256=request_sha256,
            final_path=final_path,
            final_path_sha256=final_path_sha256,
            authority_sha256=authority_sha256,
            root_prestate_sha256=root_prestate_sha256,
            expected_pointer_version=expected_pointer_version,
            reservation_version=0,
            state="reserved",
        )
        self.session.add(reservation)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ReviewRepositoryConflict("audio reservation conflict") from exc
        return _reservation_record(reservation)

    def append_audio_publication_transition(
        self,
        *,
        reservation_id: str,
        from_state: str,
        to_state: str,
        expected_version: int,
        transition_sha256: str,
    ) -> AudioTransitionRecord:
        _require_sha256(transition_sha256, "transition_sha256")
        reservation = self._reservation(reservation_id)
        if reservation.state != from_state or reservation.reservation_version != expected_version:
            raise ReviewRepositoryCASConflict("audio reservation transition conflict")
        next_version = expected_version + 1
        self.session.add(
            AudioPublicationTransitionModel(
                id=_stable_id("trn", transition_sha256),
                reservation_id=reservation_id,
                from_state=from_state,
                to_state=to_state,
                expected_version=expected_version,
                next_version=next_version,
                transition_sha256=transition_sha256,
            )
        )
        reservation.state = to_state
        reservation.reservation_version = next_version
        self.session.add(reservation)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ReviewRepositoryConflict("audio transition conflict") from exc
        return AudioTransitionRecord(reservation_id=reservation_id, state=to_state, version=next_version)

    def list_reconcilable_audio_publications(self) -> tuple[AudioReservationRecord, ...]:
        rows = self.session.scalars(
            select(AudioPublicationReservationModel)
            .where(AudioPublicationReservationModel.state.in_(("reserved", "staged", "published", "failed_unknown")))
            .order_by(AudioPublicationReservationModel.created_at.asc(), AudioPublicationReservationModel.id.asc())
        )
        return tuple(_reservation_record(row) for row in rows)

    def finalize_audio_publication(
        self,
        *,
        reservation_id: str,
        expected_reservation_version: int,
        artifact_sha256: str,
        byte_length: int,
        spoken_text_sha256: str,
        voice_profile_sha256: str,
        evidence_sha256: str,
    ) -> AudioEvidenceRecord:
        for name, value in {
            "artifact_sha256": artifact_sha256,
            "spoken_text_sha256": spoken_text_sha256,
            "voice_profile_sha256": voice_profile_sha256,
            "evidence_sha256": evidence_sha256,
        }.items():
            _require_sha256(value, name)
        reservation = self._reservation(reservation_id)
        if reservation.state != "published" or reservation.reservation_version != expected_reservation_version:
            raise ReviewRepositoryCASConflict("audio finalization requires published reservation")
        if byte_length <= 0:
            raise ValueError("audio byte length must be positive")
        next_version = expected_reservation_version + 1
        transition_hash = _command_sha256(
            "finalize_audio_publication",
            reservation_id=reservation_id,
            expected_reservation_version=expected_reservation_version,
            artifact_sha256=artifact_sha256,
            evidence_sha256=evidence_sha256,
        )
        self.session.add(
            AudioPublicationTransitionModel(
                id=_stable_id("trn", transition_hash),
                reservation_id=reservation_id,
                from_state="published",
                to_state="finalized",
                expected_version=expected_reservation_version,
                next_version=next_version,
                transition_sha256=transition_hash,
            )
        )
        self.session.add(
            AudioRevisionEvidenceModel(
                id=_stable_id("aud", evidence_sha256),
                reservation_id=reservation_id,
                field_revision_id=reservation.field_revision_id,
                role=reservation.field_name,
                root_sha256=reservation.root_prestate_sha256,
                final_path_sha256=reservation.final_path_sha256,
                request_sha256=reservation.request_sha256,
                artifact_sha256=artifact_sha256,
                byte_length=byte_length,
                spoken_text_sha256=spoken_text_sha256,
                voice_profile_sha256=voice_profile_sha256,
                review_status="approved",
                reservation_state="finalized",
                evidence_sha256=evidence_sha256,
            )
        )
        reservation.state = "finalized"
        reservation.reservation_version = next_version
        self.session.add(reservation)
        pointer = self._pointer(reservation.job_id, reservation.item_id, reservation.field_name)
        if pointer is not None and pointer.current_revision_id == reservation.field_revision_id:
            pointer.review_status = "approved"
            pointer.pointer_version += 1
            self.session.add(pointer)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ReviewRepositoryConflict("audio finalization conflict") from exc
        return AudioEvidenceRecord(
            reservation_id=reservation_id,
            state="finalized",
            artifact_sha256=artifact_sha256,
        )

    def _pointer(self, job_id: str, item_id: str, field_name: str) -> ReviewCurrentPointerModel | None:
        return self.session.scalar(
            select(ReviewCurrentPointerModel).where(
                ReviewCurrentPointerModel.job_id == job_id,
                ReviewCurrentPointerModel.item_id == item_id,
                ReviewCurrentPointerModel.field_name == field_name,
            )
        )

    def _candidate_replay(
        self,
        *,
        revision_id: str,
        job_id: str,
        item_id: str,
        field_name: str,
        value_sha256: str,
    ) -> ReviewMutationResult | None:
        revision = self.session.scalar(
            select(ReviewFieldRevisionModel).where(ReviewFieldRevisionModel.id == revision_id)
        )
        if revision is None:
            return None
        if (
            revision.job_id != job_id
            or revision.item_id != item_id
            or revision.field_name != field_name
            or revision.value_sha256 != value_sha256
        ):
            raise ReviewRepositoryConflict("candidate command hash conflict")
        pointer = self._pointer(job_id, item_id, field_name)
        if pointer is None:
            raise ReviewRepositoryConflict("candidate replay missing pointer")
        return ReviewMutationResult(
            revision=_revision_record(revision),
            pointer_version=pointer.pointer_version,
            pointer_status=pointer.review_status,
        )

    def _next_revision_no(self, job_id: str, item_id: str, field_name: str) -> int:
        return int(
            self.session.scalar(
                select(func.max(ReviewFieldRevisionModel.revision_no)).where(
                    ReviewFieldRevisionModel.job_id == job_id,
                    ReviewFieldRevisionModel.item_id == item_id,
                    ReviewFieldRevisionModel.field_name == field_name,
                )
            )
            or 0
        ) + 1

    def _next_decision_revision(self, revision_id: str) -> int:
        return int(
            self.session.scalar(
                select(func.max(ReviewDecisionModel.decision_revision)).where(
                    ReviewDecisionModel.revision_id == revision_id
                )
            )
            or 0
        ) + 1

    def _revision(
        self,
        job_id: str,
        item_id: str,
        field_name: str,
        revision_id: str,
    ) -> ReviewFieldRevisionModel:
        revision = self.session.scalar(
            select(ReviewFieldRevisionModel).where(
                ReviewFieldRevisionModel.id == revision_id,
                ReviewFieldRevisionModel.job_id == job_id,
                ReviewFieldRevisionModel.item_id == item_id,
                ReviewFieldRevisionModel.field_name == field_name,
            )
        )
        if revision is None:
            raise ReviewRepositoryCASConflict("review revision not current")
        return revision

    def _safe_field_rows(
        self,
        job_id: str,
        fields: tuple[str, ...],
        statuses: tuple[str, ...],
        source_types: tuple[str, ...],
    ) -> tuple[dict[str, object], ...]:
        statement = (
            select(ReviewCurrentPointerModel, ReviewFieldRevisionModel)
            .join(ReviewFieldRevisionModel, ReviewFieldRevisionModel.id == ReviewCurrentPointerModel.current_revision_id)
            .join(GenerationJob, GenerationJob.id == ReviewCurrentPointerModel.job_id)
            .where(
                ReviewCurrentPointerModel.job_id == job_id,
                ReviewCurrentPointerModel.field_name.in_(fields),
                ReviewCurrentPointerModel.review_status.in_(statuses),
                GenerationJob.source_type.in_(source_types),
            )
            .order_by(ReviewCurrentPointerModel.item_id.asc(), ReviewCurrentPointerModel.field_name.asc())
        )
        rows = []
        for pointer, revision in self.session.execute(statement):
            rows.append(
                {
                    "job_id": pointer.job_id,
                    "item_id": pointer.item_id,
                    "field": pointer.field_name,
                    "candidate_revision_id": pointer.current_revision_id,
                    "approved_revision_id": pointer.current_revision_id if pointer.review_status == "approved" else None,
                    "status": pointer.review_status,
                    "pointer_version": pointer.pointer_version,
                    "value_sha256": revision.value_sha256,
                }
            )
        return tuple(rows)

    def _reservation(self, reservation_id: str) -> AudioPublicationReservationModel:
        reservation = self.session.scalar(
            select(AudioPublicationReservationModel).where(AudioPublicationReservationModel.id == reservation_id)
        )
        if reservation is None:
            raise ReviewRepositoryCASConflict("audio reservation not found")
        return reservation


def _revision_record(row: ReviewFieldRevisionModel) -> ReviewRevisionRecord:
    return ReviewRevisionRecord(
        revision_id=row.id,
        job_id=row.job_id,
        item_id=row.item_id,
        field_name=row.field_name,
        revision_no=row.revision_no,
        value_sha256=row.value_sha256,
    )


def _access_event_record(row: ReviewAccessEventModel) -> ReviewAccessEventRecord:
    return ReviewAccessEventRecord(
        event_id=row.id,
        action=row.action,
        command_sha256=row.command_sha256,
        result_id_sha256=row.result_id_sha256,
        result_hash_count=row.result_hash_count,
    )


def _reservation_record(row: AudioPublicationReservationModel) -> AudioReservationRecord:
    return AudioReservationRecord(
        reservation_id=row.id,
        job_id=row.job_id,
        item_id=row.item_id,
        field_name=row.field_name,
        field_revision_id=row.field_revision_id,
        final_path=row.final_path,
        state=row.state,
        version=row.reservation_version,
    )


def _reservation_payload(row: AudioPublicationReservationModel) -> dict[str, object]:
    return {
        "job_id": row.job_id,
        "item_id": row.item_id,
        "field_name": row.field_name,
        "field_revision_id": row.field_revision_id,
        "request_sha256": row.request_sha256,
        "final_path": row.final_path,
        "final_path_sha256": row.final_path_sha256,
        "authority_sha256": row.authority_sha256,
        "root_prestate_sha256": row.root_prestate_sha256,
        "expected_pointer_version": row.expected_pointer_version,
    }


def _command_sha256(kind: str, **payload: object) -> str:
    return canonical_json_sha256({"kind": kind, **payload})


def _stable_id(prefix: str, digest: str) -> str:
    _require_sha256(digest, "digest")
    return f"{prefix}-{digest[:31]}"


def _text_sha256(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
