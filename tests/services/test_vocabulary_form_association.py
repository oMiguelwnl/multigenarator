import copy
import hashlib
import json

import pytest

from multilang.services.vocabulary_adjudication import _hash
from multilang.services.vocabulary_finalization import consolidate


def case():
    parent_raw = dict(word="žlutý", lang_code="cs", pos="adj", senses=[dict(glosses=["yellow"])])
    form_raw = dict(
        word="žlutých",
        lang_code="cs",
        pos="adj",
        senses=[dict(glosses=["genitive/locative plural of žlutý"])],
    )

    def row(raw, uid, decision):
        h = _hash(raw)
        cid = "candidate:" + _hash(dict(record=h, sense=0))
        return dict(
            language="cs",
            review_unit_id=uid,
            decision=decision,
            source_group=dict(
                entry_id=uid,
                review_unit_id=uid,
                lemma=raw["word"],
                pos="ADJ",
                sense_candidates=[dict(candidate_id=cid, source_record_sha256=h)],
                forms_for_review=[],
                readings=[],
            ),
            imported_review=dict(
                entry_id=uid,
                review_unit_id=uid,
                decision=decision,
                selected_candidate_ids=[cid] if decision == "include" else [],
                selected_forms=[],
            ),
        )

    parent_row = row(parent_raw, "parent", "include")
    form_row = row(form_raw, "form", "uncertain")
    parent = consolidate([parent_row], language="cs")["identities"][0]
    link = dict(
        source_candidate_id=form_row["source_group"]["sense_candidates"][0]["candidate_id"],
        source_record=form_raw,
        source_record_sha256=_hash(form_raw),
        source_sense_index=0,
        parent_identity_id=parent["identity_id"],
        parent_candidate_id=parent["senses"][0]["candidate_id"],
        parent_record=parent_raw,
        parent_record_sha256=_hash(parent_raw),
        parent_relation_quote="genitive/locative plural of žlutý",
        features=["plural", "genitive-or-locative"],
        rationale="Individually checked own-source plural case form; bind exact yellow adjective parent without adding a lemma.",
    )
    return parent_row, form_row, parent, link


def test_verified_inflection_attaches_to_existing_identity_without_creating_lemma():
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    parent_row, row, parent, link = case()
    before = copy.deepcopy(row)
    resolved = prepare_form_resolution(row, [link], {parent["identity_id"]: parent})
    assert row == before
    assert resolved["source_group"] == before["source_group"]
    assert resolved["imported_review"] == before["imported_review"]
    result = consolidate([resolved, parent_row], language="cs")
    assert len(result["identities"]) == 1
    assert result["form_only_units"] == ["form"]
    assert not result["pending_review_units"]
    form = result["identities"][0]["retained_forms"][0]
    assert form["source_form"]["form"] == "žlutých"
    assert form["parent_identity_id"] == parent["identity_id"]
    assert form["selected_for_card"] is False
    assert form["production_eligible"] is False
    assert consolidate([parent_row, resolved], language="cs") == result


@pytest.mark.parametrize(
    "damage",
    ["raw", "parent_raw", "candidate", "parent", "quote", "features", "missing", "duplicate"],
)
def test_form_link_rejects_unbound_or_incomplete_evidence(damage):
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    _, row, parent, link = case()
    links = [link]
    if damage == "raw":
        link["source_record"]["word"] = "other"
    elif damage == "parent_raw":
        link["parent_record"]["word"] = "other"
    elif damage == "candidate":
        link["parent_candidate_id"] = "unselected"
    elif damage == "parent":
        link["parent_identity_id"] = "absent"
    elif damage == "quote":
        link["parent_relation_quote"] = "not attested"
    elif damage == "features":
        link["features"] = []
    elif damage == "missing":
        links = []
    else:
        links = [link, link]
    with pytest.raises(ValueError):
        prepare_form_resolution(row, links, {parent["identity_id"]: parent})


def test_final_consolidation_rejects_missing_parent_and_tampered_link():
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    parent_row, row, parent, link = case()
    resolved = prepare_form_resolution(row, [link], {parent["identity_id"]: parent})
    with pytest.raises(ValueError):
        consolidate([resolved], language="cs")
    resolved["resolved_content"]["form_only_associations"][0]["source_record"]["word"] = "forged"
    with pytest.raises(ValueError):
        consolidate([resolved, parent_row], language="cs")


def test_prior_uncertainty_is_preserved_as_history_not_silently_replaced():
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    _, row, parent, link = case()
    row["resolved_content"] = dict(unresolved_questions=["Parent linkage pending."])
    previous = copy.deepcopy(row["resolved_content"])
    resolved = prepare_form_resolution(row, [link], {parent["identity_id"]: parent})
    assert resolved["resolved_content"]["previous_resolution"] == previous
    assert resolved["resolved_content"]["original_binding"]["baseline_sha256"] == _hash(row)


@pytest.mark.parametrize("damage", ["language", "pos", "source_candidate", "target_candidate"])
def test_form_link_checks_lexical_identity_and_exact_sense_index(damage):
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    _, row, parent, link = case()
    if damage == "language":
        parent["language"] = "sk"
    elif damage == "pos":
        parent["pos"] = "NOUN"
    elif damage == "source_candidate":
        link["source_sense_index"] = 1
    else:
        fake = "candidate:" + _hash(dict(record=link["parent_record_sha256"], sense=999))
        parent["senses"][0]["candidate_id"] = fake
        link["parent_candidate_id"] = fake
    with pytest.raises(ValueError):
        prepare_form_resolution(row, [link], {parent["identity_id"]: parent})


def test_publication_counts_forms_separately_from_lemmas_and_card_selections(tmp_path):
    from multilang.services.vocabulary_finalization import publish_inventory
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    parent_row, row, parent, link = case()
    resolved = prepare_form_resolution(row, [link], {parent["identity_id"]: parent})
    source = tmp_path / "source.jsonl"
    source.write_text("\n".join(json.dumps(r) for r in [parent_row, resolved]) + "\n")
    output = tmp_path / "published"
    summary = publish_inventory(
        inputs=[
            dict(
                language="cs",
                path=str(source),
                sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            )
        ],
        output=output,
    )
    report = summary["languages"]["cs"]
    assert report["review_units"] == 2
    assert report["included_identities"] == 1
    assert report["form_only_units"] == 1
    assert report["retained_form_associations"] == 1
    assert report["selected_form_associations"] == 0
    assert not summary["production_eligible"]
    assert summary["generation_status"] == "deferred_by_user"
    identity = json.loads((output / "languages/cs/identities.jsonl").read_text())
    assert identity["retained_forms"][0]["selected_for_card"] is False
    snapshots = [
        json.loads(s) for s in (output / "snapshot/inventory/cs.jsonl").read_text().splitlines()
    ]
    form_row = next(r for r in snapshots if r["review_unit_id"] == "form")
    assert form_row["resolved_content"] == resolved["resolved_content"]
