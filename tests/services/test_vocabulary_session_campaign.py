"""Session work remains resumable, source-bound and visibly incomplete."""

import hashlib
import json
from pathlib import Path

import pytest

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.vocabulary_session_review import import_session_review


def _catalog(tmp_path, *, fragments=False):
    root = tmp_path / "packets"
    (root / "en").mkdir(parents=True)
    groups = [{
        "entry_id": "e0" if fragments else f"e{i}",
        "review_unit_id": f"unit{i}",
        "source_group_fragment_index": i if fragments else 0,
        "source_group_fragment_count": 2 if fragments else 1,
        "lemma": "cat" if fragments else ("cat", "dog")[i], "pos": "NOUN",
        "source_priority": i + 1,
        "sense_candidates": [{"candidate_id": f"s{i}", "glosses": ["animal"]}],
        "forms_for_review": [], "readings": [],
    } for i in range(2)]
    packet = {"language": "en", "generation_status": "deferred_by_user", "groups": groups}
    packet["packet_sha256"] = canonical_sha256(packet)
    content = json.dumps(packet).encode()
    digest = hashlib.sha256(content).hexdigest()
    (root / "en/00000.json").write_bytes(content)
    count = 1 if fragments else 2
    summary = {
        "generation_status": "deferred_by_user", "source_manifest_sha256": "a" * 64,
        "entry_count": count, "review_unit_count": 2, "packet_count": 1,
        "languages": [{"language": "en", "entry_count": count, "review_unit_count": 2,
                       "packet_count": 1, "packets": [{"path": "en/00000.json", "sha256": digest,
                                                        "entries": 2}]}],
    }
    summary_bytes = json.dumps(summary).encode()
    (root / "summary.json").write_bytes(summary_bytes)
    (root / "manifest.json").write_text(json.dumps({"files": {
        "en/00000.json": digest, "summary.json": hashlib.sha256(summary_bytes).hexdigest(),
    }}))
    return dict(packets=root, manifest_sha256=hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest(),
                requests=tmp_path / "requests", reviews=tmp_path / "reviews")


def _respond(request, reviews, *, decision="include"):
    group = json.loads((Path(request["request"]) / "request.json").read_text())["groups"][0]
    response = {"decisions": [{"i": 0, "decision": decision, "senses": [0] if decision == "include" else [],
                                "display": group["lemma"], "pos": None, "forms": [],
                                "reason": "general_use" if decision == "include" else "insufficient_evidence"}]}
    return import_session_review(request=Path(request["request"]), request_sha256=request["request_sha256"],
                                 response=response, context_id="test-session", output=reviews / request["request_sha256"])


def test_next_reuses_pending_request_then_advances_without_provider_calls(tmp_path):
    from multilang.services.vocabulary_session_campaign import (
        prepare_next_session_review,
        session_progress,
    )

    args = _catalog(tmp_path)
    first = prepare_next_session_review(**args, language="en", batch_size=1)
    assert first["source_indices"] == [0]
    assert prepare_next_session_review(**args, language="en", batch_size=1) == first
    _respond(first, args["reviews"])
    second = prepare_next_session_review(**args, language="en", batch_size=1)
    assert second["source_indices"] == [1]
    summary, proposals = session_progress(**args)
    assert summary["reviewed_units"] == 1
    assert summary["unreviewed_units"] == 1
    assert summary["completed_source_groups"] == 1
    assert summary["proposal_include_units"] == 1
    assert summary["provider_calls_executed"] == 0
    assert summary["production_eligible"] is False
    assert summary["coverage_90_percent_verified"] is False
    assert proposals["en"][0]["selected_candidate_ids"] == ["s0"]
    _respond(second, args["reviews"], decision="uncertain")
    assert prepare_next_session_review(**args, language="en", batch_size=1)["status"] == "first_pass_complete"
    summary, _ = session_progress(**args)
    assert summary["unreviewed_units"] == 0
    assert summary["proposal_uncertain_units"] == 1
    assert summary["review_status"] == "single_session_proposals_require_validation"


def test_source_fragments_are_not_counted_as_completed_lexical_identities(tmp_path):
    from multilang.services.vocabulary_session_campaign import (
        prepare_next_session_review,
        session_progress,
    )

    args = _catalog(tmp_path, fragments=True)
    first = prepare_next_session_review(**args, language="en", batch_size=1)
    _respond(first, args["reviews"])
    summary, _ = session_progress(**args)
    assert summary["reviewed_units"] == 1
    assert summary["completed_source_groups"] == 0
    assert summary["touched_source_groups"] == 1


def test_checksums_do_not_allow_copied_request_content_to_change_source(tmp_path):
    from multilang.services.vocabulary_session_campaign import (
        prepare_next_session_review,
        session_progress,
    )

    args = _catalog(tmp_path)
    first = prepare_next_session_review(**args, language="en", batch_size=1)
    folder = Path(first["request"])
    path = folder / "request.json"
    data = json.loads(path.read_text())
    data["groups"][0]["lemma"] = "changed"
    path.write_text(json.dumps(data))
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["binding_sha256"] = canonical_sha256(data)
    manifest["files"]["request.json"] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="source packet"):
        session_progress(**args)


def test_catalog_paths_and_stale_review_cannot_be_used(tmp_path):
    from multilang.services.vocabulary_session_campaign import (
        prepare_next_session_review,
        session_progress,
    )

    args = _catalog(tmp_path)
    first = prepare_next_session_review(**args, language="en", batch_size=1)
    _respond(first, args["reviews"])
    result = args["reviews"] / first["request_sha256"] / "result.json"
    result.write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        session_progress(**args)
    with pytest.raises(ValueError):
        prepare_next_session_review(**args, language="../", batch_size=1)


def test_explicit_correction_supersedes_a_proposal_without_erasing_history(tmp_path):
    from multilang.services.vocabulary_session_campaign import (
        prepare_next_session_review,
        session_progress,
    )

    args = _catalog(tmp_path)
    request = prepare_next_session_review(**args, language="en", batch_size=1)
    _respond(request, args["reviews"])
    original = args["reviews"] / request["request_sha256"]
    response = {"decisions": [{"i": 0, "decision": "exclude", "senses": [], "display": "cat",
                                "pos": None, "forms": [], "reason": "duplicate_variant"}]}
    correction = import_session_review(
        request=Path(request["request"]), request_sha256=request["request_sha256"],
        response=response, context_id="test-correction", supersedes=original,
        output=args["reviews"] / "corrected",
    )
    assert correction["supersedes_review_sha256"]
    assert json.loads((original / "result.json").read_text())["decisions"][0]["decision"] == "include"
    summary, rows = session_progress(**args)
    assert summary["reviewed_units"] == 1
    assert summary["proposal_include_units"] == 0
    assert summary["proposal_exclude_units"] == 1
    assert rows["en"][0]["selected_candidate_ids"] == []
    assert summary["production_eligible"] is False
    # Two competing corrections must not silently choose the latest directory.
    import_session_review(
        request=Path(request["request"]), request_sha256=request["request_sha256"],
        response=response, context_id="conflicting-correction", supersedes=original,
        output=args["reviews"] / "other-correction",
    )
    with pytest.raises(ValueError, match="reconciliation"):
        session_progress(**args)
