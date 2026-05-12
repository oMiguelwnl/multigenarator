"""Trust-first lexical grounding for frequency and custom-list inputs."""

from __future__ import annotations

import re
from html import escape
from pathlib import Path
from typing import Protocol

from multilang.domain.highlights import HighlightCandidate
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import (
    DefinitionRecord,
    GroundingStatus,
    LexicalCardCandidate,
    LexicalProvenance,
    PronunciationRecord,
    policy_for_language,
)
from multilang.services.lexical_lookup import LexicalLookup, LexicalRecord, normalize_lexical_key
from multilang.services.provider_pronunciation_adapters import PronunciationGenerationRequest
from multilang.services.text_generation import DefinitionGenerationRequest, DefinitionGenerationResult
from multilang.services.word_list_parser import ParsedWordListItem


def build_lexical_grounding_service(lexicon_data_dir: str | Path) -> "LexicalGroundingService":
    """Create the runtime grounding service backed by the cached lexical lookup."""

    return LexicalGroundingService(lookup=LexicalLookup(data_dir=lexicon_data_dir))


class PronunciationGenerator(Protocol):
    def generate_pronunciation(self, request: PronunciationGenerationRequest) -> object: ...


class DefinitionGenerator(Protocol):
    def generate_definition(self, request: DefinitionGenerationRequest) -> DefinitionGenerationResult: ...


class LexicalGroundingService:
    """Ground parsed lexical inputs against authoritative cached lookups."""

    def __init__(
        self,
        lookup: object,
        pronunciation_generator: PronunciationGenerator | None = None,
        definition_generator: DefinitionGenerator | None = None,
    ) -> None:
        self._lookup = lookup
        self._pronunciation_generator = pronunciation_generator
        self._definition_generator = definition_generator

    def ground_word_list_item(
        self,
        *,
        language: SupportedLanguage,
        item: ParsedWordListItem,
    ) -> LexicalCardCandidate:
        record = self._lookup_record(language=language, term=item.item_key)
        if record is None:
            return self._pending_candidate(language=language, item=item)
        candidate = self._grounded_candidate(
            language=language,
            submitted_form=item.submitted_form,
            display_form=item.display_form,
            record=record,
            definition_language=language.value,
        )
        return candidate.model_copy(
            update={
                "definition_language": language.value,
                "translation_target_language": language.value,
            }
        )

    def ground_frequency_candidate(
        self,
        *,
        language: SupportedLanguage,
        candidate: LexicalCardCandidate,
    ) -> LexicalCardCandidate:
        record = self._lookup_record(language=language, term=candidate.lemma_key)
        if record is None:
            return self._backfill_required_candidate(
                candidate,
                warning_detail=f"no authoritative lexical match for '{candidate.lemma}'",
            )
        if not _is_frequency_card_worthy(record, candidate=candidate, language=language):
            return self._backfill_required_candidate(
                candidate,
                warning_detail=f"lexical match for '{candidate.lemma}' is not a primary card entry",
            )

        grounded = self._grounded_candidate(
            language=language,
            submitted_form=candidate.submitted_form,
            display_form=candidate.display_form,
            record=record,
        )
        return grounded.model_copy(
            update={
                "frequency_rank": candidate.frequency_rank,
                "frequency_level": candidate.frequency_level,
            }
        )

    def ground_highlight_candidate(
        self,
        *,
        language: SupportedLanguage,
        candidate: HighlightCandidate,
    ) -> LexicalCardCandidate:
        record = self._lookup_record(language=language, term=candidate.lemma_key)
        if record is None:
            policy = policy_for_language(language)
            return LexicalCardCandidate(
                submitted_form=candidate.display_form,
                display_form=candidate.display_form,
                lemma=candidate.display_form,
                lemma_key=candidate.lemma_key,
                definition_language=policy.definition_language,
                translation_target_language=policy.translation_target_language,
                grounding_status=GroundingStatus.INSUFFICIENT,
                warning_code="highlight_grounding_missing",
                warning_detail="no authoritative lexical match for highlight candidate",
                provenance=LexicalProvenance(source="kindle_highlight"),
            )
        return self._grounded_candidate(
            language=language,
            submitted_form=candidate.display_form,
            display_form=candidate.display_form,
            record=record,
            definition_language=language.value,
        )

    def _lookup_record(self, *, language: SupportedLanguage, term: str) -> LexicalRecord | None:
        return self._lookup.lookup(language_code=language.value, term=term)

    def _grounded_candidate(
        self,
        *,
        language: SupportedLanguage,
        submitted_form: str,
        display_form: str,
        record: LexicalRecord,
        definition_language: str | None = None,
    ) -> LexicalCardCandidate:
        policy = policy_for_language(language)
        resolved_definition_language = definition_language or policy.definition_language
        learner_display_form = self._select_display_form(default=display_form, record=record)
        definition_result = self._generate_definition(
            display_form=learner_display_form,
            lemma=record.lemma,
            target_language=resolved_definition_language,
            part_of_speech=record.part_of_speech,
        )
        definitions_html = definition_result.definitions_html if definition_result is not None else None
        ipa = record.ipa
        spoken_form: str | None = learner_display_form if record.ipa else None
        pronunciation_source = record.source if record.ipa else f"{record.source}_missing"
        notes: list[str] = []
        if record.ipa is None:
            notes.append("authoritative IPA missing in lexical source")
        if self._pronunciation_generator is not None and record.ipa is None:
            pronunciation = self._pronunciation_generator.generate_pronunciation(
                PronunciationGenerationRequest(
                    target_language=language.value,
                    display_form=learner_display_form,
                    lemma=record.lemma,
                    definitions_html=definitions_html,
                )
            )
            ipa = str(getattr(pronunciation, "ipa")).strip()
            spoken_form = str(getattr(pronunciation, "spoken_form")).strip()
            pronunciation_source = str(
                getattr(pronunciation, "provenance", {}).get(
                    "source", "provider-pronunciation-generator"
                )
            )

        return LexicalCardCandidate(
            submitted_form=submitted_form,
            display_form=learner_display_form,
            lemma=record.lemma,
            lemma_key=normalize_lexical_key(record.lemma),
            definitions_html=definitions_html,
            definition_language=resolved_definition_language,
            ipa=ipa,
            spoken_form=spoken_form,
            translation_target_language=policy.translation_target_language,
            grounding_status=GroundingStatus.GROUNDED,
            provenance=LexicalProvenance(
                source=record.source,
                definition=(
                    DefinitionRecord(
                        source=str(definition_result.provenance.get("source", "definition-generator")),
                        value=definitions_html,
                        fallback_used=False,
                    )
                    if definition_result is not None
                    else None
                ),
                pronunciation=PronunciationRecord(
                    source=pronunciation_source,
                    value=ipa,
                    authoritative=True,
                ),
                notes=notes,
            ),
        )

    def _generate_definition(
        self,
        *,
        display_form: str,
        lemma: str,
        target_language: str,
        part_of_speech: str | None,
    ) -> DefinitionGenerationResult | None:
        if self._definition_generator is None:
            return None
        return self._definition_generator.generate_definition(
            DefinitionGenerationRequest(
                display_form=display_form,
                lemma=lemma,
                target_language=target_language,
                part_of_speech=part_of_speech,
            )
        )

    def _pending_candidate(
        self,
        *,
        language: SupportedLanguage,
        item: ParsedWordListItem,
    ) -> LexicalCardCandidate:
        return LexicalCardCandidate(
            submitted_form=item.submitted_form,
            display_form=item.display_form,
            lemma=item.display_form,
            lemma_key=item.item_key,
            definition_language=language.value,
            translation_target_language=language.value,
            grounding_status=GroundingStatus.PENDING,
            warning_code="lexical_lookup_missing",
            warning_detail=(
                f"no authoritative lexical match for '{item.display_form}' from word-list line "
                f"{item.line_number}"
            ),
            provenance=LexicalProvenance(source="word_list", notes=["custom word retained for later review"]),
        )

    @staticmethod
    def _backfill_required_candidate(
        candidate: LexicalCardCandidate,
        *,
        warning_detail: str,
    ) -> LexicalCardCandidate:
        return candidate.model_copy(
            update={
                "grounding_status": GroundingStatus.BACKFILL_REQUIRED,
                "warning_code": "backfill_required",
                "warning_detail": warning_detail,
                "provenance": LexicalProvenance(
                    source=candidate.provenance.source,
                    notes=["frequency candidate requires lexical backfill"],
                ),
            }
        )

    @staticmethod
    def _select_display_form(*, default: str, record: LexicalRecord) -> str:
        candidate = record.display_form.strip()
        if not candidate:
            return default
        if candidate.casefold() != record.lemma.casefold():
            return candidate
        return default

    @staticmethod
    def _format_definitions(
        definitions: list[str],
        *,
        part_of_speech: str | None = None,
    ) -> str | None:
        primary_definition = _select_primary_definition(definitions)
        if primary_definition is None:
            return None
        formatted = _format_definition_text(
            primary_definition,
            part_of_speech=part_of_speech,
        )
        return escape(formatted)


_PART_OF_SPEECH_LABELS = {
    "adj": "adjective",
    "adjective": "adjective",
    "adv": "adverb",
    "adverb": "adverb",
    "article": "article",
    "aux": "auxiliary verb",
    "conj": "conjunction",
    "conjunction": "conjunction",
    "det": "determiner",
    "determiner": "determiner",
    "interj": "interjection",
    "interjection": "interjection",
    "noun": "noun",
    "num": "numeral",
    "numeral": "numeral",
    "particle": "particle",
    "postp": "postposition",
    "prep": "preposition",
    "preposition": "preposition",
    "pron": "pronoun",
    "pronoun": "pronoun",
    "proper": "proper noun",
    "proper noun": "proper noun",
    "verb": "verb",
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


def _is_frequency_card_worthy(
    record: LexicalRecord,
    *,
    candidate: LexicalCardCandidate,
    language: SupportedLanguage,
) -> bool:
    if (
        language is SupportedLanguage.RU
        and candidate.submitted_form == candidate.submitted_form.casefold()
        and record.lemma != record.lemma.casefold()
    ):
        return False
    return True


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


def _select_primary_definition(definitions: list[str]) -> str | None:
    fallback: str | None = None
    for definition in definitions:
        cleaned = _clean_definition_text(definition)
        if not cleaned:
            continue
        fallback = fallback or cleaned
        if _is_substantive_definition(cleaned):
            return cleaned
    return fallback


def _format_definition_text(
    meaning: str,
    *,
    part_of_speech: str | None,
) -> str:
    label = _part_of_speech_label(part_of_speech)
    if label is None:
        return meaning
    return f"{label}: {meaning}"


def _part_of_speech_label(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.replace("-", " ").replace("_", " ").casefold().split())
    if not normalized:
        return None
    return _PART_OF_SPEECH_LABELS.get(normalized, normalized)


def _clean_definition_text(value: str) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) <= _MAX_CARD_DEFINITION_CHARS:
        return cleaned

    for separator in (". ", "; "):
        first_segment = cleaned.split(separator, 1)[0].strip()
        if 20 <= len(first_segment) <= _MAX_CARD_DEFINITION_CHARS:
            return first_segment

    return cleaned[:_MAX_CARD_DEFINITION_CHARS].rsplit(" ", 1)[0].strip() + "..."


__all__ = ["LexicalGroundingService", "build_lexical_grounding_service"]
