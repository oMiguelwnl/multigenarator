from __future__ import annotations

import re
from pathlib import Path

import pytest

from multilang.domain.exporting import (
    HIGHLIGHT_EXPORT_CARD_FIELD_NAMES,
    JAPANESE_EXPORT_CARD_FIELD_NAMES,
    LATIN_EXPORT_CARD_FIELD_NAMES,
)
from multilang.domain.jobs import SupportedLanguage
from multilang.services.card_template_loader import (
    CardTemplate,
    load_card_template,
    validate_template_references,
)
from multilang.services.japanese_frequency_deck import (
    JAPANESE_FIELD_NAMES,
    build_japanese_model,
)
from multilang.services.japanese_kana_deck import KANA_FIELD_NAMES, build_kana_model
from multilang.services.russian_phoneme_deck import (
    PHONEME_FIELD_NAMES,
    build_greek_phoneme_model,
    build_polish_phoneme_model,
    build_russian_phoneme_model,
)


NORMAL_TEMPLATE = """
# Template

## Front Template

```html
{{word}} {{Translation}} {{#Image}}{{Image}}{{/Image}}
```

## Back Template

```html
{{FrontSide}} {{Definitions}}
```

## Styling (CSS)

```css
.card { color: blue; }
```
"""


HIGHLIGHT_TEMPLATE = """
# Highlight Template

## Front Template

```html
{{Word}} {{#IPA}}{{IPA}}{{/IPA}} {{Example Sentence}} {{sentence_audio}}
```

## Back Template

```html
{{FrontSide}}<hr id="answer"><div>Definition</div>{{Definition}}{{#Image}}{{Image}}{{/Image}}
```

## Styling (CSS)

```css
.highlight-card { color: var(--multilang-blue); }
```
"""


def _balanced_div(markup: str, *, class_name: str) -> str:
    opening = re.search(
        rf'<div\s+[^>]*class="[^"]*\b{re.escape(class_name)}\b[^"]*"[^>]*>',
        markup,
    )
    assert opening is not None, f"missing div with class {class_name!r}"
    depth = 1
    for token in re.finditer(r"<div\b[^>]*>|</div>", markup[opening.end() :]):
        depth += -1 if token.group() == "</div>" else 1
        if depth == 0:
            return markup[opening.start() : opening.end() + token.end()]
    raise AssertionError(f"unclosed div with class {class_name!r}")


def _last_css_block(css: str, *, selector: str) -> str:
    css_without_comments = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    blocks = [
        declarations
        for selector_list, declarations in re.findall(r"([^{}]+)\{([^{}]*)\}", css_without_comments)
        if selector in {item.strip() for item in selector_list.split(",")}
    ]
    assert blocks, f"missing CSS selector {selector!r}"
    return blocks[-1]


def _last_css_value(css: str, property_name: str, *, selector: str | None = None) -> str:
    declarations = css if selector is None else _last_css_block(css, selector=selector)
    values = re.findall(rf"(?:^|[;\s]){re.escape(property_name)}:\s*([^;]+);", declarations)
    assert values, f"missing CSS property {property_name!r}"
    return values[-1].strip()


def _write_templates(root: Path) -> Path:
    template_dir = root / "src" / "multilang" / "templates"
    template_dir.mkdir(parents=True)
    (template_dir / "normal_card.md").write_text(NORMAL_TEMPLATE, encoding="utf-8")
    (template_dir / "highlight_card.md").write_text(HIGHLIGHT_TEMPLATE, encoding="utf-8")
    return template_dir


def test_load_card_template_keeps_normal_template_and_translation_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    template_dir = _write_templates(tmp_path)
    monkeypatch.setattr("multilang.services.card_template_loader.TEMPLATE_ROOT", template_dir)

    template = load_card_template(source_type="frequency")

    assert template.source_template_name == "normal_card"
    assert "{{Translation}}" in template.front
    assert "{{FrontSide}}" in template.back
    validate_template_references(
        template,
        field_names=(
            "SortIndex",
            "word",
            "IPA",
            "Definitions",
            "Example Sentence",
            "Translation",
            "word_audio",
            "sentence_audio",
            "Image",
        ),
    )


def test_normal_template_validation_rejects_removed_front_of_card_field() -> None:
    template = CardTemplate(
        front="{{Front of Card}} {{Translation}}",
        back="{{FrontSide}} {{Definitions}}",
        css=".card { color: blue; }",
        source_template_name="normal_card",
    )

    with pytest.raises(ValueError, match="Front of Card"):
        validate_template_references(
            template,
            field_names=(
                "SortIndex",
                "word",
                "IPA",
                "Definitions",
                "Example Sentence",
                "Translation",
                "word_audio",
                "sentence_audio",
                "Image",
            ),
        )


def test_project_normal_template_groups_example_sentence_and_audio_in_one_row() -> None:
    template = load_card_template(source_type="frequency")

    assert 'exampleSentenceLine' in template.front
    assert '<span class="exampleSentenceText">{{Example Sentence}}</span>' in template.front
    assert '<span class="sentenceAudioButton">{{sentence_audio}}</span>' in template.front
    assert template.front.index('class="exampleSentenceText"') < template.front.index('class="sentenceAudioButton"')
    assert 'id="translation"' in template.front
    assert 'style="display:none;"' in template.front
    assert '{{Translation}}' in template.front
    assert 'document.getElementById("translation").style.display = "block";' in template.back
    assert '{{FrontSide}}' in template.back


def test_project_normal_template_css_keeps_sentence_audio_beside_text_responsively() -> None:
    template = load_card_template(source_type="frequency")

    assert ".exampleSentenceLine" in template.css
    assert "display: flex;" in template.css
    assert "align-items: center;" in template.css
    assert "gap:" in template.css
    assert ".exampleSentenceText" in template.css
    assert "flex: 1 1 auto;" in template.css
    assert "min-width: 0;" in template.css
    assert ".sentenceAudioButton" in template.css
    assert "flex: 0 0 auto;" in template.css
    assert "margin-left: 8px;" in template.css


def test_project_normal_template_preserves_contract_and_uses_gemini_dark_layout() -> None:
    template = load_card_template(source_type="frequency")
    references = re.findall(r"{{[#/]?([^{}]+)}}", template.front + template.back)

    assert references == [
        "word",
        "IPA",
        "IPA",
        "IPA",
        "word_audio",
        "Definitions",
        "Image",
        "Image",
        "Image",
        "Example Sentence",
        "sentence_audio",
        "Translation",
        "FrontSide",
    ]
    assert 'id="translation"' in template.front
    assert 'style="display:none;"' in template.front
    assert template.back.count("<script>") == 1
    assert 'document.getElementById("translation").style.display = "block";' in template.back
    assert "innerHTML" not in template.front + template.back

    css = template.css
    assert _last_css_value(css, "--color-page-background") == "#121212"
    assert _last_css_value(css, "--color-card-background") == "#1E1E1E"
    assert _last_css_value(css, "--color-text-primary") == "#EAEAEA"
    assert _last_css_value(css, "--color-text-muted") == "#A0A0A0"
    assert _last_css_value(css, "--color-divider") == "#333333"

    expected_declarations = {
        ".card": {
            "padding": "40px 16px",
            "min-height": "100vh",
            "overflow-x": "hidden",
        },
        ".customCard": {
            "max-width": "460px",
            "width": "100%",
            "padding": "28px 24px",
            "border": "1px solid var(--color-divider)",
            "border-radius": "8px",
            "box-shadow": "0 4px 20px rgba(0, 0, 0, 0.5)",
            "font-family": 'Georgia, Cambria, "Times New Roman", Times, serif',
        },
        ".targetWordContainer": {
            "align-items": "baseline",
            "flex-wrap": "wrap",
            "gap": "10px",
            "margin": "0 0 20px",
        },
        ".wordBlock": {
            "align-items": "baseline",
            "flex-wrap": "wrap",
            "gap": "10px",
        },
        ".targetWord": {
            "font-size": "38px",
            "font-weight": "600",
            "line-height": "1.1",
            "letter-spacing": "-0.5px",
        },
        ".ipa": {
            "font-size": "16px",
            "font-weight": "400",
            "color": "var(--color-text-muted)",
            "font-family": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        },
        ".dividerLine": {
            "height": "1px",
            "background": "var(--color-divider)",
            "margin": "20px 0",
        },
        ".header": {
            "font-size": "12px",
            "font-weight": "600",
            "letter-spacing": "0.5px",
            "margin": "0 0 8px",
            "text-transform": "uppercase",
        },
        ".definitionsList": {
            "font-size": "16px",
            "line-height": "1.6",
            "padding-left": "0",
        },
        ".examplePanel": {
            "padding": "0",
            "margin-top": "6px",
            "background": "transparent",
            "border": "0",
        },
        ".exampleSentenceLine": {
            "justify-content": "space-between",
            "gap": "10px",
            "font-size": "16px",
            "line-height": "1.5",
        },
        ".sentenceTranslation": {
            "margin-top": "8px",
            "font-size": "16px",
            "line-height": "1.5",
            "color": "var(--color-text-muted)",
        },
        ".replay-button": {
            "background": "transparent",
            "border": "0",
            "border-radius": "0",
        },
    }
    for selector, declarations in expected_declarations.items():
        for property_name, expected_value in declarations.items():
            assert _last_css_value(css, property_name, selector=selector) == expected_value

    assert "border-top: 4px" not in css
    assert "border-left: 3px" not in css
    assert "#3b82f6" not in css.casefold()

    example_panel = _balanced_div(template.front, class_name="examplePanel")
    assert example_panel.index("{{Example Sentence}}") < example_panel.index("{{sentence_audio}}")
    assert example_panel.index("{{sentence_audio}}") < example_panel.index('id="translation"')
    assert "{{Translation}}" in example_panel
    assert _last_css_value(css, "object-fit", selector=".image img") == "contain"
    assert _last_css_value(css, "max-width", selector=".image img") == "100% !important"
    assert _last_css_value(css, "overflow-wrap", selector=".customCard") == "anywhere"


def test_project_latin_mvp_template_uses_wordfreq_layout_with_latin_fields() -> None:
    template = load_card_template(source_type="latin-mvp")
    rendered = template.front + template.back

    assert template.source_template_name == "latin_mvp_card"
    assert 'class="customCard cardBack"' in template.front
    assert 'class="targetWord"' in template.front
    assert "exampleSentenceLine" in template.front
    assert ".customCard" in template.css
    assert ".exampleSentenceLine" in template.css
    assert "{{SortIndex}}" in rendered
    assert "{{Word}}" in rendered
    assert "{{Sentence}}" in rendered
    assert "{{Sentence Translation}}" in rendered
    assert "{{Grammar}}" in rendered
    assert "{{word_audio}}" in rendered
    assert "{{sentence_audio}}" in rendered
    assert "{{#Image}}" in rendered
    assert "{{Latin Word}}" not in rendered
    assert "{{Latin Sentence}}" not in rendered
    assert "{{Gramatica}}" not in rendered
    assert "{{word}}" not in rendered
    assert "{{IPA}}" not in rendered
    assert "{{Definitions}}" not in rendered
    assert "{{Example Sentence}}" not in rendered
    assert "{{Translation}}" not in rendered
    validate_template_references(template, field_names=LATIN_EXPORT_CARD_FIELD_NAMES)


def test_project_japanese_template_uses_japanese_fields_and_furigana_filter() -> None:
    template = load_card_template(source_type="frequency", language=SupportedLanguage.JA)
    rendered = template.front + template.back

    assert template.source_template_name == "japanese_card"
    assert "toggleFurigana" in rendered
    assert "{{furigana:Word Reading}}" in rendered
    assert "{{furigana:Sentence Furigana}}" in rendered
    assert "{{Target Word}}" in rendered
    assert "{{Sentence Translation}}" in rendered
    assert "{{IPA}}" not in rendered
    assert "{{Definitions}}" not in rendered
    validate_template_references(template, field_names=JAPANESE_EXPORT_CARD_FIELD_NAMES)


def test_generated_japanese_frequency_model_keeps_pedagogy_and_original_palette() -> None:
    model = build_japanese_model()
    front = model.templates[0]["qfmt"]
    back = model.templates[0]["afmt"]

    assert tuple(field["name"] for field in model.fields) == JAPANESE_FIELD_NAMES
    for anchor in (
        'class="jpCard jpCard--front"',
        'onclick="toggleFurigana()"',
        '{{furigana:Word Reading}}',
        '{{furigana:Sentence Furigana}}',
        '{{word_audio}}',
        '{{sentence_audio}}',
    ):
        assert anchor in front
    assert front.index("{{Target Word}}") < front.index("{{Sentence}}")
    assert front.index("{{word_audio}}") < front.index("{{sentence_audio}}")

    for anchor in (
        'class="jpCard jpCard--back"',
        "{{#Image}}",
        "{{Definition}}",
        "{{Sentence Translation}}",
        "https://jisho.org/",
        "https://www.google.co.jp/",
        "https://www.weblio.jp/",
    ):
        assert anchor in back
    assert back.index("{{#Image}}") < back.index("{{furigana:Word Reading}}")
    assert back.index("{{Definition}}") < back.index("{{Sentence Translation}}")
    assert back.index("jisho.org") < back.index("google.co.jp") < back.index("weblio.jp")

    assert _last_css_value(model.css, "--jp-color-page") == "#fdf6e3"
    assert _last_css_value(model.css, "--jp-color-card") == "#ffffff"
    assert _last_css_value(model.css, "--jp-color-text") == "#1f2430"
    assert _last_css_value(model.css, "--jp-color-nightMode-page") == "#0b0716"
    assert _last_css_value(model.css, "--jp-color-nightMode-card") == "#171226"
    assert "border-top: 4px solid var(--jp-color-accent);" in model.css


def test_generated_kana_model_keeps_media_sequence_and_original_palette() -> None:
    model = build_kana_model()
    front = model.templates[0]["qfmt"]
    back = model.templates[0]["afmt"]

    assert tuple(field["name"] for field in model.fields) == KANA_FIELD_NAMES
    assert 'class="kanaCard kanaCard--front"' in front
    assert front.index("{{Script}}") < front.index("{{Kana}}")
    assert 'class="kanaCard kanaCard--back"' in back
    ordered_anchors = (
        "{{#Gif}}",
        'class="kanaDivider"',
        "{{Romaji}}",
        "{{Audio}}",
        "{{#Picture}}",
        "{{#Strokes}}",
        "{{#Mnemonic}}",
    )
    assert list(map(back.index, ordered_anchors)) == sorted(map(back.index, ordered_anchors))
    for field in ("Gif", "Picture", "Strokes", "Mnemonic"):
        assert f"{{{{#{field}}}}}" in back
        assert f"{{{{/{field}}}}}" in back

    assert _last_css_value(model.css, "--kana-color-page") == "#fdf6e3"
    assert _last_css_value(model.css, "--kana-color-card") == "#ffffff"
    assert _last_css_value(model.css, "--kana-color-text") == "#1f2430"
    assert _last_css_value(model.css, "--kana-color-nightMode-page") == "#0b0716"
    assert _last_css_value(model.css, "--kana-color-nightMode-card") == "#171226"
    assert "border-top: 4px solid var(--kana-color-accent);" in model.css


@pytest.mark.parametrize(
    "private_reference",
    [
        "Translation",
        "Raw Highlight",
        "Book Title",
        "source_path",
        "private_import_record_id",
        "Unknown Field",
    ],
)
def test_highlight_template_validation_rejects_translation_private_and_unknown_fields(
    private_reference: str,
) -> None:
    template = CardTemplate(
        front=f"{{{{Word}}}} {{{{{private_reference}}}}}",
        back="{{FrontSide}} {{Definition}}",
        css=".card { overflow-x: hidden; }",
        source_template_name="highlight_card",
    )

    with pytest.raises(ValueError, match=private_reference):
        validate_template_references(template, field_names=HIGHLIGHT_EXPORT_CARD_FIELD_NAMES)


def test_validate_template_references_allows_frontside_and_conditionals() -> None:
    template = CardTemplate(
        front="{{Word}} {{#IPA}}{{IPA}}{{/IPA}} {{#Image}}{{Image}}{{/Image}}",
        back="{{FrontSide}} {{Definition}}",
        css=".card { overflow-x: hidden; }",
        source_template_name="highlight_card",
    )

    validate_template_references(template, field_names=HIGHLIGHT_EXPORT_CARD_FIELD_NAMES)


def test_load_card_template_routes_highlights_to_highlight_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    template_dir = _write_templates(tmp_path)
    monkeypatch.setattr("multilang.services.card_template_loader.TEMPLATE_ROOT", template_dir)

    template = load_card_template(source_type="kindle-highlights")

    assert template.source_template_name == "highlight_card"
    assert "{{Word}}" in template.front
    assert "{{Translation}}" not in template.front + template.back


def test_load_card_template_routes_word_lists_to_highlight_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    template_dir = _write_templates(tmp_path)
    monkeypatch.setattr("multilang.services.card_template_loader.TEMPLATE_ROOT", template_dir)

    template = load_card_template(source_type="word-list")

    assert template.source_template_name == "highlight_card"
    assert "{{Word}}" in template.front
    assert "{{Definition}}" in template.back
    assert "{{Translation}}" not in template.front + template.back


def test_project_highlight_template_front_contains_prompt_side_content_only() -> None:
    template = load_card_template(source_type="kindle-highlights")

    assert "{{Word}}" in template.front
    assert 'class="word"' in template.front
    assert "{{#IPA}}" in template.front
    assert 'class="ipa"' in template.front
    assert "{{IPA}}" in template.front
    assert "{{/IPA}}" in template.front
    assert "{{word_audio}}" not in template.front
    assert "{{Example Sentence}}" in template.front
    assert "{{sentence_audio}}" in template.front
    assert "{{Image}}" not in template.front
    assert "{{Translation}}" not in template.front + template.back


def test_project_highlight_template_back_reuses_frontside_and_reveals_definition_only() -> None:
    template = load_card_template(source_type="kindle-highlights")
    back_without_frontside = template.back.replace("{{FrontSide}}", "")

    assert "{{FrontSide}}" in template.back
    assert template.back.count('id="answer"') == 1
    assert "Definition" in template.back
    assert "{{Definition}}" in template.back
    assert "{{#Image}}" in template.back
    assert "{{Image}}" in template.back
    assert "{{/Image}}" in template.back
    assert template.back.index('{{Definition}}') < template.back.index('{{Image}}')
    assert "{{word_audio}}" not in back_without_frontside
    assert "{{sentence_audio}}" not in back_without_frontside
    assert "autoplay" not in template.back.lower()
    assert "{{Translation}}" not in template.back


def test_project_highlight_template_definition_is_revealed_as_meaning() -> None:
    template = load_card_template(source_type="kindle-highlights")

    assert '<div class="back-card">' in template.back
    assert '<div class="meaning">{{Definition}}</div>' in template.back
    assert "source.innerHTML" not in template.back
    assert "item.innerHTML" not in template.back


def test_project_highlight_template_css_is_centered_responsive_and_scroll_safe() -> None:
    template = load_card_template(source_type="kindle-highlights")
    css = template.css

    assert ".card" in css
    assert ".back-card" in css
    assert ".back-card > .card" in css
    assert ".word" in css
    assert ".ipa" in css
    assert ".example" in css
    assert ".meaning" in css
    assert ".audio-controls" in css
    assert ".replay-button" in css
    assert ".image-container" in css
    assert ".divider" in css
    assert ".answer-divider" in css
    assert "#4CAF50" in css
    assert "#00BCD4" in css
    assert "#FF5252" in css
    assert "width: min(" in css or "width: 100%" in css
    assert "margin: 0 auto" in css
    assert "overflow-y: auto" in css
    assert "overflow-x: hidden" in css


def test_shared_phoneme_models_keep_contract_and_panel_contained_answer() -> None:
    models = (
        build_russian_phoneme_model(),
        build_polish_phoneme_model(),
        build_greek_phoneme_model(),
    )
    russian = models[0]
    front = russian.templates[0]["qfmt"]
    back = russian.templates[0]["afmt"]

    assert all(tuple(field["name"] for field in model.fields) == PHONEME_FIELD_NAMES for model in models)
    assert all(model.templates == russian.templates for model in models[1:])
    assert all(model.css == russian.css for model in models[1:])
    references = re.findall(r"{{[#/]?([^{}]+)}}", front + back)
    assert references == [
        "Spellings",
        "Sound",
        "letter_audio",
        "Example Word",
        "word_audio",
        "Word Translation",
        "Example Sentence",
        "sentence_audio",
        "Sentence Translation",
        "FrontSide",
        "Sentence Translation",
    ]
    example_panel = _balanced_div(front, class_name="examplePanel")
    assert example_panel.index("{{Example Sentence}}") < example_panel.index("{{sentence_audio}}")
    assert example_panel.index("{{sentence_audio}}") < example_panel.index('id="sentenceTranslation"')
    assert "{{Sentence Translation}}" in example_panel
    assert "(function ()" in back
    assert 'document.getElementById("sentenceTranslation").style.display = "block";' in back
    assert "<noscript>" in back
    assert _last_css_value(russian.css, "--color-page-background") == "#0a1220"
    assert _last_css_value(russian.css, "--color-card-background") == "#0f1b2d"
    assert _last_css_value(russian.css, "--color-text-primary") == "#e8f0fe"
    assert _last_css_value(russian.css, "--color-panel-background") == "#12213a"


def test_mandarin_template_preserves_base_css_and_pedagogical_field_order() -> None:
    from multilang.domain.jobs import SupportedLanguage
    from multilang.services.card_template_loader import load_card_template

    base = load_card_template(source_type="frequency")
    frequency = load_card_template(source_type="frequency", language=SupportedLanguage.ZH)
    word_list = load_card_template(source_type="word-list", language=SupportedLanguage.ZH)

    assert frequency == word_list
    assert frequency.source_template_name == "mandarin_card"
    assert frequency.css.startswith(base.css)
    mandarin_source = (
        Path(__file__).parents[2] / "src" / "multilang" / "templates" / "mandarin_card.md"
    ).read_text(encoding="utf-8")
    css_match = re.search(
        r"## Styling \(CSS\)\s+```css\n(?P<css>.*?)```",
        mandarin_source,
        flags=re.DOTALL,
    )
    assert css_match is not None
    assert frequency.css == f"{base.css}\n\n{css_match.group('css').strip()}"
    references = re.findall(r"{{[#/]?([^{}]+)}}", frequency.front + frequency.back)
    assert references == [
        "word",
        "Pinyin",
        "Pinyin",
        "Pinyin",
        "Traditional",
        "Traditional",
        "Traditional",
        "word_audio",
        "Definitions",
        "Image",
        "Image",
        "Image",
        "Example Sentence",
        "sentence_audio",
        "Sentence Pinyin",
        "Sentence Pinyin",
        "Sentence Pinyin",
        "Traditional Sentence",
        "Traditional Sentence",
        "Traditional Sentence",
        "Translation",
        "FrontSide",
    ]
    assert frequency.front.index("{{word}}") < frequency.front.index("{{Pinyin}}")
    assert frequency.front.index("{{Pinyin}}") < frequency.front.index("{{Traditional}}")
    assert frequency.front.index("{{Example Sentence}}") < frequency.front.index("{{Sentence Pinyin}}")
    assert frequency.front.index("{{Sentence Pinyin}}") < frequency.front.index("{{Traditional Sentence}}")
    assert '{{#Image}}' in frequency.front and '{{/Image}}' in frequency.front
    assert 'id="translation"' in frequency.front
    assert 'style="display:none;"' in frequency.front
    assert 'document.getElementById("translation").style.display = "block";' in frequency.back
    for selector in (".traditional", ".sentencePinyin", ".traditionalSentence"):
        assert selector in frequency.css
        assert f".nightMode {selector}" in frequency.css
    assert ".ipa {" in frequency.css
    assert "color: #7f9bc4;" in frequency.css
    assert ".traditional {\n  color: #93c5fd;" in frequency.css
    assert ".sentencePinyin {\n  color: #7f9bc4;" in frequency.css
    assert ".traditionalSentence {\n  color: #93c5fd;" in frequency.css
    example_panel = _balanced_div(frequency.front, class_name="examplePanel")
    assert example_panel.index("{{Example Sentence}}") < example_panel.index("{{sentence_audio}}")
    assert example_panel.index("{{sentence_audio}}") < example_panel.index("{{Sentence Pinyin}}")
    assert example_panel.index("{{Sentence Pinyin}}") < example_panel.index("{{Traditional Sentence}}")
    assert example_panel.index("{{Traditional Sentence}}") < example_panel.index("{{Translation}}")
    markup = "\n".join((frequency.front, frequency.back, frequency.css)).casefold()
    assert "tone" not in markup
    assert "migaku" not in markup
