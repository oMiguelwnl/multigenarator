"""Integration coverage for the shipped Phase 3 text runtime path."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.db.models import GenerationJob, TextQualityRecordModel
from multilang.runtime import build_runtime_service
from multilang.settings import Settings

runner = CliRunner()


def write_word_list(tmp_path: Path, *items: str) -> Path:
    path = tmp_path / "words.txt"
    path.write_text("\n".join(items), encoding="utf-8")
    return path


def write_lookup_index(tmp_path: Path, *terms: str, language_code: str = "en") -> Path:
    index_path = tmp_path / "lexicon" / language_code / "kaikki-index.json"
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


def test_generate_command_regenerates_one_flagged_item_without_full_rerun(tmp_path: Path) -> None:
    database_path = tmp_path / "text-runtime.db"
    lexicon_dir = write_lookup_index(tmp_path, "alpha", "flag-beta")
    source = write_word_list(tmp_path, "alpha", "flag-beta")
    service = build_runtime_service(
        Settings(
            database_url=f"sqlite+pysqlite:///{database_path}",
            lexicon_data_dir=lexicon_dir,
            tatoeba_enabled=False,
        )
    )
    app = create_app(service=service)
    review_report = tmp_path / "review.json"

    first_result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "word-list",
            "--input-file",
            str(source),
            "--review-report-file",
            str(review_report),
        ],
    )

    session = Session(create_engine(f"sqlite+pysqlite:///{database_path}"))
    try:
        job = session.scalar(select(GenerationJob))
        assert job is not None
        assert session.scalar(select(func.count()).select_from(GenerationJob)) == 1
        assert session.scalar(select(func.count()).select_from(TextQualityRecordModel)) == 2

        alpha_before = session.scalar(
            select(TextQualityRecordModel).where(TextQualityRecordModel.item_key == "alpha")
        )
        flagged_before = session.scalar(
            select(TextQualityRecordModel).where(TextQualityRecordModel.item_key == "flag-beta")
        )
        assert alpha_before is not None
        assert flagged_before is not None
        alpha_id = alpha_before.id
        alpha_sentence = alpha_before.example_sentence
        flagged_id = flagged_before.id
        flagged_sentence = flagged_before.example_sentence

        second_result = runner.invoke(
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
                "--regenerate-item-key",
                "flag-beta",
                "--review-report-file",
                str(review_report),
            ],
        )

        assert second_result.exit_code == 0
        assert "text_processed_items=1" in second_result.output
        assert "review_required_text_items=1" in second_result.output
        session.expire_all()
        assert session.scalar(select(func.count()).select_from(GenerationJob)) == 1
        assert session.scalar(select(func.count()).select_from(TextQualityRecordModel)) == 2

        alpha_after = session.scalar(
            select(TextQualityRecordModel).where(TextQualityRecordModel.item_key == "alpha")
        )
        flagged_after = session.scalar(
            select(TextQualityRecordModel).where(TextQualityRecordModel.item_key == "flag-beta")
        )
        assert alpha_after is not None
        assert flagged_after is not None
        assert alpha_after.id == alpha_id
        assert alpha_after.example_sentence == alpha_sentence
        assert flagged_after.id == flagged_id
        assert flagged_after.example_sentence == flagged_sentence
        assert flagged_after.review_status == "review_required"
    finally:
        session.close()

    assert first_result.exit_code == 0
    assert "accepted_text_items=1" in first_result.output
    assert "review_required_text_items=1" in first_result.output
    assert review_report.exists()


def test_generate_command_skips_pending_groundings_during_text_generation(tmp_path: Path) -> None:
    database_path = tmp_path / "mixed-runtime.db"
    lexicon_dir = write_lookup_index(tmp_path, "alpha")
    source = write_word_list(tmp_path, "alpha", "unknown-term")
    service = build_runtime_service(
        Settings(
            database_url=f"sqlite+pysqlite:///{database_path}",
            lexicon_data_dir=lexicon_dir,
            tatoeba_enabled=False,
        )
    )
    app = create_app(service=service)

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
    assert "grounded_candidates=1" in result.output
    assert "pending_groundings=1" in result.output
    assert "text_processed_items=1" in result.output
    assert "accepted_text_items=1" in result.output

    session = Session(create_engine(f"sqlite+pysqlite:///{database_path}"))
    try:
        assert session.scalar(select(func.count()).select_from(GenerationJob)) == 1
        assert session.scalar(select(func.count()).select_from(TextQualityRecordModel)) == 1
        generated = session.scalar(select(TextQualityRecordModel))
        assert generated is not None
        assert generated.item_key == "alpha"
    finally:
        session.close()


def test_generate_command_uses_requested_sentence_and_translation_languages(tmp_path: Path) -> None:
    database_path = tmp_path / "spanish-runtime.db"
    lexicon_dir = write_lookup_index(tmp_path, "usar", language_code="es")
    source = write_word_list(tmp_path, "usar")
    service = build_runtime_service(
        Settings(
            database_url=f"sqlite+pysqlite:///{database_path}",
            lexicon_data_dir=lexicon_dir,
            tatoeba_enabled=False,
        )
    )
    app = create_app(service=service)

    result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "es",
            "--source",
            "word-list",
            "--input-file",
            str(source),
        ],
    )

    assert result.exit_code == 0
    assert "accepted_text_items=1" in result.output

    session = Session(create_engine(f"sqlite+pysqlite:///{database_path}"))
    try:
        generated = session.scalar(select(TextQualityRecordModel))
        assert generated is not None
        assert generated.example_sentence == "Yo uso usar cada día."
        assert generated.translation_text == "I use this every day."
    finally:
        session.close()
