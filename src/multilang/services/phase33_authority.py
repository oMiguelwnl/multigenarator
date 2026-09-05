"""Phase 33 local authority and review-input safety helpers."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


_AUTHORITY_KINDS = frozenset(
    {
        "phase33-local-migration",
        "phase33-provider",
        "phase33-audio",
        "phase33-private",
        "phase33-prepared-output",
    }
)
_AUDIO_ROOTS = frozenset({"word", "sentence", "staging", "journal"})
_SHA256_ALPHABET = frozenset("0123456789abcdef")
_VALUE_MAX_BYTES = 16 * 1024
_EVIDENCE_MAX_BYTES = 64 * 1024
_REVIEW_EVIDENCE_KEYS = frozenset(
    {"schema_version", "source_kind", "policy_sha256", "evidence_sha256", "reviewer_id_sha256", "status"}
)


class Phase33AuthorityError(ValueError):
    """Raised when Phase 33 authority or review-input evidence is unsafe."""


class Phase33AuthorityPreflight(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str
    job_id: str
    policy_sha256: str
    curriculum_sha256: str
    profile_sha256: str
    source_sha256: str
    target_sha256: str
    output_pair_count: int = Field(ge=1)
    output_pairs_sha256: str
    audio_root_identities: dict[str, str]
    custom_count: int = Field(ge=1)
    custom_ids_sha256: str
    highlight_count: int = Field(ge=1)
    highlight_ids_sha256: str
    migration_revision: str
    private_capability: str
    max_private_tokens: int = Field(ge=1, le=24)


class Phase33AuthorityValidation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str
    kind: str
    job_id: str
    authority_sha256: str


class Phase33ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    relative_path: str
    sha256: str
    size_bytes: int
    text: str | None = None


def build_phase33_authority_preflight(
    *,
    job_id: str,
    policy_sha256: str,
    curriculum_sha256: str,
    profile_sha256: str,
    source_sha256: str,
    target_sha256: str,
    output_pairs: tuple[str, ...],
    audio_roots: dict[str, Path],
    custom_safe_ids: tuple[str, ...],
    highlight_safe_ids: tuple[str, ...],
    migration_revision: str,
    private_capability: str,
    max_private_tokens: int,
) -> Phase33AuthorityPreflight:
    """Build content-free local authority preflight evidence."""

    for name, value in {
        "policy_sha256": policy_sha256,
        "curriculum_sha256": curriculum_sha256,
        "profile_sha256": profile_sha256,
        "source_sha256": source_sha256,
        "target_sha256": target_sha256,
    }.items():
        _require_sha256(value, name)
    if not output_pairs:
        raise Phase33AuthorityError("authority preflight requires narrow output pairs")
    if set(audio_roots) != _AUDIO_ROOTS:
        raise Phase33AuthorityError("authority preflight requires all four audio roots")
    if not custom_safe_ids or not highlight_safe_ids:
        raise Phase33AuthorityError("authority preflight requires nonempty custom and highlight safe identities")
    if migration_revision != "20260828_19":
        raise Phase33AuthorityError("authority preflight requires migration revision 20260828_19")
    if private_capability != "phase33-private-token-v1" or max_private_tokens != 24:
        raise Phase33AuthorityError("authority preflight requires exact private capability")

    return Phase33AuthorityPreflight(
        status="ready",
        job_id=job_id,
        policy_sha256=policy_sha256,
        curriculum_sha256=curriculum_sha256,
        profile_sha256=profile_sha256,
        source_sha256=source_sha256,
        target_sha256=target_sha256,
        output_pair_count=len(output_pairs),
        output_pairs_sha256=_json_sha256(tuple(output_pairs)),
        audio_root_identities={key: _path_identity(value) for key, value in sorted(audio_roots.items())},
        custom_count=len(custom_safe_ids),
        custom_ids_sha256=_json_sha256(tuple(sorted(custom_safe_ids))),
        highlight_count=len(highlight_safe_ids),
        highlight_ids_sha256=_json_sha256(tuple(sorted(highlight_safe_ids))),
        migration_revision=migration_revision,
        private_capability=private_capability,
        max_private_tokens=max_private_tokens,
    )


def validate_phase33_authority(authority_file: Path, *, expected_kind: str) -> Phase33AuthorityValidation:
    if expected_kind not in _AUTHORITY_KINDS:
        raise Phase33AuthorityError("unsupported authority kind")
    payload = json.loads(authority_file.read_text(encoding="utf-8"))
    kind = str(payload.get("kind", ""))
    if kind != expected_kind:
        raise Phase33AuthorityError("authority kind mismatch")
    if kind not in _AUTHORITY_KINDS:
        raise Phase33AuthorityError("unsupported authority kind")
    _require_sha256(str(payload.get("policy_sha256", "")), "policy_sha256")
    if payload.get("migration_revision") not in {None, "20260828_19"}:
        raise Phase33AuthorityError("authority migration revision mismatch")
    if payload.get("private_capability") not in {None, "phase33-private-token-v1"}:
        raise Phase33AuthorityError("authority private capability mismatch")
    if payload.get("max_private_tokens") not in {None, 24}:
        raise Phase33AuthorityError("authority private token cap mismatch")
    return Phase33AuthorityValidation(
        status="valid",
        kind=kind,
        job_id=str(payload.get("job_id", "")),
        authority_sha256=sha256(authority_file.read_bytes()).hexdigest(),
    )


def read_phase33_review_input(path: Path, *, project_root: Path, kind: str) -> Phase33ReviewInput:
    """Read one bounded review input from the fixed inbox without following symlinks."""

    if kind not in {"value", "evidence"}:
        raise Phase33AuthorityError("unsupported review input kind")
    project_root = project_root.resolve()
    inbox = project_root / ".multilang" / "phase33" / "review-inputs"
    try:
        resolved_parent = path.parent.resolve(strict=True)
    except OSError as exc:
        raise Phase33AuthorityError("review input must be below fixed inbox") from exc
    if resolved_parent != inbox.resolve(strict=True):
        raise Phase33AuthorityError("review input must be below fixed inbox")
    if path.is_symlink():
        raise Phase33AuthorityError("review input symlink is not allowed")
    stat = path.stat(follow_symlinks=False)
    if not path.is_file():
        raise Phase33AuthorityError("review input must be a regular file")
    expected_suffix = ".txt" if kind == "value" else ".json"
    max_bytes = _VALUE_MAX_BYTES if kind == "value" else _EVIDENCE_MAX_BYTES
    if path.suffix != expected_suffix:
        raise Phase33AuthorityError("review input extension mismatch")
    if stat.st_size > max_bytes:
        raise Phase33AuthorityError("review input is too large")
    data = path.read_bytes()
    post_stat = path.stat(follow_symlinks=False)
    if (stat.st_ino, stat.st_size, stat.st_mtime_ns) != (post_stat.st_ino, post_stat.st_size, post_stat.st_mtime_ns):
        raise Phase33AuthorityError("review input changed while reading")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Phase33AuthorityError("review input must be utf-8") from exc
    if "\x00" in text:
        raise Phase33AuthorityError("review input must not contain NUL")
    if kind == "evidence":
        _validate_evidence_json(text)
        text_value: str | None = None
    else:
        text_value = text
    return Phase33ReviewInput(
        relative_path=path.relative_to(project_root).as_posix(),
        sha256=sha256(data).hexdigest(),
        size_bytes=len(data),
        text=text_value,
    )


def _validate_evidence_json(text: str) -> None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise Phase33AuthorityError("review evidence schema error") from exc
    if not isinstance(payload, dict) or not set(payload).issubset(_REVIEW_EVIDENCE_KEYS):
        raise Phase33AuthorityError("review evidence schema error")


def _require_sha256(value: str, name: str) -> None:
    if len(value) != 64 or any(character not in _SHA256_ALPHABET for character in value):
        raise Phase33AuthorityError(f"{name} must be lowercase sha256")


def _json_sha256(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _path_identity(path: Path) -> str:
    return sha256(str(path).encode("utf-8")).hexdigest()


__all__ = [
    "Phase33AuthorityError",
    "Phase33AuthorityPreflight",
    "Phase33AuthorityValidation",
    "Phase33ReviewInput",
    "build_phase33_authority_preflight",
    "read_phase33_review_input",
    "validate_phase33_authority",
]
