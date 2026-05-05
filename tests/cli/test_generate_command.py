"""CLI tests for the generate command."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import ClassVar

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.db.base import Base
from multilang.services.audio_synthesis import AudioSynthesisAdapter, AudioSynthesisResponse
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.db.models import AudioAssetModel, GenerationJob
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.lexical_repository import LexicalRepository
import multilang.runtime as runtime_module
from multilang.runtime import build_runtime_service
from multilang.services.generate_job import GenerateJobService
from multilang.services.input_fingerprint import build_run_key
from multilang.services.ingest_lexical_items import IngestLexicalItemsService
from multilang.services.kaikki_lookup import KaikkiRecord
from multilang.services.lexical_grounding import LexicalGroundingService
from multilang.services.text_review import ReviewReport, ReviewReportItem
from multilang.settings import Settings

runner = CliRunner()


class FileWritingAudioAdapter(AudioSynthesisAdapter):
    def available_voice_ids(self) -> set[str] | None:
        return None

    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
    ) -> AudioSynthesisResponse:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = f"{voice_id}:{locale}:{audio_format}:{ssml_text}".encode("utf-8")
        output_path.write_bytes(payload)
        return AudioSynthesisResponse(storage_path=output_path, byte_size=len(payload), duration_ms=800)


class FakeAzureSpeechAdapter(AudioSynthesisAdapter):
    instances: ClassVar[list[FakeAzureSpeechAdapter]] = []
    available_ids: ClassVar[set[str] | None] = None

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.calls: list[Path] = []
        type(self).instances.append(self)

    def available_voice_ids(self) -> set[str] | None:
        return None if self.available_ids is None else set(self.available_ids)

    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
    ) -> AudioSynthesisResponse:
        self.calls.append(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = b"ID3" + f":{voice_id}:{locale}:{audio_format}:{ssml_text}".encode("utf-8")
        output_path.write_bytes(payload)
        return AudioSynthesisResponse(storage_path=output_path, byte_size=len(payload), duration_ms=800)


def build_service() -> tuple[GenerateJobService, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return GenerateJobService(JobRepository(session)), session


class StubLookup:
    def __init__(self, mapping: dict[str, KaikkiRecord]) -> None:
        self._mapping = mapping

    def lookup(self, *, language_code: str, term: str) -> KaikkiRecord | None:
        return self._mapping.get(term.casefold())


def build_ingest_service(*, lookup_terms: list[str]) -> tuple[IngestLexicalItemsService, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    lookup = StubLookup(
        {
            term.casefold(): KaikkiRecord(
                term=term,
                display_form=term,
                lemma=term,
                definitions=[f"definition for {term}"],
                ipa=f"/{term}/",
            )
            for term in lookup_terms
        }
    )
    service = IngestLexicalItemsService(
        job_service=GenerateJobService(JobRepository(session)),
        lexical_repo=LexicalRepository(session),
        grounding_service=LexicalGroundingService(lookup),
    )
    return service, session


def write_word_list(tmp_path: Path, *items: str) -> Path:
    path = tmp_path / "words.txt"
    path.write_text("\n".join(items), encoding="utf-8")
    return path


def write_kaikki_archive(path: Path, rows: list[dict[str, object]]) -> Path:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")
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


def test_generate_command_rejects_unsupported_language() -> None:
    app = create_app()

    result = runner.invoke(
        app,
        ["generate", "--language", "sv", "--source", "frequency", "--level", "1"],
    )

    assert result.exit_code != 0
    assert "Invalid value for '--language'" in result.output


def test_word_list_source_requires_input_file() -> None:
    app = create_app()

    result = runner.invoke(app, ["generate", "--language", "en", "--source", "word-list"])

    assert result.exit_code != 0
    assert "--input-file is required when --source word-list" in result.output


def test_word_list_source_rejects_frequency_only_flags(tmp_path: Path) -> None:
    app = create_app()
    source = write_word_list(tmp_path, "alpha")

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
            "--test-mode",
        ],
    )

    assert result.exit_code != 0
    assert "--test-mode is only valid when --source frequency" in result.output


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


def test_generate_command_prints_review_report_for_flagged_text_rows(tmp_path: Path) -> None:
    service, session = build_service()
    source = write_word_list(tmp_path, "alpha")
    report_path = tmp_path / "flagged-review.json"

    def build_review_report(*, job_id: str, output_path: Path | None) -> ReviewReport:
        path = output_path or report_path
        path.write_text('{"job_id": "job-1", "item_count": 2}\n', encoding="utf-8")
        return ReviewReport(
            job_id=job_id,
            item_count=2,
            items=[
                ReviewReportItem(
                    confidence_label="low",
                    example_sentence="I wash the cup at home.",
                    item_key="alpha",
                    job_id=job_id,
                    review_reason="low_confidence",
                    translation_text="Eu lavo a xícara em casa.",
                    validation_flags=["low_confidence"],
                )
            ],
            report_path=path,
        )

    app = create_app(service=service, review_report_builder=build_review_report)

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
            "--review-report-file",
            str(report_path),
        ],
    )

    session.close()

    assert result.exit_code == 0
    assert "flagged_cards=2" in result.output
    assert f"review_report={report_path}" in result.output


def test_generate_command_skips_empty_review_artifacts(tmp_path: Path) -> None:
    service, session = build_service()
    source = write_word_list(tmp_path, "alpha")
    report_path = tmp_path / "flagged-review.json"

    def build_review_report(*, job_id: str, output_path: Path | None) -> ReviewReport:
        return ReviewReport(job_id=job_id, item_count=0, items=[], report_path=output_path)

    app = create_app(service=service, review_report_builder=build_review_report)

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
            "--review-report-file",
            str(report_path),
        ],
    )

    session.close()

    assert result.exit_code == 0
    assert "flagged_cards=0" in result.output
    assert "review_report=" not in result.output
    assert report_path.exists() is False


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


def test_generate_frequency_command_reports_grounded_candidate_counts(monkeypatch) -> None:
    service, session = build_ingest_service(
        lookup_terms=[f"word-{rank}" for rank in range(1, 3005) if rank not in {17, 1013, 2400}],
    )
    app = create_app(service=service)

    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: (
            (rank, f"word-{rank}") for rank in range(1, 3008)
        ),
    )

    result = runner.invoke(app, ["generate", "--language", "en", "--source", "frequency"])

    session.close()

    assert result.exit_code == 0
    assert "grounded_candidates=3000" in result.output
    assert "backfilled_candidates=3" in result.output
    assert "level_1_candidates=1000" in result.output
    assert "level_2_candidates=1000" in result.output
    assert "level_3_candidates=1000" in result.output
    assert "pending_groundings=0" in result.output


def test_generate_frequency_command_supports_test_mode(monkeypatch) -> None:
    service, session = build_ingest_service(
        lookup_terms=[f"word-{rank}" for rank in range(1, 3010)],
    )
    app = create_app(service=service)

    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: ((rank, f"word-{rank}") for rank in range(1, 3010)),
    )

    result = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "frequency", "--test-mode"],
    )

    session.close()

    assert result.exit_code == 0
    assert "grounded_candidates=9" in result.output
    assert "level_1_candidates=3" in result.output
    assert "level_2_candidates=3" in result.output
    assert "level_3_candidates=3" in result.output


def test_generate_frequency_command_supports_cards_per_level_override(monkeypatch) -> None:
    service, session = build_ingest_service(
        lookup_terms=[f"word-{rank}" for rank in range(1, 2010)],
    )
    app = create_app(service=service)

    from multilang.services import frequency_decks

    monkeypatch.setattr(
        frequency_decks,
        "iter_curated_frequency_candidates",
        lambda language, scan_limit=6000: ((rank, f"word-{rank}") for rank in range(1, 2010)),
    )

    result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "frequency",
            "--level",
            "2",
            "--cards-per-level",
            "3",
        ],
    )

    session.close()

    assert result.exit_code == 0
    assert "grounded_candidates=3" in result.output
    assert "level_1_candidates=0" in result.output
    assert "level_2_candidates=3" in result.output
    assert "level_3_candidates=0" in result.output


def test_generate_word_list_command_reports_pending_groundings(tmp_path: Path) -> None:
    service, session = build_ingest_service(lookup_terms=["hello", "world"])
    app = create_app(service=service)
    source = write_word_list(tmp_path, "hello", "", "world", "xyzqwe")

    result = runner.invoke(
        app,
        ["generate", "--language", "en", "--source", "word-list", "--input-file", str(source)],
    )

    session.close()

    assert result.exit_code == 0
    assert "grounded_candidates=2" in result.output
    assert "pending_groundings=1" in result.output
    assert "rejected_rows=1" in result.output
    assert "completed_items=2" in result.output


def test_generate_command_bootstraps_missing_lexicon_from_explicit_source_file(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "bootstrap.db"
    lexicon_dir = tmp_path / "lexicon"
    source_file = write_kaikki_archive(
        tmp_path / "kaikki-en.jsonl.gz",
        [{"word": "hello", "lang_code": "en", "senses": [{"glosses": ["hello"]}]}],
    )

    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))

    app = create_app()
    result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "word-list",
            "--input-file",
            str(write_word_list(tmp_path, "hello")),
            "--lexicon-source-file",
            str(source_file),
        ],
    )

    assert result.exit_code == 0
    assert (lexicon_dir / "en" / "kaikki-index.json").exists()
    assert "grounded_candidates=1" in result.output


def test_generate_command_bootstraps_missing_lexicon_from_default_source_file(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "bootstrap-default.db"
    lexicon_dir = tmp_path / "lexicon"
    source_dir = tmp_path / ".multilang" / "sources" / "kaikki"
    source_dir.mkdir(parents=True)
    write_kaikki_archive(
        source_dir / "kaikki-en.jsonl.gz",
        [{"word": "hello", "lang_code": "en", "senses": [{"glosses": ["hello"]}]}],
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))

    app = create_app()
    result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "word-list",
            "--input-file",
            str(write_word_list(tmp_path, "hello")),
        ],
    )

    assert result.exit_code == 0
    assert (lexicon_dir / "en" / "kaikki-index.json").exists()
    assert "grounded_candidates=1" in result.output


def test_generate_command_fails_fast_when_lexical_data_is_missing(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "missing-lexicon.db"
    lexicon_dir = tmp_path / "lexicon"
    lexicon_dir.mkdir()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MULTILANG_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("MULTILANG_LEXICON_DATA_DIR", str(lexicon_dir))

    app = create_app()
    result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "word-list",
            "--input-file",
            str(write_word_list(tmp_path, "hello")),
        ],
    )

    assert result.exit_code == 1
    assert "lexical data is missing for language 'en'" in result.output
    assert "--lexicon-source-file" in result.output
    assert "grounded_candidates=" not in result.output


def test_generate_command_regenerates_single_flagged_item(tmp_path: Path) -> None:
    database_path = tmp_path / "runtime.db"
    lexicon_dir = write_lookup_index(tmp_path, "wash", "flag-beta")
    source = write_word_list(tmp_path, "wash", "flag-beta")
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
    job_id = service.repository.session.scalar(select(GenerationJob.id))
    assert job_id is not None

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
            job_id,
            "--regenerate-item-key",
            "flag-beta",
            "--review-report-file",
            str(review_report),
        ],
    )

    assert first_result.exit_code == 0
    assert "review_required_text_items=1" in first_result.output
    assert "flagged_cards=1" in first_result.output
    assert second_result.exit_code == 0
    assert "--regenerate-item-key" not in second_result.output
    assert "text_processed_items=1" in second_result.output
    assert "review_required_text_items=1" in second_result.output


def test_generate_command_default_runtime_reports_audio_counters(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "audio-runtime.db"
    lexicon_dir = write_lookup_index(tmp_path, "wash")
    source = write_word_list(tmp_path, "wash")
    FakeAzureSpeechAdapter.instances.clear()
    FakeAzureSpeechAdapter.available_ids = {"en-US-GuyNeural"}
    monkeypatch.setattr(runtime_module, "AzureSpeechAdapter", FakeAzureSpeechAdapter)
    service = build_runtime_service(
        Settings(
            database_url=f"sqlite+pysqlite:///{database_path}",
            lexicon_data_dir=lexicon_dir,
            audio_storage_dir=tmp_path / "audio",
            azure_speech_key="key",
            azure_speech_region="eastus",
            tatoeba_enabled=False,
        ),
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
            service.repository.session.scalar(select(GenerationJob.id)),
        ],
    )

    assert first_result.exit_code == 0
    assert "audio_processed_items=2" in first_result.output
    assert "audio_reused_items=0" in first_result.output
    assert "fallback_audio_items=2" in first_result.output
    assert "failed_audio_items=0" in first_result.output
    assert second_result.exit_code == 0
    assert "audio_processed_items=2" in second_result.output
    assert "audio_reused_items=2" in second_result.output
    assert len(FakeAzureSpeechAdapter.instances) == 1
    assert service.repository.session.scalar(select(GenerationJob.id)) is not None
    assert service.repository.session.scalar(select(func.count()).select_from(AudioAssetModel)) == 2


def test_generate_command_reports_failed_audio_when_no_approved_voice_exists(
    tmp_path: Path, monkeypatch
) -> None:
    database_path = tmp_path / "audio-runtime.db"
    lexicon_dir = write_lookup_index(tmp_path, "wash")
    source = write_word_list(tmp_path, "wash")
    FakeAzureSpeechAdapter.instances.clear()
    FakeAzureSpeechAdapter.available_ids = {"en-AU-NatashaNeural"}
    monkeypatch.setattr(runtime_module, "AzureSpeechAdapter", FakeAzureSpeechAdapter)
    service = build_runtime_service(
        Settings(
            database_url=f"sqlite+pysqlite:///{database_path}",
            lexicon_data_dir=lexicon_dir,
            audio_storage_dir=tmp_path / "audio",
            azure_speech_key="key",
            azure_speech_region="eastus",
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
    assert "audio_processed_items=2" in result.output
    assert "failed_audio_items=2" in result.output
