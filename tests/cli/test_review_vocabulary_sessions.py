"""The partition CLI is offline and preserves explicit bindings and artifacts."""

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/review_vocabulary_sessions.py"
SERVICE = "multilang.services.vocabulary_session_partitions"


def test_cli_entrypoint_exists():
    assert SCRIPT.is_file(), "partition CLI is not implemented"


@pytest.fixture
def cli(monkeypatch):
    calls = []
    results = {
        "partition_vocabulary_sessions": {
            "total_units": 200,
            "session_count": 2,
            "sessions": [{"session_id": "en-001", "units": ["secret-evidence"]}],
        },
        "next_partition_request": {
            "request": "work/en-001/request",
            "request_sha256": "b" * 64,
            "session_id": "en-001",
            "group_count": 8,
        },
        "import_partition_response": {
            "review_status": "single_session_proposal",
            "session_id": "en-001",
            "decisions": [{"decision": "include"}],
            "provider_calls_executed": 0,
        },
        "partition_progress": {
            "total_review_units": 200,
            "reviewed_units": 8,
            "unreviewed_units": 192,
            "sessions": [{"session_id": "en-001", "reviewed_units": 8}],
        },
    }
    service = types.ModuleType(SERVICE)
    for name in results:

        def invoke(_name=name, **kwargs):
            calls.append((_name, kwargs))
            return results[_name]

        setattr(service, name, invoke)
    monkeypatch.setitem(sys.modules, SERVICE, service)
    assert SCRIPT.is_file(), "partition CLI is not implemented"
    spec = importlib.util.spec_from_file_location("partition_cli_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, calls, results


def _bound(command):
    return [command, "--plan", "plan", "--plan-sha256", "a" * 64, "--work", "work"]


def test_split_forwards_bounded_defaults_without_dumping_evidence(cli, capsys):
    module, calls, _ = cli
    assert (
        module.main(
            [
                "split",
                "--packets",
                "packets",
                "--manifest-sha256",
                "a" * 64,
                "--requests",
                "requests",
                "--reviews",
                "reviews",
                "--output",
                "plan",
            ]
        )
        == 0
    )
    assert calls == [
        (
            "partition_vocabulary_sessions",
            {
                "packets": Path("packets"),
                "manifest_sha256": "a" * 64,
                "requests": Path("requests"),
                "reviews": Path("reviews"),
                "output": Path("plan"),
                "max_units": 256,
                "max_evidence_bytes": 256000,
            },
        )
    ]
    result = json.loads(capsys.readouterr().out)
    assert result["total_units"] == 200
    assert result["session_count"] == 2
    assert "sessions" not in result


def test_next_requires_hash_and_preserves_request_reference(cli, capsys):
    module, calls, _ = cli
    with pytest.raises(SystemExit) as error:
        module.main(["next", "--plan", "plan", "--session-id", "en-001", "--work", "work"])
    assert error.value.code == 2
    assert calls == []
    assert module.main(_bound("next") + ["--session-id", "en-001"]) == 0
    assert calls[-1][1]["batch_size"] == 8
    assert calls[-1][1]["plan_sha256"] == "a" * 64
    assert json.loads(capsys.readouterr().out)["request_sha256"] == "b" * 64


def test_import_reads_json_and_forwards_supersession(cli, tmp_path, capsys):
    module, calls, _ = cli
    response = tmp_path / "response.json"
    payload = {"decisions": [{"i": 0, "decision": "include"}]}
    response.write_text(json.dumps(payload))
    assert (
        module.main(
            _bound("import")
            + [
                "--session-id",
                "en-001",
                "--request",
                "request",
                "--request-sha256",
                "b" * 64,
                "--response",
                str(response),
                "--context-id",
                "assistant-session",
                "--supersedes",
                "old",
            ]
        )
        == 0
    )
    assert calls[-1] == (
        "import_partition_response",
        {
            "plan": Path("plan"),
            "plan_sha256": "a" * 64,
            "work": Path("work"),
            "session_id": "en-001",
            "request": Path("request"),
            "request_sha256": "b" * 64,
            "response": payload,
            "context_id": "assistant-session",
            "supersedes": Path("old"),
        },
    )
    result = json.loads(capsys.readouterr().out)
    assert result["reviewed_units"] == 1
    assert "decisions" not in result


@pytest.mark.parametrize("invalid", ["broken", "symlink"])
def test_import_rejects_unsafe_or_invalid_json_before_service(cli, tmp_path, invalid):
    module, calls, _ = cli
    response = tmp_path / "response.json"
    if invalid == "broken":
        response.write_text("{invalid")
    else:
        target = tmp_path / "target.json"
        target.write_text('{"decisions": []}')
        response.symlink_to(target)
    with pytest.raises(SystemExit) as error:
        module.main(
            _bound("import")
            + [
                "--session-id",
                "en-001",
                "--request",
                "request",
                "--request-sha256",
                "b" * 64,
                "--response",
                str(response),
                "--context-id",
                "assistant-session",
            ]
        )
    assert error.value.code == 2
    assert calls == []


def test_status_saves_full_report_exclusively_and_prints_counts(cli, tmp_path, capsys):
    module, _, results = cli
    output = tmp_path / "status.json"
    args = _bound("status") + ["--output", str(output)]
    assert module.main(args) == 0
    assert json.loads(output.read_text()) == results["partition_progress"]
    assert json.loads(capsys.readouterr().out)["unreviewed_units"] == 192
    original = output.read_bytes()
    with pytest.raises(SystemExit) as error:
        module.main(args)
    assert error.value.code == 2
    assert output.read_bytes() == original


def test_status_rejects_symlink_in_output_parent(cli, tmp_path):
    module, _, _ = cli
    real = tmp_path / "real"
    real.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(SystemExit) as error:
        module.main(_bound("status") + ["--output", str(linked / "status.json")])
    assert error.value.code == 2
    assert not (real / "status.json").exists()
