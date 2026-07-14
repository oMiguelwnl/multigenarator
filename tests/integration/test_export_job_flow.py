"""Integration coverage for the shipped export runtime path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.db.models import AudioAssetModel, CardExportModel, DeckExportModel, GenerationJob
import multilang.runtime as runtime_module
from multilang.runtime import build_runtime_service
from multilang.services.audio_synthesis import AudioSynthesisAdapter, AudioSynthesisResponse
from multilang.settings import Settings

runner = CliRunner()


class FakeAzureSpeechAdapter(AudioSynthesisAdapter):
    instances: ClassVar[list[FakeAzureSpeechAdapter]] = []

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        type(self).instances.append(self)

    def available_voice_ids(self) -> set[str] | None:
        return {"en-US-JennyNeural", "en-US-GuyNeural"}

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
        payload = b"ID3" + f":{voice_id}:{locale}:{audio_format}:{ssml_text}".encode("utf-8")
        output_path.write_bytes(payload)
        return AudioSynthesisResponse(storage_path=output_path, byte_size=len(payload), duration_ms=800)


def write_word_list(tmp_path: Path, *items: str) -> Path:
    path = tmp_path / "words.txt"
    path.write_text("\n".join(items), encoding="utf-8")
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
                    "part_of_speech": "verb",
                    "ipa": f"/{term}/",
                    "source": "manual",
                }
                for term in terms
            }
        ),
        encoding="utf-8",
    )
    return index_path.parent.parent


def test_export_command_runtime_path_writes_apkg_csv_and_tsv_artifacts(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "export-runtime.db"
    lexicon_dir = write_lookup_index(tmp_path, "wash")
    source = write_word_list(tmp_path, "wash")
    output_dir = tmp_path / "exports"
    FakeAzureSpeechAdapter.instances.clear()
    monkeypatch.setattr(runtime_module, "AzureSpeechAdapter", FakeAzureSpeechAdapter)
    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{database_path}",
            lexicon_data_dir=lexicon_dir,
            audio_storage_dir=tmp_path / "audio",
            audio_provider="azure",
            azure_speech_key="key",
            azure_speech_region="eastus",
            tatoeba_enabled=False,
        ),
    )
    app = create_app(service=service)

    generate_result = runner.invoke(
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

        apkg_result = runner.invoke(
            app,
            ["export", "--job-id", job.id, "--format", "apkg", "--output-dir", str(output_dir)],
        )
        csv_result = runner.invoke(
            app,
            ["export", "--job-id", job.id, "--format", "csv", "--output-dir", str(output_dir)],
        )
        tsv_result = runner.invoke(
            app,
            ["export", "--job-id", job.id, "--format", "tsv", "--output-dir", str(output_dir)],
        )

        assert generate_result.exit_code == 0
        assert apkg_result.exit_code == 0
        assert csv_result.exit_code == 0
        assert tsv_result.exit_code == 0
        assert (output_dir / f"{job.id}.apkg").exists()
        assert (output_dir / f"{job.id}.csv").exists()
        assert (output_dir / f"{job.id}.tsv").exists()
        assert session.scalar(select(func.count()).select_from(CardExportModel)) == 1
        assert session.scalar(select(func.count()).select_from(DeckExportModel)) == 3
        deck_exports = list(session.scalars(select(DeckExportModel).order_by(DeckExportModel.export_format.asc())))
        assert all(export.deck_name == "Multilang English" for export in deck_exports)
    finally:
        session.close()


@pytest.mark.parametrize("export_format", ["apkg", "csv", "tsv"])
def test_export_command_runtime_path_fails_loudly_when_audio_is_missing(
    export_format: str,
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "export-missing-audio.db"
    lexicon_dir = write_lookup_index(tmp_path, "wash")
    source = write_word_list(tmp_path, "wash")
    monkeypatch.setattr(runtime_module, "AzureSpeechAdapter", FakeAzureSpeechAdapter)
    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{database_path}",
            lexicon_data_dir=lexicon_dir,
            audio_storage_dir=tmp_path / "audio",
            audio_provider="azure",
            azure_speech_key="key",
            azure_speech_region="eastus",
            tatoeba_enabled=False,
        ),
    )
    app = create_app(service=service)

    generate_result = runner.invoke(
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
        audio_dir = tmp_path / "audio"
        for mp3_file in audio_dir.rglob("*.mp3"):
            mp3_file.unlink()

        export_result = runner.invoke(
            app,
            ["export", "--job-id", job.id, "--format", export_format, "--output-dir", str(tmp_path / "exports")],
        )

        assert generate_result.exit_code == 0
        assert export_result.exit_code == 1
        assert "missing media file" in export_result.output or "missing required" in export_result.output
    finally:
        session.close()


@pytest.mark.parametrize("export_format", ["apkg", "csv", "tsv"])
def test_export_command_runtime_path_blocks_persisted_word_audio_mismatches(
    export_format: str,
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / f"export-audio-integrity-{export_format}.db"
    lexicon_dir = write_lookup_index(tmp_path, "the")
    output_dir = tmp_path / "exports"
    monkeypatch.setattr(runtime_module, "AzureSpeechAdapter", FakeAzureSpeechAdapter)
    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{database_path}",
            lexicon_data_dir=lexicon_dir,
            audio_storage_dir=tmp_path / "audio",
            audio_provider="azure",
            azure_speech_key="key",
            azure_speech_region="eastus",
            tatoeba_enabled=False,
        ),
    )
    app = create_app(service=service)

    generate_result = runner.invoke(
        app,
        [
            "generate",
            "--language",
            "en",
            "--source",
            "frequency",
            "--level",
            "1",
            "--test-mode",
            "--cards-per-level",
            "1",
        ],
    )

    session = Session(create_engine(f"sqlite+pysqlite:///{database_path}"))
    try:
        job = session.scalar(select(GenerationJob))
        assert job is not None
        first_export = runner.invoke(
            app,
            ["export", "--job-id", job.id, "--format", export_format, "--output-dir", str(output_dir), "--allow-partial"],
        )
        assert generate_result.exit_code == 0
        assert first_export.exit_code == 0
        session.rollback()
        word_audio = session.scalar(
            select(AudioAssetModel).where(
                AudioAssetModel.job_id == job.id,
                AudioAssetModel.asset_kind == "word",
            )
        )
        assert word_audio is not None
        word_audio.display_text = "jump"
        word_audio.tts_text = "jump"
        word_audio.text_hash = "stale-jump-hash"
        session.commit()

        second_export = runner.invoke(
            app,
            ["export", "--job-id", job.id, "--format", export_format, "--output-dir", str(output_dir), "--allow-partial"],
        )

        assert second_export.exit_code == 1
        assert "word_audio" in second_export.output
        assert "Word" in second_export.output
    finally:
        session.close()
