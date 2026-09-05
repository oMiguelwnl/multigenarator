"""Pure item outcome runner with per-item isolation and truthful aggregation."""

from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.jobs import (
    ControlledReasonCode,
    FieldObligationSummary,
    ItemAttemptRecord,
    ItemDiagnostic,
    ItemOutcome,
    ItemRunReport,
    ItemTerminalStatus,
)


class SystemicJobError(Exception):
    """Fail-closed error for job-level contract/config/authority problems."""


class ItemLocalError(Exception):
    """Controlled per-item failure; its message is never persisted."""

    def __init__(
        self,
        *,
        reason_code: ControlledReasonCode,
        terminal_status: ItemTerminalStatus = ItemTerminalStatus.FAILED,
        processed: bool = False,
    ) -> None:
        super().__init__(reason_code.value)
        self.reason_code = reason_code
        self.terminal_status = terminal_status
        self.processed = processed


class RetryableItemError(ItemLocalError):
    """Controlled per-item failure that can be retried within a fixed bound."""


class ItemWorkItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    item_id: str = Field(min_length=1)
    idempotency_key: str | None = Field(default=None, min_length=1)
    duplicate_of: str | None = Field(default=None, min_length=1)
    deferred_reason_code: ControlledReasonCode | None = None

    @model_validator(mode="after")
    def duplicate_and_deferred_are_distinct_dispositions(self) -> "ItemWorkItem":
        if self.duplicate_of is not None and self.deferred_reason_code is not None:
            raise ValueError("an item cannot be both duplicate and deferred")
        return self

    @property
    def is_duplicate(self) -> bool:
        return self.duplicate_of is not None

    @property
    def is_deferred(self) -> bool:
        return self.deferred_reason_code is not None


class ItemHandlerResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: ItemTerminalStatus
    obligations: FieldObligationSummary = Field(default_factory=FieldObligationSummary)
    reason_code: ControlledReasonCode | None = None
    processed: bool = True


class ItemRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcomes: tuple[ItemOutcome, ...]
    report: ItemRunReport


def run_item_outcomes(
    items: Sequence[ItemWorkItem | dict[str, object]],
    *,
    validate: Callable[[tuple[ItemWorkItem, ...]], None],
    handle: Callable[[ItemWorkItem, int], ItemHandlerResult],
    load_prior: Callable[[ItemWorkItem], ItemOutcome | None],
    save_atomic: Callable[[ItemOutcome], ItemOutcome | None],
    now: Callable[[], datetime] | None = None,
    max_attempts: int = 2,
    process_limit: int | None = None,
    correlation_id_factory: Callable[[], str] | None = None,
) -> ItemRunResult:
    """Run item handlers in order, isolating item-local failures only."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if process_limit is not None and process_limit < 0:
        raise ValueError("process_limit must be non-negative")

    work_items = tuple(ItemWorkItem.model_validate(item) for item in items)
    item_ids = tuple(item.item_id for item in work_items)
    if len(item_ids) != len(set(item_ids)):
        raise SystemicJobError("duplicate item_id in run")

    validate(work_items)

    attempted_ids: list[str] = []
    skipped_current_ids: list[str] = []
    duplicate_ids: list[str] = []
    deferred_ids: list[str] = []
    saved_outcomes: list[ItemOutcome] = []
    current_outcomes: dict[str, ItemOutcome] = {}

    for item in work_items:
        if item.is_duplicate:
            duplicate_ids.append(item.item_id)
            continue
        if item.is_deferred:
            deferred_ids.append(item.item_id)
            continue

        prior = load_prior(item)
        if _is_current_accepted(prior):
            skipped_current_ids.append(item.item_id)
            current_outcomes[item.item_id] = prior
            continue

        if process_limit is not None and len(attempted_ids) >= process_limit:
            if prior is not None:
                current_outcomes[item.item_id] = prior
            continue

        attempted_ids.append(item.item_id)
        saved = _run_one_item(
            item=item,
            handle=handle,
            save_atomic=save_atomic,
            now=now,
            max_attempts=max_attempts,
            correlation_id_factory=correlation_id_factory,
        )
        saved_outcomes.append(saved)
        current_outcomes[item.item_id] = saved

    attempted = set(attempted_ids)
    skipped = set(skipped_current_ids)
    not_attempted_ids = tuple(
        item_id for item_id in item_ids if item_id not in attempted and item_id not in skipped
    )
    processed_ids = tuple(
        item_id
        for item_id in item_ids
        if item_id in attempted
        and current_outcomes.get(item_id, None) is not None
        and current_outcomes[item_id].was_processed
    )
    accepted_ids = _ids_with_status(
        item_ids, current_outcomes, ItemTerminalStatus.ACCEPTED
    )
    review_required_ids = _ids_with_status(
        item_ids, current_outcomes, ItemTerminalStatus.REVIEW_REQUIRED
    )
    failed_ids = _ids_with_status(item_ids, current_outcomes, ItemTerminalStatus.FAILED)
    field_obligations = {
        item_id: outcome.obligations
        for item_id, outcome in current_outcomes.items()
        if outcome.status in {ItemTerminalStatus.ACCEPTED, ItemTerminalStatus.REVIEW_REQUIRED}
    }
    report = ItemRunReport(
        eligible_item_ids=item_ids,
        attempted_item_ids=tuple(attempted_ids),
        processed_item_ids=processed_ids,
        skipped_current_item_ids=tuple(skipped_current_ids),
        not_attempted_item_ids=not_attempted_ids,
        accepted_item_ids=accepted_ids,
        review_required_item_ids=review_required_ids,
        failed_item_ids=failed_ids,
        duplicate_item_ids=tuple(duplicate_ids),
        deferred_item_ids=tuple(deferred_ids),
        field_obligations=field_obligations,
    )
    return ItemRunResult(outcomes=tuple(saved_outcomes), report=report)


def _run_one_item(
    *,
    item: ItemWorkItem,
    handle: Callable[[ItemWorkItem, int], ItemHandlerResult],
    save_atomic: Callable[[ItemOutcome], ItemOutcome | None],
    now: Callable[[], datetime] | None,
    max_attempts: int,
    correlation_id_factory: Callable[[], str] | None,
) -> ItemOutcome:
    attempts: list[ItemAttemptRecord] = []
    for attempt_number in range(1, max_attempts + 1):
        attempted_at = _now(now)
        try:
            raw_result = handle(item, attempt_number)
        except SystemicJobError:
            raise
        except RetryableItemError as exc:
            attempts.append(
                ItemAttemptRecord(
                    attempt_number=attempt_number,
                    attempted_at=attempted_at,
                    processed_at=_now(now) if exc.processed else None,
                )
            )
            if attempt_number < max_attempts:
                continue
            return _save(
                save_atomic,
                ItemOutcome(
                    item_id=item.item_id,
                    status=ItemTerminalStatus.FAILED,
                    attempts=tuple(attempts),
                    diagnostic=ItemDiagnostic(reason_code=ControlledReasonCode.RETRY_EXHAUSTED),
                ),
            )
        except ItemLocalError as exc:
            attempts.append(
                ItemAttemptRecord(
                    attempt_number=attempt_number,
                    attempted_at=attempted_at,
                    processed_at=_now(now) if exc.processed else None,
                )
            )
            return _save(
                save_atomic,
                ItemOutcome(
                    item_id=item.item_id,
                    status=exc.terminal_status,
                    attempts=tuple(attempts),
                    diagnostic=ItemDiagnostic(reason_code=exc.reason_code),
                ),
            )
        except Exception:
            attempts.append(
                ItemAttemptRecord(
                    attempt_number=attempt_number,
                    attempted_at=attempted_at,
                    processed_at=None,
                )
            )
            return _save(
                save_atomic,
                ItemOutcome(
                    item_id=item.item_id,
                    status=ItemTerminalStatus.FAILED,
                    attempts=tuple(attempts),
                    diagnostic=ItemDiagnostic(
                        reason_code=ControlledReasonCode.FAILED_UNKNOWN,
                        correlation_id=_correlation_id(correlation_id_factory),
                    ),
                ),
            )

        try:
            handled = ItemHandlerResult.model_validate(raw_result)
        except Exception as exc:
            raise SystemicJobError("handler result schema mismatch") from exc

        attempts.append(
            ItemAttemptRecord(
                attempt_number=attempt_number,
                attempted_at=attempted_at,
                processed_at=_now(now) if handled.processed else None,
            )
        )
        return _save(
            save_atomic,
            ItemOutcome(
                item_id=item.item_id,
                status=handled.status,
                attempts=tuple(attempts),
                obligations=handled.obligations,
                diagnostic=(
                    ItemDiagnostic(reason_code=handled.reason_code)
                    if handled.reason_code is not None
                    else None
                ),
            ),
        )

    raise RuntimeError("unreachable item retry loop")


def _save(
    save_atomic: Callable[[ItemOutcome], ItemOutcome | None], outcome: ItemOutcome
) -> ItemOutcome:
    saved = save_atomic(outcome)
    if saved is None:
        saved = outcome
    if saved.item_id != outcome.item_id:
        raise SystemicJobError("save_atomic returned mismatched item_id")
    return saved


def _now(now: Callable[[], datetime] | None) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    return now()


def _correlation_id(correlation_id_factory: Callable[[], str] | None) -> str:
    if correlation_id_factory is None:
        return uuid4().hex
    return correlation_id_factory()


def _is_current_accepted(outcome: ItemOutcome | None) -> bool:
    return (
        outcome is not None
        and outcome.status is ItemTerminalStatus.ACCEPTED
        and outcome.obligations.all_required_current
    )


def _ids_with_status(
    item_ids: tuple[str, ...],
    outcomes: dict[str, ItemOutcome],
    status: ItemTerminalStatus,
) -> tuple[str, ...]:
    return tuple(
        item_id
        for item_id in item_ids
        if item_id in outcomes and outcomes[item_id].status is status
    )


__all__ = [
    "ItemHandlerResult",
    "ItemLocalError",
    "ItemRunResult",
    "ItemWorkItem",
    "RetryableItemError",
    "SystemicJobError",
    "run_item_outcomes",
]
