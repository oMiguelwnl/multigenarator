"""Fixed, single-resolution reader for immutable Korean foundation snapshots."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
from typing import Any, Final, Literal, Self, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from multilang.services._korean_foundation_state_lock import (
    _korean_foundation_state_lock,
)
from multilang.services.korean_curriculum import (
    KoreanConceptRegistry,
    KoreanHangulSourcePack,
    KoreanPronunciationSourcePack,
)
from multilang.services.korean_foundation_review import (
    KoreanFoundationCurationManifest,
    KoreanFoundationReviewError,
    validate_korean_foundation_curation,
)


ACTIVE_KOREAN_FOUNDATIONS_POINTER_PATH: Final = (
    Path("data") / "korean_foundations" / "active-foundations.json"
)
KOREAN_FOUNDATION_SNAPSHOT_ROOT: Final = (
    Path("data") / "korean_foundations" / "snapshots"
)
KOREAN_FOUNDATION_SNAPSHOT_CONTRACT_VERSION: Final = (
    "phase31-korean-foundation-snapshot-v2"
)
KOREAN_FOUNDATION_PREPARED_VERIFICATION_VERSION: Final = (
    "phase31-korean-foundation-prepared-verification-v1"
)
KOREAN_FOUNDATION_ACTIVATION_AUTHORIZATION_VERSION: Final = (
    "phase31-korean-foundation-activation-authorization-v1"
)
KOREAN_FOUNDATION_ACTIVE_POINTER_VERSION: Final = (
    "phase31-korean-foundation-active-pointer-v2"
)
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
_POINTER_MAX_BYTES: Final = 4_096
_SNAPSHOT_MANIFEST_MAX_BYTES: Final = 262_144
_SNAPSHOT_MEMBER_MAX_BYTES: Final = 32 * 1_048_576
_SNAPSHOT_TOTAL_MAX_BYTES: Final = 512 * 1_048_576
_SNAPSHOT_MAX_MEMBERS: Final = 8_192
_MAX_RELPATH_LENGTH: Final = 512
_LOWERCASE_HEX: Final = frozenset("0123456789abcdef")
_ARCHIVE_SUFFIXES: Final = frozenset(
    {".apkg", ".zip", ".tar", ".tgz", ".gz", ".bz2", ".7z", ".rar"}
)
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
_REVIEW_EVIDENCE_RELPATHS: Final = (
    "curriculum-review.json",
    "audio-playback-review.json",
    "rights.json",
    "reviewers/korean-orthography.json",
    "reviewers/korean-phonetics.json",
    "reviewers/portuguese.json",
    "reviewers/independent-native-speaker.json",
)


@dataclass(frozen=True, slots=True)
class _KoreanFoundationSnapshotPaths:
    project_dir: Path
    candidate_dir: Path
    phase_dir: Path
    inbox: Path
    receipt: Path
    snapshot_root: Path
    active_pointer: Path

    @classmethod
    def from_project_root(
        cls,
        project_dir: Path,
    ) -> "_KoreanFoundationSnapshotPaths":
        candidate_dir = project_dir / "data" / "korean_foundations"
        phase_dir = project_dir / _PHASE_RELPATH
        inbox = phase_dir / "evidence-inbox"
        return cls(
            project_dir=project_dir,
            candidate_dir=candidate_dir,
            phase_dir=phase_dir,
            inbox=inbox,
            receipt=inbox / "validation-receipt.json",
            snapshot_root=candidate_dir / "snapshots",
            active_pointer=candidate_dir / "active-foundations.json",
        )


_FIXED_PATHS = _KoreanFoundationSnapshotPaths.from_project_root(_PROJECT_ROOT)

_SnapshotRole: TypeAlias = Literal[
    "concept_registry",
    "hangul_source_pack",
    "pronunciation_source_pack",
    "curation_manifest",
    "media_manifest",
    "review_evidence",
    "media",
]
_SINGLETON_ROLES: Final = (
    "concept_registry",
    "hangul_source_pack",
    "pronunciation_source_pack",
    "curation_manifest",
    "media_manifest",
)


class KoreanFoundationSnapshotReasonCode(str, Enum):
    """Content-free active-pointer and immutable-tree failures."""

    PRODUCTION_NOT_ACTIVE = "production_not_active"
    ACTIVE_POINTER_MALFORMED = "active_pointer_malformed"
    ACTIVE_POINTER_OVERSIZED = "active_pointer_oversized"
    ACTIVE_POINTER_INVALID = "active_pointer_invalid"
    UNSAFE_SNAPSHOT_PATH = "unsafe_snapshot_path"
    UNSAFE_FILESYSTEM_COMPONENT = "unsafe_filesystem_component"
    BUNDLE_NAME_MISMATCH = "bundle_name_mismatch"
    SNAPSHOT_MANIFEST_MISSING = "snapshot_manifest_missing"
    SNAPSHOT_MANIFEST_MALFORMED = "snapshot_manifest_malformed"
    SNAPSHOT_MANIFEST_OVERSIZED = "snapshot_manifest_oversized"
    SNAPSHOT_MANIFEST_INVALID = "snapshot_manifest_invalid"
    SNAPSHOT_MANIFEST_HASH_MISMATCH = "snapshot_manifest_hash_mismatch"
    SNAPSHOT_MEMBER_MISSING = "snapshot_member_missing"
    SNAPSHOT_MEMBER_HASH_MISMATCH = "snapshot_member_hash_mismatch"
    SNAPSHOT_MEMBER_INVALID = "snapshot_member_invalid"
    SNAPSHOT_EXTRA_MEMBER = "snapshot_extra_member"
    RECEIPT_MISSING = "receipt_missing"
    RECEIPT_HASH_MISMATCH = "receipt_hash_mismatch"
    RECEIPT_INVALID = "receipt_invalid"
    AUTHORITY_DRIFT = "authority_drift"
    ACTIVE_PRESTATE_DRIFT = "active_prestate_drift"
    SNAPSHOT_ROOT_HASH_MISMATCH = "snapshot_root_hash_mismatch"
    IMMUTABLE_SNAPSHOT_COLLISION = "immutable_snapshot_collision"
    SNAPSHOT_PREPARATION_FAILED = "snapshot_preparation_failed"
    AUTHORIZATION_INVALID = "authorization_invalid"
    ACTIVATION_AUTHORIZATION_MISMATCH = "activation_authorization_mismatch"
    ACTIVATION_FAILED = "activation_failed"
    ACTIVE_PROVENANCE_INVALID = "active_provenance_invalid"


class KoreanFoundationSnapshotError(ValueError):
    """A public snapshot failure that never includes paths or member content."""

    def __init__(self, reason_code: KoreanFoundationSnapshotReasonCode) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code.value)


class _FrozenSnapshotModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        arbitrary_types_allowed=True,
    )


def _sha256_text(value: str, *, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEX for character in value)
    ):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _safe_relpath(value: str, *, allow_archive: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError("snapshot path must be repository-relative")
    if (
        not value
        or value != value.strip()
        or len(value) > _MAX_RELPATH_LENGTH
        or value.startswith(("/", "~"))
        or "\\" in value
        or ":" in value
        or "\x00" in value
        or "//" in value
    ):
        raise ValueError("snapshot path must be repository-relative")
    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError("snapshot path must be repository-relative")
    path = PurePosixPath(value)
    if path.is_absolute() or tuple(path.parts) != tuple(raw_parts):
        raise ValueError("snapshot path must be repository-relative")
    if not allow_archive and path.suffix.casefold() in _ARCHIVE_SUFFIXES:
        raise ValueError("snapshot path cannot be an archive")
    if any(
        not part
        or not all(
            character.isascii()
            and (character.isalnum() or character in "._-")
            for character in part
        )
        for part in path.parts
    ):
        raise ValueError("snapshot path contains unsupported characters")
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


def _canonical_bytes(payload: object) -> bytes:
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json")
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _json_file_bytes(payload: object) -> bytes:
    return _canonical_bytes(payload) + b"\n"


def _bundle_sha256(
    manifest: "KoreanFoundationSnapshotManifest | dict[str, object]",
) -> str:
    payload = (
        manifest.model_dump(mode="json", exclude_none=True)
        if isinstance(manifest, BaseModel)
        else dict(manifest)
    )
    payload.pop("bundle_sha256", None)
    return _canonical_sha256(payload)


def _snapshot_root_sha256(
    *,
    source_root: str,
    review_evidence_root: str,
    media_root: str,
    members: tuple["KoreanFoundationSnapshotMember", ...]
    | list[dict[str, object]],
) -> str:
    serialized_members = [
        member.model_dump(mode="json")
        if isinstance(member, BaseModel)
        else dict(member)
        for member in members
    ]
    return _canonical_sha256(
        {
            "source_root": source_root,
            "review_evidence_root": review_evidence_root,
            "media_root": media_root,
            "members": serialized_members,
        }
    )


class KoreanFoundationActivePointer(_FrozenSnapshotModel):
    """The entire fixed activation contract; mutable metadata is forbidden."""

    schema_version: Literal[1, 2] = 1
    pointer_version: Literal["phase31-korean-foundation-active-pointer-v2"] | None = (
        None
    )
    receipt_sha256: str | None = None
    bundle_sha256: str = Field(min_length=64, max_length=64)
    snapshot_relpath: str = Field(min_length=1, max_length=_MAX_RELPATH_LENGTH)
    snapshot_manifest_sha256: str = Field(min_length=64, max_length=64)
    snapshot_root_sha256: str | None = None
    active_prestate_sha256: str | None = None
    authorization_sha256: str | None = None

    @field_validator(
        "receipt_sha256",
        "bundle_sha256",
        "snapshot_manifest_sha256",
        "snapshot_root_sha256",
        "active_prestate_sha256",
        "authorization_sha256",
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
            field_name=getattr(info, "field_name", "pointer hash"),
        )

    @field_validator("snapshot_relpath")
    @classmethod
    def relpath_must_be_safe(cls, value: str) -> str:
        return _safe_relpath(value)

    @model_validator(mode="after")
    def versioned_provenance_must_be_complete(self) -> Self:
        provenance = (
            self.pointer_version,
            self.receipt_sha256,
            self.snapshot_root_sha256,
            self.active_prestate_sha256,
            self.authorization_sha256,
        )
        if self.schema_version == 1:
            if any(value is not None for value in provenance):
                raise ValueError("legacy pointer cannot contain activation provenance")
            return self
        if any(value is None for value in provenance):
            raise ValueError("active pointer provenance must be complete")
        return self


class KoreanFoundationSnapshotMember(_FrozenSnapshotModel):
    """One exact non-empty file declared by an immutable snapshot manifest."""

    role: _SnapshotRole
    relpath: str = Field(min_length=1, max_length=_MAX_RELPATH_LENGTH)
    size_bytes: int = Field(ge=1, le=_SNAPSHOT_MEMBER_MAX_BYTES)
    sha256: str = Field(min_length=64, max_length=64)

    @field_validator("relpath")
    @classmethod
    def relpath_must_be_safe(cls, value: str) -> str:
        return _safe_relpath(value)

    @field_validator("sha256")
    @classmethod
    def hash_must_be_lowercase_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="snapshot member hash")


class KoreanFoundationSnapshotManifest(_FrozenSnapshotModel):
    """Bounded declaration of every source, review, and media snapshot file."""

    schema_version: Literal[1, 2] = 1
    snapshot_contract_version: Literal[
        "phase31-korean-foundation-snapshot-v2"
    ] | None = None
    receipt_sha256: str | None = None
    receipt_payload_sha256: str | None = None
    confirmed_index_sha256: str | None = None
    evidence_bundle_sha256: str | None = None
    source_evidence_sha256: str | None = None
    reviewer_evidence_sha256: str | None = None
    rights_evidence_sha256: str | None = None
    media_evidence_sha256: str | None = None
    active_prestate_marker: Literal["absent", "present"] | None = None
    active_prestate_sha256: str | None = None
    snapshot_root_sha256: str | None = None
    bundle_sha256: str = Field(min_length=64, max_length=64)
    source_root: str = Field(min_length=1, max_length=_MAX_RELPATH_LENGTH)
    review_evidence_root: str = Field(
        min_length=1,
        max_length=_MAX_RELPATH_LENGTH,
    )
    media_root: str = Field(min_length=1, max_length=_MAX_RELPATH_LENGTH)
    members: tuple[KoreanFoundationSnapshotMember, ...] = Field(
        min_length=1,
        max_length=_SNAPSHOT_MAX_MEMBERS,
    )

    @field_validator(
        "receipt_sha256",
        "receipt_payload_sha256",
        "confirmed_index_sha256",
        "evidence_bundle_sha256",
        "source_evidence_sha256",
        "reviewer_evidence_sha256",
        "rights_evidence_sha256",
        "media_evidence_sha256",
        "active_prestate_sha256",
        "snapshot_root_sha256",
        "bundle_sha256",
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
            field_name=getattr(info, "field_name", "snapshot hash"),
        )

    @field_validator("source_root", "review_evidence_root", "media_root")
    @classmethod
    def roots_must_be_safe(cls, value: str) -> str:
        return _safe_relpath(value)

    @model_validator(mode="after")
    def tree_roles_roots_and_bundle_hash_must_be_exact(self) -> Self:
        provenance = (
            self.snapshot_contract_version,
            self.receipt_sha256,
            self.receipt_payload_sha256,
            self.confirmed_index_sha256,
            self.evidence_bundle_sha256,
            self.source_evidence_sha256,
            self.reviewer_evidence_sha256,
            self.rights_evidence_sha256,
            self.media_evidence_sha256,
            self.active_prestate_marker,
            self.active_prestate_sha256,
            self.snapshot_root_sha256,
        )
        if self.schema_version == 1:
            if any(value is not None for value in provenance):
                raise ValueError(
                    "legacy snapshot cannot contain preparation provenance"
                )
        elif any(value is None for value in provenance):
            raise ValueError("prepared snapshot provenance must be complete")
        roots = (self.source_root, self.review_evidence_root, self.media_root)
        if len(set(roots)) != len(roots) or any("/" in root for root in roots):
            raise ValueError("snapshot roots must be distinct top-level directories")
        relpaths = tuple(member.relpath for member in self.members)
        if len(relpaths) != len(set(relpaths)):
            raise ValueError("snapshot member paths must be unique")
        if (
            sum(member.size_bytes for member in self.members)
            > _SNAPSHOT_TOTAL_MAX_BYTES
        ):
            raise ValueError("snapshot member bytes exceed the bounded total")
        role_counts = {
            role: sum(member.role == role for member in self.members)
            for role in _SINGLETON_ROLES
        }
        if any(count != 1 for count in role_counts.values()):
            raise ValueError("snapshot requires each singleton role exactly once")
        if not any(member.role == "review_evidence" for member in self.members):
            raise ValueError("snapshot requires review evidence")
        for member in self.members:
            expected_root = (
                self.source_root
                if member.role in _SINGLETON_ROLES
                else self.review_evidence_root
                if member.role == "review_evidence"
                else self.media_root
            )
            if PurePosixPath(member.relpath).parts[0] != expected_root:
                raise ValueError("snapshot member is outside its declared role root")
        if self.schema_version == 2 and self.snapshot_root_sha256 != (
            _snapshot_root_sha256(
                source_root=self.source_root,
                review_evidence_root=self.review_evidence_root,
                media_root=self.media_root,
                members=self.members,
            )
        ):
            raise ValueError("snapshot root hash does not match member tree")
        if self.bundle_sha256 != _bundle_sha256(self):
            raise ValueError("snapshot bundle hash does not match manifest")
        return self


class ResolvedKoreanFoundationSnapshotMember(_FrozenSnapshotModel):
    """One lstat-checked, hash-verified member captured by a single resolution."""

    role: _SnapshotRole
    relpath: str
    path: Path
    size_bytes: int
    sha256: str
    content: bytes


class ResolvedKoreanFoundationSnapshot(_FrozenSnapshotModel):
    """Frozen complete snapshot selected by exactly one active-pointer read."""

    bundle_sha256: str
    snapshot_manifest_sha256: str
    snapshot_root: Path
    source_root: Path
    review_evidence_root: Path
    media_root: Path
    manifest: KoreanFoundationSnapshotManifest
    members: tuple[ResolvedKoreanFoundationSnapshotMember, ...]
    review_evidence_members: tuple[ResolvedKoreanFoundationSnapshotMember, ...]
    media_members: tuple[ResolvedKoreanFoundationSnapshotMember, ...]
    concept_registry: KoreanConceptRegistry
    hangul_source_pack: KoreanHangulSourcePack
    pronunciation_source_pack: KoreanPronunciationSourcePack
    curation_manifest: KoreanFoundationCurationManifest
    media_manifest_bytes: bytes
    receipt_sha256: str | None = None
    snapshot_root_sha256: str | None = None
    active_prestate_sha256: str | None = None
    authorization_sha256: str | None = None


class PreparedKoreanFoundationSnapshot(_FrozenSnapshotModel):
    """Path-free immutable preparation result bound to one receipt and prestate."""

    prepared: Literal[True] = True
    snapshot_contract_version: Literal[
        "phase31-korean-foundation-snapshot-v2"
    ]
    prepared_verification_version: Literal[
        "phase31-korean-foundation-prepared-verification-v1"
    ]
    authorization_contract_version: Literal[
        "phase31-korean-foundation-activation-authorization-v1"
    ]
    receipt_sha256: str
    receipt_payload_sha256: str
    confirmed_index_sha256: str
    evidence_bundle_sha256: str
    bundle_sha256: str
    snapshot_manifest_sha256: str
    snapshot_root_sha256: str
    active_prestate_marker: Literal["absent", "present"]
    active_prestate_sha256: str
    authorization_sha256: str
    member_count: int = Field(ge=1, le=_SNAPSHOT_MAX_MEMBERS)
    media_member_count: int = Field(ge=1, le=_SNAPSHOT_MAX_MEMBERS)

    @field_validator(
        "receipt_sha256",
        "receipt_payload_sha256",
        "confirmed_index_sha256",
        "evidence_bundle_sha256",
        "bundle_sha256",
        "snapshot_manifest_sha256",
        "snapshot_root_sha256",
        "active_prestate_sha256",
        "authorization_sha256",
    )
    @classmethod
    def hashes_must_be_lowercase_sha256(cls, value: str, info: object) -> str:
        return _sha256_text(
            value,
            field_name=getattr(info, "field_name", "prepared hash"),
        )


class KoreanFoundationPreparedVerificationReport(PreparedKoreanFoundationSnapshot):
    """Exact path-free report from the separately read-only verifier."""


class KoreanFoundationActivationResult(PreparedKoreanFoundationSnapshot):
    """Path-free result of one atomic activation attempt."""

    activated: bool
    already_active: bool
    active_pointer_sha256: str

    @field_validator("active_pointer_sha256")
    @classmethod
    def pointer_hash_must_be_lowercase_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="active pointer hash")


class KoreanFoundationActiveProvenanceReport(PreparedKoreanFoundationSnapshot):
    """Read-only proof that the active pointer is the authorized prepared tuple."""

    active: Literal[True] = True
    active_pointer_sha256: str

    @field_validator("active_pointer_sha256")
    @classmethod
    def pointer_hash_must_be_lowercase_sha256(cls, value: str) -> str:
        return _sha256_text(value, field_name="active pointer hash")


@dataclass(frozen=True, slots=True)
class _SnapshotCopyMember:
    role: _SnapshotRole
    relpath: str
    content: bytes


@dataclass(frozen=True, slots=True)
class _AuthorityState:
    receipt: Any
    receipt_raw: bytes
    receipt_sha256: str
    validated: Any
    copy_members: tuple[_SnapshotCopyMember, ...]
    current_prestate_marker: Literal["absent", "present"]
    current_prestate_sha256: str


@dataclass(frozen=True, slots=True)
class _StaleStage:
    path: Path
    device: int
    inode: int


@dataclass(frozen=True, slots=True)
class _PreparationState:
    authority: _AuthorityState
    manifest: KoreanFoundationSnapshotManifest
    manifest_raw: bytes
    result: PreparedKoreanFoundationSnapshot
    target: Path
    stale_stages: tuple[_StaleStage, ...]
    snapshot_root_missing: bool
    exact_target_exists: bool


@dataclass(frozen=True, slots=True)
class _ActivationState:
    authority: _AuthorityState
    prepared: PreparedKoreanFoundationSnapshot
    manifest: KoreanFoundationSnapshotManifest
    manifest_raw: bytes
    target: Path
    stale_stages: tuple[_StaleStage, ...]
    pointer: KoreanFoundationActivePointer
    pointer_raw: bytes
    pointer_sha256: str
    already_active: bool


def _evidence_api() -> Any:
    # Lazy import avoids the evidence module's intentional pointer-model import cycle.
    return import_module("multilang.services.korean_foundation_evidence")


def _snapshot_evidence_paths(paths: _KoreanFoundationSnapshotPaths) -> Any:
    evidence = _evidence_api()
    return evidence._KoreanFoundationEvidencePaths.from_project_root(paths.project_dir)


def _translate_evidence_failure(exc: BaseException) -> KoreanFoundationSnapshotError:
    reason = getattr(getattr(exc, "reason_code", None), "value", None)
    mapped = {
        "receipt_missing": KoreanFoundationSnapshotReasonCode.RECEIPT_MISSING,
        "receipt_hash_mismatch": (
            KoreanFoundationSnapshotReasonCode.RECEIPT_HASH_MISMATCH
        ),
        "receipt_invalid": KoreanFoundationSnapshotReasonCode.RECEIPT_INVALID,
        "active_prestate_invalid": (
            KoreanFoundationSnapshotReasonCode.ACTIVE_PRESTATE_DRIFT
        ),
        "continuity_drift": KoreanFoundationSnapshotReasonCode.AUTHORITY_DRIFT,
        "between_stage_drift": KoreanFoundationSnapshotReasonCode.AUTHORITY_DRIFT,
    }.get(reason, KoreanFoundationSnapshotReasonCode.AUTHORITY_DRIFT)
    return KoreanFoundationSnapshotError(mapped)


def korean_foundation_activation_authorization_sha256(
    *,
    receipt_sha256: str,
    bundle_sha256: str,
    snapshot_manifest_sha256: str,
    snapshot_root_sha256: str,
    active_prestate_sha256: str,
) -> str:
    """Bind one exact prepared snapshot and active prestate for activation."""

    values = {
        "receipt_sha256": receipt_sha256,
        "bundle_sha256": bundle_sha256,
        "snapshot_manifest_sha256": snapshot_manifest_sha256,
        "snapshot_root_sha256": snapshot_root_sha256,
        "active_prestate_sha256": active_prestate_sha256,
    }
    try:
        for field_name, value in values.items():
            _sha256_text(value, field_name=field_name)
    except ValueError as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.AUTHORIZATION_INVALID
        ) from exc
    return _canonical_sha256(
        {
            "authorization_contract_version": (
                KOREAN_FOUNDATION_ACTIVATION_AUTHORIZATION_VERSION
            ),
            **values,
        }
    )


def _raise(reason_code: KoreanFoundationSnapshotReasonCode) -> None:
    raise KoreanFoundationSnapshotError(reason_code)


def _stat_is_link_or_reparse(stat_result: os.stat_result) -> bool:
    if stat.S_ISLNK(stat_result.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(stat_result, "st_file_attributes", 0) & reparse_flag)


def _relative_parts(path: Path, root: Path) -> tuple[str, ...]:
    try:
        return path.relative_to(root).parts
    except ValueError as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.UNSAFE_SNAPSHOT_PATH
        ) from exc


def _assert_no_link_components(
    path: Path,
    *,
    root: Path,
    missing_reason: KoreanFoundationSnapshotReasonCode,
) -> os.stat_result:
    parts = _relative_parts(path, root)
    current = root
    try:
        root_stat = root.lstat()
    except FileNotFoundError:
        _raise(missing_reason)
    if _stat_is_link_or_reparse(root_stat):
        _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    current_stat = root_stat
    for part in parts:
        current = current / part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            _raise(missing_reason)
        except OSError:
            _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
        if _stat_is_link_or_reparse(current_stat):
            _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    return current_stat


def _read_regular_bytes(
    path: Path,
    *,
    root: Path,
    maximum_bytes: int,
    missing_reason: KoreanFoundationSnapshotReasonCode,
    oversized_reason: KoreanFoundationSnapshotReasonCode,
    malformed_reason: KoreanFoundationSnapshotReasonCode,
) -> bytes:
    before = _assert_no_link_components(
        path,
        root=root,
        missing_reason=missing_reason,
    )
    if not stat.S_ISREG(before.st_mode):
        _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    if before.st_size > maximum_bytes:
        _raise(oversized_reason)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        _raise(missing_reason)
    except OSError as exc:
        raise KoreanFoundationSnapshotError(malformed_reason) from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or _stat_is_link_or_reparse(opened)
            or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
        ):
            _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if len(raw) > maximum_bytes:
        _raise(oversized_reason)
    if (
        (after.st_dev, after.st_ino, after.st_size)
        != (opened.st_dev, opened.st_ino, opened.st_size)
        or len(raw) != opened.st_size
    ):
        _raise(malformed_reason)
    return raw


def _read_pointer_once(pointer_path: Path) -> bytes:
    _assert_no_link_components(
        pointer_path,
        root=_PROJECT_ROOT,
        missing_reason=KoreanFoundationSnapshotReasonCode.PRODUCTION_NOT_ACTIVE,
    )
    try:
        size = pointer_path.stat().st_size
        if size > _POINTER_MAX_BYTES:
            _raise(KoreanFoundationSnapshotReasonCode.ACTIVE_POINTER_OVERSIZED)
        raw = pointer_path.read_bytes()
        if len(raw) > _POINTER_MAX_BYTES:
            _raise(KoreanFoundationSnapshotReasonCode.ACTIVE_POINTER_OVERSIZED)
        return raw
    except KoreanFoundationSnapshotError:
        raise
    except FileNotFoundError as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.PRODUCTION_NOT_ACTIVE
        ) from exc
    except OSError as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.ACTIVE_POINTER_MALFORMED
        ) from exc


def _parse_pointer(raw: bytes) -> KoreanFoundationActivePointer:
    try:
        payload = json.loads(raw.decode("utf-8"))
        return KoreanFoundationActivePointer.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.ACTIVE_POINTER_MALFORMED
        ) from exc
    except ValidationError as exc:
        if any(error.get("loc") == ("snapshot_relpath",) for error in exc.errors()):
            raise KoreanFoundationSnapshotError(
                KoreanFoundationSnapshotReasonCode.UNSAFE_SNAPSHOT_PATH
            ) from exc
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.ACTIVE_POINTER_INVALID
        ) from exc
    except (TypeError, ValueError) as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.ACTIVE_POINTER_INVALID
        ) from exc


def _read_snapshot_manifest(path: Path) -> bytes:
    return _read_regular_bytes(
        path,
        root=_PROJECT_ROOT,
        maximum_bytes=_SNAPSHOT_MANIFEST_MAX_BYTES,
        missing_reason=KoreanFoundationSnapshotReasonCode.SNAPSHOT_MANIFEST_MISSING,
        oversized_reason=(
            KoreanFoundationSnapshotReasonCode.SNAPSHOT_MANIFEST_OVERSIZED
        ),
        malformed_reason=(
            KoreanFoundationSnapshotReasonCode.SNAPSHOT_MANIFEST_MALFORMED
        ),
    )


def _parse_snapshot_manifest(raw: bytes) -> KoreanFoundationSnapshotManifest:
    try:
        payload = json.loads(raw.decode("utf-8"))
        return KoreanFoundationSnapshotManifest.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.SNAPSHOT_MANIFEST_MALFORMED
        ) from exc
    except (ValidationError, TypeError, ValueError) as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.SNAPSHOT_MANIFEST_INVALID
        ) from exc


def _read_member(
    member: KoreanFoundationSnapshotMember,
    *,
    snapshot_root: Path,
) -> ResolvedKoreanFoundationSnapshotMember:
    path = snapshot_root.joinpath(*PurePosixPath(member.relpath).parts)
    content = _read_regular_bytes(
        path,
        root=_PROJECT_ROOT,
        maximum_bytes=member.size_bytes,
        missing_reason=KoreanFoundationSnapshotReasonCode.SNAPSHOT_MEMBER_MISSING,
        oversized_reason=(
            KoreanFoundationSnapshotReasonCode.SNAPSHOT_MEMBER_HASH_MISMATCH
        ),
        malformed_reason=(
            KoreanFoundationSnapshotReasonCode.SNAPSHOT_MEMBER_HASH_MISMATCH
        ),
    )
    if (
        len(content) != member.size_bytes
        or not content
        or sha256(content).hexdigest() != member.sha256
    ):
        _raise(KoreanFoundationSnapshotReasonCode.SNAPSHOT_MEMBER_HASH_MISMATCH)
    return ResolvedKoreanFoundationSnapshotMember(
        role=member.role,
        relpath=member.relpath,
        path=path,
        size_bytes=member.size_bytes,
        sha256=member.sha256,
        content=content,
    )


def _collect_snapshot_files(snapshot_root: Path) -> set[str]:
    files: set[str] = set()
    stack = [snapshot_root]
    while stack:
        directory = stack.pop()
        try:
            children = tuple(directory.iterdir())
        except OSError:
            _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
        for child in children:
            try:
                child_stat = child.lstat()
            except OSError:
                _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
            if _stat_is_link_or_reparse(child_stat):
                _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
            if stat.S_ISDIR(child_stat.st_mode):
                stack.append(child)
            elif stat.S_ISREG(child_stat.st_mode):
                relative = child.relative_to(snapshot_root).as_posix()
                files.add(relative)
            else:
                _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    return files


def _member_by_role(
    members: tuple[ResolvedKoreanFoundationSnapshotMember, ...],
    role: str,
) -> ResolvedKoreanFoundationSnapshotMember:
    return next(member for member in members if member.role == role)


def _parse_typed_members(
    members: tuple[ResolvedKoreanFoundationSnapshotMember, ...],
) -> tuple[
    KoreanConceptRegistry,
    KoreanHangulSourcePack,
    KoreanPronunciationSourcePack,
    KoreanFoundationCurationManifest,
]:
    try:
        registry = KoreanConceptRegistry.model_validate_json(
            _member_by_role(members, "concept_registry").content
        )
        hangul = KoreanHangulSourcePack.model_validate_json(
            _member_by_role(members, "hangul_source_pack").content
        )
        pronunciation = KoreanPronunciationSourcePack.model_validate_json(
            _member_by_role(members, "pronunciation_source_pack").content
        )
        curation = KoreanFoundationCurationManifest.model_validate_json(
            _member_by_role(members, "curation_manifest").content
        )
        validate_korean_foundation_curation(
            curation,
            registry=registry,
            hangul_pack=hangul,
            pronunciation_pack=pronunciation,
        )
    except (ValidationError, KoreanFoundationReviewError, TypeError, ValueError) as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.SNAPSHOT_MEMBER_INVALID
        ) from exc
    return registry, hangul, pronunciation, curation


def _verify_snapshot_tree(
    snapshot_root: Path,
    *,
    expected_bundle_sha256: str,
    expected_manifest_sha256: str | None = None,
    expected_manifest_raw: bytes | None = None,
    expected_contents: dict[str, bytes] | None = None,
    require_bundle_name: bool = True,
) -> tuple[
    KoreanFoundationSnapshotManifest,
    bytes,
    tuple[ResolvedKoreanFoundationSnapshotMember, ...],
]:
    root_stat = _assert_no_link_components(
        snapshot_root,
        root=_PROJECT_ROOT,
        missing_reason=KoreanFoundationSnapshotReasonCode.SNAPSHOT_MANIFEST_MISSING,
    )
    if not stat.S_ISDIR(root_stat.st_mode):
        _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    manifest_raw = _read_snapshot_manifest(snapshot_root / "snapshot-manifest.json")
    actual_manifest_sha256 = sha256(manifest_raw).hexdigest()
    if (
        expected_manifest_sha256 is not None
        and actual_manifest_sha256 != expected_manifest_sha256
    ):
        _raise(KoreanFoundationSnapshotReasonCode.SNAPSHOT_MANIFEST_HASH_MISMATCH)
    if expected_manifest_raw is not None and manifest_raw != expected_manifest_raw:
        _raise(KoreanFoundationSnapshotReasonCode.SNAPSHOT_MANIFEST_HASH_MISMATCH)
    manifest = _parse_snapshot_manifest(manifest_raw)
    if manifest.bundle_sha256 != expected_bundle_sha256 or (
        require_bundle_name and snapshot_root.name != expected_bundle_sha256
    ):
        _raise(KoreanFoundationSnapshotReasonCode.BUNDLE_NAME_MISMATCH)
    members = tuple(
        _read_member(member, snapshot_root=snapshot_root)
        for member in manifest.members
    )
    expected_files = {
        "snapshot-manifest.json",
        *(member.relpath for member in manifest.members),
    }
    actual_files = _collect_snapshot_files(snapshot_root)
    if actual_files != expected_files:
        if actual_files - expected_files:
            _raise(KoreanFoundationSnapshotReasonCode.SNAPSHOT_EXTRA_MEMBER)
        _raise(KoreanFoundationSnapshotReasonCode.SNAPSHOT_MEMBER_MISSING)
    if expected_contents is not None:
        actual_contents = {member.relpath: member.content for member in members}
        if actual_contents != expected_contents:
            _raise(KoreanFoundationSnapshotReasonCode.SNAPSHOT_MEMBER_HASH_MISMATCH)
    return manifest, manifest_raw, members


def _resolved_snapshot(
    *,
    pointer: KoreanFoundationActivePointer,
    snapshot_root: Path,
    manifest: KoreanFoundationSnapshotManifest,
    members: tuple[ResolvedKoreanFoundationSnapshotMember, ...],
) -> ResolvedKoreanFoundationSnapshot:
    registry, hangul, pronunciation, curation = _parse_typed_members(members)
    media_manifest_bytes = _member_by_role(members, "media_manifest").content
    return ResolvedKoreanFoundationSnapshot(
        bundle_sha256=pointer.bundle_sha256,
        snapshot_manifest_sha256=pointer.snapshot_manifest_sha256,
        snapshot_root=snapshot_root,
        source_root=snapshot_root / manifest.source_root,
        review_evidence_root=snapshot_root / manifest.review_evidence_root,
        media_root=snapshot_root / manifest.media_root,
        manifest=manifest,
        members=members,
        review_evidence_members=tuple(
            member for member in members if member.role == "review_evidence"
        ),
        media_members=tuple(member for member in members if member.role == "media"),
        concept_registry=registry,
        hangul_source_pack=hangul,
        pronunciation_source_pack=pronunciation,
        curation_manifest=curation,
        media_manifest_bytes=media_manifest_bytes,
        receipt_sha256=pointer.receipt_sha256,
        snapshot_root_sha256=pointer.snapshot_root_sha256,
        active_prestate_sha256=pointer.active_prestate_sha256,
        authorization_sha256=pointer.authorization_sha256,
    )


def resolve_active_korean_foundation_snapshot() -> ResolvedKoreanFoundationSnapshot:
    """Read the fixed pointer once and return one complete hash-validated snapshot."""

    pointer_path = _PROJECT_ROOT / ACTIVE_KOREAN_FOUNDATIONS_POINTER_PATH
    pointer = _parse_pointer(_read_pointer_once(pointer_path))
    expected_relpath = f"snapshots/{pointer.bundle_sha256}"
    if pointer.snapshot_relpath != expected_relpath:
        _raise(KoreanFoundationSnapshotReasonCode.BUNDLE_NAME_MISMATCH)

    data_root = _PROJECT_ROOT / ACTIVE_KOREAN_FOUNDATIONS_POINTER_PATH.parent
    snapshot_root = data_root.joinpath(
        *PurePosixPath(pointer.snapshot_relpath).parts
    )
    fixed_snapshot_root = _PROJECT_ROOT / KOREAN_FOUNDATION_SNAPSHOT_ROOT
    if snapshot_root.parent != fixed_snapshot_root:
        _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_SNAPSHOT_PATH)
    _assert_no_link_components(
        snapshot_root,
        root=_PROJECT_ROOT,
        missing_reason=KoreanFoundationSnapshotReasonCode.SNAPSHOT_MANIFEST_MISSING,
    )
    manifest, _manifest_raw, members = _verify_snapshot_tree(
        snapshot_root,
        expected_bundle_sha256=pointer.bundle_sha256,
        expected_manifest_sha256=pointer.snapshot_manifest_sha256,
    )
    if pointer.schema_version == 2:
        if (
            manifest.schema_version != 2
            or manifest.receipt_sha256 != pointer.receipt_sha256
            or manifest.snapshot_root_sha256 != pointer.snapshot_root_sha256
            or manifest.active_prestate_sha256 != pointer.active_prestate_sha256
            or pointer.authorization_sha256
            != korean_foundation_activation_authorization_sha256(
                receipt_sha256=str(pointer.receipt_sha256),
                bundle_sha256=pointer.bundle_sha256,
                snapshot_manifest_sha256=pointer.snapshot_manifest_sha256,
                snapshot_root_sha256=str(pointer.snapshot_root_sha256),
                active_prestate_sha256=str(pointer.active_prestate_sha256),
            )
        ):
            _raise(KoreanFoundationSnapshotReasonCode.ACTIVE_POINTER_INVALID)
    return _resolved_snapshot(
        pointer=pointer,
        snapshot_root=snapshot_root,
        manifest=manifest,
        members=members,
    )


def _read_receipt_authority(
    paths: _KoreanFoundationSnapshotPaths,
    *,
    expected_receipt_sha256: str,
    require_recorded_prestate: bool,
) -> _AuthorityState:
    evidence = _evidence_api()
    evidence_paths = _snapshot_evidence_paths(paths)
    try:
        _sha256_text(
            expected_receipt_sha256,
            field_name="expected receipt hash",
        )
    except ValueError as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.RECEIPT_HASH_MISMATCH
        ) from exc
    try:
        receipt_raw = evidence._read_regular_file(
            paths.receipt,
            paths=evidence_paths,
            maximum_bytes=evidence._RECEIPT_MAX_BYTES,
            missing_reason=evidence.KoreanFoundationEvidenceReasonCode.RECEIPT_MISSING,
        )
        actual_receipt_sha256 = sha256(receipt_raw).hexdigest()
        if actual_receipt_sha256 != expected_receipt_sha256:
            _raise(KoreanFoundationSnapshotReasonCode.RECEIPT_HASH_MISMATCH)
        try:
            receipt = evidence.KoreanFoundationValidationReceipt.model_validate_json(
                receipt_raw
            )
        except (ValidationError, TypeError, ValueError) as exc:
            raise KoreanFoundationSnapshotError(
                KoreanFoundationSnapshotReasonCode.RECEIPT_INVALID
            ) from exc
        validated = evidence._validate_fixed_evidence(
            evidence_paths,
            confirmed_index_sha256=receipt.confirmed_index_sha256,
        )
        current_marker = validated.active_prestate_marker
        current_hash = validated.active_prestate_sha256
        receipt_bound = replace(
            validated,
            active_prestate_marker=receipt.active_prestate_marker,
            active_prestate_sha256=receipt.active_prestate_sha256,
        )
        if evidence._derive_receipt(receipt_bound) != receipt:
            _raise(KoreanFoundationSnapshotReasonCode.AUTHORITY_DRIFT)
        if require_recorded_prestate and (
            current_marker != receipt.active_prestate_marker
            or current_hash != receipt.active_prestate_sha256
        ):
            _raise(KoreanFoundationSnapshotReasonCode.ACTIVE_PRESTATE_DRIFT)

        bundle_relpath = evidence._current_bundle_relpath(validated.layout.index)
        registry_raw = evidence._read_regular_file(
            evidence._candidate_source_path(
                evidence_paths,
                _REGISTRY_FILENAME,
                bundle_relpath=bundle_relpath,
            ),
            paths=evidence_paths,
            maximum_bytes=evidence._CANDIDATE_MAX_BYTES,
            missing_reason=(
                evidence.KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH
            ),
        )
        candidate_raw: dict[str, bytes] = {}
        for binding in validated.layout.index.candidate_bindings:
            raw = evidence._read_regular_file(
                evidence._candidate_source_path(
                    evidence_paths,
                    binding.filename,
                    bundle_relpath=bundle_relpath,
                ),
                paths=evidence_paths,
                maximum_bytes=evidence._CANDIDATE_MAX_BYTES,
                missing_reason=(
                    evidence.KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH
                ),
            )
            if sha256(raw).hexdigest() != binding.file_sha256:
                _raise(KoreanFoundationSnapshotReasonCode.AUTHORITY_DRIFT)
            candidate_raw[binding.filename] = raw

        request_paths = {
            "31-CURRICULUM-REVIEW.md": paths.phase_dir
            / "31-CURRICULUM-REVIEW.md",
            "31-AUDIO-PLAYBACK-REVIEW.md": paths.phase_dir
            / "31-AUDIO-PLAYBACK-REVIEW.md",
        }
        request_raw: dict[str, bytes] = {}
        for binding in validated.layout.index.request_bindings:
            raw = evidence._read_regular_file(
                request_paths[binding.filename],
                paths=evidence_paths,
                maximum_bytes=evidence._REQUEST_MAX_BYTES,
                missing_reason=(
                    evidence.KoreanFoundationEvidenceReasonCode.SOURCE_BINDING_MISMATCH
                ),
            )
            if sha256(raw).hexdigest() != binding.file_sha256:
                _raise(KoreanFoundationSnapshotReasonCode.AUTHORITY_DRIFT)
            request_raw[binding.filename] = raw

        members = validated.layout.members
        approved_media = evidence.KoreanFoundationMediaManifest.model_validate_json(
            members["proposed-media.json"]
        )
        media_relpath_by_basename = {
            slot.basename: slot.storage_relpath for slot in approved_media.slots
        }
        if len(media_relpath_by_basename) != len(approved_media.slots):
            _raise(KoreanFoundationSnapshotReasonCode.AUTHORITY_DRIFT)
        copy_members: list[_SnapshotCopyMember] = [
            _SnapshotCopyMember(
                role="concept_registry",
                relpath="content/korean-concepts-v1.json",
                content=registry_raw,
            ),
            _SnapshotCopyMember(
                role="hangul_source_pack",
                relpath="content/hangul-v2.json",
                content=candidate_raw["hangul-v2.json"],
            ),
            _SnapshotCopyMember(
                role="pronunciation_source_pack",
                relpath="content/pronunciation-i-plus-1-v2.json",
                content=candidate_raw["pronunciation-i-plus-1-v2.json"],
            ),
            _SnapshotCopyMember(
                role="curation_manifest",
                relpath="content/korean-foundations-v2-curation.json",
                content=members["proposed-curation.json"],
            ),
            _SnapshotCopyMember(
                role="media_manifest",
                relpath="content/korean-foundations-v2-media.json",
                content=members["proposed-media.json"],
            ),
            _SnapshotCopyMember(
                role="review_evidence",
                relpath="review/validation-receipt.json",
                content=receipt_raw,
            ),
            _SnapshotCopyMember(
                role="review_evidence",
                relpath="review/evidence-index.json",
                content=validated.layout.index_raw,
            ),
            _SnapshotCopyMember(
                role="review_evidence",
                relpath="review/candidates/korean-foundations-v2-curation.json",
                content=candidate_raw["korean-foundations-v2-curation.json"],
            ),
            _SnapshotCopyMember(
                role="review_evidence",
                relpath="review/candidates/korean-foundations-v2-media.json",
                content=candidate_raw["korean-foundations-v2-media.json"],
            ),
        ]
        copy_members.extend(
            _SnapshotCopyMember(
                role="review_evidence",
                relpath=f"review/requests/{filename}",
                content=request_raw[filename],
            )
            for filename in _REQUEST_FILENAMES
        )
        copy_members.extend(
            _SnapshotCopyMember(
                role="review_evidence",
                relpath=f"review/{relpath}",
                content=members[relpath],
            )
            for relpath in _REVIEW_EVIDENCE_RELPATHS
        )
        copy_members.extend(
            _SnapshotCopyMember(
                role="media",
                relpath=media_relpath_by_basename[
                    PurePosixPath(member.relpath).name
                ],
                content=members[member.relpath],
            )
            for member in validated.layout.index.members
            if member.role == "media"
        )
        if len(copy_members) != 527 or sum(
            member.role == "media" for member in copy_members
        ) != 509:
            _raise(KoreanFoundationSnapshotReasonCode.AUTHORITY_DRIFT)
        evidence._assert_state_unchanged(evidence_paths, validated)
    except KoreanFoundationSnapshotError:
        raise
    except evidence.KoreanFoundationEvidenceError as exc:
        raise _translate_evidence_failure(exc) from exc
    return _AuthorityState(
        receipt=receipt,
        receipt_raw=receipt_raw,
        receipt_sha256=actual_receipt_sha256,
        validated=validated,
        copy_members=tuple(copy_members),
        current_prestate_marker=current_marker,
        current_prestate_sha256=current_hash,
    )


def _build_snapshot_manifest(
    authority: _AuthorityState,
) -> tuple[KoreanFoundationSnapshotManifest, bytes, PreparedKoreanFoundationSnapshot]:
    members = tuple(
        KoreanFoundationSnapshotMember(
            role=member.role,
            relpath=member.relpath,
            size_bytes=len(member.content),
            sha256=sha256(member.content).hexdigest(),
        )
        for member in authority.copy_members
    )
    root_hash = _snapshot_root_sha256(
        source_root="content",
        review_evidence_root="review",
        media_root="media",
        members=members,
    )
    receipt = authority.receipt
    payload: dict[str, object] = {
        "schema_version": 2,
        "snapshot_contract_version": KOREAN_FOUNDATION_SNAPSHOT_CONTRACT_VERSION,
        "receipt_sha256": authority.receipt_sha256,
        "receipt_payload_sha256": receipt.payload_sha256,
        "confirmed_index_sha256": receipt.confirmed_index_sha256,
        "evidence_bundle_sha256": receipt.evidence_bundle_sha256,
        "source_evidence_sha256": receipt.source_evidence_sha256,
        "reviewer_evidence_sha256": receipt.reviewer_evidence_sha256,
        "rights_evidence_sha256": receipt.rights_evidence_sha256,
        "media_evidence_sha256": receipt.media_evidence_sha256,
        "active_prestate_marker": receipt.active_prestate_marker,
        "active_prestate_sha256": receipt.active_prestate_sha256,
        "snapshot_root_sha256": root_hash,
        "source_root": "content",
        "review_evidence_root": "review",
        "media_root": "media",
        "members": [member.model_dump(mode="json") for member in members],
    }
    payload["bundle_sha256"] = _bundle_sha256(payload)
    manifest = KoreanFoundationSnapshotManifest.model_validate(payload)
    manifest_raw = _json_file_bytes(manifest)
    manifest_sha256 = sha256(manifest_raw).hexdigest()
    authorization = korean_foundation_activation_authorization_sha256(
        receipt_sha256=authority.receipt_sha256,
        bundle_sha256=manifest.bundle_sha256,
        snapshot_manifest_sha256=manifest_sha256,
        snapshot_root_sha256=root_hash,
        active_prestate_sha256=receipt.active_prestate_sha256,
    )
    result = PreparedKoreanFoundationSnapshot(
        snapshot_contract_version=KOREAN_FOUNDATION_SNAPSHOT_CONTRACT_VERSION,
        prepared_verification_version=(
            KOREAN_FOUNDATION_PREPARED_VERIFICATION_VERSION
        ),
        authorization_contract_version=(
            KOREAN_FOUNDATION_ACTIVATION_AUTHORIZATION_VERSION
        ),
        receipt_sha256=authority.receipt_sha256,
        receipt_payload_sha256=receipt.payload_sha256,
        confirmed_index_sha256=receipt.confirmed_index_sha256,
        evidence_bundle_sha256=receipt.evidence_bundle_sha256,
        bundle_sha256=manifest.bundle_sha256,
        snapshot_manifest_sha256=manifest_sha256,
        snapshot_root_sha256=root_hash,
        active_prestate_marker=receipt.active_prestate_marker,
        active_prestate_sha256=receipt.active_prestate_sha256,
        authorization_sha256=authorization,
        member_count=len(members),
        media_member_count=sum(member.role == "media" for member in members),
    )
    return manifest, manifest_raw, result


def _validate_stale_stage_tree(stage: Path) -> _StaleStage:
    try:
        stage_stat = stage.lstat()
    except OSError as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT
        ) from exc
    if _stat_is_link_or_reparse(stage_stat) or not stat.S_ISDIR(stage_stat.st_mode):
        _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    stack = [stage]
    visited = 0
    while stack:
        directory = stack.pop()
        try:
            children = tuple(directory.iterdir())
        except OSError as exc:
            raise KoreanFoundationSnapshotError(
                KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT
            ) from exc
        for child in children:
            visited += 1
            if visited > _SNAPSHOT_MAX_MEMBERS + 1:
                _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
            try:
                child_stat = child.lstat()
            except OSError as exc:
                raise KoreanFoundationSnapshotError(
                    KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT
                ) from exc
            if _stat_is_link_or_reparse(child_stat):
                _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
            if stat.S_ISDIR(child_stat.st_mode):
                stack.append(child)
            elif not stat.S_ISREG(child_stat.st_mode):
                _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    return _StaleStage(
        path=stage,
        device=stage_stat.st_dev,
        inode=stage_stat.st_ino,
    )


def _inspect_snapshot_area(
    paths: _KoreanFoundationSnapshotPaths,
    *,
    manifest: KoreanFoundationSnapshotManifest,
    manifest_raw: bytes,
    copy_members: tuple[_SnapshotCopyMember, ...],
) -> tuple[Path, tuple[_StaleStage, ...], bool, bool]:
    target = paths.snapshot_root / manifest.bundle_sha256
    try:
        root_stat = paths.snapshot_root.lstat()
    except FileNotFoundError:
        return target, (), True, False
    except OSError as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT
        ) from exc
    if _stat_is_link_or_reparse(root_stat) or not stat.S_ISDIR(root_stat.st_mode):
        _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    stale_stages: list[_StaleStage] = []
    try:
        children = tuple(paths.snapshot_root.iterdir())
    except OSError as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT
        ) from exc
    for child in children:
        if child.name.startswith(".staging-"):
            stale_stages.append(_validate_stale_stage_tree(child))

    try:
        target.lstat()
    except FileNotFoundError:
        return target, tuple(stale_stages), False, False
    except OSError as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.IMMUTABLE_SNAPSHOT_COLLISION
        ) from exc
    expected_contents = {
        member.relpath: member.content for member in copy_members
    }
    try:
        _verify_snapshot_tree(
            target,
            expected_bundle_sha256=manifest.bundle_sha256,
            expected_manifest_sha256=sha256(manifest_raw).hexdigest(),
            expected_manifest_raw=manifest_raw,
            expected_contents=expected_contents,
        )
    except KoreanFoundationSnapshotError as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.IMMUTABLE_SNAPSHOT_COLLISION
        ) from exc
    return target, tuple(stale_stages), False, True


def _validate_preparation_state(
    paths: _KoreanFoundationSnapshotPaths,
    *,
    expected_receipt_sha256: str,
) -> _PreparationState:
    authority = _read_receipt_authority(
        paths,
        expected_receipt_sha256=expected_receipt_sha256,
        require_recorded_prestate=True,
    )
    manifest, manifest_raw, result = _build_snapshot_manifest(authority)
    target, stages, root_missing, exact = _inspect_snapshot_area(
        paths,
        manifest=manifest,
        manifest_raw=manifest_raw,
        copy_members=authority.copy_members,
    )
    evidence = _evidence_api()
    try:
        evidence._assert_state_unchanged(
            _snapshot_evidence_paths(paths),
            authority.validated,
        )
    except evidence.KoreanFoundationEvidenceError as exc:
        raise _translate_evidence_failure(exc) from exc
    return _PreparationState(
        authority=authority,
        manifest=manifest,
        manifest_raw=manifest_raw,
        result=result,
        target=target,
        stale_stages=stages,
        snapshot_root_missing=root_missing,
        exact_target_exists=exact,
    )


def _recover_stale_stages(
    stages: tuple[_StaleStage, ...],
    *,
    snapshot_root: Path,
) -> None:
    for stage in stages:
        try:
            current = stage.path.lstat()
        except FileNotFoundError:
            continue
        if (
            stage.path.parent != snapshot_root
            or not stage.path.name.startswith(".staging-")
            or _stat_is_link_or_reparse(current)
            or not stat.S_ISDIR(current.st_mode)
            or (current.st_dev, current.st_ino) != (stage.device, stage.inode)
        ):
            _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
        shutil.rmtree(stage.path)


def _fsync_descriptor(descriptor: int) -> None:
    os.fsync(descriptor)


def _write_all(descriptor: int, content: bytes) -> None:
    view = memoryview(content)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("snapshot_write_failed")
        view = view[written:]


def _ensure_stage_parent(stage: Path, relpath: str) -> Path:
    destination = stage.joinpath(*PurePosixPath(relpath).parts)
    current = stage
    for part in PurePosixPath(relpath).parts[:-1]:
        current = current / part
        try:
            current.mkdir(mode=0o700)
        except FileExistsError:
            current_stat = current.lstat()
            if _stat_is_link_or_reparse(current_stat) or not stat.S_ISDIR(
                current_stat.st_mode
            ):
                _raise(KoreanFoundationSnapshotReasonCode.UNSAFE_FILESYSTEM_COMPONENT)
    return destination


def _copy_member_to_stage(stage: Path, member: _SnapshotCopyMember) -> None:
    destination = _ensure_stage_parent(stage, member.relpath)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(destination, flags, 0o600)
    try:
        _write_all(descriptor, member.content)
        _fsync_descriptor(descriptor)
    finally:
        os.close(descriptor)


def _write_manifest_to_stage(stage: Path, raw: bytes) -> None:
    destination = stage / "snapshot-manifest.json"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(destination, flags, 0o600)
    try:
        _write_all(descriptor, raw)
        _fsync_descriptor(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return
    try:
        _fsync_descriptor(descriptor)
    finally:
        os.close(descriptor)


def _fsync_stage_directories(stage: Path) -> None:
    directories = [stage, *(path for path in stage.rglob("*") if path.is_dir())]
    for directory in sorted(
        directories,
        key=lambda value: len(value.parts),
        reverse=True,
    ):
        _fsync_directory(directory)


def _validate_staged_snapshot(state: _PreparationState, stage: Path) -> None:
    manifest, manifest_raw, _members = _verify_snapshot_tree(
        stage,
        expected_bundle_sha256=state.manifest.bundle_sha256,
        expected_manifest_sha256=state.result.snapshot_manifest_sha256,
        expected_manifest_raw=state.manifest_raw,
        expected_contents={
            member.relpath: member.content
            for member in state.authority.copy_members
        },
        require_bundle_name=False,
    )
    if (
        manifest.snapshot_root_sha256 != state.result.snapshot_root_sha256
        or manifest_raw != state.manifest_raw
    ):
        _raise(KoreanFoundationSnapshotReasonCode.SNAPSHOT_ROOT_HASH_MISMATCH)


def _rename_snapshot_stage(stage: Path, target: Path) -> None:
    os.rename(stage, target)


def _cleanup_own_stage(stage: Path) -> None:
    try:
        value = stage.lstat()
    except FileNotFoundError:
        return
    except OSError:
        return
    if (
        stage.name.startswith(".staging-")
        and not _stat_is_link_or_reparse(value)
        and stat.S_ISDIR(value.st_mode)
    ):
        try:
            shutil.rmtree(stage)
        except OSError:
            pass


def _stage_prepared_snapshot(
    state: _PreparationState,
    paths: _KoreanFoundationSnapshotPaths,
) -> None:
    stage: Path | None = None
    try:
        if state.snapshot_root_missing:
            paths.snapshot_root.mkdir(mode=0o700)
        stage = Path(
            tempfile.mkdtemp(prefix=".staging-", dir=paths.snapshot_root)
        )
        try:
            os.chmod(stage, 0o700)
        except OSError:
            pass
        for member in state.authority.copy_members:
            _copy_member_to_stage(stage, member)
        _write_manifest_to_stage(stage, state.manifest_raw)
        _fsync_stage_directories(stage)
        _validate_staged_snapshot(state, stage)
        _rename_snapshot_stage(stage, state.target)
        stage = None
        _fsync_directory(paths.snapshot_root)
    except KoreanFoundationSnapshotError as exc:
        if stage is not None:
            _cleanup_own_stage(stage)
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.SNAPSHOT_PREPARATION_FAILED
        ) from exc
    except OSError as exc:
        if stage is not None:
            _cleanup_own_stage(stage)
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.SNAPSHOT_PREPARATION_FAILED
        ) from exc


def prepare_korean_foundation_snapshot_from_receipt(
    *,
    expected_receipt_sha256: str,
) -> PreparedKoreanFoundationSnapshot:
    """Validate under the shared lock before recovery and immutable preparation."""

    paths = _FIXED_PATHS
    with _korean_foundation_state_lock(paths.project_dir):
        state = _validate_preparation_state(
            paths,
            expected_receipt_sha256=expected_receipt_sha256,
        )
        if state.exact_target_exists:
            return state.result
        try:
            _recover_stale_stages(
                state.stale_stages,
                snapshot_root=paths.snapshot_root,
            )
        except (OSError, KoreanFoundationSnapshotError) as exc:
            raise KoreanFoundationSnapshotError(
                KoreanFoundationSnapshotReasonCode.SNAPSHOT_PREPARATION_FAILED
            ) from exc
        _stage_prepared_snapshot(state, paths)
        return state.result


def _verify_prepared_read_only(
    paths: _KoreanFoundationSnapshotPaths,
    *,
    expected_receipt_sha256: str,
) -> KoreanFoundationPreparedVerificationReport:
    authority = _read_receipt_authority(
        paths,
        expected_receipt_sha256=expected_receipt_sha256,
        require_recorded_prestate=True,
    )
    manifest, manifest_raw, result = _build_snapshot_manifest(authority)
    target = paths.snapshot_root / manifest.bundle_sha256
    expected_contents = {
        member.relpath: member.content for member in authority.copy_members
    }
    _verify_snapshot_tree(
        target,
        expected_bundle_sha256=manifest.bundle_sha256,
        expected_manifest_sha256=result.snapshot_manifest_sha256,
        expected_manifest_raw=manifest_raw,
        expected_contents=expected_contents,
    )

    evidence = _evidence_api()
    evidence_paths = _snapshot_evidence_paths(paths)
    try:
        evidence._assert_state_unchanged(evidence_paths, authority.validated)
        final_receipt = evidence._read_regular_file(
            paths.receipt,
            paths=evidence_paths,
            maximum_bytes=evidence._RECEIPT_MAX_BYTES,
            missing_reason=evidence.KoreanFoundationEvidenceReasonCode.RECEIPT_MISSING,
        )
        final_marker, final_prestate = evidence._read_active_prestate(evidence_paths)
    except evidence.KoreanFoundationEvidenceError as exc:
        raise _translate_evidence_failure(exc) from exc
    if (
        final_receipt != authority.receipt_raw
        or sha256(final_receipt).hexdigest() != authority.receipt_sha256
        or final_marker != authority.receipt.active_prestate_marker
        or final_prestate != authority.receipt.active_prestate_sha256
    ):
        _raise(KoreanFoundationSnapshotReasonCode.AUTHORITY_DRIFT)
    _verify_snapshot_tree(
        target,
        expected_bundle_sha256=manifest.bundle_sha256,
        expected_manifest_sha256=result.snapshot_manifest_sha256,
        expected_manifest_raw=manifest_raw,
        expected_contents=expected_contents,
    )
    try:
        evidence._assert_state_unchanged(evidence_paths, authority.validated)
    except evidence.KoreanFoundationEvidenceError as exc:
        raise _translate_evidence_failure(exc) from exc
    return KoreanFoundationPreparedVerificationReport.model_validate(
        result.model_dump(mode="json")
    )


def verify_prepared_korean_foundation_snapshot(
    *,
    expected_receipt_sha256: str,
) -> KoreanFoundationPreparedVerificationReport:
    """Strictly read and re-read one prepared snapshot without lock or repair."""

    return _verify_prepared_read_only(
        _FIXED_PATHS,
        expected_receipt_sha256=expected_receipt_sha256,
    )


def _active_pointer_for_prepared(
    prepared: PreparedKoreanFoundationSnapshot,
) -> KoreanFoundationActivePointer:
    return KoreanFoundationActivePointer(
        schema_version=2,
        pointer_version=KOREAN_FOUNDATION_ACTIVE_POINTER_VERSION,
        receipt_sha256=prepared.receipt_sha256,
        bundle_sha256=prepared.bundle_sha256,
        snapshot_relpath=f"snapshots/{prepared.bundle_sha256}",
        snapshot_manifest_sha256=prepared.snapshot_manifest_sha256,
        snapshot_root_sha256=prepared.snapshot_root_sha256,
        active_prestate_sha256=prepared.active_prestate_sha256,
        authorization_sha256=prepared.authorization_sha256,
    )


def _read_current_pointer_raw(
    paths: _KoreanFoundationSnapshotPaths,
    authority: _AuthorityState,
) -> bytes | None:
    if authority.current_prestate_marker == "absent":
        return None
    evidence = _evidence_api()
    evidence_paths = _snapshot_evidence_paths(paths)
    try:
        raw = evidence._read_regular_file(
            paths.active_pointer,
            paths=evidence_paths,
            maximum_bytes=_POINTER_MAX_BYTES,
            missing_reason=(
                evidence.KoreanFoundationEvidenceReasonCode.ACTIVE_PRESTATE_INVALID
            ),
        )
    except evidence.KoreanFoundationEvidenceError as exc:
        raise _translate_evidence_failure(exc) from exc
    if sha256(raw).hexdigest() != authority.current_prestate_sha256:
        _raise(KoreanFoundationSnapshotReasonCode.ACTIVE_PRESTATE_DRIFT)
    _parse_pointer(raw)
    return raw


def _validate_activation_state(
    paths: _KoreanFoundationSnapshotPaths,
    *,
    expected_receipt_sha256: str,
    authorization_sha256: str | None,
) -> _ActivationState:
    if authorization_sha256 is not None:
        try:
            _sha256_text(
                authorization_sha256,
                field_name="activation authorization hash",
            )
        except ValueError as exc:
            raise KoreanFoundationSnapshotError(
                KoreanFoundationSnapshotReasonCode.ACTIVATION_AUTHORIZATION_MISMATCH
            ) from exc
    authority = _read_receipt_authority(
        paths,
        expected_receipt_sha256=expected_receipt_sha256,
        require_recorded_prestate=False,
    )
    manifest, manifest_raw, prepared = _build_snapshot_manifest(authority)
    if (
        authorization_sha256 is not None
        and authorization_sha256 != prepared.authorization_sha256
    ):
        _raise(
            KoreanFoundationSnapshotReasonCode.ACTIVATION_AUTHORIZATION_MISMATCH
        )
    target, stale_stages, _root_missing, exact_target = _inspect_snapshot_area(
        paths,
        manifest=manifest,
        manifest_raw=manifest_raw,
        copy_members=authority.copy_members,
    )
    if not exact_target:
        _raise(KoreanFoundationSnapshotReasonCode.IMMUTABLE_SNAPSHOT_COLLISION)
    pointer = _active_pointer_for_prepared(prepared)
    pointer_raw = _json_file_bytes(pointer)
    pointer_sha256 = sha256(pointer_raw).hexdigest()
    current_pointer_raw = _read_current_pointer_raw(paths, authority)
    already_active = current_pointer_raw == pointer_raw
    receipt = authority.receipt
    if not already_active and (
        authority.current_prestate_marker != receipt.active_prestate_marker
        or authority.current_prestate_sha256 != receipt.active_prestate_sha256
    ):
        _raise(KoreanFoundationSnapshotReasonCode.ACTIVE_PRESTATE_DRIFT)

    evidence = _evidence_api()
    try:
        evidence._assert_state_unchanged(
            _snapshot_evidence_paths(paths),
            authority.validated,
        )
    except evidence.KoreanFoundationEvidenceError as exc:
        raise _translate_evidence_failure(exc) from exc
    _verify_snapshot_tree(
        target,
        expected_bundle_sha256=manifest.bundle_sha256,
        expected_manifest_sha256=prepared.snapshot_manifest_sha256,
        expected_manifest_raw=manifest_raw,
        expected_contents={
            member.relpath: member.content for member in authority.copy_members
        },
    )
    if _read_current_pointer_raw(paths, authority) != current_pointer_raw:
        _raise(KoreanFoundationSnapshotReasonCode.ACTIVE_PRESTATE_DRIFT)
    return _ActivationState(
        authority=authority,
        prepared=prepared,
        manifest=manifest,
        manifest_raw=manifest_raw,
        target=target,
        stale_stages=stale_stages,
        pointer=pointer,
        pointer_raw=pointer_raw,
        pointer_sha256=pointer_sha256,
        already_active=already_active,
    )


def _write_pointer_temp(
    paths: _KoreanFoundationSnapshotPaths,
    raw: bytes,
) -> Path:
    descriptor = -1
    temporary_name: str | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".active-foundations.",
            suffix=".tmp",
            dir=paths.candidate_dir,
        )
        try:
            os.fchmod(descriptor, 0o600)
        except (AttributeError, OSError):
            pass
        _write_all(descriptor, raw)
        _fsync_descriptor(descriptor)
        os.close(descriptor)
        descriptor = -1
        result = Path(temporary_name)
        temporary_name = None
        return result
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass


def _replace_active_pointer(temporary_path: Path, pointer_path: Path) -> None:
    os.replace(temporary_path, pointer_path)


def _atomic_activate_pointer(
    paths: _KoreanFoundationSnapshotPaths,
    raw: bytes,
) -> None:
    temporary_path: Path | None = None
    try:
        temporary_path = _write_pointer_temp(paths, raw)
        _replace_active_pointer(temporary_path, paths.active_pointer)
        temporary_path = None
        _fsync_directory(paths.candidate_dir)
    except OSError as exc:
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.ACTIVATION_FAILED
        ) from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass


def _activation_result(
    state: _ActivationState,
    *,
    activated: bool,
    already_active: bool,
) -> KoreanFoundationActivationResult:
    return KoreanFoundationActivationResult.model_validate(
        {
            **state.prepared.model_dump(mode="json"),
            "activated": activated,
            "already_active": already_active,
            "active_pointer_sha256": state.pointer_sha256,
        }
    )


def activate_prepared_korean_foundation_snapshot_from_receipt(
    *,
    expected_receipt_sha256: str,
    authorization_sha256: str,
) -> KoreanFoundationActivationResult:
    """Validate everything under the shared lock before one atomic pointer swap."""

    paths = _FIXED_PATHS
    with _korean_foundation_state_lock(paths.project_dir):
        state = _validate_activation_state(
            paths,
            expected_receipt_sha256=expected_receipt_sha256,
            authorization_sha256=authorization_sha256,
        )
        if state.already_active:
            return _activation_result(
                state,
                activated=False,
                already_active=True,
            )
        try:
            _recover_stale_stages(
                state.stale_stages,
                snapshot_root=paths.snapshot_root,
            )
        except (OSError, KoreanFoundationSnapshotError) as exc:
            raise KoreanFoundationSnapshotError(
                KoreanFoundationSnapshotReasonCode.ACTIVATION_FAILED
            ) from exc
        _atomic_activate_pointer(paths, state.pointer_raw)
        return _activation_result(
            state,
            activated=True,
            already_active=False,
        )


def verify_active_korean_foundation_snapshot_provenance(
    *,
    expected_receipt_sha256: str,
) -> KoreanFoundationActiveProvenanceReport:
    """Read only the receipt, authority, immutable tree, and active provenance."""

    try:
        state = _validate_activation_state(
            _FIXED_PATHS,
            expected_receipt_sha256=expected_receipt_sha256,
            authorization_sha256=None,
        )
        if not state.already_active:
            _raise(KoreanFoundationSnapshotReasonCode.ACTIVE_PROVENANCE_INVALID)
    except KoreanFoundationSnapshotError as exc:
        if exc.reason_code in {
            KoreanFoundationSnapshotReasonCode.RECEIPT_MISSING,
            KoreanFoundationSnapshotReasonCode.RECEIPT_HASH_MISMATCH,
        }:
            raise
        raise KoreanFoundationSnapshotError(
            KoreanFoundationSnapshotReasonCode.ACTIVE_PROVENANCE_INVALID
        ) from exc
    return KoreanFoundationActiveProvenanceReport.model_validate(
        {
            **state.prepared.model_dump(mode="json"),
            "active": True,
            "active_pointer_sha256": state.pointer_sha256,
        }
    )


__all__ = [
    "ACTIVE_KOREAN_FOUNDATIONS_POINTER_PATH",
    "KOREAN_FOUNDATION_ACTIVATION_AUTHORIZATION_VERSION",
    "KOREAN_FOUNDATION_ACTIVE_POINTER_VERSION",
    "KOREAN_FOUNDATION_PREPARED_VERIFICATION_VERSION",
    "KOREAN_FOUNDATION_SNAPSHOT_CONTRACT_VERSION",
    "KOREAN_FOUNDATION_SNAPSHOT_ROOT",
    "KoreanFoundationActivationResult",
    "KoreanFoundationActiveProvenanceReport",
    "KoreanFoundationActivePointer",
    "KoreanFoundationPreparedVerificationReport",
    "KoreanFoundationSnapshotError",
    "KoreanFoundationSnapshotManifest",
    "KoreanFoundationSnapshotMember",
    "KoreanFoundationSnapshotReasonCode",
    "PreparedKoreanFoundationSnapshot",
    "ResolvedKoreanFoundationSnapshot",
    "ResolvedKoreanFoundationSnapshotMember",
    "activate_prepared_korean_foundation_snapshot_from_receipt",
    "korean_foundation_activation_authorization_sha256",
    "prepare_korean_foundation_snapshot_from_receipt",
    "resolve_active_korean_foundation_snapshot",
    "verify_active_korean_foundation_snapshot_provenance",
    "verify_prepared_korean_foundation_snapshot",
]
