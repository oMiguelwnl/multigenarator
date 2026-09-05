"""Read-only Korean audio pilot evidence reconciliation tests."""

from __future__ import annotations

from hashlib import sha256

import pytest

from multilang.domain.audio import AudioAssetKind
from multilang.services.korean_audio import build_korean_audio_asset, build_korean_tts_input
from multilang.services.korean_audio import KoreanAzureCatalogVoice, KoreanVoiceProfile
from multilang.services.korean_audio_pilot_evidence import (
    KoreanAudioPilotAuthority,
    validate_korean_audio_pilot_result,
)


def _hash(seed: str) -> str:
    return sha256(seed.encode("utf-8")).hexdigest()


def _authority(**overrides: str) -> KoreanAudioPilotAuthority:
    payload = {
        "job_id": "job-ko",
        "phase31_validation_receipt_sha256": _hash("phase31-receipt"),
        "phase31_snapshot_manifest_sha256": _hash("phase31-manifest"),
        "phase31_snapshot_root_sha256": _hash("phase31-root"),
        "binding_receipt_sha256": _hash("binding"),
        "catalog_receipt_sha256": _hash("catalog-receipt"),
        "profile_authority_sha256": _hash("profile-authority"),
        "budget_sha256": _hash("budget"),
        "retry_policy_sha256": _hash("retry-policy"),
    }
    payload.update(overrides)
    return KoreanAudioPilotAuthority(**payload)


def _profile() -> KoreanVoiceProfile:
    return KoreanVoiceProfile.from_catalog_voice(
        KoreanAzureCatalogVoice(
            short_name="ko-KR-SunHiNeural",
            locale="ko-KR",
            region="koreacentral",
            status="available",
            voice_type="Neural",
            provider_sdk_version="1.49.1",
        ),
        catalog_receipt_sha256=_hash("catalog-receipt"),
        profile_authority_sha256=_hash("profile-authority"),
    )


def _asset(kind: AudioAssetKind, text: str):
    profile = _profile()
    normalized = build_korean_tts_input(text, asset_kind=kind, profile=profile)
    return build_korean_audio_asset(
        job_id="job-ko",
        item_key="item-1",
        asset_kind=kind,
        normalized_input=normalized,
        profile=profile,
        storage_path=f"audio/{kind.value}.mp3",
        media_bytes=f"{kind.value}-bytes".encode("utf-8"),
        duration_ms=100,
        fallback_used=False,
    )


def test_audio_pilot_reconcile_request_bytes_budget_zero_fallback_and_invariance() -> None:
    authority = _authority()
    calls: list[str] = []

    def verifier(*, expected_receipt_sha256: str) -> object:
        calls.append("verify_phase31")
        assert expected_receipt_sha256 == authority.phase31_validation_receipt_sha256
        return type(
            "Report",
            (),
            {
                "receipt_sha256": authority.phase31_validation_receipt_sha256,
                "snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
                "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
            },
        )()

    evidence = validate_korean_audio_pilot_result(
        authority=authority,
        assets=(_asset(AudioAssetKind.WORD, "학교"), _asset(AudioAssetKind.SENTENCE, "저는 학교에 가요.")),
        expected_item_count=1,
        protected_pre_sha256=_hash("protected"),
        protected_post_sha256=_hash("protected"),
        phase31_verifier=verifier,
    )

    assert calls == ["verify_phase31"]
    assert evidence.job_id == "job-ko"
    assert evidence.word_asset_count == 1
    assert evidence.sentence_asset_count == 1
    assert evidence.fallback_count == 0
    assert evidence.budget_sha256 == authority.budget_sha256
    assert evidence.grants_heard_approval is False


def test_audio_pilot_blocks_phase31_fallback_or_mutation_drift() -> None:
    authority = _authority()
    word = _asset(AudioAssetKind.WORD, "학교")
    sentence = _asset(AudioAssetKind.SENTENCE, "저는 학교에 가요.")

    def verifier(*, expected_receipt_sha256: str) -> object:
        return type(
            "Report",
            (),
            {
                "receipt_sha256": expected_receipt_sha256,
                "snapshot_manifest_sha256": "0" * 64,
                "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
            },
        )()

    with pytest.raises(ValueError, match="Phase 31 active authority drift"):
        validate_korean_audio_pilot_result(
            authority=authority,
            assets=(word, sentence),
            expected_item_count=1,
            protected_pre_sha256=_hash("protected"),
            protected_post_sha256=_hash("protected"),
            phase31_verifier=verifier,
        )

    with pytest.raises(ValueError, match="protected audio evidence drift"):
        validate_korean_audio_pilot_result(
            authority=authority,
            assets=(word, sentence),
            expected_item_count=1,
            protected_pre_sha256=_hash("before"),
            protected_post_sha256=_hash("after"),
            phase31_verifier=lambda **_: type(
                "Report",
                (),
                {
                    "receipt_sha256": authority.phase31_validation_receipt_sha256,
                    "snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
                    "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
                },
            )(),
        )
