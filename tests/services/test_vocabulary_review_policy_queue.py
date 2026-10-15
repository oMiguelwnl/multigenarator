"""Isolated policy launcher: native imports, no model/provider execution."""

import hashlib
import importlib
import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def api():
    name = "multilang.services.vocabulary_review_policy_queue"
    assert importlib.util.find_spec(name), "versioned policy launcher is missing"
    return importlib.import_module(name)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def setup(tmp_path, monkeypatch):
    mod = api()
    spec = importlib.util.spec_from_file_location(
        "policy_queue_native_fixtures", Path(__file__).with_name("test_vocabulary_session_partitions.py")
    )
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    common = fixtures._queue_fixture(tmp_path)
    common["repository"] = REPO
    parent = tmp_path / "parent"
    parent.mkdir()
    binding = {
        "plan_sha256": common["plan_sha256"], "work": str(common["work"]),
        "repository": str(REPO), "session_ids": ["ja-0001", "ja-0002"],
        "exclude_languages": ["en"], "requested_model": "gpt-6-astra",
        "reasoning_effort": "high",
    }
    (parent / "binding.json").write_text(json.dumps(binding))
    policy = tmp_path / "policy.md"
    policy.write_text("Trusted clarification: unresolved POS may remain uncertain with pos:null.\n")
    kw = {"plan": common["plan"], "plan_sha256": common["plan_sha256"],
          "output": common["output"], "parent_queue": parent,
          "parent_binding_sha256": sha(parent / "binding.json"),
          "policy": policy, "policy_sha256": sha(policy),
          "implementation_sha256": mod.implementation_identity()["sha256"], "workers": 1}
    calls = []
    monkeypatch.setattr(mod, "_account_check", lambda: calls.append("account"))
    return mod, kw, common, fixtures, calls


def test_native_completion_preserves_original_and_binds_effective_prompt(setup):
    mod, kw, common, fixtures, calls = setup
    originals = {}

    def worker(task):
        assert calls
        prompt = Path(task["prompt_file"])
        assert prompt.name == "effective-prompt.txt"
        assert "Trusted clarification" in prompt.read_text()
        original = prompt.with_name("prompt.txt")
        originals[str(original)] = original.read_bytes()
        audit = json.loads(prompt.with_name("policy-context.json").read_text())
        assert audit["original_prompt_sha256"] == sha(original)
        assert audit["effective_prompt_sha256"] == sha(prompt)
        assert audit["policy_sha256"] == kw["policy_sha256"]
        assert audit["context_id"].startswith("queue-ja-")
        assert task["directory"] == str(common["work"] / task["session_id"])
        assert task["controller_lock_fd"] >= 0
        return fixtures._finish_queue_task(common, task)

    result = mod.run_policy_queue(**kw, worker=worker)
    assert result["status"] == "first_pass_complete"
    assert set(result["sessions"]) == {"ja-0001", "ja-0002"}
    assert not (common["work"] / "en-0001").exists()
    assert all(Path(path).read_bytes() == raw for path, raw in originals.items())
    again = mod.run_policy_queue(**kw, worker=lambda _: pytest.fail("completed work dispatched"))
    assert again["status"] == "first_pass_complete"
    assert len(calls) == 2


def test_account_failure_blocks_even_custom_worker(setup, monkeypatch):
    mod, kw, _, _, _ = setup

    def fail():
        raise ValueError("ChatGPT account required")

    monkeypatch.setattr(mod, "_account_check", fail)
    result = mod.run_policy_queue(**kw, worker=lambda _: pytest.fail("account bypass"))
    assert result["status"] == "stopped_with_error"
    assert result["completed_sessions"] == 0


@pytest.mark.parametrize("field", ["policy_sha256", "implementation_sha256", "parent_binding_sha256"])
def test_bad_hash_rejected_before_queue_writes(setup, field):
    mod, kw, _, _, calls = setup
    kw[field] = "0" * 64
    with pytest.raises(ValueError, match="checksum|binding|implementation"):
        mod.run_policy_queue(**kw, worker=lambda _: pytest.fail("drift dispatched"))
    assert not kw["output"].exists() and not calls


@pytest.mark.parametrize("field", ["policy", "parent_queue", "output"])
def test_symlink_arguments_rejected(setup, tmp_path, field):
    mod, kw, _, _, _ = setup
    alias = tmp_path / "alias"
    alias.symlink_to(kw[field], target_is_directory=field != "policy")
    kw[field] = alias
    with pytest.raises(ValueError, match="symlink"):
        mod.run_policy_queue(**kw, worker=lambda _: pytest.fail("symlink dispatched"))


@pytest.mark.parametrize("overlap", ["parent_queue", "plan", "work"])
def test_output_cannot_overlap_existing_authoritative_paths(setup, overlap):
    mod, kw, common, _, _ = setup
    kw["output"] = common["work"] if overlap == "work" else kw[overlap]
    with pytest.raises(ValueError, match="overlap|separate"):
        mod.run_policy_queue(**kw, worker=lambda _: pytest.fail("unsafe output"))


def test_no_progress_never_reports_complete_and_resume_preserves_import(setup):
    mod, kw, common, fixtures, _ = setup

    def partial(task):
        fixtures._finish_queue_task(common, task, one_unit=True)
        raise TimeoutError("bounded interruption")

    result = mod.run_policy_queue(**kw, worker=partial)
    assert result["status"] == "stopped_with_error"
    assert result["sessions"]["ja-0001"]["new_reviewed_units"] == 1
    again = mod.run_policy_queue(**kw, worker=lambda task: fixtures._finish_queue_task(common, task))
    assert again["status"] == "first_pass_complete"


def test_cancellation_object_and_controller_lease_are_preserved(setup):
    mod, kw, _, _, _ = setup

    def cancel(task):
        from multilang.services.vocabulary_session_queue import _controller_lock

        binding = json.loads((kw["parent_queue"] / "binding.json").read_text())
        with pytest.raises(ValueError, match="lock"):
            with _controller_lock(Path(binding["work"]) / "queue-controller"):
                pytest.fail("lease bypass")
        task["cancel_event"].set()
        raise InterruptedError("requested stop")

    result = mod.run_policy_queue(**kw, worker=cancel)
    assert result["status"] == "stopped_by_request"


def test_policy_drift_between_assignments_stops_before_next_launch(setup):
    mod, kw, common, fixtures, calls = setup

    def change(task):
        fixtures._finish_queue_task(common, task)
        kw["policy"].write_text("changed policy")
        return 0

    result = mod.run_policy_queue(**kw, worker=change)
    assert result["status"] == "stopped_with_error"
    assert len(calls) == 1


def test_attempt_path_escape_is_rejected_before_read(setup, monkeypatch, tmp_path):
    mod, kw, _, _, calls = setup
    outside = tmp_path / "outside.txt"
    outside.write_text("do not rewrite")

    def queue(**args):
        return args["worker"]({"prompt_file": str(outside), "session_id": "ja-0001"})

    monkeypatch.setattr(mod, "run_queue", queue)
    with pytest.raises(ValueError, match="attempt|boundary"):
        mod.run_policy_queue(**kw)
    assert outside.read_text() == "do not rewrite" and not calls


def test_native_safe_uncertainty_is_not_relaxed():
    api()
    from multilang.services.vocabulary_curation import validate_selections

    group = {"lemma": "literal", "pos": "X", "sense_candidates": [{"candidate_id": "x"}]}
    row = {"i": 0, "decision": "uncertain", "display": "literal", "pos": None,
           "senses": [], "forms": [], "reason": "insufficient_evidence"}
    assert validate_selections([group], {"decisions": [row]})[0].pos is None
    with pytest.raises(ValueError, match="resolved POS"):
        validate_selections([group], {"decisions": [row | {"decision": "include", "senses": [0]}]})


def test_supervisor_callback_keeps_policy_and_rejects_drift(setup, monkeypatch):
    mod, kw, common, fixtures, _ = setup
    mod.run_policy_queue(**kw, worker=lambda task: fixtures._finish_queue_task(common, task))

    def supervise(**args):
        native = json.loads((kw["output"] / "binding.json").read_text())
        invoke = {k: native[k] for k in ("plan_sha256", "work", "repository", "session_ids", "exclude_languages")}
        invoke.update(plan=kw["plan"], output=kw["output"], workers=1)
        kw["policy"].write_text("tampered during cooldown")
        with pytest.raises(ValueError, match="checksum"):
            args["runner"](**invoke)
        return {"status": "blocked"}

    monkeypatch.setattr(mod, "supervise_queue", supervise)
    assert mod.supervise_policy_queue(**kw)["status"] == "blocked"


def test_default_launch_reuses_native_command_and_account(setup, monkeypatch):
    mod, kw, common, fixtures, calls = setup
    from multilang.services.vocabulary_session_queue import codex_command, worker_environment

    def launch(task):
        assert calls
        cmd = codex_command(task)
        assert cmd[cmd.index("--model") + 1] == "gpt-6-astra"
        assert 'forced_login_method="chatgpt"' in cmd
        assert 'model_reasoning_effort="high"' in cmd
        assert "agents.enabled=false" in cmd
        assert "sandbox_workspace_write.network_access=false" in cmd
        assert "OPENAI_API_KEY" not in worker_environment({"OPENAI_API_KEY": "never"})
        return fixtures._finish_queue_task(common, task)

    monkeypatch.setattr(mod, "_launch", launch)
    assert mod.run_policy_queue(**kw)["status"] == "first_pass_complete"


@pytest.mark.parametrize("message,retry", [("Selected model is at capacity", True), ("unknown failure", False)])
def test_real_supervisor_classification_and_resume_keep_policy(setup, monkeypatch, message, retry):
    mod, kw, common, fixtures, _ = setup
    from multilang.services.vocabulary_queue_supervisor import supervise_queue

    def failed(task):
        Path(task["events_file"]).write_text(json.dumps({"type": "turn.failed", "error": {"message": message}}) + "\n")
        return 75

    assert mod.run_policy_queue(**kw, worker=failed)["status"] == "stopped_with_error"
    seen = []

    def launch(task):
        seen.append(task["session_id"])
        assert Path(task["prompt_file"]).name == "effective-prompt.txt"
        assert kw["policy_sha256"] in Path(task["prompt_file"]).read_text()
        return fixtures._finish_queue_task(common, task)

    monkeypatch.setattr(mod, "_launch", launch)
    ticks = [0.0]

    def sleep(seconds):
        ticks[0] += seconds

    monkeypatch.setattr(mod, "supervise_queue", lambda **args: supervise_queue(
        **args, clock=lambda: ticks[0], sleeper=sleep
    ))
    result = mod.supervise_policy_queue(**kw, cooldown_seconds=1, poll_seconds=1)
    assert result["status"] == ("first_pass_complete" if retry else "blocked")
    assert result["restarts"] == int(retry)
    assert bool(seen) is retry


def test_supervisor_cannot_change_native_selection(setup, monkeypatch):
    mod, kw, common, fixtures, _ = setup
    mod.run_policy_queue(**kw, worker=lambda task: fixtures._finish_queue_task(common, task))

    def wrong(**args):
        with pytest.raises(ValueError, match="lineage"):
            args["runner"](plan=kw["plan"], plan_sha256=kw["plan_sha256"], output=kw["output"],
                             work=common["work"], repository=REPO, workers=1,
                             session_ids=["en-0001"], exclude_languages=[])
        return {"status": "blocked"}

    monkeypatch.setattr(mod, "supervise_queue", wrong)
    assert mod.supervise_policy_queue(**kw)["status"] == "blocked"


def test_bound_code_drift_stops_before_dispatch(setup, monkeypatch):
    mod, kw, _, _, calls = setup
    original = mod.implementation_identity
    number = [0]

    def identity():
        number[0] += 1
        return original() if number[0] == 1 else {"sha256": "0" * 64, "files": {}}

    monkeypatch.setattr(mod, "implementation_identity", identity)
    result = mod.run_policy_queue(**kw, worker=lambda _: pytest.fail("changed code dispatched"))
    assert result["status"] == "stopped_with_error" and not calls


def test_existing_unbound_native_output_is_not_adopted(setup):
    mod, kw, _, _, _ = setup
    kw["output"].mkdir()
    (kw["output"] / "binding.json").write_text("{}")
    with pytest.raises(ValueError, match="unbound"):
        mod.run_policy_queue(**kw, worker=lambda _: pytest.fail("adopted old output"))


def test_existing_effective_prompt_symlink_cannot_write_outside(setup, monkeypatch, tmp_path):
    mod, kw, _, _, _ = setup
    original_account = mod._account_check
    outside = tmp_path / "untouched"
    outside.write_text("unchanged")

    def account():
        original_account()
        prompt = next(kw["output"].glob("attempts/*/*/prompt.txt"))
        prompt.with_name("effective-prompt.txt").symlink_to(outside)

    monkeypatch.setattr(mod, "_account_check", account)
    result = mod.run_policy_queue(**kw, worker=lambda _: pytest.fail("symlink dispatched"))
    assert result["status"] == "stopped_with_error"
    assert outside.read_text() == "unchanged"


def test_drift_during_account_check_is_rejected_before_launch(setup, monkeypatch):
    mod, kw, _, _, _ = setup
    monkeypatch.setattr(mod, "_account_check", lambda: kw["policy"].write_text("policy changed during auth"))
    result = mod.run_policy_queue(**kw, worker=lambda _: pytest.fail("post-auth drift dispatched"))
    assert result["status"] == "stopped_with_error"
    assert not list(kw["output"].glob("attempts/*/*/effective-prompt.txt"))


def test_fingerprint_covers_executed_language_contracts():
    files = api().implementation_identity()["files"]
    assert "src/multilang/domain/jobs.py" in files
    assert "src/multilang/domain/language_profiles.py" in files
