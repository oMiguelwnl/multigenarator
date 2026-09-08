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
from multilang.domain.korean import KoreanFrequencyJobAuthority
from multilang.domain.korean_provider import (
    KoreanProviderBudget,
    KoreanProviderPolicy,
    KoreanProviderRoute,
    KoreanProviderTask,
)
from multilang.services.audio_voice_registry import VoiceSelectionError, select_voice
from multilang.services.korean_audio import (
    KoreanAudioAuthority,
    KoreanAzureCatalogVoice,
    KoreanVoiceProfile,
    build_korean_audio_asset,
    build_korean_voice_profile_from_authority,
    build_korean_tts_input,
    capture_korean_azure_catalog,
    capture_korean_azure_catalog_pilot,
    korean_audio_asset_reusable,
)


def _hash(seed: str) -> str:
    return sha256(seed.encode("utf-8")).hexdigest()


LIVE_JOB_ID = "phase32-live-text-catalog-pilot"
CATALOG_RESULT_FILE_SHA256 = _hash("catalog-result-file")
CATALOG_LOCATOR_SHA256 = _hash("catalog-locator-live")
CATALOG_CONTENT_SHA256 = _hash("catalog-content-live")
PROVIDER_POLICY_SHA256 = _hash("provider-policy-live")
PILOT_AUTHORITY_SHA256 = _hash("pilot-authority-live")
PROFILE_AUTHORITY_SHA256 = _hash("profile-authority-file")
SELECTED_VOICE_ID = "ko-KR-SunHi:DragonHDLatestNeural"


def _catalog_result(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "korean-azure-catalog-pilot-result-v1",
        "job_id": LIVE_JOB_ID,
        "binding_receipt_sha256": _hash("binding"),
        "provider_policy_sha256": PROVIDER_POLICY_SHA256,
        "pilot_authority_sha256": PILOT_AUTHORITY_SHA256,
        "catalog_locale": "ko-KR",
        "catalog_locator_sha256": CATALOG_LOCATOR_SHA256,
        "catalog_content_sha256": CATALOG_CONTENT_SHA256,
        "voice_count": 2,
        "catalog_query_count": 1,
        "synthesis_attempt_count": 0,
        "production_database_used": False,
        "voices": [
            {"voice_id": SELECTED_VOICE_ID, "locale": "ko-KR", "region": "eastus"},
            {"voice_id": "ko-KR-Hyunsu:DragonHDLatestNeural", "locale": "ko-KR", "region": "eastus"},
        ],
    }
    payload.update(overrides)
    return payload


def _profile_authority_mapping(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "korean-voice-profile-authority-v1",
        "kind": "voice-profile-authority",
        "selected_voice_id": SELECTED_VOICE_ID,
        "locale": "ko-KR",
        "region": "eastus",
        "catalog_result_file_sha256": CATALOG_RESULT_FILE_SHA256,
        "catalog_locator_sha256": CATALOG_LOCATOR_SHA256,
        "catalog_content_sha256": CATALOG_CONTENT_SHA256,
        "provider_policy_sha256": PROVIDER_POLICY_SHA256,
        "pilot_authority_sha256": PILOT_AUTHORITY_SHA256,
        "catalog_voice_count": 2,
        "catalog_query_count": 1,
        "catalog_synthesis_attempt_count": 0,
        "profile_policy_version": "korean-neutral-ssml-v1",
        "ssml_policy": "neutral",
        "output_format": "audio-24khz-48kbitrate-mono-mp3",
        "usage_scope": [
            "ordinary-frequency-word-audio",
            "ordinary-frequency-sentence-audio",
        ],
        "powers": ["bind-voice-profile"],
        "synthesis_allowed": False,
        "fallback_policy": "none",
        "grants_route_authority": False,
        "grants_voice_profile_authority": True,
        "grants_audio_authority": False,
        "grants_review_authority": False,
        "grants_export_authority": False,
        "grants_release_authority": False,
        "grants_publication_authority": False,
        "grants_delivery_authority": False,
    }
    payload.update(overrides)
    return payload


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


def _provider_policy() -> KoreanProviderPolicy:
    budget = KoreanProviderBudget(
        max_attempts=2,
        max_input_tokens=4096,
        max_output_tokens=1024,
        max_total_tokens=5120,
        max_estimated_cost_usd=1.0,
        max_latency_ms=60000,
        timeout_seconds=60.0,
        max_batch_items=10,
        max_concurrency=1,
    )
    routes = []
    for task in KoreanProviderTask:
        provider = "disabled" if task in {KoreanProviderTask.WORD_AUDIO, KoreanProviderTask.SENTENCE_AUDIO} else "openai"
        if task is KoreanProviderTask.TRANSLATION:
            provider = "deepl"
        if task is KoreanProviderTask.CATALOG:
            provider = "azure-speech"
        routes.append(
            KoreanProviderRoute(
                task=task,
                provider=provider,
                model=None if provider == "disabled" else f"{task.value}-model",
                budget=budget,
                cache_namespace=f"test-{task.value}",
                response_schema_sha256=_hash(f"schema:{task.value}"),
            )
        )
    return KoreanProviderPolicy(routes=tuple(routes))


def _frequency_authority(provider_policy_sha256: str) -> KoreanFrequencyJobAuthority:
    return KoreanFrequencyJobAuthority(
        stage="pilot_base",
        phase31_pointer_locator_sha256=_hash("phase31-pointer-locator"),
        phase31_pointer_content_sha256=_hash("phase31-pointer-content"),
        phase31_validation_receipt_sha256=_hash("phase31-receipt"),
        phase31_snapshot_manifest_sha256=_hash("phase31-manifest"),
        phase31_snapshot_root_sha256=_hash("phase31-root"),
        frequency_bundle_locator_sha256=_hash("bundle-manifest"),
        frequency_bundle_content_sha256=_hash("bundle-content"),
        source_retrieval_sha256=_hash("source-retrieval"),
        source_build_result_sha256=_hash("source-build"),
        source_review_aggregate_sha256=_hash("source-review"),
        provider_policy_sha256=provider_policy_sha256,
        pilot_authority_sha256=_hash("pilot-authority"),
    )


def test_voice_profile_authority_binds_user_selected_catalog_voice_without_downstream_grants() -> None:
    profile, evidence = build_korean_voice_profile_from_authority(
        catalog_result=_catalog_result(),
        profile_authority=_profile_authority_mapping(),
        job_id=LIVE_JOB_ID,
        provider_policy_sha256=PROVIDER_POLICY_SHA256,
        pilot_authority_sha256=PILOT_AUTHORITY_SHA256,
        catalog_locator_sha256=CATALOG_LOCATOR_SHA256,
        catalog_content_sha256=CATALOG_CONTENT_SHA256,
        catalog_result_file_sha256=CATALOG_RESULT_FILE_SHA256,
        profile_authority_sha256=PROFILE_AUTHORITY_SHA256,
    )

    assert profile.schema_version == "korean-voice-profile-v1"
    assert profile.voice_id == SELECTED_VOICE_ID
    assert profile.locale == "ko-KR"
    assert profile.region == "eastus"
    assert profile.provider == "azure-speech"
    assert profile.output_format == "audio-24khz-48kbitrate-mono-mp3"
    assert profile.profile_policy_version == "korean-neutral-ssml-v1"
    assert profile.ssml_policy == "neutral"
    assert profile.fallback_policy == "none"
    assert profile.usage_scope == (
        "ordinary-frequency-word-audio",
        "ordinary-frequency-sentence-audio",
    )
    assert profile.catalog_result_file_sha256 == CATALOG_RESULT_FILE_SHA256
    assert profile.catalog_locator_sha256 == CATALOG_LOCATOR_SHA256
    assert profile.catalog_content_sha256 == CATALOG_CONTENT_SHA256
    assert profile.catalog_receipt_sha256 == CATALOG_CONTENT_SHA256
    assert profile.provider_policy_sha256 == PROVIDER_POLICY_SHA256
    assert profile.pilot_authority_sha256 == PILOT_AUTHORITY_SHA256
    assert profile.profile_authority_sha256 == PROFILE_AUTHORITY_SHA256
    assert profile.profile_sha256 != PROFILE_AUTHORITY_SHA256

    assert evidence.status == "valid"
    assert evidence.selected_voice_in_catalog is True
    assert evidence.catalog_voice_count == 2
    assert evidence.catalog_locale_set == ("ko-KR",)
    assert evidence.synthesis_attempt_count == 0
    assert evidence.fallback_attempt_count == 0
    assert evidence.protected_input_drift_count == 0
    assert evidence.static_registry_activated is False
    assert evidence.grants_voice_profile_authority is True
    assert evidence.grants_audio_authority is False
    assert evidence.grants_review_authority is False
    assert evidence.grants_export_authority is False
    assert evidence.grants_release_authority is False
    assert evidence.grants_publication_authority is False
    assert evidence.grants_delivery_authority is False
    assert evidence.profile_sha256 == profile.profile_sha256
    assert evidence.profile_sha256 != evidence.profile_authority_sha256
    assert "korean_text" not in profile.model_dump(mode="json")
    assert "portuguese_text" not in evidence.model_dump(mode="json")


def test_voice_profile_authority_rejects_drift_and_missing_selected_voice() -> None:
    with pytest.raises(ValueError, match="selected voice is not present"):
        build_korean_voice_profile_from_authority(
            catalog_result=_catalog_result(),
            profile_authority=_profile_authority_mapping(selected_voice_id="ko-KR-MissingNeural"),
            job_id=LIVE_JOB_ID,
            provider_policy_sha256=PROVIDER_POLICY_SHA256,
            pilot_authority_sha256=PILOT_AUTHORITY_SHA256,
            catalog_locator_sha256=CATALOG_LOCATOR_SHA256,
            catalog_content_sha256=CATALOG_CONTENT_SHA256,
            catalog_result_file_sha256=CATALOG_RESULT_FILE_SHA256,
            profile_authority_sha256=PROFILE_AUTHORITY_SHA256,
        )

    with pytest.raises(ValueError, match="provider policy drift"):
        build_korean_voice_profile_from_authority(
            catalog_result=_catalog_result(provider_policy_sha256=_hash("other-policy")),
            profile_authority=_profile_authority_mapping(),
            job_id=LIVE_JOB_ID,
            provider_policy_sha256=PROVIDER_POLICY_SHA256,
            pilot_authority_sha256=PILOT_AUTHORITY_SHA256,
            catalog_locator_sha256=CATALOG_LOCATOR_SHA256,
            catalog_content_sha256=CATALOG_CONTENT_SHA256,
            catalog_result_file_sha256=CATALOG_RESULT_FILE_SHA256,
            profile_authority_sha256=PROFILE_AUTHORITY_SHA256,
        )

    missing_hash_catalog = _catalog_result()
    missing_hash_catalog.pop("catalog_content_sha256")
    with pytest.raises(ValueError, match="catalog_content_sha256"):
        build_korean_voice_profile_from_authority(
            catalog_result=missing_hash_catalog,
            profile_authority=_profile_authority_mapping(),
            job_id=LIVE_JOB_ID,
            provider_policy_sha256=PROVIDER_POLICY_SHA256,
            pilot_authority_sha256=PILOT_AUTHORITY_SHA256,
            catalog_locator_sha256=CATALOG_LOCATOR_SHA256,
            catalog_content_sha256=CATALOG_CONTENT_SHA256,
            catalog_result_file_sha256=CATALOG_RESULT_FILE_SHA256,
            profile_authority_sha256=PROFILE_AUTHORITY_SHA256,
        )


def test_voice_profile_authority_rejects_locale_synthesis_and_grant_drift() -> None:
    with pytest.raises(ValueError, match="catalog locale drift"):
        build_korean_voice_profile_from_authority(
            catalog_result=_catalog_result(
                voice_count=3,
                voices=[
                    {"voice_id": SELECTED_VOICE_ID, "locale": "ko-KR", "region": "eastus"},
                    {"voice_id": "ko-KR-Hyunsu:DragonHDLatestNeural", "locale": "ko-KR", "region": "eastus"},
                    {"voice_id": "en-US-JennyNeural", "locale": "en-US", "region": "eastus"},
                ],
            ),
            profile_authority=_profile_authority_mapping(catalog_voice_count=3),
            job_id=LIVE_JOB_ID,
            provider_policy_sha256=PROVIDER_POLICY_SHA256,
            pilot_authority_sha256=PILOT_AUTHORITY_SHA256,
            catalog_locator_sha256=CATALOG_LOCATOR_SHA256,
            catalog_content_sha256=CATALOG_CONTENT_SHA256,
            catalog_result_file_sha256=CATALOG_RESULT_FILE_SHA256,
            profile_authority_sha256=PROFILE_AUTHORITY_SHA256,
        )

    with pytest.raises(ValueError, match="zero synthesis"):
        build_korean_voice_profile_from_authority(
            catalog_result=_catalog_result(synthesis_attempt_count=1),
            profile_authority=_profile_authority_mapping(catalog_synthesis_attempt_count=1),
            job_id=LIVE_JOB_ID,
            provider_policy_sha256=PROVIDER_POLICY_SHA256,
            pilot_authority_sha256=PILOT_AUTHORITY_SHA256,
            catalog_locator_sha256=CATALOG_LOCATOR_SHA256,
            catalog_content_sha256=CATALOG_CONTENT_SHA256,
            catalog_result_file_sha256=CATALOG_RESULT_FILE_SHA256,
            profile_authority_sha256=PROFILE_AUTHORITY_SHA256,
        )

    with pytest.raises(ValueError, match="only bind-voice-profile"):
        build_korean_voice_profile_from_authority(
            catalog_result=_catalog_result(),
            profile_authority=_profile_authority_mapping(powers=["bind-voice-profile", "synthesize-audio"]),
            job_id=LIVE_JOB_ID,
            provider_policy_sha256=PROVIDER_POLICY_SHA256,
            pilot_authority_sha256=PILOT_AUTHORITY_SHA256,
            catalog_locator_sha256=CATALOG_LOCATOR_SHA256,
            catalog_content_sha256=CATALOG_CONTENT_SHA256,
            catalog_result_file_sha256=CATALOG_RESULT_FILE_SHA256,
            profile_authority_sha256=PROFILE_AUTHORITY_SHA256,
        )


def test_catalog_pilot_logs_with_explicit_job_id_for_frequency_authority() -> None:
    provider_policy = _provider_policy()
    authority = _frequency_authority(provider_policy.policy_sha256)
    records = []

    class Logger:
        def insert(self, record: object) -> None:
            records.append(record)

    def verifier(*, expected_receipt_sha256: str) -> object:
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

    payload = capture_korean_azure_catalog_pilot(
        job_id="job-ko",
        authority=authority,
        provider_policy=provider_policy,
        endpoint_url="https://koreacentral.tts.speech.microsoft.com/cognitiveservices/voices/list",
        provider_call_logger=Logger(),
        phase31_verifier=verifier,
        catalog_fetcher=lambda _: ({"ShortName": "ko-KR-TestNeural", "Locale": "ko-KR"},),
    )

    assert payload["job_id"] == "job-ko"
    assert len(records) == 1
    assert records[0].job_id == "job-ko"
    assert records[0].operation == KoreanProviderTask.CATALOG.value


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
