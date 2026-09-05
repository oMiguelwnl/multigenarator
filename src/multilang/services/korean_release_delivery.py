"""Constrained offline Korean release delivery actions."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from pydantic import BaseModel, ConfigDict, Field

from multilang.services.korean_release_safety import KoreanReleaseAuthorization


GitRunner = Callable[[tuple[str, ...], Path], None]


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class KoreanReleaseDeliveryActionResult(_FrozenModel):
    kind: str = "korean-release-delivery-action"
    action_sha256: str = Field(min_length=64, max_length=64)
    authorization_sha256: str = Field(min_length=64, max_length=64)
    status: str
    git_action_count: int = Field(ge=0)
    publication_action_count: int = Field(ge=0)
    before_state_sha256: str = Field(min_length=64, max_length=64)
    after_state_sha256: str = Field(min_length=64, max_length=64)
    zero_action_channels: tuple[str, ...]


class KoreanReleaseDeliveryValidation(_FrozenModel):
    kind: str = "korean-release-delivery-validation"
    validation_sha256: str = Field(min_length=64, max_length=64)
    authorization_sha256: str = Field(min_length=64, max_length=64)
    action_sha256: str = Field(min_length=64, max_length=64)
    status: str


def execute_korean_release_delivery(
    *,
    authorization: KoreanReleaseAuthorization,
    release_dir: Path,
    git_worktree: Path,
    git_runner: Callable[[tuple[str, ...], Path], None] | None = None,
) -> KoreanReleaseDeliveryActionResult:
    runner = git_runner or _run_git
    before_state = _state_sha256(
        {
            "authorization_sha256": authorization.authorization_sha256,
            "release_root_sha256": authorization.release_root_sha256,
            "commit_members": authorization.commit_members,
            "publication_members": authorization.publication_members,
            "release_dir_exists": release_dir.is_dir(),
        }
    )
    git_action_count = 0
    publication_action_count = 0
    if authorization.commit_token_present:
        for member in authorization.commit_members:
            runner(("git", "add", "--", member), git_worktree, shell=False)  # type: ignore[misc]
            git_action_count += 1
        runner(("git", "commit", "-m", "Add Korean release bundle"), git_worktree, shell=False)  # type: ignore[misc]
        git_action_count += 1
    if authorization.publication_token_present:
        publication_action_count = len(authorization.publication_members)
    status = "zero_action" if git_action_count == 0 and publication_action_count == 0 else "executed"
    after_state = before_state if status == "zero_action" else _state_sha256({"before": before_state, "git": git_action_count, "publication": publication_action_count})
    payload = {
        "kind": "korean-release-delivery-action",
        "authorization_sha256": authorization.authorization_sha256,
        "status": status,
        "git_action_count": git_action_count,
        "publication_action_count": publication_action_count,
        "before_state_sha256": before_state,
        "after_state_sha256": after_state,
        "zero_action_channels": authorization.zero_action_channels,
    }
    return KoreanReleaseDeliveryActionResult(**payload, action_sha256=_state_sha256(payload))


def validate_korean_release_delivery(
    *,
    authorization: KoreanReleaseAuthorization,
    action_result: KoreanReleaseDeliveryActionResult,
) -> KoreanReleaseDeliveryValidation:
    if action_result.authorization_sha256 != authorization.authorization_sha256:
        raise ValueError("Korean release delivery authorization drift")
    expected_git_actions = len(authorization.commit_members) + 1 if authorization.commit_token_present else 0
    expected_publication_actions = len(authorization.publication_members) if authorization.publication_token_present else 0
    if action_result.git_action_count != expected_git_actions:
        raise ValueError("Korean release delivery git action drift")
    if action_result.publication_action_count != expected_publication_actions:
        raise ValueError("Korean release delivery publication action drift")
    if set(action_result.zero_action_channels) != set(authorization.zero_action_channels):
        raise ValueError("Korean release delivery zero-action channel drift")
    if not authorization.commit_token_present and not authorization.publication_token_present:
        if action_result.before_state_sha256 != action_result.after_state_sha256:
            raise ValueError("Korean release delivery zero-action state drift")
    payload = {
        "kind": "korean-release-delivery-validation",
        "authorization_sha256": authorization.authorization_sha256,
        "action_sha256": action_result.action_sha256,
        "status": "validated",
    }
    return KoreanReleaseDeliveryValidation(**payload, validation_sha256=_state_sha256(payload))


def _run_git(argv: tuple[str, ...], cwd: Path, *, shell: bool = False) -> None:
    if shell:
        raise ValueError("Korean release delivery forbids shell execution")
    subprocess.run(argv, cwd=cwd, shell=False, check=True)


def _state_sha256(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


__all__ = [
    "KoreanReleaseDeliveryActionResult",
    "KoreanReleaseDeliveryValidation",
    "execute_korean_release_delivery",
    "validate_korean_release_delivery",
]
