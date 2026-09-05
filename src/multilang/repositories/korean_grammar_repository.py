"""SQLAlchemy repository for immutable Korean grammar bundles."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from multilang.db.models import KoreanGrammarBundleModel, KoreanGrammarMemberModel
from multilang.domain.korean import canonical_json_sha256


class KoreanGrammarRepositoryError(ValueError):
    """Base error for grammar repository conflicts."""


class KoreanGrammarRepositoryConflict(KoreanGrammarRepositoryError):
    """The same immutable grammar identity was reused with changed content."""


class KoreanGrammarRepositoryIntegrityError(KoreanGrammarRepositoryError):
    """Persisted grammar evidence no longer matches its stored hash."""


class _Record(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class GrammarMemberRecord(_Record):
    construction_id: str
    sequence_index: int = Field(ge=1)
    form: str
    function_label: str
    usage_register: str = Field(alias="register", serialization_alias="register")
    prerequisite_ids: tuple[str, ...] = ()
    member_sha256: str

    @field_validator("member_sha256")
    @classmethod
    def member_hash_must_be_hex(cls, value: str) -> str:
        _require_sha256(value, "member_sha256")
        return value

    @model_validator(mode="after")
    def member_hash_must_match_payload(self) -> GrammarMemberRecord:
        expected = canonical_grammar_member_sha256(
            self.model_dump(exclude={"member_sha256"}, by_alias=True)
        )
        if self.member_sha256 != expected:
            raise ValueError("member_sha256 does not match member payload")
        return self

    @property
    def register(self) -> str:
        return self.usage_register


class GrammarBundleRecord(_Record):
    bundle_id: str
    bundle_sha256: str
    source_kind: str
    source_sha256: str
    version: str
    status: str
    members: tuple[GrammarMemberRecord, ...] = Field(min_length=1)

    @field_validator("bundle_sha256", "source_sha256")
    @classmethod
    def hashes_must_be_hex(cls, value: str, info: object) -> str:
        _require_sha256(value, getattr(info, "field_name", "sha256"))
        return value

    @model_validator(mode="after")
    def bundle_hash_must_match_payload(self) -> GrammarBundleRecord:
        expected = canonical_grammar_bundle_sha256(
            self.model_dump(exclude={"bundle_sha256"}, by_alias=True)
        )
        if self.bundle_sha256 != expected:
            raise ValueError("bundle_sha256 does not match bundle payload")
        return self


def canonical_grammar_member_sha256(payload: dict[str, Any]) -> str:
    return canonical_json_sha256(_jsonable(payload))


def canonical_grammar_bundle_sha256(payload: dict[str, Any]) -> str:
    return canonical_json_sha256(_jsonable(payload))


class KoreanGrammarRepository:
    """Insert-only grammar bundle adapter with exact retry semantics."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def store_bundle(self, record: GrammarBundleRecord) -> GrammarBundleRecord:
        existing = self.load_bundle(record.bundle_id, require_exists=False)
        if existing is not None:
            if existing == record:
                return existing
            raise KoreanGrammarRepositoryConflict("grammar bundle identity conflict")

        bundle_row = KoreanGrammarBundleModel(
            id=str(uuid4()),
            bundle_id=record.bundle_id,
            bundle_sha256=record.bundle_sha256,
            source_kind=record.source_kind,
            source_sha256=record.source_sha256,
            version=record.version,
            status=record.status,
            sequence_count=len(record.members),
        )
        self.session.add(bundle_row)
        for member in record.members:
            self.session.add(
                KoreanGrammarMemberModel(
                    id=str(uuid4()),
                    bundle_id=bundle_row.id,
                    construction_id=member.construction_id,
                    sequence_index=member.sequence_index,
                    form=member.form,
                    function_label=member.function_label,
                    register=member.register,
                    prerequisite_ids=list(member.prerequisite_ids),
                    member_sha256=member.member_sha256,
                )
            )
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            replay = self.load_bundle(record.bundle_id, require_exists=False)
            if replay == record:
                return replay
            raise KoreanGrammarRepositoryConflict("grammar bundle identity conflict") from exc
        return self.load_bundle(record.bundle_id)

    def load_bundle(
        self,
        bundle_id: str,
        *,
        require_exists: bool = True,
    ) -> GrammarBundleRecord | None:
        bundle = self.session.scalar(
            select(KoreanGrammarBundleModel).where(KoreanGrammarBundleModel.bundle_id == bundle_id)
        )
        if bundle is None:
            if require_exists:
                raise KoreanGrammarRepositoryIntegrityError("grammar bundle not found")
            return None
        return self._to_record(bundle)

    def list_active_ready_bundles(self, *, source_sha256: str) -> tuple[GrammarBundleRecord, ...]:
        _require_sha256(source_sha256, "source_sha256")
        rows = self.session.scalars(
            select(KoreanGrammarBundleModel)
            .where(
                KoreanGrammarBundleModel.status == "active",
                KoreanGrammarBundleModel.source_kind == "active-approved-snapshot",
                KoreanGrammarBundleModel.source_sha256 == source_sha256,
            )
            .order_by(KoreanGrammarBundleModel.bundle_id.asc())
        )
        return tuple(self._to_record(row) for row in rows)

    def _to_record(self, bundle: KoreanGrammarBundleModel) -> GrammarBundleRecord:
        member_rows = self.session.scalars(
            select(KoreanGrammarMemberModel)
            .where(KoreanGrammarMemberModel.bundle_id == bundle.id)
            .order_by(KoreanGrammarMemberModel.sequence_index.asc())
        )
        try:
            members = tuple(
                GrammarMemberRecord(
                    construction_id=row.construction_id,
                    sequence_index=row.sequence_index,
                    form=row.form,
                    function_label=row.function_label,
                    register=row.register,
                    prerequisite_ids=tuple(row.prerequisite_ids),
                    member_sha256=row.member_sha256,
                )
                for row in member_rows
            )
            return GrammarBundleRecord(
                bundle_id=bundle.bundle_id,
                bundle_sha256=bundle.bundle_sha256,
                source_kind=bundle.source_kind,
                source_sha256=bundle.source_sha256,
                version=bundle.version,
                status=bundle.status,
                members=members,
            )
        except (ValueError, ValidationError) as exc:
            raise KoreanGrammarRepositoryIntegrityError(str(exc)) from exc


def _jsonable(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, tuple | list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
