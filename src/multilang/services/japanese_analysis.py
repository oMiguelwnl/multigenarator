"""Shared, local Japanese morphology with exact spans and explicit dictionary.

Set MULTILANG_JAPANESE_DICTIONARY=unidic for the full installed distribution,
or MULTILANG_JAPANESE_DICTIONARY_PATH for a separately acquired UniDic. The
default is explicitly unidic-lite. No implicit downloads or fallback dictionaries.
Morphological readings are evidence, not semantic-sense adjudication.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import os
import re
import threading
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from multilang.services.japanese_pos import unidic_to_upos

_LOCAL = threading.local()
_DICTIONARY_FILES = ("sys.dic", "unk.dic", "char.bin", "matrix.bin", "dicrc")


class JapaneseAnalysisError(ValueError):
    """A content-free diagnostic suitable for private highlight processing."""


def katakana_to_hiragana(value: str) -> str:
    return "".join(chr(ord(c) - 0x60) if 0x30A1 <= ord(c) <= 0x30F6 else c for c in value)


def validate_japanese_reading(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    if not 1 <= len(value) <= 512 or not re.fullmatch(r"[ぁ-ゖァ-ヶー]+", value):
        raise JapaneseAnalysisError("Japanese reading must contain kana only")
    return katakana_to_hiragana(value)


def candidate_japanese_reading(candidate) -> str | None:
    """Use explicitly recorded source readings, never generic spoken text."""
    provenance = getattr(candidate, "provenance", None)
    notes = provenance.get("notes", ()) if isinstance(provenance, Mapping) else getattr(provenance, "notes", ())
    readings = {note.partition("=")[2] for note in notes if note.startswith("japanese_reading=")}
    if not readings:
        return None
    if len(readings) != 1:
        raise JapaneseAnalysisError("conflicting Japanese source readings")
    reading = validate_japanese_reading(readings.pop())
    if getattr(candidate, "spoken_form", None) != reading:
        raise JapaneseAnalysisError("Japanese source reading drift")
    return reading


def japanese_dictionary_path() -> Path:
    configured = os.environ.get("MULTILANG_JAPANESE_DICTIONARY_PATH")
    if configured:
        path = Path(configured).absolute()
    else:
        package = os.environ.get("MULTILANG_JAPANESE_DICTIONARY", "unidic-lite")
        if package not in {"unidic", "unidic-lite"}:
            raise JapaneseAnalysisError("unsupported Japanese dictionary selection")
        try:
            module = importlib.import_module(package.replace("-", "_"))
            path = Path(module.DICDIR).absolute()
        except (ImportError, AttributeError) as exc:
            raise JapaneseAnalysisError("selected Japanese dictionary is unavailable") from exc
    if any(c in str(path) for c in ('"', "\n", "\r", "\x00")):
        raise JapaneseAnalysisError("invalid Japanese dictionary path")
    if not all((path / name).is_file() and not (path / name).is_symlink() for name in _DICTIONARY_FILES):
        raise JapaneseAnalysisError("selected Japanese dictionary is incomplete")
    return path


@lru_cache(maxsize=8)
def _dictionary_digest(path: str, stats: tuple) -> str:
    digest = hashlib.sha256()
    for name in _DICTIONARY_FILES:
        digest.update(name.encode())
        with (Path(path) / name).open("rb") as handle:
            digest.update(hashlib.file_digest(handle, "sha256").digest())
    return digest.hexdigest()


def japanese_dictionary_identity() -> dict:
    path = japanese_dictionary_path()
    stats = tuple((p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns)
                  for p in (path / name for name in _DICTIONARY_FILES))
    package = ("configured-unidic" if os.environ.get("MULTILANG_JAPANESE_DICTIONARY_PATH")
               else os.environ.get("MULTILANG_JAPANESE_DICTIONARY", "unidic-lite"))
    version = "external"
    if package != "configured-unidic":
        version = importlib.metadata.version(package)
    return {"model_package": package, "model_package_version": version,
            "model_artifact_sha256": _dictionary_digest(str(path), stats)}


def japanese_mecab_arguments() -> str:
    return f'-r "{os.devnull}" -d "{japanese_dictionary_path()}"'


def japanese_tagger():
    from fugashi import Tagger

    try:
        identity = japanese_dictionary_identity()["model_artifact_sha256"]
        if getattr(_LOCAL, "identity", None) != identity:
            _LOCAL.tagger = Tagger(japanese_mecab_arguments())
            _LOCAL.identity = identity
        return _LOCAL.tagger
    except (OSError, RuntimeError, ImportError) as exc:
        raise JapaneseAnalysisError("Japanese analyzer unavailable") from exc


@dataclass(frozen=True, slots=True)
class JapaneseToken:
    surface: str
    start: int
    end: int
    lemma: str
    orthographic_base: str
    reading: str
    lemma_reading: str
    pronunciation: str
    pos: str
    known: bool


def analyze_japanese(text: str) -> tuple[JapaneseToken, ...]:
    if len(text) > 64000 or unicodedata.normalize("NFC", text) != text:
        raise JapaneseAnalysisError("Japanese input must be bounded NFC text")
    result = []
    position = 0
    try:
        nodes = japanese_tagger()(text)
        for node in nodes:
            whitespace = node.white_space
            if (not isinstance(whitespace, str) or whitespace.strip()
                    or text[position:position + len(whitespace)] != whitespace):
                raise JapaneseAnalysisError("Japanese whitespace alignment failed")
            position += len(whitespace)
            surface = str(node.surface)
            end = position + len(surface)
            if text[position:end] != surface:
                raise JapaneseAnalysisError("Japanese token alignment failed")
            feature = node.feature

            def value(name):
                candidate = getattr(feature, name, "") or ""
                return "" if candidate == "*" else str(candidate)

            pos = unidic_to_upos(value("pos1"), value("pos2"), value("lemma"))
            result.append(JapaneseToken(
                surface=surface, start=position, end=end, lemma=value("lemma"),
                orthographic_base=value("orthBase") or value("lemma"),
                reading=katakana_to_hiragana(value("kana") or value("pron")),
                lemma_reading=katakana_to_hiragana(value("kanaBase") or value("lForm")),
                pronunciation=katakana_to_hiragana(value("pron")), pos=pos,
                known=not node.is_unk and pos != "X" and bool(value("lemma")),
            ))
            position = end
            if len(result) > 4096:
                raise JapaneseAnalysisError("Japanese token limit exceeded")
        if text[position:].strip():
            raise JapaneseAnalysisError("Japanese trailing source alignment failed")
    except JapaneseAnalysisError:
        raise
    except Exception as exc:
        raise JapaneseAnalysisError("Japanese analysis failed") from exc
    return tuple(result)


def japanese_target_spans(
    sentence: str, target: str, *, reading: str | None = None, pos: str | None = None
) -> tuple[tuple[int, int], ...]:
    """Match a whole lexical token sequence, including supported conjugation.

    Without a reviewed reading/POS this only proves lexical morphology, never
    a semantic sense. Unavailable/unknown target analysis returns no evidence.
    """
    try:
        expected, observed = analyze_japanese(target), analyze_japanese(sentence)
    except JapaneseAnalysisError:
        return ()
    if not expected or not all(t.known for t in expected):
        return ()
    spans = []
    for index in range(len(observed) - len(expected) + 1):
        window = observed[index:index + len(expected)]
        if not all(actual.known and actual.pos == wanted.pos
                   and actual.lemma == wanted.lemma for actual, wanted in zip(window, expected)):
            continue
        if pos and len(window) == 1 and window[0].pos != pos:
            continue
        if reading and katakana_to_hiragana(reading) != "".join(t.lemma_reading for t in window):
            continue
        spans.append((window[0].start, window[-1].end))
    return tuple(spans)
