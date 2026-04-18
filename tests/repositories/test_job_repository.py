"""Repository tests for persisted job orchestration state."""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.jobs import GenerationRequest, JobStage, JobStatus, SupportedLanguage
from multilang.repositories.job_repository import JobRepository


def build_repository() -> tuple[JobRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return JobRepository(session), session


def make_request() -> GenerationRequest:
    return GenerationRequest(language=SupportedLanguage.EN, source_type="frequency", level=1)


def test_completed_items_are_reused_on_rerun() -> None:
    repository, session = build_repository()
    job = repository.create_job(
        request=make_request(),
        run_key="en-frequency-level-1",
        source_fingerprint="level-1",
        total_items=3,
    )

    repository.record_item_success(job.id, item_key="hola", completed_stage=JobStage.INGEST)
    repository.record_item_success(job.id, item_key="hola", completed_stage=JobStage.INGEST)
    session.expire_all()

    rerun = repository.get_job(run_key="en-frequency-level-1")

    assert rerun is not None
    assert repository.list_completed_item_keys("en-frequency-level-1") == {"hola"}
    assert rerun.completed_items == 1
    assert rerun.skipped_duplicates == 1


def test_corrupted_resume_state_returns_diagnostic() -> None:
    repository, session = build_repository()
    job = repository.create_job(
        request=make_request(),
        run_key="en-frequency-level-1",
        source_fingerprint="level-1",
        total_items=2,
        current_stage=JobStage.GENERATE_TEXT,
        last_completed_stage=JobStage.GENERATE_TEXT,
        status=JobStatus.RUNNING,
    )
    repository.record_item_success(job.id, item_key="hola", completed_stage=JobStage.INGEST)
    job.current_stage = JobStage.GENERATE_TEXT.value
    job.last_completed_stage = JobStage.GENERATE_TEXT.value
    session.add(job)
    session.commit()

    diagnostic = repository.validate_resume_state(job.id)

    assert diagnostic is not None
    assert diagnostic.job_id == job.id
    assert diagnostic.reason
    assert diagnostic.details["stored_current_stage"] == JobStage.GENERATE_TEXT.value
    assert diagnostic.details["actual_last_completed_stage"] == JobStage.INGEST.value


def test_duplicate_item_success_is_not_silently_persisted_twice() -> None:
    repository, session = build_repository()
    job = repository.create_job(
        request=make_request(),
        run_key="en-frequency-level-1",
        source_fingerprint="level-1",
        total_items=1,
    )

    repository.record_item_success(job.id, item_key="hola", completed_stage=JobStage.INGEST)
    repository.record_item_success(job.id, item_key="hola", completed_stage=JobStage.INGEST)

    assert session.execute(
        text(
            "SELECT COUNT(*) FROM generation_items "
            "WHERE run_key = 'en-frequency-level-1' AND item_key = 'hola'"
        )
    ).scalar_one() == 1
