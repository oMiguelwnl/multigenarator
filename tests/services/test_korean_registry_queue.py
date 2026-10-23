"""Serial account queue: synthetic native imports only, never launch Codex."""

import importlib
import importlib.util
import json
import os
from pathlib import Path

import pytest


def queue():
    name = "multilang.services.korean_registry_queue"
    assert importlib.util.find_spec(name), "isolated registry queue is missing"
    return importlib.import_module(name)


@pytest.fixture
def campaign(tmp_path):
    path = Path(__file__).with_name("test_korean_registry_review.py")
    spec = importlib.util.spec_from_file_location("registry_queue_fixture", path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    args = fixture.fixture_inputs(tmp_path)
    native = fixture.service()
    result = native.prepare_registry_review(**args, max_units=2)
    common = {
        "plan": args["output"],
        "plan_sha256": result["plan_sha256"],
        "work": tmp_path / "work",
    }
    return (
        fixture,
        native,
        common,
        common | {"output": tmp_path / "queue", "repository": Path.cwd()},
    )


def finish_task(campaign, task):
    fixture, native, common, _ = campaign
    assert task["directory"] == str(common["work"])
    while True:
        request = native.next_registry_request(**common, task_id=task["task_id"], batch_size=8)
        if request["status"] == "first_pass_complete":
            return 0
        native.import_registry_response(
            **common,
            task_id=task["task_id"],
            request=Path(request["request"]),
            request_sha256=request["request_sha256"],
            response=fixture.response_for(request),
            context_id="synthetic-queue-test",
        )


def test_serial_queue_preserves_preexisting_imports_and_resumes_complete(campaign):
    fixture, native, common, args = campaign
    req = native.next_registry_request(**common, task_id="ko-pending-0001", batch_size=1)
    imported = native.import_registry_response(
        **common,
        task_id="ko-pending-0001",
        request=Path(req["request"]),
        request_sha256=req["request_sha256"],
        response=fixture.response_for(req),
        context_id="synthetic-pilot",
    )
    original = (Path(imported["review"]) / "review.json").read_bytes()
    calls = []

    def worker(task):
        calls.append(task["task_id"])
        assert task["batch_size"] == 8
        assert os.fstat(task["controller_lock_fd"])
        return finish_task(campaign, task)

    result = queue().run_registry_queue(**args, worker=worker)
    assert result["status"] == "first_pass_complete"
    assert result["snapshot"]["reviewed_units"] == 3
    assert calls == ["ko-pending-0001", "ko-pending-0002"]
    assert (Path(imported["review"]) / "review.json").read_bytes() == original
    assert queue().run_registry_queue(**args, worker=worker)["status"] == "first_pass_complete"
    assert len(calls) == 2


def test_success_prose_without_import_is_not_progress(campaign):
    result = queue().run_registry_queue(**campaign[3], worker=lambda _task: 0)
    assert result["status"] == "stopped_with_error"
    assert result["snapshot"]["reviewed_units"] == 0
    assert result["reason"] == "worker_no_validated_progress"


@pytest.mark.parametrize(
    "kind", ["other_task_request", "old_request_bytes", "same_task_supersession"]
)
def test_any_preexisting_artifact_or_other_task_mutation_blocks(campaign, kind):
    fixture, native, common, args = campaign
    req = native.next_registry_request(**common, task_id="ko-pending-0001", batch_size=1)
    first = native.import_registry_response(
        **common,
        task_id="ko-pending-0001",
        request=Path(req["request"]),
        request_sha256=req["request_sha256"],
        response=fixture.response_for(req),
        context_id="synthetic-pilot",
    )
    calls = []

    def worker(task):
        calls.append(task["task_id"])
        if kind == "other_task_request":
            native.next_registry_request(**common, task_id="ko-pending-0002")
        elif kind == "old_request_bytes":
            with (Path(req["request"]) / "messages.json").open("ab") as stream:
                stream.write(b" ")
        else:
            response = fixture.response_for(req)
            response["decisions"][0].update(
                decision="uncertain", reason="unresolved_meaning", resolved_upos=None
            )
            native.import_registry_response(
                **common,
                task_id="ko-pending-0001",
                request=Path(req["request"]),
                request_sha256=req["request_sha256"],
                response=response,
                context_id="synthetic-revision",
                supersedes=Path(first["review"]),
            )
        return 0

    result = queue().run_registry_queue(**args, worker=worker)
    assert result["status"] == "stopped_with_error" and len(calls) == 1
    assert result["reason"] in {
        "artifact_integrity_failed",
        "cross_task_mutation",
        "preexisting_review_superseded",
    }


@pytest.mark.parametrize(
    "kind", ["unknown", "nested", "mixed", "capacity", "usage_ascii", "usage_curly"]
)
def test_only_top_level_known_turn_failures_retry(campaign, kind):
    module = queue()
    calls = []
    delays = []

    def worker(task):
        calls.append(task["task_id"])
        if len(calls) > 1:
            return finish_task(campaign, task)
        message = {
            "capacity": "Selected model is at capacity. Try later.",
            "usage_ascii": "You've hit your usage limit.",
            "usage_curly": "You’ve hit your usage limit.",
        }.get(kind, "unknown error")
        event = {"type": "turn.failed", "error": {"message": message}}
        if kind == "nested":
            event = {"type": "item.completed", "item": {"text": "Selected model is at capacity."}}
        events = [event]
        if kind == "mixed":
            events = [
                {"type": "turn.failed", "error": {"message": "Selected model is at capacity."}},
                event,
            ]
        Path(task["events_file"]).write_text("".join(json.dumps(e) + "\n" for e in events))
        Path(task["stderr_file"]).write_text("")
        return 1

    ticks = [0.0]

    def sleep(seconds):
        delays.append(seconds)
        ticks[0] += seconds

    result = module.run_registry_queue(
        **campaign[3], worker=worker, _clock=lambda: ticks[0], _sleep=sleep
    )
    if kind.startswith("usage") or kind == "capacity":
        assert result["status"] == "first_pass_complete" and sum(delays) == 1800
        assert len(calls) == 3 and max(delays) <= 1
    else:
        assert result["status"] == "stopped_with_error" and len(calls) == 1 and not delays


def test_retry_cap_and_stop_during_cooldown(campaign):
    module = queue()
    calls = []
    ticks = [0.0]

    def worker(task):
        calls.append(task)
        Path(task["events_file"]).write_text(
            json.dumps(
                {"type": "turn.failed", "error": {"message": "Selected model is at capacity."}}
            )
            + "\n"
        )
        return 1

    def sleep(seconds):
        ticks[0] += seconds

    result = module.run_registry_queue(
        **campaign[3], worker=worker, _clock=lambda: ticks[0], _sleep=sleep
    )
    assert len(calls) == 4 and result["reason"] == "transient_retry_budget_exhausted"

    def stopping_sleep(seconds):
        ticks[0] += seconds
        (campaign[3]["output"] / "STOP").write_text("stop")

    result = module.run_registry_queue(
        **campaign[3], worker=worker, _clock=lambda: ticks[0], _sleep=stopping_sleep
    )
    assert result["status"] == "stopped_by_request" and len(calls) == 5


def test_stop_watchdog_cancels_running_worker(campaign):
    def worker(task):
        (campaign[3]["output"] / "STOP").write_text("stop")
        assert task["cancel_event"].wait(3)
        raise InterruptedError("stop")

    result = queue().run_registry_queue(**campaign[3], worker=worker)
    assert result["status"] == "stopped_by_request"
    assert result["snapshot"]["reviewed_units"] == 0


def test_busy_snapshot_is_bounded_and_never_zero(campaign, monkeypatch):
    import fcntl

    _, native, common, args = campaign
    native.next_registry_request(**common, task_id="ko-pending-0001")
    module = queue()
    monkeypatch.setattr(module, "SNAPSHOT_WAIT_SECONDS", 2)
    fd = os.open(common["work"] / ".operation.lock", os.O_RDONLY)
    ticks = [0.0]
    calls = []

    def sleep(seconds):
        ticks[0] += seconds

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = module.run_registry_queue(
            **args, worker=lambda task: calls.append(task), _clock=lambda: ticks[0], _sleep=sleep
        )
    finally:
        os.close(fd)
    assert result["status"] == "stopped_with_error" and result["counts_observed"] is False
    assert result["snapshot"] is None and not calls and ticks[0] <= 3


def test_fifo_lease_refused_without_blocking(campaign):
    import signal

    module = queue()
    work = campaign[2]["work"]
    path = work.parent / ("." + work.name + "-korean-registry-controller.lock")
    os.mkfifo(path)

    def timeout(*_args):
        raise AssertionError("lease blocked")

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(3)
    try:
        with pytest.raises(ValueError, match="regular"):
            module.run_registry_queue(**campaign[3], worker=lambda task: 0)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def test_auth_failure_never_launches_and_secrets_are_removed(campaign, monkeypatch):
    module = queue()
    calls = []

    def auth():
        raise ValueError("API login")

    monkeypatch.setattr(module, "_account_check", auth)
    monkeypatch.setattr(module, "_launch", lambda task: calls.append(task))
    result = module.run_registry_queue(**campaign[3])
    assert result["reason"] == "chatgpt_authentication_failed" and not calls
    from multilang.services.vocabulary_session_queue import codex_command, worker_environment

    env = worker_environment(
        {
            "OPENAI_API_KEY": "secret",
            "OPENROUTER_API_KEY": "secret",
            "AZURE_KEY": "secret",
            "HOME": "/safe",
            "PATH": "/bin",
        }
    )
    assert "secret" not in str(env)
    cmd = codex_command({"directory": str(campaign[2]["work"]), "final_message": "/tmp/final"})
    for flag in [
        "--ignore-user-config",
        "--ephemeral",
        "gpt-6-astra",
        'forced_login_method="chatgpt"',
        'model_reasoning_effort="high"',
        "sandbox_workspace_write.network_access=false",
    ]:
        assert flag in cmd


def test_stale_running_and_binding_drift_block(campaign):
    module = queue()
    args = campaign[3]
    module.run_registry_queue(**args, worker=lambda task: 0)
    path = args["output"] / "status.json"
    state = json.loads(path.read_text())
    state["status"] = "running"
    path.write_text(json.dumps(state))
    result = module.run_registry_queue(**args, worker=lambda task: pytest.fail("must not launch"))
    assert result["reason"] == "stale_running_requires_inspection"
    binding = args["output"] / "binding.json"
    data = json.loads(binding.read_text())
    data["requested_model"] = "other"
    binding.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="binding"):
        module.run_registry_queue(**args, worker=lambda task: 0)


def test_preexisting_response_with_lock_suffix_is_still_immutable(campaign):
    _, native, common, args = campaign
    native.next_registry_request(**common, task_id="ko-pending-0001")
    folder = common["work"] / "worker-responses" / "ko-pending-0001"
    folder.mkdir(parents=True)
    path = folder / "original.lock"
    path.write_text("original response data")

    def worker(task):
        path.write_text("changed response data")
        return finish_task(campaign, task)

    result = queue().run_registry_queue(**args, worker=worker)
    assert (
        result["status"] == "stopped_with_error" and result["reason"] == "artifact_integrity_failed"
    )
    assert result["snapshot"]["reviewed_units"] == 2


def test_auth_timeout_is_recorded_without_launch(campaign, monkeypatch):
    import subprocess

    module = queue()

    def timeout():
        raise subprocess.TimeoutExpired(["codex", "login", "status"], 30)

    monkeypatch.setattr(module, "_account_check", timeout)
    monkeypatch.setattr(module, "_launch", lambda task: pytest.fail("must not launch"))
    result = module.run_registry_queue(**campaign[3])
    assert result["reason"] == "chatgpt_authentication_failed"


def test_signal_exit_with_old_capacity_event_never_retries(campaign):
    calls = []

    def worker(task):
        calls.append(task)
        Path(task["events_file"]).write_text(
            json.dumps(
                {"type": "turn.failed", "error": {"message": "Selected model is at capacity."}}
            )
            + "\n"
        )
        return -9

    ticks = [0.0]

    def sleep(seconds):
        ticks[0] += seconds

    result = queue().run_registry_queue(
        **campaign[3], worker=worker, _sleep=sleep, _clock=lambda: ticks[0]
    )
    assert result["reason"] == "unrecognized_worker_failure" and len(calls) == 1


def test_executor_dependency_drift_during_worker_blocks_next_launch(campaign, monkeypatch):
    module = queue()
    original = module._fingerprints
    calls = []

    def worker(task):
        calls.append(task)
        result = finish_task(campaign, task)
        monkeypatch.setattr(module, "_fingerprints", lambda repository: {"changed": "0" * 64})
        return result

    result = module.run_registry_queue(**campaign[3], worker=worker)
    monkeypatch.setattr(module, "_fingerprints", original)
    assert (
        result["status"] == "stopped_with_error"
        and result["reason"] == "executor_fingerprint_drift"
        and len(calls) == 1
    )


@pytest.mark.parametrize("mode", ["timeout", "logs"])
def test_reused_launcher_enforces_real_bounds_with_mock_process(tmp_path, monkeypatch, mode):
    import threading

    from multilang.services import vocabulary_session_queue as launcher

    calls = []
    cleaned = []

    class Process:
        pid = 99999999

        def poll(self):
            return None

    def popen(command, **kwargs):
        calls.append((command, kwargs))
        if mode == "logs":
            kwargs["stdout"].seek(64 * 1024**2)
            kwargs["stdout"].write(b"x")
            kwargs["stdout"].flush()
        return Process()

    monkeypatch.setattr(launcher.subprocess, "Popen", popen)
    monkeypatch.setattr(launcher, "_terminate_group", lambda process: cleaned.append(process.pid))
    moments = iter([0, 3601] if mode == "timeout" else [0, 0])
    monkeypatch.setattr(launcher.time, "monotonic", lambda: next(moments))
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("synthetic")
    task = {
        "directory": str(tmp_path),
        "prompt_file": str(prompt),
        "events_file": str(tmp_path / "events.jsonl"),
        "stderr_file": str(tmp_path / "stderr.log"),
        "final_message": str(tmp_path / "final.txt"),
        "cancel_event": threading.Event(),
        "controller_lock_fd": 9,
    }
    with pytest.raises(ValueError, match="one-hour|log size"):
        launcher._launch(task)
    assert len(calls) == 1 and cleaned == [99999999]
    assert calls[0][1]["start_new_session"] is True and calls[0][1]["pass_fds"] == (9,)


def test_terminal_log_burst_over_budget_blocks(campaign):
    module = queue()

    def worker(task):
        finish_task(campaign, task)
        with Path(task["events_file"]).open("wb") as stream:
            stream.truncate(module.MAX_LOG_BYTES + 1)
        return 0

    result = module.run_registry_queue(**campaign[3], worker=worker)
    assert result["status"] == "stopped_with_error"
    assert result["counts_observed"] is False


def test_other_controller_lease_blocks_even_with_different_output(campaign):
    import fcntl

    module = queue()
    work = campaign[2]["work"]
    path = work.parent / ("." + work.name + "-korean-registry-controller.lock")
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match="another controller"):
            module.run_registry_queue(
                **campaign[3], worker=lambda task: pytest.fail("must not launch")
            )
    finally:
        os.close(fd)


def test_previous_run_receipt_is_immutable(campaign):
    module = queue()
    args = campaign[3]
    first = module.run_registry_queue(**args, worker=lambda task: 0)
    prior = args["output"] / "runs" / first["run_id"] / "result.json"

    def worker(task):
        prior.write_text("{}")
        return finish_task(campaign, task)

    result = module.run_registry_queue(**args, worker=worker)
    assert (
        result["status"] == "stopped_with_error" and result["reason"] == "artifact_integrity_failed"
    )


def test_stale_running_block_persists_across_repeated_invocations(campaign):
    module = queue()
    args = campaign[3]
    module.run_registry_queue(**args, worker=lambda task: 0)
    path = args["output"] / "status.json"
    state = json.loads(path.read_text())
    state["status"] = "running"
    path.write_text(json.dumps(state))
    calls = []

    def worker(task):
        calls.append(task)
        return 0

    for _ in range(2):
        result = module.run_registry_queue(**args, worker=worker)
        assert result["status"] == "stopped_with_error"
        assert result["reason"] == "stale_running_requires_inspection"
        assert result["counts_observed"] is False
    assert not calls
