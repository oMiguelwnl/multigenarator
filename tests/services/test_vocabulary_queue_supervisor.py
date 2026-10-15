"""Only explicit top-level account capacity failures permit a bounded retry."""

import json
import threading
from pathlib import Path

import pytest


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def _fixture(tmp_path):
    output = tmp_path / "queue"
    binding = {
        "plan_sha256": "a" * 64,
        "work": str(tmp_path / "work"),
        "repository": str(tmp_path),
        "session_ids": ["de-0001"],
        "requested_model": "gpt-6-astra",
        "reasoning_effort": "high",
        "exclude_languages": ["pt"],
    }
    state = {
        **binding,
        "schema_version": "vocabulary-session-queue-1",
        "status": "stopped_with_error",
        "workers": 3,
        "selected_sessions": 1,
        "completed_sessions": 0,
        "generation_status": "deferred_by_user",
        "production_eligible": False,
        "project_provider_api_calls": 0,
        "sessions": {
            "de-0001": {
                "remaining_units": 5,
                "status": "error",
                "exit_code": 1,
                "attempt_directory": str(output / "attempts/de-0001" / ("b" * 32)),
            }
        },
        "failures": [
            {
                "session_id": "de-0001",
                "reason": "Codex exited with code 1; inspect the local attempt log; no API fallback",
            }
        ],
    }
    _write(output / "binding.json", binding)
    _write(output / "status.json", state)
    events = Path(state["sessions"]["de-0001"]["attempt_directory"]) / "events.jsonl"
    _write(
        events,
        {
            "type": "turn.failed",
            "error": {"message": "Selected model is at capacity. Please try again later."},
        },
    )
    return output, binding, state, events


@pytest.mark.parametrize(
    "message",
    [
        "Selected model is at capacity. Please try again later.",
        "You've hit your usage limit. Try again later.",
        "You’ve hit your usage limit. Try again later.",
    ],
)
def test_only_explicit_transient_turn_failed_is_retryable(tmp_path, message):
    from multilang.services.vocabulary_queue_supervisor import classify_failures

    output, _, state, events = _fixture(tmp_path)
    _write(events, {"type": "turn.failed", "error": {"message": message}})
    assert classify_failures(state, output)["retryable"] is True


@pytest.mark.parametrize(
    "change",
    ["nested", "unknown", "mixed", "timeout", "no_progress", "path", "symlink", "malformed", "row"],
)
def test_unsafe_or_other_failures_never_retry(tmp_path, change):
    from multilang.services.vocabulary_queue_supervisor import classify_failures

    output, _, state, events = _fixture(tmp_path)
    if change == "row":
        state["sessions"]["de-0001"] = []
    elif change == "nested":
        _write(
            events,
            {
                "type": "item.completed",
                "item": {
                    "type": "agent_message",
                    "text": "Selected model is at capacity.",
                    "event": {"type": "turn.failed"},
                },
            },
        )
    elif change == "unknown":
        _write(events, {"type": "turn.failed", "error": {"message": "Authentication failed"}})
    elif change == "mixed":
        with events.open("a") as stream:
            stream.write('\n{"type":"turn.failed","error":{"message":"Unknown failure"}}')
    elif change in {"timeout", "no_progress"}:
        state["failures"][0]["reason"] = (
            "Codex worker exceeded its one-hour attempt limit"
            if change == "timeout"
            else "worker made no progress in validated imports"
        )
    elif change == "path":
        state["sessions"]["de-0001"]["attempt_directory"] = str(tmp_path / "outside")
    elif change == "symlink":
        other = tmp_path / "other"
        events.rename(other)
        events.symlink_to(other)
    else:
        events.write_text('{"type":')
    assert classify_failures(state, output)["retryable"] is False


@pytest.fixture
def setup_supervisor(tmp_path, monkeypatch):
    from multilang.services import vocabulary_queue_supervisor as module

    output, binding, state, events = _fixture(tmp_path)
    monkeypatch.setattr(
        module,
        "_load_plan",
        lambda p, h: (
            p,
            {"languages": [{"language": "de"}, {"language": "pt"}]},
            {"de-0001": {"language": "de"}},
        ),
    )
    args = dict(
        plan=tmp_path / "plan",
        plan_sha256="a" * 64,
        output=output,
        supervision=tmp_path / "supervision",
        cooldown_seconds=3,
        poll_seconds=1,
    )
    now = [0.0]
    sleeps = []

    def sleep(seconds):
        now[0] += seconds
        sleeps.append(seconds)

    return module, args, binding, state, events, now, sleeps, sleep


def test_supervisor_archives_then_resumes_identical_binding(setup_supervisor):
    module, args, binding, state, _, now, sleeps, sleep = setup_supervisor
    calls = []

    def run(**kwargs):
        calls.append(kwargs)
        state.update(status="first_pass_complete", failures=[], completed_sessions=1)
        state["sessions"]["de-0001"]["remaining_units"] = 0
        _write(args["output"] / "status.json", state)
        return state

    result = module.supervise_queue(**args, runner=run, clock=lambda: now[0], sleeper=sleep)
    assert result["status"] == "first_pass_complete"
    assert len(calls) == 1
    assert calls[0]["session_ids"] == binding["session_ids"]
    assert calls[0]["exclude_languages"] == ["pt"]
    assert calls[0]["repository"] == Path(binding["repository"])
    assert sum(sleeps) >= 3 and max(sleeps) <= 1
    archived = list((args["supervision"] / "history").glob("*/status.json"))
    assert len(archived) == 1
    assert json.loads(archived[0].read_text())["status"] == "stopped_with_error"


@pytest.mark.parametrize("status", ["running", "stopped_by_request", "stopped_with_error"])
def test_stale_unknown_and_requested_stop_do_not_resume(setup_supervisor, status):
    module, args, _, state, events, now, _, sleep = setup_supervisor
    state["status"] = status
    if status == "stopped_with_error":
        _write(events, {"type": "turn.failed", "error": {"message": "invalid credentials"}})
    _write(args["output"] / "status.json", state)

    def forbidden(**kwargs):
        pytest.fail("runner must not execute")

    result = module.supervise_queue(**args, runner=forbidden, clock=lambda: now[0], sleeper=sleep)
    assert result["status"] == (
        "stopped_by_request" if status == "stopped_by_request" else "blocked"
    )


def test_busy_controller_is_observed_without_relaunch(setup_supervisor):
    from multilang.services.vocabulary_session_queue import _controller_lock

    module, args, binding, _, _, _, _, _ = setup_supervisor
    cancel = threading.Event()

    def sleep(_):
        cancel.set()

    with _controller_lock(Path(binding["work"]) / "queue-controller"):
        result = module.supervise_queue(
            **args,
            cancel=cancel,
            sleeper=sleep,
            runner=lambda **_: pytest.fail("running queue duplicated"),
        )
    assert result["status"] == "stopped_by_request"


@pytest.mark.parametrize("stop", ["STOP", "binding", "cancel"])
def test_cooldown_checks_stop_and_binding_before_relaunch(setup_supervisor, stop):
    module, args, binding, _, _, now, _, _ = setup_supervisor
    cancel = threading.Event()

    def sleep(seconds):
        now[0] += seconds
        if stop == "STOP":
            (args["output"] / "STOP").touch()
        elif stop == "binding":
            binding["requested_model"] = "different-model"
            _write(args["output"] / "binding.json", binding)
        else:
            cancel.set()

    result = module.supervise_queue(
        **args,
        cancel=cancel,
        clock=lambda: now[0],
        sleeper=sleep,
        runner=lambda **_: pytest.fail("unsafe resume"),
    )
    assert result["status"] == ("blocked" if stop == "binding" else "stopped_by_request")


def test_second_supervisor_is_refused(setup_supervisor):
    from multilang.services.qualification_machine_runner import _locked

    module, args, *_ = setup_supervisor
    with _locked(args["output"] / "supervisor-controller"):
        with pytest.raises(ValueError, match="lock"):
            module.supervise_queue(**args)


def test_multiple_failures_all_must_be_transient(tmp_path):
    from multilang.services.vocabulary_queue_supervisor import classify_failures

    output, _, state, _ = _fixture(tmp_path)
    state["failures"].append({"session_id": None, "reason": "Authentication failed"})
    assert classify_failures(state, output)["retryable"] is False


@pytest.mark.parametrize("corruption", ["sessions", "row", "completion", "schema"])
def test_corrupt_status_blocks_without_launch(setup_supervisor, corruption):
    module, args, _, state, _, _, _, _ = setup_supervisor
    if corruption == "sessions":
        state["sessions"] = []
    elif corruption == "row":
        state["sessions"]["de-0001"] = "invalid"
    elif corruption == "completion":
        state["status"] = "first_pass_complete"
    else:
        state["schema_version"] = "unknown"
    _write(args["output"] / "status.json", state)
    result = module.supervise_queue(
        **args, runner=lambda **_: pytest.fail("corrupt status launched")
    )
    assert result["status"] == "blocked"


def test_cli_defaults_and_blocked_exit(monkeypatch, tmp_path, capsys):
    import importlib.util

    script = Path(__file__).resolve().parents[2] / "scripts/supervise_vocabulary_session_queue.py"
    assert script.is_file()
    spec = importlib.util.spec_from_file_location("supervisor_cli", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls = []

    def supervise(**kwargs):
        calls.append(kwargs)
        return {"status": "blocked", "reason": "unknown failure"}

    monkeypatch.setattr(module, "supervise_queue", supervise)
    assert (
        module.main(
            [
                "--plan",
                str(tmp_path / "plan"),
                "--plan-sha256",
                "a" * 64,
                "--output",
                str(tmp_path / "queue"),
                "--supervision",
                str(tmp_path / "supervision"),
            ]
        )
        == 2
    )
    assert calls[0]["cooldown_seconds"] == 1800
    assert calls[0]["poll_seconds"] == 5
    assert json.loads(capsys.readouterr().out)["status"] == "blocked"


@pytest.mark.parametrize(
    "event,expected",
    [
        ({"type": "turn.failed", "error": {"message": "Selected model is at capacity."}}, True),
        ({"type": "item.completed", "error": {"message": "Selected model is at capacity."}}, False),
        ({"type": "turn.failed", "error": {"message": "Authentication failed"}}, False),
        ({"type": "turn.failed", "error": []}, False),
        (None, False),
    ],
)
def test_pure_event_classifier(event, expected):
    from multilang.services.vocabulary_queue_supervisor import is_transient_turn_failure

    assert is_transient_turn_failure(event) is expected
