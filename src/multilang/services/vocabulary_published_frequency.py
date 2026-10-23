"""Strict, pure adapters for Lexique 4.10 and BNC published lemma rates.

Callers pin source bytes and provenance before parsing. Rates remain per million,
not reconstructed counts or a coverage denominator. Conservative class alignment
never splits source aggregates across ambiguous POS, senses, or readings.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation

LEXIQUE_POS = {
    "NOM": "NOUN",
    "ADJ": "ADJ",
    "ADV": "ADV",
    "VER": "VERB",
    "AUX": "AUX",
    "PRE": "ADP",
    "PRO:per": "PRON",
    "PRO:ind": "PRON",
    "PRO:pos": "PRON",
    "PRO:dem": "PRON",
    "PRO:int": "PRON",
    "PRO:rel": "PRON",
    "ART:def": "DET",
    "ART:ind": "DET",
}
BNC_POS = {
    "NoC": "NOUN",
    "Adj": "ADJ",
    "Adv": "ADV",
    "Verb": "VERB",
    "VMod": "AUX",
    "Prep": "ADP",
    "Pron": "PRON",
    "Det": "DET",
    "Int": "INTJ",
    "Num": "NUM",
}
FLAGS = dict(
    is_coverage_measurement=False,
    general_frequency_certified=False,
    coverage_90_percent_verified=False,
    generation_status="deferred_by_user",
)


def _hash(value):
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _lines(text, max_bytes, max_rows):
    if not isinstance(text, str) or len(text.encode()) > max_bytes:
        raise ValueError("source byte limit exceeded")
    lines = text.splitlines()
    if len(lines) > max_rows:
        raise ValueError("source row limit exceeded")
    return lines


def _rate(value):
    if not isinstance(value, str) or len(value) > 32 or any(c in value for c in "eE"):
        raise ValueError("invalid published rate representation")
    try:
        rate = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid published rate") from exc
    if not rate.is_finite() or rate < 0 or rate > 1_000_000:
        raise ValueError("invalid published rate")
    return rate


def _number(value):
    return format(value.normalize(), "f")


def _lemma(value):
    if (
        not value
        or value != value.strip()
        or len(value) > 512
        or any(unicodedata.category(c).startswith("C") for c in value)
    ):
        raise ValueError("invalid lemma")
    return unicodedata.normalize("NFC", value)


def _finish(groups, excluded, examples, *, source_id, language, modality, rows, cutoff):
    entries, quarantine, keys = [], [], defaultdict(list)
    for (lemma, pos, source_pos), observations in sorted(groups.items()):
        rates = sorted({value for _, value in observations})
        item = dict(
            lemma=lemma,
            pos=pos,
            source_pos=source_pos,
            source_lines=[line for line, _ in observations],
        )
        if len(rates) != 1:
            quarantine.append(
                dict(
                    **item,
                    reason="conflicting_published_lemma_rates",
                    values=[_number(v) for v in rates],
                )
            )
            continue
        item["frequency_per_million"] = _number(rates[0])
        keys[lemma, pos].append(item)
    for rows_for_key in keys.values():
        if len(rows_for_key) > 1:
            quarantine.append(
                dict(
                    lemma=rows_for_key[0]["lemma"],
                    pos=rows_for_key[0]["pos"],
                    reason="multiple_source_classes_for_same_inventory_key",
                    source_classes=rows_for_key,
                )
            )
        else:
            entries.append(rows_for_key[0])
    entries.sort(key=lambda r: (-Decimal(r["frequency_per_million"]), r["lemma"], r["pos"]))
    previous, rank = None, 0
    for i, row in enumerate(entries, 1):
        rate = Decimal(row["frequency_per_million"])
        if rate != previous:
            rank = i
        previous = rate
        row["source_rank"] = rank
        row["source_key"] = source_id + ":" + _hash([row["lemma"], row["source_pos"]])
    return dict(
        schema_version="published-lemma-rates-1",
        source_id=source_id,
        language=language,
        modality=modality,
        source_rows=rows,
        entries=entries,
        quarantined_groups=quarantine,
        excluded_counts=dict(excluded),
        excluded_examples=examples,
        publication_cutoff_per_million=cutoff,
        frequency_unit="published_occurrences_per_million",
        rank_scope="competition_rank_within_positive_unambiguous_admitted_source_classes",
        alignment_policy="exact_NFC_lemma_case_preserved_conservative_source_POS",
        **FLAGS,
    )


def parse_lexique410(text, *, max_bytes=100_000_000, max_rows=500_000):
    """Collapse identical repeated FreqLemme; quarantine conflicting rates/classes."""
    lines = _lines(text, max_bytes, max_rows)
    header = lines[0].split("\t") if lines else []
    required = {"1_Mot", "4_Lemme", "5_Cgram", "12_FreqLemme"}
    if not required <= set(header) or len(header) != len(set(header)):
        raise ValueError("unsupported Lexique header")
    positions = {name: header.index(name) for name in required}
    groups, excluded, examples = defaultdict(list), Counter(), []
    rows = 0
    for line, raw in enumerate(lines[1:], 2):
        if not raw:
            continue
        rows += 1
        cells = raw.split("\t")
        if len(cells) != len(header):
            raise ValueError(f"Lexique columns differ on line {line}")
        source_pos = cells[positions["5_Cgram"]]
        if source_pos not in LEXIQUE_POS:
            reason = "unmapped_or_ambiguous_source_pos"
        else:
            try:
                lemma = _lemma(cells[positions["4_Lemme"]])
            except ValueError:
                reason = "invalid_source_lemma"
            else:
                value = _rate(cells[positions["12_FreqLemme"]])
                if value > 0:
                    groups[lemma, LEXIQUE_POS[source_pos], source_pos].append((line, value))
                    continue
                reason = "nonpositive_published_rate"
        excluded[reason] += 1
        if len(examples) < 20:
            examples.append(
                dict(
                    line=line,
                    reason=reason,
                    source_pos=source_pos,
                    source_row_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                )
            )
    return _finish(
        groups,
        excluded,
        examples,
        source_id="lexique-4.10",
        language="fr",
        modality="scripted_subtitles",
        rows=rows,
        cutoff=None,
    )


def parse_bnc(text, *, modality="whole", max_bytes=50_000_000, max_rows=1_000_000):
    """Read lemma head rows; never add @ variants to their published aggregate."""
    if modality not in {"whole", "spoken", "written"}:
        raise ValueError("invalid BNC modality")
    groups, excluded, examples, seen = defaultdict(list), Counter(), [], set()
    rows = 0
    for line, raw in enumerate(_lines(text, max_bytes, max_rows), 1):
        header = "Word\tPoS\t\tFrSp\tRa\tDiSp\t\tLogLi\tFrWr\tRa\tDiWr"
        if not raw.strip() or (modality != "whole" and raw in {header, "\t" + header}):
            continue
        rows += 1
        cells = raw.split("\t")
        width = 7 if modality == "whole" else 12
        if len(cells) == width + 1 and cells[-1] == "":
            cells.pop()
        if len(cells) != width or cells[0] != "":
            raise ValueError(f"BNC columns differ on line {line}")
        lemma, source_pos, marker = cells[1:4]
        if lemma == "@" or source_pos == "@":
            if lemma != "@" or source_pos != "@":
                raise ValueError("invalid BNC variant markers")
            reason = "variant_row"
        else:
            if marker not in {":", "%"}:
                raise ValueError("invalid BNC headword marker")
            key = lemma, source_pos
            if key in seen:
                raise ValueError("duplicate BNC headword key")
            seen.add(key)
            lemma = _lemma(lemma)
            rate_cells = [cells[4]] if modality == "whole" else [cells[4], cells[9]]
            marked_rate = any(any(c in value for c in "#&") for value in rate_cells)
            value = None if marked_rate else _rate(cells[4 if modality != "written" else 9])
            if marked_rate:
                reason = "editorially_marked_rate"
            elif source_pos not in BNC_POS:
                reason = "unmapped_or_ambiguous_source_pos"
            elif source_pos == "Verb" and lemma in {"be", "have", "do"}:
                reason = "verb_auxiliary_function_not_disambiguated"
            elif any(c in lemma for c in "&_*~/"):
                reason = "encoded_or_editorially_marked_headword"
            elif value == 0:
                reason = "nonpositive_published_rate"
            else:
                groups[lemma, BNC_POS[source_pos], source_pos].append((line, value))
                continue
        excluded[reason] += 1
        if len(examples) < 20:
            examples.append(
                dict(
                    line=line,
                    reason=reason,
                    source_pos=source_pos,
                    source_row_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                )
            )
    return _finish(
        groups,
        excluded,
        examples,
        source_id="bnc-wfwse-2001-" + modality,
        language="en",
        modality=modality,
        rows=rows,
        cutoff=None if modality == "whole" else 160,
    )


def bind_published_frequency(identities, evidence):
    """Bind exact lemma/class aggregates once; no sense-frequency allocation or sum."""
    source = {(r["lemma"], r["pos"]): r for r in evidence["entries"]}
    if len(source) != len(evidence["entries"]):
        raise ValueError("duplicate source key")
    bound, unmatched, seen = {}, [], set()
    for row in identities:
        uid = row["identity_id"]
        if uid in seen:
            raise ValueError("duplicate inventory identity")
        seen.add(uid)
        if row["language"] != evidence["language"]:
            raise ValueError("inventory language differs")
        key = _lemma(row["lemma"]), row["pos"]
        item = source.get(key)
        pin = dict(identity_id=uid, sha256=_hash(row))
        if item is None:
            unmatched.append(
                dict(
                    **pin,
                    lemma=row["lemma"],
                    pos=row["pos"],
                    reason="no_unique_positive_exact_lemma_class_rate",
                )
            )
            continue
        group = bound.setdefault(
            item["source_key"],
            dict(
                **item,
                identity_ids=[],
                inventory_pins=[],
                final_frequency_rank=None,
                frequency_scope="aggregate_lemma_source_class_not_individual_sense",
                semantic_eligibility_inferred=False,
                production_eligible=False,
            ),
        )
        group["identity_ids"].append(uid)
        group["inventory_pins"].append(pin)
    bindings = sorted(bound.values(), key=lambda r: (r["source_rank"], r["lemma"], r["pos"]))
    for group in bindings:
        group["identity_ids"].sort()
        group["inventory_pins"].sort(key=lambda p: p["identity_id"])
    return dict(
        schema_version="published-frequency-bindings-1",
        source_id=evidence["source_id"],
        language=evidence["language"],
        modality=evidence["modality"],
        frequency_unit=evidence["frequency_unit"],
        bindings=bindings,
        unmatched=unmatched,
        matched_identity_rows=len(seen) - len(unmatched),
        unmatched_identity_rows=len(unmatched),
        matched_source_keys=len(bindings),
        **FLAGS,
    )
