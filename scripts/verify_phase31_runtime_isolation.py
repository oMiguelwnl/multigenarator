#!/usr/bin/env python3
"""Verify the fixed Phase 31 isolated runtime boundary without side effects."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import sys
from typing import Final


PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
TMP_ROOT: Path = Path("/tmp")
FIXED_ENV_PATH: Path = TMP_ROOT / "multilang-phase31-py312"
REPOSITORY_VENV_RELPATH: Final = Path(".venv")
PUBLIC_OPERATIONS: Final = ("prepare", "hash-venv")
ABSENT_VENV_SHA256: Final = sha256(b"phase31-runtime-isolation:.venv:absent").hexdigest()
_ENV_BASENAME: Final = "multilang-phase31-py312"


class RuntimeIsolationError(ValueError):
    """Content-free helper failure."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)

    def __str__(self) -> str:
        return self.reason_code


def _raise(reason_code: str) -> None:
    raise RuntimeIsolationError(reason_code)


def _is_link_or_reparse(metadata: os.stat_result) -> bool:
    if stat.S_ISLNK(metadata.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(metadata, "st_file_attributes", 0) & reparse_flag)


def _assert_fixed_env_path() -> None:
    if (
        FIXED_ENV_PATH.parent != TMP_ROOT
        or FIXED_ENV_PATH.name != _ENV_BASENAME
        or FIXED_ENV_PATH.as_posix() != f"{TMP_ROOT.as_posix()}/{_ENV_BASENAME}"
    ):
        _raise("env_unsafe")


def _expected_tmp_owner() -> int:
    return 0 if TMP_ROOT == Path("/tmp") else os.getuid()


def _assert_tmp_root_is_safe() -> None:
    try:
        metadata = TMP_ROOT.lstat()
    except OSError:
        _raise("tmp_unsafe")
    mode = stat.S_IMODE(metadata.st_mode)
    if (
        _is_link_or_reparse(metadata)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != _expected_tmp_owner()
        or (mode & 0o777) != 0o777
        or not (metadata.st_mode & stat.S_ISVTX)
    ):
        _raise("tmp_unsafe")


def _assert_env_child_is_safe() -> None:
    try:
        metadata = FIXED_ENV_PATH.lstat()
    except FileNotFoundError:
        try:
            FIXED_ENV_PATH.mkdir(mode=0o700)
        except OSError:
            _raise("env_create_failed")
        try:
            metadata = FIXED_ENV_PATH.lstat()
        except OSError:
            _raise("env_create_failed")
    except OSError:
        _raise("env_unsafe")
    if (
        _is_link_or_reparse(metadata)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        _raise("env_unsafe")


def prepare_runtime_isolation() -> dict[str, object]:
    """Create or verify the one fixed isolated runtime directory."""

    _assert_fixed_env_path()
    _assert_tmp_root_is_safe()
    _assert_env_child_is_safe()
    return {
        "operation": "prepare",
        "path": "/tmp/multilang-phase31-py312",
        "status": "ready",
        "mode": "0700",
    }


def _mode_text(metadata: os.stat_result) -> str:
    return f"{stat.S_IMODE(metadata.st_mode):04o}"


def _hash_file(path: Path) -> str:
    try:
        return sha256(path.read_bytes()).hexdigest()
    except OSError:
        _raise("venv_unsafe")


def _venv_rows(venv: Path) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    file_count = 0
    for candidate in (venv, *sorted(venv.rglob("*"))):
        try:
            metadata = candidate.lstat()
        except OSError:
            _raise("venv_unsafe")
        if _is_link_or_reparse(metadata):
            _raise("venv_unsafe")
        relpath = "." if candidate == venv else candidate.relative_to(venv).as_posix()
        if stat.S_ISDIR(metadata.st_mode):
            rows.append([relpath, "directory", _mode_text(metadata), ""])
        elif stat.S_ISREG(metadata.st_mode):
            file_count += 1
            rows.append([relpath, "file", _mode_text(metadata), _hash_file(candidate)])
        else:
            _raise("venv_unsafe")
    return rows, file_count


def hash_repository_venv() -> dict[str, object]:
    """Return a deterministic recursive hash for the repository `.venv` tree."""

    venv = PROJECT_ROOT / REPOSITORY_VENV_RELPATH
    try:
        metadata = venv.lstat()
    except FileNotFoundError:
        return {
            "operation": "hash-venv",
            "path": ".venv",
            "status": "absent",
            "tree_sha256": ABSENT_VENV_SHA256,
            "file_count": 0,
        }
    except OSError:
        _raise("venv_unsafe")
    if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
        _raise("venv_unsafe")
    rows, file_count = _venv_rows(venv)
    digest = sha256(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "operation": "hash-venv",
        "path": ".venv",
        "status": "present",
        "tree_sha256": digest,
        "file_count": file_count,
    }


def _print_result(result: dict[str, object]) -> None:
    for key, value in result.items():
        print(f"{key}={value}")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] not in PUBLIC_OPERATIONS:
        print("runtime_isolation_error=unsupported_operation", file=sys.stderr)
        return 2
    try:
        result = (
            prepare_runtime_isolation()
            if args[0] == "prepare"
            else hash_repository_venv()
        )
    except RuntimeIsolationError as exc:
        print(f"runtime_isolation_error={exc}", file=sys.stderr)
        return 1
    _print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
