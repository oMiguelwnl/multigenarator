"""SQLAlchemy repository for ordered Korean personal-source rows."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from multilang.db.models import PersonalSourceDecisionModel, PersonalSourceRowModel
from multilang.domain.korean import canonical_json_sha256
from multilang.domain.personal_sources import PersonalSourceRow


class PersonalSourceConflict(ValueError):
    """The same personal-source identity was replayed with changed rows."""


class PersonalSourceCASConflict(ValueError):
    """A decision append did not match the expected latest revision."""


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PersonalSourceDecisionRecord(_Record):
    decision_id: str
    row_id: str
    decision_revision: int = Field(ge=1)
    decision_state: str
    decision_reason_code: str | None = None
    korean_identity_sha256: str | None = None
    prerequisite_ids: tuple[str, ...] = ()
    resolved_lemma: str | None = None
    resolved_pos: str | None = None
    resolved_sense_id: str | None = None

    @field_validator("korean_identity_sha256")
    @classmethod
    def optional_hash_must_be_hex(cls, value: str | None) -> str | None:
        if value is not None:
            _require_sha256(value, "korean_identity_sha256")
        return value


class PersonalSourceStoredRow(_Record):
    row_id: str
    item_key: str
    source_type: str
    input_position: int = Field(ge=1)
    submitted_form: str
    normalized_form: str
    source_row_sha256: str
    parser_version: str
    duplicate_of_position: int | None = None
    latest_decision: PersonalSourceDecisionRecord | None = None

    @field_validator("source_row_sha256")
    @classmethod
    def row_hash_must_be_hex(cls, value: str) -> str:
        _require_sha256(value, "source_row_sha256")
        return value


class PersonalSourceInventory(_Record):
    job_id: str
    source_type: str
    inventory_root_sha256: str
    rows: tuple[PersonalSourceStoredRow, ...]


class KoreanPersonalSourceRepository:
    """Insert-only ordered row persistence with explicit decision CAS."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def store_rows(
        self,
        *,
        job_id: str,
        source_type: str,
        parser_version: str,
        rows: tuple[PersonalSourceRow, ...],
    ) -> PersonalSourceInventory:
        ordered_rows = tuple(sorted(rows, key=lambda row: row.input_position))
        existing = self._row_models(job_id, source_type)
        expected_hashes = tuple(
            _source_row_sha256(source_type=source_type, parser_version=parser_version, row=row)
            for row in ordered_rows
        )
        if existing:
            current_hashes = tuple(row.source_row_sha256 for row in existing)
            if current_hashes == expected_hashes:
                return self.list_inventory(job_id, source_type)
            raise PersonalSourceConflict("personal source rows changed for existing request")

        for row, digest in zip(ordered_rows, expected_hashes, strict=True):
            self.session.add(
                PersonalSourceRowModel(
                    id=str(uuid4()),
                    job_id=job_id,
                    item_key=row.stable_item_key,
                    source_type=source_type,
                    input_position=row.input_position,
                    submitted_form=row.submitted_form,
                    normalized_form=row.display_form,
                    source_row_sha256=digest,
                    parser_version=parser_version,
                )
            )
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            existing_after_conflict = self._row_models(job_id, source_type)
            if tuple(row.source_row_sha256 for row in existing_after_conflict) == expected_hashes:
                return self.list_inventory(job_id, source_type)
            raise PersonalSourceConflict("personal source rows changed for existing request") from exc
        return self.list_inventory(job_id, source_type)

    def list_inventory(self, job_id: str, source_type: str) -> PersonalSourceInventory:
        rows = self._row_models(job_id, source_type)
        first_position_by_key: dict[str, int] = {}
        stored_rows: list[PersonalSourceStoredRow] = []
        for row in rows:
            duplicate_of = first_position_by_key.get(row.item_key)
            first_position_by_key.setdefault(row.item_key, row.input_position)
            stored_rows.append(
                PersonalSourceStoredRow(
                    row_id=row.id,
                    item_key=row.item_key,
                    source_type=row.source_type,
                    input_position=row.input_position,
                    submitted_form=row.submitted_form,
                    normalized_form=row.normalized_form,
                    source_row_sha256=row.source_row_sha256,
                    parser_version=row.parser_version,
                    duplicate_of_position=duplicate_of,
                    latest_decision=self._latest_decision(row.id),
                )
            )
        root_payload = {
            "job_id": job_id,
            "source_type": source_type,
            "rows": [row.model_dump(mode="json") for row in stored_rows],
        }
        return PersonalSourceInventory(
            job_id=job_id,
            source_type=source_type,
            inventory_root_sha256=canonical_json_sha256(root_payload),
            rows=tuple(stored_rows),
        )

    def append_decision(
        self,
        *,
        row_id: str,
        expected_latest_revision: int,
        decision_state: str,
        decision_reason_code: str | None = None,
        korean_identity_sha256: str | None = None,
        prerequisite_ids: tuple[str, ...] = (),
        resolved_lemma: str | None = None,
        resolved_pos: str | None = None,
        resolved_sense_id: str | None = None,
    ) -> PersonalSourceDecisionRecord:
        if korean_identity_sha256 is not None:
            _require_sha256(korean_identity_sha256, "korean_identity_sha256")
        latest = self._latest_revision(row_id)
        if latest != expected_latest_revision:
            raise PersonalSourceCASConflict("personal source decision revision conflict")
        next_revision = latest + 1
        decision_id = canonical_json_sha256(
            {
                "row_id": row_id,
                "decision_revision": next_revision,
                "decision_state": decision_state,
                "decision_reason_code": decision_reason_code,
                "korean_identity_sha256": korean_identity_sha256,
                "prerequisite_ids": prerequisite_ids,
                "resolved_lemma": resolved_lemma,
                "resolved_pos": resolved_pos,
                "resolved_sense_id": resolved_sense_id,
            }
        )
        model = PersonalSourceDecisionModel(
            id=str(uuid4()),
            row_id=row_id,
            decision_revision=next_revision,
            resolved_lemma=resolved_lemma,
            resolved_pos=resolved_pos,
            resolved_sense_id=resolved_sense_id,
            decision_state=decision_state,
            decision_reason_code=decision_reason_code,
            korean_identity_sha256=korean_identity_sha256,
            prerequisite_ids=list(prerequisite_ids),
        )
        self.session.add(model)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise PersonalSourceCASConflict("personal source decision revision conflict") from exc
        return PersonalSourceDecisionRecord(
            decision_id=decision_id,
            row_id=row_id,
            decision_revision=next_revision,
            decision_state=decision_state,
            decision_reason_code=decision_reason_code,
            korean_identity_sha256=korean_identity_sha256,
            prerequisite_ids=prerequisite_ids,
            resolved_lemma=resolved_lemma,
            resolved_pos=resolved_pos,
            resolved_sense_id=resolved_sense_id,
        )

    def _row_models(self, job_id: str, source_type: str) -> tuple[PersonalSourceRowModel, ...]:
        rows = self.session.scalars(
            select(PersonalSourceRowModel)
            .where(
                PersonalSourceRowModel.job_id == job_id,
                PersonalSourceRowModel.source_type == source_type,
            )
            .order_by(PersonalSourceRowModel.input_position.asc())
        )
        return tuple(rows)

    def _latest_revision(self, row_id: str) -> int:
        return int(
            self.session.scalar(
                select(func.max(PersonalSourceDecisionModel.decision_revision)).where(
                    PersonalSourceDecisionModel.row_id == row_id
                )
            )
            or 0
        )

    def _latest_decision(self, row_id: str) -> PersonalSourceDecisionRecord | None:
        row = self.session.scalar(
            select(PersonalSourceDecisionModel)
            .where(PersonalSourceDecisionModel.row_id == row_id)
            .order_by(PersonalSourceDecisionModel.decision_revision.desc())
            .limit(1)
        )
        if row is None:
            return None
        return _decision_to_record(row)


def _decision_to_record(row: PersonalSourceDecisionModel) -> PersonalSourceDecisionRecord:
    decision_id = canonical_json_sha256(
        {
            "row_id": row.row_id,
            "decision_revision": row.decision_revision,
            "decision_state": row.decision_state,
            "decision_reason_code": row.decision_reason_code,
            "korean_identity_sha256": row.korean_identity_sha256,
            "prerequisite_ids": tuple(row.prerequisite_ids),
            "resolved_lemma": row.resolved_lemma,
            "resolved_pos": row.resolved_pos,
            "resolved_sense_id": row.resolved_sense_id,
        }
    )
    return PersonalSourceDecisionRecord(
        decision_id=decision_id,
        row_id=row.row_id,
        decision_revision=row.decision_revision,
        decision_state=row.decision_state,
        decision_reason_code=row.decision_reason_code,
        korean_identity_sha256=row.korean_identity_sha256,
        prerequisite_ids=tuple(row.prerequisite_ids),
        resolved_lemma=row.resolved_lemma,
        resolved_pos=row.resolved_pos,
        resolved_sense_id=row.resolved_sense_id,
    )


def _source_row_sha256(
    *,
    source_type: str,
    parser_version: str,
    row: PersonalSourceRow,
) -> str:
    return canonical_json_sha256(
        {
            "source_type": source_type,
            "parser_version": parser_version,
            "input_position": row.input_position,
            "line_number": row.line_number,
            "submitted_form": row.submitted_form,
            "display_form": row.display_form,
            "normalized_duplicate_key": row.normalized_duplicate_key,
            "duplicate_of_position": row.duplicate_of_position,
        }
    )


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
