"""Coverage for the shipped CLI runtime bootstrap path."""

from __future__ import annotations

import gzip
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
    index_path = tmp_path / "lexicon" / "en" / "kaikki-index.json"
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
                    "source": "kaikki",
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


def test_prepare_local_smoke_writes_english_archive_words_and_index(tmp_path: Path) -> None:
    output_dir = tmp_path / "live-smoke-azure"

    result = runner.invoke(
        create_app(),
        [
            "prepare-local-smoke",
            "--output-dir",
            str(output_dir),
        ],
    )

    archive_path = output_dir / "kaikki-en.jsonl.gz"
    words_path = output_dir / "words.txt"
    index_path = output_dir / "lexicon" / "en" / "kaikki-index.json"

    assert result.exit_code == 0
    assert archive_path.exists()
    assert words_path.read_text(encoding="utf-8") == "harbor\nlantern\nmeadow"
    assert index_path.exists()
    assert f"archive={archive_path}" in result.output
    assert f"words={words_path}" in result.output
    assert f"index={index_path}" in result.output

    with gzip.open(archive_path, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]

    assert rows == [
        {
            "word": "harbor",
            "lang_code": "en",
            "senses": [{"glosses": ["a sheltered place where boats can anchor safely"]}],
            "sounds": [{"ipa": "/ˈhɑrbər/"}],
        },
        {
            "word": "lantern",
            "lang_code": "en",
            "senses": [{"glosses": ["a portable light protected by a transparent case"]}],
            "sounds": [{"ipa": "/ˈlæntərn/"}],
        },
        {
            "word": "meadow",
            "lang_code": "en",
            "senses": [{"glosses": ["a field of grass and wildflowers"]}],
            "sounds": [{"ipa": "/ˈmɛdoʊ/"}],
        },
    ]
