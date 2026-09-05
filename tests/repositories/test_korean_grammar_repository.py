"""Repository tests for immutable Korean grammar bundle persistence."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, func, select, update
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import KoreanGrammarMemberModel
from multilang.repositories.korean_grammar_repository import (
    GrammarBundleRecord,
    GrammarMemberRecord,
    KoreanGrammarRepository,
    KoreanGrammarRepositoryConflict,
    KoreanGrammarRepositoryIntegrityError,
    canonical_grammar_bundle_sha256,
    canonical_grammar_member_sha256,
)


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _member(*, sequence: int = 1, construction_id: str = "grammar:topic") -> GrammarMemberRecord:
    payload = {
        "construction_id": construction_id,
        "sequence_index": sequence,
        "form": "은/는",
        "function_label": "marca tópico",
        "register": "해요체",
        "prerequisite_ids": ("orthography.hangul",),
    }
    return GrammarMemberRecord(
        **payload,
        member_sha256=canonical_grammar_member_sha256(payload),
    )


def _bundle(
    *,
    bundle_id: str = "grammar-bundle-v1",
    source_kind: str = "active-approved-snapshot",
    status: str = "active",
    members: tuple[GrammarMemberRecord, ...] | None = None,
) -> GrammarBundleRecord:
    member_records = members or (_member(),)
    payload = {
        "bundle_id": bundle_id,
        "source_kind": source_kind,
        "source_sha256": SHA_C,
        "version": "2026.08",
        "status": status,
        "members": tuple(member.model_dump() for member in member_records),
    }
    return GrammarBundleRecord(
        **payload,
        bundle_sha256=canonical_grammar_bundle_sha256(payload),
    )


def test_insert_retry_conflict_rollback_load_rehash_candidate_and_synthetic_filter() -> None:
    session = _session()
    repository = KoreanGrammarRepository(session)
    bundle = _bundle()

    stored = repository.store_bundle(bundle)
    replayed = repository.store_bundle(bundle)

    assert replayed == stored
    assert replayed.members[0].sequence_index == 1
    assert session.scalar(select(func.count(KoreanGrammarMemberModel.id))) == 1

    changed = _bundle(members=(_member(construction_id="grammar:changed"),))
    with pytest.raises(KoreanGrammarRepositoryConflict):
        repository.store_bundle(changed)
    assert session.scalar(select(func.count(KoreanGrammarMemberModel.id))) == 1

    repository.store_bundle(_bundle(bundle_id="candidate", source_kind="current-candidate"))
    repository.store_bundle(_bundle(bundle_id="synthetic", source_kind="synthetic-fixture"))
    ready = repository.list_active_ready_bundles(source_sha256=SHA_C)

    assert [record.bundle_id for record in ready] == ["grammar-bundle-v1"]

    session.execute(
        update(KoreanGrammarMemberModel)
        .where(KoreanGrammarMemberModel.construction_id == "grammar:topic")
        .values(member_sha256=SHA_B)
    )
    session.commit()

    with pytest.raises(KoreanGrammarRepositoryIntegrityError):
        repository.load_bundle("grammar-bundle-v1")
