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


def write_highlight_export(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "highlights.txt"
    path.write_text(f"Synthetic Learner Reader\n- Your Highlight at Location 1\n{text}\n==========", encoding="utf-8")
    return path


def write_lookup_index(tmp_path: Path, *terms: str, language_code: str = "en") -> Path:
    index_path = tmp_path / "lexicon" / language_code / "lexical-index.json"
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


def test_generate_resume_missing_only_skips_existing_review_rows(tmp_path: Path) -> None:
    database_path = tmp_path / "missing-only-runtime.db"
    lexicon_dir = write_lookup_index(tmp_path, "alpha", "flag-beta", "gamma")
    source = write_word_list(tmp_path, "alpha", "flag-beta")
    service = build_runtime_service(
        Settings(
            database_url=f"sqlite+pysqlite:///{database_path}",
            lexicon_data_dir=lexicon_dir,
            tatoeba_enabled=False,
        )
    )
    app = create_app(service=service)

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
        ],
    )

    session = Session(create_engine(f"sqlite+pysqlite:///{database_path}"))
    try:
        job = session.scalar(select(GenerationJob))
        assert job is not None
        flagged_before = session.scalar(
            select(TextQualityRecordModel).where(TextQualityRecordModel.item_key == "flag-beta")
        )
        assert flagged_before is not None
        flagged_id = flagged_before.id
        flagged_sentence = flagged_before.example_sentence

        source.write_text("alpha\nflag-beta\ngamma", encoding="utf-8")
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
                "--missing-only",
            ],
        )

        assert first_result.exit_code == 0
        assert second_result.exit_code == 0
        assert "text_processed_items=1" in second_result.output
        assert "accepted_text_items=1" in second_result.output
        assert "review_required_text_items=0" in second_result.output
        session.expire_all()
        assert session.scalar(select(func.count()).select_from(TextQualityRecordModel)) == 3

        flagged_after = session.scalar(
            select(TextQualityRecordModel).where(TextQualityRecordModel.item_key == "flag-beta")
        )
        gamma = session.scalar(
            select(TextQualityRecordModel).where(TextQualityRecordModel.item_key == "gamma")
        )
        assert flagged_after is not None
        assert gamma is not None
        assert flagged_after.id == flagged_id
        assert flagged_after.example_sentence == flagged_sentence
        assert flagged_after.review_status == "review_required"
        assert gamma.review_status == "accepted"
    finally:
        session.close()


def test_generate_resume_missing_only_respects_max_items(tmp_path: Path) -> None:
    database_path = tmp_path / "missing-only-max-items-runtime.db"
    lexicon_dir = write_lookup_index(tmp_path, "alpha", "flag-beta", "gamma", "delta", "epsilon")
    source = write_word_list(tmp_path, "alpha", "flag-beta")
    service = build_runtime_service(
        Settings(
            database_url=f"sqlite+pysqlite:///{database_path}",
            lexicon_data_dir=lexicon_dir,
            tatoeba_enabled=False,
        )
    )
    app = create_app(service=service)

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
        ],
    )

    session = Session(create_engine(f"sqlite+pysqlite:///{database_path}"))
    try:
        job = session.scalar(select(GenerationJob))
        assert job is not None
        source.write_text("alpha\nflag-beta\ngamma\ndelta\nepsilon", encoding="utf-8")

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
                "--missing-only",
                "--max-items",
                "2",
            ],
        )

        assert first_result.exit_code == 0
        assert second_result.exit_code == 0
        assert "text_processed_items=2" in second_result.output
        assert "accepted_text_items=2" in second_result.output
        assert "review_required_text_items=0" in second_result.output
        session.expire_all()
        assert session.scalar(select(func.count()).select_from(TextQualityRecordModel)) == 4
        generated_keys = session.scalars(
            select(TextQualityRecordModel.item_key).order_by(TextQualityRecordModel.item_key.asc())
        ).all()
        assert generated_keys == ["alpha", "delta", "epsilon", "flag-beta"]
    finally:
        session.close()


def test_generate_text_progress_reports_counters_without_private_content(tmp_path: Path) -> None:
    database_path = tmp_path / "highlight-progress-runtime.db"
    lexicon_dir = write_lookup_index(tmp_path, "meadow")
    private_highlight = "The meadow keeps a lantern beside a private cottage"
    source = write_highlight_export(tmp_path, private_highlight)
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
            "highlights",
            "--input-file",
            str(source),
        ],
    )

    assert result.exit_code == 0
    assert "stage=generate_text" in result.output
    assert "processed_this_run=1" in result.output
    assert "accepted_this_run=1" in result.output
    assert "review_this_run=0" in result.output
    assert "remaining_missing=0" in result.output
    assert "last_item_key=" in result.output
    assert "elapsed_seconds=" in result.output
    assert private_highlight not in result.output
    assert "private cottage" not in result.output
    assert "Readers notice" not in result.output


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


def test_generate_command_uses_requested_language_for_manual_word_list_text(tmp_path: Path) -> None:
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
    assert "accepted_text_items=0" in result.output
    assert "review_required_text_items=1" in result.output

    session = Session(create_engine(f"sqlite+pysqlite:///{database_path}"))
    try:
        generated = session.scalar(select(TextQualityRecordModel))
        assert generated is not None
        assert generated.review_status == "review_required"
        assert generated.review_reason == "banned_pattern"
        assert "usar" in generated.example_sentence.casefold()
        assert not generated.example_sentence.casefold().startswith(("la palabra", "the word"))
        assert generated.translation_text
        assert generated.translation_text == generated.example_sentence
    finally:
        session.close()
