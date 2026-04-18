"""Service tests for start/resume/rerun orchestration."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.jobs import GenerationRequest, JobStage, JobStatus, SupportedLanguage
from multilang.repositories.job_repository import JobRepository
from multilang.services.generate_job import GenerateJobService
from multilang.services.input_fingerprint import build_run_key


def build_repository() -> tuple[JobRepository, Session]:
    from sqlalchemy import create_engine

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return JobRepository(session), session


def make_frequency_request() -> GenerationRequest:
    return GenerationRequest(language=SupportedLanguage.EN, source_type="frequency", level=1)


def make_word_list_request() -> GenerationRequest:
    return GenerationRequest(
        language=SupportedLanguage.EN,
        source_type="word-list",
        input_file=Path("words.txt"),
    )


def test_start_builds_deterministic_run_key() -> None:
    repository, _ = build_repository()
    service = GenerateJobService(repository)
    request = make_word_list_request()

    result = service.start(request, requested_item_keys=[" Hola ", "adios", "hola"])

    assert result.mode == "start"
    assert result.run_key == build_run_key(request, requested_item_keys=["hola", "adios"])
    assert result.pending_item_keys == ["adios", "hola"]


def test_resume_reuses_completed_items() -> None:
    repository, session = build_repository()
    service = GenerateJobService(repository)
    request = make_frequency_request()
    run_key = build_run_key(request, requested_item_keys=["hola", "adios"])
    job = repository.create_job(
        request=request,
        run_key=run_key,
        source_fingerprint="level:1",
        total_items=2,
        current_stage=JobStage.ENRICH,
        last_completed_stage=JobStage.INGEST,
        status=JobStatus.RUNNING,
    )
    repository.record_item_success(job.id, item_key="hola", completed_stage=JobStage.INGEST)
    job.current_stage = JobStage.ENRICH.value
    session.add(job)
    session.commit()

    result = service.resume(job.id, requested_item_keys=["hola", "adios"])

    assert result.mode == "resume"
    assert result.resume_from_stage == JobStage.ENRICH
    assert result.pending_item_keys == ["adios"]
    assert result.skipped_item_keys == ["hola"]
    assert result.diagnostic is None


def test_resume_stops_on_inconsistent_persisted_state() -> None:
    repository, session = build_repository()
    service = GenerateJobService(repository)
    request = make_frequency_request()
    job = repository.create_job(
        request=request,
        run_key=build_run_key(request, requested_item_keys=["hola", "adios"]),
        source_fingerprint="level:1",
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

    result = service.resume(job.id, requested_item_keys=["hola", "adios"])

    assert result.mode == "resume"
    assert result.pending_item_keys == []
    assert result.skipped_item_keys == []
    assert result.diagnostic is not None
    assert result.diagnostic.reason == "persisted resume state is inconsistent"


def test_rerun_skips_duplicates_by_default() -> None:
    repository, _ = build_repository()
    service = GenerateJobService(repository)
    request = make_frequency_request()
    initial = service.start(request, requested_item_keys=["hola", "adios"])
    repository.record_item_success(initial.job_id, item_key="hola", completed_stage=JobStage.INGEST)

    result = service.start(request, requested_item_keys=["hola", "adios"])

    assert result.mode == "rerun"
    assert result.pending_item_keys == ["adios"]
    assert result.skipped_item_keys == ["hola"]
    assert result.resume_from_stage == JobStage.INGEST
