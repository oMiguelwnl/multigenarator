"""Run one isolated review queue, supervise known limits, and reconcile its work."""

from __future__ import annotations

import hashlib
import re
import time
from datetime import UTC, datetime
from pathlib import Path

from multilang.services.qualification_machine_runner import json_bytes
from multilang.services.vocabulary_queue_shards import _json, _path, merge_shard
from multilang.services.vocabulary_review import _read_bytes
from multilang.services.vocabulary_review_policy_queue import (
    run_policy_queue,
    supervise_policy_queue,
)
from multilang.services.vocabulary_session_queue import _atomic_json, _controller_lock

_BUSY = "another queue controller or inherited worker holds this lock"


def execute_shard(
    *,
    manifest: Path,
    manifest_sha256: str,
    group: str,
    policy: Path,
    policy_sha256: str,
    implementation_sha256: str,
    workers: int = 3,
) -> dict:
    """Use existing account-only review/retry rules; merge only a completed queue.

    A canonical merge lock may be held by the other completing shard. Only that
    exact contention is retried, for up to one hour. Data conflicts stop safely.
    """
    manifest, policy = map(_path, (manifest, policy))
    data = _json(manifest, manifest_sha256)
    if (
        data.get("schema_version") != "vocabulary-queue-shards-1"
        or data.get("output") != str(manifest.parent)
        or not isinstance(group, str)
        or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", group)
        or group not in data["groups"]
        or type(workers) is not int
        or not 1 <= workers <= 3
    ):
        raise ValueError("invalid shard execution binding")
    root = _path(manifest.parent / "groups" / group)
    row = data["groups"][group]
    parent = _path(row["parent_binding"])
    if parent != root / "parent/binding.json" or _path(row["work"]) != root / "work":
        raise ValueError("shard execution paths changed")
    bound_parent = _json(parent, row["parent_binding_sha256"])
    if (
        bound_parent["work"] != str(root / "work")
        or bound_parent["session_ids"] != row["session_ids"]
    ):
        raise ValueError("shard selection changed")
    settings = dict(
        plan=Path(data["plan"]),
        plan_sha256=data["plan_sha256"],
        output=root / "queue",
        parent_queue=parent.parent,
        parent_binding_sha256=row["parent_binding_sha256"],
        policy=policy,
        policy_sha256=policy_sha256,
        implementation_sha256=implementation_sha256,
        workers=workers,
    )
    binding = {
        "schema_version": "vocabulary-shard-execution-1",
        "manifest": str(manifest),
        "manifest_sha256": manifest_sha256,
        "group": group,
        "settings": {k: str(v) if isinstance(v, Path) else v for k, v in settings.items()},
        "runner_sha256": hashlib.sha256(_read_bytes(Path(__file__))).hexdigest(),
    }
    with _controller_lock(root / "execution-controller"):
        binding_file = root / "execution-binding.json"
        try:
            with binding_file.open("xb") as stream:
                stream.write(json_bytes(binding))
        except FileExistsError:
            if _json(binding_file) != binding:
                raise ValueError("immutable execution settings changed") from None

        def save(status, **extra):
            result = {
                "schema_version": "vocabulary-shard-execution-status-1",
                "status": status,
                "group": group,
                "manifest_sha256": manifest_sha256,
                "updated_at": datetime.now(UTC).isoformat(),
                "generation_status": "deferred_by_user",
                "provider_calls_executed": 0,
                "production_eligible": False,
                **extra,
            }
            _atomic_json(root / "execution.json", result)
            return result

        try:
            save("reviewing")
            result = run_policy_queue(**settings)
            if result["status"] == "stopped_with_error":
                save("supervising")
                result = supervise_policy_queue(**settings)
            if result["status"] != "first_pass_complete":
                return save("needs_attention", queue_status=result["status"])
            save("consolidating")
            deadline = time.monotonic() + 3600
            while True:
                if (root / "queue/STOP").exists():
                    return save("needs_attention", queue_status="stopped_by_request")
                try:
                    merged = merge_shard(
                        manifest=manifest,
                        manifest_sha256=manifest_sha256,
                        group=group,
                        report=root / "merge",
                    )
                    break
                except ValueError as error:
                    if str(error) != _BUSY or time.monotonic() >= deadline:
                        raise
                    save("waiting_for_consolidation_lock")
                    time.sleep(5)
            sessions = merged["sessions"]
            if set(sessions) != set(row["session_ids"]) or any(
                v["remaining_units"] != 0 for v in sessions.values()
            ):
                raise ValueError("consolidation did not confirm the entire shard completion")
            return save(
                "consolidated", sessions=len(sessions), report=str(root / "merge/merge.json")
            )
        except (ValueError, OSError, KeyError, TypeError) as error:
            save("needs_attention", reason=str(error)[:1000])
            raise
