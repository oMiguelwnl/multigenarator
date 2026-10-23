"""Immutable native records, exact scope binding and no broad alias transfer."""

import copy
import importlib
import importlib.util

import pytest

from multilang.domain.lexical_identity import canonical_sha256 as digest

MODULE = "multilang.services.vocabulary_scoped_alias"


def seal(p):
    p.pop("proposal_id", None)
    p["proposal_id"] = "scoped-alias:" + digest(p)


@pytest.fixture
def evidence():
    a = dict(word="color", lang_code="en", pos="noun", senses=[dict(alt_of=[dict(word="colour")])])
    t = dict(
        word="colour",
        lang_code="en",
        pos="noun",
        senses=[dict(glosses=["visual quality"]), dict(glosses=["flag"])],
        forms=[dict(form="color", tags=["alternative"])],
    )
    c = dict(candidate_id="c1", source_record_sha256=digest(a))
    g = dict(lemma="color", pos="NOUN", entry_id="e1", review_unit_id="u1", sense_candidates=[c])
    r = dict(
        review_sha256="r",
        request_sha256="q",
        review_unit_id="u1",
        entry_id="e1",
        decision="uncertain",
    )
    row = dict(
        language="en",
        record_id="record",
        review_unit_id="u1",
        decision="uncertain",
        source_group=g,
        imported_review=r,
    )

    def binding(raw):
        return dict(
            source_path="dictionary/en.jsonl",
            source_file_sha256="a" * 64,
            source_line_locator=1,
            source_record_sha256=digest(raw),
            raw_file=dict(path="raw.json", sha256="b" * 64),
        )

    ab, tb = binding(a), binding(t)
    p = dict(
        schema_version="scoped-alias-resolution-proposal-1",
        language="en",
        review_unit_id="u1",
        inventory_record_id="record",
        inventory_record_sha256=digest(row),
        baseline_decision="uncertain",
        native_review_binding_sha256="r",
        native_request_sha256="q",
        alias=dict(
            lemma="color",
            pos="NOUN",
            candidate_id="c1",
            candidate_sha256=digest(c),
            raw_binding=ab,
            source_sense_index=0,
            relation="US standard spelling of",
            target_word="colour",
        ),
        target=dict(
            lemma="colour",
            pos="NOUN",
            raw_binding=tb,
            allowed_raw_sense_indices=[0],
            selected_senses=[
                dict(
                    raw_sense_index=0,
                    source_sense_sha256=digest(t["senses"][0]),
                    source_sense=t["senses"][0],
                )
            ],
            rejected_raw_sense_indices=[1],
        ),
        display="color",
        forms=[],
        proposed_action="include_derived_scoped_alias",
        production_eligible=False,
        generation_status="deferred_by_user",
    )
    seal(p)
    return row, p, {digest(a): dict(raw=a, binding=ab), digest(t): dict(raw=t, binding=tb)}


def resolve(*args):
    assert importlib.util.find_spec(MODULE) is not None, (
        "strict scoped alias resolver is not implemented"
    )
    return importlib.import_module(MODULE).resolve_scoped_alias(*args)


def test_retains_only_selected_target_sense_and_preserves_native(evidence):
    before = copy.deepcopy(evidence)
    result = resolve(*evidence)
    assert evidence == before
    assert result["decision"] == "include"
    assert result["imported_review"] == before[0]["imported_review"]
    assert result["source_group"] == before[0]["source_group"]
    c = result["resolved_content"]["resolved_candidates"][0]
    assert c["source_candidate_id"] == "c1" and c["lemma"] == "color"
    assert c["target_scope"]["allowed_raw_sense_indices"] == [0]
    assert len(c["target_scope"]["selected_senses"]) == 1
    assert c["evidence"][0]["proposal_id"] == before[1]["proposal_id"]
    assert result["production_eligible"] is False


@pytest.mark.parametrize(
    "change",
    [
        "absent_target",
        "stale_target",
        "row",
        "candidate",
        "review",
        "request",
        "wrong_source",
        "relation",
        "language",
        "pos",
        "index",
        "gloss",
        "all_senses",
        "empty",
        "duplicate",
        "negative",
        "boolean_index",
        "proposal_id",
    ],
)
def test_rejects_missing_stale_or_expanded_evidence(evidence, change):
    row, p, raws = evidence
    k = p["target"]["raw_binding"]["source_record_sha256"]
    if change == "absent_target":
        raws.pop(k)
    elif change == "stale_target":
        raws[k]["raw"]["senses"][0]["glosses"] = ["changed"]
    elif change == "row":
        row["decision"] = "exclude"
    elif change == "candidate":
        p["alias"]["candidate_sha256"] = "wrong"
    elif change == "review":
        p["native_review_binding_sha256"] = "wrong"
    elif change == "request":
        p["native_request_sha256"] = "wrong"
    elif change == "wrong_source":
        raws[k]["binding"] = dict(raws[k]["binding"], source_path="different.jsonl")
    elif change == "relation":
        p["alias"]["target_word"] = "wrong"
    elif change == "language":
        p["language"] = "fr"
    elif change == "pos":
        p["target"]["pos"] = "VERB"
    elif change == "index":
        p["target"]["allowed_raw_sense_indices"] = [1]
    elif change == "gloss":
        p["target"]["selected_senses"][0]["source_sense"] = dict(glosses=["invented"])
    elif change == "all_senses":
        p["target"]["allowed_raw_sense_indices"] = [0, 1]
    elif change == "empty":
        p["target"]["allowed_raw_sense_indices"] = []
    elif change == "duplicate":
        p["target"]["allowed_raw_sense_indices"] = [0, 0]
    elif change == "negative":
        p["target"]["allowed_raw_sense_indices"] = [-1]
    elif change == "boolean_index":
        p["target"]["allowed_raw_sense_indices"] = [False]
    elif change == "proposal_id":
        p["proposal_id"] = "tampered"
    if change != "proposal_id":
        seal(p)
    with pytest.raises(ValueError):
        resolve(row, p, raws)
