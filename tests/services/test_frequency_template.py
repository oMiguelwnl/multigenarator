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
        assert '"Noto Serif KR"' in frequency.css
        assert "word-break: keep-all" in frequency.css


def test_frequency_redesign_preserves_mandarin_word_list_base() -> None:
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


@pytest.mark.parametrize(('language', 'font'), [
    (SupportedLanguage.EN, 'Georgia'),
    (SupportedLanguage.JA, 'Noto Serif JP'),
    (SupportedLanguage.ZH, 'Noto Serif SC'),
    (SupportedLanguage.KO, 'Noto Serif KR'),
])
def test_frequency_uses_shared_hero_dark_shell_and_serif(language, font) -> None:
    template = load_card_template('frequency', language=language)
    assert '--max-width-card: 620px;' in template.css
    assert '--color-card-background: #0f1b2d;' in template.css
    assert '--color-nightMode-card-background: #0f1b2d;' in template.css
    assert 'border-left: 3px solid #3b82f6;' in template.css
    assert font in template.css
    assert 'examplePanel' in template.front
    assert '{{word_audio}}' in template.front
    assert '{{sentence_audio}}' in template.front


def test_japanese_frequency_exporter_uses_the_shared_loader() -> None:
    from multilang.services.japanese_frequency_deck import build_japanese_model

    template = load_card_template('frequency', language=SupportedLanguage.JA)
    model = build_japanese_model()
    assert model.css == template.css
    assert model.templates[0]['qfmt'] == template.front
    assert model.templates[0]['afmt'] == template.back
    highlight = load_card_template('kindle-highlights', language=SupportedLanguage.JA)
    assert highlight.css != template.css
    assert '{{furigana:Word Reading}}' in template.front
    assert '{{Sentence Romaji}}' in template.back
