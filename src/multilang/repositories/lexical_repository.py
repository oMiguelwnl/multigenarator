"""Persistence helpers for grounded lexical candidates."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from multilang.db.models import LexicalCandidate
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance


class LexicalRepository:
    """Repository boundary for lexical candidate persistence and queries."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_candidate(
        self,
        *,
        job_id: str,
        run_key: str,
        item_key: str,
        source_type: str,
        normalized_source: str,
        candidate: LexicalCardCandidate,
    ) -> LexicalCardCandidate:
        row = self.session.scalar(
            select(LexicalCandidate).where(
                LexicalCandidate.job_id == job_id,
                LexicalCandidate.item_key == item_key,
            )
        )

        payload = {
            "job_id": job_id,
            "run_key": run_key,
            "item_key": item_key,
            "source_type": source_type,
            "submitted_form": candidate.submitted_form,
            "normalized_source": normalized_source,
            "display_form": candidate.display_form,
            "lemma": candidate.lemma,
            "lemma_key": candidate.lemma_key,
            "frequency_rank": candidate.frequency_rank,
            "frequency_level": candidate.frequency_level,
            "definitions_html": candidate.definitions_html,
            "definition_language": candidate.definition_language,
            "ipa": candidate.ipa,
            "translation_target_language": candidate.translation_target_language,
            "grounding_status": candidate.grounding_status.value,
            "warning_code": candidate.warning_code,
            "warning_detail": candidate.warning_detail,
            "provenance": candidate.provenance.model_dump(mode="json"),
        }

        if row is None:
            row = LexicalCandidate(id=str(uuid4()), **payload)
            self.session.add(row)
        else:
            for field, value in payload.items():
                setattr(row, field, value)

        self.session.commit()
        self.session.refresh(row)
        return self._to_domain(row)

    def list_candidates(self, job_id: str) -> list[LexicalCardCandidate]:
        rows = self.session.scalars(
            select(LexicalCandidate)
            .where(LexicalCandidate.job_id == job_id)
            .order_by(LexicalCandidate.item_key.asc())
        )
        return [self._to_domain(row) for row in rows]

    def get_candidate_for_item(self, job_id: str, item_key: str) -> LexicalCandidate | None:
        return self.session.scalar(
            select(LexicalCandidate).where(
                LexicalCandidate.job_id == job_id,
                LexicalCandidate.item_key == item_key,
            )
        )

    def count_pending_candidates(self, job_id: str) -> int:
        statement = select(func.count(LexicalCandidate.id)).where(
            LexicalCandidate.job_id == job_id,
            or_(
                LexicalCandidate.grounding_status == GroundingStatus.PENDING.value,
                LexicalCandidate.grounding_status == GroundingStatus.INSUFFICIENT.value,
            ),
        )
        return int(self.session.scalar(statement) or 0)

    def _to_domain(self, row: LexicalCandidate) -> LexicalCardCandidate:
        return LexicalCardCandidate(
            submitted_form=row.submitted_form,
            display_form=row.display_form,
            lemma=row.lemma,
            lemma_key=row.lemma_key,
            frequency_rank=row.frequency_rank,
            frequency_level=row.frequency_level,
            definitions_html=row.definitions_html,
            definition_language=row.definition_language,
            ipa=row.ipa,
            translation_target_language=row.translation_target_language,
            grounding_status=GroundingStatus(row.grounding_status),
            warning_code=row.warning_code,
            warning_detail=row.warning_detail,
            provenance=LexicalProvenance.model_validate(row.provenance),
        )
