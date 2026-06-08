"""Classical Latin MVP export row contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


LATIN_EXPORT_FIELD_NAMES: tuple[str, ...] = (
    "SortIndex",
    "Latin Word",
    "Latin Sentence",
    "Lemma",
    "Translation",
    "Sentence Translation",
    "Gramatica",
    "Source",
    "word_audio",
    "sentence_audio",
    "Image",
)
LATIN_NOTE_TYPE_NAME = "Multilang::Classical Latin MVP"
LATIN_DECK_NAME = "Multilang::Classical Latin::MVP 50"


@dataclass(frozen=True)
class LatinExportRow:
    """One learner-facing Classical Latin MVP row in stable Anki field order."""

    sort_index: int
    item_key: str
    latin_word: str
    latin_sentence: str
    lemma: str
    translation: str
    sentence_translation: str
    gramatica: str
    source: str
    word_audio: str
    sentence_audio: str
    image: str = ""

    def __post_init__(self) -> None:
        if self.image != "":
            raise ValueError("Image must remain blank for Latin MVP export rows")
        if self.sort_index < 1:
            raise ValueError("sort_index must be positive")
        for field_name in (
            "item_key",
            "latin_word",
            "latin_sentence",
            "lemma",
            "translation",
            "sentence_translation",
            "gramatica",
            "source",
            "word_audio",
            "sentence_audio",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must not be blank")

    def ordered_field_mapping(self) -> dict[str, object]:
        """Return the Anki-ready mapping in the stable Latin field order."""

        return {
            "SortIndex": self.sort_index,
            "Latin Word": self.latin_word,
            "Latin Sentence": self.latin_sentence,
            "Lemma": self.lemma,
            "Translation": self.translation,
            "Sentence Translation": self.sentence_translation,
            "Gramatica": self.gramatica,
            "Source": self.source,
            "word_audio": self.word_audio,
            "sentence_audio": self.sentence_audio,
            "Image": self.image,
        }


@dataclass(frozen=True)
class LatinExportBundle:
    """Latin export rows plus media references keyed by sound tags."""

    rows: list[LatinExportRow]
    media_index: dict[str, Path]


__all__ = [
    "LATIN_DECK_NAME",
    "LATIN_EXPORT_FIELD_NAMES",
    "LATIN_NOTE_TYPE_NAME",
    "LatinExportBundle",
    "LatinExportRow",
]
