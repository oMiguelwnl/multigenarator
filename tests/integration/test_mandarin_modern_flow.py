"""Offline Mandarin slices through the modern CLI, repositories, and exporters."""

from __future__ import annotations

import csv
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from typing import ClassVar
import zipfile

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.db.models import AudioAssetModel, CardExportModel, GenerationJob, TextQualityRecordModel
from multilang.domain.exporting import MANDARIN_EXPORT_CARD_FIELD_NAMES, ExportCardIdentity, ExportCardRow
from multilang.domain.jobs import SupportedLanguage
import multilang.runtime as runtime_module
from multilang.runtime import build_runtime_service
from multilang.services import frequency_decks
from multilang.services.audio_synthesis import AudioSynthesisAdapter, AudioSynthesisResponse
from multilang.services.export_anki_package import (
    MANDARIN_MODEL_ID,
    MANDARIN_NOTE_TYPE_NAME,
    export_anki_package,
)
from multilang.services.mandarin_orthography import MandarinOrthographyService
from multilang.services.text_generation import (
    DefinitionGenerationResult,
    SentenceGenerationResult,
    SentenceTranslationResult,
)
from multilang.settings import Settings


runner = CliRunner()


class FakeMandarinAzureSpeechAdapter(AudioSynthesisAdapter):
    calls: ClassVar[list[tuple[str, str, str]]] = []

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings(_env_file=None)

    def available_voice_ids(self) -> set[str] | None:
        return {"zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"}

    def synthesize(
        self,
        *,
        ssml_text: str,
        voice_id: str,
        locale: str,
        output_path: Path,
        audio_format: str,
    ) -> AudioSynthesisResponse:
        type(self).calls.append((voice_id, locale, ssml_text))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = b"ID3" + f":{voice_id}:{locale}:{audio_format}:{ssml_text}".encode("utf-8")
        output_path.write_bytes(payload)
        return AudioSynthesisResponse(storage_path=output_path, byte_size=len(payload), duration_ms=800)


class CountingMandarinOrthographyService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self._delegate = MandarinOrthographyService()

    def derive(self, *, word: str, sentence: str):
        self.calls.append((word, sentence))
        return self._delegate.derive(word=word, sentence=sentence)


class FakeMandarinSentenceAdapter:
    def generate_definition(self, request) -> DefinitionGenerationResult:
        return DefinitionGenerationResult(
            definitions_html=f"noun: learner meaning for {request.lemma}",
            provenance={"source": "mandarin-e2e-fixture", "provider": "fixture"},
        )

    def generate_sentence(self, request) -> SentenceGenerationResult:
        return SentenceGenerationResult(
            sentence=f"朋友们在晚饭时讨论{request.display_form}。",
            intended_sense=f"learner meaning for {request.display_form}",
            uncertainty_notes=[],
            provenance={
                "source": "mandarin-e2e-fixture",
                "provider": "fixture",
                "template_kind": "curated:mandarin-e2e",
            },
        )


class FakeMandarinTranslationAdapter:
    def translate_sentence(self, request) -> SentenceTranslationResult:
        return SentenceTranslationResult(
            translation="Friends discuss the target term during dinner.",
            provenance={"source": "mandarin-e2e-fixture", "provider": "fixture"},
        )


def write_lookup_index(tmp_path: Path, *terms: str) -> Path:
    index_path = tmp_path / "lexicon" / "zh" / "lexical-index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(
            {
                term: {
                    "term": term,
                    "display_form": term,
                    "lemma": term,
                    "definitions": [f"learner meaning for {index + 1}"],
                    "part_of_speech": "noun",
                    "ipa": f"/{term}/",
                    "source": "manual",
                }
                for index, term in enumerate(terms)
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return index_path.parent.parent


def write_word_list(tmp_path: Path, *terms: str) -> Path:
    path = tmp_path / "mandarin-words.txt"
    path.write_text("\n".join(terms), encoding="utf-8")
    return path


def fake_mandarin_frequency_wordlist(language: str):
    assert language == "zh"
    words = [f"junk{rank}" for rank in range(1, 2002)]
    words[0] = "中国"
    words[1000] = "银行"
    words[2000] = "学习"
    return iter(words)


def _build_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *terms: str):
    database_path = tmp_path / "mandarin-e2e.db"
    FakeMandarinAzureSpeechAdapter.calls.clear()
    monkeypatch.setattr(runtime_module, "AzureSpeechAdapter", FakeMandarinAzureSpeechAdapter)
    monkeypatch.setattr(runtime_module, "LocalSentenceAdapter", FakeMandarinSentenceAdapter)
    monkeypatch.setattr(runtime_module, "LocalTranslationAdapter", FakeMandarinTranslationAdapter)
    service = build_runtime_service(
        Settings(
            _env_file=None,
            database_url=f"sqlite+pysqlite:///{database_path}",
            lexicon_data_dir=write_lookup_index(tmp_path, *terms),
            audio_storage_dir=tmp_path / "audio",
            audio_provider="azure",
            text_generation_provider="local",
            translation_provider="local",
            azure_speech_key="offline-key",
            azure_speech_region="eastus",
            tatoeba_enabled=False,
        )
    )
    orthography = CountingMandarinOrthographyService()
    service.assemble_export_cards_service.mandarin_orthography_service = orthography
    return service, database_path, orthography


def _export_all_formats(
    *,
    service,
    job_id: str,
    output_dir: Path,
    expected_cards: int,
    allow_partial: bool,
) -> dict[str, Path]:
    app = create_app(service=service)
    artifacts: dict[str, Path] = {}
    for index, export_format in enumerate(("apkg", "csv", "tsv")):
        if index == 1:
            service.export_repository.session.expire_all()
        args = ["export", "--job-id", job_id, "--format", export_format, "--output-dir", str(output_dir)]
        if allow_partial:
            args.append("--allow-partial")
        result = runner.invoke(app, args)
        assert result.exit_code == 0, result.output
        assert f"card_count={expected_cards}" in result.output
        if allow_partial:
            assert "export_status=partial" in result.output
        artifact = output_dir / f"{job_id}.{export_format}"
        assert artifact.is_file()
        artifacts[export_format] = artifact
    return artifacts


def _assert_tabular_contract(path: Path, *, delimiter: str, expected_cards: int) -> None:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert lines[0] == f"#separator:{'Comma' if delimiter == ',' else 'Tab'}"
    assert lines[1] == "#html:true"
    assert lines[2] == f"#notetype:{MANDARIN_NOTE_TYPE_NAME}"
    assert lines[4] == f"#columns:{delimiter.join(MANDARIN_EXPORT_CARD_FIELD_NAMES)}"
    rows = list(csv.reader(lines[5:], delimiter=delimiter))
    assert len(rows) == expected_cards
    assert all(row[-1] == "" for row in rows)
    assert all(row[9].startswith("[sound:") and row[10].startswith("[sound:") for row in rows)


def _inspect_mandarin_apkg(path: Path, *, expected_notes: int) -> dict[str, object]:
    with TemporaryDirectory() as directory:
        collection_path = Path(directory) / "collection.anki2"
        with zipfile.ZipFile(path) as archive:
            media_manifest = json.loads(archive.read("media").decode("utf-8"))
            assert len(media_manifest) == expected_notes * 2
            assert all(archive.read(archived_name).startswith(b"ID3") for archived_name in media_manifest)
            collection_path.write_bytes(archive.read("collection.anki2"))
        with closing(sqlite3.connect(collection_path)) as connection:
            models = json.loads(connection.execute("select models from col").fetchone()[0])
            notes = connection.execute("select flds, tags from notes order by id").fetchall()

    model = models[str(MANDARIN_MODEL_ID)]
    assert model["name"] == MANDARIN_NOTE_TYPE_NAME
    assert tuple(field["name"] for field in model["flds"]) == MANDARIN_EXPORT_CARD_FIELD_NAMES
    assert "{{Pinyin}}" in model["tmpls"][0]["qfmt"]
    assert "{{Traditional Sentence}}" in model["tmpls"][0]["qfmt"]
    assert len(notes) == expected_notes
    assert all(" zh " in tags for _, tags in notes)
    assert all(fields.split("\x1f")[-1] == "" for fields, _ in notes)
    return {"model": model, "notes": notes, "media": media_manifest}


def _assert_frozen_rows(session: Session, *, expected_cards: int, source_type: str) -> list[CardExportModel]:
    rows = list(session.scalars(select(CardExportModel).order_by(CardExportModel.sort_index.asc())))
    assert len(rows) == expected_cards
    assert all(row.job.language == "zh" and row.job.source_type == source_type for row in rows)
    assert all(row.mandarin_word_pinyin and row.mandarin_word_traditional for row in rows)
    assert all(row.mandarin_sentence_pinyin and row.mandarin_sentence_traditional for row in rows)
    assert all(row.word_audio and row.sentence_audio and row.image == "" for row in rows)
    return rows


def test_mandarin_frequency_cli_exports_frozen_rows_and_all_formats(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    terms = ("中国", "银行", "学习")
    monkeypatch.setattr(frequency_decks, "iter_wordlist", fake_mandarin_frequency_wordlist)
    service, database_path, orthography = _build_service(tmp_path, monkeypatch, *terms)
    app = create_app(service=service)

    generated = runner.invoke(
        app,
        ["generate", "--language", "zh", "--source", "frequency", "--cards-per-level", "1"],
    )
    assert generated.exit_code == 0, generated.output
    assert "accepted_text_items=3" in generated.output
    assert "audio_processed_items=6" in generated.output
    assert len(FakeMandarinAzureSpeechAdapter.calls) == 6
    assert {locale for _, locale, _ in FakeMandarinAzureSpeechAdapter.calls} == {"zh-CN"}
    assert {voice for voice, _, _ in FakeMandarinAzureSpeechAdapter.calls} <= {
        "zh-CN-XiaoxiaoNeural",
        "zh-CN-YunxiNeural",
    }

    session = Session(create_engine(f"sqlite+pysqlite:///{database_path}"))
    try:
        job = session.scalar(select(GenerationJob))
        assert job is not None and job.language == "zh"
        assert session.scalar(select(func.count()).select_from(TextQualityRecordModel)) == 3
        assert {row.review_status for row in session.scalars(select(TextQualityRecordModel))} == {"accepted"}
        assert session.scalar(select(func.count()).select_from(AudioAssetModel)) == 6

        artifacts = _export_all_formats(
            service=service,
            job_id=job.id,
            output_dir=tmp_path / "exports",
            expected_cards=3,
            allow_partial=True,
        )
        assert len(orthography.calls) == 3
        _assert_frozen_rows(session, expected_cards=3, source_type="frequency")
        _inspect_mandarin_apkg(artifacts["apkg"], expected_notes=3)
        _assert_tabular_contract(artifacts["csv"], delimiter=",", expected_cards=3)
        _assert_tabular_contract(artifacts["tsv"], delimiter="\t", expected_cards=3)

        for row in service.export_repository.list_card_snapshots(job.id):
            media_index = service._build_media_index([row])
            assert media_index[row.word_audio].is_file()
            assert media_index[row.sentence_audio].is_file()
        assert len(orthography.calls) == 3
    finally:
        session.close()


def test_mandarin_word_list_cli_keeps_two_audio_assets_per_card_after_reload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    terms = ("中国", "银行")
    service, database_path, orthography = _build_service(tmp_path, monkeypatch, *terms)
    source = write_word_list(tmp_path, *terms)
    app = create_app(service=service)

    generated = runner.invoke(
        app,
        ["generate", "--language", "zh", "--source", "word-list", "--input-file", str(source)],
    )
    assert generated.exit_code == 0, generated.output
    assert "accepted_text_items=2" in generated.output
    assert "audio_processed_items=4" in generated.output

    session = Session(create_engine(f"sqlite+pysqlite:///{database_path}"))
    try:
        job = session.scalar(select(GenerationJob))
        assert job is not None and job.language == "zh" and job.source_type == "word-list"
        assert session.scalar(select(func.count()).select_from(AudioAssetModel)) == 4
        artifacts = _export_all_formats(
            service=service,
            job_id=job.id,
            output_dir=tmp_path / "exports",
            expected_cards=2,
            allow_partial=False,
        )
        assert len(orthography.calls) == 2
        _assert_frozen_rows(session, expected_cards=2, source_type="word-list")
        _inspect_mandarin_apkg(artifacts["apkg"], expected_notes=2)
        _assert_tabular_contract(artifacts["csv"], delimiter=",", expected_cards=2)
        _assert_tabular_contract(artifacts["tsv"], delimiter="\t", expected_cards=2)
        assert len(orthography.calls) == 2
    finally:
        session.close()


def _proof_row() -> ExportCardRow:
    return ExportCardRow(
        identity=ExportCardIdentity(
            language=SupportedLanguage.ZH,
            source_type="frequency",
            job_id="mandarin-proof",
            item_key="level-1-rank-0001:中国",
            lemma_key="zh:中国",
            sort_index=1,
        ),
        word="中国",
        front_of_card="中国",
        definitions="proper noun: China",
        example_sentence="我哥哥明天想去中国。",
        translation="My brother wants to go to China tomorrow.",
        word_audio="[sound:mandarin-proof-word.mp3]",
        sentence_audio="[sound:mandarin-proof-sentence.mp3]",
        mandarin_word_pinyin="zhōng guó",
        mandarin_word_traditional="中國",
        mandarin_sentence_pinyin="wǒ gē ge míng tiān xiǎng qù zhōng guó。",
        mandarin_sentence_traditional="我哥哥明天想去中國。",
    )


def write_mandarin_proof_artifact(output_path: Path) -> None:
    """Write and fail-closed validate the persistent offline visual-review artifact."""

    row = _proof_row()
    with TemporaryDirectory() as directory:
        media_root = Path(directory)
        word_media = media_root / "mandarin-proof-word.mp3"
        sentence_media = media_root / "mandarin-proof-sentence.mp3"
        word_media.write_bytes(b"ID3-offline-word-proof")
        sentence_media.write_bytes(b"ID3-offline-sentence-proof")
        export_anki_package(
            rows=[row],
            media_index={row.word_audio: word_media, row.sentence_audio: sentence_media},
            output_path=output_path,
            deck_name="Multilang Mandarin Chinese Proof",
        )
    proof = _inspect_mandarin_apkg(output_path, expected_notes=1)
    fields = proof["notes"][0][0].split("\x1f")
    if fields[-1] != "" or fields[1] != "中国" or len(proof["media"]) != 2:
        raise AssertionError("Mandarin proof artifact contract validation failed")


def test_write_mandarin_proof_artifact_is_offline_and_fail_closed(tmp_path: Path) -> None:
    output_path = tmp_path / "mandarin-proof.apkg"
    write_mandarin_proof_artifact(output_path)
    assert output_path.is_file() and output_path.stat().st_size > 0


__all__ = ["write_mandarin_proof_artifact"]
