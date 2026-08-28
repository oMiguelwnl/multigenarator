"""Repository tests for persisted job orchestration state."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.domain.korean import KoreanFrequencyJobAuthority, raw_bytes_sha256
from multilang.domain.jobs import GenerationRequest, JobStage, JobStatus, SupportedLanguage
from multilang.repositories.job_repository import JobRepository
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
