"""Korean release safety and durable local promotion tests."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from multilang.services.korean_release_safety import (
    KOREAN_RELEASE_INPUT_MEMBER_PATHS,
    build_korean_release_safety,
    promote_korean_release_bundle,
    validate_korean_release_authorization,
)


def _hash(seed: str) -> str:
    return sha256(seed.encode("utf-8")).hexdigest()


def _write_input_members(root: Path) -> None:
    for member in KOREAN_RELEASE_INPUT_MEMBER_PATHS:
        path = root / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"safe fixture {member}\n".encode("utf-8"))


def _controls(*, publish: bool = False) -> dict[str, dict[str, object]]:
    return {
        member: {
            "visibility": "local_only" if not publish else "public",
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


def test_release_safety_allows_private_local_release_but_blocks_publication(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    _write_input_members(staging)

    safety, build_result = build_korean_release_safety(
        staging_root=staging,
        member_controls=_controls(publish=False),
        authority_sha256s={"local_use": _hash("local-use"), "content_promotion": _hash("content-promotion")},
    )

    assert safety.safe_for_local_release is True
    assert safety.safe_to_publish is False
    assert build_result.safety_report_sha256 == sha256((staging / "release-safety.json").read_bytes()).hexdigest()
    payload = json.loads((staging / "release-safety.json").read_text(encoding="utf-8"))
    assert "private/audio" not in json.dumps(payload)

    bad = staging / KOREAN_RELEASE_INPUT_MEMBER_PATHS[0]
    bad.write_text("LEAK-private/audio/path", encoding="utf-8")
    with pytest.raises(ValueError, match="private content"):
        build_korean_release_safety(
            staging_root=staging,
            member_controls=_controls(publish=False),
            authority_sha256s={"local_use": _hash("local-use"), "content_promotion": _hash("content-promotion")},
        )


def test_release_promoter_installs_complete_tree_pointer_and_exact_retry_is_noop(tmp_path: Path) -> None:
    authorization = _hash("authorization")
    release_parent = tmp_path / "release"
    staging = release_parent / f"staging-{authorization}"
    _write_input_members(staging)
    safety, build_result = build_korean_release_safety(
        staging_root=staging,
        member_controls=_controls(publish=False),
        authority_sha256s={"local_use": _hash("local-use"), "content_promotion": authorization},
    )

    pointer = release_parent / "current-release.json"
    first = promote_korean_release_bundle(
        staging_root=staging,
        release_parent=release_parent,
        current_pointer=pointer,
        authorization_sha256=authorization,
        safety_report=safety,
        build_result=build_result,
    )
    assert first.status == "promoted"
    assert (release_parent / authorization / "release-manifest.json").is_file()
    first_pointer_bytes = pointer.read_bytes()

    retry = promote_korean_release_bundle(
        staging_root=staging,
        release_parent=release_parent,
        current_pointer=pointer,
        authorization_sha256=authorization,
        safety_report=safety,
        build_result=build_result,
    )
    assert retry.status == "already_current"
    assert pointer.read_bytes() == first_pointer_bytes


def test_authorization_rejects_unsafe_publication_scope_and_accepts_token_commit_scope(tmp_path: Path) -> None:
    authorization = _hash("authorization-safety")
    release_parent = tmp_path / "release-authz"
    staging = release_parent / f"staging-{authorization}"
    _write_input_members(staging)
    safety, build_result = build_korean_release_safety(
        staging_root=staging,
        member_controls=_controls(publish=False),
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
    release_dir = release_parent / authorization

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

    result = validate_korean_release_authorization(
        release_dir=release_dir,
        current_pointer=pointer,
        authorization_sha256=authorization,
        safety_report=safety,
        build_result=build_result,
        commit_members=[KOREAN_RELEASE_INPUT_MEMBER_PATHS[0]],
        commit_token_sha256=_hash("commit-token"),
    )
    assert result.commit_token_present is True
    assert result.publication_token_present is False
