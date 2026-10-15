import importlib.util
from pathlib import Path

import pytest


def cli():
    path = Path(__file__).resolve().parents[2] / "scripts/run_vocabulary_review_policy_queue.py"
    assert path.exists(), "policy CLI missing"
    spec = importlib.util.spec_from_file_location("policy_queue_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def args(tmp_path):
    result = []
    for name in ["plan", "output", "parent-queue", "policy"]:
        result += ["--" + name, str(tmp_path / name)]
    for name in ["plan-sha256", "policy-sha256", "parent-binding-sha256", "implementation-sha256"]:
        result += ["--" + name, "a" * 64]
    return result


@pytest.mark.parametrize("mode", ["run", "supervise"])
def test_cli_uses_bound_mode_and_hides_source_content(tmp_path, monkeypatch, capsys, mode):
    module = cli()
    function = "run_policy_queue" if mode == "run" else "supervise_policy_queue"
    monkeypatch.setattr(module, function, lambda **kw: {"status": "first_pass_complete", "source_text": "private"})
    assert module.main([mode, *args(tmp_path)]) == 0
    assert "private" not in capsys.readouterr().out
    with pytest.raises(SystemExit):
        module.main([mode, *args(tmp_path), "--model", "other"])


def test_cli_requires_all_digests_and_sanitizes_exception(tmp_path, monkeypatch, capsys):
    module = cli()
    with pytest.raises(SystemExit):
        module.main(["run", "--plan", str(tmp_path)])

    def fail(**_):
        raise ValueError("private source text")

    monkeypatch.setattr(module, "run_policy_queue", fail)
    with pytest.raises(SystemExit) as caught:
        module.main(["run", *args(tmp_path)])
    assert caught.value.code == 2 and "private source text" not in capsys.readouterr().err
