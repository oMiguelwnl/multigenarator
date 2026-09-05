"""Persistence helpers for resumable generation jobs."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from multilang.db.models import (
    GenerationItem,
    GenerationJob,
    GenerationRunDenominatorModel,
    ItemProcessingFactModel,
    ItemTerminalStatusEventModel,
    ProviderCallLogModel,
)
from multilang.domain.korean import KoreanFrequencyJobAuthority, canonical_json_sha256
from multilang.domain.jobs import (
    ControlledReasonCode,
    FieldObligationSummary,
    GenerationRequest,
    ItemRunReport,
    ItemTerminalStatus,
    JobProgressSnapshot,
    JobStage,
    JobStatus,
    ResumeDiagnostic,
)
from multilang.repositories.highlight_import_repository import HighlightImportRepository
from multilang.repositories.korean_personal_source_repository import KoreanPersonalSourceRepository


_KOREAN_OPERATION_STAGE: dict[str, str] = {
    "pilot_text": "pilot_base",
    "pilot_catalog": "pilot_base",
    "pilot_audio_sample": "pilot_audio",
    "production_text": "full",
    "production_audio": "full",
    "production_export": "full",
}
_KOREAN_STAGE_ORDER = {"pilot_base": 1, "pilot_audio": 2, "full": 3}


class Phase33ProcessingFactRecord(BaseModel):
    """Content-free processing fact for one item/stage attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    item_id: str
    stage: str
    attempt_count: int = Field(ge=0)
    attempted_at: datetime | None = None
    processed_at: datetime | None = None
    fact_sha256: str


class Phase33ItemStatusRecord(BaseModel):
    """Content-free current terminal status projection for one item/stage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    item_id: str
    stage: str
    terminal_status: str
    reason_code: str | None = None
    attempt_count: int = Field(ge=0)
    attempted_at: datetime | None = None
    processed_at: datetime | None = None
    fact_sha256: str | None = None
    event_sha256: str


class Phase33InventoryStatus(BaseModel):
    """Safe inventory/status projection that keeps source inventory separate from readiness."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    job_id: str
    source_type: str
    stage: str
    inventory_root_sha256: str
    inventory_count: int = Field(ge=0)
    eligible_card_count: int = Field(ge=0)
    ready_count: int = Field(ge=0)
    inventory_row_ids: tuple[str, ...] = ()
    inventory_item_ids: tuple[str, ...]
    eligible_item_ids: tuple[str, ...]
    ready_item_ids: tuple[str, ...]


class JobRepository:
    """Repository boundary for persisted job and item state."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_job(
        self,
        *,
        request: GenerationRequest,
        run_key: str,
        source_fingerprint: str,
        total_items: int,
        current_stage: JobStage = JobStage.INGEST,
        last_completed_stage: JobStage | None = None,
        status: JobStatus = JobStatus.PENDING,
    ) -> GenerationJob:
        job = GenerationJob(
            id=str(uuid4()),
            run_key=run_key,
            language=request.language.value,
            source_type=request.source_type,
            source_fingerprint=source_fingerprint,
            status=status.value,
            current_stage=current_stage.value,
            last_completed_stage=last_completed_stage.value if last_completed_stage else None,
            total_items=total_items,
            completed_items=0,
            failed_items=0,
            retrying_items=0,
            skipped_duplicates=0,
            resume_state={},
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get_job(self, job_id: str | None = None, *, run_key: str | None = None) -> GenerationJob | None:
        if job_id is None and run_key is None:
            raise ValueError("job_id or run_key is required")

        statement = select(GenerationJob)
        if job_id is not None:
            statement = statement.where(GenerationJob.id == job_id)
        if run_key is not None:
            statement = statement.where(GenerationJob.run_key == run_key)

        return self.session.scalar(statement)

    def bind_execution_authority(
        self,
        job_id: str,
        authority: KoreanFrequencyJobAuthority,
    ) -> KoreanFrequencyJobAuthority:
        if authority.stage == "pilot_audio":
            raise ValueError("audio authority must be bound through bind_audio_authority")
        return self._bind_korean_authority(job_id, authority)

    def bind_audio_authority(
        self,
        job_id: str,
        authority: KoreanFrequencyJobAuthority,
    ) -> KoreanFrequencyJobAuthority:
        if authority.stage not in {"pilot_audio", "full"}:
            raise ValueError("audio authority requires pilot_audio or full stage")
        return self._bind_korean_authority(job_id, authority)

    def load_korean_authority(self, job_id: str) -> KoreanFrequencyJobAuthority:
        job = self._require_job(job_id)
        if job.korean_frequency_authority is None:
            raise ValueError("Korean frequency authority is not bound")
        authority = KoreanFrequencyJobAuthority.model_validate(job.korean_frequency_authority)
        self._assert_authority_columns_match(job, authority)
        return authority

    def require_korean_attempt_authority(self, job_id: str, operation: str) -> None:
        required_stage = _KOREAN_OPERATION_STAGE.get(operation)
        if required_stage is None:
            raise ValueError("unknown Korean provider operation")
        authority = self.load_korean_authority(job_id)
        if _KOREAN_STAGE_ORDER[authority.stage] < _KOREAN_STAGE_ORDER[required_stage]:
            raise ValueError("Korean provider attempt is not authorized for this stage")

    def count_provider_attempts(self, job_id: str) -> int:
        return int(
            self.session.scalar(
                select(func.count(ProviderCallLogModel.id)).where(ProviderCallLogModel.job_id == job_id)
            )
            or 0
        )

    def record_phase33_attempt_fact(
        self,
        job_id: str,
        *,
        item_id: str,
        stage: str,
        attempt_count: int,
        attempted_at: datetime | None,
        processed_at: datetime | None,
        idempotency_key: str,
    ) -> Phase33ProcessingFactRecord:
        """Persist one immutable attempt/processed fact without private payloads."""
        self._require_job(job_id)
        fact, created = self._prepare_phase33_attempt_fact(
            job_id=job_id,
            item_id=item_id,
            stage=stage,
            attempt_count=attempt_count,
            attempted_at=attempted_at,
            processed_at=processed_at,
            idempotency_key=idempotency_key,
        )
        if created:
            try:
                self.session.commit()
            except IntegrityError as exc:
                self.session.rollback()
                replay = self._phase33_attempt_fact(job_id, item_id, stage, attempt_count)
                if replay is not None and replay.fact_sha256 == fact.fact_sha256:
                    return _phase33_fact_record(replay)
                raise ValueError("phase33 processing fact conflict") from exc
        return _phase33_fact_record(fact)

    def record_phase33_item_outcome(
        self,
        job_id: str,
        *,
        item_id: str,
        stage: str,
        attempt_count: int,
        attempted_at: datetime | None,
        processed_at: datetime | None,
        terminal_status: ItemTerminalStatus | str,
        reason_code: ControlledReasonCode | str | None,
        obligations: FieldObligationSummary,
        idempotency_key: str,
    ) -> Phase33ItemStatusRecord:
        """Persist one item-local outcome as separate attempt and terminal-status facts."""
        self._require_job(job_id)
        fact, fact_created = self._prepare_phase33_attempt_fact(
            job_id=job_id,
            item_id=item_id,
            stage=stage,
            attempt_count=attempt_count,
            attempted_at=attempted_at,
            processed_at=processed_at,
            idempotency_key=idempotency_key,
        )
        event, event_created = self._prepare_phase33_terminal_event(
            job_id=job_id,
            item_id=item_id,
            stage=stage,
            terminal_status=_terminal_status_value(terminal_status),
            reason_code=_reason_code_value(reason_code),
            obligations=obligations,
            idempotency_key=idempotency_key,
        )
        if fact_created or event_created:
            try:
                self.session.commit()
            except IntegrityError as exc:
                self.session.rollback()
                replay_fact = self._phase33_attempt_fact(job_id, item_id, stage, attempt_count)
                replay_event = self._phase33_terminal_event(job_id, item_id, stage)
                if (
                    replay_fact is not None
                    and replay_event is not None
                    and replay_fact.fact_sha256 == fact.fact_sha256
                    and replay_event.event_sha256 == event.event_sha256
                ):
                    return _phase33_status_record(replay_event, replay_fact)
                raise ValueError("phase33 item outcome conflict") from exc
        return _phase33_status_record(event, fact)

    def record_phase33_skipped_current(
        self,
        job_id: str,
        *,
        item_id: str,
        stage: str,
        terminal_status: ItemTerminalStatus | str,
        obligations: FieldObligationSummary,
    ) -> Phase33ItemStatusRecord:
        """Record a current prior outcome skipped during this run."""
        return self.record_phase33_item_outcome(
            job_id,
            item_id=item_id,
            stage=stage,
            attempt_count=0,
            attempted_at=None,
            processed_at=None,
            terminal_status=terminal_status,
            reason_code=None,
            obligations=obligations,
            idempotency_key="skipped-current",
        )

    def list_phase33_item_statuses(self, job_id: str, *, stage: str) -> tuple[Phase33ItemStatusRecord, ...]:
        self._require_job(job_id)
        events = self.session.scalars(
            select(ItemTerminalStatusEventModel)
            .where(
                ItemTerminalStatusEventModel.job_id == job_id,
                ItemTerminalStatusEventModel.stage == stage,
            )
            .order_by(ItemTerminalStatusEventModel.item_id.asc())
        )
        return tuple(
            _phase33_status_record(event, self._latest_phase33_attempt_fact(job_id, event.item_id, stage))
            for event in events
        )

    def list_phase33_processing_facts(self, job_id: str, *, stage: str) -> tuple[Phase33ProcessingFactRecord, ...]:
        self._require_job(job_id)
        rows = self.session.scalars(
            select(ItemProcessingFactModel)
            .where(
                ItemProcessingFactModel.job_id == job_id,
                ItemProcessingFactModel.stage == stage,
            )
            .order_by(ItemProcessingFactModel.item_id.asc(), ItemProcessingFactModel.attempt_count.asc())
        )
        return tuple(_phase33_fact_record(row) for row in rows)

    def recompute_phase33_run_report(
        self,
        job_id: str,
        *,
        stage: str,
        eligible_item_ids: tuple[str, ...],
        duplicate_item_ids: tuple[str, ...] = (),
        deferred_item_ids: tuple[str, ...] = (),
    ) -> ItemRunReport:
        """Recompute the seven-count report from persisted item facts and statuses."""
        self._require_job(job_id)
        facts_by_item = self._phase33_facts_by_item(job_id, stage)
        status_by_item = self._phase33_status_by_item(job_id, stage)

        attempted_ids = tuple(
            item_id
            for item_id in eligible_item_ids
            if any(fact.attempt_count > 0 for fact in facts_by_item.get(item_id, ()))
        )
        attempted_set = set(attempted_ids)
        skipped_ids = tuple(
            item_id
            for item_id in eligible_item_ids
            if item_id not in attempted_set
            and any(fact.attempt_count == 0 for fact in facts_by_item.get(item_id, ()))
        )
        skipped_set = set(skipped_ids)
        processed_ids = tuple(
            item_id
            for item_id in attempted_ids
            if any(fact.attempt_count > 0 and fact.processed_at is not None for fact in facts_by_item.get(item_id, ()))
        )
        not_attempted_ids = tuple(
            item_id
            for item_id in eligible_item_ids
            if item_id not in attempted_set and item_id not in skipped_set
        )
        accepted_ids = _eligible_ids_with_status(
            eligible_item_ids,
            status_by_item,
            ItemTerminalStatus.ACCEPTED.value,
        )
        review_required_ids = _eligible_ids_with_status(
            eligible_item_ids,
            status_by_item,
            ItemTerminalStatus.REVIEW_REQUIRED.value,
        )
        failed_ids = _eligible_ids_with_status(
            eligible_item_ids,
            status_by_item,
            ItemTerminalStatus.FAILED.value,
        )
        field_obligations = {
            item_id: _obligations_for_status(status_by_item[item_id])
            for item_id in (*accepted_ids, *review_required_ids)
            if item_id in status_by_item
        }
        report = ItemRunReport(
            eligible_item_ids=eligible_item_ids,
            attempted_item_ids=attempted_ids,
            processed_item_ids=processed_ids,
            skipped_current_item_ids=skipped_ids,
            not_attempted_item_ids=not_attempted_ids,
            accepted_item_ids=accepted_ids,
            review_required_item_ids=review_required_ids,
            failed_item_ids=failed_ids,
            duplicate_item_ids=duplicate_item_ids,
            deferred_item_ids=deferred_item_ids,
            field_obligations=field_obligations,
        )
        self._record_phase33_denominator(job_id, stage, report)
        return report

    def load_phase33_personal_inventory_status(
        self,
        job_id: str,
        *,
        source_type: str,
        stage: str,
    ) -> Phase33InventoryStatus:
        inventory = KoreanPersonalSourceRepository(self.session).list_inventory(job_id, source_type)
        status_by_item = self._phase33_status_by_item(job_id, stage)
        eligible_item_ids = tuple(
            row.item_key
            for row in inventory.rows
            if row.duplicate_of_position is None
            and row.latest_decision is not None
            and row.latest_decision.decision_state in {"accepted", "bridge"}
        )
        ready_item_ids = tuple(
            item_id
            for item_id in eligible_item_ids
            if status_by_item.get(item_id) == ItemTerminalStatus.ACCEPTED.value
        )
        return Phase33InventoryStatus(
            job_id=job_id,
            source_type=source_type,
            stage=stage,
            inventory_root_sha256=inventory.inventory_root_sha256,
            inventory_count=len(inventory.rows),
            eligible_card_count=len(eligible_item_ids),
            ready_count=len(ready_item_ids),
            inventory_row_ids=tuple(row.row_id for row in inventory.rows),
            inventory_item_ids=tuple(row.item_key for row in inventory.rows),
            eligible_item_ids=eligible_item_ids,
            ready_item_ids=ready_item_ids,
        )

    def load_phase33_highlight_inventory_status(self, job_id: str, *, stage: str) -> Phase33InventoryStatus:
        inventory = HighlightImportRepository(self.session).list_korean_safe_inventory(job_id)
        status_by_item = self._phase33_status_by_item(job_id, stage)
        eligible_item_ids = tuple(row.candidate_id for row in inventory.rows)
        ready_item_ids = tuple(
            item_id
            for item_id in eligible_item_ids
            if status_by_item.get(item_id) == ItemTerminalStatus.ACCEPTED.value
        )
        return Phase33InventoryStatus(
            job_id=job_id,
            source_type="kindle-highlights",
            stage=stage,
            inventory_root_sha256=inventory.inventory_root_sha256,
            inventory_count=inventory.candidate_count,
            eligible_card_count=len(eligible_item_ids),
            ready_count=len(ready_item_ids),
            inventory_row_ids=tuple(row.excerpt_revision_id for row in inventory.rows),
            inventory_item_ids=eligible_item_ids,
            eligible_item_ids=eligible_item_ids,
            ready_item_ids=ready_item_ids,
        )

    def list_completed_item_keys(self, run_key: str) -> set[str]:
        rows = self.session.scalars(
            select(GenerationItem.item_key).where(
                GenerationItem.run_key == run_key,
                GenerationItem.status == JobStatus.COMPLETED.value,
            )
        )
        return set(rows)

    def record_item_success(
        self,
        job_id: str,
        *,
        item_key: str,
        completed_stage: JobStage,
    ) -> JobProgressSnapshot:
        job = self._require_job(job_id)
        item = self._get_item(job.run_key, item_key)

        if item and item.status == JobStatus.COMPLETED.value:
            previous_stage = (
                JobStage(item.last_completed_stage)
                if item.last_completed_stage is not None
                else None
            )
            if previous_stage == completed_stage:
                job.skipped_duplicates += 1
            elif previous_stage is None or self._is_later_stage(completed_stage, previous_stage):
                item.last_completed_stage = completed_stage.value
            item.last_error = None
            job.current_stage = completed_stage.value
            job.last_completed_stage = completed_stage.value
            self.session.add(item)
            self.session.add(job)
            self.session.commit()
            self._sync_job_counters(job)
            self.session.refresh(job)
            return self._snapshot(job)

        if item is None:
            item = GenerationItem(
                id=str(uuid4()),
                job_id=job.id,
                run_key=job.run_key,
                item_key=item_key,
                status=JobStatus.COMPLETED.value,
                last_completed_stage=completed_stage.value,
                retry_count=0,
            )
            self.session.add(item)
        else:
            item.status = JobStatus.COMPLETED.value
            item.last_completed_stage = completed_stage.value
            item.last_error = None

        job.current_stage = completed_stage.value
        job.last_completed_stage = completed_stage.value
        self.session.commit()
        self._sync_job_counters(job)
        self.session.refresh(job)
        return self._snapshot(job)

    def record_item_successes(
        self,
        job_id: str,
        *,
        item_keys: Iterable[str],
        completed_stage: JobStage,
    ) -> JobProgressSnapshot:
        normalized_item_keys = list(item_keys)
        if not normalized_item_keys:
            return self._snapshot(self._require_job(job_id))

        job = self._require_job(job_id)
        existing = {
            item.item_key: item
            for item in self.session.scalars(
                select(GenerationItem).where(
                    GenerationItem.run_key == job.run_key,
                    GenerationItem.item_key.in_(normalized_item_keys),
                )
            )
        }

        for item_key in normalized_item_keys:
            item = existing.get(item_key)
            if item is None:
                self.session.add(
                    GenerationItem(
                        id=str(uuid4()),
                        job_id=job.id,
                        run_key=job.run_key,
                        item_key=item_key,
                        status=JobStatus.COMPLETED.value,
                        last_completed_stage=completed_stage.value,
                        retry_count=0,
                    )
                )
                continue

            if item.status == JobStatus.COMPLETED.value:
                previous_stage = (
                    JobStage(item.last_completed_stage)
                    if item.last_completed_stage is not None
                    else None
                )
                if previous_stage == completed_stage:
                    job.skipped_duplicates += 1
                elif previous_stage is None or self._is_later_stage(completed_stage, previous_stage):
                    item.last_completed_stage = completed_stage.value
            else:
                item.status = JobStatus.COMPLETED.value
                item.last_completed_stage = completed_stage.value
            item.last_error = None
            self.session.add(item)

        job.current_stage = completed_stage.value
        job.last_completed_stage = completed_stage.value
        self.session.add(job)
        self.session.commit()
        self._sync_job_counters(job)
        self.session.refresh(job)
        return self._snapshot(job)

    def record_item_failure(
        self,
        job_id: str,
        *,
        item_key: str,
        failed_stage: JobStage,
        error: str,
        retry_count: int,
    ) -> JobProgressSnapshot:
        job = self._require_job(job_id)
        item = self._get_item(job.run_key, item_key)

        if item is None:
            item = GenerationItem(
                id=str(uuid4()),
                job_id=job.id,
                run_key=job.run_key,
                item_key=item_key,
                status=JobStatus.FAILED.value,
                last_completed_stage=job.last_completed_stage,
                retry_count=retry_count,
                last_error=error,
            )
            self.session.add(item)
        else:
            item.status = JobStatus.FAILED.value
            item.retry_count = retry_count
            item.last_error = error

        job.retrying_items = retry_count
        job.current_stage = failed_stage.value
        self.session.commit()
        self._sync_job_counters(job)
        self.session.refresh(job)
        return self._snapshot(job)

    def validate_resume_state(self, job_id: str) -> ResumeDiagnostic | None:
        job = self._require_job(job_id)
        items = list(
            self.session.scalars(select(GenerationItem).where(GenerationItem.job_id == job.id))
        )
        completed_items = [item for item in items if item.status == JobStatus.COMPLETED.value]
        failed_items = [item for item in items if item.status == JobStatus.FAILED.value]
        actual_last_completed_stage = self._latest_stage(
            item.last_completed_stage for item in completed_items if item.last_completed_stage
        )

        mismatches: dict[str, object] = {}
        if job.completed_items != len(completed_items):
            mismatches["completed_items"] = {
                "stored": job.completed_items,
                "actual": len(completed_items),
            }
        if job.failed_items != len(failed_items):
            mismatches["failed_items"] = {"stored": job.failed_items, "actual": len(failed_items)}

        stored_last = job.last_completed_stage
        actual_last = actual_last_completed_stage.value if actual_last_completed_stage else None
        if stored_last != actual_last:
            mismatches["last_completed_stage"] = {"stored": stored_last, "actual": actual_last}

        if self._stage_mismatch(job.current_stage, actual_last_completed_stage):
            mismatches["current_stage"] = {
                "stored": job.current_stage,
                "actual_last_completed_stage": actual_last,
            }

        if not mismatches:
            return None

        return ResumeDiagnostic(
            job_id=job.id,
            reason="persisted resume state is inconsistent",
            details={
                "stored_current_stage": job.current_stage,
                "stored_last_completed_stage": job.last_completed_stage,
                "actual_last_completed_stage": actual_last,
                "mismatches": mismatches,
            },
        )

    def advance_job_to_stage(self, job_id: str, stage: JobStage) -> JobProgressSnapshot:
        job = self._require_job(job_id)
        job.current_stage = stage.value
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return self._snapshot(job)

    def update_job_status(
        self,
        job_id: str,
        *,
        status: JobStatus,
        current_stage: JobStage | None = None,
        failed_items: int | None = None,
    ) -> JobProgressSnapshot:
        job = self._require_job(job_id)
        job.status = status.value
        if current_stage is not None:
            job.current_stage = current_stage.value
        if failed_items is not None:
            job.failed_items = failed_items
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return self._snapshot(job)

    def _prepare_phase33_attempt_fact(
        self,
        *,
        job_id: str,
        item_id: str,
        stage: str,
        attempt_count: int,
        attempted_at: datetime | None,
        processed_at: datetime | None,
        idempotency_key: str,
    ) -> tuple[ItemProcessingFactModel, bool]:
        if attempt_count < 0:
            raise ValueError("attempt_count must be non-negative")
        if attempt_count == 0 and (attempted_at is not None or processed_at is not None):
            raise ValueError("skipped-current facts cannot carry attempt timestamps")
        if attempt_count > 0 and attempted_at is None:
            raise ValueError("attempted facts require attempted_at")
        if attempted_at is not None and processed_at is not None and processed_at < attempted_at:
            raise ValueError("processed_at cannot be before attempted_at")
        payload = _phase33_fact_payload(
            job_id=job_id,
            item_id=item_id,
            stage=stage,
            attempt_count=attempt_count,
            attempted_at=attempted_at,
            processed_at=processed_at,
            idempotency_key=idempotency_key,
        )
        fact_sha256 = canonical_json_sha256(payload)
        existing = self._phase33_attempt_fact(job_id, item_id, stage, attempt_count)
        if existing is not None:
            if existing.fact_sha256 != fact_sha256:
                raise ValueError("phase33 processing fact conflict")
            return existing, False
        fact = ItemProcessingFactModel(
            id=str(uuid4()),
            job_id=job_id,
            item_id=item_id,
            stage=stage,
            attempt_count=attempt_count,
            attempted_at=attempted_at,
            processed_at=processed_at,
            fact_sha256=fact_sha256,
        )
        self.session.add(fact)
        return fact, True

    def _prepare_phase33_terminal_event(
        self,
        *,
        job_id: str,
        item_id: str,
        stage: str,
        terminal_status: str,
        reason_code: str | None,
        obligations: FieldObligationSummary,
        idempotency_key: str,
    ) -> tuple[ItemTerminalStatusEventModel, bool]:
        if terminal_status not in {
            ItemTerminalStatus.ACCEPTED.value,
            ItemTerminalStatus.REVIEW_REQUIRED.value,
            ItemTerminalStatus.FAILED.value,
        }:
            raise ValueError("phase33 terminal status must be accepted, review_required, or failed")
        if terminal_status == ItemTerminalStatus.ACCEPTED.value and not obligations.all_required_current:
            raise ValueError("accepted phase33 outcomes require current obligations")
        payload = _phase33_event_payload(
            job_id=job_id,
            item_id=item_id,
            stage=stage,
            terminal_status=terminal_status,
            reason_code=reason_code,
            obligations=obligations,
            idempotency_key=idempotency_key,
        )
        event_sha256 = canonical_json_sha256(payload)
        existing = self._phase33_terminal_event(job_id, item_id, stage)
        if existing is not None:
            if existing.event_sha256 != event_sha256:
                raise ValueError("phase33 terminal status conflict")
            return existing, False
        event = ItemTerminalStatusEventModel(
            id=str(uuid4()),
            job_id=job_id,
            item_id=item_id,
            stage=stage,
            terminal_status=terminal_status,
            reason_code=reason_code,
            event_sha256=event_sha256,
        )
        self.session.add(event)
        return event, True

    def _phase33_attempt_fact(
        self,
        job_id: str,
        item_id: str,
        stage: str,
        attempt_count: int,
    ) -> ItemProcessingFactModel | None:
        return self.session.scalar(
            select(ItemProcessingFactModel).where(
                ItemProcessingFactModel.job_id == job_id,
                ItemProcessingFactModel.item_id == item_id,
                ItemProcessingFactModel.stage == stage,
                ItemProcessingFactModel.attempt_count == attempt_count,
            )
        )

    def _latest_phase33_attempt_fact(
        self,
        job_id: str,
        item_id: str,
        stage: str,
    ) -> ItemProcessingFactModel | None:
        return self.session.scalar(
            select(ItemProcessingFactModel)
            .where(
                ItemProcessingFactModel.job_id == job_id,
                ItemProcessingFactModel.item_id == item_id,
                ItemProcessingFactModel.stage == stage,
            )
            .order_by(ItemProcessingFactModel.attempt_count.desc(), ItemProcessingFactModel.created_at.desc())
            .limit(1)
        )

    def _phase33_terminal_event(
        self,
        job_id: str,
        item_id: str,
        stage: str,
    ) -> ItemTerminalStatusEventModel | None:
        return self.session.scalar(
            select(ItemTerminalStatusEventModel).where(
                ItemTerminalStatusEventModel.job_id == job_id,
                ItemTerminalStatusEventModel.item_id == item_id,
                ItemTerminalStatusEventModel.stage == stage,
            )
        )

    def _phase33_facts_by_item(
        self,
        job_id: str,
        stage: str,
    ) -> dict[str, tuple[ItemProcessingFactModel, ...]]:
        rows = self.session.scalars(
            select(ItemProcessingFactModel)
            .where(
                ItemProcessingFactModel.job_id == job_id,
                ItemProcessingFactModel.stage == stage,
            )
            .order_by(ItemProcessingFactModel.item_id.asc(), ItemProcessingFactModel.attempt_count.asc())
        )
        facts: dict[str, list[ItemProcessingFactModel]] = {}
        for row in rows:
            facts.setdefault(row.item_id, []).append(row)
        return {item_id: tuple(item_facts) for item_id, item_facts in facts.items()}

    def _phase33_status_by_item(self, job_id: str, stage: str) -> dict[str, str]:
        rows = self.session.scalars(
            select(ItemTerminalStatusEventModel).where(
                ItemTerminalStatusEventModel.job_id == job_id,
                ItemTerminalStatusEventModel.stage == stage,
            )
        )
        return {row.item_id: row.terminal_status for row in rows}

    def _record_phase33_denominator(self, job_id: str, stage: str, report: ItemRunReport) -> None:
        payload = {
            "job_id": job_id,
            "stage": stage,
            "expected_count": report.total_eligible,
            "accepted_count": report.accepted,
            "review_required_count": report.review_required,
            "failed_count": report.failed,
            "eligible_item_ids": report.eligible_item_ids,
            "accepted_item_ids": report.accepted_item_ids,
            "review_required_item_ids": report.review_required_item_ids,
            "failed_item_ids": report.failed_item_ids,
        }
        denominator_sha256 = canonical_json_sha256(payload)
        existing = self.session.scalar(
            select(GenerationRunDenominatorModel).where(
                GenerationRunDenominatorModel.job_id == job_id,
                GenerationRunDenominatorModel.stage == stage,
            )
        )
        if existing is not None:
            if existing.denominator_sha256 != denominator_sha256:
                raise ValueError("phase33 denominator conflict")
            return
        self.session.add(
            GenerationRunDenominatorModel(
                id=str(uuid4()),
                job_id=job_id,
                stage=stage,
                expected_count=report.total_eligible,
                accepted_count=report.accepted,
                review_required_count=report.review_required,
                failed_count=report.failed,
                denominator_sha256=denominator_sha256,
            )
        )
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            replay = self.session.scalar(
                select(GenerationRunDenominatorModel).where(
                    GenerationRunDenominatorModel.job_id == job_id,
                    GenerationRunDenominatorModel.stage == stage,
                )
            )
            if replay is not None and replay.denominator_sha256 == denominator_sha256:
                return
            raise ValueError("phase33 denominator conflict") from exc

    def _bind_korean_authority(
        self,
        job_id: str,
        authority: KoreanFrequencyJobAuthority,
    ) -> KoreanFrequencyJobAuthority:
        job = self._require_job(job_id)
        payload = authority.model_dump(mode="json", exclude_none=True)
        existing_payload = job.korean_frequency_authority
        if existing_payload is not None:
            existing = KoreanFrequencyJobAuthority.model_validate(existing_payload)
            self._assert_authority_columns_match(job, existing)
            if existing.model_dump(mode="json", exclude_none=True) == payload:
                return existing
            if _KOREAN_STAGE_ORDER[authority.stage] <= _KOREAN_STAGE_ORDER[existing.stage]:
                raise ValueError("Korean frequency authority drift")
        self._store_korean_authority_columns(job, authority, payload)
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return self.load_korean_authority(job_id)

    @staticmethod
    def _store_korean_authority_columns(
        job: GenerationJob,
        authority: KoreanFrequencyJobAuthority,
        payload: dict[str, object],
    ) -> None:
        job.korean_phase31_pointer_locator_sha256 = authority.phase31_pointer_locator_sha256
        job.korean_phase31_pointer_content_sha256 = authority.phase31_pointer_content_sha256
        job.korean_phase31_validation_receipt_sha256 = authority.phase31_validation_receipt_sha256
        job.korean_phase31_snapshot_manifest_sha256 = authority.phase31_snapshot_manifest_sha256
        job.korean_phase31_snapshot_root_sha256 = authority.phase31_snapshot_root_sha256
        job.korean_frequency_bundle_locator_sha256 = authority.frequency_bundle_locator_sha256
        job.korean_frequency_bundle_content_sha256 = authority.frequency_bundle_content_sha256
        job.korean_provider_policy_sha256 = authority.provider_policy_sha256
        job.korean_frequency_authority = payload
        job.korean_provider_policy = {
            "provider_policy_sha256": authority.provider_policy_sha256,
        }

    @staticmethod
    def _assert_authority_columns_match(
        job: GenerationJob,
        authority: KoreanFrequencyJobAuthority,
    ) -> None:
        expected = {
            "korean_phase31_pointer_locator_sha256": authority.phase31_pointer_locator_sha256,
            "korean_phase31_pointer_content_sha256": authority.phase31_pointer_content_sha256,
            "korean_phase31_validation_receipt_sha256": authority.phase31_validation_receipt_sha256,
            "korean_phase31_snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
            "korean_phase31_snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
            "korean_frequency_bundle_locator_sha256": authority.frequency_bundle_locator_sha256,
            "korean_frequency_bundle_content_sha256": authority.frequency_bundle_content_sha256,
            "korean_provider_policy_sha256": authority.provider_policy_sha256,
        }
        for field, value in expected.items():
            if getattr(job, field) != value:
                raise ValueError("Korean frequency authority column drift")

    def _require_job(self, job_id: str) -> GenerationJob:
        job = self.get_job(job_id)
        if job is None:
            raise ValueError(f"unknown job_id: {job_id}")
        return job

    def _get_item(self, run_key: str, item_key: str) -> GenerationItem | None:
        return self.session.scalar(
            select(GenerationItem).where(
                GenerationItem.run_key == run_key,
                GenerationItem.item_key == item_key,
            )
        )

    def _count_items(self, run_key: str, statuses: Iterable[str]) -> int:
        return len(
            list(
                self.session.scalars(
                    select(GenerationItem.id).where(
                        GenerationItem.run_key == run_key,
                        GenerationItem.status.in_(tuple(statuses)),
                    )
                )
            )
        )

    def _sync_job_counters(self, job: GenerationJob) -> None:
        job.completed_items = self._count_items(job.run_key, [JobStatus.COMPLETED.value])
        job.failed_items = self._count_items(job.run_key, [JobStatus.FAILED.value])
        self.session.add(job)
        self.session.commit()

    def _latest_stage(self, stages: Iterable[str]) -> JobStage | None:
        ordered_stages = {stage.value: index for index, stage in enumerate(JobStage)}
        available = [stage for stage in stages if stage in ordered_stages]
        if not available:
            return None
        latest = max(available, key=lambda stage: ordered_stages[stage])
        return JobStage(latest)

    def _stage_mismatch(self, current_stage: str, actual_last_completed_stage: JobStage | None) -> bool:
        if actual_last_completed_stage is None:
            return current_stage != JobStage.INGEST.value

        stage_order = list(JobStage)
        actual_index = stage_order.index(actual_last_completed_stage)
        allowed_current = {actual_last_completed_stage.value}
        if actual_index + 1 < len(stage_order):
            allowed_current.add(stage_order[actual_index + 1].value)
        return current_stage not in allowed_current

    def _is_later_stage(self, candidate: JobStage, current: JobStage) -> bool:
        stage_order = list(JobStage)
        return stage_order.index(candidate) > stage_order.index(current)

    def _snapshot(self, job: GenerationJob) -> JobProgressSnapshot:
        return JobProgressSnapshot(
            stage=JobStage(job.current_stage),
            completed_items=job.completed_items,
            failed_items=job.failed_items,
            retrying_items=job.retrying_items,
            skipped_duplicates=job.skipped_duplicates,
        )


def _phase33_fact_payload(
    *,
    job_id: str,
    item_id: str,
    stage: str,
    attempt_count: int,
    attempted_at: datetime | None,
    processed_at: datetime | None,
    idempotency_key: str,
) -> dict[str, object]:
    return {
        "kind": "phase33_processing_fact",
        "job_id": job_id,
        "item_id": item_id,
        "stage": stage,
        "attempt_count": attempt_count,
        "attempted_at": _datetime_json(attempted_at),
        "processed_at": _datetime_json(processed_at),
        "idempotency_key_sha256": canonical_json_sha256({"idempotency_key": idempotency_key}),
    }


def _phase33_event_payload(
    *,
    job_id: str,
    item_id: str,
    stage: str,
    terminal_status: str,
    reason_code: str | None,
    obligations: FieldObligationSummary,
    idempotency_key: str,
) -> dict[str, object]:
    return {
        "kind": "phase33_terminal_status_event",
        "job_id": job_id,
        "item_id": item_id,
        "stage": stage,
        "terminal_status": terminal_status,
        "reason_code": reason_code,
        "obligations": obligations.model_dump(mode="json"),
        "idempotency_key_sha256": canonical_json_sha256({"idempotency_key": idempotency_key}),
    }


def _phase33_fact_record(row: ItemProcessingFactModel) -> Phase33ProcessingFactRecord:
    return Phase33ProcessingFactRecord(
        item_id=row.item_id,
        stage=row.stage,
        attempt_count=row.attempt_count,
        attempted_at=row.attempted_at,
        processed_at=row.processed_at,
        fact_sha256=row.fact_sha256,
    )


def _phase33_status_record(
    event: ItemTerminalStatusEventModel,
    fact: ItemProcessingFactModel | None,
) -> Phase33ItemStatusRecord:
    return Phase33ItemStatusRecord(
        item_id=event.item_id,
        stage=event.stage,
        terminal_status=event.terminal_status,
        reason_code=event.reason_code,
        attempt_count=fact.attempt_count if fact is not None else 0,
        attempted_at=fact.attempted_at if fact is not None else None,
        processed_at=fact.processed_at if fact is not None else None,
        fact_sha256=fact.fact_sha256 if fact is not None else None,
        event_sha256=event.event_sha256,
    )


def _eligible_ids_with_status(
    eligible_item_ids: tuple[str, ...],
    status_by_item: dict[str, str],
    status: str,
) -> tuple[str, ...]:
    return tuple(item_id for item_id in eligible_item_ids if status_by_item.get(item_id) == status)


def _obligations_for_status(status: str) -> FieldObligationSummary:
    if status == ItemTerminalStatus.ACCEPTED.value:
        return FieldObligationSummary(
            ai_review_current=True,
            integrity_current=True,
            word_audio_required=True,
            word_audio_current=True,
            sentence_audio_required=True,
            sentence_audio_current=True,
        )
    return FieldObligationSummary()


def _terminal_status_value(value: ItemTerminalStatus | str) -> str:
    return value.value if isinstance(value, ItemTerminalStatus) else value


def _reason_code_value(value: ControlledReasonCode | str | None) -> str | None:
    if value is None:
        return None
    return value.value if isinstance(value, ControlledReasonCode) else value


def _datetime_json(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()
