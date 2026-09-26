"""Machine selection must stay bound to source senses, forms and both reviews."""

import hashlib
import json

import pytest


def _group():
    return {
        "entry_id": "e1", "lemma": "go", "pos": "VERB", "source_priority": 5,
        "sense_candidates": [
            {"candidate_id": "s1", "glosses": ["to move to another place"], "tags": []},
            {"candidate_id": "s2", "glosses": ["an obsolete technical sense"], "tags": ["obsolete"]},
        ],
        "readings": [],
        "forms_for_review": [
            {"form_id": "f1", "form": "went", "tags": ["past"], "priority": 10,
             "parent_entry_ids": ["e1"], "evidence_candidate_ids": ["s1"]},
        ],
    }


def _decision(**changes):
    return {"i": 0, "decision": "include", "senses": [0], "display": "go",
            "forms": [{"f": 0, "s": 0, "reason": "frequent_irregular_form"}],
            "reason": "general_use", **changes}


def test_selects_only_cited_senses_and_forms_with_explicit_parent():
    from multilang.services.vocabulary_curation import reconcile_selections

    result = reconcile_selections([_group()], {"decisions": [_decision()]}, {"decisions": [_decision()]})
    row = result[0]
    assert row["status"] == "machine_consensus"
    assert row["selected_candidate_ids"] == ["s1"]
    assert row["selected_forms"][0]["parent_candidate_id"] == "s1"
    assert row["selected_forms"][0]["form_id"] == "f1"
    assert row["human_approved"] is False


@pytest.mark.parametrize("change", [
    {"senses": [8]}, {"display": "invented"}, {"senses": []},
    {"forms": [{"f": 0, "s": 1, "reason": "frequent_irregular_form"}]},
    {"i": 42}, {"forms": [{"f": 8, "s": 0, "reason": "frequent_irregular_form"}]},
])
def test_model_cannot_invent_identity_form_or_display(change):
    from multilang.services.vocabulary_curation import validate_selections

    with pytest.raises(ValueError):
        validate_selections([_group()], {"decisions": [_decision(**change)]})


def test_missing_duplicate_or_extra_decisions_fail_closed():
    from multilang.services.vocabulary_curation import validate_selections

    for decisions in [[], [_decision(), _decision()]]:
        with pytest.raises(ValueError):
            validate_selections([_group()], {"decisions": decisions})


def test_disagreement_never_becomes_consensus_approval():
    from multilang.services.vocabulary_curation import reconcile_selections

    other = _decision(decision="exclude", senses=[], forms=[], reason="specialized_or_obsolete")
    result = reconcile_selections([_group()], {"decisions": [_decision()]}, {"decisions": [other]})
    assert result[0]["status"] == "review_disagreement"
    assert result[0]["selected_candidate_ids"] == []
    assert result[0]["selected_forms"] == []


def test_form_frequency_does_not_approve_every_inflection():
    from multilang.services.vocabulary_curation import compact_group

    compact = compact_group(_group())
    assert compact["senses"][1]["tags"] == ["obsolete"]
    assert compact["forms"][0]["rank"] == 10
    assert "selected_for_card" not in compact["forms"][0]


def test_source_attested_display_variants_can_resolve_rare_japanese_headword():
    from multilang.services.vocabulary_curation import validate_selections

    group = _group()
    group.update(lemma="乃", pos="PART", forms_for_review=[],
                 readings=[{"candidate_id":"s1","form":"の","reading":"の"}])
    row = _decision(display="の", forms=[])
    assert validate_selections([group], {"decisions":[row]})[0].display == "の"


def test_review_prompt_is_source_only_and_does_not_request_card_text():
    from multilang.services.vocabulary_curation import selection_messages

    messages = selection_messages("de", [_group()])
    assert "Do not generate" in messages[0]["content"]
    assert "untrusted" in messages[0]["content"]
    assert "source_candidate_index" in messages[1]["content"]


def test_prepare_packets_verifies_sources_and_keeps_forms_outside_frequency_as_unselected(tmp_path):
    from multilang.services.vocabulary_curation import prepare_curation_packets

    source = tmp_path / "prepared"
    (source / "en").mkdir(parents=True)
    priority = tmp_path / "priority.json"
    priority.write_text(json.dumps({"rows":[{"rank":1,"form":"go"},{"rank":2,"form":"went"}]}))
    group = _group()
    forms = group.pop("forms_for_review")
    forms.append({**forms[0],"form_id":"rare","form":"goeth"})
    (source/"en/vocabulary.json").write_text(json.dumps({"entries":[group]}))
    (source/"en/forms.jsonl").write_text("\n".join(json.dumps(x) for x in forms)+"\n")
    request={"languages":[{"language":"en","priority":{"path":str(priority),"sha256":hashlib.sha256(priority.read_bytes()).hexdigest()}}]}
    (source/"request.json").write_text(json.dumps(request))
    manifest={"files":{str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}}
    (source/"manifest.json").write_text(json.dumps(manifest))
    checksum=hashlib.sha256((source/"manifest.json").read_bytes()).hexdigest()
    report=prepare_curation_packets(source,checksum,output=tmp_path/"packets")
    assert report["languages"][0]["entry_count"] == 1
    assert report["languages"][0]["forms_without_frequency_evidence"] == 1
    packet=json.loads((tmp_path/"packets/en/00000.json").read_text())
    assert [f["form"] for f in packet["groups"][0]["forms_for_review"]] == ["went"]
    assert report["provider_calls_executed"] == 0
    (source/"en/vocabulary.json").write_text('{}')
    with pytest.raises(ValueError,match="checksum"):
        prepare_curation_packets(source,checksum,output=tmp_path/"bad")
    assert not (tmp_path/"bad").exists()


def test_large_homograph_group_is_split_without_losing_senses_or_parent_identity():
    from multilang.services.vocabulary_curation import split_review_group

    group=_group()
    group['sense_candidates']=[{'candidate_id':f's{i}','glosses':[f'source meaning {i}'],'tags':[]} for i in range(180)]
    fragments=split_review_group(group,max_senses=32)
    ids=[s['candidate_id'] for part in fragments for s in part['sense_candidates']]
    assert ids==[s['candidate_id'] for s in group['sense_candidates']]
    assert len(set(part['review_unit_id'] for part in fragments))==len(fragments)
    assert all(part['entry_id']=='e1' and len(part['sense_candidates'])<=32 for part in fragments)
    assert all(part['source_group_fragment_count']==len(fragments) for part in fragments)


@pytest.mark.parametrize("index", [True, "0", 0.0])
def test_sense_indices_must_be_literal_integers(index):
    from multilang.services.vocabulary_curation import validate_selections

    with pytest.raises(ValueError):
        validate_selections([_group()], {"decisions": [_decision(senses=[index], forms=[])]})
