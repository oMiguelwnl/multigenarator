"""Offline, physically isolated queue inventories and append-only reconciliation.

Controllers must be stopped before preparing or merging. This module does not
launch, stop, reserve or supersede any service. The operator must keep the old
queue stopped until all shards have been reconciled. Publication is atomic per
native artifact directory; an interrupted merge is safe to repeat.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from contextlib import ExitStack
from pathlib import Path

from multilang.services.qualification_machine_runner import _locked, json_bytes
from multilang.services.vocabulary_review import _plain_path, _read_bytes
from multilang.services.vocabulary_session_partitions import _assignment, _load_plan, _local_state
from multilang.services.vocabulary_session_queue import _controller_lock

_VERSION = "vocabulary-queue-shards-1"
_SESSION = re.compile(r"[a-z]{2,3}-[0-9]{4}")
_GROUP = re.compile(r"[a-z][a-z0-9_-]{0,63}")
_LIMIT = 128 * 1024**2


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _path(path):
    return _plain_path(Path(path)).resolve()


def _read(path, digest=None):
    path = _plain_path(path)
    if path.stat().st_nlink != 1:
        raise ValueError("hardlinked files are not allowed")
    return _read_bytes(path, digest, limit=_LIMIT)


def _json(path, digest=None):
    return json.loads(_read(path, digest))


def _inventory(root):
    root = _path(root)
    files = {}
    if not root.exists():
        return files
    for directory, names, filenames in os.walk(root, followlinks=False):
        for name in list(names):
            path = Path(directory) / name
            _plain_path(path)
            if name == ".codex-runtime":
                names.remove(name)
        for name in filenames:
            path = Path(directory) / name
            _plain_path(path)
            mode = path.stat()
            if not stat.S_ISREG(mode.st_mode) or mode.st_nlink != 1:
                raise ValueError("special files and hardlinks are not allowed")
            if name.endswith(".lock"):
                continue
            files[path.relative_to(root).as_posix()] = _sha(_read(path))
    return dict(sorted(files.items()))


def _copy_files(source, destination, files):
    for relative, digest in files.items():
        rel = Path(relative)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("invalid inventory path")
        target = _plain_path(destination / rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(_read(source / rel, digest))


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(json_bytes(data))


def _validate(work, plan, data, refs, ids):
    result = {}
    for sid in ids:
        assignment, members, packet = _assignment(plan, data, refs[sid])
        _, requests, reviewed = _local_state(work, assignment, members, packet)
        result[sid] = {
            "reviewed_units": len(reviewed),
            "remaining_units": assignment["pending_units"] - len(reviewed),
            "pending_requests": sum(not item["reviewed"] for item in requests.values()),
        }
    return result


def _groups(groups, parent_ids, refs):
    if not isinstance(groups, dict) or not groups:
        raise ValueError("nonempty groups required")
    seen = set()
    for name, ids in groups.items():
        if not isinstance(name, str) or not _GROUP.fullmatch(name):
            raise ValueError("invalid group name")
        if not isinstance(ids, list) or not ids:
            raise ValueError("nonempty session selection required")
        for sid in ids:
            if (
                not isinstance(sid, str)
                or not _SESSION.fullmatch(sid)
                or sid not in parent_ids
                or sid not in refs
                or sid in seen
            ):
                raise ValueError("unknown, duplicate or overlapping session selection")
            seen.add(sid)
    return seen


def prepare_shards(
    *,
    plan: Path,
    plan_sha256: str,
    parent_binding: Path,
    parent_binding_sha256: str,
    groups: dict,
    output: Path,
) -> dict:
    """Freeze explicitly selected sessions into disjoint physical work roots."""
    plan, parent_binding, output = map(_path, (plan, parent_binding, output))
    parent = _json(parent_binding, parent_binding_sha256)
    keys = {
        "plan_sha256",
        "work",
        "repository",
        "session_ids",
        "requested_model",
        "reasoning_effort",
    }
    if (
        set(parent) not in (keys, keys | {"exclude_languages"})
        or parent["plan_sha256"] != plan_sha256
        or parent["requested_model"] != "gpt-6-astra"
        or parent["reasoning_effort"] != "high"
    ):
        raise ValueError("unsupported parent binding")
    original = _path(parent["work"])
    _, data, refs = _load_plan(plan, plan_sha256)
    ids = _groups(groups, parent["session_ids"], refs)
    if any(refs[sid]["language"] in parent.get("exclude_languages", []) for sid in ids):
        raise ValueError("reserved language selected")
    for protected in (original, plan, parent_binding.parent):
        if output.is_relative_to(protected) or protected.is_relative_to(output):
            raise ValueError("output overlaps authoritative path")
    if output.exists():
        raise ValueError("immutable shard output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    with _controller_lock(original / "queue-controller"), ExitStack() as locks:
        for sid in sorted(ids):
            locks.enter_context(_locked(original / sid / "operation"))
        baseline = _validate(original, plan, data, refs, sorted(ids))
        with tempfile.TemporaryDirectory(prefix=".queue-shards-", dir=output.parent) as temp:
            stage = Path(temp) / "publish"
            stage.mkdir()
            manifest = {
                "schema_version": _VERSION,
                "plan": str(plan),
                "plan_sha256": plan_sha256,
                "original_work": str(original),
                "parent_binding": str(parent_binding),
                "parent_binding_sha256": parent_binding_sha256,
                "implementation_sha256": _sha(_read(Path(__file__))),
                "output": str(output),
                "groups": {},
                "sessions": baseline,
                "generation_status": "deferred_by_user",
                "provider_calls_executed": 0,
            }
            for name, selected in groups.items():
                group = stage / "groups" / name
                final = output / "groups" / name
                files = {}
                for sid in selected:
                    inventory = _inventory(original / sid)
                    (group / "work" / sid).mkdir(parents=True)
                    _copy_files(original / sid, group / "work" / sid, inventory)
                    files.update({f"{sid}/{rel}": digest for rel, digest in inventory.items()})
                binding = parent | {"work": str(final / "work"), "session_ids": selected}
                _write(group / "parent/binding.json", binding)
                if _validate(group / "work", plan, data, refs, selected) != {
                    sid: baseline[sid] for sid in selected
                }:
                    raise ValueError("copied native state differs")
                manifest["groups"][name] = {
                    "session_ids": selected,
                    "work": str(final / "work"),
                    "parent_binding": str(final / "parent/binding.json"),
                    "parent_binding_sha256": _sha(json_bytes(binding)),
                    "baseline_files": files,
                }
            # Detect any mutation that bypassed the cooperative controller locks.
            for name, row in manifest["groups"].items():
                current = {
                    f"{sid}/{rel}": digest
                    for sid in row["session_ids"]
                    for rel, digest in _inventory(original / sid).items()
                }
                if current != row["baseline_files"]:
                    raise ValueError("source changed during shard preparation")
            _write(stage / "manifest.json", manifest)
            if output.exists():
                raise ValueError("shard destination appeared during preparation")
            stage.rename(output)
    return manifest


def _artifact_roots(files):
    roots = set()
    for relative in files:
        parts = Path(relative).parts
        if len(parts) >= 2 and parts[1] in ("requests", "reviews"):
            if len(parts) < 4:
                raise ValueError("unexpected file outside native artifact directory")
            roots.add(Path(*parts[:3]))
    return roots


def _publication_order(shard, baseline, roots):
    """Publish requests first and corrections after their exact predecessors."""
    ordered = sorted(root for root in roots if root.parts[1] == "requests")
    remaining = sorted(root for root in roots if root.parts[1] == "reviews")
    known = {
        (_root.parts[0], _json(shard / _root / "manifest.json")["binding_sha256"])
        for _root in _artifact_roots(baseline)
        if _root.parts[1] == "reviews"
    }
    metadata = {
        root: (
            _json(shard / root / "manifest.json")["binding_sha256"],
            _json(shard / root / "result.json").get("supersedes_review_sha256"),
        )
        for root in remaining
    }
    while remaining:
        ready = [
            root
            for root in remaining
            if metadata[root][1] is None or (root.parts[0], metadata[root][1]) in known
        ]
        if not ready:
            raise ValueError("review dependency cycle or missing predecessor")
        for root in ready:
            known.add((root.parts[0], metadata[root][0]))
            ordered.append(root)
            remaining.remove(root)
    return ordered


def merge_shard(*, manifest: Path, manifest_sha256: str, group: str, report: Path) -> dict:
    """Validate both histories, then append whole native artifact directories."""
    manifest, report = map(_path, (manifest, report))
    data = _json(manifest, manifest_sha256)
    if data.get("implementation_sha256") != _sha(_read(Path(__file__))):
        raise ValueError("shard implementation checksum changed")
    if data.get("schema_version") != _VERSION or group not in data["groups"]:
        raise ValueError("unsupported shard manifest or group")
    if str(manifest.parent) != data["output"]:
        raise ValueError("manifest location changed")
    row = data["groups"][group]
    original, shard, plan = map(_path, (data["original_work"], row["work"], data["plan"]))
    expected_shard = manifest.parent / "groups" / group / "work"
    if shard != expected_shard:
        raise ValueError("shard work binding changed")
    for protected in (original, shard, plan):
        if report.is_relative_to(protected) or protected.is_relative_to(report):
            raise ValueError("report overlaps authoritative path")
    parent = _json(Path(data["parent_binding"]), data["parent_binding_sha256"])
    if str(original) != parent["work"]:
        raise ValueError("original work binding changed")
    _json(Path(row["parent_binding"]), row["parent_binding_sha256"])
    _, plan_data, refs = _load_plan(plan, data["plan_sha256"])
    _groups(
        {name: value["session_ids"] for name, value in data["groups"].items()},
        parent["session_ids"],
        refs,
    )
    ids = row["session_ids"]
    baseline = row["baseline_files"]
    with (
        _controller_lock(original / "queue-controller"),
        _controller_lock(shard / "queue-controller"),
        ExitStack() as locks,
    ):
        for sid in sorted(ids):
            locks.enter_context(_locked(original / sid / "operation"))
            locks.enter_context(_locked(shard / sid / "operation"))
        canonical_files = {
            f"{sid}/{rel}": digest
            for sid in ids
            for rel, digest in _inventory(original / sid).items()
        }
        shard_files = {
            f"{sid}/{rel}": digest for sid in ids for rel, digest in _inventory(shard / sid).items()
        }
        for relative, digest in baseline.items():
            if canonical_files.get(relative) != digest:
                raise ValueError("canonical baseline changed or deleted")
            if (
                Path(relative).parts[1] in ("requests", "reviews")
                and shard_files.get(relative) != digest
            ):
                raise ValueError("shard baseline changed or deleted")
        for relative, digest in canonical_files.items():
            if relative not in baseline and shard_files.get(relative) != digest:
                raise ValueError("canonical additions conflict with shard")
        _validate(original, plan, plan_data, refs, ids)
        _validate(shard, plan, plan_data, refs, ids)
        artifact_roots = _artifact_roots(shard_files)
        new_roots = []
        for root in sorted(artifact_roots):
            prefix = root.as_posix() + "/"
            before = {k: v for k, v in baseline.items() if k.startswith(prefix)}
            current = {k: v for k, v in shard_files.items() if k.startswith(prefix)}
            if before and current != before:
                raise ValueError("existing artifact inventory changed")
            if not before:
                new_roots.append(root)
        new_roots = _publication_order(shard, baseline, new_roots)
        report.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".queue-merge-", dir=report.parent) as temp:
            stage = Path(temp)
            combined = stage / "combined"
            combined.mkdir()
            _copy_files(original, combined, canonical_files)
            for root in new_roots:
                prefix = root.as_posix() + "/"
                files = {k: v for k, v in shard_files.items() if k.startswith(prefix)}
                existing = {k: v for k, v in canonical_files.items() if k.startswith(prefix)}
                if existing and existing != files:
                    raise ValueError("artifact destination conflicts")
                if not existing:
                    _copy_files(shard, combined, files)
            sessions = _validate(combined, plan, plan_data, refs, ids)
            archive = {
                k: v
                for k, v in shard_files.items()
                if Path(k).parts[1] not in ("requests", "reviews")
            }
            result = {
                "schema_version": "vocabulary-queue-shard-merge-1",
                "manifest_sha256": manifest_sha256,
                "group": group,
                "sessions": sessions,
                "artifact_directories": [p.as_posix() for p in new_roots],
                "archive_files": archive,
                "generation_status": "deferred_by_user",
                "provider_calls_executed": 0,
            }
            publication = stage / "report"
            publication.mkdir()
            _copy_files(shard, publication / "archive", archive)
            _write(publication / "merge.json", result)
            if report.exists() and _inventory(report) != _inventory(publication):
                raise ValueError("immutable merge report differs; use a new report path")
            for root in new_roots:
                target = _plain_path(original / root)
                if target.exists():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                # Stage on the same filesystem as the destination for atomic rename.
                with tempfile.TemporaryDirectory(
                    prefix=".shard-import-", dir=target.parent
                ) as local:
                    ready = Path(local) / "artifact"
                    ready.mkdir()
                    subfiles = _inventory(combined / root)
                    _copy_files(combined / root, ready, subfiles)
                    if target.exists():
                        raise ValueError("artifact destination appeared during merge")
                    ready.rename(target)
            if _validate(original, plan, plan_data, refs, ids) != sessions:
                raise ValueError("post-publication native state differs; inspect and resume")
            if not report.exists():
                publication.rename(report)
            return result
