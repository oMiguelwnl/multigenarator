"""Persistence helpers for resumable generation jobs."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from multilang.db.models import GenerationItem, GenerationJob
from multilang.domain.jobs import (
    GenerationRequest,
    JobProgressSnapshot,
    JobStage,
    JobStatus,
    ResumeDiagnostic,
)


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
