"""Resolve pinned spelling aliases into an offline, sense-scoped preparation view.

This pure function performs no I/O. Callers must verify the inventory/proposal
file hashes and the raw-file provenance before supplying records. Hashes bind
content; they are not approval signatures. Native review objects are preserved.
"""

from __future__ import annotations

from copy import deepcopy

from multilang.domain.lexical_identity import canonical_sha256


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _raw(binding, records):
    key = binding["source_record_sha256"]
    envelope = records[key]
    _require(envelope["binding"] == binding, "raw source binding mismatch")
    raw = envelope["raw"]
    _require(canonical_sha256(raw) == key, "stale raw source")
    return raw


def resolve_scoped_alias(row, proposal, raw_records):
    """Return a new snapshot row, accepting only explicitly pinned target senses.

    ``raw_records`` maps canonical raw hashes to ``{raw, binding}`` envelopes.
    Binding includes exact source file/path/locator and evidence file pins from
    the proposal. This deliberately cannot open paths supplied by a proposal.
    Malformed, stale or conflicting input raises ValueError; no fallback exists.
    """
    try:
        return _resolve(row, proposal, raw_records)
    except (KeyError, TypeError, IndexError, AttributeError) as exc:
        raise ValueError("incomplete or malformed scoped alias evidence") from exc


def _resolve(row, proposal, raw_records):
    payload = {k: v for k, v in proposal.items() if k != "proposal_id"}
    _require(
        proposal["proposal_id"] == "scoped-alias:" + canonical_sha256(payload),
        "proposal hash mismatch",
    )
    _require(
        proposal["schema_version"] == "scoped-alias-resolution-proposal-1",
        "unsupported proposal schema",
    )
    _require(proposal["proposed_action"] == "include_derived_scoped_alias", "unsupported action")
    _require(
        proposal["production_eligible"] is False
        and proposal["generation_status"] == "deferred_by_user",
        "proposal is not preparation-only",
    )
    _require(
        proposal["baseline_decision"] == row["decision"] == "uncertain",
        "baseline decision mismatch",
    )
    _require(
        proposal["inventory_record_sha256"] == canonical_sha256(row), "inventory row hash mismatch"
    )
    _require(proposal["inventory_record_id"] == row["record_id"], "record identity mismatch")
    _require(proposal["review_unit_id"] == row["review_unit_id"], "review unit mismatch")
    _require(proposal["language"] == row["language"], "language mismatch")
    _require(
        not row.get("resolved_content") and proposal["forms"] == [],
        "unexpected previous resolution or forms",
    )
    review, group = row["imported_review"], row["source_group"]
    _require(
        review["review_sha256"] == proposal["native_review_binding_sha256"], "review hash mismatch"
    )
    _require(review["request_sha256"] == proposal["native_request_sha256"], "request hash mismatch")
    _require(
        review["review_unit_id"] == group["review_unit_id"] == row["review_unit_id"],
        "native unit mismatch",
    )
    _require(review["entry_id"] == group["entry_id"], "native entry mismatch")
    alias, target = proposal["alias"], proposal["target"]
    candidates = group["sense_candidates"]
    _require(len(candidates) == 1, "scoped alias requires one original candidate")
    candidate = candidates[0]
    _require(candidate["candidate_id"] == alias["candidate_id"], "candidate identity mismatch")
    _require(canonical_sha256(candidate) == alias["candidate_sha256"], "candidate hash mismatch")
    _require(
        candidate["source_record_sha256"] == alias["raw_binding"]["source_record_sha256"],
        "candidate raw mismatch",
    )
    a, t = _raw(alias["raw_binding"], raw_records), _raw(target["raw_binding"], raw_records)
    _require(a["lang_code"] == t["lang_code"] == row["language"], "raw language mismatch")
    _require(
        a["word"] == alias["lemma"] == group["lemma"] == proposal["display"],
        "alias identity mismatch",
    )
    _require(t["word"] == target["lemma"] == alias["target_word"], "target identity mismatch")
    _require(alias["lemma"] != target["lemma"], "self alias is not a resolution")
    _require(alias["pos"] == target["pos"] == group["pos"], "POS mismatch")
    _require(a["pos"].upper() == t["pos"].upper() == alias["pos"], "raw POS mismatch")
    _require(alias["relation"] == "US standard spelling of", "unsupported alias relation")
    i = alias["source_sense_index"]
    _require(type(i) is int and 0 <= i < len(a["senses"]), "invalid alias sense index")
    _require(
        any(v.get("word") == t["word"] for v in a["senses"][i].get("alt_of", [])),
        "explicit alt_of relation missing",
    )
    _require(
        any(
            v.get("form") == a["word"] and "alternative" in v.get("tags", [])
            for v in t.get("forms", [])
        ),
        "inverse spelling evidence missing",
    )
    indices, selected = target["allowed_raw_sense_indices"], target["selected_senses"]
    _require(isinstance(indices, list) and bool(indices), "empty target scope")
    _require(
        all(type(i) is int and 0 <= i < len(t["senses"]) for i in indices),
        "invalid target sense index",
    )
    _require(len(set(indices)) == len(indices), "duplicate target sense index")
    _require(
        [s["raw_sense_index"] for s in selected] == indices,
        "target scope does not match selected senses",
    )
    _require(
        target["rejected_raw_sense_indices"]
        == [i for i in range(len(t["senses"])) if i not in indices],
        "excluded target scope mismatch",
    )
    for i, sense in zip(indices, selected, strict=True):
        _require(sense["source_sense"] == t["senses"][i], "target sense content mismatch")
        _require(
            sense["source_sense_sha256"] == canonical_sha256(t["senses"][i]),
            "target sense hash mismatch",
        )
    result = deepcopy(row)
    result.update(
        decision="include",
        human_approved=False,
        production_eligible=False,
        generation_status="deferred_by_user",
    )
    result["resolved_content"] = dict(
        schema_version="scoped-alias-resolution-1",
        baseline_inventory_record_sha256=proposal["inventory_record_sha256"],
        resolved_candidates=[
            dict(
                source_candidate_id=candidate["candidate_id"],
                lemma=alias["lemma"],
                pos=alias["pos"],
                display=proposal["display"],
                disposition="retained",
                evidence=[deepcopy(proposal)],
                target_scope=deepcopy(target),
            )
        ],
        resolved_forms=dict(selected_forms=[], source_forms=[]),
        unresolved_questions=[],
        native_review_unchanged=True,
        frequency_rank=None,
        frequency_status="pending_qualified_evidence",
    )
    return result
