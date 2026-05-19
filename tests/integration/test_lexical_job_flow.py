"""Integration tests for lexical job flow in the shipped CLI path."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

import multilang.cli as cli_module
from multilang.cli import create_app
from multilang.db.base import Base
from multilang.db.models import GenerationJob, LexicalCandidate
from multilang.runtime import RuntimeGenerateService, RuntimeTextResult

runner = CliRunner()


def build_session(database_path: str) -> Session:
    """Build a session against the test database."""

    engine = create_engine(f"sqlite+pysqlite:///{database_path}")
    Base.metadata.create_all(engine)
    return Session(engine)


def write_word_list(tmp_path: Path, *items: str) -> Path:
    """Write a word list file for testing."""

    path = tmp_path / "words.txt"
    path.write_text("\n".join(items), encoding="utf-8")
    return path


def write_lookup_index(tmp_path: Path, *, language_code: str, terms: list[str]) -> Path:
    """Write a small cached lexical index for runtime lookups."""

    index_path = tmp_path / "lexicon" / language_code / "lexical-index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
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
    index_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return index_path.parent.parent


def skip_runtime_text_generation(monkeypatch) -> None:
    monkeypatch.setattr(
        RuntimeGenerateService,
        "generate_text",
        lambda self, *, job_id, deck_language, missing_only=False, max_items=None, progress_callback=None, rate_limiter=None: RuntimeTextResult(
            processed_items=0,
            accepted_items=0,
            review_required_items=0,
        ),
    )


def test_generate_frequency_deck_persists_three_grounded_levels(monkeypatch, tmp_path: Path) -> None:
    """Default frequency runs persist 1000 grounded candidates in each level."""

    database_path = str(tmp_path / "lexical-flow.db")
    missing_ranks = {17, 1013, 2400, 2600}
    all_terms = [f"word-{rank}" for rank in range(1, 3005) if rank not in missing_ranks]
    lexicon_dir = write_lookup_index(tmp_path, language_code="en", terms=all_terms)

    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))
    skip_runtime_text_generation(monkeypatch)

    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: (
            (rank, f"word-{rank}") for rank in range(1, 3010)
        ),
    )

    app = create_app()
    result = runner.invoke(app, ["generate", "--language", "en", "--source", "frequency"])

    assert result.exit_code == 0
    assert "grounded_candidates=3000" in result.output
    assert "level_1_candidates=1000" in result.output
    assert "level_2_candidates=1000" in result.output
    assert "level_3_candidates=1000" in result.output
    assert "pending_groundings=0" in result.output
    assert "backfilled_candidates=4" in result.output

    session = build_session(database_path)
    try:
        job = session.scalar(select(GenerationJob).order_by(GenerationJob.created_at))
        assert job is not None

        counts = {
            level: session.scalar(
                select(func.count(LexicalCandidate.id)).where(
                    LexicalCandidate.job_id == job.id,
                    LexicalCandidate.frequency_level == level,
                    LexicalCandidate.grounding_status == "grounded",
                )
            )
            for level in (1, 2, 3)
        }
        assert counts == {1: 1000, 2: 1000, 3: 1000}
    finally:
        session.close()


def test_generate_frequency_deck_uses_manual_lexicon_cache(monkeypatch, tmp_path: Path) -> None:
    database_path = str(tmp_path / "manual-cache-flow.db")
    all_terms = [f"word-{rank}" for rank in range(1, 3001)]
    lexicon_dir = write_lookup_index(tmp_path, language_code="en", terms=all_terms)

    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))
    skip_runtime_text_generation(monkeypatch)

    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: ((rank, f"word-{rank}") for rank in range(1, 3001)),
    )

    app = create_app()
    result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "frequency",
        ],
    )

    assert result.exit_code == 0
    assert "grounded_candidates=3000" in result.output
    assert (lexicon_dir / "en" / "lexical-index.json").exists()


def test_generate_frequency_deck_persists_custom_cards_per_level(monkeypatch, tmp_path: Path) -> None:
    database_path = str(tmp_path / "custom-frequency-count.db")
    all_terms = [f"word-{rank}" for rank in range(1, 3010)]
    lexicon_dir = write_lookup_index(tmp_path, language_code="en", terms=all_terms)

    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))

    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: ((rank, f"word-{rank}") for rank in range(1, 3010)),
    )

    app = create_app()
    result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "frequency",
            "--cards-per-level",
            "7",
        ],
    )

    assert result.exit_code == 0
    assert "grounded_candidates=21" in result.output
    assert "level_1_candidates=7" in result.output
    assert "level_2_candidates=7" in result.output
    assert "level_3_candidates=7" in result.output

    session = build_session(database_path)
    try:
        job = session.scalar(select(GenerationJob).order_by(GenerationJob.created_at))
        assert job is not None

        counts = {
            level: session.scalar(
                select(func.count(LexicalCandidate.id)).where(
                    LexicalCandidate.job_id == job.id,
                    LexicalCandidate.frequency_level == level,
                    LexicalCandidate.grounding_status == "grounded",
                )
            )
            for level in (1, 2, 3)
        }
        assert counts == {1: 7, 2: 7, 3: 7}
    finally:
        session.close()


def test_generate_frequency_deck_can_run_without_lexicon_data(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = str(tmp_path / "frequency-without-lexicon.db")
    lexicon_dir = tmp_path / "lexicon"
    lexicon_dir.mkdir()

    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))
    skip_runtime_text_generation(monkeypatch)

    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: (
            (rank, f"word-{rank}")
            for rank in [1, 2, 3, 1001, 1002, 1003, 2001, 2002, 2003]
        ),
    )

    app = create_app()
    result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "frequency",
            "--cards-per-level",
            "3",
        ],
    )

    assert result.exit_code == 0
    assert "grounded_candidates=9" in result.output
    assert "pending_groundings=0" in result.output
    assert not (lexicon_dir / "en" / "lexical-index.json").exists()

    session = build_session(database_path)
    try:
        job_count = session.scalar(select(func.count(GenerationJob.id)))
        candidate_count = session.scalar(select(func.count(LexicalCandidate.id)))

        assert job_count == 1
        assert candidate_count == 9
    finally:
        session.close()


def test_custom_word_list_preserves_pending_items(monkeypatch, tmp_path: Path) -> None:
    """Custom word-list runs preserve grounded and pending items across reruns and resume."""

    database_path = str(tmp_path / "custom-list.db")
    lexicon_dir = write_lookup_index(tmp_path, language_code="en", terms=["hello", "world", "test"])
    source = write_word_list(tmp_path, "hello", "", "world", "xyzqwe", "test")

    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))

    app = create_app()
    first_result = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "word-list", "--input-file", str(source)],
    )

    assert first_result.exit_code == 0
    assert "grounded_candidates=3" in first_result.output
    assert "pending_groundings=1" in first_result.output
    assert "rejected_rows=1" in first_result.output

    session = build_session(database_path)
    try:
        job = session.scalar(select(GenerationJob).order_by(GenerationJob.created_at))
        assert job is not None

        total_candidates = session.scalar(
            select(func.count(LexicalCandidate.id)).where(LexicalCandidate.job_id == job.id)
        )
        grounded_count = session.scalar(
            select(func.count(LexicalCandidate.id)).where(
                LexicalCandidate.job_id == job.id,
                LexicalCandidate.grounding_status == "grounded",
            )
        )
        pending_count = session.scalar(
            select(func.count(LexicalCandidate.id)).where(
                LexicalCandidate.job_id == job.id,
                LexicalCandidate.grounding_status == "pending",
            )
        )

        assert total_candidates == 4
        assert grounded_count == 3
        assert pending_count == 1

        rerun_result = runner.invoke(
            app,
            ["generate", "--language", "en", "--source", "word-list", "--input-file", str(source)],
        )
        resume_result = runner.invoke(
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

        assert rerun_result.exit_code == 0
        assert "grounded_candidates=3" in rerun_result.output
        assert "pending_groundings=1" in rerun_result.output

        assert resume_result.exit_code == 0
        assert "grounded_candidates=3" in resume_result.output
        assert "pending_groundings=1" in resume_result.output
        assert f"resumed_from_job={job.id}" in resume_result.output

        total_after_resume = session.scalar(
            select(func.count(LexicalCandidate.id)).where(LexicalCandidate.job_id == job.id)
        )
        assert total_after_resume == 4
    finally:
        session.close()
