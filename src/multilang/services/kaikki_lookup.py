"""Cached Kaikki lookup backed by a local JSON index."""

from __future__ import annotations

import gzip
import json
import re
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
        record_scores: dict[str, int] = {}
        with gzip.open(Path(source_path), "rt", encoding="utf-8") as handle:
            for line in handle:
                payload = json.loads(line)
                record = self._record_from_payload(payload)
                if record is None:
                    continue
                key = normalize_lexical_key(record.term)
                score = self._payload_score(payload=payload, record=record)
                if key in records and score <= record_scores[key]:
                    continue
                records[key] = record.model_dump()
                record_scores[key] = score

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
            term=lemma,
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
                    if not form_value:
                        continue
                    tags = form.get("tags")
                    tag_values = {str(tag) for tag in tags} if isinstance(tags, list) else set()
                    if "romanization" in tag_values:
                        continue
                    if "canonical" in tag_values:
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
                gloss_text = _clean_definition_text(str(gloss))
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

    @staticmethod
    def _payload_score(*, payload: dict[str, object], record: KaikkiRecord) -> int:
        score = 0
        if any(_is_substantive_definition(definition) for definition in record.definitions):
            score += 50
        else:
            score -= 80

        pos = str(payload.get("pos") or "")
        if pos in _PREFERRED_PARTS_OF_SPEECH:
            score += _PREFERRED_PARTS_OF_SPEECH[pos]
        if pos in {"character", "symbol"}:
            score -= 15

        word = str(payload.get("word") or "")
        if word and word == word.casefold():
            score += 5
        elif word:
            score -= 5

        tags = _sense_tags(payload)
        if tags & {"form-of", "alt-of", "abbreviation"}:
            score -= 40
        return score


_PREFERRED_PARTS_OF_SPEECH = {
    "prep": 30,
    "postp": 30,
    "conj": 28,
    "particle": 26,
    "pron": 24,
    "det": 22,
    "num": 20,
    "adv": 18,
    "verb": 16,
    "noun": 14,
    "proper": 12,
    "adj": 12,
    "interj": 8,
}

_RELATION_PREFIX_RE = re.compile(
    r"^(?:abbreviation|acronym|alternative form|alternative spelling|archaic spelling|"
    r"clipping|initialism|misspelling|obsolete spelling|pre-1918 spelling|"
    r"romanization|same as|superseded spelling|transliteration)\b"
)
_LETTER_DEFINITION_RE = re.compile(r"\bletter of (?:the )?.*alphabet\b")
_MAX_CARD_DEFINITION_CHARS = 180

_FORM_OF_TERMS = {
    "ablative",
    "accusative",
    "active",
    "adverbial",
    "animate",
    "aorist",
    "comparative",
    "conditional",
    "dative",
    "definite",
    "feminine",
    "first",
    "form",
    "future",
    "genitive",
    "gerund",
    "imperative",
    "imperfect",
    "imperfective",
    "indicative",
    "infinitive",
    "instrumental",
    "locative",
    "masculine",
    "neuter",
    "nominative",
    "participle",
    "passive",
    "past",
    "perfect",
    "perfective",
    "person",
    "plural",
    "prepositional",
    "present",
    "second",
    "singular",
    "subjunctive",
    "superlative",
    "third",
    "vocative",
}

_IGNORED_GRAMMAR_TAGS = {
    "abbreviation",
    "alt-of",
    "alternative",
    "canonical",
    "form-of",
    "romanization",
    "table-tags",
}


def _sense_tags(payload: dict[str, object]) -> set[str]:
    tags: set[str] = set()
    senses = payload.get("senses")
    if not isinstance(senses, list):
        return tags
    for sense in senses:
        if not isinstance(sense, dict):
            continue
        sense_tags = sense.get("tags")
        if isinstance(sense_tags, list):
            tags.update(str(tag) for tag in sense_tags)
    return tags


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


def _is_substantive_definition(definition: str) -> bool:
    normalized = " ".join(definition.casefold().split())
    if not normalized or re.fullmatch(r"\[[^\]]+\]", normalized):
        return False
    if _LETTER_DEFINITION_RE.search(normalized):
        return False
    if _RELATION_PREFIX_RE.match(normalized):
        return False

    before_of, separator, _ = normalized.partition(" of ")
    if separator:
        terms = set(re.findall(r"[a-z]+", before_of))
        if terms and terms.issubset(_FORM_OF_TERMS):
            return False
    return True


def _clean_definition_text(value: str) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) <= _MAX_CARD_DEFINITION_CHARS:
        return cleaned

    for separator in (". ", "; "):
        first_segment = cleaned.split(separator, 1)[0].strip()
        if 20 <= len(first_segment) <= _MAX_CARD_DEFINITION_CHARS:
            return first_segment

    return cleaned[:_MAX_CARD_DEFINITION_CHARS].rsplit(" ", 1)[0].strip() + "..."


def _select_best_definition(definitions: list[str]) -> str | None:
    cleaned = [_clean_definition_text(definition) for definition in definitions]
    candidates = [definition for definition in cleaned if definition]
    substantive = [definition for definition in candidates if _is_substantive_definition(definition)]
    if substantive:
        return max(substantive, key=_definition_quality_score)
    return candidates[0] if candidates else None


def _definition_quality_score(definition: str) -> int:
    length = len(definition)
    score = min(length, 120)
    if " " in definition:
        score += 30
    if any(separator in definition for separator in (";", ",", " or ")):
        score += 10
    if 25 <= length <= _MAX_CARD_DEFINITION_CHARS:
        score += 20
    if length < 12:
        score -= 20
    return score


__all__ = ["KaikkiLookup", "KaikkiRecord", "normalize_lexical_key"]
