"""Cached Kaikki lookup backed by a local JSON index."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

from pydantic import BaseModel, Field


def normalize_lexical_key(value: str) -> str:
    """Normalize a lexical term into a stable lookup key."""

    return " ".join(value.split()).casefold()


class KaikkiRecord(BaseModel):
    """Small normalized lexical record loaded from Kaikki data."""

    term: str = Field(min_length=1)
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    definitions: list[str] = Field(default_factory=list)
    ipa: str | None = None
    source: str = Field(min_length=1, default="kaikki")


class KaikkiLookup:
    """Build and query per-language cached Kaikki indexes."""

    def __init__(self, data_dir: str | Path) -> None:
        self._data_dir = Path(data_dir)
        self._cache: dict[str, dict[str, dict[str, object]]] = {}

    def build_index(
        self,
        *,
        language_code: str,
        source_path: str | Path,
        force_refresh: bool = False,
    ) -> Path:
        """Build or refresh a small local JSON index from a Kaikki JSONL gzip extract."""

        index_path = self._index_path(language_code)
        if index_path.exists() and not force_refresh:
            return index_path

        index_path.parent.mkdir(parents=True, exist_ok=True)
        records: dict[str, dict[str, object]] = {}
        with gzip.open(Path(source_path), "rt", encoding="utf-8") as handle:
            for line in handle:
                payload = json.loads(line)
                record = self._record_from_payload(payload)
                if record is None:
                    continue
                records[normalize_lexical_key(record.term)] = record.model_dump()

        index_path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self._cache[language_code] = records
        return index_path

    def lookup(self, *, language_code: str, term: str) -> KaikkiRecord | None:
        """Query the cached index for a normalized term."""

        index_path = self._index_path(language_code)
        if not index_path.exists():
            return None

        payload = self._cache.get(language_code)
        if payload is None:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
            self._cache[language_code] = payload
        record = payload.get(normalize_lexical_key(term))
        if record is None:
            return None
        return KaikkiRecord.model_validate(record)

    def _index_path(self, language_code: str) -> Path:
        return self._data_dir / language_code / "kaikki-index.json"

    def _record_from_payload(self, payload: dict[str, object]) -> KaikkiRecord | None:
        lemma = str(payload.get("word") or "").strip()
        if not lemma:
            return None

        definitions = self._definitions_from_payload(payload)
        display_form = self._display_form_from_payload(payload, lemma)
        ipa = self._ipa_from_payload(payload)
        return KaikkiRecord(
            term=display_form,
            display_form=display_form,
            lemma=lemma,
            definitions=definitions,
            ipa=ipa,
        )

    @staticmethod
    def _display_form_from_payload(payload: dict[str, object], lemma: str) -> str:
        forms = payload.get("forms")
        if isinstance(forms, list):
            for form in forms:
                if isinstance(form, dict):
                    form_value = str(form.get("form") or "").strip()
                    if form_value:
                        return form_value
        return lemma

    @staticmethod
    def _definitions_from_payload(payload: dict[str, object]) -> list[str]:
        definitions: list[str] = []
        senses = payload.get("senses")
        if not isinstance(senses, list):
            return definitions
        for sense in senses:
            if not isinstance(sense, dict):
                continue
            glosses = sense.get("glosses")
            if not isinstance(glosses, list):
                continue
            for gloss in glosses:
                gloss_text = str(gloss).strip()
                if gloss_text and gloss_text not in definitions:
                    definitions.append(gloss_text)
        return definitions

    @staticmethod
    def _ipa_from_payload(payload: dict[str, object]) -> str | None:
        sounds = payload.get("sounds")
        if not isinstance(sounds, list):
            return None
        for sound in sounds:
            if not isinstance(sound, dict):
                continue
            ipa = sound.get("ipa")
            if isinstance(ipa, str) and ipa.strip():
                return ipa.strip()
        return None


__all__ = ["KaikkiLookup", "KaikkiRecord", "normalize_lexical_key"]
