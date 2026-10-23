import importlib.util
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[2] / "scripts/run_korean_registry_queue.py"
    assert path.exists(), "isolated Korean queue CLI missing"
    spec = importlib.util.spec_from_file_location("ko_queue_cli", path)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    return cli


def args(tmp_path):
    result = []
    for name in ["plan", "work", "output", "repository"]:
        result += ["--" + name, str(tmp_path / name)]
    return result + ["--plan-sha256", "a" * 64]


def test_cli_no_model_override_and_concise_output(tmp_path, monkeypatch, capsys):
    cli = module()
    monkeypatch.setattr(
        cli,
        "run_registry_queue",
        lambda **kw: {
            "status": "first_pass_complete",
            "requested_model": "gpt-6-astra",
            "source_text": "untrusted secret",
        },
    )
    assert cli.main(args(tmp_path)) == 0
    assert "source_text" not in capsys.readouterr().out
    with pytest.raises(SystemExit):
        cli.main(args(tmp_path) + ["--workers", "2"])


def test_cli_hides_exception_content(tmp_path, monkeypatch, capsys):
    cli = module()

    def fail(**_kw):
        raise ValueError("private source")

    monkeypatch.setattr(cli, "run_registry_queue", fail)
    with pytest.raises(SystemExit) as result:
        cli.main(args(tmp_path))
    assert result.value.code == 2 and "private source" not in capsys.readouterr().err
