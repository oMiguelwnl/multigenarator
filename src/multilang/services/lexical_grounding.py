"""Trust-first lexical grounding for frequency and custom-list inputs."""

from __future__ import annotations

from html import escape

from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import (
    DefinitionRecord,
    GroundingStatus,
    LexicalCardCandidate,
    LexicalProvenance,
    PronunciationRecord,
    policy_for_language,
)
from multilang.services.kaikki_lookup import KaikkiRecord, normalize_lexical_key
from multilang.services.word_list_parser import ParsedWordListItem


class LexicalGroundingService:
    """Ground parsed lexical inputs against authoritative cached lookups."""

    def __init__(self, lookup: object) -> None:
        self._lookup = lookup

    def ground_word_list_item(
        self,
        *,
        language: SupportedLanguage,
        item: ParsedWordListItem,
    ) -> LexicalCardCandidate:
        record = self._lookup_record(language=language, term=item.item_key)
        if record is None:
            return self._pending_candidate(language=language, item=item)
        return self._grounded_candidate(
            language=language,
            submitted_form=item.submitted_form,
            display_form=item.display_form,
            record=record,
        )

    def ground_frequency_candidate(
        self,
        *,
        language: SupportedLanguage,
        candidate: LexicalCardCandidate,
    ) -> LexicalCardCandidate:
        record = self._lookup_record(language=language, term=candidate.lemma_key)
        if record is None:
            return candidate.model_copy(
                update={
                    "grounding_status": GroundingStatus.BACKFILL_REQUIRED,
                    "warning_code": "backfill_required",
                    "warning_detail": f"no authoritative lexical match for '{candidate.lemma}'",
                    "provenance": LexicalProvenance(
                        source=candidate.provenance.source,
                        notes=["frequency candidate requires lexical backfill"],
                    ),
                }
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

    def _lookup_record(self, *, language: SupportedLanguage, term: str) -> KaikkiRecord | None:
        return self._lookup.lookup(language_code=language.value, term=term)

    def _grounded_candidate(
        self,
        *,
        language: SupportedLanguage,
        submitted_form: str,
        display_form: str,
        record: KaikkiRecord,
    ) -> LexicalCardCandidate:
        policy = policy_for_language(language)
        learner_display_form = self._select_display_form(default=display_form, record=record)
        definitions_html = self._format_definitions(record.definitions)
        pronunciation_source = "kaikki" if record.ipa else "kaikki_missing"
        notes: list[str] = []
        if record.ipa is None:
            notes.append("authoritative IPA missing in lexical source")

        return LexicalCardCandidate(
            submitted_form=submitted_form,
            display_form=learner_display_form,
            lemma=record.lemma,
            lemma_key=normalize_lexical_key(record.lemma),
            definitions_html=definitions_html,
            definition_language=policy.definition_language,
            ipa=record.ipa,
            translation_target_language=policy.translation_target_language,
            grounding_status=GroundingStatus.GROUNDED,
            provenance=LexicalProvenance(
                source=record.source,
                definition=DefinitionRecord(source=record.source, value=definitions_html, fallback_used=False),
                pronunciation=PronunciationRecord(
                    source=pronunciation_source,
                    value=record.ipa,
                    authoritative=True,
                ),
                notes=notes,
            ),
        )

    def _pending_candidate(
        self,
        *,
        language: SupportedLanguage,
        item: ParsedWordListItem,
    ) -> LexicalCardCandidate:
        policy = policy_for_language(language)
        return LexicalCardCandidate(
            submitted_form=item.submitted_form,
            display_form=item.display_form,
            lemma=item.display_form,
            lemma_key=item.item_key,
            definition_language=policy.definition_language,
            translation_target_language=policy.translation_target_language,
            grounding_status=GroundingStatus.PENDING,
            warning_code="lexical_lookup_missing",
            warning_detail=(
                f"no authoritative lexical match for '{item.display_form}' from word-list line "
                f"{item.line_number}"
            ),
            provenance=LexicalProvenance(source="word_list", notes=["custom word retained for later review"]),
        )

    @staticmethod
    def _select_display_form(*, default: str, record: KaikkiRecord) -> str:
        candidate = record.display_form.strip()
        if not candidate:
            return default
        if candidate.casefold() != record.lemma.casefold():
            return candidate
        return default

    @staticmethod
    def _format_definitions(definitions: list[str]) -> str | None:
        cleaned = [escape(definition.strip()) for definition in definitions if definition.strip()]
        if not cleaned:
            return None
        return "<br>".join(cleaned)


__all__ = ["LexicalGroundingService"]
