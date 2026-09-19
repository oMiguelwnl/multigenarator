"""CLI coverage for Phase 33 local authority and review contracts."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import click
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typer.main import get_command
from typer.testing import CliRunner

from multilang.cli import create_app

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolated_learning_runtime(monkeypatch):
    from multilang.cli_commands import phase33
    from multilang.db.base import Base
    from multilang.domain.jobs import GenerationRequest, SupportedLanguage
    from multilang.repositories.job_repository import JobRepository
    from multilang.services.korean_learning_runtime import KoreanLearningRuntime
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        job = JobRepository(session).create_job(request=GenerationRequest(language=SupportedLanguage.KO, source_type="korean-grammar"),
            run_key="cli-test", source_fingerprint="fixture", total_items=0)
        job.id = "job-33"
        session.commit()
        runtime = KoreanLearningRuntime(session)
        monkeypatch.setattr(phase33, "build_korean_learning_runtime", lambda: runtime)
        yield runtime


def _options(command_path: tuple[str, ...]) -> tuple[str, ...]:
    command: click.Command = get_command(create_app())
    for part in command_path:
        assert isinstance(command, click.Group)
        command = command.commands[part]
    return tuple(option for parameter in command.params for option in parameter.opts)


def test_exact_process_contract_source_enum_mode_enum_no_server_no_fallback_and_signature() -> None:
    assert {"--job-id", "--source", "--mode", "--max-items"} <= set(_options(("phase33", "process")))
    assert "--server" not in set(_options(("phase33", "process")))
    assert "--fallback" not in set(_options(("phase33", "process")))

    result = runner.invoke(
        create_app(),
        ["phase33", "process", "--job-id", "job-33", "--source", "grammar", "--mode", "start", "--max-items", "2"],
    )

    assert result.exit_code != 0
    assert result.output.strip() == "korean_error=empty_source"

    invalid = runner.invoke(
        create_app(),
        ["phase33", "process", "--job-id", "job-33", "--source", "all", "--mode", "start"],
    )
    assert invalid.exit_code != 0


def test_status_seven_denominator_ids_counts_order_and_safe_source_counts(tmp_path: Path) -> None:
    output = tmp_path / "status.json"
    result = runner.invoke(
        create_app(),
        [
            "phase33",
            "status",
            "--job-id",
            "job-33",
            "--format",
            "json",
            "--require-exact-authority",
            "--no-private-values",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "incomplete"
    assert list(payload["denominators"]) == [
        "attempted",
        "processed",
        "accepted",
        "review_required",
        "failed",
        "skipped_current",
        "not_attempted",
    ]
    assert payload["safe_sources"] == {
        "grammar": {"eligible_count": 0, "ready_count": 0},
        "custom": {"eligible_count": 0, "ready_count": 0},
        "highlight": {"eligible_count": 0, "ready_count": 0},
    }
    assert "private" not in json.dumps(payload).lower()


def test_authority_preflight_cli_exact_allowlist_and_validate_authority_output(tmp_path: Path) -> None:
    output = tmp_path / "preflight.json"
    authority = tmp_path / "authority.json"
    authority.write_text(
        json.dumps(
            {
                "kind": "phase33-local-migration",
                "job_id": "job-33",
                "policy_sha256": "a" * 64,
                "migration_revision": "20260828_19",
                "private_capability": "phase33-private-token-v1",
                "max_private_tokens": 24,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        create_app(),
        [
            "phase33",
            "authority-preflight",
            "--job-id",
            "job-33",
            "--policy-sha256",
            "a" * 64,
            "--curriculum-sha256",
            "b" * 64,
            "--profile-sha256",
            "c" * 64,
            "--source-sha256",
            "d" * 64,
            "--target-sha256",
            "e" * 64,
            "--output-pair",
            "prepared=/tmp/prepared.json",
            "--audio-root",
            f"word={tmp_path / 'word'}",
            "--audio-root",
            f"sentence={tmp_path / 'sentence'}",
            "--audio-root",
            f"staging={tmp_path / 'staging'}",
            "--audio-root",
            f"journal={tmp_path / 'journal'}",
            "--custom-safe-id",
            "custom-1",
            "--highlight-safe-id",
            "highlight-1",
            "--migration-revision",
            "20260828_19",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "ready"

    validate = runner.invoke(
        create_app(),
        [
            "phase33",
            "validate-authority",
            "--authority-file",
            str(authority),
            "--expected-kind",
            "phase33-local-migration",
        ],
    )
    assert validate.exit_code == 0, validate.output
    assert f"authority_sha256={sha256(authority.read_bytes()).hexdigest()}" in validate.output


def test_review_list_audit_commit_before_output_and_changed_hash_conflict_no_output() -> None:
    app = create_app()
    first = runner.invoke(
        app,
        [
            "phase33",
            "review",
            "list",
            "--job-id",
            "job-33",
            "--actor-id",
            "actor",
            "--request-id",
            "req-1",
            "--status",
            "needs_review",
            "--field",
            "sentence",
            "--source",
            "grammar",
            "--format",
            "json",
        ],
    )
    assert first.exit_code == 0, first.output
    payload = json.loads(first.output)
    assert payload["access_event_id"]
    assert payload["rows"] == []

    changed = runner.invoke(
        app,
        [
            "phase33",
            "review",
            "list",
            "--job-id",
            "job-33",
            "--actor-id",
            "actor",
            "--request-id",
            "req-1",
            "--status",
            "approved",
            "--field",
            "sentence",
            "--source",
            "grammar",
            "--format",
            "json",
        ],
    )
    assert changed.exit_code != 0
    assert changed.output.strip() == "korean_error=operation_failed"
