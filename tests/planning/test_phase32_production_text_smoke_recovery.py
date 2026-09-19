from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

HELPER_PATH = Path(
    ".planning/phases/32-frequency-portuguese-text-and-audio/tools/production_text_smoke_20.py"
)


def _load_helper():
    spec = importlib.util.spec_from_file_location("phase32_production_text_smoke", HELPER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def helper():
    return _load_helper()


def test_build_runtime_returns_constructed_service_with_forbidden_audio_adapter(helper, monkeypatch):
    settings = object()
    runtime = object()
    policy = helper.load_policy()
    authority = helper.build_authority()
    captured = {}

    monkeypatch.setattr(helper, "build_settings", lambda values: settings)

    def build_service(**kwargs):
        captured.update(kwargs)
        return runtime

    monkeypatch.setattr(helper, "build_korean_frequency_text_runtime_service", build_service)

    assert helper.build_runtime({}, policy, authority) is runtime
    assert captured["settings"] is settings
    assert captured["korean_provider_policy"] is policy
    runtime_authority = captured["runtime_authority"]
    assert runtime_authority.job_id == helper.JOB_ID
    assert runtime_authority.bundle_root == helper.BUNDLE_ROOT
    assert runtime_authority.binding_receipt_sha256 == helper.SOURCE_REVIEW_AGGREGATE_SHA256
    assert runtime_authority.authority is authority
    assert captured["phase31_provenance_verifier"] is (
        helper.verify_active_korean_foundation_snapshot_provenance_with_approved_fallback
    )
    builder = captured["runtime_builder"]
    assert builder.func is helper.build_runtime_service
    with pytest.raises(helper.ControlledBlock, match="audio_invocation_forbidden"):
        builder.keywords["audio_adapter"].synthesize()


def _hash(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _row(
    *,
    row_id: str,
    attempt: int,
    status: str,
    error_code: str | None = None,
    item_key: str = "level-1-rank-0001",
):
    return SimpleNamespace(
        id=row_id,
        job_id="phase32-prod-text-smoke-20",
        item_key=item_key,
        operation="definition",
        provider="litellm",
        model="gpt-4.1-mini",
        attempt=attempt,
        status=status,
        error_code=error_code,
        route_policy_sha256=_hash("route"),
        budget_snapshot_sha256=_hash("budget"),
        cache_key_sha256=_hash("cache"),
        response_schema_sha256=_hash("schema"),
        created_at=datetime.now(UTC),
    )


def test_protected_artifacts_use_anchored_hashes_and_reject_changed_bytes(helper, tmp_path, monkeypatch):
    paths = {}
    expected = {}
    for name in ("authorization", "preflight", "result", "summary"):
        path = tmp_path / name
        path.write_bytes(name.encode("utf-8"))
        paths[name] = path
        expected[name] = helper.sha256_bytes(path.read_bytes())
    monkeypatch.setattr(helper, "PROTECTED_PLAN_32_54_PATHS", paths)
    monkeypatch.setattr(helper, "PROTECTED_PLAN_32_54_SHA256", expected)

    assert helper.validate_protected_plan_32_54_artifacts() == expected
    paths["result"].write_bytes(b"changed")
    with pytest.raises(helper.ControlledBlock, match="protected_plan_32_54_result_drift"):
        helper.validate_protected_plan_32_54_artifacts()


def test_recovery_authority_is_sidecar_only_and_preserves_original_job_authority(helper, tmp_path, monkeypatch):
    original_result = tmp_path / "prior-result.json"
    original_result.write_text("{}\n", encoding="utf-8")
    sidecar = tmp_path / "authorization.md"
    sidecar.write_text(
        "```json\n"
        + json.dumps(
            {
                "authority_kind": "production-text-smoke-recovery",
                "decision": "Autorizar retry",
                "job_id": helper.JOB_ID,
                "authorized_ranks": list(range(1, 21)),
                "original_result_sha256": helper.PROTECTED_PLAN_32_54_SHA256["result"],
                "recovery_invocations": 1,
                "max_attempts_per_operation": 2,
                "unit_1_max_items": 10,
                "unit_2_gate_text_records": 10,
                "missing_only": True,
                "audio": False,
                "fallback": "none",
                "full_run_authorized": False,
                "terminal_state": "wait_for_user_before_3000_item_execution",
            }
        )
        + "\n```\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(helper, "RECOVERY_AUTHORIZATION_PATH", sidecar)

    payload = helper.recovery_authorization_payload()
    assert payload["recovery_invocations"] == 1
    assert payload["audio"] is False
    assert helper.build_authority().pilot_authority_sha256 == helper.sha256_bytes(
        helper.AUTHORIZATION_PATH.read_bytes()
    )


def test_historical_shape_and_cooldown_fail_closed(helper):
    now = datetime.now(UTC)
    rows = [
        _row(row_id="one", attempt=1, status="failure", error_code="rate_limited"),
        _row(row_id="two", attempt=2, status="failure", error_code="rate_limited"),
        _row(row_id="outer", attempt=1, status="failure", error_code="ProviderRetryError"),
    ]
    for row in rows:
        row.created_at = now - timedelta(seconds=61)
    snapshot = helper.validate_historical_telemetry(rows, now=now)
    assert snapshot["external_attempt_count"] == 2
    assert snapshot["aggregate_failure_count"] == 1
    assert snapshot["cooldown_satisfied"] is True

    rows[-1].created_at = now - timedelta(seconds=59)
    with pytest.raises(helper.ControlledBlock, match="provider_cooldown_not_satisfied"):
        helper.validate_historical_telemetry(rows, now=now)


@pytest.mark.parametrize("attempts", [[2], [1, 1], [1, 2, 3]])
def test_invocation_attempt_ordinals_must_be_unique_prefix_and_at_most_two(helper, attempts):
    rows = [_row(row_id=f"row-{index}", attempt=value, status="failure", error_code="rate_limited") for index, value in enumerate(attempts)]
    with pytest.raises(helper.ControlledBlock):
        helper.classify_recovery_telemetry(rows, historical_row_ids=set())


def test_recovery_telemetry_accepts_success_retryable_refailure_and_lone_permanent_surrogate(helper):
    success = [_row(row_id="success", attempt=1, status="success")]
    assert helper.classify_recovery_telemetry(success, historical_row_ids=set())["external_attempt_count"] == 1

    retryable = [
        _row(row_id="retry-1", attempt=1, status="failure", error_code="rate_limited"),
        _row(row_id="retry-2", attempt=2, status="failure", error_code="rate_limited"),
        _row(row_id="aggregate", attempt=1, status="failure", error_code="ProviderRetryError"),
    ]
    report = helper.classify_recovery_telemetry(retryable, historical_row_ids=set())
    assert report["external_attempt_count"] == 2
    assert report["aggregate_row_count"] == 1

    permanent = [_row(row_id="quota", attempt=1, status="failure", error_code="quota_exceeded")]
    report = helper.classify_recovery_telemetry(permanent, historical_row_ids=set())
    assert report["external_attempt_count"] == 1
    assert report["non_retryable_surrogate_count"] == 1

    ambiguous = permanent + [_row(row_id="retry", attempt=1, status="failure", error_code="rate_limited")]
    with pytest.raises(helper.ControlledBlock, match="ambiguous_non_retryable_surrogate"):
        helper.classify_recovery_telemetry(ambiguous, historical_row_ids=set())


def test_recovery_telemetry_rejects_missing_hashes_aggregate_confusion_and_unexplained_rows(helper):
    missing = _row(row_id="missing", attempt=1, status="success")
    missing.cache_key_sha256 = None
    with pytest.raises(helper.ControlledBlock, match="recovery_telemetry_hash_missing"):
        helper.classify_recovery_telemetry([missing], historical_row_ids=set())

    outer = _row(row_id="outer", attempt=1, status="failure", error_code="ProviderRetryError")
    with pytest.raises(helper.ControlledBlock, match="ambiguous_aggregate_rows"):
        helper.classify_recovery_telemetry([outer], historical_row_ids=set())

    unknown = _row(row_id="unknown", attempt=1, status="failure", error_code="mystery")
    with pytest.raises(helper.ControlledBlock, match="unexplained_recovery_telemetry"):
        helper.classify_recovery_telemetry([unknown], historical_row_ids=set())


def test_one_shot_invocation_marker_is_created_exclusively(helper, tmp_path, monkeypatch):
    marker = tmp_path / "marker.json"
    monkeypatch.setattr(helper, "RECOVERY_INVOCATION_PATH", marker)
    payload = {"schema_version": "test", "status": "claimed"}
    helper.create_recovery_invocation_marker(payload)
    assert json.loads(marker.read_text(encoding="utf-8")) == payload
    assert marker.stat().st_mode & 0o777 == 0o600
    with pytest.raises(helper.ControlledBlock, match="recovery_invocation_already_claimed"):
        helper.create_recovery_invocation_marker(payload)


def test_result_validation_accepts_recovered_or_bounded_refailure_and_enforces_unit_two_gate(helper):
    common = {
        "job_id": helper.JOB_ID,
        "candidate_count": 20,
        "audio_asset_count": 0,
        "card_export_count": 0,
        "deck_export_count": 0,
        "azure_call_count": 0,
        "full_run_attempted": False,
        "invocation_marker_count": 1,
        "terminal_state": "wait_for_user_before_3000_item_execution",
    }
    recovered = {
        **common,
        "status": "recovered",
        "text_record_count": 20,
        "processed_items": 20,
        "units": [{"unit": 1, "processed_items": 10}, {"unit": 2, "processed_items": 10}],
    }
    assert helper.validate_recovery_result_envelope(recovered) == "recovered"

    failed = {
        **common,
        "status": "bounded_refailure",
        "text_record_count": 4,
        "processed_items": 4,
        "units": [],
        "unit_2_attempted": False,
    }
    assert helper.validate_recovery_result_envelope(failed) == "bounded_refailure"
    failed["unit_2_attempted"] = True
    with pytest.raises(helper.ControlledBlock, match="unit_2_gate_violated"):
        helper.validate_recovery_result_envelope(failed)


def test_recovery_log_scan_rejects_leaks(helper):
    with pytest.raises(helper.ControlledBlock):
        helper.scan_text("prompt=unsafe", secrets=set(), runtime_log=True)
    with pytest.raises(helper.ControlledBlock):
        helper.scan_text("\uD55C\uAE00", secrets=set(), runtime_log=True)
