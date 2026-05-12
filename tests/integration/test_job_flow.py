"""Shipped-app lifecycle smoke tests for job execution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from multilang.cli import build_generate_executor, create_app
from multilang.db.base import Base
from multilang.db.models import GenerationJob
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.repositories.job_repository import JobRepository
from multilang.services.generate_job import GenerateJobService
from multilang.services.input_fingerprint import build_run_key

runner = CliRunner()


def write_word_list(tmp_path: Path, *items: str) -> Path:
    path = tmp_path / "words.txt"
    path.write_text("\n".join(items), encoding="utf-8")
    return path


def write_lookup_index(tmp_path: Path, *terms: str) -> Path:
    index_path = tmp_path / "lexicon" / "en" / "lexical-index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(
            {
                term: {
                    "term": term,
                    "display_form": term,
                    "lemma": term,
                    "definitions": [f"definition for {term}"],
                    "ipa": f"/{term}/",
                    "source": "manual",
                }
                for term in terms
            }
        ),
        encoding="utf-8",
    )
    return index_path.parent.parent


def build_repository(database_path: Path) -> tuple[JobRepository, Session]:
    engine = create_engine(f"sqlite+pysqlite:///{database_path}")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return JobRepository(session), session


def test_shipped_app_supports_resume_and_duplicate_safe_rerun(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "job-flow.db"
    source = write_word_list(tmp_path, "alpha", "beta")
    lexicon_dir = write_lookup_index(tmp_path, "alpha", "beta")
    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))
    app = create_app()

    first_result = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "word-list", "--input-file", str(source)],
    )

    repository, session = build_repository(database_path)
    try:
        jobs = list(session.scalars(select(GenerationJob).order_by(GenerationJob.created_at)))
        assert len(jobs) == 1
        first_job = jobs[0]
        assert first_job.completed_items == 2

        request = GenerationRequest(
            language=SupportedLanguage.EN,
            source_type="word-list",
            input_file=source,
        )
        run_key = build_run_key(request, requested_item_keys=["alpha", "beta"])

        interrupted_repository, interrupted_session = build_repository(tmp_path / "resume.db")
        interrupted_service = GenerateJobService(interrupted_repository)
        interrupted_request = GenerationRequest(
            language=SupportedLanguage.EN,
            source_type="word-list",
            input_file=source,
        )

        def interrupted_processor(item_key: str) -> None:
            if item_key == "beta":
                raise KeyboardInterrupt("simulate interruption")

        interrupted_executor = build_generate_executor(
            interrupted_service,
            item_processor=interrupted_processor,
            progress_sink=lambda _: None,
        )

        with pytest.raises(KeyboardInterrupt):
            interrupted_executor(interrupted_request)

        interrupted_job = interrupted_repository.get_job(
            run_key=build_run_key(interrupted_request, requested_item_keys=["alpha", "beta"])
        )
        assert interrupted_job is not None
    finally:
        session.close()
        if 'interrupted_session' in locals():
            interrupted_session.close()

    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'resume.db'}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))
    resume_app = create_app()
    resume_result = runner.invoke(
        resume_app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "word-list",
            "--input-file",
            str(source),
            "--resume",
            interrupted_job.id,
        ],
    )

    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))
    rerun_result = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "word-list", "--input-file", str(source)],
    )
    overwrite_result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "word-list",
            "--input-file",
            str(source),
            "--overwrite",
            "--yes-overwrite",
        ],
    )

    assert "grounded_candidates=2" in first_result.output
    assert "completed_items=2" in first_result.output
    assert first_result.exit_code == 0
    assert run_key == first_job.run_key
    assert resume_result.exit_code == 0
    assert "resumed_from_job=" in resume_result.output
    assert "completed_items=2" in resume_result.output
    assert rerun_result.exit_code == 0
    assert "skipped_duplicates=2" in rerun_result.output
    assert overwrite_result.exit_code == 0
    assert "overwritten_items=2" in overwrite_result.output
