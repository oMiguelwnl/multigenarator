"""Deterministic Simplified Chinese validation and orthography derivation."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from html import escape

from opencc import OpenCC
from pypinyin import Style, lazy_pinyin
from pypinyin.contrib.tone_convert import to_tone, to_tone3

_PINYIN_LETTERS = re.compile(r"[A-Za-z\u00c0-\u024f\u1e00-\u1eff]+")


class MandarinOrthographyError(ValueError):
    """Raised when Mandarin source text or a derived value is invalid."""


@dataclass(frozen=True, slots=True)
class MandarinOrthography:
    """Frozen orthography values stored with a Mandarin export snapshot."""

    word_pinyin: str
    word_traditional: str
    sentence_pinyin: str
    sentence_traditional: str


@dataclass(frozen=True, slots=True)
class ScriptCounts:
    """Counts of scripts that distinguish Mandarin from other text."""

    han: int
    kana: int
    latin: int
    unsupported_letter: int = 0


class MandarinOrthographyService:
    """Validate source text and derive all four persisted Mandarin fields."""

    def derive(self, *, word: str, sentence: str) -> MandarinOrthography:
        return derive_mandarin_orthography(word=word, sentence=sentence)


def derive_mandarin_orthography(*, word: str, sentence: str) -> MandarinOrthography:
    """Derive tonal pinyin and Traditional forms from Simplified source text."""

    normalized_word = validate_simplified_mandarin(word)
    normalized_sentence = validate_simplified_mandarin(sentence)
    value = MandarinOrthography(
        word_pinyin=tonal_pinyin(normalized_word),
        word_traditional=_s2t().convert(normalized_word).strip(),
        sentence_pinyin=tonal_pinyin(normalized_sentence),
        sentence_traditional=_s2t().convert(normalized_sentence).strip(),
    )
    if not all(
        (
            value.word_pinyin,
            value.word_traditional,
            value.sentence_pinyin,
            value.sentence_traditional,
        )
    ):
        raise MandarinOrthographyError("Mandarin orthography produced an empty derived value")
    return value


def validate_simplified_mandarin(text: str) -> str:
    """Normalize and require non-empty, Han-dominant Simplified Chinese text."""

    value = unicodedata.normalize("NFKC", str(text or "")).strip()
    if not value:
        raise MandarinOrthographyError("Mandarin text must not be empty")

    counts = script_counts(value)
    if counts.han == 0:
        raise MandarinOrthographyError("Mandarin text must contain Han characters")
    if counts.kana:
        raise MandarinOrthographyError("Mandarin text must not contain kana")
    if counts.latin:
        raise MandarinOrthographyError("Mandarin text must not contain Latin letters")
    if counts.unsupported_letter:
        raise MandarinOrthographyError("Mandarin text must not contain unsupported letters")
    if counts.han <= counts.kana + counts.latin:
        raise MandarinOrthographyError("Mandarin text must be Han predominant")
    if _t2s().convert(value) != value:
        raise MandarinOrthographyError("Mandarin primary text must use canonical Simplified Chinese")
    return value


def tonal_pinyin(text: str) -> str:
    """Return phrase-aware pinyin with tone marks and punctuation attached."""

    value = validate_simplified_mandarin(text)
    # ``lazy_pinyin`` always returns a single reading. Its 0.55 API does not
    # expose the ``heteronym`` keyword available on ``pinyin``.
    tokens = lazy_pinyin(
        value,
        style=Style.TONE,
        v_to_u=True,
        neutral_tone_with_five=False,
        tone_sandhi=False,
    )
    rendered = ""
    for raw_token in tokens:
        token = str(raw_token or "")
        if not token:
            continue
        if _is_pinyin_syllable(token):
            if rendered and not rendered.endswith((" ", "\n", "\t")) and not _ends_with_opening_mark(rendered):
                rendered += " "
            rendered += token
        elif token.isspace():
            if rendered and not rendered.endswith(" "):
                rendered += " "
        else:
            rendered = rendered.rstrip() + token

    rendered = rendered.strip()
    if not rendered:
        raise MandarinOrthographyError("Mandarin pinyin derivation produced an empty value")
    _validate_pinyin_output(rendered)
    return rendered


def render_mandarin_sentence(
    *, sentence: str, sentence_pinyin: str, cloze_span: tuple[int, int] | None = None
) -> str:
    """Render saved readings as safe ruby, without deriving new pronunciations.

    Walk both strings together: punctuation and literal numbers are alignment
    anchors, and each Han character consumes exactly one separated syllable.
    A misaligned reading fails closed. Input offsets and visible source
    characters are preserved; normalization is only used to compare punctuation.
    """
    if not sentence or not sentence_pinyin or max(len(sentence), len(sentence_pinyin)) > 4000:
        raise MandarinOrthographyError("Mandarin annotation requires bounded non-empty text")
    if any(unicodedata.category(c).startswith("C") and c not in "\n\r\t"
           for c in sentence + sentence_pinyin):
        raise MandarinOrthographyError("Mandarin annotation contains control characters")
    counts = script_counts(sentence)
    if not counts.han or counts.kana or counts.latin or counts.unsupported_letter:
        raise MandarinOrthographyError("Mandarin annotation requires Han source text")
    if cloze_span is not None and not 0 <= cloze_span[0] < cloze_span[1] <= len(sentence):
        raise MandarinOrthographyError("Mandarin cloze span is out of bounds")
    reading = unicodedata.normalize("NFC", sentence_pinyin)
    cursor = 0
    output: list[str] = []
    for index, character in enumerate(sentence):
        if cloze_span is not None and index == cloze_span[0]:
            output.append('<span class="semantic-cloze-target">')
        while cursor < len(reading) and reading[cursor].isspace():
            cursor += 1
        if character.isspace():
            output.append(escape(character))
        elif _is_han(character):
            if index and _is_han(sentence[index - 1]) and reading[cursor:cursor + 1] in {"'", "’"}:
                cursor += 1
            match = _PINYIN_LETTERS.match(reading, cursor)
            if match is None:
                raise MandarinOrthographyError("Mandarin pinyin does not align with the sentence")
            syllable = match.group()
            cursor = match.end()
            # Source numbers disambiguate neutral syllables (了2 -> le2).
            # Accented syllables cannot carry a second numeric tone marker.
            numbered = to_tone3(syllable.lower())
            marked_tone = next((c for c in numbered if c in "1234"), None)
            source_number = re.match(r"\d+", sentence[index + 1:].lstrip())
            reading_number = re.match(r"\d+", reading[cursor:])
            literal_number = (
                source_number is not None and reading_number is not None
                and unicodedata.normalize("NFKC", source_number.group())
                == unicodedata.normalize("NFKC", reading_number.group())
            )
            if (
                marked_tone is None and not literal_number
                and reading[cursor:cursor + 1] in {"1", "2", "3", "4", "5"}
            ):
                syllable += reading[cursor]
                cursor += 1
            tone = marked_tone or (syllable[-1] if syllable[-1] in "12345" else "5")
            annotation = to_tone(syllable)
            output.append(
                f'<ruby class="mandarin-ruby tone-{tone}">{escape(character)}'
                f'<rt>{escape(annotation)}</rt></ruby>'
            )
        else:
            if cursor >= len(reading) or _comparable_punctuation(character) != _comparable_punctuation(reading[cursor]):
                raise MandarinOrthographyError("Mandarin pinyin punctuation does not align with the sentence")
            cursor += 1
            output.append(escape(character))
        if cloze_span is not None and index + 1 == cloze_span[1]:
            output.append("</span>")
    if reading[cursor:].strip():
        raise MandarinOrthographyError("Mandarin pinyin has extra text after the sentence")
    return "".join(output)


def _comparable_punctuation(value: str) -> str:
    return unicodedata.normalize("NFKC", value).replace("。", ".")


def script_counts(text: str) -> ScriptCounts:
    """Count Han, kana, and Latin letters after NFKC normalization."""

    value = unicodedata.normalize("NFKC", str(text or ""))
    return ScriptCounts(
        han=sum(_is_han(character) for character in value),
        kana=sum(_is_kana(character) for character in value),
        latin=sum(_is_latin(character) for character in value),
        unsupported_letter=sum(_is_unsupported_letter(character) for character in value),
    )


def _is_han(character: str) -> bool:
    name = unicodedata.name(character, "")
    return character == "〇" or "CJK UNIFIED IDEOGRAPH" in name or "CJK COMPATIBILITY IDEOGRAPH" in name


def _is_kana(character: str) -> bool:
    name = unicodedata.name(character, "")
    return "HIRAGANA" in name or "KATAKANA" in name


def _is_latin(character: str) -> bool:
    return "LATIN" in unicodedata.name(character, "") and unicodedata.category(character).startswith("L")


def _is_unsupported_letter(character: str) -> bool:
    return (
        unicodedata.category(character).startswith("L")
        and not _is_han(character)
        and not _is_kana(character)
        and not _is_latin(character)
    )


def _is_pinyin_syllable(token: str) -> bool:
    has_latin_letter = False
    for character in token:
        if _is_latin(character):
            has_latin_letter = True
            continue
        if unicodedata.category(character).startswith("M"):
            continue
        return False
    return has_latin_letter


def _validate_pinyin_output(value: str) -> None:
    if any(_is_han(character) or _is_kana(character) or _is_unsupported_letter(character) for character in value):
        raise MandarinOrthographyError("Mandarin pinyin derivation produced non-pinyin characters")


def _ends_with_opening_mark(value: str) -> bool:
    return value.endswith(("“", "‘", "（", "(", "[", "【", "《", "〈"))


@lru_cache(maxsize=1)
def _s2t() -> OpenCC:
    return OpenCC("s2t")


@lru_cache(maxsize=1)
def _t2s() -> OpenCC:
    return OpenCC("t2s")


__all__ = [
    "MandarinOrthography",
    "MandarinOrthographyError",
    "MandarinOrthographyService",
    "ScriptCounts",
    "derive_mandarin_orthography",
    "script_counts",
    "tonal_pinyin",
    "render_mandarin_sentence",
    "validate_simplified_mandarin",
]
