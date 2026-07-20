"""Generate Anki-native furigana for Japanese text."""

from __future__ import annotations

from functools import lru_cache
import unicodedata


class JapaneseFuriganaError(ValueError):
    """Raised when a kanji-bearing Japanese string cannot be annotated."""


def format_japanese_furigana(text: str) -> str:
    """Return text with Anki furigana brackets for kanji tokens.

    Example: ``学校に行く。`` -> ``学校[がっこう]に行[い]く。``.
    """

    value = str(text or "").strip()
    if not value:
        return ""

    rendered = ""
    for token in _tagger()(value):
        surface = str(token.surface)
        reading = _token_reading(token)
        rendered_token = _annotate_token(surface=surface, reading=reading)
        rendered += rendered_token
    return rendered


def katakana_to_hiragana(value: str) -> str:
    """Convert full-width katakana to hiragana, preserving other characters."""

    chars: list[str] = []
    for character in value:
        codepoint = ord(character)
        if 0x30A1 <= codepoint <= 0x30F6:
            chars.append(chr(codepoint - 0x60))
        else:
            chars.append(character)
    return "".join(chars)


@lru_cache(maxsize=1)
def _tagger():
    import unidic_lite
    from fugashi import Tagger

    return Tagger(f"-d {unidic_lite.DICDIR}")


def _token_reading(token: object) -> str:
    feature = getattr(token, "feature", None)
    reading = getattr(feature, "kana", None) or getattr(feature, "pron", None) or ""
    return katakana_to_hiragana(str(reading or "").strip())


def _annotate_token(*, surface: str, reading: str) -> str:
    if not _contains_kanji(surface):
        return surface
    if not reading:
        raise JapaneseFuriganaError(f"missing reading for kanji token: {surface}")

    runs = _surface_runs(surface)
    reading_index = 0
    output = ""
    for index, (is_kanji_run, run_text) in enumerate(runs):
        if not is_kanji_run:
            output += run_text
            literal = katakana_to_hiragana(run_text)
            if literal and reading.startswith(literal, reading_index):
                reading_index += len(literal)
            continue

        next_literal = _next_non_kanji_literal(runs[index + 1 :])
        if next_literal:
            next_literal = katakana_to_hiragana(next_literal)
            next_index = reading.find(next_literal, reading_index)
            if next_index < reading_index:
                raise JapaneseFuriganaError(
                    f"unable to align reading for kanji token: {surface} ({reading})"
                )
            run_reading = reading[reading_index:next_index]
            reading_index = next_index
        else:
            run_reading = reading[reading_index:]
            reading_index = len(reading)

        if not run_reading:
            raise JapaneseFuriganaError(f"empty reading for kanji run: {run_text}")
        output += f"{run_text}[{run_reading}]"

    return output


def _surface_runs(surface: str) -> list[tuple[bool, str]]:
    runs: list[tuple[bool, str]] = []
    current_is_kanji: bool | None = None
    current = ""
    for character in surface:
        is_kanji = _is_kanji(character)
        if current and is_kanji != current_is_kanji:
            runs.append((bool(current_is_kanji), current))
            current = ""
        current += character
        current_is_kanji = is_kanji
    if current:
        runs.append((bool(current_is_kanji), current))
    return runs


def _next_non_kanji_literal(runs: list[tuple[bool, str]]) -> str:
    for is_kanji_run, run_text in runs:
        if not is_kanji_run and _contains_kana(run_text):
            return run_text
    return ""


def _contains_kanji(value: str) -> bool:
    return any(_is_kanji(character) for character in value)


def _contains_kana(value: str) -> bool:
    return any(_is_hiragana(character) or _is_katakana(character) for character in value)


def _is_kanji(character: str) -> bool:
    if character in {"々", "〆", "ヶ", "ヵ"}:
        return True
    return "CJK UNIFIED IDEOGRAPH" in unicodedata.name(character, "")


def _is_hiragana(character: str) -> bool:
    return "HIRAGANA" in unicodedata.name(character, "")


def _is_katakana(character: str) -> bool:
    return "KATAKANA" in unicodedata.name(character, "")


__all__ = ["JapaneseFuriganaError", "format_japanese_furigana", "katakana_to_hiragana"]
