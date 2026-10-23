"""CLI remains offline and reports only status/bindings, never source strings."""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/prepare_vocabulary_context_supplement.py"


def cli():
    assert SCRIPT.is_file(), "context recovery CLI not implemented"
    spec = importlib.util.spec_from_file_location("context_cli_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("operation", ["create", "validate"])
def test_cli_passes_external_bindings_and_prints_only_summary(monkeypatch, capsys, operation):
    module = cli()
    calls = []

    def call(**kwargs):
        calls.append(kwargs)
        return {
            "status": "context_available_for_review_only",
            "sense_count": 4,
            "manifest_sha256": "a" * 64,
        }

    monkeypatch.setattr(module, operation + "_context_supplement", call)
    args = [
        operation,
        "--root",
        "repository",
        "--specification",
        "input.json",
        "--specification-sha256",
        "b" * 64,
    ]
    if operation == "create":
        args += ["--output", "new-supplement"]
    else:
        args += ["--supplement", "saved-supplement", "--manifest-sha256", "c" * 64]
    assert module.main(args) == 0
    assert calls[0]["root"] == Path("repository")
    assert calls[0]["specification_sha256"] == "b" * 64
    assert json.loads(capsys.readouterr().out)["status"] == "context_available_for_review_only"


def test_cli_validation_error_does_not_echo_source_data(monkeypatch, capsys):
    module = cli()

    def fail(**_):
        raise ValueError("private raw source text")

    monkeypatch.setattr(module, "create_context_supplement", fail)
    with pytest.raises(SystemExit) as exc:
        module.main(
            [
                "create",
                "--root",
                ".",
                "--specification",
                "input.json",
                "--specification-sha256",
                "b" * 64,
                "--output",
                "out",
            ]
        )
    assert exc.value.code == 2
    assert "private raw source text" not in capsys.readouterr().err
