"""Thin Phase 33 coordinator for persisted multi-source item jobs."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.jobs import (
    ControlledReasonCode,
    ItemOutcome,
    ItemRunReport,
    ItemTerminalStatus,
    JobStage,
)
from multilang.repositories.job_repository import JobRepository, Phase33ItemStatusRecord
from multilang.services.item_outcomes import (
    ItemHandlerResult,
    ItemRunResult,
    ItemWorkItem,
    SystemicJobError,
    run_item_outcomes,
)


_SOURCE_ORDER = ("grammar", "custom", "highlight")
_PRIVATE_CLOSED_STATES = frozenset({"disclosing", "disclosed", "failed_unknown"})


class Phase33Source(Protocol):
    def list_items(self, job_id: str) -> Sequence["Phase33JobItem" | dict[str, object]]: ...


Phase33ItemHandler = Callable[["Phase33JobItem", int], ItemHandlerResult]


class Phase33JobItem(BaseModel):
    """Safe source item envelope for Phase 33 persisted orchestration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_family: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    idempotency_key: str | None = Field(default=None, min_length=1)
    duplicate_of: str | None = Field(default=None, min_length=1)
    deferred_reason_code: ControlledReasonCode | None = None
    retryable: bool = False
    private_state: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def duplicate_and_deferred_are_distinct(self) -> "Phase33JobItem":
        if self.duplicate_of is not None and self.deferred_reason_code is not None:
            raise ValueError("an item cannot be both duplicate and deferred")
        return self

    @property
    def is_private_closed(self) -> bool:
        return self.private_state in _PRIVATE_CLOSED_STATES

    def to_work_item(self) -> ItemWorkItem:
        return ItemWorkItem(
            item_id=self.item_id,
            idempotency_key=self.idempotency_key,
            duplicate_of=self.duplicate_of,
            deferred_reason_code=self.deferred_reason_code,
        )


@dataclass(frozen=True, slots=True)
class Phase33JobResult:
    """Result returned by a Phase 33 coordinator execution."""

    report: ItemRunReport
    outcomes: tuple[ItemOutcome, ...]

    @property
    def processed_item_ids(self) -> tuple[str, ...]:
        return self.report.processed_item_ids

    @property
    def failed_item_ids(self) -> tuple[str, ...]:
        return self.report.failed_item_ids


class Phase33JobCoordinator:
    """Compose source adapters, item handlers, and persisted outcome facts."""

    def __init__(
        self,
        *,
        job_repository: JobRepository,
        sources: Mapping[str, Phase33Source],
        handlers: Mapping[str, Phase33ItemHandler],
        stage: JobStage | str = JobStage.GENERATE_TEXT,
        now: Callable[[], datetime] | None = None,
        max_attempts: int = 2,
    ) -> None:
        self.job_repository = job_repository
        self.sources = dict(sources)
        self.handlers = dict(handlers)
        self.stage = stage.value if isinstance(stage, JobStage) else stage
        self.now = now
        self.max_attempts = max_attempts

    def execute(
        self,
        *,
        job_id: str,
        mode: str,
        max_items: int | None = None,
    ) -> Phase33JobResult:
        if mode not in {"start", "resume"}:
            raise ValueError("mode must be start or resume")
        if max_items is not None and max_items < 1:
            raise ValueError("max_items must be greater than or equal to 1")

        all_items = self._list_source_items(job_id)
        prior_statuses = self._prior_statuses(job_id)
        prior_attempt_counts = self._prior_attempt_counts(job_id)
        process_items = self._select_process_items(
            items=all_items,
            prior_statuses=prior_statuses,
            prior_attempt_counts=prior_attempt_counts,
            mode=mode,
        )
        items_by_id = {item.item_id: item for item in process_items}
        item_run = self._run_selected_items(
            job_id=job_id,
            items=process_items,
            items_by_id=items_by_id,
            prior_attempt_counts=prior_attempt_counts,
            max_items=max_items,
        )
        report = self.job_repository.recompute_phase33_run_report(
            job_id,
            stage=self.stage,
            eligible_item_ids=tuple(item.item_id for item in all_items),
            duplicate_item_ids=tuple(item.item_id for item in all_items if item.duplicate_of is not None),
            deferred_item_ids=tuple(
                item.item_id for item in all_items if item.deferred_reason_code is not None
            ),
        )
        return Phase33JobResult(report=report, outcomes=item_run.outcomes)

    def _list_source_items(self, job_id: str) -> tuple[Phase33JobItem, ...]:
        ordered_source_keys = sorted(
            self.sources,
            key=lambda key: (_SOURCE_ORDER.index(key) if key in _SOURCE_ORDER else len(_SOURCE_ORDER), key),
        )
        items: list[Phase33JobItem] = []
        for source_key in ordered_source_keys:
            for raw_item in self.sources[source_key].list_items(job_id):
                item = Phase33JobItem.model_validate(raw_item)
                if item.source_family != source_key:
                    raise SystemicJobError("source family mismatch")
                items.append(item)
        return tuple(items)

    def _prior_statuses(self, job_id: str) -> dict[str, Phase33ItemStatusRecord]:
        return {
            status.item_id: status
            for status in self.job_repository.list_phase33_item_statuses(job_id, stage=self.stage)
        }

    def _prior_attempt_counts(self, job_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for fact in self.job_repository.list_phase33_processing_facts(job_id, stage=self.stage):
            counts[fact.item_id] = max(counts.get(fact.item_id, 0), fact.attempt_count)
        return counts

    def _select_process_items(
        self,
        *,
        items: tuple[Phase33JobItem, ...],
        prior_statuses: Mapping[str, Phase33ItemStatusRecord],
        prior_attempt_counts: Mapping[str, int],
        mode: str,
    ) -> tuple[Phase33JobItem, ...]:
        selected: list[Phase33JobItem] = []
        for item in items:
            if item.duplicate_of is not None or item.deferred_reason_code is not None or item.is_private_closed:
                continue
            prior = prior_statuses.get(item.item_id)
            if mode == "start":
                if prior is None and item.item_id not in prior_attempt_counts:
                    selected.append(item)
                continue
            if prior is None or _is_retryable_prior(prior, item):
                selected.append(item)
        return tuple(selected)

    def _run_selected_items(
        self,
        *,
        job_id: str,
        items: tuple[Phase33JobItem, ...],
        items_by_id: Mapping[str, Phase33JobItem],
        prior_attempt_counts: Mapping[str, int],
        max_items: int | None,
    ) -> ItemRunResult:
        return run_item_outcomes(
            tuple(item.to_work_item() for item in items),
            validate=lambda work_items: self._validate_handlers(work_items, items_by_id),
            handle=lambda work_item, attempt_number: self._handle_item(
                work_item,
                attempt_number,
                items_by_id,
            ),
            load_prior=lambda work_item: None,
            save_atomic=lambda outcome: self._save_outcome(
                job_id,
                outcome,
                items_by_id[outcome.item_id],
                prior_attempt_counts.get(outcome.item_id, 0),
            ),
            now=self.now,
            max_attempts=self.max_attempts,
            process_limit=max_items,
        )

    def _validate_handlers(
        self,
        work_items: tuple[ItemWorkItem, ...],
        items_by_id: Mapping[str, Phase33JobItem],
    ) -> None:
        for work_item in work_items:
            item = items_by_id[work_item.item_id]
            if item.source_family not in self.handlers:
                raise SystemicJobError("missing source handler")

    def _handle_item(
        self,
        work_item: ItemWorkItem,
        attempt_number: int,
        items_by_id: Mapping[str, Phase33JobItem],
    ) -> ItemHandlerResult:
        item = items_by_id[work_item.item_id]
        return self.handlers[item.source_family](item, attempt_number)

    def _save_outcome(
        self,
        job_id: str,
        outcome: ItemOutcome,
        item: Phase33JobItem,
        attempt_offset: int,
    ) -> ItemOutcome:
        if not outcome.attempts:
            return outcome

        for attempt in outcome.attempts[:-1]:
            persisted_attempt_number = attempt.attempt_number + attempt_offset
            self.job_repository.record_phase33_attempt_fact(
                job_id,
                item_id=outcome.item_id,
                stage=self.stage,
                attempt_count=persisted_attempt_number,
                attempted_at=attempt.attempted_at,
                processed_at=attempt.processed_at,
                idempotency_key=_attempt_idempotency_key(job_id, self.stage, item, persisted_attempt_number),
            )

        latest_attempt = outcome.attempts[-1]
        persisted_latest_attempt_number = latest_attempt.attempt_number + attempt_offset
        self.job_repository.record_phase33_item_outcome(
            job_id,
            item_id=outcome.item_id,
            stage=self.stage,
            attempt_count=persisted_latest_attempt_number,
            attempted_at=latest_attempt.attempted_at,
            processed_at=latest_attempt.processed_at,
            terminal_status=outcome.status,
            reason_code=(outcome.diagnostic.reason_code if outcome.diagnostic is not None else None),
            obligations=outcome.obligations,
            idempotency_key=_terminal_idempotency_key(job_id, self.stage, item, persisted_latest_attempt_number),
        )
        return outcome


def _is_retryable_prior(status: Phase33ItemStatusRecord, item: Phase33JobItem) -> bool:
    return status.terminal_status == ItemTerminalStatus.FAILED.value and item.retryable


def _base_idempotency_key(job_id: str, stage: str, item: Phase33JobItem) -> str:
    if item.idempotency_key is not None:
        return item.idempotency_key
    return f"phase33:{job_id}:{stage}:{item.source_family}:{item.item_id}"


def _attempt_idempotency_key(job_id: str, stage: str, item: Phase33JobItem, attempt_number: int) -> str:
    return f"{_base_idempotency_key(job_id, stage, item)}:attempt:{attempt_number}"


def _terminal_idempotency_key(job_id: str, stage: str, item: Phase33JobItem, attempt_number: int) -> str:
    return f"{_base_idempotency_key(job_id, stage, item)}:terminal:{attempt_number}"


__all__ = [
    "Phase33JobCoordinator",
    "Phase33JobItem",
    "Phase33JobResult",
    "Phase33ItemHandler",
    "Phase33Source",
]
