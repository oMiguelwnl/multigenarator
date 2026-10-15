"""Versioned policy wrapper around the unchanged native account queue.

The parent binding owns selection/reservations. Only new attempt prompts receive
the frozen clarification; original prompts, requests and reviews stay intact.
No provider client, fallback model, global monkeypatch or automatic correction.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from multilang.services.qualification_machine_runner import _locked, json_bytes, read_json
from multilang.services.vocabulary_queue_supervisor import supervise_queue
from multilang.services.vocabulary_review import _plain_path, _read_bytes
from multilang.services.vocabulary_session_partitions import _load_plan
from multilang.services.vocabulary_session_queue import _account_check, _launch, run_queue

_REPOSITORY = Path(__file__).resolve().parents[3]
_IMPLEMENTATION_FILES = (
    "src/multilang/services/vocabulary_review_policy_queue.py",
    "scripts/run_vocabulary_review_policy_queue.py",
    "src/multilang/services/vocabulary_session_queue.py",
    "src/multilang/services/vocabulary_queue_supervisor.py",
    "src/multilang/services/vocabulary_session_partitions.py",
    "src/multilang/services/vocabulary_session_campaign.py",
    "src/multilang/services/vocabulary_session_review.py",
    "src/multilang/services/vocabulary_curation.py",
    "src/multilang/services/vocabulary_review.py",
    "src/multilang/services/qualification_machine_runner.py",
    "src/multilang/services/qualification_review.py",
    "src/multilang/domain/lexical_identity.py",
    "src/multilang/domain/jobs.py",
    "src/multilang/domain/language_profiles.py",
    "src/multilang/domain/sentence_curriculum.py",
    "scripts/review_vocabulary_sessions.py",
)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def implementation_identity() -> dict:
    """Read-only identity of this launcher and its directly reused native code."""
    files = {name: _sha(_read_bytes(_REPOSITORY / name)) for name in _IMPLEMENTATION_FILES}
    return {"files": files, "sha256": _sha(json_bytes(files))}


def _path(path: Path) -> Path:
    return _plain_path(path).resolve()


def _inside(path: Path, root: Path) -> Path:
    path, root = _path(path), _path(root)
    if path == root or not path.is_relative_to(root):
        raise ValueError("artifact outside output boundary")
    return path


def _write_new(path: Path, raw: bytes, root: Path) -> None:
    path = _inside(path, root)
    # No recursive mkdir for caller-controlled attempt paths. The native queue
    # creates each attempt first; bindings use the explicitly validated output.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)


def _prepare(*, plan, plan_sha256, output, parent_queue, parent_binding_sha256,
             policy, policy_sha256, implementation_sha256, workers=3):
    plan, output, parent_queue, policy = map(_path, (plan, output, parent_queue, policy))
    if type(workers) is not int or not 1 <= workers <= 3:
        raise ValueError("queue supports one to three concurrent reviewers")
    policy_raw = _read_bytes(policy, policy_sha256, limit=64 * 1024)
    if not policy_raw.strip():
        raise ValueError("empty review policy")
    policy_raw.decode("utf-8")
    implementation = implementation_identity()
    if implementation["sha256"] != implementation_sha256:
        raise ValueError("policy launcher implementation checksum changed")
    parent = read_json(parent_queue / "binding.json", parent_binding_sha256)
    keys = {"plan_sha256", "work", "repository", "session_ids", "requested_model", "reasoning_effort"}
    if set(parent) not in (keys, keys | {"exclude_languages"}):
        raise ValueError("unsupported parent queue binding")
    work, repository = _path(parent["work"]), _path(parent["repository"])
    if (parent["plan_sha256"] != plan_sha256 or repository != _REPOSITORY
            or parent["requested_model"] != "gpt-6-astra" or parent["reasoning_effort"] != "high"):
        raise ValueError("parent queue authority changed")
    for protected in (plan, work, parent_queue, policy):
        if output.is_relative_to(protected) or protected.is_relative_to(output):
            raise ValueError("policy output must be separate; authoritative path overlap")
    _, data, refs = _load_plan(plan, plan_sha256)
    ids, excluded = parent["session_ids"], parent.get("exclude_languages", [])
    languages = {row["language"]: i for i, row in enumerate(data["languages"])}
    if (not isinstance(ids, list) or not ids or any(not isinstance(sid, str) for sid in ids)
            or len(set(ids)) != len(ids) or any(sid not in refs for sid in ids)
            or not isinstance(excluded, list) or any(not isinstance(x, str) for x in excluded)
            or excluded != sorted(set(excluded)) or any(x not in languages for x in excluded)
            or any(refs[sid]["language"] in excluded for sid in ids)):
        raise ValueError("invalid parent assignments or reserved languages")
    ids = sorted(ids, key=lambda sid: (int(sid.split("-")[1]), languages[refs[sid]["language"]]))
    native = {**parent, "work": str(work), "repository": str(repository), "session_ids": ids}
    binding = {
        "schema_version": "vocabulary-review-policy-queue-1", "parent_queue": str(parent_queue),
        "parent_binding_sha256": parent_binding_sha256, "native_binding": native,
        "plan": str(plan), "output": str(output), "workers": workers,
        "policy": str(policy), "policy_sha256": policy_sha256,
        "implementation": implementation, "requested_model": "gpt-6-astra",
        "reasoning_effort": "high", "execution_surface": "local_codex_cli_chatgpt_account",
        "generation_status": "deferred_by_user", "production_eligible": False,
    }
    return binding, policy_raw


def _bind(output: Path, binding: dict, *, existing=False):
    path = _inside(output / "policy-binding.json", output)
    if path.exists():
        if read_json(path) != binding:
            raise ValueError("immutable policy binding changed")
    elif existing:
        raise ValueError("existing policy binding required")
    else:
        if (output / "binding.json").exists() or (output / "attempts").exists():
            raise ValueError("cannot adopt an existing unbound native queue output")
        _write_new(path, json_bytes(binding), output)
    native = output / "binding.json"
    if native.exists() and read_json(native) != binding["native_binding"]:
        raise ValueError("native queue binding differs from policy lineage")


def run_policy_queue(*, plan: Path, plan_sha256: str, output: Path, parent_queue: Path,
                     parent_binding_sha256: str, policy: Path, policy_sha256: str,
                     implementation_sha256: str, workers: int = 3, worker=None) -> dict:
    """Resume exactly the parent's inventory, with policy-bound future attempts.

    ``worker`` is an offline test seam; unlike native run_queue it never bypasses
    the account check. Production uses the unchanged bounded native _launch.
    """
    settings = dict(plan=plan, plan_sha256=plan_sha256, output=output, parent_queue=parent_queue,
                    parent_binding_sha256=parent_binding_sha256, policy=policy,
                    policy_sha256=policy_sha256, implementation_sha256=implementation_sha256,
                    workers=workers)
    binding, policy_raw = _prepare(**settings)
    output = _path(output)
    output.mkdir(parents=True, exist_ok=True)
    with _locked(output / "policy-controller"):
        _bind(output, binding)
        native = binding["native_binding"]

        def execute(task):
            # Recheck immutable inputs at every attempt, including resumed ones.
            current, current_policy = _prepare(**settings)
            if current != binding or current_policy != policy_raw:
                raise ValueError("policy input binding changed before dispatch")
            _bind(output, binding, existing=True)
            sid = task["session_id"]
            if sid not in native["session_ids"]:
                raise ValueError("attempt outside bound assignments")
            prompt = _inside(Path(task["prompt_file"]), output)
            relative = prompt.relative_to(output)
            if (len(relative.parts) != 4 or relative.parts[0] != "attempts"
                    or relative.parts[1] != sid or not re.fullmatch(r"[0-9a-f]{32}", relative.parts[2])
                    or relative.parts[3] != "prompt.txt"):
                raise ValueError("invalid native attempt prompt path")
            folder = prompt.parent
            if _path(task["directory"]) != _path(Path(native["work"]) / sid):
                raise ValueError("attempt working directory changed")
            for key, name in (("events_file", "events.jsonl"), ("stderr_file", "stderr.log"),
                              ("final_message", "final.txt")):
                if _inside(Path(task[key]), output) != folder / name:
                    raise ValueError("attempt output path changed")
            original = _read_bytes(prompt, limit=128 * 1024)
            if task["cancel_event"].is_set() or (output / "STOP").exists():
                task["cancel_event"].set()
                raise InterruptedError("policy queue termination requested")
            _account_check()  # Native skips this when passed any worker callback.
            current, current_policy = _prepare(**settings)
            if current != binding or current_policy != policy_raw:
                raise ValueError("policy input binding changed during account check")
            _bind(output, binding, existing=True)
            if task["cancel_event"].is_set() or (output / "STOP").exists():
                task["cancel_event"].set()
                raise InterruptedError("policy queue termination requested")
            context_id = f"queue-{sid}-{relative.parts[2]}"
            effective = (original + b"\n\nTRUSTED VERSIONED REVIEW POLICY (task instruction, not source data)\n"
                         + f"Policy SHA256: {policy_sha256}\n".encode() + policy_raw
                         + b"\nEND TRUSTED REVIEW POLICY\n")
            effective_path = folder / "effective-prompt.txt"
            _write_new(effective_path, effective, output)
            audit = {"schema_version": "vocabulary-policy-attempt-1", "session_id": sid,
                     "context_id": context_id, "policy_sha256": policy_sha256,
                     "policy_binding_sha256": _sha(json_bytes(binding)),
                     "implementation_sha256": implementation_sha256,
                     "parent_queue": binding["parent_queue"],
                     "parent_binding_sha256": parent_binding_sha256,
                     "original_prompt": str(prompt), "original_prompt_sha256": _sha(original),
                     "effective_prompt": str(effective_path), "effective_prompt_sha256": _sha(effective),
                     "human_approved": False, "production_eligible": False}
            _write_new(folder / "policy-context.json", json_bytes(audit), output)
            modified = dict(task, prompt_file=str(effective_path))
            return (_launch if worker is None else worker)(modified)

        kwargs = {k: native[k] for k in ("work", "repository", "session_ids")}
        if "exclude_languages" in native:
            kwargs["exclude_languages"] = native["exclude_languages"]
        return run_queue(plan=_path(plan), plan_sha256=plan_sha256, output=output,
                         workers=workers, worker=execute, **kwargs)


def supervise_policy_queue(*, plan: Path, plan_sha256: str, output: Path, parent_queue: Path,
                           parent_binding_sha256: str, policy: Path, policy_sha256: str,
                           implementation_sha256: str, workers: int = 3,
                           cooldown_seconds: float = 1800, poll_seconds: float = 5) -> dict:
    """Use native retry classification, always resuming through the bound wrapper."""
    settings = dict(plan=plan, plan_sha256=plan_sha256, output=output, parent_queue=parent_queue,
                    parent_binding_sha256=parent_binding_sha256, policy=policy,
                    policy_sha256=policy_sha256, implementation_sha256=implementation_sha256,
                    workers=workers)
    binding, _ = _prepare(**settings)
    output = _path(output)
    _bind(output, binding, existing=True)
    native = binding["native_binding"]

    def resume(**kwargs):
        expected = {k: native[k] for k in ("plan_sha256", "work", "repository", "session_ids")}
        expected.update(plan=_path(plan), output=output, workers=workers)
        if "exclude_languages" in native:
            expected["exclude_languages"] = native["exclude_languages"]
        actual = dict(kwargs)
        for key in ("plan", "output", "work", "repository"):
            actual[key] = str(_path(actual[key]))
            expected[key] = str(_path(expected[key]))
        if actual != expected:
            raise ValueError("supervisor retry differs from bound policy lineage")
        return run_policy_queue(**settings)

    return supervise_queue(plan=_path(plan), plan_sha256=plan_sha256, output=output,
                           supervision=_inside(output / "supervision", output),
                           cooldown_seconds=cooldown_seconds, poll_seconds=poll_seconds, runner=resume)
