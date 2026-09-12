"""Native Korean authority locations and explicit hash-preserving legacy import."""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory


def native_korean_evidence_relpath() -> Path:
    configured = os.environ.get(
        "MULTILANG_KOREAN_EVIDENCE_ROOT", "data/korean_foundations/evidence"
    )
    path = PurePosixPath(configured)
    if (
        path.is_absolute()
        or not path.parts
        or ".." in path.parts
        or ".planning" in path.parts
        or "\\" in configured
        or ":" in configured
        or "\x00" in configured
    ):
        raise ValueError(
            "Korean evidence root must be a safe native project-relative path"
        )
    return Path(*path.parts)


def _hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _no_links(path: Path, root: Path) -> None:
    relative = path.relative_to(root)
    current = root
    if root.is_symlink():
        raise ValueError("evidence root cannot be a symlink")
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("evidence paths cannot include symlinks")


def import_legacy_evidence(
    *, legacy_root: Path, project_root: Path, expected_files: Mapping[str, str]
) -> dict[str, object]:
    """Copy only caller-selected, hash-bound artifacts; runtime never searches legacy state.

    Imports are explicit and idempotent. No reapproval or path rewriting occurs:
    signed bytes and their historical references remain byte-for-byte unchanged.
    """
    legacy_root = Path(legacy_root).absolute()
    project_root = Path(project_root).absolute()
    destination = project_root / native_korean_evidence_relpath()
    if not expected_files or len(expected_files) > 8192:
        raise ValueError("evidence import file count limit")
    if legacy_root == destination or destination.is_relative_to(legacy_root):
        raise ValueError(
            "legacy evidence source and native destination must be isolated"
        )
    total = 0
    sources: dict[str, Path] = {}
    for name, expected_hash in sorted(expected_files.items()):
        relative = PurePosixPath(name)
        if (
            relative.is_absolute()
            or not relative.parts
            or ".." in relative.parts
            or "\\" in name
            or ":" in name
            or Path(name).suffix not in {".json", ".md", ".wav", ".png"}
            or name == "native-import-manifest.json"
        ):
            raise ValueError("unsafe evidence import member")
        if len(expected_hash) != 64 or any(
            value not in "0123456789abcdef" for value in expected_hash
        ):
            raise ValueError("invalid evidence SHA-256 hash")
        source = legacy_root.joinpath(*relative.parts)
        _no_links(source, legacy_root)
        if not source.is_file() or source.stat().st_size > 32 * 1024 * 1024:
            raise ValueError("evidence import member limit or missing file")
        total += source.stat().st_size
        if total > 512 * 1024 * 1024:
            raise ValueError("evidence import byte limit")
        if _hash(source) != expected_hash:
            raise ValueError("legacy evidence hash mismatch")
        sources[name] = source
    payload = {
        "version": "native-evidence-import-1",
        "file_count": len(sources),
        "total_bytes": total,
        "files": dict(sorted(expected_files.items())),
    }
    payload["manifest_sha256"] = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    _no_links(destination, project_root)
    if destination.exists():
        for name, expected_hash in expected_files.items():
            path = destination / name
            _no_links(path, project_root)
            if not path.is_file() or _hash(path) != expected_hash:
                raise ValueError("native evidence import conflicts with existing hash")
        return payload
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix="native-evidence-import-", dir=destination.parent
    ) as temporary:
        staged = Path(temporary) / "evidence"
        staged.mkdir()
        for name, source in sources.items():
            target = staged / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if _hash(target) != expected_files[name]:
                raise ValueError("evidence changed during import")
        (staged / "native-import-manifest.json").write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        staged.rename(destination)
    return payload
