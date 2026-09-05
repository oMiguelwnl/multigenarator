"""Korean Azure catalog, SSML, audio identity, and reuse contracts."""

from __future__ import annotations

from hashlib import sha256
from html import escape
import json
from pathlib import Path
from typing import Callable, Literal
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
from multilang.domain.korean import KOREAN_PROVIDER_LOCALE
from multilang.services.korean_foundation_snapshot import verify_active_korean_foundation_snapshot_provenance


_HEX = frozenset("0123456789abcdef")


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


class KoreanVoiceProfile(_FrozenModel):
    voice_id: str = Field(min_length=1, max_length=160)
    locale: Literal["ko-KR"]
    region: str = Field(min_length=1, max_length=64)
    provider_sdk_version: str = Field(min_length=1, max_length=64)
    catalog_receipt_sha256: str = Field(min_length=64, max_length=64)
    profile_authority_sha256: str = Field(min_length=64, max_length=64)
    profile_sha256: str = Field(min_length=64, max_length=64)

    @field_validator("catalog_receipt_sha256", "profile_authority_sha256", "profile_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
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


def _validate_azure_catalog_endpoint(endpoint_url: str, *, region: str) -> None:
    parsed = urlparse(endpoint_url)
    if parsed.scheme != "https":
        raise ValueError("Azure catalog endpoint must use HTTPS")
    if parsed.netloc != f"{region}.tts.speech.microsoft.com":
        raise ValueError("Azure catalog endpoint host is not authorized")
    if parsed.path != "/cognitiveservices/voices/list" or parsed.params or parsed.query or parsed.fragment:
        raise ValueError("Azure catalog endpoint path is not authorized")


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
    "build_korean_audio_asset",
    "build_korean_tts_input",
    "capture_korean_azure_catalog",
    "korean_audio_asset_reusable",
    "synthesize_korean_frequency_audio",
]
