"""Private cross-process lock for Korean foundation state transitions."""

from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import os
from pathlib import Path
import stat
from typing import Final, Iterator


KOREAN_FOUNDATION_STATE_LOCK_VERSION: Final = (
    "phase31-korean-foundation-state-lock-v1"
)


def _is_link_or_reparse(value: os.stat_result) -> bool:
    if stat.S_ISLNK(value.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(value, "st_file_attributes", 0) & reparse_flag)


def _validated_lock_root(lock_root: Path) -> Path:
    try:
        root_stat = lock_root.lstat()
    except OSError as exc:
        raise RuntimeError("korean_foundation_state_lock_unavailable") from exc
    if _is_link_or_reparse(root_stat) or not stat.S_ISDIR(root_stat.st_mode):
        raise RuntimeError("korean_foundation_state_lock_unsafe_root")
    try:
        return lock_root.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("korean_foundation_state_lock_unavailable") from exc


@contextmanager
def _windows_named_mutex(lock_root: Path) -> Iterator[None]:
    # A named kernel mutex serializes processes without creating mutable lock files.
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_mutex = kernel32.CreateMutexW
    create_mutex.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
    create_mutex.restype = wintypes.HANDLE
    wait_for_single_object = kernel32.WaitForSingleObject
    wait_for_single_object.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    wait_for_single_object.restype = wintypes.DWORD
    release_mutex = kernel32.ReleaseMutex
    release_mutex.argtypes = (wintypes.HANDLE,)
    release_mutex.restype = wintypes.BOOL
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL

    lock_identity = os.path.normcase(str(lock_root)).encode("utf-8")
    mutex_name = (
        "Local\\MultilangKoreanFoundationState-"
        + sha256(lock_identity).hexdigest()
    )
    handle = create_mutex(None, False, mutex_name)
    if not handle:
        raise RuntimeError("korean_foundation_state_lock_unavailable")
    acquired = False
    try:
        result = wait_for_single_object(handle, 0xFFFFFFFF)
        if result not in {0x00000000, 0x00000080}:
            raise RuntimeError("korean_foundation_state_lock_unavailable")
        acquired = True
        yield
    finally:
        if acquired:
            release_mutex(handle)
        close_handle(handle)


@contextmanager
def _posix_directory_lock(lock_root: Path) -> Iterator[None]:
    import fcntl

    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(lock_root, flags)
    except OSError as exc:
        raise RuntimeError("korean_foundation_state_lock_unavailable") from exc
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


@contextmanager
def _korean_foundation_state_lock(lock_root: Path) -> Iterator[None]:
    """Serialize fixed state changes without leaving filesystem lock artifacts."""

    validated_root = _validated_lock_root(lock_root)
    manager = (
        _windows_named_mutex(validated_root)
        if os.name == "nt"
        else _posix_directory_lock(validated_root)
    )
    with manager:
        yield


__all__ = [
    "KOREAN_FOUNDATION_STATE_LOCK_VERSION",
    "_korean_foundation_state_lock",
]
