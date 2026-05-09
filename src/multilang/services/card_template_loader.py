"""Source-profile-aware Anki card template loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from multilang.domain.exporting import export_field_names_for_source_type
from multilang.domain.source_profiles import get_source_profile

PROJECT_ROOT = Path(__file__).resolve().parents[3]

_SECTION_RE = re.compile(
    r"## Front Template\s+```html\n(?P<front>.*?)```.*?"
    r"## Back Template\s+```html\n(?P<back>.*?)```.*?"
    r"## Styling \(CSS\)\s+```css\n(?P<css>.*?)```",
    re.DOTALL,
)
_ANKI_REFERENCE_RE = re.compile(r"{{\s*(?P<prefix>[#/^]?)(?P<name>[^{}]+?)\s*}}")
_ALLOWED_NON_FIELD_HELPERS = frozenset({"FrontSide"})
_TEMPLATE_FILES = {
    "normal_card": Path("templates/normal_card.md"),
    "highlight_card": Path("templates/highlight_card.md"),
}


@dataclass(frozen=True, slots=True)
class CardTemplate:
    front: str
    back: str
    css: str
    source_template_name: str


def load_card_template(source_type: str) -> CardTemplate:
    """Load and validate the card template selected by a source profile."""

    profile = get_source_profile(source_type)
    template_path = PROJECT_ROOT / _TEMPLATE_FILES[profile.template_name]
    content = template_path.read_text(encoding="utf-8")
    template = _parse_card_template(
        content,
        template_path=template_path,
        source_template_name=profile.template_name,
    )
    validate_template_references(
        template,
        field_names=export_field_names_for_source_type(profile.source_type),
    )
    return template


def validate_template_references(template: CardTemplate, field_names: tuple[str, ...]) -> None:
    """Fail closed if a template references fields outside the exported note schema."""

    allowed_fields = set(field_names)
    invalid_references: list[str] = []
    for reference in _iter_template_references(template):
        if reference in allowed_fields or reference in _ALLOWED_NON_FIELD_HELPERS:
            continue
        invalid_references.append(reference)

    if invalid_references:
        invalid = ", ".join(dict.fromkeys(invalid_references))
        allowed = ", ".join((*field_names, *_ALLOWED_NON_FIELD_HELPERS))
        raise ValueError(
            "card template references fields that are not exported: "
            f"{invalid}; allowed references: {allowed}"
        )


def _parse_card_template(
    content: str, *, template_path: Path, source_template_name: str
) -> CardTemplate:
    match = _SECTION_RE.search(content)
    if match is None:
        raise ValueError(f"unable to parse card template from {template_path}")
    return CardTemplate(
        front=match.group("front").strip(),
        back=match.group("back").strip(),
        css=match.group("css").strip(),
        source_template_name=source_template_name,
    )


def _iter_template_references(template: CardTemplate) -> list[str]:
    markup = "\n".join((template.front, template.back))
    references: list[str] = []
    for match in _ANKI_REFERENCE_RE.finditer(markup):
        reference = match.group("name").strip()
        if reference:
            references.append(reference)
    return references


__all__ = [
    "CardTemplate",
    "load_card_template",
    "validate_template_references",
]
