"""Isolated queues only consolidate after a verified successful review run."""

import hashlib
import importlib
import importlib.util
import json

import pytest


def api():
    name = "multilang.services.vocabulary_queue_shard_execution"
    assert importlib.util.find_spec(name), "shard execution implementation is missing"
    return importlib.import_module(name)


def test_execution_contract_available():
    assert callable(api().execute_shard)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    mod = api()
    group = tmp_path / "groups/ko"
    (group / "parent").mkdir(parents=True)
    parent = {"work": str(group / "work"), "session_ids": ["ko-0032"]}
    raw = json.dumps(parent).encode()
    (group / "parent/binding.json").write_bytes(raw)
    data = {
        "schema_version": "vocabulary-queue-shards-1",
        "output": str(tmp_path),
        "plan": str(tmp_path / "plan"),
        "plan_sha256": "a" * 64,
        "groups": {
            "ko": {
                "work": str(group / "work"),
                "session_ids": ["ko-0032"],
                "parent_binding": str(group / "parent/binding.json"),
                "parent_binding_sha256": hashlib.sha256(raw).hexdigest(),
            }
        },
    }
    raw = json.dumps(data).encode()
    manifest = tmp_path / "manifest.json"
    manifest.write_bytes(raw)
    kwargs = dict(
        manifest=manifest,
        manifest_sha256=hashlib.sha256(raw).hexdigest(),
        group="ko",
        policy=tmp_path / "policy.md",
        policy_sha256="b" * 64,
        implementation_sha256="c" * 64,
        workers=3,
    )
    calls = []
    monkeypatch.setattr(
        mod,
        "run_policy_queue",
        lambda **k: calls.append(("run", k)) or {"status": "first_pass_complete"},
    )
    monkeypatch.setattr(
        mod,
        "supervise_policy_queue",
        lambda **k: calls.append(("supervise", k)) or {"status": "first_pass_complete"},
    )
    monkeypatch.setattr(
        mod,
        "merge_shard",
        lambda **k: calls.append(("merge", k)) or {"sessions": {"ko-0032": {"remaining_units": 0}}},
    )
    return mod, kwargs, calls, group


def test_complete_queue_is_consolidated_and_settings_bound(setup):
    mod, kwargs, calls, group = setup
    result = mod.execute_shard(**kwargs)
    assert result["status"] == "consolidated"
    assert [c[0] for c in calls] == ["run", "merge"]
    assert calls[0][1]["output"] == group / "queue"
    assert calls[0][1]["parent_queue"] == group / "parent"
    assert calls[1][1]["report"] == group / "merge"
    assert json.loads((group / "execution.json").read_text())["status"] == "consolidated"
    with pytest.raises(ValueError, match="settings"):
        mod.execute_shard(**(kwargs | {"workers": 2}))


def test_failure_only_uses_existing_supervisor_before_merge(setup, monkeypatch):
    mod, kwargs, calls, _ = setup
    monkeypatch.setattr(
        mod,
        "run_policy_queue",
        lambda **k: calls.append(("run", k)) or {"status": "stopped_with_error"},
    )
    mod.execute_shard(**kwargs)
    assert [c[0] for c in calls] == ["run", "supervise", "merge"]


@pytest.mark.parametrize("status", ["stopped_by_request", "stopped_with_error"])
def test_incomplete_or_nonretryable_run_does_not_merge(setup, monkeypatch, status):
    mod, kwargs, calls, _ = setup
    monkeypatch.setattr(mod, "run_policy_queue", lambda **k: {"status": status})
    monkeypatch.setattr(
        mod, "supervise_policy_queue", lambda **k: {"status": "stopped_nonretryable_error"}
    )
    assert mod.execute_shard(**kwargs)["status"] == "needs_attention"
    assert calls == []


def test_only_controller_contention_is_retried(setup, monkeypatch):
    mod, kwargs, calls, _ = setup
    sleeps = []

    def merge(**k):
        calls.append(("merge", k))
        if len([c for c in calls if c[0] == "merge"]) == 1:
            raise ValueError("another queue controller or inherited worker holds this lock")
        return {"sessions": {"ko-0032": {"remaining_units": 0}}}

    monkeypatch.setattr(mod, "merge_shard", merge)
    monkeypatch.setattr(mod.time, "sleep", sleeps.append)
    assert mod.execute_shard(**kwargs)["status"] == "consolidated"
    assert sleeps == [5]


def test_merge_conflict_is_not_retried(setup, monkeypatch):
    mod, kwargs, calls, group = setup

    def merge(**k):
        calls.append(("merge", k))
        raise ValueError("canonical baseline changed or deleted")

    monkeypatch.setattr(mod, "merge_shard", merge)
    with pytest.raises(ValueError, match="canonical baseline"):
        mod.execute_shard(**kwargs)
    assert [c[0] for c in calls] == ["run", "merge"]
    assert json.loads((group / "execution.json").read_text())["status"] == "needs_attention"


def test_tampered_manifest_cannot_launch(setup):
    mod, kwargs, calls, _ = setup
    kwargs["manifest"].write_text("{}")
    with pytest.raises(ValueError):
        mod.execute_shard(**kwargs)
    assert calls == []
