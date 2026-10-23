"""The contextual CLI does no provider or model dispatch."""

import importlib.util
from pathlib import Path

import pytest


def cli():
    path = Path(__file__).parents[2] / "scripts/review_korean_registry_context.py"
    assert path.exists(), "isolated context CLI is not implemented"
    spec = importlib.util.spec_from_file_location("context_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_help_exposes_offline_operations(capsys):
    with pytest.raises(SystemExit) as result:
        cli().main(["--help"])
    assert result.value.code == 0
    output = capsys.readouterr().out
    assert all(name in output for name in ["prepare", "next", "validate", "import", "status"])


def test_status_pinned_hash_required():
    with pytest.raises(SystemExit) as result:
        cli().main(["status", "--plan", "/tmp/none", "--work", "/tmp/none"])
    assert result.value.code == 2


def test_validate_routes_without_response_or_model(monkeypatch, capsys):
    module = cli()
    calls = []
    monkeypatch.setattr(
        module,
        "validate_context_review",
        lambda **kw: calls.append(kw) or {"valid": True, "production_eligible": False},
    )
    module.main(
        ["validate", "--plan", "/tmp/plan", "--plan-sha256", "a" * 64, "--work", "/tmp/work"]
    )
    assert calls[0]["plan_sha256"] == "a" * 64
    assert '"valid": true' in capsys.readouterr().out
