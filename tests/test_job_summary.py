"""Lifecycle summary tests for completed job runs."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.cli import build_generate_executor
from multilang.db.base import Base
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.repositories.job_repository import JobRepository
from multilang.services.generate_job import GenerateJobService
from multilang.services.job_summary import JobSummaryBuilder
from multilang.settings import Settings


def build_repository() -> tuple[JobRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return JobRepository(session), session


def write_word_list(tmp_path: Path, *items: str) -> Path:
    path = tmp_path / "words.txt"
    path.write_text("\n".join(items), encoding="utf-8")
    return path


def test_summary_lists_failed_items_after_retries(tmp_path: Path) -> None:
    repository, _ = build_repository()
    service = GenerateJobService(repository)
    builder = JobSummaryBuilder(repository)
    request = GenerationRequest(
        language=SupportedLanguage.EN,
        source_type="word-list",
        input_file=write_word_list(tmp_path, "alpha", "beta"),
    )

    def process(item_key: str) -> None:
        if item_key == "alpha":
            raise RuntimeError("boom")

    executor = build_generate_executor(
        service,
        settings=Settings(default_retry_attempts=2),
        item_processor=process,
        progress_sink=lambda _: None,
    )

    report = executor(request)
    summary = builder.build(report)

    assert summary.completed_items == 1
    assert summary.retried_items == 1
    assert len(summary.failed_items) == 1
    assert summary.failed_items[0].item_key == "alpha"
    assert summary.failed_items[0].retry_count == 2
    assert summary.failed_items[0].error == "boom"


def test_summary_includes_resumed_skipped_and_overwritten_counts(tmp_path: Path) -> None:
    repository, _ = build_repository()
    service = GenerateJobService(repository)
    builder = JobSummaryBuilder(repository)
    source = write_word_list(tmp_path, "alpha", "beta")

    start_request = GenerationRequest(
        language=SupportedLanguage.EN,
        source_type="word-list",
        input_file=source,
    )
    first_executor = build_generate_executor(service, progress_sink=lambda _: None)
    first_report = first_executor(start_request)

    resume_request = GenerationRequest(
        language=SupportedLanguage.EN,
        source_type="word-list",
        input_file=source,
        resume_job_id=first_report.job_id,
    )
    resume_report = first_executor(resume_request)
    resume_summary = builder.build(resume_report)

    overwrite_request = GenerationRequest(
        language=SupportedLanguage.EN,
        source_type="word-list",
        input_file=source,
        overwrite=True,
        yes_overwrite=True,
    )
    overwrite_report = first_executor(overwrite_request)
    overwrite_summary = builder.build(overwrite_report)

    assert resume_summary.resumed_from_job == first_report.job_id
    assert resume_summary.skipped_duplicates == 2
    assert resume_summary.overwritten_items == 0
    assert overwrite_summary.resumed_from_job is None
    assert overwrite_summary.skipped_duplicates == 0
    assert overwrite_summary.overwritten_items == 2
