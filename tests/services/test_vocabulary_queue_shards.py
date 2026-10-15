"""Native queue shards preserve immutable reviews and merge without overwrites."""

import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path

import pytest


def api():
    name = "multilang.services.vocabulary_queue_shards"
    assert importlib.util.find_spec(name), "isolated shard implementation is missing"
    return importlib.import_module(name)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def setup(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "shard_fixtures", Path(__file__).with_name("test_vocabulary_session_partitions.py")
    )
    fx = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fx)
    common = fx._queue_fixture(tmp_path)
    fx._finish_queue_task(common, {"session_id": "ja-0001"}, one_unit=True)
    notes = common["work"] / "ja-0001/notes"
    notes.mkdir()
    (notes / "progress.md").write_text("original note")
    (tmp_path / "parent").mkdir()
    binding = tmp_path / "parent/binding.json"
    binding.write_text(
        json.dumps(
            {
                k: str(common[k]) if isinstance(common[k], Path) else common[k]
                for k in ("plan_sha256", "work", "repository")
            }
            | {
                "session_ids": ["ja-0001", "ja-0002"],
                "requested_model": "gpt-6-astra",
                "reasoning_effort": "high",
            }
        )
    )
    kw = dict(
        plan=common["plan"],
        plan_sha256=common["plan_sha256"],
        parent_binding=binding,
        parent_binding_sha256=sha(binding),
        groups={"first": ["ja-0001"], "second": ["ja-0002"]},
        output=tmp_path / "split",
    )
    return api(), kw, common, fx


def prepare(setup):
    mod, kw, common, fx = setup
    mod.prepare_shards(**kw)
    manifest = kw["output"] / "manifest.json"
    merge = dict(
        manifest=manifest,
        manifest_sha256=sha(manifest),
        group="first",
        report=kw["output"].parent / "merge-report",
    )
    return mod, kw, common, fx, merge


def test_physical_copy_preserves_imports_and_bindings(setup):
    mod, kw, common, fx, merge = prepare(setup)
    root = kw["output"] / "groups/first"
    original = common["work"] / "ja-0001/notes/progress.md"
    copied = root / "work/ja-0001/notes/progress.md"
    assert copied.read_bytes() == original.read_bytes()
    assert copied.stat().st_ino != original.stat().st_ino
    binding = json.loads((root / "parent/binding.json").read_text())
    assert binding["session_ids"] == ["ja-0001"]
    assert binding["work"] == str(root / "work")
    assert binding["requested_model"] == "gpt-6-astra"
    assert not (kw["output"] / "groups/second/work/ja-0001").exists()
    manifest = json.loads(merge["manifest"].read_text())
    assert manifest["groups"]["first"]["baseline_files"]
    with pytest.raises((ValueError, FileExistsError)):
        mod.prepare_shards(**kw)


def test_merge_native_decisions_and_idempotent_notes_archive(setup):
    mod, kw, common, fx, merge = prepare(setup)
    shard = kw["output"] / "groups/first/work"
    fx._finish_queue_task(common | {"work": shard}, {"session_id": "ja-0001"})
    (shard / "ja-0001/notes/progress.md").write_text("worker progress")
    result = mod.merge_shard(**merge)
    assert result["sessions"]["ja-0001"]["reviewed_units"] == 2
    assert (common["work"] / "ja-0001/notes/progress.md").read_text() == "original note"
    assert (merge["report"] / "archive/ja-0001/notes/progress.md").read_text() == "worker progress"
    before = {str(p): sha(p) for p in common["work"].rglob("*") if p.is_file()}
    assert mod.merge_shard(**merge) == result
    assert before == {str(p): sha(p) for p in common["work"].rglob("*") if p.is_file()}


@pytest.mark.parametrize("operation", ["prepare", "merge-original", "merge-shard"])
def test_live_controller_rejected(setup, operation):
    from multilang.services.vocabulary_session_queue import _controller_lock

    mod, kw, common, fx = setup
    if operation == "prepare":

        def call():
            return mod.prepare_shards(**kw)

        work = common["work"]
    else:
        mod, kw, common, fx, merge = prepare(setup)

        def call():
            return mod.merge_shard(**merge)

        work = (
            common["work"] if operation == "merge-original" else kw["output"] / "groups/first/work"
        )
    with _controller_lock(work / "queue-controller"), pytest.raises(ValueError, match="lock"):
        call()


@pytest.mark.parametrize(
    "groups",
    [
        {"a": ["ja-0001"], "b": ["ja-0001"]},
        {"a": ["en-0001"]},
        {"../escape": ["ja-0001"]},
        {"a": ["../ja-0001"]},
        {"a": []},
    ],
)
def test_invalid_selection_rejected(setup, groups):
    mod, kw, _, _ = setup
    with pytest.raises(ValueError):
        mod.prepare_shards(**(kw | {"groups": groups}))
    assert not kw["output"].exists()


@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_links_rejected(setup, kind):
    mod, kw, common, _ = setup
    path = common["work"] / "ja-0001/notes/unsafe"
    target = common["work"] / "ja-0001/notes/progress.md"
    if kind == "symlink":
        path.symlink_to(target)
    else:
        os.link(target, path)
    with pytest.raises(ValueError, match="link"):
        mod.prepare_shards(**kw)


@pytest.mark.parametrize("where", ["canonical", "shard"])
@pytest.mark.parametrize("change", ["edit", "delete"])
def test_baseline_artifact_change_conflicts(setup, where, change):
    mod, kw, common, _, merge = prepare(setup)
    work = common["work"] if where == "canonical" else kw["output"] / "groups/first/work"
    path = next((work / "ja-0001/reviews").glob("*/result.json"))
    if change == "edit":
        path.write_text("{}")
    else:
        path.unlink()
    with pytest.raises(ValueError):
        mod.merge_shard(**merge)
    assert not merge["report"].exists()


def test_unbound_review_rejected_without_canonical_writes(setup):
    mod, kw, common, fx, merge = prepare(setup)
    shard = kw["output"] / "groups/first/work"
    fx._finish_queue_task(common | {"work": shard}, {"session_id": "ja-0001"})
    import shutil

    requests = sorted((shard / "ja-0001/requests").iterdir())
    shutil.rmtree(requests[-1])
    with pytest.raises(ValueError):
        mod.merge_shard(**merge)
    assert len([p for p in (common["work"] / "ja-0001/reviews").iterdir() if p.is_dir()]) == 1


def test_runtime_and_lockfiles_excluded(setup):
    mod, kw, common, _ = setup
    session = common["work"] / "ja-0001"
    (session / ".codex-runtime").mkdir()
    (session / ".codex-runtime/cache").write_text("runtime")
    (session / ".operation.lock").touch()
    mod.prepare_shards(**kw)
    copied = kw["output"] / "groups/first/work/ja-0001"
    assert not (copied / ".codex-runtime").exists()
    assert not (copied / ".operation.lock").exists()


def test_shard_implementation_available():
    assert callable(api().prepare_shards)


@pytest.mark.parametrize(
    "relative", ["completion.json", "review-notes.md", "responses/pending.json"]
)
def test_mutable_worker_auxiliary_archived_without_overwrite(setup, relative):
    mod, kw, common, fx = setup
    original = common["work"] / "ja-0001" / relative
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_text("original")
    mod, kw, common, fx, merge = prepare(setup)
    shard = kw["output"] / "groups/first/work"
    (shard / "ja-0001" / relative).write_text("updated")
    mod.merge_shard(**merge)
    assert original.read_text() == "original"
    assert (merge["report"] / "archive/ja-0001" / relative).read_text() == "updated"


def test_cli_prepare_and_merge_offline(setup, monkeypatch):
    mod, kw, common, fx = setup
    script = Path(__file__).resolve().parents[2] / "scripts/manage_vocabulary_queue_shards.py"
    assert script.exists(), "shard CLI missing"
    spec = importlib.util.spec_from_file_location("shard_cli", script)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    groups = kw["output"].parent / "groups.json"
    groups.write_text(json.dumps(kw["groups"]))
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script),
            "prepare",
            "--plan",
            str(kw["plan"]),
            "--plan-sha256",
            kw["plan_sha256"],
            "--parent-binding",
            str(kw["parent_binding"]),
            "--parent-binding-sha256",
            kw["parent_binding_sha256"],
            "--groups",
            str(groups),
            "--output",
            str(kw["output"]),
        ],
    )
    cli.main()
    manifest = kw["output"] / "manifest.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script),
            "merge",
            "--manifest",
            str(manifest),
            "--manifest-sha256",
            sha(manifest),
            "--group",
            "first",
            "--report",
            str(kw["output"].parent / "report"),
        ],
    )
    cli.main()
    assert (kw["output"].parent / "report/merge.json").exists()


def test_each_published_revision_prefix_is_valid(setup, monkeypatch):
    from multilang.services.vocabulary_session_partitions import import_partition_response

    mod, kw, common, fx, merge = prepare(setup)
    shard = kw["output"] / "groups/first/work"
    request = next(p for p in (shard / "ja-0001/requests").iterdir() if p.is_dir())
    review = next(p for p in (shard / "ja-0001/reviews").iterdir() if p.is_dir())
    request_sha = json.loads((review / "result.json").read_text())["request_sha256"]
    for index in range(5):
        result = import_partition_response(
            plan=common["plan"],
            plan_sha256=common["plan_sha256"],
            session_id="ja-0001",
            work=shard,
            request=request,
            request_sha256=request_sha,
            response=fx._response(request, "uncertain" if index % 2 == 0 else "include"),
            context_id=f"correction-{index}",
            supersedes=review,
        )
        review = Path(result["output_directory"])
    native_rename = Path.rename
    published = []

    def checked_rename(source, target):
        result = native_rename(source, target)
        if Path(target).is_relative_to(common["work"]) and Path(target).parent.name == "reviews":
            _, data, refs = mod._load_plan(common["plan"], common["plan_sha256"])
            mod._validate(common["work"], common["plan"], data, refs, ["ja-0001"])
            published.append(target)
        return result

    monkeypatch.setattr(Path, "rename", checked_rename)
    mod.merge_shard(**merge)
    assert len(published) == 5


def test_merge_rejects_different_implementation_before_canonical_changes(setup):
    mod, kw, common, fx, merge = prepare(setup)
    manifest = json.loads(merge["manifest"].read_text())
    manifest["implementation_sha256"] = "0" * 64
    merge["manifest"].write_text(json.dumps(manifest))
    merge["manifest_sha256"] = sha(merge["manifest"])
    before = mod._inventory(common["work"])
    with pytest.raises(ValueError, match="implementation"):
        mod.merge_shard(**merge)
    assert mod._inventory(common["work"]) == before
    assert not merge["report"].exists()
