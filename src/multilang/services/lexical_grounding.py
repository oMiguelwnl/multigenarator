"""Trust-first lexical grounding for frequency and custom-list inputs."""

from __future__ import annotations

from dataclasses import dataclass
import re
from html import escape
from pathlib import Path
from typing import Literal, Protocol, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from multilang.domain.highlights import HighlightCandidate
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.korean import (
    KoreanAnalyzerFingerprint,
    KoreanLexicalIdentity,
    KoreanMorphologyResult,
    KoreanMorphologyStatus,
    KoreanSignatureItem,
    KoreanTextError,
    KoreanWordAnalysis,
    canonicalize_korean,
)
from multilang.domain.lexicon import (
    DefinitionRecord,
    GroundingStatus,
    LexicalCardCandidate,
    LexicalProvenance,
    PronunciationRecord,
    policy_for_language,
)
from multilang.services.lexical_lookup import LexicalLookup, LexicalRecord, normalize_lexical_key
from multilang.services.part_of_speech import canonical_part_of_speech_label, resolve_part_of_speech_label
from multilang.services.polish_function_words import lookup_polish_function_word
from multilang.services.provider_pronunciation_adapters import PronunciationGenerationRequest
from multilang.services.rate_limit import RateLimiter
from multilang.services.text_field_remediation import remediate_definition_html
from multilang.services.text_generation import DefinitionGenerationRequest, DefinitionGenerationResult
from multilang.services.word_list_parser import ParsedWordListItem

_GERMAN_LEXICAL_OVERRIDES = {
    "pause": {
        "display_form": "Pause",
        "lemma": "Pause",
        "part_of_speech": "noun",
    },
}


def build_lexical_grounding_service(lexicon_data_dir: str | Path) -> "LexicalGroundingService":
    """Create the runtime grounding service backed by the cached lexical lookup."""

    return LexicalGroundingService(lookup=LexicalLookup(data_dir=lexicon_data_dir))


class PronunciationGenerator(Protocol):
    def generate_pronunciation(self, request: PronunciationGenerationRequest) -> object: ...


class DefinitionGenerator(Protocol):
    def generate_definition(self, request: DefinitionGenerationRequest) -> DefinitionGenerationResult: ...


class KoreanSourceMorphology(Protocol):
    @property
    def fingerprint(self) -> KoreanAnalyzerFingerprint: ...

    def analyze(self, text: str) -> KoreanMorphologyResult: ...


class KoreanSourceBindingResult(BaseModel):
    """Content-free outcome of intersecting morphology with source records."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    status: Literal["resolved", "insufficient", "ambiguous", "unavailable"]
    identity: KoreanLexicalIdentity | None = None
    reason_code: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")

    @model_validator(mode="after")
    def identity_must_match_status(self) -> Self:
        if self.status == "resolved" and self.identity is None:
            raise ValueError("resolved source binding requires identity")
        if self.status != "resolved" and self.identity is not None:
            raise ValueError("non-passing source binding cannot carry identity")
        return self


class KoreanResolvedLexeme(BaseModel):
    """One source-resolved Korean eojeol without surrounding highlight text."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    surface_form: str = Field(min_length=1)
    identity: KoreanLexicalIdentity
    word_position: int = Field(ge=0)

    @model_validator(mode="after")
    def surface_must_be_canonical_and_match_identity(self) -> Self:
        try:
            canonical = canonicalize_korean(self.surface_form)
        except KoreanTextError as exc:
            raise ValueError("resolved surface must be canonical Korean") from exc
        if canonical != self.surface_form:
            raise ValueError("resolved surface must already be NFC")
        if self.identity.canonical_nfc != self.surface_form:
            raise ValueError("resolved surface must match identity canonical form")
        return self


@dataclass(frozen=True, slots=True)
class _KoreanSourceSignatureProjection:
    signature: tuple[KoreanSignatureItem, ...] | None
    identity_pos: str | None
    reason_code: str | None
    observed_signatures: tuple[tuple[KoreanSignatureItem, ...], ...]


@dataclass(frozen=True, slots=True)
class _KoreanSourceCatalogEntry:
    record_index: int
    lemma: str
    source_pos: str
    sense_id: str
    register: str
    signature: tuple[KoreanSignatureItem, ...]
    identity_pos: str


@dataclass(frozen=True, slots=True)
class _KoreanSourceCatalogIssue:
    reason_code: str
    observed_signatures: tuple[tuple[KoreanSignatureItem, ...], ...]


@dataclass(frozen=True, slots=True)
class _KoreanCatalogSelection:
    status: Literal["resolved", "insufficient", "ambiguous", "unavailable"]
    reason_code: str
    entry: _KoreanSourceCatalogEntry | None = None


_SOURCE_POS_BY_TAG = {
    "NNG": "noun",
    "NNP": "proper_noun",
    "NNB": "noun",
    "NR": "numeral",
    "NP": "pronoun",
    "VV": "verb",
    "VA": "adjective",
    "VX": "auxiliary_verb",
    "VCP": "verb",
    "VCN": "verb",
    "MM": "determiner",
    "MAG": "adverb",
    "MAJ": "conjunction",
    "IC": "interjection",
    "XSV": "verb",
    "XSA": "adjective",
}

_SOURCE_POS_ALIASES = {
    "adj": "adjective",
    "adjective": "adjective",
    "adverb": "adverb",
    "aux": "auxiliary_verb",
    "auxiliary": "auxiliary_verb",
    "auxiliary verb": "auxiliary_verb",
    "conjunction": "conjunction",
    "determiner": "determiner",
    "interjection": "interjection",
    "noun": "noun",
    "numeral": "numeral",
    "pronoun": "pronoun",
    "proper": "proper_noun",
    "proper noun": "proper_noun",
    "verb": "verb",
}


class LexicalGroundingService:
    """Ground parsed lexical inputs against authoritative cached lookups."""

    def __init__(
        self,
        lookup: object,
        pronunciation_generator: PronunciationGenerator | None = None,
        definition_generator: DefinitionGenerator | None = None,
        allow_frequency_seed_fallback: bool = False,
        korean_morphology: KoreanSourceMorphology | None = None,
    ) -> None:
        self._lookup = lookup
        self._pronunciation_generator = pronunciation_generator
        self._definition_generator = definition_generator
        self._allow_frequency_seed_fallback = allow_frequency_seed_fallback
        self._korean_morphology = korean_morphology
        self._korean_source_signature_cache: dict[
            tuple[KoreanAnalyzerFingerprint, str, str, str],
            _KoreanSourceSignatureProjection,
        ] = {}

    def resolve_korean_source_identity(
        self,
        *,
        surface_form: str,
        submitted_form: str | None = None,
    ) -> KoreanSourceBindingResult:
        """Bind one Korean surface only through exact source-signature consensus."""

        morphology = self._korean_morphology
        if morphology is None:
            return _korean_binding_result(
                status="unavailable",
                reason_code="korean_morphology_unavailable",
            )
        try:
            canonical_surface = canonicalize_korean(surface_form)
            canonical_submitted = (
                canonicalize_korean(submitted_form)
                if submitted_form is not None
                else canonical_surface
            )
        except KoreanTextError:
            return _korean_binding_result(
                status="insufficient",
                reason_code="surface_text_invalid",
            )

        catalog, catalog_issues, inventory_reason = self._korean_source_catalog()
        if inventory_reason is not None:
            return _korean_binding_result(
                status="unavailable",
                reason_code=inventory_reason,
            )

        analysis = self._analyze_korean_safely(canonical_surface)
        if analysis is None:
            return _korean_binding_result(
                status="unavailable",
                reason_code="surface_analysis_unavailable",
            )
        if analysis.analyzer_fingerprint != morphology.fingerprint:
            return _korean_binding_result(
                status="unavailable",
                reason_code="surface_fingerprint_mismatch",
            )
        if analysis.status is KoreanMorphologyStatus.OOV:
            return _korean_binding_result(
                status="insufficient",
                reason_code="surface_analysis_oov",
            )
        if analysis.status is KoreanMorphologyStatus.UNAVAILABLE:
            return _korean_binding_result(
                status="unavailable",
                reason_code="surface_analysis_unavailable",
            )
        if analysis.status is KoreanMorphologyStatus.AMBIGUOUS:
            return _korean_binding_result(
                status="ambiguous",
                reason_code="surface_analysis_ambiguous",
            )
        if analysis.status is not KoreanMorphologyStatus.RESOLVED:
            return _korean_binding_result(
                status="insufficient",
                reason_code="surface_analysis_invalid",
            )
        if any(len(alternative.words) != 1 for alternative in analysis.alternatives):
            return _korean_binding_result(
                status="insufficient",
                reason_code="surface_analysis_invalid",
            )

        selection = self._select_korean_source_entry(
            words_by_alternative=tuple(
                tuple(alternative.words) for alternative in analysis.alternatives
            ),
            catalog=catalog,
            catalog_issues=catalog_issues,
        )
        if selection.entry is None:
            return _korean_binding_result(
                status=selection.status,
                reason_code=selection.reason_code,
            )

        identity = self._identity_from_korean_source_entry(
            entry=selection.entry,
            canonical_nfc=canonical_submitted,
            submitted_form=submitted_form,
        )
        if identity is None:
            return _korean_binding_result(
                status="insufficient",
                reason_code="source_record_invalid",
            )
        return _korean_binding_result(
            status="resolved",
            reason_code="source_consensus_resolved",
            identity=identity,
        )

    def resolve_korean_highlight_text(
        self,
        text: str,
    ) -> tuple[KoreanResolvedLexeme, ...]:
        """Analyze one local highlight once and return only consensus identities."""

        morphology = self._korean_morphology
        if morphology is None:
            return ()
        try:
            canonical_text = canonicalize_korean(text)
        except KoreanTextError:
            return ()
        catalog, catalog_issues, inventory_reason = self._korean_source_catalog()
        if inventory_reason is not None:
            return ()
        analysis = self._analyze_korean_safely(canonical_text)
        if (
            analysis is None
            or analysis.status is not KoreanMorphologyStatus.RESOLVED
            or analysis.analyzer_fingerprint != morphology.fingerprint
            or len(analysis.alternatives) != morphology.fingerprint.top_n
        ):
            return ()

        words_by_alternative = tuple(
            {word.word_position: word for word in alternative.words}
            for alternative in analysis.alternatives
        )
        positions = sorted(
            {
                word_position
                for words in words_by_alternative
                for word_position in words
            }
        )
        resolved: list[KoreanResolvedLexeme] = []
        for word_position in positions:
            words = tuple(
                (word,)
                if (word := alternative_words.get(word_position)) is not None
                else ()
                for alternative_words in words_by_alternative
            )
            selection = self._select_korean_source_entry(
                words_by_alternative=words,
                catalog=catalog,
                catalog_issues=catalog_issues,
            )
            if selection.entry is None or any(not alternative for alternative in words):
                continue
            surfaces = {
                alternative[0].surface_form
                for alternative in words
            }
            if len(surfaces) != 1:
                continue
            surface_form = surfaces.pop()
            identity = self._identity_from_korean_source_entry(
                entry=selection.entry,
                canonical_nfc=surface_form,
                submitted_form=None,
            )
            if identity is None:
                continue
            resolved.append(
                KoreanResolvedLexeme(
                    surface_form=surface_form,
                    identity=identity,
                    word_position=word_position,
                )
            )
        return tuple(resolved)

    def _select_korean_source_entry(
        self,
        *,
        words_by_alternative: tuple[tuple[KoreanWordAnalysis, ...], ...],
        catalog: tuple[_KoreanSourceCatalogEntry, ...],
        catalog_issues: tuple[_KoreanSourceCatalogIssue, ...],
    ) -> _KoreanCatalogSelection:
        morphology = self._korean_morphology
        assert morphology is not None
        if len(words_by_alternative) != morphology.fingerprint.top_n:
            return _KoreanCatalogSelection(
                status="unavailable",
                reason_code="surface_analysis_unavailable",
            )

        selections: list[tuple[_KoreanSourceCatalogEntry, ...]] = []
        for words in words_by_alternative:
            matching_indexes: set[int] = set()
            for word in words:
                signature = tuple(word.lexical_signature)
                source_pos = _source_pos_for_signature(signature)
                if source_pos is None:
                    continue
                matching_indexes.update(
                    entry.record_index
                    for entry in catalog
                    if entry.source_pos == source_pos
                    and entry.signature == signature
                )
            selections.append(
                tuple(
                    entry
                    for entry in catalog
                    if entry.record_index in matching_indexes
                )
            )

        if any(len(selection) > 1 for selection in selections):
            return _KoreanCatalogSelection(
                status="ambiguous",
                reason_code="source_record_ambiguous",
            )
        if any(len(selection) == 1 for selection in selections) and any(
            not selection for selection in selections
        ):
            return _KoreanCatalogSelection(
                status="ambiguous",
                reason_code="surface_source_disagreement",
            )
        if all(not selection for selection in selections):
            catalog_issue = _catalog_issue_for_words(
                words_by_alternative=words_by_alternative,
                issues=catalog_issues,
            )
            return _KoreanCatalogSelection(
                status=(
                    "unavailable"
                    if catalog_issue
                    in {
                        "source_analysis_unavailable",
                        "source_fingerprint_mismatch",
                    }
                    else "insufficient"
                ),
                reason_code=catalog_issue or "source_record_missing",
            )

        selected = tuple(selection[0] for selection in selections)
        selected_keys = {
            (entry.lemma, entry.source_pos, entry.sense_id)
            for entry in selected
        }
        if len(selected_keys) != 1:
            return _KoreanCatalogSelection(
                status="ambiguous",
                reason_code="surface_source_disagreement",
            )
        return _KoreanCatalogSelection(
            status="resolved",
            reason_code="source_consensus_resolved",
            entry=selected[0],
        )

    def _identity_from_korean_source_entry(
        self,
        *,
        entry: _KoreanSourceCatalogEntry,
        canonical_nfc: str,
        submitted_form: str | None,
    ) -> KoreanLexicalIdentity | None:
        morphology = self._korean_morphology
        assert morphology is not None
        try:
            return KoreanLexicalIdentity(
                submitted_form=submitted_form,
                canonical_nfc=canonical_nfc,
                lemma=entry.lemma,
                part_of_speech=entry.identity_pos,
                sense_id=entry.sense_id,
                register=entry.register,
                morpheme_signature=entry.signature,
                analyzer_fingerprint=morphology.fingerprint,
                status="resolved",
            )
        except ValueError:
            return None

    def _korean_source_catalog(
        self,
    ) -> tuple[
        tuple[_KoreanSourceCatalogEntry, ...],
        tuple[_KoreanSourceCatalogIssue, ...],
        str | None,
    ]:
        morphology = self._korean_morphology
        assert morphology is not None
        iter_candidates = getattr(self._lookup, "iter_candidates", None)
        if not callable(iter_candidates):
            return (), (), "source_inventory_unavailable"
        try:
            records = tuple(iter_candidates(language_code="ko"))
        except Exception:
            return (), (), "source_inventory_unavailable"

        def sort_key(record: LexicalRecord) -> tuple[str, str, str, str, str]:
            try:
                lemma = canonicalize_korean(record.lemma)
            except KoreanTextError:
                lemma = ""
            return (
                lemma,
                str(record.part_of_speech or "").strip().casefold(),
                str(record.sense_id or "").strip(),
                str(record.register or "").strip(),
                record.source,
            )

        entries: list[_KoreanSourceCatalogEntry] = []
        issues: list[_KoreanSourceCatalogIssue] = []
        for record_index, record in enumerate(sorted(records, key=sort_key)):
            source_pos = _normalize_source_pos(record.part_of_speech)
            sense_id = str(record.sense_id or "").strip()
            if source_pos is None or not sense_id:
                continue
            try:
                lemma = canonicalize_korean(record.lemma)
            except KoreanTextError:
                continue
            if lemma != lemma.strip():
                continue
            cache_key = (
                morphology.fingerprint,
                lemma,
                source_pos,
                sense_id,
            )
            projection = self._korean_source_signature_cache.get(cache_key)
            if projection is None:
                projection = self._project_korean_source_signature(
                    lemma=lemma,
                    source_pos=source_pos,
                )
                self._korean_source_signature_cache[cache_key] = projection
            if projection.signature is None or projection.identity_pos is None:
                if projection.reason_code is not None:
                    issues.append(
                        _KoreanSourceCatalogIssue(
                            reason_code=projection.reason_code,
                            observed_signatures=projection.observed_signatures,
                        )
                    )
                continue
            entries.append(
                _KoreanSourceCatalogEntry(
                    record_index=record_index,
                    lemma=lemma,
                    source_pos=source_pos,
                    sense_id=sense_id,
                    register=str(record.register or "standard").strip(),
                    signature=projection.signature,
                    identity_pos=projection.identity_pos,
                )
            )
        return tuple(entries), tuple(issues), None

    def _project_korean_source_signature(
        self,
        *,
        lemma: str,
        source_pos: str,
    ) -> _KoreanSourceSignatureProjection:
        morphology = self._korean_morphology
        assert morphology is not None
        analysis = self._analyze_korean_safely(lemma)
        if analysis is None or analysis.status is KoreanMorphologyStatus.UNAVAILABLE:
            return _source_projection_failure("source_analysis_unavailable")
        observed_signatures = tuple(
            sorted(
                {
                    tuple(word.lexical_signature)
                    for alternative in analysis.alternatives
                    for word in alternative.words
                },
                key=_signature_sort_key,
            )
        )
        if any(len(alternative.words) != 1 for alternative in analysis.alternatives):
            return _source_projection_failure(
                "source_analysis_invalid",
                observed_signatures=observed_signatures,
            )
        if analysis.analyzer_fingerprint != morphology.fingerprint:
            return _source_projection_failure(
                "source_fingerprint_mismatch",
                observed_signatures=observed_signatures,
            )
        if analysis.status is KoreanMorphologyStatus.OOV:
            return _source_projection_failure(
                "source_analysis_oov",
                observed_signatures=observed_signatures,
            )
        if analysis.status is not KoreanMorphologyStatus.RESOLVED:
            return _source_projection_failure(
                "source_analysis_invalid",
                observed_signatures=observed_signatures,
            )

        compatible = tuple(
            sorted(
                {
                    signature
                    for signature in observed_signatures
                    if _source_pos_for_signature(signature) == source_pos
                },
                key=_signature_sort_key,
            )
        )
        if not compatible:
            return _source_projection_failure(
                "source_pos_conflict",
                observed_signatures=observed_signatures,
            )
        if len(compatible) != 1:
            return _source_projection_failure(
                "source_signature_ambiguous",
                observed_signatures=observed_signatures,
            )
        signature = compatible[0]
        identity_pos = _identity_pos_for_signature(
            signature=signature,
            source_pos=source_pos,
        )
        if identity_pos is None:
            return _source_projection_failure(
                "source_pos_conflict",
                observed_signatures=observed_signatures,
            )
        return _KoreanSourceSignatureProjection(
            signature=signature,
            identity_pos=identity_pos,
            reason_code=None,
            observed_signatures=observed_signatures,
        )

    def _analyze_korean_safely(self, text: str) -> KoreanMorphologyResult | None:
        morphology = self._korean_morphology
        assert morphology is not None
        try:
            result = morphology.analyze(text)
        except Exception:
            return None
        return result if isinstance(result, KoreanMorphologyResult) else None

    def ground_word_list_item(
        self,
        *,
        language: SupportedLanguage,
        item: ParsedWordListItem,
        rate_limiter: RateLimiter | None = None,
    ) -> LexicalCardCandidate:
        if language is SupportedLanguage.KO:
            binding = self.resolve_korean_source_identity(
                surface_form=item.display_form,
                submitted_form=item.submitted_form,
            )
            if binding.identity is None:
                return self._pending_korean_word_list_candidate(
                    item=item,
                    binding=binding,
                )
            return self._grounded_korean_identity_candidate(
                identity=binding.identity,
                submitted_form=item.submitted_form,
                rate_limiter=rate_limiter,
            )
        record = self._lookup_record(language=language, term=item.item_key)
        if record is None:
            return self._pending_candidate(language=language, item=item)
        policy = policy_for_language(language)
        word_list_output_language = (
            policy.definition_language
            if language is SupportedLanguage.ZH
            else language.value
        )
        candidate = self._grounded_candidate(
            language=language,
            submitted_form=item.submitted_form,
            display_form=item.display_form,
            record=record,
            definition_language=word_list_output_language,
            rate_limiter=rate_limiter,
        )
        return candidate.model_copy(
            update={
                "definition_language": word_list_output_language,
                "translation_target_language": (
                    policy.translation_target_language
                    if language is SupportedLanguage.ZH
                    else language.value
                ),
            }
        )

    def ground_frequency_candidate(
        self,
        *,
        language: SupportedLanguage,
        candidate: LexicalCardCandidate,
        rate_limiter: RateLimiter | None = None,
    ) -> LexicalCardCandidate:
        if language is SupportedLanguage.KO:
            if (
                candidate.grounding_status is GroundingStatus.GROUNDED
                and candidate.korean_identity is not None
                and candidate.korean_frequency_evidence is not None
            ):
                return candidate
            binding = self.resolve_korean_source_identity(
                surface_form=candidate.display_form,
                submitted_form=candidate.submitted_form,
            )
            if binding.identity is None:
                policy = policy_for_language(language)
                return candidate.model_copy(
                    update={
                        "definition_language": policy.definition_language,
                        "translation_target_language": policy.translation_target_language,
                        "grounding_status": GroundingStatus.BACKFILL_REQUIRED,
                        "warning_code": f"korean_source_binding_{binding.status}",
                        "warning_detail": binding.reason_code,
                        "korean_identity": None,
                        "provenance": LexicalProvenance(
                            source=candidate.provenance.source,
                            notes=["Korean source identity requires review"],
                        ),
                    }
                )
            return self._grounded_korean_identity_candidate(
                identity=binding.identity,
                submitted_form=candidate.submitted_form,
                frequency_rank=candidate.frequency_rank,
                frequency_level=candidate.frequency_level,
                rate_limiter=rate_limiter,
            )
        record = self._lookup_record(language=language, term=candidate.lemma_key)
        if record is None:
            if self._should_use_frequency_seed_fallback(language):
                return self._ground_frequency_seed_candidate(
                    language=language,
                    candidate=candidate,
                    rate_limiter=rate_limiter,
                )
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
            rate_limiter=rate_limiter,
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
        rate_limiter: RateLimiter | None = None,
    ) -> LexicalCardCandidate:
        if language is SupportedLanguage.KO:
            existing_identity = getattr(candidate, "korean_identity", None)
            if isinstance(existing_identity, KoreanLexicalIdentity):
                binding = self._bind_existing_korean_source_identity(
                    existing_identity
                )
            else:
                binding = self.resolve_korean_source_identity(
                    surface_form=candidate.display_form,
                )
            if binding.identity is None:
                policy = policy_for_language(language)
                safe_key = candidate.item_key
                return LexicalCardCandidate(
                    submitted_form=safe_key,
                    display_form=safe_key,
                    lemma=safe_key,
                    lemma_key=safe_key,
                    definition_language=policy.definition_language,
                    translation_target_language=policy.translation_target_language,
                    grounding_status=GroundingStatus.INSUFFICIENT,
                    warning_code=f"korean_source_binding_{binding.status}",
                    warning_detail=binding.reason_code,
                    provenance=LexicalProvenance(
                        source="kindle_highlight",
                        notes=["Korean source identity requires review"],
                    ),
                )
            return self._grounded_korean_identity_candidate(
                identity=binding.identity,
                submitted_form=binding.identity.canonical_nfc,
                rate_limiter=rate_limiter,
            )
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
            rate_limiter=rate_limiter,
        )

    def _bind_existing_korean_source_identity(
        self,
        identity: KoreanLexicalIdentity,
    ) -> KoreanSourceBindingResult:
        morphology = self._korean_morphology
        if morphology is None:
            return _korean_binding_result(
                status="unavailable",
                reason_code="korean_morphology_unavailable",
            )
        if identity.analyzer_fingerprint != morphology.fingerprint:
            return _korean_binding_result(
                status="unavailable",
                reason_code="surface_fingerprint_mismatch",
            )
        catalog, _issues, inventory_reason = self._korean_source_catalog()
        if inventory_reason is not None:
            return _korean_binding_result(
                status="unavailable",
                reason_code=inventory_reason,
            )
        matches = tuple(
            entry
            for entry in catalog
            if entry.lemma == identity.lemma
            and entry.identity_pos == identity.part_of_speech
            and entry.sense_id == identity.sense_id
            and entry.register == identity.register
            and entry.signature == identity.morpheme_signature
        )
        if not matches:
            return _korean_binding_result(
                status="insufficient",
                reason_code="source_identity_mismatch",
            )
        if len(matches) != 1:
            return _korean_binding_result(
                status="ambiguous",
                reason_code="source_record_ambiguous",
            )
        return _korean_binding_result(
            status="resolved",
            reason_code="source_consensus_resolved",
            identity=identity,
        )

    def _grounded_korean_identity_candidate(
        self,
        *,
        identity: KoreanLexicalIdentity,
        submitted_form: str,
        frequency_rank: int | None = None,
        frequency_level: int | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> LexicalCardCandidate:
        policy = policy_for_language(SupportedLanguage.KO)
        definition_result = self._generate_definition(
            display_form=identity.lemma,
            lemma=identity.lemma,
            source_language=SupportedLanguage.KO.value,
            target_language=policy.definition_language,
            part_of_speech=identity.part_of_speech,
            korean_identity=identity,
            rate_limiter=rate_limiter,
        )
        definitions_html = (
            canonicalize_korean(definition_result.definitions_html)
            if definition_result is not None
            else None
        )
        return LexicalCardCandidate(
            submitted_form=submitted_form,
            display_form=identity.lemma,
            lemma=identity.lemma,
            lemma_key=identity.lexical_key,
            frequency_rank=frequency_rank,
            frequency_level=frequency_level,
            definitions_html=definitions_html,
            definition_language=policy.definition_language,
            translation_target_language=policy.translation_target_language,
            grounding_status=GroundingStatus.GROUNDED,
            provenance=LexicalProvenance(
                source="source_backed_korean_lexicon",
                definition=(
                    DefinitionRecord(
                        source=str(
                            definition_result.provenance.get(
                                "source", "definition-generator"
                            )
                        ),
                        value=definitions_html,
                        fallback_used=False,
                    )
                    if definition_result is not None
                    else None
                ),
                notes=["Korean identity resolved by exact source signature consensus"],
            ),
            korean_identity=identity,
        )

    @staticmethod
    def _pending_korean_word_list_candidate(
        *,
        item: ParsedWordListItem,
        binding: KoreanSourceBindingResult,
    ) -> LexicalCardCandidate:
        policy = policy_for_language(SupportedLanguage.KO)
        return LexicalCardCandidate(
            submitted_form=item.submitted_form,
            display_form=item.display_form,
            lemma=item.display_form,
            lemma_key=item.item_key,
            definition_language=policy.definition_language,
            translation_target_language=policy.translation_target_language,
            grounding_status=GroundingStatus.PENDING,
            warning_code=f"korean_source_binding_{binding.status}",
            warning_detail=binding.reason_code,
            provenance=LexicalProvenance(
                source="word_list",
                notes=["Korean source identity requires review"],
            ),
        )

    def _lookup_record(self, *, language: SupportedLanguage, term: str) -> LexicalRecord | None:
        if language is SupportedLanguage.PL:
            fixed = lookup_polish_function_word(term)
            if fixed is not None:
                return fixed
        return self._lookup.lookup(language_code=language.value, term=term)

    def _should_use_frequency_seed_fallback(self, language: SupportedLanguage) -> bool:
        if not self._allow_frequency_seed_fallback:
            return False
        has_index = getattr(self._lookup, "has_index", None)
        if not callable(has_index):
            return False
        return not bool(has_index(language_code=language.value))

    def _ground_frequency_seed_candidate(
        self,
        *,
        language: SupportedLanguage,
        candidate: LexicalCardCandidate,
        rate_limiter: RateLimiter | None = None,
    ) -> LexicalCardCandidate:
        record = LexicalRecord(
            term=candidate.display_form,
            display_form=candidate.display_form,
            lemma=candidate.lemma,
            definitions=[],
            source="wordfreq",
        )
        grounded = self._grounded_candidate(
            language=language,
            submitted_form=candidate.submitted_form,
            display_form=candidate.display_form,
            record=record,
            rate_limiter=rate_limiter,
        )
        return grounded.model_copy(
            update={
                "frequency_rank": candidate.frequency_rank,
                "frequency_level": candidate.frequency_level,
            }
        )

    def _grounded_candidate(
        self,
        *,
        language: SupportedLanguage,
        submitted_form: str,
        display_form: str,
        record: LexicalRecord,
        definition_language: str | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> LexicalCardCandidate:
        record = _apply_language_lexical_overrides(language=language, record=record)
        policy = policy_for_language(language)
        resolved_definition_language = definition_language or policy.definition_language
        learner_display_form = self._select_display_form(default=display_form, record=record)
        resolved_part_of_speech = resolve_part_of_speech_label(
            part_of_speech=record.part_of_speech,
            source_language=language.value,
            display_form=learner_display_form,
            lemma=record.lemma,
        )
        definition_result = self._generate_definition(
            display_form=learner_display_form,
            lemma=record.lemma,
            source_language=language.value,
            target_language=resolved_definition_language,
            part_of_speech=resolved_part_of_speech,
            rate_limiter=rate_limiter,
        )
        generated_definitions_html = definition_result.definitions_html if definition_result is not None else None
        definitions_html = remediate_definition_html(
            display_form=learner_display_form,
            lemma=record.lemma,
            part_of_speech=resolved_part_of_speech,
            generated_html=generated_definitions_html,
            source_definitions=record.definitions,
            source_language=language.value,
        )
        ipa = record.ipa.strip() if record.ipa else None
        spoken_form: str | None = learner_display_form if ipa else None
        pronunciation_source = record.source if ipa else f"{record.source}_missing"
        pronunciation_authoritative = bool(ipa)
        notes: list[str] = []
        if ipa:
            notes.append("authoritative IPA used from lexical source")
        else:
            notes.append("authoritative IPA missing in lexical source")
        if self._pronunciation_generator is not None and ipa is None:
            if rate_limiter is not None:
                rate_limiter.wait()
            try:
                pronunciation = self._pronunciation_generator.generate_pronunciation(
                    PronunciationGenerationRequest(
                        target_language=language.value,
                        display_form=learner_display_form,
                        lemma=record.lemma,
                        definitions_html=definitions_html,
                    )
                )
            except Exception:
                notes.append("pronunciation generator failed; word fallback will be used")
            else:
                ipa = str(getattr(pronunciation, "ipa")).strip()
                spoken_form = str(getattr(pronunciation, "spoken_form")).strip()
                pronunciation_source = str(
                    getattr(pronunciation, "provenance", {}).get(
                        "source", "provider-pronunciation-generator"
                    )
                )
                pronunciation_authoritative = True
                notes.append("provider IPA used because authoritative IPA was missing")
        if not ipa:
            ipa = learner_display_form
            spoken_form = learner_display_form
            pronunciation_authoritative = False
            notes.append("word fallback used because authoritative IPA was missing")

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
                    authoritative=pronunciation_authoritative,
                ),
                notes=notes,
            ),
        )

    def _generate_definition(
        self,
        *,
        display_form: str,
        lemma: str,
        source_language: str,
        target_language: str,
        part_of_speech: str | None,
        korean_identity: KoreanLexicalIdentity | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> DefinitionGenerationResult | None:
        if self._definition_generator is None:
            return None
        if rate_limiter is not None:
            rate_limiter.wait()
        return self._definition_generator.generate_definition(
            DefinitionGenerationRequest(
                display_form=display_form,
                lemma=lemma,
                source_language=source_language,
                target_language=target_language,
                part_of_speech=part_of_speech,
                korean_identity=korean_identity,
            )
        )

    def _pending_candidate(
        self,
        *,
        language: SupportedLanguage,
        item: ParsedWordListItem,
    ) -> LexicalCardCandidate:
        policy = policy_for_language(language)
        output_language = (
            policy.definition_language
            if language is SupportedLanguage.ZH
            else language.value
        )
        return LexicalCardCandidate(
            submitted_form=item.submitted_form,
            display_form=item.display_form,
            lemma=item.display_form,
            lemma_key=item.item_key,
            definition_language=output_language,
            translation_target_language=(
                policy.translation_target_language
                if language is SupportedLanguage.ZH
                else language.value
            ),
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
        return candidate

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


def _korean_binding_result(
    *,
    status: Literal["resolved", "insufficient", "ambiguous", "unavailable"],
    reason_code: str,
    identity: KoreanLexicalIdentity | None = None,
) -> KoreanSourceBindingResult:
    return KoreanSourceBindingResult(
        status=status,
        identity=identity,
        reason_code=reason_code,
    )


def _source_projection_failure(
    reason_code: str,
    *,
    observed_signatures: tuple[tuple[KoreanSignatureItem, ...], ...] = (),
) -> _KoreanSourceSignatureProjection:
    return _KoreanSourceSignatureProjection(
        signature=None,
        identity_pos=None,
        reason_code=reason_code,
        observed_signatures=observed_signatures,
    )


def _normalize_source_pos(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    base_tag = stripped.upper().partition("-")[0]
    tagged = _SOURCE_POS_BY_TAG.get(base_tag)
    if tagged is not None:
        return tagged
    normalized = " ".join(
        stripped.replace("-", " ").replace("_", " ").casefold().split()
    )
    return _SOURCE_POS_ALIASES.get(normalized)


def _source_pos_for_signature(
    signature: tuple[KoreanSignatureItem, ...],
) -> str | None:
    if not signature:
        return None
    tags = tuple(item.pos for item in signature)
    has_xsv = "XSV" in tags
    has_xsa = "XSA" in tags
    if has_xsv and has_xsa:
        return None
    if has_xsv:
        return "verb"
    if has_xsa:
        return "adjective"
    categories = {
        category
        for tag in tags
        if (category := _SOURCE_POS_BY_TAG.get(tag)) is not None
    }
    return next(iter(categories)) if len(categories) == 1 else None


def _identity_pos_for_signature(
    *,
    signature: tuple[KoreanSignatureItem, ...],
    source_pos: str,
) -> str | None:
    tags = tuple(item.pos for item in signature)
    if source_pos == "verb":
        if "XSV" in tags:
            return "VV"
        return next((tag for tag in tags if tag in {"VV", "VCP", "VCN"}), None)
    if source_pos == "adjective":
        if "XSA" in tags:
            return "VA"
        return "VA" if "VA" in tags else None
    if source_pos == "auxiliary_verb":
        return "VX" if "VX" in tags else None
    identity_tags = {
        "noun": {"NNG", "NNB"},
        "proper_noun": {"NNP"},
        "numeral": {"NR"},
        "pronoun": {"NP"},
        "determiner": {"MM"},
        "adverb": {"MAG"},
        "conjunction": {"MAJ"},
        "interjection": {"IC"},
    }.get(source_pos)
    if identity_tags is None:
        return None
    return next((tag for tag in tags if tag in identity_tags), None)


def _signature_sort_key(
    signature: tuple[KoreanSignatureItem, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple((item.form, item.pos) for item in signature)


def _catalog_issue_for_words(
    *,
    words_by_alternative: tuple[tuple[KoreanWordAnalysis, ...], ...],
    issues: tuple[_KoreanSourceCatalogIssue, ...],
) -> str | None:
    surface_signatures = {
        tuple(word.lexical_signature)
        for words in words_by_alternative
        for word in words
    }
    matching_reasons = {
        issue.reason_code
        for issue in issues
        if (
            surface_signatures.intersection(issue.observed_signatures)
            or (
                not issue.observed_signatures
                and issue.reason_code == "source_analysis_unavailable"
            )
        )
    }
    for reason_code in (
        "source_fingerprint_mismatch",
        "source_analysis_unavailable",
        "source_signature_ambiguous",
        "source_pos_conflict",
        "source_analysis_oov",
        "source_analysis_invalid",
    ):
        if reason_code in matching_reasons:
            return reason_code
    return None


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
    label = canonical_part_of_speech_label(part_of_speech)
    if label is None:
        return meaning
    return f"{label}: {meaning}"


def _clean_definition_text(value: str) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) <= _MAX_CARD_DEFINITION_CHARS:
        return cleaned

    for separator in (". ", "; "):
        first_segment = cleaned.split(separator, 1)[0].strip()
        if 20 <= len(first_segment) <= _MAX_CARD_DEFINITION_CHARS:
            return first_segment

    return cleaned[:_MAX_CARD_DEFINITION_CHARS].rsplit(" ", 1)[0].strip() + "..."


def _apply_language_lexical_overrides(*, language: SupportedLanguage, record: LexicalRecord) -> LexicalRecord:
    if language is not SupportedLanguage.DE:
        return record
    override = _GERMAN_LEXICAL_OVERRIDES.get(normalize_lexical_key(record.display_form)) or _GERMAN_LEXICAL_OVERRIDES.get(
        normalize_lexical_key(record.lemma)
    )
    if override is None:
        return record
    return record.model_copy(update=override)


__all__ = [
    "KoreanResolvedLexeme",
    "KoreanSourceBindingResult",
    "KoreanSourceMorphology",
    "LexicalGroundingService",
    "build_lexical_grounding_service",
]
