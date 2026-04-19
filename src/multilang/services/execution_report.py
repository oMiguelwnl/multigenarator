"""Shared execution-report contracts for CLI and summary code."""

from __future__ import annotations

from dataclasses import dataclass

from multilang.services.generate_job import GenerateJobResult


@dataclass(slots=True)
class JobExecutionReport:
    """Execution details returned by the default CLI runner."""

    orchestration: GenerateJobResult
    progress_updates: list[str]
    retried_item_keys: list[str]
    failed_item_keys: list[str]

    @property
    def job_id(self) -> str:
        return self.orchestration.job_id
