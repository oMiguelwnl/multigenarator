"""CLI tests for constrained Korean release delivery commands."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from typer.testing import CliRunner

import multilang.cli as cli_module
from multilang.cli import create_app
from multilang.services.korean_release_delivery import KoreanReleaseDeliveryActionResult, KoreanReleaseDeliveryValidation
from multilang.services.korean_release_safety import KoreanReleaseAuthorization


runner = CliRunner()


def _hash(seed: str) -> str:
    return sha256(seed.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def _authorization() -> KoreanReleaseAuthorization:
    return KoreanReleaseAuthorization(
        authorization_sha256=_hash("authorization"),
        release_root_sha256=_hash("release-root"),
        pointer_sha256=_hash("pointer"),
        commit_members=("generation-report.json",),
        publication_members=(),
        commit_token_present=True,
        publication_token_present=False,
        zero_action_channels=("publication",),
        authorization_sha256s={"content_promotion": _hash("authorization")},
    )


def _action() -> KoreanReleaseDeliveryActionResult:
    return KoreanReleaseDeliveryActionResult(
        action_sha256=_hash("action"),
        authorization_sha256=_hash("authorization"),
        status="executed",
        git_action_count=2,
        publication_action_count=0,
        before_state_sha256=_hash("before"),
        after_state_sha256=_hash("after"),
        zero_action_channels=("publication",),
    )


def test_execute_korean_release_delivery_cli_writes_action_result(tmp_path: Path, monkeypatch) -> None:
    auth_file = _write_json(tmp_path / "auth.json", _authorization().model_dump(mode="json"))
    action_file = tmp_path / "action.json"
    monkeypatch.setattr(cli_module, "execute_korean_release_delivery", lambda **_: _action(), raising=False)

    result = runner.invoke(
        create_app(),
        [
            "execute-korean-release-delivery",
            "--authorization",
            str(auth_file),
            "--release-dir",
            str(tmp_path),
            "--git-worktree",
            str(tmp_path / "repo"),
            "--action-result",
            str(action_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "korean_release_delivery_status=executed" in result.output
    assert json.loads(action_file.read_text(encoding="utf-8"))["git_action_count"] == 2


def test_validate_korean_release_delivery_cli_writes_actual_state_result(tmp_path: Path, monkeypatch) -> None:
    auth_file = _write_json(tmp_path / "auth.json", _authorization().model_dump(mode="json"))
    action_file = _write_json(tmp_path / "action.json", _action().model_dump(mode="json"))
    validation_file = tmp_path / "validation.json"
    monkeypatch.setattr(
        cli_module,
        "validate_korean_release_delivery",
        lambda **_: KoreanReleaseDeliveryValidation(
            validation_sha256=_hash("validation"),
            authorization_sha256=_hash("authorization"),
            action_sha256=_hash("action"),
            status="validated",
        ),
        raising=False,
    )

    result = runner.invoke(
        create_app(),
        [
            "validate-korean-release-delivery",
            "--authorization",
            str(auth_file),
            "--action-result",
            str(action_file),
            "--validation-result",
            str(validation_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "korean_release_delivery_validation_status=validated" in result.output
    assert json.loads(validation_file.read_text(encoding="utf-8"))["status"] == "validated"
