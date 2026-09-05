"""Tests for Phase 33 source-aware persisted job coordination."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.jobs import (
    ControlledReasonCode,
    FieldObligationSummary,
    GenerationRequest,
    ItemTerminalStatus,
    JobStage,
    SupportedLanguage,
)
from multilang.repositories.job_repository import JobRepository
from multilang.services.item_outcomes import ItemHandlerResult, ItemLocalError, SystemicJobError
from multilang.services.phase33_jobs import Phase33JobCoordinator, Phase33JobItem


NOW = datetime(2026, 1, 3, 4, 5, tzinfo=timezone.utc)


def build_repository() -> tuple[JobRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return JobRepository(session), session


def make_job(repository: JobRepository, *, source_type: str = "word-list") -> str:
    job = repository.create_job(
        request=GenerationRequest(language=SupportedLanguage.KO, source_type=source_type),
        run_key=f"ko-phase33-{source_type}",
        source_fingerprint="fixture",
        total_items=10,
    )
    return job.id


def current_obligations() -> FieldObligationSummary:
    return FieldObligationSummary(
        ai_review_current=True,
        integrity_current=True,
        word_audio_required=True,
        word_audio_current=True,
        sentence_audio_required=True,
        sentence_audio_current=True,
    )


def stale_obligations() -> FieldObligationSummary:
    return FieldObligationSummary(
        ai_review_current=True,
        integrity_current=True,
        word_audio_required=True,
        word_audio_current=False,
        sentence_audio_required=True,
        sentence_audio_current=True,
    )


@dataclass
class FakeSource:
    items: tuple[Phase33JobItem, ...]

    def list_items(self, job_id: str) -> tuple[Phase33JobItem, ...]:
        return self.items


@dataclass
class RecordingHandlers:
    calls: list[str] = field(default_factory=list)

    def accepted(self, item: Phase33JobItem, attempt_number: int) -> ItemHandlerResult:
        self.calls.append(item.item_id)
        return ItemHandlerResult(status=ItemTerminalStatus.ACCEPTED, obligations=current_obligations())

    def review_required(self, item: Phase33JobItem, attempt_number: int) -> ItemHandlerResult:
        self.calls.append(item.item_id)
        return ItemHandlerResult(
            status=ItemTerminalStatus.REVIEW_REQUIRED,
            obligations=stale_obligations(),
            reason_code=ControlledReasonCode.MEDIA_OUTSTANDING,
        )

    def item_failed(self, item: Phase33JobItem, attempt_number: int) -> ItemHandlerResult:
        self.calls.append(item.item_id)
        raise ItemLocalError(reason_code=ControlledReasonCode.ITEM_LOCAL_EXCEPTION)


def test_grammar_custom_highlight_start_deterministic_order_isolation_and_seven_denominators() -> None:
    repository, _session = build_repository()
    job_id = make_job(repository)
    handlers = RecordingHandlers()
    coordinator = Phase33JobCoordinator(
        job_repository=repository,
        sources={
            "grammar": FakeSource((Phase33JobItem(source_family="grammar", item_id="grammar:topic"),)),
            "custom": FakeSource(
                (
                    Phase33JobItem(source_family="custom", item_id="custom:duplicate", duplicate_of="custom:failed"),
                    Phase33JobItem(source_family="custom", item_id="custom:failed"),
                )
            ),
            "highlight": FakeSource((Phase33JobItem(source_family="highlight", item_id="highlight:needs-media"),)),
        },
        handlers={
            "grammar": handlers.accepted,
            "custom": handlers.item_failed,
            "highlight": handlers.review_required,
        },
        now=lambda: NOW,
    )

    result = coordinator.execute(job_id=job_id, mode="start")

    assert handlers.calls == ["grammar:topic", "custom:failed", "highlight:needs-media"]
    assert result.processed_item_ids == ("grammar:topic", "highlight:needs-media")
    assert result.failed_item_ids == ("custom:failed",)
    assert result.report.counts == {
        "total_eligible": 4,
        "attempted": 3,
        "processed": 2,
        "accepted": 1,
        "review_required": 1,
        "failed": 1,
        "skipped_current": 0,
        "not_attempted": 1,
        "duplicate": 1,
        "deferred": 0,
    }
    assert result.report.duplicate_item_ids == ("custom:duplicate",)
    assert result.report.is_complete is False


def test_resume_persisted_facts_skip_current_accepted_retry_pending_leave_review_required_no_repeat_disclosing_disclosed_failed_unknown() -> None:
    repository, _session = build_repository()
    job_id = make_job(repository, source_type="kindle-highlights")
    stage = JobStage.GENERATE_TEXT.value
    repository.record_phase33_skipped_current(
        job_id,
        item_id="accepted-current",
        stage=stage,
        terminal_status=ItemTerminalStatus.ACCEPTED,
        obligations=current_obligations(),
    )
    repository.record_phase33_item_outcome(
        job_id,
        item_id="review-current",
        stage=stage,
        attempt_count=1,
        attempted_at=NOW,
        processed_at=NOW,
        terminal_status=ItemTerminalStatus.REVIEW_REQUIRED,
        reason_code=ControlledReasonCode.REVIEW_OUTSTANDING,
        obligations=stale_obligations(),
        idempotency_key="review-current",
    )
    handlers = RecordingHandlers()
    coordinator = Phase33JobCoordinator(
        job_repository=repository,
        sources={
            "highlight": FakeSource(
                (
                    Phase33JobItem(source_family="highlight", item_id="accepted-current"),
                    Phase33JobItem(source_family="highlight", item_id="pending-new"),
                    Phase33JobItem(source_family="highlight", item_id="retryable-pending", retryable=True),
                    Phase33JobItem(source_family="highlight", item_id="review-current"),
                    Phase33JobItem(source_family="highlight", item_id="private-disclosing", private_state="disclosing"),
                    Phase33JobItem(source_family="highlight", item_id="private-disclosed", private_state="disclosed"),
                    Phase33JobItem(source_family="highlight", item_id="private-failed", private_state="failed_unknown"),
                )
            )
        },
        handlers={"highlight": handlers.accepted},
        now=lambda: NOW,
    )

    result = coordinator.execute(job_id=job_id, mode="resume", max_items=2)

    assert handlers.calls == ["pending-new", "retryable-pending"]
    assert result.report.skipped_current_item_ids == ("accepted-current",)
    assert result.report.review_required_item_ids == ("review-current",)
    assert set(result.report.not_attempted_item_ids) == {
        "private-disclosing",
        "private-disclosed",
        "private-failed",
    }


def test_start_new_only_skips_attempt_only_pending_and_resume_retry_pending() -> None:
    repository, _session = build_repository()
    start_job_id = make_job(repository, source_type="word-list")
    stage = JobStage.GENERATE_TEXT.value
    repository.record_phase33_attempt_fact(
        start_job_id,
        item_id="pending-open",
        stage=stage,
        attempt_count=1,
        attempted_at=NOW,
        processed_at=None,
        idempotency_key="pending-open-attempt",
    )
    handlers = RecordingHandlers()
    start_coordinator = Phase33JobCoordinator(
        job_repository=repository,
        sources={
            "grammar": FakeSource(
                (
                    Phase33JobItem(source_family="grammar", item_id="pending-open"),
                    Phase33JobItem(source_family="grammar", item_id="new-item"),
                )
            )
        },
        handlers={"grammar": handlers.accepted},
        now=lambda: NOW,
    )

    start_result = start_coordinator.execute(job_id=start_job_id, mode="start")

    assert handlers.calls == ["new-item"]
    assert start_result.report.accepted_item_ids == ("new-item",)

    resume_repository, _resume_session = build_repository()
    resume_job_id = make_job(resume_repository, source_type="word-list")
    resume_repository.record_phase33_attempt_fact(
        resume_job_id,
        item_id="pending-open",
        stage=stage,
        attempt_count=1,
        attempted_at=NOW,
        processed_at=None,
        idempotency_key="pending-open-attempt",
    )
    resume_handlers = RecordingHandlers()
    resume_coordinator = Phase33JobCoordinator(
        job_repository=resume_repository,
        sources={"grammar": FakeSource((Phase33JobItem(source_family="grammar", item_id="pending-open"),))},
        handlers={"grammar": resume_handlers.accepted},
        now=lambda: NOW,
    )

    resume_result = resume_coordinator.execute(job_id=resume_job_id, mode="resume")

    assert resume_handlers.calls == ["pending-open"]
    assert resume_result.report.accepted_item_ids == ("pending-open",)


def test_systemic_failure_stops_fail_closed_without_later_item_processing() -> None:
    repository, _session = build_repository()
    job_id = make_job(repository)
    calls: list[str] = []

    def systemic(item: Phase33JobItem, attempt_number: int) -> ItemHandlerResult:
        calls.append(item.item_id)
        raise SystemicJobError("schema/config authority mismatch")

    coordinator = Phase33JobCoordinator(
        job_repository=repository,
        sources={
            "grammar": FakeSource(
                (
                    Phase33JobItem(source_family="grammar", item_id="grammar:broken"),
                    Phase33JobItem(source_family="grammar", item_id="grammar:later"),
                )
            )
        },
        handlers={"grammar": systemic},
        now=lambda: NOW,
    )

    with pytest.raises(SystemicJobError):
        coordinator.execute(job_id=job_id, mode="start")

    assert calls == ["grammar:broken"]
    assert repository.list_phase33_item_statuses(job_id, stage=JobStage.GENERATE_TEXT.value) == ()
