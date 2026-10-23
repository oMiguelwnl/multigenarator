import importlib.util
from pathlib import Path

import pytest


def cli():
    path = Path("scripts/review_korean_official_context.py")
    assert path.exists(), "official context CLI is not implemented"
    spec = importlib.util.spec_from_file_location("official_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_help(capsys):
    with pytest.raises(SystemExit) as exc:
        cli().main(["--help"])
    assert exc.value.code == 0
    assert "prepare" in capsys.readouterr().out


def test_missing_hash():
    with pytest.raises(SystemExit) as exc:
        cli().main(["status", "--plan", "/tmp/p", "--work", "/tmp/w"])
    assert exc.value.code == 2
