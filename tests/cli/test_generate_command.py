"""CLI tests for the generate command."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.db.base import Base
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.repositories.job_repository import JobRepository
from multilang.services.generate_job import GenerateJobService
from multilang.services.input_fingerprint import build_run_key

runner = CliRunner()


def build_service() -> tuple[GenerateJobService, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return GenerateJobService(JobRepository(session)), session


def write_word_list(tmp_path: Path, *items: str) -> Path:
    path = tmp_path / "words.txt"
    path.write_text("\n".join(items), encoding="utf-8")
    return path


def test_generate_command_rejects_unsupported_language() -> None:
    app = create_app()

    result = runner.invoke(
        app,
        ["generate", "--language", "it", "--source", "frequency", "--level", "1"],
    )

    assert result.exit_code != 0
    assert "Invalid value for '--language'" in result.output


def test_frequency_source_requires_level() -> None:
    app = create_app()

    result = runner.invoke(app, ["generate", "--language", "en", "--source", "frequency"])

    assert result.exit_code != 0
    assert "--level is required when --source frequency" in result.output


def test_word_list_source_requires_input_file() -> None:
    app = create_app()

    result = runner.invoke(app, ["generate", "--language", "en", "--source", "word-list"])

    assert result.exit_code != 0
    assert "--input-file is required when --source word-list" in result.output


def test_overwrite_requires_explicit_confirmation() -> None:
    app = create_app(conflict_checker=lambda _: True)

    result = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "frequency", "--level", "1", "--overwrite"],
        input="n\n",
    )

    assert result.exit_code == 1
    assert "Overwrite and reprocess" in result.output


def test_yes_overwrite_allows_non_interactive_confirmation() -> None:
    called = False

    def execute(_: object) -> None:
        nonlocal called
        called = True

    app = create_app(conflict_checker=lambda _: True, generate_executor=execute)

    result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "frequency",
            "--level",
            "1",
            "--overwrite",
            "--yes-overwrite",
        ],
    )

    assert result.exit_code == 0
    assert called is True


def test_generate_command_prints_runtime_summary_and_duplicate_counts(tmp_path: Path) -> None:
    service, session = build_service()
    app = create_app(service=service)
    source = write_word_list(tmp_path, "alpha", "beta")

    first_result = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "word-list", "--input-file", str(source)],
    )
    rerun_result = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "word-list", "--input-file", str(source)],
    )

    session.close()

    assert first_result.exit_code == 0
    assert "stage=ingest" in first_result.output
    assert "completed_items=2" in first_result.output
    assert "retried_items=0" in first_result.output
    assert "failed_items=0" in first_result.output
    assert "skipped_duplicates=0" in first_result.output
    assert rerun_result.exit_code == 0
    assert "skipped_duplicates=2" in rerun_result.output


def test_generate_command_aborts_on_inconsistent_resume_state(tmp_path: Path) -> None:
    service, session = build_service()
    app = create_app(service=service)
    source = write_word_list(tmp_path, "alpha", "beta")
    request = GenerationRequest(
        language=SupportedLanguage.EN,
        source_type="word-list",
        input_file=source,
    )
    runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "word-list", "--input-file", str(source)],
    )
    job = service.repository.get_job(
        run_key=build_run_key(request, requested_item_keys=["alpha", "beta"])
    )
    assert job is not None
    job.completed_items = 99
    session.add(job)
    session.commit()

    result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "word-list",
            "--input-file",
            str(source),
            "--resume",
            job.id,
        ],
    )

    session.close()

    assert result.exit_code == 1
    assert "persisted resume state is inconsistent" in result.output
