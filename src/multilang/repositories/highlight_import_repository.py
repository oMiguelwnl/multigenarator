"""Persistence helpers for private highlight imports and safe manifests."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from multilang.db.models import HighlightImportManifestModel, HighlightImportRecordModel
from multilang.domain.highlights import HighlightImportManifest, NormalizedHighlight


class HighlightImportRepository:
    """Repository boundary for private highlight records and safe manifests."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_import_records(
        self,
        job_id: str,
        import_content_hash: str,
        highlights: Iterable[NormalizedHighlight],
    ) -> int:
        records = list(highlights)
        if not records:
            return 0

        existing = {
            row.highlight_id: row
            for row in self.session.scalars(
                select(HighlightImportRecordModel).where(
                    HighlightImportRecordModel.job_id == job_id,
                    HighlightImportRecordModel.highlight_id.in_([highlight.highlight_id for highlight in records]),
                )
            )
        }

        for highlight in records:
            payload = {
                "job_id": job_id,
                "import_content_hash": import_content_hash,
                "highlight_id": highlight.highlight_id,
                "source_content_hash": highlight.provenance.content_hash,
                "source_index": highlight.provenance.source_index,
                "normalized_text": highlight.text,
            }
            row = existing.get(highlight.highlight_id)
            if row is None:
                self.session.add(HighlightImportRecordModel(id=str(uuid4()), **payload))
                continue
            for field, value in payload.items():
                setattr(row, field, value)

        self.session.commit()
        return len(records)

    def upsert_import_manifest(
        self,
        job_id: str,
        manifest: HighlightImportManifest,
    ) -> HighlightImportManifest:
        row = self.session.scalar(
            select(HighlightImportManifestModel).where(HighlightImportManifestModel.job_id == job_id)
        )
        payload = {
            "job_id": job_id,
            "import_content_hash": manifest.import_content_hash,
            "candidate_keys": list(manifest.candidate_keys),
            "counts": dict(manifest.counts),
        }
        if row is None:
            row = HighlightImportManifestModel(id=str(uuid4()), **payload)
            self.session.add(row)
        else:
            for field, value in payload.items():
                setattr(row, field, value)

        self.session.commit()
        self.session.refresh(row)
        return self._to_manifest(row)

    def get_manifest(self, job_id: str) -> HighlightImportManifest | None:
        row = self.session.scalar(
            select(HighlightImportManifestModel).where(HighlightImportManifestModel.job_id == job_id)
        )
        if row is None:
            return None
        return self._to_manifest(row)

    def list_private_records(self, job_id: str) -> list[HighlightImportRecordModel]:
        return list(
            self.session.scalars(
                select(HighlightImportRecordModel)
                .where(HighlightImportRecordModel.job_id == job_id)
                .order_by(HighlightImportRecordModel.source_index.asc())
            )
        )

    def get_private_record(self, job_id: str, highlight_id: str) -> HighlightImportRecordModel | None:
        return self.session.scalar(
            select(HighlightImportRecordModel).where(
                HighlightImportRecordModel.job_id == job_id,
                HighlightImportRecordModel.highlight_id == highlight_id,
            )
        )

    @staticmethod
    def _to_manifest(row: HighlightImportManifestModel) -> HighlightImportManifest:
        return HighlightImportManifest(
            import_content_hash=row.import_content_hash,
            candidate_keys=list(row.candidate_keys or []),
            counts=dict(row.counts or {}),
        )


__all__ = ["HighlightImportRepository"]
