"""Observe one bound queue and retry only explicit Codex capacity/usage failures.

The queue remains responsible for source-bound imports and reviewer processes.
This supervisor never changes model, account, selection, or generation authority.
"""

from __future__ import annotations

import hashlib
import re
import threading
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from multilang.services.qualification_machine_runner import _locked, json_bytes, read_json
from multilang.services.qualification_review import _json
from multilang.services.vocabulary_review import _plain_path, _read_bytes
from multilang.services.vocabulary_session_partitions import _load_plan
from multilang.services.vocabulary_session_queue import (
    _atomic_json,
    _controller_lock,
    _termination_signals,
    run_queue,
)

_TRANSIENT = re.compile(
    r"^(Selected model is at capacity|You['’]ve hit your usage limit)(?:[.!:\s]|$)"
)


def is_transient_turn_failure(event: object) -> bool:
    """Pure classification; nested messages or unrelated event types never qualify."""
    if not isinstance(event, dict) or event.get("type") != "turn.failed":
        return False
    error = event.get("error")
    message = error.get("message") if isinstance(error, dict) else None
    return isinstance(message, str) and bool(_TRANSIENT.match(message))


def classify_failures(state: dict, output: Path) -> dict:
    """Inspect only top-level failed turns in each exact failed worker attempt."""
    evidence = []
    try:
        output = _plain_path(output)
        failures = state["failures"]
        if not isinstance(failures, list) or not failures:
            raise ValueError("no explicit worker failures")
        for failure in failures:
            sid = failure["session_id"]
            if not isinstance(sid, str) or not re.fullmatch(r"[a-z]{2}-[0-9]{4}", sid):
                raise ValueError("failure has no validated session")
            row = state["sessions"][sid]
            if not isinstance(row, dict):
                raise ValueError("invalid failed-session structure")
            code = row.get("exit_code")
            if (
                type(code) is not int
                or code == 0
                or failure["reason"]
                != (
                    f"Codex exited with code {code}; inspect the local attempt log; no API fallback"
                )
            ):
                raise ValueError("failure is not a completed nonzero Codex exit")
            folder = _plain_path(Path(row["attempt_directory"]))
            if folder.parent != output / "attempts" / sid or not re.fullmatch(
                r"[0-9a-f]{32}", folder.name
            ):
                raise ValueError("attempt path is outside its assigned queue session")
            path = folder / "events.jsonl"
            content = _read_bytes(path, limit=64 * 1024**2)
            messages = []
            for line in content.splitlines():
                if not line.strip():
                    continue
                event = _json(line)
                if not isinstance(event, dict):
                    raise ValueError("invalid event structure")
                if event.get("type") == "turn.failed":
                    if not is_transient_turn_failure(event):
                        raise ValueError("unrecognized failed-turn error")
                    messages.append(event["error"]["message"])
            if not messages:
                raise ValueError("attempt has no explicit transient failed turn")
            evidence.append(
                {
                    "session_id": sid,
                    "events": str(path),
                    "events_sha256": hashlib.sha256(content).hexdigest(),
                    "failure_count": len(messages),
                }
            )
    except (ValueError, OSError, KeyError, TypeError) as error:
        return {"retryable": False, "reason": str(error), "evidence": evidence}
    return {
        "retryable": True,
        "reason": "explicit_codex_capacity_or_usage_limit",
        "evidence": evidence,
    }


@contextmanager
def _available_controller(work):
    manager = _controller_lock(work / "queue-controller")
    try:
        manager.__enter__()
    except ValueError as error:
        if str(error) != "another queue controller or inherited worker holds this lock":
            raise
        yield False
    else:
        try:
            yield True
        finally:
            manager.__exit__(None, None, None)


def _validate_status(state, binding, workers):
    if not isinstance(state, dict):
        raise ValueError("invalid queue status structure")
    if any(state.get(key) != value for key, value in binding.items()):
        raise ValueError("queue status binding changed")
    if (
        state.get("schema_version") != "vocabulary-session-queue-1"
        or state.get("generation_status") != "deferred_by_user"
        or state.get("production_eligible") is not False
        or state.get("project_provider_api_calls") != 0
        or state.get("workers") != workers
    ):
        raise ValueError("queue status authority or worker configuration changed")
    sessions = state["sessions"]
    if (
        not isinstance(sessions, dict)
        or set(sessions) != set(binding["session_ids"])
        or state["selected_sessions"] != len(sessions)
    ):
        raise ValueError("queue session inventory changed")
    if any(
        not isinstance(row, dict)
        or type(row.get("remaining_units")) is not int
        or row["remaining_units"] < 0
        for row in sessions.values()
    ):
        raise ValueError("invalid remaining-unit count")
    completed = sum(row["remaining_units"] == 0 for row in sessions.values())
    if state["completed_sessions"] != completed:
        raise ValueError("inconsistent queue completion count")
    if state["status"] == "first_pass_complete" and (
        completed != len(sessions) or state["failures"]
    ):
        raise ValueError("inconsistent first-pass completion")


def supervise_queue(
    *,
    plan: Path,
    plan_sha256: str,
    output: Path,
    supervision: Path,
    cooldown_seconds: float = 1800,
    poll_seconds: float = 5,
    runner=None,
    clock=None,
    sleeper=None,
    cancel=None,
) -> dict:
    """Observe an existing queue; stop for unknown errors instead of guessing.

    Clock/sleeper/runner injection is for deterministic offline tests. The default
    runner uses the existing queue's fixed Astra/high ChatGPT account execution.
    """
    if not 1 <= cooldown_seconds <= 86400 or not 0 < poll_seconds <= 30:
        raise ValueError("cooldown must be 1..86400s and polling 0..30s")
    output, supervision, plan = map(_plain_path, (output, supervision, plan))
    if supervision == output or output.is_relative_to(supervision):
        raise ValueError("supervision must not contain the queue output")
    runner = run_queue if runner is None else runner
    clock = time.monotonic if clock is None else clock
    cancel = threading.Event() if cancel is None else cancel
    sleeper = cancel.wait if sleeper is None else sleeper
    with _locked(output / "supervisor-controller"), _termination_signals(cancel):
        supervision.mkdir(parents=True, exist_ok=True)
        report = {
            "schema_version": "vocabulary-queue-supervisor-1",
            "status": "starting",
            "queue_output": str(output),
            "restarts": 0,
            "generation_status": "deferred_by_user",
            "project_provider_api_calls": 0,
            "production_eligible": False,
        }

        def save(status, reason=None):
            report.update(status=status, reason=reason, updated_at=datetime.now(UTC).isoformat())
            _atomic_json(supervision / "status.json", report)
            return dict(report)

        def stopped():
            return cancel.is_set() or (output / "STOP").exists() or (supervision / "STOP").exists()

        try:
            binding = read_json(output / "binding.json")
            expected_keys = {
                "plan_sha256",
                "work",
                "repository",
                "session_ids",
                "requested_model",
                "reasoning_effort",
            }
            if set(binding) not in (expected_keys, expected_keys | {"exclude_languages"}):
                raise ValueError("unexpected queue binding structure")
            if (
                binding["plan_sha256"] != plan_sha256
                or binding["requested_model"] != "gpt-6-astra"
                or binding["reasoning_effort"] != "high"
            ):
                raise ValueError("unsupported or changed queue binding")
            _, data, refs = _load_plan(plan, plan_sha256)
            ids = binding["session_ids"]
            excluded = binding.get("exclude_languages", [])
            languages = {row["language"] for row in data["languages"]}
            if (
                not ids
                or len(set(ids)) != len(ids)
                or any(sid not in refs for sid in ids)
                or excluded != sorted(set(excluded))
                or any(code not in languages for code in excluded)
                or any(refs[sid]["language"] in excluded for sid in ids)
            ):
                raise ValueError("invalid bound assignments or exclusions")
            work, repository = map(
                _plain_path, (Path(binding["work"]), Path(binding["repository"]))
            )
            workers = read_json(output / "status.json")["workers"]
            if type(workers) is not int or not 1 <= workers <= 3:
                raise ValueError("invalid bound worker count")
            frozen = {
                "queue_binding": binding,
                "queue_output": str(output),
                "plan": str(plan),
                "workers": workers,
                "cooldown_seconds": cooldown_seconds,
                "poll_seconds": poll_seconds,
            }
            frozen_path = supervision / "binding.json"
            if frozen_path.exists():
                if read_json(frozen_path) != frozen:
                    raise ValueError("immutable supervisor binding changed")
            else:
                with frozen_path.open("xb") as stream:
                    stream.write(json_bytes(frozen))
            deadline, candidate = None, None
            while True:
                if stopped():
                    return save("stopped_by_request")
                if read_json(output / "binding.json") != binding:
                    raise ValueError("queue binding changed")
                ready = False
                with _available_controller(work) as available:
                    state = read_json(output / "status.json")
                    _validate_status(state, binding, workers)
                    report["completed_sessions"] = state["completed_sessions"]
                    report["selected_sessions"] = state["selected_sessions"]
                    if not available:
                        deadline, candidate = None, None
                        save("observing_running_queue")
                    elif state["status"] == "first_pass_complete":
                        return save("first_pass_complete")
                    elif state["status"] in {"stop_by_request", "stopped_by_request"}:
                        return save("stopped_by_request")
                    elif state["status"] != "stopped_with_error":
                        raise ValueError(
                            "queue lock is free with stale running or unknown status; investigation required"
                        )
                    else:
                        classification = classify_failures(state, output)
                        if not classification["retryable"]:
                            raise ValueError(classification["reason"])
                        snapshot = hashlib.sha256(
                            json_bytes({"state": state, "classification": classification})
                        ).hexdigest()
                        if candidate != snapshot:
                            candidate, deadline = snapshot, clock() + cooldown_seconds
                        report["cooldown_remaining_seconds"] = max(0, deadline - clock())
                        save("cooldown", classification["reason"])
                        if clock() >= deadline and not stopped():
                            archive = supervision / "history" / uuid4().hex
                            archive.mkdir(parents=True)
                            for name, value in (
                                ("status.json", state),
                                ("binding.json", binding),
                                ("retry.json", classification),
                            ):
                                with (archive / name).open("xb") as stream:
                                    stream.write(json_bytes(value))
                            ready = True
                if ready:
                    if stopped():
                        return save("stopped_by_request")
                    if read_json(output / "binding.json") != binding:
                        raise ValueError("queue binding changed before resume")
                    save("resuming_same_queue")
                    kwargs = {
                        "plan": plan,
                        "plan_sha256": plan_sha256,
                        "work": work,
                        "output": output,
                        "repository": repository,
                        "workers": workers,
                        "session_ids": list(ids),
                    }
                    if "exclude_languages" in binding:
                        kwargs["exclude_languages"] = list(excluded)
                    runner(**kwargs)
                    report["restarts"] += 1
                    deadline, candidate = None, None
                else:
                    sleeper(
                        min(poll_seconds, max(0.01, deadline - clock()))
                        if deadline is not None
                        else poll_seconds
                    )
        except (ValueError, OSError, KeyError, TypeError) as error:
            return save("blocked", str(error))
