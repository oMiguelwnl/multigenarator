"""Every source unit gets exactly one bounded, resumable session assignment."""

import hashlib
import json
from pathlib import Path

import pytest

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.vocabulary_session_review import (
    export_session_request,
    import_session_review,
)


def _source(tmp_path, *, fragments=False, long=False):
    root = tmp_path / "packets"
    hashes, languages = {}, []
    for language in ("en", "ja"):
        (root / language).mkdir(parents=True)
        groups = []
        for index in range(4):
            fragmented = fragments and index in (1, 2)
            groups.append({
                "entry_id": f"{language}-e{1 if fragmented else index}",
                "review_unit_id": f"{language}-u{index}",
                "source_group_fragment_index": index - 1 if fragmented else 0,
                "source_group_fragment_count": 2 if fragmented else 1,
                "lemma": f"word{1 if fragmented else index}", "pos": "NOUN",
                "source_priority": index + 1,
                "sense_candidates": [{"candidate_id": f"{language}-s{index}",
                                      "glosses": ["animal" * (800 if long and fragmented else 1)]}],
                "forms_for_review": [], "readings": [],
            })
        refs = []
        for start in (0, 2):
            packet = {"language": language, "generation_status": "deferred_by_user",
                      "groups": groups[start:start + 2]}
            packet["packet_sha256"] = canonical_sha256(packet)
            relative = f"{language}/{start // 2:05d}.json"
            content = json.dumps(packet).encode()
            (root / relative).write_bytes(content)
            digest = hashlib.sha256(content).hexdigest()
            hashes[relative] = digest
            refs.append({"path": relative, "sha256": digest, "entries": 2})
        languages.append({"language": language, "entry_count": 3 if fragments else 4,
                          "review_unit_count": 4, "packet_count": 2, "packets": refs})
    summary = {"generation_status": "deferred_by_user", "source_manifest_sha256": "a" * 64,
               "entry_count": sum(row["entry_count"] for row in languages), "review_unit_count": 8,
               "packet_count": 4, "languages": languages}
    content = json.dumps(summary).encode()
    (root / "summary.json").write_bytes(content)
    hashes["summary.json"] = hashlib.sha256(content).hexdigest()
    (root / "manifest.json").write_text(json.dumps({"files": hashes}))
    return dict(packets=root, manifest_sha256=hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest(),
                requests=tmp_path / "previous-requests", reviews=tmp_path / "previous-reviews")


def _response(request, decision="include"):
    data = json.loads((Path(request) / "request.json").read_text())
    return {"decisions": [{"i": i, "decision": decision, "display": group["lemma"],
                           "senses": [0] if decision == "include" else [], "pos": None, "forms": [],
                           "reason": "general_use" if decision == "include" else "insufficient_evidence"}
                          for i, group in enumerate(data["groups"])]}


def _baseline(args):
    packet = args["packets"] / "en/00000.json"
    request = args["requests"] / "en"
    exported = export_session_request(packet, hashlib.sha256(packet.read_bytes()).hexdigest(),
                                      indices=[0], output=request)
    import_session_review(request=request, request_sha256=exported["request_sha256"],
                          response=_response(request, "uncertain"), context_id="previous-session",
                          output=args["reviews"] / "en")


def test_partition_covers_every_unit_once_and_preserves_existing_reviews(tmp_path):
    from multilang.services.vocabulary_session_partitions import partition_vocabulary_sessions

    args = _source(tmp_path)
    _baseline(args)
    result = partition_vocabulary_sessions(**args, output=tmp_path / "plan", max_units=2)
    assert (result["total_units"], result["baseline_reviewed_units"], result["pending_units"]) == (8, 1, 7)
    assert result["session_count"] == 4
    assert result["requested_model"] == "gpt-6-astra"
    assert result["provider_calls_executed"] == 0
    assert result["production_eligible"] is False
    plan = json.loads((tmp_path / "plan/plan.json").read_text())
    units = []
    for row in plan["sessions"]:
        assignment = json.loads((tmp_path / "plan" / row["path"]).read_text())
        units.extend((assignment["language"], unit["review_unit_id"]) for unit in assignment["units"])
        assert len(assignment["units"]) <= 2
        assert (tmp_path / "plan/sessions" / row["session_id"] / "START.md").is_file()
    assert len(units) == len(set(units)) == 8
    assert (tmp_path / "plan/baseline/reviews/en/result.json").is_file()
    again = partition_vocabulary_sessions(**args, output=tmp_path / "other", max_units=2)
    assert again["plan_sha256"] == result["plan_sha256"]


def test_fragments_across_packets_stay_together_even_when_the_group_exceeds_budget(tmp_path):
    from multilang.services.vocabulary_session_partitions import partition_vocabulary_sessions

    args = _source(tmp_path, fragments=True, long=True)
    result = partition_vocabulary_sessions(**args, output=tmp_path / "plan", max_units=2, max_evidence_bytes=4096)
    plan = json.loads((tmp_path / "plan/plan.json").read_text())
    assert result["oversized_sessions"] == 2
    for language in ("en", "ja"):
        locations = []
        for row in plan["sessions"]:
            assignment = json.loads((tmp_path / "plan" / row["path"]).read_text())
            if assignment["language"] != language:
                continue
            members = {unit["review_unit_id"] for unit in assignment["units"]}
            if f"{language}-u1" in members or f"{language}-u2" in members:
                locations.append(assignment)
        assert len(locations) == 1
        assert len(locations[0]["units"]) == 2
        assert locations[0]["oversized_single_entry"] is True


def test_sessions_resume_exclusively_and_consolidate_without_fake_completion(tmp_path):
    from multilang.services.vocabulary_session_partitions import (
        import_partition_response,
        next_partition_request,
        partition_progress,
        partition_vocabulary_sessions,
    )

    args = _source(tmp_path)
    _baseline(args)
    created = partition_vocabulary_sessions(**args, output=tmp_path / "plan", max_units=2)
    common = dict(plan=tmp_path / "plan", plan_sha256=created["plan_sha256"], work=tmp_path / "work")
    first = next_partition_request(**common, session_id="en-0001")
    assert first["source_indices"] == [1]
    assert next_partition_request(**common, session_id="en-0001") == first
    independent = next_partition_request(**common, session_id="en-0002")
    assert independent["request_sha256"] != first["request_sha256"]
    imported = import_partition_response(**common, session_id="en-0001", request=Path(first["request"]),
                                        request_sha256=first["request_sha256"], response=_response(first["request"]),
                                        context_id="en-0001-live")
    assert imported["production_eligible"] is False
    assert next_partition_request(**common, session_id="en-0001")["status"] == "first_pass_complete"
    status = partition_progress(**common)
    assert status["total_units"] == 8
    assert status["baseline_reviewed_units"] == 1
    assert status["newly_reviewed_units"] == 1
    assert status["unreviewed_units"] == 6
    assert status["uncertain_units"] == 1
    assert status["first_pass_complete_sessions"] == 1
    assert status["production_eligible"] is False
    assert status["generation_status"] == "deferred_by_user"
    with pytest.raises(ValueError, match="session|assignment"):
        import_partition_response(**common, session_id="en-0002", request=Path(first["request"]),
                                  request_sha256=first["request_sha256"], response=_response(first["request"]),
                                  context_id="wrong-session")


def test_changed_source_or_plan_cannot_be_reviewed_and_paths_cannot_escape(tmp_path):
    from multilang.services.vocabulary_session_partitions import (
        next_partition_request,
        partition_vocabulary_sessions,
    )

    args = _source(tmp_path)
    created = partition_vocabulary_sessions(**args, output=tmp_path / "plan", max_units=2)
    common = dict(plan=tmp_path / "plan", plan_sha256=created["plan_sha256"], work=tmp_path / "work")
    with pytest.raises(ValueError):
        next_partition_request(**common, session_id="../outside")
    (args["packets"] / "en/00000.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        next_partition_request(**common, session_id="en-0001")
    (tmp_path / "plan/plan.json").write_text("{}")
    with pytest.raises(ValueError, match="binding|checksum"):
        next_partition_request(**common, session_id="ja-0001")


def test_correction_retries_are_idempotent_but_stale_forks_are_rejected(tmp_path):
    from multilang.services.vocabulary_session_partitions import (
        import_partition_response,
        next_partition_request,
        partition_progress,
        partition_vocabulary_sessions,
    )

    created = partition_vocabulary_sessions(**_source(tmp_path), output=tmp_path / "plan", max_units=2)
    common = dict(plan=tmp_path / "plan", plan_sha256=created["plan_sha256"], work=tmp_path / "work")
    request = next_partition_request(**common, session_id="en-0001")
    importing = dict(**common, session_id="en-0001", request=Path(request["request"]),
                     request_sha256=request["request_sha256"], context_id="review-session")
    first = import_partition_response(**importing, response=_response(request["request"]))
    correction = dict(**importing, response=_response(request["request"], "uncertain"),
                      supersedes=Path(first["output_directory"]))
    second = import_partition_response(**correction)
    assert import_partition_response(**correction) == second
    assert partition_progress(**common)["newly_reviewed_units"] == 2
    assert partition_progress(**common)["uncertain_units"] == 2
    with pytest.raises(ValueError, match="current session proposal"):
        import_partition_response(**(correction | {"context_id": "forked-review"}))


def test_baseline_decisions_are_derived_from_the_frozen_copy(tmp_path, monkeypatch):
    from multilang.services import vocabulary_session_partitions as partitions

    args = _source(tmp_path)
    _baseline(args)
    original = partitions._artifacts

    def artifacts(root):
        if root == args["reviews"]:
            request = args["requests"] / "en"
            data = json.loads((request / "request.json").read_text())
            import_session_review(request=request, request_sha256=canonical_sha256(data),
                                  response=_response(request), context_id="concurrent-correction",
                                  supersedes=args["reviews"] / "en", output=args["reviews"] / "correction")
        return original(root)

    monkeypatch.setattr(partitions, "_artifacts", artifacts)
    result = partitions.partition_vocabulary_sessions(**args, output=tmp_path / "plan", max_units=2)
    progress = partitions.partition_progress(plan=tmp_path / "plan", plan_sha256=result["plan_sha256"],
                                             work=tmp_path / "work")
    assert progress["baseline_reviewed_units"] == 1
    assert progress["include_units"] == 1
    assert progress["uncertain_units"] == 0


def _queue_fixture(tmp_path):
    from multilang.services.vocabulary_session_partitions import partition_vocabulary_sessions

    created = partition_vocabulary_sessions(**_source(tmp_path), output=tmp_path / "plan", max_units=2)
    return dict(plan=tmp_path / "plan", plan_sha256=created["plan_sha256"],
                work=tmp_path / "work", output=tmp_path / "queue", repository=Path.cwd())


def _finish_queue_task(common, task, *, one_unit=False):
    from multilang.services.vocabulary_session_partitions import (
        import_partition_response,
        next_partition_request,
    )

    args = {k: common[k] for k in ("plan", "plan_sha256", "work")}
    while True:
        request = next_partition_request(**args, session_id=task["session_id"], batch_size=1)
        if request["status"] == "first_pass_complete":
            break
        import_partition_response(**args, session_id=task["session_id"], request=Path(request["request"]),
                                  request_sha256=request["request_sha256"], response=_response(request["request"]),
                                  context_id="queue-fixture")
        if one_unit:
            break
    return 0


def test_queue_runs_exclusive_parallel_assignments_and_skips_completed_on_resume(tmp_path):
    import threading

    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)
    guard, rendezvous = threading.Lock(), threading.Barrier(3)
    seen, active, maximum = [], set(), [0]

    def worker(task):
        with guard:
            assert task["session_id"] not in active
            active.add(task["session_id"])
            seen.append(task["session_id"])
            order = len(seen)
            maximum[0] = max(maximum[0], len(active))
        if order <= 3:
            rendezvous.wait(timeout=10)
        _finish_queue_task(common, task)
        with guard:
            active.remove(task["session_id"])
        return 0

    result = run_queue(**common, worker=worker)
    assert result["status"] == "first_pass_complete"
    assert result["completed_sessions"] == 4
    assert len(seen) == len(set(seen)) == 4
    assert maximum[0] == 3
    assert result["production_eligible"] is False
    again = run_queue(**common, worker=lambda _: pytest.fail("completed session relaunched"))
    assert again["completed_sessions"] == 4


def test_queue_retries_partial_progress_and_never_trusts_worker_completion_text(tmp_path):
    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)
    calls = []

    def worker(task):
        calls.append(task["session_id"])
        return _finish_queue_task(common, task, one_unit=True)

    result = run_queue(**common, worker=worker, workers=1)
    assert result["status"] == "first_pass_complete"
    assert len(calls) == 8


def test_queue_stops_on_worker_error_or_no_progress_and_preserves_pending(tmp_path):
    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)
    result = run_queue(**common, worker=lambda _: 19, workers=1)
    assert result["status"] == "stopped_with_error"
    assert result["completed_sessions"] == 0
    assert len(result["failures"]) == 1
    result = run_queue(**common, worker=lambda _: 0, workers=1)
    assert result["status"] == "stopped_with_error"
    assert result["completed_sessions"] == 0
    assert "no progress" in result["failures"][0]["reason"]


def test_queue_requires_exclusive_controller_and_honors_stop_file(tmp_path):
    from multilang.services.qualification_machine_runner import _locked
    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)
    with _locked(common["work"] / "queue-controller"):
        with pytest.raises(ValueError, match="lock|running"):
            run_queue(**common, worker=lambda _: pytest.fail("duplicate controller"))
    common["output"].mkdir(exist_ok=True)
    (common["output"] / "STOP").touch()
    result = run_queue(**common, worker=lambda _: pytest.fail("stop ignored"))
    assert result["status"] == "stopped_by_request"


def test_codex_queue_command_forces_chatgpt_and_drops_api_credentials(tmp_path):
    from multilang.services.vocabulary_session_queue import codex_command, worker_environment

    task = {"directory": str(tmp_path), "final_message": str(tmp_path / "final.txt")}
    command = codex_command(task)
    assert command[:2] == ["codex", "exec"]
    assert 'forced_login_method="chatgpt"' in command
    assert 'model_reasoning_effort="high"' in command
    assert command[command.index("--model") + 1] == "gpt-6-astra"
    assert command[command.index("--sandbox") + 1] == "workspace-write"
    assert not any("bypass" in arg or "danger-full-access" in arg for arg in command)
    env = worker_environment({"HOME": "/home/test", "PATH": "/bin", "OPENAI_API_KEY": "secret",
                              "CODEX_API_KEY": "secret", "OPENROUTER_API_KEY": "secret",
                              "DATABASE_URL": "secret", "CODEX_THREAD_ID": "parent-thread"})
    assert env["HOME"] == "/home/test"
    assert not any("secret" == value for value in env.values())
    assert "CODEX_THREAD_ID" not in env


def test_queue_rejects_drift_and_unsafe_paths_before_launch(tmp_path):
    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)
    with pytest.raises(ValueError):
        run_queue(**(common | {"plan_sha256": "0" * 64}), worker=lambda _: pytest.fail("drift launched"))
    with pytest.raises(ValueError):
        run_queue(**common, workers=4, worker=lambda _: pytest.fail("limit ignored"))
    link = tmp_path / "link"
    link.symlink_to(common["output"], target_is_directory=True)
    with pytest.raises(ValueError):
        run_queue(**(common | {"output": link}), worker=lambda _: pytest.fail("symlink accepted"))


def test_queue_records_auth_failure_without_claiming_running(tmp_path, monkeypatch):
    from multilang.services import vocabulary_session_queue as queue

    common = _queue_fixture(tmp_path)

    def unavailable():
        raise ValueError("ChatGPT login unavailable")

    monkeypatch.setattr(queue, "_account_check", unavailable)
    result = queue.run_queue(**common)
    assert result["status"] == "stopped_with_error"
    assert result["completed_sessions"] == 0
    assert result["failures"][0]["session_id"] is None


def test_queue_cooperative_stop_event_prevents_new_launches(tmp_path):
    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)
    calls = []

    def worker(task):
        calls.append(task["session_id"])
        task["cancel_event"].set()
        return 0

    result = run_queue(**common, workers=1, worker=worker)
    assert result["status"] == "stopped_by_request"
    assert len(calls) == 1
    assert result["completed_sessions"] == 0


def test_worker_failure_cancels_other_active_workers_before_retry(tmp_path):
    import threading

    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)
    rendezvous = threading.Barrier(2)
    calls, observed = [], []

    def worker(task):
        calls.append(task["session_id"])
        if len(calls) <= 2:
            rendezvous.wait(timeout=10)
        if task["session_id"] == "en-0001":
            return 17
        _finish_queue_task(common, task, one_unit=True)
        observed.append(task["cancel_event"].wait(timeout=3))
        return 0

    result = run_queue(**common, workers=2, worker=worker)
    assert result["status"] == "stopped_with_error"
    assert observed == [True]
    assert len(calls) == 2


def test_stop_file_observation_is_sticky_even_when_file_is_removed(tmp_path):
    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)

    def worker(task):
        stop = common["output"] / "STOP"
        stop.touch()
        task["cancel_event"].wait(timeout=3)
        stop.unlink()
        return 0

    result = run_queue(**common, workers=1, worker=worker)
    assert result["status"] == "stopped_by_request"
    assert result["completed_sessions"] == 0


def test_controller_lock_remains_exclusive_while_inherited_child_is_alive(tmp_path):
    import subprocess
    import sys

    from multilang.services.qualification_machine_runner import _locked
    from multilang.services.vocabulary_session_queue import _controller_lock

    target = tmp_path / "work/queue-controller"
    child = None
    try:
        with _controller_lock(target) as descriptor:
            child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                     pass_fds=(descriptor,))
        with pytest.raises(ValueError, match="lock"):
            with _locked(target):
                pytest.fail("orphan child lost exclusive ownership")
    finally:
        if child is not None:
            child.terminate()
            child.wait(timeout=5)
    with _locked(target):
        pass


def test_stop_seen_only_by_worker_stops_the_entire_queue(tmp_path, monkeypatch):
    import threading

    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)
    original = Path.exists
    stop, observed, calls = common["output"] / "STOP", [False], []

    def exists(path):
        if path == stop and calls and not observed[0] and threading.current_thread().name.startswith("ThreadPool"):
            observed[0] = True
            return True
        return original(path)

    def worker(task):
        calls.append(task["session_id"])
        return _finish_queue_task(common, task, one_unit=True)

    monkeypatch.setattr(Path, "exists", exists)
    result = run_queue(**common, workers=1, worker=worker)
    assert result["status"] == "stopped_by_request"
    assert len(calls) == 1


def test_process_cleanup_kills_descendant_that_ignores_term(tmp_path):
    import os
    import signal
    import subprocess
    import sys
    import time

    from multilang.services.vocabulary_session_queue import _terminate_group

    child_code = "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print('ready',flush=True); time.sleep(30)"
    leader_code = (
        "import subprocess,sys,time; "
        f"p=subprocess.Popen([sys.executable,'-c',{child_code!r}],stdout=subprocess.PIPE,text=True); "
        "p.stdout.readline(); print(p.pid,flush=True); time.sleep(30)"
    )
    leader = subprocess.Popen([sys.executable, "-c", leader_code], stdout=subprocess.PIPE,
                              text=True, start_new_session=True)
    descendant = int(leader.stdout.readline())
    try:
        _terminate_group(leader)
        for _ in range(50):
            stat = Path(f"/proc/{descendant}/stat")
            if not stat.exists() or stat.read_text().rsplit(") ", 1)[1].startswith("Z "):
                break
            time.sleep(0.02)
        else:
            pytest.fail("descendant still executing after group cleanup")
        assert leader.poll() is not None
    finally:
        try:
            os.killpg(leader.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        leader.wait(timeout=5)


@pytest.mark.parametrize("interrupted", [False, True])
def test_queue_refreshes_imported_progress_after_worker_exception(tmp_path, interrupted):
    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)

    def worker(task):
        _finish_queue_task(common, task, one_unit=True)
        if interrupted:
            task["cancel_event"].set()
            raise InterruptedError("review stopped after import")
        raise TimeoutError("review deadline after import")

    result = run_queue(**common, workers=1, session_ids=["en-0001"], worker=worker)
    assert result["status"] == ("stopped_by_request" if interrupted else "stopped_with_error")
    row = result["sessions"]["en-0001"]
    assert row["new_reviewed_units"] == 1
    assert row["remaining_units"] == 1
    assert row["status"] == ("interrupted" if interrupted else "error")
    assert row["attempt_directory"]
    assert json.loads((common["output"] / "status.json").read_text())["sessions"]["en-0001"] == row
    if not interrupted:
        assert result["failures"] == [{"session_id": "en-0001", "reason": "review deadline after import"}]


def test_queue_preserves_original_exception_when_progress_replay_fails(tmp_path):
    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)

    def worker(task):
        _finish_queue_task(common, task, one_unit=True)
        result = next((common["work"] / task["session_id"] / "reviews").glob("*/result.json"))
        result.write_text("{}")
        raise TimeoutError("original worker timeout")

    result = run_queue(**common, workers=1, session_ids=["en-0001"], worker=worker)
    assert result["status"] == "stopped_with_error"
    assert result["failures"] == [{"session_id": "en-0001", "reason": "original worker timeout"}]
    row = result["sessions"]["en-0001"]
    assert row["remaining_units"] == 2
    assert row["new_reviewed_units"] == 0
    assert "checksum" in row["progress_refresh_error"]


def test_queue_excludes_reserved_languages_before_dispatch_and_binding(tmp_path):
    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)
    calls = []

    def worker(task):
        calls.append(task["session_id"])
        assert task["session_id"].startswith("ja-")
        return _finish_queue_task(common, task)

    result = run_queue(**common, workers=1, exclude_languages=["en", "en"], worker=worker)
    assert result["status"] == "first_pass_complete"
    assert calls == ["ja-0001", "ja-0002"]
    assert result["selected_sessions"] == 2
    binding = json.loads((common["output"] / "binding.json").read_text())
    assert binding["exclude_languages"] == ["en"]
    assert binding["session_ids"] == calls
    again = run_queue(**common, exclude_languages=["en"],
                      worker=lambda _: pytest.fail("completed assignment dispatched again"))
    assert again["completed_sessions"] == 2
    assert not (common["work"] / "en-0001").exists()


@pytest.mark.parametrize("excluded", [["unknown"], ["../en"], ["en", "ja"]])
def test_queue_rejects_invalid_or_empty_language_selection_before_dispatch(tmp_path, excluded):
    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)
    with pytest.raises(ValueError, match="language|assignments"):
        run_queue(**common, exclude_languages=excluded,
                  worker=lambda _: pytest.fail("invalid language selection dispatched"))
    assert not common["output"].exists()


def test_queue_default_binding_stays_compatible_without_language_exclusions(tmp_path):
    from multilang.services.vocabulary_session_queue import run_queue

    common = _queue_fixture(tmp_path)
    run_queue(**common, workers=1, worker=lambda task: _finish_queue_task(common, task))
    binding = json.loads((common["output"] / "binding.json").read_text())
    assert set(binding) == {"plan_sha256", "work", "repository", "session_ids", "requested_model", "reasoning_effort"}


def test_queue_cli_accepts_repeated_exclude_language(monkeypatch):
    import runpy
    import sys

    from multilang.services import vocabulary_session_queue as queue

    captured = {}

    def run(**kwargs):
        captured.update(kwargs)
        return {"status": "first_pass_complete"}

    monkeypatch.setattr(queue, "run_queue", run)
    monkeypatch.setattr(sys, "argv", [
        "run_vocabulary_session_queue.py", "--plan", "plan", "--plan-sha256", "a" * 64,
        "--work", "work", "--output", "output", "--exclude-language", "pt",
        "--exclude-language", "es", "--exclude-language", "fr",
    ])
    namespace = runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts/run_vocabulary_session_queue.py"))
    assert namespace["main"]() == 0
    assert captured["exclude_languages"] == ["pt", "es", "fr"]
