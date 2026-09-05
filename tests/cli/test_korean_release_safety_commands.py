"""CLI tests for Korean release safety tooling."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from typer.testing import CliRunner

from multilang.cli import create_app
from multilang.services.korean_release_safety import KOREAN_RELEASE_INPUT_MEMBER_PATHS


runner = CliRunner()


def _hash(seed: str) -> str:
    return sha256(seed.encode("utf-8")).hexdigest()


def _write_input_members(root: Path) -> None:
    for member in KOREAN_RELEASE_INPUT_MEMBER_PATHS:
        path = root / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"safe fixture {member}\n", encoding="utf-8")


def _write_controls(path: Path) -> Path:
    controls = {
        member: {
            "visibility": "local_only",
            "sensitivity": "controlled",
            "retention": "retain_until_replaced",
            "license_id": "nikl-local-use",
            "attribution_id": "nikl-attribution",
            "local_use_allowed": True,
            "publication_allowed": False,
            "privacy_scan_passed": True,
            "security_scan_passed": True,
            "retention_control_passed": True,
        }
        for member in KOREAN_RELEASE_INPUT_MEMBER_PATHS
    }
    path.write_text(json.dumps(controls, sort_keys=True), encoding="utf-8")
    return path


def test_build_safety_cli_writes_reports_with_fixed_roots_privacy_and_release_graph(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    _write_input_members(staging)
    controls = _write_controls(tmp_path / "controls.json")

    result = runner.invoke(
        create_app(),
        [
            "build-korean-release-safety",
            "--staging-root",
            str(staging),
            "--member-controls",
            str(controls),
            "--authority-sha256",
            f"local_use={_hash('local-use')}",
            "--authority-sha256",
            f"content_promotion={_hash('content-promotion')}",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "korean_release_safety_status=validated" in result.output
    assert (staging / "release-safety.json").is_file()
    assert (staging / "production-build-result.json").is_file()


def test_release_promoter_cli_promotes_fixed_tree_pointer_and_exact_retry(tmp_path: Path) -> None:
    authorization = _hash("authorization")
    release_parent = tmp_path / "release"
    staging = release_parent / f"staging-{authorization}"
    _write_input_members(staging)
    controls = _write_controls(tmp_path / "controls.json")
    app = create_app()
    build = runner.invoke(
        app,
        [
            "build-korean-release-safety",
            "--staging-root",
            str(staging),
            "--member-controls",
            str(controls),
            "--authority-sha256",
            f"content_promotion={authorization}",
        ],
    )
    assert build.exit_code == 0, build.output

    result = runner.invoke(
        app,
        [
            "promote-korean-release-bundle",
            "--staging-root",
            str(staging),
            "--release-parent",
            str(release_parent),
            "--current-pointer",
            str(release_parent / "current-release.json"),
            "--authorization-sha256",
            authorization,
            "--safety-report",
            str(staging / "release-safety.json"),
            "--build-result",
            str(staging / "production-build-result.json"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "korean_release_promotion_status=promoted" in result.output
    assert (release_parent / authorization / "release-manifest.json").is_file()


def test_validate_authorization_cli_writes_output_for_pointer_selected_tree(tmp_path: Path) -> None:
    authorization = _hash("authorization-cli")
    release_parent = tmp_path / "release-auth"
    staging = release_parent / f"staging-{authorization}"
    _write_input_members(staging)
    controls = _write_controls(tmp_path / "controls-auth.json")
    app = create_app()
    build = runner.invoke(
        app,
        [
            "build-korean-release-safety",
            "--staging-root",
            str(staging),
            "--member-controls",
            str(controls),
            "--authority-sha256",
            f"content_promotion={authorization}",
        ],
    )
    assert build.exit_code == 0, build.output
    promote = runner.invoke(
        app,
        [
            "promote-korean-release-bundle",
            "--staging-root",
            str(staging),
            "--release-parent",
            str(release_parent),
            "--current-pointer",
            str(release_parent / "current-release.json"),
            "--authorization-sha256",
            authorization,
            "--safety-report",
            str(staging / "release-safety.json"),
            "--build-result",
            str(staging / "production-build-result.json"),
        ],
    )
    assert promote.exit_code == 0, promote.output

    output = tmp_path / "authorization.json"
    result = runner.invoke(
        app,
        [
            "validate-korean-release-authorization",
            "--release-dir",
            str(release_parent / authorization),
            "--current-pointer",
            str(release_parent / "current-release.json"),
            "--authorization-sha256",
            authorization,
            "--safety-report",
            str(release_parent / authorization / "release-safety.json"),
            "--build-result",
            str(release_parent / authorization / "production-build-result.json"),
            "--authorization-output",
            str(output),
            "--commit-member",
            KOREAN_RELEASE_INPUT_MEMBER_PATHS[0],
            "--commit-token-sha256",
            _hash("commit-token"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "korean_release_authorization_status=validated" in result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["commit_token_present"] is True
    assert payload["publication_token_present"] is False
