"""Local, source-bound evidence for Mandarin review; never production approval.

CC-CEDICT supplies readings and spelling pairs, not reliable structured POS.
Wiktextract supplies POS/sense candidates; Chinese also includes other varieties.
Conversions expand lookup only and must never silently merge lexical identities.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

from opencc import OpenCC
from pypinyin.contrib.tone_convert import to_tone

from multilang.domain.lexical_identity import canonical_sha256
from multilang.services.mandarin_orthography import (
    MandarinOrthography,
    MandarinOrthographyError,
    derive_mandarin_orthography,
    render_mandarin_sentence,
    script_counts,
    validate_simplified_mandarin,
)
from multilang.services.vocabulary_sources import _POS, SourceLimits, _verified_lines

_CEDICT_V1 = re.compile(r"([^\s]+) ([^\s]+) \[([^\[\]\r\n]+)\] /(.+)/")
_NUMBERED = re.compile(r"([a-zü:]+)([1-5])", re.IGNORECASE)
_MARKED = re.compile(r"[a-züāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜńňǹḿêếề]+")
_OTHER_VARIETIES = {
    "Cantonese", "Hakka", "Hokkien", "Min-Nan", "Min-Dong", "Min-Bei",
    "Min", "Wu", "Gan", "Jin", "Xiang", "Southern-Min", "Teochew",
    "Classical-Chinese", "Middle-Chinese", "Old-Chinese",
}


@dataclass(frozen=True, slots=True)
class CedictEntry:
    traditional: str
    simplified: str
    numbered_pinyin: str
    glosses: tuple[str, ...]
    source_sha256: str
    line_number: int
    line_sha256: str


def read_cedict(
    path: Path, *, expected_sha256: str, limits: SourceLimits | None = None,
) -> Iterator[CedictEntry]:
    """Read the published v1 export, retaining every reading, variant and gloss.

    Nonstandard reading notation is retained as evidence, not guessed. The v2
    format needs a separate parser and is deliberately rejected here.
    """
    limits = limits or SourceLimits(
        max_bytes=32 * 1024**2, max_expanded_bytes=64 * 1024**2,
        max_line_bytes=64 * 1024, max_records=500_000,
    )
    for number, line in enumerate(_verified_lines(path, expected_sha256, limits), 1):
        value = line.rstrip("\r\n")
        if not value or value.startswith("#"):
            continue
        match = _CEDICT_V1.fullmatch(value)
        if match is None:
            raise ValueError(f"invalid CC-CEDICT v1 record at line {number}")
        traditional, simplified, pinyin, gloss = match.groups()
        yield CedictEntry(
            traditional=traditional, simplified=simplified, numbered_pinyin=pinyin,
            glosses=tuple(gloss.split("/")), source_sha256=expected_sha256,
            line_number=number, line_sha256=hashlib.sha256(value.encode()).hexdigest(),
        )


def pinyin_key(value: str) -> str | None:
    """Compare marked or v1 numbered readings without guessing syllable splits.

    Lexical tones remain distinct. Whitespace, hyphens and syllable apostrophes
    are orthographic separators. Parentheses, regional notes, rhotic r5 and
    other special notation remain unresolved rather than silently discarded.
    """
    value = unicodedata.normalize("NFC", value.strip().lower()).replace("u:", "ü")
    if re.search(r"\d", value):
        parts = value.split()
        if not parts or any(not _NUMBERED.fullmatch(p) or p == "r5" for p in parts):
            return None
        value = "".join(to_tone(p).replace("v", "ü") for p in parts)
    else:
        value = re.sub(r"[\s'’\-]", "", value)
    return value if _MARKED.fullmatch(value) else None


def lookup_forms(
    words: Iterable[str], entries: Iterable[CedictEntry],
) -> dict[str, list[dict]]:
    """Expand source lookups, retaining how each spelling was discovered."""
    seeds = set(words)
    forms: dict[str, list[dict]] = defaultdict(list)
    converter = OpenCC("s2t")
    for word in sorted(seeds):
        forms[word].append({"seed": word, "kind": "frequency-spelling"})
        converted = converter.convert(word)
        if converted != word:
            forms[converted].append({"seed": word, "kind": "conversion-hint-only"})
    for entry in entries:
        if entry.simplified in seeds and entry.traditional != entry.simplified:
            forms[entry.traditional].append({
                "seed": entry.simplified, "kind": "cedict-pair",
                "source_record_sha256": entry.line_sha256,
            })
    return dict(sorted(forms.items()))


def mandarin_readings(record: dict) -> tuple[str, ...]:
    """Select explicit Mandarin Pinyin, excluding phonetic sandhi and Taiwan-only.

    These readings can belong to a whole record with several senses. They are
    NOT an automatic mapping of each pronunciation to every sense in it.
    """
    selected = set()
    for sound in record.get("sounds", []):
        tags = set(sound.get("tags", []))
        value = sound.get("zh_pron")
        if (
            {"Mandarin", "Pinyin"}.issubset(tags)
            and not tags.intersection({"phonetic", "Taiwan", "Taiwanese-Mandarin"})
            and (tags.intersection({"Standard", "Standard-Chinese"})
                 or (tags == {"Mandarin", "Pinyin"} and not sound.get("raw_tags")))
            and isinstance(value, str) and pinyin_key(value)
        ):
            selected.add(value)
    return tuple(sorted(selected))


def lexical_evidence(record: dict) -> dict:
    """Keep structured dictionary evidence and dialect uncertainty visible."""
    readings = mandarin_readings(record)
    senses = []
    for sense in record.get("senses", []):
        tags = set(record.get("tags", [])) | set(sense.get("tags", []))
        glosses = sense.get("glosses", [])
        if not glosses:
            continue
        if tags.intersection(_OTHER_VARIETIES) and "Mandarin" not in tags:
            scope = "other-variety"
        elif readings:
            scope = "mandarin-candidate"
        else:
            scope = "scope-unresolved"
        senses.append({
            "source_sense_id": sense.get("id"), "glosses": glosses,
            "tags": sorted(tags), "scope": scope,
            "form_of": sense.get("form_of", []),
            "alt_of": sense.get("alt_of", []),
        })
    return {
        "source_word": record.get("word"), "source_pos": record.get("pos"),
        "source_record_sha256": canonical_sha256(record),
        "record_pinyin": readings, "senses": senses,
        "production_eligible": False,
    }


def audit_word(word: str, *, entries: list[CedictEntry], records: list[dict]) -> dict:
    """Triage one frequency candidate; a matching reading is not sense review.

    Caller supplies lookup records, which are retained with their exact source
    spelling. Only source-attested spelling pairs contribute structured support;
    OpenCC-only hits remain inspectable evidence, never qualification votes.
    """
    entries = [e for e in entries if e.simplified == word]
    forms = {word, *(e.traditional for e in entries)}
    evidence = [lexical_evidence(r) for r in records]
    flags = []
    readings = {pinyin_key(e.numbered_pinyin) for e in entries} - {None}
    if not entries:
        flags.append("missing-cedict-entry")
    if any(pinyin_key(e.numbered_pinyin) is None for e in entries):
        flags.append("special-reading-notation")
    if len(readings) > 1:
        flags.append("multiple-readings")
    if len({e.traditional for e in entries}) > 1:
        flags.append("multiple-traditional-forms")
    structured = [e for e in evidence if (
        e["source_word"] in forms
        and e["source_pos"] in _POS
        and (not entries or any(pinyin_key(p) in readings for p in e["record_pinyin"]))
        and any(s["scope"] == "mandarin-candidate" for s in e["senses"])
    )]
    if not structured:
        flags.append("missing-structured-mandarin-sense")
    lexical = None
    try:
        generated = derive_mandarin_orthography(word=word, sentence=word)
        lexical = {"pinyin": generated.word_pinyin, "traditional": generated.word_traditional}
        if readings and pinyin_key(generated.word_pinyin) not in readings:
            # Can be an attested alternate in a gloss or a regional convention.
            # A mismatch is a review request, not a demonstrated error.
            flags.append("default-reading-not-in-cedict-headings")
        if entries and generated.word_traditional not in {e.traditional for e in entries}:
            flags.append("traditional-conversion-needs-review")
    except MandarinOrthographyError as error:
        flags.append("primary-script-or-reading-rejected")
        lexical = {"error": str(error)}
    if "primary-script-or-reading-rejected" in flags or not entries:
        status = "needs-source-or-script-review"
    elif flags:
        status = "needs-context-review"
    else:
        status = "dictionary-supported-candidate"
    return {
        "word": word, "status": status, "flags": flags,
        "generated": lexical, "cedict": [asdict(e) for e in entries],
        "wiktextract": evidence,
        "structured_mandarin_record_count": len(structured),
        "review_level": "automated-source-triage",
        "production_eligible": False,
    }


@dataclass(frozen=True, slots=True)
class MandarinPronunciationReview:
    """An evidence-referenced reading for one exact word/sentence pair.

    References are audit links, not signatures or proof of human approval. The
    reviewer must examine their contents. This validates structural consistency
    only and never issues a production, audio or redistribution receipt.
    """

    word: str
    sentence: str
    orthography: MandarinOrthography
    evidence_record_sha256: tuple[str, ...]

    def __post_init__(self) -> None:
        for value in (self.word, self.sentence):
            validate_simplified_mandarin(value)
        if self.sentence.count(self.word) != 1:
            raise MandarinOrthographyError("review requires one exact target occurrence")
        if not self.evidence_record_sha256 or any(
            not re.fullmatch(r"[0-9a-f]{64}", digest) for digest in self.evidence_record_sha256
        ):
            raise MandarinOrthographyError("review requires source evidence hashes")
        word_html = render_mandarin_sentence(
            sentence=self.word, sentence_pinyin=self.orthography.word_pinyin,
        )
        sentence_html = render_mandarin_sentence(
            sentence=self.sentence, sentence_pinyin=self.orthography.sentence_pinyin,
        )
        word_readings = re.findall(r"<rt>([^<]+)</rt>", word_html)
        sentence_readings = re.findall(r"<rt>([^<]+)</rt>", sentence_html)
        start = script_counts(self.sentence[:self.sentence.index(self.word)]).han
        if sentence_readings[start:start + len(word_readings)] != word_readings:
            raise MandarinOrthographyError("reviewed word reading differs from sentence target")
        converter = OpenCC("t2s")
        for original, traditional in (
            (self.word, self.orthography.word_traditional),
            (self.sentence, self.orthography.sentence_traditional),
        ):
            if converter.convert(traditional) != original:
                raise MandarinOrthographyError("reviewed Traditional text changes the source")


class ReviewedMandarinOrthographyService:
    """Inject into AssembleExportCardsService to require contextual readings.

    Missing or changed contexts fail closed instead of silently recomputing a
    polyphonic character. Does not alter pypinyin global dictionaries or the
    generic default service; persisted rows retain the existing 12-field model.
    """

    def __init__(self, reviews: Iterable[MandarinPronunciationReview]) -> None:
        self._reviews = {}
        for review in reviews:
            key = (
                validate_simplified_mandarin(review.word),
                validate_simplified_mandarin(review.sentence),
            )
            if key in self._reviews:
                raise MandarinOrthographyError("duplicate Mandarin review context")
            self._reviews[key] = review.orthography

    def derive(self, *, word: str, sentence: str) -> MandarinOrthography:
        key = (validate_simplified_mandarin(word), validate_simplified_mandarin(sentence))
        if key not in self._reviews:
            raise MandarinOrthographyError("Mandarin context requires a pronunciation review")
        return self._reviews[key]
