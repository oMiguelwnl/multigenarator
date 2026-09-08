"""Tests for the bounded Phase 31 fallback verifier used by Phase 32."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from multilang.domain.korean import raw_bytes_sha256
from multilang.services.korean_foundation_snapshot import (
    KoreanFoundationActiveProvenanceReport,
    KoreanFoundationSnapshotError,
    KoreanFoundationSnapshotReasonCode,
)
from multilang.services.korean_foundation_snapshot_fallback import (
    KoreanFoundationApprovedFallback,
    verify_active_korean_foundation_snapshot_provenance_with_approved_fallback,
)


def _hash(seed: str) -> str:
    return raw_bytes_sha256(seed.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    return raw_bytes_sha256(path.read_bytes())


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_text(path: Path, payload: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    return path


def _fallback_fixture(tmp_path: Path) -> tuple[KoreanFoundationApprovedFallback, Path, Path, Path, Path]:
    manifest = _write_json(
        tmp_path / "snapshot-manifest.json",
        {
            "active_prestate_marker": "absent",
            "active_prestate_sha256": _hash("active-prestate"),
            "bundle_sha256": _hash("bundle"),
            "confirmed_index_sha256": _hash("index"),
            "evidence_bundle_sha256": _hash("evidence-bundle"),
            "members": [
                {"relpath": "content/example.json", "role": "content", "sha256": _hash("content"), "size_bytes": 2},
                {"relpath": "media/example.wav", "role": "media", "sha256": _hash("media"), "size_bytes": 2},
            ],
            "receipt_payload_sha256": _hash("receipt-payload"),
            "snapshot_root_sha256": _hash("snapshot-root"),
        },
    )
    pointer = _write_json(
        tmp_path / "active-foundations.json",
        {
            "active_prestate_sha256": _hash("active-prestate"),
            "authorization_sha256": _hash("authorization"),
            "bundle_sha256": _hash("bundle"),
            "receipt_sha256": _hash("receipt"),
            "snapshot_manifest_sha256": _sha256_file(manifest),
            "snapshot_root_sha256": _hash("snapshot-root"),
        },
    )
    summary = _write_text(tmp_path / "31-32-SUMMARY.md", "receipt-bound summary\n")
    verification = _write_text(tmp_path / "31-VERIFICATION.md", "receipt-bound verification\n")
    fallback = KoreanFoundationApprovedFallback(
        active_pointer_sha256=_sha256_file(pointer),
        bundle_sha256=_hash("bundle"),
        receipt_sha256=_hash("receipt"),
        snapshot_manifest_sha256=_sha256_file(manifest),
        snapshot_root_sha256=_hash("snapshot-root"),
        summary_sha256=_sha256_file(summary),
        verification_report_sha256=_sha256_file(verification),
        confirmed_index_sha256=_hash("index"),
    )
    return fallback, pointer, manifest, summary, verification


def test_phase31_fallback_prefers_live_verifier_without_reading_fallback_files(tmp_path: Path) -> None:
    live_report = SimpleNamespace(receipt_sha256=_hash("live"))

    result = verify_active_korean_foundation_snapshot_provenance_with_approved_fallback(
        expected_receipt_sha256=_hash("live"),
        approved_fallback=KoreanFoundationApprovedFallback(
            active_pointer_sha256=_hash("pointer"),
            bundle_sha256=_hash("bundle"),
            receipt_sha256=_hash("receipt"),
            snapshot_manifest_sha256=_hash("manifest"),
            snapshot_root_sha256=_hash("root"),
            summary_sha256=_hash("summary"),
            verification_report_sha256=_hash("verification"),
            confirmed_index_sha256=_hash("index"),
        ),
        active_pointer_file=tmp_path / "missing-pointer.json",
        snapshot_manifest_file=tmp_path / "missing-manifest.json",
        summary_file=tmp_path / "missing-summary.md",
        verification_report_file=tmp_path / "missing-verification.md",
        live_verifier=lambda **_: live_report,
    )

    assert result is live_report


def test_phase31_fallback_accepts_only_known_active_provenance_drift(tmp_path: Path) -> None:
    fallback, pointer, manifest, summary, verification = _fallback_fixture(tmp_path)

    def active_drift(**_: object) -> object:
        raise KoreanFoundationSnapshotError(KoreanFoundationSnapshotReasonCode.ACTIVE_PROVENANCE_INVALID)

    result = verify_active_korean_foundation_snapshot_provenance_with_approved_fallback(
        expected_receipt_sha256=fallback.receipt_sha256,
        approved_fallback=fallback,
        active_pointer_file=pointer,
        snapshot_manifest_file=manifest,
        summary_file=summary,
        verification_report_file=verification,
        live_verifier=active_drift,
    )

    assert isinstance(result, KoreanFoundationActiveProvenanceReport)
    assert result.receipt_sha256 == fallback.receipt_sha256
    assert result.bundle_sha256 == fallback.bundle_sha256
    assert result.snapshot_manifest_sha256 == fallback.snapshot_manifest_sha256
    assert result.snapshot_root_sha256 == fallback.snapshot_root_sha256
    assert result.active_pointer_sha256 == fallback.active_pointer_sha256
    assert result.confirmed_index_sha256 == fallback.confirmed_index_sha256


def test_phase31_fallback_rejects_other_live_verifier_errors(tmp_path: Path) -> None:
    fallback, pointer, manifest, summary, verification = _fallback_fixture(tmp_path)

    def receipt_mismatch(**_: object) -> object:
        raise KoreanFoundationSnapshotError(KoreanFoundationSnapshotReasonCode.RECEIPT_HASH_MISMATCH)

    with pytest.raises(KoreanFoundationSnapshotError) as exc_info:
        verify_active_korean_foundation_snapshot_provenance_with_approved_fallback(
            expected_receipt_sha256=fallback.receipt_sha256,
            approved_fallback=fallback,
            active_pointer_file=pointer,
            snapshot_manifest_file=manifest,
            summary_file=summary,
            verification_report_file=verification,
            live_verifier=receipt_mismatch,
        )

    assert exc_info.value.reason_code is KoreanFoundationSnapshotReasonCode.RECEIPT_HASH_MISMATCH


def test_phase31_fallback_rejects_hash_drift_without_paths(tmp_path: Path) -> None:
    fallback, pointer, manifest, summary, verification = _fallback_fixture(tmp_path)
    summary.write_text("drifted summary\n", encoding="utf-8")

    def active_drift(**_: object) -> object:
        raise KoreanFoundationSnapshotError(KoreanFoundationSnapshotReasonCode.ACTIVE_PROVENANCE_INVALID)

    with pytest.raises(ValueError) as exc_info:
        verify_active_korean_foundation_snapshot_provenance_with_approved_fallback(
            expected_receipt_sha256=fallback.receipt_sha256,
            approved_fallback=fallback,
            active_pointer_file=pointer,
            snapshot_manifest_file=manifest,
            summary_file=summary,
            verification_report_file=verification,
            live_verifier=active_drift,
        )

    assert "Phase 31 fallback authority drift" in str(exc_info.value)
    assert str(tmp_path) not in str(exc_info.value)
