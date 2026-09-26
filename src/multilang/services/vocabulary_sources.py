"""Bounded readers for real lexical evidence and annotated evaluation corpora.

Dictionary sense candidates and treebank labels are never production approval.
Files are verified locally; these parsers neither fetch URLs nor execute content.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import lzma
import os
import re
import stat
import unicodedata
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from pydantic import Field

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.language_profiles import NativeContract
from multilang.domain.lexical_identity import canonical_sha256


class SourceLimits(NativeContract):
    max_bytes: int = Field(default=512 * 1024**2, ge=1, le=64 * 1024**3)
    max_expanded_bytes: int = Field(default=1024**3, ge=1, le=64 * 1024**3)
    max_line_bytes: int = Field(default=2 * 1024**2, ge=1, le=16 * 1024**2)
    max_records: int = Field(default=2_000_000, ge=1, le=50_000_000)
    max_tokens_per_sentence: int = Field(default=4096, ge=1, le=16384)
    max_output_bytes: int = Field(default=128 * 1024**2, ge=1, le=4 * 1024**3)
    max_unique_entries: int = Field(default=100000, ge=1, le=1000000)


class CorpusToken(NativeContract):
    index: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=4096)
    lemma: str | None = None
    pos: str | None = None
    features: dict[str, str] = Field(default_factory=dict)
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=1)
    sense_id: str | None = None
    misc: str = Field(default="_", max_length=64000)


class CorpusSentence(NativeContract):
    language: SupportedLanguage
    document_id: str
    sentence_id: str
    text: str = Field(min_length=1, max_length=64000)
    tokens: tuple[CorpusToken, ...]
    source_sha256: str


class LexicalSenseCandidate(NativeContract):
    language: SupportedLanguage
    lemma: str = Field(min_length=1, max_length=512)
    pos: str
    candidate_id: str
    source_record_sha256: str
    source_sense_ids: tuple[str, ...] = ()
    stable_sense_id: str | None = None
    glosses: tuple[str, ...]
    examples: tuple[str, ...] = ()
    form_of: tuple[str, ...] = ()
    forms: tuple[dict, ...] = ()
    sounds: tuple[dict, ...] = ()
    tags: tuple[str, ...] = ()
    kind: Literal["lexeme", "inflection"] = "lexeme"
    review_status: Literal["pending"] = "pending"


_POS = {
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
    "conj": "CCONJ",
    "num": "NUM",
    "intj": "INTJ",
    "particle": "PART",
    "punct": "PUNCT",
    "symbol": "SYM",
}


def _modern_language(language: str) -> SupportedLanguage:
    code = SupportedLanguage(language)
    if code is SupportedLanguage.LA:
        raise ValueError("Classical Latin requires its isolated source pipeline")
    return code


def _verified_lines(
    path: Path, expected_sha256: str, limits: SourceLimits, *, max_lines: int | None = None
) -> Iterator[str]:
    path = Path(path).absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("source symlink is not permitted")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("source checksum must be a SHA-256")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as raw:
        before = os.fstat(raw.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("source must be a regular file")
        if before.st_size > limits.max_bytes:
            raise ValueError("source byte limit exceeded")
        digest = hashlib.file_digest(raw, "sha256").hexdigest()
        if digest != expected_sha256:
            raise ValueError("source checksum mismatch")
        raw.seek(0)
        stream = (gzip.GzipFile(fileobj=raw) if path.suffix == ".gz"
                  else lzma.LZMAFile(raw) if path.suffix == ".xz" else raw)
        expanded = lines = 0
        try:
            while data := stream.readline(limits.max_line_bytes + 1):
                lines += 1
                expanded += len(data)
                if len(data) > limits.max_line_bytes:
                    raise ValueError("source line byte limit exceeded")
                if expanded > limits.max_expanded_bytes:
                    raise ValueError("expanded source byte limit exceeded")
                if lines > (max_lines if max_lines is not None else limits.max_records):
                    raise ValueError("source record limit exceeded")
                yield data.decode("utf-8")
            after = os.fstat(raw.fileno())
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                raise ValueError("source changed during ingestion")
        finally:
            if stream is not raw:
                stream.close()


def _attributes(value: str) -> dict[str, str]:
    if value == "_":
        return {}
    pairs = value.split("|")
    if any("=" not in pair for pair in pairs):
        raise ValueError("malformed CoNLL-U attributes")
    result = dict(pair.split("=", 1) for pair in pairs)
    if len(result) != len(pairs):
        raise ValueError("duplicate CoNLL-U attribute")
    return result


def _spacing(value: str) -> dict[str, str]:
    # Unlike FEATS, MISC is free-form, can contain flags and repeated CxnElt
    # values. Retain it on the token; only consume its exact spacing directive.
    values = [part.partition("=")[2] for part in value.split("|") if part.startswith("SpaceAfter=")]
    if len(values) > 1 or (values and values[0] not in {"No", "Yes"}):
        raise ValueError("conflicting CoNLL-U spacing annotation")
    return {"SpaceAfter": values[0]} if values else {}


def _sentence(rows, metadata, *, language, document_id, sequence, digest, limits):
    surfaces = []
    covered: set[int] = set()
    lexical = []
    for fields in rows:
        index = fields[0]
        if "." in index:
            continue  # UD empty nodes do not occupy observed character spans.
        if "-" in index:
            start, end = map(int, index.split("-"))
            if (
                start >= end
                or end > limits.max_tokens_per_sentence
                or start != len(lexical) + 1
                or start in covered
            ):
                raise ValueError("invalid CoNLL-U multiword range")
            covered.update(range(start, end + 1))
            surfaces.append((None, fields[1], _spacing(fields[9])))
        else:
            number = int(index)
            if number != len(lexical) + 1 or number > limits.max_tokens_per_sentence:
                raise ValueError("invalid or duplicate CoNLL-U token ID")
            lexical.append(fields)
            if number not in covered:
                surfaces.append((number, fields[1], _spacing(fields[9])))
    if len(lexical) > limits.max_tokens_per_sentence:
        raise ValueError("sentence token limit exceeded")
    if not covered.issubset(range(1, len(lexical) + 1)):
        raise ValueError("CoNLL-U multiword range has missing members")
    text = metadata.get("text")
    if text is None:
        text = "".join(
            surface + ("" if misc.get("SpaceAfter") == "No" else " ")
            for _, surface, misc in surfaces
        ).rstrip()
    spans = {}
    cursor = 0
    for index, surface, _ in surfaces:
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if not text.startswith(surface, cursor):
            raise ValueError("CoNLL-U text does not align with its source tokens")
        if index is not None:
            spans[index] = (cursor, cursor + len(surface))
        cursor += len(surface)
    if text[cursor:].strip():
        raise ValueError("CoNLL-U text has unmatched trailing characters")
    tokens = tuple(
        CorpusToken(
            index=int(row[0]),
            text=row[1],
            lemma=None if row[2] == "_" else row[2],
            pos=None if row[3] == "_" else row[3],
            features=_attributes(row[5]),
            misc=row[9],
            start=spans.get(int(row[0]), (None, None))[0],
            end=spans.get(int(row[0]), (None, None))[1],
        )
        for row in lexical
    )
    return CorpusSentence(
        language=language,
        document_id=document_id,
        sentence_id=metadata.get("sent_id", f"sentence-{sequence}"),
        text=text,
        tokens=tokens,
        source_sha256=digest,
    )


def read_conllu(
    path: Path, *, language: str, expected_sha256: str, limits: SourceLimits | None = None
) -> Iterator[CorpusSentence]:
    limits = limits or SourceLimits()
    code = _modern_language(language)
    rows, metadata = [], {}
    document_id, sequence = f"source-{expected_sha256}", 0
    declared_document = None
    for line in _verified_lines(path, expected_sha256, limits):
        line = line.rstrip("\r\n")
        if line.startswith("#"):
            key, separator, value = line[1:].strip().partition(" = ")
            if separator:
                if key in {"newdoc id", "newdoc_id"}:
                    if declared_document is not None and declared_document != value:
                        raise ValueError("conflicting CoNLL-U document headers")
                    declared_document = value
                    document_id = value
                else:
                    metadata[key] = value
        elif line:
            fields = line.split("\t")
            if len(fields) != 10:
                raise ValueError("CoNLL-U requires ten columns")
            if not re.fullmatch(
                r"(?:[1-9][0-9]*(?:-[1-9][0-9]*)?|(?:0|[1-9][0-9]*)\.[1-9][0-9]*)", fields[0]
            ):
                raise ValueError("malformed CoNLL-U token ID")
            rows.append(fields)
            if len(rows) > limits.max_tokens_per_sentence * 2:
                raise ValueError("sentence token limit exceeded")
        elif rows:
            sequence += 1
            yield _sentence(
                rows,
                metadata,
                language=code,
                document_id=document_id,
                sequence=sequence,
                digest=expected_sha256,
                limits=limits,
            )
            rows, metadata = [], {}
            declared_document = None
    if rows:
        yield _sentence(
            rows,
            metadata,
            language=code,
            document_id=document_id,
            sequence=sequence + 1,
            digest=expected_sha256,
            limits=limits,
        )


def read_wiktextract(
    path: Path,
    *,
    language: str,
    expected_sha256: str,
    lemmas: set[str] | None = None,
    limits: SourceLimits | None = None,
) -> Iterator[LexicalSenseCandidate]:
    """Read the documented English-edition schema without language alias guessing.

    Candidate hashes identify exact source evidence, not stable semantic senses.
    Explicit review maps them to stable senses before production import.
    """
    _modern_language(language)
    lemma_filter = (
        {unicodedata.normalize("NFC", word).casefold() for word in lemmas}
        if lemmas is not None
        else None
    )
    for line in _verified_lines(path, expected_sha256, limits or SourceLimits()):
        if not line.strip():
            continue
        for _, candidate in wiktextract_record_candidates(
            json.loads(line), language=language, lemma_filter=lemma_filter
        ):
            yield candidate


def wiktextract_record_candidates(
    record: dict, *, language: str, lemma_filter: set[str] | None = None
) -> Iterator[tuple[int, LexicalSenseCandidate]]:
    """Parse one original record, retaining its exact sense indexes and legacy hashes.

    Callers must verify and bound the source bytes before invoking this parser.
    The optional lemma filter must already be NFC and casefolded.
    This is shared by preparation and additive original-dictionary evidence recovery.
    """
    code = _modern_language(language)
    if not isinstance(record, dict):
        raise ValueError("dictionary JSONL records must be objects")
    if record.get("lang_code") != language:
        return
    word = record.get("word")
    if not isinstance(word, str) or not word.strip():
        raise ValueError("dictionary record has no lexical word")
    word = unicodedata.normalize("NFC", word)
    if lemma_filter is not None and word.casefold() not in lemma_filter:
        return
    if len(word) > 512:
        raise ValueError("dictionary word exceeds lexical limit")
    record_hash = canonical_sha256(record)
    senses = record.get("senses", [])
    if not isinstance(senses, list) or len(senses) > 4096:
        raise ValueError("dictionary sense list invalid or exceeds limit")
    for index, sense in enumerate(senses):
        if not isinstance(sense, dict):
            raise ValueError("dictionary sense must be an object")
        glosses = _strings(sense.get("glosses", ()))
        if not glosses or any(not isinstance(g, str) or len(g) > 16000 for g in glosses):
            continue
        forms_of = tuple(
            item["word"]
            for item in sense.get("form_of", ())
            if isinstance(item, dict) and isinstance(item.get("word"), str)
        )
        examples = tuple(
            item["text"]
            for item in sense.get("examples", ())
            if isinstance(item, dict)
            and isinstance(item.get("text"), str)
            and len(item["text"]) <= 64000
        )
        yield (
            index,
            LexicalSenseCandidate(
                language=code,
                lemma=word,
                pos=_POS.get(record.get("pos"), "X"),
                candidate_id="candidate:"
                + canonical_sha256({"record": record_hash, "sense": index}),
                source_record_sha256=record_hash,
                source_sense_ids=_strings(sense.get("senseid", ()), allow_scalar=True),
                glosses=glosses,
                examples=examples,
                form_of=forms_of,
                forms=tuple(item for item in record.get("forms", ()) if isinstance(item, dict)),
                sounds=tuple(item for item in record.get("sounds", ()) if isinstance(item, dict)),
                tags=tuple(
                    dict.fromkeys(
                        (*_strings(record.get("tags", ())), *_strings(sense.get("tags", ())))
                    )
                ),
                kind="inflection" if forms_of else "lexeme",
            ),
        )


def _strings(value, *, allow_scalar=False) -> tuple[str, ...]:
    if allow_scalar and isinstance(value, str):
        return (value,)
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
        raise ValueError("dictionary string list has an invalid shape")
    return tuple(value)
