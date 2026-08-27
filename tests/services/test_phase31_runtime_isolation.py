"""Fixed runtime-isolation helper for Phase 31 final-suite closure."""

from __future__ import annotations

from hashlib import sha256
from importlib import util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from types import ModuleType

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "verify_phase31_runtime_isolation.py"


def _load_helper() -> ModuleType:
    spec = util.spec_from_file_location(
        "_phase31_runtime_isolation_helper",
        SCRIPT_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_file(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _reason(exc_info: pytest.ExceptionInfo[BaseException]) -> str:
    return str(exc_info.value)


def test_runtime_isolation_contract_is_not_implemented() -> None:
    assert SCRIPT_PATH.is_file()
    helper = _load_helper()
    assert tuple(helper.FIXED_ENV_PATH.parts) == (
        "/",
        "tmp",
        "multilang-phase31-py312",
    )
    assert tuple(helper.REPOSITORY_VENV_RELPATH.parts) == (".venv",)
    assert tuple(helper.PUBLIC_OPERATIONS) == (
        "prepare",
        "hash-venv",
        "fingerprint-venv",
    )


def test_prepare_creates_only_fixed_current_user_0700_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    fake_tmp = tmp_path / "tmp"
    fake_tmp.mkdir(mode=0o777)
    fake_tmp.chmod(0o1777)
    monkeypatch.setattr(helper, "TMP_ROOT", fake_tmp)
    monkeypatch.setattr(helper, "FIXED_ENV_PATH", fake_tmp / "multilang-phase31-py312")

    result = helper.prepare_runtime_isolation()

    assert result == {
        "operation": "prepare",
        "path": "/tmp/multilang-phase31-py312",
        "status": "ready",
        "mode": "0700",
    }
    child = fake_tmp / "multilang-phase31-py312"
    metadata = child.lstat()
    assert stat.S_ISDIR(metadata.st_mode)
    assert stat.S_IMODE(metadata.st_mode) == 0o700
    assert metadata.st_uid == os.getuid()
    assert sorted(path.relative_to(fake_tmp).as_posix() for path in fake_tmp.rglob("*")) == [
        "multilang-phase31-py312",
    ]


def test_prepare_accepts_existing_safe_empty_child_without_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    fake_tmp = tmp_path / "tmp"
    child = fake_tmp / "multilang-phase31-py312"
    child.mkdir(parents=True, mode=0o700)
    fake_tmp.chmod(0o1777)
    child.chmod(0o700)
    monkeypatch.setattr(helper, "TMP_ROOT", fake_tmp)
    monkeypatch.setattr(helper, "FIXED_ENV_PATH", child)

    before = child.lstat().st_mtime_ns
    result = helper.prepare_runtime_isolation()

    assert result["status"] == "ready"
    assert child.lstat().st_mtime_ns == before


@pytest.mark.parametrize(
    ("setup", "expected_reason"),
    [
        ("tmp-link", "tmp_unsafe"),
        ("tmp-not-sticky", "tmp_unsafe"),
        ("child-link", "env_unsafe"),
        ("child-file", "env_unsafe"),
        ("child-mode", "env_unsafe"),
    ],
)
def test_prepare_rejects_unsafe_tmp_or_child_without_cleanup(
    setup: str,
    expected_reason: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    fake_tmp = tmp_path / "tmp"
    real_tmp = fake_tmp
    if setup == "tmp-link":
        target = tmp_path / "target"
        target.mkdir()
        fake_tmp.symlink_to(target, target_is_directory=True)
    else:
        fake_tmp.mkdir(mode=0o777)
        fake_tmp.chmod(0o1777)
        if setup == "tmp-not-sticky":
            fake_tmp.chmod(0o755)
        child = fake_tmp / "multilang-phase31-py312"
        if setup == "child-link":
            target = tmp_path / "target"
            target.mkdir()
            child.symlink_to(target, target_is_directory=True)
        elif setup == "child-file":
            child.write_text("not a directory", encoding="utf-8")
        elif setup == "child-mode":
            child.mkdir(mode=0o755)
            child.chmod(0o755)
    monkeypatch.setattr(helper, "TMP_ROOT", real_tmp)
    monkeypatch.setattr(helper, "FIXED_ENV_PATH", real_tmp / "multilang-phase31-py312")
    before = _tree_state(tmp_path)

    with pytest.raises(helper.RuntimeIsolationError) as exc_info:
        helper.prepare_runtime_isolation()

    assert _reason(exc_info) == expected_reason
    assert _tree_state(tmp_path) == before


def test_hash_venv_reports_absent_marker_without_creating_venv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    monkeypatch.setattr(helper, "PROJECT_ROOT", tmp_path)

    result = helper.hash_repository_venv()

    assert result == {
        "operation": "hash-venv",
        "path": ".venv",
        "status": "absent",
        "tree_sha256": helper.ABSENT_VENV_SHA256,
        "file_count": 0,
    }
    assert not (tmp_path / ".venv").exists()


def test_hash_venv_is_recursive_deterministic_and_mode_bound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    monkeypatch.setattr(helper, "PROJECT_ROOT", tmp_path)
    venv = tmp_path / ".venv"
    _write_file(venv / "pyvenv.cfg", b"home = /fixture\n")
    venv.chmod(0o700)
    (venv / "pyvenv.cfg").chmod(0o644)
    _write_file(venv / "bin" / "python", b"#!/fixture/python\n")
    (venv / "bin").chmod(0o755)
    (venv / "bin" / "python").chmod(0o755)
    _write_file(venv / "lib" / "module.py", b"VALUE = 1\n")
    (venv / "lib").chmod(0o755)
    (venv / "lib" / "module.py").chmod(0o644)
    expected_rows = [
        [".", "directory", "0700", ""],
        ["bin", "directory", "0755", ""],
        ["bin/python", "file", "0755", sha256(b"#!/fixture/python\n").hexdigest()],
        ["lib", "directory", "0755", ""],
        ["lib/module.py", "file", "0644", sha256(b"VALUE = 1\n").hexdigest()],
        ["pyvenv.cfg", "file", "0644", sha256(b"home = /fixture\n").hexdigest()],
    ]
    expected_hash = sha256(
        json.dumps(expected_rows, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()

    first = helper.hash_repository_venv()
    second = helper.hash_repository_venv()

    assert first == second
    assert first == {
        "operation": "hash-venv",
        "path": ".venv",
        "status": "present",
        "tree_sha256": expected_hash,
        "file_count": 3,
    }


def test_hash_venv_rejects_links_and_special_files_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    monkeypatch.setattr(helper, "PROJECT_ROOT", tmp_path)
    venv = tmp_path / ".venv"
    venv.mkdir()
    _write_file(venv / "pyvenv.cfg", b"home = /fixture\n")
    (venv / "link").symlink_to(venv / "pyvenv.cfg")
    before = _tree_state(tmp_path)

    with pytest.raises(helper.RuntimeIsolationError) as exc_info:
        helper.hash_repository_venv()

    assert _reason(exc_info) == "venv_unsafe"
    assert _tree_state(tmp_path) == before


def test_fingerprint_venv_records_links_without_following_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    monkeypatch.setattr(helper, "PROJECT_ROOT", tmp_path)
    venv = tmp_path / ".venv"
    venv.mkdir(mode=0o700)
    outside = tmp_path / "outside-one"
    outside.write_bytes(b"secret-one")
    link = venv / "python"
    link.symlink_to(outside)

    first = helper.fingerprint_repository_venv()
    outside.write_bytes(b"changed-but-must-not-be-read")
    second = helper.fingerprint_repository_venv()
    link.unlink()
    replacement = tmp_path / "outside-two"
    replacement.write_bytes(b"secret-one")
    link.symlink_to(replacement)
    third = helper.fingerprint_repository_venv()

    assert first == second
    assert first["operation"] == "fingerprint-venv"
    assert first["status"] == "unsafe"
    assert first["link_count"] == 1
    assert first["special_count"] == 0
    assert first["tree_sha256"] != third["tree_sha256"]


def test_fingerprint_venv_reports_deterministic_absent_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    monkeypatch.setattr(helper, "PROJECT_ROOT", tmp_path)

    first = helper.fingerprint_repository_venv()
    second = helper.fingerprint_repository_venv()

    assert first == second
    assert first == {
        "operation": "fingerprint-venv",
        "path": ".venv",
        "status": "absent",
        "tree_sha256": helper.ABSENT_VENV_FINGERPRINT_SHA256,
        "file_count": 0,
        "link_count": 0,
        "special_count": 0,
    }


def test_cli_accepts_only_fixed_operations_and_content_free_errors(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "unexpected", str(tmp_path)],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "runtime_isolation_error=unsupported_operation\n"
    assert str(tmp_path) not in result.stderr


def _tree_state(root: Path) -> dict[str, tuple[str, int, int]]:
    rows: dict[str, tuple[str, int, int]] = {}
    for path in sorted(root.rglob("*")):
        metadata = path.lstat()
        kind = (
            "link"
            if stat.S_ISLNK(metadata.st_mode)
            else "directory"
            if stat.S_ISDIR(metadata.st_mode)
            else "file"
            if stat.S_ISREG(metadata.st_mode)
            else "special"
        )
        rows[path.relative_to(root).as_posix()] = (
            kind,
            stat.S_IMODE(metadata.st_mode),
            metadata.st_mtime_ns,
        )
    return rows
