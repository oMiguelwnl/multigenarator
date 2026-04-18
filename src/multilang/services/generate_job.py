"""Repository-backed start, resume, and rerun orchestration."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from multilang.domain.jobs import GenerationRequest, JobStage, ResumeDiagnostic
from multilang.repositories.job_repository import JobRepository
from multilang.services.input_fingerprint import (
    build_input_fingerprint,
    build_run_key,
    normalize_requested_item_keys,
)


@dataclass(slots=True)
class GenerateJobResult:
    """Prepared job orchestration data for a run."""

    mode: str
    job_id: str
    run_key: str
    source_fingerprint: str
    pending_item_keys: list[str]
    skipped_item_keys: list[str]
    resume_from_stage: JobStage
    diagnostic: ResumeDiagnostic | None = None


class GenerateJobService:
    """Prepare safe start/resume/rerun decisions from persisted state."""

    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    def start(
        self,
        request: GenerationRequest,
        *,
        requested_item_keys: Iterable[str],
        overwrite_confirmed: bool = False,
    ) -> GenerateJobResult:
        normalized_items = normalize_requested_item_keys(requested_item_keys)
        source_fingerprint = build_input_fingerprint(
            request,
            requested_item_keys=normalized_items,
        )
        run_key = build_run_key(request, requested_item_keys=normalized_items)
        existing_job = self.repository.get_job(run_key=run_key)

        if existing_job is None:
            job = self.repository.create_job(
                request=request,
                run_key=run_key,
                source_fingerprint=source_fingerprint,
                total_items=len(normalized_items),
            )
            return GenerateJobResult(
                mode="start",
                job_id=job.id,
                run_key=run_key,
                source_fingerprint=source_fingerprint,
                pending_item_keys=normalized_items,
                skipped_item_keys=[],
                resume_from_stage=JobStage(job.current_stage),
            )

        pending_item_keys, skipped_item_keys = self._partition_items(
            run_key=run_key,
            requested_item_keys=normalized_items,
            overwrite_confirmed=overwrite_confirmed,
        )
        return GenerateJobResult(
            mode="rerun",
            job_id=existing_job.id,
            run_key=run_key,
            source_fingerprint=existing_job.source_fingerprint,
            pending_item_keys=pending_item_keys,
            skipped_item_keys=skipped_item_keys,
            resume_from_stage=JobStage(existing_job.current_stage),
        )

    def resume(
        self,
        job_id: str,
        *,
        requested_item_keys: Iterable[str],
        overwrite_confirmed: bool = False,
    ) -> GenerateJobResult:
        job = self.repository.get_job(job_id)
        if job is None:
            raise ValueError(f"unknown job_id: {job_id}")

        diagnostic = self.repository.validate_resume_state(job_id)
        if diagnostic is not None:
            return GenerateJobResult(
                mode="resume",
                job_id=job.id,
                run_key=job.run_key,
                source_fingerprint=job.source_fingerprint,
                pending_item_keys=[],
                skipped_item_keys=[],
                resume_from_stage=JobStage(job.current_stage),
                diagnostic=diagnostic,
            )

        normalized_items = normalize_requested_item_keys(requested_item_keys)
        pending_item_keys, skipped_item_keys = self._partition_items(
            run_key=job.run_key,
            requested_item_keys=normalized_items,
            overwrite_confirmed=overwrite_confirmed,
        )
        return GenerateJobResult(
            mode="resume",
            job_id=job.id,
            run_key=job.run_key,
            source_fingerprint=job.source_fingerprint,
            pending_item_keys=pending_item_keys,
            skipped_item_keys=skipped_item_keys,
            resume_from_stage=JobStage(job.current_stage),
            diagnostic=None,
        )

    def orchestrate(
        self,
        request: GenerationRequest,
        *,
        requested_item_keys: Iterable[str],
    ) -> GenerateJobResult:
        if request.resume_job_id:
            return self.resume(
                request.resume_job_id,
                requested_item_keys=requested_item_keys,
                overwrite_confirmed=request.overwrite and request.yes_overwrite,
            )

        return self.start(
            request,
            requested_item_keys=requested_item_keys,
            overwrite_confirmed=request.overwrite and request.yes_overwrite,
        )

    def _partition_items(
        self,
        *,
        run_key: str,
        requested_item_keys: list[str],
        overwrite_confirmed: bool,
    ) -> tuple[list[str], list[str]]:
        if overwrite_confirmed:
            return requested_item_keys, []

        completed_item_keys = self.repository.list_completed_item_keys(run_key)
        skipped_item_keys = [item for item in requested_item_keys if item in completed_item_keys]
        pending_item_keys = [item for item in requested_item_keys if item not in completed_item_keys]
        return pending_item_keys, skipped_item_keys
