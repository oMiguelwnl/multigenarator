"""Persistence helpers for Phase 3 text-quality records."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from multilang.db.models import LexicalCandidate, TextQualityRecordModel
from multilang.domain.lexicon import GroundingStatus
from multilang.domain.text_quality import (
    ConfidenceLabel,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationFlag,
    ValidationStatus,
)


class TextRepository:
    """Repository boundary for sentence, translation, and review persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_text_record(self, record: TextQualityRecord) -> TextQualityRecord:
        row = self.session.scalar(
            select(TextQualityRecordModel).where(
                TextQualityRecordModel.job_id == record.job_id,
                TextQualityRecordModel.item_key == record.item_key,
            )
        )

        payload = {
            "job_id": record.job_id,
            "lexical_candidate_id": record.lexical_candidate_id,
            "run_key": self._resolve_run_key(record.job_id, record.lexical_candidate_id),
            "item_key": record.item_key,
            "example_sentence": record.example_sentence,
            "translation_text": record.translation_text,
            "generation_status": record.generation_status.value,
            "validation_status": record.validation_status.value,
            "review_status": record.review_status.value,
            "repair_attempt_count": record.repair_attempt_count,
            "confidence_score": record.confidence_score,
            "confidence_label": record.confidence_label.value,
            "validation_flags": [flag.model_dump(mode="json") for flag in record.validation_flags],
            "review_reason": record.review_reason,
            "sentence_provenance": record.sentence_provenance.model_dump(mode="json"),
            "translation_provenance": record.translation_provenance.model_dump(mode="json"),
        }

        if row is None:
            row = TextQualityRecordModel(id=str(uuid4()), **payload)
            self.session.add(row)
        else:
            for field, value in payload.items():
                setattr(row, field, value)

        self.session.commit()
        self.session.refresh(row)
        return self._to_domain(row)

    def get_text_record(self, job_id: str, item_key: str) -> TextQualityRecord | None:
        row = self.session.scalar(
            select(TextQualityRecordModel).where(
                TextQualityRecordModel.job_id == job_id,
                TextQualityRecordModel.item_key == item_key,
            )
        )
        return self._to_domain(row) if row is not None else None

    def list_records_for_job(self, job_id: str) -> list[TextQualityRecord]:
        rows = self.session.scalars(
            select(TextQualityRecordModel)
            .where(TextQualityRecordModel.job_id == job_id)
            .order_by(TextQualityRecordModel.item_key.asc())
        )
        return [self._to_domain(row) for row in rows]

    def list_example_sentences_for_job(
        self,
        job_id: str,
        *,
        exclude_item_key: str | None = None,
    ) -> list[str]:
        statement = select(TextQualityRecordModel.example_sentence).where(
            TextQualityRecordModel.job_id == job_id,
            TextQualityRecordModel.example_sentence.is_not(None),
        )
        if exclude_item_key is not None:
            statement = statement.where(TextQualityRecordModel.item_key != exclude_item_key)

        rows = self.session.scalars(statement.order_by(TextQualityRecordModel.item_key.asc()))
        return [sentence for sentence in rows if sentence]

    def list_flagged_records(self, job_id: str) -> list[TextQualityRecord]:
        rows = self.session.scalars(
            select(TextQualityRecordModel)
            .where(
                TextQualityRecordModel.job_id == job_id,
                TextQualityRecordModel.review_status == ReviewStatus.REVIEW_REQUIRED.value,
            )
            .order_by(TextQualityRecordModel.item_key.asc())
        )
        return [self._to_domain(row) for row in rows]

    def get_source_metadata_for_item(self, job_id: str, item_key: str) -> dict[str, object] | None:
        row = self.session.execute(
            select(LexicalCandidate.source_type, LexicalCandidate.item_key).where(
                LexicalCandidate.job_id == job_id,
                LexicalCandidate.item_key == item_key,
            )
        ).first()
        if row is None:
            return None
        return {"source_type": row[0], "item_key": row[1]}

    def list_accepted_records(self, job_id: str) -> list[TextQualityRecord]:
        rows = self.session.scalars(
            select(TextQualityRecordModel)
            .where(
                TextQualityRecordModel.job_id == job_id,
                TextQualityRecordModel.review_status == ReviewStatus.ACCEPTED.value,
                TextQualityRecordModel.validation_status == ValidationStatus.PASSED.value,
            )
            .order_by(TextQualityRecordModel.item_key.asc())
        )
        return [self._to_domain(row) for row in rows]

    def list_generation_candidates(self, job_id: str, *, missing_only: bool = False) -> list[LexicalCandidate]:
        text_filter = (
            TextQualityRecordModel.id.is_(None)
            if missing_only
            else or_(
                TextQualityRecordModel.id.is_(None),
                TextQualityRecordModel.review_status != ReviewStatus.ACCEPTED.value,
            )
        )
        rows = self.session.scalars(
            select(LexicalCandidate)
            .outerjoin(
                TextQualityRecordModel,
                TextQualityRecordModel.lexical_candidate_id == LexicalCandidate.id,
            )
            .where(
                LexicalCandidate.job_id == job_id,
                LexicalCandidate.grounding_status == GroundingStatus.GROUNDED.value,
                text_filter,
            )
            .order_by(LexicalCandidate.item_key.asc())
        )
        return list(rows)

    def _resolve_run_key(self, job_id: str, lexical_candidate_id: str) -> str:
        lexical_candidate = self.session.scalar(
            select(LexicalCandidate).where(
                LexicalCandidate.id == lexical_candidate_id,
                LexicalCandidate.job_id == job_id,
            )
        )
        if lexical_candidate is None:
            raise ValueError(
                f"unknown lexical candidate {lexical_candidate_id!r} for job {job_id!r}"
            )
        return lexical_candidate.run_key

    def _to_domain(self, row: TextQualityRecordModel) -> TextQualityRecord:
        return TextQualityRecord(
            job_id=row.job_id,
            item_key=row.item_key,
            lexical_candidate_id=row.lexical_candidate_id,
            example_sentence=row.example_sentence,
            translation_text=row.translation_text,
            generation_status=TextGenerationStatus(row.generation_status),
            validation_status=ValidationStatus(row.validation_status),
            review_status=ReviewStatus(row.review_status),
            repair_attempt_count=row.repair_attempt_count,
            confidence_score=row.confidence_score,
            confidence_label=ConfidenceLabel(row.confidence_label),
            validation_flags=[ValidationFlag.model_validate(flag) for flag in row.validation_flags],
            review_reason=row.review_reason,
            sentence_provenance=TextProvenance.model_validate(row.sentence_provenance),
            translation_provenance=TextProvenance.model_validate(row.translation_provenance),
        )
