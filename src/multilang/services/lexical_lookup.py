"""Cached lexical lookup backed by a local JSON index."""

from __future__ import annotations

import json
from pathlib import Path
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_lexical_key(value: str) -> str:
    """Normalize a lexical term into a stable lookup key."""

    canonical = unicodedata.normalize("NFC", value)
    return " ".join(canonical.split()).casefold()


class LexicalRecord(BaseModel):
    """Small normalized lexical record loaded from cached lexical data."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    term: str = Field(min_length=1)
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    definitions: list[str] = Field(default_factory=list)
    part_of_speech: str | None = None
    sense_id: str | None = Field(default=None, min_length=1)
    usage_register: str | None = Field(
        default=None,
        validation_alias="register",
        serialization_alias="register",
        min_length=1,
    )
    grammar_tags: list[str] = Field(default_factory=list)
    ipa: str | None = None
    source: str = Field(min_length=1, default="manual")

    @field_validator("term", "display_form", "lemma")
    @classmethod
    def stable_text_must_be_nfc(cls, value: str) -> str:
        return unicodedata.normalize("NFC", value)

    @property
    def register(self) -> str | None:
        return self.usage_register


class LexicalLookup:
    """Query per-language cached lexical indexes."""

    def __init__(self, data_dir: str | Path) -> None:
        self._data_dir = Path(data_dir)
        self._cache: dict[str, dict[str, tuple[LexicalRecord, ...]]] = {}

    def has_index(self, *, language_code: str) -> bool:
        """Return whether the runtime index already exists for a language."""

        return self.index_path(language_code=language_code).exists()

    def index_path(self, *, language_code: str) -> Path:
        """Return the deterministic runtime index path for a language."""

        return self._data_dir / language_code / "lexical-index.json"

    def lookup(self, *, language_code: str, term: str) -> LexicalRecord | None:
        """Query the cached index for a normalized term."""

        candidates = self.lookup_candidates(language_code=language_code, term=term)
        return candidates[0] if candidates else None

    def lookup_candidates(
        self,
        *,
        language_code: str,
        term: str,
    ) -> tuple[LexicalRecord, ...]:
        """Return all declared records for a term without selecting a source sense."""

        payload = self._load_index(language_code=language_code)
        if payload is None:
            return ()
        records = payload.get(normalize_lexical_key(term), ())
        self._validate_language_records(language_code=language_code, records=records)
        return records

    def iter_candidates(self, *, language_code: str) -> tuple[LexicalRecord, ...]:
        """Enumerate source records in deterministic key and declared-list order."""

        payload = self._load_index(language_code=language_code)
        if payload is None:
            return ()

        result: list[LexicalRecord] = []
        seen_complete_identities: set[tuple[str, str, str, str | None, str]] = set()
        for normalized_key in sorted(payload):
            records = payload[normalized_key]
            self._validate_language_records(language_code=language_code, records=records)
            for record in records:
                if record.part_of_speech is None or record.sense_id is None:
                    result.append(record)
                    continue
                identity = (
                    unicodedata.normalize("NFC", record.lemma),
                    record.part_of_speech,
                    record.sense_id,
                    record.register,
                    record.source,
                )
                if identity in seen_complete_identities:
                    continue
                seen_complete_identities.add(identity)
                result.append(record)
        return tuple(result)

    def _load_index(
        self,
        *,
        language_code: str,
    ) -> dict[str, tuple[LexicalRecord, ...]] | None:
        cached = self._cache.get(language_code)
        if cached is not None:
            return cached

        index_path = self.index_path(language_code=language_code)
        if not index_path.exists():
            return None
        raw_payload = json.loads(index_path.read_text(encoding="utf-8"))
        if not isinstance(raw_payload, dict):
            raise ValueError("lexical index must contain an object")

        normalized_payload: dict[str, list[LexicalRecord]] = {}
        for raw_key in sorted(raw_payload, key=lambda key: (normalize_lexical_key(key), key)):
            raw_records = raw_payload[raw_key]
            declared_records = raw_records if isinstance(raw_records, list) else [raw_records]
            if not declared_records:
                raise ValueError("lexical index record list must not be empty")
            key = normalize_lexical_key(raw_key)
            normalized_payload.setdefault(key, []).extend(
                LexicalRecord.model_validate(record) for record in declared_records
            )

        payload = {key: tuple(records) for key, records in normalized_payload.items()}
        self._cache[language_code] = payload
        return payload

    @staticmethod
    def _validate_language_records(
        *,
        language_code: str,
        records: tuple[LexicalRecord, ...],
    ) -> None:
        if language_code != "ko":
            return
        if any(record.part_of_speech is None or record.sense_id is None for record in records):
            raise ValueError("Korean lexical records require source-backed POS and sense_id")


__all__ = ["LexicalLookup", "LexicalRecord", "normalize_lexical_key"]
