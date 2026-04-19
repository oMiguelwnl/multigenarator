"""Progress rendering and bounded retry tests."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.cli import build_generate_executor
from multilang.db.base import Base
from multilang.domain.jobs import GenerationRequest, JobStage, SupportedLanguage
from multilang.progress import ProgressRenderer
from multilang.repositories.job_repository import JobRepository
from multilang.services.generate_job import GenerateJobService
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


def test_progress_renderer_shows_stage_counters() -> None:
    renderer = ProgressRenderer()

    line = renderer.render_line(
        stage=JobStage.GENERATE_TEXT,
        completed_items=3,
        total_items=10,
        retrying_items=1,
        failed_items=2,
        skipped_duplicates=4,
    )

    assert "generate text" in line.lower()
    assert "generate_text" not in line
    assert "3/10" in line
    assert "retrying=1" in line
    assert "failed=2" in line
    assert "skipped_duplicates=4" in line


def test_executor_retries_once_then_marks_item_failed_and_continues(tmp_path: Path) -> None:
    repository, _ = build_repository()
    service = GenerateJobService(repository)
    request = GenerationRequest(
        language=SupportedLanguage.EN,
        source_type="word-list",
        input_file=write_word_list(tmp_path, "alpha", "beta"),
    )
    output: list[str] = []
    attempts: dict[str, int] = {}

    def process(item_key: str) -> None:
        attempts[item_key] = attempts.get(item_key, 0) + 1
        if item_key == "alpha":
            raise RuntimeError("boom")

    executor = build_generate_executor(
        service,
        settings=Settings(default_retry_attempts=2),
        item_processor=process,
        progress_sink=output.append,
    )

    result = executor(request)
    job = repository.get_job(result.job_id)

    assert job is not None
    assert attempts == {"alpha": 2, "beta": 1}
    assert job.completed_items == 1
    assert job.failed_items == 1
    assert any("retrying=1" in line for line in output)
    assert any("failed=1" in line for line in output)


def test_default_execution_path_uses_progress_counters_not_item_logs(tmp_path: Path) -> None:
    repository, _ = build_repository()
    service = GenerateJobService(repository)
    request = GenerationRequest(
        language=SupportedLanguage.EN,
        source_type="word-list",
        input_file=write_word_list(tmp_path, "alpha", "beta"),
    )
    output: list[str] = []

    executor = build_generate_executor(service, progress_sink=output.append)

    executor(request)

    assert output
    assert all("alpha" not in line and "beta" not in line for line in output)
    assert any("completed=" in line for line in output)
    assert any("retrying=" in line for line in output)
