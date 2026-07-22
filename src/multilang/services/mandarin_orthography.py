"""Deterministic Simplified Chinese validation and orthography derivation."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import unicodedata

from opencc import OpenCC
from pypinyin import Style, lazy_pinyin


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
    "validate_simplified_mandarin",
]
