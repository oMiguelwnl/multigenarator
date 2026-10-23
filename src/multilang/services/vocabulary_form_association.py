"""Validate individually authored inflection links, without creating new lemmas.

This module verifies evidence integrity; it never infers a morphological relation
from text. Both the relation and its features require an explicit editorial act.
"""

from __future__ import annotations

import copy
import unicodedata

from multilang.services.vocabulary_adjudication import FLAGS, UPOS, _hash

SCHEMA = "source-bound-form-association-1"


def _text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 2048:
        raise ValueError("invalid form evidence text")
    if any(unicodedata.category(c).startswith("C") for c in value):
        raise ValueError("control character in form evidence")
    return unicodedata.normalize("NFC", value)


def validate_coverage(row, links):
    """Require exactly one authored association for every original candidate."""
    available = [c["candidate_id"] for c in row["source_group"]["sense_candidates"]]
    ids = [link.get("source_candidate_id") for link in links]
    if (
        not ids
        or len(available) != len(set(available))
        or len(ids) != len(set(ids))
        or set(ids) != set(available)
    ):
        raise ValueError("form-only resolution must account for every source candidate once")


def _validate_explicit_chain(evidence, raw, target, source_index, language, pos):
    edges = evidence.get("edges")
    if not isinstance(edges, list) or not 2 <= len(edges) <= 4:
        raise ValueError("explicit form chain must have two to four edges")
    expected_word = _text(raw["word"])
    seen = set()
    for number, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise ValueError("invalid explicit form chain edge")
        record = edge.get("record")
        if not isinstance(record, dict) or _hash(record) != edge.get("record_sha256"):
            raise ValueError("chain record hash differs")
        word = _text(record.get("word"))
        if (
            word != expected_word
            or word in seen
            or record.get("lang_code") != language
            or UPOS.get(record.get("pos")) != pos
            or (number == 0 and record != raw)
        ):
            raise ValueError("chain source, language or part of speech differs")
        seen.add(word)
        index = edge.get("sense_index")
        if type(index) is not int or not 0 <= index < len(record.get("senses", [])):
            raise ValueError("invalid chain sense index")
        if number == 0 and index != source_index:
            raise ValueError("chain begins at a different source sense")
        sense = record["senses"][index]
        kind = edge.get("relation_kind")
        if kind not in {"alt_of", "form_of"}:
            raise ValueError("unsupported chain relation")
        relation = sense.get(kind)
        relation_target = edge.get("target")
        if (
            not isinstance(relation, list)
            or not isinstance(relation_target, dict)
            or relation_target not in relation
        ):
            raise ValueError("chain target is not an exact source relation")
        expected_word = _text(relation_target.get("word"))
        quotes = sense.get("glosses", []) + sense.get("raw_glosses", [])
        quote = _text(edge.get("quote"))
        if quote not in [_text(q) for q in quotes] or expected_word not in quote:
            raise ValueError("chain relation quote is not attested")
    if expected_word != _text(target["word"]) or expected_word in seen:
        raise ValueError("chain does not terminate at retained parent")
    if edges[-1]["relation_kind"] != "form_of":
        raise ValueError("chain lacks an explicit morphological edge")


def _validate_ro_aux(evidence, raw, target, parent_candidate_id):
    if raw.get("lang_code") != "ro" or _text(raw.get("word")) != "a" or _text(target.get("word")) != "avea":
        raise ValueError("Romanian auxiliary adapter is limited to a/avea")
    if evidence.get("parent_sense_index") != 2:
        raise ValueError("auxiliary parent must be compound-perfect sense")
    target_sha = _hash(target)
    if parent_candidate_id != "candidate:" + _hash(dict(record=target_sha, sense=2)):
        raise ValueError("auxiliary parent candidate differs from source sense")
    senses = target.get("senses", [])
    if len(senses) <= 2 or not any(
        "compound perfect tense" in _text(q)
        for q in senses[2].get("glosses", []) + senses[2].get("raw_glosses", [])
    ):
        raise ValueError("parent source does not attest compound-perfect auxiliary")
    templates = raw.get("head_templates")
    if not isinstance(templates, list):
        raise ValueError("Romanian auxiliary templates are absent")
    checked = []
    for key, name in (("head_template", "head"), ("aux_template", "ro-aux")):
        item = evidence.get(key)
        if not isinstance(item, dict) or type(item.get("index")) is not int:
            raise ValueError("invalid authored auxiliary template index")
        index = item["index"]
        if not 0 <= index < len(templates) or item.get("template") != templates[index]:
            raise ValueError("authored auxiliary template differs from source")
        template = templates[index]
        if template.get("name") != name:
            raise ValueError("wrong auxiliary template kind")
        checked.append(template)
    head, aux = checked
    args = head.get("args")
    if (
        not isinstance(args, dict)
        or args.get("5") != "third-person singular form of"
        or args.get("6") != "avea"
        or args.get("7") != "used with past participles to form perfect compus tenses"
        or aux.get("args") != {"1": "avea", "person": "3s", "tense": "comp"}
        or head.get("expansion") != aux.get("expansion")
        or "third-person singular form of avea" not in _text(head.get("expansion"))
        or "past participles" not in head["expansion"]
    ):
        raise ValueError("Romanian auxiliary template does not attest compound perfect")


def _validate_greek_spelling_note(link, evidence, raw, target, source_index, language, pos):
    if language != "el" or pos != "NOUN" or source_index != 1:
        raise ValueError("spelling-note adapter is limited to the Greek nominal source sense")
    senses = raw.get("senses", [])
    support_index = evidence.get("support_sense_index")
    if type(support_index) is not int or support_index != 0 or len(senses) <= source_index:
        raise ValueError("spelling note lacks its exact sibling relation")
    support, note = senses[support_index], senses[source_index]
    relation_target = evidence.get("support_target")
    if (
        not isinstance(relation_target, dict)
        or relation_target not in support.get("form_of", [])
        or _text(relation_target.get("word")) != _text(target["word"])
    ):
        raise ValueError("sibling form relation does not reach retained parent")
    quote = _text(evidence.get("support_quote"))
    if (
        quote not in support.get("glosses", []) + support.get("raw_glosses", [])
        or _text(target["word"]) not in quote
        or not {"feminine", "form-of", "genitive", "plural"} <= set(support.get("tags", []))
        or not {"feminine", "genitive", "plural"} <= set(link.get("features", []))
    ):
        raise ValueError("sibling form or morphology is not explicitly attested")
    note_quote = _text(evidence.get("spelling_note_quote"))
    if (
        note_quote not in note.get("glosses", []) + note.get("raw_glosses", [])
        or not note_quote.startswith("older spelling: ")
        or note.get("form_of")
        or note.get("alt_of")
        or "form-of" in note.get("tags", [])
        or not any(
            isinstance(item, list)
            and len(item) == 2
            and _text(item[0]) in note_quote
            and _text(item[1]).endswith("#Ancient_Greek")
            for item in note.get("links", [])
        )
    ):
        raise ValueError("source sense is not an attested documentary spelling note")


def _validate_fi_superlative(link, evidence, raw, target, source_index, language, pos):
    if (
        language != "fi"
        or pos != "ADV"
        or source_index != 0
        or _text(raw.get("word")) != "helpoiten"
        or _text(target.get("word")) != "helposti"
        or len(target.get("senses", [])) != 1
        or link.get("features") != ["superlative"]
    ):
        raise ValueError("official Finnish paradigm adapter is limited to this exact adverb")
    own = raw["senses"][0]
    synonym = evidence.get("synonym_target")
    if (
        not isinstance(synonym, dict)
        or synonym not in own.get("synonyms", [])
        or _text(synonym.get("word")) != "helpoimmin"
        or "synonym-of" not in synonym.get("tags", [])
        or _text(evidence.get("source_quote")) not in own.get("glosses", []) + own.get("raw_glosses", [])
        or "helpoimmin" not in evidence["source_quote"]
    ):
        raise ValueError("Finnish variant does not have its exact source synonym evidence")
    middle = evidence.get("intermediate_record")
    if (
        not isinstance(middle, dict)
        or _hash(middle) != evidence.get("intermediate_record_sha256")
        or middle.get("lang_code") != "fi"
        or UPOS.get(middle.get("pos")) != "ADV"
        or _text(middle.get("word")) != "helpoimmin"
        or evidence.get("intermediate_sense_index") != 0
        or len(middle.get("senses", [])) != 1
    ):
        raise ValueError("Finnish intermediate superlative record differs")
    sense = middle["senses"][0]
    relation = evidence.get("intermediate_target")
    if (
        not isinstance(relation, dict)
        or relation not in sense.get("form_of", [])
        or _text(relation.get("word")) != "helposti"
        or not {"form-of", "superlative"} <= set(sense.get("tags", []))
        or _text(evidence.get("intermediate_quote"))
        not in sense.get("glosses", []) + sense.get("raw_glosses", [])
    ):
        raise ValueError("intermediate does not attest the retained base and degree")
    observation, pin = evidence.get("primary_observation"), evidence.get("primary_research_pin")
    if not isinstance(observation, dict) or _hash(observation) != evidence.get(
        "primary_observation_sha256"
    ) or not isinstance(pin, dict):
        raise ValueError("official Finnish paradigm observation is unbound")
    cells = ["helposti", "helpommin", "helpoimmin", "~ helpoiten"]
    html_sha = pin.get("html_sha256")
    if (
        observation.get("url")
        != "https://kielitoimistonohjepankki.fi/ohje/vertailuilmauksia-parhaiten-vai-parhaimmin-tavan-adverbit/"
        or observation.get("exact_short_quote") != " | ".join(cells)
        or "research" not in _text(observation.get("license_gate")).lower()
        or "commercial" not in observation["license_gate"].lower()
        or pin.get("exact_paradigm_row", {}).get("cells") != cells
        or pin.get("license") != "CC BY-NC-ND 4.0"
        or not isinstance(html_sha, str)
        or len(html_sha) != 64
        or any(c not in "0123456789abcdef" for c in html_sha)
    ):
        raise ValueError("official Finnish paradigm row or license gate differs")


def _validate_relation_evidence(link, raw, target, source_index, language, pos):
    evidence = link.get("relation_evidence")
    if evidence is None:
        sense = raw["senses"][source_index]
        quote = _text(link.get("parent_relation_quote"))
        quotes = sense.get("glosses", []) + sense.get("raw_glosses", [])
        if quote not in [_text(q) for q in quotes] or _text(target["word"]) not in quote:
            raise ValueError("authored relation quote is not attested for this parent")
    elif isinstance(evidence, dict) and evidence.get("kind") == "explicit_chain":
        _validate_explicit_chain(evidence, raw, target, source_index, language, pos)
    elif isinstance(evidence, dict) and evidence.get("kind") == "ro_compound_perfect_aux":
        if source_index != 0 or pos != "VERB":
            raise ValueError("Romanian auxiliary source sense or part of speech differs")
        _validate_ro_aux(evidence, raw, target, link["parent_candidate_id"])
    elif isinstance(evidence, dict) and evidence.get("kind") == "sibling_form_of_spelling_note":
        _validate_greek_spelling_note(link, evidence, raw, target, source_index, language, pos)
    elif isinstance(evidence, dict) and evidence.get("kind") == "fi_official_superlative_variant":
        _validate_fi_superlative(link, evidence, raw, target, source_index, language, pos)
    else:
        raise ValueError("unsupported form relation evidence")


def validate_form_link(row, link, parent):
    """Recheck a bound source sense and an actually retained parent candidate."""
    if not parent or parent.get("identity_id") != link.get("parent_identity_id"):
        raise ValueError("form parent is absent or differs")
    language = row["language"]
    raw, target = link.get("source_record"), link.get("parent_record")
    if not isinstance(raw, dict) or not isinstance(target, dict):
        raise ValueError("full source and parent records required")
    own_sha, target_sha = _hash(raw), _hash(target)
    if (
        own_sha != link.get("source_record_sha256")
        or target_sha != link.get("parent_record_sha256")
        or raw.get("lang_code") != language
        or target.get("lang_code") != language
        or parent.get("language") != language
    ):
        raise ValueError("source record integrity or language differs")
    cid = link.get("source_candidate_id")
    available = {c["candidate_id"]: c for c in row["source_group"]["sense_candidates"]}
    index = link.get("source_sense_index")
    if (
        cid not in available
        or available[cid].get("source_record_sha256") != own_sha
        or type(index) is not int
        or not 0 <= index < len(raw.get("senses", []))
        or cid != "candidate:" + _hash(dict(record=own_sha, sense=index))
    ):
        raise ValueError("exact source candidate binding differs")
    form, lemma = _text(raw.get("word")), _text(target.get("word"))
    pos = UPOS.get(raw.get("pos"))
    if (
        form != _text(row["source_group"].get("lemma"))
        or lemma != _text(parent.get("lemma"))
        or form == lemma
        or not pos
        or pos != UPOS.get(target.get("pos"))
        or pos != parent.get("pos")
    ):
        raise ValueError("form or parent lexical identity differs")
    senses = parent.get("senses", [])
    if isinstance(senses, dict):
        senses = senses.values()
    retained = [s for s in senses if s.get("candidate_id") == link.get("parent_candidate_id")]
    if not retained or any(
        s.get("source_metadata", {}).get("source_record_sha256") != target_sha for s in retained
    ):
        raise ValueError("parent candidate is not retained from this exact source record")
    parent_ids = {
        "candidate:" + _hash(dict(record=target_sha, sense=i))
        for i in range(len(target.get("senses", [])))
    }
    if link["parent_candidate_id"] not in parent_ids:
        raise ValueError("parent candidate has no exact source sense")
    sense = raw["senses"][index]
    _validate_relation_evidence(link, raw, target, index, language, pos)
    features = link.get("features")
    if not isinstance(features, list) or not 1 <= len(features) <= 32:
        raise ValueError("explicit bounded morphological features required")
    features = [_text(f) for f in features]
    if len(set(features)) != len(features) or len(_text(link.get("rationale"))) < 12:
        raise ValueError("unique features and explicit rationale required")
    return dict(
        source_form=dict(form=form, features=features, source_sense=copy.deepcopy(sense)),
        source_review_unit_id=row["review_unit_id"],
        source_candidate_id=cid,
        parent_identity_id=parent["identity_id"],
        evidence=copy.deepcopy(link),
        selected_for_card=False,
        **FLAGS,
    )


def prepare_form_resolution(row, links, parents):
    """Preserve native data and previous resolution; prepare verified form links."""
    validate_coverage(row, links)
    for link in links:
        validate_form_link(row, link, parents.get(link.get("parent_identity_id")))
    result = copy.deepcopy(row)
    previous = copy.deepcopy(row.get("resolved_content"))
    result["decision"] = "include"
    result["resolved_content"] = dict(
        schema_version=SCHEMA,
        review_unit_id=row["review_unit_id"],
        original_binding=dict(baseline_sha256=_hash(row)),
        previous_resolution=previous,
        form_only_associations=copy.deepcopy(links),
        resolved_candidates=[],
        resolved_forms=dict(source_forms=[], selected_forms=[]),
        unresolved_questions=[],
        **FLAGS,
    )
    result.update(FLAGS)
    return result
