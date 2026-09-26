"""Source-bound Mandarin inventory qualification.

This module turns an explicit reviewer decision into stable lexical identities.
It never invents a reading, treats OpenCC as evidence, or marks a card ready for
production. Contextual examples and pronunciation reviews remain separate gates.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from pypinyin.contrib.tone_convert import to_tone

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexical_identity import LexicalIdentity, canonical_sha256
from multilang.services.mandarin_review import pinyin_key
from multilang.services.vocabulary_sources import _POS

_POS_BY_CANONICAL = set(_POS.values()) | {"AUX", "SCONJ", "PHRASE"}
_DISPOSITIONS = {"lexical", "compositional", "exclude", "pending"}


def _display_pinyin(value: str) -> str | None:
    """Convert an explicitly numbered reading to spaced tone-marked Pinyin."""
    parts = value.strip().lower().replace("u:", "ü").split()
    if pinyin_key(value) is None or not parts or any(not re.fullmatch(r"[a-zü:]+[1-5]", part) for part in parts):
        return None
    return " ".join(to_tone(part).replace("v", "ü") for part in parts)


def _canonical_pos(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if normalized in _POS_BY_CANONICAL:
        return normalized
    return _POS.get(normalized.casefold())


def _record_refs(evidence: dict) -> dict[str, dict]:
    """Expose only source records/senses that can support a decision."""
    allowed_forms = {_validate_word(evidence.get("word"), "evidence word")}
    allowed_forms.update(
        entry.get("traditional")
        for entry in evidence.get("cedict", [])
        if isinstance(entry, dict) and isinstance(entry.get("traditional"), str)
    )
    refs: dict[str, dict] = {}
    for index, entry in enumerate(evidence.get("cedict", [])):
        if not isinstance(entry, dict):
            continue
        pinyin = _display_pinyin(str(entry.get("numbered_pinyin", "")))
        if (pinyin is None or entry.get("simplified") != evidence["word"]
                or not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("line_sha256", "")))):
            continue
        refs[f"c{index}"] = {
            "traditional": entry.get("traditional"),
            "pinyin": pinyin,
            "pinyin_key": pinyin_key(pinyin),
            "glosses": entry.get("glosses", []),
            "pos": None,
            "source_record_sha256": entry.get("line_sha256"),
            "source_kind": "cc-cedict",
        }
    for record_index, record in enumerate(evidence.get("wiktextract", [])):
        if not isinstance(record, dict):
            continue
        if record.get("source_word") not in allowed_forms:
            continue
        pos = _canonical_pos(record.get("source_pos"))
        readings = {pinyin_key(item): item for item in record.get("record_pinyin", []) if pinyin_key(item)}
        if (not pos or len(readings) != 1 or
                not re.fullmatch(r"[0-9a-f]{64}", str(record.get("source_record_sha256", "")))):
            continue
        reading_key, reading = next(iter(readings.items()))
        # A traditional homograph such as 乾 qián is not evidence for 干 gān.
        pairs = [entry for entry in evidence.get("cedict", [])
                 if entry.get("traditional") == record.get("source_word")]
        if pairs and reading_key not in {pinyin_key(e["numbered_pinyin"]) for e in pairs}:
            continue
        for sense_index, sense in enumerate(record.get("senses", [])):
            if not isinstance(sense, dict) or sense.get("scope") != "mandarin-candidate":
                continue
            glosses = sense.get("glosses", [])
            if not glosses:
                continue
            source_id = sense.get("source_sense_id") or f"sense-{sense_index}"
            ref = f"w{record_index}:{source_id}"
            refs[ref] = {
                "traditional": record.get("source_word"),
                "pinyin": reading,
                "pinyin_key": reading_key,
                "glosses": glosses,
                "pos": pos,
                "source_record_sha256": record["source_record_sha256"],
                "source_kind": "wiktextract",
                "source_sense_key": canonical_sha256({
                    "source_sense_id": sense.get("source_sense_id"), "glosses": glosses,
                }),
            }
    return refs


def source_choices(evidence: dict) -> list[dict]:
    """Return candidate decisions backed by explicit source readings and senses."""
    refs = _record_refs(evidence)
    choices = []
    for ref, value in refs.items():
        choices.append({"source_ref": ref, **value})
    return choices


def _validate_word(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        raise ValueError(f"{label} must be bounded text")
    result = unicodedata.normalize("NFC", value.strip())
    if any(unicodedata.category(char).startswith("C") for char in result):
        raise ValueError(f"{label} contains a control character")
    return result


def _identity(*, word: str, pos: str, pinyin: str,
              source_hash: str, gloss_indices: list[int], source_sense_key: str | None = None) -> LexicalIdentity:
    binding = {
        "word": word, "pos": pos, "source_record_sha256": source_hash,
        "pinyin": pinyin_key(pinyin), "gloss_indices": sorted(gloss_indices),
    }
    if source_sense_key is not None:
        binding["source_sense_key"] = source_sense_key
    sense_id = "zh-sense-" + canonical_sha256(binding)[:48]
    return LexicalIdentity(
        language=SupportedLanguage.ZH,
        normalized_lemma=word,
        part_of_speech=pos,
        sense_id=sense_id,
        profile_version="mandarin-standard-v1",
        normalizer_version="nfc-preserve-1",
        analyzer_version="source-bound-v3" if source_sense_key is not None else "source-bound-v2",
        source_id="mandarin-qualification",
        source_version="2026-09-20",
        source_sha256=source_hash,
    )


def qualify_decision(evidence: dict, decision: dict, *, reviewer: str) -> dict:
    """Validate one explicit decision against frozen evidence.

    The result is source-qualified metadata only. ``production_eligible`` stays
    false until contextual content, audio and export gates are independently met.
    """
    if not isinstance(evidence, dict) or not isinstance(decision, dict):
        raise ValueError("evidence and decision must be objects")
    if set(decision) - {"word", "disposition", "reason", "components", "senses"}:
        raise ValueError("unknown decision fields")
    reviewer = _validate_word(reviewer, "reviewer")
    word = _validate_word(evidence.get("word"), "evidence word")
    if _validate_word(decision.get("word"), "decision word") != word:
        raise ValueError("decision word does not match evidence")
    disposition = decision.get("disposition")
    if disposition not in _DISPOSITIONS:
        raise ValueError("unsupported Mandarin disposition")
    candidate = evidence.get("frequency_candidate")
    if not isinstance(candidate, dict):
        raise ValueError("frequency candidate metadata is required")
    try:
        rank, level = int(candidate["rank"]), int(candidate["level"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("frequency rank and level are required") from None
    if rank < 1 or level not in {1, 2, 3}:
        raise ValueError("frequency rank or level is invalid")
    if disposition in {"exclude", "pending"}:
        if decision.get("senses") or decision.get("components"):
            raise ValueError("excluded or pending decisions cannot declare senses or components")
        return {
            "word": word, "disposition": disposition, "reason": _validate_word(decision.get("reason", ""), "reason"),
            "frequency_rank": rank, "frequency_level": level, "senses": [], "components": [],
            "reviewer": reviewer, "production_eligible": False,
            "pronunciation_context_reviewed": False, "independent_human_review": False,
            "source_evidence_sha256": [],
        }
    if disposition == "compositional":
        components = decision.get("components")
        if (not isinstance(components, list) or not components or
                any(not isinstance(item, str) or not item for item in components) or
                "".join(components) != word):
            raise ValueError("components must concatenate exactly to the word")
        if decision.get("senses") or len(components) < 2:
            raise ValueError("compositional decisions require multiple components and no senses")
        return {
            "word": word, "disposition": disposition, "reason": _validate_word(decision.get("reason", ""), "reason"),
            "frequency_rank": rank, "frequency_level": level, "senses": [],
            "components": [_validate_word(item, "component") for item in components],
            "reviewer": reviewer, "production_eligible": False,
            "pronunciation_context_reviewed": False, "independent_human_review": False,
            "source_evidence_sha256": [],
        }
    refs = _record_refs(evidence)
    raw_senses = decision.get("senses")
    if not isinstance(raw_senses, list) or not 1 <= len(raw_senses) <= 40:
        raise ValueError("lexical decision requires senses")
    components = decision.get("components", [])
    if components and (not isinstance(components, list) or len(components) < 2 or
                       any(not isinstance(x, str) for x in components) or "".join(components) != word):
        raise ValueError("components must concatenate exactly to the word")
    senses, hashes = [], []
    for raw in raw_senses:
        if not isinstance(raw, dict) or raw.get("source_ref") not in refs:
            raise ValueError("sense source_ref is not present in evidence")
        if set(raw) - {"source_ref", "source_record_sha256", "gloss_indices", "pos", "pinyin", "label_en", "usage"}:
            raise ValueError("unknown sense fields")
        source_ref = raw["source_ref"]
        source = refs[source_ref]
        if raw.get("source_record_sha256", source["source_record_sha256"]) != source["source_record_sha256"]:
            raise ValueError("sense source hash differs from evidence")
        pos = _canonical_pos(raw.get("pos"))
        if not pos or source["source_kind"] == "cc-cedict" and not pos:
            raise ValueError("sense POS must be a supported canonical source POS")
        if source["pos"] is not None and pos != source["pos"]:
            raise ValueError("sense POS does not match the source record")
        indices = raw.get("gloss_indices")
        if (not isinstance(indices, list) or not indices or
                any(type(item) is not int or item < 0 or item >= len(source["glosses"])
                    for item in indices) or len(indices) != len(set(indices))):
            raise ValueError("sense gloss_indices do not match source")
        glosses = [source["glosses"][index] for index in sorted(indices)]
        if any(re.match(r"surname\b", gloss, re.I) for gloss in glosses) and pos != "PROPN":
            raise ValueError("surname evidence requires PROPN")
        pinyin = raw.get("pinyin") or source["pinyin"]
        if not isinstance(pinyin, str) or pinyin_key(pinyin) != source["pinyin_key"]:
            raise ValueError("sense pinyin is not source-attested")
        identity = _identity(word=word, pos=pos, pinyin=pinyin,
                             source_hash=source["source_record_sha256"], gloss_indices=indices,
                             source_sense_key=source.get("source_sense_key"))
        senses.append({
            "identity": identity.model_dump(mode="json"), "source_ref": source_ref,
            "source_kind": source["source_kind"], "source_record_sha256": source["source_record_sha256"],
            "traditional": source["traditional"], "pinyin": pinyin, "pos": pos,
            "glosses": glosses, "gloss_indices": sorted(indices),
            "label_en": _validate_word(raw.get("label_en", glosses[0]), "sense label"),
            "usage": _validate_word(raw.get("usage", "general"), "usage"),
            "frequency_rank": rank, "frequency_level": level,
        })
        hashes.append(source["source_record_sha256"])
    if len({item["identity"]["lexical_identity_id"] for item in senses}) != len(senses):
        raise ValueError("lexical senses must have distinct identities")
    return {
        "word": word, "disposition": disposition, "reason": _validate_word(decision.get("reason", ""), "reason"),
        "frequency_rank": rank, "frequency_level": level, "senses": senses, "components": components,
        "reviewer": reviewer, "production_eligible": False,
        "pronunciation_context_reviewed": False, "independent_human_review": False,
        "source_evidence_sha256": sorted(set(hashes)),
    }


def validate_batch(evidence_rows: Iterable[dict], payload: dict, *, reviewer: str = "machine-proposal") -> list[dict]:
    """Require a one-to-one decision inventory before persisting a batch."""
    rows = list(evidence_rows)
    decisions = payload.get("decisions") if isinstance(payload, dict) else None
    if not isinstance(decisions, list):
        raise ValueError("batch decisions must be a list")
    words = [_validate_word(row.get("word"), "evidence word") for row in rows]
    if any(not isinstance(item, dict) for item in decisions):
        raise ValueError("decisions must be objects")
    decision_words = [_validate_word(item.get("word"), "decision word") for item in decisions]
    if (len(words) != len(set(words)) or len(decision_words) != len(set(decision_words))
            or set(words) != set(decision_words)):
        raise ValueError("batch word set must match evidence exactly")
    by_word = {row["word"]: row for row in rows}
    return [qualify_decision(by_word[d["word"]], d, reviewer=reviewer) for d in decisions]


__all__ = ["qualify_decision", "source_choices", "validate_batch"]
