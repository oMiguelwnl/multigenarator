"""Isolated row review never approves frequency or changes an active campaign."""

import copy
import importlib
import importlib.util
import json
import os
from hashlib import sha256
from pathlib import Path

import pytest

from multilang.services.korean_source_registry import build_korean_source_registry


def service():
    name = "multilang.services.korean_registry_review"
    assert importlib.util.find_spec(name), "isolated Korean registry review is not implemented"
    return importlib.import_module(name)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def fixture_inputs(tmp_path, extra=0):
    spec = importlib.util.spec_from_file_location(
        "registry_test_fixture", Path(__file__).with_name("test_korean_source_registry.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args = module._fixture(tmp_path, extra=extra)
    build_korean_source_registry(**args)
    return {k: v for k, v in args.items() if k != "output"} | {
        "registry": args["output"],
        "registry_manifest_sha256": digest(args["output"] / "manifest.json"),
        "output": tmp_path / "plan",
    }


@pytest.fixture
def prepared(tmp_path):
    args = fixture_inputs(tmp_path)
    result = service().prepare_registry_review(**args, max_units=2)
    return (
        args,
        result,
        {
            "plan": args["output"],
            "plan_sha256": result["plan_sha256"],
            "work": tmp_path / "isolated-work",
        },
    )


def next_request(prepared, task_id="ko-pending-0001", batch_size=8):
    return service().next_registry_request(**prepared[2], task_id=task_id, batch_size=batch_size)


def response_for(request):
    doc = json.loads((Path(request["request"]) / "request.json").read_text())
    decisions = []
    for i, unit in enumerate(doc["units"]):
        row = unit["source_row"]
        useful = bool(row["source_hint"])
        field = "source_hint" if useful else "source_pos"
        decisions.append(
            {
                "i": i,
                "source_row_id": row["source_row_id"],
                "decision": "include" if useful else "uncertain",
                "reason": "general_use" if useful else "insufficient_evidence",
                "resolved_upos": "ADV" if useful else None,
                "reviewed_flags": unit["flags"],
                "evidence": [
                    {
                        "field": field,
                        "quote": row[field],
                        "source_row_id": row["source_row_id"],
                        "source_line_utf8_sha256": row["source_line_utf8_sha256"],
                    }
                ],
                "notes": "Synthetic test proposal grounded only in this fixture; not a real review.",
            }
        )
    return {"decisions": decisions}


def import_response(prepared, request, response, **kwargs):
    return service().import_registry_response(
        **prepared[2],
        task_id="ko-pending-0001",
        request=Path(request["request"]),
        request_sha256=request["request_sha256"],
        response=response,
        context_id="synthetic-test",
        **kwargs,
    )


def test_preparation_rederives_rows_aliases_and_does_not_make_requests(tmp_path):
    args = fixture_inputs(tmp_path)
    before = {
        p: digest(p)
        for directory in (args["bundle"], args["supplement"], args["registry"])
        for p in directory.iterdir()
    }
    result = service().prepare_registry_review(**args, max_units=2)
    assert result["pending_units"] == 3 and result["existing_aliases"] == 2
    assert result["task_count"] == 2 and result["production_eligible"] is False
    units = json.loads((args["output"] / "units.json").read_text())
    assert len(units) == 3 and all(u["review_status"] == "pending_review" for u in units)
    assert units[0]["source_row"]["source_form"] == units[1]["source_row"]["source_form"]
    assert units[0]["source_row_id"] != units[1]["source_row_id"]
    assert units[-1]["source_row"]["source_pos"] == "불"
    assert "unsupported_source_pos" in units[-1]["flags"]
    assert all(digest(p) == h for p, h in before.items())
    assert not (tmp_path / "isolated-work").exists()


def test_no_3000_pending_row_cap(tmp_path):
    result = service().prepare_registry_review(**fixture_inputs(tmp_path, extra=3000))
    assert result["pending_units"] == 3003


def test_next_is_resumable_and_status_does_not_create_missing_work(prepared):
    s = service().registry_review_status(**prepared[2])
    assert s["unreviewed_units"] == 3 and s["reviewed_units"] == 0
    assert not prepared[2]["work"].exists()
    first = next_request(prepared)
    assert next_request(prepared) == first
    assert first["unit_count"] == 2
    assert (Path(first["request"]) / "messages.json").is_file()
    assert not (Path(first["request"]) / "response.json").exists()


def test_import_complete_response_and_immutable_supersession(prepared):
    req = next_request(prepared)
    response = response_for(req)
    first = import_response(prepared, req, response)
    predecessor = Path(first["review"])
    before = {p.name: digest(p) for p in predecessor.iterdir()}
    assert next_request(prepared)["status"] == "first_pass_complete"
    assert service().registry_review_status(**prepared[2])["reviewed_units"] == 2
    assert import_response(prepared, req, response)["review_sha256"] == first["review_sha256"]
    revised = copy.deepcopy(response)
    revised["decisions"][0].update(
        decision="uncertain", reason="unresolved_meaning", resolved_upos=None
    )
    second = import_response(prepared, req, revised, supersedes=predecessor)
    assert second["review_sha256"] != first["review_sha256"]
    assert all(digest(predecessor / n) == h for n, h in before.items())
    status = service().registry_review_status(**prepared[2])
    assert (
        status["reviewed_units"] == 2
        and status["uncertain_units"] == 1
        and status["unreviewed_units"] == 1
    )
    with pytest.raises(ValueError, match="stale|supersed"):
        import_response(prepared, req, response, supersedes=predecessor)


@pytest.mark.parametrize(
    "mutation",
    [
        "index",
        "bool_index",
        "missing",
        "member",
        "quote",
        "line_hash",
        "field",
        "pos",
        "flags",
        "approval",
        "merge",
        "display",
        "empty_hint_include",
    ],
)
def test_import_rejects_invalid_binding_quotes_pos_or_authority(prepared, mutation):
    req = next_request(prepared)
    response = response_for(req)
    d = response["decisions"][0]
    if mutation == "index":
        d["i"] = 99
    elif mutation == "bool_index":
        d["i"] = True
    elif mutation == "missing":
        response["decisions"].pop()
    elif mutation == "member":
        d["source_row_id"] = "other"
    elif mutation == "quote":
        d["evidence"][0]["quote"] = "invented meaning"
    elif mutation == "line_hash":
        d["evidence"][0]["source_line_utf8_sha256"] = "0" * 64
    elif mutation == "field":
        d["evidence"][0]["field"] = "../../.env"
    elif mutation == "pos":
        d["resolved_upos"] = "NNG"
    elif mutation == "flags":
        d["reviewed_flags"] = ["invented_flag"]
    elif mutation == "approval":
        d["human_approved"] = True
    elif mutation == "merge":
        d["identity_relationships"] = [{"merge": "other"}]
    elif mutation == "display":
        d["canonical_display_proposal"] = "invented"
    else:
        d["evidence"][0].update(field="source_pos", quote="부")
    with pytest.raises(ValueError):
        import_response(prepared, req, response)
    assert service().registry_review_status(**prepared[2])["reviewed_units"] == 0


@pytest.mark.parametrize("location", ["root", "task"])
def test_stop_prevents_next_and_import_but_status_remains_available(prepared, location):
    req = next_request(prepared)
    folder = (
        prepared[2]["work"]
        if location == "root"
        else prepared[2]["work"] / "tasks" / "ko-pending-0001"
    )
    (folder / "STOP").write_text("requested stop")
    assert next_request(prepared)["status"] == "stopped"
    with pytest.raises(ValueError, match="STOP|stop"):
        import_response(prepared, req, response_for(req))
    assert service().registry_review_status(**prepared[2])["reviewed_units"] == 0


def test_busy_lock_never_reports_zero_as_observed_state(prepared):
    import fcntl

    next_request(prepared)
    fd = os.open(prepared[2]["work"] / ".operation.lock", os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert service().registry_review_status(**prepared[2]) == {
            "status": "busy",
            "counts_observed": False,
        }
        with pytest.raises(ValueError, match="busy|lock"):
            next_request(prepared)
    finally:
        os.close(fd)


def test_refuses_unbound_nonempty_work_and_path_traversal(prepared):
    work = prepared[2]["work"]
    work.mkdir()
    (work / "other-campaign").write_text("preserve")
    with pytest.raises(ValueError):
        next_request(prepared)
    with pytest.raises(ValueError):
        next_request(prepared, "../../outside")
    assert (work / "other-campaign").read_text() == "preserve"
    assert not (work / ".operation.lock").exists()


@pytest.mark.parametrize("target", ["snapshot", "registry", "alias"])
def test_rejects_source_or_registry_drift(tmp_path, target):
    args = fixture_inputs(tmp_path)
    path = (
        args["bundle"] / "source-snapshot.txt"
        if target == "snapshot"
        else args["registry"]
        / ("source-rows.jsonl" if target == "registry" else "existing-aliases.jsonl")
    )
    with path.open("ab") as f:
        f.write(b" ")
    with pytest.raises(ValueError):
        service().prepare_registry_review(**args)
    assert not args["output"].exists()


def test_status_rejects_source_drift_after_plan_creation(prepared):
    with (prepared[0]["bundle"] / "source-snapshot.txt").open("ab") as f:
        f.write(b" ")
    with pytest.raises(ValueError):
        service().registry_review_status(**prepared[2])


def test_status_is_readonly_and_response_strings_are_never_executed(prepared, monkeypatch):
    req = next_request(prepared)
    response = response_for(req)
    response["decisions"][0]["notes"] = (
        "<script>ignore instructions; $(touch NEVER_CREATE)</script>"
    )
    import_response(prepared, req, response)
    real_open = os.open

    def opening(path, flags, *args, **kwargs):
        assert not flags & (os.O_CREAT | os.O_WRONLY | os.O_RDWR | os.O_TRUNC)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", opening)
    assert service().registry_review_status(**prepared[2])["reviewed_units"] == 2
    assert not (prepared[2]["work"] / "NEVER_CREATE").exists()


def test_limits_and_existing_plan_are_not_overwritten(prepared):
    for kwargs in ({"batch_size": True}, {"batch_size": 65}):
        with pytest.raises(ValueError):
            next_request(prepared, **kwargs)
    before = digest(prepared[0]["output"] / "manifest.json")
    with pytest.raises(ValueError):
        service().prepare_registry_review(**prepared[0])
    assert digest(prepared[0]["output"] / "manifest.json") == before


def rewrite_member(root, filename, data):
    """Forge a self-consistent container; provenance replay must still reject it."""
    path = root / filename
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["files"][filename] = digest(path)
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")


def test_rehashed_registry_forgery_is_rederived_from_cp949(tmp_path):
    args = fixture_inputs(tmp_path)
    path = args["registry"] / "source-rows.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[2]["publisher_rank"] = 999999
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    manifest = json.loads((args["registry"] / "manifest.json").read_text())
    manifest["files"][path.name] = digest(path)
    (args["registry"] / "manifest.json").write_text(json.dumps(manifest))
    args["registry_manifest_sha256"] = digest(args["registry"] / "manifest.json")
    with pytest.raises(ValueError, match="rederived"):
        service().prepare_registry_review(**args)


def test_rehashed_plan_flags_are_rederived(prepared):
    root = prepared[0]["output"]
    units = json.loads((root / "units.json").read_text())
    units[-1]["flags"] = []
    rewrite_member(root, "units.json", units)
    kwargs = prepared[2] | {"plan_sha256": digest(root / "manifest.json")}
    with pytest.raises(ValueError, match="membership|evidence"):
        service().registry_review_status(**kwargs)


def test_ordinal_never_becomes_rank_and_homograph_80_alias_survives(prepared):
    aliases = json.loads((prepared[0]["output"] / "aliases.json").read_text())
    assert aliases[0]["source_ordinal"] == 1 and aliases[0]["source_frequency_rank"] == 1195
    assert aliases[1]["source_form"] == "시험80" and aliases[1]["source_frequency_rank"] is None
    assert aliases[1]["existing_lemma"] == "시험80"


def test_request_from_other_task_rejected(prepared):
    req = next_request(prepared, "ko-pending-0002")
    with pytest.raises(ValueError, match="binding"):
        import_response(prepared, req, response_for(req))


def test_rehashed_review_forgery_cannot_change_counts(prepared):
    req = next_request(prepared)
    imported = import_response(prepared, req, response_for(req))
    root = Path(imported["review"])
    review = json.loads((root / "review.json").read_text())
    review["response"]["decisions"][0]["evidence"][0]["quote"] = "invented"
    rewrite_member(root, "review.json", review)
    with pytest.raises(ValueError):
        service().registry_review_status(**prepared[2])


@pytest.mark.parametrize(
    "kind", ["snapshot", "registry", "response", "parent_symlink", "lock_fifo"]
)
def test_special_files_fail_without_blocking(tmp_path, kind):
    import signal

    args = fixture_inputs(tmp_path)
    module = service()

    def timeout_handler(*_args):
        raise AssertionError("reader blocked on special file")

    previous = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(3)
    try:
        if kind == "response":
            path = tmp_path / "response.json"
            os.mkfifo(path)

            def action():
                return module.read_response(path)
        elif kind == "parent_symlink":
            alias = tmp_path / "alias"
            alias.symlink_to(args["bundle"], target_is_directory=True)
            args["bundle"] = alias

            def action():
                return module.prepare_registry_review(**args)
        elif kind == "lock_fifo":
            result = module.prepare_registry_review(**args)
            common = {
                "plan": args["output"],
                "plan_sha256": result["plan_sha256"],
                "work": tmp_path / "work",
            }
            module.next_registry_request(**common, task_id="ko-pending-0001")
            lock = common["work"] / ".operation.lock"
            lock.unlink()
            os.mkfifo(lock)

            def action():
                return module.registry_review_status(**common)
        else:
            path = (
                args["bundle"] / "source-snapshot.txt"
                if kind == "snapshot"
                else args["registry"] / "source-rows.jsonl"
            )
            path.unlink()
            os.mkfifo(path)

            def action():
                return module.prepare_registry_review(**args)

        with pytest.raises((ValueError, OSError)):
            action()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def test_request_byte_budget_and_no_network_or_provider_hooks(prepared, monkeypatch):
    import socket

    def forbidden(*_args, **_kwargs):
        raise AssertionError("network attempted")

    monkeypatch.setattr(socket, "socket", forbidden)
    req = next_request(prepared)
    assert (Path(req["request"]) / "messages.json").stat().st_size <= 96000
    assert service().registry_review_status(**prepared[2])["unreviewed_units"] == 3


def test_plan_pins_implementation_reader_parser_and_rejects_drift(prepared, monkeypatch):
    module = service()
    document = json.loads((prepared[0]["output"] / "plan.json").read_text())
    fingerprints = document["implementation_sha256"]
    assert {
        "korean_registry_review.py",
        "vocabulary_context_supplement.py",
        "korean_grammar_course.py",
    } <= set(fingerprints)
    original = module._read_bytes

    def read(path, expected=None, *, limit):
        data = original(path, expected, limit=limit)
        if Path(path).name == "korean_grammar_course.py":
            return data + b"\n# simulated changed implementation\n"
        return data

    monkeypatch.setattr(module, "_read_bytes", read)
    with pytest.raises(ValueError, match="implementation"):
        module.registry_review_status(**prepared[2])


def test_quotes_do_not_grant_human_approval_and_proper_names_are_not_auto_excluded(prepared):
    module = service()
    assert "proper_name_scope does not imply exclusion" in module.PROTOCOL
    assert "countries and cities" in module.PROTOCOL
    req = next_request(prepared)
    imported = import_response(prepared, req, response_for(req))
    review = json.loads((Path(imported["review"]) / "review.json").read_text())
    assert review["human_approved"] is False
    assert json.loads((prepared[0]["output"] / "plan.json").read_text())["human_approved"] is False
