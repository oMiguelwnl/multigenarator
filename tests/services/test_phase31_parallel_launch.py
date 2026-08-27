"""Tamper-resistant Phase 31 parallel launch and join contracts."""

from __future__ import annotations

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
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "phase31_parallel_launch.py"


def _load_helper() -> ModuleType:
    assert SCRIPT_PATH.is_file(), "parallel launch helper is not implemented"
    spec = util.spec_from_file_location("_phase31_parallel_launch", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def committed_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "integration")
    _git(root, "config", "user.name", "Phase Test")
    _git(root, "config", "user.email", "phase-test@example.invalid")
    _write(root / "pyproject.toml", "[project]\nname='fixture'\n")
    _write(root / "uv.lock", "version = 1\n")
    _write(root / "protected.txt", "protected\n")
    _write(root / "src" / "multilang" / "__init__.py", "VALUE = 1\n")
    _git(root, "add", "pyproject.toml", "uv.lock", "protected.txt", "src")
    _git(root, "commit", "-m", "fixture baseline")
    return root


def _configure(
    helper: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    repo: Path,
    tmp_path: Path,
) -> None:
    state = tmp_path / "parallel"
    ai = tmp_path / "ai-worktree"
    media = tmp_path / "media-worktree"
    monkeypatch.setattr(helper, "PROJECT_ROOT", repo)
    monkeypatch.setattr(helper, "BASELINE_ROOT", state)
    monkeypatch.setattr(helper, "BASELINE_PATH", state / "baseline.json")
    monkeypatch.setattr(helper, "BASELINE_SIDECAR_PATH", state / "baseline.json.sha256")
    monkeypatch.setattr(helper, "LANE_HEADS_PATH", state / "lane-heads.json")
    monkeypatch.setattr(helper, "LANE_HEADS_SIDECAR_PATH", state / "lane-heads.json.sha256")
    monkeypatch.setattr(helper, "AI_WORKTREE", ai)
    monkeypatch.setattr(helper, "MEDIA_WORKTREE", media)
    monkeypatch.setattr(
        helper,
        "LANE_ALLOWLISTS",
        {
            "ai": ("ai.txt", "handoffs/ai-lane.json"),
            "media": ("media.txt", "handoffs/media-lane.json"),
        },
    )
    monkeypatch.setattr(
        helper,
        "LANE_HANDOFF_RELPATHS",
        {
            "ai": "handoffs/ai-lane.json",
            "media": "handoffs/media-lane.json",
        },
    )
    monkeypatch.setattr(helper, "PROTECTED_PATHS", ("protected.txt",))
    monkeypatch.setattr(helper, "RUNTIME_PYTHON", Path(sys.executable))
    monkeypatch.setattr(
        helper,
        "_venv_fingerprint",
        lambda: {
            "operation": "fingerprint-venv",
            "path": ".venv",
            "status": "unsafe",
            "tree_sha256": "f" * 64,
            "file_count": 0,
            "link_count": 1,
            "special_count": 0,
        },
    )


def test_parallel_helper_contract_is_fixed_and_pathless() -> None:
    helper = _load_helper()

    assert helper.PUBLIC_OPERATIONS == (
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
    assert helper.BASELINE_PATH == Path("/tmp/multilang-phase31-parallel/baseline.json")
    assert helper.AI_WORKTREE == Path("/tmp/multilang-phase31-ai")
    assert helper.MEDIA_WORKTREE == Path("/tmp/multilang-phase31-media")
    assert set(helper.LANE_ALLOWLISTS["ai"]).isdisjoint(helper.LANE_ALLOWLISTS["media"])


def test_real_shared_tmp_parent_is_accepted_only_with_sticky_0777_mode() -> None:
    helper = _load_helper()
    metadata = Path("/tmp").lstat()

    assert helper._shared_tmp_parent_is_safe(metadata)


def test_prepare_baseline_rejects_dirty_repo_and_overlapping_lanes(
    committed_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    _configure(helper, monkeypatch, committed_repo, tmp_path)
    _write(committed_repo / "dirty.txt", "dirty\n")

    with pytest.raises(helper.ParallelLaunchError, match="integration_dirty"):
        helper.prepare_baseline()

    assert not helper.BASELINE_ROOT.exists()
    (committed_repo / "dirty.txt").unlink()
    monkeypatch.setattr(
        helper,
        "LANE_ALLOWLISTS",
        {"ai": ("same.txt",), "media": ("same.txt",)},
    )

    with pytest.raises(helper.ParallelLaunchError, match="lane_allowlist_overlap"):
        helper.prepare_baseline()

    assert not helper.BASELINE_ROOT.exists()


def test_prepare_baseline_requires_available_python_312_runtime(
    committed_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    _configure(helper, monkeypatch, committed_repo, tmp_path)
    monkeypatch.setattr(helper, "RUNTIME_PYTHON", tmp_path / "missing-python")

    with pytest.raises(helper.ParallelLaunchError, match="runtime_invalid"):
        helper.prepare_baseline()

    assert not helper.BASELINE_PATH.exists()


def test_prepare_baseline_rejects_non_python_312_runtime(
    committed_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    _configure(helper, monkeypatch, committed_repo, tmp_path)
    monkeypatch.setattr(helper, "_runtime_version", lambda: "3.11.9")

    with pytest.raises(helper.ParallelLaunchError, match="runtime_invalid"):
        helper.prepare_baseline()

    assert not helper.BASELINE_PATH.exists()


def test_prepare_baseline_accepts_existing_safe_empty_state_root(
    committed_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    _configure(helper, monkeypatch, committed_repo, tmp_path)
    helper.BASELINE_ROOT.mkdir(mode=0o700)

    digest = helper.prepare_baseline()

    assert helper.verify_baseline(helper.BASELINE_PATH, digest)["baseline_commit"] == _git(
        committed_repo, "rev-parse", "HEAD"
    )


def test_baseline_digest_is_independent_of_coordinated_file_replacement(
    committed_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    _configure(helper, monkeypatch, committed_repo, tmp_path)

    expected = helper.prepare_baseline()
    baseline = json.loads(helper.BASELINE_PATH.read_text(encoding="utf-8"))
    baseline["baseline_commit"] = "0" * 40
    replacement = helper.canonical_json_bytes(baseline)
    helper.BASELINE_PATH.chmod(0o600)
    helper.BASELINE_PATH.write_bytes(replacement)
    helper.BASELINE_PATH.chmod(0o444)
    forged = helper.sha256_bytes(replacement)
    helper.BASELINE_SIDECAR_PATH.chmod(0o600)
    helper.BASELINE_SIDECAR_PATH.write_text(f"{forged}\n", encoding="ascii")
    helper.BASELINE_SIDECAR_PATH.chmod(0o444)

    with pytest.raises(helper.ParallelLaunchError, match="baseline_digest_mismatch"):
        helper.verify_baseline(helper.BASELINE_PATH, expected)


def test_parallel_lane_heads_join_and_merge_are_exact(
    committed_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    _configure(helper, monkeypatch, committed_repo, tmp_path)
    expected = helper.prepare_baseline()
    baseline = helper.verify_baseline(helper.BASELINE_PATH, expected)
    ai = helper.AI_WORKTREE
    media = helper.MEDIA_WORKTREE
    _git(committed_repo, "worktree", "add", "-b", "ai-lane", str(ai), baseline["baseline_commit"])
    _git(
        committed_repo,
        "worktree",
        "add",
        "-b",
        "media-lane",
        str(media),
        baseline["baseline_commit"],
    )
    _write(ai / "ai.txt", "ai result\n")
    helper.record_lane(
        "ai",
        worktree=ai,
        baseline_path=helper.BASELINE_PATH,
        baseline_sha256=expected,
        aggregate_root="a" * 64,
        evidence_root="b" * 64,
    )
    _git(ai, "add", "ai.txt", "handoffs/ai-lane.json")
    _git(ai, "commit", "-m", "ai lane")
    ai_head = _git(ai, "rev-parse", "HEAD")
    _write(media / "media.txt", "media result\n")
    helper.record_lane(
        "media",
        worktree=media,
        baseline_path=helper.BASELINE_PATH,
        baseline_sha256=expected,
        aggregate_root="c" * 64,
        evidence_root="d" * 64,
    )
    _git(media, "add", "media.txt", "handoffs/media-lane.json")
    _git(media, "commit", "-m", "media lane")
    media_head = _git(media, "rev-parse", "HEAD")

    helper.record_lane_head(
        "ai", ai_head, ai, helper.BASELINE_PATH, expected
    )
    helper.record_lane_head(
        "media", media_head, media, helper.BASELINE_PATH, expected
    )

    assert helper.trusted_baseline_sha256(ai_head, media_head) == expected
    assert helper.verify_join(helper.BASELINE_PATH, expected) == "parallel_join_status=verified"
    assert helper.verify_integration_base(
        committed_repo, helper.BASELINE_PATH, expected
    ) == "parallel_integration_base_status=verified"
    helper.merge_lanes(helper.BASELINE_PATH, expected)
    assert helper.verify_merged_lanes(
        helper.BASELINE_PATH, expected
    ) == "parallel_merged_status=verified"
    assert (committed_repo / "ai.txt").read_text(encoding="utf-8") == "ai result\n"
    assert (committed_repo / "media.txt").read_text(encoding="utf-8") == "media result\n"


def test_verify_worktree_runtime_requires_exact_pythonpath(
    committed_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    _configure(helper, monkeypatch, committed_repo, tmp_path)
    expected = helper.prepare_baseline()
    baseline = helper.verify_baseline(helper.BASELINE_PATH, expected)
    ai = helper.AI_WORKTREE
    _git(committed_repo, "worktree", "add", "-b", "ai-runtime", str(ai), baseline["baseline_commit"])
    monkeypatch.setenv("PYTHONPATH", str(ai / "src"))

    assert helper.verify_worktree_runtime(
        "ai", helper.BASELINE_PATH, expected, worktree=ai
    ) == "parallel_worktree_runtime_status=verified"

    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "wrong-src"))

    with pytest.raises(helper.ParallelLaunchError, match="runtime_pythonpath_invalid"):
        helper.verify_worktree_runtime(
            "ai", helper.BASELINE_PATH, expected, worktree=ai
        )


def test_record_lane_rejects_symlinked_handoff_parent_without_external_write(
    committed_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    _configure(helper, monkeypatch, committed_repo, tmp_path)
    expected = helper.prepare_baseline()
    baseline = helper.verify_baseline(helper.BASELINE_PATH, expected)
    ai = helper.AI_WORKTREE
    _git(committed_repo, "worktree", "add", "-b", "ai-symlink", str(ai), baseline["baseline_commit"])
    _write(ai / "ai.txt", "ai result\n")
    outside = tmp_path / "outside"
    outside.mkdir()
    (ai / "handoffs").symlink_to(outside, target_is_directory=True)

    with pytest.raises(helper.ParallelLaunchError, match="lane_write_scope_violation"):
        helper.record_lane(
            "ai",
            worktree=ai,
            baseline_path=helper.BASELINE_PATH,
            baseline_sha256=expected,
            aggregate_root="a" * 64,
            evidence_root="b" * 64,
        )

    assert not (outside / "ai-lane.json").exists()


def test_record_lane_head_rejects_forged_baseline_tree_in_committed_handoff(
    committed_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    _configure(helper, monkeypatch, committed_repo, tmp_path)
    expected = helper.prepare_baseline()
    baseline = helper.verify_baseline(helper.BASELINE_PATH, expected)
    ai = helper.AI_WORKTREE
    _git(committed_repo, "worktree", "add", "-b", "ai-forged", str(ai), baseline["baseline_commit"])
    _write(ai / "ai.txt", "ai result\n")
    helper.record_lane(
        "ai",
        worktree=ai,
        baseline_path=helper.BASELINE_PATH,
        baseline_sha256=expected,
        aggregate_root="a" * 64,
        evidence_root="b" * 64,
    )
    handoff_path = ai / "handoffs" / "ai-lane.json"
    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    handoff["baseline_tree"] = "0" * 40
    handoff_path.write_bytes(helper.canonical_json_bytes(handoff))
    _git(ai, "add", "ai.txt", "handoffs/ai-lane.json")
    _git(ai, "commit", "-m", "forged ai lane")
    head = _git(ai, "rev-parse", "HEAD")

    with pytest.raises(helper.ParallelLaunchError, match="lane_handoff_mismatch"):
        helper.record_lane_head(
            "ai", head, ai, helper.BASELINE_PATH, expected
        )


def test_coordinated_lane_head_document_and_sidecar_replacement_is_rejected(
    committed_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    _configure(helper, monkeypatch, committed_repo, tmp_path)
    expected = helper.prepare_baseline()
    helper.BASELINE_ROOT.mkdir(mode=0o700, exist_ok=True)
    forged_document = helper.canonical_json_bytes(
        {"schema_version": 1, "lanes": {"ai": {"head": "0" * 40}}}
    )
    helper.atomic_write(helper.LANE_HEADS_PATH, forged_document, mode=0o600)
    helper.atomic_write(
        helper.LANE_HEADS_SIDECAR_PATH,
        f"{helper.sha256_bytes(forged_document)}\n".encode("ascii"),
        mode=0o600,
    )

    with pytest.raises(helper.ParallelLaunchError, match="lane_heads_invalid"):
        helper.verify_join(helper.BASELINE_PATH, expected)


def test_protected_state_drift_fails_closed(
    committed_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    _configure(helper, monkeypatch, committed_repo, tmp_path)
    expected = helper.prepare_baseline()
    (committed_repo / "protected.txt").write_text("changed\n", encoding="utf-8")

    with pytest.raises(helper.ParallelLaunchError, match="protected_state_drift"):
        helper.verify_protected_state(
            (), helper.BASELINE_PATH, expected, worktree=committed_repo
        )


def test_baseline_files_use_restrictive_fixed_modes(
    committed_repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper = _load_helper()
    _configure(helper, monkeypatch, committed_repo, tmp_path)

    helper.prepare_baseline()

    assert stat.S_IMODE(helper.BASELINE_ROOT.lstat().st_mode) == 0o700
    assert stat.S_IMODE(helper.BASELINE_PATH.lstat().st_mode) == 0o444
    assert stat.S_IMODE(helper.BASELINE_SIDECAR_PATH.lstat().st_mode) == 0o444
    assert helper.BASELINE_PATH.lstat().st_uid == os.getuid()
