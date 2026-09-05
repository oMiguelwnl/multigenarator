"""Repository tests for persisted job orchestration state."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.db.models import GenerationRunDenominatorModel, ItemProcessingFactModel, ItemTerminalStatusEventModel
from multilang.domain.highlights import HighlightProvenance, NormalizedHighlight
from multilang.domain.korean import KoreanFrequencyJobAuthority, raw_bytes_sha256
from multilang.domain.jobs import (
    ControlledReasonCode,
    FieldObligationSummary,
    GenerationRequest,
    ItemTerminalStatus,
    JobStage,
    JobStatus,
    SupportedLanguage,
)
from multilang.domain.personal_sources import PersonalSourceRow
from multilang.repositories.highlight_import_repository import HighlightImportRepository
from multilang.repositories.job_repository import JobRepository
from multilang.repositories.korean_personal_source_repository import KoreanPersonalSourceRepository
from multilang.services.authority_locator import canonical_authority_locator_sha256


def build_repository() -> tuple[JobRepository, Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return JobRepository(session), session


def make_request() -> GenerationRequest:
    return GenerationRequest(language=SupportedLanguage.EN, source_type="frequency", level=1)


def _hash(seed: str) -> str:
    return raw_bytes_sha256(seed.encode("utf-8"))


NOW = datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc)


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


def _authority(stage: str = "pilot_base", **overrides: str) -> KoreanFrequencyJobAuthority:
    payload = {
        "stage": stage,
        "phase31_pointer_locator_sha256": _hash("phase31-pointer-locator"),
        "phase31_pointer_content_sha256": _hash("phase31-pointer-content"),
        "phase31_validation_receipt_sha256": _hash("phase31-validation-receipt"),
        "phase31_snapshot_manifest_sha256": _hash("phase31-snapshot-manifest"),
        "phase31_snapshot_root_sha256": _hash("phase31-snapshot-root"),
        "frequency_bundle_locator_sha256": _hash("frequency-bundle-locator"),
        "frequency_bundle_content_sha256": _hash("frequency-bundle-content"),
        "source_retrieval_sha256": _hash("source-retrieval"),
        "source_build_result_sha256": _hash("source-build-result"),
        "source_review_aggregate_sha256": _hash("source-review-aggregate"),
        "provider_policy_sha256": _hash("provider-policy"),
        "pilot_authority_sha256": _hash("pilot-authority"),
    }
    if stage in {"pilot_audio", "full"}:
        payload.update(
            {
                "catalog_locator_sha256": _hash("catalog-locator"),
                "catalog_content_sha256": _hash("catalog-content"),
                "profile_sample_authority_sha256": _hash("profile-sample-authority"),
            }
        )
    if stage == "full":
        payload.update(
            {
                "provider_review_authority_sha256": _hash("provider-review-authority"),
                "heard_review_authority_sha256": _hash("heard-review-authority"),
            }
        )
    payload.update(overrides)
    return KoreanFrequencyJobAuthority.model_validate(payload)


def test_completed_items_are_reused_on_rerun() -> None:
    repository, session = build_repository()
    job = repository.create_job(
        request=make_request(),
        run_key="en-frequency-level-1",
        source_fingerprint="level-1",
        total_items=3,
    )

    repository.record_item_success(job.id, item_key="hola", completed_stage=JobStage.INGEST)
    repository.record_item_success(job.id, item_key="hola", completed_stage=JobStage.INGEST)
    session.expire_all()

    rerun = repository.get_job(run_key="en-frequency-level-1")

    assert rerun is not None
    assert repository.list_completed_item_keys("en-frequency-level-1") == {"hola"}
    assert rerun.completed_items == 1
    assert rerun.skipped_duplicates == 1


def test_corrupted_resume_state_returns_diagnostic() -> None:
    repository, session = build_repository()
    job = repository.create_job(
        request=make_request(),
        run_key="en-frequency-level-1",
        source_fingerprint="level-1",
        total_items=2,
        current_stage=JobStage.GENERATE_TEXT,
        last_completed_stage=JobStage.GENERATE_TEXT,
        status=JobStatus.RUNNING,
    )
    repository.record_item_success(job.id, item_key="hola", completed_stage=JobStage.INGEST)
    job.current_stage = JobStage.GENERATE_TEXT.value
    job.last_completed_stage = JobStage.GENERATE_TEXT.value
    session.add(job)
    session.commit()

    diagnostic = repository.validate_resume_state(job.id)

    assert diagnostic is not None
    assert diagnostic.job_id == job.id
    assert diagnostic.reason
    assert diagnostic.details["stored_current_stage"] == JobStage.GENERATE_TEXT.value
    assert diagnostic.details["actual_last_completed_stage"] == JobStage.INGEST.value


def test_duplicate_item_success_is_not_silently_persisted_twice() -> None:
    repository, session = build_repository()
    job = repository.create_job(
        request=make_request(),
        run_key="en-frequency-level-1",
        source_fingerprint="level-1",
        total_items=1,
    )

    repository.record_item_success(job.id, item_key="hola", completed_stage=JobStage.INGEST)
    repository.record_item_success(job.id, item_key="hola", completed_stage=JobStage.INGEST)

    assert session.execute(
        text(
            "SELECT COUNT(*) FROM generation_items "
            "WHERE run_key = 'en-frequency-level-1' AND item_key = 'hola'"
        )
    ).scalar_one() == 1


def test_stage_progression_does_not_count_as_duplicate_skip() -> None:
    repository, _ = build_repository()
    job = repository.create_job(
        request=make_request(),
        run_key="en-frequency-level-1",
        source_fingerprint="level-1",
        total_items=1,
    )

    repository.record_item_success(job.id, item_key="hola", completed_stage=JobStage.INGEST)
    snapshot = repository.record_item_success(
        job.id,
        item_key="hola",
        completed_stage=JobStage.GENERATE_TEXT,
    )

    refreshed = repository.get_job(job.id)

    assert refreshed is not None
    assert refreshed.skipped_duplicates == 0
    assert refreshed.last_completed_stage == JobStage.GENERATE_TEXT.value
    assert snapshot.stage == JobStage.GENERATE_TEXT


def test_canonical_authority_locator_hashes_repo_relative_length_prefixed_paths(tmp_path) -> None:
    repo_root = tmp_path / "repo"
    evidence_dir = repo_root / "evidence"
    evidence_dir.mkdir(parents=True)
    authority_file = evidence_dir / "authority.json"
    authority_file.write_text("{}", encoding="utf-8")

    digest = canonical_authority_locator_sha256(authority_file, repo_root=repo_root)
    canonical_locator = b"evidence/authority.json"

    assert digest == raw_bytes_sha256(len(canonical_locator).to_bytes(8, "big") + canonical_locator)
    assert canonical_authority_locator_sha256(repo_root / "evidence" / ".." / "evidence" / "authority.json", repo_root=repo_root) == digest


def test_canonical_authority_locator_rejects_missing_outside_and_symlink(tmp_path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    target = repo_root / "target.json"
    target.write_text("{}", encoding="utf-8")
    linked = repo_root / "linked.json"
    linked.symlink_to(target)

    for path in (repo_root / "missing.json", outside, linked):
        with pytest.raises(ValueError):
            canonical_authority_locator_sha256(path, repo_root=repo_root)


def test_execution_authority_exact_retry_is_no_update_and_drift_is_rejected() -> None:
    repository, session = build_repository()
    job = repository.create_job(
        request=GenerationRequest(language=SupportedLanguage.KO, source_type="frequency", level=1),
        run_key="ko-frequency-pilot-base",
        source_fingerprint="source-fixture",
        total_items=3000,
    )
    authority = _authority()
    update_count = 0

    def count_updates(*args: object) -> None:
        nonlocal update_count
        statement = str(args[2]).upper()
        if statement.startswith("UPDATE "):
            update_count += 1

    event.listen(session.bind, "before_cursor_execute", count_updates)
    try:
        inserted = repository.bind_execution_authority(job.id, authority)
        update_count = 0
        retried = repository.bind_execution_authority(job.id, authority)

        assert inserted == authority
        assert retried == authority
        assert update_count == 0
        with pytest.raises(ValueError):
            repository.bind_execution_authority(
                job.id,
                _authority(frequency_bundle_content_sha256=_hash("changed-bundle")),
            )
        assert repository.count_provider_attempts(job.id) == 0
    finally:
        event.remove(session.bind, "before_cursor_execute", count_updates)


def test_attempt_guard_requires_base_audio_and_full_authority() -> None:
    repository, _ = build_repository()
    job = repository.create_job(
        request=GenerationRequest(language=SupportedLanguage.KO, source_type="frequency", level=1),
        run_key="ko-frequency-guards",
        source_fingerprint="source-fixture",
        total_items=3000,
    )

    with pytest.raises(ValueError):
        repository.require_korean_attempt_authority(job.id, "pilot_text")

    repository.bind_execution_authority(job.id, _authority("pilot_base"))
    repository.require_korean_attempt_authority(job.id, "pilot_text")
    repository.require_korean_attempt_authority(job.id, "pilot_catalog")
    with pytest.raises(ValueError):
        repository.require_korean_attempt_authority(job.id, "pilot_audio_sample")

    repository.bind_audio_authority(job.id, _authority("pilot_audio"))
    repository.require_korean_attempt_authority(job.id, "pilot_audio_sample")
    with pytest.raises(ValueError):
        repository.require_korean_attempt_authority(job.id, "production_text")

    repository.bind_audio_authority(job.id, _authority("full"))
    repository.require_korean_attempt_authority(job.id, "production_text")
    repository.require_korean_attempt_authority(job.id, "production_audio")


def test_granular_outcome_retry_conflict_and_private_sentinel_content_free_facts() -> None:
    repository, session = build_repository()
    job = repository.create_job(
        request=GenerationRequest(language=SupportedLanguage.KO, source_type="word-list"),
        run_key="ko-custom-granular-outcome",
        source_fingerprint="custom-fixture",
        total_items=1,
    )
    sentinel = "PRIVATE_PROVIDER_PAYLOAD should never persist"

    first = repository.record_phase33_item_outcome(
        job.id,
        item_id="custom:1",
        stage=JobStage.GENERATE_TEXT.value,
        attempt_count=1,
        attempted_at=NOW,
        processed_at=NOW,
        terminal_status=ItemTerminalStatus.REVIEW_REQUIRED,
        reason_code=ControlledReasonCode.REVIEW_OUTSTANDING,
        obligations=_stale_audio_obligations(),
        idempotency_key="provider-command-1",
    )
    replay = repository.record_phase33_item_outcome(
        job.id,
        item_id="custom:1",
        stage=JobStage.GENERATE_TEXT.value,
        attempt_count=1,
        attempted_at=NOW,
        processed_at=NOW,
        terminal_status=ItemTerminalStatus.REVIEW_REQUIRED,
        reason_code=ControlledReasonCode.REVIEW_OUTSTANDING,
        obligations=_stale_audio_obligations(),
        idempotency_key="provider-command-1",
    )

    assert replay == first
    with pytest.raises(ValueError):
        repository.record_phase33_item_outcome(
            job.id,
            item_id="custom:1",
            stage=JobStage.GENERATE_TEXT.value,
            attempt_count=1,
            attempted_at=NOW,
            processed_at=NOW,
            terminal_status=ItemTerminalStatus.ACCEPTED,
            reason_code=None,
            obligations=_current_obligations(),
            idempotency_key="provider-command-1",
        )

    assert session.query(ItemProcessingFactModel).count() == 1
    assert session.query(ItemTerminalStatusEventModel).count() == 1
    safe_rows = repository.list_phase33_item_statuses(job.id, stage=JobStage.GENERATE_TEXT.value)
    rendered = str([row.model_dump(mode="json") for row in safe_rows])
    assert safe_rows[0].item_id == "custom:1"
    assert safe_rows[0].reason_code == ControlledReasonCode.REVIEW_OUTSTANDING.value
    assert sentinel not in rendered
    assert "PRIVATE_PROVIDER_PAYLOAD" not in rendered


def test_seven_denominators_aggregate_uses_persisted_facts_not_caller_totals() -> None:
    repository, session = build_repository()
    job = repository.create_job(
        request=GenerationRequest(language=SupportedLanguage.KO, source_type="word-list"),
        run_key="ko-custom-seven-denominators",
        source_fingerprint="custom-fixture",
        total_items=8,
    )
    stage = JobStage.GENERATE_TEXT.value
    repository.record_phase33_item_outcome(
        job.id,
        item_id="accepted-run",
        stage=stage,
        attempt_count=1,
        attempted_at=NOW,
        processed_at=NOW,
        terminal_status=ItemTerminalStatus.ACCEPTED,
        reason_code=None,
        obligations=_current_obligations(),
        idempotency_key="accepted-command",
    )
    repository.record_phase33_item_outcome(
        job.id,
        item_id="review-run",
        stage=stage,
        attempt_count=1,
        attempted_at=NOW,
        processed_at=NOW,
        terminal_status=ItemTerminalStatus.REVIEW_REQUIRED,
        reason_code=ControlledReasonCode.MEDIA_OUTSTANDING,
        obligations=_stale_audio_obligations(),
        idempotency_key="review-command",
    )
    repository.record_phase33_attempt_fact(
        job.id,
        item_id="attempt-open",
        stage=stage,
        attempt_count=1,
        attempted_at=NOW,
        processed_at=None,
        idempotency_key="open-command",
    )
    repository.record_phase33_skipped_current(
        job.id,
        item_id="accepted-before-run",
        stage=stage,
        terminal_status=ItemTerminalStatus.ACCEPTED,
        obligations=_current_obligations(),
    )
    repository.record_phase33_item_outcome(
        job.id,
        item_id="failed-run",
        stage=stage,
        attempt_count=1,
        attempted_at=NOW,
        processed_at=None,
        terminal_status=ItemTerminalStatus.FAILED,
        reason_code=ControlledReasonCode.FAILED_UNKNOWN,
        obligations=FieldObligationSummary(),
        idempotency_key="failed-command",
    )

    report = repository.recompute_phase33_run_report(
        job.id,
        stage=stage,
        eligible_item_ids=(
            "accepted-run",
            "review-run",
            "attempt-open",
            "accepted-before-run",
            "duplicate-row",
            "deferred-row",
            "untouched-row",
            "failed-run",
        ),
        duplicate_item_ids=("duplicate-row",),
        deferred_item_ids=("deferred-row",),
    )

    assert report.counts == {
        "total_eligible": 8,
        "attempted": 4,
        "processed": 2,
        "accepted": 2,
        "review_required": 1,
        "failed": 1,
        "skipped_current": 1,
        "not_attempted": 3,
        "duplicate": 1,
        "deferred": 1,
    }
    assert report.attempted_item_ids == ("accepted-run", "review-run", "attempt-open", "failed-run")
    assert report.processed_item_ids == ("accepted-run", "review-run")
    assert report.skipped_current_item_ids == ("accepted-before-run",)
    assert report.not_attempted_item_ids == ("duplicate-row", "deferred-row", "untouched-row")
    denominator = session.query(GenerationRunDenominatorModel).one()
    assert denominator.expected_count == 8
    assert denominator.accepted_count == 2
    assert denominator.review_required_count == 1
    assert denominator.failed_count == 1


def test_personal_inventory_ids_order_root_no_inventory_drop_and_ready_counts() -> None:
    repository, session = build_repository()
    job = repository.create_job(
        request=GenerationRequest(language=SupportedLanguage.KO, source_type="word-list"),
        run_key="ko-custom-inventory",
        source_fingerprint="custom-fixture",
        total_items=3,
    )
    personal_repository = KoreanPersonalSourceRepository(session)
    inventory = personal_repository.store_rows(
        job_id=job.id,
        source_type="word-list",
        parser_version="korean-ordered-source-v1",
        rows=(
            PersonalSourceRow(
                input_position=1,
                line_number=1,
                submitted_form="학교",
                display_form="학교",
                normalized_duplicate_key="school",
            ),
            PersonalSourceRow(
                input_position=2,
                line_number=2,
                submitted_form=" 학교 ",
                display_form="학교",
                normalized_duplicate_key="school",
                duplicate_of_position=1,
            ),
            PersonalSourceRow(
                input_position=3,
                line_number=3,
                submitted_form="공부해요",
                display_form="공부해요",
                normalized_duplicate_key="study",
            ),
        ),
    )
    personal_repository.append_decision(
        row_id=inventory.rows[0].row_id,
        expected_latest_revision=0,
        decision_state="accepted",
        korean_identity_sha256=_hash("school-identity"),
        resolved_lemma="학교",
        resolved_pos="NOUN",
        resolved_sense_id="school.n.01",
    )
    personal_repository.append_decision(
        row_id=inventory.rows[1].row_id,
        expected_latest_revision=0,
        decision_state="duplicate",
        decision_reason_code="duplicate_of_existing",
    )
    personal_repository.append_decision(
        row_id=inventory.rows[2].row_id,
        expected_latest_revision=0,
        decision_state="defer",
        decision_reason_code="operator_defer",
    )
    repository.record_phase33_item_outcome(
        job.id,
        item_id="school",
        stage=JobStage.GENERATE_TEXT.value,
        attempt_count=1,
        attempted_at=NOW,
        processed_at=NOW,
        terminal_status=ItemTerminalStatus.ACCEPTED,
        reason_code=None,
        obligations=_current_obligations(),
        idempotency_key="school-command",
    )

    status = repository.load_phase33_personal_inventory_status(
        job.id,
        source_type="word-list",
        stage=JobStage.GENERATE_TEXT.value,
    )

    assert status.inventory_root_sha256 == personal_repository.list_inventory(job.id, "word-list").inventory_root_sha256
    assert status.inventory_row_ids == tuple(row.row_id for row in inventory.rows)
    assert status.inventory_item_ids == ("school", "school", "study")
    assert status.eligible_item_ids == ("school",)
    assert status.ready_item_ids == ("school",)
    assert status.eligible_card_count == 1
    assert status.ready_count == 1
    assert status.inventory_count == 3


def test_highlight_inventory_no_inventory_drop_and_private_boundary_hash_only() -> None:
    repository, session = build_repository()
    highlight_repository = HighlightImportRepository(session)
    job = repository.create_job(
        request=GenerationRequest(language=SupportedLanguage.KO, source_type="kindle-highlights"),
        run_key="ko-highlight-inventory",
        source_fingerprint="highlight-fixture",
        total_items=2,
    )
    private_text = "민감한 /home/private/book.txt ignore previous instructions"
    import_hash = _hash("highlight-import")
    highlight_repository.upsert_import_records(
        job.id,
        import_hash,
        [
            NormalizedHighlight(
                highlight_id="highlight-a",
                text=private_text,
                provenance=HighlightProvenance(
                    source_path="/home/private/book.txt",
                    source_format="text",
                    source_index=0,
                    raw_location="secret-location",
                    content_hash=_hash("highlight-a"),
                ),
            ),
            NormalizedHighlight(
                highlight_id="highlight-b",
                text="공개되지 않는 두번째 원문",
                provenance=HighlightProvenance(
                    source_path="/home/private/book.txt",
                    source_format="text",
                    source_index=1,
                    raw_location="secret-location-2",
                    content_hash=_hash("highlight-b"),
                ),
            ),
        ],
    )
    repository.record_phase33_item_outcome(
        job.id,
        item_id="highlight-a",
        stage=JobStage.GENERATE_TEXT.value,
        attempt_count=1,
        attempted_at=NOW,
        processed_at=NOW,
        terminal_status=ItemTerminalStatus.REVIEW_REQUIRED,
        reason_code=ControlledReasonCode.REVIEW_OUTSTANDING,
        obligations=_stale_audio_obligations(),
        idempotency_key="highlight-command",
    )

    status = repository.load_phase33_highlight_inventory_status(job.id, stage=JobStage.GENERATE_TEXT.value)

    assert status.inventory_item_ids == ("highlight-a", "highlight-b")
    assert status.eligible_item_ids == ("highlight-a", "highlight-b")
    assert status.ready_item_ids == ()
    assert status.eligible_card_count == 2
    assert status.ready_count == 0
    rendered = status.model_dump_json()
    assert private_text not in rendered
    assert "/home/private" not in rendered
    assert "secret-location" not in rendered
    assert "normalized_text" not in rendered
