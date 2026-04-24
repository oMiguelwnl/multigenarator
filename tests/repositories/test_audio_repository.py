"""Repository tests for persisted audio assets."""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioFormat,
    AudioProvenance,
    AudioProvider,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)
from multilang.domain.jobs import GenerationRequest, SupportedLanguage
from multilang.repositories.audio_repository import AudioRepository
from multilang.repositories.job_repository import JobRepository


def build_repositories() -> tuple[AudioRepository, JobRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return AudioRepository(session), JobRepository(session), session


def make_request() -> GenerationRequest:
    return GenerationRequest(language=SupportedLanguage.EN, source_type="word-list", input_file=None)


def make_record(
    *,
    job_id: str,
    item_key: str,
    asset_kind: AudioAssetKind,
    display_text: str,
    tts_text: str,
    voice_id: str = "en-US-JennyNeural",
    locale: str = "en-US",
    status: AudioSynthesisStatus = AudioSynthesisStatus.SYNTHESIZED,
    fallback_used: bool = False,
    storage_path: str | None = None,
    byte_size: int = 4096,
    duration_ms: int | None = 1200,
) -> AudioAssetRecord:
    normalized_input = NormalizedTtsInput(
        display_text=display_text,
        tts_text=tts_text,
        ssml_text=f"<speak version=\"1.0\">{tts_text}</speak>",
    )
    return AudioAssetRecord(
        job_id=job_id,
        item_key=item_key,
        asset_kind=asset_kind,
        display_text=display_text,
        normalized_input=normalized_input,
        provenance=AudioProvenance(
            provider=AudioProvider.AZURE,
            voice_id=voice_id,
            locale=locale,
            format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
            text_hash=normalized_input.text_hash or "",
            ssml_hash=normalized_input.ssml_hash or "",
            storage_path=storage_path or f"audio/{asset_kind.value}/{item_key}-{voice_id}.mp3",
            byte_size=byte_size,
            duration_ms=duration_ms,
            status=status,
            fallback_used=fallback_used,
        ),
    )


def test_upsert_audio_asset_updates_existing_row() -> None:
    repository, job_repository, session = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-audio-upsert",
        source_fingerprint="word-list-a",
        total_items=1,
    )

    repository.upsert_audio_asset(
        make_record(
            job_id=job.id,
            item_key="line-1",
            asset_kind=AudioAssetKind.WORD,
            display_text="run",
            tts_text="run",
        )
    )
    updated = repository.upsert_audio_asset(
        make_record(
            job_id=job.id,
            item_key="line-1",
            asset_kind=AudioAssetKind.WORD,
            display_text="run",
            tts_text="run",
            voice_id="en-GB-SoniaNeural",
            locale="en-GB",
            fallback_used=True,
            storage_path="audio/word/line-1-en-GB-SoniaNeural.mp3",
            duration_ms=1300,
        )
    )

    assert session.execute(
        text(
            "SELECT COUNT(*) FROM audio_assets WHERE job_id = :job_id AND item_key = :item_key AND asset_kind = :asset_kind"
        ),
        {"job_id": job.id, "item_key": "line-1", "asset_kind": AudioAssetKind.WORD.value},
    ).scalar_one() == 1
    assert updated.provenance.voice_id == "en-GB-SoniaNeural"
    assert updated.provenance.locale == "en-GB"
    assert updated.provenance.fallback_used is True
    assert repository.get_asset(job.id, "line-1", AudioAssetKind.WORD) is not None


def test_repository_queries_preserve_word_sentence_and_failures() -> None:
    repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-audio-list",
        source_fingerprint="word-list-b",
        total_items=2,
    )

    repository.upsert_audio_asset(
        make_record(
            job_id=job.id,
            item_key="line-2",
            asset_kind=AudioAssetKind.SENTENCE,
            display_text="I run every morning.",
            tts_text="I run every morning.",
        )
    )
    repository.upsert_audio_asset(
        make_record(
            job_id=job.id,
            item_key="line-1",
            asset_kind=AudioAssetKind.WORD,
            display_text="run",
            tts_text="run",
        )
    )
    repository.upsert_audio_asset(
        make_record(
            job_id=job.id,
            item_key="line-1",
            asset_kind=AudioAssetKind.SENTENCE,
            display_text="I run every morning.",
            tts_text="I run every morning.",
            status=AudioSynthesisStatus.FAILED,
            byte_size=0,
            duration_ms=None,
            storage_path="audio/sentence/failed-line-1.mp3",
        )
    )

    assets = repository.list_assets_for_job(job.id)
    failed_assets = repository.list_failed_assets(job.id)

    assert [(asset.item_key, asset.asset_kind) for asset in assets] == [
        ("line-1", AudioAssetKind.SENTENCE),
        ("line-1", AudioAssetKind.WORD),
        ("line-2", AudioAssetKind.SENTENCE),
    ]
    assert [(asset.item_key, asset.asset_kind) for asset in failed_assets] == [
        ("line-1", AudioAssetKind.SENTENCE)
    ]


def test_repository_round_trips_provenance_and_reusable_lookup() -> None:
    repository, job_repository, _ = build_repositories()
    job = job_repository.create_job(
        request=make_request(),
        run_key="run-audio-reuse",
        source_fingerprint="word-list-c",
        total_items=1,
    )
    record = make_record(
        job_id=job.id,
        item_key="line-1",
        asset_kind=AudioAssetKind.WORD,
        display_text="read",
        tts_text="read",
        voice_id="en-US-JennyNeural",
        locale="en-US",
        fallback_used=False,
        storage_path="audio/word/read-en-US-JennyNeural.mp3",
        byte_size=5120,
        duration_ms=900,
    )

    stored = repository.upsert_audio_asset(record)
    reusable = repository.get_reusable_asset(
        asset_kind=AudioAssetKind.WORD,
        text_hash=record.normalized_input.text_hash or "",
        ssml_hash=record.normalized_input.ssml_hash or "",
        voice_id="en-US-JennyNeural",
        format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
    )

    assert stored.provenance.storage_path == "audio/word/read-en-US-JennyNeural.mp3"
    assert stored.provenance.byte_size == 5120
    assert stored.provenance.duration_ms == 900
    assert stored.provenance.status is AudioSynthesisStatus.SYNTHESIZED
    assert reusable is not None
    assert reusable.job_id == job.id
    assert reusable.item_key == "line-1"
    assert reusable.provenance.text_hash == record.normalized_input.text_hash
    assert reusable.provenance.ssml_hash == record.normalized_input.ssml_hash
