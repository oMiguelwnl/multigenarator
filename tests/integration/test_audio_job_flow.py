"""Integration coverage for the shipped Phase 4 audio runtime path."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.db.models import AudioAssetModel, GenerationJob
from multilang.runtime import build_runtime_service
from multilang.services.audio_synthesis import AudioSynthesisAdapter, AudioSynthesisResponse
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


def test_generate_command_reuses_existing_audio_assets_on_resume(tmp_path: Path) -> None:
    database_path = tmp_path / "audio-runtime.db"
    lexicon_dir = write_lookup_index(tmp_path, "wash")
    source = write_word_list(tmp_path, "wash")
    service = build_runtime_service(
        Settings(
            database_url=f"sqlite+pysqlite:///{database_path}",
            lexicon_data_dir=lexicon_dir,
            audio_storage_dir=tmp_path / "audio",
            tatoeba_enabled=False,
        ),
        audio_adapter=FileWritingAudioAdapter(),
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
        first_assets = list(session.scalars(select(AudioAssetModel).order_by(AudioAssetModel.asset_kind.asc())))
        assert len(first_assets) == 2
        first_paths = [asset.storage_path for asset in first_assets]

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
            ],
        )

        assert second_result.exit_code == 0
        assert "audio_reused_items=2" in second_result.output
        session.expire_all()
        second_assets = list(session.scalars(select(AudioAssetModel).order_by(AudioAssetModel.asset_kind.asc())))
        assert len(second_assets) == 2
        assert [asset.storage_path for asset in second_assets] == first_paths
        assert session.scalar(select(func.count()).select_from(AudioAssetModel)) == 2
    finally:
        session.close()

    assert first_result.exit_code == 0
    assert "audio_processed_items=2" in first_result.output
