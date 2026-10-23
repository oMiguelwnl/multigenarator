import copy

import pytest

from multilang.services.vocabulary_adjudication import _hash
from multilang.services.vocabulary_continuation_composition import apply_addition, apply_proposal


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


def _addition():
    candidate = dict(candidate_id="candidate:one", source_record_sha256="a" * 64)
    return dict(
        language="cs", review_unit_id="supplemental-parent:one#fragment-0000",
        origin="supplemental_recovered_parent_preparation", decision="include",
        source_group=dict(entry_id="supplemental-parent:one", review_unit_id="supplemental-parent:one#fragment-0000", lemma="one", pos="ADJ", sense_candidates=[candidate]),
        source_binding=dict(source_record_sha256="a" * 64, recovery_manifest_sha256="b" * 64, source_license="CC BY-SA"),
        resolved_content=dict(resolved_candidates=[dict(source_candidate_id="candidate:one", disposition="retained", lemma="one", pos="ADJ")], unresolved_questions=[]),
        human_approved=False, production_eligible=False, selected_for_card=False,
        generation_status="deferred_by_user",
    )


def test_addition_requires_explicit_pinned_lexical_parent():
    row = _addition()
    assert apply_addition(row, _hash(row), "a" * 64, "b" * 64) == row


@pytest.mark.parametrize("damage", ["hash", "origin", "decision", "approval", "source", "recovery", "candidate", "pending"])
def test_addition_rejects_missing_provenance_or_unreviewed_parent(damage):
    row = _addition()
    proposal_hash = _hash(row)
    source_hash, recovery_hash = "a" * 64, "b" * 64
    if damage == "hash":
        proposal_hash = "0" * 64
    elif damage == "origin":
        row["origin"] = "unknown"
        proposal_hash = _hash(row)
    elif damage == "decision":
        row["decision"] = "uncertain"
        proposal_hash = _hash(row)
    elif damage == "approval":
        row["production_eligible"] = True
        proposal_hash = _hash(row)
    elif damage == "source":
        source_hash = "0" * 64
    elif damage == "recovery":
        recovery_hash = "0" * 64
    elif damage == "candidate":
        row["resolved_content"]["resolved_candidates"][0]["source_candidate_id"] = "other"
        proposal_hash = _hash(row)
    else:
        row["resolved_content"]["unresolved_questions"] = ["unknown"]
        proposal_hash = _hash(row)
    with pytest.raises(ValueError):
        apply_addition(row, proposal_hash, source_hash, recovery_hash)
