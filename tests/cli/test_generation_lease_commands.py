"""Explicit recovery never retries providers or silently clears unknown work."""

import json
from hashlib import sha256

from sqlalchemy import create_engine
from typer.testing import CliRunner

import multilang.cli as cli_module
from multilang.db.base import Base
from multilang.services.generation_leases import GenerationLeaseManager
from multilang.settings import Settings


def test_cli_inspects_and_recovers_exact_interrupted_item_without_provider_work(monkeypatch, tmp_path):
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'leases.db'}")
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(engine)
    manager = GenerationLeaseManager(engine)
    lease = manager.claim("job-a")
    lease.begin_item("private learner form")
    manager.release(lease)
    digest = sha256(b"private learner form").hexdigest()
    app = cli_module.create_app()
    monkeypatch.setattr(cli_module, "Settings", lambda: settings)

    def forbidden(*args, **kwargs):
        raise AssertionError("lease inspection/recovery must not construct runtime providers")

    monkeypatch.setattr(cli_module, "build_runtime_service", forbidden)
    runner = CliRunner()
    status = runner.invoke(app, ["generation-lease-status", "--job-id", "job-a"])
    assert status.exit_code == 0, status.output
    assert json.loads(status.output)["inflight_item_sha256"] == digest
    assert "private learner" not in status.output
    recovered = runner.invoke(app, [
        "recover-generation-lease", "--job-id", "job-a",
        "--expected-item-sha256", digest, "--acknowledge-unknown-outcome",
    ])
    assert recovered.exit_code == 0, recovered.output
    assert json.loads(recovered.output)["paid_replay_authorized"] is False
    resumed = manager.claim("job-a")
    manager.release(resumed)
    engine.dispose()


def test_cli_requires_recovery_acknowledgement_before_database_access(monkeypatch):
    app = cli_module.create_app()

    def forbidden():
        raise AssertionError("no database settings before acknowledgement")

    monkeypatch.setattr(cli_module, "Settings", forbidden)
    result = CliRunner().invoke(app, [
        "recover-generation-lease", "--job-id", "job-a", "--expected-item-sha256", "a" * 64,
    ])
    assert result.exit_code == 2
    assert "--acknowledge-unknown-outcome" in result.output
