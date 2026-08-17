"""Language-neutral model and note mechanics for nine-field phoneme decks."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import re

import genanki


PHONEME_FIELD_NAMES = (
    "Spellings",
    "Sound",
    "letter_audio",
    "Example Word",
    "word_audio",
    "Word Translation",
    "Example Sentence",
    "sentence_audio",
    "Sentence Translation",
)

_TEMPLATE_SECTION_RE = re.compile(
    r"## Front Template\s+```html\n(?P<front>.*?)```.*?"
    r"## Back Template\s+```html\n(?P<back>.*?)```.*?"
    r"## Styling \(CSS\)\s+```css\n(?P<css>.*?)```",
    re.DOTALL,
)
_ANKI_REFERENCE_RE = re.compile(r"{{\s*[#/^]?(?P<name>[^{}]+?)\s*}}")
_ADDITIONAL_FONT_CSS_RE = re.compile(
    r"(?:\s*\.[A-Za-z][A-Za-z0-9_-]*"
    r"(?:\s*,\s*\.[A-Za-z][A-Za-z0-9_-]*)*"
    r"\s*\{\s*font-family\s*:\s*[^{};]+;\s*\}\s*)+",
    re.IGNORECASE,
)
_ALLOWED_NON_FIELD_REFERENCES = frozenset({"FrontSide"})


@dataclass(frozen=True)
class PhonemeCard:
    sort_index: int
    letters: str
    ipa: str
    example_word: str
    example_word_translation: str
    example_sentence: str
    example_sentence_translation: str
    letter_audio: str = ""
    word_audio: str = ""
    sentence_audio: str = ""


class PhonemeNote(genanki.Note):
    @property
    def guid(self) -> str:
        return self._multilang_guid  # type: ignore[attr-defined]


def build_phoneme_model(
    *,
    model_id: int,
    note_type_name: str,
    additional_css: str = "",
) -> genanki.Model:
    """Build the shared nine-field model with optional font-only additive CSS."""

    template = _load_phoneme_template()
    _validate_template_references(template)
    _validate_additional_css(additional_css)
    css = template["css"]
    if additional_css:
        css = f"{css}\n\n{additional_css}"
    return genanki.Model(
        model_id,
        note_type_name,
        fields=[{"name": field_name} for field_name in PHONEME_FIELD_NAMES],
        templates=[
            {
                "name": "Phoneme Card",
                "qfmt": template["front"],
                "afmt": template["back"],
            }
        ],
        css=css,
    )


def build_phoneme_note(
    card: PhonemeCard,
    *,
    model: genanki.Model,
    guid: str | None = None,
) -> genanki.Note:
    """Map a phoneme card into the shared field order and inject its stable GUID."""

    fields = phoneme_card_fields(card)
    resolved_guid = guid
    if resolved_guid is None:
        resolved_guid = getattr(card, "guid", None)
    if resolved_guid is None:
        resolved_guid = genanki.guid_for(*fields)
    note = PhonemeNote(model=model, fields=fields)
    note._multilang_guid = resolved_guid  # type: ignore[attr-defined]
    return note


def phoneme_card_fields(card: PhonemeCard) -> list[str]:
    """Return learner values in the exact shared nine-field order."""

    values = {
        "Spellings": card.letters,
        "Sound": card.ipa,
        "letter_audio": card.letter_audio,
        "Example Word": card.example_word,
        "word_audio": card.word_audio,
        "Word Translation": card.example_word_translation,
        "Example Sentence": card.example_sentence,
        "sentence_audio": card.sentence_audio,
        "Sentence Translation": card.example_sentence_translation,
    }
    return [values[field_name] for field_name in PHONEME_FIELD_NAMES]


def _load_phoneme_template() -> dict[str, str]:
    template_path = files("multilang").joinpath("templates", "russian_phoneme_card.md")
    content = template_path.read_text(encoding="utf-8")
    match = _TEMPLATE_SECTION_RE.search(content)
    if match is None:
        raise ValueError(f"unable to parse phoneme template from {template_path}")
    return {name: match.group(name).strip() for name in ("front", "back", "css")}


def _validate_template_references(template: dict[str, str]) -> None:
    allowed = set(PHONEME_FIELD_NAMES) | _ALLOWED_NON_FIELD_REFERENCES
    invalid: list[str] = []
    for match in _ANKI_REFERENCE_RE.finditer(f'{template["front"]}\n{template["back"]}'):
        reference = match.group("name").strip().rsplit(":", 1)[-1].strip()
        if reference not in allowed:
            invalid.append(reference)
    if invalid:
        invalid_names = ", ".join(dict.fromkeys(invalid))
        raise ValueError(f"phoneme template references unknown fields: {invalid_names}")


def _validate_additional_css(additional_css: str) -> None:
    if additional_css and _ADDITIONAL_FONT_CSS_RE.fullmatch(additional_css) is None:
        raise ValueError(
            "additional phoneme CSS must contain class-scoped font-family declarations only"
        )


__all__ = [
    "PHONEME_FIELD_NAMES",
    "PhonemeCard",
    "PhonemeNote",
    "build_phoneme_model",
    "build_phoneme_note",
    "phoneme_card_fields",
]
