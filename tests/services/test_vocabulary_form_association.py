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


def _romanian_row(raw, uid, decision, indices):
    record_sha = _hash(raw)
    candidates = [
        dict(candidate_id="candidate:" + _hash(dict(record=record_sha, sense=i)), source_record_sha256=record_sha)
        for i in indices
    ]
    return dict(
        language="ro", review_unit_id=uid, decision=decision,
        source_group=dict(entry_id=uid, review_unit_id=uid, lemma=raw["word"], pos="VERB", sense_candidates=candidates, forms_for_review=[], readings=[]),
        imported_review=dict(entry_id=uid, review_unit_id=uid, decision=decision, selected_candidate_ids=[c["candidate_id"] for c in candidates] if decision == "include" else [], selected_forms=[]),
    )


def _romanian_link(form_raw, form_row, parent_raw, parent, source_index):
    return dict(
        source_candidate_id=form_row["source_group"]["sense_candidates"][source_index]["candidate_id"],
        source_record=form_raw, source_record_sha256=_hash(form_raw),
        source_sense_index=source_index, parent_identity_id=parent["identity_id"],
        parent_candidate_id=parent["senses"][0]["candidate_id"],
        parent_record=parent_raw, parent_record_sha256=_hash(parent_raw),
        features=["second-person", "plural", "present", "indicative"],
        rationale="Exact Romanian source relation and retained parent sense reviewed individually.",
    )


def _romanian_chain_case():
    parent_raw = dict(word="fi", lang_code="ro", pos="verb", senses=[dict(glosses=["to be"])])
    middle = dict(word="sunteți", lang_code="ro", pos="verb", senses=[dict(glosses=["second-person plural present indicative of fi"], form_of=[dict(word="fi")])])
    form_raw = dict(word="sînteți", lang_code="ro", pos="verb", senses=[
        dict(glosses=["alternative form of sunteți"], alt_of=[dict(word="sunteți")]),
        dict(glosses=["obsolete form of sunteți"], alt_of=[dict(word="sunteți")]),
    ])
    parent_row = _romanian_row(parent_raw, "parent-ro", "include", [0])
    form_row = _romanian_row(form_raw, "form-ro", "uncertain", [0, 1])
    parent = consolidate([parent_row], language="ro")["identities"][0]
    links = []
    for index, register in [(0, "Moldova"), (1, "obsolete")]:
        link = _romanian_link(form_raw, form_row, parent_raw, parent, index)
        link["features"].append(register)
        link["relation_evidence"] = dict(kind="explicit_chain", edges=[
            dict(record=form_raw, record_sha256=_hash(form_raw), sense_index=index,
                 relation_kind="alt_of", target=dict(word="sunteți"),
                 quote=form_raw["senses"][index]["glosses"][0]),
            dict(record=middle, record_sha256=_hash(middle), sense_index=0,
                 relation_kind="form_of", target=dict(word="fi"),
                 quote=middle["senses"][0]["glosses"][0]),
        ])
        links.append(link)
    return parent_row, form_row, parent, links


def test_explicit_romanian_form_chain_resolves_both_source_senses_without_new_lemma():
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    parent_row, row, parent, links = _romanian_chain_case()
    resolved = prepare_form_resolution(row, links, {parent["identity_id"]: parent})
    result = consolidate([parent_row, resolved], language="ro")
    assert len(result["identities"]) == 1
    assert len(result["identities"][0]["retained_forms"]) == 2
    assert not result["pending_review_units"]


@pytest.mark.parametrize("damage", ["hash", "target", "intermediate", "cycle", "relation", "index", "language", "quote", "parent"])
def test_explicit_chain_rejects_broken_edges(damage):
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    _, row, parent, links = _romanian_chain_case()
    edges = links[0]["relation_evidence"]["edges"]
    if damage == "hash":
        edges[1]["record_sha256"] = "0" * 64
    elif damage == "target":
        edges[0]["target"] = dict(word="altul")
    elif damage == "intermediate":
        edges[1]["record"]["word"] = "altul"
    elif damage == "cycle":
        edges[1]["target"] = dict(word="sînteți")
    elif damage == "relation":
        edges[0]["relation_kind"] = "form_of"
    elif damage == "index":
        edges[0]["sense_index"] = 1
    elif damage == "language":
        edges[1]["record"]["lang_code"] = "fr"
    elif damage == "quote":
        edges[0]["quote"] = "invented"
    else:
        links[0]["parent_candidate_id"] = "candidate:wrong"
    with pytest.raises(ValueError):
        prepare_form_resolution(row, links, {parent["identity_id"]: parent})


def _romanian_aux_case():
    parent_raw = dict(word="avea", lang_code="ro", pos="verb", senses=[
        dict(glosses=["to have"]), dict(glosses=["to stand"]),
        dict(glosses=["Used with past participles to form the compound perfect tense."]),
    ])
    head = dict(name="head", args={"1": "ro", "2": "verb form", "5": "third-person singular form of", "6": "avea", "7": "used with past participles to form perfect compus tenses"}, expansion="(el/ea) a (modal auxiliary, third-person singular form of avea, used with past participles to form perfect compus tenses)")
    aux = dict(name="ro-aux", args={"1": "avea", "person": "3s", "tense": "comp"}, expansion=head["expansion"])
    form_raw = dict(word="a", lang_code="ro", pos="verb", senses=[dict(glosses=["modal auxiliary"])], head_templates=[head, aux])
    parent_row = _romanian_row(parent_raw, "avea-parent", "include", [2])
    row = _romanian_row(form_raw, "a-form", "uncertain", [0])
    parent = consolidate([parent_row], language="ro")["identities"][0]
    link = _romanian_link(form_raw, row, parent_raw, parent, 0)
    link["features"] = ["third-person", "singular", "compound-perfect", "auxiliary"]
    link["relation_evidence"] = dict(kind="ro_compound_perfect_aux", parent_sense_index=2,
                                     head_template=dict(index=0, template=head),
                                     aux_template=dict(index=1, template=aux))
    return parent_row, row, parent, link


def test_romanian_aux_template_attaches_only_compound_perfect_sense():
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    parent_row, row, parent, link = _romanian_aux_case()
    resolved = prepare_form_resolution(row, [link], {parent["identity_id"]: parent})
    result = consolidate([parent_row, resolved], language="ro")
    assert len(result["identities"]) == 1
    assert result["identities"][0]["retained_forms"][0]["evidence"]["parent_candidate_id"] == parent["senses"][0]["candidate_id"]


@pytest.mark.parametrize("damage", ["args", "expansion", "sense", "head_index", "aux_index", "parent", "language"])
def test_romanian_aux_rejects_mismatched_template_or_parent(damage):
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    _, row, parent, link = _romanian_aux_case()
    evidence = link["relation_evidence"]
    if damage == "args":
        evidence["aux_template"]["template"]["args"]["tense"] = "future"
    elif damage == "expansion":
        evidence["head_template"]["template"]["expansion"] = "invented"
    elif damage == "sense":
        evidence["parent_sense_index"] = 0
    elif damage == "head_index":
        evidence["head_template"]["index"] = 1
    elif damage == "aux_index":
        evidence["aux_template"]["index"] = 0
    elif damage == "parent":
        link["parent_candidate_id"] = "candidate:wrong"
    else:
        link["source_record"]["lang_code"] = "fr"
    with pytest.raises(ValueError):
        prepare_form_resolution(row, [link], {parent["identity_id"]: parent})


def _greek_spelling_note_case():
    parent_raw = dict(word="τεχνολογία", lang_code="el", pos="noun", senses=[dict(glosses=["technology"])])
    raw = dict(word="τεχνολογιών", lang_code="el", pos="noun", senses=[
        dict(glosses=["genitive plural of τεχνολογία"], tags=["feminine", "form-of", "genitive", "plural"], form_of=[dict(word="τεχνολογία")]),
        dict(glosses=["older spelling: τεχνολογιῶν"], tags=["feminine"], links=[["τεχνολογιῶν", "τεχνολογιῶν#Ancient_Greek"]]),
    ])
    parent_row = _romanian_row(parent_raw, "greek-parent", "include", [0])
    row = _romanian_row(raw, "greek-note", "uncertain", [1])
    for item in (parent_row, row):
        item["language"] = "el"
        item["source_group"]["pos"] = "NOUN"
    parent = consolidate([parent_row], language="el")["identities"][0]
    link = dict(
        source_candidate_id=row["source_group"]["sense_candidates"][0]["candidate_id"],
        source_record=raw, source_record_sha256=_hash(raw), source_sense_index=1,
        parent_identity_id=parent["identity_id"], parent_candidate_id=parent["senses"][0]["candidate_id"],
        parent_record=parent_raw, parent_record_sha256=_hash(parent_raw),
        features=["genitive", "plural", "feminine", "older polytonic spelling note retained as documentary metadata"],
        rationale="Explicit sibling form relation and spelling note in the identical Greek source record.",
        relation_evidence=dict(
            kind="sibling_form_of_spelling_note", support_sense_index=0,
            support_target=raw["senses"][0]["form_of"][0],
            support_quote=raw["senses"][0]["glosses"][0],
            spelling_note_quote=raw["senses"][1]["glosses"][0],
        ),
    )
    return parent_row, row, parent, link


def test_greek_spelling_note_binds_existing_form_without_creating_lemma():
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    parent_row, row, parent, link = _greek_spelling_note_case()
    resolved = prepare_form_resolution(row, [link], {parent["identity_id"]: parent})
    result = consolidate([parent_row, resolved], language="el")
    assert len(result["identities"]) == 1
    assert len(result["identities"][0]["retained_forms"]) == 1
    assert not result["pending_review_units"]


@pytest.mark.parametrize("damage", ["support_index", "support_target", "support_quote", "note", "tags", "sense", "parent"])
def test_greek_spelling_note_rejects_unbound_sibling_evidence(damage):
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    _, row, parent, link = _greek_spelling_note_case()
    evidence = link["relation_evidence"]
    if damage == "support_index":
        evidence["support_sense_index"] = 1
    elif damage == "support_target":
        evidence["support_target"] = dict(word="other")
    elif damage == "support_quote":
        evidence["support_quote"] = "invented"
    elif damage == "note":
        evidence["spelling_note_quote"] = "invented"
    elif damage == "tags":
        link["features"] = ["singular", "nominative"]
    elif damage == "sense":
        link["source_sense_index"] = 0
    else:
        link["parent_candidate_id"] = "candidate:wrong"
    with pytest.raises(ValueError):
        prepare_form_resolution(row, [link], {parent["identity_id"]: parent})


def _finnish_superlative_case():
    parent_raw = dict(word="helposti", lang_code="fi", pos="adv", senses=[dict(glosses=["easily"])])
    middle = dict(word="helpoimmin", lang_code="fi", pos="adv", senses=[dict(glosses=["superlative degree of helposti"], tags=["form-of", "superlative"], form_of=[dict(word="helposti")])])
    raw = dict(word="helpoiten", lang_code="fi", pos="adv", senses=[dict(glosses=["synonym of helpoimmin"], synonyms=[dict(word="helpoimmin", tags=["synonym", "synonym-of"])])])
    parent_row = _romanian_row(parent_raw, "fi-parent", "include", [0])
    row = _romanian_row(raw, "fi-form", "uncertain", [0])
    for item in (parent_row, row):
        item["language"] = "fi"
        item["source_group"]["pos"] = "ADV"
    parent = consolidate([parent_row], language="fi")["identities"][0]
    observation = dict(url="https://kielitoimistonohjepankki.fi/ohje/vertailuilmauksia-parhaiten-vai-parhaimmin-tavan-adverbit/", exact_short_quote="helposti | helpommin | helpoimmin | ~ helpoiten", license_gate="Private research only; no commercial text export")
    link = dict(
        source_candidate_id=row["source_group"]["sense_candidates"][0]["candidate_id"],
        source_record=raw, source_record_sha256=_hash(raw), source_sense_index=0,
        parent_identity_id=parent["identity_id"], parent_candidate_id=parent["senses"][0]["candidate_id"],
        parent_record=parent_raw, parent_record_sha256=_hash(parent_raw), features=["superlative"],
        rationale="Pinned Finnish superlative paradigm independently relates the variant to the retained adverb.",
        relation_evidence=dict(
            kind="fi_official_superlative_variant", synonym_target=raw["senses"][0]["synonyms"][0],
            source_quote=raw["senses"][0]["glosses"][0], intermediate_record=middle,
            intermediate_record_sha256=_hash(middle), intermediate_sense_index=0,
            intermediate_target=middle["senses"][0]["form_of"][0],
            intermediate_quote=middle["senses"][0]["glosses"][0],
            primary_observation=observation, primary_observation_sha256=_hash(observation),
            primary_research_pin=dict(html_sha256="a" * 64, exact_paradigm_row=dict(cells=["helposti", "helpommin", "helpoimmin", "~ helpoiten"]), license="CC BY-NC-ND 4.0"),
        ),
    )
    return parent_row, row, parent, link


def test_finnish_official_paradigm_validates_variant_without_generic_synonym_rule():
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    parent_row, row, parent, link = _finnish_superlative_case()
    resolved = prepare_form_resolution(row, [link], {parent["identity_id"]: parent})
    result = consolidate([parent_row, resolved], language="fi")
    assert len(result["identities"]) == 1
    assert len(result["identities"][0]["retained_forms"]) == 1


@pytest.mark.parametrize("damage", ["synonym", "quote", "intermediate", "relation", "target", "observation", "table", "license", "feature"])
def test_finnish_official_paradigm_rejects_unsupported_variant(damage):
    from multilang.services.vocabulary_form_association import prepare_form_resolution

    _, row, parent, link = _finnish_superlative_case()
    evidence = link["relation_evidence"]
    if damage == "synonym":
        evidence["synonym_target"] = dict(word="other")
    elif damage == "quote":
        evidence["source_quote"] = "invented"
    elif damage == "intermediate":
        evidence["intermediate_record_sha256"] = "0" * 64
    elif damage == "relation":
        evidence["intermediate_sense_index"] = 1
    elif damage == "target":
        evidence["intermediate_target"] = dict(word="other")
    elif damage == "observation":
        evidence["primary_observation_sha256"] = "0" * 64
    elif damage == "table":
        evidence["primary_research_pin"]["exact_paradigm_row"]["cells"][-1] = "~ other"
    elif damage == "license":
        evidence["primary_research_pin"]["license"] = "CC0"
    else:
        link["features"] = ["comparative"]
    with pytest.raises(ValueError):
        prepare_form_resolution(row, [link], {parent["identity_id"]: parent})
