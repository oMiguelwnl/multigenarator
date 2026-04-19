"""Repository-backed lifecycle smoke tests for job execution."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from multilang.cli import build_generate_executor, create_app
from multilang.db.base import Base
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.repositories.job_repository import JobRepository
from multilang.services.generate_job import GenerateJobService
from multilang.services.job_summary import JobSummaryBuilder

runner = CliRunner()


def build_repository() -> tuple[JobRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return JobRepository(session), session


def write_word_list(tmp_path: Path, *items: str) -> Path:
    path = tmp_path / "words.txt"
    path.write_text("\n".join(items), encoding="utf-8")
    return path


def test_job_flow_supports_resume_and_duplicate_safe_rerun(tmp_path: Path) -> None:
    repository, _ = build_repository()
    service = GenerateJobService(repository)
    builder = JobSummaryBuilder(repository)
    source = write_word_list(tmp_path, "alpha", "beta")
    attempts: list[str] = []

    def interrupted_processor(item_key: str) -> None:
        attempts.append(item_key)
        if item_key == "beta":
            raise KeyboardInterrupt("simulate interruption")

    start_request = GenerationRequest(
        language=SupportedLanguage.EN,
        source_type="word-list",
        input_file=source,
    )
    interrupted_executor = build_generate_executor(
        service,
        item_processor=interrupted_processor,
        progress_sink=lambda _: None,
    )

    with pytest.raises(KeyboardInterrupt):
        interrupted_executor(start_request)

    original_job = repository.get_job(run_key=service.start(start_request, requested_item_keys=["alpha", "beta"]).run_key)
    assert original_job is not None
    assert original_job.completed_items == 1

    resumed_items: list[str] = []
    resume_request = GenerationRequest(
        language=SupportedLanguage.EN,
        source_type="word-list",
        input_file=source,
        resume_job_id=original_job.id,
    )
    resume_executor = build_generate_executor(
        service,
        item_processor=resumed_items.append,
        progress_sink=lambda _: None,
    )
    resume_report = resume_executor(resume_request)
    resume_summary = builder.build(resume_report)

    assert resumed_items == ["beta"]
    assert resume_summary.resumed_from_job == original_job.id
    assert resume_summary.skipped_duplicates == 1

    rerun_report = resume_executor(start_request)
    rerun_summary = builder.build(rerun_report)

    assert rerun_report.orchestration.pending_item_keys == []
    assert rerun_summary.skipped_duplicates == 2

    app = create_app(service=service, conflict_checker=lambda _: True)
    denied = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "word-list", "--input-file", str(source), "--overwrite"],
        input="n\n",
    )
    assert denied.exit_code == 1

    overwrite_request = GenerationRequest(
        language=SupportedLanguage.EN,
        source_type="word-list",
        input_file=source,
        overwrite=True,
        yes_overwrite=True,
    )
    overwrite_report = resume_executor(overwrite_request)
    overwrite_summary = builder.build(overwrite_report)

    assert overwrite_summary.overwritten_items == 2
