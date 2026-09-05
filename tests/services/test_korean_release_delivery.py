"""Korean release delivery action and actual-state validation tests."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from multilang.services.korean_release_delivery import (
    execute_korean_release_delivery,
    validate_korean_release_delivery,
)
from multilang.services.korean_release_safety import (
    KOREAN_RELEASE_INPUT_MEMBER_PATHS,
    build_korean_release_safety,
    promote_korean_release_bundle,
    validate_korean_release_authorization,
)


def _hash(seed: str) -> str:
    return sha256(seed.encode("utf-8")).hexdigest()


def _controls(*, publish: bool = False) -> dict[str, dict[str, object]]:
    return {
        member: {
            "visibility": "public" if publish else "local_only",
            "sensitivity": "controlled",
            "retention": "retain_until_replaced",
            "license_id": "nikl-local-use",
            "attribution_id": "nikl-attribution",
            "local_use_allowed": True,
            "publication_allowed": publish,
            "privacy_scan_passed": True,
            "security_scan_passed": True,
            "retention_control_passed": True,
        }
        for member in KOREAN_RELEASE_INPUT_MEMBER_PATHS
    }


def _prepared_release(tmp_path: Path, *, publish: bool = False):
    authorization = _hash("authorization")
    release_parent = tmp_path / "release"
    staging = release_parent / f"staging-{authorization}"
    for member in KOREAN_RELEASE_INPUT_MEMBER_PATHS:
        path = staging / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"safe fixture {member}\n", encoding="utf-8")
    safety, build_result = build_korean_release_safety(
        staging_root=staging,
        member_controls=_controls(publish=publish),
        authority_sha256s={"content_promotion": authorization},
    )
    pointer = release_parent / "current-release.json"
    promote_korean_release_bundle(
        staging_root=staging,
        release_parent=release_parent,
        current_pointer=pointer,
        authorization_sha256=authorization,
        safety_report=safety,
        build_result=build_result,
    )
    return authorization, release_parent / authorization, pointer, safety, build_result


def test_release_authorization_rejects_publication_scope_for_local_only_member(tmp_path: Path) -> None:
    authorization, release_dir, pointer, safety, build_result = _prepared_release(tmp_path, publish=False)

    with pytest.raises(ValueError, match="publication"):
        validate_korean_release_authorization(
            release_dir=release_dir,
            current_pointer=pointer,
            authorization_sha256=authorization,
            safety_report=safety,
            build_result=build_result,
            publication_members=[KOREAN_RELEASE_INPUT_MEMBER_PATHS[0]],
            publication_token_sha256=_hash("publication-token"),
        )

    authorization_result = validate_korean_release_authorization(
        release_dir=release_dir,
        current_pointer=pointer,
        authorization_sha256=authorization,
        safety_report=safety,
        build_result=build_result,
        commit_members=[KOREAN_RELEASE_INPUT_MEMBER_PATHS[0]],
        commit_token_sha256=_hash("commit-token"),
    )
    assert authorization_result.commit_token_present is True
    assert authorization_result.publication_token_present is False


def test_delivery_action_uses_shell_false_argv_and_zero_action_validation(tmp_path: Path) -> None:
    authorization, release_dir, pointer, safety, build_result = _prepared_release(tmp_path, publish=False)
    auth = validate_korean_release_authorization(
        release_dir=release_dir,
        current_pointer=pointer,
        authorization_sha256=authorization,
        safety_report=safety,
        build_result=build_result,
        commit_members=[KOREAN_RELEASE_INPUT_MEMBER_PATHS[0]],
        commit_token_sha256=_hash("commit-token"),
    )
    calls: list[tuple[tuple[str, ...], Path, bool]] = []

    def runner(argv: tuple[str, ...], cwd: Path, *, shell: bool) -> None:
        calls.append((argv, cwd, shell))

    result = execute_korean_release_delivery(
        authorization=auth,
        release_dir=release_dir,
        git_worktree=tmp_path / "repo",
        git_runner=runner,
    )

    assert result.git_action_count == 2
    assert all(call[2] is False for call in calls)
    assert calls[0][0] == ("git", "add", "--", KOREAN_RELEASE_INPUT_MEMBER_PATHS[0])
    validated = validate_korean_release_delivery(authorization=auth, action_result=result)
    assert validated.status == "validated"

    zero_auth = validate_korean_release_authorization(
        release_dir=release_dir,
        current_pointer=pointer,
        authorization_sha256=authorization,
        safety_report=safety,
        build_result=build_result,
    )
    zero_result = execute_korean_release_delivery(
        authorization=zero_auth,
        release_dir=release_dir,
        git_worktree=tmp_path / "repo",
        git_runner=runner,
    )
    assert zero_result.git_action_count == 0
    forged = zero_result.model_copy(update={"after_state_sha256": _hash("changed")})
    with pytest.raises(ValueError, match="zero-action"):
        validate_korean_release_delivery(authorization=zero_auth, action_result=forged)
