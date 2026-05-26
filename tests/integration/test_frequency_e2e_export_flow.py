"""Frequency-deck E2E coverage from accepted text through export artifacts."""

from __future__ import annotations

import inspect
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
from multilang.services import frequency_decks
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


def fake_frequency_wordlist(language: str):
    words = [f"junk{rank}" for rank in range(1, 2002)]
    words[0] = "alpha"
    words[1000] = "bravo"
    words[2000] = "charlie"
    return iter(words)


def test_frequency_sample_generates_audio_and_exports_all_formats(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "frequency-e2e.db"
    lexicon_dir = write_lookup_index(tmp_path, "alpha", "bravo", "charlie")
    output_dir = tmp_path / "exports"
    FakeAzureSpeechAdapter.instances.clear()
    monkeypatch.setattr(runtime_module, "AzureSpeechAdapter", FakeAzureSpeechAdapter)
    monkeypatch.setattr(frequency_decks, "iter_wordlist", fake_frequency_wordlist)
    service = build_runtime_service(
        Settings(
            _env_file=None,
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
            "frequency",
            "--cards-per-level",
            "1",
        ],
    )

    assert generate_result.exit_code == 0
    assert "level_1_candidates=1" in generate_result.output
    assert "level_2_candidates=1" in generate_result.output
    assert "level_3_candidates=1" in generate_result.output
    assert "accepted_text_items=3" in generate_result.output
    assert "review_required_text_items=0" in generate_result.output
    assert "audio_processed_items=6" in generate_result.output

    session = Session(create_engine(f"sqlite+pysqlite:///{database_path}"))
    try:
        job = session.scalar(select(GenerationJob))
        assert job is not None
        assert session.scalar(select(func.count()).select_from(TextQualityRecordModel)) == 3
        assert session.scalar(select(func.count()).select_from(AudioAssetModel)) == 6
        text_rows = list(session.scalars(select(TextQualityRecordModel)))
        assert {row.review_status for row in text_rows} == {"accepted"}
        for asset in session.scalars(select(AudioAssetModel)):
            assert Path(asset.storage_path).read_bytes().startswith(b"ID3")

        for export_format in ["apkg", "csv", "tsv"]:
            export_result = runner.invoke(
                app,
                ["export", "--job-id", job.id, "--format", export_format, "--output-dir", str(output_dir)],
            )
            assert export_result.exit_code == 1
            assert "export quality gate failed" in export_result.output
            assert "frequency deck has 3/3000 cards" in export_result.output

            export_result = runner.invoke(
                app,
                [
                    "export",
                    "--job-id",
                    job.id,
                    "--format",
                    export_format,
                    "--output-dir",
                    str(output_dir),
                    "--allow-partial",
                ],
            )
            assert export_result.exit_code == 0
            assert "card_count=3" in export_result.output
            assert "export_status=partial" in export_result.output
            assert "generation_report_json=" in export_result.output
            assert (output_dir / f"{job.id}.{export_format}").exists()

        assert (output_dir / "generation-report.json").exists()
        report = json.loads((output_dir / "generation-report.json").read_text(encoding="utf-8"))
        assert report["export"]["card_count"] == 3
        assert report["warnings"]

        assert session.scalar(select(func.count()).select_from(DeckExportModel)) == 3
        assert session.scalar(select(func.count()).select_from(CardExportModel)) == 3
    finally:
        session.close()


def test_frequency_production_contract_remains_three_levels_of_one_thousand() -> None:
    signature = inspect.signature(frequency_decks.build_frequency_deck)

    assert signature.parameters["required_count_per_level"].default == 1000
    assert frequency_decks.LEVEL_WINDOWS == {
        1: (1, 1000),
        2: (1001, 2000),
        3: (2001, 3000),
    }
