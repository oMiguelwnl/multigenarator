"""Frequency presentation must not restyle other source modes."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from multilang.domain.jobs import SupportedLanguage
from multilang.services.card_template_loader import load_card_template


@pytest.mark.parametrize("language", [SupportedLanguage.EN, SupportedLanguage.DE, SupportedLanguage.KO])
def test_frequency_redesign_is_separate_from_korean_grammar(language: SupportedLanguage) -> None:
    frequency = load_card_template("frequency", language=language)
    grammar = load_card_template("korean-grammar", language=SupportedLanguage.KO)

    assert frequency.source_template_name == "frequency_card"
    assert grammar.source_template_name == "normal_card"
    assert frequency.css != grammar.css
    assert "{{Definitions}}" in frequency.front
    assert "{{Translation}}" in frequency.front
    if language is SupportedLanguage.KO:
        assert '"Noto Sans KR"' in frequency.css
        assert "word-break: keep-all" in frequency.css


def test_mandarin_frequency_redesign_does_not_restyle_personal_word_lists() -> None:
    base = load_card_template("frequency")
    frequency = load_card_template("frequency", language=SupportedLanguage.ZH)
    personal = load_card_template("word-list", language=SupportedLanguage.ZH)
    legacy = Path("src/multilang/templates/normal_card.md").read_text(encoding="utf-8")
    old_css = re.search(r"## Styling \(CSS\)\s+```css\n(.*?)```", legacy, re.DOTALL)

    assert old_css is not None
    assert frequency.front == personal.front
    assert frequency.back == personal.back
    assert frequency.css != personal.css
    assert frequency.css.startswith(base.css + "\n\n")
    assert personal.css.startswith(old_css[1].strip() + "\n\n")
    assert frequency.css.removeprefix(base.css + "\n\n") == personal.css.removeprefix(
        old_css[1].strip() + "\n\n"
    )
