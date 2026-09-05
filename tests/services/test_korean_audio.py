"""Tests for Korean catalog, SSML, exact audio identity, and reuse gates."""

from __future__ import annotations

from hashlib import sha256

import pytest

from multilang.domain.audio import (
    AudioAssetKind,
    AudioFormat,
    AudioProvider,
    AudioReviewStatus,
    AudioSynthesisStatus,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.services.audio_voice_registry import VoiceSelectionError, select_voice
from multilang.services.korean_audio import (
    KoreanAudioAuthority,
    KoreanAzureCatalogVoice,
    KoreanVoiceProfile,
    build_korean_audio_asset,
    build_korean_tts_input,
    capture_korean_azure_catalog,
    korean_audio_asset_reusable,
)


def _hash(seed: str) -> str:
    return sha256(seed.encode("utf-8")).hexdigest()


def _authority(**overrides: str) -> KoreanAudioAuthority:
    payload = {
        "job_id": "job-ko",
        "phase31_validation_receipt_sha256": _hash("phase31-receipt"),
        "phase31_snapshot_manifest_sha256": _hash("phase31-manifest"),
        "phase31_snapshot_root_sha256": _hash("phase31-root"),
        "binding_receipt_sha256": _hash("binding"),
        "provider_policy_sha256": _hash("provider-policy"),
        "pilot_authority_sha256": _hash("pilot-authority"),
        "catalog_locator_sha256": _hash("catalog-locator"),
        "catalog_content_sha256": _hash("catalog-content"),
        "profile_sample_authority_sha256": _hash("profile-authority"),
    }
    payload.update(overrides)
    return KoreanAudioAuthority(**payload)


def _voice() -> KoreanAzureCatalogVoice:
    return KoreanAzureCatalogVoice(
        short_name="ko-KR-SunHiNeural",
        locale="ko-KR",
        region="koreacentral",
        status="available",
        voice_type="Neural",
        provider_sdk_version="1.49.1",
    )


def _profile() -> KoreanVoiceProfile:
    return KoreanVoiceProfile.from_catalog_voice(
        _voice(),
        catalog_receipt_sha256=_hash("catalog-receipt"),
        profile_authority_sha256=_hash("profile-authority"),
    )


def test_catalog_capture_validates_endpoint_authority_order_and_no_static_korean_registry() -> None:
    with pytest.raises(VoiceSelectionError):
        select_voice(SupportedLanguage.KO, available_voice_ids={"ko-KR-SunHiNeural"})

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

    def adapter_factory() -> object:
        calls.append("adapter")
        return object()

    def fetcher(endpoint_url: str) -> tuple[KoreanAzureCatalogVoice, ...]:
        calls.append("fetch")
        assert endpoint_url == "https://koreacentral.tts.speech.microsoft.com/cognitiveservices/voices/list"
        return (_voice(),)

    result = capture_korean_azure_catalog(
        authority=authority,
        endpoint_url="https://koreacentral.tts.speech.microsoft.com/cognitiveservices/voices/list",
        phase31_verifier=verifier,
        adapter_factory=adapter_factory,
        catalog_fetcher=fetcher,
    )

    assert calls == ["verify_phase31", "adapter", "fetch"]
    assert result.job_id == "job-ko"
    assert result.selected_voice.short_name == "ko-KR-SunHiNeural"
    assert result.catalog_receipt_sha256

    calls.clear()

    def drift_verifier(*, expected_receipt_sha256: str) -> object:
        calls.append("verify_phase31")
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
        capture_korean_azure_catalog(
            authority=authority,
            endpoint_url="https://koreacentral.tts.speech.microsoft.com/cognitiveservices/voices/list",
            phase31_verifier=drift_verifier,
            adapter_factory=adapter_factory,
            catalog_fetcher=fetcher,
        )
    assert calls == ["verify_phase31"]


def test_korean_tts_input_is_neutral_nfc_escaped_and_exact_request_hashed() -> None:
    normalized = build_korean_tts_input(
        "학교 & 친구",
        asset_kind=AudioAssetKind.SENTENCE,
        profile=_profile(),
    )

    assert normalized.display_text == "학교 & 친구"
    assert normalized.tts_text == "학교 & 친구"
    assert 'xml:lang="ko-KR"' in (normalized.ssml_text or "")
    assert "&amp;" in (normalized.ssml_text or "")
    assert "<audio" not in (normalized.ssml_text or "")
    assert normalized.synthesis_request_sha256 is not None


def test_korean_audio_asset_is_pending_review_no_fallback_and_exact_reuse() -> None:
    profile = _profile()
    normalized = build_korean_tts_input(
        "학교",
        asset_kind=AudioAssetKind.WORD,
        profile=profile,
    )
    asset = build_korean_audio_asset(
        job_id="job-ko",
        item_key="item-1",
        asset_kind=AudioAssetKind.WORD,
        normalized_input=normalized,
        profile=profile,
        storage_path="audio/ko-word.mp3",
        media_bytes=b"mp3-bytes",
        duration_ms=123,
        fallback_used=False,
    )

    assert asset.provenance.provider is AudioProvider.AZURE
    assert asset.provenance.locale == "ko-KR"
    assert asset.provenance.status is AudioSynthesisStatus.SYNTHESIZED
    assert asset.provenance.audio_review_status is AudioReviewStatus.SYNTHESIZED_PENDING
    assert asset.provenance.voice_profile_sha256 == profile.profile_sha256
    assert asset.provenance.synthesis_request_sha256 == normalized.synthesis_request_sha256
    assert asset.provenance.artifact_sha256 == _hash("artifact:mp3-bytes")

    with pytest.raises(ValueError, match="fallback"):
        build_korean_audio_asset(
            job_id="job-ko",
            item_key="item-1",
            asset_kind=AudioAssetKind.WORD,
            normalized_input=normalized,
            profile=profile,
            storage_path="audio/ko-word.mp3",
            media_bytes=b"mp3-bytes",
            duration_ms=123,
            fallback_used=True,
        )

    approved = asset.model_copy(
        update={
            "provenance": asset.provenance.model_copy(
                update={
                    "audio_review_status": AudioReviewStatus.APPROVED,
                    "audio_review_receipt_sha256": _hash("audio-review"),
                    "heard_review_receipt_sha256": _hash("heard-review"),
                }
            )
        }
    )

    assert korean_audio_asset_reusable(asset, approved) is True
    assert korean_audio_asset_reusable(
        asset,
        approved.model_copy(
            update={
                "provenance": approved.provenance.model_copy(
                    update={"voice_profile_sha256": _hash("other-profile")}
                )
            }
        ),
    ) is False
