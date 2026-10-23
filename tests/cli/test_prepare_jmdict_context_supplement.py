"""Offline CLI exposes only pinned recovery and validation."""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/prepare_jmdict_context_supplement.py"


def cli():
    assert SCRIPT.is_file(), "JMdict recovery CLI not implemented"
    spec = importlib.util.spec_from_file_location("jmdict_cli_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("operation", ["create", "validate"])
def test_cli_passes_pins_and_only_prints_safe_summary(monkeypatch, capsys, operation):
    module = cli()
    calls = []

    def call(**kwargs):
        calls.append(kwargs)
        return {
            "status": "context_available_for_review_only",
            "sense_count": 4,
            "manifest_sha256": "a" * 64,
            "raw_source": "DO NOT PRINT",
        }

    monkeypatch.setattr(module, operation + "_jmdict_context_supplement", call)
    args = [
        operation,
        "--root",
        "repo",
        "--specification",
        "input.json",
        "--specification-sha256",
        "b" * 64,
    ]
    args += (
        ["--output", "out"]
        if operation == "create"
        else ["--supplement", "out", "--manifest-sha256", "c" * 64]
    )
    assert module.main(args) == 0
    assert calls[0]["root"] == Path("repo")
    assert "raw_source" not in json.loads(capsys.readouterr().out)


def test_cli_errors_hide_untrusted_strings(monkeypatch, capsys):
    module = cli()

    def fail(**kw):
        raise ValueError("private source \x1b[2J")

    monkeypatch.setattr(module, "create_jmdict_context_supplement", fail)
    with pytest.raises(SystemExit) as e:
        module.main(
            [
                "create",
                "--root",
                ".",
                "--specification",
                "input.json",
                "--specification-sha256",
                "a" * 64,
                "--output",
                "out",
            ]
        )
    assert e.value.code == 2
    assert "private source" not in capsys.readouterr().err
