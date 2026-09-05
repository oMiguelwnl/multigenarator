"""Persistence helpers for frozen export snapshots and artifact manifests."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from multilang.db.models import CardExportModel, DeckExportModel, GenerationJob
from multilang.domain.exporting import (
    ExportArtifactFormat,
    ExportArtifactStatus,
    ExportCardIdentity,
    ExportCardRow,
    ExportDeckArtifact,
    build_export_note_guid,
)
from multilang.domain.jobs import SupportedLanguage


class ExportRepository:
    """Repository boundary for persisted export snapshots."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_card_snapshot(self, record: ExportCardRow) -> ExportCardRow:
        return self.upsert_card_snapshots([record])[0]

    def upsert_card_snapshots(self, records: list[ExportCardRow]) -> list[ExportCardRow]:
        if not records:
            return []

        job_ids = {record.identity.job_id for record in records}
        if len(job_ids) != 1:
            raise ValueError("cannot bulk upsert export snapshots for multiple jobs")

        job_id = next(iter(job_ids))
        run_key = self._resolve_run_key(job_id)
        existing = {
            row.item_key: row
            for row in self.session.scalars(
                select(CardExportModel).where(CardExportModel.job_id == job_id)
            )
        }

        ordered_rows: list[CardExportModel] = []
        for record in records:
            payload = self._card_payload(record, run_key=run_key)
            row = existing.get(record.identity.item_key)
            if row is None:
                row = CardExportModel(id=str(uuid4()), **payload)
                self.session.add(row)
                existing[record.identity.item_key] = row
            else:
                for field, value in payload.items():
                    setattr(row, field, value)
            ordered_rows.append(row)

        self.session.commit()
        for row in ordered_rows:
            self.session.refresh(row)
        return [self._to_card_domain(row) for row in ordered_rows]

    def list_card_snapshots(self, job_id: str) -> list[ExportCardRow]:
        rows = self.session.scalars(
            select(CardExportModel)
            .where(CardExportModel.job_id == job_id)
            .order_by(CardExportModel.sort_index.asc(), CardExportModel.item_key.asc())
        )
        return [self._to_card_domain(row) for row in rows]

    def upsert_deck_export(self, artifact: ExportDeckArtifact) -> ExportDeckArtifact:
        row = self.session.scalar(
            select(DeckExportModel).where(
                DeckExportModel.job_id == artifact.job_id,
                DeckExportModel.export_format == artifact.export_format.value,
            )
        )

        payload = {
            "job_id": artifact.job_id,
            "run_key": self._resolve_run_key(artifact.job_id),
            "export_format": artifact.export_format.value,
            "deck_name": artifact.deck_name,
            "output_path": artifact.output_path,
            "card_count": artifact.card_count,
            "status": artifact.status.value,
            "frequency_bundle_sha256": artifact.frequency_bundle_sha256,
            "export_manifest_sha256": artifact.export_manifest_sha256,
            "export_gate_receipt_sha256": artifact.export_gate_receipt_sha256,
        }

        if row is None:
            row = DeckExportModel(id=str(uuid4()), **payload)
            self.session.add(row)
        else:
            for field, value in payload.items():
                setattr(row, field, value)

        self.session.commit()
        self.session.refresh(row)
        return self._to_artifact_domain(row)

    def list_deck_exports(self, job_id: str) -> list[ExportDeckArtifact]:
        rows = self.session.scalars(
            select(DeckExportModel)
            .where(DeckExportModel.job_id == job_id)
            .order_by(DeckExportModel.export_format.asc())
        )
        return [self._to_artifact_domain(row) for row in rows]

    def _resolve_run_key(self, job_id: str) -> str:
        job = self.session.scalar(select(GenerationJob).where(GenerationJob.id == job_id))
        if job is None:
            raise ValueError(f"unknown job_id: {job_id}")
        return job.run_key

    @staticmethod
    def _card_payload(record: ExportCardRow, *, run_key: str) -> dict[str, object]:
        return {
            "job_id": record.identity.job_id,
            "run_key": run_key,
            "item_key": record.identity.item_key,
            "lemma_key": record.identity.lemma_key,
            "note_guid": build_export_note_guid(record.identity),
            "sort_index": record.sort_index,
            "frequency_level": record.frequency_level,
            "frequency_bundle_sha256": record.frequency_bundle_sha256,
            "export_gate_receipt_sha256": record.export_gate_receipt_sha256,
            "word": record.word,
            "front_of_card": record.front_of_card,
            "ipa": record.ipa,
            "definitions": record.definitions,
            "example_sentence": record.example_sentence,
            "translation": record.translation,
            "word_audio": record.word_audio,
            "sentence_audio": record.sentence_audio,
            "image": record.image,
            "gramatica": record.gramatica,
            "word_reading": record.word_reading,
            "word_romaji": record.word_romaji,
            "sentence_furigana": record.sentence_furigana,
            "sentence_romaji": record.sentence_romaji,
            "mandarin_word_pinyin": record.mandarin_word_pinyin,
            "mandarin_word_traditional": record.mandarin_word_traditional,
            "mandarin_sentence_pinyin": record.mandarin_sentence_pinyin,
            "mandarin_sentence_traditional": record.mandarin_sentence_traditional,
        }

    def _to_card_domain(self, row: CardExportModel) -> ExportCardRow:
        return ExportCardRow(
            identity=ExportCardIdentity(
                language=SupportedLanguage(row.job.language),
                source_type=row.job.source_type,
                job_id=row.job_id,
                item_key=row.item_key,
                lemma_key=row.lemma_key,
                sort_index=row.sort_index,
            ),
            note_guid=row.note_guid,
            sort_index=row.sort_index,
            frequency_level=row.frequency_level,
            frequency_bundle_sha256=row.frequency_bundle_sha256,
            export_gate_receipt_sha256=row.export_gate_receipt_sha256,
            word=row.word,
            front_of_card=row.front_of_card,
            ipa=row.ipa,
            definitions=row.definitions,
            example_sentence=row.example_sentence,
            translation=row.translation,
            word_audio=row.word_audio,
            sentence_audio=row.sentence_audio,
            image=row.image,
            gramatica=row.gramatica,
            word_reading=row.word_reading,
            word_romaji=row.word_romaji,
            sentence_furigana=row.sentence_furigana,
            sentence_romaji=row.sentence_romaji,
            mandarin_word_pinyin=row.mandarin_word_pinyin,
            mandarin_word_traditional=row.mandarin_word_traditional,
            mandarin_sentence_pinyin=row.mandarin_sentence_pinyin,
            mandarin_sentence_traditional=row.mandarin_sentence_traditional,
        )

    def _to_artifact_domain(self, row: DeckExportModel) -> ExportDeckArtifact:
        return ExportDeckArtifact(
            job_id=row.job_id,
            export_format=ExportArtifactFormat(row.export_format),
            deck_name=row.deck_name,
            output_path=row.output_path,
            card_count=row.card_count,
            status=ExportArtifactStatus(row.status),
            frequency_bundle_sha256=row.frequency_bundle_sha256,
            export_manifest_sha256=row.export_manifest_sha256,
            export_gate_receipt_sha256=row.export_gate_receipt_sha256,
        )


__all__ = ["ExportRepository"]
