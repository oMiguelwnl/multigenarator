"""Fixed active-pointer and immutable Korean foundation snapshot contracts."""

from __future__ import annotations

import builtins
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from importlib import import_module, util
import inspect
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import threading
import time
from types import ModuleType, SimpleNamespace
from typing import Any, Callable, Iterator

import pytest
from pydantic import ValidationError


def _snapshot() -> ModuleType:
    assert (
        util.find_spec("multilang.services.korean_foundation_snapshot")
        is not None
    ), "the Korean foundation snapshot service must exist"
    return import_module("multilang.services.korean_foundation_snapshot")


def _canonical_sha256(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _bundle_sha256(payload: dict[str, object]) -> str:
    unsigned = deepcopy(payload)
    unsigned.pop("bundle_sha256", None)
    return _canonical_sha256(unsigned)


def _production_member_bytes() -> dict[str, bytes]:
    return {
        "content/korean-concepts-v1.json": Path(
            "data/korean_foundations/korean-concepts-v1.json"
        ).read_bytes(),
        "content/hangul-v1.json": Path(
            "data/korean_foundations/hangul-v1.json"
        ).read_bytes(),
        "content/pronunciation-i-plus-1-v1.json": Path(
            "data/korean_foundations/pronunciation-i-plus-1-v1.json"
        ).read_bytes(),
        "content/korean-foundations-v1-curation.json": Path(
            "data/korean_foundations/korean-foundations-v1-curation.json"
        ).read_bytes(),
        "content/korean-foundations-v1-media.json": b'{"test_media_manifest":true}\n',
        "review/test-review-evidence.json": b'{"test_evidence":true}\n',
        "media/test-image.png": b"\x89PNG\r\n\x1a\nTEST-SNAPSHOT-IMAGE",
    }


_ROLE_BY_RELPATH = {
    "content/korean-concepts-v1.json": "concept_registry",
    "content/hangul-v1.json": "hangul_source_pack",
    "content/pronunciation-i-plus-1-v1.json": "pronunciation_source_pack",
    "content/korean-foundations-v1-curation.json": "curation_manifest",
    "content/korean-foundations-v1-media.json": "media_manifest",
    "review/test-review-evidence.json": "review_evidence",
    "media/test-image.png": "media",
}


def _write_snapshot_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    pointer_update: dict[str, object] | None = None,
    manifest_mutator: Callable[[dict[str, object]], None] | None = None,
    omit_relpath: str | None = None,
    add_extra: bool = False,
) -> tuple[ModuleType, Path, dict[str, object]]:
    api = _snapshot()
    monkeypatch.setattr(api, "_PROJECT_ROOT", tmp_path)
    members = _production_member_bytes()
    manifest: dict[str, object] = {
        "schema_version": 1,
        "source_root": "content",
        "review_evidence_root": "review",
        "media_root": "media",
        "members": [
            {
                "role": _ROLE_BY_RELPATH[relpath],
                "relpath": relpath,
                "size_bytes": len(content),
                "sha256": sha256(content).hexdigest(),
            }
            for relpath, content in members.items()
        ],
    }
    manifest["bundle_sha256"] = _bundle_sha256(manifest)
    if manifest_mutator is not None:
        manifest_mutator(manifest)
    bundle_hash = str(manifest["bundle_sha256"])
    snapshot_root = (
        tmp_path / "data" / "korean_foundations" / "snapshots" / bundle_hash
    )
    snapshot_root.mkdir(parents=True)
    for relpath, content in members.items():
        if relpath == omit_relpath:
            continue
        destination = snapshot_root / Path(relpath)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    if add_extra:
        (snapshot_root / "content" / "unmanifested.json").write_text(
            "{}\n", encoding="utf-8"
        )
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    manifest_path = snapshot_root / "snapshot-manifest.json"
    manifest_path.write_bytes(manifest_bytes)

    pointer: dict[str, object] = {
        "schema_version": 1,
        "bundle_sha256": bundle_hash,
        "snapshot_relpath": f"snapshots/{bundle_hash}",
        "snapshot_manifest_sha256": sha256(manifest_bytes).hexdigest(),
    }
    if pointer_update:
        pointer.update(pointer_update)
    pointer_path = (
        tmp_path / "data" / "korean_foundations" / "active-foundations.json"
    )
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    pointer_path.write_text(
        json.dumps(pointer, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return api, pointer_path, pointer


def _reason(exc_info: pytest.ExceptionInfo[BaseException]) -> str:
    reason_code = getattr(exc_info.value, "reason_code")
    return getattr(reason_code, "value", reason_code)


def _plan_31_08_fixture_helpers() -> ModuleType:
    """Load the prior plan's private fixture factory without a public test package."""

    module_name = "_plan_31_08_korean_foundation_evidence_fixture"
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    module_path = Path(__file__).with_name("test_korean_foundation_evidence.py")
    spec = util.spec_from_file_location(module_name, module_path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _install_snapshot_fixture_paths(
    api: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    project_root: Path,
) -> None:
    monkeypatch.setattr(api, "_PROJECT_ROOT", project_root)
    monkeypatch.setattr(
        api,
        "_FIXED_PATHS",
        api._KoreanFoundationSnapshotPaths.from_project_root(project_root),
    )


def _build_receipted_snapshot_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    with_old_active: bool = False,
) -> SimpleNamespace:
    helpers = _plan_31_08_fixture_helpers()
    evidence_api = import_module("multilang.services.korean_foundation_evidence")
    fixture = helpers._build_complete_fixture(tmp_path)
    old_pointer_bytes: bytes | None = None
    old_bundle_sha256: str | None = None
    if with_old_active:
        _old_api, pointer_path, pointer = _write_snapshot_fixture(
            fixture.project_root,
            monkeypatch,
        )
        old_pointer_bytes = pointer_path.read_bytes()
        old_bundle_sha256 = str(pointer["bundle_sha256"])
    helpers._install_fixture_paths(evidence_api, monkeypatch, fixture)
    receipt = (
        evidence_api.validate_and_write_fixed_korean_foundation_validation_receipt(
            confirmed_index_sha256=fixture.index_sha256
        )
    )
    receipt_sha256 = sha256(fixture.receipt_path.read_bytes()).hexdigest()
    api = _snapshot()
    _install_snapshot_fixture_paths(api, monkeypatch, fixture.project_root)
    return SimpleNamespace(
        api=api,
        evidence_api=evidence_api,
        evidence=fixture,
        receipt=receipt,
        receipt_sha256=receipt_sha256,
        paths=api._FIXED_PATHS,
        old_pointer_bytes=old_pointer_bytes,
        old_bundle_sha256=old_bundle_sha256,
    )


def _tree_state(root: Path) -> dict[str, tuple[object, ...]]:
    state: dict[str, tuple[object, ...]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        value = path.lstat()
        if stat.S_ISDIR(value.st_mode):
            state[relative] = ("directory", value.st_mtime_ns)
        elif stat.S_ISREG(value.st_mode):
            state[relative] = ("file", path.read_bytes(), value.st_mtime_ns)
        elif stat.S_ISLNK(value.st_mode):
            state[relative] = ("link", os.readlink(path), value.st_mtime_ns)
        else:
            state[relative] = ("special", value.st_mode, value.st_mtime_ns)
    return state


def _valid_pointer_bytes(seed: str = "9") -> bytes:
    payload = {
        "schema_version": 1,
        "bundle_sha256": seed * 64,
        "snapshot_relpath": f"snapshots/{seed * 64}",
        "snapshot_manifest_sha256": "8" * 64,
    }
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _active_pointer_bytes_for(prepared: object) -> bytes:
    payload = {
        "schema_version": 2,
        "pointer_version": "phase31-korean-foundation-active-pointer-v2",
        "receipt_sha256": getattr(prepared, "receipt_sha256"),
        "bundle_sha256": getattr(prepared, "bundle_sha256"),
        "snapshot_relpath": f"snapshots/{getattr(prepared, 'bundle_sha256')}",
        "snapshot_manifest_sha256": getattr(
            prepared, "snapshot_manifest_sha256"
        ),
        "snapshot_root_sha256": getattr(prepared, "snapshot_root_sha256"),
        "active_prestate_sha256": getattr(prepared, "active_prestate_sha256"),
        "authorization_sha256": getattr(prepared, "authorization_sha256"),
    }
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _poison_snapshot_write_primitives(
    api: ModuleType,
    evidence_api: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Make every write/recovery/lock-creation route reachable in verification fail."""

    def forbidden(*_args: object, **_kwargs: object) -> Any:
        raise AssertionError("strictly read-only verification attempted a write")

    original_os_open = os.open
    write_flags = (
        os.O_WRONLY
        | os.O_RDWR
        | os.O_CREAT
        | os.O_TRUNC
        | os.O_APPEND
        | getattr(os, "O_EXCL", 0)
    )

    def guarded_os_open(
        path: object,
        flags: int,
        *args: object,
        **kwargs: object,
    ) -> int:
        if flags & write_flags:
            return forbidden(path, flags, *args, **kwargs)
        return original_os_open(path, flags, *args, **kwargs)

    original_path_open = Path.open

    def guarded_path_open(
        path: Path,
        mode: str = "r",
        *args: object,
        **kwargs: object,
    ) -> Any:
        if any(marker in mode for marker in ("w", "a", "x", "+")):
            return forbidden(path, mode, *args, **kwargs)
        return original_path_open(path, mode, *args, **kwargs)

    original_builtin_open = builtins.open

    def guarded_builtin_open(
        file: object,
        mode: str = "r",
        *args: object,
        **kwargs: object,
    ) -> Any:
        if any(marker in mode for marker in ("w", "a", "x", "+")):
            return forbidden(file, mode, *args, **kwargs)
        return original_builtin_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(api, "_recover_stale_stages", forbidden)
    monkeypatch.setattr(api, "_korean_foundation_state_lock", forbidden)
    monkeypatch.setattr(evidence_api, "_atomic_write_receipt", forbidden)
    for name in (
        "_atomic_activate_pointer",
        "_cleanup_own_stage",
        "_copy_member_to_stage",
        "_rename_snapshot_stage",
        "_stage_prepared_snapshot",
        "_write_all",
        "_write_manifest_to_stage",
        "_write_pointer_temp",
    ):
        if hasattr(api, name):
            monkeypatch.setattr(api, name, forbidden)
    monkeypatch.setattr(api.tempfile, "mkdtemp", forbidden)
    monkeypatch.setattr(api.tempfile, "mkstemp", forbidden)
    for name in (
        "copy",
        "copy2",
        "copyfile",
        "copyfileobj",
        "copytree",
        "move",
        "rmtree",
    ):
        monkeypatch.setattr(api.shutil, name, forbidden)
    for name in (
        "chmod",
        "fchmod",
        "fsync",
        "rename",
        "replace",
        "remove",
        "write",
        "unlink",
        "rmdir",
        "mkdir",
        "makedirs",
    ):
        if name == "fchmod" and not hasattr(api.os, name):
            continue
        monkeypatch.setattr(api.os, name, forbidden)
    monkeypatch.setattr(api.os, "open", guarded_os_open)
    monkeypatch.setattr(Path, "open", guarded_path_open)
    monkeypatch.setattr(builtins, "open", guarded_builtin_open)
    for name in (
        "chmod",
        "mkdir",
        "rename",
        "replace",
        "rmdir",
        "touch",
        "unlink",
        "write_bytes",
        "write_text",
    ):
        monkeypatch.setattr(Path, name, forbidden)


def test_snapshot_public_contract_uses_one_fixed_no_argument_resolver() -> None:
    api = _snapshot()

    assert api.ACTIVE_KOREAN_FOUNDATIONS_POINTER_PATH == Path(
        "data/korean_foundations/active-foundations.json"
    )
    assert api.KOREAN_FOUNDATION_SNAPSHOT_ROOT == Path(
        "data/korean_foundations/snapshots"
    )
    assert tuple(
        inspect.signature(api.resolve_active_korean_foundation_snapshot).parameters
    ) == ()
    assert "path" not in inspect.signature(
        api.resolve_active_korean_foundation_snapshot
    ).parameters
    assert "root" not in inspect.signature(
        api.resolve_active_korean_foundation_snapshot
    ).parameters
    source = inspect.getsource(api.resolve_active_korean_foundation_snapshot).casefold()
    assert "http://" not in source
    assert "https://" not in source
    assert "requests" not in source


def test_missing_active_pointer_fails_before_any_candidate_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _snapshot()
    monkeypatch.setattr(api, "_PROJECT_ROOT", tmp_path)

    with pytest.raises(api.KoreanFoundationSnapshotError) as exc_info:
        api.resolve_active_korean_foundation_snapshot()
    assert _reason(exc_info) == "production_not_active"
    assert str(exc_info.value) == "production_not_active"


def test_resolver_reads_pointer_once_and_returns_one_frozen_complete_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api, pointer_path, pointer = _write_snapshot_fixture(tmp_path, monkeypatch)
    original_read_bytes = Path.read_bytes
    pointer_reads = 0

    def counted_read_bytes(path: Path) -> bytes:
        nonlocal pointer_reads
        if path == pointer_path:
            pointer_reads += 1
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", counted_read_bytes)
    resolved = api.resolve_active_korean_foundation_snapshot()

    assert pointer_reads == 1
    assert resolved.bundle_sha256 == pointer["bundle_sha256"]
    assert resolved.concept_registry.registry_version == "korean-concepts-v1"
    assert len(resolved.hangul_source_pack.entries) == 92
    assert len(resolved.pronunciation_source_pack.entries) == 47
    assert len(resolved.curation_manifest.records) == 139
    assert resolved.media_manifest_bytes == b'{"test_media_manifest":true}\n'
    assert len(resolved.review_evidence_members) == 1
    assert len(resolved.media_members) == 1
    assert all(
        member.path.is_relative_to(resolved.snapshot_root)
        for member in resolved.members
    )
    with pytest.raises(ValidationError):
        resolved.bundle_sha256 = "0" * 64


def test_pointer_contract_rejects_extras_mutable_timestamps_and_uppercase_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for extra in (
        {"activated_at": "2026-08-05T00:00:00Z"},
        {"reviewer": "test-reviewer"},
        {"bundle_sha256": "A" * 64},
    ):
        case_root = tmp_path / str(len(list(tmp_path.iterdir())))
        case_root.mkdir()
        api, _, _ = _write_snapshot_fixture(
            case_root,
            monkeypatch,
            pointer_update=extra,
        )
        with pytest.raises(api.KoreanFoundationSnapshotError) as exc_info:
            api.resolve_active_korean_foundation_snapshot()
        assert _reason(exc_info) == "active_pointer_invalid"


@pytest.mark.parametrize(
    "unsafe_relpath",
    [
        "/absolute/snapshot",
        "C:/snapshot",
        "C:\\snapshot",
        "../snapshots/escape",
        "snapshots\\bundle",
        "https://example.invalid/snapshot",
        "file://snapshot",
        "snapshots/bundle.apkg",
        "snapshots/bundle.zip",
    ],
)
def test_pointer_rejects_paths_urls_archives_drives_and_traversal(
    unsafe_relpath: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api, _, _ = _write_snapshot_fixture(
        tmp_path,
        monkeypatch,
        pointer_update={"snapshot_relpath": unsafe_relpath},
    )

    with pytest.raises(api.KoreanFoundationSnapshotError) as exc_info:
        api.resolve_active_korean_foundation_snapshot()
    assert _reason(exc_info) == "unsafe_snapshot_path"
    diagnostic = str(exc_info.value)
    assert unsafe_relpath not in diagnostic
    assert str(tmp_path) not in diagnostic


def test_bundle_name_manifest_hash_and_member_hash_drift_all_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name_root = tmp_path / "name"
    name_root.mkdir()
    api, _, pointer = _write_snapshot_fixture(name_root, monkeypatch)
    pointer_path = (
        name_root / "data" / "korean_foundations" / "active-foundations.json"
    )
    changed_pointer = dict(pointer)
    changed_pointer["bundle_sha256"] = "0" * 64
    pointer_path.write_text(json.dumps(changed_pointer) + "\n", encoding="utf-8")
    with pytest.raises(api.KoreanFoundationSnapshotError) as exc_info:
        api.resolve_active_korean_foundation_snapshot()
    assert _reason(exc_info) == "bundle_name_mismatch"

    manifest_root = tmp_path / "manifest"
    manifest_root.mkdir()
    api, _, pointer = _write_snapshot_fixture(manifest_root, monkeypatch)
    manifest_path = (
        manifest_root
        / "data"
        / "korean_foundations"
        / str(pointer["snapshot_relpath"])
        / "snapshot-manifest.json"
    )
    manifest_path.write_bytes(manifest_path.read_bytes() + b" ")
    with pytest.raises(api.KoreanFoundationSnapshotError) as exc_info:
        api.resolve_active_korean_foundation_snapshot()
    assert _reason(exc_info) == "snapshot_manifest_hash_mismatch"

    member_root = tmp_path / "member"
    member_root.mkdir()
    api, _, pointer = _write_snapshot_fixture(member_root, monkeypatch)
    member_path = (
        member_root
        / "data"
        / "korean_foundations"
        / str(pointer["snapshot_relpath"])
        / "content"
        / "hangul-v1.json"
    )
    member_path.write_bytes(member_path.read_bytes() + b"tampered")
    with pytest.raises(api.KoreanFoundationSnapshotError) as exc_info:
        api.resolve_active_korean_foundation_snapshot()
    assert _reason(exc_info) == "snapshot_member_hash_mismatch"


@pytest.mark.parametrize(
    ("omit_relpath", "add_extra", "expected_reason"),
    [
        ("content/hangul-v1.json", False, "snapshot_member_missing"),
        (None, True, "snapshot_extra_member"),
    ],
)
def test_missing_and_unmanifested_snapshot_files_are_rejected(
    omit_relpath: str | None,
    add_extra: bool,
    expected_reason: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api, _, _ = _write_snapshot_fixture(
        tmp_path,
        monkeypatch,
        omit_relpath=omit_relpath,
        add_extra=add_extra,
    )
    with pytest.raises(api.KoreanFoundationSnapshotError) as exc_info:
        api.resolve_active_korean_foundation_snapshot()
    assert _reason(exc_info) == expected_reason


def test_symlink_member_and_simulated_windows_reparse_component_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    symlink_root = tmp_path / "symlink"
    symlink_root.mkdir()
    api, _, pointer = _write_snapshot_fixture(symlink_root, monkeypatch)
    snapshot_root = (
        symlink_root
        / "data"
        / "korean_foundations"
        / str(pointer["snapshot_relpath"])
    )
    member = snapshot_root / "media" / "test-image.png"
    outside = symlink_root / "outside.png"
    outside.write_bytes(member.read_bytes())
    member.unlink()
    try:
        member.symlink_to(outside)
    except OSError:
        original_lstat = Path.lstat

        def simulated_symlink_lstat(path: Path) -> os.stat_result:
            if path == member:
                return SimpleNamespace(
                    st_mode=stat.S_IFLNK,
                    st_file_attributes=0,
                    st_size=outside.stat().st_size,
                )
            return original_lstat(path)

        monkeypatch.setattr(Path, "lstat", simulated_symlink_lstat)
    with pytest.raises(api.KoreanFoundationSnapshotError) as exc_info:
        api.resolve_active_korean_foundation_snapshot()
    assert _reason(exc_info) == "unsafe_filesystem_component"
    assert str(outside) not in str(exc_info.value)

    reparse_root = tmp_path / "reparse"
    reparse_root.mkdir()
    api, _, _ = _write_snapshot_fixture(reparse_root, monkeypatch)
    original = api._stat_is_link_or_reparse
    calls = 0

    def simulated_reparse(stat_result: os.stat_result) -> bool:
        nonlocal calls
        calls += 1
        return calls == 4 or original(stat_result)

    monkeypatch.setattr(api, "_stat_is_link_or_reparse", simulated_reparse)
    with pytest.raises(api.KoreanFoundationSnapshotError) as exc_info:
        api.resolve_active_korean_foundation_snapshot()
    assert _reason(exc_info) == "unsafe_filesystem_component"


def test_snapshot_manifest_rejects_unsafe_member_paths_and_duplicate_roles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unsafe_member(manifest: dict[str, object]) -> None:
        members = manifest["members"]
        assert isinstance(members, list)
        member = members[0]
        assert isinstance(member, dict)
        member["relpath"] = "../candidate.json"
        manifest["bundle_sha256"] = _bundle_sha256(manifest)

    api, _, _ = _write_snapshot_fixture(
        tmp_path / "unsafe",
        monkeypatch,
        manifest_mutator=unsafe_member,
    )
    with pytest.raises(api.KoreanFoundationSnapshotError) as exc_info:
        api.resolve_active_korean_foundation_snapshot()
    assert _reason(exc_info) == "snapshot_manifest_invalid"

    def archive_member(manifest: dict[str, object]) -> None:
        members = manifest["members"]
        assert isinstance(members, list)
        member = members[0]
        assert isinstance(member, dict)
        member["relpath"] = "content/source.apkg"
        manifest["bundle_sha256"] = _bundle_sha256(manifest)

    api, _, _ = _write_snapshot_fixture(
        tmp_path / "archive",
        monkeypatch,
        manifest_mutator=archive_member,
    )
    with pytest.raises(api.KoreanFoundationSnapshotError) as exc_info:
        api.resolve_active_korean_foundation_snapshot()
    assert _reason(exc_info) == "snapshot_manifest_invalid"

    def duplicate_role(manifest: dict[str, object]) -> None:
        members = manifest["members"]
        assert isinstance(members, list)
        first = members[0]
        second = members[1]
        assert isinstance(first, dict) and isinstance(second, dict)
        second["role"] = first["role"]
        manifest["bundle_sha256"] = _bundle_sha256(manifest)

    api, _, _ = _write_snapshot_fixture(
        tmp_path / "duplicate",
        monkeypatch,
        manifest_mutator=duplicate_role,
    )
    with pytest.raises(api.KoreanFoundationSnapshotError) as exc_info:
        api.resolve_active_korean_foundation_snapshot()
    assert _reason(exc_info) == "snapshot_manifest_invalid"


def test_snapshot_preparation_and_verification_public_contracts_are_pathless() -> None:
    api = _snapshot()
    expected_signatures = {
        "prepare_korean_foundation_snapshot_from_receipt": (
            "expected_receipt_sha256",
        ),
        "verify_prepared_korean_foundation_snapshot": (
            "expected_receipt_sha256",
        ),
        "korean_foundation_activation_authorization_sha256": (
            "receipt_sha256",
            "bundle_sha256",
            "snapshot_manifest_sha256",
            "snapshot_root_sha256",
            "active_prestate_sha256",
        ),
    }
    for name, expected in expected_signatures.items():
        assert tuple(inspect.signature(getattr(api, name)).parameters) == expected
        assert not any(
            token in parameter.casefold()
            for parameter in expected
            for token in (
                "path",
                "root_path",
                "source",
                "url",
                "archive",
                "hook",
                "barrier",
            )
        )
    source = inspect.getsource(api).casefold()
    for forbidden in (
        "os.environ",
        "getenv(",
        "http://",
        "https://",
        "requests.",
        "allow_unapproved",
        "public_stage_hook",
        "before_replace_hook",
    ):
        assert forbidden not in source


def test_prepare_validation_order_is_lock_then_reads_then_recovery_then_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)
    api = state.api
    events: list[str] = []
    original_lock = api._korean_foundation_state_lock
    original_validate = api._validate_preparation_state
    original_recover = api._recover_stale_stages
    original_stage = api._stage_prepared_snapshot

    @contextmanager
    def traced_lock(root: Path) -> Iterator[None]:
        events.append("lock-enter")
        with original_lock(root):
            yield
        events.append("lock-exit")

    def traced_validate(*args: object, **kwargs: object) -> object:
        events.append("validation-start")
        value = original_validate(*args, **kwargs)
        events.append("validation-complete")
        return value

    def traced_recover(*args: object, **kwargs: object) -> object:
        events.append("recovery")
        return original_recover(*args, **kwargs)

    def traced_stage(*args: object, **kwargs: object) -> object:
        events.append("stage")
        return original_stage(*args, **kwargs)

    monkeypatch.setattr(api, "_korean_foundation_state_lock", traced_lock)
    monkeypatch.setattr(api, "_validate_preparation_state", traced_validate)
    monkeypatch.setattr(api, "_recover_stale_stages", traced_recover)
    monkeypatch.setattr(api, "_stage_prepared_snapshot", traced_stage)

    api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )

    assert events == [
        "lock-enter",
        "validation-start",
        "validation-complete",
        "recovery",
        "stage",
        "lock-exit",
    ]


@pytest.mark.parametrize(
    "drift_case",
    [
        "receipt",
        "confirmed-index",
        "reviewer",
        "rights",
        "media",
        "candidate-source",
        "active-prestate",
    ],
)
def test_prepare_zero_write_drift_preserves_stale_stages_and_every_path(
    drift_case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)
    evidence = state.evidence
    stale = state.paths.snapshot_root / ".staging-stale-before-drift"
    stale.mkdir(parents=True)
    (stale / "partial.bin").write_bytes(b"STALE-STAGE-MUST-SURVIVE")
    if drift_case == "receipt":
        evidence.receipt_path.write_bytes(evidence.receipt_path.read_bytes() + b" ")
    elif drift_case == "confirmed-index":
        evidence.index_path.write_bytes(evidence.index_path.read_bytes() + b" ")
    elif drift_case == "reviewer":
        path = evidence.inbox / "reviewers" / "portuguese.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "rights":
        path = evidence.inbox / "rights.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "media":
        path = evidence.inbox / "media" / "hangul-audio-0001.wav"
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "candidate-source":
        path = state.paths.candidate_dir / "hangul-v1.json"
        path.write_bytes(path.read_bytes() + b" ")
    else:
        evidence.active_pointer.write_bytes(_valid_pointer_bytes())
    before = _tree_state(evidence.project_root)

    with pytest.raises(state.api.KoreanFoundationSnapshotError):
        state.api.prepare_korean_foundation_snapshot_from_receipt(
            expected_receipt_sha256=state.receipt_sha256
        )

    assert _tree_state(evidence.project_root) == before
    assert stale.is_dir()


def test_prepare_recovers_only_safe_stages_and_builds_exact_immutable_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)
    stale = state.paths.snapshot_root / ".staging-safe-unreferenced"
    stale.mkdir(parents=True)
    (stale / "partial.bin").write_bytes(b"safe stale fixture")
    unrelated = state.paths.snapshot_root / "leave-unrelated-alone"
    unrelated.mkdir()
    (unrelated / "sentinel.bin").write_bytes(b"unchanged")
    fsync_calls = 0
    original_fsync = state.api._fsync_descriptor

    def counted_fsync(descriptor: int) -> None:
        nonlocal fsync_calls
        fsync_calls += 1
        original_fsync(descriptor)

    monkeypatch.setattr(state.api, "_fsync_descriptor", counted_fsync)
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )

    target = state.paths.snapshot_root / prepared.bundle_sha256
    manifest_path = target / "snapshot-manifest.json"
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw.decode("utf-8"))
    actual_files = {
        path.relative_to(target).as_posix()
        for path in target.rglob("*")
        if path.is_file()
    }
    assert prepared.snapshot_contract_version == (
        "phase31-korean-foundation-snapshot-v2"
    )
    assert prepared.receipt_sha256 == state.receipt_sha256
    assert prepared.bundle_sha256 == target.name
    assert prepared.snapshot_manifest_sha256 == sha256(manifest_raw).hexdigest()
    assert prepared.snapshot_root_sha256 == manifest["snapshot_root_sha256"]
    assert prepared.member_count == 527
    assert prepared.media_member_count == 509
    assert len(actual_files) == 528
    assert actual_files == {
        "snapshot-manifest.json",
        *(member["relpath"] for member in manifest["members"]),
    }
    assert stale.exists() is False
    assert (unrelated / "sentinel.bin").read_bytes() == b"unchanged"
    assert not tuple(state.paths.snapshot_root.glob(".staging-*"))
    assert fsync_calls >= prepared.member_count + 1
    assert state.paths.active_pointer.exists() is False


def test_recovery_rejects_uncontained_same_named_snapshot_directory(
    tmp_path: Path,
) -> None:
    api = _snapshot()
    fixed_snapshot_root = tmp_path / "fixed" / "snapshots"
    fixed_snapshot_root.mkdir(parents=True)
    outside = tmp_path / "attacker" / "snapshots" / ".staging-outside"
    outside.mkdir(parents=True)
    (outside / "sentinel.bin").write_bytes(b"never delete outside fixed root")
    value = outside.lstat()
    stage = api._StaleStage(
        path=outside,
        device=value.st_dev,
        inode=value.st_ino,
    )

    with pytest.raises(api.KoreanFoundationSnapshotError):
        api._recover_stale_stages((stage,), snapshot_root=fixed_snapshot_root)

    assert (outside / "sentinel.bin").read_bytes() == (
        b"never delete outside fixed root"
    )


def test_prepare_exact_immutable_retry_is_no_write_and_collision_is_never_overwritten(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    stale = state.paths.snapshot_root / ".staging-preserved-on-exact-retry"
    stale.mkdir()
    (stale / "sentinel.bin").write_bytes(b"do-not-recover")
    before_retry = _tree_state(state.evidence.project_root)

    retry = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    assert retry == prepared
    assert _tree_state(state.evidence.project_root) == before_retry
    assert stale.is_dir()

    target = state.paths.snapshot_root / prepared.bundle_sha256
    collision_member = target / "content" / "hangul-v1.json"
    collision_member.write_bytes(collision_member.read_bytes() + b"collision")
    before_collision = _tree_state(state.evidence.project_root)
    with pytest.raises(state.api.KoreanFoundationSnapshotError) as exc_info:
        state.api.prepare_korean_foundation_snapshot_from_receipt(
            expected_receipt_sha256=state.receipt_sha256
        )
    assert _reason(exc_info) == "immutable_snapshot_collision"
    assert _tree_state(state.evidence.project_root) == before_collision
    assert stale.is_dir()


@pytest.mark.parametrize(
    "failure_helper",
    [
        "_copy_member_to_stage",
        "_write_manifest_to_stage",
        "_validate_staged_snapshot",
        "_fsync_descriptor",
        "_rename_snapshot_stage",
    ],
)
def test_injected_prepare_failure_removes_only_its_failed_stage(
    failure_helper: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)

    def fail(*_args: object, **_kwargs: object) -> None:
        raise OSError(f"fixture-only-{failure_helper}")

    monkeypatch.setattr(state.api, failure_helper, fail)
    with pytest.raises(state.api.KoreanFoundationSnapshotError) as exc_info:
        state.api.prepare_korean_foundation_snapshot_from_receipt(
            expected_receipt_sha256=state.receipt_sha256
        )
    assert _reason(exc_info) == "snapshot_preparation_failed"
    assert not tuple(state.paths.snapshot_root.glob(".staging-*"))
    immutable_children = tuple(
        path
        for path in state.paths.snapshot_root.iterdir()
        if path.name != "leave-unrelated-alone"
    ) if state.paths.snapshot_root.exists() else ()
    assert immutable_children == ()
    assert state.paths.active_pointer.exists() is False


def test_verify_prepared_is_strictly_read_only_with_all_write_primitives_poisoned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    before = _tree_state(state.evidence.project_root)
    _poison_snapshot_write_primitives(state.api, state.evidence_api, monkeypatch)

    report = state.api.verify_prepared_korean_foundation_snapshot(
        expected_receipt_sha256=state.receipt_sha256
    )

    assert report.prepared is True
    assert report.receipt_sha256 == prepared.receipt_sha256
    assert report.bundle_sha256 == prepared.bundle_sha256
    assert report.snapshot_manifest_sha256 == prepared.snapshot_manifest_sha256
    assert report.snapshot_root_sha256 == prepared.snapshot_root_sha256
    assert report.active_prestate_sha256 == state.receipt.active_prestate_sha256
    assert report.authorization_sha256 == (
        state.api.korean_foundation_activation_authorization_sha256(
            receipt_sha256=report.receipt_sha256,
            bundle_sha256=report.bundle_sha256,
            snapshot_manifest_sha256=report.snapshot_manifest_sha256,
            snapshot_root_sha256=report.snapshot_root_sha256,
            active_prestate_sha256=report.active_prestate_sha256,
        )
    )
    assert _tree_state(state.evidence.project_root) == before
    verifier_source = inspect.getsource(
        state.api.verify_prepared_korean_foundation_snapshot
    )
    for forbidden_call in (
        "prepare_korean_foundation_snapshot_from_receipt(",
        "activate_prepared_korean_foundation_snapshot_from_receipt(",
        "_recover_stale_stages(",
        "_korean_foundation_state_lock(",
    ):
        assert forbidden_call not in verifier_source


@pytest.mark.parametrize(
    "drift_case",
    [
        "missing-member",
        "source-member",
        "media-member",
        "manifest-file",
        "root-extra",
        "manifest-tuple",
        "root-hash",
        "receipt",
        "active-prestate",
    ],
)
def test_verify_prepared_drift_fails_read_only_with_tree_byte_identical(
    drift_case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    target = state.paths.snapshot_root / prepared.bundle_sha256
    manifest_path = target / "snapshot-manifest.json"
    if drift_case == "missing-member":
        (target / "review" / "rights.json").unlink()
    elif drift_case == "source-member":
        path = target / "content" / "hangul-v1.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "media-member":
        path = next(
            candidate
            for candidate in (target / "media").rglob("*")
            if candidate.is_file()
        )
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "manifest-file":
        manifest_path.write_bytes(manifest_path.read_bytes() + b" ")
    elif drift_case == "root-extra":
        (target / "review" / "unmanifested.json").write_bytes(b"{}\n")
    elif drift_case in {"manifest-tuple", "root-hash"}:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if drift_case == "manifest-tuple":
            payload["active_prestate_sha256"] = "7" * 64
        else:
            payload["snapshot_root_sha256"] = "6" * 64
        payload["bundle_sha256"] = _bundle_sha256(payload)
        manifest_path.write_bytes(
            (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
        )
    elif drift_case == "receipt":
        state.evidence.receipt_path.write_bytes(
            state.evidence.receipt_path.read_bytes() + b" "
        )
    else:
        state.evidence.active_pointer.write_bytes(_valid_pointer_bytes())
    before = _tree_state(state.evidence.project_root)
    _poison_snapshot_write_primitives(state.api, state.evidence_api, monkeypatch)

    with pytest.raises(state.api.KoreanFoundationSnapshotError):
        state.api.verify_prepared_korean_foundation_snapshot(
            expected_receipt_sha256=state.receipt_sha256
        )

    assert _tree_state(state.evidence.project_root) == before


def test_verify_prepared_rechecks_prestate_after_final_snapshot_reread(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)
    state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    original_verify = state.api._verify_snapshot_tree
    calls = 0

    def drift_after_final_snapshot_read(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        result = original_verify(*args, **kwargs)
        if calls == 2:
            state.paths.active_pointer.write_bytes(_valid_pointer_bytes("6"))
        return result

    monkeypatch.setattr(
        state.api,
        "_verify_snapshot_tree",
        drift_after_final_snapshot_read,
    )
    with pytest.raises(state.api.KoreanFoundationSnapshotError):
        state.api.verify_prepared_korean_foundation_snapshot(
            expected_receipt_sha256=state.receipt_sha256
        )


def test_activation_and_active_provenance_contracts_are_pathless() -> None:
    api = _snapshot()
    expected = {
        "activate_prepared_korean_foundation_snapshot_from_receipt": (
            "expected_receipt_sha256",
            "authorization_sha256",
        ),
        "verify_active_korean_foundation_snapshot_provenance": (
            "expected_receipt_sha256",
        ),
    }
    for name, parameters in expected.items():
        assert tuple(inspect.signature(getattr(api, name)).parameters) == parameters
        assert not any(
            token in parameter.casefold()
            for parameter in parameters
            for token in ("path", "root", "url", "archive", "hook", "barrier")
        )


def test_activation_authorization_binds_every_prepared_hash() -> None:
    api = _snapshot()
    values = {
        "receipt_sha256": "1" * 64,
        "bundle_sha256": "2" * 64,
        "snapshot_manifest_sha256": "3" * 64,
        "snapshot_root_sha256": "4" * 64,
        "active_prestate_sha256": "5" * 64,
    }
    expected = api.korean_foundation_activation_authorization_sha256(**values)
    assert len(expected) == 64
    for field_name in values:
        changed = dict(values)
        changed[field_name] = "f" * 64
        assert (
            api.korean_foundation_activation_authorization_sha256(**changed)
            != expected
        )


def test_activation_order_is_lock_then_complete_validation_then_recovery_then_pointer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    stale = state.paths.snapshot_root / ".staging-activation-order"
    stale.mkdir()
    events: list[str] = []
    original_lock = state.api._korean_foundation_state_lock
    original_validate = state.api._validate_activation_state
    original_recover = state.api._recover_stale_stages
    original_pointer = state.api._atomic_activate_pointer

    @contextmanager
    def traced_lock(root: Path) -> Iterator[None]:
        events.append("lock-enter")
        with original_lock(root):
            yield
        events.append("lock-exit")

    def traced_validate(*args: object, **kwargs: object) -> object:
        events.append("validation-start")
        value = original_validate(*args, **kwargs)
        events.append("validation-complete")
        return value

    def traced_recover(*args: object, **kwargs: object) -> object:
        events.append("recovery")
        return original_recover(*args, **kwargs)

    def traced_pointer(*args: object, **kwargs: object) -> object:
        events.append("pointer-write")
        return original_pointer(*args, **kwargs)

    monkeypatch.setattr(state.api, "_korean_foundation_state_lock", traced_lock)
    monkeypatch.setattr(state.api, "_validate_activation_state", traced_validate)
    monkeypatch.setattr(state.api, "_recover_stale_stages", traced_recover)
    monkeypatch.setattr(state.api, "_atomic_activate_pointer", traced_pointer)
    state.api.activate_prepared_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256,
        authorization_sha256=prepared.authorization_sha256,
    )

    assert events == [
        "lock-enter",
        "validation-start",
        "validation-complete",
        "recovery",
        "pointer-write",
        "lock-exit",
    ]


@pytest.mark.parametrize(
    "drift_case",
    [
        "receipt",
        "confirmed-index",
        "reviewer",
        "rights",
        "media",
        "snapshot-member",
        "snapshot-manifest",
        "authorization",
        "active-prestate",
    ],
)
def test_activation_zero_write_drift_leaves_stale_stage_and_all_paths_unchanged(
    drift_case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    stale = state.paths.snapshot_root / ".staging-activation-drift"
    stale.mkdir()
    (stale / "sentinel.bin").write_bytes(b"must remain")
    authorization = prepared.authorization_sha256
    if drift_case == "receipt":
        path = state.evidence.receipt_path
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "confirmed-index":
        path = state.evidence.index_path
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "reviewer":
        path = state.evidence.inbox / "reviewers" / "korean-phonetics.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "rights":
        path = state.evidence.inbox / "rights.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "media":
        path = state.evidence.inbox / "media" / "hangul-audio-0001.wav"
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "snapshot-member":
        path = (
            state.paths.snapshot_root
            / prepared.bundle_sha256
            / "content"
            / "korean-concepts-v1.json"
        )
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "snapshot-manifest":
        path = (
            state.paths.snapshot_root
            / prepared.bundle_sha256
            / "snapshot-manifest.json"
        )
        path.write_bytes(path.read_bytes() + b" ")
    elif drift_case == "authorization":
        authorization = "f" * 64
    else:
        state.evidence.active_pointer.write_bytes(_valid_pointer_bytes())
    before = _tree_state(state.evidence.project_root)

    with pytest.raises(state.api.KoreanFoundationSnapshotError):
        state.api.activate_prepared_korean_foundation_snapshot_from_receipt(
            expected_receipt_sha256=state.receipt_sha256,
            authorization_sha256=authorization,
        )

    assert _tree_state(state.evidence.project_root) == before
    assert stale.is_dir()


def test_authorized_activation_atomically_publishes_hash_bound_active_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(
        tmp_path,
        monkeypatch,
        with_old_active=True,
    )
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    old_pointer = state.paths.active_pointer.read_bytes()
    stale = state.paths.snapshot_root / ".staging-valid-activation"
    stale.mkdir()
    (stale / "partial.bin").write_bytes(b"recover after validation")

    result = state.api.activate_prepared_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256,
        authorization_sha256=prepared.authorization_sha256,
    )

    new_pointer = state.paths.active_pointer.read_bytes()
    assert result.activated is True
    assert result.already_active is False
    assert result.authorization_sha256 == prepared.authorization_sha256
    assert result.active_pointer_sha256 == sha256(new_pointer).hexdigest()
    assert new_pointer == _active_pointer_bytes_for(prepared)
    assert new_pointer != old_pointer
    assert stale.exists() is False
    resolved = state.api.resolve_active_korean_foundation_snapshot()
    assert resolved.bundle_sha256 == prepared.bundle_sha256
    assert resolved.receipt_sha256 == state.receipt_sha256
    assert resolved.snapshot_root_sha256 == prepared.snapshot_root_sha256
    assert resolved.authorization_sha256 == prepared.authorization_sha256

    original_read_bytes = Path.read_bytes
    pointer_reads = 0

    def counted_read_bytes(path: Path) -> bytes:
        nonlocal pointer_reads
        if path == state.paths.active_pointer:
            pointer_reads += 1
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", counted_read_bytes)
    state.api.resolve_active_korean_foundation_snapshot()
    assert pointer_reads == 1


@pytest.mark.parametrize(
    "failure_helper",
    [
        "_write_pointer_temp",
        "_fsync_descriptor",
        "_replace_active_pointer",
        "_fsync_directory",
    ],
)
def test_injected_activation_failure_leaves_complete_old_or_new_pointer(
    failure_helper: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(
        tmp_path,
        monkeypatch,
        with_old_active=True,
    )
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    old_pointer = state.paths.active_pointer.read_bytes()
    new_pointer = _active_pointer_bytes_for(prepared)

    def fail(*_args: object, **_kwargs: object) -> None:
        raise OSError(f"fixture-only-{failure_helper}")

    monkeypatch.setattr(state.api, failure_helper, fail)
    with pytest.raises(state.api.KoreanFoundationSnapshotError) as exc_info:
        state.api.activate_prepared_korean_foundation_snapshot_from_receipt(
            expected_receipt_sha256=state.receipt_sha256,
            authorization_sha256=prepared.authorization_sha256,
        )
    assert _reason(exc_info) == "activation_failed"
    actual_pointer = state.paths.active_pointer.read_bytes()
    assert actual_pointer in {old_pointer, new_pointer}
    resolved = state.api.resolve_active_korean_foundation_snapshot()
    assert resolved.bundle_sha256 in {
        state.old_bundle_sha256,
        prepared.bundle_sha256,
    }
    assert not tuple(state.paths.candidate_dir.glob(".active-foundations.*.tmp"))


def test_abrupt_termination_before_pointer_replace_preserves_exact_old_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(
        tmp_path,
        monkeypatch,
        with_old_active=True,
    )
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    old_pointer = state.paths.active_pointer.read_bytes()
    worker = Path(__file__).parents[1] / "helpers" / (
        "korean_foundation_activation_worker.py"
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(worker),
            str(state.evidence.project_root),
            state.receipt_sha256,
            prepared.authorization_sha256,
        ],
        check=False,
        capture_output=True,
        timeout=30,
    )

    assert completed.returncode == 91
    assert state.paths.active_pointer.read_bytes() == old_pointer
    assert state.api.resolve_active_korean_foundation_snapshot().bundle_sha256 == (
        state.old_bundle_sha256
    )


def _resolved_identity(resolved: object) -> tuple[object, ...]:
    manifest = getattr(resolved, "manifest")
    members = getattr(resolved, "members")
    return (
        getattr(resolved, "bundle_sha256"),
        manifest.bundle_sha256,
        getattr(resolved, "snapshot_manifest_sha256"),
        getattr(resolved, "snapshot_root").name,
        tuple((member.relpath, member.sha256) for member in members),
    )


def test_concurrent_readers_observe_complete_old_or_new_snapshot_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(
        tmp_path,
        monkeypatch,
        with_old_active=True,
    )
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    old_identity = _resolved_identity(
        state.api.resolve_active_korean_foundation_snapshot()
    )
    before_replace = threading.Event()
    release_replace = threading.Event()
    stop_readers = threading.Event()
    original_replace = state.api._replace_active_pointer
    observations: list[tuple[object, ...]] = []
    reader_failures: list[BaseException] = []
    activation_failures: list[BaseException] = []

    def paused_replace(temporary_path: Path, pointer_path: Path) -> None:
        before_replace.set()
        if not release_replace.wait(30):
            raise TimeoutError("fixture-only activation barrier timed out")
        original_replace(temporary_path, pointer_path)

    def reader_loop() -> None:
        while not stop_readers.is_set():
            try:
                observations.append(
                    _resolved_identity(
                        state.api.resolve_active_korean_foundation_snapshot()
                    )
                )
            except BaseException as exc:  # noqa: BLE001 - captured for assertion
                reader_failures.append(exc)
                return

    def activate() -> None:
        try:
            state.api.activate_prepared_korean_foundation_snapshot_from_receipt(
                expected_receipt_sha256=state.receipt_sha256,
                authorization_sha256=prepared.authorization_sha256,
            )
        except BaseException as exc:  # noqa: BLE001 - captured for assertion
            activation_failures.append(exc)

    monkeypatch.setattr(state.api, "_replace_active_pointer", paused_replace)
    reader = threading.Thread(target=reader_loop, daemon=True)
    activation = threading.Thread(target=activate, daemon=True)
    activation.start()
    if not before_replace.wait(20):
        stop_readers.set()
        activation.join(20)
        activation_error_chain = [
            (repr(value), repr(value.__cause__))
            for value in activation_failures
        ]
        pytest.fail(
            "activation did not reach replacement; "
            f"activation_alive={activation.is_alive()} "
            f"activation_failures={activation_error_chain!r} "
            f"reader_failures={reader_failures!r} "
            f"observations={len(observations)}"
        )
    reader.start()
    deadline = time.monotonic() + 10
    while old_identity not in observations and time.monotonic() < deadline:
        time.sleep(0.01)
    assert old_identity in observations
    release_replace.set()
    activation.join(20)
    assert activation.is_alive() is False
    new_identity = _resolved_identity(
        state.api.resolve_active_korean_foundation_snapshot()
    )
    deadline = time.monotonic() + 20
    while new_identity not in observations and time.monotonic() < deadline:
        time.sleep(0.01)
    stop_readers.set()
    reader.join(20)

    assert reader_failures == []
    assert activation_failures == []
    assert reader.is_alive() is False
    assert new_identity in observations
    assert set(observations) == {old_identity, new_identity}


def test_idempotent_activation_and_active_provenance_are_no_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    first = state.api.activate_prepared_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256,
        authorization_sha256=prepared.authorization_sha256,
    )
    report = state.api.verify_active_korean_foundation_snapshot_provenance(
        expected_receipt_sha256=state.receipt_sha256
    )
    assert report.active is True
    assert report.active_pointer_sha256 == first.active_pointer_sha256
    assert report.authorization_sha256 == prepared.authorization_sha256

    stale = state.paths.snapshot_root / ".staging-idempotent-activation"
    stale.mkdir()
    (stale / "sentinel.bin").write_bytes(b"do not recover")
    before = _tree_state(state.evidence.project_root)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("idempotent activation attempted a write or recovery")

    monkeypatch.setattr(state.api, "_recover_stale_stages", forbidden)
    monkeypatch.setattr(state.api, "_atomic_activate_pointer", forbidden)
    retry = state.api.activate_prepared_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256,
        authorization_sha256=prepared.authorization_sha256,
    )
    assert retry.activated is False
    assert retry.already_active is True
    assert retry.active_pointer_sha256 == first.active_pointer_sha256
    assert _tree_state(state.evidence.project_root) == before
    assert stale.is_dir()


def test_active_provenance_rejects_pointer_authorization_drift_without_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    state.api.activate_prepared_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256,
        authorization_sha256=prepared.authorization_sha256,
    )
    payload = json.loads(state.paths.active_pointer.read_text(encoding="utf-8"))
    payload["authorization_sha256"] = "f" * 64
    state.paths.active_pointer.write_bytes(
        (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    )
    before = _tree_state(state.evidence.project_root)

    with pytest.raises(state.api.KoreanFoundationSnapshotError):
        state.api.verify_active_korean_foundation_snapshot_provenance(
            expected_receipt_sha256=state.receipt_sha256
        )

    assert _tree_state(state.evidence.project_root) == before


def test_active_provenance_rejects_pointer_drift_during_final_snapshot_reread(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _build_receipted_snapshot_fixture(tmp_path, monkeypatch)
    prepared = state.api.prepare_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256
    )
    state.api.activate_prepared_korean_foundation_snapshot_from_receipt(
        expected_receipt_sha256=state.receipt_sha256,
        authorization_sha256=prepared.authorization_sha256,
    )
    original_verify = state.api._verify_snapshot_tree
    calls = 0

    def drift_after_final_snapshot_read(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        result = original_verify(*args, **kwargs)
        if calls == 2:
            state.paths.active_pointer.write_bytes(_valid_pointer_bytes("7"))
        return result

    monkeypatch.setattr(
        state.api,
        "_verify_snapshot_tree",
        drift_after_final_snapshot_read,
    )
    with pytest.raises(state.api.KoreanFoundationSnapshotError):
        state.api.verify_active_korean_foundation_snapshot_provenance(
            expected_receipt_sha256=state.receipt_sha256
        )


def test_repository_has_no_active_pointer_or_committed_snapshot_tree() -> None:
    api = _snapshot()

    assert not api.ACTIVE_KOREAN_FOUNDATIONS_POINTER_PATH.exists()
    assert not api.KOREAN_FOUNDATION_SNAPSHOT_ROOT.exists()
