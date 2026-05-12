"""Cached lexical lookup backed by a local JSON index."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


def normalize_lexical_key(value: str) -> str:
    """Normalize a lexical term into a stable lookup key."""

    return " ".join(value.split()).casefold()


class LexicalRecord(BaseModel):
    """Small normalized lexical record loaded from cached lexical data."""

    term: str = Field(min_length=1)
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    definitions: list[str] = Field(default_factory=list)
    part_of_speech: str | None = None
    grammar_tags: list[str] = Field(default_factory=list)
    ipa: str | None = None
    source: str = Field(min_length=1, default="manual")


class LexicalLookup:
    """Query per-language cached lexical indexes."""

    def __init__(self, data_dir: str | Path) -> None:
        self._data_dir = Path(data_dir)
        self._cache: dict[str, dict[str, dict[str, object]]] = {}

    def has_index(self, *, language_code: str) -> bool:
        """Return whether the runtime index already exists for a language."""

        return self.index_path(language_code=language_code).exists()

    def index_path(self, *, language_code: str) -> Path:
        """Return the deterministic runtime index path for a language."""

        return self._data_dir / language_code / "lexical-index.json"

    def lookup(self, *, language_code: str, term: str) -> LexicalRecord | None:
        """Query the cached index for a normalized term."""

        index_path = self.index_path(language_code=language_code)
        if not index_path.exists():
            return None

        payload = self._cache.get(language_code)
        if payload is None:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
            self._cache[language_code] = payload
        record = payload.get(normalize_lexical_key(term))
        if record is None:
            return None
        return LexicalRecord.model_validate(record)


__all__ = ["LexicalLookup", "LexicalRecord", "normalize_lexical_key"]
