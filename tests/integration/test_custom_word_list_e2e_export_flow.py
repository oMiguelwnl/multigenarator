"""Custom word-list E2E coverage from accepted text through export artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.db.models import AudioAssetModel, CardExportModel, DeckExportModel, GenerationJob, TextQualityRecordModel
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
                    "part_of_speech": "noun",
                    "ipa": f"/{term}/",
                    "source": "manual",
                }
                for term in terms
            }
        ),
        encoding="utf-8",
    )
    return index_path.parent.parent


def test_custom_word_list_generates_audio_and_exports_all_formats(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "custom-e2e.db"
    lexicon_dir = write_lookup_index(tmp_path, "alpha", "bravo")
    source = write_word_list(tmp_path, "alpha", "bravo")
    output_dir = tmp_path / "exports"
    FakeAzureSpeechAdapter.instances.clear()
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

    assert generate_result.exit_code == 0
    assert "grounded_candidates=2" in generate_result.output
    assert "accepted_text_items=2" in generate_result.output
    assert "review_required_text_items=0" in generate_result.output
    assert "audio_processed_items=2" in generate_result.output

    session = Session(create_engine(f"sqlite+pysqlite:///{database_path}"))
    try:
        job = session.scalar(select(GenerationJob))
        assert job is not None
        assert session.scalar(select(func.count()).select_from(GenerationJob)) == 1
        assert session.scalar(select(func.count()).select_from(TextQualityRecordModel)) == 2
        assert session.scalar(select(func.count()).select_from(AudioAssetModel)) == 2
        text_rows = list(session.scalars(select(TextQualityRecordModel).order_by(TextQualityRecordModel.item_key.asc())))
        assert {row.review_status for row in text_rows} == {"accepted"}
        audio_assets = list(session.scalars(select(AudioAssetModel)))
        for asset in audio_assets:
            assert Path(asset.storage_path).read_bytes().startswith(b"ID3")

        for export_format in ["apkg", "csv", "tsv"]:
            export_result = runner.invoke(
                app,
                ["export", "--job-id", job.id, "--format", export_format, "--output-dir", str(output_dir)],
            )
            assert export_result.exit_code == 0
            assert f"artifact_path={output_dir / f'{job.id}.{export_format}'}" in export_result.output
            assert "card_count=2" in export_result.output
            assert (output_dir / f"{job.id}.{export_format}").exists()

        assert session.scalar(select(func.count()).select_from(DeckExportModel)) == 3
        assert session.scalar(select(func.count()).select_from(CardExportModel)) == 2
    finally:
        session.close()
