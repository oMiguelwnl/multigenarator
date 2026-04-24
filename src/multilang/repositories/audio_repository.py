"""Persistence helpers for Phase 4 audio assets."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from multilang.db.models import AudioAssetModel, GenerationJob
from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioFormat,
    AudioProvenance,
    AudioProvider,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)


class AudioRepository:
    """Repository boundary for persisted word and sentence audio assets."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_audio_asset(self, record: AudioAssetRecord) -> AudioAssetRecord:
        row = self.session.scalar(
            select(AudioAssetModel).where(
                AudioAssetModel.job_id == record.job_id,
                AudioAssetModel.item_key == record.item_key,
                AudioAssetModel.asset_kind == record.asset_kind.value,
            )
        )

        payload = {
            "job_id": record.job_id,
            "run_key": self._resolve_run_key(record.job_id),
            "item_key": record.item_key,
            "asset_kind": record.asset_kind.value,
            "display_text": record.display_text,
            "tts_text": record.normalized_input.tts_text,
            "ssml_text": record.normalized_input.ssml_text,
            "provider": record.provenance.provider.value,
            "voice_id": record.provenance.voice_id,
            "locale": record.provenance.locale,
            "format": record.provenance.format.value,
            "text_hash": record.provenance.text_hash,
            "ssml_hash": record.provenance.ssml_hash,
            "storage_path": record.provenance.storage_path,
            "byte_size": record.provenance.byte_size,
            "duration_ms": record.provenance.duration_ms,
            "status": record.provenance.status.value,
            "fallback_used": record.provenance.fallback_used,
        }

        if row is None:
            row = AudioAssetModel(id=str(uuid4()), **payload)
            self.session.add(row)
        else:
            for field, value in payload.items():
                setattr(row, field, value)

        self.session.commit()
        self.session.refresh(row)
        return self._to_domain(row)

    def get_asset(
        self, job_id: str, item_key: str, asset_kind: AudioAssetKind
    ) -> AudioAssetRecord | None:
        row = self.session.scalar(
            select(AudioAssetModel).where(
                AudioAssetModel.job_id == job_id,
                AudioAssetModel.item_key == item_key,
                AudioAssetModel.asset_kind == asset_kind.value,
            )
        )
        return self._to_domain(row) if row is not None else None

    def list_assets_for_job(self, job_id: str) -> list[AudioAssetRecord]:
        rows = self.session.scalars(
            select(AudioAssetModel)
            .where(AudioAssetModel.job_id == job_id)
            .order_by(AudioAssetModel.item_key.asc(), AudioAssetModel.asset_kind.asc())
        )
        return [self._to_domain(row) for row in rows]

    def list_failed_assets(self, job_id: str) -> list[AudioAssetRecord]:
        rows = self.session.scalars(
            select(AudioAssetModel)
            .where(
                AudioAssetModel.job_id == job_id,
                AudioAssetModel.status == AudioSynthesisStatus.FAILED.value,
            )
            .order_by(AudioAssetModel.item_key.asc(), AudioAssetModel.asset_kind.asc())
        )
        return [self._to_domain(row) for row in rows]

    def get_reusable_asset(
        self,
        *,
        asset_kind: AudioAssetKind,
        text_hash: str,
        ssml_hash: str,
        voice_id: str,
        format: AudioFormat,
    ) -> AudioAssetRecord | None:
        row = self.session.scalar(
            select(AudioAssetModel)
            .where(
                AudioAssetModel.asset_kind == asset_kind.value,
                AudioAssetModel.text_hash == text_hash,
                AudioAssetModel.ssml_hash == ssml_hash,
                AudioAssetModel.voice_id == voice_id,
                AudioAssetModel.format == format.value,
                AudioAssetModel.status == AudioSynthesisStatus.SYNTHESIZED.value,
                AudioAssetModel.byte_size > 0,
            )
            .order_by(AudioAssetModel.created_at.asc())
        )
        return self._to_domain(row) if row is not None else None

    def _resolve_run_key(self, job_id: str) -> str:
        job = self.session.scalar(select(GenerationJob).where(GenerationJob.id == job_id))
        if job is None:
            raise ValueError(f"unknown job_id: {job_id}")
        return job.run_key

    def _to_domain(self, row: AudioAssetModel) -> AudioAssetRecord:
        normalized_input = NormalizedTtsInput(
            display_text=row.display_text,
            tts_text=row.tts_text,
            ssml_text=row.ssml_text,
            text_hash=row.text_hash,
            ssml_hash=row.ssml_hash,
        )
        return AudioAssetRecord(
            job_id=row.job_id,
            item_key=row.item_key,
            asset_kind=AudioAssetKind(row.asset_kind),
            display_text=row.display_text,
            normalized_input=normalized_input,
            provenance=AudioProvenance(
                provider=AudioProvider(row.provider),
                voice_id=row.voice_id,
                locale=row.locale,
                format=AudioFormat(row.format),
                text_hash=row.text_hash,
                ssml_hash=row.ssml_hash,
                storage_path=row.storage_path,
                byte_size=row.byte_size,
                duration_ms=row.duration_ms,
                status=AudioSynthesisStatus(row.status),
                fallback_used=row.fallback_used,
            ),
        )


__all__ = ["AudioRepository"]
