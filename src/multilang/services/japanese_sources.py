"""Bounded Japanese dictionary evidence and aggregate frequency sources.

JMdict entities are labels, never executable or recursively expanded XML. Source
locators include the snapshot: neither a sense ordinal nor a corpus rank is a
permanent semantic identity. TUBELEX rows deliberately are not CorpusObservation.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from collections import deque
from collections.abc import Iterator
from pathlib import Path
from xml.etree.ElementTree import Element, tostring
from xml.parsers import expat

from pydantic import Field, model_validator

from multilang.domain.language_profiles import NativeContract
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.vocabulary_sources import (
    LexicalSenseCandidate,
    SourceLimits,
    _verified_lines,
)


class JapaneseFrequencyCount(NativeContract):
    word: str = Field(min_length=1, max_length=512)
    count: int = Field(ge=1)
    videos: int = Field(ge=1)
    channels: int = Field(ge=1)
    majority_pos: str | None = None
    category_counts: dict[str, int] = Field(default_factory=dict)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def counts_are_consistent(self):
        if not self.channels <= self.videos <= self.count:
            raise ValueError("inconsistent TUBELEX occurrence/dispersion counts")
        if any(n < 0 or n > self.count for n in self.category_counts.values()):
            raise ValueError("invalid TUBELEX category count")
        return self


def read_tubelex(
    path: Path, *, expected_sha256: str, limits: SourceLimits | None = None
) -> Iterator[JapaneseFrequencyCount]:
    """Read the published TSV schema, including totals, without normalizing words.

    Different upstream normalizations must remain separate snapshots. POS is the
    majority label for a spelling, not an assertion about every occurrence.
    """
    limits = limits or SourceLimits()
    reader = csv.DictReader(_verified_lines(path, expected_sha256, limits), delimiter="\t", quoting=csv.QUOTE_NONE)
    columns = reader.fieldnames or []
    if (not {"word", "count", "videos", "channels"}.issubset(columns)
            or len(columns) != len(set(columns))):
        raise ValueError("invalid TUBELEX header")
    seen = set()
    total = None
    count_sum = max_videos = max_channels = 0
    for row in reader:
        if None in row or any(value is None for value in row.values()) or total is not None:
            raise ValueError("malformed TUBELEX row or trailing data after totals")
        numeric = {}
        for name in columns:
            if name in {"count", "videos", "channels"} or name.startswith("count:"):
                if not re.fullmatch(r"[0-9]{1,18}", row[name]):
                    raise ValueError("invalid TUBELEX numeric value")
                numeric[name] = int(row[name])
        if row["word"] == "[TOTAL]":
            total = numeric
            continue
        if row["word"] in seen:
            raise ValueError("duplicate TUBELEX word")
        seen.add(row["word"])
        if len(seen) > limits.max_unique_entries:
            raise ValueError("TUBELEX unique entry limit exceeded")
        result = JapaneseFrequencyCount(
            word=row["word"], count=numeric["count"], videos=numeric["videos"],
            channels=numeric["channels"], majority_pos=row.get("pos") or None,
            category_counts={key[6:]: value for key, value in numeric.items() if key.startswith("count:")},
            source_sha256=expected_sha256,
        )
        count_sum += result.count
        max_videos = max(max_videos, result.videos)
        max_channels = max(max_channels, result.channels)
        yield result
    if (total is None or total["count"] != count_sum or total["videos"] < max_videos
            or total["channels"] < max_channels):
        raise ValueError("TUBELEX totals do not match the published rows")


def _texts(element: Element, name: str) -> tuple[str, ...]:
    return tuple(unicodedata.normalize("NFC", (e.text or "").strip()) for e in element.findall(name))


def _pos(label: str) -> str:
    if label in {"n", "n-adv", "n-t", "n-pref", "n-suf"}:
        return "NOUN"
    if label == "n-pr":
        return "PROPN"
    if label in {"aux", "aux-v", "aux-adj"}:
        return "AUX"
    if re.fullmatch(r"v(?:[1-5][a-z0-9-]*|[krsz][a-z0-9-]*)", label):
        return "VERB"
    if label.startswith("adj-"):
        return "ADJ"
    return {"adv": "ADV", "adv-to": "ADV", "pn": "PRON", "prt": "PART",
            "conj": "CCONJ", "int": "INTJ", "num": "NUM"}.get(label, "X")


def _jmdict_candidates(entry: Element, digest: str, selected: set[str] | None, diagnostics=None):
    sequence = entry.findtext("ent_seq", "")
    if not re.fullmatch(r"[0-9]{1,12}", sequence):
        raise ValueError("invalid JMdict entry identifier")
    written = {e.findtext("keb", ""): e for e in entry.findall("k_ele")}
    readings = {e.findtext("reb", ""): e for e in entry.findall("r_ele")}
    if not readings or "" in readings or "" in written:
        raise ValueError("JMdict requires nonempty forms and readings")
    pairs = []
    for reading, node in readings.items():
        restrictions = _texts(node, "re_restr")
        if not set(restrictions).issubset(written):
            raise ValueError("dangling JMdict reading restriction")
        if node.find("re_nokanji") is not None or not written:
            if restrictions:
                raise ValueError("conflicting JMdict kana-only restriction")
            forms = (reading,)
        else:
            forms = restrictions or tuple(written)
        pairs.extend((word, reading) for word in forms)
    inherited_pos = ()
    record_hash = None
    for index, sense in enumerate(entry.findall("sense"), 1):
        inherited_pos = _texts(sense, "pos") or inherited_pos
        spellings, pronunciations = _texts(sense, "stagk"), _texts(sense, "stagr")
        if not set(spellings).issubset(written) or not set(pronunciations).issubset(readings):
            raise ValueError("dangling JMdict sense restriction")
        glosses = tuple((node.text or "").strip() for node in sense.findall("gloss")
                       if node.attrib.get("xml:lang", "eng") == "eng" and (node.text or "").strip())
        if not glosses:
            continue
        permitted = [(word, reading) for word, reading in pairs
                     if (not spellings or word in spellings)
                     and (not pronunciations or reading in pronunciations)]
        if not permitted:
            if diagnostics is None:
                raise ValueError("JMdict sense has no permitted written/reading pair")
            diagnostics.append({"entry_id": sequence, "sense_ordinal": index,
                "source_sha256": digest,
                "reason": "incompatible_jmdict_reading_and_sense_restrictions"})
            continue
        usage = tuple(f"{name}:{value}" for name in ("misc", "field", "dial", "s_inf")
                      for value in _texts(sense, name))
        for word, reading in permitted:
            if selected is not None and not {word.casefold(), reading.casefold()} & selected:
                continue
            if record_hash is None:
                record_hash = canonical_sha256(tostring(entry, encoding="unicode"))
            tags = tuple(f"pos:{label}" for label in inherited_pos) + usage
            tags += tuple(f"priority:{value}" for value in _texts(readings[reading], "re_pri"))
            if word in written:
                tags += tuple(f"priority:{value}" for value in _texts(written[word], "ke_pri"))
                tags += tuple(f"writing:{value}" for value in _texts(written[word], "ke_inf"))
            tags += tuple(f"reading:{value}" for value in _texts(readings[reading], "re_inf"))
            for pos in sorted({_pos(label) for label in inherited_pos if label not in {"vt", "vi"}} or {"X"}):
                evidence = f"jmdict:{digest}:{sequence}:sense:{index}"
                yield LexicalSenseCandidate(
                    language="ja", lemma=word, pos=pos,
                    candidate_id="jmdict-" + canonical_sha256((evidence, word, reading, pos)),
                    source_record_sha256=record_hash, source_sense_ids=(evidence,),
                    glosses=glosses, tags=tags,
                    forms=tuple({"form": form, "reading": sound, "tags": ["jmdict-permitted-pair"]}
                                for form, sound in permitted),
                    sounds=({"reading": reading, "source": "jmdict", "entry_id": sequence,
                             "stagk": list(spellings), "stagr": list(pronunciations)},),
                )


def read_jmdict(
    path: Path, *, expected_sha256: str, lemmas: set[str] | None = None,
    limits: SourceLimits | None = None,
    diagnostics: list[dict] | None = None,
) -> Iterator[LexicalSenseCandidate]:
    """Stream legacy JMdict XML with entity expansion and network access disabled.

    Only bounded literal entity declarations are accepted. Their descriptions
    never enter the parser: references retain the label (e.g. ``v1``). Unknown
    POS labels stay X for review. External/parameter/recursive entities fail.
    """
    limits = limits or SourceLimits()
    selected = {unicodedata.normalize("NFC", word).casefold() for word in lemmas} if lemmas is not None else None
    parser = expat.ParserCreate()
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    stack: list[Element] = []
    completed: deque[Element] = deque()
    entities: set[str] = set()
    entry_bytes = entry_nodes = entry_count = 0

    def doctype(name, system, public, internal):
        if name != "JMdict" or system or public:
            raise ValueError("external or unsupported JMdict DTD")

    def entity(name, parameter, value, base, system, public, notation):
        if (parameter or system or public or notation or value is None
                or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9-]{0,31}", name)
                or len(value) > 512 or any(c in value for c in "&%<>") or name in entities):
            raise ValueError("unsafe JMdict entity declaration")
        entities.add(name)
        if len(entities) > 512:
            raise ValueError("JMdict entity limit exceeded")

    def start(name, attributes):
        nonlocal entry_nodes, entry_bytes
        if len(stack) >= 16 or (not stack and name != "JMdict"):
            raise ValueError("invalid JMdict nesting or root")
        if len(stack) == 1:
            if name != "entry":
                raise ValueError("unsupported JMdict root child")
            entry_nodes = entry_bytes = 0
        entry_nodes += 1
        if entry_nodes > 8192:
            raise ValueError("JMdict entry node limit exceeded")
        node = Element(name, attributes)
        if len(stack) > 1:
            stack[-1].append(node)
        stack.append(node)

    def end(name):
        nonlocal entry_count
        node = stack.pop()
        if name == "entry":
            entry_count += 1
            if entry_count > limits.max_records:
                raise ValueError("JMdict entry limit exceeded")
            completed.append(node)

    def characters(value):
        nonlocal entry_bytes
        if len(stack) > 1:
            entry_bytes += len(value.encode("utf-8"))
            if entry_bytes > limits.max_line_bytes:
                raise ValueError("JMdict entry byte limit exceeded")
            stack[-1].text = (stack[-1].text or "") + value

    def default(value):
        if value.startswith("&") and value.endswith(";") and len(stack) > 1:
            label = value[1:-1]
            if label not in entities:
                raise ValueError("undeclared JMdict entity")
            characters(label)

    def external(*args):
        raise ValueError("external JMdict entities are forbidden")

    parser.StartDoctypeDeclHandler = doctype
    parser.EntityDeclHandler = entity
    parser.ExternalEntityRefHandler = external
    parser.StartElementHandler, parser.EndElementHandler = start, end
    parser.CharacterDataHandler, parser.DefaultHandler = characters, default
    try:
        for line in _verified_lines(path, expected_sha256, limits, max_lines=limits.max_records * 128):
            parser.Parse(line, False)
            while completed:
                yield from _jmdict_candidates(completed.popleft(), expected_sha256, selected, diagnostics)
        parser.Parse("", True)
    except expat.ExpatError as exc:
        raise ValueError("malformed JMdict XML") from exc
