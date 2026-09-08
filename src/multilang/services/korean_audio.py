"""Korean Azure catalog, SSML, audio identity, and reuse contracts."""

from __future__ import annotations

from hashlib import sha256
from html import escape
import json
from pathlib import Path
from time import perf_counter
from typing import Callable, Literal, Mapping
from urllib.parse import urlparse
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator

from multilang.domain.audio import (
    AudioAssetKind,
    AudioAssetRecord,
    AudioFormat,
    AudioProvider,
    AudioProvenance,
    AudioReviewStatus,
    AudioSynthesisStatus,
    NormalizedTtsInput,
)
from multilang.domain.korean import KOREAN_PROVIDER_LOCALE, KoreanFrequencyJobAuthority
from multilang.domain.korean_provider import KoreanProviderPolicy, KoreanProviderTask
from multilang.repositories.provider_call_log_repository import ProviderCallLogCreate
from multilang.services.korean_foundation_snapshot import verify_active_korean_foundation_snapshot_provenance


_HEX = frozenset("0123456789abcdef")
_KOREAN_VOICE_PROFILE_SCHEMA_VERSION = "korean-voice-profile-v1"
_KOREAN_VOICE_PROFILE_VALIDATION_SCHEMA_VERSION = "korean-voice-profile-validation-v1"
_KOREAN_VOICE_PROFILE_AUTHORITY_SCHEMA_VERSION = "korean-voice-profile-authority-v1"
_KOREAN_VOICE_PROFILE_KIND = "voice-profile-authority"
_KOREAN_VOICE_PROFILE_POLICY_VERSION = "korean-neutral-ssml-v1"
_KOREAN_VOICE_PROFILE_SSML_POLICY = "neutral"
_KOREAN_VOICE_PROFILE_PROVIDER = "azure-speech"
_KOREAN_VOICE_PROFILE_FALLBACK_POLICY = "none"
_KOREAN_VOICE_PROFILE_OUTPUT_FORMAT = AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3.value
_KOREAN_VOICE_PROFILE_USAGE_SCOPE = (
    "ordinary-frequency-word-audio",
    "ordinary-frequency-sentence-audio",
)


def _sha256_identifier(value: str, *, field_name: str) -> str:
    if len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class KoreanAudioAuthority(_FrozenModel):
    """Hash-only authority needed before Korean catalog/audio work."""

    job_id: str = Field(min_length=1, max_length=128)
    phase31_validation_receipt_sha256: str = Field(min_length=64, max_length=64)
    phase31_snapshot_manifest_sha256: str = Field(min_length=64, max_length=64)
    phase31_snapshot_root_sha256: str = Field(min_length=64, max_length=64)
    binding_receipt_sha256: str = Field(min_length=64, max_length=64)
    provider_policy_sha256: str = Field(min_length=64, max_length=64)
    pilot_authority_sha256: str = Field(min_length=64, max_length=64)
    catalog_locator_sha256: str = Field(min_length=64, max_length=64)
    catalog_content_sha256: str = Field(min_length=64, max_length=64)
    profile_sample_authority_sha256: str = Field(min_length=64, max_length=64)
    region: str = Field(default="koreacentral", min_length=1, max_length=64)

    @field_validator(
        "phase31_validation_receipt_sha256",
        "phase31_snapshot_manifest_sha256",
        "phase31_snapshot_root_sha256",
        "binding_receipt_sha256",
        "provider_policy_sha256",
        "pilot_authority_sha256",
        "catalog_locator_sha256",
        "catalog_content_sha256",
        "profile_sample_authority_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))


class KoreanAzureCatalogVoice(_FrozenModel):
    short_name: str = Field(min_length=1, max_length=160)
    locale: Literal["ko-KR"]
    region: str = Field(min_length=1, max_length=64)
    status: Literal["available"]
    voice_type: str = Field(min_length=1, max_length=64)
    provider_sdk_version: str = Field(min_length=1, max_length=64)

    @field_validator("short_name")
    @classmethod
    def voice_must_be_korean_locale(cls, value: str) -> str:
        if not value.startswith("ko-KR-"):
            raise ValueError("Korean Azure voice must be a ko-KR voice")
        return value


class KoreanAzureCatalogResult(_FrozenModel):
    job_id: str = Field(min_length=1, max_length=128)
    endpoint_url: str = Field(min_length=1, max_length=256)
    selected_voice: KoreanAzureCatalogVoice
    catalog_receipt_sha256: str = Field(min_length=64, max_length=64)


class KoreanVoiceProfileAuthority(_FrozenModel):
    """Sanitized operator authority for binding one Korean Azure voice profile."""

    schema_version: Literal["korean-voice-profile-authority-v1"]
    kind: Literal["voice-profile-authority"]
    selected_voice_id: str = Field(min_length=1, max_length=160)
    locale: Literal["ko-KR"]
    region: str = Field(min_length=1, max_length=64)
    catalog_result_file_sha256: str = Field(min_length=64, max_length=64)
    catalog_locator_sha256: str = Field(min_length=64, max_length=64)
    catalog_content_sha256: str = Field(min_length=64, max_length=64)
    provider_policy_sha256: str = Field(min_length=64, max_length=64)
    pilot_authority_sha256: str = Field(min_length=64, max_length=64)
    catalog_voice_count: int = Field(ge=1)
    catalog_query_count: int = Field(ge=0)
    catalog_synthesis_attempt_count: int = Field(ge=0)
    profile_policy_version: Literal["korean-neutral-ssml-v1"]
    ssml_policy: Literal["neutral"]
    output_format: Literal["audio-24khz-48kbitrate-mono-mp3"]
    usage_scope: tuple[str, ...]
    powers: tuple[str, ...]
    synthesis_allowed: bool
    fallback_policy: Literal["none"]
    grants_route_authority: bool
    grants_voice_profile_authority: bool
    grants_audio_authority: bool
    grants_review_authority: bool
    grants_export_authority: bool
    grants_release_authority: bool
    grants_publication_authority: bool
    grants_delivery_authority: bool

    @field_validator(
        "catalog_result_file_sha256",
        "catalog_locator_sha256",
        "catalog_content_sha256",
        "provider_policy_sha256",
        "pilot_authority_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @field_validator("selected_voice_id")
    @classmethod
    def selected_voice_must_be_korean(cls, value: str) -> str:
        if not value.startswith("ko-KR-"):
            raise ValueError("selected voice must be a ko-KR Azure voice")
        return value


class KoreanVoiceProfile(_FrozenModel):
    schema_version: Literal["korean-voice-profile-v1"] = _KOREAN_VOICE_PROFILE_SCHEMA_VERSION
    voice_id: str = Field(min_length=1, max_length=160)
    locale: Literal["ko-KR"]
    region: str = Field(min_length=1, max_length=64)
    provider: Literal["azure-speech"] = _KOREAN_VOICE_PROFILE_PROVIDER
    output_format: Literal["audio-24khz-48kbitrate-mono-mp3"] = _KOREAN_VOICE_PROFILE_OUTPUT_FORMAT
    profile_policy_version: Literal["korean-neutral-ssml-v1"] = _KOREAN_VOICE_PROFILE_POLICY_VERSION
    ssml_policy: Literal["neutral"] = _KOREAN_VOICE_PROFILE_SSML_POLICY
    usage_scope: tuple[str, ...] = _KOREAN_VOICE_PROFILE_USAGE_SCOPE
    fallback_policy: Literal["none"] = _KOREAN_VOICE_PROFILE_FALLBACK_POLICY
    provider_sdk_version: str = Field(min_length=1, max_length=64)
    catalog_receipt_sha256: str = Field(min_length=64, max_length=64)
    catalog_result_file_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    catalog_locator_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    catalog_content_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    provider_policy_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    pilot_authority_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    profile_authority_sha256: str = Field(min_length=64, max_length=64)
    profile_sha256: str = Field(min_length=64, max_length=64)

    @field_validator(
        "catalog_receipt_sha256",
        "catalog_result_file_sha256",
        "catalog_locator_sha256",
        "catalog_content_sha256",
        "provider_policy_sha256",
        "pilot_authority_sha256",
        "profile_authority_sha256",
        "profile_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return value
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))

    @classmethod
    def from_catalog_voice(
        cls,
        voice: KoreanAzureCatalogVoice,
        *,
        catalog_receipt_sha256: str,
        profile_authority_sha256: str,
    ) -> "KoreanVoiceProfile":
        profile_payload = {
            "voice_id": voice.short_name,
            "locale": voice.locale,
            "region": voice.region,
            "provider": _KOREAN_VOICE_PROFILE_PROVIDER,
            "output_format": _KOREAN_VOICE_PROFILE_OUTPUT_FORMAT,
            "profile_policy_version": _KOREAN_VOICE_PROFILE_POLICY_VERSION,
            "ssml_policy": _KOREAN_VOICE_PROFILE_SSML_POLICY,
            "usage_scope": _KOREAN_VOICE_PROFILE_USAGE_SCOPE,
            "fallback_policy": _KOREAN_VOICE_PROFILE_FALLBACK_POLICY,
            "provider_sdk_version": voice.provider_sdk_version,
            "catalog_receipt_sha256": catalog_receipt_sha256,
            "profile_authority_sha256": profile_authority_sha256,
        }
        return cls(
            voice_id=voice.short_name,
            locale=voice.locale,
            region=voice.region,
            provider_sdk_version=voice.provider_sdk_version,
            catalog_receipt_sha256=catalog_receipt_sha256,
            profile_authority_sha256=profile_authority_sha256,
            profile_sha256=_canonical_sha256(profile_payload),
        )


class KoreanVoiceProfileValidation(_FrozenModel):
    """Hash-only validation evidence for a bound Korean voice profile."""

    schema_version: Literal["korean-voice-profile-validation-v1"] = _KOREAN_VOICE_PROFILE_VALIDATION_SCHEMA_VERSION
    status: Literal["valid"]
    job_id: str = Field(min_length=1, max_length=128)
    profile_sha256: str = Field(min_length=64, max_length=64)
    evidence_sha256: str = Field(min_length=64, max_length=64)
    profile_authority_sha256: str = Field(min_length=64, max_length=64)
    catalog_result_file_sha256: str = Field(min_length=64, max_length=64)
    catalog_locator_sha256: str = Field(min_length=64, max_length=64)
    catalog_content_sha256: str = Field(min_length=64, max_length=64)
    provider_policy_sha256: str = Field(min_length=64, max_length=64)
    pilot_authority_sha256: str = Field(min_length=64, max_length=64)
    selected_voice_id: str = Field(min_length=1, max_length=160)
    selected_voice_in_catalog: bool
    catalog_voice_count: int = Field(ge=1)
    catalog_locale_set: tuple[str, ...]
    catalog_query_count: int = Field(ge=0)
    synthesis_attempt_count: int = Field(ge=0)
    fallback_attempt_count: int = Field(ge=0)
    protected_input_drift_count: int = Field(ge=0)
    production_database_used: bool
    fallback_policy: Literal["none"]
    static_registry_activated: bool
    grants_route_authority: bool
    grants_voice_profile_authority: bool
    grants_audio_authority: bool
    grants_review_authority: bool
    grants_export_authority: bool
    grants_release_authority: bool
    grants_publication_authority: bool
    grants_delivery_authority: bool

    @field_validator(
        "profile_sha256",
        "evidence_sha256",
        "profile_authority_sha256",
        "catalog_result_file_sha256",
        "catalog_locator_sha256",
        "catalog_content_sha256",
        "provider_policy_sha256",
        "pilot_authority_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_identifier(value, field_name=getattr(info, "field_name", "hash"))


def build_korean_voice_profile_from_authority(
    *,
    catalog_result: Mapping[str, object],
    profile_authority: Mapping[str, object],
    job_id: str,
    provider_policy_sha256: str,
    pilot_authority_sha256: str,
    catalog_locator_sha256: str,
    catalog_content_sha256: str,
    catalog_result_file_sha256: str,
    profile_authority_sha256: str,
) -> tuple[KoreanVoiceProfile, KoreanVoiceProfileValidation]:
    """Build a sanitized Korean voice profile from explicit catalog/profile authority."""

    if not job_id.strip():
        raise ValueError("Korean voice profile requires job_id")
    expected_hashes = {
        "provider_policy_sha256": _sha256_identifier(
            provider_policy_sha256, field_name="provider_policy_sha256"
        ),
        "pilot_authority_sha256": _sha256_identifier(
            pilot_authority_sha256, field_name="pilot_authority_sha256"
        ),
        "catalog_locator_sha256": _sha256_identifier(
            catalog_locator_sha256, field_name="catalog_locator_sha256"
        ),
        "catalog_content_sha256": _sha256_identifier(
            catalog_content_sha256, field_name="catalog_content_sha256"
        ),
        "catalog_result_file_sha256": _sha256_identifier(
            catalog_result_file_sha256, field_name="catalog_result_file_sha256"
        ),
    }
    profile_authority_sha256 = _sha256_identifier(
        profile_authority_sha256, field_name="profile_authority_sha256"
    )
    authority = KoreanVoiceProfileAuthority.model_validate(profile_authority)

    _validate_profile_authority_contract(authority, expected_hashes=expected_hashes)
    _validate_catalog_result_contract(
        catalog_result,
        job_id=job_id,
        expected_hashes=expected_hashes,
    )
    voices = _catalog_voice_mappings(catalog_result)
    selected_voice = _selected_catalog_voice(
        voices,
        selected_voice_id=authority.selected_voice_id,
        region=authority.region,
    )
    if authority.catalog_voice_count != len(voices) or _int_field(catalog_result, "voice_count") != len(voices):
        raise ValueError("Korean voice profile catalog voice count drift")
    if authority.catalog_query_count != _int_field(catalog_result, "catalog_query_count"):
        raise ValueError("Korean voice profile catalog query count drift")

    provider_sdk_version = _optional_str_field(selected_voice, "provider_sdk_version", default="not-captured")
    profile_payload = {
        "schema_version": _KOREAN_VOICE_PROFILE_SCHEMA_VERSION,
        "voice_id": authority.selected_voice_id,
        "locale": KOREAN_PROVIDER_LOCALE,
        "region": authority.region,
        "provider": _KOREAN_VOICE_PROFILE_PROVIDER,
        "output_format": _KOREAN_VOICE_PROFILE_OUTPUT_FORMAT,
        "profile_policy_version": _KOREAN_VOICE_PROFILE_POLICY_VERSION,
        "ssml_policy": _KOREAN_VOICE_PROFILE_SSML_POLICY,
        "usage_scope": _KOREAN_VOICE_PROFILE_USAGE_SCOPE,
        "fallback_policy": _KOREAN_VOICE_PROFILE_FALLBACK_POLICY,
        "provider_sdk_version": provider_sdk_version,
        "catalog_receipt_sha256": catalog_content_sha256,
        "catalog_result_file_sha256": catalog_result_file_sha256,
        "catalog_locator_sha256": catalog_locator_sha256,
        "catalog_content_sha256": catalog_content_sha256,
        "provider_policy_sha256": provider_policy_sha256,
        "pilot_authority_sha256": pilot_authority_sha256,
        "profile_authority_sha256": profile_authority_sha256,
    }
    profile = KoreanVoiceProfile(
        **profile_payload,
        profile_sha256=_canonical_sha256(profile_payload),
    )
    validation_payload = {
        "schema_version": _KOREAN_VOICE_PROFILE_VALIDATION_SCHEMA_VERSION,
        "status": "valid",
        "job_id": job_id,
        "profile_sha256": profile.profile_sha256,
        "profile_authority_sha256": profile_authority_sha256,
        "catalog_result_file_sha256": catalog_result_file_sha256,
        "catalog_locator_sha256": catalog_locator_sha256,
        "catalog_content_sha256": catalog_content_sha256,
        "provider_policy_sha256": provider_policy_sha256,
        "pilot_authority_sha256": pilot_authority_sha256,
        "selected_voice_id": authority.selected_voice_id,
        "selected_voice_in_catalog": True,
        "catalog_voice_count": len(voices),
        "catalog_locale_set": (KOREAN_PROVIDER_LOCALE,),
        "catalog_query_count": authority.catalog_query_count,
        "synthesis_attempt_count": 0,
        "fallback_attempt_count": 0,
        "protected_input_drift_count": 0,
        "production_database_used": False,
        "fallback_policy": _KOREAN_VOICE_PROFILE_FALLBACK_POLICY,
        "static_registry_activated": False,
        "grants_route_authority": False,
        "grants_voice_profile_authority": True,
        "grants_audio_authority": False,
        "grants_review_authority": False,
        "grants_export_authority": False,
        "grants_release_authority": False,
        "grants_publication_authority": False,
        "grants_delivery_authority": False,
    }
    return profile, KoreanVoiceProfileValidation(
        **validation_payload,
        evidence_sha256=_canonical_sha256(validation_payload),
    )


def capture_korean_azure_catalog(
    *,
    authority: KoreanAudioAuthority,
    endpoint_url: str,
    phase31_verifier: Callable[..., object] = verify_active_korean_foundation_snapshot_provenance,
    adapter_factory: Callable[[], object] | None = None,
    catalog_fetcher: Callable[[str], tuple[KoreanAzureCatalogVoice, ...]],
) -> KoreanAzureCatalogResult:
    """Capture fake/live catalog evidence only after fresh Phase 31 authority checks."""

    _validate_azure_catalog_endpoint(endpoint_url, region=authority.region)
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
    if adapter_factory is not None:
        adapter_factory()
    voices = catalog_fetcher(endpoint_url)
    selected = _select_korean_catalog_voice(voices, region=authority.region)
    payload = {
        "job_id": authority.job_id,
        "endpoint_url": endpoint_url,
        "selected_voice": selected.model_dump(mode="json"),
        "catalog_content_sha256": authority.catalog_content_sha256,
        "provider_policy_sha256": authority.provider_policy_sha256,
    }
    return KoreanAzureCatalogResult(
        job_id=authority.job_id,
        endpoint_url=endpoint_url,
        selected_voice=selected,
        catalog_receipt_sha256=_canonical_sha256(payload),
    )


def capture_korean_azure_catalog_pilot(
    *,
    job_id: str,
    authority: KoreanFrequencyJobAuthority,
    provider_policy: KoreanProviderPolicy,
    endpoint_url: str,
    provider_call_logger: object | None,
    phase31_verifier: Callable[..., object] = verify_active_korean_foundation_snapshot_provenance,
    catalog_fetcher: Callable[[str], object],
) -> dict[str, object]:
    """Capture a sanitized Korean Azure voice-list pilot result without synthesis."""

    if not job_id.strip():
        raise ValueError("Korean Azure catalog pilot requires job_id")
    if authority.stage != "pilot_base":
        raise ValueError("Korean Azure catalog pilot requires pilot_base authority")
    if provider_policy.policy_sha256 != authority.provider_policy_sha256:
        raise ValueError("Korean Azure catalog pilot provider policy drift")
    region = _region_from_catalog_endpoint(endpoint_url)
    _validate_azure_catalog_endpoint(endpoint_url, region=region)
    _verify_phase31_for_authority(authority, phase31_verifier=phase31_verifier)
    route = provider_policy.route_for(KoreanProviderTask.CATALOG)
    if not route.enabled or route.provider != "azure-speech":
        raise ValueError("Korean Azure catalog pilot requires an Azure Speech route")

    locator_sha256 = _canonical_sha256(
        {
            "endpoint_url": endpoint_url,
            "locale": KOREAN_PROVIDER_LOCALE,
            "task": KoreanProviderTask.CATALOG.value,
        }
    )
    telemetry = {
        "route_policy_sha256": route.route_policy_sha256,
        "budget_snapshot_sha256": route.budget_snapshot_sha256,
        "cache_key_sha256": route.cache_key_sha256(
            item_sha256=sha256(b"catalog").hexdigest(),
            input_sha256=locator_sha256,
        ),
        "response_schema_sha256": route.response_schema_sha256,
    }
    started = perf_counter()
    try:
        raw_catalog = catalog_fetcher(endpoint_url)
        voices = _sanitize_korean_catalog_voices(raw_catalog, region=region)
        content_sha256 = _canonical_sha256(
            {
                "catalog_locale": KOREAN_PROVIDER_LOCALE,
                "voices": voices,
            }
        )
    except Exception as exc:
        _log_catalog_provider_call(
            provider_call_logger,
            job_id=job_id,
            authority=authority,
            route_provider=route.provider,
            route_model=route.model,
            status="failure",
            latency_ms=_elapsed_ms(started),
            error_code=type(exc).__name__,
            error_summary=f"{type(exc).__name__}: redacted catalog failure",
            prompt_hash=locator_sha256,
            response_hash=None,
            telemetry=telemetry,
        )
        raise

    _log_catalog_provider_call(
        provider_call_logger,
        job_id=job_id,
        authority=authority,
        route_provider=route.provider,
        route_model=route.model,
        status="success",
        latency_ms=_elapsed_ms(started),
        error_code=None,
        error_summary=None,
        prompt_hash=locator_sha256,
        response_hash=content_sha256,
        telemetry=telemetry,
    )
    return {
        "schema_version": "korean-azure-catalog-pilot-result-v1",
        "job_id": job_id,
        "binding_receipt_sha256": authority.source_review_aggregate_sha256,
        "provider_policy_sha256": authority.provider_policy_sha256,
        "pilot_authority_sha256": authority.pilot_authority_sha256,
        "catalog_locale": KOREAN_PROVIDER_LOCALE,
        "catalog_locator_sha256": locator_sha256,
        "catalog_content_sha256": content_sha256,
        "voice_count": len(voices),
        "catalog_query_count": 1,
        "synthesis_attempt_count": 0,
        "production_database_used": False,
        "voices": voices,
    }


def build_korean_tts_input(
    text: str,
    *,
    asset_kind: AudioAssetKind,
    profile: KoreanVoiceProfile,
) -> NormalizedTtsInput:
    normalized = " ".join(unicodedata.normalize("NFC", text).strip().split())
    if not normalized:
        raise ValueError("Korean TTS text must not be blank")
    escaped = escape(normalized, quote=True)
    ssml_text = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{KOREAN_PROVIDER_LOCALE}">'
        f'<voice name="{escape(profile.voice_id, quote=True)}">{escaped}</voice>'
        "</speak>"
    )
    request_payload = {
        "asset_kind": asset_kind.value,
        "locale": profile.locale,
        "voice_id": profile.voice_id,
        "profile_sha256": profile.profile_sha256,
        "text": normalized,
        "ssml_text": ssml_text,
    }
    return NormalizedTtsInput(
        display_text=normalized,
        tts_text=normalized,
        ssml_text=ssml_text,
        synthesis_request_sha256=_canonical_sha256(request_payload),
    )


def build_korean_audio_asset(
    *,
    job_id: str,
    item_key: str,
    asset_kind: AudioAssetKind,
    normalized_input: NormalizedTtsInput,
    profile: KoreanVoiceProfile,
    storage_path: str | Path,
    media_bytes: bytes,
    duration_ms: int | None,
    fallback_used: bool,
) -> AudioAssetRecord:
    if fallback_used:
        raise ValueError("Korean audio cannot use fallback")
    if profile.locale != KOREAN_PROVIDER_LOCALE:
        raise ValueError("Korean audio requires ko-KR profile")
    artifact_sha256 = sha256(b"artifact:" + media_bytes).hexdigest()
    return AudioAssetRecord(
        job_id=job_id,
        item_key=item_key,
        asset_kind=asset_kind,
        display_text=normalized_input.display_text,
        normalized_input=normalized_input,
        provenance=AudioProvenance(
            provider=AudioProvider.AZURE,
            voice_id=profile.voice_id,
            locale=profile.locale,
            format=AudioFormat.AUDIO_24KHZ_48KBITRATE_MONO_MP3,
            text_hash=normalized_input.text_hash or "",
            ssml_hash=normalized_input.ssml_hash or "",
            storage_path=str(storage_path),
            byte_size=len(media_bytes),
            duration_ms=duration_ms,
            status=AudioSynthesisStatus.SYNTHESIZED,
            fallback_used=False,
            provider_sdk_version=profile.provider_sdk_version,
            voice_profile_sha256=profile.profile_sha256,
            catalog_receipt_sha256=profile.catalog_receipt_sha256,
            synthesis_request_sha256=normalized_input.synthesis_request_sha256,
            artifact_sha256=artifact_sha256,
            audio_review_status=AudioReviewStatus.SYNTHESIZED_PENDING,
        ),
    )


def korean_audio_asset_reusable(prepared_asset: AudioAssetRecord, reusable_asset: AudioAssetRecord) -> bool:
    """Return whether a Korean asset has the exact reviewed identity needed for reuse."""

    provenance = reusable_asset.provenance
    prepared = prepared_asset.provenance
    if prepared.locale != KOREAN_PROVIDER_LOCALE or provenance.locale != KOREAN_PROVIDER_LOCALE:
        return False
    if reusable_asset.asset_kind is not prepared_asset.asset_kind:
        return False
    if reusable_asset.normalized_input.tts_text != prepared_asset.normalized_input.tts_text:
        return False
    if reusable_asset.normalized_input.ssml_text != prepared_asset.normalized_input.ssml_text:
        return False
    if provenance.provider is not AudioProvider.AZURE or provenance.fallback_used:
        return False
    if provenance.status is not AudioSynthesisStatus.SYNTHESIZED or provenance.byte_size <= 0:
        return False
    if provenance.audio_review_status is not AudioReviewStatus.APPROVED:
        return False
    required = (
        provenance.provider_sdk_version,
        provenance.voice_profile_sha256,
        provenance.catalog_receipt_sha256,
        provenance.synthesis_request_sha256,
        provenance.artifact_sha256,
        provenance.audio_review_receipt_sha256,
        provenance.heard_review_receipt_sha256,
    )
    if any(value is None for value in required):
        return False
    return (
        provenance.voice_id == prepared.voice_id
        and provenance.format is prepared.format
        and provenance.provider_sdk_version == prepared.provider_sdk_version
        and provenance.voice_profile_sha256 == prepared.voice_profile_sha256
        and provenance.catalog_receipt_sha256 == prepared.catalog_receipt_sha256
        and provenance.synthesis_request_sha256 == prepared.synthesis_request_sha256
        and provenance.artifact_sha256 == prepared.artifact_sha256
    )


def synthesize_korean_frequency_audio(**kwargs: object) -> object:
    """CLI seam for later authority-bound runtime synthesis implementation."""

    raise ValueError("Korean frequency audio synthesis requires an authorized runtime")


def _validate_profile_authority_contract(
    authority: KoreanVoiceProfileAuthority,
    *,
    expected_hashes: Mapping[str, str],
) -> None:
    if authority.schema_version != _KOREAN_VOICE_PROFILE_AUTHORITY_SCHEMA_VERSION:
        raise ValueError("Korean voice profile authority schema drift")
    if authority.kind != _KOREAN_VOICE_PROFILE_KIND:
        raise ValueError("Korean voice profile authority kind drift")
    for field_name, expected in expected_hashes.items():
        if getattr(authority, field_name) != expected:
            if field_name == "provider_policy_sha256":
                raise ValueError("Korean voice profile provider policy drift")
            raise ValueError(f"Korean voice profile authority {field_name} drift")
    if authority.locale != KOREAN_PROVIDER_LOCALE:
        raise ValueError("Korean voice profile authority locale drift")
    if tuple(authority.usage_scope) != _KOREAN_VOICE_PROFILE_USAGE_SCOPE:
        raise ValueError("Korean voice profile authority must cover word and sentence usage scope")
    if tuple(authority.powers) != ("bind-voice-profile",):
        raise ValueError("Korean voice profile authority can only bind-voice-profile")
    if authority.catalog_query_count != 1:
        raise ValueError("Korean voice profile requires exactly one catalog query")
    if authority.catalog_synthesis_attempt_count != 0 or authority.synthesis_allowed:
        raise ValueError("Korean voice profile requires zero synthesis attempts")
    if authority.fallback_policy != _KOREAN_VOICE_PROFILE_FALLBACK_POLICY:
        raise ValueError("Korean voice profile fallback policy drift")
    if authority.grants_route_authority or not authority.grants_voice_profile_authority:
        raise ValueError("Korean voice profile authority grant drift")
    downstream_grants = (
        authority.grants_audio_authority,
        authority.grants_review_authority,
        authority.grants_export_authority,
        authority.grants_release_authority,
        authority.grants_publication_authority,
        authority.grants_delivery_authority,
    )
    if any(downstream_grants):
        raise ValueError("Korean voice profile authority grant drift")


def _validate_catalog_result_contract(
    catalog_result: Mapping[str, object],
    *,
    job_id: str,
    expected_hashes: Mapping[str, str],
) -> None:
    if _str_field(catalog_result, "schema_version", context="catalog") != "korean-azure-catalog-pilot-result-v1":
        raise ValueError("Korean voice profile catalog schema drift")
    if _str_field(catalog_result, "job_id", context="catalog") != job_id:
        raise ValueError("Korean voice profile catalog job drift")
    for field_name in (
        "provider_policy_sha256",
        "pilot_authority_sha256",
        "catalog_locator_sha256",
        "catalog_content_sha256",
    ):
        if _hash_field(catalog_result, field_name, context="catalog") != expected_hashes[field_name]:
            if field_name == "provider_policy_sha256":
                raise ValueError("Korean voice profile provider policy drift")
            raise ValueError(f"Korean voice profile catalog {field_name} drift")
    if _str_field(catalog_result, "catalog_locale", context="catalog") != KOREAN_PROVIDER_LOCALE:
        raise ValueError("Korean voice profile catalog locale drift")
    if _int_field(catalog_result, "catalog_query_count") != 1:
        raise ValueError("Korean voice profile requires exactly one catalog query")
    if _int_field(catalog_result, "synthesis_attempt_count") != 0:
        raise ValueError("Korean voice profile requires zero synthesis attempts")
    if _optional_int_field(catalog_result, "fallback_attempt_count", default=0) != 0:
        raise ValueError("Korean voice profile requires zero fallback attempts")
    if _bool_field(catalog_result, "production_database_used", default=False):
        raise ValueError("Korean voice profile cannot use production database evidence")
    for field_name in (
        "grants_route_authority",
        "grants_voice_profile_authority",
        "grants_audio_authority",
        "grants_review_authority",
        "grants_export_authority",
        "grants_release_authority",
        "grants_publication_authority",
        "grants_delivery_authority",
    ):
        if _bool_field(catalog_result, field_name, default=False):
            raise ValueError("Korean voice profile catalog grants downstream authority")


def _catalog_voice_mappings(catalog_result: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    voices = catalog_result.get("voices")
    if not isinstance(voices, (list, tuple)) or not voices:
        raise ValueError("Korean voice profile catalog voices are invalid")
    normalized: list[Mapping[str, object]] = []
    locale_set: set[str] = set()
    for voice in voices:
        if not isinstance(voice, Mapping):
            raise ValueError("Korean voice profile catalog voices are invalid")
        voice_id = voice.get("voice_id") or voice.get("short_name") or voice.get("ShortName")
        locale = voice.get("locale") or voice.get("Locale")
        region = voice.get("region")
        if not isinstance(voice_id, str) or not isinstance(locale, str) or not isinstance(region, str):
            raise ValueError("Korean voice profile catalog voices are invalid")
        locale_set.add(locale)
        if locale != KOREAN_PROVIDER_LOCALE or not voice_id.startswith("ko-KR-"):
            raise ValueError("Korean voice profile catalog locale drift")
        normalized.append(voice)
    if locale_set != {KOREAN_PROVIDER_LOCALE}:
        raise ValueError("Korean voice profile catalog locale drift")
    return tuple(normalized)


def _selected_catalog_voice(
    voices: tuple[Mapping[str, object], ...],
    *,
    selected_voice_id: str,
    region: str,
) -> Mapping[str, object]:
    for voice in voices:
        voice_id = voice.get("voice_id") or voice.get("short_name") or voice.get("ShortName")
        if voice_id == selected_voice_id and voice.get("region") == region:
            return voice
    raise ValueError("Korean voice profile selected voice is not present in catalog")


def _hash_field(payload: Mapping[str, object], field_name: str, *, context: str) -> str:
    return _sha256_identifier(_str_field(payload, field_name, context=context), field_name=field_name)


def _str_field(payload: Mapping[str, object], field_name: str, *, context: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Korean voice profile {context} {field_name} is invalid")
    return value


def _optional_str_field(payload: Mapping[str, object], field_name: str, *, default: str) -> str:
    value = payload.get(field_name, default)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Korean voice profile catalog {field_name} is invalid")
    return value


def _int_field(payload: Mapping[str, object], field_name: str) -> int:
    value = payload.get(field_name)
    if type(value) is not int or value < 0:
        raise ValueError(f"Korean voice profile catalog {field_name} is invalid")
    return value


def _optional_int_field(payload: Mapping[str, object], field_name: str, *, default: int) -> int:
    value = payload.get(field_name, default)
    if type(value) is not int or value < 0:
        raise ValueError(f"Korean voice profile catalog {field_name} is invalid")
    return value


def _bool_field(payload: Mapping[str, object], field_name: str, *, default: bool) -> bool:
    value = payload.get(field_name, default)
    if type(value) is not bool:
        raise ValueError(f"Korean voice profile catalog {field_name} is invalid")
    return value


def _validate_azure_catalog_endpoint(endpoint_url: str, *, region: str) -> None:
    parsed = urlparse(endpoint_url)
    if parsed.scheme != "https":
        raise ValueError("Azure catalog endpoint must use HTTPS")
    if parsed.netloc != f"{region}.tts.speech.microsoft.com":
        raise ValueError("Azure catalog endpoint host is not authorized")
    if parsed.path != "/cognitiveservices/voices/list" or parsed.params or parsed.query or parsed.fragment:
        raise ValueError("Azure catalog endpoint path is not authorized")


def _region_from_catalog_endpoint(endpoint_url: str) -> str:
    parsed = urlparse(endpoint_url)
    suffix = ".tts.speech.microsoft.com"
    if not parsed.netloc.endswith(suffix):
        raise ValueError("Azure catalog endpoint host is not authorized")
    region = parsed.netloc[: -len(suffix)]
    if not region:
        raise ValueError("Azure catalog endpoint host is not authorized")
    return region


def _verify_phase31_for_authority(
    authority: KoreanFrequencyJobAuthority,
    *,
    phase31_verifier: Callable[..., object],
) -> None:
    report = phase31_verifier(expected_receipt_sha256=authority.phase31_validation_receipt_sha256)
    expected = {
        "receipt_sha256": authority.phase31_validation_receipt_sha256,
        "snapshot_manifest_sha256": authority.phase31_snapshot_manifest_sha256,
        "snapshot_root_sha256": authority.phase31_snapshot_root_sha256,
    }
    for field, value in expected.items():
        if getattr(report, field, None) != value:
            raise ValueError("Phase 31 active authority drift")


def _sanitize_korean_catalog_voices(raw_catalog: object, *, region: str) -> list[dict[str, str]]:
    if not isinstance(raw_catalog, (list, tuple)):
        raise ValueError("Korean Azure catalog payload is invalid")
    voices: list[dict[str, str]] = []
    for item in raw_catalog:
        if isinstance(item, KoreanAzureCatalogVoice):
            short_name = item.short_name
            locale = item.locale
        elif isinstance(item, Mapping):
            short_name = item.get("ShortName") or item.get("short_name") or item.get("voice_id")
            locale = item.get("Locale") or item.get("locale")
        else:
            continue
        if not isinstance(short_name, str) or not isinstance(locale, str):
            continue
        if locale != KOREAN_PROVIDER_LOCALE or not short_name.startswith("ko-KR-"):
            continue
        voices.append({"voice_id": short_name, "locale": KOREAN_PROVIDER_LOCALE, "region": region})
    if not voices:
        raise ValueError("Korean Azure catalog did not include an available ko-KR voice")
    return voices


def _log_catalog_provider_call(
    provider_call_logger: object | None,
    *,
    job_id: str,
    authority: KoreanFrequencyJobAuthority,
    route_provider: str,
    route_model: str | None,
    status: str,
    latency_ms: int,
    error_code: str | None,
    error_summary: str | None,
    prompt_hash: str,
    response_hash: str | None,
    telemetry: dict[str, str],
) -> None:
    insert = getattr(provider_call_logger, "insert", None)
    if not callable(insert):
        return
    insert(
        ProviderCallLogCreate(
            job_id=job_id,
            item_key="catalog",
            operation=KoreanProviderTask.CATALOG.value,
            provider=route_provider,
            model=route_model,
            status=status,
            attempt=1,
            latency_ms=latency_ms,
            error_code=error_code,
            error_summary=error_summary,
            prompt_hash=prompt_hash,
            response_hash=response_hash,
            **telemetry,
        )
    )


def _elapsed_ms(started: float) -> int:
    return max(0, int((perf_counter() - started) * 1000))


def _select_korean_catalog_voice(
    voices: tuple[KoreanAzureCatalogVoice, ...],
    *,
    region: str,
) -> KoreanAzureCatalogVoice:
    for voice in voices:
        if voice.locale == KOREAN_PROVIDER_LOCALE and voice.region == region and voice.status == "available":
            return voice
    raise ValueError("Korean Azure catalog did not include an available ko-KR voice")


__all__ = [
    "KoreanAudioAuthority",
    "KoreanAzureCatalogResult",
    "KoreanAzureCatalogVoice",
    "KoreanVoiceProfile",
    "KoreanVoiceProfileAuthority",
    "KoreanVoiceProfileValidation",
    "build_korean_audio_asset",
    "build_korean_voice_profile_from_authority",
    "build_korean_tts_input",
    "capture_korean_azure_catalog",
    "capture_korean_azure_catalog_pilot",
    "korean_audio_asset_reusable",
    "synthesize_korean_frequency_audio",
]
