"""Reviews from the current assistant session are source-bound single passes."""

import hashlib
import json

import pytest

from multilang.domain.lexical_identity import canonical_sha256


def _source(tmp_path):
    groups = []
    for i in range(2):
        groups.append({
            "entry_id": f"e{i}", "review_unit_id": f"e{i}#fragment-0000",
            "source_group_fragment_index": 0, "source_group_fragment_count": 1,
            "lemma": f"word{i}", "pos": "NOUN", "source_priority": i + 1,
            "sense_candidates": [{"candidate_id": f"s{i}", "glosses": ["source meaning"]}],
            "forms_for_review": [], "readings": [],
        })
    data = {"language": "en", "groups": groups, "generation_status": "deferred_by_user"}
    data["packet_sha256"] = canonical_sha256(data)
    path = tmp_path / "packet.json"
    path.write_text(json.dumps(data))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _response():
    return {"decisions": [{"i": 0, "decision": "include", "senses": [0],
                            "display": "word1", "pos": None, "forms": [],
                            "reason": "general_use"}]}


def test_session_response_is_a_single_proposal_without_paid_calls_or_human_approval(tmp_path):
    from multilang.services.vocabulary_session_review import (
        export_session_request,
        import_session_review,
    )

    path, digest = _source(tmp_path)
    request = tmp_path / "request"
    exported = export_session_request(path, digest, indices=[1], output=request)
    args = dict(request=request, request_sha256=exported["request_sha256"], response=_response(),
                context_id="fixture-session", output=tmp_path / "result")
    result = import_session_review(**args)
    assert result["decisions"][0]["entry_id"] == "e1"
    assert result["decisions"][0]["selected_candidate_ids"] == ["s1"]
    assert result["review_status"] == "single_session_proposal"
    assert result["independent_passes"] == 0
    assert result["provider_calls_executed"] == 0
    assert result["human_approved"] is False
    assert result["production_eligible"] is False
    assert import_session_review(**args) == result


def test_session_review_rejects_forged_indices_source_edits_and_overwrite(tmp_path):
    from multilang.services.vocabulary_session_review import (
        export_session_request,
        import_session_review,
    )

    path, digest = _source(tmp_path)
    request = tmp_path / "request"
    exported = export_session_request(path, digest, indices=[1], output=request)
    bad = _response()
    bad["decisions"][0]["senses"] = [99]
    args = dict(request=request, request_sha256=exported["request_sha256"], context_id="fixture-session",
                output=tmp_path / "result")
    with pytest.raises(ValueError, match="absent"):
        import_session_review(**args, response=bad)
    import_session_review(**args, response=_response())
    bad = _response()
    bad["decisions"][0].update(decision="exclude", senses=[])
    with pytest.raises(ValueError, match="drift"):
        import_session_review(**args, response=bad)
    (request / "request.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        import_session_review(**args, response=_response())


def test_session_request_cannot_repeat_units_or_claim_a_different_source(tmp_path):
    from multilang.services.vocabulary_session_review import export_session_request

    path, digest = _source(tmp_path)
    for indices in ([], [0, 0], [5], [True]):
        with pytest.raises(ValueError):
            export_session_request(path, digest, indices=indices, output=tmp_path / "out")
    path.write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        export_session_request(path, digest, indices=[0], output=tmp_path / "out")


@pytest.mark.parametrize("change", ["approval", "selected_sense"])
def test_rehashed_result_cannot_upgrade_authority_or_forge_the_response(tmp_path, change):
    from multilang.services.vocabulary_session_review import (
        export_session_request,
        import_session_review,
        load_session_review,
    )

    path, digest = _source(tmp_path)
    request, output = tmp_path / "request", tmp_path / "review"
    exported = export_session_request(path, digest, indices=[1], output=request)
    import_session_review(request=request, request_sha256=exported["request_sha256"],
                          response=_response(), context_id="fixture", output=output)
    result_path = output / "result.json"
    result = json.loads(result_path.read_text())
    if change == "approval":
        result["human_approved"] = True
    else:
        result["decisions"][0]["selected_candidate_ids"] = ["forged-sense"]
    result_path.write_text(json.dumps(result))
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["result.json"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="authority|replay"):
        load_session_review(request=request, output=output)
