"""Bind offline vocabulary review proposals to an immutable inventory snapshot."""

from __future__ import annotations

import copy

from multilang.services.vocabulary_adjudication import _hash

_MUTABLE = frozenset(
    {"decision", "resolved_content", "human_approved", "production_eligible", "generation_status"}
)
_SETTLED = frozenset({"retained", "omitted", "excluded"})


def _candidate_key(candidate):
    return (
        candidate.get("resolved_candidate_id")
        or candidate.get("derived_candidate_id")
        or candidate.get("source_candidate_id")
    )


def apply_proposal(old, proposed, baseline_sha256, proposed_sha256):
    """Accept a complete review row only when its history and source are intact."""
    if _hash(old) != baseline_sha256 or _hash(proposed) != proposed_sha256:
        raise ValueError("proposal row hash or baseline row hash differs")
    if (
        old.get("language") != proposed.get("language")
        or old.get("review_unit_id") != proposed.get("review_unit_id")
    ):
        raise ValueError("proposal language or review unit differs")
    if {k: v for k, v in old.items() if k not in _MUTABLE} != {
        k: v for k, v in proposed.items() if k not in _MUTABLE
    }:
        raise ValueError("proposal changes native source fields")
    resolution = proposed.get("resolved_content")
    if not isinstance(resolution, dict) or resolution.get("previous_resolution") != old.get(
        "resolved_content"
    ):
        raise ValueError("proposal loses previous resolution")
    if (
        proposed.get("human_approved") is not False
        or proposed.get("production_eligible") is not False
        or proposed.get("generation_status") != "deferred_by_user"
    ):
        raise ValueError("proposal cannot approve production or generation")
    new_candidates = resolution.get("resolved_candidates", [])
    if not isinstance(new_candidates, list):
        raise ValueError("invalid proposal candidates")
    by_key = {_candidate_key(c): c for c in new_candidates}
    if None in by_key or len(by_key) != len(new_candidates):
        raise ValueError("duplicate or unbound proposed candidates")
    prior = (old.get("resolved_content") or {}).get("resolved_candidates", [])
    for candidate in prior:
        if candidate.get("disposition") not in _SETTLED:
            continue
        replacement = by_key.get(_candidate_key(candidate))
        if replacement is None:
            raise ValueError("proposal drops a settled candidate")
        for field in ("disposition", "lemma", "pos", "display"):
            if candidate.get(field) != replacement.get(field):
                raise ValueError("proposal changes a settled candidate")
    return copy.deepcopy(proposed)
