"""CLI exposes only offline preparation/review and concise fixed summaries."""

import importlib.util
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[2] / "scripts/review_korean_registry.py"
    assert path.is_file(), "Korean registry CLI is not implemented"
    spec = importlib.util.spec_from_file_location("korean_registry_cli_test", path)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    return cli


@pytest.mark.parametrize(
    "operation,function",
    [
        ("prepare", "prepare_registry_review"),
        ("next", "next_registry_request"),
        ("import", "import_registry_response"),
        ("status", "registry_review_status"),
    ],
)
def test_commands_require_hashes_and_print_only_summary(
    monkeypatch, capsys, tmp_path, operation, function
):
    cli = module()
    calls = []

    def run(**kwargs):
        calls.append(kwargs)
        return {
            "status": "pending_review",
            "pending_units": 3,
            "untrusted_context": "do not print source",
        }

    monkeypatch.setattr(cli, function, run)
    args = [operation]
    if operation == "prepare":
        for name in ["registry", "bundle", "supplement"]:
            args += ["--" + name, str(tmp_path / name), "--" + name + "-manifest-sha256", "a" * 64]
        args += ["--output", str(tmp_path / "plan")]
    else:
        args += [
            "--plan",
            str(tmp_path / "plan"),
            "--plan-sha256",
            "b" * 64,
            "--work",
            str(tmp_path / "work"),
        ]
        if operation != "status":
            args += ["--task-id", "ko-pending-0001"]
        if operation == "import":
            response = tmp_path / "response.json"
            response.write_text('{"decisions": []}')
            args += [
                "--request",
                str(tmp_path / "request"),
                "--request-sha256",
                "c" * 64,
                "--response",
                str(response),
                "--context-id",
                "test",
            ]
    assert cli.main(args) == 0
    assert calls and "untrusted_context" not in capsys.readouterr().out


def test_cli_errors_do_not_echo_source_strings(monkeypatch, capsys, tmp_path):
    cli = module()

    def fail(**kwargs):
        raise ValueError("secret source string")

    monkeypatch.setattr(cli, "registry_review_status", fail)
    with pytest.raises(SystemExit) as exc:
        cli.main(
            [
                "status",
                "--plan",
                str(tmp_path),
                "--plan-sha256",
                "a" * 64,
                "--work",
                str(tmp_path / "work"),
            ]
        )
    assert exc.value.code == 2
    assert "secret source string" not in capsys.readouterr().err
