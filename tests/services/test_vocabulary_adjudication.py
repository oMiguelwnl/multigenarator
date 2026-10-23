import copy
import hashlib
import json

import pytest


def digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def fixture():
    raw = dict(
        word="im",
        lang_code="de",
        pos="contraction",
        senses=[dict(glosses=["contraction of in + dem"], tags=["contraction"])],
    )
    rh = digest(raw)
    cid = "candidate:" + digest(dict(record=rh, sense=0))
    row = dict(
        language="de",
        review_unit_id="u",
        decision="uncertain",
        source_group=dict(
            entry_id="e",
            review_unit_id="u",
            lemma="im",
            pos="X",
            sense_candidates=[dict(candidate_id=cid, source_record_sha256=rh)],
            forms_for_review=[],
        ),
        imported_review=dict(decision="uncertain", review_sha256="r"),
    )
    proposal = dict(
        language="de",
        review_unit_id="u",
        baseline_sha256=digest(row),
        decision="include",
        candidates=[
            dict(
                source_candidate_id=cid,
                disposition="retained",
                rationale="Explicit source contraction of the preposition and dative article.",
                sense_index=0,
                sense_sha256=digest(raw["senses"][0]),
            )
        ],
    )
    return row, proposal, {rh: raw}


def test_source_contraction_preserves_documentary_class_and_native_review():
    from multilang.services.vocabulary_adjudication import adjudicate

    row, proposal, raws = fixture()
    original = copy.deepcopy(row)
    result = adjudicate(row, proposal, raws)
    assert row == original
    assert result["imported_review"] == original["imported_review"]
    assert result["source_group"] == original["source_group"]
    candidate = result["resolved_content"]["resolved_candidates"][0]
    assert candidate["pos"] == "CONTRACTION"
    assert candidate["pos_namespace"] == "wiktextract-documentary"
    assert candidate["lexical_unit_kind"] == "contraction"
    assert candidate["evidence"][0]["sense_sha256"] == proposal["candidates"][0]["sense_sha256"]
    assert result["production_eligible"] is False


@pytest.mark.parametrize(
    "damage",
    ["baseline", "raw", "candidate", "sense", "language", "decision", "missing", "duplicate"],
)
def test_no_resolution_accepts_unbound_evidence(damage):
    from multilang.services.vocabulary_adjudication import adjudicate

    row, proposal, raws = fixture()
    if damage == "baseline":
        proposal["baseline_sha256"] = "0" * 64
    elif damage == "raw":
        next(iter(raws.values()))["word"] = "else"
    elif damage == "candidate":
        proposal["candidates"][0]["source_candidate_id"] = "other"
    elif damage == "sense":
        proposal["candidates"][0]["sense_sha256"] = "0" * 64
    elif damage == "language":
        proposal["language"] = "en"
    elif damage == "decision":
        proposal["decision"] = "exclude"
    elif damage == "missing":
        proposal["candidates"] = []
    else:
        proposal["candidates"] *= 2
    with pytest.raises(ValueError):
        adjudicate(row, proposal, raws)


def test_exclusion_is_explicit_and_cannot_select_a_form():
    from multilang.services.vocabulary_adjudication import adjudicate

    row, proposal, raws = fixture()
    proposal["decision"] = "exclude"
    proposal["candidates"][0]["disposition"] = "omitted"
    proposal["candidates"][0]["rationale"] = (
        "An explicit source classification is outside this inventory scope."
    )
    result = adjudicate(row, proposal, raws)
    assert result["decision"] == "exclude"
    assert result["resolved_content"]["resolved_forms"]["selected_forms"] == []


def test_unknown_source_class_remains_pending_instead_of_being_guessed():
    from multilang.services.vocabulary_adjudication import adjudicate

    row, proposal, raws = fixture()
    raw = next(iter(raws.values()))
    raw["pos"] = "invented-class"
    rh = digest(raw)
    cid = "candidate:" + digest(dict(record=rh, sense=0))
    row["source_group"]["sense_candidates"][0].update(candidate_id=cid, source_record_sha256=rh)
    proposal["baseline_sha256"] = digest(row)
    proposal["candidates"][0]["source_candidate_id"] = cid
    with pytest.raises(ValueError):
        adjudicate(row, proposal, {rh: raw})


@pytest.mark.parametrize(
    "source_pos, expected",
    [
        ("conj", "CONJUNCTION"),
        ("circumpos", "CIRCUMPOSITION"),
        ("prep_phrase", "PREPOSITIONAL_EXPRESSION"),
    ],
)
def test_documentary_classes_do_not_invent_a_universal_pos(source_pos, expected):
    from multilang.services.vocabulary_adjudication import adjudicate

    row, proposal, raws = fixture()
    raw = next(iter(raws.values()))
    raw["pos"] = source_pos
    rh = digest(raw)
    cid = "candidate:" + digest(dict(record=rh, sense=0))
    row["source_group"]["sense_candidates"][0].update(candidate_id=cid, source_record_sha256=rh)
    proposal["baseline_sha256"] = digest(row)
    proposal["candidates"][0]["source_candidate_id"] = cid
    result = adjudicate(row, proposal, {rh: raw})
    assert result["resolved_content"]["resolved_candidates"][0]["pos"] == expected


def test_adjudication_survives_inventory_consolidation():
    from multilang.services.vocabulary_adjudication import adjudicate
    from multilang.services.vocabulary_finalization import consolidate

    row, proposal, raws = fixture()
    row["imported_review"].update(review_unit_id="u", entry_id="e")
    proposal["baseline_sha256"] = digest(row)
    result = consolidate([adjudicate(row, proposal, raws)], language="de")
    assert len(result["identities"]) == 1
    identity = result["identities"][0]
    assert identity["pos"] == "CONTRACTION"
    assert (
        identity["senses"][0]["resolution"]["source_sense"]
        == next(iter(raws.values()))["senses"][0]
    )
    assert identity["production_eligible"] is False


@pytest.mark.parametrize("tamper", [False, True])
def test_related_context_is_hashed_and_preserved_without_inheriting_senses(tamper):
    from multilang.services.vocabulary_adjudication import adjudicate

    row, proposal, raws = fixture()
    target = dict(word="in", lang_code="de", pos="prep", senses=[dict(glosses=["in"])])
    rh = digest(target)
    raws[rh] = target
    proposal["candidates"][0]["source_contexts"] = [
        dict(
            source_record_sha256=rh,
            sense_index=0,
            sense_sha256=digest(target["senses"][0]),
            relation_type="component_of_contraction",
            rationale="This is a documented component, not an inherited target sense.",
        )
    ]
    if tamper:
        target["senses"][0]["glosses"] = ["changed"]
        with pytest.raises(ValueError):
            adjudicate(row, proposal, raws)
        return
    candidate = adjudicate(row, proposal, raws)["resolved_content"]["resolved_candidates"][0]
    assert candidate["source_contexts"][0]["source_word"] == "in"
    assert candidate["source_contexts"][0]["source_sense"] == target["senses"][0]
    assert candidate["source_sense"] != target["senses"][0]
