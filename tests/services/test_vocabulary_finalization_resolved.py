"""Regression shapes from frozen DA starter / NB for / SV eftersom resolutions."""

import copy

import pytest


def adapt(row):
    from multilang.services.vocabulary_finalization_resolved import adapt_resolved

    return adapt_resolved(row)


def candidate(cid="ancestor", rid="sense", **kw):
    return dict(
        source_candidate_id=cid,
        resolved_candidate_id=rid,
        lemma="starter",
        pos="NOUN",
        disposition="retained",
        evidence=[{"type": "unit_evidence_reference"}],
        **kw,
    )


def row(candidates, forms=None):
    content = dict(
        review_unit_id="unit",
        resolved_unit_disposition="include",
        resolved_candidates=candidates,
        unresolved_questions=[],
    )
    if forms is not None:
        content["resolved_forms"] = forms
    return dict(
        language="da",
        review_unit_id="unit",
        decision="include",
        source_group=dict(entry_id="entry", review_unit_id="unit", forms_for_review=[]),
        imported_review=dict(selected_forms=[]),
        resolved_content=content,
    )


def test_danish_starter_split_keeps_four_senses_and_twelve_exact_form_associations():
    ids = [
        "derived:starter:" + key
        for key in [
            "race_start_official",
            "starting_competitor",
            "person_starting_activity",
            "engine_starting_mechanism",
        ]
    ]
    candidates = [candidate(rid=rid, scope={"sense_key": rid.rsplit(":", 1)[1]}) for rid in ids]
    forms = [
        dict(
            resolved_form_id="derived:starter:" + form,
            source_form_id=None,
            form=form,
            disposition="retained",
            parent_candidate_ids=ids,
            evidence=[{"type": "unit_evidence_reference"}],
            selected_for_generation=False,
        )
        for form in ["starteren", "startere", "starterne"]
    ]
    original = row(candidates, forms)
    before = copy.deepcopy(original)
    result = adapt(original)
    assert original == before
    assert result["original_resolved_content"] == before["resolved_content"]
    resolved = result["resolved_content"]
    assert {c["resolved_sense_key"] for c in resolved["resolved_candidates"]} == set(ids)
    assert {c["source_candidate_id"] for c in resolved["resolved_candidates"]} == {"ancestor"}
    assert {c["resolved_identity_key"] for c in resolved["resolved_candidates"]} == {None}
    normalized = resolved["resolved_forms"]
    assert len(normalized["selected_forms"]) == 12
    assert {f["parent_resolution_id"] for f in normalized["selected_forms"]} == set(ids)
    assert all(f["parent_candidate_id"] == "ancestor" for f in normalized["selected_forms"])
    assert all(f["parent_entry_ids"] == ["entry"] for f in normalized["source_forms"])
    assert all(f["evidence_candidate_ids"] == ["ancestor"] for f in normalized["source_forms"])
    assert adapt(result) == result


def test_norwegian_for_homonyms_and_embedded_forms_stay_separate():
    candidates = []
    for n, homonym in enumerate(["feed", "lining"]):
        c = candidate(rid="unused", homonym=homonym)
        del c["resolved_candidate_id"]
        c.update(
            derived_candidate_id=f"derived:nb:part{n}",
            lemma="for",
            scope={"semantic_domain": homonym, "canonical_variants": ["fôr", "for"]},
        )
        c["forms"] = [
            dict(
                form="foret",
                source_form_id="shared-source-form",
                parent_derived_candidate_id=c["derived_candidate_id"],
                disposition="retained",
                evidence=[{"url": f"dictionary/{n}"}],
                selected_for_card=False,
            )
        ]
        candidates.append(c)
    result = adapt(row(candidates))["resolved_content"]
    assert len({c["resolved_identity_key"] for c in result["resolved_candidates"]}) == 2
    forms = result["resolved_forms"]
    assert len(forms["selected_forms"]) == 2
    assert len({f["form_id"] for f in forms["source_forms"]}) == 2
    assert {f["parent_resolution_id"] for f in forms["selected_forms"]} == {
        "derived:nb:part0",
        "derived:nb:part1",
    }
    assert all(not f["original_form"]["selected_for_card"] for f in forms["source_forms"])


def test_swedish_eftersom_has_two_classes_and_an_empty_list_of_forms():
    candidates = [
        candidate(rid="derived:eftersom:adverb"),
        candidate(rid="derived:eftersom:temporal"),
    ]
    for c, pos in zip(candidates, ["ADV", "SCONJ"], strict=True):
        c.update(lemma="eftersom", pos=pos)
    result = adapt(row(candidates, []))["resolved_content"]
    assert [c["pos"] for c in result["resolved_candidates"]] == ["ADV", "SCONJ"]
    assert result["resolved_forms"]["selected_forms"] == []


@pytest.mark.parametrize("pos", [None, "", "X", "unknown"])
def test_missing_pos_is_quarantined_without_losing_previous_questions(pos):
    c = candidate()
    c.update(lemma="min.", pos=pos, lexical_type="abbreviation")
    original = row([c], [])
    original["resolved_content"]["unresolved_questions"] = [{"question": "old"}]
    result = adapt(original)
    c = result["resolved_content"]["resolved_candidates"][0]
    assert c["pos"] == pos
    assert c["disposition"] == "quarantined_preparation_missing_pos"
    assert result["resolved_content"]["unresolved_questions"][0] == {"question": "old"}
    assert len(result["resolved_content"]["unresolved_questions"]) == 2
    assert result["decision"] == "include"


def test_native_forms_remain_source_bound_and_keep_reviewer_selected_parent():
    c = candidate()
    del c["resolved_candidate_id"]
    form = dict(
        form_id="f",
        form="fulgte",
        evidence_candidate_ids=["form-of-record"],
        parent_entry_ids=["entry"],
        source_parent_lemmas=["følge"],
    )
    selection = dict(form_id="f", form="fulgte", parent_candidate_id="ancestor")
    original = row([c], dict(source_forms=[form], selected_forms=[selection]))
    result = adapt(original)["resolved_content"]["resolved_forms"]
    assert result["source_forms"] == [form]
    assert result["selected_forms"] == [{**selection, "parent_resolution_id": "ancestor"}]


def test_absent_resolved_content_returns_an_independent_unchanged_copy():
    original = dict(language="sv", nested={"v": []})
    result = adapt(original)
    assert result == original and result is not original
    result["nested"]["v"].append(1)
    assert original["nested"]["v"] == []


@pytest.mark.parametrize("damage", ["missing_parent", "no_evidence", "ambiguous_ancestor"])
def test_unbound_derived_form_is_preserved_as_pending_not_attached_by_spelling(damage):
    candidates = [candidate()]
    f = dict(
        form="startere",
        disposition="retained",
        parent_candidate_ids=["sense"],
        evidence=[{"type": "unit_evidence_reference"}],
    )
    if damage == "missing_parent":
        f["parent_candidate_ids"] = ["missing"]
    if damage == "no_evidence":
        f["evidence"] = []
    if damage == "ambiguous_ancestor":
        candidates.append(candidate(rid="other-sense"))
        f["parent_candidate_ids"] = ["ancestor"]
    result = adapt(row(candidates, [f]))["resolved_content"]
    assert not result["resolved_forms"]["selected_forms"]
    assert result["preparation_unbound_forms"][0]["form"] == f
    assert result["unresolved_questions"]


def test_resolved_unit_binding_mismatch_is_not_normalized_away():
    original = row([candidate()], [])
    original["resolved_content"]["review_unit_id"] = "wrong-unit"
    with pytest.raises(ValueError, match="binding"):
        adapt(original)


def test_swedish_gick_uses_exact_frozen_form_provenance_and_resolved_parent():
    c = candidate(rid="derived:ga:motion")
    f = dict(
        form_id="source-gick",
        form="gick",
        evidence_candidate_ids=["ancestor"],
        parent_entry_ids=["entry"],
    )
    derived = dict(
        form="gick",
        source_form_id="source-gick",
        disposition="retained",
        parent_resolved_candidate_id="derived:ga:motion",
        provenance=copy.deepcopy(f),
        reason="prior_review_selected_form",
    )
    original = row([c], [derived])
    original["source_group"]["forms_for_review"] = [f]
    result = adapt(original)["resolved_content"]
    assert len(result["resolved_forms"]["selected_forms"]) == 1
    assert (
        result["resolved_forms"]["selected_forms"][0]["parent_resolution_id"] == "derived:ga:motion"
    )
    original["resolved_content"]["resolved_forms"][0]["provenance"]["form"] = "corrupted"
    assert not adapt(original)["resolved_content"]["resolved_forms"]["selected_forms"]


def test_ancestral_key_is_ambiguous_when_one_split_reuses_its_spelling():
    first = candidate(rid="ancestor")
    second = candidate(rid="second-sense")
    f = dict(
        form="forms",
        disposition="retained",
        parent_candidate_ids=["ancestor"],
        evidence=[{"kind": "source"}],
    )
    result = adapt(row([first, second], [f]))["resolved_content"]
    assert not result["resolved_forms"]["selected_forms"]
    assert result["preparation_unbound_forms"]
