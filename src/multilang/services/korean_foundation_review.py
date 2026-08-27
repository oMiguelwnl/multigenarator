"""Independent, hash-bound review gates for Korean foundation snapshots."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
from typing import Final, Literal, Protocol, Self, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from multilang.services.korean_curriculum import (
    CURRENT_KOREAN_FOUNDATION_CANDIDATE_PATH,
    KoreanConceptRegistry,
    KoreanCurriculumError,
    KoreanFoundationFamily,
    KoreanHangulSourcePack,
    KoreanPronunciationSourcePack,
    load_korean_current_foundation_bundle,
    load_korean_v1_foundation_bundle,
    validate_korean_foundation_pack,
)


DEFAULT_KOREAN_FOUNDATION_CURATION_PATH: Final = (
    CURRENT_KOREAN_FOUNDATION_CANDIDATE_PATH
)
_KOREAN_FOUNDATION_CURATION_V1_PATH: Final = (
    Path("data")
    / "korean_foundations"
    / "korean-foundations-v1-curation.json"
)
_KOREAN_FOUNDATION_CURRENT_CURATION_MEMBER: Final = (
    "korean-foundations-v2-curation.json"
)
_CURATION_MAX_BYTES: Final = 1_048_576
_MAX_RECORDS: Final = 4_096
_MAX_IDENTIFIER_LENGTH: Final = 128
_LOWERCASE_HEX: Final = frozenset("0123456789abcdef")

KoreanFoundationReviewStatus: TypeAlias = Literal[
    "needs_review",
    "approved",
    "ai_review_passed",
    "rejected",
]
_CurationManifestVersion: TypeAlias = Literal[
    "korean-foundations-v1-curation",
    "korean-foundations-v2-curation",
]
_ReviewGateName: TypeAlias = Literal[
    "source_content",
    "curriculum_atomicity",
    "korean_orthography",
    "korean_phonetics",
    "portuguese",
    "media_license",
    "media_integrity",
    "audio_playback",
]

KOREAN_FOUNDATION_GATE_REVIEWER_ROLES: Final[dict[str, str]] = {
    "source_content": "korean-foundation-content-reviewer",
    "curriculum_atomicity": "korean-curriculum-reviewer",
    "korean_orthography": "korean-orthography-reviewer",
    "korean_phonetics": "korean-phonetics-specialist",
    "portuguese": "portuguese-reviewer",
    "media_license": "media-rights-reviewer",
    "media_integrity": "media-integrity-reviewer",
    "audio_playback": "audio-playback-reviewer",
}

_PENDING_REASON_BY_GATE: Final[dict[str, str]] = {
    "source_content": "source-content-review-required",
    "curriculum_atomicity": "curriculum-atomicity-review-required",
    "korean_orthography": "korean-orthography-review-required",
    "korean_phonetics": "korean-phonetics-review-required",
    "portuguese": "portuguese-review-required",
    "media_license": "media-license-review-required",
    "media_integrity": "media-integrity-review-required",
    "audio_playback": "audio-playback-review-required",
}
_REJECTED_REASON_BY_GATE: Final[dict[str, str]] = {
    gate_name: pending_reason.replace("review-required", "rejected")
    for gate_name, pending_reason in _PENDING_REASON_BY_GATE.items()
}

_HANGUL_GATE_SCOPES: Final[dict[str, tuple[str, ...]]] = {
    "source_content": (
        "mapping",
        "name-or-reading",
        "block-or-example",
        "stroke-order",
        "mnemonic",
    ),
    "curriculum_atomicity": (
        "target-concept",
        "prerequisites",
        "observed-concepts",
        "one-target-unknown",
    ),
    "korean_orthography": (
        "canonical-jamo-or-block",
        "pedagogical-jamo-mapping",
        "orthographic-example",
    ),
    "portuguese": ("learner-facing-portuguese",),
    "media_license": ("all-declared-media-rights",),
    "media_integrity": ("all-required-media-slots",),
    "audio_playback": ("exact-audio-bytes", "heard-playback"),
}
_PRONUNCIATION_GATE_SCOPES: Final[dict[str, tuple[str, ...]]] = {
    "source_content": (
        "spelling",
        "example-word",
        "example-sentence",
        "register-context",
    ),
    "curriculum_atomicity": (
        "target-concept",
        "prerequisites",
        "active-rules",
        "one-target-unknown",
    ),
    "korean_phonetics": (
        "normative-pronunciation",
        "surface-pronunciation",
        "optional-ipa",
        "phonological-rules",
    ),
    "portuguese": (
        "word-translation",
        "sentence-translation",
        "register-alignment",
    ),
    "media_license": ("all-declared-audio-rights",),
    "media_integrity": ("letter-word-sentence-audio",),
    "audio_playback": ("exact-audio-bytes", "heard-playback"),
}
_GATE_SCOPES_BY_FAMILY: Final = {
    KoreanFoundationFamily.HANGUL: _HANGUL_GATE_SCOPES,
    KoreanFoundationFamily.PRONUNCIATION: _PRONUNCIATION_GATE_SCOPES,
}
_CURATION_MANIFEST_VERSION_BY_SOURCE_PACKS: Final[
    dict[tuple[str, str], _CurationManifestVersion]
] = {
    ("hangul-v1", "pronunciation-i-plus-1-v1"): "korean-foundations-v1-curation",
    ("hangul-v2", "pronunciation-i-plus-1-v2"): "korean-foundations-v2-curation",
}
_SOURCE_PACK_VERSIONS_BY_CURATION_MANIFEST: Final[
    dict[_CurationManifestVersion, tuple[str, str]]
] = {
    manifest_version: source_versions
    for source_versions, manifest_version in _CURATION_MANIFEST_VERSION_BY_SOURCE_PACKS.items()
}
_SOURCE_PACK_VERSIONS_BY_FAMILY: Final[dict[KoreanFoundationFamily, tuple[str, ...]]] = {
    KoreanFoundationFamily.HANGUL: tuple(
        versions[0] for versions in _CURATION_MANIFEST_VERSION_BY_SOURCE_PACKS
    ),
    KoreanFoundationFamily.PRONUNCIATION: tuple(
        versions[1] for versions in _CURATION_MANIFEST_VERSION_BY_SOURCE_PACKS
    ),
}


class KoreanFoundationReviewReasonCode(str, Enum):
    """Content-free failures at the source-to-review trust boundary."""

    MANIFEST_MISSING = "manifest_missing"
    MANIFEST_MALFORMED = "manifest_malformed"
    MANIFEST_OVERSIZED = "manifest_oversized"
    MANIFEST_INVALID = "manifest_invalid"
    SOURCE_INVALID = "source_invalid"
    SOURCE_IDENTITY_MISMATCH = "source_identity_mismatch"
    RECORD_ORDER_MISMATCH = "record_order_mismatch"
    GATE_APPLICABILITY_MISMATCH = "gate_applicability_mismatch"
    GATE_BINDING_MISMATCH = "gate_binding_mismatch"
    MANIFEST_INTEGRITY_MISMATCH = "manifest_integrity_mismatch"
    UNKNOWN_ITEM = "unknown_item"
    UNKNOWN_GATE = "unknown_gate"
    GATE_NAME_MISMATCH = "gate_name_mismatch"
    APPROVED_GATE_OVERWRITE_REQUIRES_FORCE = (
        "approved_gate_overwrite_requires_force"
    )
    CANDIDATE_MANIFEST_NOT_ACTIVE = "candidate_manifest_not_active"
    REVIEW_NOT_READY = "review_not_ready"


class KoreanFoundationReviewError(ValueError):
    """A scanner-safe review failure that never echoes content or local paths."""

    def __init__(
        self,
        reason_code: KoreanFoundationReviewReasonCode,
        *,
        item_key: str | None = None,
        gate_names: tuple[str, ...] = (),
    ) -> None:
        self.reason_code = reason_code
        self.item_key = item_key
        self.gate_names = gate_names
        parts = [reason_code.value]
        if item_key is not None:
            parts.append(f"item_key={item_key}")
        if gate_names:
            parts.append(f"gates={','.join(gate_names)}")
        super().__init__(" ".join(parts))


class _FrozenReviewModel(BaseModel):
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
        or not normalized[0].isalnum()
        or not all(
            character.isascii()
            and (character.isalnum() or character in "._:-")
            for character in normalized
        )
    ):
        raise ValueError(f"{field_name} must be a bounded identifier")
    return normalized


def _sha256(value: str, *, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEX for character in value)
    ):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _canonical_sha256(payload: object) -> str:
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json")
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _manifest_sha256(manifest: "KoreanFoundationCurationManifest") -> str:
    payload = manifest.model_dump(mode="json")
    payload.pop("content_hash", None)
    return _canonical_sha256(payload)


class KoreanFoundationReviewGate(_FrozenReviewModel):
    """One independently reviewable gate bound to exact source evidence."""

    gate_name: _ReviewGateName
    status: KoreanFoundationReviewStatus
    reason_code: str | None = Field(default=None, max_length=_MAX_IDENTIFIER_LENGTH)
    scope_ids: tuple[str, ...] = Field(min_length=1, max_length=32)
    reviewer_id: str | None = Field(default=None, max_length=_MAX_IDENTIFIER_LENGTH)
    reviewer_role: str | None = Field(
        default=None,
        max_length=_MAX_IDENTIFIER_LENGTH,
    )
    reviewed_at: str | None = Field(default=None, max_length=20)
    source_pack_version: str | None = Field(
        default=None,
        max_length=_MAX_IDENTIFIER_LENGTH,
    )
    source_content_sha256: str | None = Field(default=None, max_length=64)
    reviewed_evidence_sha256: str | None = Field(default=None, max_length=64)

    @field_validator("scope_ids")
    @classmethod
    def scope_ids_must_be_bounded(
        cls,
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        normalized = tuple(
            _identifier(value, field_name="review scope") for value in values
        )
        if len(normalized) != len(set(normalized)):
            raise ValueError("review scopes must be unique")
        return normalized

    @field_validator("reviewer_id", "reviewer_role", "source_pack_version")
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
            field_name=getattr(info, "field_name", "review identifier"),
        )

    @field_validator("source_content_sha256", "reviewed_evidence_sha256")
    @classmethod
    def optional_hashes_must_be_sha256(
        cls,
        value: str | None,
        info: object,
    ) -> str | None:
        if value is None:
            return None
        return _sha256(
            value,
            field_name=getattr(info, "field_name", "review hash"),
        )

    @model_validator(mode="after")
    def gate_state_must_be_complete_and_controlled(self) -> Self:
        expected_reason = (
            _PENDING_REASON_BY_GATE[self.gate_name]
            if self.status == "needs_review"
            else _REJECTED_REASON_BY_GATE[self.gate_name]
            if self.status == "rejected"
            else None
        )
        approval_fields = (
            self.reviewer_id,
            self.reviewer_role,
            self.reviewed_at,
            self.source_pack_version,
            self.source_content_sha256,
            self.reviewed_evidence_sha256,
        )
        if self.status not in {"approved", "ai_review_passed"}:
            if self.reason_code != expected_reason:
                raise ValueError("blocking gate requires its controlled reason")
            if any(value is not None for value in approval_fields):
                raise ValueError("blocking gate cannot carry approval metadata")
            return self

        if self.status == "ai_review_passed":
            ai_fields = (
                self.reviewed_at,
                self.source_pack_version,
                self.source_content_sha256,
                self.reviewed_evidence_sha256,
            )
            if (
                self.reason_code is not None
                or self.reviewer_id is not None
                or self.reviewer_role is not None
                or any(value is None for value in ai_fields)
            ):
                raise ValueError(
                    "AI-passed gate requires evidence without human reviewer fields"
                )
            try:
                datetime.strptime(self.reviewed_at or "", "%Y-%m-%dT%H:%M:%SZ")
            except ValueError as exc:
                raise ValueError("reviewed_at must be an exact UTC timestamp") from exc
            return self

        if self.reason_code is not None or any(value is None for value in approval_fields):
            raise ValueError("approved gate requires complete review metadata")
        if self.reviewer_role != KOREAN_FOUNDATION_GATE_REVIEWER_ROLES[
            self.gate_name
        ]:
            raise ValueError("approved gate reviewer role does not match gate")
        try:
            datetime.strptime(self.reviewed_at or "", "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as exc:
            raise ValueError("reviewed_at must be an exact UTC timestamp") from exc
        return self


class KoreanFoundationCurationRecord(_FrozenReviewModel):
    """Stable source identity plus all independently applicable review gates."""

    family: KoreanFoundationFamily
    item_key: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    sequence: int = Field(ge=1, le=_MAX_RECORDS)
    source_pack_version: str = Field(
        min_length=1,
        max_length=_MAX_IDENTIFIER_LENGTH,
    )
    source_content_sha256: str = Field(min_length=64, max_length=64)
    gates: tuple[KoreanFoundationReviewGate, ...] = Field(
        min_length=1,
        max_length=8,
    )

    @field_validator("item_key", "source_pack_version")
    @classmethod
    def record_identifiers_must_be_bounded(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "record identifier"),
        )

    @field_validator("source_content_sha256")
    @classmethod
    def source_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256(value, field_name="source content hash")

    @model_validator(mode="after")
    def identity_and_gate_set_must_be_deterministic(self) -> Self:
        prefix = (
            "ko-hangul"
            if self.family is KoreanFoundationFamily.HANGUL
            else "ko-pron"
        )
        if self.item_key != f"{prefix}-{self.sequence:04d}":
            raise ValueError("curation identity does not match family and sequence")
        if self.source_pack_version not in _SOURCE_PACK_VERSIONS_BY_FAMILY[self.family]:
            raise ValueError("curation source-pack version is unsupported")
        expected_scopes = _GATE_SCOPES_BY_FAMILY[self.family]
        if tuple(gate.gate_name for gate in self.gates) != tuple(expected_scopes):
            raise ValueError("curation applicable gate order is invalid")
        if any(
            gate.scope_ids != expected_scopes[gate.gate_name]
            for gate in self.gates
        ):
            raise ValueError("curation gate scope is invalid")
        if any(
            gate.status in {"approved", "ai_review_passed"}
            and (
                gate.source_pack_version != self.source_pack_version
                or gate.source_content_sha256 != self.source_content_sha256
            )
            for gate in self.gates
        ):
            raise ValueError("approved gate binding does not match source identity")
        return self


class KoreanFoundationCurationManifest(_FrozenReviewModel):
    """Complete curation join for both Korean foundation source packs."""

    schema_version: Literal[1] = 1
    manifest_version: _CurationManifestVersion
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
    records: tuple[KoreanFoundationCurationRecord, ...] = Field(
        min_length=1,
        max_length=_MAX_RECORDS,
    )
    content_hash: str = Field(min_length=64, max_length=64)

    @field_validator(
        "registry_version",
        "hangul_source_pack_version",
        "pronunciation_source_pack_version",
    )
    @classmethod
    def manifest_identifiers_must_be_bounded(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "manifest identifier"),
        )

    @field_validator(
        "registry_content_sha256",
        "hangul_source_pack_sha256",
        "pronunciation_source_pack_sha256",
        "content_hash",
    )
    @classmethod
    def manifest_hashes_must_be_sha256(
        cls,
        value: str,
        info: object,
    ) -> str:
        return _sha256(
            value,
            field_name=getattr(info, "field_name", "manifest hash"),
        )

    @model_validator(mode="after")
    def record_order_and_manifest_hash_must_be_deterministic(self) -> Self:
        expected_hangul_version, expected_pronunciation_version = (
            _SOURCE_PACK_VERSIONS_BY_CURATION_MANIFEST[self.manifest_version]
        )
        if (
            self.hangul_source_pack_version != expected_hangul_version
            or self.pronunciation_source_pack_version != expected_pronunciation_version
        ):
            raise ValueError("curation manifest source versions are mixed")
        families = tuple(record.family for record in self.records)
        first_pronunciation = next(
            (
                index
                for index, family in enumerate(families)
                if family is KoreanFoundationFamily.PRONUNCIATION
            ),
            len(families),
        )
        if any(
            family is not KoreanFoundationFamily.HANGUL
            for family in families[:first_pronunciation]
        ) or any(
            family is not KoreanFoundationFamily.PRONUNCIATION
            for family in families[first_pronunciation:]
        ):
            raise ValueError("curation records must be grouped by family")
        for family in KoreanFoundationFamily:
            sequences = tuple(
                record.sequence
                for record in self.records
                if record.family is family
            )
            if sequences != tuple(range(1, len(sequences) + 1)):
                raise ValueError("curation family sequences must be contiguous")
        item_keys = tuple(record.item_key for record in self.records)
        if len(item_keys) != len(set(item_keys)):
            raise ValueError("curation item keys must be unique")
        for record in self.records:
            expected_version = (
                expected_hangul_version
                if record.family is KoreanFoundationFamily.HANGUL
                else expected_pronunciation_version
            )
            if record.source_pack_version != expected_version:
                raise ValueError("curation record source version is mixed")
        if self.content_hash != _manifest_sha256(self):
            raise ValueError("curation manifest content hash does not match")
        return self


class KoreanFoundationReviewSummary(_FrozenReviewModel):
    """Aggregate, content-free Korean foundation review readiness."""

    total_records: int = Field(ge=0)
    learner_ready_records: int = Field(ge=0)
    blocked_records: int = Field(ge=0)
    family_counts: dict[str, int]
    gate_counts: dict[str, dict[str, int]]
    blocking_gates_by_item_key: dict[str, tuple[str, ...]]


class _ReviewSnapshot(Protocol):
    concept_registry: KoreanConceptRegistry
    hangul_source_pack: KoreanHangulSourcePack
    pronunciation_source_pack: KoreanPronunciationSourcePack
    curation_manifest: KoreanFoundationCurationManifest


def _raise(
    reason_code: KoreanFoundationReviewReasonCode,
    *,
    item_key: str | None = None,
    gate_names: tuple[str, ...] = (),
) -> None:
    raise KoreanFoundationReviewError(
        reason_code,
        item_key=item_key,
        gate_names=gate_names,
    )


def _pending_gate(
    family: KoreanFoundationFamily,
    gate_name: str,
) -> KoreanFoundationReviewGate:
    return KoreanFoundationReviewGate(
        gate_name=gate_name,
        status="needs_review",
        reason_code=_PENDING_REASON_BY_GATE[gate_name],
        scope_ids=_GATE_SCOPES_BY_FAMILY[family][gate_name],
    )


def _build_pending_korean_foundation_curation(
    *,
    registry: KoreanConceptRegistry,
    hangul_pack: KoreanHangulSourcePack,
    pronunciation_pack: KoreanPronunciationSourcePack,
) -> KoreanFoundationCurationManifest:
    source_versions = (
        hangul_pack.source_pack_version,
        pronunciation_pack.source_pack_version,
    )
    try:
        manifest_version = _CURATION_MANIFEST_VERSION_BY_SOURCE_PACKS[source_versions]
    except KeyError as exc:
        raise ValueError("unsupported Korean foundation source-pack tuple") from exc
    records = tuple(
        KoreanFoundationCurationRecord(
            family=pack.family,
            item_key=entry.item_key,
            sequence=entry.sequence,
            source_pack_version=pack.source_pack_version,
            source_content_sha256=entry.content_hash,
            gates=tuple(
                _pending_gate(pack.family, gate_name)
                for gate_name in _GATE_SCOPES_BY_FAMILY[pack.family]
            ),
        )
        for pack in (hangul_pack, pronunciation_pack)
        for entry in pack.entries
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
        "records": [record.model_dump(mode="json") for record in records],
    }
    payload["content_hash"] = _canonical_sha256(payload)
    return KoreanFoundationCurationManifest.model_validate(payload)


def _load_curation_manifest(path: Path) -> KoreanFoundationCurationManifest:
    try:
        size = path.stat().st_size
    except FileNotFoundError as exc:
        raise KoreanFoundationReviewError(
            KoreanFoundationReviewReasonCode.MANIFEST_MISSING
        ) from exc
    except OSError as exc:
        raise KoreanFoundationReviewError(
            KoreanFoundationReviewReasonCode.MANIFEST_MALFORMED
        ) from exc
    if size > _CURATION_MAX_BYTES:
        _raise(KoreanFoundationReviewReasonCode.MANIFEST_OVERSIZED)
    try:
        raw = path.read_bytes()
        if len(raw) > _CURATION_MAX_BYTES:
            _raise(KoreanFoundationReviewReasonCode.MANIFEST_OVERSIZED)
        payload = json.loads(raw.decode("utf-8"))
        return KoreanFoundationCurationManifest.model_validate(payload)
    except KoreanFoundationReviewError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KoreanFoundationReviewError(
            KoreanFoundationReviewReasonCode.MANIFEST_MALFORMED
        ) from exc
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationReviewError(
            KoreanFoundationReviewReasonCode.MANIFEST_INVALID
        ) from exc


def _assert_member_file_hash(path: Path, expected_hash: str) -> None:
    try:
        actual_hash = sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise KoreanFoundationReviewError(
            KoreanFoundationReviewReasonCode.MANIFEST_MALFORMED
        ) from exc
    if actual_hash != expected_hash:
        _raise(KoreanFoundationReviewReasonCode.MANIFEST_INTEGRITY_MISMATCH)


def validate_korean_foundation_curation(
    manifest: KoreanFoundationCurationManifest,
    *,
    registry: KoreanConceptRegistry,
    hangul_pack: KoreanHangulSourcePack,
    pronunciation_pack: KoreanPronunciationSourcePack,
) -> None:
    """Validate source structure first, then exact review identity and bindings."""

    try:
        validate_korean_foundation_pack(
            registry=registry,
            pack=hangul_pack,
        )
        validate_korean_foundation_pack(
            registry=registry,
            pack=pronunciation_pack,
            inherited_known_ids=pronunciation_pack.inherited_orthographic_concept_ids,
        )
    except (KoreanCurriculumError, ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationReviewError(
            KoreanFoundationReviewReasonCode.SOURCE_INVALID
        ) from exc

    expected_manifest_identity = (
        registry.registry_version,
        registry.content_hash,
        hangul_pack.source_pack_version,
        hangul_pack.content_hash,
        pronunciation_pack.source_pack_version,
        pronunciation_pack.content_hash,
    )
    actual_manifest_identity = (
        manifest.registry_version,
        manifest.registry_content_sha256,
        manifest.hangul_source_pack_version,
        manifest.hangul_source_pack_sha256,
        manifest.pronunciation_source_pack_version,
        manifest.pronunciation_source_pack_sha256,
    )
    if actual_manifest_identity != expected_manifest_identity:
        _raise(KoreanFoundationReviewReasonCode.SOURCE_IDENTITY_MISMATCH)

    expected_entries = (*hangul_pack.entries, *pronunciation_pack.entries)
    if len(manifest.records) != len(expected_entries):
        _raise(KoreanFoundationReviewReasonCode.RECORD_ORDER_MISMATCH)
    for record, entry in zip(manifest.records, expected_entries, strict=True):
        expected_identity = (
            entry.family,
            entry.item_key,
            entry.sequence,
            entry.source_pack_version,
            entry.content_hash,
        )
        actual_identity = (
            record.family,
            record.item_key,
            record.sequence,
            record.source_pack_version,
            record.source_content_sha256,
        )
        if actual_identity != expected_identity:
            _raise(KoreanFoundationReviewReasonCode.SOURCE_IDENTITY_MISMATCH)
        expected_scopes = _GATE_SCOPES_BY_FAMILY[record.family]
        if tuple(gate.gate_name for gate in record.gates) != tuple(expected_scopes):
            _raise(KoreanFoundationReviewReasonCode.GATE_APPLICABILITY_MISMATCH)
        for gate in record.gates:
            if gate.scope_ids != expected_scopes[gate.gate_name]:
                _raise(KoreanFoundationReviewReasonCode.GATE_APPLICABILITY_MISMATCH)
            if gate.status in {"approved", "ai_review_passed"} and (
                gate.source_pack_version != record.source_pack_version
                or gate.source_content_sha256 != record.source_content_sha256
            ):
                _raise(KoreanFoundationReviewReasonCode.GATE_BINDING_MISMATCH)
    if manifest.content_hash != _manifest_sha256(manifest):
        _raise(KoreanFoundationReviewReasonCode.MANIFEST_INTEGRITY_MISMATCH)


def load_pending_korean_foundation_curation() -> KoreanFoundationCurationManifest:
    """Load the fixed current-candidate bundle curation member."""

    bundle = load_korean_current_foundation_bundle()
    manifest_path = Path(bundle.source_root) / _KOREAN_FOUNDATION_CURRENT_CURATION_MEMBER
    _assert_member_file_hash(
        manifest_path,
        bundle.member_file_sha256[_KOREAN_FOUNDATION_CURRENT_CURATION_MEMBER],
    )
    manifest = _load_curation_manifest(manifest_path)
    if not manifest.candidate_only:
        _raise(KoreanFoundationReviewReasonCode.MANIFEST_INVALID)
    validate_korean_foundation_curation(
        manifest,
        registry=bundle.registry,
        hangul_pack=bundle.hangul,
        pronunciation_pack=bundle.pronunciation,
    )
    return manifest


def load_korean_v1_foundation_curation() -> KoreanFoundationCurationManifest:
    """Load the immutable v1 curation manifest explicitly for history."""

    bundle = load_korean_v1_foundation_bundle()
    manifest = _load_curation_manifest(_KOREAN_FOUNDATION_CURATION_V1_PATH)
    validate_korean_foundation_curation(
        manifest,
        registry=bundle.registry,
        hangul_pack=bundle.hangul,
        pronunciation_pack=bundle.pronunciation,
    )
    return manifest


def summarize_korean_foundation_review(
    manifest: KoreanFoundationCurationManifest,
) -> KoreanFoundationReviewSummary:
    """Return aggregate statuses and content-free blockers for a curation manifest."""

    gate_counts: dict[str, dict[str, int]] = {}
    for gate_name in KOREAN_FOUNDATION_GATE_REVIEWER_ROLES:
        counter = Counter(
            gate.status
            for record in manifest.records
            for gate in record.gates
            if gate.gate_name == gate_name
        )
        gate_counts[gate_name] = {
            status: counter.get(status, 0)
            for status in ("needs_review", "approved", "ai_review_passed", "rejected")
        }
    blockers = {
        record.item_key: tuple(
            gate.gate_name
            for gate in record.gates
            if gate.status not in {"approved", "ai_review_passed"}
        )
        for record in manifest.records
        if any(
            gate.status not in {"approved", "ai_review_passed"}
            for gate in record.gates
        )
    }
    fully_approved = len(manifest.records) - len(blockers)
    learner_ready = 0 if manifest.candidate_only else fully_approved
    blocked_records = len(manifest.records) - learner_ready
    family_counter = Counter(record.family.value for record in manifest.records)
    return KoreanFoundationReviewSummary(
        total_records=len(manifest.records),
        learner_ready_records=learner_ready,
        blocked_records=blocked_records,
        family_counts={
            family.value: family_counter.get(family.value, 0)
            for family in KoreanFoundationFamily
        },
        gate_counts=gate_counts,
        blocking_gates_by_item_key=blockers,
    )


def update_korean_foundation_review_gate(
    manifest: KoreanFoundationCurationManifest,
    *,
    item_key: str,
    gate_name: str,
    gate: KoreanFoundationReviewGate,
    force: bool = False,
) -> KoreanFoundationCurationManifest:
    """Return one isolated gate update while protecting an existing approval."""

    if gate_name not in KOREAN_FOUNDATION_GATE_REVIEWER_ROLES:
        _raise(KoreanFoundationReviewReasonCode.UNKNOWN_GATE)
    if gate.gate_name != gate_name:
        _raise(KoreanFoundationReviewReasonCode.GATE_NAME_MISMATCH)
    updated_records: list[KoreanFoundationCurationRecord] = []
    matched = False
    for record in manifest.records:
        if record.item_key != item_key:
            updated_records.append(record)
            continue
        matched = True
        if gate_name not in _GATE_SCOPES_BY_FAMILY[record.family]:
            _raise(KoreanFoundationReviewReasonCode.UNKNOWN_GATE)
        if gate.scope_ids != _GATE_SCOPES_BY_FAMILY[record.family][gate_name]:
            _raise(KoreanFoundationReviewReasonCode.GATE_APPLICABILITY_MISMATCH)
        current = next(
            current_gate
            for current_gate in record.gates
            if current_gate.gate_name == gate_name
        )
        if (
            current.status in {"approved", "ai_review_passed"}
            and current != gate
            and not force
        ):
            _raise(
                KoreanFoundationReviewReasonCode.APPROVED_GATE_OVERWRITE_REQUIRES_FORCE
            )
        gates = tuple(
            gate if current_gate.gate_name == gate_name else current_gate
            for current_gate in record.gates
        )
        record_payload = record.model_dump(mode="json")
        record_payload["gates"] = [value.model_dump(mode="json") for value in gates]
        try:
            updated_records.append(
                KoreanFoundationCurationRecord.model_validate(record_payload)
            )
        except ValidationError as exc:
            raise KoreanFoundationReviewError(
                KoreanFoundationReviewReasonCode.GATE_BINDING_MISMATCH
            ) from exc
    if not matched:
        _raise(KoreanFoundationReviewReasonCode.UNKNOWN_ITEM)

    payload = manifest.model_dump(mode="json")
    payload["records"] = [record.model_dump(mode="json") for record in updated_records]
    payload.pop("content_hash", None)
    payload["content_hash"] = _canonical_sha256(payload)
    return KoreanFoundationCurationManifest.model_validate(payload)


def assert_korean_foundation_review_ready(snapshot: _ReviewSnapshot) -> None:
    """Fail closed unless one resolved non-candidate snapshot is fully reviewed."""

    manifest = snapshot.curation_manifest
    validate_korean_foundation_curation(
        manifest,
        registry=snapshot.concept_registry,
        hangul_pack=snapshot.hangul_source_pack,
        pronunciation_pack=snapshot.pronunciation_source_pack,
    )
    if manifest.candidate_only:
        _raise(KoreanFoundationReviewReasonCode.CANDIDATE_MANIFEST_NOT_ACTIVE)
    summary = summarize_korean_foundation_review(manifest)
    if summary.learner_ready_records == summary.total_records:
        return
    item_key, gate_names = next(iter(summary.blocking_gates_by_item_key.items()))
    _raise(
        KoreanFoundationReviewReasonCode.REVIEW_NOT_READY,
        item_key=item_key,
        gate_names=gate_names,
    )


__all__ = [
    "DEFAULT_KOREAN_FOUNDATION_CURATION_PATH",
    "KOREAN_FOUNDATION_GATE_REVIEWER_ROLES",
    "KoreanFoundationCurationManifest",
    "KoreanFoundationCurationRecord",
    "KoreanFoundationReviewError",
    "KoreanFoundationReviewGate",
    "KoreanFoundationReviewReasonCode",
    "KoreanFoundationReviewStatus",
    "KoreanFoundationReviewSummary",
    "assert_korean_foundation_review_ready",
    "load_korean_v1_foundation_curation",
    "load_pending_korean_foundation_curation",
    "summarize_korean_foundation_review",
    "update_korean_foundation_review_gate",
    "validate_korean_foundation_curation",
]
