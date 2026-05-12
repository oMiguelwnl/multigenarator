"""Coverage for the shipped CLI runtime bootstrap path."""

from __future__ import annotations

import json
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


def test_default_app_bootstraps_runtime_service(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "runtime.db"
    source = write_word_list(tmp_path, "alpha", "beta")
    lexicon_dir = write_lookup_index(tmp_path, "alpha", "beta")
    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))

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
    assert "grounded_candidates=2" in result.output
    assert "completed_items=2" in result.output

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
    lexicon_dir = write_lookup_index(tmp_path, "alpha")
    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))

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


def test_prepare_local_smoke_writes_english_words_and_index(tmp_path: Path) -> None:
    output_dir = tmp_path / "live-smoke-azure"

    result = runner.invoke(
        create_app(),
        [
            "prepare-local-smoke",
            "--output-dir",
            str(output_dir),
        ],
    )

    words_path = output_dir / "words.txt"
    index_path = output_dir / "lexicon" / "en" / "lexical-index.json"

    assert result.exit_code == 0
    assert words_path.read_text(encoding="utf-8") == "harbor\nlantern\nmeadow"
    assert index_path.exists()
    assert f"words={words_path}" in result.output
    assert f"index={index_path}" in result.output

    rows = json.loads(index_path.read_text(encoding="utf-8"))

    assert rows["harbor"]["definitions"] == ["a sheltered place where boats can anchor safely"]
    assert rows["lantern"]["definitions"] == ["a portable light protected by a transparent case"]
    assert rows["meadow"]["definitions"] == ["a field of grass and wildflowers"]
