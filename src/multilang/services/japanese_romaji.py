"""Deterministic, local Modified-Hepburn romanization for Japanese cards."""

from __future__ import annotations

from functools import lru_cache

import cutlet


class JapaneseRomajiError(ValueError):
    """Raised when Japanese text cannot be safely converted to romaji."""


@lru_cache(maxsize=1)
def _get_converter() -> cutlet.Cutlet:
    return cutlet.Cutlet(
        "hepburn",
        use_foreign_spelling=False,
        ensure_ascii=True,
    )


def romanize_japanese(value: str) -> str:
    """Convert Japanese text to validated ASCII Modified-Hepburn romaji."""

    source = value.strip()
    if not source:
        raise JapaneseRomajiError("Japanese source text must not be blank")

    try:
        converted = _get_converter().romaji(source)
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
