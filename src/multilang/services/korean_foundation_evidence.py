"""Fixed, pathless evidence validation for Korean foundation state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import struct
import tempfile
from typing import Any, Callable, Final, Literal, Self
import unicodedata
import wave

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from multilang.services.ai_acoustic_review import (
    AIAcousticReviewAggregate,
    ai_acoustic_review_sha256,
)
from multilang.services.ai_linguistic_review import (
    AIReviewAggregate,
    AIReviewAttempt,
    AIReviewPolicy,
    AIReviewSubject,
    AIValidatorRun,
    ai_review_content_hash,
    build_ai_review_aggregate,
)
from multilang.services._korean_foundation_state_lock import (
    KOREAN_FOUNDATION_STATE_LOCK_VERSION,
    _korean_foundation_state_lock,
)
from multilang.services.korean_curriculum import (
    KoreanConceptRegistry,
    KoreanFoundationFamily,
    KoreanHangulSourceEntry,
    KoreanHangulSourcePack,
    KoreanPronunciationSourceEntry,
    KoreanPronunciationSourcePack,
)
from multilang.services.korean_foundation_media import (
    KoreanFoundationMediaManifest,
    KoreanFoundationMediaSlot,
    korean_foundation_media_manifest_sha256,
    korean_foundation_media_metadata_sha256,
)
from multilang.services.korean_foundation_review import (
    KoreanFoundationCurationManifest,
    validate_korean_foundation_curation,
)
from multilang.services.korean_foundation_snapshot import KoreanFoundationActivePointer


PHASE31_EVIDENCE_INBOX: Final = Path(
    ".planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox"
)
PHASE31_EVIDENCE_INDEX: Final = PHASE31_EVIDENCE_INBOX / "evidence-index.json"
PHASE31_VALIDATION_RECEIPT: Final = (
    PHASE31_EVIDENCE_INBOX / "validation-receipt.json"
)
KOREAN_FOUNDATION_EVIDENCE_LAYOUT_VERSION: Final = (
    "phase31-korean-foundation-evidence-layout-v1"
)
KOREAN_FOUNDATION_EVIDENCE_POLICY_VERSION: Final = (
    "phase31-korean-foundation-evidence-policy-v1"
)
_RECEIPT_VERSION: Final = "phase31-korean-foundation-validation-receipt-v1"
_INDEX_VERSION: Final = "phase31-korean-foundation-evidence-index-v1"
_PROJECT_ROOT: Final = Path(__file__).resolve().parents[3]
_PHASE_RELPATH: Final = Path(
    ".planning/phases/31-hangul-and-pronunciation-i-plus-1"
)
_REGISTRY_FILENAME: Final = "korean-concepts-v1.json"
_CURRENT_CANDIDATE_FILENAME: Final = "current-candidate.json"
_BUNDLE_MANIFEST_FILENAME: Final = "bundle-manifest.json"
_CANDIDATE_MEMBER_FILENAMES: Final = (
    "hangul-v2.json",
    "pronunciation-i-plus-1-v2.json",
    "korean-foundations-v2-curation.json",
    "korean-foundations-v2-media.json",
)
_CANDIDATE_FILENAMES: Final = (
    _CURRENT_CANDIDATE_FILENAME,
    _BUNDLE_MANIFEST_FILENAME,
    *_CANDIDATE_MEMBER_FILENAMES,
)
_REQUEST_FILENAMES: Final = (
    "31-CURRICULUM-REVIEW.md",
    "31-AUDIO-PLAYBACK-REVIEW.md",
)
_FIXED_MEMBER_ROLES: Final = (
    ("proposed-curation.json", "proposed_curation"),
    ("proposed-media.json", "proposed_media"),
    ("curriculum-review.json", "curriculum_review"),
    ("audio-playback-review.json", "audio_playback_review"),
    ("rights.json", "rights"),
    ("reviewers/korean-orthography.json", "reviewer"),
    ("reviewers/korean-phonetics.json", "reviewer"),
    ("reviewers/portuguese.json", "reviewer"),
    ("reviewers/independent-native-speaker.json", "reviewer"),
)
_AI_REVIEW_ROOT_RELPATH: Final = "ai-review"
_AI_ATTEMPTS_RELPATH: Final = "ai-review/attempts"
_AI_FAILED_ATTEMPTS_RELPATH: Final = "ai-review/failed-attempts"
_AI_PROJECTIONS_RELPATH: Final = "ai-review/projections"
_AI_POLICY_RELPATH: Final = "ai-review/policy.json"
_AI_SUBJECTS_RELPATH: Final = "ai-review/subjects.json"
_AI_VALIDATORS_RELPATH: Final = "ai-review/validator-runs.json"
_AI_AGGREGATE_RELPATH: Final = "ai-review/aggregate.json"
_ACOUSTIC_REVIEW_RELPATH: Final = "acoustic-review.json"
_MEDIA_RIGHTS_RELPATH: Final = "media-rights.json"
_MEDIA_ARTIFACTS_RELPATH: Final = "media/artifacts.json"
_MEDIA_AUTHORITY_RELPATH: Final = "execution-handoffs/media-authority.json"
_CURRENT_LAYOUT_FIXED_MEMBER_ROLES: Final = (
    (_AI_POLICY_RELPATH, "ai_review_policy"),
    (_AI_SUBJECTS_RELPATH, "ai_review_subjects"),
    (_AI_VALIDATORS_RELPATH, "ai_review_validators"),
    (_AI_AGGREGATE_RELPATH, "ai_review_aggregate"),
    (_ACOUSTIC_REVIEW_RELPATH, "acoustic_review"),
    (_MEDIA_RIGHTS_RELPATH, "media_rights"),
    (_MEDIA_AUTHORITY_RELPATH, "media_authority"),
    (_MEDIA_ARTIFACTS_RELPATH, "media_artifacts"),
)
_CURRENT_LAYOUT_DIRECTORIES: Final = {
    _AI_REVIEW_ROOT_RELPATH,
    _AI_ATTEMPTS_RELPATH,
    _AI_FAILED_ATTEMPTS_RELPATH,
    _AI_PROJECTIONS_RELPATH,
    "media",
    "media/hangul",
    "media/pronunciation",
}
_AI_ATTEMPT_COUNT: Final = 21
_AI_PROJECTION_COUNT: Final = 7
_CURRENT_REQUIRED_MEDIA_COUNT: Final = 325
_CURRENT_AI_REVIEW_SOURCE_VERSION: Final = "phase31-ai-linguistic-review-v1"
_CURRENT_MEDIA_SOURCE_VERSION: Final = "phase31-ai-acoustic-review-v1"
_CURRENT_MEDIA_SOURCE_ID: Final = "phase31-ai-media-authority"
_CURRENT_MEDIA_LICENSE_ID: Final = "phase31-project-owner-authorized-local-use"
_CURRENT_AUDIO_SOURCE_ID: Final = "azure-speech-service"
_CURRENT_VISUAL_SOURCE_ID: Final = "local-deterministic-project-authored"
_CURRENT_VISUAL_SOURCE_VERSION: Final = "phase31-local-deterministic-visual-v1"
_CURRENT_AUDIO_ATTRIBUTION: Final = (
    "Project-owner authorized Azure Speech Service Korean TTS for Phase 31 local closure."
)
_CURRENT_VISUAL_ATTRIBUTION: Final = (
    "Project-owner authorized deterministic project-authored visual media for Phase 31 local closure."
)
_SENTINEL_SHA256: Final = sha256(b"not_applicable").hexdigest()
_HANGUL_AUDIO_TEXT_BY_DISPLAY: Final = {
    "ㄳ": "ㄱ ㅅ",
    "ㄵ": "ㄴ ㅈ",
    "ㄶ": "ㄴ ㅎ",
    "ㄺ": "ㄹ ㄱ",
    "ㄻ": "ㄹ ㅁ",
    "ㄼ": "ㄹ ㅂ",
    "ㄽ": "ㄹ ㅅ",
    "ㄾ": "ㄹ ㅌ",
    "ㄿ": "ㄹ ㅍ",
    "ㅀ": "ㄹ ㅎ",
    "ㅄ": "ㅂ ㅅ",
}
_REVIEWER_ROLE_CONTRACT: Final = {
    "reviewers/korean-orthography.json": (
        "korean-orthography-reviewer",
        (
            "korean-foundation-content-reviewer",
            "korean-curriculum-reviewer",
            "korean-orthography-reviewer",
            "media-rights-reviewer",
            "media-integrity-reviewer",
        ),
    ),
    "reviewers/korean-phonetics.json": (
        "korean-phonetics-specialist",
        ("korean-phonetics-specialist",),
    ),
    "reviewers/portuguese.json": (
        "portuguese-reviewer",
        ("portuguese-reviewer",),
    ),
    "reviewers/independent-native-speaker.json": (
        "independent-native-speaker",
        ("audio-playback-reviewer", "independent-native-speaker"),
    ),
}
_CURRICULUM_GATES: Final = {
    "hangul": (
        "source_content",
        "curriculum_atomicity",
        "korean_orthography",
        "portuguese",
    ),
    "pronunciation": (
        "source_content",
        "curriculum_atomicity",
        "korean_phonetics",
        "portuguese",
    ),
}
_AUDIO_KINDS: Final = frozenset(
    {"audio", "letter_audio", "word_audio", "sentence_audio"}
)
_LOWERCASE_HEX: Final = frozenset("0123456789abcdef")
_ARCHIVE_SUFFIXES: Final = frozenset(
    {".apkg", ".zip", ".tar", ".tgz", ".gz", ".bz2", ".7z", ".rar"}
)
_INDEX_MAX_BYTES: Final = 4 * 1_048_576
_JSON_MEMBER_MAX_BYTES: Final = 4 * 1_048_576
_MEDIA_MEMBER_MAX_BYTES: Final = 16 * 1_048_576
_RECEIPT_MAX_BYTES: Final = 1_048_576
_REQUEST_MAX_BYTES: Final = 1_048_576
_CANDIDATE_MAX_BYTES: Final = 32 * 1_048_576
_MAX_IDENTIFIER_LENGTH: Final = 192
_MAX_ENTRIES: Final = 4_096
_MAX_RELPATH_LENGTH: Final = 512
_ABSENT_PRESTATE_SHA256: Final = sha256(
    b"phase31-korean-foundation-active-prestate:absent"
).hexdigest()


@dataclass(frozen=True, slots=True)
class _KoreanFoundationEvidencePaths:
    project_dir: Path
    candidate_dir: Path
    phase_dir: Path
    inbox: Path
    index: Path
    receipt: Path
    curriculum_request: Path
    audio_request: Path
    active_pointer: Path

    @classmethod
    def from_project_root(
        cls,
        project_dir: Path,
    ) -> "_KoreanFoundationEvidencePaths":
        phase_dir = project_dir / _PHASE_RELPATH
        inbox = project_dir / PHASE31_EVIDENCE_INBOX
        candidate_dir = project_dir / "data" / "korean_foundations"
        return cls(
            project_dir=project_dir,
            candidate_dir=candidate_dir,
            phase_dir=phase_dir,
            inbox=inbox,
            index=inbox / "evidence-index.json",
            receipt=inbox / "validation-receipt.json",
            curriculum_request=phase_dir / "31-CURRICULUM-REVIEW.md",
            audio_request=phase_dir / "31-AUDIO-PLAYBACK-REVIEW.md",
            active_pointer=candidate_dir / "active-foundations.json",
        )


_FIXED_PATHS = _KoreanFoundationEvidencePaths.from_project_root(_PROJECT_ROOT)


class KoreanFoundationEvidenceReasonCode(str, Enum):
    """Content-free failures for the fixed evidence boundary."""

    INDEX_MISSING = "index_missing"
    INDEX_INVALID = "index_invalid"
    INDEX_HASH_MISMATCH = "index_hash_mismatch"
    UNSAFE_MEMBER = "unsafe_member"
    UNSAFE_FILESYSTEM_COMPONENT = "unsafe_filesystem_component"
    MEMBER_MISSING = "member_missing"
    MEMBER_OVERSIZED = "member_oversized"
    MEMBER_HASH_MISMATCH = "member_hash_mismatch"
    UNEXPECTED_MEMBER = "unexpected_member"
    ARCHIVE_MEMBER = "archive_member"
    SOURCE_BINDING_MISMATCH = "source_binding_mismatch"
    REVIEW_INVALID = "review_invalid"
    REVIEWER_QUALIFICATION_INVALID = "reviewer_qualification_invalid"
    RIGHTS_INVALID = "rights_invalid"
    PLAYBACK_INVALID = "playback_invalid"
    MEDIA_INVALID = "media_invalid"
    MEDIA_HASH_MISMATCH = "media_hash_mismatch"
    ACTIVE_PRESTATE_INVALID = "active_prestate_invalid"
    BETWEEN_STAGE_DRIFT = "between_stage_drift"
    STALE_RECEIPT = "stale_receipt"
    RECEIPT_MISSING = "receipt_missing"
    RECEIPT_HASH_MISMATCH = "receipt_hash_mismatch"
    RECEIPT_INVALID = "receipt_invalid"
    CONTINUITY_DRIFT = "continuity_drift"
    ATOMIC_WRITE_FAILED = "atomic_write_failed"


class KoreanFoundationEvidenceError(ValueError):
    """A scanner-safe failure that never includes content or absolute paths."""

    def __init__(self, reason_code: KoreanFoundationEvidenceReasonCode) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code.value)


class _FrozenEvidenceModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


def _sha256_text(value: str, *, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEX for character in value)
    ):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _identifier(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a bounded identifier")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(value) > _MAX_IDENTIFIER_LENGTH
        or not normalized[0].isalnum()
        or not all(
            character.isascii()
            and (character.isalnum() or character in "._:-")
            for character in normalized
        )
    ):
        raise ValueError(f"{field_name} must be a bounded identifier")
    return normalized


def _reviewed_at(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError) as exc:
        raise ValueError("reviewed_at must be an exact UTC timestamp") from exc
    return value


def _canonical_bytes(value: object) -> bytes:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _canonical_sha256(value: object) -> str:
    return sha256(_canonical_bytes(value)).hexdigest()


def _json_file_bytes(value: object) -> bytes:
    return _canonical_bytes(value) + b"\n"


def _text_sha256(value: str) -> str:
    return sha256(unicodedata.normalize("NFC", value).encode("utf-8")).hexdigest()


def _safe_relpath(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > _MAX_RELPATH_LENGTH
        or value.startswith(("/", "~"))
        or "\\" in value
        or ":" in value
        or "\x00" in value
        or "//" in value
    ):
        raise ValueError("evidence member path must be repository-relative")
    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError("evidence member path must be repository-relative")
    relpath = PurePosixPath(value)
    if relpath.is_absolute() or tuple(relpath.parts) != tuple(raw_parts):
        raise ValueError("evidence member path must be repository-relative")
    if relpath.suffix.casefold() in _ARCHIVE_SUFFIXES:
        raise ValueError("evidence member cannot be an archive")
    if any(
        not all(
            character.isascii()
            and (character.isalnum() or character in "._-")
            for character in part
        )
        for part in relpath.parts
    ):
        raise ValueError("evidence member path contains unsupported characters")
    return value


class KoreanFoundationEvidenceCandidateBinding(_FrozenEvidenceModel):
    filename: str = Field(min_length=1, max_length=128)
    file_sha256: str = Field(min_length=64, max_length=64)
    version: str | None = Field(
        default=None,
        min_length=1,
        max_length=_MAX_IDENTIFIER_LENGTH,
    )
    canonical_content_sha256: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    bundle_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    bundle_relpath: str | None = Field(
        default=None,
        min_length=1,
        max_length=_MAX_RELPATH_LENGTH,
    )
    bundle_manifest_sha256: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    selected_draft_manifest_sha256: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    draft_validation_sha256: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    total_record_count: int | None = Field(default=None, ge=1, le=_MAX_ENTRIES)
    media_slot_count: int | None = Field(default=None, ge=1, le=8_192)
    item_count: int | None = Field(default=None, ge=1, le=_MAX_ENTRIES)
    record_count: int | None = Field(default=None, ge=1, le=_MAX_ENTRIES)
    gate_count: int | None = Field(default=None, ge=1, le=32_768)
    asset_count: int | None = Field(default=None, ge=1, le=8_192)
    required_asset_count: int | None = Field(default=None, ge=1, le=8_192)

    @field_validator("filename")
    @classmethod
    def filename_must_be_fixed_basename(cls, value: str) -> str:
        if value != Path(value).name or value not in _CANDIDATE_FILENAMES:
            raise ValueError("candidate filename is unsupported")
        return value

    @field_validator("version")
    @classmethod
    def version_must_be_bounded(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _identifier(value, field_name="candidate version")

    @field_validator(
        "file_sha256",
        "canonical_content_sha256",
        "bundle_sha256",
        "bundle_manifest_sha256",
        "selected_draft_manifest_sha256",
        "draft_validation_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "candidate hash"),
        )

    @field_validator("bundle_relpath")
    @classmethod
    def bundle_relpath_must_be_exact_current_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            relpath = _safe_relpath(value)
        except ValueError as exc:
            raise ValueError("bundle path must be fixed") from exc
        parts = PurePosixPath(relpath).parts
        if (
            len(parts) != 2
            or parts[0] != "candidate-bundles"
            or len(parts[1]) != 64
            or any(character not in _LOWERCASE_HEX for character in parts[1])
        ):
            raise ValueError("bundle path must be fixed")
        return relpath

    @model_validator(mode="after")
    def binding_shape_must_match_filename(self) -> Self:
        provided = set(self.model_fields_set)
        pointer_fields = {
            "filename",
            "bundle_sha256",
            "bundle_relpath",
            "bundle_manifest_sha256",
            "file_sha256",
        }
        manifest_fields = {
            "filename",
            "bundle_sha256",
            "selected_draft_manifest_sha256",
            "draft_validation_sha256",
            "file_sha256",
            "total_record_count",
            "media_slot_count",
        }
        member_fields = {
            "filename",
            "version",
            "file_sha256",
            "canonical_content_sha256",
        }
        expected_versions = {
            "hangul-v2.json": "hangul-v2",
            "pronunciation-i-plus-1-v2.json": "pronunciation-i-plus-1-v2",
            "korean-foundations-v2-curation.json": "korean-foundations-v2-curation",
            "korean-foundations-v2-media.json": "korean-foundations-v2-media",
        }
        if self.filename == _CURRENT_CANDIDATE_FILENAME:
            if provided != pointer_fields:
                raise ValueError("current candidate binding shape is unsupported")
            if self.bundle_relpath != f"candidate-bundles/{self.bundle_sha256}":
                raise ValueError("current candidate bundle path mismatch")
            return self
        if self.filename == _BUNDLE_MANIFEST_FILENAME:
            if provided != manifest_fields:
                raise ValueError("bundle manifest binding shape is unsupported")
            if self.total_record_count != 139 or self.media_slot_count != 509:
                raise ValueError("bundle manifest counts are unsupported")
            return self
        if self.filename in expected_versions:
            expected_fields = set(member_fields)
            if self.filename in {"hangul-v2.json", "pronunciation-i-plus-1-v2.json"}:
                expected_fields.add("item_count")
            elif self.filename == "korean-foundations-v2-curation.json":
                expected_fields.update({"record_count", "gate_count"})
            else:
                expected_fields.update({"asset_count", "required_asset_count"})
            if provided != expected_fields:
                raise ValueError("candidate member binding shape is unsupported")
            if self.version != expected_versions[self.filename]:
                raise ValueError("candidate member version mismatch")
            return self
        raise ValueError("candidate filename is unsupported")


class KoreanFoundationEvidenceRequestBinding(_FrozenEvidenceModel):
    filename: str = Field(min_length=1, max_length=128)
    file_sha256: str = Field(min_length=64, max_length=64)

    @field_validator("filename")
    @classmethod
    def filename_must_be_fixed_basename(cls, value: str) -> str:
        if value != Path(value).name or value not in _REQUEST_FILENAMES:
            raise ValueError("request filename is unsupported")
        return value

    @field_validator("file_sha256")
    @classmethod
    def hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="request hash")


class KoreanFoundationEvidenceMember(_FrozenEvidenceModel):
    relpath: str = Field(min_length=1, max_length=_MAX_RELPATH_LENGTH)
    role: Literal[
        "proposed_curation",
        "proposed_media",
        "curriculum_review",
        "audio_playback_review",
        "rights",
        "reviewer",
        "ai_review_policy",
        "ai_review_subjects",
        "ai_review_validators",
        "ai_review_aggregate",
        "ai_review_attempt",
        "ai_review_projection",
        "acoustic_review",
        "media_rights",
        "media_authority",
        "media_artifacts",
        "media",
    ]
    size_bytes: int = Field(ge=1, le=_MEDIA_MEMBER_MAX_BYTES)
    sha256: str = Field(min_length=64, max_length=64)

    @field_validator("relpath")
    @classmethod
    def relpath_must_be_safe(cls, value: str) -> str:
        return _safe_relpath(value)

    @field_validator("sha256")
    @classmethod
    def hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="member hash")


class KoreanFoundationEvidenceIndex(_FrozenEvidenceModel):
    schema_version: Literal[1] = 1
    index_version: Literal["phase31-korean-foundation-evidence-index-v1"]
    layout_version: Literal["phase31-korean-foundation-evidence-layout-v1"]
    policy_version: Literal["phase31-korean-foundation-evidence-policy-v1"]
    candidate_bindings: tuple[KoreanFoundationEvidenceCandidateBinding, ...] = Field(
        min_length=6,
        max_length=6,
    )
    request_bindings: tuple[KoreanFoundationEvidenceRequestBinding, ...] = Field(
        min_length=2,
        max_length=2,
    )
    members: tuple[KoreanFoundationEvidenceMember, ...] = Field(
        min_length=1,
        max_length=8_192,
    )
    declared_members_sha256: str = Field(min_length=64, max_length=64)
    index_payload_sha256: str = Field(min_length=64, max_length=64)

    @field_validator("declared_members_sha256", "index_payload_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "index hash"),
        )

    @model_validator(mode="after")
    def declarations_and_payload_hash_must_match(self) -> Self:
        members = [
            member.model_dump(mode="json", exclude_none=True)
            for member in self.members
        ]
        if self.declared_members_sha256 != _canonical_sha256(members):
            raise ValueError("declared member hash does not match")
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("index_payload_sha256", None)
        if self.index_payload_sha256 != _canonical_sha256(payload):
            raise ValueError("index payload hash does not match")
        relpaths = tuple(member.relpath for member in self.members)
        if len(relpaths) != len(set(relpaths)):
            raise ValueError("index member paths must be unique")
        return self


class KoreanFoundationReviewerQualification(_FrozenEvidenceModel):
    schema_version: Literal[1] = 1
    record_version: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    reviewer_id: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    primary_role: str = Field(min_length=1, max_length=_MAX_IDENTIFIER_LENGTH)
    qualified_roles: tuple[str, ...] = Field(min_length=1, max_length=16)
    qualification_status: Literal["approved"]
    reviewed_at: str = Field(min_length=20, max_length=20)
    qualification_evidence_sha256: str = Field(min_length=64, max_length=64)

    @field_validator("record_version", "reviewer_id", "primary_role")
    @classmethod
    def identifiers_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(
            value,
            field_name=getattr(info, "field_name", "reviewer identifier"),
        )

    @field_validator("qualified_roles")
    @classmethod
    def roles_must_be_unique(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(
            _identifier(value, field_name="qualified role") for value in values
        )
        if len(normalized) != len(set(normalized)):
            raise ValueError("qualified roles must be unique")
        return normalized

    @field_validator("reviewed_at")
    @classmethod
    def timestamp_must_be_exact(cls, value: str) -> str:
        return _reviewed_at(value)

    @field_validator("qualification_evidence_sha256")
    @classmethod
    def qualification_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="qualification evidence hash")

    @model_validator(mode="after")
    def qualification_hash_must_match(self) -> Self:
        payload = {
            "reviewer_id": self.reviewer_id,
            "primary_role": self.primary_role,
            "qualified_roles": list(self.qualified_roles),
            "qualification_status": self.qualification_status,
            "reviewed_at": self.reviewed_at,
        }
        if self.qualification_evidence_sha256 != _canonical_sha256(payload):
            raise ValueError("qualification evidence hash does not match")
        return self


class _CurriculumGateReview(_FrozenEvidenceModel):
    gate_name: str
    scope_ids: tuple[str, ...] = Field(min_length=1, max_length=32)
    reviewer_id: str
    reviewer_role: str
    reviewed_at: str
    source_content_sha256: str
    reviewed_evidence_sha256: str

    @field_validator("gate_name", "reviewer_id", "reviewer_role")
    @classmethod
    def identifiers_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(value, field_name=getattr(info, "field_name", "review"))

    @field_validator("scope_ids")
    @classmethod
    def scopes_must_be_bounded(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_identifier(value, field_name="review scope") for value in values)

    @field_validator("reviewed_at")
    @classmethod
    def timestamp_must_be_exact(cls, value: str) -> str:
        return _reviewed_at(value)

    @field_validator("source_content_sha256", "reviewed_evidence_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "review hash"))


class _CurriculumItemReview(_FrozenEvidenceModel):
    family: Literal["hangul", "pronunciation"]
    item_key: str
    source_pack_version: str
    source_content_sha256: str
    gate_reviews: tuple[_CurriculumGateReview, ...] = Field(min_length=4, max_length=4)

    @field_validator("item_key", "source_pack_version")
    @classmethod
    def identifiers_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(value, field_name=getattr(info, "field_name", "item identity"))

    @field_validator("source_content_sha256")
    @classmethod
    def source_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="source content hash")


class _SpecialistAtomizationReview(_FrozenEvidenceModel):
    item_key: str
    stage_id: Literal["P11", "P12", "P13"]
    scope_ids: tuple[str, ...] = Field(min_length=3, max_length=3)
    reviewer_id: str
    reviewer_role: Literal["korean-phonetics-specialist"]
    reviewed_at: str
    source_content_sha256: str
    reviewed_evidence_sha256: str

    @field_validator("item_key", "reviewer_id")
    @classmethod
    def identifiers_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(value, field_name=getattr(info, "field_name", "review identity"))

    @field_validator("scope_ids")
    @classmethod
    def scopes_must_be_bounded(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_identifier(value, field_name="atomization scope") for value in values)

    @field_validator("reviewed_at")
    @classmethod
    def timestamp_must_be_exact(cls, value: str) -> str:
        return _reviewed_at(value)

    @field_validator("source_content_sha256", "reviewed_evidence_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "review hash"))


class _PortuguesePolicyReview(_FrozenEvidenceModel):
    canonical_language_code: Literal["pt"]
    regional_editorial_policy: str
    reviewer_id: str
    reviewer_role: Literal["portuguese-reviewer"]
    reviewed_at: str
    reviewed_evidence_sha256: str

    @field_validator("regional_editorial_policy", "reviewer_id")
    @classmethod
    def identifiers_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(value, field_name=getattr(info, "field_name", "policy identity"))

    @field_validator("reviewed_at")
    @classmethod
    def timestamp_must_be_exact(cls, value: str) -> str:
        return _reviewed_at(value)

    @field_validator("reviewed_evidence_sha256")
    @classmethod
    def hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="policy review hash")


class _CurriculumReview(_FrozenEvidenceModel):
    schema_version: Literal[1] = 1
    review_version: str
    curriculum_request_sha256: str
    proposed_curation_sha256: str
    item_reviews: tuple[_CurriculumItemReview, ...] = Field(min_length=1, max_length=4_096)
    specialist_atomization_reviews: tuple[_SpecialistAtomizationReview, ...] = Field(
        min_length=6,
        max_length=6,
    )
    portuguese_policy: _PortuguesePolicyReview

    @field_validator("review_version")
    @classmethod
    def version_must_be_bounded(cls, value: str) -> str:
        return _identifier(value, field_name="curriculum review version")

    @field_validator("curriculum_request_sha256", "proposed_curation_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "review hash"))


class _RightsRecord(_FrozenEvidenceModel):
    slot_id: str
    media_kind: str
    source_id: str
    source_version: str
    attribution: str = Field(min_length=1, max_length=4_096)
    license_id: str
    reuse_disposition: Literal["approved"]
    redistribution_disposition: Literal["approved"]
    artifact_sha256: str
    reviewed_metadata_sha256: str
    reviewer_id: str
    reviewer_role: Literal["media-rights-reviewer"]
    reviewed_at: str

    @field_validator(
        "slot_id",
        "media_kind",
        "source_id",
        "source_version",
        "license_id",
        "reviewer_id",
    )
    @classmethod
    def identifiers_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(value, field_name=getattr(info, "field_name", "rights identity"))

    @field_validator("artifact_sha256", "reviewed_metadata_sha256")
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "rights hash"))

    @field_validator("reviewed_at")
    @classmethod
    def timestamp_must_be_exact(cls, value: str) -> str:
        return _reviewed_at(value)


class _RightsEvidence(_FrozenEvidenceModel):
    schema_version: Literal[1] = 1
    rights_version: str
    records: tuple[_RightsRecord, ...] = Field(min_length=1, max_length=8_192)

    @field_validator("rights_version")
    @classmethod
    def version_must_be_bounded(cls, value: str) -> str:
        return _identifier(value, field_name="rights version")


class _PlaybackReviewer(_FrozenEvidenceModel):
    reviewer_id: str
    reviewer_role: Literal[
        "audio-playback-reviewer",
        "korean-phonetics-specialist",
        "independent-native-speaker",
    ]
    reviewed_at: str

    @field_validator("reviewer_id")
    @classmethod
    def id_must_be_bounded(cls, value: str) -> str:
        return _identifier(value, field_name="playback reviewer id")

    @field_validator("reviewed_at")
    @classmethod
    def timestamp_must_be_exact(cls, value: str) -> str:
        return _reviewed_at(value)


class _PlaybackRecord(_FrozenEvidenceModel):
    slot_id: str
    media_kind: str
    exact_media_version: str
    display_text_sha256: str
    spoken_text_sha256: str
    text_nfc_sha256: str
    artifact_sha256: str
    metadata_sha256: str
    heard_playback_result: Literal["approved"]
    reviews: tuple[_PlaybackReviewer, ...] = Field(min_length=3, max_length=3)

    @field_validator("slot_id", "media_kind", "exact_media_version")
    @classmethod
    def identifiers_must_be_bounded(cls, value: str, info: object) -> str:
        return _identifier(value, field_name=getattr(info, "field_name", "playback identity"))

    @field_validator(
        "display_text_sha256",
        "spoken_text_sha256",
        "text_nfc_sha256",
        "artifact_sha256",
        "metadata_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "playback hash"))


class _PlaybackEvidence(_FrozenEvidenceModel):
    schema_version: Literal[1] = 1
    playback_version: str
    audio_request_sha256: str
    records: tuple[_PlaybackRecord, ...] = Field(min_length=1, max_length=8_192)

    @field_validator("playback_version")
    @classmethod
    def version_must_be_bounded(cls, value: str) -> str:
        return _identifier(value, field_name="playback version")

    @field_validator("audio_request_sha256")
    @classmethod
    def request_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="audio request hash")


class KoreanFoundationEvidenceInventory(_FrozenEvidenceModel):
    complete: bool
    evidence_member_count: int = Field(ge=0, le=8_193)
    declared_media_count: int = Field(ge=0, le=8_192)
    missing_members: tuple[str, ...] = ()
    unexpected_members: tuple[str, ...] = ()
    index_sha256: str | None = None
    evidence_bundle_sha256: str | None = None


class KoreanFoundationValidationReceipt(_FrozenEvidenceModel):
    schema_version: Literal[1] = 1
    receipt_version: Literal["phase31-korean-foundation-validation-receipt-v1"]
    layout_version: Literal["phase31-korean-foundation-evidence-layout-v1"]
    policy_version: Literal["phase31-korean-foundation-evidence-policy-v1"]
    lock_version: Literal["phase31-korean-foundation-state-lock-v1"]
    continuity_token: str
    confirmed_index_sha256: str
    index_payload_sha256: str
    evidence_bundle_sha256: str
    source_evidence_sha256: str
    reviewer_evidence_sha256: str
    rights_evidence_sha256: str
    media_evidence_sha256: str
    active_prestate_marker: Literal["absent", "present"]
    active_prestate_sha256: str
    payload_sha256: str

    @field_validator(
        "continuity_token",
        "confirmed_index_sha256",
        "index_payload_sha256",
        "evidence_bundle_sha256",
        "source_evidence_sha256",
        "reviewer_evidence_sha256",
        "rights_evidence_sha256",
        "media_evidence_sha256",
        "active_prestate_sha256",
        "payload_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "receipt hash"))

    @model_validator(mode="after")
    def payload_and_continuity_hashes_must_match(self) -> Self:
        payload = self.model_dump(mode="json")
        claimed_payload_hash = payload.pop("payload_sha256")
        if claimed_payload_hash != _canonical_sha256(payload):
            raise ValueError("receipt payload hash does not match")
        continuity = {
            key: value
            for key, value in payload.items()
            if key not in {"schema_version", "receipt_version", "continuity_token"}
        }
        if self.continuity_token != _canonical_sha256(continuity):
            raise ValueError("receipt continuity token does not match")
        return self


class KoreanFoundationReceiptContinuityReport(_FrozenEvidenceModel):
    continuous: Literal[True]
    receipt_sha256: str
    payload_sha256: str
    confirmed_index_sha256: str
    evidence_bundle_sha256: str
    active_prestate_sha256: str

    @field_validator(
        "receipt_sha256",
        "payload_sha256",
        "confirmed_index_sha256",
        "evidence_bundle_sha256",
        "active_prestate_sha256",
    )
    @classmethod
    def hashes_must_be_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(value, field_name=getattr(info, "field_name", "continuity hash"))


@dataclass(frozen=True, slots=True)
class _LayoutAssembly:
    index: KoreanFoundationEvidenceIndex
    index_raw: bytes
    index_sha256: str
    members: dict[str, bytes]
    inventory: KoreanFoundationEvidenceInventory


@dataclass(frozen=True, slots=True)
class _ValidatedEvidence:
    layout: _LayoutAssembly
    state_fingerprint: str
    source_evidence_sha256: str
    reviewer_evidence_sha256: str
    rights_evidence_sha256: str
    media_evidence_sha256: str
    active_prestate_marker: Literal["absent", "present"]
    active_prestate_sha256: str


def _raise(reason_code: KoreanFoundationEvidenceReasonCode) -> None:
    raise KoreanFoundationEvidenceError(reason_code)


def _stat_is_link_or_reparse(value: os.stat_result) -> bool:
    if stat.S_ISLNK(value.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(value, "st_file_attributes", 0) & reparse_flag)


def _assert_no_link_components(
    path: Path,
    *,
    paths: _KoreanFoundationEvidencePaths,
    missing_reason: KoreanFoundationEvidenceReasonCode,
) -> os.stat_result:
    try:
        parts = path.relative_to(paths.project_dir).parts
    except ValueError:
        _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_MEMBER)
    current = paths.project_dir
    try:
        current_stat = current.lstat()
    except OSError:
        _raise(missing_reason)
    if _stat_is_link_or_reparse(current_stat):
        _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    for part in parts:
        current = current / part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            _raise(missing_reason)
        except OSError:
            _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
        if _stat_is_link_or_reparse(current_stat):
            _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    return current_stat


def _read_regular_file(
    path: Path,
    *,
    paths: _KoreanFoundationEvidencePaths,
    maximum_bytes: int,
    missing_reason: KoreanFoundationEvidenceReasonCode,
) -> bytes:
    before = _assert_no_link_components(
        path,
        paths=paths,
        missing_reason=missing_reason,
    )
    if not stat.S_ISREG(before.st_mode):
        _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    if before.st_size > maximum_bytes:
        _raise(KoreanFoundationEvidenceReasonCode.MEMBER_OVERSIZED)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        _raise(missing_reason)
    except OSError:
        _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or _stat_is_link_or_reparse(opened)
            or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
        ):
            _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if len(content) > maximum_bytes:
        _raise(KoreanFoundationEvidenceReasonCode.MEMBER_OVERSIZED)
    if (
        (after.st_dev, after.st_ino, after.st_size)
        != (opened.st_dev, opened.st_ino, opened.st_size)
        or len(content) != opened.st_size
    ):
        _raise(KoreanFoundationEvidenceReasonCode.BETWEEN_STAGE_DRIFT)
    return content


def _has_archive_magic(content: bytes) -> bool:
    return (
        content.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))
        or content.startswith(b"\x1f\x8b")
        or content.startswith(b"7z\xbc\xaf\x27\x1c")
        or content.startswith(b"Rar!\x1a\x07")
        or (len(content) > 262 and content[257:262] == b"ustar")
    )


def _parse_model(
    raw: bytes,
    model_type: type[BaseModel],
    reason_code: KoreanFoundationEvidenceReasonCode,
) -> BaseModel:
    try:
        payload = json.loads(raw.decode("utf-8"))
        return model_type.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KoreanFoundationEvidenceError(reason_code) from exc
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(reason_code) from exc


def _is_external_evidence_member(relpath: str) -> bool:
    return relpath == _MEDIA_AUTHORITY_RELPATH


def _member_path(paths: _KoreanFoundationEvidencePaths, relpath: str) -> Path:
    if _is_external_evidence_member(relpath):
        return paths.phase_dir.joinpath(*PurePosixPath(relpath).parts)
    return paths.inbox.joinpath(*PurePosixPath(relpath).parts)


def _read_index(
    paths: _KoreanFoundationEvidencePaths,
    *,
    confirmed_index_sha256: str | None = None,
) -> tuple[KoreanFoundationEvidenceIndex, bytes, str]:
    try:
        raw = _read_regular_file(
            paths.index,
            paths=paths,
            maximum_bytes=_INDEX_MAX_BYTES,
            missing_reason=KoreanFoundationEvidenceReasonCode.INDEX_MISSING,
        )
    except KoreanFoundationEvidenceError as exc:
        if exc.reason_code is not KoreanFoundationEvidenceReasonCode.INDEX_MISSING:
            raise
        return _derive_current_ai_media_index(
            paths,
            confirmed_index_sha256=confirmed_index_sha256,
        )
    actual_hash = sha256(raw).hexdigest()
    if confirmed_index_sha256 is not None and actual_hash != confirmed_index_sha256:
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_HASH_MISMATCH)
    try:
        payload = json.loads(raw.decode("utf-8"))
        index = KoreanFoundationEvidenceIndex.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.INDEX_INVALID
        ) from exc
    except ValidationError as exc:
        unsafe_locations = {
            error.get("loc", ())[-1]
            for error in exc.errors()
            if error.get("loc")
        }
        reason = (
            KoreanFoundationEvidenceReasonCode.UNSAFE_MEMBER
            if "relpath" in unsafe_locations
            else KoreanFoundationEvidenceReasonCode.INDEX_INVALID
        )
        raise KoreanFoundationEvidenceError(reason) from exc
    except (TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.INDEX_INVALID
        ) from exc
    return index, raw, actual_hash


def _is_current_ai_media_index(index: KoreanFoundationEvidenceIndex) -> bool:
    fixed_count = len(_CURRENT_LAYOUT_FIXED_MEMBER_ROLES)
    return tuple(
        (member.relpath, member.role) for member in index.members[:fixed_count]
    ) == _CURRENT_LAYOUT_FIXED_MEMBER_ROLES


def _validate_current_ai_media_index_contract(
    index: KoreanFoundationEvidenceIndex,
) -> None:
    fixed_count = len(_CURRENT_LAYOUT_FIXED_MEMBER_ROLES)
    tail = index.members[fixed_count:]
    attempts = tuple(member for member in tail if member.role == "ai_review_attempt")
    projections = tuple(member for member in tail if member.role == "ai_review_projection")
    media = tuple(member for member in tail if member.role == "media")
    if (
        len(attempts) != _AI_ATTEMPT_COUNT
        or len(projections) != _AI_PROJECTION_COUNT
        or len(media) != _CURRENT_REQUIRED_MEDIA_COUNT
        or len(tail) != len(attempts) + len(projections) + len(media)
    ):
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)
    expected_attempts = tuple(
        f"ai-review/attempts/batch-{batch:02d}-pass-{pass_number}.json"
        for batch in range(1, 8)
        for pass_number in range(1, 4)
    )
    if tuple(member.relpath for member in attempts) != expected_attempts:
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)
    expected_projections = tuple(
        f"ai-review/projections/batch-{batch:02d}.json" for batch in range(1, 8)
    )
    if tuple(member.relpath for member in projections) != expected_projections:
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)
    basenames: list[str] = []
    for member in media:
        relpath = PurePosixPath(member.relpath)
        if (
            len(relpath.parts) != 3
            or relpath.parts[0] != "media"
            or relpath.parts[1] not in {"hangul", "pronunciation"}
            or relpath.suffix.casefold() not in {".png", ".wav"}
        ):
            _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_MEMBER)
        basenames.append(relpath.name)
    if len(basenames) != len(set(basenames)):
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)


def _validate_index_contract(index: KoreanFoundationEvidenceIndex) -> None:
    if index.index_version != _INDEX_VERSION:
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)
    if tuple(binding.filename for binding in index.candidate_bindings) != (
        _CANDIDATE_FILENAMES
    ):
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)
    if tuple(binding.filename for binding in index.request_bindings) != (
        _REQUEST_FILENAMES
    ):
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)
    if _is_current_ai_media_index(index):
        _validate_current_ai_media_index_contract(index)
        return
    fixed_count = len(_FIXED_MEMBER_ROLES)
    fixed_rows = tuple(
        (member.relpath, member.role) for member in index.members[:fixed_count]
    )
    if fixed_rows != _FIXED_MEMBER_ROLES:
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)
    media_rows = index.members[fixed_count:]
    if len(media_rows) != 509 or any(member.role != "media" for member in media_rows):
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)
    basenames: list[str] = []
    for member in media_rows:
        relpath = PurePosixPath(member.relpath)
        if (
            len(relpath.parts) != 2
            or relpath.parts[0] != "media"
            or relpath.suffix.casefold() not in {".png", ".gif", ".wav"}
        ):
            _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_MEMBER)
        basenames.append(relpath.name)
    if len(basenames) != len(set(basenames)):
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)


def _collect_inbox_tree(
    paths: _KoreanFoundationEvidencePaths,
) -> tuple[set[str], set[str]]:
    inbox_stat = _assert_no_link_components(
        paths.inbox,
        paths=paths,
        missing_reason=KoreanFoundationEvidenceReasonCode.MEMBER_MISSING,
    )
    if not stat.S_ISDIR(inbox_stat.st_mode):
        _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    files: set[str] = set()
    directories: set[str] = set()
    stack = [paths.inbox]
    while stack:
        directory = stack.pop()
        try:
            children = tuple(directory.iterdir())
        except OSError:
            _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
        for child in children:
            try:
                child_stat = child.lstat()
            except OSError:
                _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
            if _stat_is_link_or_reparse(child_stat):
                _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
            relpath = child.relative_to(paths.inbox).as_posix()
            if stat.S_ISDIR(child_stat.st_mode):
                directories.add(relpath)
                stack.append(child)
            elif stat.S_ISREG(child_stat.st_mode):
                files.add(relpath)
            else:
                _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    return files, directories


def _expected_inbox_files(index: KoreanFoundationEvidenceIndex) -> set[str]:
    files = {
        "README.md",
        *(
            member.relpath
            for member in index.members
            if not _is_external_evidence_member(member.relpath)
        ),
    }
    if not _is_current_ai_media_index(index):
        files.add("evidence-index.json")
    return files


def _expected_inbox_directories(index: KoreanFoundationEvidenceIndex) -> set[str]:
    if _is_current_ai_media_index(index):
        return set(_CURRENT_LAYOUT_DIRECTORIES)
    return {"media", "reviewers"}


def _validate_layout(
    paths: _KoreanFoundationEvidencePaths,
    *,
    confirmed_index_sha256: str | None = None,
) -> _LayoutAssembly:
    index, index_raw, index_sha256 = _read_index(
        paths,
        confirmed_index_sha256=confirmed_index_sha256,
    )
    _validate_index_contract(index)
    actual_files, actual_directories = _collect_inbox_tree(paths)
    expected_files = _expected_inbox_files(index)
    expected_directories = _expected_inbox_directories(index)
    if "validation-receipt.json" in actual_files:
        expected_files.add("validation-receipt.json")
    if actual_directories - expected_directories:
        _raise(KoreanFoundationEvidenceReasonCode.UNEXPECTED_MEMBER)
    if expected_directories - actual_directories:
        _raise(KoreanFoundationEvidenceReasonCode.MEMBER_MISSING)
    if actual_files - expected_files:
        _raise(KoreanFoundationEvidenceReasonCode.UNEXPECTED_MEMBER)
    if expected_files - actual_files:
        _raise(KoreanFoundationEvidenceReasonCode.MEMBER_MISSING)

    readme = _read_regular_file(
        paths.inbox / "README.md",
        paths=paths,
        maximum_bytes=262_144,
        missing_reason=KoreanFoundationEvidenceReasonCode.MEMBER_MISSING,
    )
    if not readme:
        _raise(KoreanFoundationEvidenceReasonCode.MEMBER_HASH_MISMATCH)

    members: dict[str, bytes] = {}
    for member in index.members:
        maximum_bytes = (
            _MEDIA_MEMBER_MAX_BYTES if member.role == "media" else _JSON_MEMBER_MAX_BYTES
        )
        member_path = _member_path(paths, member.relpath)
        raw = _read_regular_file(
            member_path,
            paths=paths,
            maximum_bytes=maximum_bytes,
            missing_reason=KoreanFoundationEvidenceReasonCode.MEMBER_MISSING,
        )
        if _has_archive_magic(raw):
            _raise(KoreanFoundationEvidenceReasonCode.ARCHIVE_MEMBER)
        if len(raw) != member.size_bytes or sha256(raw).hexdigest() != member.sha256:
            reason = (
                KoreanFoundationEvidenceReasonCode.MEDIA_HASH_MISMATCH
                if member.role == "media"
                else KoreanFoundationEvidenceReasonCode.MEMBER_HASH_MISMATCH
            )
            _raise(reason)
        members[member.relpath] = raw

    evidence_bundle_sha256 = _canonical_sha256(
        {
            "index_sha256": index_sha256,
            "index_payload_sha256": index.index_payload_sha256,
            "declared_members_sha256": index.declared_members_sha256,
        }
    )
    inventory = KoreanFoundationEvidenceInventory(
        complete=True,
        evidence_member_count=len(index.members) + 1,
        declared_media_count=sum(member.role == "media" for member in index.members),
        missing_members=(),
        unexpected_members=(),
        index_sha256=index_sha256,
        evidence_bundle_sha256=evidence_bundle_sha256,
    )
    return _LayoutAssembly(
        index=index,
        index_raw=index_raw,
        index_sha256=index_sha256,
        members=members,
        inventory=inventory,
    )


def _inspect_inventory(paths: _KoreanFoundationEvidencePaths) -> KoreanFoundationEvidenceInventory:
    try:
        index, _raw, index_sha256 = _read_index(paths)
    except KoreanFoundationEvidenceError as exc:
        if exc.reason_code is not KoreanFoundationEvidenceReasonCode.INDEX_MISSING:
            raise
        actual_files, actual_directories = _collect_inbox_tree(paths)
        unexpected = tuple(
            sorted(actual_files - {"README.md", "validation-receipt.json"})
        )
        if actual_directories:
            unexpected = (*unexpected, *tuple(sorted(actual_directories)))
        return KoreanFoundationEvidenceInventory(
            complete=False,
            evidence_member_count=0,
            declared_media_count=0,
            missing_members=("evidence-index.json",),
            unexpected_members=unexpected,
            index_sha256=None,
            evidence_bundle_sha256=None,
        )
    _validate_index_contract(index)
    actual_files, actual_directories = _collect_inbox_tree(paths)
    expected_files = _expected_inbox_files(index)
    expected_directories = _expected_inbox_directories(index)
    if "validation-receipt.json" in actual_files:
        expected_files.add("validation-receipt.json")
    missing = tuple(sorted(expected_files - actual_files))
    unexpected = tuple(sorted(actual_files - expected_files))
    unexpected_directories = tuple(
        sorted(actual_directories - expected_directories)
    )
    missing_directories = tuple(
        sorted(expected_directories - actual_directories)
    )
    if missing or unexpected or unexpected_directories or missing_directories:
        return KoreanFoundationEvidenceInventory(
            complete=False,
            evidence_member_count=1 + sum(
                member.relpath in actual_files for member in index.members
            ),
            declared_media_count=sum(member.role == "media" for member in index.members),
            missing_members=(*missing_directories, *missing),
            unexpected_members=(*unexpected_directories, *unexpected),
            index_sha256=index_sha256,
            evidence_bundle_sha256=None,
        )
    return _validate_layout(paths).inventory


def _candidate_version(filename: str, model: BaseModel) -> str:
    field_name = {
        "hangul-v2.json": "source_pack_version",
        "pronunciation-i-plus-1-v2.json": "source_pack_version",
        "korean-foundations-v2-curation.json": "manifest_version",
        "korean-foundations-v2-media.json": "manifest_version",
    }[filename]
    return str(getattr(model, field_name))


def _parse_json_object(
    raw: bytes,
    reason_code: KoreanFoundationEvidenceReasonCode,
) -> dict[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KoreanFoundationEvidenceError(reason_code) from exc
    if not isinstance(payload, dict):
        _raise(reason_code)
    return payload


def _binding_by_filename(
    index: KoreanFoundationEvidenceIndex,
) -> dict[str, KoreanFoundationEvidenceCandidateBinding]:
    return {binding.filename: binding for binding in index.candidate_bindings}


def _current_bundle_relpath(index: KoreanFoundationEvidenceIndex) -> str:
    binding = _binding_by_filename(index)[_CURRENT_CANDIDATE_FILENAME]
    if binding.bundle_relpath is None:
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)
    return binding.bundle_relpath


def _candidate_source_path(
    paths: _KoreanFoundationEvidencePaths,
    filename: str,
    *,
    bundle_relpath: str,
) -> Path:
    if filename == _REGISTRY_FILENAME or filename == _CURRENT_CANDIDATE_FILENAME:
        return paths.candidate_dir / filename
    if filename not in {_BUNDLE_MANIFEST_FILENAME, *_CANDIDATE_MEMBER_FILENAMES}:
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    return (
        paths.candidate_dir.joinpath(*PurePosixPath(bundle_relpath).parts)
        / filename
    )


def _read_bound_candidate_file(
    paths: _KoreanFoundationEvidencePaths,
    binding: KoreanFoundationEvidenceCandidateBinding,
    *,
    bundle_relpath: str,
) -> bytes:
    raw = _read_regular_file(
        _candidate_source_path(paths, binding.filename, bundle_relpath=bundle_relpath),
        paths=paths,
        maximum_bytes=_CANDIDATE_MAX_BYTES,
        missing_reason=KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
    )
    if _has_archive_magic(raw) or sha256(raw).hexdigest() != binding.file_sha256:
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    return raw


def _candidate_binding_payload(
    filename: str,
    payload: dict[str, Any],
    raw: bytes,
) -> dict[str, Any]:
    if filename == _CURRENT_CANDIDATE_FILENAME:
        return {
            "filename": filename,
            "bundle_sha256": payload["bundle_sha256"],
            "bundle_relpath": payload["bundle_relpath"],
            "bundle_manifest_sha256": payload["bundle_manifest_sha256"],
            "file_sha256": sha256(raw).hexdigest(),
        }
    if filename == _BUNDLE_MANIFEST_FILENAME:
        return {
            "filename": filename,
            "bundle_sha256": payload["bundle_sha256"],
            "selected_draft_manifest_sha256": payload[
                "selected_draft_manifest_sha256"
            ],
            "draft_validation_sha256": payload["draft_validation_sha256"],
            "file_sha256": sha256(raw).hexdigest(),
            "total_record_count": 139,
            "media_slot_count": 509,
        }

    version_field = {
        "hangul-v2.json": "source_pack_version",
        "pronunciation-i-plus-1-v2.json": "source_pack_version",
        "korean-foundations-v2-curation.json": "manifest_version",
        "korean-foundations-v2-media.json": "manifest_version",
    }[filename]
    binding: dict[str, Any] = {
        "filename": filename,
        "version": payload[version_field],
        "file_sha256": sha256(raw).hexdigest(),
        "canonical_content_sha256": payload["content_hash"],
    }
    if filename == "hangul-v2.json":
        binding["item_count"] = len(payload["entries"])
    elif filename == "pronunciation-i-plus-1-v2.json":
        binding["item_count"] = len(payload["entries"])
    elif filename == "korean-foundations-v2-curation.json":
        records = payload["records"]
        binding["record_count"] = len(records)
        binding["gate_count"] = sum(len(record["gates"]) for record in records)
    else:
        slots = payload["slots"]
        binding["asset_count"] = len(slots)
        binding["required_asset_count"] = sum(slot["required"] for slot in slots)
    return binding


def _current_candidate_bindings(
    paths: _KoreanFoundationEvidencePaths,
) -> tuple[KoreanFoundationEvidenceCandidateBinding, ...]:
    current_raw = _read_regular_file(
        paths.candidate_dir / _CURRENT_CANDIDATE_FILENAME,
        paths=paths,
        maximum_bytes=_CANDIDATE_MAX_BYTES,
        missing_reason=KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
    )
    current_pointer = _parse_json_object(
        current_raw,
        KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
    )
    try:
        bundle_relpath = _safe_relpath(str(current_pointer["bundle_relpath"]))
        raw_by_filename = {_CURRENT_CANDIDATE_FILENAME: current_raw}
        payload_by_filename = {_CURRENT_CANDIDATE_FILENAME: current_pointer}
        for filename in (_BUNDLE_MANIFEST_FILENAME, *_CANDIDATE_MEMBER_FILENAMES):
            raw = _read_regular_file(
                _candidate_source_path(paths, filename, bundle_relpath=bundle_relpath),
                paths=paths,
                maximum_bytes=_CANDIDATE_MAX_BYTES,
                missing_reason=(
                    KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH
                ),
            )
            raw_by_filename[filename] = raw
            payload_by_filename[filename] = _parse_json_object(
                raw,
                KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
            )
        return tuple(
            KoreanFoundationEvidenceCandidateBinding.model_validate(
                _candidate_binding_payload(
                    filename,
                    payload_by_filename[filename],
                    raw_by_filename[filename],
                )
            )
            for filename in _CANDIDATE_FILENAMES
        )
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH
        ) from exc


def _current_request_bindings(
    paths: _KoreanFoundationEvidencePaths,
) -> tuple[KoreanFoundationEvidenceRequestBinding, ...]:
    request_paths = {
        "31-CURRICULUM-REVIEW.md": paths.curriculum_request,
        "31-AUDIO-PLAYBACK-REVIEW.md": paths.audio_request,
    }
    return tuple(
        KoreanFoundationEvidenceRequestBinding(
            filename=filename,
            file_sha256=sha256(
                _read_regular_file(
                    request_paths[filename],
                    paths=paths,
                    maximum_bytes=_REQUEST_MAX_BYTES,
                    missing_reason=(
                        KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH
                    ),
                )
            ).hexdigest(),
        )
        for filename in _REQUEST_FILENAMES
    )


def _evidence_member_row(
    paths: _KoreanFoundationEvidencePaths,
    relpath: str,
    role: str,
) -> dict[str, Any]:
    safe_relpath = _safe_relpath(relpath)
    raw = _read_regular_file(
        _member_path(paths, safe_relpath),
        paths=paths,
        maximum_bytes=(
            _MEDIA_MEMBER_MAX_BYTES if role == "media" else _JSON_MEMBER_MAX_BYTES
        ),
        missing_reason=KoreanFoundationEvidenceReasonCode.MEMBER_MISSING,
    )
    if _has_archive_magic(raw):
        _raise(KoreanFoundationEvidenceReasonCode.ARCHIVE_MEMBER)
    return {
        "relpath": safe_relpath,
        "role": role,
        "size_bytes": len(raw),
        "sha256": sha256(raw).hexdigest(),
    }


def _derive_current_ai_media_index(
    paths: _KoreanFoundationEvidencePaths,
    *,
    confirmed_index_sha256: str | None = None,
) -> tuple[KoreanFoundationEvidenceIndex, bytes, str]:
    actual_files, actual_directories = _collect_inbox_tree(paths)
    required_signature = {
        _AI_POLICY_RELPATH,
        _AI_SUBJECTS_RELPATH,
        _AI_VALIDATORS_RELPATH,
        _AI_AGGREGATE_RELPATH,
        _ACOUSTIC_REVIEW_RELPATH,
        _MEDIA_RIGHTS_RELPATH,
        _MEDIA_ARTIFACTS_RELPATH,
    }
    if not required_signature <= actual_files or not _CURRENT_LAYOUT_DIRECTORIES <= actual_directories:
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_MISSING)
    artifacts = _parse_json_object(
        _read_regular_file(
            _member_path(paths, _MEDIA_ARTIFACTS_RELPATH),
            paths=paths,
            maximum_bytes=_JSON_MEMBER_MAX_BYTES,
            missing_reason=KoreanFoundationEvidenceReasonCode.MEMBER_MISSING,
        ),
        KoreanFoundationEvidenceReasonCode.INDEX_INVALID,
    )
    artifact_rows = artifacts.get("artifacts")
    if not isinstance(artifact_rows, list):
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)

    member_rows = [
        _evidence_member_row(paths, relpath, role)
        for relpath, role in _CURRENT_LAYOUT_FIXED_MEMBER_ROLES
    ]
    member_rows.extend(
        _evidence_member_row(
            paths,
            f"ai-review/attempts/batch-{batch:02d}-pass-{pass_number}.json",
            "ai_review_attempt",
        )
        for batch in range(1, 8)
        for pass_number in range(1, 4)
    )
    member_rows.extend(
        _evidence_member_row(
            paths,
            f"ai-review/projections/batch-{batch:02d}.json",
            "ai_review_projection",
        )
        for batch in range(1, 8)
    )
    try:
        media_relpaths = tuple(
            _safe_relpath(str(row["repository_relpath"]))
            for row in artifact_rows
            if isinstance(row, dict)
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.INDEX_INVALID
        ) from exc
    if len(media_relpaths) != _CURRENT_REQUIRED_MEDIA_COUNT:
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)
    member_rows.extend(
        _evidence_member_row(paths, relpath, "media") for relpath in media_relpaths
    )
    payload: dict[str, Any] = {
        "schema_version": 1,
        "index_version": _INDEX_VERSION,
        "layout_version": KOREAN_FOUNDATION_EVIDENCE_LAYOUT_VERSION,
        "policy_version": KOREAN_FOUNDATION_EVIDENCE_POLICY_VERSION,
        "candidate_bindings": [
            binding.model_dump(mode="json", exclude_none=True)
            for binding in _current_candidate_bindings(paths)
        ],
        "request_bindings": [
            binding.model_dump(mode="json", exclude_none=True)
            for binding in _current_request_bindings(paths)
        ],
        "members": member_rows,
        "declared_members_sha256": _canonical_sha256(member_rows),
    }
    payload["index_payload_sha256"] = _canonical_sha256(payload)
    try:
        index = KoreanFoundationEvidenceIndex.model_validate(payload)
    except ValidationError as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.INDEX_INVALID
        ) from exc
    index_payload = index.model_dump(mode="json", exclude_none=True)
    raw = _json_file_bytes(index_payload)
    actual_hash = sha256(raw).hexdigest()
    if confirmed_index_sha256 is not None and actual_hash != confirmed_index_sha256:
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_HASH_MISMATCH)
    return index, raw, actual_hash


def _assert_current_pointer_binding(
    pointer: dict[str, Any],
    binding: KoreanFoundationEvidenceCandidateBinding,
) -> None:
    if (
        set(pointer) != {
            "schema_version",
            "bundle_sha256",
            "bundle_relpath",
            "bundle_manifest_sha256",
        }
        or pointer.get("schema_version") != 1
        or pointer.get("bundle_sha256") != binding.bundle_sha256
        or pointer.get("bundle_relpath") != binding.bundle_relpath
        or pointer.get("bundle_manifest_sha256") != binding.bundle_manifest_sha256
        or pointer.get("bundle_relpath") != f"candidate-bundles/{binding.bundle_sha256}"
    ):
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)


def _assert_bundle_manifest_binding(
    manifest: dict[str, Any],
    binding: KoreanFoundationEvidenceCandidateBinding,
    member_bindings: dict[str, KoreanFoundationEvidenceCandidateBinding],
) -> None:
    declarations = manifest.get("members")
    if not isinstance(declarations, list):
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    declared_names = tuple(
        declaration.get("name") if isinstance(declaration, dict) else None
        for declaration in declarations
    )
    if declared_names != _CANDIDATE_MEMBER_FILENAMES:
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    declared_hashes = {
        str(declaration["name"]): declaration.get("sha256")
        for declaration in declarations
        if isinstance(declaration, dict) and set(declaration) == {"name", "sha256"}
    }
    if set(declared_hashes) != set(_CANDIDATE_MEMBER_FILENAMES):
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    if any(
        declared_hashes[filename] != member_bindings[filename].file_sha256
        for filename in _CANDIDATE_MEMBER_FILENAMES
    ):
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    if (
        manifest.get("schema_version") != 1
        or manifest.get("bundle_sha256") != binding.bundle_sha256
        or manifest.get("candidate_only") is not True
        or manifest.get("review_status") != "needs_review"
        or manifest.get("promotion_authority") is not False
        or manifest.get("selected_draft_manifest_sha256")
        != binding.selected_draft_manifest_sha256
        or manifest.get("draft_validation_sha256") != binding.draft_validation_sha256
        or manifest.get("total_record_count") != binding.total_record_count
        or manifest.get("media_slot_count") != binding.media_slot_count
        or manifest.get("hangul_record_count") != 92
        or manifest.get("pronunciation_record_count") != 47
    ):
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)


def _assert_member_binding_counts(
    binding: KoreanFoundationEvidenceCandidateBinding,
    model: BaseModel,
) -> None:
    if binding.filename == "hangul-v2.json":
        count_valid = binding.item_count == len(getattr(model, "entries")) == 92
    elif binding.filename == "pronunciation-i-plus-1-v2.json":
        count_valid = binding.item_count == len(getattr(model, "entries")) == 47
    elif binding.filename == "korean-foundations-v2-curation.json":
        records = getattr(model, "records")
        count_valid = (
            binding.record_count == len(records) == 139
            and binding.gate_count
            == sum(len(record.gates) for record in records)
        )
    elif binding.filename == "korean-foundations-v2-media.json":
        slots = getattr(model, "slots")
        count_valid = (
            binding.asset_count == len(slots) == 509
            and binding.required_asset_count
            == sum(slot.required for slot in slots)
        )
    else:
        count_valid = False
    if not count_valid:
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)


def _load_sources(
    paths: _KoreanFoundationEvidencePaths,
    index: KoreanFoundationEvidenceIndex,
) -> tuple[
    KoreanConceptRegistry,
    KoreanHangulSourcePack,
    KoreanPronunciationSourcePack,
    KoreanFoundationCurationManifest,
    KoreanFoundationMediaManifest,
    tuple[bytes, ...],
    tuple[bytes, ...],
]:
    model_types: dict[str, type[BaseModel]] = {
        "hangul-v2.json": KoreanHangulSourcePack,
        "pronunciation-i-plus-1-v2.json": KoreanPronunciationSourcePack,
        "korean-foundations-v2-curation.json": KoreanFoundationCurationManifest,
        "korean-foundations-v2-media.json": KoreanFoundationMediaManifest,
    }
    bindings = _binding_by_filename(index)
    current_binding = bindings[_CURRENT_CANDIDATE_FILENAME]
    bundle_relpath = _current_bundle_relpath(index)
    current_raw = _read_bound_candidate_file(
        paths,
        current_binding,
        bundle_relpath=bundle_relpath,
    )
    current_pointer = _parse_json_object(
        current_raw,
        KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
    )
    _assert_current_pointer_binding(current_pointer, current_binding)
    bundle_binding = bindings[_BUNDLE_MANIFEST_FILENAME]
    bundle_raw = _read_bound_candidate_file(
        paths,
        bundle_binding,
        bundle_relpath=bundle_relpath,
    )
    if current_binding.bundle_manifest_sha256 != sha256(bundle_raw).hexdigest():
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    bundle_manifest = _parse_json_object(
        bundle_raw,
        KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
    )
    _assert_bundle_manifest_binding(bundle_manifest, bundle_binding, bindings)

    registry_raw = _read_regular_file(
        _candidate_source_path(paths, _REGISTRY_FILENAME, bundle_relpath=bundle_relpath),
        paths=paths,
        maximum_bytes=_CANDIDATE_MAX_BYTES,
        missing_reason=KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
    )
    registry = _parse_model(
        registry_raw,
        KoreanConceptRegistry,
        KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
    )
    models: dict[str, BaseModel] = {}
    candidate_raw = [current_raw, bundle_raw]
    for filename in _CANDIDATE_MEMBER_FILENAMES:
        binding = bindings[filename]
        raw = _read_bound_candidate_file(
            paths,
            binding,
            bundle_relpath=bundle_relpath,
        )
        model = _parse_model(
            raw,
            model_types[binding.filename],
            KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
        )
        if (
            _candidate_version(binding.filename, model) != binding.version
            or getattr(model, "content_hash", None)
            != binding.canonical_content_sha256
        ):
            _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
        _assert_member_binding_counts(binding, model)
        candidate_raw.append(raw)
        models[binding.filename] = model

    request_by_filename = {
        "31-CURRICULUM-REVIEW.md": paths.curriculum_request,
        "31-AUDIO-PLAYBACK-REVIEW.md": paths.audio_request,
    }
    request_raw: list[bytes] = []
    for binding in index.request_bindings:
        raw = _read_regular_file(
            request_by_filename[binding.filename],
            paths=paths,
            maximum_bytes=_REQUEST_MAX_BYTES,
            missing_reason=KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
        )
        if _has_archive_magic(raw) or sha256(raw).hexdigest() != binding.file_sha256:
            _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
        request_raw.append(raw)

    hangul = models["hangul-v2.json"]
    pronunciation = models["pronunciation-i-plus-1-v2.json"]
    candidate_curation = models["korean-foundations-v2-curation.json"]
    candidate_media = models["korean-foundations-v2-media.json"]
    assert isinstance(registry, KoreanConceptRegistry)
    assert isinstance(hangul, KoreanHangulSourcePack)
    assert isinstance(pronunciation, KoreanPronunciationSourcePack)
    assert isinstance(candidate_curation, KoreanFoundationCurationManifest)
    assert isinstance(candidate_media, KoreanFoundationMediaManifest)
    try:
        validate_korean_foundation_curation(
            candidate_curation,
            registry=registry,
            hangul_pack=hangul,
            pronunciation_pack=pronunciation,
        )
    except (TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH
        ) from exc
    if not candidate_curation.candidate_only or any(
        gate.status != "needs_review"
        for record in candidate_curation.records
        for gate in record.gates
    ):
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    return (
        registry,
        hangul,
        pronunciation,
        candidate_curation,
        candidate_media,
        tuple(candidate_raw),
        tuple(request_raw),
    )


def _expected_media_rows(
    hangul: KoreanHangulSourcePack,
    pronunciation: KoreanPronunciationSourcePack,
) -> tuple[tuple[object, object, int], ...]:
    rows: list[tuple[object, object, int]] = []
    sequence = 0
    for pack in (hangul, pronunciation):
        for entry in pack.entries:
            for media_slot in entry.media_slots:
                sequence += 1
                rows.append((entry, media_slot, sequence))
    return tuple(rows)


def _manifest_source_identity(
    manifest: KoreanFoundationMediaManifest,
    *,
    registry: KoreanConceptRegistry,
    hangul: KoreanHangulSourcePack,
    pronunciation: KoreanPronunciationSourcePack,
) -> tuple[object, ...]:
    return (
        manifest.registry_version,
        manifest.registry_content_sha256,
        manifest.hangul_source_pack_version,
        manifest.hangul_source_pack_sha256,
        manifest.pronunciation_source_pack_version,
        manifest.pronunciation_source_pack_sha256,
        registry.registry_version,
        registry.content_hash,
        hangul.source_pack_version,
        hangul.content_hash,
        pronunciation.source_pack_version,
        pronunciation.content_hash,
    )


def _validate_media_source_alignment(
    manifest: KoreanFoundationMediaManifest,
    *,
    registry: KoreanConceptRegistry,
    hangul: KoreanHangulSourcePack,
    pronunciation: KoreanPronunciationSourcePack,
) -> tuple[tuple[object, object, int], ...]:
    identity = _manifest_source_identity(
        manifest,
        registry=registry,
        hangul=hangul,
        pronunciation=pronunciation,
    )
    if identity[:6] != identity[6:]:
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    rows = _expected_media_rows(hangul, pronunciation)
    if len(rows) != len(manifest.slots):
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    for slot, (entry, source_slot, sequence) in zip(
        manifest.slots,
        rows,
        strict=True,
    ):
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
            _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    return rows


def _load_reviewers(
    members: dict[str, bytes],
) -> tuple[dict[str, KoreanFoundationReviewerQualification], dict[str, str]]:
    reviewers: dict[str, KoreanFoundationReviewerQualification] = {}
    reviewer_by_role: dict[str, str] = {}
    try:
        for relpath, (primary_role, qualified_roles) in _REVIEWER_ROLE_CONTRACT.items():
            record = KoreanFoundationReviewerQualification.model_validate_json(
                members[relpath]
            )
            if (
                record.primary_role != primary_role
                or record.qualified_roles != qualified_roles
            ):
                _raise(
                    KoreanFoundationEvidenceReasonCode.REVIEWER_QUALIFICATION_INVALID
                )
            reviewers[relpath] = record
            for role in record.qualified_roles:
                if role in reviewer_by_role:
                    _raise(
                        KoreanFoundationEvidenceReasonCode.REVIEWER_QUALIFICATION_INVALID
                    )
                reviewer_by_role[role] = record.reviewer_id
    except KoreanFoundationEvidenceError:
        raise
    except (KeyError, ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.REVIEWER_QUALIFICATION_INVALID
        ) from exc
    identities = tuple(record.reviewer_id for record in reviewers.values())
    if len(identities) != len(set(identities)):
        _raise(KoreanFoundationEvidenceReasonCode.REVIEWER_QUALIFICATION_INVALID)
    if (
        reviewer_by_role.get("korean-phonetics-specialist")
        == reviewer_by_role.get("independent-native-speaker")
    ):
        _raise(KoreanFoundationEvidenceReasonCode.REVIEWER_QUALIFICATION_INVALID)
    return reviewers, reviewer_by_role


def _gate_evidence_sha256(record: object, gate: object) -> str:
    return _canonical_sha256(
        {
            "item_key": record.item_key,
            "gate_name": gate.gate_name,
            "scope_ids": list(gate.scope_ids),
            "source_pack_version": record.source_pack_version,
            "source_content_sha256": record.source_content_sha256,
        }
    )


def _validate_curation_and_curriculum(
    *,
    members: dict[str, bytes],
    registry: KoreanConceptRegistry,
    hangul: KoreanHangulSourcePack,
    pronunciation: KoreanPronunciationSourcePack,
    curriculum_request_raw: bytes,
    reviewer_by_role: dict[str, str],
) -> tuple[KoreanFoundationCurationManifest, _CurriculumReview]:
    proposed_raw = members["proposed-curation.json"]
    try:
        proposed = KoreanFoundationCurationManifest.model_validate_json(proposed_raw)
        validate_korean_foundation_curation(
            proposed,
            registry=registry,
            hangul_pack=hangul,
            pronunciation_pack=pronunciation,
        )
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.REVIEW_INVALID
        ) from exc
    if proposed.candidate_only or len(proposed.records) != 139:
        _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)
    for record in proposed.records:
        for gate in record.gates:
            expected_reviewer = reviewer_by_role.get(str(gate.reviewer_role))
            if (
                gate.status != "approved"
                or expected_reviewer is None
                or gate.reviewer_id != expected_reviewer
                or gate.reviewed_evidence_sha256
                != _gate_evidence_sha256(record, gate)
            ):
                _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)

    try:
        review = _CurriculumReview.model_validate_json(
            members["curriculum-review.json"]
        )
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.REVIEW_INVALID
        ) from exc
    if (
        review.curriculum_request_sha256
        != sha256(curriculum_request_raw).hexdigest()
        or review.proposed_curation_sha256 != sha256(proposed_raw).hexdigest()
        or len(review.item_reviews) != len(proposed.records)
    ):
        _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)

    for record, item_review in zip(
        proposed.records,
        review.item_reviews,
        strict=True,
    ):
        family = record.family.value
        expected_gate_names = _CURRICULUM_GATES[family]
        gates = tuple(
            gate for gate in record.gates if gate.gate_name in expected_gate_names
        )
        if (
            item_review.family != family
            or item_review.item_key != record.item_key
            or item_review.source_pack_version != record.source_pack_version
            or item_review.source_content_sha256 != record.source_content_sha256
            or tuple(gate.gate_name for gate in gates) != expected_gate_names
            or len(item_review.gate_reviews) != len(gates)
        ):
            _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)
        for gate, gate_review in zip(
            gates,
            item_review.gate_reviews,
            strict=True,
        ):
            expected = (
                gate.gate_name,
                gate.scope_ids,
                gate.reviewer_id,
                gate.reviewer_role,
                gate.reviewed_at,
                record.source_content_sha256,
                gate.reviewed_evidence_sha256,
            )
            actual = (
                gate_review.gate_name,
                gate_review.scope_ids,
                gate_review.reviewer_id,
                gate_review.reviewer_role,
                gate_review.reviewed_at,
                gate_review.source_content_sha256,
                gate_review.reviewed_evidence_sha256,
            )
            if actual != expected:
                _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)

    records_by_key = {record.item_key: record for record in proposed.records}
    expected_specialist_ids = tuple(f"ko-pron-{sequence:04d}" for sequence in range(42, 48))
    if tuple(value.item_key for value in review.specialist_atomization_reviews) != (
        expected_specialist_ids
    ):
        _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)
    expected_scopes = (
        "P11-P13-atomization",
        "active-rule-analysis",
        "rule-ordering",
    )
    for sequence, specialist_review in zip(
        range(42, 48),
        review.specialist_atomization_reviews,
        strict=True,
    ):
        record = records_by_key[specialist_review.item_key]
        expected_stage = "P11" if sequence == 42 else "P12" if sequence < 47 else "P13"
        expected_hash = _canonical_sha256(
            {
                "item_key": specialist_review.item_key,
                "source_content_sha256": record.source_content_sha256,
                "scope_ids": list(expected_scopes),
            }
        )
        if (
            specialist_review.stage_id != expected_stage
            or specialist_review.scope_ids != expected_scopes
            or specialist_review.reviewer_id
            != reviewer_by_role["korean-phonetics-specialist"]
            or specialist_review.source_content_sha256
            != record.source_content_sha256
            or specialist_review.reviewed_evidence_sha256 != expected_hash
        ):
            _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)

    policy_payload = review.portuguese_policy.model_dump(mode="json")
    policy_hash = policy_payload.pop("reviewed_evidence_sha256")
    if (
        review.portuguese_policy.reviewer_id
        != reviewer_by_role["portuguese-reviewer"]
        or policy_hash != _canonical_sha256(policy_payload)
    ):
        _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)
    return proposed, review


def _expected_display_text(
    slot: KoreanFoundationMediaSlot,
    entry: KoreanHangulSourceEntry | KoreanPronunciationSourceEntry,
) -> str:
    if slot.family is KoreanFoundationFamily.HANGUL:
        if not isinstance(entry, KoreanHangulSourceEntry):
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        mapping = entry.pedagogical_jamo_mapping
        return mapping.display_glyph if mapping is not None else entry.canonical_jamo_or_block
    if not isinstance(entry, KoreanPronunciationSourceEntry):
        _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
    if slot.media_kind == "letter_audio":
        return entry.spellings
    if slot.media_kind == "word_audio":
        return entry.example_word
    return entry.example_sentence


def _validate_media_header(slot: KoreanFoundationMediaSlot, content: bytes) -> None:
    if slot.output_format == "pcm_s16le_wav":
        try:
            with wave.open(io.BytesIO(content), "rb") as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                frame_count = wav_file.getnframes()
                compression = wav_file.getcomptype()
        except (EOFError, wave.Error) as exc:
            raise KoreanFoundationEvidenceError(
                KoreanFoundationEvidenceReasonCode.MEDIA_INVALID
            ) from exc
        duration_ms = round(frame_count * 1_000 / frame_rate) if frame_rate else 0
        if (
            compression != "NONE"
            or channels not in {1, 2}
            or sample_width != 2
            or not 8_000 <= frame_rate <= 96_000
            or frame_count <= 0
            or duration_ms != slot.duration_ms
        ):
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        return
    if slot.output_format == "png":
        if (
            len(content) < 33
            or not content.startswith(b"\x89PNG\r\n\x1a\n")
            or content[12:16] != b"IHDR"
            or not content.endswith(b"IEND\xaeB`\x82")
        ):
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        width, height = struct.unpack(">II", content[16:24])
        if not 1 <= width <= 8_192 or not 1 <= height <= 8_192:
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        return
    if slot.output_format == "gif":
        if len(content) < 10 or content[:6] not in {b"GIF87a", b"GIF89a"}:
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        width, height = struct.unpack("<HH", content[6:10])
        if not 1 <= width <= 8_192 or not 1 <= height <= 8_192:
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        return
    _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)


def _validate_rights(
    *,
    raw: bytes,
    media_manifest: KoreanFoundationMediaManifest,
    reviewer_by_role: dict[str, str],
) -> _RightsEvidence:
    try:
        rights = _RightsEvidence.model_validate_json(raw)
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.RIGHTS_INVALID
        ) from exc
    if len(rights.records) != len(media_manifest.slots):
        _raise(KoreanFoundationEvidenceReasonCode.RIGHTS_INVALID)
    expected_reviewer = reviewer_by_role["media-rights-reviewer"]
    for record, slot in zip(rights.records, media_manifest.slots, strict=True):
        expected = (
            slot.slot_id,
            slot.media_kind,
            slot.source_id,
            slot.source_version,
            slot.attribution,
            slot.license_id,
            "approved",
            slot.redistribution_disposition,
            slot.artifact_sha256,
            slot.reviewed_metadata_sha256,
            expected_reviewer,
            "media-rights-reviewer",
        )
        actual = (
            record.slot_id,
            record.media_kind,
            record.source_id,
            record.source_version,
            record.attribution,
            record.license_id,
            record.reuse_disposition,
            record.redistribution_disposition,
            record.artifact_sha256,
            record.reviewed_metadata_sha256,
            record.reviewer_id,
            record.reviewer_role,
        )
        if actual != expected:
            _raise(KoreanFoundationEvidenceReasonCode.RIGHTS_INVALID)
    return rights


def _validate_playback(
    *,
    raw: bytes,
    audio_request_raw: bytes,
    media_manifest: KoreanFoundationMediaManifest,
    reviewer_by_role: dict[str, str],
) -> _PlaybackEvidence:
    try:
        playback = _PlaybackEvidence.model_validate_json(raw)
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.PLAYBACK_INVALID
        ) from exc
    audio_slots = tuple(
        slot for slot in media_manifest.slots if slot.media_kind in _AUDIO_KINDS
    )
    if (
        playback.audio_request_sha256 != sha256(audio_request_raw).hexdigest()
        or len(audio_slots) != 233
        or len(playback.records) != len(audio_slots)
    ):
        _raise(KoreanFoundationEvidenceReasonCode.PLAYBACK_INVALID)
    expected_roles = (
        "audio-playback-reviewer",
        "korean-phonetics-specialist",
        "independent-native-speaker",
    )
    for record, slot in zip(playback.records, audio_slots, strict=True):
        if tuple(review.reviewer_role for review in record.reviews) != expected_roles:
            _raise(KoreanFoundationEvidenceReasonCode.PLAYBACK_INVALID)
        if any(
            review.reviewer_id != reviewer_by_role[review.reviewer_role]
            for review in record.reviews
        ):
            _raise(KoreanFoundationEvidenceReasonCode.PLAYBACK_INVALID)
        expected = (
            slot.slot_id,
            slot.media_kind,
            slot.display_text_sha256,
            slot.spoken_text_sha256,
            slot.text_nfc_sha256,
            slot.artifact_sha256,
            slot.metadata_sha256,
        )
        actual = (
            record.slot_id,
            record.media_kind,
            record.display_text_sha256,
            record.spoken_text_sha256,
            record.text_nfc_sha256,
            record.artifact_sha256,
            record.metadata_sha256,
        )
        if actual != expected:
            _raise(KoreanFoundationEvidenceReasonCode.PLAYBACK_INVALID)
        identities = {review.reviewer_role: review.reviewer_id for review in record.reviews}
        if (
            identities["korean-phonetics-specialist"]
            == identities["independent-native-speaker"]
        ):
            _raise(KoreanFoundationEvidenceReasonCode.PLAYBACK_INVALID)
    return playback


def _validate_media_evidence(
    *,
    layout: _LayoutAssembly,
    candidate_media: KoreanFoundationMediaManifest,
    registry: KoreanConceptRegistry,
    hangul: KoreanHangulSourcePack,
    pronunciation: KoreanPronunciationSourcePack,
    audio_request_raw: bytes,
    reviewer_by_role: dict[str, str],
) -> tuple[KoreanFoundationMediaManifest, _RightsEvidence, _PlaybackEvidence]:
    candidate_rows = _validate_media_source_alignment(
        candidate_media,
        registry=registry,
        hangul=hangul,
        pronunciation=pronunciation,
    )
    if not candidate_media.candidate_only or any(
        slot.status != "needs_review" for slot in candidate_media.slots
    ):
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    try:
        proposed = KoreanFoundationMediaManifest.model_validate_json(
            layout.members["proposed-media.json"]
        )
    except (KeyError, ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.MEDIA_INVALID
        ) from exc
    rows = _validate_media_source_alignment(
        proposed,
        registry=registry,
        hangul=hangul,
        pronunciation=pronunciation,
    )
    if proposed.candidate_only or len(proposed.slots) != 509:
        _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
    if tuple(
        (candidate_slot.slot_id, candidate_slot.basename)
        for candidate_slot in candidate_media.slots
    ) != tuple((slot.slot_id, slot.basename) for slot in proposed.slots):
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    if len(candidate_rows) != len(rows):
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)

    indexed_media_paths = tuple(
        member.relpath for member in layout.index.members if member.role == "media"
    )
    expected_media_paths = tuple(f"media/{slot.basename}" for slot in proposed.slots)
    if indexed_media_paths != expected_media_paths:
        _raise(KoreanFoundationEvidenceReasonCode.INDEX_INVALID)

    for slot, (entry, _source_slot, _sequence) in zip(
        proposed.slots,
        rows,
        strict=True,
    ):
        if slot.status != "approved" or slot.display_text != _expected_display_text(
            slot,
            entry,
        ):
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        if any(
            receipt.reviewer_id != reviewer_by_role[receipt.reviewer_role]
            for receipt in slot.review_receipts
        ):
            _raise(KoreanFoundationEvidenceReasonCode.REVIEWER_QUALIFICATION_INVALID)
        relpath = f"media/{slot.basename}"
        content = layout.members[relpath]
        actual_hash = sha256(content).hexdigest()
        if (
            actual_hash != slot.artifact_sha256
            or actual_hash != slot.reviewed_artifact_sha256
        ):
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_HASH_MISMATCH)
        _validate_media_header(slot, content)

    rights = _validate_rights(
        raw=layout.members["rights.json"],
        media_manifest=proposed,
        reviewer_by_role=reviewer_by_role,
    )
    playback = _validate_playback(
        raw=layout.members["audio-playback-review.json"],
        audio_request_raw=audio_request_raw,
        media_manifest=proposed,
        reviewer_by_role=reviewer_by_role,
    )
    return proposed, rights, playback


def _source_evidence_sha256(
    *,
    index: KoreanFoundationEvidenceIndex,
    candidate_raw: tuple[bytes, ...],
    request_raw: tuple[bytes, ...],
) -> str:
    return _canonical_sha256(
        [
            *(
                {
                    "filename": binding.filename,
                    "sha256": sha256(raw).hexdigest(),
                    "canonical_content_sha256": binding.canonical_content_sha256,
                }
                for binding, raw in zip(
                    index.candidate_bindings,
                    candidate_raw,
                    strict=True,
                )
            ),
            *(
                {
                    "filename": binding.filename,
                    "sha256": sha256(raw).hexdigest(),
                }
                for binding, raw in zip(
                    index.request_bindings,
                    request_raw,
                    strict=True,
                )
            ),
        ]
    )


def _current_json_member(
    members: dict[str, bytes],
    relpath: str,
    reason_code: KoreanFoundationEvidenceReasonCode,
) -> dict[str, Any]:
    try:
        return _parse_json_object(members[relpath], reason_code)
    except KeyError as exc:
        raise KoreanFoundationEvidenceError(reason_code) from exc


def _load_current_ai_review(
    layout: _LayoutAssembly,
) -> tuple[AIReviewAggregate, dict[str, AIReviewSubject]]:
    try:
        policy = AIReviewPolicy.model_validate_json(layout.members[_AI_POLICY_RELPATH])
        subjects_payload = _current_json_member(
            layout.members,
            _AI_SUBJECTS_RELPATH,
            KoreanFoundationEvidenceReasonCode.REVIEW_INVALID,
        )
        validators_payload = _current_json_member(
            layout.members,
            _AI_VALIDATORS_RELPATH,
            KoreanFoundationEvidenceReasonCode.REVIEW_INVALID,
        )
        subjects = tuple(
            AIReviewSubject.model_validate(subject)
            for subject in subjects_payload["subjects"]
        )
        validators = tuple(
            AIValidatorRun.model_validate(run)
            for run in validators_payload["validator_runs"]
        )
        attempts = tuple(
            AIReviewAttempt.model_validate_json(layout.members[member.relpath])
            for member in layout.index.members
            if member.role == "ai_review_attempt"
        )
        aggregate = AIReviewAggregate.model_validate_json(
            layout.members[_AI_AGGREGATE_RELPATH]
        )
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.REVIEW_INVALID
        ) from exc

    if (
        subjects_payload.get("schema_version") != 1
        or subjects_payload.get("subject_count") != len(subjects)
        or subjects_payload.get("candidate_sha256") != aggregate.candidate_sha256
        or validators_payload.get("schema_version") != 1
        or validators_payload.get("validator_run_count") != len(validators)
        or sha256(layout.members[_AI_VALIDATORS_RELPATH]).hexdigest()
        != aggregate.validator_manifest_sha256
        or aggregate.candidate_sha256
        != _binding_by_filename(layout.index)[_CURRENT_CANDIDATE_FILENAME].bundle_sha256
        or aggregate.total_subjects != 139
        or aggregate.passing_subjects != 139
        or aggregate.blocked_subjects != 0
        or aggregate.status_counts
        != {
            "ai_review_passed": 139,
            "ai_review_failed": 0,
            "blocked_uncertainty": 0,
            "blocked_disagreement": 0,
            "stale": 0,
        }
        or any(decision.status != "ai_review_passed" for decision in aggregate.decisions)
    ):
        _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)

    try:
        rebuilt = build_ai_review_aggregate(
            policy=policy,
            subjects=subjects,
            validator_runs=validators,
            attempts=attempts,
            candidate_sha256=aggregate.candidate_sha256,
            request_sha256=aggregate.request_sha256,
            validator_manifest_sha256=aggregate.validator_manifest_sha256,
            generated_at=aggregate.generated_at,
        )
    except (TypeError, ValueError, ValidationError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.REVIEW_INVALID
        ) from exc
    if rebuilt != aggregate or aggregate.content_hash != ai_review_content_hash(aggregate):
        _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)

    subjects_by_id = {subject.subject_id: subject for subject in subjects}
    if len(subjects_by_id) != len(subjects):
        _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)
    _validate_current_ai_projections(layout, subjects_by_id)
    return aggregate, subjects_by_id


def _validate_current_ai_projections(
    layout: _LayoutAssembly,
    subjects_by_id: dict[str, AIReviewSubject],
) -> None:
    seen: set[str] = set()
    for batch in range(1, 8):
        relpath = f"ai-review/projections/batch-{batch:02d}.json"
        projection_payload = _current_json_member(
            layout.members,
            relpath,
            KoreanFoundationEvidenceReasonCode.REVIEW_INVALID,
        )
        rows = projection_payload.get("subjects")
        if (
            projection_payload.get("schema_version") != 1
            or projection_payload.get("batch_id") != f"batch-{batch:02d}"
            or tuple(projection_payload.get("required_pass_ids", ()))
            != ("pass-1", "pass-2", "pass-3")
            or not isinstance(rows, list)
            or not rows
        ):
            _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)
        for row in rows:
            if not isinstance(row, dict):
                _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)
            subject_id = row.get("subject_id")
            if not isinstance(subject_id, str) or subject_id in seen:
                _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)
            subject = subjects_by_id.get(subject_id)
            if subject is None:
                _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)
            if (
                tuple(row.get("claim_ids", ())) != subject.claim_ids
                or tuple(row.get("source_reference_ids", ()))
                != subject.source_reference_ids
                or _canonical_sha256(row.get("projection")) != subject.projection_sha256
            ):
                _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)
            seen.add(subject_id)
    if seen != set(subjects_by_id):
        _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)


def _derive_current_curation_manifest(
    *,
    candidate_curation: KoreanFoundationCurationManifest,
    registry: KoreanConceptRegistry,
    hangul: KoreanHangulSourcePack,
    pronunciation: KoreanPronunciationSourcePack,
    aggregate: AIReviewAggregate,
    subjects_by_id: dict[str, AIReviewSubject],
) -> KoreanFoundationCurationManifest:
    decisions_by_id = {decision.subject_id: decision for decision in aggregate.decisions}
    records: list[dict[str, Any]] = []
    for record in candidate_curation.records:
        subject = subjects_by_id.get(record.item_key)
        decision = decisions_by_id.get(record.item_key)
        if (
            subject is None
            or decision is None
            or decision.status != "ai_review_passed"
            or subject.source_pack_version != record.source_pack_version
            or subject.source_content_sha256 != record.source_content_sha256
            or decision.subject_content_sha256 != subject.content_hash
        ):
            _raise(KoreanFoundationEvidenceReasonCode.REVIEW_INVALID)
        record_payload = record.model_dump(mode="json")
        gate_rows: list[dict[str, Any]] = []
        for gate in record.gates:
            gate_payload = gate.model_dump(mode="json")
            gate_payload.update(
                {
                    "status": "ai_review_passed",
                    "reason_code": None,
                    "reviewer_id": None,
                    "reviewer_role": None,
                    "reviewed_at": aggregate.generated_at,
                    "source_pack_version": record.source_pack_version,
                    "source_content_sha256": record.source_content_sha256,
                    "reviewed_evidence_sha256": decision.content_hash,
                }
            )
            gate_rows.append(gate_payload)
        record_payload["gates"] = gate_rows
        records.append(record_payload)
    payload = candidate_curation.model_dump(mode="json")
    payload["candidate_only"] = False
    payload["records"] = records
    payload.pop("content_hash", None)
    payload["content_hash"] = _canonical_sha256(payload)
    try:
        manifest = KoreanFoundationCurationManifest.model_validate(payload)
        validate_korean_foundation_curation(
            manifest,
            registry=registry,
            hangul_pack=hangul,
            pronunciation_pack=pronunciation,
        )
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.REVIEW_INVALID
        ) from exc
    return manifest


def _validated_current_json_content_hash(
    payload: dict[str, Any],
    *,
    hash_field: str = "content_hash",
    hash_payload: object | None = None,
    reason_code: KoreanFoundationEvidenceReasonCode,
) -> None:
    declared = payload.get(hash_field)
    if not isinstance(declared, str):
        _raise(reason_code)
    expected_payload = hash_payload
    if expected_payload is None:
        expected_payload = {key: value for key, value in payload.items() if key != hash_field}
    if declared != _canonical_sha256(expected_payload):
        _raise(reason_code)


def _validate_current_media_authority(
    *,
    media_rights_sha256: str,
    authority_sha256: str,
    authority: dict[str, Any],
) -> None:
    _validated_current_json_content_hash(
        authority,
        reason_code=KoreanFoundationEvidenceReasonCode.RIGHTS_INVALID,
    )
    exact_response = authority.get("exact_supplied_response")
    if (
        authority.get("schema_version") != 1
        or authority.get("handoff_version") != "phase31-handoff-v1"
        or authority.get("kind") != "media-authority"
        or authority.get("actor_type") != "project_owner"
        or authority.get("agent_authored") is not False
        or authority.get("consumed") is not True
        or authority.get("rights_document_sha256") != media_rights_sha256
        or exact_response != f"authorize-media {media_rights_sha256}"
        or authority.get("supplied_response_sha256")
        != sha256(str(exact_response).encode("utf-8")).hexdigest()
        or authority.get("route") != "azure-speech-tts"
        or authority.get("item_count") != _CURRENT_REQUIRED_MEDIA_COUNT
        or authority.get("voice_profile_id") != "ko-KR-SunHiNeural"
        or authority_sha256 != sha256(_json_file_bytes(authority)).hexdigest()
    ):
        _raise(KoreanFoundationEvidenceReasonCode.RIGHTS_INVALID)


def _validate_current_media_rights(
    *,
    rights_sha256: str,
    rights: dict[str, Any],
    authority: dict[str, Any],
    candidate_media: KoreanFoundationMediaManifest,
) -> None:
    _validated_current_json_content_hash(
        rights,
        reason_code=KoreanFoundationEvidenceReasonCode.RIGHTS_INVALID,
    )
    item_set = rights.get("item_set")
    provider_scope = rights.get("provider_scope")
    rights_scope = rights.get("rights_scope")
    if not isinstance(item_set, dict) or not isinstance(provider_scope, dict) or not isinstance(rights_scope, dict):
        _raise(KoreanFoundationEvidenceReasonCode.RIGHTS_INVALID)
    if (
        rights.get("schema_version") != 1
        or rights.get("document_type") != "phase31-media-rights-request"
        or rights.get("status") != "awaiting_project_owner_authorization"
        or rights.get("authority_prompt") != "authorize-media {media-rights-file-sha256}"
        or tuple(rights.get("blockers_until_authorized", ()))
        != ("no-project-owner-media-authority-recorded",)
        or item_set.get("all_slots") != len(candidate_media.slots)
        or item_set.get("required_slots") != _CURRENT_REQUIRED_MEDIA_COUNT
        or item_set.get("audio_subjects") != 233
        or item_set.get("visual_subjects") != 92
        or item_set.get("manifest_content_sha256") != candidate_media.content_hash
        or provider_scope.get("provider_id") != _CURRENT_AUDIO_SOURCE_ID
        or provider_scope.get("route") != authority.get("route")
        or provider_scope.get("locale") != "ko-KR"
        or provider_scope.get("voice_profile_id") != authority.get("voice_profile_id")
        or provider_scope.get("voice_profile_version")
        != authority.get("voice_profile_version")
        or rights_scope.get("human_listening_claim") is not False
        or rights_scope.get("third_party_media_reuse") is not False
        or rights_scope.get("redistribution_disposition")
        != "requires_project_owner_authorization"
        or authority.get("rights_document_sha256") != rights_sha256
    ):
        _raise(KoreanFoundationEvidenceReasonCode.RIGHTS_INVALID)


def _validate_current_acoustic_bindings(
    *,
    layout: _LayoutAssembly,
    candidate_media: KoreanFoundationMediaManifest,
) -> tuple[AIAcousticReviewAggregate, dict[str, Any], dict[str, Any], dict[str, Any]]:
    rights = _current_json_member(
        layout.members,
        _MEDIA_RIGHTS_RELPATH,
        KoreanFoundationEvidenceReasonCode.RIGHTS_INVALID,
    )
    authority = _current_json_member(
        layout.members,
        _MEDIA_AUTHORITY_RELPATH,
        KoreanFoundationEvidenceReasonCode.RIGHTS_INVALID,
    )
    artifacts = _current_json_member(
        layout.members,
        _MEDIA_ARTIFACTS_RELPATH,
        KoreanFoundationEvidenceReasonCode.MEDIA_INVALID,
    )
    rights_sha256 = sha256(layout.members[_MEDIA_RIGHTS_RELPATH]).hexdigest()
    authority_sha256 = sha256(layout.members[_MEDIA_AUTHORITY_RELPATH]).hexdigest()
    _validate_current_media_authority(
        media_rights_sha256=rights_sha256,
        authority_sha256=authority_sha256,
        authority=authority,
    )
    _validate_current_media_rights(
        rights_sha256=rights_sha256,
        rights=rights,
        authority=authority,
        candidate_media=candidate_media,
    )
    artifact_rows = artifacts.get("artifacts")
    if not isinstance(artifact_rows, list):
        _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
    _validated_current_json_content_hash(
        artifacts,
        hash_payload=artifact_rows,
        reason_code=KoreanFoundationEvidenceReasonCode.MEDIA_INVALID,
    )
    try:
        acoustic = AIAcousticReviewAggregate.model_validate_json(
            layout.members[_ACOUSTIC_REVIEW_RELPATH]
        )
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.MEDIA_INVALID
        ) from exc
    if (
        acoustic.aggregate_root != ai_acoustic_review_sha256(acoustic)
        or acoustic.media_rights_sha256 != rights_sha256
        or acoustic.media_authority_sha256 != authority_sha256
        or acoustic.media_artifacts_sha256 != artifacts.get("content_hash")
        or acoustic.item_set_sha256 != rights.get("item_set", {}).get("item_set_sha256")
        or acoustic.item_set_sha256 != artifacts.get("item_set_sha256")
        or acoustic.status != "passing"
        or acoustic.required_slots != _CURRENT_REQUIRED_MEDIA_COUNT
        or acoustic.passing != _CURRENT_REQUIRED_MEDIA_COUNT
        or acoustic.blocked != 0
        or acoustic.audio_subjects != 233
        or acoustic.visual_subjects != 92
        or artifacts.get("media_rights_sha256") != rights_sha256
        or artifacts.get("media_authority_sha256") != authority_sha256
        or artifacts.get("required_slots") != _CURRENT_REQUIRED_MEDIA_COUNT
        or artifacts.get("audio_subjects") != 233
        or artifacts.get("visual_subjects") != 92
    ):
        _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
    return acoustic, rights, authority, artifacts


def _current_projection_text(value: object) -> str:
    if not isinstance(value, str) or not value:
        _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
    normalized = unicodedata.normalize("NFC", value)
    if normalized != value:
        _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
    return value


def _current_display_text(
    slot: KoreanFoundationMediaSlot,
    subject: AIReviewSubject,
) -> str:
    projection = subject.projection
    if slot.family is KoreanFoundationFamily.HANGUL:
        mapping = projection.get("pedagogical_jamo_mapping")
        if isinstance(mapping, dict) and mapping.get("display_glyph") is not None:
            return _current_projection_text(mapping.get("display_glyph"))
        return _current_projection_text(projection.get("canonical_jamo_or_block"))
    if slot.media_kind == "letter_audio":
        return _current_projection_text(projection.get("spellings"))
    if slot.media_kind == "word_audio":
        return _current_projection_text(projection.get("example_word"))
    return _current_projection_text(projection.get("example_sentence"))


def _current_spoken_text(
    *,
    slot: KoreanFoundationMediaSlot,
    subject: AIReviewSubject,
    artifact: dict[str, Any],
    display_text: str,
) -> str | None:
    spoken_hash = artifact.get("spoken_text_sha256")
    if slot.media_kind not in _AUDIO_KINDS:
        if spoken_hash is not None:
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        return None
    if not isinstance(spoken_hash, str):
        _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
    projection = subject.projection
    pronunciation = projection.get("pronunciation_evidence")
    pronunciation_values: tuple[object, ...] = ()
    if isinstance(pronunciation, dict):
        pronunciation_values = (
            pronunciation.get("surface_pronunciation"),
            pronunciation.get("normative_pronunciation"),
        )
    candidates = (
        _HANGUL_AUDIO_TEXT_BY_DISPLAY.get(display_text),
        display_text,
        projection.get("sound"),
        *pronunciation_values,
        projection.get("spellings"),
        projection.get("example_word"),
        projection.get("example_sentence"),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and _text_sha256(candidate) == spoken_hash:
            return _current_projection_text(candidate)
    _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)


def _artifact_by_required_slot(
    *,
    layout: _LayoutAssembly,
    candidate_media: KoreanFoundationMediaManifest,
    artifacts: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    artifact_rows = artifacts.get("artifacts")
    if not isinstance(artifact_rows, list):
        _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
    rows: dict[str, dict[str, Any]] = {}
    required_slots = {slot.slot_id: slot for slot in candidate_media.slots if slot.required}
    for row in artifact_rows:
        if not isinstance(row, dict):
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        slot_id = row.get("slot_id")
        if not isinstance(slot_id, str) or slot_id in rows:
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        slot = required_slots.get(slot_id)
        if slot is None:
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        relpath = row.get("repository_relpath")
        if not isinstance(relpath, str) or _safe_relpath(relpath) != slot.storage_relpath:
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        if (
            row.get("sequence") != slot.sequence
            or row.get("media_kind") != slot.media_kind
            or row.get("source_content_sha256") != slot.source_content_sha256
            or row.get("output_format") != slot.output_format
        ):
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        try:
            content = layout.members[slot.storage_relpath]
        except KeyError as exc:
            raise KoreanFoundationEvidenceError(
                KoreanFoundationEvidenceReasonCode.MEMBER_MISSING
            ) from exc
        if (
            row.get("size_bytes") != len(content)
            or row.get("artifact_sha256") != sha256(content).hexdigest()
        ):
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_HASH_MISMATCH)
        rows[slot_id] = row
    if set(rows) != set(required_slots):
        _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
    return rows


def _derive_current_media_manifest(
    *,
    layout: _LayoutAssembly,
    candidate_media: KoreanFoundationMediaManifest,
    registry: KoreanConceptRegistry,
    hangul: KoreanHangulSourcePack,
    pronunciation: KoreanPronunciationSourcePack,
    subjects_by_id: dict[str, AIReviewSubject],
    authority: dict[str, Any],
    artifacts: dict[str, Any],
) -> KoreanFoundationMediaManifest:
    rows = _validate_media_source_alignment(
        candidate_media,
        registry=registry,
        hangul=hangul,
        pronunciation=pronunciation,
    )
    if not candidate_media.candidate_only or any(
        slot.status != "needs_review" for slot in candidate_media.slots
    ):
        _raise(KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH)
    artifacts_by_slot = _artifact_by_required_slot(
        layout=layout,
        candidate_media=candidate_media,
        artifacts=artifacts,
    )
    slots: list[dict[str, Any]] = []
    for slot, (entry, _source_slot, _sequence) in zip(
        candidate_media.slots,
        rows,
        strict=True,
    ):
        payload = slot.model_dump(mode="json")
        artifact = artifacts_by_slot.get(slot.slot_id)
        if artifact is None:
            slots.append(payload)
            continue
        subject = subjects_by_id.get(slot.item_key)
        if subject is None:
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        display_text = _current_display_text(slot, subject)
        if display_text != _expected_display_text(slot, entry) and slot.family is KoreanFoundationFamily.HANGUL:
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        if _text_sha256(display_text) != artifact.get("display_text_sha256"):
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        spoken_text = _current_spoken_text(
            slot=slot,
            subject=subject,
            artifact=artifact,
            display_text=display_text,
        )
        text_nfc = unicodedata.normalize("NFC", spoken_text or display_text)
        artifact_hash = artifact.get("artifact_sha256")
        source_id = artifact.get("provider_id")
        if not isinstance(artifact_hash, str) or not isinstance(source_id, str):
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        provider_version = None
        if slot.media_kind in _AUDIO_KINDS:
            provider_version = authority.get("voice_profile_version")
            if not isinstance(provider_version, str):
                _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        attribution = (
            _CURRENT_AUDIO_ATTRIBUTION
            if slot.media_kind in _AUDIO_KINDS
            else _CURRENT_VISUAL_ATTRIBUTION
        )
        payload.update(
            {
                "status": "approved",
                "reason_code": None,
                "source_id": source_id,
                "source_version": _CURRENT_MEDIA_SOURCE_VERSION,
                "attribution": attribution,
                "license_id": _CURRENT_MEDIA_LICENSE_ID,
                "redistribution_disposition": "approved",
                "display_text": display_text,
                "spoken_text": spoken_text,
                "text_nfc": text_nfc,
                "display_text_sha256": str(artifact["display_text_sha256"]),
                "spoken_text_sha256": artifact.get("spoken_text_sha256"),
                "text_nfc_sha256": _text_sha256(text_nfc),
                "provider": source_id if slot.media_kind in _AUDIO_KINDS else None,
                "provider_version": provider_version,
                "voice_id": artifact.get("voice_profile_id"),
                "locale": artifact.get("locale"),
                "ssml_sha256": (
                    _SENTINEL_SHA256 if slot.media_kind in _AUDIO_KINDS else None
                ),
                "prosody_sha256": (
                    _SENTINEL_SHA256 if slot.media_kind in _AUDIO_KINDS else None
                ),
                "duration_ms": artifact.get("duration_ms"),
                "artifact_sha256": artifact_hash,
                "reviewed_artifact_sha256": artifact_hash,
                "metadata_sha256": "0" * 64,
                "reviewed_metadata_sha256": "0" * 64,
                "review_receipts": [],
            }
        )
        if slot.media_kind in _AUDIO_KINDS:
            if (
                payload["source_id"] != _CURRENT_AUDIO_SOURCE_ID
                or payload["provider"] != _CURRENT_AUDIO_SOURCE_ID
                or payload["voice_id"] != authority.get("voice_profile_id")
                or payload["locale"] != "ko-KR"
                or not isinstance(payload["duration_ms"], int)
            ):
                _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        elif (
            payload["source_id"] != _CURRENT_VISUAL_SOURCE_ID
            or payload["spoken_text"] is not None
            or payload["spoken_text_sha256"] is not None
            or payload["voice_id"] is not None
            or payload["locale"] is not None
            or payload["duration_ms"] is not None
        ):
            _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
        metadata_sha256 = korean_foundation_media_metadata_sha256(payload)
        payload["metadata_sha256"] = metadata_sha256
        payload["reviewed_metadata_sha256"] = metadata_sha256
        try:
            approved_slot = KoreanFoundationMediaSlot.model_validate(payload)
        except (ValidationError, TypeError, ValueError) as exc:
            raise KoreanFoundationEvidenceError(
                KoreanFoundationEvidenceReasonCode.MEDIA_INVALID
            ) from exc
        content = layout.members[approved_slot.storage_relpath]
        _validate_media_header(approved_slot, content)
        slots.append(approved_slot.model_dump(mode="json"))

    manifest_payload = candidate_media.model_dump(mode="json")
    manifest_payload["candidate_only"] = False
    manifest_payload["slots"] = slots
    manifest_payload.pop("content_hash", None)
    manifest_payload["content_hash"] = korean_foundation_media_manifest_sha256(
        manifest_payload
    )
    try:
        manifest = KoreanFoundationMediaManifest.model_validate(manifest_payload)
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.MEDIA_INVALID
        ) from exc
    if (
        sum(slot.required and slot.status == "approved" for slot in manifest.slots)
        != _CURRENT_REQUIRED_MEDIA_COUNT
        or sum((not slot.required) and slot.status == "needs_review" for slot in manifest.slots)
        != 184
    ):
        _raise(KoreanFoundationEvidenceReasonCode.MEDIA_INVALID)
    return manifest


def _read_active_prestate(
    paths: _KoreanFoundationEvidencePaths,
) -> tuple[Literal["absent", "present"], str]:
    try:
        paths.active_pointer.lstat()
    except FileNotFoundError:
        return "absent", _ABSENT_PRESTATE_SHA256
    except OSError as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.ACTIVE_PRESTATE_INVALID
        ) from exc
    raw = _read_regular_file(
        paths.active_pointer,
        paths=paths,
        maximum_bytes=4_096,
        missing_reason=KoreanFoundationEvidenceReasonCode.ACTIVE_PRESTATE_INVALID,
    )
    try:
        KoreanFoundationActivePointer.model_validate_json(raw)
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.ACTIVE_PRESTATE_INVALID
        ) from exc
    return "present", sha256(raw).hexdigest()


def _fingerprint_file(
    *,
    label: str,
    path: Path,
    paths: _KoreanFoundationEvidencePaths,
    maximum_bytes: int,
    optional: bool = False,
    missing_reason: KoreanFoundationEvidenceReasonCode = (
        KoreanFoundationEvidenceReasonCode.MEMBER_MISSING
    ),
) -> tuple[object, ...]:
    try:
        path.lstat()
    except FileNotFoundError:
        if optional:
            return (label, "absent")
        _raise(missing_reason)
    except OSError:
        _raise(KoreanFoundationEvidenceReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    raw = _read_regular_file(
        path,
        paths=paths,
        maximum_bytes=maximum_bytes,
        missing_reason=KoreanFoundationEvidenceReasonCode.BETWEEN_STAGE_DRIFT,
    )
    try:
        current = path.lstat()
    except OSError:
        _raise(KoreanFoundationEvidenceReasonCode.BETWEEN_STAGE_DRIFT)
    return (
        label,
        "present",
        current.st_dev,
        current.st_ino,
        current.st_size,
        current.st_mtime_ns,
        sha256(raw).hexdigest(),
    )


def _capture_state_fingerprint(
    paths: _KoreanFoundationEvidencePaths,
    index: KoreanFoundationEvidenceIndex,
) -> str:
    files, directories = _collect_inbox_tree(paths)
    rows: list[tuple[object, ...]] = [
        ("inbox-files", *sorted(files)),
        ("inbox-directories", *sorted(directories)),
        _fingerprint_file(
            label="inbox/README.md",
            path=paths.inbox / "README.md",
            paths=paths,
            maximum_bytes=262_144,
        ),
        _fingerprint_file(
            label="inbox/evidence-index.json",
            path=paths.index,
            paths=paths,
            maximum_bytes=_INDEX_MAX_BYTES,
            optional=_is_current_ai_media_index(index),
        ),
    ]
    for member in index.members:
        rows.append(
            _fingerprint_file(
                label=member.relpath,
                path=_member_path(paths, member.relpath),
                paths=paths,
                maximum_bytes=(
                    _MEDIA_MEMBER_MAX_BYTES
                    if member.role == "media"
                    else _JSON_MEMBER_MAX_BYTES
                ),
            )
        )
    bundle_relpath = _current_bundle_relpath(index)
    for filename in _CANDIDATE_FILENAMES:
        rows.append(
            _fingerprint_file(
                label=f"candidate/{filename}",
                path=_candidate_source_path(
                    paths,
                    filename,
                    bundle_relpath=bundle_relpath,
                ),
                paths=paths,
                maximum_bytes=_CANDIDATE_MAX_BYTES,
                missing_reason=KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
            )
        )
    rows.append(
        _fingerprint_file(
            label=f"candidate/{_REGISTRY_FILENAME}",
            path=_candidate_source_path(
                paths,
                _REGISTRY_FILENAME,
                bundle_relpath=bundle_relpath,
            ),
            paths=paths,
            maximum_bytes=_CANDIDATE_MAX_BYTES,
            missing_reason=KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
        )
    )
    for filename, path in (
        ("31-CURRICULUM-REVIEW.md", paths.curriculum_request),
        ("31-AUDIO-PLAYBACK-REVIEW.md", paths.audio_request),
    ):
        rows.append(
            _fingerprint_file(
                label=f"request/{filename}",
                path=path,
                paths=paths,
                maximum_bytes=_REQUEST_MAX_BYTES,
                missing_reason=KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH,
            )
        )
    rows.append(
        _fingerprint_file(
            label="validation-receipt",
            path=paths.receipt,
            paths=paths,
            maximum_bytes=_RECEIPT_MAX_BYTES,
            optional=True,
        )
    )
    rows.append(
        _fingerprint_file(
            label="active-prestate",
            path=paths.active_pointer,
            paths=paths,
            maximum_bytes=4_096,
            optional=True,
        )
    )
    return _canonical_sha256(rows)


def _validate_fixed_evidence(
    paths: _KoreanFoundationEvidencePaths,
    *,
    confirmed_index_sha256: str,
) -> _ValidatedEvidence:
    preliminary_index, _preliminary_raw, preliminary_hash = _read_index(
        paths,
        confirmed_index_sha256=confirmed_index_sha256,
    )
    _validate_index_contract(preliminary_index)
    initial_fingerprint = _capture_state_fingerprint(paths, preliminary_index)
    layout = _validate_layout(
        paths,
        confirmed_index_sha256=confirmed_index_sha256,
    )
    if layout.index != preliminary_index or layout.index_sha256 != preliminary_hash:
        _raise(KoreanFoundationEvidenceReasonCode.BETWEEN_STAGE_DRIFT)

    (
        registry,
        hangul,
        pronunciation,
        candidate_curation,
        candidate_media,
        candidate_raw,
        request_raw,
    ) = _load_sources(paths, layout.index)
    if _is_current_ai_media_index(layout.index):
        ai_aggregate, subjects_by_id = _load_current_ai_review(layout)
        curation_manifest = _derive_current_curation_manifest(
            candidate_curation=candidate_curation,
            registry=registry,
            hangul=hangul,
            pronunciation=pronunciation,
            aggregate=ai_aggregate,
            subjects_by_id=subjects_by_id,
        )
        acoustic_aggregate, _rights, authority, artifacts = (
            _validate_current_acoustic_bindings(
                layout=layout,
                candidate_media=candidate_media,
            )
        )
        media_manifest = _derive_current_media_manifest(
            layout=layout,
            candidate_media=candidate_media,
            registry=registry,
            hangul=hangul,
            pronunciation=pronunciation,
            subjects_by_id=subjects_by_id,
            authority=authority,
            artifacts=artifacts,
        )
        layout.members["proposed-curation.json"] = _json_file_bytes(curation_manifest)
        layout.members["proposed-media.json"] = _json_file_bytes(media_manifest)
        source_evidence_sha256 = _source_evidence_sha256(
            index=layout.index,
            candidate_raw=candidate_raw,
            request_raw=request_raw,
        )
        reviewer_evidence_sha256 = ai_aggregate.aggregate_root
        rights_evidence_sha256 = sha256(layout.members[_MEDIA_RIGHTS_RELPATH]).hexdigest()
        media_evidence_sha256 = acoustic_aggregate.aggregate_root
    else:
        reviewers, reviewer_by_role = _load_reviewers(layout.members)
        _validate_curation_and_curriculum(
            members=layout.members,
            registry=registry,
            hangul=hangul,
            pronunciation=pronunciation,
            curriculum_request_raw=request_raw[0],
            reviewer_by_role=reviewer_by_role,
        )
        media_manifest, _rights, _playback = _validate_media_evidence(
            layout=layout,
            candidate_media=candidate_media,
            registry=registry,
            hangul=hangul,
            pronunciation=pronunciation,
            audio_request_raw=request_raw[1],
            reviewer_by_role=reviewer_by_role,
        )
        source_evidence_sha256 = _source_evidence_sha256(
            index=layout.index,
            candidate_raw=candidate_raw,
            request_raw=request_raw,
        )
        reviewer_paths = (
            "proposed-curation.json",
            "curriculum-review.json",
            *_REVIEWER_ROLE_CONTRACT,
        )
        reviewer_evidence_sha256 = _canonical_sha256(
            [
                {
                    "relpath": relpath,
                    "sha256": sha256(layout.members[relpath]).hexdigest(),
                }
                for relpath in reviewer_paths
            ]
        )
        rights_evidence_sha256 = sha256(layout.members["rights.json"]).hexdigest()
        media_evidence_sha256 = _canonical_sha256(
            [
                {
                    "relpath": "proposed-media.json",
                    "sha256": sha256(layout.members["proposed-media.json"]).hexdigest(),
                },
                {
                    "relpath": "audio-playback-review.json",
                    "sha256": sha256(
                        layout.members["audio-playback-review.json"]
                    ).hexdigest(),
                },
                *(
                    {
                        "relpath": f"media/{slot.basename}",
                        "sha256": slot.artifact_sha256,
                    }
                    for slot in media_manifest.slots
                ),
            ]
        )
    active_marker, active_hash = _read_active_prestate(paths)
    final_fingerprint = _capture_state_fingerprint(paths, layout.index)
    if final_fingerprint != initial_fingerprint:
        _raise(KoreanFoundationEvidenceReasonCode.BETWEEN_STAGE_DRIFT)
    if not _is_current_ai_media_index(layout.index) and len(reviewers) != 4:
        _raise(KoreanFoundationEvidenceReasonCode.REVIEWER_QUALIFICATION_INVALID)
    return _ValidatedEvidence(
        layout=layout,
        state_fingerprint=final_fingerprint,
        source_evidence_sha256=source_evidence_sha256,
        reviewer_evidence_sha256=reviewer_evidence_sha256,
        rights_evidence_sha256=rights_evidence_sha256,
        media_evidence_sha256=media_evidence_sha256,
        active_prestate_marker=active_marker,
        active_prestate_sha256=active_hash,
    )


def _derive_receipt(value: _ValidatedEvidence) -> KoreanFoundationValidationReceipt:
    payload: dict[str, object] = {
        "schema_version": 1,
        "receipt_version": _RECEIPT_VERSION,
        "layout_version": KOREAN_FOUNDATION_EVIDENCE_LAYOUT_VERSION,
        "policy_version": KOREAN_FOUNDATION_EVIDENCE_POLICY_VERSION,
        "lock_version": KOREAN_FOUNDATION_STATE_LOCK_VERSION,
        "confirmed_index_sha256": value.layout.index_sha256,
        "index_payload_sha256": value.layout.index.index_payload_sha256,
        "evidence_bundle_sha256": value.layout.inventory.evidence_bundle_sha256,
        "source_evidence_sha256": value.source_evidence_sha256,
        "reviewer_evidence_sha256": value.reviewer_evidence_sha256,
        "rights_evidence_sha256": value.rights_evidence_sha256,
        "media_evidence_sha256": value.media_evidence_sha256,
        "active_prestate_marker": value.active_prestate_marker,
        "active_prestate_sha256": value.active_prestate_sha256,
    }
    continuity = {
        key: item
        for key, item in payload.items()
        if key not in {"schema_version", "receipt_version"}
    }
    payload["continuity_token"] = _canonical_sha256(continuity)
    payload["payload_sha256"] = _canonical_sha256(payload)
    return KoreanFoundationValidationReceipt.model_validate(payload)


def _assert_state_unchanged(
    paths: _KoreanFoundationEvidencePaths,
    value: _ValidatedEvidence,
) -> None:
    try:
        current = _capture_state_fingerprint(paths, value.layout.index)
    except KoreanFoundationEvidenceError as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.BETWEEN_STAGE_DRIFT
        ) from exc
    if current != value.state_fingerprint:
        _raise(KoreanFoundationEvidenceReasonCode.BETWEEN_STAGE_DRIFT)


def _default_stage_hook(
    _stage: str,
    _paths: _KoreanFoundationEvidencePaths,
) -> None:
    return None


_PRIVATE_STAGE_HOOK: Callable[[str, _KoreanFoundationEvidencePaths], None] = (
    _default_stage_hook
)


def _receipt_exists(paths: _KoreanFoundationEvidencePaths) -> bool:
    try:
        paths.receipt.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        _raise(KoreanFoundationEvidenceReasonCode.STALE_RECEIPT)
    return True


def _read_existing_receipt(
    paths: _KoreanFoundationEvidencePaths,
    *,
    missing_reason: KoreanFoundationEvidenceReasonCode,
) -> bytes:
    return _read_regular_file(
        paths.receipt,
        paths=paths,
        maximum_bytes=_RECEIPT_MAX_BYTES,
        missing_reason=missing_reason,
    )


def _fsync_parent_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _atomic_write_receipt(
    paths: _KoreanFoundationEvidencePaths,
    raw: bytes,
) -> None:
    descriptor = -1
    temporary_name: str | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".validation-receipt.",
            suffix=".tmp",
            dir=paths.inbox,
        )
        try:
            os.fchmod(descriptor, 0o600)
        except (AttributeError, OSError):
            pass
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, paths.receipt)
        temporary_name = None
        _fsync_parent_directory(paths.inbox)
    except KoreanFoundationEvidenceError:
        raise
    except OSError as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.ATOMIC_WRITE_FAILED
        ) from exc
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            except OSError:
                pass


def inspect_fixed_korean_foundation_evidence_inbox() -> KoreanFoundationEvidenceInventory:
    """Inspect only the fixed local evidence inbox without creating state."""

    return _inspect_inventory(_FIXED_PATHS)


def validate_and_write_fixed_korean_foundation_validation_receipt(
    *,
    confirmed_index_sha256: str,
) -> KoreanFoundationValidationReceipt:
    """Freshly validate fixed evidence and atomically mint one exact receipt."""

    try:
        _sha256_text(confirmed_index_sha256, field_name="confirmed index hash")
    except ValueError as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.INDEX_INVALID
        ) from exc
    paths = _FIXED_PATHS
    with _korean_foundation_state_lock(paths.project_dir):
        validated = _validate_fixed_evidence(
            paths,
            confirmed_index_sha256=confirmed_index_sha256,
        )
        _PRIVATE_STAGE_HOOK("after_validation", paths)
        _assert_state_unchanged(paths, validated)

        receipt = _derive_receipt(validated)
        receipt_raw = _json_file_bytes(receipt)
        _PRIVATE_STAGE_HOOK("after_payload_derivation", paths)
        _assert_state_unchanged(paths, validated)

        if _receipt_exists(paths):
            try:
                existing = _read_existing_receipt(
                    paths,
                    missing_reason=KoreanFoundationEvidenceReasonCode.STALE_RECEIPT,
                )
            except KoreanFoundationEvidenceError as exc:
                raise KoreanFoundationEvidenceError(
                    KoreanFoundationEvidenceReasonCode.STALE_RECEIPT
                ) from exc
            if existing == receipt_raw:
                object.__setattr__(
                    receipt,
                    "_receipt_write_status",
                    "already_current",
                )
                return receipt
            _raise(KoreanFoundationEvidenceReasonCode.STALE_RECEIPT)

        _PRIVATE_STAGE_HOOK("before_write", paths)
        _assert_state_unchanged(paths, validated)
        _atomic_write_receipt(paths, receipt_raw)
        object.__setattr__(receipt, "_receipt_write_status", "written")
        return receipt


def check_korean_foundation_validation_receipt_continuity(
    *,
    expected_receipt_sha256: str,
) -> KoreanFoundationReceiptContinuityReport:
    """Revalidate a fixed receipt and current authority using read-only operations."""

    try:
        _sha256_text(expected_receipt_sha256, field_name="expected receipt hash")
    except ValueError as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.RECEIPT_HASH_MISMATCH
        ) from exc
    paths = _FIXED_PATHS
    raw = _read_existing_receipt(
        paths,
        missing_reason=KoreanFoundationEvidenceReasonCode.RECEIPT_MISSING,
    )
    actual_receipt_sha256 = sha256(raw).hexdigest()
    if actual_receipt_sha256 != expected_receipt_sha256:
        _raise(KoreanFoundationEvidenceReasonCode.RECEIPT_HASH_MISMATCH)
    try:
        receipt = KoreanFoundationValidationReceipt.model_validate_json(raw)
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.RECEIPT_INVALID
        ) from exc
    try:
        validated = _validate_fixed_evidence(
            paths,
            confirmed_index_sha256=receipt.confirmed_index_sha256,
        )
        expected = _derive_receipt(validated)
        if expected != receipt:
            _raise(KoreanFoundationEvidenceReasonCode.CONTINUITY_DRIFT)
        if (
            _capture_state_fingerprint(paths, validated.layout.index)
            != validated.state_fingerprint
        ):
            _raise(KoreanFoundationEvidenceReasonCode.CONTINUITY_DRIFT)
    except KoreanFoundationEvidenceError as exc:
        if exc.reason_code is KoreanFoundationEvidenceReasonCode.CONTINUITY_DRIFT:
            raise
        raise KoreanFoundationEvidenceError(
            KoreanFoundationEvidenceReasonCode.CONTINUITY_DRIFT
        ) from exc
    return KoreanFoundationReceiptContinuityReport(
        continuous=True,
        receipt_sha256=actual_receipt_sha256,
        payload_sha256=receipt.payload_sha256,
        confirmed_index_sha256=receipt.confirmed_index_sha256,
        evidence_bundle_sha256=receipt.evidence_bundle_sha256,
        active_prestate_sha256=receipt.active_prestate_sha256,
    )


__all__ = [
    "KOREAN_FOUNDATION_EVIDENCE_LAYOUT_VERSION",
    "KOREAN_FOUNDATION_EVIDENCE_POLICY_VERSION",
    "KOREAN_FOUNDATION_STATE_LOCK_VERSION",
    "PHASE31_EVIDENCE_INDEX",
    "PHASE31_EVIDENCE_INBOX",
    "PHASE31_VALIDATION_RECEIPT",
    "KoreanFoundationEvidenceCandidateBinding",
    "KoreanFoundationEvidenceError",
    "KoreanFoundationEvidenceIndex",
    "KoreanFoundationEvidenceInventory",
    "KoreanFoundationEvidenceMember",
    "KoreanFoundationEvidenceReasonCode",
    "KoreanFoundationReceiptContinuityReport",
    "KoreanFoundationReviewerQualification",
    "KoreanFoundationValidationReceipt",
    "check_korean_foundation_validation_receipt_continuity",
    "inspect_fixed_korean_foundation_evidence_inbox",
    "validate_and_write_fixed_korean_foundation_validation_receipt",
]
