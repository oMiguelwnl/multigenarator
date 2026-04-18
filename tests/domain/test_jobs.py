"""Contract tests for job lifecycle models."""

from pydantic import ValidationError
import pytest

from multilang.domain.jobs import (
    GenerationRequest,
    JobProgressSnapshot,
    JobStage,
    ResumeDiagnostic,
    SupportedLanguage,
)


def test_supported_languages() -> None:
    assert {language.value for language in SupportedLanguage} == {
        "pt",
        "es",
        "en",
        "fr",
        "de",
        "ru",
        "nl",
    }

    request = GenerationRequest(language="pt", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.PT


def test_generation_request_rejects_unsupported_language() -> None:
    with pytest.raises(ValidationError):
        GenerationRequest(language="it", source_type="frequency", level=1)


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
