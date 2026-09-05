"""Contract tests for job lifecycle models."""

from datetime import datetime, timedelta, timezone

from pydantic import ValidationError
import pytest

from multilang.domain.latin import LatinGenerationRequest, LatinVariant
from multilang.domain.jobs import (
    ControlledReasonCode,
    FieldObligationSummary,
    GenerationRequest,
    ItemAttemptRecord,
    ItemDiagnostic,
    ItemOutcome,
    ItemRunReport,
    ItemTerminalStatus,
    JobProgressSnapshot,
    JobStage,
    JobStatus,
    ResumeDiagnostic,
    SupportedLanguage,
)


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _attempt(*, processed: bool = True, offset_seconds: int = 0) -> ItemAttemptRecord:
    attempted_at = NOW + timedelta(seconds=offset_seconds)
    return ItemAttemptRecord(
        attempt_number=1,
        attempted_at=attempted_at,
        processed_at=attempted_at if processed else None,
    )


def _obligations(*, word_audio_current: bool = True) -> FieldObligationSummary:
    return FieldObligationSummary(
        ai_review_current=True,
        integrity_current=True,
        word_audio_required=True,
        word_audio_current=word_audio_current,
        sentence_audio_required=False,
    )


def test_supported_languages() -> None:
    assert {language.value for language in SupportedLanguage} == {
        "pt",
        "es",
        "en",
        "fr",
        "de",
        "el",
        "it",
        "pl",
        "tr",
        "ro",
        "ru",
        "nl",
        "da",
        "nb",
        "sv",
        "fi",
        "hu",
        "cs",
        "hr",
        "la",
        "ja",
        "zh",
        "ko",
    }

    request = GenerationRequest(language="pt", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.PT


def test_generation_request_accepts_norwegian_bokmal() -> None:
    request = GenerationRequest(language="nb", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.NB


def test_generation_request_accepts_danish() -> None:
    request = GenerationRequest(language="da", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.DA


def test_generation_request_accepts_swedish() -> None:
    request = GenerationRequest(language="sv", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.SV


def test_generation_request_accepts_finnish() -> None:
    request = GenerationRequest(language="fi", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.FI


def test_generation_request_accepts_hungarian() -> None:
    request = GenerationRequest(language="hu", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.HU


def test_generation_request_accepts_czech() -> None:
    request = GenerationRequest(language="cs", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.CS


def test_generation_request_accepts_greek() -> None:
    request = GenerationRequest(language="el", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.EL


def test_generation_request_accepts_croatian() -> None:
    request = GenerationRequest(language="hr", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.HR


def test_generation_request_accepts_japanese() -> None:
    request = GenerationRequest(language="ja", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.JA


@pytest.mark.parametrize("source_type", ["frequency", "word-list"])
def test_generation_request_accepts_canonical_mandarin_code(source_type: str) -> None:
    request = GenerationRequest(language="zh", source_type=source_type)

    assert request.language is SupportedLanguage.ZH


def test_generation_request_rejects_mandarin_locale_as_language_identity() -> None:
    with pytest.raises(ValidationError):
        GenerationRequest(language="zh-CN", source_type="frequency")


@pytest.mark.parametrize(
    "source_type",
    ["frequency", "word-list", "kindle-highlights"],
)
def test_generation_request_accepts_canonical_korean_code(source_type: str) -> None:
    request = GenerationRequest(language="ko", source_type=source_type)

    assert request.language is SupportedLanguage.KO


def test_generation_request_rejects_korean_locale_as_language_identity() -> None:
    with pytest.raises(ValidationError):
        GenerationRequest(language="ko-KR", source_type="frequency")


def test_generation_request_accepts_latin_mvp_source_for_shared_infrastructure() -> None:
    request = GenerationRequest(language="en", source_type="latin-mvp")

    assert request.language is SupportedLanguage.EN
    assert request.source_type == "latin-mvp"


def test_generation_request_accepts_latin_for_shared_infrastructure() -> None:
    request = GenerationRequest(language="la", source_type="word-list")

    assert request.language is SupportedLanguage.LA


def test_latin_contracts_remain_importable_separate_from_modern_generation_request() -> None:
    request = LatinGenerationRequest()

    assert request.language_code == "la"
    assert request.variant is LatinVariant.CLASSICAL
    assert request.source_type == "latin-mvp"


def test_generation_request_rejects_unsupported_language() -> None:
    with pytest.raises(ValidationError):
        GenerationRequest(language="zz", source_type="frequency", level=1)


def test_generation_request_accepts_existing_frequency_source_type() -> None:
    request = GenerationRequest(language="en", source_type="frequency")

    assert request.source_type == "frequency"


def test_generation_request_accepts_existing_word_list_source_type(tmp_path) -> None:
    source = tmp_path / "words.txt"
    source.write_text("alpha\n", encoding="utf-8")

    request = GenerationRequest(language="en", source_type="word-list", input_file=source)

    assert request.source_type == "word-list"
    assert request.input_file == source


def test_generation_request_accepts_internal_kindle_highlights_source_type(tmp_path) -> None:
    source = tmp_path / "kindle-highlights.html"
    source.write_text("synthetic highlight", encoding="utf-8")

    request = GenerationRequest(language="en", source_type="kindle-highlights", input_file=source)

    assert request.source_type == "kindle-highlights"
    assert request.input_file == source



def test_generation_request_rejects_unsupported_source_type() -> None:
    with pytest.raises(ValidationError):
        GenerationRequest(language="en", source_type="unsupported")


def test_resume_diagnostic_requires_reason() -> None:
    with pytest.raises(ValidationError):
        ResumeDiagnostic(job_id="job-123", reason="", details={"stage": "export"})


def test_resume_diagnostic_preserves_machine_readable_fields() -> None:
    diagnostic = ResumeDiagnostic(
        job_id="job-123",
        reason="resume_state_mismatch",
        details={"expected_stage": "enrich", "actual_stage": "export"},
    )

    assert diagnostic.reason == "resume_state_mismatch"
    assert diagnostic.job_id == "job-123"
    assert diagnostic.details == {
        "expected_stage": "enrich",
        "actual_stage": "export",
    }


def test_progress_snapshot_tracks_all_counters() -> None:
    snapshot = JobProgressSnapshot(
        stage=JobStage.SYNTHESIZE_AUDIO,
        completed_items=10,
        failed_items=2,
        retrying_items=1,
        skipped_duplicates=3,
    )

    assert snapshot.stage is JobStage.SYNTHESIZE_AUDIO
    assert snapshot.completed_items == 10
    assert snapshot.failed_items == 2
    assert snapshot.retrying_items == 1
    assert snapshot.skipped_duplicates == 3


def test_pending_processing_accepted_review_required_failed_are_only_item_terminal_statuses_and_processed_is_rejected() -> None:
    assert [status.value for status in ItemTerminalStatus] == [
        "pending",
        "processing",
        "accepted",
        "review_required",
        "failed",
    ]

    with pytest.raises(ValidationError):
        ItemOutcome(item_id="word-1", status="processed")


def test_attempted_at_and_processed_at_are_orthogonal_for_early_and_late_failed_items() -> None:
    early_failure = ItemOutcome(
        item_id="early",
        status=ItemTerminalStatus.FAILED,
        attempts=(_attempt(processed=False),),
        diagnostic=ItemDiagnostic(reason_code=ControlledReasonCode.ITEM_LOCAL_EXCEPTION),
    )
    late_failure = ItemOutcome(
        item_id="late",
        status=ItemTerminalStatus.FAILED,
        attempts=(_attempt(processed=True),),
        diagnostic=ItemDiagnostic(reason_code=ControlledReasonCode.ITEM_LOCAL_EXCEPTION),
    )
    processing = ItemOutcome(
        item_id="open",
        status=ItemTerminalStatus.PROCESSING,
        attempts=(_attempt(processed=False),),
    )

    assert early_failure.attempted_at == NOW
    assert early_failure.processed_at is None
    assert late_failure.attempted_at == NOW
    assert late_failure.processed_at == NOW
    assert processing.processed_at is None

    with pytest.raises(ValidationError):
        ItemAttemptRecord(
            attempt_number=1,
            attempted_at=NOW,
            processed_at=NOW - timedelta(seconds=1),
        )


def test_denominator_report_partitions_attempted_skipped_current_not_attempted_and_processed_subset() -> None:
    report = ItemRunReport(
        eligible_item_ids=("a", "b", "c", "d"),
        attempted_item_ids=("a", "b"),
        processed_item_ids=("b",),
        skipped_current_item_ids=("c",),
        not_attempted_item_ids=("d",),
        accepted_item_ids=("b", "c"),
        review_required_item_ids=("a",),
        failed_item_ids=(),
        field_obligations={"b": _obligations(), "c": _obligations()},
    )

    assert report.counts == {
        "total_eligible": 4,
        "attempted": 2,
        "processed": 1,
        "accepted": 2,
        "review_required": 1,
        "failed": 0,
        "skipped_current": 1,
        "not_attempted": 1,
        "duplicate": 0,
        "deferred": 0,
    }
    assert report.is_complete is False

    with pytest.raises(ValidationError):
        ItemRunReport(
            eligible_item_ids=("a", "b"),
            attempted_item_ids=("a",),
            processed_item_ids=("b",),
            skipped_current_item_ids=(),
            not_attempted_item_ids=("b",),
            accepted_item_ids=(),
            review_required_item_ids=(),
            failed_item_ids=(),
        )

    with pytest.raises(ValidationError):
        ItemRunReport(
            eligible_item_ids=("a", "b"),
            attempted_item_ids=("a",),
            processed_item_ids=(),
            skipped_current_item_ids=("a",),
            not_attempted_item_ids=("b",),
            accepted_item_ids=(),
            review_required_item_ids=(),
            failed_item_ids=(),
        )


def test_complete_requires_no_review_required_failed_not_attempted_or_media_debt() -> None:
    complete = ItemRunReport(
        eligible_item_ids=("a", "b"),
        attempted_item_ids=("a",),
        processed_item_ids=("a",),
        skipped_current_item_ids=("b",),
        not_attempted_item_ids=(),
        accepted_item_ids=("a", "b"),
        review_required_item_ids=(),
        failed_item_ids=(),
        field_obligations={"a": _obligations(), "b": _obligations()},
    )
    incomplete = ItemRunReport(
        eligible_item_ids=("a", "b"),
        attempted_item_ids=("a",),
        processed_item_ids=("a",),
        skipped_current_item_ids=(),
        not_attempted_item_ids=("b",),
        accepted_item_ids=("a",),
        review_required_item_ids=(),
        failed_item_ids=(),
        field_obligations={"a": _obligations()},
    )

    assert complete.is_complete is True
    assert incomplete.is_complete is False

    with pytest.raises(ValidationError):
        ItemOutcome(
            item_id="stale-audio",
            status=ItemTerminalStatus.ACCEPTED,
            attempts=(_attempt(processed=True),),
            obligations=_obligations(word_audio_current=False),
        )

    with pytest.raises(ValidationError):
        ItemOutcome(
            item_id="missing-evidence",
            status=ItemTerminalStatus.ACCEPTED,
            attempts=(_attempt(processed=True),),
        )


def test_existing_job_status_and_stage_payloads_keep_existing_serialization() -> None:
    snapshot = JobProgressSnapshot(
        stage=JobStage.GENERATE_TEXT,
        completed_items=1,
        failed_items=2,
        retrying_items=3,
        skipped_duplicates=4,
    )

    assert JobStatus.COMPLETED.value == "completed"
    assert snapshot.model_dump(mode="json") == {
        "stage": "generate_text",
        "completed_items": 1,
        "failed_items": 2,
        "retrying_items": 3,
        "skipped_duplicates": 4,
    }


def test_mixed_resumable_media_stale_later_accept_completion_matrix() -> None:
    stale_media = ItemOutcome(
        item_id="needs-audio",
        status=ItemTerminalStatus.REVIEW_REQUIRED,
        attempts=(_attempt(processed=True),),
        obligations=_obligations(word_audio_current=False),
        diagnostic=ItemDiagnostic(reason_code=ControlledReasonCode.MEDIA_OUTSTANDING),
    )
    blocked = ItemRunReport(
        eligible_item_ids=("ok", "needs-audio"),
        attempted_item_ids=("ok", "needs-audio"),
        processed_item_ids=("ok", "needs-audio"),
        skipped_current_item_ids=(),
        not_attempted_item_ids=(),
        accepted_item_ids=("ok",),
        review_required_item_ids=("needs-audio",),
        failed_item_ids=(),
        field_obligations={"ok": _obligations()},
    )
    later_accepted = ItemRunReport(
        eligible_item_ids=("ok", "needs-audio"),
        attempted_item_ids=("needs-audio",),
        processed_item_ids=("needs-audio",),
        skipped_current_item_ids=("ok",),
        not_attempted_item_ids=(),
        accepted_item_ids=("ok", "needs-audio"),
        review_required_item_ids=(),
        failed_item_ids=(),
        field_obligations={"ok": _obligations(), "needs-audio": _obligations()},
    )

    assert stale_media.obligations.has_outstanding_work is True
    assert blocked.is_complete is False
    assert blocked.is_resumable is True
    assert later_accepted.is_complete is True


def test_duplicate_deferred_and_force_complete_do_not_masquerade_as_complete() -> None:
    report = ItemRunReport(
        eligible_item_ids=("accepted", "duplicate", "deferred"),
        attempted_item_ids=("accepted",),
        processed_item_ids=("accepted",),
        skipped_current_item_ids=(),
        not_attempted_item_ids=("duplicate", "deferred"),
        accepted_item_ids=("accepted",),
        review_required_item_ids=(),
        failed_item_ids=(),
        duplicate_item_ids=("duplicate",),
        deferred_item_ids=("deferred",),
        field_obligations={"accepted": _obligations()},
    )

    assert report.counts["duplicate"] == 1
    assert report.counts["deferred"] == 1
    assert report.is_complete is False

    with pytest.raises(ValidationError):
        ItemRunReport(
            eligible_item_ids=("accepted",),
            attempted_item_ids=("accepted",),
            processed_item_ids=("accepted",),
            skipped_current_item_ids=(),
            not_attempted_item_ids=(),
            accepted_item_ids=("accepted",),
            review_required_item_ids=(),
            failed_item_ids=(),
            field_obligations={"accepted": _obligations()},
            force_complete=True,
        )
