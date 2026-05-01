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
    part_of_speech: str | None = None
    grammar_tags: list[str] = Field(default_factory=list)
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

    def has_index(self, *, language_code: str) -> bool:
        """Return whether the runtime index already exists for a language."""

        return self.index_path(language_code=language_code).exists()

    def index_path(self, *, language_code: str) -> Path:
        """Return the deterministic runtime index path for a language."""

        return self._index_path(language_code)

    def ensure_index(
        self,
        *,
        language_code: str,
        source_path: str | Path | None = None,
        force_refresh: bool = False,
    ) -> Path | None:
        """Return an existing index or build one from an explicit source archive."""

        if self.has_index(language_code=language_code) and not force_refresh:
            return self.index_path(language_code=language_code)
        if source_path is None:
            return None
        return self.build_index(
            language_code=language_code,
            source_path=source_path,
            force_refresh=force_refresh,
        )

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
            part_of_speech=self._part_of_speech_from_payload(payload),
            grammar_tags=self._grammar_tags_from_payload(payload),
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
        selected = _select_best_definition(definitions)
        return [selected] if selected else []

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



    @staticmethod
    def _part_of_speech_from_payload(payload: dict[str, object]) -> str | None:
        value = str(payload.get("pos") or "").strip()
        return value or None

    @staticmethod
    def _grammar_tags_from_payload(payload: dict[str, object]) -> list[str]:
        tags: list[str] = []
        for tag in _payload_tags(payload):
            if tag in _IGNORED_GRAMMAR_TAGS or tag in tags:
                continue
            tags.append(tag)
        return tags


_IGNORED_GRAMMAR_TAGS = {
    "abbreviation",
    "alt-of",
    "alternative",
    "canonical",
    "form-of",
    "romanization",
    "table-tags",
}


def _payload_tags(payload: dict[str, object]) -> list[str]:
    tags: list[str] = []
    for section_name in ("forms", "senses"):
        section = payload.get(section_name)
        if not isinstance(section, list):
            continue
        for item in section:
            if not isinstance(item, dict):
                continue
            item_tags = item.get("tags")
            if not isinstance(item_tags, list):
                continue
            for tag in item_tags:
                tag_value = str(tag).strip().casefold()
                if tag_value and tag_value not in tags:
                    tags.append(tag_value)
    return tags


def _select_best_definition(definitions: list[str]) -> str | None:
    candidates = [" ".join(definition.split()) for definition in definitions if definition.strip()]
    if not candidates:
        return None
    return max(candidates, key=_definition_quality_score)



def _definition_quality_score(definition: str) -> int:
    score = min(len(definition), 120)
    if " " in definition:
        score += 30
    if 25 <= len(definition) <= 180:
        score += 20
    return score


__all__ = ["KaikkiLookup", "KaikkiRecord", "normalize_lexical_key"]
