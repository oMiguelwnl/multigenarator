"""Tests for item-local outcome isolation and aggregation."""

from datetime import datetime, timezone

import pytest

from multilang.domain.jobs import (
    ControlledReasonCode,
    FieldObligationSummary,
    ItemAttemptRecord,
    ItemDiagnostic,
    ItemOutcome,
    ItemTerminalStatus,
)
from multilang.services.item_outcomes import (
    ItemHandlerResult,
    ItemLocalError,
    ItemWorkItem,
    RetryableItemError,
    SystemicJobError,
    run_item_outcomes,
)


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _current_obligations() -> FieldObligationSummary:
    return FieldObligationSummary(
        ai_review_current=True,
        integrity_current=True,
        word_audio_required=True,
        word_audio_current=True,
        sentence_audio_required=True,
        sentence_audio_current=True,
    )


def _stale_audio_obligations() -> FieldObligationSummary:
    return FieldObligationSummary(
        ai_review_current=True,
        integrity_current=True,
        word_audio_required=True,
        word_audio_current=False,
        sentence_audio_required=True,
        sentence_audio_current=True,
    )


def _accepted_prior(item_id: str) -> ItemOutcome:
    return ItemOutcome(
        item_id=item_id,
        status=ItemTerminalStatus.ACCEPTED,
        attempts=(
            ItemAttemptRecord(attempt_number=1, attempted_at=NOW, processed_at=NOW),
        ),
        obligations=_current_obligations(),
    )


def test_continue_preserves_order_after_item_local_exception_and_aggregate_counts() -> None:
    saved: list[ItemOutcome] = []

    def handle(item: ItemWorkItem, attempt_number: int) -> ItemHandlerResult:
        if item.item_id == "b":
            raise ItemLocalError(
                reason_code=ControlledReasonCode.ITEM_LOCAL_EXCEPTION,
                terminal_status=ItemTerminalStatus.FAILED,
            )
        return ItemHandlerResult(status=ItemTerminalStatus.ACCEPTED, obligations=_current_obligations())

    result = run_item_outcomes(
        [ItemWorkItem(item_id="a"), ItemWorkItem(item_id="b"), ItemWorkItem(item_id="c")],
        validate=lambda items: None,
        handle=handle,
        load_prior=lambda item: None,
        save_atomic=lambda outcome: saved.append(outcome) or outcome,
        now=lambda: NOW,
    )

    assert [outcome.item_id for outcome in saved] == ["a", "b", "c"]
    assert [outcome.item_id for outcome in result.outcomes] == ["a", "b", "c"]
    assert result.report.counts["attempted"] == 3
    assert result.report.counts["accepted"] == 2
    assert result.report.counts["failed"] == 1
    assert result.report.is_complete is False


def test_systemic_failure_stops_before_item_processing_or_immediately() -> None:
    handled: list[str] = []
    saved: list[ItemOutcome] = []

    def validate(items: tuple[ItemWorkItem, ...]) -> None:
        raise SystemicJobError("schema mismatch PRIVATE_TOKEN")

    with pytest.raises(SystemicJobError):
        run_item_outcomes(
            [ItemWorkItem(item_id="a"), ItemWorkItem(item_id="b")],
            validate=validate,
            handle=lambda item, attempt_number: handled.append(item.item_id),
            load_prior=lambda item: None,
            save_atomic=lambda outcome: saved.append(outcome) or outcome,
            now=lambda: NOW,
        )

    assert handled == []
    assert saved == []

    with pytest.raises(SystemicJobError):
        run_item_outcomes(
            [ItemWorkItem(item_id="a")],
            validate=lambda items: None,
            handle=lambda item, attempt_number: {"status": "processed"},
            load_prior=lambda item: None,
            save_atomic=lambda outcome: saved.append(outcome) or outcome,
            now=lambda: NOW,
        )

    assert saved == []


def test_exception_private_provider_strings_become_content_free_diagnostics() -> None:
    secret = "PRIVATE_PROVIDER_PAYLOAD_123"

    def handle(item: ItemWorkItem, attempt_number: int) -> ItemHandlerResult:
        raise RuntimeError(f"provider leaked {secret}")

    result = run_item_outcomes(
        [ItemWorkItem(item_id="a")],
        validate=lambda items: None,
        handle=handle,
        load_prior=lambda item: None,
        save_atomic=lambda outcome: outcome,
        now=lambda: NOW,
        correlation_id_factory=lambda: "corr-123",
    )

    outcome = result.outcomes[0]
    assert outcome.status is ItemTerminalStatus.FAILED
    assert outcome.diagnostic == ItemDiagnostic(
        reason_code=ControlledReasonCode.FAILED_UNKNOWN,
        correlation_id="corr-123",
    )
    assert secret not in outcome.model_dump_json()
    assert "provider leaked" not in outcome.model_dump_json()

    default_correlation = run_item_outcomes(
        [ItemWorkItem(item_id="b")],
        validate=lambda items: None,
        handle=handle,
        load_prior=lambda item: None,
        save_atomic=lambda outcome: outcome,
        now=lambda: NOW,
    ).outcomes[0].diagnostic.correlation_id
    assert default_correlation
    assert default_correlation != "failed_unknown"


def test_idempotent_completed_key_skips_side_effects_and_marks_skipped_current() -> None:
    handled: list[str] = []

    result = run_item_outcomes(
        [ItemWorkItem(item_id="a", idempotency_key="key-a")],
        validate=lambda items: None,
        handle=lambda item, attempt_number: handled.append(item.item_id),
        load_prior=lambda item: _accepted_prior(item.item_id),
        save_atomic=lambda outcome: outcome,
        now=lambda: NOW,
    )

    assert handled == []
    assert result.report.counts["attempted"] == 0
    assert result.report.counts["skipped_current"] == 1
    assert result.report.counts["accepted"] == 1
    assert result.report.is_complete is True


def test_retry_is_bounded_and_aggregate_uses_persisted_outcome_not_optimistic_handler_result() -> None:
    attempts: list[int] = []

    def handle(item: ItemWorkItem, attempt_number: int) -> ItemHandlerResult:
        attempts.append(attempt_number)
        if item.item_id == "retry-me":
            raise RetryableItemError(reason_code=ControlledReasonCode.ITEM_LOCAL_EXCEPTION)
        return ItemHandlerResult(status=ItemTerminalStatus.ACCEPTED, obligations=_current_obligations())

    def save_atomic(outcome: ItemOutcome) -> ItemOutcome:
        if outcome.item_id == "optimistic":
            return outcome.model_copy(
                update={
                    "status": ItemTerminalStatus.REVIEW_REQUIRED,
                    "diagnostic": ItemDiagnostic(reason_code=ControlledReasonCode.REVIEW_OUTSTANDING),
                }
            )
        return outcome

    result = run_item_outcomes(
        [ItemWorkItem(item_id="retry-me"), ItemWorkItem(item_id="optimistic")],
        validate=lambda items: None,
        handle=handle,
        load_prior=lambda item: None,
        save_atomic=save_atomic,
        now=lambda: NOW,
        max_attempts=2,
    )

    retry_outcome = result.outcomes[0]
    assert attempts == [1, 2, 1]
    assert retry_outcome.status is ItemTerminalStatus.FAILED
    assert len(retry_outcome.attempts) == 2
    assert retry_outcome.diagnostic == ItemDiagnostic(reason_code=ControlledReasonCode.RETRY_EXHAUSTED)
    assert result.report.counts["accepted"] == 0
    assert result.report.counts["review_required"] == 1
    assert result.report.counts["failed"] == 1


def test_mixed_resumable_media_stale_later_accept_completion_transition() -> None:
    store: dict[str, ItemOutcome] = {}

    def save_atomic(outcome: ItemOutcome) -> ItemOutcome:
        store[outcome.item_id] = outcome
        return outcome

    first = run_item_outcomes(
        [ItemWorkItem(item_id="accepted"), ItemWorkItem(item_id="needs-media")],
        validate=lambda items: None,
        handle=lambda item, attempt_number: ItemHandlerResult(
            status=(
                ItemTerminalStatus.REVIEW_REQUIRED
                if item.item_id == "needs-media"
                else ItemTerminalStatus.ACCEPTED
            ),
            obligations=(
                _stale_audio_obligations()
                if item.item_id == "needs-media"
                else _current_obligations()
            ),
            reason_code=(
                ControlledReasonCode.MEDIA_OUTSTANDING
                if item.item_id == "needs-media"
                else None
            ),
        ),
        load_prior=lambda item: store.get(item.item_id),
        save_atomic=save_atomic,
        now=lambda: NOW,
    )

    second = run_item_outcomes(
        [ItemWorkItem(item_id="accepted"), ItemWorkItem(item_id="needs-media")],
        validate=lambda items: None,
        handle=lambda item, attempt_number: ItemHandlerResult(
            status=ItemTerminalStatus.ACCEPTED,
            obligations=_current_obligations(),
        ),
        load_prior=lambda item: store.get(item.item_id),
        save_atomic=save_atomic,
        now=lambda: NOW,
    )

    assert first.report.is_complete is False
    assert first.report.is_resumable is True
    assert first.report.counts["review_required"] == 1
    assert second.report.counts["skipped_current"] == 1
    assert second.report.counts["attempted"] == 1
    assert second.report.is_complete is True


def test_duplicate_and_deferred_rows_are_explicit_not_attempted_denominators() -> None:
    handled: list[str] = []

    result = run_item_outcomes(
        [
            ItemWorkItem(item_id="accepted"),
            ItemWorkItem(item_id="duplicate", duplicate_of="accepted"),
            ItemWorkItem(item_id="deferred", deferred_reason_code=ControlledReasonCode.DEFERRED),
        ],
        validate=lambda items: None,
        handle=lambda item, attempt_number: handled.append(item.item_id)
        or ItemHandlerResult(status=ItemTerminalStatus.ACCEPTED, obligations=_current_obligations()),
        load_prior=lambda item: None,
        save_atomic=lambda outcome: outcome,
        now=lambda: NOW,
    )

    assert handled == ["accepted"]
    assert result.report.counts["attempted"] == 1
    assert result.report.counts["not_attempted"] == 2
    assert result.report.counts["duplicate"] == 1
    assert result.report.counts["deferred"] == 1
    assert result.report.counts["accepted"] == 1
    assert result.report.is_complete is False
