"""Licensed, exact-byte media gates for Korean foundation snapshots."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from enum import Enum
from hashlib import sha256
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import struct
from typing import Final, Literal, Protocol, Self, TypeAlias
import unicodedata
import wave

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from multilang.domain.korean import KOREAN_PROVIDER_LOCALE
from multilang.services.korean_curriculum import (
    CURRENT_KOREAN_FOUNDATION_CANDIDATE_PATH,
    KoreanConceptRegistry,
    KoreanCurriculumError,
    KoreanFoundationFamily,
    KoreanHangulSourceEntry,
    KoreanHangulSourcePack,
    KoreanPronunciationSourceEntry,
    KoreanPronunciationSourcePack,
    load_korean_current_foundation_bundle,
    load_korean_v1_foundation_bundle,
    validate_korean_foundation_pack,
)
from multilang.services.korean_foundation_snapshot import (
    ResolvedKoreanFoundationSnapshot,
    resolve_active_korean_foundation_snapshot,
)


DEFAULT_KOREAN_FOUNDATION_MEDIA_MANIFEST_PATH: Final = (
    CURRENT_KOREAN_FOUNDATION_CANDIDATE_PATH
)
_KOREAN_FOUNDATION_MEDIA_MANIFEST_V1_PATH: Final = (
    Path("data") / "korean_foundations" / "korean-foundations-v1-media.json"
)
_KOREAN_FOUNDATION_CURRENT_MEDIA_MEMBER: Final = (
    "korean-foundations-v2-media.json"
)
_MEDIA_MANIFEST_MAX_BYTES: Final = 4 * 1_048_576
_MAX_SLOTS: Final = 8_192
_MAX_IDENTIFIER_LENGTH: Final = 160
_MAX_TEXT_LENGTH: Final = 4_096
_MAX_MEDIA_BYTES: Final = 16 * 1_048_576
_LOWERCASE_HEX: Final = frozenset("0123456789abcdef")
_UNKNOWN_VALUES: Final = frozenset(
    {"unknown", "unresolved", "unspecified", "none", "null", "n/a", "na"}
)
_UNSAFE_TEXT_MARKERS: Final = (
    "<script",
    "</script",
    "javascript:",
    "data:text/html",
    "file://",
    "http://",
    "https://",
    "onerror=",
    "onload=",
    "onclick=",
    "[sound:",
    "[anki:play:",
    "\x00",
)

KoreanFoundationMediaStatus: TypeAlias = Literal[
    "needs_review",
    "approved",
    "rejected",
]
_MediaManifestVersion: TypeAlias = Literal[
    "korean-foundations-v1-media",
    "korean-foundations-v2-media",
]
_MediaKind: TypeAlias = Literal[
    "picture",
    "strokes",
    "gif",
    "audio",
    "letter_audio",
    "word_audio",
    "sentence_audio",
]
_OutputFormat: TypeAlias = Literal["png", "gif", "pcm_s16le_wav"]
_ReviewerRole: TypeAlias = Literal[
    "media-rights-reviewer",
    "media-integrity-reviewer",
    "audio-playback-reviewer",
    "korean-phonetics-specialist",
    "independent-native-speaker",
]

_AUDIO_KINDS: Final = frozenset(
    {"audio", "letter_audio", "word_audio", "sentence_audio"}
)
_FORMAT_BY_KIND: Final[dict[str, str]] = {
    "picture": "png",
    "strokes": "png",
    "gif": "gif",
    "audio": "pcm_s16le_wav",
    "letter_audio": "pcm_s16le_wav",
    "word_audio": "pcm_s16le_wav",
    "sentence_audio": "pcm_s16le_wav",
}
_EXTENSION_BY_FORMAT: Final = {
    "png": ".png",
    "gif": ".gif",
    "pcm_s16le_wav": ".wav",
}
_REQUIRED_IMAGE_ROLES: Final = (
    "media-rights-reviewer",
    "media-integrity-reviewer",
)
_REQUIRED_AUDIO_ROLES: Final = (
    *_REQUIRED_IMAGE_ROLES,
    "audio-playback-reviewer",
    "korean-phonetics-specialist",
    "independent-native-speaker",
)
_METADATA_HASH_FIELDS: Final = (
    "family",
    "item_key",
    "sequence",
    "slot_id",
    "media_kind",
    "required",
    "source_pack_version",
    "source_content_sha256",
    "basename",
    "storage_relpath",
    "output_format",
    "source_id",
    "source_version",
    "attribution",
    "license_id",
    "redistribution_disposition",
    "display_text",
    "spoken_text",
    "text_nfc",
    "display_text_sha256",
    "spoken_text_sha256",
    "text_nfc_sha256",
    "provider",
    "provider_version",
    "voice_id",
    "locale",
    "ssml_sha256",
    "prosody_sha256",
    "duration_ms",
    "artifact_sha256",
)
_MEDIA_MANIFEST_VERSION_BY_SOURCE_PACKS: Final[
    dict[tuple[str, str], _MediaManifestVersion]
] = {
    ("hangul-v1", "pronunciation-i-plus-1-v1"): "korean-foundations-v1-media",
    ("hangul-v2", "pronunciation-i-plus-1-v2"): "korean-foundations-v2-media",
}
_SOURCE_PACK_VERSIONS_BY_MEDIA_MANIFEST: Final[
    dict[_MediaManifestVersion, tuple[str, str]]
] = {
    manifest_version: source_versions
    for source_versions, manifest_version in _MEDIA_MANIFEST_VERSION_BY_SOURCE_PACKS.items()
}


class KoreanFoundationMediaReasonCode(str, Enum):
    """Content-free media failures at path, rights, byte, and review gates."""

    MANIFEST_MISSING = "manifest_missing"
    MANIFEST_MALFORMED = "manifest_malformed"
    MANIFEST_OVERSIZED = "manifest_oversized"
    MANIFEST_INVALID = "manifest_invalid"
    SOURCE_INVALID = "source_invalid"
    SOURCE_IDENTITY_MISMATCH = "source_identity_mismatch"
    SLOT_ORDER_MISMATCH = "slot_order_mismatch"
    MANIFEST_INTEGRITY_MISMATCH = "manifest_integrity_mismatch"
    CANDIDATE_MANIFEST_NOT_ACTIVE = "candidate_manifest_not_active"
    MEDIA_NOT_READY = "media_not_ready"
    UNSAFE_MEDIA_PATH = "unsafe_media_path"
    UNSAFE_FILESYSTEM_COMPONENT = "unsafe_filesystem_component"
    DUPLICATE_MEDIA_BASENAME = "duplicate_media_basename"
    UNMANIFESTED_MEDIA_MEMBER = "unmanifested_media_member"
    MEDIA_FILE_MISSING = "media_file_missing"
    MEDIA_FILE_EMPTY = "media_file_empty"
    MEDIA_HEADER_INVALID = "media_header_invalid"
    MEDIA_DURATION_MISMATCH = "media_duration_mismatch"
    MEDIA_FORMAT_MISMATCH = "media_format_mismatch"
    ARTIFACT_HASH_MISMATCH = "artifact_hash_mismatch"
    TEXT_BINDING_MISMATCH = "text_binding_mismatch"
    METADATA_BINDING_MISMATCH = "metadata_binding_mismatch"
    RIGHTS_METADATA_INVALID = "rights_metadata_invalid"
    REVIEWER_ROLE_INVALID = "reviewer_role_invalid"


class KoreanFoundationMediaError(ValueError):
    """Scanner-safe media failure with identifiers only, never content or paths."""

    def __init__(
        self,
        reason_code: KoreanFoundationMediaReasonCode,
        *,
        item_key: str | None = None,
        media_kind: str | None = None,
        field_name: str | None = None,
    ) -> None:
        self.reason_code = reason_code
        self.item_key = item_key
        self.media_kind = media_kind
        self.field_name = field_name
        parts = [reason_code.value]
        if item_key is not None:
            parts.append(f"item_key={item_key}")
        if media_kind is not None:
            parts.append(f"media_kind={media_kind}")
        if field_name is not None:
            parts.append(f"field={field_name}")
        super().__init__(" ".join(parts))


class _FrozenMediaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


def _identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a bounded identifier")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(normalized) > _MAX_IDENTIFIER_LENGTH
        or normalized.casefold() in _UNKNOWN_VALUES
        or not normalized[0].isalnum()
        or not all(
            character.isascii()
            and (character.isalnum() or character in "._:-")
            for character in normalized
        )
    ):
        raise ValueError(f"{field_name} must be a bounded identifier")
    return normalized


def _safe_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be bounded plain text")
    normalized = value.strip()
    folded = normalized.casefold()
    if (
        not normalized
        or normalized != value
        or len(normalized) > _MAX_TEXT_LENGTH
        or unicodedata.normalize("NFC", normalized) != normalized
        or any(marker in folded for marker in _UNSAFE_TEXT_MARKERS)
    ):
        raise ValueError(f"{field_name} must be bounded plain text")
    return normalized


def _sha256_text(value: str, *, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEX for character in value)
    ):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _text_sha256(value: str) -> str:
    return sha256(unicodedata.normalize("NFC", value).encode("utf-8")).hexdigest()


def _safe_media_relpath(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("media path must be snapshot-relative")
    if (
        not value
        or value != value.strip()
        or len(value) > 512
        or value.startswith(("/", "~"))
        or "\\" in value
        or ":" in value
        or "\x00" in value
        or "//" in value
    ):
        raise ValueError("media path must be snapshot-relative")
    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError("media path must be snapshot-relative")
    path = PurePosixPath(value)
    if path.is_absolute() or tuple(path.parts) != tuple(raw_parts):
        raise ValueError("media path must be snapshot-relative")
    if any(
        not all(
            character.isascii()
            and (character.isalnum() or character in "._-")
            for character in part
        )
        for part in path.parts
    ):
        raise ValueError("media path contains unsupported characters")
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


def korean_foundation_media_metadata_sha256(value: object) -> str:
    """Hash all media identity, rights, text, provider, format, and byte fields."""

    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    elif isinstance(value, dict):
        payload = value
    else:
        raise TypeError("media metadata hash input must be a model or mapping")
    return _canonical_sha256(
        {field_name: payload.get(field_name) for field_name in _METADATA_HASH_FIELDS}
    )


def korean_foundation_media_manifest_sha256(value: object) -> str:
    """Hash a complete media manifest without trusting its serialized hash field."""

    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    elif isinstance(value, dict):
        payload = deepcopy(value)
    else:
        raise TypeError("media manifest hash input must be a model or mapping")
    payload = deepcopy(payload)
    payload.pop("content_hash", None)
    return _canonical_sha256(payload)


class KoreanFoundationMediaReviewReceipt(_FrozenMediaModel):
    """One qualified human receipt bound to exact metadata and artifact hashes."""

    reviewer_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    reviewer_role: _ReviewerRole
    reviewed_at: str = Field(min_length=20, max_length=20)
    artifact_sha256: str = Field(min_length=64, max_length=64)
    metadata_sha256: str = Field(min_length=64, max_length=64)

    @field_validator("reviewer_id")
    @classmethod
    def reviewer_id_must_be_bounded(cls, value: str) -> str:
        return _identifier(value, field_name="reviewer id")

    @field_validator("artifact_sha256", "metadata_sha256")
    @classmethod
    def receipt_hashes_must_be_sha256(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "receipt hash"),
        )

    @field_validator("reviewed_at")
    @classmethod
    def reviewed_at_must_be_exact_utc(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as exc:
            raise ValueError("reviewed_at must be an exact UTC timestamp") from exc
        return value


class KoreanFoundationMediaSlot(_FrozenMediaModel):
    """One pending or fully hash-bound media slot for a source-pack item."""

    family: KoreanFoundationFamily
    item_key: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    sequence: int = Field(ge=1, le=_MAX_SLOTS)
    slot_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    media_kind: _MediaKind
    required: bool
    source_pack_version: str = Field(
        min_length=1,
        max_length=_MAX_IDENTIFIER_LENGTH,
    )
    source_content_sha256: str = Field(min_length=64, max_length=64)
    basename: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    storage_relpath: str = Field(min_length=1, max_length=512)
    output_format: _OutputFormat
    status: KoreanFoundationMediaStatus
    reason_code: Literal["media-evidence-required", "media-rejected"] | None = None
    source_id: str | None = Field(default=None, max_length=_MAX_IDENTIFIER_LENGTH)
    source_version: str | None = Field(default=None, max_length=_MAX_IDENTIFIER_LENGTH)
    attribution: str | None = Field(default=None, max_length=_MAX_TEXT_LENGTH)
    license_id: str | None = Field(default=None, max_length=_MAX_IDENTIFIER_LENGTH)
    redistribution_disposition: Literal["approved"] | None = None
    display_text: str | None = Field(default=None, max_length=_MAX_TEXT_LENGTH)
    spoken_text: str | None = Field(default=None, max_length=_MAX_TEXT_LENGTH)
    text_nfc: str | None = Field(default=None, max_length=_MAX_TEXT_LENGTH)
    display_text_sha256: str | None = Field(default=None, max_length=64)
    spoken_text_sha256: str | None = Field(default=None, max_length=64)
    text_nfc_sha256: str | None = Field(default=None, max_length=64)
    provider: str | None = Field(default=None, max_length=_MAX_IDENTIFIER_LENGTH)
    provider_version: str | None = Field(
        default=None,
        max_length=_MAX_IDENTIFIER_LENGTH,
    )
    voice_id: str | None = Field(default=None, max_length=_MAX_IDENTIFIER_LENGTH)
    locale: str | None = Field(default=None, max_length=_MAX_IDENTIFIER_LENGTH)
    ssml_sha256: str | None = Field(default=None, max_length=64)
    prosody_sha256: str | None = Field(default=None, max_length=64)
    duration_ms: int | None = Field(default=None, ge=1, le=30_000)
    artifact_sha256: str | None = Field(default=None, max_length=64)
    reviewed_artifact_sha256: str | None = Field(default=None, max_length=64)
    metadata_sha256: str | None = Field(default=None, max_length=64)
    reviewed_metadata_sha256: str | None = Field(default=None, max_length=64)
    review_receipts: tuple[KoreanFoundationMediaReviewReceipt, ...] = Field(
        default=(),
        max_length=8,
    )

    @field_validator(
        "item_key",
        "slot_id",
        "source_pack_version",
        "basename",
    )
    @classmethod
    def identity_fields_must_be_bounded(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "media identity"),
        )

    @field_validator(
        "source_id",
        "source_version",
        "license_id",
        "provider",
        "provider_version",
        "voice_id",
    )
    @classmethod
    def optional_identifiers_must_be_bounded(
        cls,
        value: str | None,
        info: object,
    ) -> str | None:
        if value is None:
            return None
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "media metadata identifier"),
        )

    @field_validator("locale")
    @classmethod
    def locale_must_use_canonical_provider_value(cls, value: str | None) -> str | None:
        if value is not None and value != KOREAN_PROVIDER_LOCALE:
            raise ValueError("locale must use the canonical Korean provider locale")
        return value

    @field_validator("attribution", "display_text", "spoken_text", "text_nfc")
    @classmethod
    def optional_text_must_be_safe(
        cls,
        value: str | None,
        info: object,
    ) -> str | None:
        if value is None:
            return None
        return _safe_text(
            value,
            field_name=getattr(info, "field_name", "media text"),
        )

    @field_validator(
        "source_content_sha256",
        "display_text_sha256",
        "spoken_text_sha256",
        "text_nfc_sha256",
        "ssml_sha256",
        "prosody_sha256",
        "artifact_sha256",
        "reviewed_artifact_sha256",
        "metadata_sha256",
        "reviewed_metadata_sha256",
    )
    @classmethod
    def hashes_must_be_lowercase_sha256(
        cls,
        value: str | None,
        info: object,
    ) -> str | None:
        if value is None:
            return None
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "media hash"),
        )

    @field_validator("storage_relpath")
    @classmethod
    def storage_path_must_be_safe(cls, value: str) -> str:
        return _safe_media_relpath(value)

    @model_validator(mode="after")
    def state_rights_text_metadata_and_roles_must_be_exact(self) -> Self:
        expected_format = _FORMAT_BY_KIND[self.media_kind]
        if self.output_format != expected_format:
            raise ValueError("media format does not match media kind")
        expected_basename = _basename_for_slot(self.slot_id, self.output_format)
        expected_relpath = _storage_relpath(
            self.family,
            expected_basename,
        )
        if self.basename != expected_basename or self.storage_relpath != expected_relpath:
            raise ValueError("media destination does not match slot identity")

        approval_fields = (
            self.source_id,
            self.source_version,
            self.attribution,
            self.license_id,
            self.redistribution_disposition,
            self.display_text,
            self.text_nfc,
            self.display_text_sha256,
            self.text_nfc_sha256,
            self.artifact_sha256,
            self.reviewed_artifact_sha256,
            self.metadata_sha256,
            self.reviewed_metadata_sha256,
        )
        if self.status != "approved":
            expected_reason = (
                "media-evidence-required"
                if self.status == "needs_review"
                else "media-rejected"
            )
            if self.reason_code != expected_reason:
                raise ValueError("blocking media requires its controlled reason")
            optional_approval_fields = (
                *approval_fields,
                self.spoken_text,
                self.spoken_text_sha256,
                self.provider,
                self.provider_version,
                self.voice_id,
                self.locale,
                self.ssml_sha256,
                self.prosody_sha256,
                self.duration_ms,
            )
            if any(value is not None for value in optional_approval_fields):
                raise ValueError("blocking media cannot carry approval metadata")
            if self.review_receipts:
                raise ValueError("blocking media cannot carry review receipts")
            return self

        if self.reason_code is not None or any(value is None for value in approval_fields):
            raise ValueError("approved media requires complete rights and hash metadata")
        if self.redistribution_disposition != "approved":
            raise ValueError("approved media requires redistribution approval")
        if self.display_text_sha256 != _text_sha256(self.display_text or ""):
            raise ValueError("display text hash does not match")
        if self.text_nfc != unicodedata.normalize(
            "NFC", self.spoken_text or self.display_text or ""
        ):
            raise ValueError("text_nfc does not match approved text")
        if self.text_nfc_sha256 != _text_sha256(self.text_nfc or ""):
            raise ValueError("NFC text hash does not match")
        if self.media_kind in _AUDIO_KINDS:
            if any(
                value is None
                for value in (
                    self.spoken_text,
                    self.spoken_text_sha256,
                    self.provider,
                    self.provider_version,
                    self.voice_id,
                    self.locale,
                    self.ssml_sha256,
                    self.prosody_sha256,
                    self.duration_ms,
                )
            ):
                raise ValueError("approved audio requires complete production metadata")
            if self.spoken_text_sha256 != _text_sha256(self.spoken_text or ""):
                raise ValueError("spoken text hash does not match")
            if (
                self.media_kind in {"audio", "letter_audio"}
                and self.spoken_text == self.display_text
            ):
                raise ValueError("raw display glyph or rule label cannot be approved audio")
        else:
            if any(
                value is not None
                for value in (
                    self.spoken_text,
                    self.spoken_text_sha256,
                    self.provider,
                    self.provider_version,
                    self.voice_id,
                    self.locale,
                    self.ssml_sha256,
                    self.prosody_sha256,
                    self.duration_ms,
                )
            ):
                raise ValueError("image media cannot carry audio metadata")

        if self.artifact_sha256 != self.reviewed_artifact_sha256:
            raise ValueError("reviewed artifact hash does not match artifact hash")
        expected_metadata_hash = korean_foundation_media_metadata_sha256(self)
        if (
            self.metadata_sha256 != expected_metadata_hash
            or self.reviewed_metadata_sha256 != expected_metadata_hash
        ):
            raise ValueError("reviewed metadata hash does not match exact metadata")

        required_roles = (
            _REQUIRED_AUDIO_ROLES
            if self.media_kind in _AUDIO_KINDS
            else _REQUIRED_IMAGE_ROLES
        )
        roles = tuple(receipt.reviewer_role for receipt in self.review_receipts)
        if roles != required_roles:
            raise ValueError("approved media requires every qualified reviewer role")
        if any(
            receipt.artifact_sha256 != self.artifact_sha256
            or receipt.metadata_sha256 != self.metadata_sha256
            for receipt in self.review_receipts
        ):
            raise ValueError("review receipt hashes do not match media")
        if self.media_kind in _AUDIO_KINDS:
            reviewer_by_role = {
                receipt.reviewer_role: receipt.reviewer_id
                for receipt in self.review_receipts
            }
            if (
                reviewer_by_role["korean-phonetics-specialist"]
                == reviewer_by_role["independent-native-speaker"]
            ):
                raise ValueError("specialist and native-speaker reviewers must differ")
        return self


class KoreanFoundationMediaManifest(_FrozenMediaModel):
    """Complete media-slot join for both Korean foundation candidate packs."""

    schema_version: Literal[1] = 1
    manifest_version: _MediaManifestVersion
    candidate_only: bool
    registry_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    registry_content_sha256: str = Field(min_length=64, max_length=64)
    hangul_source_pack_version: str = Field(
        min_length=1,
        max_length=_MAX_IDENTIFIER_LENGTH,
    )
    hangul_source_pack_sha256: str = Field(min_length=64, max_length=64)
    pronunciation_source_pack_version: str = Field(
        min_length=1,
        max_length=_MAX_IDENTIFIER_LENGTH,
    )
    pronunciation_source_pack_sha256: str = Field(min_length=64, max_length=64)
    slots: tuple[KoreanFoundationMediaSlot, ...] = Field(
        min_length=1,
        max_length=_MAX_SLOTS,
    )
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator(
        "registry_version",
        "hangul_source_pack_version",
        "pronunciation_source_pack_version",
    )
    @classmethod
    def versions_must_be_bounded(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "media manifest version"),
        )

    @field_validator(
        "registry_content_sha256",
        "hangul_source_pack_sha256",
        "pronunciation_source_pack_sha256",
        "content_hash",
    )
    @classmethod
    def hashes_must_be_sha256(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "media manifest hash"),
        )

    @model_validator(mode="after")
    def order_uniqueness_and_hash_must_be_deterministic(self) -> Self:
        expected_hangul_version, expected_pronunciation_version = (
            _SOURCE_PACK_VERSIONS_BY_MEDIA_MANIFEST[self.manifest_version]
        )
        if (
            self.hangul_source_pack_version != expected_hangul_version
            or self.pronunciation_source_pack_version != expected_pronunciation_version
        ):
            raise ValueError("media manifest source versions are mixed")
        slot_ids = tuple(slot.slot_id for slot in self.slots)
        basenames = tuple(slot.basename for slot in self.slots)
        relpaths = tuple(slot.storage_relpath for slot in self.slots)
        for slot in self.slots:
            expected_version = (
                expected_hangul_version
                if slot.family is KoreanFoundationFamily.HANGUL
                else expected_pronunciation_version
            )
            if slot.source_pack_version != expected_version:
                raise ValueError("media slot source version is mixed")
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("media slot ids must be unique")
        if len(basenames) != len(set(basenames)):
            raise ValueError("media basenames must be unique")
        if len(relpaths) != len(set(relpaths)):
            raise ValueError("media storage paths must be unique")
        if self.content_hash != korean_foundation_media_manifest_sha256(self):
            raise ValueError("media manifest content hash does not match")
        return self


class _MediaSnapshot(Protocol):
    concept_registry: KoreanConceptRegistry
    hangul_source_pack: KoreanHangulSourcePack
    pronunciation_source_pack: KoreanPronunciationSourcePack
    snapshot_root: Path
    media_root: Path
    media_manifest_bytes: bytes
    media_members: tuple[object, ...]


def _raise(
    reason_code: KoreanFoundationMediaReasonCode,
    *,
    slot: KoreanFoundationMediaSlot | None = None,
    field_name: str | None = None,
) -> None:
    raise KoreanFoundationMediaError(
        reason_code,
        item_key=slot.item_key if slot is not None else None,
        media_kind=slot.media_kind if slot is not None else None,
        field_name=field_name,
    )


def _basename_for_slot(slot_id: str, output_format: str) -> str:
    return f"{slot_id.replace('.', '-').replace('_', '-')}" f"{_EXTENSION_BY_FORMAT[output_format]}"


def _storage_relpath(family: KoreanFoundationFamily, basename: str) -> str:
    return f"media/{family.value}/{basename}"


def _build_pending_korean_foundation_media_manifest(
    *,
    registry: KoreanConceptRegistry,
    hangul_pack: KoreanHangulSourcePack,
    pronunciation_pack: KoreanPronunciationSourcePack,
) -> KoreanFoundationMediaManifest:
    source_versions = (
        hangul_pack.source_pack_version,
        pronunciation_pack.source_pack_version,
    )
    try:
        manifest_version = _MEDIA_MANIFEST_VERSION_BY_SOURCE_PACKS[source_versions]
    except KeyError as exc:
        raise ValueError("unsupported Korean foundation source-pack tuple") from exc
    slots: list[KoreanFoundationMediaSlot] = []
    slot_sequence = 0
    for pack in (hangul_pack, pronunciation_pack):
        for entry in pack.entries:
            for source_slot in entry.media_slots:
                slot_sequence += 1
                output_format = _FORMAT_BY_KIND[source_slot.media_kind]
                basename = _basename_for_slot(source_slot.slot_id, output_format)
                slots.append(
                    KoreanFoundationMediaSlot(
                        family=pack.family,
                        item_key=entry.item_key,
                        sequence=slot_sequence,
                        slot_id=source_slot.slot_id,
                        media_kind=source_slot.media_kind,
                        required=source_slot.required,
                        source_pack_version=pack.source_pack_version,
                        source_content_sha256=entry.content_hash,
                        basename=basename,
                        storage_relpath=_storage_relpath(pack.family, basename),
                        output_format=output_format,
                        status="needs_review",
                        reason_code="media-evidence-required",
                    )
                )
    payload: dict[str, object] = {
        "schema_version": 1,
        "manifest_version": manifest_version,
        "candidate_only": True,
        "registry_version": registry.registry_version,
        "registry_content_sha256": registry.content_hash,
        "hangul_source_pack_version": hangul_pack.source_pack_version,
        "hangul_source_pack_sha256": hangul_pack.content_hash,
        "pronunciation_source_pack_version": pronunciation_pack.source_pack_version,
        "pronunciation_source_pack_sha256": pronunciation_pack.content_hash,
        "slots": [slot.model_dump(mode="json") for slot in slots],
    }
    payload["content_hash"] = korean_foundation_media_manifest_sha256(payload)
    return KoreanFoundationMediaManifest.model_validate(payload)


def _load_media_manifest_bytes(raw: bytes) -> KoreanFoundationMediaManifest:
    try:
        payload = json.loads(raw.decode("utf-8"))
        return KoreanFoundationMediaManifest.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KoreanFoundationMediaError(
            KoreanFoundationMediaReasonCode.MANIFEST_MALFORMED
        ) from exc
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationMediaError(
            KoreanFoundationMediaReasonCode.MANIFEST_INVALID
        ) from exc


def _load_media_manifest_file(path: Path) -> KoreanFoundationMediaManifest:
    try:
        size = path.stat().st_size
    except FileNotFoundError as exc:
        raise KoreanFoundationMediaError(
            KoreanFoundationMediaReasonCode.MANIFEST_MISSING
        ) from exc
    except OSError as exc:
        raise KoreanFoundationMediaError(
            KoreanFoundationMediaReasonCode.MANIFEST_MALFORMED
        ) from exc
    if size > _MEDIA_MANIFEST_MAX_BYTES:
        _raise(KoreanFoundationMediaReasonCode.MANIFEST_OVERSIZED)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise KoreanFoundationMediaError(
            KoreanFoundationMediaReasonCode.MANIFEST_MALFORMED
        ) from exc
    if len(raw) > _MEDIA_MANIFEST_MAX_BYTES:
        _raise(KoreanFoundationMediaReasonCode.MANIFEST_OVERSIZED)
    return _load_media_manifest_bytes(raw)


def _assert_member_file_hash(path: Path, expected_hash: str) -> None:
    try:
        actual_hash = sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise KoreanFoundationMediaError(
            KoreanFoundationMediaReasonCode.MANIFEST_MALFORMED
        ) from exc
    if actual_hash != expected_hash:
        _raise(KoreanFoundationMediaReasonCode.MANIFEST_INTEGRITY_MISMATCH)


def _expected_slot_rows(
    hangul_pack: KoreanHangulSourcePack,
    pronunciation_pack: KoreanPronunciationSourcePack,
) -> tuple[tuple[object, object, int], ...]:
    rows: list[tuple[object, object, int]] = []
    sequence = 0
    for pack in (hangul_pack, pronunciation_pack):
        for entry in pack.entries:
            for source_slot in entry.media_slots:
                sequence += 1
                rows.append((entry, source_slot, sequence))
    return tuple(rows)


def _validate_source_alignment(
    manifest: KoreanFoundationMediaManifest,
    *,
    registry: KoreanConceptRegistry,
    hangul_pack: KoreanHangulSourcePack,
    pronunciation_pack: KoreanPronunciationSourcePack,
) -> tuple[tuple[object, object, int], ...]:
    try:
        validate_korean_foundation_pack(registry=registry, pack=hangul_pack)
        validate_korean_foundation_pack(
            registry=registry,
            pack=pronunciation_pack,
            inherited_known_ids=pronunciation_pack.inherited_orthographic_concept_ids,
        )
    except (KoreanCurriculumError, ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationMediaError(
            KoreanFoundationMediaReasonCode.SOURCE_INVALID
        ) from exc
    expected_identity = (
        registry.registry_version,
        registry.content_hash,
        hangul_pack.source_pack_version,
        hangul_pack.content_hash,
        pronunciation_pack.source_pack_version,
        pronunciation_pack.content_hash,
    )
    actual_identity = (
        manifest.registry_version,
        manifest.registry_content_sha256,
        manifest.hangul_source_pack_version,
        manifest.hangul_source_pack_sha256,
        manifest.pronunciation_source_pack_version,
        manifest.pronunciation_source_pack_sha256,
    )
    if actual_identity != expected_identity:
        _raise(KoreanFoundationMediaReasonCode.SOURCE_IDENTITY_MISMATCH)
    rows = _expected_slot_rows(hangul_pack, pronunciation_pack)
    if len(rows) != len(manifest.slots):
        _raise(KoreanFoundationMediaReasonCode.SLOT_ORDER_MISMATCH)
    return rows


def load_pending_korean_foundation_media_manifest() -> KoreanFoundationMediaManifest:
    """Load the fixed current-candidate bundle media member."""

    bundle = load_korean_current_foundation_bundle()
    manifest_path = Path(bundle.source_root) / _KOREAN_FOUNDATION_CURRENT_MEDIA_MEMBER
    _assert_member_file_hash(
        manifest_path,
        bundle.member_file_sha256[_KOREAN_FOUNDATION_CURRENT_MEDIA_MEMBER],
    )
    manifest = _load_media_manifest_file(manifest_path)
    if not manifest.candidate_only:
        _raise(KoreanFoundationMediaReasonCode.MANIFEST_INVALID)
    rows = _validate_source_alignment(
        manifest,
        registry=bundle.registry,
        hangul_pack=bundle.hangul,
        pronunciation_pack=bundle.pronunciation,
    )
    for slot, (entry, source_slot, sequence) in zip(
        manifest.slots,
        rows,
        strict=True,
    ):
        _validate_slot_source_identity(slot, entry, source_slot, sequence)
        if slot.status != "needs_review":
            _raise(KoreanFoundationMediaReasonCode.MANIFEST_INVALID)
    if manifest.content_hash != korean_foundation_media_manifest_sha256(manifest):
        _raise(KoreanFoundationMediaReasonCode.MANIFEST_INTEGRITY_MISMATCH)
    return manifest


def load_korean_v1_foundation_media_manifest() -> KoreanFoundationMediaManifest:
    """Load the immutable v1 media manifest explicitly for history."""

    bundle = load_korean_v1_foundation_bundle()
    manifest = _load_media_manifest_file(_KOREAN_FOUNDATION_MEDIA_MANIFEST_V1_PATH)
    _validate_source_alignment(
        manifest,
        registry=bundle.registry,
        hangul_pack=bundle.hangul,
        pronunciation_pack=bundle.pronunciation,
    )
    return manifest


def _validate_slot_source_identity(
    slot: KoreanFoundationMediaSlot,
    entry: object,
    source_slot: object,
    sequence: int,
) -> None:
    expected = (
        entry.family,
        entry.item_key,
        sequence,
        source_slot.slot_id,
        source_slot.media_kind,
        source_slot.required,
        entry.source_pack_version,
        entry.content_hash,
    )
    actual = (
        slot.family,
        slot.item_key,
        slot.sequence,
        slot.slot_id,
        slot.media_kind,
        slot.required,
        slot.source_pack_version,
        slot.source_content_sha256,
    )
    if actual != expected:
        _raise(KoreanFoundationMediaReasonCode.SOURCE_IDENTITY_MISMATCH, slot=slot)


def _expected_display_text(
    slot: KoreanFoundationMediaSlot,
    entry: KoreanHangulSourceEntry | KoreanPronunciationSourceEntry,
) -> str:
    if slot.family is KoreanFoundationFamily.HANGUL:
        assert isinstance(entry, KoreanHangulSourceEntry)
        mapping = entry.pedagogical_jamo_mapping
        return mapping.display_glyph if mapping is not None else entry.canonical_jamo_or_block
    assert isinstance(entry, KoreanPronunciationSourceEntry)
    if slot.media_kind == "letter_audio":
        return entry.spellings
    if slot.media_kind == "word_audio":
        return entry.example_word
    return entry.example_sentence


def _validate_slot_contract(
    slot: KoreanFoundationMediaSlot,
    *,
    entry: KoreanHangulSourceEntry | KoreanPronunciationSourceEntry,
) -> None:
    try:
        _safe_media_relpath(slot.storage_relpath)
    except ValueError:
        _raise(
            KoreanFoundationMediaReasonCode.UNSAFE_MEDIA_PATH,
            slot=slot,
            field_name="storage_relpath",
        )
    expected_format = _FORMAT_BY_KIND.get(slot.media_kind)
    if slot.output_format != expected_format:
        _raise(
            KoreanFoundationMediaReasonCode.MEDIA_FORMAT_MISMATCH,
            slot=slot,
            field_name="output_format",
        )
    expected_basename = _basename_for_slot(slot.slot_id, slot.output_format)
    if (
        slot.basename != expected_basename
        or slot.storage_relpath != _storage_relpath(slot.family, expected_basename)
    ):
        _raise(
            KoreanFoundationMediaReasonCode.UNSAFE_MEDIA_PATH,
            slot=slot,
            field_name="storage_relpath",
        )
    if slot.status != "approved":
        return
    expected_display = _expected_display_text(slot, entry)
    if (
        slot.display_text != expected_display
        or slot.display_text_sha256 != _text_sha256(expected_display)
        or slot.text_nfc != unicodedata.normalize(
            "NFC", slot.spoken_text or expected_display
        )
        or slot.text_nfc_sha256 != _text_sha256(slot.text_nfc or "")
        or (
            slot.spoken_text is not None
            and slot.spoken_text_sha256 != _text_sha256(slot.spoken_text)
        )
    ):
        _raise(KoreanFoundationMediaReasonCode.TEXT_BINDING_MISMATCH, slot=slot)
    if (
        slot.artifact_sha256 is None
        or slot.reviewed_artifact_sha256 != slot.artifact_sha256
    ):
        _raise(KoreanFoundationMediaReasonCode.ARTIFACT_HASH_MISMATCH, slot=slot)
    expected_metadata = korean_foundation_media_metadata_sha256(slot)
    if (
        slot.metadata_sha256 != expected_metadata
        or slot.reviewed_metadata_sha256 != expected_metadata
    ):
        _raise(KoreanFoundationMediaReasonCode.METADATA_BINDING_MISMATCH, slot=slot)
    try:
        KoreanFoundationMediaSlot.model_validate(slot.model_dump(mode="json"))
    except ValidationError as exc:
        errors = exc.errors()
        locations = {error.get("loc", (None,))[0] for error in errors}
        if locations & {
            "source_id",
            "source_version",
            "attribution",
            "license_id",
            "redistribution_disposition",
        }:
            reason = KoreanFoundationMediaReasonCode.RIGHTS_METADATA_INVALID
        elif "review_receipts" in locations:
            reason = KoreanFoundationMediaReasonCode.REVIEWER_ROLE_INVALID
        else:
            reason = KoreanFoundationMediaReasonCode.METADATA_BINDING_MISMATCH
        raise KoreanFoundationMediaError(
            reason,
            item_key=slot.item_key,
            media_kind=slot.media_kind,
        ) from exc


def _stat_is_link_or_reparse(stat_result: os.stat_result) -> bool:
    if stat.S_ISLNK(stat_result.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(stat_result, "st_file_attributes", 0) & reparse_flag)


def _read_exact_media_file(
    slot: KoreanFoundationMediaSlot,
    *,
    snapshot: _MediaSnapshot,
) -> bytes:
    expected_path = snapshot.snapshot_root.joinpath(
        *PurePosixPath(slot.storage_relpath).parts
    )
    try:
        expected_path.relative_to(snapshot.media_root)
    except ValueError:
        _raise(KoreanFoundationMediaReasonCode.UNSAFE_MEDIA_PATH, slot=slot)
    current = snapshot.snapshot_root
    try:
        root_stat = current.lstat()
    except OSError:
        _raise(KoreanFoundationMediaReasonCode.MEDIA_FILE_MISSING, slot=slot)
    if _stat_is_link_or_reparse(root_stat):
        _raise(KoreanFoundationMediaReasonCode.UNSAFE_FILESYSTEM_COMPONENT, slot=slot)
    for part in PurePosixPath(slot.storage_relpath).parts:
        current = current / part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            _raise(KoreanFoundationMediaReasonCode.MEDIA_FILE_MISSING, slot=slot)
        except OSError:
            _raise(
                KoreanFoundationMediaReasonCode.UNSAFE_FILESYSTEM_COMPONENT,
                slot=slot,
            )
        if _stat_is_link_or_reparse(current_stat):
            _raise(
                KoreanFoundationMediaReasonCode.UNSAFE_FILESYSTEM_COMPONENT,
                slot=slot,
            )
    if not stat.S_ISREG(current_stat.st_mode):
        _raise(KoreanFoundationMediaReasonCode.UNSAFE_FILESYSTEM_COMPONENT, slot=slot)
    if current_stat.st_size <= 0:
        _raise(KoreanFoundationMediaReasonCode.MEDIA_FILE_EMPTY, slot=slot)
    if current_stat.st_size > _MAX_MEDIA_BYTES:
        _raise(KoreanFoundationMediaReasonCode.MEDIA_FORMAT_MISMATCH, slot=slot)
    try:
        with expected_path.open("rb") as handle:
            content = handle.read(_MAX_MEDIA_BYTES + 1)
    except OSError:
        _raise(KoreanFoundationMediaReasonCode.MEDIA_FILE_MISSING, slot=slot)
    if not content:
        _raise(KoreanFoundationMediaReasonCode.MEDIA_FILE_EMPTY, slot=slot)
    if len(content) > _MAX_MEDIA_BYTES:
        _raise(KoreanFoundationMediaReasonCode.MEDIA_FORMAT_MISMATCH, slot=slot)
    actual_hash = sha256(content).hexdigest()
    if (
        actual_hash != slot.artifact_sha256
        or actual_hash != slot.reviewed_artifact_sha256
    ):
        _raise(KoreanFoundationMediaReasonCode.ARTIFACT_HASH_MISMATCH, slot=slot)
    _validate_header_and_duration(slot, content)
    return content


def _validate_header_and_duration(
    slot: KoreanFoundationMediaSlot,
    content: bytes,
) -> None:
    if slot.output_format == "pcm_s16le_wav":
        try:
            with wave.open(io.BytesIO(content), "rb") as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                frame_count = wav_file.getnframes()
                compression = wav_file.getcomptype()
        except (EOFError, wave.Error) as exc:
            raise KoreanFoundationMediaError(
                KoreanFoundationMediaReasonCode.MEDIA_HEADER_INVALID,
                item_key=slot.item_key,
                media_kind=slot.media_kind,
            ) from exc
        if (
            compression != "NONE"
            or channels not in {1, 2}
            or sample_width != 2
            or not 8_000 <= frame_rate <= 96_000
            or frame_count <= 0
        ):
            _raise(KoreanFoundationMediaReasonCode.MEDIA_HEADER_INVALID, slot=slot)
        duration_ms = round(frame_count * 1_000 / frame_rate)
        if duration_ms != slot.duration_ms:
            _raise(KoreanFoundationMediaReasonCode.MEDIA_DURATION_MISMATCH, slot=slot)
        return
    if slot.output_format == "png":
        if (
            len(content) < 33
            or not content.startswith(b"\x89PNG\r\n\x1a\n")
            or content[12:16] != b"IHDR"
            or not content.endswith(b"IEND\xaeB`\x82")
        ):
            _raise(KoreanFoundationMediaReasonCode.MEDIA_HEADER_INVALID, slot=slot)
        width, height = struct.unpack(">II", content[16:24])
        if not 1 <= width <= 8_192 or not 1 <= height <= 8_192:
            _raise(KoreanFoundationMediaReasonCode.MEDIA_HEADER_INVALID, slot=slot)
        return
    if slot.output_format == "gif":
        if len(content) < 10 or content[:6] not in {b"GIF87a", b"GIF89a"}:
            _raise(KoreanFoundationMediaReasonCode.MEDIA_HEADER_INVALID, slot=slot)
        width, height = struct.unpack("<HH", content[6:10])
        if not 1 <= width <= 8_192 or not 1 <= height <= 8_192:
            _raise(KoreanFoundationMediaReasonCode.MEDIA_HEADER_INVALID, slot=slot)
        return
    _raise(KoreanFoundationMediaReasonCode.MEDIA_FORMAT_MISMATCH, slot=slot)


def validate_korean_foundation_media_manifest(
    manifest: KoreanFoundationMediaManifest,
    *,
    snapshot: _MediaSnapshot,
) -> None:
    """Validate one snapshot's exact source/slot/media join without rereading activation."""

    rows = _validate_source_alignment(
        manifest,
        registry=snapshot.concept_registry,
        hangul_pack=snapshot.hangul_source_pack,
        pronunciation_pack=snapshot.pronunciation_source_pack,
    )
    basenames = tuple(slot.basename for slot in manifest.slots)
    if len(basenames) != len(set(basenames)):
        _raise(KoreanFoundationMediaReasonCode.DUPLICATE_MEDIA_BASENAME)
    for slot, (entry, source_slot, sequence) in zip(
        manifest.slots,
        rows,
        strict=True,
    ):
        _validate_slot_source_identity(slot, entry, source_slot, sequence)
        _validate_slot_contract(slot, entry=entry)

    approved_relpaths = {
        slot.storage_relpath
        for slot in manifest.slots
        if slot.status == "approved"
    }
    member_relpaths = {member.relpath for member in snapshot.media_members}
    if member_relpaths - approved_relpaths:
        _raise(KoreanFoundationMediaReasonCode.UNMANIFESTED_MEDIA_MEMBER)

    member_by_relpath = {member.relpath: member for member in snapshot.media_members}
    for slot in manifest.slots:
        if slot.required and slot.status != "approved":
            _raise(KoreanFoundationMediaReasonCode.MEDIA_NOT_READY, slot=slot)
        if slot.status != "approved":
            continue
        member = member_by_relpath.get(slot.storage_relpath)
        if member is None:
            _raise(KoreanFoundationMediaReasonCode.MEDIA_FILE_MISSING, slot=slot)
        content = _read_exact_media_file(slot, snapshot=snapshot)
        actual_hash = sha256(content).hexdigest()
        if (
            member.path
            != snapshot.snapshot_root.joinpath(
                *PurePosixPath(slot.storage_relpath).parts
            )
            or member.sha256 != actual_hash
            or member.size_bytes != len(content)
            or member.content != content
        ):
            _raise(KoreanFoundationMediaReasonCode.ARTIFACT_HASH_MISMATCH, slot=slot)
    if approved_relpaths - member_relpaths:
        _raise(KoreanFoundationMediaReasonCode.MEDIA_FILE_MISSING)
    if manifest.content_hash != korean_foundation_media_manifest_sha256(manifest):
        _raise(KoreanFoundationMediaReasonCode.MANIFEST_INTEGRITY_MISMATCH)


def _manifest_from_snapshot(snapshot: _MediaSnapshot) -> KoreanFoundationMediaManifest:
    if len(snapshot.media_manifest_bytes) > _MEDIA_MANIFEST_MAX_BYTES:
        _raise(KoreanFoundationMediaReasonCode.MANIFEST_OVERSIZED)
    return _load_media_manifest_bytes(snapshot.media_manifest_bytes)


def assert_korean_foundation_media_ready(snapshot: _MediaSnapshot) -> None:
    """Fail closed unless every required slot in one resolved snapshot is ready."""

    manifest = _manifest_from_snapshot(snapshot)
    if manifest.candidate_only:
        rows = _validate_source_alignment(
            manifest,
            registry=snapshot.concept_registry,
            hangul_pack=snapshot.hangul_source_pack,
            pronunciation_pack=snapshot.pronunciation_source_pack,
        )
        for slot, (entry, source_slot, sequence) in zip(
            manifest.slots,
            rows,
            strict=True,
        ):
            _validate_slot_source_identity(slot, entry, source_slot, sequence)
        _raise(KoreanFoundationMediaReasonCode.CANDIDATE_MANIFEST_NOT_ACTIVE)
    validate_korean_foundation_media_manifest(manifest, snapshot=snapshot)


def resolve_korean_foundation_media(snapshot: _MediaSnapshot) -> tuple[Path, ...]:
    """Return exact required media paths only after one snapshot passes every gate."""

    assert_korean_foundation_media_ready(snapshot)
    manifest = _manifest_from_snapshot(snapshot)
    return tuple(
        snapshot.snapshot_root.joinpath(*PurePosixPath(slot.storage_relpath).parts)
        for slot in manifest.slots
        if slot.required
    )


def assert_active_korean_foundation_media_ready() -> None:
    """Resolve the fixed active pointer once and assert media readiness."""

    snapshot = resolve_active_korean_foundation_snapshot()
    assert_korean_foundation_media_ready(snapshot)


def resolve_active_korean_foundation_media() -> tuple[Path, ...]:
    """Resolve the fixed active pointer once and return its exact approved media."""

    snapshot = resolve_active_korean_foundation_snapshot()
    return resolve_korean_foundation_media(snapshot)


__all__ = [
    "DEFAULT_KOREAN_FOUNDATION_MEDIA_MANIFEST_PATH",
    "KoreanFoundationMediaError",
    "KoreanFoundationMediaManifest",
    "KoreanFoundationMediaReasonCode",
    "KoreanFoundationMediaReviewReceipt",
    "KoreanFoundationMediaSlot",
    "KoreanFoundationMediaStatus",
    "assert_active_korean_foundation_media_ready",
    "assert_korean_foundation_media_ready",
    "korean_foundation_media_manifest_sha256",
    "korean_foundation_media_metadata_sha256",
    "load_korean_v1_foundation_media_manifest",
    "load_pending_korean_foundation_media_manifest",
    "resolve_active_korean_foundation_media",
    "resolve_korean_foundation_media",
    "validate_korean_foundation_media_manifest",
]
