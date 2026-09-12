"""Exact Croatian OMW -> Princeton WordNet 3.0 evidence joins, with no extraction."""

from __future__ import annotations

import gzip
import hashlib
import io
import re
import tarfile
import unicodedata
from pathlib import Path

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.vocabulary_sources import (
    LexicalSenseCandidate,
    SourceLimits,
    _verified_lines,
)


class _ExpandedReader:
    def __init__(self, stream, limit):
        self.stream, self.remaining = stream, limit

    def read(self, size=-1):
        # This sits below tarfile, which consumes GNU/PAX metadata before
        # yielding members. Header and metadata bytes count towards the cap.
        size = self.remaining + 1 if size < 0 else min(size, self.remaining + 1)
        data = self.stream.read(min(size, 1024**2))
        self.remaining -= len(data)
        if self.remaining < 0:
            raise ValueError("WordNet expanded byte limit exceeded")
        return data


def _wordnet_glosses(path: Path, expected_sha256: str, *, max_expanded_bytes=256 * 1024**2) -> dict:
    path = Path(path).absolute()
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError("WordNet source cannot contain symlinks")
    if not path.is_file() or path.stat().st_size > 64 * 1024**2:
        raise ValueError("WordNet source is missing or exceeds 64 MiB")
    with path.open("rb") as handle:
        content = handle.read(64 * 1024**2 + 1)
    if len(content) > 64 * 1024**2 or hashlib.sha256(content).hexdigest() != expected_sha256:
        raise ValueError("WordNet source checksum or byte limit mismatch")
    selected = {f"WordNet-3.0/dict/data.{name}" for name in ["noun", "verb", "adj", "adv"]}
    glosses = {}
    expanded = count = 0
    # Read tar members through a stream; never materialize paths from the archive.
    with (
        gzip.GzipFile(fileobj=io.BytesIO(content)) as compressed,
        tarfile.open(fileobj=_ExpandedReader(compressed, max_expanded_bytes), mode="r|") as archive,
    ):
        for member in archive:
            count += 1
            expanded += member.size
            if count > 10000 or expanded > 256 * 1024**2:
                raise ValueError("WordNet archive exceeds expanded bounds")
            if member.name not in selected:
                continue
            if not member.isfile() or member.size > 64 * 1024**2:
                raise ValueError("WordNet gloss data must be a bounded regular member")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("WordNet gloss member missing")
            with stream:
                while raw := stream.readline(128000):
                    if len(raw) >= 128000:
                        raise ValueError("WordNet gloss line exceeds bounds")
                    line = raw.decode("utf-8").rstrip("\r\n")
                    if not line or not line[0].isdigit():
                        continue
                    fields, separator, gloss = line.partition(" | ")
                    parts = fields.split()
                    if (
                        not separator
                        or len(parts) < 3
                        or not re.fullmatch(r"[0-9]{8}", parts[0])
                        or parts[2] not in {"n", "v", "a", "s", "r"}
                        or not gloss.strip()
                    ):
                        raise ValueError("malformed Princeton WordNet 3.0 gloss")
                    key = parts[0] + "-" + ("a" if parts[2] == "s" else parts[2])
                    if key in glosses:
                        raise ValueError("duplicate WordNet synset")
                    glosses[key] = (gloss.strip(), hashlib.sha256(raw).hexdigest())
                    if len(glosses) > 200000:
                        raise ValueError("WordNet synset limit exceeded")
    if not glosses:
        raise ValueError("WordNet archive has no recognized gloss data")
    return glosses


def read_croatian_wordnet(
    path: Path,
    *,
    expected_sha256: str,
    glosses: Path,
    glosses_sha256: str,
    limits: SourceLimits | None = None,
    lemmas: set[str] | None = None,
):
    limits = limits or SourceLimits()
    definitions = _wordnet_glosses(
        glosses, glosses_sha256, max_expanded_bytes=min(limits.max_expanded_bytes, 256 * 1024**2)
    )
    filters = (
        {unicodedata.normalize("NFC", word).casefold() for word in lemmas}
        if lemmas is not None
        else None
    )
    for line in _verified_lines(path, expected_sha256, limits or SourceLimits()):
        if not line.strip() or line.startswith("#"):
            continue
        row = line.rstrip("\r\n").split("\t")
        if len(row) != 3 or not re.fullmatch(r"[0-9]{8}-[nvar]", row[0]):
            raise ValueError("malformed Croatian OMW row")
        if row[1] != "hrv:lemma":
            continue
        word = unicodedata.normalize("NFC", row[2])
        if filters is not None and word.casefold() not in filters:
            continue
        if row[0] not in definitions:
            raise ValueError("Croatian source synset has no exact WordNet 3.0 gloss")
        definition, gloss_record_sha256 = definitions[row[0]]
        digest = canonical_sha256(
            {
                "omw_sha256": expected_sha256,
                "row": row,
                "glosses_sha256": glosses_sha256,
                "gloss_record_sha256": gloss_record_sha256,
            }
        )
        yield LexicalSenseCandidate(
            language="hr",
            lemma=word,
            pos={"n": "NOUN", "v": "VERB", "a": "ADJ", "r": "ADV"}[row[0][-1]],
            candidate_id="candidate:" + digest,
            source_record_sha256=digest,
            source_sense_ids=("pwn30:" + row[0],),
            glosses=(definition,),
        )
