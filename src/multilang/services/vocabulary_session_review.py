"""Import source-bound reviews from the current session without calling an API.

This records a single assistant proposal. It never synthesizes a second pass,
claims human approval, changes provider settings or starts card generation.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.qualification_machine_runner import (
    json_bytes,
    persist_artifact,
    read_json,
    verify_artifact,
)
from multilang.services.vocabulary_curation import (
    SelectionResponse,
    selection_messages,
    validate_selections,
)
from multilang.services.vocabulary_review import _plain_path


def _review_binding(request, response, context_id, supersedes=None):
    payload = {"request": request, "response": response, "context_id": context_id,
               "policy": "single-session-proposal-1"}
    if supersedes is not None:
        payload.update(policy="single-session-proposal-revision-1", supersedes=supersedes)
    return canonical_sha256(payload)


def export_session_request(
    packet: Path, packet_sha256: str, *, indices: list[int], output: Path,
) -> dict:
    data = read_json(packet, packet_sha256)
    if data.get("packet_sha256") != canonical_sha256(
        {key: value for key, value in data.items() if key != "packet_sha256"}
    ):
        raise ValueError("packet canonical binding mismatch")
    if data.get("generation_status") != "deferred_by_user":
        raise ValueError("selection must remain separate from generation")
    if (not 1 <= len(indices) <= 64 or any(type(i) is not int for i in indices)
            or len(set(indices)) != len(indices)
            or any(i < 0 or i >= len(data["groups"]) for i in indices)):
        raise ValueError("session review needs distinct valid source indices")
    groups = [data["groups"][i] for i in indices]
    if any(not g.get("review_unit_id") for g in groups):
        raise ValueError("session review requires source review unit identities")
    request = {
        "schema_version": "vocabulary-session-request-1",
        "language": data["language"], "packet_sha256": packet_sha256,
        "source_indices": indices, "groups": groups,
        "generation_status": "deferred_by_user",
        "response_schema": SelectionResponse.model_json_schema(),
        "messages": selection_messages(data["language"], groups),
    }
    digest = canonical_sha256(request)
    persist_artifact(output, kind="vocabulary-session-request", binding=digest, files={
        "request.json": json_bytes(request),
        "messages.json": json_bytes(request["messages"]),
        "response-schema.json": json_bytes(request["response_schema"]),
    })
    return {"request_sha256": digest, "group_count": len(groups), "provider_calls_executed": 0}


def import_session_review(
    *, request: Path, request_sha256: str, response: dict, context_id: str, output: Path,
    supersedes: Path | None = None,
) -> dict:
    if not re.fullmatch(r"[a-zA-Z0-9_.:-]{1,256}", context_id):
        raise ValueError("invalid session context identifier")
    manifest = verify_artifact(request, kind="vocabulary-session-request")
    data = read_json(request / "request.json")
    if manifest["binding_sha256"] != request_sha256 or canonical_sha256(data) != request_sha256:
        raise ValueError("session request binding changed")
    if data.get("generation_status") != "deferred_by_user":
        raise ValueError("generation must remain deferred")
    decisions = validate_selections(data["groups"], response)
    response = {"decisions": [row.model_dump(mode="json") for row in decisions]}
    previous_digest = None
    if supersedes is not None:
        load_session_review(request=request, output=supersedes)
        previous_digest = verify_artifact(supersedes, kind="vocabulary-session-review")["binding_sha256"]
    binding = _review_binding(request_sha256, response, context_id, previous_digest)
    output = _plain_path(output)
    if output.exists():
        existing = verify_artifact(output, kind="vocabulary-session-review")
        if existing["binding_sha256"] != binding:
            raise ValueError("session review input/output drift")
        return load_session_review(request=request, output=output)
    result = {
        "schema_version": "vocabulary-session-review-1",
        "language": data["language"], "packet_sha256": data["packet_sha256"],
        "request_sha256": request_sha256, "context_id": context_id,
        "executed_at": datetime.now(UTC).isoformat(),
        "execution_surface": "current_assistant_session", "model_revision": None,
        "input_tokens": None, "output_tokens": None,
        "review_status": "single_session_proposal", "independent_passes": 0,
        "provider_calls_executed": 0, "human_approved": False, "production_eligible": False,
        "generation_status": "deferred_by_user",
        "new_card_texts": 0, "new_translations": 0, "new_audio": 0, "new_decks": 0,
        "decisions": _decision_rows(data["groups"], decisions),
    }
    if previous_digest is not None:
        result["supersedes_review_sha256"] = previous_digest
    persist_artifact(output, kind="vocabulary-session-review", binding=binding, files={
        "result.json": json_bytes(result), "response.json": json_bytes(response),
    })
    return result


def _decision_rows(groups, decisions):
    rows = []
    for group, decision in zip(groups, decisions, strict=True):
        rows.append({
            "entry_id": group["entry_id"], "review_unit_id": group["review_unit_id"],
            "source_group_fragment_index": group["source_group_fragment_index"],
            "source_group_fragment_count": group["source_group_fragment_count"],
            "lemma": group["lemma"], "pos": decision.pos or group["pos"],
            "display": decision.display, "decision": decision.decision, "reason": decision.reason,
            "source_priority": group.get("source_priority"),
            "reviewed_candidate_ids": [s["candidate_id"] for s in group["sense_candidates"]],
            "selected_candidate_ids": [group["sense_candidates"][i]["candidate_id"]
                                       for i in decision.senses],
            "selected_forms": [{
                "form_id": group["forms_for_review"][f.f]["form_id"],
                "form": group["forms_for_review"][f.f]["form"],
                "parent_candidate_id": group["sense_candidates"][f.s]["candidate_id"],
                "reason": f.reason,
            } for f in decision.forms],
            "status": "session_proposal_" + decision.decision,
            "human_approved": False, "production_eligible": False,
        })
    return rows


def load_session_review(*, request: Path, output: Path) -> dict:
    """Replay a saved response; matching file hashes alone are not approval."""
    request_manifest = verify_artifact(request, kind="vocabulary-session-request")
    data = read_json(request / "request.json")
    digest = canonical_sha256(data)
    if request_manifest["binding_sha256"] != digest:
        raise ValueError("session request binding changed")
    manifest = verify_artifact(output, kind="vocabulary-session-review")
    result = read_json(output / "result.json")
    response = read_json(output / "response.json")
    decisions = validate_selections(data["groups"], response)
    context_id = result.get("context_id", "")
    if not isinstance(context_id, str) or not re.fullmatch(r"[a-zA-Z0-9_.:-]{1,256}", context_id):
        raise ValueError("invalid session context identifier")
    previous_digest = result.get("supersedes_review_sha256")
    if previous_digest is not None and (
        not isinstance(previous_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", previous_digest)
    ):
        raise ValueError("invalid superseded session review binding")
    expected = _review_binding(digest, response, context_id, previous_digest)
    if manifest["binding_sha256"] != expected or result.get("request_sha256") != digest:
        raise ValueError("session result binding changed")
    constants = {
        "schema_version": "vocabulary-session-review-1", "language": data["language"],
        "packet_sha256": data["packet_sha256"], "execution_surface": "current_assistant_session",
        "review_status": "single_session_proposal", "independent_passes": 0,
        "provider_calls_executed": 0, "human_approved": False, "production_eligible": False,
        "generation_status": "deferred_by_user", "new_card_texts": 0, "new_translations": 0,
        "new_audio": 0, "new_decks": 0,
    }
    if data.get("generation_status") != "deferred_by_user" or any(
        type(result.get(key)) is not type(value) or result.get(key) != value
        for key, value in constants.items()
    ):
        raise ValueError("session result authority or generation drift")
    if result.get("decisions") != _decision_rows(data["groups"], decisions):
        raise ValueError("session decisions do not replay from their source response")
    return result
