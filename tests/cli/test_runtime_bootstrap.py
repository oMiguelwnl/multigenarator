"""Coverage for the shipped CLI runtime bootstrap path."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from multilang.cli import app, create_app
from multilang.db.models import GenerationJob

runner = CliRunner()


def write_word_list(tmp_path: Path, *items: str) -> Path:
    path = tmp_path / "words.txt"
    path.write_text("\n".join(items), encoding="utf-8")
    return path


def test_default_app_bootstraps_runtime_service(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "runtime.db"
    source = write_word_list(tmp_path, "alpha", "beta")
    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")

    result = runner.invoke(
        create_app(),
        [
            "generate",
            "--language",
            "en",
            "--source",
            "word-list",
            "--input-file",
            str(source),
        ],
    )

    assert result.exit_code == 0
    assert "stage=ingest" in result.output

    session = Session(create_engine(f"sqlite+pysqlite:///{database_path}"))
    try:
        jobs = list(session.scalars(select(GenerationJob)))
    finally:
        session.close()

    assert len(jobs) == 1
    assert jobs[0].total_items == 2


def test_module_level_app_honors_runtime_database_override(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "module-app.db"
    source = write_word_list(tmp_path, "alpha")
    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")

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
        ],
    )

    assert result.exit_code == 0
    assert database_path.exists()
