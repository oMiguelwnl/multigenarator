"""Read-only Korean audio pilot evidence reconciliation."""

from __future__ import annotations

from hashlib import sha256
import json

from pydantic import BaseModel, ConfigDict, Field, field_validator

from multilang.domain.audio import AudioAssetKind, AudioAssetRecord, AudioSynthesisStatus
from multilang.domain.korean import KOREAN_PROVIDER_LOCALE
from multilang.services.korean_foundation_snapshot import verify_active_korean_foundation_snapshot_provenance


_HEX = frozenset("0123456789abcdef")


def _sha256_identifier(value: str, *, field_name: str) -> str:
    if len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _canonical_sha256(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class KoreanAudioPilotAuthority(_FrozenModel):
    job_id: str = Field(min_length=1, max_length=128)
    phase31_validation_receipt_sha256: str = Field(min_length=64, max_length=64)
    phase31_snapshot_manifest_sha256: str = Field(min_length=64, max_length=64)
    phase31_snapshot_root_sha256: str = Field(min_length=64, max_length=64)
    binding_receipt_sha256: str = Field(min_length=64, max_length=64)
    catalog_receipt_sha256: str = Field(min_length=64, max_length=64)
    profile_authority_sha256: str = Field(min_length=64, max_length=64)
    budget_sha256: str = Field(min_length=64, max_length=64)
    retry_policy_sha256: str = Field(min_length=64, max_length=64)

    @field_validator(
        "phase31_validation_receipt_sha256",
        "phase31_snapshot_manifest_sha256",
        "phase31_snapshot_root_sha256",
        "binding_receipt_sha256",
        "catalog_receipt_sha256",
        "profile_authority_sha256",
        "budget_sha256",
        "retry_policy_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))


class KoreanAudioPilotEvidence(_FrozenModel):
    job_id: str = Field(min_length=1, max_length=128)
    evidence_sha256: str = Field(min_length=64, max_length=64)
    word_asset_count: int = Field(ge=0)
    sentence_asset_count: int = Field(ge=0)
    fallback_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    missing_request_count: int = Field(ge=0)
    missing_artifact_count: int = Field(ge=0)
    budget_sha256: str = Field(min_length=64, max_length=64)
    retry_policy_sha256: str = Field(min_length=64, max_length=64)
    grants_heard_approval: bool = False


def validate_korean_audio_pilot_result(
    *,
    authority: KoreanAudioPilotAuthority,
    assets: tuple[AudioAssetRecord, ...],
    expected_item_count: int,
    protected_pre_sha256: str,
    protected_post_sha256: str,
    phase31_verifier=verify_active_korean_foundation_snapshot_provenance,
) -> KoreanAudioPilotEvidence:
    """Recompute pilot facts without mutating rows or granting approval."""

    _sha256_identifier(protected_pre_sha256, field_name="protected_pre_sha256")
    _sha256_identifier(protected_post_sha256, field_name="protected_post_sha256")
    if protected_pre_sha256 != protected_post_sha256:
        raise ValueError("protected audio evidence drift")

    report = phase31_verifier(
        expected_receipt_sha256=authority.phase31_validation_receipt_sha256,
    )
    expected = {
        "receipt_sha256": authority.phase31_validation_receipt_sha256,
        "snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
        "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
    }
    for field, value in expected.items():
        if getattr(report, field, None) != value:
            raise ValueError("Phase 31 active authority drift")

    word_assets = [asset for asset in assets if asset.asset_kind is AudioAssetKind.WORD]
    sentence_assets = [asset for asset in assets if asset.asset_kind is AudioAssetKind.SENTENCE]
    fallback_count = sum(1 for asset in assets if asset.provenance.fallback_used)
    failed_count = sum(1 for asset in assets if asset.provenance.status is not AudioSynthesisStatus.SYNTHESIZED)
    missing_request_count = sum(1 for asset in assets if asset.provenance.synthesis_request_sha256 is None)
    missing_artifact_count = sum(1 for asset in assets if asset.provenance.artifact_sha256 is None or asset.provenance.byte_size <= 0)
    if any(asset.job_id != authority.job_id for asset in assets):
        raise ValueError("Korean audio pilot evidence contains wrong job")
    if fallback_count:
        raise ValueError("Korean audio pilot evidence contains fallback audio")
    if failed_count or missing_request_count or missing_artifact_count:
        raise ValueError("Korean audio pilot evidence is missing exact request or bytes")
    if len(word_assets) != expected_item_count or len(sentence_assets) != expected_item_count:
        raise ValueError("Korean audio pilot evidence denominator mismatch")
    if any(asset.provenance.locale != KOREAN_PROVIDER_LOCALE for asset in assets):
        raise ValueError("Korean audio pilot evidence contains wrong locale")
    if any(asset.provenance.catalog_receipt_sha256 != authority.catalog_receipt_sha256 for asset in assets):
        raise ValueError("Korean audio pilot evidence catalog drift")

    payload = {
        "job_id": authority.job_id,
        "assets": [
            {
                "item_key": asset.item_key,
                "asset_kind": asset.asset_kind.value,
                "request": asset.provenance.synthesis_request_sha256,
                "artifact": asset.provenance.artifact_sha256,
            }
            for asset in sorted(assets, key=lambda item: (item.item_key, item.asset_kind.value))
        ],
        "budget_sha256": authority.budget_sha256,
        "retry_policy_sha256": authority.retry_policy_sha256,
    }
    return KoreanAudioPilotEvidence(
        job_id=authority.job_id,
        evidence_sha256=_canonical_sha256(payload),
        word_asset_count=len(word_assets),
        sentence_asset_count=len(sentence_assets),
        fallback_count=fallback_count,
        failed_count=failed_count,
        missing_request_count=missing_request_count,
        missing_artifact_count=missing_artifact_count,
        budget_sha256=authority.budget_sha256,
        retry_policy_sha256=authority.retry_policy_sha256,
        grants_heard_approval=False,
    )


__all__ = [
    "KoreanAudioPilotAuthority",
    "KoreanAudioPilotEvidence",
    "validate_korean_audio_pilot_result",
]
