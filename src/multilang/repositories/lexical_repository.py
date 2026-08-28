"""Persistence helpers for grounded lexical candidates."""

from __future__ import annotations

from collections.abc import Iterable
from collections import Counter
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from multilang.db.models import LexicalCandidate
from multilang.domain.korean import KoreanLexicalIdentity
from multilang.domain.lexicon import (
    GroundingStatus,
    KoreanFrequencyLexicalEvidence,
    LexicalCardCandidate,
    LexicalProvenance,
)


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
        payload = self._candidate_payload(
            job_id=job_id,
            run_key=run_key,
            item_key=item_key,
            source_type=source_type,
            normalized_source=normalized_source,
            candidate=candidate,
        )
        if source_type == "frequency":
            self._reject_frequency_duplicate(
                job_id=job_id,
                item_key=item_key,
                lemma_key=str(payload["lemma_key"]),
                display_form=str(payload["display_form"]),
            )
        row = self.session.scalar(
            select(LexicalCandidate).where(
                LexicalCandidate.job_id == job_id,
                LexicalCandidate.item_key == item_key,
            )
        )

        if row is None:
            row = LexicalCandidate(id=str(uuid4()), **payload)
            self.session.add(row)
        else:
            for field, value in payload.items():
                setattr(row, field, value)

        self.session.commit()
        self.session.refresh(row)
        return self._to_domain(row)

    def upsert_candidates(
        self,
        *,
        job_id: str,
        run_key: str,
        source_type: str,
        candidates: Iterable[tuple[str, str, LexicalCardCandidate]],
    ) -> None:
        candidate_rows = list(candidates)
        if not candidate_rows:
            return

        if source_type == "frequency":
            self._reject_frequency_batch_duplicates(job_id=job_id, candidate_rows=candidate_rows)

        item_keys = [item_key for item_key, _, _ in candidate_rows]
        existing = {
            row.item_key: row
            for row in self.session.scalars(
                select(LexicalCandidate).where(
                    LexicalCandidate.job_id == job_id,
                    LexicalCandidate.item_key.in_(item_keys),
                )
            )
        }

        for item_key, normalized_source, candidate in candidate_rows:
            payload = self._candidate_payload(
                job_id=job_id,
                run_key=run_key,
                item_key=item_key,
                source_type=source_type,
                normalized_source=normalized_source,
                candidate=candidate,
            )
            row = existing.get(item_key)
            if row is None:
                self.session.add(LexicalCandidate(id=str(uuid4()), **payload))
                continue
            for field, value in payload.items():
                setattr(row, field, value)

        self.session.commit()

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

    def _reject_frequency_batch_duplicates(
        self,
        *,
        job_id: str,
        candidate_rows: list[tuple[str, str, LexicalCardCandidate]],
    ) -> None:
        lemma_counts = Counter(candidate.lemma_key.casefold() for _, _, candidate in candidate_rows)
        display_counts = Counter(candidate.display_form.casefold() for _, _, candidate in candidate_rows)
        if duplicates := [key for key, count in lemma_counts.items() if count > 1]:
            raise ValueError(f"duplicate frequency lemma_key values before persistence: {duplicates[:5]}")
        if duplicates := [key for key, count in display_counts.items() if count > 1]:
            raise ValueError(f"duplicate frequency display_form values before persistence: {duplicates[:5]}")

        item_keys = {item_key for item_key, _, _ in candidate_rows}
        for item_key, _, candidate in candidate_rows:
            self._reject_frequency_duplicate(
                job_id=job_id,
                item_key=item_key,
                lemma_key=candidate.lemma_key,
                display_form=candidate.display_form,
                excluded_item_keys=item_keys,
            )

    def _reject_frequency_duplicate(
        self,
        *,
        job_id: str,
        item_key: str,
        lemma_key: str,
        display_form: str,
        excluded_item_keys: set[str] | None = None,
    ) -> None:
        excluded = excluded_item_keys or {item_key}
        existing = self.session.scalars(
            select(LexicalCandidate).where(
                LexicalCandidate.job_id == job_id,
                LexicalCandidate.source_type == "frequency",
                LexicalCandidate.item_key.not_in(excluded),
                or_(
                    func.lower(LexicalCandidate.lemma_key) == lemma_key.casefold(),
                    func.lower(LexicalCandidate.display_form) == display_form.casefold(),
                ),
            )
        ).first()
        if existing is not None:
            raise ValueError(
                "duplicate frequency lexical candidate across levels: "
                f"{item_key} conflicts with {existing.item_key}"
            )

    @staticmethod
    def _candidate_payload(
        *,
        job_id: str,
        run_key: str,
        item_key: str,
        source_type: str,
        normalized_source: str,
        candidate: LexicalCardCandidate,
    ) -> dict[str, object]:
        evidence = candidate.korean_frequency_evidence
        if evidence is not None and source_type != "frequency":
            raise ValueError("Korean frequency lexical evidence requires frequency source type")
        return {
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
            "spoken_form": candidate.spoken_form,
            "translation_target_language": candidate.translation_target_language,
            "grounding_status": candidate.grounding_status.value,
            "warning_code": candidate.warning_code,
            "warning_detail": candidate.warning_detail,
            "provenance": candidate.provenance.model_dump(mode="json"),
            "korean_identity": (
                candidate.korean_identity.model_dump(mode="json")
                if candidate.korean_identity is not None
                else None
            ),
            "frequency_bundle_sha256": evidence.bundle_sha256 if evidence is not None else None,
            "frequency_source_sha256": evidence.source_sha256 if evidence is not None else None,
            "source_review_receipt_sha256": evidence.source_review_receipt_sha256 if evidence is not None else None,
            "source_review_aggregate_sha256": evidence.source_review_aggregate_sha256 if evidence is not None else None,
            "lexical_evidence": evidence.model_dump(mode="json") if evidence is not None else None,
        }

    def _to_domain(self, row: LexicalCandidate) -> LexicalCardCandidate:
        evidence = self._korean_frequency_evidence_from_row(row)
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
            spoken_form=row.spoken_form,
            translation_target_language=row.translation_target_language,
            grounding_status=GroundingStatus(row.grounding_status),
            warning_code=row.warning_code,
            warning_detail=row.warning_detail,
            provenance=LexicalProvenance.model_validate(row.provenance),
            korean_identity=(
                KoreanLexicalIdentity.model_validate(row.korean_identity)
                if row.korean_identity is not None
                else None
            ),
            korean_frequency_evidence=evidence,
        )

    @staticmethod
    def _korean_frequency_evidence_from_row(
        row: LexicalCandidate,
    ) -> KoreanFrequencyLexicalEvidence | None:
        hash_columns = {
            "frequency_bundle_sha256": row.frequency_bundle_sha256,
            "frequency_source_sha256": row.frequency_source_sha256,
            "source_review_receipt_sha256": row.source_review_receipt_sha256,
            "source_review_aggregate_sha256": row.source_review_aggregate_sha256,
        }
        if row.lexical_evidence is None:
            if any(value is not None for value in hash_columns.values()):
                raise ValueError("Korean frequency lexical evidence column drift")
            return None
        evidence = KoreanFrequencyLexicalEvidence.model_validate(row.lexical_evidence)
        expected = {
            "frequency_bundle_sha256": evidence.bundle_sha256,
            "frequency_source_sha256": evidence.source_sha256,
            "source_review_receipt_sha256": evidence.source_review_receipt_sha256,
            "source_review_aggregate_sha256": evidence.source_review_aggregate_sha256,
        }
        if hash_columns != expected:
            raise ValueError("Korean frequency lexical evidence hash drift")
        return evidence
