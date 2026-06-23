"""Contract tests for job lifecycle models."""

from pydantic import ValidationError
import pytest

from multilang.domain.latin import LatinGenerationRequest, LatinVariant
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
        "it",
        "pl",
        "tr",
        "ro",
        "ru",
        "nl",
        "nb",
        "la",
    }

    request = GenerationRequest(language="pt", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.PT


def test_generation_request_accepts_norwegian_bokmal() -> None:
    request = GenerationRequest(language="nb", source_type="frequency", level=1)

    assert request.language is SupportedLanguage.NB


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
        GenerationRequest(language="sv", source_type="frequency", level=1)


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
