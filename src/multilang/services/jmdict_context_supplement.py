"""Bounded, offline JMdict context for frozen requests; never a review/import.

The legacy parser and all frozen artifacts stay untouched. All strings are
untrusted data. Integrity hashes bind inputs, not publisher or semantic approval.
"""

from __future__ import annotations

import csv
import hashlib
import io
import lzma
import platform
import re
import unicodedata
import zlib
from pathlib import Path, PurePosixPath
from xml.etree.ElementTree import Element, tostring
from xml.parsers import expat

from multilang.domain import jobs, language_profiles, lexical_identity, sentence_curriculum
from multilang.domain.lexical_identity import canonical_sha256
from multilang.services import (
    japanese_sources,
    qualification_machine_runner,
    qualification_review,
    vocabulary_curation,
    vocabulary_review,
    vocabulary_sources,
)
from multilang.services import (
    vocabulary_context_supplement as safe,
)
from multilang.services.qualification_machine_runner import json_bytes, persist_artifact
from multilang.services.qualification_review import _json
from multilang.services.vocabulary_curation import (
    SelectionResponse,
    selection_messages,
    split_review_group,
)
from multilang.services.vocabulary_review import _manifest_check, _plain_path

MIB = 1024**2
LIMITS = {
    "compressed_dictionary_bytes": 64 * MIB,
    "expanded_dictionary_bytes": 128 * MIB,
    "compressed_frequency_bytes": 16 * MIB,
    "expanded_frequency_bytes": 128 * MIB,
    "candidates_jsonl_bytes": 64 * MIB,
    "prepared_vocabulary_bytes": 64 * MIB,
    "prepared_forms_bytes": 64 * MIB,
    "metadata_file_bytes": 16 * MIB,
    "dictionary_entry_bytes": 2 * MIB,
    "jsonl_line_bytes": 2 * MIB,
    "xml_token_bytes": 256 * 1024,
    "xml_attribute_value_bytes": 64 * 1024,
    "dtd_bytes": 256 * 1024,
    "declared_entities": 512,
    "entity_description_chars": 512,
    "entry_nodes": 8192,
    "xml_depth": 16,
    "attributes_per_element": 32,
    "dictionary_entries": 1_000_000,
    "frequency_unique_surfaces": 1_000_000,
    "selected_request_units": 32,
    "selected_candidates": 256,
    "selected_unique_entries": 256,
    "entry_base_pairs": 1024,
    "reconstructed_candidates": 2048,
    "reconstructed_form_cells": 65536,
    "reconstruction_estimated_bytes": 16 * MIB,
    "output_total_bytes": 8 * MIB,
}
CHILDREN = {
    "JMdict": {"entry"},
    "entry": {"ent_seq", "k_ele", "r_ele", "sense"},
    "k_ele": {"keb", "ke_inf", "ke_pri"},
    "r_ele": {"reb", "re_nokanji", "re_restr", "re_inf", "re_pri"},
    "sense": {
        "stagk",
        "stagr",
        "pos",
        "xref",
        "ant",
        "field",
        "misc",
        "s_inf",
        "lsource",
        "dial",
        "gloss",
        "example",
    },
    "gloss": {"pri"},
    "example": {"ex_srce", "ex_text", "ex_sent"},
}
ELEMENTS = set(CHILDREN).union(*(v for v in CHILDREN.values()))
ATTRIBUTES = {
    "gloss": {"xml:lang", "g_gend", "g_type"},
    "lsource": {"xml:lang", "ls_type", "ls_wasei"},
    "ex_sent": {"xml:lang"},
    "ex_srce": {"exsrc_type"},
}
DTD_MODEL_HASHES = {
    "JMdict": "716ac9db91d2d7ecf25a5f9944545f9983370f3ff411cde908ca0fa8e53aa692",
    "ant": "63e951bde61937f01b9716a87ea4011b51fb444c36757510d45e8ffcacc01d4c",
    "dial": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "ent_seq": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "entry": "87ae22aadde59fdae3af8d4489f4e6e0da04a0473be694a0b4aa08288f47f744",
    "ex_sent": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "ex_srce": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "ex_text": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "example": "3a5d4c45fbc002286e315b365363822af7532003da7dfe49fff040cf46380913",
    "field": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "gloss": "a03369c4eb2d8dc57ca6f1131413349707ae87ae2822e6d32861b259f5ccedc9",
    "k_ele": "efa5f693a7064cc6615b25755af5312a6153b4adfe047b90159286e93450cedc",
    "ke_inf": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "ke_pri": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "keb": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "lsource": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "misc": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "pos": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "pri": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "r_ele": "5fc847d09729b2e95fae030c6dfa06d06d1619bd7c5327f06d67c29ccc6b43a5",
    "re_inf": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "re_nokanji": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "re_pri": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "re_restr": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "reb": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "s_inf": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "sense": "31dfef9ce6f36b11d073d4a5d20d9f47ac46a795f33f72ed2c1851e112746357",
    "stagk": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "stagr": "ce559c3becfed8ed1f4f702264c786fc945cdf1277f625aaf58e91047c91b932",
    "xref": "63e951bde61937f01b9716a87ea4011b51fb444c36757510d45e8ffcacc01d4c",
}

POLICY = {
    "schema_version": "jmdict-context-policy-3",
    "data": "All strings are untrusted literal data; no execution, decision, import or provider.",
    "identity": "whole legacy candidate equality; own reading is sounds/ID, never an arbitrary permitted form",
    "source_record_hash": "canonical JSON SHA256 of legacy ElementTree.tostring string with DTD defaults; not XML C14N",
    "raw_entry_hash": "SHA256 expanded UTF-8 bytes from <entry> through </entry>, excluding following CR/LF; half-open offsets",
    "jsonl_line_hash": "SHA256 physical line bytes excluding trailing CR/LF only; full file hash includes them",
    "source_hash": "SHA256 exact compressed bytes, separately expanded bytes; single member; EOF/CRC required",
    "xml": "bounded internal JMdict DTD; entity labels retained; external/parameter/recursive entities rejected; known elements/attributes only",
    "attributes": "expanded attributes include supported DTD defaults; explicit/default distinction not inferred; declarations retained",
    "completeness": "all supported literal entry fields preserved; linguistic interpretation incomplete; unknown XML fields rejected",
    "uninterpreted_semantics": [
        "xref/ant target resolution",
        "misc cross-sense scope",
        "priority-label frequency calibration",
        "example quality",
        "sense frequency",
        "semantic approval",
    ],
    "pos": "literal labels plus version-pinned legacy mapped POS and inheritance origin; unknown remains X",
    "frequency": "TUBELEX aggregate surface counts; derived count-desc-channels-desc-word-v1 ordinal; publisher_rank null; no sense or sibling rank inheritance",
    "supported_frequency_variants": ["unidic310-base", "unidic310-lemma"],
    "sibling": "reconstructed context only; frozen/request presence rederived; never new selectable indices",
    "limits": LIMITS,
    "reconstruction_budget": "before legacy materialization: bounded reading/writing pairs; cumulative candidates and copied form cells across target entries; conservative serialized payload estimate, not a hard RSS limit; original sense order/POS inheritance and literal restrictions retained",
    "element_declaration_model_hashes": DTD_MODEL_HASHES,
    "dtd_validation_scope": "internal DOCTYPE required; declared element models match pinned JMdict profile; supported child/attribute/identity checks, not a full validating DTD processor",
    "authority": "context_available_for_review_only",
}
KIND = "jmdict-context-supplement-3"
REFS = {
    "source_preparation",
    "source_catalog",
    "source",
    "candidates",
    "frequency_source",
    "frequency_comparison",
    "surface_priority",
    "prepared_vocabulary",
    "prepared_forms",
    "prepared_manifest",
    "packet",
    "request_manifest",
}
SENSE_KEYS = (
    "candidate_id",
    "source_record_sha256",
    "source_sense_ids",
    "glosses",
    "tags",
    "stable_sense_id",
)


def _limits(overrides=None):
    result = dict(LIMITS)
    if overrides is not None:
        if not isinstance(overrides, dict) or set(overrides) - set(result):
            raise ValueError("unsupported budget override")
        for key, value in overrides.items():
            result[key] = safe._budget(value, result[key])
    return result


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _expand(data: bytes, kind: str, maximum: int) -> bytes:
    """One bounded member; parsing receives exactly the already hashed bytes."""
    try:
        decoder = (
            zlib.decompressobj(31)
            if kind == "gzip"
            else lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=64 * MIB)
            if kind == "xz"
            else None
        )
        if decoder is None:
            raise ValueError("unsupported compression")
        raw = decoder.decompress(data, maximum + 1)
        if len(raw) > maximum:
            raise ValueError("expanded byte limit exceeded")
        if not decoder.eof or decoder.unused_data:
            raise ValueError("incomplete or multiple compressed members/trailing bytes")
        return raw
    except (zlib.error, lzma.LZMAError, EOFError) as exc:
        raise ValueError("invalid compressed source") from exc


def _xml_preflight(data, limits):
    """Bound tokens BEFORE Expat allocates them; this is not an XML parser.

    Delimiters inside quoted attributes/DTD declarations are skipped. Expat is
    still the syntax authority. Plain-text runs are also bounded before parsing.
    """
    if len(data) > limits["expanded_dictionary_bytes"]:
        raise ValueError("expanded dictionary byte limit exceeded")
    data.decode("utf-8", errors="strict")
    cursor = 0
    while cursor < len(data):
        start = data.find(b"<", cursor)
        if start < 0:
            start = len(data)
        reference_start = data.find(b"&", cursor, start)
        while reference_start >= 0:
            reference_end = data.find(b";", reference_start + 1, start)
            if reference_end < 0 or reference_end - reference_start + 1 > limits["xml_token_bytes"]:
                raise ValueError("XML entity-reference token limit exceeded")
            reference_start = data.find(b"&", reference_end + 1, start)
        if start - cursor > limits["dictionary_entry_bytes"]:
            raise ValueError("XML text byte limit exceeded")
        if start == len(data):
            break
        maximum = limits["xml_token_bytes"]
        if data.startswith(b"<!--", start):
            end = data.find(b"-->", start + 4)
            end = end + 3 if end >= 0 else len(data) + 1
        elif data.startswith(b"<![CDATA[", start):
            end = data.find(b"]]>", start + 9)
            end = end + 3 if end >= 0 else len(data) + 1
        elif data.startswith(b"<?", start):
            end = data.find(b"?>", start + 2)
            end = end + 2 if end >= 0 else len(data) + 1
        else:
            is_dtd = data.startswith(b"<!DOCTYPE", start)
            if is_dtd:
                maximum = min(maximum, limits["dtd_bytes"])
            quote = None
            brackets = 0
            end = start + 1
            while end < len(data):
                ch = data[end]
                if quote:
                    if ch == quote:
                        quote = None
                elif ch in (34, 39):
                    quote = ch
                elif is_dtd and data.startswith(b"<!--", end):
                    close = data.find(b"-->", end + 4)
                    if close < 0:
                        raise ValueError("malformed DTD comment")
                    end = close + 2
                elif is_dtd and ch == 91:
                    brackets += 1
                elif is_dtd and ch == 93:
                    brackets -= 1
                elif ch == 62 and not brackets:
                    end += 1
                    break
                end += 1
                if end - start > maximum:
                    raise ValueError("XML token/DTD byte limit exceeded")
        if end > len(data) or end - start > maximum:
            raise ValueError("XML token byte limit or unterminated token")
        cursor = end


def _check_reconstruction_budget(entry, raw_size, limits, usage):
    """Count the legacy product before allocating it, across all target entries.

    This is an allocation guard, not a second candidate/POS implementation.
    The unchanged legacy helper still constructs candidates and their identity.
    """
    if usage["raw"] + raw_size > limits["output_total_bytes"]:
        raise ValueError("raw context exceeds output byte limit")
    written = {x.findtext("keb", "") for x in entry.findall("k_ele")}
    readings = {x.findtext("reb", ""): x for x in entry.findall("r_ele")}
    if not readings or "" in written or "" in readings:
        raise ValueError("JMdict requires nonempty forms and readings")
    pairs = []
    for reading, node in readings.items():
        restrictions = japanese_sources._texts(node, "re_restr")
        if not set(restrictions).issubset(written):
            raise ValueError("dangling JMdict reading restriction")
        if node.find("re_nokanji") is not None or not written:
            if restrictions:
                raise ValueError("conflicting JMdict kana-only restriction")
            forms = (reading,)
        else:
            forms = restrictions or written
        if len(pairs) + len(forms) > limits["entry_base_pairs"]:
            raise ValueError("entry base pair limit exceeded")
        pairs.extend((word, reading) for word in forms)
    inherited_pos = ()
    candidate_count = form_cells = estimate = 0
    for sense in entry.findall("sense"):
        inherited_pos = japanese_sources._texts(sense, "pos") or inherited_pos
        spellings = set(japanese_sources._texts(sense, "stagk"))
        pronunciations = set(japanese_sources._texts(sense, "stagr"))
        if not spellings.issubset(written) or not pronunciations.issubset(readings):
            raise ValueError("dangling JMdict sense restriction")
        if not any(
            node.attrib.get("xml:lang", "eng") == "eng" and (node.text or "").strip()
            for node in sense.findall("gloss")
        ):
            continue
        permitted = [
            (word, reading)
            for word, reading in pairs
            if (not spellings or word in spellings)
            and (not pronunciations or reading in pronunciations)
        ]
        if not permitted:
            raise ValueError("JMdict sense has no permitted written/reading pair")
        mapped = {japanese_sources._pos(p) for p in inherited_pos if p not in {"vt", "vi"}}
        count = len(permitted) * len(mapped or {"X"})
        candidate_count += count
        form_cells += count * len(permitted)
        if usage["candidates"] + candidate_count > limits["reconstructed_candidates"]:
            raise ValueError("reconstructed candidate limit exceeded")
        if usage["forms"] + form_cells > limits["reconstructed_form_cells"]:
            raise ValueError("reconstructed form cell limit exceeded")
        # Escape/metadata allowance without constructing repeated dictionaries.
        form_bytes = sum(6 * (len(w.encode()) + len(r.encode())) + 256 for w, r in permitted)
        estimate += count * (8 * raw_size + 4096 + form_bytes)
    if usage["bytes"] + estimate > limits["reconstruction_estimated_bytes"]:
        raise ValueError("reconstruction estimated byte limit exceeded")
    usage["raw"] += raw_size
    usage["candidates"] += candidate_count
    usage["forms"] += form_cells
    usage["bytes"] += estimate


def _parse_jmdict(data: bytes, wanted: set[str], digest: str, limits=None):
    limits = _limits(limits)
    _xml_preflight(data, limits)
    parser = expat.ParserCreate(encoding="UTF-8")
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    stack = []
    literal = []
    entities = {}
    defaults = []
    found = {}
    seen = set()
    entry_start = entry_line = entry_nodes = entry_text = 0
    declared = set()
    seen_doctype = False
    reconstruction_usage = {"raw": 0, "candidates": 0, "forms": 0, "bytes": 0}

    def doctype(name, system, public, internal):
        nonlocal seen_doctype
        seen_doctype = True
        if name != "JMdict" or system or public or not internal:
            raise ValueError("external or unsupported JMdict DTD")

    def entity(name, parameter, value, base, system, public, notation):
        if (
            parameter
            or system
            or public
            or notation
            or value is None
            or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9-]{0,31}", name)
            or len(value) > limits["entity_description_chars"]
            or any(c in value for c in "&%<>")
            or name in entities
        ):
            raise ValueError("unsafe JMdict entity declaration")
        entities[name] = {
            "description": value,
            "declaration_byte_offset": parser.CurrentByteIndex,
            "declaration_line": parser.CurrentLineNumber,
        }
        if len(entities) > limits["declared_entities"]:
            raise ValueError("entity limit exceeded")

    def attlist(element, name, kind, default, required):
        if (
            name not in ATTRIBUTES.get(element, set())
            or kind != "CDATA"
            or required
            or (default is not None and (name != "xml:lang" or default != "eng"))
        ):
            raise ValueError("unsupported DTD attribute/default")
        if any(d["element"] == element and d["attribute"] == name for d in defaults):
            raise ValueError("duplicate DTD attribute declaration")
        defaults.append(
            {
                "element": element,
                "attribute": name,
                "default": default,
                "type": kind,
                "declaration_byte_offset": parser.CurrentByteIndex,
            }
        )

    def element_decl(name, model):
        if name not in ELEMENTS or name in declared:
            raise ValueError("unsupported or duplicate DTD element")
        if canonical_sha256(model) != DTD_MODEL_HASHES[name]:
            raise ValueError("unsupported DTD element production model")
        declared.add(name)

    def start(name, attributes):
        nonlocal entry_start, entry_line, entry_nodes, entry_text
        if (
            len(stack) >= limits["xml_depth"]
            or (not stack and name != "JMdict")
            or name not in ELEMENTS
        ):
            raise ValueError("unsupported XML nesting/element")
        if stack and name not in CHILDREN.get(stack[-1].tag, set()):
            raise ValueError("unsupported XML child")
        if (
            set(attributes) - ATTRIBUTES.get(name, set())
            or len(attributes) > limits["attributes_per_element"]
        ):
            raise ValueError("unsupported XML attributes")
        if any(len(v.encode()) > limits["xml_attribute_value_bytes"] for v in attributes.values()):
            raise ValueError("XML attribute byte limit exceeded")
        if name == "entry":
            entry_start = parser.CurrentByteIndex
            entry_line = parser.CurrentLineNumber
            entry_nodes = entry_text = 0
        if len(stack) >= 1:
            entry_nodes += 1
            if (
                entry_nodes > limits["entry_nodes"]
                or parser.CurrentByteIndex - entry_start > limits["dictionary_entry_bytes"]
            ):
                raise ValueError("entry node/byte limit exceeded")
        node = Element(name, attributes)
        tree = {"tag": name, "attributes": dict(attributes), "content": []}
        if len(stack) > 1:
            stack[-1].append(node)
            literal[-1]["content"].append(tree)
        stack.append(node)
        literal.append(tree)

    def characters(value):
        nonlocal entry_text
        if len(stack) > 1:
            entry_text += len(value.encode())
            if entry_text > limits["dictionary_entry_bytes"]:
                raise ValueError("entry text byte limit exceeded")
            stack[-1].text = (stack[-1].text or "") + value
            content = literal[-1]["content"]
            if content and isinstance(content[-1], str):
                content[-1] += value
            else:
                content.append(value)

    def default(value):
        if value.startswith("&") and value.endswith(";") and len(stack) > 1:
            label = value[1:-1]
            if label not in entities:
                raise ValueError("undeclared XML entity")
            characters(label)

    def end(name):
        node = stack.pop()
        tree = literal.pop()
        if name != "entry":
            return
        sequence = node.findtext("ent_seq", "")
        if (
            not re.fullmatch(r"[0-9]{1,12}", sequence)
            or len(node.findall("ent_seq")) != 1
            or sequence in seen
        ):
            raise ValueError("ambiguous entry identity")
        seen.add(sequence)
        if len(seen) > limits["dictionary_entries"]:
            raise ValueError("dictionary entry limit exceeded")
        if sequence not in wanted:
            return
        end_offset = data.find(b">", parser.CurrentByteIndex) + 1
        if end_offset <= entry_start or end_offset - entry_start > limits["dictionary_entry_bytes"]:
            raise ValueError("entry byte limit exceeded")
        for container, field in [("k_ele", "keb"), ("r_ele", "reb")]:
            values = [x.findtext(field, "") for x in node.findall(container)]
            if any(len(x.findall(field)) != 1 for x in node.findall(container)) or len(
                values
            ) != len(set(values)):
                raise ValueError("ambiguous duplicate written/reading identity")
        _check_reconstruction_budget(node, end_offset - entry_start, limits, reconstruction_usage)
        candidates = [
            c.model_dump(mode="json")
            for c in japanese_sources._jmdict_candidates(node, digest, None)
        ]
        raw = data[entry_start:end_offset]
        used = set(re.findall(rb"&([a-zA-Z][a-zA-Z0-9-]*);", raw))
        pos = []
        origin = None
        senses = []
        for ordinal, sense in enumerate(node.findall("sense"), 1):
            own = japanese_sources._texts(sense, "pos")
            if own:
                pos = list(own)
                origin = ordinal
            senses.append(
                {
                    "ordinal": ordinal,
                    "literal_pos": list(pos),
                    "pos_origin_sense_ordinal": origin,
                    "stagk": list(japanese_sources._texts(sense, "stagk")),
                    "stagr": list(japanese_sources._texts(sense, "stagr")),
                }
            )
        found[sequence] = {
            "raw_xml": raw.decode(),
            "raw_entry_sha256": _hash(raw),
            "expanded_byte_interval": [entry_start, end_offset],
            "start_line_1based": entry_line,
            "source_record_sha256": canonical_sha256(tostring(node, encoding="unicode")),
            "literal_tree": tree,
            "entities": {k: v for k, v in entities.items() if k.encode() in used},
            "dtd_attribute_declarations": defaults.copy(),
            "candidates": candidates,
            "sense_context": senses,
            "writing_context": [
                {
                    "ordinal": i,
                    "writing": x.findtext("keb"),
                    "ke_inf": list(japanese_sources._texts(x, "ke_inf")),
                    "ke_pri": list(japanese_sources._texts(x, "ke_pri")),
                }
                for i, x in enumerate(node.findall("k_ele"), 1)
            ],
            "reading_context": [
                {
                    "ordinal": i,
                    "reading": x.findtext("reb"),
                    "re_nokanji": x.find("re_nokanji") is not None,
                    "re_restr": list(japanese_sources._texts(x, "re_restr")),
                    "re_inf": list(japanese_sources._texts(x, "re_inf")),
                    "re_pri": list(japanese_sources._texts(x, "re_pri")),
                }
                for i, x in enumerate(node.findall("r_ele"), 1)
            ],
        }

    def forbidden(*args):
        raise ValueError("external/notation/processing instruction XML forbidden")

    def xml_declaration(version, encoding, standalone):
        if version != "1.0" or (
            encoding is not None and encoding.lower().replace("-", "") != "utf8"
        ):
            raise ValueError("unsupported XML version/encoding")

    parser.XmlDeclHandler = xml_declaration
    parser.StartDoctypeDeclHandler = doctype
    parser.EntityDeclHandler = entity
    parser.AttlistDeclHandler = attlist
    parser.ElementDeclHandler = element_decl
    parser.ExternalEntityRefHandler = forbidden
    parser.NotationDeclHandler = forbidden
    parser.ProcessingInstructionHandler = forbidden
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = characters
    parser.DefaultHandler = default
    try:
        parser.Parse(data, True)
    except expat.ExpatError as exc:
        raise ValueError("malformed JMdict XML") from exc
    if not seen_doctype:
        raise ValueError("internal JMdict DOCTYPE/DTD is required")
    if set(found) != wanted:
        raise ValueError("requested original entries missing")
    return found


def _lines(root, reference, maximum, limits):
    reference = safe._ref(reference)
    data = safe._read_bytes(safe._path(root, reference["path"]), reference["sha256"], limit=maximum)
    for number, line in enumerate(io.BytesIO(data), 1):
        if len(line) > limits["jsonl_line_bytes"]:
            raise ValueError("JSONL line byte limit exceeded")
        if line.strip():
            yield number, line, _json(line)


def _frequency(data, needed, comparison, all_index, limits):
    """Sort compact rank keys only. Full details retained for top-K/needed rows."""
    count = comparison.get("selected_count")
    if (
        type(count) is not int
        or not 1 <= count <= 30000
        or comparison.get("ranking_policy") != "count-desc-channels-desc-word-v1"
        or comparison.get("source_id")
        not in {"tubelex-ja-unidic310-base", "tubelex-ja-unidic310-lemma"}
    ):
        raise ValueError("unsupported frequency policy")

    def rows():
        reader = csv.DictReader(
            io.TextIOWrapper(io.BytesIO(data), encoding="utf-8"),
            delimiter="\t",
            quoting=csv.QUOTE_NONE,
        )
        cols = reader.fieldnames or []
        if not {"word", "count", "videos", "channels"} <= set(cols) or len(cols) != len(set(cols)):
            raise ValueError("invalid TUBELEX header")
        for r in reader:
            if None in r or any(v is None for v in r.values()):
                raise ValueError("malformed TUBELEX row")
            values = {}
            for k in cols:
                if k in {"count", "videos", "channels"} or k.startswith("count:"):
                    if not re.fullmatch("[0-9]{1,18}", r[k]):
                        raise ValueError("invalid TUBELEX count")
                    values[k] = int(r[k])
            yield r, values

    seen = set()
    keys = []
    total = None
    count_sum = max_video = max_channel = 0
    for r, n in rows():
        if total is not None:
            raise ValueError("trailing TUBELEX data")
        if r["word"] == "[TOTAL]":
            total = n
            continue
        word = r["word"]
        if (
            not word
            or len(word) > 512
            or word in seen
            or not 1 <= n["channels"] <= n["videos"] <= n["count"]
            or any(v > n["count"] for k, v in n.items() if k.startswith("count:"))
        ):
            raise ValueError("invalid or duplicate TUBELEX surface")
        seen.add(word)
        if len(seen) > limits["frequency_unique_surfaces"]:
            raise ValueError("frequency unique surface limit exceeded")
        keys.append((-n["count"], -n["channels"], word))
        count_sum += n["count"]
        max_video = max(max_video, n["videos"])
        max_channel = max(max_channel, n["channels"])
    if (
        total is None
        or total["count"] != count_sum
        or total["videos"] < max_video
        or total["channels"] < max_channel
        or comparison.get("source_entry_count") != len(keys)
    ):
        raise ValueError("TUBELEX totals/count mismatch")
    keys.sort()
    top = [word for _, _, word in keys[:count]]
    needed = set(needed) | set(top)
    ranks = {word: i for i, (_, _, word) in enumerate(keys, 1) if word in needed}
    del keys, seen
    details = {}
    for r, n in rows():
        if r["word"] not in needed:
            continue
        details[r["word"]] = {
            "word": r["word"],
            "count": n["count"],
            "videos": n["videos"],
            "channels": n["channels"],
            "majority_pos": r.get("pos") or None,
            "category_counts": {k[6:]: v for k, v in n.items() if k.startswith("count:")},
            "source_sha256": comparison["source_sha256"],
            "derived_surface_rank": ranks[r["word"]],
            "publisher_rank": None,
            "frequency_unit": "aggregate_literal_surface_not_sense",
        }
    links = {unicodedata.normalize("NFC", w): set() for w in top}
    for cid, c in all_index.items():
        for word in {c["lemma"], *c["own_readings"]}:
            if word in links:
                links[word].add(cid)
    expected = []
    actual = comparison.get("rows")
    if not isinstance(actual, list) or len(actual) != len(top):
        raise ValueError("frequency selection rows mismatch")
    for ordinal, (word, row) in enumerate(zip(top, actual, strict=True), 1):
        d = details[word]
        ids = sorted(links[unicodedata.normalize("NFC", word)])
        base = {
            k: d[k]
            for k in (
                "word",
                "count",
                "videos",
                "channels",
                "majority_pos",
                "category_counts",
                "source_sha256",
            )
        }
        if (
            any(row.get(k) != v for k, v in base.items())
            or type(row.get("source_rank")) is not int
            or row.get("source_rank") != ordinal
            or row.get("candidate_ids") != ids
            or row.get("decision") != "pending"
            or row.get("selected_candidate_id") is not None
        ):
            raise ValueError("frequency source/candidate association mismatch")
        expected.append({"form": word, "rank": ordinal, "candidate_ids": ids})
    seeds = {unicodedata.normalize("NFC", word).casefold() for word in top}
    return details, expected, seeds


def _fingerprint():
    modules = {
        "jmdict_context": __file__,
        "safe_reader": safe.__file__,
        "japanese_sources": japanese_sources.__file__,
        "vocabulary_sources": vocabulary_sources.__file__,
        "curation": vocabulary_curation.__file__,
        "vocabulary_review": vocabulary_review.__file__,
        "qualification_review": qualification_review.__file__,
        "artifact_writer": qualification_machine_runner.__file__,
        "lexical_identity": lexical_identity.__file__,
        "language_profiles": language_profiles.__file__,
        "sentence_curriculum": sentence_curriculum.__file__,
        "jobs": jobs.__file__,
    }
    return {
        "modules": {
            k: _hash(safe._read_bytes(Path(v), limit=16 * MIB)) for k, v in modules.items()
        },
        "python": platform.python_version(),
        "expat": expat.EXPAT_VERSION,
    }


def _reconstruct(root, specification, specification_sha256, limits):
    root = _plain_path(root)
    limits = _limits(limits)

    def read(r, limit=None):
        return safe._read(root, r, limits["metadata_file_bytes"] if limit is None else limit)

    spec = read({"path": str(specification), "sha256": specification_sha256})
    if (
        not isinstance(spec, dict)
        or set(spec) != REFS | {"schema_version", "request_indices"}
        or spec["schema_version"] != "jmdict-context-input-1"
    ):
        raise ValueError("unsupported JMdict context input contract")
    for k in REFS:
        safe._path(root, safe._ref(spec[k])["path"])
    prep = read(spec["source_preparation"])
    _manifest_check(prep)
    if prep.get("language") != "ja" or prep.get("dictionary_format") != "jmdict":
        raise ValueError("only Japanese JMdict preparations are supported")
    if prep["dictionary_sha256"] != spec["source"]["sha256"] or any(
        prep["files"].get(name) != spec[key]["sha256"]
        for name, key in [
            ("candidates.jsonl", "candidates"),
            ("sources.json", "source_catalog"),
            ("frequency-comparison.json", "frequency_comparison"),
        ]
    ):
        raise ValueError("source preparation binding drift")
    if (
        PurePosixPath(spec["candidates"]["path"]).parent
        != PurePosixPath(spec["source_preparation"]["path"]).parent
    ):
        raise ValueError("candidate preparation path mismatch")
    catalog = read(spec["source_catalog"])
    if prep.get("source_catalog_sha256") is not None and prep[
        "source_catalog_sha256"
    ] != canonical_sha256(catalog):
        raise ValueError("source catalog canonical binding drift")
    packet = read(spec["packet"])
    if (
        packet.get("schema_version") != "vocabulary-selection-packet-1"
        or packet.get("language") != "ja"
        or packet.get("generation_status") != "deferred_by_user"
        or packet.get("packet_sha256")
        != canonical_sha256({k: v for k, v in packet.items() if k != "packet_sha256"})
    ):
        raise ValueError("packet binding drift")
    manifest = read(spec["request_manifest"])
    if (
        set(manifest) != {"kind", "binding_sha256", "files", "production_eligible"}
        or manifest["kind"] != "vocabulary-session-request"
        or manifest["production_eligible"] is not False
        or set(manifest["files"]) != {"request.json", "messages.json", "response-schema.json"}
    ):
        raise ValueError("unsupported frozen request manifest")
    directory = PurePosixPath(spec["request_manifest"]["path"]).parent
    request_refs = {
        n: {"path": str(directory / n), "sha256": h} for n, h in manifest["files"].items()
    }
    request = read(request_refs["request.json"])
    messages = read(request_refs["messages.json"])
    schema = read(request_refs["response-schema.json"])
    if (
        request.get("schema_version") != "vocabulary-session-request-1"
        or canonical_sha256(request) != manifest["binding_sha256"]
        or request.get("packet_sha256") != spec["packet"]["sha256"]
        or request.get("language") != "ja"
        or request.get("generation_status") != "deferred_by_user"
    ):
        raise ValueError("request binding drift")
    source_indices = safe._indices(request["source_indices"], len(packet["groups"]), "packet")
    if (
        request["groups"] != [packet["groups"][i] for i in source_indices]
        or request["messages"] != messages
        or messages != selection_messages("ja", request["groups"])
        or request["response_schema"] != schema
        or schema != SelectionResponse.model_json_schema()
    ):
        raise ValueError("request group/messages/schema drift")
    selected = safe._indices(spec["request_indices"], len(request["groups"]), "request")
    if len(selected) > limits["selected_request_units"]:
        raise ValueError("selected unit limit exceeded")
    all_request_candidates = {
        s["candidate_id"] for group in request["groups"] for s in group["sense_candidates"]
    }
    targets = {}
    for i in selected:
        group = request["groups"][i]
        if not group.get("review_unit_id") or not group.get("sense_candidates"):
            raise ValueError("missing frozen review identity")
        for j, s in enumerate(group["sense_candidates"]):
            cid = s["candidate_id"]
            if cid in targets:
                raise ValueError("duplicate requested candidate")
            targets[cid] = (i, j, group, s)
    if not 1 <= len(targets) <= limits["selected_candidates"]:
        raise ValueError("selected candidate limit exceeded")
    all_index = {}
    candidates = {}
    for number, line, c in _lines(
        root, spec["candidates"], limits["candidates_jsonl_bytes"], limits
    ):
        cid = c["candidate_id"]
        if cid in all_index or c.get("language") != "ja":
            raise ValueError("ambiguous candidate inventory")
        item = {
            "candidate_sha256": canonical_sha256(c),
            "lemma": c["lemma"],
            "own_readings": [s["reading"] for s in c["sounds"]],
            "forms": [f["form"] for f in c["forms"]],
            "physical_line": number,
            "line_sha256": _hash(line.rstrip(b"\r\n")),
        }
        all_index[cid] = item
        if cid in targets:
            candidates[cid] = c
    if candidates.keys() != targets.keys():
        raise ValueError("requested candidate absent")
    wanted = set()
    for c in candidates.values():
        ids = c["source_sense_ids"]
        match = (
            re.fullmatch(r"jmdict:([0-9a-f]{64}):([0-9]{1,12}):sense:([1-9][0-9]*)", ids[0])
            if len(ids) == 1
            else None
        )
        if match is None or match[1] != spec["source"]["sha256"]:
            raise ValueError("unsupported exact JMdict sense locator")
        wanted.add(match[2])
    if len(wanted) > limits["selected_unique_entries"]:
        raise ValueError("selected entry limit exceeded")
    compressed = safe._read_bytes(
        safe._path(root, spec["source"]["path"]),
        spec["source"]["sha256"],
        limit=limits["compressed_dictionary_bytes"],
    )
    raw = _expand(compressed, "gzip", limits["expanded_dictionary_bytes"])
    del compressed
    expanded_hash = _hash(raw)
    expanded_size = len(raw)
    entries = _parse_jmdict(raw, wanted, spec["source"]["sha256"], limits)
    del raw
    reconstructed = {c["candidate_id"]: c for e in entries.values() for c in e["candidates"]}
    for cid, c in candidates.items():
        if reconstructed.get(cid) != c:
            raise ValueError("whole source candidate reconstruction mismatch")
        _, _, group, sense = targets[cid]
        if (
            group["lemma"] != c["lemma"]
            or group["pos"] != c["pos"]
            or any(sense.get(k) != c[k] for k in SENSE_KEYS)
        ):
            raise ValueError("packet/source candidate mismatch")
    comparison = read(spec["frequency_comparison"])
    if comparison.get("source_sha256") != spec["frequency_source"]["sha256"] or prep.get(
        "frequency"
    ) != {k: v for k, v in comparison.items() if k not in {"rows", "without_lexical_evidence"}}:
        raise ValueError("frequency preparation binding drift")
    needed = {
        v
        for c in reconstructed.values()
        for v in [c["lemma"], *[s["reading"] for s in c["sounds"]]]
    }
    compressed = safe._read_bytes(
        safe._path(root, spec["frequency_source"]["path"]),
        spec["frequency_source"]["sha256"],
        limit=limits["compressed_frequency_bytes"],
    )
    raw = _expand(compressed, "xz", limits["expanded_frequency_bytes"])
    del compressed
    frequency_expanded_hash = _hash(raw)
    frequencies, priority_rows, seeds = _frequency(raw, needed, comparison, all_index, limits)
    del raw
    if prep.get("candidate_filter") != {
        "policy": "nfc-casefold-selection-only-v1",
        "sha256": canonical_sha256(sorted(seeds)),
    }:
        raise ValueError("historical candidate filter mismatch")
    for cid, c in reconstructed.items():
        included = bool(
            {c["lemma"].casefold(), *[s["reading"].casefold() for s in c["sounds"]]} & seeds
        )
        if included != (cid in all_index) or (
            included and canonical_sha256(c) != all_index[cid]["candidate_sha256"]
        ):
            raise ValueError("full entry filtered candidate correspondence mismatch")
    priority = read(spec["surface_priority"])
    if priority.get("test_corpus_used") is True or priority.get("rows") != priority_rows:
        raise ValueError("surface priority linkage mismatch")
    group_provenance = _prepared_binding(
        root, spec, packet, targets, priority_rows, all_index, limits
    )
    output_rows = []
    for cid, (i, j, group, sense) in targets.items():
        c = candidates[cid]
        own = c["sounds"][0]
        sequence = own["entry_id"]
        entry = entries[sequence]
        ordinal = int(c["source_sense_ids"][0].rsplit(":", 1)[1])
        sc = entry["sense_context"][ordinal - 1]
        output_rows.append(
            {
                "candidate_id": cid,
                "candidate_sha256": all_index[cid]["candidate_sha256"],
                "source_record_sha256": c["source_record_sha256"],
                "source_sense_id": c["source_sense_ids"][0],
                "candidate_physical_line": all_index[cid]["physical_line"],
                "candidate_line_sha256": all_index[cid]["line_sha256"],
                "entry_id": group["entry_id"],
                "review_unit_id": group["review_unit_id"],
                "request_local_index": i,
                "packet_group_index": source_indices[i],
                "request_sense_index": j,
                "original_sense_ordinal": ordinal,
                "source_ent_seq": sequence,
                "own_identity": {
                    "writing": c["lemma"],
                    "writing_ordinal": next(
                        (
                            w["ordinal"]
                            for w in entry["writing_context"]
                            if w["writing"] == c["lemma"]
                        ),
                        None,
                    ),
                    "reading_ordinal": next(
                        r["ordinal"]
                        for r in entry["reading_context"]
                        if r["reading"] == own["reading"]
                    ),
                    "reading": own["reading"],
                    "mapped_pos": c["pos"],
                    "literal_pos": sc["literal_pos"],
                    "pos_origin_sense_ordinal": sc["pos_origin_sense_ordinal"],
                },
                "sense_restrictions": {"stagk": sc["stagk"], "stagr": sc["stagr"]},
                "permitted_pairs": c["forms"],
                "surface_frequency": {
                    "own_writing": frequencies.get(c["lemma"]),
                    "own_reading": frequencies.get(own["reading"]),
                    "historical_group_source_priority": group.get("source_priority"),
                    "group_priority_provenance": group_provenance[group["entry_id"]],
                    "final_frequency_rank": None,
                },
                "completeness": "supported_literal_context_preserved_linguistic_interpretation_pending",
            }
        )
    for entry in entries.values():
        entry["siblings"] = [
            {
                "candidate_id": c["candidate_id"],
                "candidate_sha256": canonical_sha256(c),
                "own_writing": c["lemma"],
                "own_reading": c["sounds"][0]["reading"],
                "mapped_pos": c["pos"],
                "source_sense_ids": c["source_sense_ids"],
                "present_in_frozen_candidates": c["candidate_id"] in all_index,
                "present_in_request": c["candidate_id"] in all_request_candidates,
                "included_in_context_targets": c["candidate_id"] in targets,
                "surface_provenance": {
                    "writing": frequencies.get(c["lemma"]),
                    "reading": frequencies.get(c["sounds"][0]["reading"]),
                },
                "selection_authority": "none",
            }
            for c in entry.pop("candidates")
        ]
        entry["uninterpreted_semantics"] = POLICY["uninterpreted_semantics"]
        entry["unhandled_xml_fields"] = []
    doc = {
        "schema_version": KIND,
        "status": "context_available_for_review_only",
        "generation_status": "deferred_by_user",
        "production_eligible": False,
        "language": "ja",
        "policy_sha256": canonical_sha256(POLICY),
        "implementation": _fingerprint(),
        "effective_limits": limits,
        "specification": {"path": str(specification), "sha256": specification_sha256},
        "inputs": spec,
        "request_files": request_refs,
        "request_binding_sha256": manifest["binding_sha256"],
        "source_expanded_sha256": expanded_hash,
        "source_expanded_bytes": expanded_size,
        "frequency_expanded_sha256": frequency_expanded_hash,
        "entries": entries,
        "senses": output_rows,
    }
    files = {"context.json": json_bytes(doc), "policy.json": json_bytes(POLICY)}
    if sum(map(len, files.values())) > limits["output_total_bytes"]:
        raise ValueError("context output byte limit exceeded; no truncation")
    return doc, files


def _prepared_binding(root, spec, packet, targets, priority_rows, index, limits):
    def read(key, maximum):
        return safe._read(root, spec[key], maximum)

    manifest = read("prepared_manifest", limits["metadata_file_bytes"])
    if (
        packet.get("source_manifest_sha256") != spec["prepared_manifest"]["sha256"]
        or packet.get("source_vocabulary_sha256") != spec["prepared_vocabulary"]["sha256"]
        or any(
            manifest["files"].get("ja/" + name) != spec[key]["sha256"]
            for name, key in [
                ("vocabulary.json", "prepared_vocabulary"),
                ("forms.jsonl", "prepared_forms"),
            ]
        )
    ):
        raise ValueError("prepared manifest binding drift")
    parent = PurePosixPath(spec["prepared_manifest"]["path"]).parent
    if any(
        PurePosixPath(spec[key]["path"]) != parent / "ja" / name
        for key, name in [
            ("prepared_vocabulary", "vocabulary.json"),
            ("prepared_forms", "forms.jsonl"),
        ]
    ):
        raise ValueError("prepared path mismatch")
    vocabulary = read("prepared_vocabulary", limits["prepared_vocabulary_bytes"])
    if (
        vocabulary.get("schema_version") != "deck-vocabulary-preparation-1"
        or vocabulary.get("language") != "ja"
        or vocabulary["ordering"]["policy"]
        != "lowest_attested_surface_priority_then_exact_lemma_pos"
    ):
        raise ValueError("unsupported prepared vocabulary")

    def contains(rows, reference):
        return any({k: r.get(k) for k in ("path", "sha256")} == reference for r in rows)

    if (
        not contains(vocabulary["sources"], spec["candidates"])
        or any(
            not contains(vocabulary["evidence"], spec[k])
            for k in ("source_preparation", "source_catalog", "frequency_comparison")
        )
        or {k: vocabulary["ordering"]["source"].get(k) for k in ("path", "sha256")}
        != spec["surface_priority"]
    ):
        raise ValueError("prepared source/priority evidence drift")
    wanted = {g["entry_id"] for _, _, g, _ in targets.values()}
    all_ids = [e["entry_id"] for e in vocabulary["entries"]]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("duplicate prepared group")
    entries = {e["entry_id"]: e for e in vocabulary["entries"] if e["entry_id"] in wanted}
    del vocabulary, all_ids
    if entries.keys() != wanted:
        raise ValueError("prepared group missing")
    ranks = {
        unicodedata.normalize("NFC", r["form"]).casefold(): r["rank"]
        for r in reversed(priority_rows)
    }
    candidate_ranks = {}
    for row in priority_rows:
        for cid in row["candidate_ids"]:
            candidate_ranks[cid] = min(row["rank"], candidate_ranks.get(cid, row["rank"]))
    forms = {eid: [] for eid in entries}
    for _, _, form in _lines(root, spec["prepared_forms"], limits["prepared_forms_bytes"], limits):
        rank = ranks.get(unicodedata.normalize("NFC", form["form"]).casefold())
        if rank is not None:
            for parent_id in form["parent_entry_ids"]:
                if parent_id in forms:
                    forms[parent_id].append({**form, "priority": rank})
    fragments = {}
    group_provenance = {}
    for eid, entry in entries.items():
        possible = []
        contributors = []
        for s in entry["sense_candidates"]:
            cid = s["candidate_id"]
            if cid not in index:
                raise ValueError("prepared source candidate missing")
            c = index[cid]
            for row in priority_rows:
                if cid in row["candidate_ids"]:
                    contributors.append(
                        {
                            "kind": "candidate_id_link",
                            "candidate_id": cid,
                            "surface": row["form"],
                            "rank": row["rank"],
                        }
                    )
            for kind, values in [
                ("lemma_surface", [c["lemma"]]),
                ("related_form_surface", c["forms"]),
            ]:
                for value in values:
                    rank = ranks.get(unicodedata.normalize("NFC", value).casefold())
                    if rank is not None:
                        contributors.append(
                            {"kind": kind, "candidate_id": cid, "surface": value, "rank": rank}
                        )
            possible.extend(
                [
                    candidate_ranks.get(cid),
                    ranks.get(unicodedata.normalize("NFC", c["lemma"]).casefold()),
                ]
            )
            possible.extend(
                ranks.get(unicodedata.normalize("NFC", f).casefold()) for f in c["forms"]
            )
        expected = min((r for r in possible if r is not None), default=None)
        if (
            type(entry.get("source_priority")) is not type(expected)
            or entry.get("source_priority") != expected
        ):
            raise ValueError("historical group priority mismatch")
        group_provenance[eid] = {
            "policy": "lowest_attested_surface_priority_then_exact_lemma_pos",
            "minimum": expected,
            "contributors": contributors,
            "frequency_unit": "historical_surface_priority_not_sense",
        }
        attached = sorted(forms[eid], key=lambda f: (f["priority"], f["form"], f["form_id"]))
        for group in split_review_group({**entry, "forms_for_review": attached}):
            fragments[group["review_unit_id"]] = group
    for _, _, group, _ in targets.values():
        if fragments.get(group["review_unit_id"]) != group:
            raise ValueError("prepared packet fragment mismatch")
    return group_provenance


def create_jmdict_context_supplement(
    *,
    root: Path,
    specification: Path,
    specification_sha256: str,
    output: Path,
    limits: dict | None = None,
):
    output = _plain_path(output)
    if output.exists():
        raise ValueError("supplement output already exists")
    document, files = _reconstruct(root, specification, specification_sha256, limits)
    manifest = persist_artifact(output, kind=KIND, binding=canonical_sha256(document), files=files)
    return {
        "status": "context_available_for_review_only",
        "sense_count": len(document["senses"]),
        "manifest_sha256": _hash(json_bytes(manifest)),
        "policy_sha256": canonical_sha256(POLICY),
    }


def validate_jmdict_context_supplement(
    *,
    root: Path,
    specification: Path,
    specification_sha256: str,
    supplement: Path,
    manifest_sha256: str,
    limits: dict | None = None,
):
    supplement = _plain_path(supplement)
    effective = _limits(limits)
    manifest = _json(
        safe._read_bytes(
            supplement / "manifest.json", manifest_sha256, limit=effective["metadata_file_bytes"]
        )
    )
    if {p.name for p in supplement.iterdir()} != {"manifest.json", "context.json", "policy.json"}:
        raise ValueError("supplement inventory drift")
    document, files = _reconstruct(root, specification, specification_sha256, limits)
    expected = {
        "kind": KIND,
        "binding_sha256": canonical_sha256(document),
        "files": {k: _hash(v) for k, v in sorted(files.items())},
        "production_eligible": False,
    }
    if manifest != expected:
        raise ValueError("supplement source/policy/content binding drift")
    for name, data in files.items():
        if (
            safe._read_bytes(
                supplement / name, manifest["files"][name], limit=effective["output_total_bytes"]
            )
            != data
        ):
            raise ValueError("literal context mismatch")
    return {
        "status": "context_available_for_review_only",
        "sense_count": len(document["senses"]),
        "manifest_sha256": manifest_sha256,
        "policy_sha256": canonical_sha256(POLICY),
    }
