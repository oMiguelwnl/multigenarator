"""Least-power checkpoint authority validation for Korean frequency work."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multilang.domain.korean import raw_bytes_sha256

_JSON_FENCE_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL)
_LOWERCASE_HEX = frozenset("0123456789abcdef")

_POWER_REGISTRY: dict[str, tuple[str, ...]] = {
    "source-access": ("retrieve-source",),
    "transformation-build": ("build-inactive-bundle",),
    "final-bundle": ("bind-final-bundle",),
    "pilot": ("run-bounded-pilot",),
    "provider-review": ("review-provider-route",),
    "production-database-migration": ("run-production-migration",),
    "profile-sample": ("capture-profile-sample",),
    "heard-review": ("record-heard-review",),
    "full-run": ("run-full-generation",),
    "no-remediation-continuation": ("continue-without-remediation",),
    "remediation": ("remediate-bound-text", "reject-dependent-audio"),
    "final-promotion": ("promote-final-output",),
    "final-release": ("release-final-output",),
}


class _AuthorityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


def _hash(value: str, *, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _LOWERCASE_HEX for character in value)
    ):
        raise ValueError(f"{field_name} must be lowercase SHA-256")
    return value


def _safe_relative(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("binding path must be relative")
    normalized = value.strip().replace("\\", "/")
    parts = tuple(part for part in normalized.split("/") if part)
    if (
        normalized != value
        or not normalized
        or normalized.startswith("/")
        or normalized.startswith("~")
        or "//" in normalized
        or any(part in {".", ".."} for part in parts)
    ):
        raise ValueError("binding path must be relative")
    return normalized


class KoreanAuthorityBinding(_AuthorityModel):
    path: str = Field(min_length=1, max_length=256)
    sha256: str = Field(min_length=64, max_length=64)
    byte_count: int = Field(ge=0, le=200_000_000)

    @field_validator("path")
    @classmethod
    def path_must_be_safe(cls, value: str) -> str:
        return _safe_relative(value)

    @field_validator("sha256")
    @classmethod
    def hash_must_be_valid(cls, value: str) -> str:
        return _hash(value, field_name="binding hash")


class KoreanDependentAudioRequest(_AuthorityModel):
    request_sha256: str = Field(min_length=64, max_length=64)
    profile_sha256: str = Field(min_length=64, max_length=64)

    @field_validator("request_sha256", "profile_sha256")
    @classmethod
    def hashes_must_be_valid(cls, value: str, info: object) -> str:
        return _hash(value, field_name=getattr(info, "field_name", "hash"))


class KoreanRemediationAuthorityEntry(_AuthorityModel):
    item_key: str = Field(min_length=1, max_length=128)
    word_spoken_text_sha256: str = Field(min_length=64, max_length=64)
    sentence_spoken_text_sha256: str = Field(min_length=64, max_length=64)
    dependent_audio_requests: tuple[KoreanDependentAudioRequest, ...] = Field(min_length=1, max_length=8)
    allows_new_audio_request: Literal[False]

    @field_validator("word_spoken_text_sha256", "sentence_spoken_text_sha256")
    @classmethod
    def hashes_must_be_valid(cls, value: str, info: object) -> str:
        return _hash(value, field_name=getattr(info, "field_name", "hash"))


class KoreanCheckpointAuthority(_AuthorityModel):
    schema_version: Literal["korean-checkpoint-authority-v1"]
    kind: str = Field(min_length=1, max_length=64)
    powers: tuple[str, ...] = Field(min_length=1, max_length=4)
    expected_kind: str = Field(min_length=1, max_length=64)
    bindings: tuple[KoreanAuthorityBinding, ...] = Field(default=(), max_length=16)
    expectations: dict[str, str] = Field(default_factory=dict)
    remediation_entries: tuple[KoreanRemediationAuthorityEntry, ...] = Field(default=(), max_length=3000)

    @field_validator("kind", "expected_kind")
    @classmethod
    def kind_must_be_registered(cls, value: str) -> str:
        if value not in _POWER_REGISTRY:
            raise ValueError("authority kind is not registered")
        return value

    @field_validator("powers")
    @classmethod
    def powers_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for power in value:
            if not isinstance(power, str) or power.strip() != power or power not in {p for powers in _POWER_REGISTRY.values() for p in powers}:
                raise ValueError("authority power is not registered")
        return value

    @field_validator("expectations")
    @classmethod
    def expectations_must_be_bounded_strings(cls, value: dict[str, str]) -> dict[str, str]:
        for key, item in value.items():
            if not isinstance(key, str) or not isinstance(item, str) or not key or len(key) > 64 or len(item) > 256:
                raise ValueError("authority expectations must be bounded strings")
        return value

    @model_validator(mode="after")
    def authority_must_match_fixed_registry(self) -> Self:
        if self.expected_kind != self.kind:
            raise ValueError("authority expected kind mismatch")
        if self.powers != _POWER_REGISTRY[self.kind]:
            raise ValueError("authority powers do not match fixed registry")
        if self.kind == "source-access" and "build-inactive-bundle" in self.powers:
            raise ValueError("source access cannot grant build power")
        if self.kind != "remediation" and self.remediation_entries:
            raise ValueError("only remediation authority may carry remediation entries")
        if self.kind == "remediation" and not self.remediation_entries:
            raise ValueError("remediation authority requires bound entries")
        return self


@dataclass(frozen=True, slots=True)
class KoreanCheckpointAuthorityValidationResult:
    kind: str
    powers: tuple[str, ...]
    binding_count: int
    authority_sha256: str


def _extract_authority_payload(authority_bytes: bytes) -> dict[str, Any]:
    try:
        text = authority_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("authority file must be UTF-8") from exc
    matches = _JSON_FENCE_RE.findall(text)
    if len(matches) != 1:
        raise ValueError("authority file must contain exactly one JSON section")
    try:
        payload = json.loads(matches[0])
    except json.JSONDecodeError as exc:
        raise ValueError("authority JSON is malformed") from exc
    if not isinstance(payload, dict):
        raise ValueError("authority JSON must be an object")
    return payload


def _verify_binding(root: Path, binding: KoreanAuthorityBinding) -> None:
    target = root / binding.path
    try:
        stat = target.lstat()
    except OSError as exc:
        raise ValueError("authority binding is unavailable") from exc
    if target.is_symlink() or not target.is_file():
        raise ValueError("authority binding is unsafe")
    payload = target.read_bytes()
    if stat.st_size != binding.byte_count or raw_bytes_sha256(payload) != binding.sha256:
        raise ValueError("authority binding hash drift")


def validate_korean_checkpoint_authority(
    authority_file: Path,
    *,
    expected_kind: str,
) -> KoreanCheckpointAuthorityValidationResult:
    """Validate one machine-readable checkpoint authority without trusting prose."""

    authority_path = Path(authority_file)
    try:
        if authority_path.is_symlink() or not authority_path.is_file():
            raise ValueError("authority file is unsafe")
        authority_bytes = authority_path.read_bytes()
        authority = KoreanCheckpointAuthority.model_validate(_extract_authority_payload(authority_bytes))
    except (OSError, ValueError) as exc:
        raise ValueError("authority validation failed") from exc
    if authority.kind != expected_kind:
        raise ValueError("authority kind mismatch")
    for binding in authority.bindings:
        _verify_binding(authority_path.parent, binding)
    return KoreanCheckpointAuthorityValidationResult(
        kind=authority.kind,
        powers=authority.powers,
        binding_count=len(authority.bindings),
        authority_sha256=raw_bytes_sha256(authority_bytes),
    )


__all__ = [
    "KoreanCheckpointAuthorityValidationResult",
    "validate_korean_checkpoint_authority",
]
