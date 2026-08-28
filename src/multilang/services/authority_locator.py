"""Canonical authority locator hashing without persisting raw paths."""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import unicodedata

from multilang.db.provisioning import find_project_root


def _safe_root(repo_root: Path | None) -> Path:
    root = Path(repo_root) if repo_root is not None else find_project_root()
    if root is None:
        raise ValueError("authority locator root is unavailable")
    try:
        root_metadata = root.lstat()
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise ValueError("authority locator root is unavailable") from exc
    if root.is_symlink() or not root_metadata or not resolved.is_dir():
        raise ValueError("authority locator root is unsafe")
    return resolved


def _candidate_under_root(path: Path, root: Path) -> Path:
    raw = Path(path)
    candidate = raw if raw.is_absolute() else root / raw
    if any(part == ".." for part in candidate.parts):
        candidate = candidate.resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("authority locator escapes root") from exc
    return candidate


def _reject_symlink_components(path: Path, root: Path) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError("authority locator escapes root") from exc
    current = root
    for part in relative.parts:
        current = current / part
        try:
            if current.is_symlink():
                raise ValueError("authority locator contains a symlink")
        except OSError as exc:
            raise ValueError("authority locator is unavailable") from exc


def _same_file(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev == right.st_dev
        and left.st_ino == right.st_ino
        and left.st_size == right.st_size
        and left.st_mtime_ns == right.st_mtime_ns
    )


def canonical_authority_locator_sha256(path: Path, *, repo_root: Path | None = None) -> str:
    """Hash a safe repo-relative locator with an 8-byte length prefix."""

    root = _safe_root(repo_root)
    candidate = _candidate_under_root(Path(path), root)
    _reject_symlink_components(candidate, root)
    try:
        before = candidate.lstat()
    except OSError as exc:
        raise ValueError("authority locator is unavailable") from exc
    if not candidate.is_file() or candidate.is_symlink():
        raise ValueError("authority locator target is unsafe")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(candidate, flags)
    except OSError as exc:
        raise ValueError("authority locator target is unsafe") from exc
    try:
        opened = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after = candidate.lstat()
    except OSError as exc:
        raise ValueError("authority locator drifted") from exc
    if not _same_file(before, opened) or not _same_file(opened, after):
        raise ValueError("authority locator drifted")
    relative = candidate.relative_to(root).as_posix()
    canonical = unicodedata.normalize("NFC", os.path.normcase(relative)).encode("utf-8")
    return sha256(len(canonical).to_bytes(8, "big") + canonical).hexdigest()


__all__ = ["canonical_authority_locator_sha256"]
