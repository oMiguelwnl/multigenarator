from __future__ import annotations

from pathlib import Path

import pytest

from multilang.domain.exporting import HIGHLIGHT_EXPORT_CARD_FIELD_NAMES
from multilang.services.card_template_loader import (
    CardTemplate,
    load_card_template,
    validate_template_references,
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
