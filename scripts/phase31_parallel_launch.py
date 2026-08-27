#!/usr/bin/env python3
"""Prepare and verify the fixed Phase 31 parallel execution boundary."""

from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from typing import Final, Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = Path("/tmp")
BASELINE_ROOT = TMP_ROOT / "multilang-phase31-parallel"
BASELINE_PATH = BASELINE_ROOT / "baseline.json"
BASELINE_SIDECAR_PATH = BASELINE_ROOT / "baseline.json.sha256"
LANE_HEADS_PATH = BASELINE_ROOT / "lane-heads.json"
LANE_HEADS_SIDECAR_PATH = BASELINE_ROOT / "lane-heads.json.sha256"
AI_WORKTREE = TMP_ROOT / "multilang-phase31-ai"
MEDIA_WORKTREE = TMP_ROOT / "multilang-phase31-media"
RUNTIME_PYTHON = TMP_ROOT / "multilang-phase31-py312" / "bin" / "python"
RUNTIME_HELPER_PATH = PROJECT_ROOT / "scripts" / "verify_phase31_runtime_isolation.py"
PHASE_RELPATH: Final = ".planning/phases/31-hangul-and-pronunciation-i-plus-1"
BASELINE_SCHEMA_VERSION: Final = 1
LANE_HEADS_SCHEMA_VERSION: Final = 1
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")

PUBLIC_OPERATIONS: Final = (
    "prepare-baseline",
    "get",
    "verify-baseline",
    "verify-worktree-runtime",
    "record-lane",
    "trusted-baseline-sha256",
    "verify-integration-base",
    "record-lane-head",
    "verify-lane",
    "verify-join",
    "verify-merged-lanes",
    "merge-lanes",
    "verify-protected-state",
)

LANE_ALLOWLISTS: Mapping[str, tuple[str, ...]] = {
    "ai": (
        "src/multilang/services/ai_linguistic_review.py",
        "src/multilang/services/korean_foundation_review.py",
        "scripts/review_korean_foundations_ai.py",
        "tests/services/test_ai_linguistic_review.py",
        "tests/services/test_korean_foundation_review.py",
        f"{PHASE_RELPATH}/evidence-inbox/ai-review/",
        f"{PHASE_RELPATH}/execution-handoffs/ai-lane.json",
    ),
    "media": (
        "src/multilang/services/korean_foundation_media.py",
        "src/multilang/services/ai_acoustic_review.py",
        "scripts/phase31_handoff.py",
        "scripts/build_korean_foundation_media.py",
        "tests/services/test_korean_foundation_media.py",
        "tests/services/test_ai_acoustic_review.py",
        "tests/services/test_korean_foundation_media_build.py",
        "tests/services/test_phase31_handoff.py",
        f"{PHASE_RELPATH}/evidence-inbox/media-rights.json",
        f"{PHASE_RELPATH}/evidence-inbox/media/",
        f"{PHASE_RELPATH}/evidence-inbox/acoustic-review.json",
        f"{PHASE_RELPATH}/execution-handoffs/media-authority.json",
        f"{PHASE_RELPATH}/execution-handoffs/media-lane.json",
    ),
}
LANE_HANDOFF_RELPATHS: Mapping[str, str] = {
    "ai": f"{PHASE_RELPATH}/execution-handoffs/ai-lane.json",
    "media": f"{PHASE_RELPATH}/execution-handoffs/media-lane.json",
}
PROTECTED_PATHS: tuple[str, ...] = (
    "pyproject.toml",
    "uv.lock",
    "data/korean_foundations",
    f"{PHASE_RELPATH}/evidence-inbox/README.md",
    f"{PHASE_RELPATH}/execution-handoffs/curation-selection.json",
    ".multilang/exports/korean-foundations",
)
PROTECTED_ALLOW_CATEGORIES: Mapping[str, tuple[str, ...]] = {
    "staged-closure": (".planning/.local/phase31-staged-closure",),
    "receipt": (f"{PHASE_RELPATH}/evidence-inbox/validation-receipt.json",),
    "snapshot": ("data/korean_foundations/snapshots",),
    "pointer": ("data/korean_foundations/active-foundations.json",),
    "exports": (".multilang/exports/korean-foundations",),
}


class ParallelLaunchError(ValueError):
    """Content-free parallel orchestration failure."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)

    def __str__(self) -> str:
        return self.reason_code


def _raise(reason_code: str) -> None:
    raise ParallelLaunchError(reason_code)


def sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _is_link_or_reparse(metadata: os.stat_result) -> bool:
    if stat.S_ISLNK(metadata.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(getattr(metadata, "st_file_attributes", 0) & reparse_flag)


def _assert_hex(value: str, pattern: re.Pattern[str], reason: str) -> None:
    if not pattern.fullmatch(value):
        _raise(reason)


def _shared_tmp_parent_is_safe(metadata: os.stat_result) -> bool:
    mode = stat.S_IMODE(metadata.st_mode)
    return (
        not _is_link_or_reparse(metadata)
        and stat.S_ISDIR(metadata.st_mode)
        and metadata.st_uid == 0
        and mode & 0o777 == 0o777
        and bool(metadata.st_mode & stat.S_ISVTX)
    )


def _assert_safe_state_root() -> None:
    parent = BASELINE_ROOT.parent
    try:
        parent_metadata = parent.lstat()
    except OSError:
        _raise("parallel_root_unsafe")
    if _is_link_or_reparse(parent_metadata) or not stat.S_ISDIR(parent_metadata.st_mode):
        _raise("parallel_root_unsafe")
    if parent == Path("/tmp"):
        if not _shared_tmp_parent_is_safe(parent_metadata):
            _raise("parallel_root_unsafe")
    elif (
        parent_metadata.st_uid != os.getuid()
        or stat.S_IMODE(parent_metadata.st_mode) & 0o022
    ):
        _raise("parallel_root_unsafe")

    try:
        metadata = BASELINE_ROOT.lstat()
    except FileNotFoundError:
        try:
            BASELINE_ROOT.mkdir(mode=0o700)
        except OSError:
            _raise("parallel_root_create_failed")
        metadata = BASELINE_ROOT.lstat()
    except OSError:
        _raise("parallel_root_unsafe")
    if (
        _is_link_or_reparse(metadata)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        _raise("parallel_root_unsafe")


def _assert_fixed_file(path: Path, expected: Path, mode: int, reason: str) -> None:
    if path != expected:
        _raise(reason)
    try:
        metadata = path.lstat()
    except OSError:
        _raise(reason)
    if (
        _is_link_or_reparse(metadata)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != mode
    ):
        _raise(reason)


def atomic_write(path: Path, content: bytes, *, mode: int) -> None:
    """Atomically replace a file inside the already-validated private state root."""

    if path.parent != BASELINE_ROOT:
        _raise("parallel_path_unsafe")
    _assert_safe_state_root()
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=BASELINE_ROOT
        )
        temporary = Path(temporary_name)
        try:
            os.fchmod(descriptor, mode)
            with os.fdopen(descriptor, "wb", closefd=True) as stream:
                descriptor = -1
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            path.chmod(mode)
            directory_fd = os.open(BASELINE_ROOT, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if temporary.exists():
                temporary.unlink()
    except ParallelLaunchError:
        raise
    except OSError:
        _raise("parallel_write_failed")


def _git(root: Path, *args: str, text: bool = True) -> str | bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            text=text,
            capture_output=True,
            check=False,
        )
    except OSError:
        _raise("git_unavailable")
    if result.returncode != 0:
        _raise("git_operation_failed")
    return result.stdout.strip() if text else result.stdout


def _git_clean(root: Path) -> bool:
    return _git(root, "status", "--porcelain=v1", "--untracked-files=all") == ""


def _git_head(root: Path) -> str:
    head = str(_git(root, "rev-parse", "HEAD"))
    _assert_hex(head, HEX_40, "git_head_invalid")
    return head


def _git_tree(root: Path, revision: str = "HEAD") -> str:
    tree = str(_git(root, "rev-parse", f"{revision}^{{tree}}"))
    _assert_hex(tree, HEX_40, "git_tree_invalid")
    return tree


def _git_is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        _raise("git_operation_failed")
    return result.returncode == 0


def _split_nul(value: bytes) -> set[str]:
    return {item.decode("utf-8") for item in value.split(b"\0") if item}


def _changed_paths(root: Path, baseline_commit: str) -> set[str]:
    changed = _split_nul(
        bytes(_git(root, "diff", "--name-only", "-z", baseline_commit, "--", text=False))
    )
    changed.update(
        _split_nul(bytes(_git(root, "ls-files", "--others", "--exclude-standard", "-z", text=False)))
    )
    return changed


def _committed_changed_paths(root: Path, baseline_commit: str, head: str) -> set[str]:
    return _split_nul(
        bytes(
            _git(
                root,
                "diff",
                "--name-only",
                "-z",
                baseline_commit,
                head,
                "--",
                text=False,
            )
        )
    )


def _path_allowed(path: str, allowlist: Sequence[str]) -> bool:
    for allowed in allowlist:
        prefix = allowed.rstrip("/")
        if path == prefix or path.startswith(f"{prefix}/"):
            return True
    return False


def _assert_disjoint_allowlists() -> None:
    ai = tuple(item.rstrip("/") for item in LANE_ALLOWLISTS["ai"])
    media = tuple(item.rstrip("/") for item in LANE_ALLOWLISTS["media"])
    if any(
        left == right
        or left.startswith(f"{right}/")
        or right.startswith(f"{left}/")
        for left in ai
        for right in media
    ):
        _raise("lane_allowlist_overlap")


def _assert_lane_paths(lane: str, paths: Iterable[str]) -> None:
    if lane not in LANE_ALLOWLISTS:
        _raise("lane_invalid")
    if any(not _path_allowed(path, LANE_ALLOWLISTS[lane]) for path in paths):
        _raise("lane_write_scope_violation")


def _read_regular_no_follow(path: Path, reason: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        before = path.lstat()
        descriptor = os.open(path, flags)
    except OSError:
        _raise(reason)
    try:
        opened = os.fstat(descriptor)
        if (
            _is_link_or_reparse(before)
            or not stat.S_ISREG(opened.st_mode)
            or before.st_dev != opened.st_dev
            or before.st_ino != opened.st_ino
        ):
            _raise(reason)
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        return b"".join(chunks)
    except OSError:
        _raise(reason)
    finally:
        os.close(descriptor)


def _snapshot_path_rows(root: Path, relpath: str) -> list[list[str]]:
    path = root / relpath
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return [[relpath, "absent", "", ""]]
    except OSError:
        _raise("protected_state_unsafe")
    if _is_link_or_reparse(metadata):
        _raise("protected_state_unsafe")
    mode = f"{stat.S_IMODE(metadata.st_mode):04o}"
    if stat.S_ISREG(metadata.st_mode):
        return [[relpath, "file", mode, sha256_bytes(_read_regular_no_follow(path, "protected_state_unsafe"))]]
    if not stat.S_ISDIR(metadata.st_mode):
        _raise("protected_state_unsafe")
    rows = [[relpath, "directory", mode, ""]]
    try:
        entries = sorted(path.iterdir(), key=lambda entry: entry.name)
    except OSError:
        _raise("protected_state_unsafe")
    for entry in entries:
        rows.extend(_snapshot_path_rows(root, entry.relative_to(root).as_posix()))
    return rows


def _allowed_protected_prefixes(categories: Sequence[str]) -> tuple[str, ...]:
    prefixes: list[str] = []
    for category in categories:
        if category not in PROTECTED_ALLOW_CATEGORIES:
            _raise("protected_allow_invalid")
        prefixes.extend(PROTECTED_ALLOW_CATEGORIES[category])
    return tuple(prefix.rstrip("/") for prefix in prefixes)


def _capture_protected(root: Path, categories: Sequence[str] = ()) -> list[list[str]]:
    allowed = _allowed_protected_prefixes(categories)
    rows: list[list[str]] = []
    for relpath in PROTECTED_PATHS:
        rows.extend(_snapshot_path_rows(root, relpath))
    return [
        row
        for row in sorted(rows)
        if not any(row[0] == prefix or row[0].startswith(f"{prefix}/") for prefix in allowed)
    ]


def _load_runtime_helper() -> object:
    spec = importlib.util.spec_from_file_location(
        "_phase31_runtime_fingerprint", RUNTIME_HELPER_PATH
    )
    if spec is None or spec.loader is None:
        _raise("runtime_helper_invalid")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _venv_fingerprint() -> Mapping[str, object]:
    helper = _load_runtime_helper()
    try:
        value = helper.fingerprint_repository_venv()
    except Exception:
        _raise("venv_fingerprint_failed")
    if not isinstance(value, dict) or not HEX_64.fullmatch(str(value.get("tree_sha256", ""))):
        _raise("venv_fingerprint_invalid")
    return value


def _runtime_version() -> str:
    try:
        result = subprocess.run(
            [str(RUNTIME_PYTHON), "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        _raise("runtime_invalid")
    if result.returncode != 0:
        _raise("runtime_invalid")
    return result.stdout.strip()


def _assert_python_312(version: str) -> None:
    parts = version.split(".")
    if len(parts) != 3 or parts[:2] != ["3", "12"] or not all(
        part.isdigit() for part in parts
    ):
        _raise("runtime_invalid")


def _baseline_document() -> dict[str, object]:
    runtime_version = _runtime_version()
    _assert_python_312(runtime_version)
    return {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "baseline_commit": _git_head(PROJECT_ROOT),
        "baseline_tree": _git_tree(PROJECT_ROOT),
        "runtime_python": str(RUNTIME_PYTHON),
        "runtime_version": runtime_version,
        "venv_fingerprint": dict(_venv_fingerprint()),
        "lane_allowlists": {
            lane: list(paths) for lane, paths in sorted(LANE_ALLOWLISTS.items())
        },
        "lane_handoff_relpaths": dict(sorted(LANE_HANDOFF_RELPATHS.items())),
        "protected_paths": list(PROTECTED_PATHS),
        "protected_rows": _capture_protected(PROJECT_ROOT),
    }


def prepare_baseline(output: Path | None = None) -> str:
    output = BASELINE_PATH if output is None else output
    if output != BASELINE_PATH:
        _raise("baseline_path_invalid")
    if not _git_clean(PROJECT_ROOT):
        _raise("integration_dirty")
    _assert_disjoint_allowlists()
    _assert_safe_state_root()
    try:
        if any(BASELINE_ROOT.iterdir()):
            _raise("baseline_exists")
    except OSError:
        _raise("parallel_root_unsafe")
    content = canonical_json_bytes(_baseline_document())
    digest = sha256_bytes(content)
    atomic_write(BASELINE_PATH, content, mode=0o444)
    atomic_write(BASELINE_SIDECAR_PATH, f"{digest}\n".encode("ascii"), mode=0o444)
    return digest


def _read_json_bytes(content: bytes, reason: str) -> dict[str, object]:
    try:
        value = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError):
        _raise(reason)
    if not isinstance(value, dict):
        _raise(reason)
    return value


def verify_baseline(path: Path, expected_sha256: str) -> dict[str, object]:
    _assert_hex(expected_sha256, HEX_64, "baseline_digest_invalid")
    _assert_safe_state_root()
    _assert_fixed_file(path, BASELINE_PATH, 0o444, "baseline_file_unsafe")
    _assert_fixed_file(
        BASELINE_SIDECAR_PATH,
        BASELINE_SIDECAR_PATH,
        0o444,
        "baseline_sidecar_unsafe",
    )
    content = _read_regular_no_follow(path, "baseline_file_unsafe")
    if sha256_bytes(content) != expected_sha256:
        _raise("baseline_digest_mismatch")
    sidecar = _read_regular_no_follow(
        BASELINE_SIDECAR_PATH, "baseline_sidecar_unsafe"
    ).decode("ascii", errors="strict").strip()
    if sidecar != expected_sha256:
        _raise("baseline_sidecar_mismatch")
    document = _read_json_bytes(content, "baseline_invalid")
    required = {
        "schema_version",
        "baseline_commit",
        "baseline_tree",
        "runtime_python",
        "runtime_version",
        "venv_fingerprint",
        "lane_allowlists",
        "lane_handoff_relpaths",
        "protected_paths",
        "protected_rows",
    }
    if set(document) != required or document["schema_version"] != BASELINE_SCHEMA_VERSION:
        _raise("baseline_invalid")
    _assert_hex(str(document["baseline_commit"]), HEX_40, "baseline_invalid")
    _assert_hex(str(document["baseline_tree"]), HEX_40, "baseline_invalid")
    expected_allowlists = {
        lane: list(paths) for lane, paths in sorted(LANE_ALLOWLISTS.items())
    }
    if document["lane_allowlists"] != expected_allowlists:
        _raise("baseline_allowlist_mismatch")
    if document["lane_handoff_relpaths"] != dict(sorted(LANE_HANDOFF_RELPATHS.items())):
        _raise("baseline_handoff_mismatch")
    if document["protected_paths"] != list(PROTECTED_PATHS):
        _raise("baseline_protected_paths_mismatch")
    if document["runtime_python"] != str(RUNTIME_PYTHON):
        _raise("runtime_invalid")
    _assert_python_312(str(document["runtime_version"]))
    return document


def get_baseline_field(path: Path, expected_sha256: str, field: str) -> object:
    document = verify_baseline(path, expected_sha256)
    if field not in document:
        _raise("baseline_field_invalid")
    return document[field]


def _assert_worktree_for_lane(lane: str, worktree: Path) -> None:
    expected = AI_WORKTREE if lane == "ai" else MEDIA_WORKTREE if lane == "media" else None
    if expected is None or worktree != expected:
        _raise("lane_worktree_invalid")


def verify_protected_state(
    allowed_categories: Sequence[str],
    baseline_path: Path,
    baseline_sha256: str,
    *,
    worktree: Path | None = None,
) -> str:
    root = PROJECT_ROOT if worktree is None else worktree
    baseline = verify_baseline(baseline_path, baseline_sha256)
    expected_rows = [
        row
        for row in baseline["protected_rows"]
        if not any(
            row[0] == prefix or row[0].startswith(f"{prefix}/")
            for prefix in _allowed_protected_prefixes(allowed_categories)
        )
    ]
    if _capture_protected(root, allowed_categories) != expected_rows:
        _raise("protected_state_drift")
    if dict(_venv_fingerprint()) != baseline["venv_fingerprint"]:
        _raise("venv_fingerprint_drift")
    return "parallel_protected_state_status=verified"


def verify_worktree_runtime(
    lane: str,
    baseline_path: Path,
    baseline_sha256: str,
    *,
    worktree: Path | None = None,
) -> str:
    root = AI_WORKTREE if lane == "ai" else MEDIA_WORKTREE if lane == "media" else Path()
    if worktree is not None:
        root = worktree
    _assert_worktree_for_lane(lane, root)
    expected_pythonpath = str(root / "src")
    if os.environ.get("PYTHONPATH") != expected_pythonpath:
        _raise("runtime_pythonpath_invalid")
    baseline = verify_baseline(baseline_path, baseline_sha256)
    head = _git_head(root)
    if not _git_is_ancestor(root, str(baseline["baseline_commit"]), head):
        _raise("lane_ancestry_invalid")
    changed = _changed_paths(root, str(baseline["baseline_commit"]))
    _assert_lane_paths(lane, changed)
    verify_protected_state((), baseline_path, baseline_sha256, worktree=root)
    try:
        result = subprocess.run(
            [str(RUNTIME_PYTHON), "-c", "import multilang; print(multilang.__file__)"],
            cwd=root,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        _raise("runtime_invalid")
    if result.returncode != 0:
        _raise("runtime_invalid")
    try:
        imported = Path(result.stdout.strip()).resolve(strict=True)
        expected_root = (root / "src").resolve(strict=True)
        imported.relative_to(expected_root)
    except (OSError, ValueError):
        _raise("runtime_import_mismatch")
    return "parallel_worktree_runtime_status=verified"


def _patch_rows_worktree(
    root: Path, baseline_commit: str, paths: Iterable[str]
) -> list[list[str]]:
    rows: list[list[str]] = []
    for relpath in sorted(paths):
        path = root / relpath
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            rows.append([relpath, "deleted", ""])
            continue
        except OSError:
            _raise("lane_patch_unsafe")
        if _is_link_or_reparse(metadata) or not stat.S_ISREG(metadata.st_mode):
            _raise("lane_patch_unsafe")
        rows.append(
            [
                relpath,
                "file",
                sha256_bytes(_read_regular_no_follow(path, "lane_patch_unsafe")),
            ]
        )
    return rows


def _patch_rows_commit(
    root: Path, baseline_commit: str, head: str, paths: Iterable[str]
) -> list[list[str]]:
    changed = _committed_changed_paths(root, baseline_commit, head)
    rows: list[list[str]] = []
    for relpath in sorted(paths):
        if relpath not in changed:
            _raise("lane_patch_mismatch")
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{head}:{relpath}"],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            rows.append([relpath, "file", sha256_bytes(result.stdout)])
        else:
            rows.append([relpath, "deleted", ""])
    return rows


def _patch_sha(rows: Sequence[Sequence[str]]) -> str:
    return sha256_bytes(canonical_json_bytes(list(rows)))


def _lane_handoff_path(lane: str, root: Path) -> Path:
    try:
        relpath = LANE_HANDOFF_RELPATHS[lane]
    except KeyError:
        _raise("lane_invalid")
    return root / relpath


def _atomic_write_worktree_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        _raise("lane_handoff_unsafe")
    temporary_fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(temporary_fd, 0o600)
        with os.fdopen(temporary_fd, "wb") as stream:
            temporary_fd = -1
            stream.write(canonical_json_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError:
        _raise("lane_handoff_write_failed")
    finally:
        if temporary_fd >= 0:
            os.close(temporary_fd)
        if temporary.exists():
            temporary.unlink()


def record_lane(
    lane: str,
    *,
    worktree: Path,
    baseline_path: Path,
    baseline_sha256: str,
    aggregate_root: str,
    evidence_root: str,
    provider_totals: Mapping[str, int] | None = None,
) -> dict[str, object]:
    _assert_worktree_for_lane(lane, worktree)
    _assert_hex(aggregate_root, HEX_64, "lane_root_invalid")
    _assert_hex(evidence_root, HEX_64, "lane_root_invalid")
    baseline = verify_baseline(baseline_path, baseline_sha256)
    baseline_commit = str(baseline["baseline_commit"])
    head = _git_head(worktree)
    if not _git_is_ancestor(worktree, baseline_commit, head):
        _raise("lane_ancestry_invalid")
    changed = _changed_paths(worktree, baseline_commit)
    handoff_relpath = LANE_HANDOFF_RELPATHS[lane]
    changed.discard(handoff_relpath)
    _assert_lane_paths(lane, changed)
    verify_protected_state((), baseline_path, baseline_sha256, worktree=worktree)
    rows = _patch_rows_worktree(worktree, baseline_commit, changed)
    handoff: dict[str, object] = {
        "schema_version": 1,
        "lane": lane,
        "baseline_sha256": baseline_sha256,
        "baseline_commit": baseline_commit,
        "baseline_tree": baseline["baseline_tree"],
        "changed_paths": sorted(changed),
        "patch_sha256": _patch_sha(rows),
        "aggregate_root": aggregate_root,
        "evidence_root": evidence_root,
        "provider_totals": dict(sorted((provider_totals or {}).items())),
    }
    _validate_lane_handoff(handoff, lane, baseline_sha256, baseline)
    _atomic_write_worktree_json(_lane_handoff_path(lane, worktree), handoff)
    return handoff


def _validate_lane_handoff(
    handoff: Mapping[str, object],
    lane: str,
    baseline_sha256: str,
    baseline: Mapping[str, object],
) -> None:
    required = {
        "schema_version",
        "lane",
        "baseline_sha256",
        "baseline_commit",
        "baseline_tree",
        "changed_paths",
        "patch_sha256",
        "aggregate_root",
        "evidence_root",
        "provider_totals",
    }
    if set(handoff) != required or handoff.get("schema_version") != 1:
        _raise("lane_handoff_invalid")
    if (
        handoff.get("lane") != lane
        or handoff.get("baseline_sha256") != baseline_sha256
        or handoff.get("baseline_commit") != baseline.get("baseline_commit")
        or handoff.get("baseline_tree") != baseline.get("baseline_tree")
    ):
        _raise("lane_handoff_mismatch")
    changed_paths = handoff.get("changed_paths")
    if (
        not isinstance(changed_paths, list)
        or any(not isinstance(path, str) for path in changed_paths)
        or changed_paths != sorted(set(changed_paths))
    ):
        _raise("lane_handoff_invalid")
    for field in ("patch_sha256", "aggregate_root", "evidence_root"):
        value = handoff.get(field)
        if not isinstance(value, str) or not HEX_64.fullmatch(value):
            _raise("lane_handoff_invalid")
    provider_totals = handoff.get("provider_totals")
    if not isinstance(provider_totals, dict) or any(
        not isinstance(key, str)
        or not key
        or isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        for key, value in provider_totals.items()
    ):
        _raise("lane_handoff_invalid")


def _read_worktree_handoff(lane: str, root: Path) -> dict[str, object]:
    content = _read_regular_no_follow(
        _lane_handoff_path(lane, root), "lane_handoff_unsafe"
    )
    handoff = _read_json_bytes(content, "lane_handoff_invalid")
    if content != canonical_json_bytes(handoff):
        _raise("lane_handoff_invalid")
    return handoff


def verify_lane(
    lane: str,
    baseline_path: Path,
    baseline_sha256: str,
    *,
    worktree: Path | None = None,
) -> dict[str, object]:
    root = AI_WORKTREE if lane == "ai" else MEDIA_WORKTREE if lane == "media" else Path()
    if worktree is not None:
        root = worktree
    _assert_worktree_for_lane(lane, root)
    baseline = verify_baseline(baseline_path, baseline_sha256)
    handoff = _read_worktree_handoff(lane, root)
    _validate_lane_handoff(handoff, lane, baseline_sha256, baseline)
    changed = _changed_paths(root, str(baseline["baseline_commit"]))
    handoff_relpath = LANE_HANDOFF_RELPATHS[lane]
    if handoff_relpath not in changed:
        _raise("lane_handoff_missing")
    changed.discard(handoff_relpath)
    _assert_lane_paths(lane, changed)
    if sorted(changed) != handoff["changed_paths"]:
        _raise("lane_patch_mismatch")
    rows = _patch_rows_worktree(root, str(baseline["baseline_commit"]), changed)
    if _patch_sha(rows) != handoff["patch_sha256"]:
        _raise("lane_patch_mismatch")
    verify_protected_state((), baseline_path, baseline_sha256, worktree=root)
    return handoff


def _git_show_json(head: str, relpath: str) -> tuple[dict[str, object], bytes]:
    _assert_hex(head, HEX_40, "lane_head_invalid")
    result = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "show", f"{head}:{relpath}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        _raise("lane_handoff_commit_missing")
    handoff = _read_json_bytes(result.stdout, "lane_handoff_invalid")
    if result.stdout != canonical_json_bytes(handoff):
        _raise("lane_handoff_invalid")
    return handoff, result.stdout


def trusted_baseline_sha256(ai_head: str, media_head: str) -> str:
    ai, _ = _git_show_json(ai_head, LANE_HANDOFF_RELPATHS["ai"])
    media, _ = _git_show_json(media_head, LANE_HANDOFF_RELPATHS["media"])
    ai_sha = str(ai.get("baseline_sha256", ""))
    media_sha = str(media.get("baseline_sha256", ""))
    _assert_hex(ai_sha, HEX_64, "trusted_baseline_invalid")
    if ai_sha != media_sha:
        _raise("trusted_baseline_mismatch")
    return ai_sha


def _lane_heads_document() -> dict[str, object]:
    if not LANE_HEADS_PATH.exists():
        return {"schema_version": LANE_HEADS_SCHEMA_VERSION, "lanes": {}}
    _assert_fixed_file(LANE_HEADS_PATH, LANE_HEADS_PATH, 0o600, "lane_heads_invalid")
    content = _read_regular_no_follow(LANE_HEADS_PATH, "lane_heads_invalid")
    document = _read_json_bytes(content, "lane_heads_invalid")
    if document.get("schema_version") != LANE_HEADS_SCHEMA_VERSION or not isinstance(
        document.get("lanes"), dict
    ):
        _raise("lane_heads_invalid")
    return document


def _write_lane_heads(document: Mapping[str, object]) -> None:
    content = canonical_json_bytes(document)
    atomic_write(LANE_HEADS_PATH, content, mode=0o600)
    atomic_write(
        LANE_HEADS_SIDECAR_PATH,
        f"{sha256_bytes(content)}\n".encode("ascii"),
        mode=0o600,
    )


def record_lane_head(
    lane: str,
    head: str,
    worktree: Path,
    baseline_path: Path,
    baseline_sha256: str,
) -> dict[str, object]:
    _assert_worktree_for_lane(lane, worktree)
    _assert_hex(head, HEX_40, "lane_head_invalid")
    if not _git_clean(worktree) or _git_head(worktree) != head:
        _raise("lane_worktree_dirty")
    baseline = verify_baseline(baseline_path, baseline_sha256)
    if not _git_is_ancestor(worktree, str(baseline["baseline_commit"]), head):
        _raise("lane_ancestry_invalid")
    handoff, handoff_bytes = _git_show_json(head, LANE_HANDOFF_RELPATHS[lane])
    _validate_lane_handoff(handoff, lane, baseline_sha256, baseline)
    changed = _committed_changed_paths(worktree, str(baseline["baseline_commit"]), head)
    handoff_relpath = LANE_HANDOFF_RELPATHS[lane]
    if handoff_relpath not in changed:
        _raise("lane_handoff_commit_missing")
    changed.discard(handoff_relpath)
    _assert_lane_paths(lane, changed)
    if sorted(changed) != handoff.get("changed_paths"):
        _raise("lane_patch_mismatch")
    rows = _patch_rows_commit(
        worktree, str(baseline["baseline_commit"]), head, changed
    )
    if _patch_sha(rows) != handoff.get("patch_sha256"):
        _raise("lane_patch_mismatch")
    record = {
        "head": head,
        "handoff_blob_sha256": sha256_bytes(handoff_bytes),
        "patch_sha256": handoff["patch_sha256"],
        "aggregate_root": handoff["aggregate_root"],
        "evidence_root": handoff["evidence_root"],
    }
    document = _lane_heads_document()
    lanes = dict(document["lanes"])
    lanes[lane] = record
    _write_lane_heads({"schema_version": LANE_HEADS_SCHEMA_VERSION, "lanes": lanes})
    return record


def _verified_lane_head_records(
    baseline_path: Path, baseline_sha256: str
) -> dict[str, dict[str, object]]:
    baseline = verify_baseline(baseline_path, baseline_sha256)
    document = _lane_heads_document()
    lanes = document.get("lanes")
    if not isinstance(lanes, dict) or set(lanes) != {"ai", "media"}:
        _raise("lane_heads_invalid")
    if not LANE_HEADS_SIDECAR_PATH.exists():
        _raise("lane_heads_invalid")
    _assert_fixed_file(
        LANE_HEADS_SIDECAR_PATH,
        LANE_HEADS_SIDECAR_PATH,
        0o600,
        "lane_heads_invalid",
    )
    document_bytes = _read_regular_no_follow(LANE_HEADS_PATH, "lane_heads_invalid")
    sidecar = _read_regular_no_follow(
        LANE_HEADS_SIDECAR_PATH, "lane_heads_invalid"
    ).decode("ascii", errors="strict").strip()
    if sidecar != sha256_bytes(document_bytes):
        _raise("lane_heads_invalid")
    verified: dict[str, dict[str, object]] = {}
    for lane in ("ai", "media"):
        record = lanes.get(lane)
        if not isinstance(record, dict) or set(record) != {
            "head",
            "handoff_blob_sha256",
            "patch_sha256",
            "aggregate_root",
            "evidence_root",
        }:
            _raise("lane_heads_invalid")
        head = str(record["head"])
        handoff, handoff_bytes = _git_show_json(head, LANE_HANDOFF_RELPATHS[lane])
        _validate_lane_handoff(handoff, lane, baseline_sha256, baseline)
        if (
            sha256_bytes(handoff_bytes) != record["handoff_blob_sha256"]
            or handoff.get("patch_sha256") != record["patch_sha256"]
            or handoff.get("aggregate_root") != record["aggregate_root"]
            or handoff.get("evidence_root") != record["evidence_root"]
        ):
            _raise("lane_heads_invalid")
        changed = _committed_changed_paths(
            PROJECT_ROOT, str(baseline["baseline_commit"]), head
        )
        changed.discard(LANE_HANDOFF_RELPATHS[lane])
        _assert_lane_paths(lane, changed)
        rows = _patch_rows_commit(
            PROJECT_ROOT, str(baseline["baseline_commit"]), head, changed
        )
        if _patch_sha(rows) != record["patch_sha256"]:
            _raise("lane_heads_invalid")
        verified[lane] = record
    return verified


def verify_join(baseline_path: Path, baseline_sha256: str) -> str:
    records = _verified_lane_head_records(baseline_path, baseline_sha256)
    trusted = trusted_baseline_sha256(
        str(records["ai"]["head"]), str(records["media"]["head"])
    )
    if trusted != baseline_sha256:
        _raise("trusted_baseline_mismatch")
    return "parallel_join_status=verified"


def verify_integration_base(
    worktree: Path, baseline_path: Path, baseline_sha256: str
) -> str:
    if worktree != PROJECT_ROOT:
        _raise("integration_worktree_invalid")
    baseline = verify_baseline(baseline_path, baseline_sha256)
    if (
        not _git_clean(worktree)
        or _git_head(worktree) != baseline["baseline_commit"]
        or _git_tree(worktree) != baseline["baseline_tree"]
    ):
        _raise("integration_base_mismatch")
    verify_protected_state((), baseline_path, baseline_sha256, worktree=worktree)
    return "parallel_integration_base_status=verified"


def merge_lanes(baseline_path: Path, baseline_sha256: str) -> str:
    verify_join(baseline_path, baseline_sha256)
    verify_integration_base(PROJECT_ROOT, baseline_path, baseline_sha256)
    records = _verified_lane_head_records(baseline_path, baseline_sha256)
    for lane in ("ai", "media"):
        _git(PROJECT_ROOT, "merge", "--no-ff", "--no-edit", str(records[lane]["head"]))
    return "parallel_merge_status=merged"


def verify_merged_lanes(baseline_path: Path, baseline_sha256: str) -> str:
    baseline = verify_baseline(baseline_path, baseline_sha256)
    records = _verified_lane_head_records(baseline_path, baseline_sha256)
    current = _git_head(PROJECT_ROOT)
    if not all(
        _git_is_ancestor(PROJECT_ROOT, str(record["head"]), current)
        for record in records.values()
    ):
        _raise("merged_ancestry_invalid")
    expected_paths: set[str] = set()
    expected_rows: dict[str, list[str]] = {}
    for lane, record in records.items():
        head = str(record["head"])
        paths = _committed_changed_paths(
            PROJECT_ROOT, str(baseline["baseline_commit"]), head
        )
        for path in paths:
            if path in expected_paths:
                _raise("merged_paths_overlap")
            expected_paths.add(path)
        for row in _patch_rows_commit(
            PROJECT_ROOT, str(baseline["baseline_commit"]), head, paths
        ):
            expected_rows[row[0]] = row
    actual_paths = _committed_changed_paths(
        PROJECT_ROOT, str(baseline["baseline_commit"]), current
    )
    if actual_paths != expected_paths:
        _raise("merged_diff_invalid")
    actual_rows = {
        row[0]: row
        for row in _patch_rows_commit(
            PROJECT_ROOT,
            str(baseline["baseline_commit"]),
            current,
            actual_paths,
        )
    }
    if actual_rows != expected_rows:
        _raise("merged_diff_invalid")
    verify_protected_state((), baseline_path, baseline_sha256)
    return "parallel_merged_status=verified"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=True)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    prepare = subparsers.add_parser("prepare-baseline")
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--print-sha256", action="store_true")
    get = subparsers.add_parser("get")
    get.add_argument("--field", required=True)
    _add_baseline_args(get)
    verify = subparsers.add_parser("verify-baseline")
    _add_baseline_args(verify)
    worktree = subparsers.add_parser("verify-worktree-runtime")
    worktree.add_argument("--lane", choices=("ai", "media"), required=True)
    _add_baseline_args(worktree)
    record = subparsers.add_parser("record-lane")
    record.add_argument("--lane", choices=("ai", "media"), required=True)
    record.add_argument("--aggregate-root", required=True)
    record.add_argument("--evidence-root", required=True)
    _add_baseline_args(record)
    trusted = subparsers.add_parser("trusted-baseline-sha256")
    trusted.add_argument("--ai-head", required=True)
    trusted.add_argument("--media-head", required=True)
    integration = subparsers.add_parser("verify-integration-base")
    integration.add_argument("--worktree", type=Path, required=True)
    _add_baseline_args(integration)
    head = subparsers.add_parser("record-lane-head")
    head.add_argument("--lane", choices=("ai", "media"), required=True)
    head.add_argument("--head", required=True)
    head.add_argument("--worktree", type=Path, required=True)
    _add_baseline_args(head)
    lane = subparsers.add_parser("verify-lane")
    lane.add_argument("--lane", choices=("ai", "media"), required=True)
    _add_baseline_args(lane)
    for operation in ("verify-join", "verify-merged-lanes", "merge-lanes"):
        command = subparsers.add_parser(operation)
        _add_baseline_args(command)
    protected = subparsers.add_parser("verify-protected-state")
    protected.add_argument("--allow", default="")
    _add_baseline_args(protected)
    return parser


def _add_baseline_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--baseline-sha256", required=True)


def _print_json_or_scalar(value: object) -> None:
    if isinstance(value, (dict, list)):
        print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print(value)


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(sys.argv[1:] if argv is None else argv)
        operation = args.operation
        if operation == "prepare-baseline":
            digest = prepare_baseline(args.output)
            print(digest if args.print_sha256 else "parallel_baseline_status=prepared")
        elif operation == "get":
            _print_json_or_scalar(
                get_baseline_field(args.baseline, args.baseline_sha256, args.field)
            )
        elif operation == "verify-baseline":
            verify_baseline(args.baseline, args.baseline_sha256)
            print("parallel_baseline_status=verified")
        elif operation == "verify-worktree-runtime":
            print(verify_worktree_runtime(args.lane, args.baseline, args.baseline_sha256))
        elif operation == "record-lane":
            root = AI_WORKTREE if args.lane == "ai" else MEDIA_WORKTREE
            record_lane(
                args.lane,
                worktree=root,
                baseline_path=args.baseline,
                baseline_sha256=args.baseline_sha256,
                aggregate_root=args.aggregate_root,
                evidence_root=args.evidence_root,
            )
            print("parallel_lane_record_status=recorded")
        elif operation == "trusted-baseline-sha256":
            print(trusted_baseline_sha256(args.ai_head, args.media_head))
        elif operation == "verify-integration-base":
            print(
                verify_integration_base(
                    args.worktree, args.baseline, args.baseline_sha256
                )
            )
        elif operation == "record-lane-head":
            record_lane_head(
                args.lane,
                args.head,
                args.worktree,
                args.baseline,
                args.baseline_sha256,
            )
            print("parallel_lane_head_status=recorded")
        elif operation == "verify-lane":
            verify_lane(args.lane, args.baseline, args.baseline_sha256)
            print("parallel_lane_status=verified")
        elif operation == "verify-join":
            print(verify_join(args.baseline, args.baseline_sha256))
        elif operation == "verify-merged-lanes":
            print(verify_merged_lanes(args.baseline, args.baseline_sha256))
        elif operation == "merge-lanes":
            print(merge_lanes(args.baseline, args.baseline_sha256))
        elif operation == "verify-protected-state":
            categories = tuple(item for item in args.allow.split(",") if item)
            print(
                verify_protected_state(
                    categories, args.baseline, args.baseline_sha256
                )
            )
        else:
            _raise("unsupported_operation")
    except ParallelLaunchError as exc:
        print(f"parallel_launch_error={exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
