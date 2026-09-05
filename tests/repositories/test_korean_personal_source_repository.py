"""Repository tests for ordered Korean personal-source persistence."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import GenerationJob, PersonalSourceRowModel
from multilang.domain.personal_sources import PersonalSourceRow
from multilang.repositories.korean_personal_source_repository import (
    KoreanPersonalSourceRepository,
    PersonalSourceCASConflict,
    PersonalSourceConflict,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.add(
        GenerationJob(
            id="job-1",
            run_key="ko-custom-run",
            language="ko",
            source_type="word-list",
            source_fingerprint="fixture",
            status="created",
            current_stage="ingest",
        )
    )
    session.commit()
    return session


def _row(position: int, form: str, *, key: str | None = None) -> PersonalSourceRow:
    return PersonalSourceRow(
        input_position=position,
        line_number=position,
        submitted_form=form,
        display_form=form.strip(),
        normalized_duplicate_key=key or form.strip(),
        duplicate_of_position=1 if position == 2 else None,
    )


def test_every_position_duplicate_of_same_lemma_ordered_inventory_root_retry_reorder_decision_cas_no_auto_bridge() -> None:
    session = _session()
    repository = KoreanPersonalSourceRepository(session)
    rows = (
        _row(1, "학교"),
        _row(2, " 학교 ", key="학교"),
        _row(3, "공부해요", key="study-surface"),
    )

    stored = repository.store_rows(
        job_id="job-1",
        source_type="word-list",
        parser_version="korean-ordered-source-v1",
        rows=rows,
    )
    replayed = repository.store_rows(
        job_id="job-1",
        source_type="word-list",
        parser_version="korean-ordered-source-v1",
        rows=rows,
    )

    assert [row.input_position for row in replayed.rows] == [1, 2, 3]
    assert replayed.rows[1].duplicate_of_position == 1
    assert replayed.rows[2].item_key == "study-surface"
    assert replayed.inventory_root_sha256 == stored.inventory_root_sha256
    assert session.scalar(select(func.count(PersonalSourceRowModel.id))) == 3

    changed_reorder = (_row(1, "공부해요", key="study-surface"), _row(2, "학교"))
    with pytest.raises(PersonalSourceConflict):
        repository.store_rows(
            job_id="job-1",
            source_type="word-list",
            parser_version="korean-ordered-source-v1",
            rows=changed_reorder,
        )
    assert session.scalar(select(func.count(PersonalSourceRowModel.id))) == 3

    decision = repository.append_decision(
        row_id=stored.rows[0].row_id,
        expected_latest_revision=0,
        decision_state="bridge",
        decision_reason_code="operator_bridge",
        korean_identity_sha256=SHA_A,
        prerequisite_ids=("grammar:past",),
        resolved_lemma="학교",
        resolved_pos="NOUN",
        resolved_sense_id="school.n.01",
    )

    assert decision.decision_revision == 1
    assert decision.decision_state == "bridge"
    assert repository.list_inventory("job-1", "word-list").rows[0].latest_decision == decision
    with pytest.raises(PersonalSourceCASConflict):
        repository.append_decision(
            row_id=stored.rows[0].row_id,
            expected_latest_revision=0,
            decision_state="defer",
            decision_reason_code="operator_defer",
            korean_identity_sha256=SHA_B,
            prerequisite_ids=(),
        )
    assert session.scalar(select(func.count(PersonalSourceRowModel.id))) == 3
