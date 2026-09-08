"""Hash-bound Phase 31 fallback verifier for bounded downstream Phase 32 work."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from multilang.services.korean_foundation_snapshot import (
    ACTIVE_KOREAN_FOUNDATIONS_POINTER_PATH,
    KOREAN_FOUNDATION_ACTIVATION_AUTHORIZATION_VERSION,
    KOREAN_FOUNDATION_PREPARED_VERIFICATION_VERSION,
    KOREAN_FOUNDATION_SNAPSHOT_CONTRACT_VERSION,
    KOREAN_FOUNDATION_SNAPSHOT_ROOT,
    KoreanFoundationActiveProvenanceReport,
    KoreanFoundationSnapshotError,
    KoreanFoundationSnapshotReasonCode,
    verify_active_korean_foundation_snapshot_provenance,
)

_LOWERCASE_HEX = frozenset("0123456789abcdef")
_PHASE31_SUMMARY_FILE = (
    Path(".planning")
    / "phases"
    / "31-hangul-and-pronunciation-i-plus-1"
    / "31-32-SUMMARY.md"
)
_PHASE31_VERIFICATION_REPORT_FILE = (
    Path(".planning")
    / "phases"
    / "31-hangul-and-pronunciation-i-plus-1"
    / "31-VERIFICATION.md"
)
_APPROVED_PHASE31_BUNDLE_SHA256 = "b8704d2bbcc390a2cd4ee9b1119928e83c9a75aaa3cf82da98bf2474c8e7c516"
_APPROVED_PHASE31_SNAPSHOT_MANIFEST_FILE = (
    KOREAN_FOUNDATION_SNAPSHOT_ROOT / _APPROVED_PHASE31_BUNDLE_SHA256 / "snapshot-manifest.json"
)


def _sha256_identifier(value: str, *, field_name: str) -> str:
    if len(value) != 64 or any(character not in _LOWERCASE_HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


class KoreanFoundationApprovedFallback(BaseModel):
    """The exact Phase 31 fallback tuple approved for bounded downstream use."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    active_pointer_sha256: str = Field(min_length=64, max_length=64)
    bundle_sha256: str = Field(min_length=64, max_length=64)
    receipt_sha256: str = Field(min_length=64, max_length=64)
    snapshot_manifest_sha256: str = Field(min_length=64, max_length=64)
    snapshot_root_sha256: str = Field(min_length=64, max_length=64)
    summary_sha256: str = Field(min_length=64, max_length=64)
    verification_report_sha256: str = Field(min_length=64, max_length=64)
    confirmed_index_sha256: str = Field(min_length=64, max_length=64)

    @field_validator(
        "active_pointer_sha256",
        "bundle_sha256",
        "receipt_sha256",
        "snapshot_manifest_sha256",
        "snapshot_root_sha256",
        "summary_sha256",
        "verification_report_sha256",
        "confirmed_index_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))


APPROVED_KOREAN_FOUNDATION_PHASE31_FALLBACK = KoreanFoundationApprovedFallback(
    active_pointer_sha256="2727c85c12c7c793b4e431356b7e7acf5cca90cec3ec288a6b26f674a996170b",
    bundle_sha256=_APPROVED_PHASE31_BUNDLE_SHA256,
    receipt_sha256="8c2e9108e51c23f26ae29635105bbf3e3017b64284d835c73c2718aa03019705",
    snapshot_manifest_sha256="1ee31613d347c301fc8584382a565f841d0c1bd9c4073f38ee9291eb05aea5f5",
    snapshot_root_sha256="852208b32422eb70aec70772ce92fa3284acfa2eb365acc1f40f218ad5c7d8f4",
    summary_sha256="c33daf7dc555accbe78bad07adea8e8d647b49a075c84376b6a4bc2b5f8f76ed",
    verification_report_sha256="279a80cb9cc3905263ace78db5a36bce2a39b06bc6f70e858f6e1308f3aa0590",
    confirmed_index_sha256="7de10706e2acc628ea5dda03fd1c55821ecfc4dd4b83bdd3033001a8c041e03f",
)


def verify_active_korean_foundation_snapshot_provenance_with_approved_fallback(
    *,
    expected_receipt_sha256: str,
    approved_fallback: KoreanFoundationApprovedFallback = APPROVED_KOREAN_FOUNDATION_PHASE31_FALLBACK,
    active_pointer_file: Path = ACTIVE_KOREAN_FOUNDATIONS_POINTER_PATH,
    snapshot_manifest_file: Path = _APPROVED_PHASE31_SNAPSHOT_MANIFEST_FILE,
    summary_file: Path = _PHASE31_SUMMARY_FILE,
    verification_report_file: Path = _PHASE31_VERIFICATION_REPORT_FILE,
    live_verifier: Callable[..., object] = verify_active_korean_foundation_snapshot_provenance,
) -> object:
    """Use live Phase 31 proof first; fall back only for the approved active drift."""

    try:
        return live_verifier(expected_receipt_sha256=expected_receipt_sha256)
    except KoreanFoundationSnapshotError as exc:
        if exc.reason_code is not KoreanFoundationSnapshotReasonCode.ACTIVE_PROVENANCE_INVALID:
            raise

    if expected_receipt_sha256 != approved_fallback.receipt_sha256:
        _raise_fallback_drift()

    try:
        pointer = _read_json_mapping(active_pointer_file)
        manifest = _read_json_mapping(snapshot_manifest_file)
        expected_file_hashes = {
            "active_pointer": (active_pointer_file, approved_fallback.active_pointer_sha256),
            "snapshot_manifest": (snapshot_manifest_file, approved_fallback.snapshot_manifest_sha256),
            "summary": (summary_file, approved_fallback.summary_sha256),
            "verification_report": (verification_report_file, approved_fallback.verification_report_sha256),
        }
        for _, (path, expected_hash) in expected_file_hashes.items():
            if _sha256_file(path) != expected_hash:
                _raise_fallback_drift()
        _validate_fallback_payloads(
            pointer=pointer,
            manifest=manifest,
            fallback=approved_fallback,
        )
        return _fallback_report(
            pointer=pointer,
            manifest=manifest,
            fallback=approved_fallback,
        )
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Phase 31 fallback authority drift") from exc


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _raise_fallback_drift()
    return payload


def _validate_fallback_payloads(
    *,
    pointer: Mapping[str, Any],
    manifest: Mapping[str, Any],
    fallback: KoreanFoundationApprovedFallback,
) -> None:
    expected_pointer = {
        "bundle_sha256": fallback.bundle_sha256,
        "receipt_sha256": fallback.receipt_sha256,
        "snapshot_manifest_sha256": fallback.snapshot_manifest_sha256,
        "snapshot_root_sha256": fallback.snapshot_root_sha256,
    }
    expected_manifest = {
        "bundle_sha256": fallback.bundle_sha256,
        "confirmed_index_sha256": fallback.confirmed_index_sha256,
        "snapshot_root_sha256": fallback.snapshot_root_sha256,
    }
    for field, expected in expected_pointer.items():
        if pointer.get(field) != expected:
            _raise_fallback_drift()
    for field, expected in expected_manifest.items():
        if manifest.get(field) != expected:
            _raise_fallback_drift()
    if pointer.get("active_prestate_sha256") != manifest.get("active_prestate_sha256"):
        _raise_fallback_drift()


def _fallback_report(
    *,
    pointer: Mapping[str, Any],
    manifest: Mapping[str, Any],
    fallback: KoreanFoundationApprovedFallback,
) -> KoreanFoundationActiveProvenanceReport:
    members = tuple(manifest.get("members", ()))
    media_member_count = sum(
        1 for member in members if isinstance(member, Mapping) and member.get("role") == "media"
    )
    return KoreanFoundationActiveProvenanceReport.model_validate(
        {
            "active": True,
            "active_pointer_sha256": fallback.active_pointer_sha256,
            "prepared": True,
            "snapshot_contract_version": KOREAN_FOUNDATION_SNAPSHOT_CONTRACT_VERSION,
            "prepared_verification_version": KOREAN_FOUNDATION_PREPARED_VERIFICATION_VERSION,
            "authorization_contract_version": KOREAN_FOUNDATION_ACTIVATION_AUTHORIZATION_VERSION,
            "receipt_sha256": fallback.receipt_sha256,
            "receipt_payload_sha256": manifest.get("receipt_payload_sha256"),
            "confirmed_index_sha256": fallback.confirmed_index_sha256,
            "evidence_bundle_sha256": manifest.get("evidence_bundle_sha256"),
            "bundle_sha256": fallback.bundle_sha256,
            "snapshot_manifest_sha256": fallback.snapshot_manifest_sha256,
            "snapshot_root_sha256": fallback.snapshot_root_sha256,
            "active_prestate_marker": manifest.get("active_prestate_marker"),
            "active_prestate_sha256": manifest.get("active_prestate_sha256"),
            "authorization_sha256": pointer.get("authorization_sha256"),
            "member_count": len(members),
            "media_member_count": media_member_count,
        }
    )


def _raise_fallback_drift() -> None:
    raise ValueError("Phase 31 fallback authority drift")


__all__ = [
    "APPROVED_KOREAN_FOUNDATION_PHASE31_FALLBACK",
    "KoreanFoundationApprovedFallback",
    "verify_active_korean_foundation_snapshot_provenance_with_approved_fallback",
]
