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
