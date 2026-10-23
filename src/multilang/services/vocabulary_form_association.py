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
    quote = _text(link.get("parent_relation_quote"))
    quotes = sense.get("glosses", []) + sense.get("raw_glosses", [])
    if quote not in [_text(q) for q in quotes] or lemma not in quote:
        raise ValueError("authored relation quote is not attested for this parent")
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
