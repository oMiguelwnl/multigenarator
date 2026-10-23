import copy

import pytest

from multilang.services.vocabulary_adjudication import _hash
from multilang.services.vocabulary_continuation_composition import apply_proposal


def _row():
    return dict(
        language="ro", review_unit_id="u", decision="uncertain",
        source_group=dict(lemma="x", sense_candidates=[dict(candidate_id="c")]),
        imported_review=dict(decision="uncertain"),
        resolved_content=dict(
            resolved_candidates=[dict(source_candidate_id="old", disposition="retained", lemma="x", pos="NOUN", display="x")],
            unresolved_questions=["review"],
        ),
        human_approved=False, production_eligible=False,
        generation_status="deferred_by_user",
    )


def _proposal(old):
    new = copy.deepcopy(old)
    new["decision"] = "include"
    new["resolved_content"] = dict(
        previous_resolution=copy.deepcopy(old["resolved_content"]),
        resolved_candidates=[
            copy.deepcopy(old["resolved_content"]["resolved_candidates"][0]),
            dict(source_candidate_id="new", disposition="retained", lemma="y", pos="NOUN", display="y"),
        ],
        unresolved_questions=[],
    )
    return new


def test_proposal_preserves_native_row_and_prior_decisions():
    old = _row()
    new = _proposal(old)
    assert apply_proposal(old, new, _hash(old), _hash(new)) == new
    assert old["decision"] == "uncertain"


@pytest.mark.parametrize("damage", ["old_hash", "new_hash", "native", "history", "retained", "approval", "uid"])
def test_proposal_rejects_unbound_or_destructive_change(damage):
    old = _row()
    new = _proposal(old)
    old_hash, new_hash = _hash(old), _hash(new)
    if damage == "old_hash":
        old_hash = "0" * 64
    elif damage == "new_hash":
        new_hash = "0" * 64
    elif damage == "native":
        new["source_group"]["lemma"] = "forged"
        new_hash = _hash(new)
    elif damage == "history":
        new["resolved_content"]["previous_resolution"] = {}
        new_hash = _hash(new)
    elif damage == "retained":
        new["resolved_content"]["resolved_candidates"][0]["disposition"] = "excluded"
        new_hash = _hash(new)
    elif damage == "approval":
        new["production_eligible"] = True
        new_hash = _hash(new)
    else:
        new["review_unit_id"] = "other"
        new_hash = _hash(new)
    with pytest.raises(ValueError):
        apply_proposal(old, new, old_hash, new_hash)
