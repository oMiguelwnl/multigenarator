"""Deterministic, local Modified-Hepburn romanization for Japanese cards."""

from __future__ import annotations

from functools import lru_cache

import cutlet

from multilang.services.japanese_analysis import (
    japanese_mecab_arguments,
    japanese_tagger,
    validate_japanese_reading,
)


class JapaneseRomajiError(ValueError):
    """Raised when Japanese text cannot be safely converted to romaji."""


@lru_cache(maxsize=1)
def _get_converter() -> cutlet.Cutlet:
    return cutlet.Cutlet(
        "hepburn",
        use_foreign_spelling=False,
        ensure_ascii=True,
        mecab_args=japanese_mecab_arguments(),
    )


def romanize_japanese(value: str, *, reading: str | None = None) -> str:
    """Convert Japanese text to validated ASCII Modified-Hepburn romaji."""

    source = value.strip()
    if not source:
        raise JapaneseRomajiError("Japanese source text must not be blank")

    try:
        # Use the same explicitly selected tokenizer as furigana and validation.
        if reading is not None:
            converted = _get_converter().map_kana(validate_japanese_reading(reading)).capitalize()
        else:
            tokens = _get_converter().romaji_tokens(japanese_tagger()(source))
            converted = "".join(str(token) for token in tokens)
    except Exception as exc:
        raise JapaneseRomajiError("Japanese text could not be romanized") from exc

    output = " ".join(str(converted or "").split())
    if not output:
        raise JapaneseRomajiError("Japanese romaji output must not be blank")
    if not output.isascii():
        raise JapaneseRomajiError("Japanese romaji output must contain only ASCII text")

    source_question_marks = source.count("?") + source.count("？")
    if output.count("?") > source_question_marks:
        raise JapaneseRomajiError("Japanese romaji output contains an unresolved placeholder")
    return output


__all__ = ["JapaneseRomajiError", "romanize_japanese"]
