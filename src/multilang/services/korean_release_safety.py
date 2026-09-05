"""Offline Korean release safety and durable local promotion."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from shutil import move
from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator


KOREAN_RELEASE_INPUT_MEMBER_PATHS: tuple[str, ...] = (
    "text-review-application.json",
    "audio-review-application.json",
    "generation-report.json",
    "generation-report.md",
    "production-before-evidence.json",
    "production-after-evidence.json",
    "production-audit.json",
    "production-audit.md",
    "offline-suite.json",
    "dependency-evidence.json",
    "korean-frequency.apkg",
)
KOREAN_RELEASE_GENERATED_MEMBER_PATHS: tuple[str, ...] = ("release-safety.json", "production-build-result.json")
KOREAN_RELEASE_PROMOTION_MEMBER_PATHS: tuple[str, ...] = KOREAN_RELEASE_INPUT_MEMBER_PATHS + KOREAN_RELEASE_GENERATED_MEMBER_PATHS

_HEX = frozenset("0123456789abcdef")
_PRIVATE_MARKERS = (b"LEAK", b"private/audio", b"/home/", b"\\home\\")


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class KoreanReleaseMemberSafety(_FrozenModel):
    member: str
    sha256: str = Field(min_length=64, max_length=64)
    byte_size: int = Field(ge=0)
    visibility: str
    sensitivity: str
    retention: str
    license_id: str = Field(min_length=1)
    attribution_id: str = Field(min_length=1)
    safe_for_local_release: bool
    safe_to_publish: bool
    control_ids: tuple[str, ...]

    @field_validator("sha256")
    @classmethod
    def hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_identifier(value, field_name="sha256")


class KoreanReleaseSafetyReport(_FrozenModel):
    kind: str = "korean-release-safety"
    report_sha256: str = Field(min_length=64, max_length=64)
    safe_for_local_release: bool
    safe_to_publish: bool
    member_count: int = Field(ge=0)
    members: tuple[KoreanReleaseMemberSafety, ...]
    authority_sha256s: dict[str, str]
    privacy: dict[str, object]

    @field_validator("report_sha256")
    @classmethod
    def report_hash_must_be_sha256(cls, value: str) -> str:
        return _sha256_identifier(value, field_name="report_sha256")


class KoreanReleaseBuildResult(_FrozenModel):
    kind: str = "korean-release-build-result"
    build_result_sha256: str = Field(min_length=64, max_length=64)
    safety_report_sha256: str = Field(min_length=64, max_length=64)
    member_root_sha256: str = Field(min_length=64, max_length=64)
    member_count: int = Field(ge=0)
    authority_sha256s: dict[str, str]


class KoreanReleasePromotionResult(_FrozenModel):
    status: str
    target_name: str
    target_root_sha256: str = Field(min_length=64, max_length=64)
    manifest_sha256: str = Field(min_length=64, max_length=64)
    pointer_sha256: str = Field(min_length=64, max_length=64)
    member_count: int = Field(ge=0)


class KoreanReleaseAuthorization(_FrozenModel):
    kind: str = "korean-release-authorization"
    authorization_sha256: str = Field(min_length=64, max_length=64)
    release_root_sha256: str = Field(min_length=64, max_length=64)
    pointer_sha256: str = Field(min_length=64, max_length=64)
    commit_members: tuple[str, ...]
    publication_members: tuple[str, ...]
    commit_token_present: bool
    publication_token_present: bool
    zero_action_channels: tuple[str, ...]
    authorization_sha256s: dict[str, str]


def build_korean_release_safety(
    *,
    staging_root: Path,
    member_controls: Mapping[str, Mapping[str, object]],
    authority_sha256s: Mapping[str, str],
) -> tuple[KoreanReleaseSafetyReport, KoreanReleaseBuildResult]:
    staging_root = _safe_directory(staging_root)
    _validate_authorities(authority_sha256s)
    members = tuple(_build_member_safety(staging_root, member, member_controls.get(member)) for member in KOREAN_RELEASE_INPUT_MEMBER_PATHS)
    safe_for_local_release = all(member.safe_for_local_release for member in members)
    safe_to_publish = safe_for_local_release and all(member.safe_to_publish for member in members)
    payload = {
        "kind": "korean-release-safety",
        "safe_for_local_release": safe_for_local_release,
        "safe_to_publish": safe_to_publish,
        "member_count": len(members),
        "members": [member.model_dump(mode="json") for member in members],
        "authority_sha256s": dict(sorted(authority_sha256s.items())),
        "privacy": {
            "excluded": ["learner_text", "korean_text", "prompts", "provider_payloads", "credentials", "private_paths"],
            "private_markers_rejected": True,
        },
    }
    report_sha256 = _canonical_sha256(payload)
    report = KoreanReleaseSafetyReport(**payload, report_sha256=report_sha256)
    safety_path = staging_root / "release-safety.json"
    _write_json_atomic(safety_path, report.model_dump(mode="json"))
    safety_report_sha256 = _sha256_file(safety_path)
    build_payload = {
        "kind": "korean-release-build-result",
        "safety_report_sha256": safety_report_sha256,
        "member_root_sha256": _member_root_sha256(staging_root, KOREAN_RELEASE_INPUT_MEMBER_PATHS),
        "member_count": len(KOREAN_RELEASE_INPUT_MEMBER_PATHS),
        "authority_sha256s": dict(sorted(authority_sha256s.items())),
    }
    build = KoreanReleaseBuildResult(**build_payload, build_result_sha256=_canonical_sha256(build_payload))
    _write_json_atomic(staging_root / "production-build-result.json", build.model_dump(mode="json"))
    return report, build


def promote_korean_release_bundle(
    *,
    staging_root: Path,
    release_parent: Path,
    current_pointer: Path,
    authorization_sha256: str,
    safety_report: KoreanReleaseSafetyReport,
    build_result: KoreanReleaseBuildResult,
) -> KoreanReleasePromotionResult:
    authorization_sha256 = _sha256_identifier(authorization_sha256, field_name="authorization_sha256")
    release_parent = _safe_directory(release_parent, create=True)
    staging_root = staging_root.resolve()
    target = (release_parent / authorization_sha256).resolve()
    if staging_root == target:
        raise ValueError("Korean release staging must be distinct from target")
    if release_parent not in staging_root.parents:
        raise ValueError("Korean release staging root must be inside release parent")
    if authorization_sha256 not in staging_root.name:
        raise ValueError("Korean release staging name must include authorization hash")
    if target.exists():
        return _validate_existing_target(target=target, current_pointer=current_pointer, authorization_sha256=authorization_sha256)
    if not safety_report.safe_for_local_release:
        raise ValueError("Korean release safety does not allow local release")
    _validate_build_inputs(staging_root, safety_report=safety_report, build_result=build_result)

    manifest_payload = _release_manifest_payload(staging_root, authorization_sha256=authorization_sha256)
    manifest_path = staging_root / "release-manifest.json"
    _write_json_atomic(manifest_path, manifest_payload)
    _fsync_tree(staging_root, KOREAN_RELEASE_PROMOTION_MEMBER_PATHS + ("release-manifest.json",))
    root_sha256 = _member_root_sha256(staging_root, KOREAN_RELEASE_PROMOTION_MEMBER_PATHS + ("release-manifest.json",))
    manifest_sha256 = _sha256_file(manifest_path)
    move(str(staging_root), str(target))
    _fsync_directory(release_parent)
    pointer_payload = {
        "kind": "korean-current-release-pointer",
        "target_name": authorization_sha256,
        "target_root_sha256": root_sha256,
        "manifest_sha256": manifest_sha256,
        "member_count": len(KOREAN_RELEASE_PROMOTION_MEMBER_PATHS),
    }
    _write_json_atomic(current_pointer, pointer_payload)
    _fsync_directory(current_pointer.parent)
    pointer_sha256 = _sha256_file(current_pointer)
    return KoreanReleasePromotionResult(
        status="promoted",
        target_name=authorization_sha256,
        target_root_sha256=root_sha256,
        manifest_sha256=manifest_sha256,
        pointer_sha256=pointer_sha256,
        member_count=len(KOREAN_RELEASE_PROMOTION_MEMBER_PATHS),
    )


def validate_korean_release_authorization(
    *,
    release_dir: Path,
    current_pointer: Path,
    authorization_sha256: str,
    safety_report: KoreanReleaseSafetyReport,
    build_result: KoreanReleaseBuildResult,
    commit_members: list[str] | tuple[str, ...] = (),
    publication_members: list[str] | tuple[str, ...] = (),
    commit_token_sha256: str | None = None,
    publication_token_sha256: str | None = None,
) -> KoreanReleaseAuthorization:
    authorization_sha256 = _sha256_identifier(authorization_sha256, field_name="authorization_sha256")
    release_dir = _safe_directory(release_dir)
    if release_dir.name != authorization_sha256:
        raise ValueError("Korean release authorization target drift")
    if not current_pointer.is_file() or current_pointer.is_symlink():
        raise ValueError("Korean release authorization pointer missing")
    try:
        pointer = json.loads(current_pointer.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Korean release authorization pointer drift") from exc
    if not isinstance(pointer, Mapping) or pointer.get("target_name") != authorization_sha256:
        raise ValueError("Korean release authorization pointer target drift")
    _validate_build_inputs(release_dir, safety_report=safety_report, build_result=build_result)
    release_root_sha256 = _member_root_sha256(release_dir, KOREAN_RELEASE_PROMOTION_MEMBER_PATHS + ("release-manifest.json",))
    if pointer.get("target_root_sha256") != release_root_sha256:
        raise ValueError("Korean release authorization root drift")
    member_safety = {member.member: member for member in safety_report.members}
    commit_tuple = tuple(_safe_authorized_member(member) for member in commit_members)
    publication_tuple = tuple(_safe_authorized_member(member) for member in publication_members)
    for member in commit_tuple:
        if member in member_safety and not member_safety[member].safe_for_local_release:
            raise ValueError("Korean release authorization commit scope drift")
    for member in publication_tuple:
        if member not in member_safety or not member_safety[member].safe_to_publish:
            raise ValueError("Korean release authorization publication scope drift")
    if commit_tuple and commit_token_sha256 is None:
        raise ValueError("Korean release authorization commit token missing")
    if publication_tuple and publication_token_sha256 is None:
        raise ValueError("Korean release authorization publication token missing")
    if commit_token_sha256 is not None:
        _sha256_identifier(commit_token_sha256, field_name="commit_token_sha256")
    if publication_token_sha256 is not None:
        _sha256_identifier(publication_token_sha256, field_name="publication_token_sha256")
    zero_channels = tuple(
        channel
        for channel, token in (("commit", commit_token_sha256), ("publication", publication_token_sha256))
        if token is None
    )
    return KoreanReleaseAuthorization(
        authorization_sha256=authorization_sha256,
        release_root_sha256=release_root_sha256,
        pointer_sha256=_sha256_file(current_pointer),
        commit_members=commit_tuple,
        publication_members=publication_tuple,
        commit_token_present=commit_token_sha256 is not None,
        publication_token_present=publication_token_sha256 is not None,
        zero_action_channels=zero_channels,
        authorization_sha256s=dict(sorted(safety_report.authority_sha256s.items())),
    )


def _build_member_safety(staging_root: Path, member: str, controls: Mapping[str, object] | None) -> KoreanReleaseMemberSafety:
    relative = _safe_relative_member(member)
    path = staging_root / relative
    if not path.is_file() or path.is_symlink():
        raise ValueError("Korean release member missing")
    data = path.read_bytes()
    if any(marker in data for marker in _PRIVATE_MARKERS):
        raise ValueError("Korean release private content drift")
    controls = controls or {}
    required_true = ("local_use_allowed", "privacy_scan_passed", "security_scan_passed", "retention_control_passed")
    local_pass = all(bool(controls.get(name)) for name in required_true)
    visibility = str(controls.get("visibility", "unknown"))
    publication_allowed = bool(controls.get("publication_allowed"))
    safe_to_publish = local_pass and publication_allowed and visibility == "public"
    return KoreanReleaseMemberSafety(
        member=str(relative),
        sha256=sha256(data).hexdigest(),
        byte_size=len(data),
        visibility=visibility,
        sensitivity=str(controls.get("sensitivity", "unknown")),
        retention=str(controls.get("retention", "unknown")),
        license_id=str(controls.get("license_id", "")),
        attribution_id=str(controls.get("attribution_id", "")),
        safe_for_local_release=local_pass,
        safe_to_publish=safe_to_publish,
        control_ids=tuple(sorted(name for name in required_true if bool(controls.get(name)))),
    )


def _validate_build_inputs(
    staging_root: Path,
    *,
    safety_report: KoreanReleaseSafetyReport,
    build_result: KoreanReleaseBuildResult,
) -> None:
    safety_path = staging_root / "release-safety.json"
    build_path = staging_root / "production-build-result.json"
    if not safety_path.is_file() or not build_path.is_file():
        raise ValueError("Korean release generated evidence missing")
    if _sha256_file(safety_path) != build_result.safety_report_sha256:
        raise ValueError("Korean release safety report drift")
    members_by_name = {member.member: member for member in safety_report.members}
    if set(members_by_name) != set(KOREAN_RELEASE_INPUT_MEMBER_PATHS):
        raise ValueError("Korean release safety member drift")
    for member in KOREAN_RELEASE_INPUT_MEMBER_PATHS:
        path = staging_root / member
        if not path.is_file() or _sha256_file(path) != members_by_name[member].sha256:
            raise ValueError("Korean release member hash drift")
        if not members_by_name[member].safe_for_local_release:
            raise ValueError("Korean release member is not local-release safe")
    if build_result.member_root_sha256 != _member_root_sha256(staging_root, KOREAN_RELEASE_INPUT_MEMBER_PATHS):
        raise ValueError("Korean release build result drift")


def _validate_existing_target(
    *,
    target: Path,
    current_pointer: Path,
    authorization_sha256: str,
) -> KoreanReleasePromotionResult:
    manifest_path = target / "release-manifest.json"
    if not manifest_path.is_file() or not current_pointer.is_file():
        raise ValueError("Korean release target collision drift")
    root_sha256 = _member_root_sha256(target, KOREAN_RELEASE_PROMOTION_MEMBER_PATHS + ("release-manifest.json",))
    manifest_sha256 = _sha256_file(manifest_path)
    try:
        pointer = json.loads(current_pointer.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Korean release pointer drift") from exc
    if not isinstance(pointer, Mapping) or pointer.get("target_name") != authorization_sha256:
        raise ValueError("Korean release pointer target drift")
    if pointer.get("target_root_sha256") != root_sha256 or pointer.get("manifest_sha256") != manifest_sha256:
        raise ValueError("Korean release pointer hash drift")
    return KoreanReleasePromotionResult(
        status="already_current",
        target_name=authorization_sha256,
        target_root_sha256=root_sha256,
        manifest_sha256=manifest_sha256,
        pointer_sha256=_sha256_file(current_pointer),
        member_count=len(KOREAN_RELEASE_PROMOTION_MEMBER_PATHS),
    )


def _release_manifest_payload(staging_root: Path, *, authorization_sha256: str) -> dict[str, object]:
    members = []
    for member in KOREAN_RELEASE_PROMOTION_MEMBER_PATHS:
        relative = _safe_relative_member(member)
        path = staging_root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError("Korean release manifest member missing")
        data = path.read_bytes()
        if any(marker in data for marker in _PRIVATE_MARKERS):
            raise ValueError("Korean release private content drift")
        members.append({"member": str(relative), "sha256": sha256(data).hexdigest(), "byte_size": len(data)})
    return {
        "kind": "korean-release-manifest",
        "authorization_sha256": authorization_sha256,
        "member_count": len(members),
        "members": members,
    }


def _member_root_sha256(root: Path, members: tuple[str, ...]) -> str:
    payload = []
    for member in members:
        relative = _safe_relative_member(member)
        path = root / relative
        if not path.is_file():
            raise ValueError("Korean release member missing")
        payload.append({"member": str(relative), "sha256": _sha256_file(path), "byte_size": path.stat().st_size})
    return _canonical_sha256(payload)


def _safe_directory(path: Path, *, create: bool = False) -> Path:
    if create:
        path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir() or path.is_symlink():
        raise ValueError("Korean release directory drift")
    return path.resolve()


def _safe_relative_member(member: str) -> Path:
    path = Path(member)
    if path.is_absolute() or ".." in path.parts or not member or member.endswith("/"):
        raise ValueError("Korean release member path drift")
    return path


def _safe_authorized_member(member: str) -> str:
    relative = str(_safe_relative_member(member))
    if relative not in KOREAN_RELEASE_PROMOTION_MEMBER_PATHS:
        raise ValueError("Korean release authorization member scope drift")
    return relative


def _validate_authorities(authority_sha256s: Mapping[str, str]) -> None:
    if not authority_sha256s:
        raise ValueError("Korean release authority missing")
    for label, value in authority_sha256s.items():
        if not label or any(character in label for character in "./\\"):
            raise ValueError("Korean release authority label drift")
        _sha256_identifier(str(value), field_name=f"{label}_sha256")


def _sha256_identifier(value: str, *, field_name: str) -> str:
    if len(value) != 64 or any(character not in _HEX for character in value):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _write_json_atomic(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    if temp_path.exists():
        raise ValueError("Korean release temporary output already exists")
    try:
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _fsync_file(temp_path)
        temp_path.replace(path)
        _fsync_directory(path.parent)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def _fsync_tree(root: Path, members: tuple[str, ...]) -> None:
    for member in members:
        _fsync_file(root / member)
    for directory in sorted({(root / member).parent for member in members}, key=lambda path: len(path.parts), reverse=True):
        _fsync_directory(directory)


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


__all__ = [
    "KOREAN_RELEASE_GENERATED_MEMBER_PATHS",
    "KOREAN_RELEASE_INPUT_MEMBER_PATHS",
    "KOREAN_RELEASE_PROMOTION_MEMBER_PATHS",
    "KoreanReleaseBuildResult",
    "KoreanReleaseAuthorization",
    "KoreanReleaseMemberSafety",
    "KoreanReleasePromotionResult",
    "KoreanReleaseSafetyReport",
    "build_korean_release_safety",
    "promote_korean_release_bundle",
    "validate_korean_release_authorization",
]
