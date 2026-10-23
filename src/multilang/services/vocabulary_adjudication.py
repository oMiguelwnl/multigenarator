"""Bind explicit editorial decisions to immutable dictionary sense evidence.

This is a validator/materializer, never a semantic classifier. The caller must
read and adjudicate each candidate; no decision is inferred from gloss text.
"""

from __future__ import annotations

import copy
import hashlib
import json
import unicodedata

FLAGS = dict(production_eligible=False, human_approved=False, generation_status="deferred_by_user")
UPOS = {
    "noun": "NOUN",
    "name": "PROPN",
    "verb": "VERB",
    "adj": "ADJ",
    "adv": "ADV",
    "pron": "PRON",
    "det": "DET",
    "article": "DET",
    "prep": "ADP",
    "postp": "ADP",
    "num": "NUM",
    "intj": "INTJ",
    "particle": "PART",
}
DOCUMENTARY = {
    "contraction": "CONTRACTION",
    "prefix": "PREFIX",
    "suffix": "SUFFIX",
    "affix": "AFFIX",
    "infix": "INFIX",
    "circumfix": "CIRCUMFIX",
    "phrase": "EXPRESSION",
    "proverb": "PROVERB",
    "character": "CHARACTER",
    "symbol": "SYMBOL",
    "abbrev": "ABBREVIATION",
    "root": "ROOT",
    "conj": "CONJUNCTION",
    "circumpos": "CIRCUMPOSITION",
    "prep_phrase": "PREPOSITIONAL_EXPRESSION",
}


def _hash(value):
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def adjudicate(row, proposal, raw_records):
    """Apply one explicit decision, preserving every native source/review field.

    All original candidates must be accounted for. Each exact sense is checked
    against both its ancestor candidate ID and the canonical raw-record hash.
    Documentary classes are kept in a named namespace, never relabeled NOUN to
    satisfy a universal tagset. They require separate corpus alignment later.
    """
    if (
        proposal.get("language") != row.get("language")
        or proposal.get("review_unit_id") != row.get("review_unit_id")
        or proposal.get("baseline_sha256") != _hash(row)
    ):
        raise ValueError("proposal baseline binding differs")
    if row.get("resolved_content"):
        raise ValueError("existing resolution requires an explicit reconciliation, not replacement")
    group = row["source_group"]
    available = {c["candidate_id"]: c for c in group["sense_candidates"]}
    candidates = proposal.get("candidates", [])
    ids = [c.get("source_candidate_id") for c in candidates]
    if len(ids) != len(set(ids)) or set(ids) != set(available) or not ids:
        raise ValueError("every original candidate requires exactly one adjudication")
    resolutions = []
    for judgment in candidates:
        cid = judgment["source_candidate_id"]
        record_hash = available[cid]["source_record_sha256"]
        raw = raw_records.get(record_hash)
        if not raw or _hash(raw) != record_hash or raw.get("lang_code") != row["language"]:
            raise ValueError("raw source integrity or language binding differs")
        index = judgment.get("sense_index")
        if type(index) is not int or not 0 <= index < len(raw.get("senses", [])):
            raise ValueError("invalid exact sense index")
        sense = raw["senses"][index]
        if cid != "candidate:" + _hash(dict(record=record_hash, sense=index)) or judgment.get(
            "sense_sha256"
        ) != _hash(sense):
            raise ValueError("candidate or sense hash binding differs")
        disposition = judgment.get("disposition")
        rationale = judgment.get("rationale")
        if (
            disposition not in {"retained", "omitted", "quarantined"}
            or not isinstance(rationale, str)
            or len(rationale.strip()) < 12
        ):
            raise ValueError("explicit candidate disposition and rationale required")
        source_pos = raw.get("pos")
        pos = UPOS.get(source_pos) or DOCUMENTARY.get(source_pos)
        if disposition == "retained" and not pos:
            raise ValueError("source class has no documented representation")
        lemma = unicodedata.normalize("NFC", raw["word"])
        if lemma != unicodedata.normalize("NFC", group["lemma"]):
            raise ValueError("lemma reconstruction requires separate source-bound evidence")
        contexts = []
        for context in judgment.get("source_contexts", []):
            related_hash = context.get("source_record_sha256")
            related = raw_records.get(related_hash)
            related_index = context.get("sense_index")
            if (
                not related
                or _hash(related) != related_hash
                or related.get("lang_code") != row["language"]
                or type(related_index) is not int
                or not 0 <= related_index < len(related.get("senses", []))
            ):
                raise ValueError("related source context binding differs")
            related_sense = related["senses"][related_index]
            if (
                context.get("sense_sha256") != _hash(related_sense)
                or not isinstance(context.get("rationale"), str)
                or len(context["rationale"].strip()) < 12
                or not isinstance(context.get("relation_type"), str)
                or not context["relation_type"].strip()
            ):
                raise ValueError("related context requires exact sense and explicit relation")
            contexts.append(
                dict(
                    **copy.deepcopy(context),
                    source_word=related["word"],
                    source_pos=related.get("pos"),
                    source_language=related["lang_code"],
                    source_sense=copy.deepcopy(related_sense),
                    selected_as_own_sense=False,
                )
            )
        resolutions.append(
            dict(
                source_candidate_id=cid,
                disposition=disposition,
                lemma=lemma,
                pos=pos,
                source_pos=source_pos,
                pos_namespace="UPOS-source-mapping"
                if source_pos in UPOS
                else "wiktextract-documentary",
                lexical_unit_kind=source_pos if source_pos in DOCUMENTARY else "word",
                rationale=rationale,
                source_sense=copy.deepcopy(sense),
                **({"source_contexts": contexts} if contexts else {}),
                unresolved_questions=[rationale] if disposition == "quarantined" else [],
                evidence=[
                    dict(
                        source_record_sha256=record_hash,
                        sense_index=index,
                        sense_sha256=_hash(sense),
                        source_candidate_id=cid,
                        source_language=raw["lang_code"],
                        source_word=raw["word"],
                        source_pos=source_pos,
                    )
                ],
                **FLAGS,
            )
        )
    dispositions = {c["disposition"] for c in resolutions}
    decision = (
        "include"
        if "retained" in dispositions
        else "uncertain"
        if "quarantined" in dispositions
        else "exclude"
    )
    if proposal.get("decision") != decision:
        raise ValueError("unit decision contradicts candidate adjudications")
    result = copy.deepcopy(row)
    result.update(decision=decision, **FLAGS)
    result["resolved_content"] = dict(
        schema_version="source-bound-adjudication-1",
        review_unit_id=row["review_unit_id"],
        original_binding=dict(
            baseline_sha256=proposal["baseline_sha256"],
            source_binding=copy.deepcopy(row.get("source_binding")),
            review_sha256=(row.get("imported_review") or {}).get("review_sha256"),
        ),
        adjudication_sha256=_hash(proposal),
        resolved_candidates=resolutions,
        resolved_forms=dict(source_forms=[], selected_forms=[]),
        unresolved_questions=[],
        derived_identities=[],
        **FLAGS,
    )
    return result
