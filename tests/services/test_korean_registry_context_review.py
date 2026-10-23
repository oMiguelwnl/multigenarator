"""An additive overlay validates provenance, never semantic equivalence."""

import copy
import fcntl
import hashlib
import importlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services import korean_registry_review as base
from multilang.services.vocabulary_sources import wiktextract_record_candidates


def service():
    name = "multilang.services.korean_registry_context_review"
    assert importlib.util.find_spec(name), "contextual overlay is not implemented"
    return importlib.import_module(name)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def fixture(tmp_path, request):
    spec = importlib.util.spec_from_file_location(
        "native_fixture", Path(__file__).with_name("test_korean_registry_review.py")
    )
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    args = native.fixture_inputs(tmp_path, extra=getattr(request, "param", 2))
    prepared = base.prepare_registry_review(**args)
    native_args = dict(
        plan=args["output"], plan_sha256=prepared["plan_sha256"], work=tmp_path / "base-work"
    )
    request = base.next_registry_request(**native_args, task_id="ko-pending-0001")
    response = native.response_for(request)
    base.import_registry_response(
        **native_args,
        task_id="ko-pending-0001",
        request=Path(request["request"]),
        request_sha256=request["request_sha256"],
        response=response,
        context_id="synthetic-fixture",
    )
    records = [
        {
            "word": "추가000",
            "lang_code": "ko",
            "pos": "noun",
            "head_templates": [{"name": "ko-noun"}],
            "senses": [
                {
                    "glosses": ["test noun"],
                    "qualifier": "school",
                    "examples": [{"text": "literal example zero"}],
                },
                {
                    "glosses": ["another sense"],
                    "raw_tags": ["regional"],
                    "examples": [{"text": "other example"}],
                },
            ],
        },
        {
            "word": "추가000",
            "lang_code": "ko",
            "pos": "verb",
            "senses": [{"glosses": ["test verb"]}],
        },
    ]
    source = tmp_path / "source.jsonl"
    source.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    candidates = [
        c.model_dump(mode="json")
        for r in records
        for _, c in wiktextract_record_candidates(r, language="ko")
    ]
    candidates_path = tmp_path / "candidates.jsonl"
    candidates_path.write_text(
        "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in candidates)
    )
    prep = tmp_path / "manifest.json"
    write(
        prep,
        {
            "language": "ko",
            "dictionary_format": "wiktextract",
            "dictionary_sha256": sha(source),
            "files": {"candidates.jsonl": sha(candidates_path)},
            "production_eligible": False,
        },
    )
    units = json.loads((args["output"] / "units.json").read_text())
    context_spec = tmp_path / "spec.json"
    specification = {
        "schema_version": "korean-context-input-1",
        "source": {"path": str(source), "sha256": sha(source)},
        "source_preparation": {"path": str(prep), "sha256": sha(prep)},
        "candidates": {"path": str(candidates_path), "sha256": sha(candidates_path)},
        "records": [
            {
                "physical_line": i + 1,
                "source_record_sha256": canonical_sha256(r),
                "candidate_ids": [
                    c.model_dump(mode="json")["candidate_id"]
                    for _, c in wiktextract_record_candidates(r, language="ko")
                ],
            }
            for i, r in enumerate(records)
        ],
        "units": [
            {
                "source_index": i,
                "source_row_id": units[i]["source_row_id"],
                "record_lines": [1, 2] if i == 3 else [],
                "indirect_record_lines": [],
            }
            for i in [3, 2]
        ],
    }
    write(context_spec, specification)
    return dict(
        args=dict(
            base_plan=native_args["plan"],
            base_plan_sha256=native_args["plan_sha256"],
            base_work=native_args["work"],
            context_spec=context_spec,
            context_spec_sha256=sha(context_spec),
            output=tmp_path / "context-plan",
        ),
        specification=specification,
        native_args=native_args,
        native_request=request,
        native_response=response,
        units=units,
        source=source,
        candidates=candidates,
    )


def prepare(fixture):
    svc = service()
    result = svc.prepare_context_review(**fixture["args"])
    return (
        svc,
        result,
        dict(
            plan=fixture["args"]["output"],
            plan_sha256=result["plan_sha256"],
            work=fixture["args"]["output"].parent / "overlay-work",
        ),
    )


def update_spec(fixture):
    write(fixture["args"]["context_spec"], fixture["specification"])
    fixture["args"]["context_spec_sha256"] = sha(fixture["args"]["context_spec"])


def response_for(request):
    decisions = []
    for i, item in enumerate(request["units"]):
        row = item["unit"]["source_row"]
        evidence = [
            {
                "kind": "nikl_row",
                "field": field,
                "quote": row[field],
                "source_row_id": row["source_row_id"],
                "source_line_utf8_sha256": row["source_line_utf8_sha256"],
            }
            for field in ["source_form", "source_pos"]
        ]
        decisions.append(
            {
                "i": i,
                "source_row_id": row["source_row_id"],
                "decision": "uncertain",
                "reason": "insufficient_evidence",
                "resolved_upos": None,
                "reviewed_flags": item["unit"]["flags"],
                "context_candidates_reviewed": [
                    {
                        "candidate_id": c["candidate"]["candidate_id"],
                        "disposition": "unresolved",
                        "rationale": "Synthetic unresolved alignment; no semantic claim.",
                    }
                    for c in item["context_candidates"]
                ],
                "selected_context_senses": [],
                "alignment_review": {
                    "status": "unresolved",
                    "rationale": "Synthetic: POS, homograph and competing meanings are unresolved.",
                },
                "evidence": evidence,
                "notes": "Synthetic test only.",
            }
        )
    return {"decisions": decisions}


def include_first(response, request):
    candidate = request["units"][0]["context_candidates"][0]
    ref = {
        k: candidate[k] for k in ["source_record_sha256", "physical_line", "original_sense_index"]
    }
    ref.update(
        candidate_id=candidate["candidate"]["candidate_id"],
        bundle_sha256=request["units"][0]["context_sha256"],
    )
    d = response["decisions"][0]
    d.update(
        decision="include",
        reason="general_use",
        resolved_upos="NOUN",
        selected_context_senses=[
            {**ref, "bounded_scope": "Synthetic first noun sense only.", "source_pos": "noun"}
        ],
        alignment_review={
            "status": "single_session_proposal",
            "rationale": "Synthetic noun versus verb alternatives considered; native noun and external noun align in this limited meaning. No NIKL marker is interpreted as sense index.",
        },
    )
    d["context_candidates_reviewed"][0]["disposition"] = "compatible"
    d["evidence"].append(
        {"kind": "dictionary", **ref, "pointer": "/senses/0/glosses/0", "quote": "test noun"}
    )
    return response


def new_request(svc, args):
    result = svc.next_context_request(**args, task_id="ko-context-0001")
    return result, json.loads((Path(result["request"]) / "request.json").read_text())


def test_prepare_reconstructs_raw_candidates_preserves_alternatives_and_base(fixture):
    before = {p: sha(p) for p in fixture["native_args"]["work"].rglob("*") if p.is_file()}
    svc, result, args = prepare(fixture)
    assert result["context_units"] == 2
    request, document = new_request(svc, args)
    assert svc.next_context_request(**args, task_id="ko-context-0001") == request
    assert len(document["units"][0]["context_candidates"]) == 3
    assert document["units"][0]["records"][0]["record"]["senses"][0]["qualifier"] == "school"
    assert document["units"][1]["context_candidates"] == []
    assert document["units"][0]["unit"] == fixture["units"][3]
    assert (
        svc.validate_context_review(
            **args, request=Path(request["request"]), request_sha256=request["request_sha256"]
        )["valid"]
        is True
    )
    status = svc.context_review_status(**args)
    assert status["reviewed_units"] == 0 and status["context_available_units"] == 1
    assert status["semantic_equivalence_proven"] is False
    assert before == {p: sha(p) for p in before}


@pytest.mark.parametrize(
    "mutation",
    [
        "hash",
        "line",
        "candidate",
        "omit_alternative",
        "wrong_row",
        "nonempty",
        "duplicate",
        "unknown",
    ],
)
def test_bad_source_spec_rejected(fixture, mutation):
    svc = service()
    spec = fixture["specification"]
    if mutation == "hash":
        spec["source"]["sha256"] = "0" * 64
    if mutation == "line":
        spec["records"][0]["physical_line"] = 99
    if mutation == "candidate":
        spec["records"][0]["candidate_ids"] = ["candidate:" + "0" * 64]
    if mutation == "omit_alternative":
        spec["units"][0]["record_lines"] = [1]
    if mutation == "wrong_row":
        spec["units"][0]["source_row_id"] = spec["units"][1]["source_row_id"]
    if mutation == "nonempty":
        spec["units"][0].update(source_index=0, source_row_id=fixture["units"][0]["source_row_id"])
    if mutation == "duplicate":
        spec["units"].append(copy.deepcopy(spec["units"][0]))
    if mutation == "unknown":
        spec["human_approved"] = True
    update_spec(fixture)
    with pytest.raises(ValueError):
        svc.prepare_context_review(**fixture["args"])
    assert not fixture["args"]["output"].exists()


def test_prepared_candidate_must_equal_rederived_candidate(fixture):
    svc = service()
    path = Path(fixture["specification"]["candidates"]["path"])
    candidates = copy.deepcopy(fixture["candidates"])
    candidates[0]["glosses"] = ["tampered"]
    path.write_text("".join(json.dumps(c) + "\n" for c in candidates))
    fixture["specification"]["candidates"]["sha256"] = sha(path)
    prep = Path(fixture["specification"]["source_preparation"]["path"])
    metadata = json.loads(prep.read_text())
    metadata["files"]["candidates.jsonl"] = sha(path)
    write(prep, metadata)
    fixture["specification"]["source_preparation"]["sha256"] = sha(prep)
    update_spec(fixture)
    with pytest.raises(ValueError, match="candidate"):
        svc.prepare_context_review(**fixture["args"])


def test_base_busy_reports_unobserved_without_creating_outputs(fixture):
    svc = service()
    with (fixture["native_args"]["work"] / ".operation.lock").open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match="busy"):
            svc.prepare_context_review(**fixture["args"])
    assert not fixture["args"]["output"].exists()


def test_source_fifo_and_symlink_rejected_before_read(fixture):
    svc = service()
    source = fixture["source"]
    source.unlink()
    os.mkfifo(source)
    with pytest.raises(ValueError, match="regular"):
        svc.prepare_context_review(**fixture["args"])
    source.unlink()
    source.symlink_to(fixture["args"]["context_spec"])
    with pytest.raises((ValueError, OSError)):
        svc.prepare_context_review(**fixture["args"])


def test_stale_native_predecessor_rejected(fixture):
    svc, _, args = prepare(fixture)
    req = fixture["native_request"]
    native_review = next(
        (fixture["native_args"]["work"] / "tasks" / "ko-pending-0001" / "reviews").glob("review-*")
    )
    changed = copy.deepcopy(fixture["native_response"])
    changed["decisions"][3]["notes"] = "Changed synthetic predecessor."
    base.import_registry_response(
        **fixture["native_args"],
        task_id="ko-pending-0001",
        request=Path(req["request"]),
        request_sha256=req["request_sha256"],
        response=changed,
        context_id="changed",
        supersedes=native_review,
    )
    with pytest.raises(ValueError, match="predecessor"):
        svc.context_review_status(**args)


def test_overlay_import_resume_supersession_and_stop_are_isolated(fixture):
    svc, _, args = prepare(fixture)
    req, doc = new_request(svc, args)
    response = include_first(response_for(doc), doc)
    kw = dict(
        **args,
        request=Path(req["request"]),
        request_sha256=req["request_sha256"],
        response=response,
        context_id="synthetic-context",
    )
    svc.validate_context_review(
        **args, request=kw["request"], request_sha256=kw["request_sha256"], response=response
    )
    first = svc.import_context_response(**kw)
    assert svc.import_context_response(**kw) == first
    status = svc.context_review_status(**args)
    assert (status["reviewed_units"], status["include_units"], status["uncertain_units"]) == (
        2,
        1,
        1,
    )
    assert status["production_eligible"] is False
    replacement = response_for(doc)
    second = svc.import_context_response(
        **{
            **kw,
            "response": replacement,
            "context_id": "synthetic-correction",
            "supersedes": Path(first["review"]),
        }
    )
    assert Path(first["review"]).exists() and Path(second["review"]).exists()
    with pytest.raises(ValueError):
        svc.import_context_response(
            **{**kw, "context_id": "fork", "supersedes": Path(first["review"])}
        )
    (args["work"] / "STOP").touch()
    assert (
        svc.next_context_request(**args, task_id="ko-context-0001")["status"]
        == "stopped_by_request"
    )
    with pytest.raises(ValueError, match="STOP"):
        svc.import_context_response(**{**kw, "supersedes": Path(second["review"])})
    assert svc.context_review_status(**args)["uncertain_units"] == 2


@pytest.mark.parametrize(
    "mutation",
    [
        "pointer",
        "other_sense",
        "quote",
        "pos",
        "flags",
        "missing_alternative",
        "index",
        "record",
        "bundle",
        "scope",
        "no_lexical",
        "approve",
        "partial",
        "unknown",
    ],
)
def test_response_provenance_and_scope_fail_closed(fixture, mutation):
    svc, _, args = prepare(fixture)
    req, doc = new_request(svc, args)
    response = include_first(response_for(doc), doc)
    d = response["decisions"][0]
    if mutation == "pointer":
        d["evidence"][-1]["pointer"] = "/senses/~2/glosses/0"
    if mutation == "other_sense":
        d["evidence"][-1].update(pointer="/senses/1/examples/0/text", quote="other example")
    if mutation == "quote":
        d["evidence"][-1]["quote"] = "invented"
    if mutation == "pos":
        d["resolved_upos"] = "VERB"
    if mutation == "flags":
        d["reviewed_flags"] = []
    if mutation == "missing_alternative":
        d["context_candidates_reviewed"].pop()
    if mutation == "index":
        d["selected_context_senses"][0]["original_sense_index"] = 1
    if mutation == "record":
        d["evidence"][-1]["source_record_sha256"] = "0" * 64
    if mutation == "bundle":
        d["evidence"][-1]["bundle_sha256"] = "0" * 64
    if mutation == "scope":
        d["selected_context_senses"][0]["bounded_scope"] = ""
    if mutation == "no_lexical":
        d["evidence"][-1].update(pointer="/word", quote="추가000")
    if mutation == "approve":
        d["alignment_review"]["status"] = "equivalence_proven"
    if mutation == "partial":
        response["decisions"].pop()
    if mutation == "unknown":
        d["source_hint"] = "fabricated"
    with pytest.raises(ValueError):
        svc.validate_context_review(
            **args,
            request=Path(req["request"]),
            request_sha256=req["request_sha256"],
            response=response,
        )


def test_fingerprint_drift_and_source_drift_detected(fixture, monkeypatch):
    svc, _, args = prepare(fixture)
    original = svc._implementations
    monkeypatch.setattr(svc, "_implementations", lambda: {"changed": "0" * 64})
    with pytest.raises(ValueError, match="fingerprint"):
        svc.context_review_status(**args)
    monkeypatch.setattr(svc, "_implementations", original)
    fixture["source"].write_bytes(fixture["source"].read_bytes() + b"\n")
    with pytest.raises(ValueError, match="checksum"):
        svc.context_review_status(**args)


def test_budget_and_output_overlap_rejected(fixture, monkeypatch):
    svc = service()
    monkeypatch.setattr(svc, "MAX_LINE_BYTES", 20)
    with pytest.raises(ValueError, match="limit"):
        svc.prepare_context_review(**fixture["args"])
    with pytest.raises(ValueError):
        svc.prepare_context_review(
            **{**fixture["args"], "output": fixture["native_args"]["work"] / "forbidden"}
        )


def test_missing_indirect_reference_cannot_be_selected(fixture):
    fixture["specification"]["units"][1]["indirect_record_lines"] = [1]
    update_spec(fixture)
    svc, _, args = prepare(fixture)
    req, doc = new_request(svc, args)
    assert doc["units"][1]["indirect_records"] and not doc["units"][1]["context_candidates"]
    response = response_for(doc)
    copied = include_first(response_for(doc), doc)["decisions"][0]
    response["decisions"][1].update(
        decision="include",
        reason="general_use",
        resolved_upos="NOUN",
        selected_context_senses=copied["selected_context_senses"],
        alignment_review=copied["alignment_review"],
    )
    with pytest.raises(ValueError):
        svc.validate_context_review(
            **args,
            request=Path(req["request"]),
            request_sha256=req["request_sha256"],
            response=response,
        )


def test_structural_expansion_budget_precedes_candidate_parser(fixture, monkeypatch):
    svc = service()
    record = {
        "word": "추가000",
        "lang_code": "ko",
        "pos": "noun",
        "forms": [{"form": "x" * 1000} for _ in range(100)],
        "senses": [{"glosses": ["bounded but amplifying"]} for _ in range(128)],
    }
    fixture["source"].write_text(json.dumps(record) + "\n")
    spec = fixture["specification"]
    spec["source"]["sha256"] = sha(fixture["source"])
    spec["records"] = [
        {"physical_line": 1, "source_record_sha256": canonical_sha256(record), "candidate_ids": []}
    ]
    spec["units"][0]["record_lines"] = [1]
    prep = Path(spec["source_preparation"]["path"])
    metadata = json.loads(prep.read_text())
    metadata["dictionary_sha256"] = spec["source"]["sha256"]
    write(prep, metadata)
    spec["source_preparation"]["sha256"] = sha(prep)
    update_spec(fixture)

    def forbidden(*a, **kw):
        raise AssertionError("parser must not expand record before budget validation")

    monkeypatch.setattr(svc.vocabulary_sources, "wiktextract_record_candidates", forbidden)
    with pytest.raises(ValueError, match="structural.*limit"):
        svc.prepare_context_review(**fixture["args"])


def test_each_selected_sense_needs_its_own_literal_lexical_quote(fixture):
    svc, _, args = prepare(fixture)
    req, doc = new_request(svc, args)
    response = include_first(response_for(doc), doc)
    d = response["decisions"][0]
    c = doc["units"][0]["context_candidates"][1]
    second = {
        **d["selected_context_senses"][0],
        "candidate_id": c["candidate"]["candidate_id"],
        "original_sense_index": 1,
    }
    d["selected_context_senses"].append(second)
    d["context_candidates_reviewed"][1]["disposition"] = "compatible"
    with pytest.raises(ValueError, match="every selected sense"):
        svc.validate_context_review(
            **args,
            request=Path(req["request"]),
            request_sha256=req["request_sha256"],
            response=response,
        )


@pytest.mark.parametrize("target", ["source", "spec", "base_lock", "overlay_lock"])
def test_fifo_fails_with_post_import_operation_timeout(fixture, target):
    svc, _, args = prepare(fixture)
    if target == "overlay_lock":
        new_request(svc, args)
    paths = {
        "source": fixture["source"],
        "spec": fixture["args"]["context_spec"],
        "base_lock": fixture["native_args"]["work"] / ".operation.lock",
        "overlay_lock": args["work"] / ".operation.lock",
    }
    path = paths[target]
    path.unlink()
    os.mkfifo(path)
    program = """import signal,sys
from pathlib import Path
from multilang.services.korean_registry_context_review import context_review_status
signal.alarm(3)
try:
 context_review_status(plan=Path(sys.argv[1]),plan_sha256=sys.argv[2],work=Path(sys.argv[3]))
except (ValueError,OSError):
 print('rejected-before-timeout')
else: raise AssertionError('FIFO accepted')
finally: signal.alarm(0)
"""
    result = subprocess.run(
        [sys.executable, "-c", program, str(args["plan"]), args["plan_sha256"], str(args["work"])],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "rejected-before-timeout"


def test_parent_symlink_and_traversal_rejected(fixture, tmp_path):
    svc = service()
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    fixture["specification"]["source"]["path"] = str(alias / "source.jsonl")
    update_spec(fixture)
    with pytest.raises((ValueError, OSError)):
        svc.prepare_context_review(**fixture["args"])
    fixture["specification"]["source"]["path"] = str(tmp_path / "sub/../source.jsonl")
    update_spec(fixture)
    with pytest.raises(ValueError):
        svc.prepare_context_review(**fixture["args"])


def test_readonly_status_absent_work_does_not_create_lock(fixture):
    svc, _, args = prepare(fixture)
    assert svc.context_review_status(**args)["unreviewed_units"] == 2
    assert not args["work"].exists()


def test_homograph_marker_is_preserved_not_original_sense_index(fixture):
    unit = fixture["specification"]["units"][1]
    unit.update(
        source_index=4, source_row_id=fixture["units"][4]["source_row_id"], record_lines=[1, 2]
    )
    update_spec(fixture)
    svc, _, args = prepare(fixture)
    _, doc = new_request(svc, args)
    first, second = doc["units"]
    assert first["unit"]["source_row_id"] != second["unit"]["source_row_id"]
    assert second["unit"]["source_row"]["homograph"]["marker"] == "01"
    assert [c["original_sense_index"] for c in second["context_candidates"]] == [0, 1, 0]


def test_base_lock_held_until_overlay_publication(fixture, monkeypatch):
    svc, _, args = prepare(fixture)
    original = svc._publish
    attempts = []

    def observed(*a, **kw):
        with (fixture["native_args"]["work"] / ".operation.lock").open("rb") as handle:
            with pytest.raises(BlockingIOError):
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            attempts.append(True)
        return original(*a, **kw)

    monkeypatch.setattr(svc, "_publish", observed)
    req, doc = new_request(svc, args)
    svc.import_context_response(
        **args,
        request=Path(req["request"]),
        request_sha256=req["request_sha256"],
        response=response_for(doc),
        context_id="synthetic-lock-test",
    )
    assert len(attempts) == 2


def test_overlay_busy_not_reported_as_zero_and_response_json_budget(fixture):
    svc, _, args = prepare(fixture)
    new_request(svc, args)
    with (args["work"] / ".operation.lock").open("rb") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match="busy"):
            svc.context_review_status(**args)
    response = args["work"].parent / "large-response.json"
    response.write_bytes(b'"' + b"x" * (1024**2) + b'"')
    with pytest.raises(ValueError, match="limit"):
        svc.read_response(response)


def test_cli_full_fixture_prepare_next_validate_status(fixture):
    service()
    script = Path(__file__).parents[2] / "scripts/review_korean_registry_context.py"
    spec = importlib.util.spec_from_file_location("cli_integration", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main(
        [
            "prepare",
            *[
                value
                for key, arg in fixture["args"].items()
                for value in ("--" + key.replace("_", "-"), str(arg))
            ],
        ]
    )
    path = fixture["args"]["output"]
    common = [
        "--plan",
        str(path),
        "--plan-sha256",
        sha(path / "manifest.json"),
        "--work",
        str(path.parent / "cli-work"),
    ]
    module.main(["next", *common, "--task-id", "ko-context-0001"])
    module.main(["validate", *common])
    module.main(["status", *common])


def test_proper_name_flag_is_not_automatic_veto_but_remains_required(fixture):
    svc, _, args = prepare(fixture)
    _, doc = new_request(svc, args)
    item = doc["units"][0]
    # Pure DTO fixture: actual provenance is checked independently by campaign replay.
    item["unit"]["source_row"]["source_pos"] = "고"
    item["unit"]["flags"].append("proper_name_scope")
    for record in item["records"]:
        record["record"]["pos"] = "name"
    for candidate in item["context_candidates"]:
        candidate["candidate"]["pos"] = "PROPN"
    item["context_sha256"] = canonical_sha256(
        {k: item[k] for k in ("records", "indirect_records", "context_candidates")}
    )
    response = include_first(response_for(doc), doc)
    d = response["decisions"][0]
    d["resolved_upos"] = "PROPN"
    d["selected_context_senses"][0]["source_pos"] = "name"
    assert svc._validate_response(response, doc) == response
    d["reviewed_flags"] = [f for f in d["reviewed_flags"] if f != "proper_name_scope"]
    with pytest.raises(ValueError, match="flags"):
        svc._validate_response(response, doc)


def test_native_empty_hint_contract_is_still_closed(fixture):
    req = fixture["native_request"]
    request = json.loads((Path(req["request"]) / "request.json").read_text())
    response = copy.deepcopy(fixture["native_response"])
    response["decisions"][3].update(decision="include", reason="general_use", resolved_upos="NOUN")
    with pytest.raises(ValueError, match="hint"):
        base._response(response, request)


def test_unrelated_line_above_old_two_mib_limit_is_explicitly_supported(fixture):
    svc = service()
    original = fixture["source"].read_bytes()
    fixture["source"].write_bytes(
        original + json.dumps({"unrelated": "x" * (2 * 1024**2 + 20)}).encode() + b"\n"
    )
    spec = fixture["specification"]
    spec["source"]["sha256"] = sha(fixture["source"])
    prep = Path(spec["source_preparation"]["path"])
    metadata = json.loads(prep.read_text())
    metadata["dictionary_sha256"] = spec["source"]["sha256"]
    write(prep, metadata)
    spec["source_preparation"]["sha256"] = sha(prep)
    update_spec(fixture)
    assert svc.prepare_context_review(**fixture["args"])["context_units"] == 2


def test_swapped_source_before_open_is_rejected_anchored(fixture, monkeypatch):
    svc = service()
    original = os.open
    source = fixture["source"]
    changed = []

    def swapped(path, flags, *a, **kw):
        if str(path) == source.name and not changed:
            source.unlink()
            source.symlink_to(fixture["args"]["context_spec"])
            changed.append(True)
        return original(path, flags, *a, **kw)

    monkeypatch.setattr(os, "open", swapped)
    with pytest.raises((OSError, ValueError)):
        svc.prepare_context_review(**fixture["args"])
    assert changed


def test_aggregate_expansion_guard_precedes_second_parser(fixture, monkeypatch):
    svc = service()
    first = json.loads(fixture["source"].read_text().splitlines()[0])
    estimate = len(svc.json_bytes(first)) * len(first["senses"])
    monkeypatch.setattr(svc, "MAX_CONTEXT_EXPANSION_BYTES", estimate, raising=False)
    original = svc.vocabulary_sources.wiktextract_record_candidates
    calls = []

    def bounded(record, **kw):
        calls.append(record["pos"])
        assert len(calls) == 1, "aggregate budget must reject before second expansion"
        return original(record, **kw)

    monkeypatch.setattr(svc.vocabulary_sources, "wiktextract_record_candidates", bounded)
    with pytest.raises(ValueError, match="aggregate.*expansion"):
        svc.prepare_context_review(**fixture["args"])
    assert calls == ["noun"]


def test_required_nikl_identity_quote_cannot_be_truncated(fixture):
    svc, _, args = prepare(fixture)
    req, doc = new_request(svc, args)
    response = include_first(response_for(doc), doc)
    response["decisions"][0]["evidence"][0]["quote"] = "추"
    with pytest.raises(ValueError, match="whole.*identity"):
        svc.validate_context_review(
            **args,
            request=Path(req["request"]),
            request_sha256=req["request_sha256"],
            response=response,
        )


def test_native_writer_can_take_exclusive_lock_during_source_scan(fixture, monkeypatch):
    svc = service()
    original = svc._lines
    observed = []

    def scanning(ref):
        with (fixture["native_args"]["work"] / ".operation.lock").open("rb") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            observed.append(ref["path"])
        yield from original(ref)

    monkeypatch.setattr(svc, "_lines", scanning)
    assert svc.prepare_context_review(**fixture["args"])["context_units"] == 2
    assert len(observed) == 2


@pytest.mark.parametrize("operation", ["prepare", "next", "import"])
def test_new_native_review_during_scan_prevents_overlay_publication(
    fixture, monkeypatch, operation
):
    svc = service()
    args = None
    if operation != "prepare":
        svc, _, args = prepare(fixture)
    if operation == "import":
        req, doc = new_request(svc, args)
    original = svc._lines
    changed = []
    before = {p: sha(p) for p in args["work"].rglob("*") if p.is_file()} if args else {}

    def scanning(ref):
        if not changed:
            native_req = fixture["native_request"]
            review = next(
                (fixture["native_args"]["work"] / "tasks/ko-pending-0001/reviews").glob("review-*")
            )
            response = copy.deepcopy(fixture["native_response"])
            response["decisions"][3]["notes"] = "Changed during external source scan."
            base.import_registry_response(
                **fixture["native_args"],
                task_id="ko-pending-0001",
                request=Path(native_req["request"]),
                request_sha256=native_req["request_sha256"],
                response=response,
                context_id="synthetic-concurrent",
                supersedes=review,
            )
            changed.append(True)
        yield from original(ref)

    monkeypatch.setattr(svc, "_lines", scanning)
    with pytest.raises(ValueError, match="base.*changed"):
        if operation == "prepare":
            svc.prepare_context_review(**fixture["args"])
        elif operation == "next":
            svc.next_context_request(**args, task_id="ko-context-0001")
        else:
            svc.import_context_response(
                **args,
                request=Path(req["request"]),
                request_sha256=req["request_sha256"],
                response=response_for(doc),
                context_id="synthetic-stale",
            )
    assert changed
    if operation == "prepare":
        assert not fixture["args"]["output"].exists()
    elif before:
        assert before == {p: sha(p) for p in before}
    if args and (args["work"] / "reviews").exists():
        assert not list((args["work"] / "reviews").glob("review-*"))


@pytest.mark.parametrize("mutation", ["rewrite", "remove", "unexpected_lock", "symlink", "fifo"])
def test_selected_task_vector_rejects_mutation_during_scan(fixture, monkeypatch, mutation):
    svc = service()
    original = svc._lines
    changed = []
    reqfile = Path(fixture["native_request"]["request"]) / "request.json"

    def scanning(ref):
        if not changed:
            if mutation == "rewrite":
                reqfile.write_bytes(reqfile.read_bytes() + b" ")
            if mutation == "remove":
                reqfile.unlink()
            if mutation == "unexpected_lock":
                (reqfile.parent / "literal.lock").write_text("not a control file")
            if mutation == "symlink":
                reqfile.unlink()
                reqfile.symlink_to(fixture["source"])
            if mutation == "fifo":
                reqfile.unlink()
                os.mkfifo(reqfile)
            changed.append(True)
        yield from original(ref)

    monkeypatch.setattr(svc, "_lines", scanning)
    with pytest.raises((ValueError, OSError)):
        svc.prepare_context_review(**fixture["args"])
    assert not fixture["args"]["output"].exists()


def test_native_vector_byte_budget_rejects_before_publication(fixture, monkeypatch):
    svc = service()
    monkeypatch.setattr(svc, "MAX_BASE_SNAPSHOT_BYTES", 8, raising=False)
    with pytest.raises(ValueError, match="snapshot.*limit"):
        svc.prepare_context_review(**fixture["args"])
    assert not fixture["args"]["output"].exists()


@pytest.mark.parametrize("fixture", [10], indirect=True)
def test_new_native_completion_in_selected_task_prevents_publish(fixture, monkeypatch):
    svc = service()
    original = svc._lines
    changed = []

    def scanning(ref):
        if not changed:
            req = base.next_registry_request(**fixture["native_args"], task_id="ko-pending-0001")
            doc = json.loads((Path(req["request"]) / "request.json").read_text())
            decisions = []
            for i, unit in enumerate(doc["units"]):
                row = unit["source_row"]
                decisions.append(
                    {
                        "i": i,
                        "source_row_id": row["source_row_id"],
                        "decision": "uncertain",
                        "reason": "insufficient_evidence",
                        "resolved_upos": None,
                        "reviewed_flags": unit["flags"],
                        "evidence": [
                            {
                                "field": "source_pos",
                                "quote": row["source_pos"],
                                "source_row_id": row["source_row_id"],
                                "source_line_utf8_sha256": row["source_line_utf8_sha256"],
                            }
                        ],
                        "notes": "Synthetic later completion.",
                    }
                )
            base.import_registry_response(
                **fixture["native_args"],
                task_id="ko-pending-0001",
                request=Path(req["request"]),
                request_sha256=req["request_sha256"],
                response={"decisions": decisions},
                context_id="synthetic-later-completion",
            )
            changed.append(True)
        yield from original(ref)

    monkeypatch.setattr(svc, "_lines", scanning)
    with pytest.raises(ValueError, match="base.*changed"):
        svc.prepare_context_review(**fixture["args"])
    assert changed and not fixture["args"]["output"].exists()


def test_base_snapshot_time_budget_fails_closed(fixture, monkeypatch):
    svc = service()
    monkeypatch.setattr(svc, "MAX_BASE_LOCK_SECONDS", -1)
    with pytest.raises(ValueError, match="snapshot time"):
        svc.prepare_context_review(**fixture["args"])
    assert not fixture["args"]["output"].exists()
