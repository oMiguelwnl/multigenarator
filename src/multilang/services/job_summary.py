"""Helpers for lifecycle summaries after job execution."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from multilang.cli import JobExecutionReport
from multilang.db.models import GenerationItem
from multilang.domain.jobs import JobStatus
from multilang.repositories.job_repository import JobRepository


@dataclass(slots=True)
class FailedItemSummary:
    """Failure details kept visible in final lifecycle output."""

    item_key: str
    retry_count: int
    error: str | None


@dataclass(slots=True)
class JobLifecycleSummary:
    """Operator-facing summary for one completed execution flow."""

    completed_items: int
    failed_items: list[FailedItemSummary]
    retried_items: int
    skipped_duplicates: int
    resumed_from_job: str | None
    overwritten_items: int


class JobSummaryBuilder:
    """Build a final summary from persisted state and execution metadata."""

    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    def build(self, report: JobExecutionReport) -> JobLifecycleSummary:
        job = self.repository.get_job(report.job_id)
        if job is None:
            raise ValueError(f"unknown job_id: {report.job_id}")

        failed_items = self._load_failed_items(report.job_id)
        retried_item_keys = set(report.retried_item_keys)
        retried_item_keys.update(item.item_key for item in failed_items if item.retry_count > 0)

        return JobLifecycleSummary(
            completed_items=job.completed_items,
            failed_items=failed_items,
            retried_items=len(retried_item_keys),
            skipped_duplicates=len(report.orchestration.skipped_item_keys),
            resumed_from_job=report.job_id if report.orchestration.mode == "resume" else None,
            overwritten_items=len(report.orchestration.overwritten_item_keys),
        )

    def _load_failed_items(self, job_id: str) -> list[FailedItemSummary]:
        rows = self.repository.session.scalars(
            select(GenerationItem)
            .where(
                GenerationItem.job_id == job_id,
                GenerationItem.status == JobStatus.FAILED.value,
            )
            .order_by(GenerationItem.item_key)
        )
        return [
            FailedItemSummary(
                item_key=row.item_key,
                retry_count=row.retry_count,
                error=row.last_error,
            )
            for row in rows
        ]
