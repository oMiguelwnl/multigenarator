"""Persistence helpers for private highlight imports and safe manifests."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from multilang.db.models import (
    GenerationJob,
    HighlightImportManifestModel,
    HighlightImportRecordModel,
    HighlightPrivateExcerptRevisionModel,
)
from multilang.domain.highlights import HighlightImportManifest, NormalizedHighlight
from multilang.domain.korean import canonical_json_sha256


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class HighlightPrivateExcerptRevisionRecord(_Record):
    """Privileged local-only private excerpt revision value."""

    excerpt_revision_id: str
    highlight_id: str
    import_content_hash: str
    source_content_hash: str
    source_index: int = Field(ge=0)
    source_path: str
    raw_location: str | None = None
    normalized_text: str
    revision_number: int = Field(ge=1)


class KoreanHighlightSafeInventoryRow(_Record):
    """Safe reference to the current private boundary for one highlight candidate."""

    candidate_id: str
    highlight_id: str
    import_content_hash: str
    source_content_hash: str
    source_index: int = Field(ge=0)
    occurrence_count: int = Field(ge=1)
    excerpt_revision_id: str
    revision_number: int = Field(ge=1)

    @field_validator("import_content_hash", "source_content_hash")
    @classmethod
    def hashes_must_be_hex(cls, value: str) -> str:
        _require_sha256(value, "hash")
        return value


class KoreanHighlightSafeInventory(_Record):
    job_id: str
    inventory_root_sha256: str
    candidate_count: int = Field(ge=0)
    rows: tuple[KoreanHighlightSafeInventoryRow, ...]

    @field_validator("inventory_root_sha256")
    @classmethod
    def root_must_be_hex(cls, value: str) -> str:
        _require_sha256(value, "inventory_root_sha256")
        return value


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
        if self._job_language(job_id) == "ko":
            return self._append_korean_private_revisions(job_id, import_content_hash, records)

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

    def list_korean_safe_inventory(self, job_id: str) -> KoreanHighlightSafeInventory:
        rows = self.session.execute(
            select(
                HighlightPrivateExcerptRevisionModel.highlight_id,
                HighlightPrivateExcerptRevisionModel.import_content_hash,
                HighlightPrivateExcerptRevisionModel.source_content_hash,
                HighlightPrivateExcerptRevisionModel.source_index,
                HighlightPrivateExcerptRevisionModel.excerpt_revision_id,
                HighlightPrivateExcerptRevisionModel.revision_number,
            )
            .where(HighlightPrivateExcerptRevisionModel.job_id == job_id)
            .order_by(
                HighlightPrivateExcerptRevisionModel.source_index.asc(),
                HighlightPrivateExcerptRevisionModel.revision_number.asc(),
            )
        ).all()
        latest_by_highlight: dict[str, object] = {}
        for row in rows:
            latest_by_highlight[row.highlight_id] = row
        safe_rows = tuple(
            KoreanHighlightSafeInventoryRow(
                candidate_id=row.highlight_id,
                highlight_id=row.highlight_id,
                import_content_hash=row.import_content_hash,
                source_content_hash=row.source_content_hash,
                source_index=row.source_index,
                occurrence_count=1,
                excerpt_revision_id=row.excerpt_revision_id,
                revision_number=row.revision_number,
            )
            for row in sorted(
                latest_by_highlight.values(),
                key=lambda current: (current.source_index, current.highlight_id),
            )
        )
        root_payload = {
            "job_id": job_id,
            "candidate_count": len(safe_rows),
            "rows": [row.model_dump(mode="json") for row in safe_rows],
        }
        return KoreanHighlightSafeInventory(
            job_id=job_id,
            inventory_root_sha256=canonical_json_sha256(root_payload),
            candidate_count=len(safe_rows),
            rows=safe_rows,
        )

    def load_private_excerpt_revision(
        self,
        job_id: str,
        excerpt_revision_id: str,
    ) -> HighlightPrivateExcerptRevisionRecord | None:
        row = self.session.scalar(
            select(HighlightPrivateExcerptRevisionModel).where(
                HighlightPrivateExcerptRevisionModel.job_id == job_id,
                HighlightPrivateExcerptRevisionModel.excerpt_revision_id == excerpt_revision_id,
            )
        )
        if row is None:
            return None
        return _private_revision_record(row)

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

    def _append_korean_private_revisions(
        self,
        job_id: str,
        import_content_hash: str,
        records: list[NormalizedHighlight],
    ) -> int:
        _require_sha256(import_content_hash, "import_content_hash")
        for highlight in records:
            _require_sha256(highlight.provenance.content_hash, "source_content_hash")
            existing_exact = self.session.scalar(
                select(HighlightPrivateExcerptRevisionModel).where(
                    HighlightPrivateExcerptRevisionModel.job_id == job_id,
                    HighlightPrivateExcerptRevisionModel.highlight_id == highlight.highlight_id,
                    HighlightPrivateExcerptRevisionModel.source_content_hash == highlight.provenance.content_hash,
                    HighlightPrivateExcerptRevisionModel.normalized_text == highlight.text,
                )
            )
            if existing_exact is not None:
                continue

            next_revision = int(
                self.session.scalar(
                    select(func.max(HighlightPrivateExcerptRevisionModel.revision_number)).where(
                        HighlightPrivateExcerptRevisionModel.job_id == job_id,
                        HighlightPrivateExcerptRevisionModel.highlight_id == highlight.highlight_id,
                    )
                )
                or 0
            ) + 1
            excerpt_revision_id = _stable_id(
                "excerpt",
                canonical_json_sha256(
                    {
                        "job_id": job_id,
                        "highlight_id": highlight.highlight_id,
                        "revision_number": next_revision,
                        "source_content_hash": highlight.provenance.content_hash,
                    }
                ),
            )
            self.session.add(
                HighlightPrivateExcerptRevisionModel(
                    id=str(uuid4()),
                    job_id=job_id,
                    excerpt_revision_id=excerpt_revision_id,
                    highlight_id=highlight.highlight_id,
                    import_content_hash=import_content_hash,
                    source_content_hash=highlight.provenance.content_hash,
                    source_index=highlight.provenance.source_index,
                    source_path=highlight.provenance.source_path,
                    raw_location=highlight.provenance.raw_location,
                    normalized_text=highlight.text,
                    revision_number=next_revision,
                )
            )
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ValueError("korean private highlight revision conflict") from exc
        return len(records)

    def _job_language(self, job_id: str) -> str | None:
        return self.session.scalar(select(GenerationJob.language).where(GenerationJob.id == job_id))

    @staticmethod
    def _to_manifest(row: HighlightImportManifestModel) -> HighlightImportManifest:
        return HighlightImportManifest(
            import_content_hash=row.import_content_hash,
            candidate_keys=list(row.candidate_keys or []),
            counts=dict(row.counts or {}),
        )


def _private_revision_record(row: HighlightPrivateExcerptRevisionModel) -> HighlightPrivateExcerptRevisionRecord:
    return HighlightPrivateExcerptRevisionRecord(
        excerpt_revision_id=row.excerpt_revision_id,
        highlight_id=row.highlight_id,
        import_content_hash=row.import_content_hash,
        source_content_hash=row.source_content_hash,
        source_index=row.source_index,
        source_path=row.source_path,
        raw_location=row.raw_location,
        normalized_text=row.normalized_text,
        revision_number=row.revision_number,
    )


def _stable_id(prefix: str, digest: str) -> str:
    return f"{prefix}-{digest[:32]}"


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")


__all__ = [
    "HighlightImportRepository",
    "HighlightPrivateExcerptRevisionRecord",
    "KoreanHighlightSafeInventory",
    "KoreanHighlightSafeInventoryRow",
]
