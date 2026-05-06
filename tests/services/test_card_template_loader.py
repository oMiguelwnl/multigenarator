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
{{Front of Card}} {{Translation}} {{#Image}}{{Image}}{{/Image}}
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
{{Word}} {{#IPA}}{{IPA}}{{/IPA}} {{word_audio}} {{Example Sentence}} {{sentence_audio}}
{{#Image}}{{Image}}{{/Image}}
```

## Back Template

```html
{{FrontSide}}<hr id="answer"><div>Definition</div>{{Definition}}
```

## Styling (CSS)

```css
.highlight-card { color: var(--multilang-blue); }
```
"""


def _write_templates(root: Path) -> None:
    (root / "CARD_TEMPLATE.md").write_text(NORMAL_TEMPLATE, encoding="utf-8")
    (root / "HIGHLIGHT_CARD_TEMPLATE.md").write_text(HIGHLIGHT_TEMPLATE, encoding="utf-8")


def test_load_card_template_keeps_normal_template_and_translation_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_templates(tmp_path)
    monkeypatch.setattr("multilang.services.card_template_loader.PROJECT_ROOT", tmp_path)

    template = load_card_template(source_type="frequency")

    assert template.source_template_name == "normal_card"
    assert "{{Translation}}" in template.front
    assert "{{FrontSide}}" in template.back
    validate_template_references(
        template,
        field_names=(
            "SortIndex",
            "word",
            "Front of Card",
            "IPA",
            "Definitions",
            "Example Sentence",
            "Translation",
            "word_audio",
            "sentence_audio",
            "Image",
        ),
    )


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
    _write_templates(tmp_path)
    monkeypatch.setattr("multilang.services.card_template_loader.PROJECT_ROOT", tmp_path)

    template = load_card_template(source_type="kindle-highlights")

    assert template.source_template_name == "highlight_card"
    assert "{{Word}}" in template.front
    assert "{{Translation}}" not in template.front + template.back


def test_project_highlight_template_front_contains_prompt_side_content_only() -> None:
    template = load_card_template(source_type="kindle-highlights")

    assert "{{Word}}" in template.front
    assert "{{#IPA}}{{IPA}}{{/IPA}}" in template.front
    assert "{{word_audio}}" in template.front
    assert "{{Example Sentence}}" in template.front
    assert "{{sentence_audio}}" in template.front
    assert "{{#Image}}" in template.front
    assert "{{Image}}" in template.front
    assert "{{/Image}}" in template.front
    assert "{{Translation}}" not in template.front + template.back


def test_project_highlight_template_back_reuses_frontside_and_reveals_definition_only() -> None:
    template = load_card_template(source_type="kindle-highlights")
    back_without_frontside = template.back.replace("{{FrontSide}}", "")

    assert "{{FrontSide}}" in template.back
    assert template.back.count('id="answer"') == 1
    assert "Definition" in template.back
    assert "{{Definition}}" in template.back
    assert "{{word_audio}}" not in back_without_frontside
    assert "{{sentence_audio}}" not in back_without_frontside
    assert "autoplay" not in template.back.lower()
    assert "{{Translation}}" not in template.back


def test_project_highlight_template_definition_list_treats_items_as_text() -> None:
    template = load_card_template(source_type="kindle-highlights")
    malicious_definition = "<img src=x onerror=alert(1)>"

    assert malicious_definition.startswith("<img")
    assert "source.innerText" in template.back
    assert "item.textContent = definition" in template.back
    assert "source.innerHTML" not in template.back
    assert "item.innerHTML" not in template.back


def test_project_highlight_template_css_is_centered_responsive_and_scroll_safe() -> None:
    template = load_card_template(source_type="kindle-highlights")
    css = template.css

    assert "--multilang-blue" in css
    assert "#2563eb" in css or "#1d4ed8" in css
    assert "max-width" in css
    assert "width: min(" in css or "width: 100%" in css
    assert "margin: 0 auto" in css
    assert "overflow-y: auto" in css
    assert "overflow-x: hidden" in css
