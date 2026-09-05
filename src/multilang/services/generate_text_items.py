"""Coordinate generated text validation, single repair, and review routing."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import re
from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Protocol

from multilang.domain.jobs import JobStage, SupportedLanguage
from multilang.domain.korean import KoreanLexicalIdentity, canonical_json_sha256
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate, LexicalProvenance
from multilang.domain.source_profiles import get_source_profile
from multilang.security.redaction import redact_sensitive_text
from multilang.domain.text_quality import (
    ConfidenceLabel,
    ReviewStatus,
    TextGenerationStatus,
    TextProvenance,
    TextQualityRecord,
    ValidationFlag,
    ValidationFlagCode,
    ValidationStatus,
)
from multilang.services.text_generation import (
    DefinitionGenerationRequest,
    DefinitionGenerationResult,
    GeneratedSentence,
    GeneratedTextBundle,
    SentenceGenerationFallback,
    SentenceGenerationRequest,
    SentenceGenerationResult,
    SentenceTranslationRequest,
    SentenceTranslationResult,
    TextGenerationService,
)
from multilang.services.korean_text_generation import (
    KoreanTextGenerationSelector,
    korean_selector_history_from_record,
    with_korean_selector_history,
)
from multilang.services.rate_limit import RateLimiter
from multilang.services.text_validation import TextValidationResult, TextValidationService

# For dynamic Latin structured generation (using the model for gramatica etc.)
try:
    from multilang.services.latin_card_generation import LatinCardGenerationSeed, LatinCardGenerationService, LatinGeneratedCard
except Exception:
    LatinCardGenerationSeed = None  # type: ignore
    LatinCardGenerationService = None  # type: ignore
    LatinGeneratedCard = None  # type: ignore


class TatoebaSentenceSource(Protocol):
    def select_sentence(
        self,
        *,
        display_form: str,
        lemma: str,
        target_language: str,
        translation_target_language: str,
    ) -> SentenceGenerationResult | None: ...


@dataclass(slots=True)
class GenerateTextItemsResult:
    processed_items: int = 0
    accepted_items: int = 0
    review_required_items: int = 0
    processed_item_keys: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class RegenerateAudioRequest:
    job_id: str
    item_id: str
    field_name: str
    text: str
    deck_language: SupportedLanguage
    field_revision_id: str
    request_sha256: str
    final_path: str
    reservation_id: str


@dataclass(frozen=True, slots=True)
class RegenerateFieldResult:
    field_name: str
    value_sha256: str
    revision_id: str | None = None
    pointer_version: int | None = None
    pointer_status: str | None = None
    audio_reservation_id: str | None = None
    final_path: str | None = None


@dataclass(slots=True)
class GenerateTextProgress:
    processed_this_run: int
    accepted_this_run: int
    review_this_run: int
    remaining_missing: int
    last_item_key: str
    elapsed_seconds: float


GenerateTextProgressCallback = Callable[[GenerateTextProgress], None]


class GenerateTextItemsService:
    """Run generate -> validate -> AI retry -> Tatoeba fallback -> persist."""

    _sentence_token_re = re.compile(r"\b[\w'-]+\b", re.UNICODE)

    def __init__(
        self,
        *,
        job_repository: Any,
        lexical_repository: Any,
        text_repository: Any,
        text_generation_service: TextGenerationService,
        text_validation_service: TextValidationService,
        tatoeba_sentence_source: TatoebaSentenceSource,
        highlight_import_repository: Any | None = None,
        latin_card_service: Any | None = None,
        review_repository: Any | None = None,
        translation_adapter: Any | None = None,
        word_audio_port: Any | None = None,
        sentence_audio_port: Any | None = None,
    ) -> None:
        self.job_repository = job_repository
        self.lexical_repository = lexical_repository
        self.text_repository = text_repository
        self.text_generation_service = text_generation_service
        self.text_validation_service = text_validation_service
        self.tatoeba_sentence_source = tatoeba_sentence_source
        self.highlight_import_repository = highlight_import_repository
        self.latin_card_service = latin_card_service  # for dynamic la using the structured model
        self.review_repository = review_repository
        self.translation_adapter = translation_adapter
        self.word_audio_port = word_audio_port
        self.sentence_audio_port = sentence_audio_port

    def regenerate_field(
        self,
        *,
        job_id: str,
        item_id: str,
        field_name: str,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        request_id: str,
        expected_pointer_version: int,
        actor_id: str = "phase33-generator",
        generator_id: str = "phase33-generator",
        generator_version: str = "1",
        source_type: str | None = None,
        highlight_context: str | None = None,
        sentence_text: str | None = None,
        intended_sense: str | None = None,
        field_revision_id: str | None = None,
        field_revision_value_sha256: str | None = None,
        authority_sha256: str | None = None,
        root_prestate_sha256: str | None = None,
        audio_format: str = "mp3",
    ) -> RegenerateFieldResult:
        if field_name not in {"definition", "sentence", "microexample", "translation", "word_audio", "sentence_audio"}:
            raise ValueError("unsupported regenerable field")
        if self.review_repository is None:
            raise ValueError("review repository is required for field regeneration")

        candidate = LexicalCardCandidate.model_validate(candidate)
        if field_name == "definition":
            return self._regenerate_definition_field(
                job_id=job_id,
                item_id=item_id,
                field_name=field_name,
                candidate=candidate,
                deck_language=deck_language,
                request_id=request_id,
                expected_pointer_version=expected_pointer_version,
                actor_id=actor_id,
                generator_id=generator_id,
                generator_version=generator_version,
            )
        if field_name in {"sentence", "microexample"}:
            return self._regenerate_sentence_field(
                job_id=job_id,
                item_id=item_id,
                field_name=field_name,
                candidate=candidate,
                deck_language=deck_language,
                request_id=request_id,
                expected_pointer_version=expected_pointer_version,
                actor_id=actor_id,
                generator_id=generator_id,
                generator_version=generator_version,
                source_type=source_type,
                highlight_context=highlight_context,
            )
        if field_name == "translation":
            return self._regenerate_translation_field(
                job_id=job_id,
                item_id=item_id,
                field_name=field_name,
                candidate=candidate,
                request_id=request_id,
                expected_pointer_version=expected_pointer_version,
                actor_id=actor_id,
                generator_id=generator_id,
                generator_version=generator_version,
                sentence_text=sentence_text,
                intended_sense=intended_sense,
            )
        return self._regenerate_audio_field(
            job_id=job_id,
            item_id=item_id,
            field_name=field_name,
            candidate=candidate,
            deck_language=deck_language,
            request_id=request_id,
            expected_pointer_version=expected_pointer_version,
            field_revision_id=field_revision_id,
            field_revision_value_sha256=field_revision_value_sha256,
            authority_sha256=authority_sha256,
            root_prestate_sha256=root_prestate_sha256,
            sentence_text=sentence_text,
            audio_format=audio_format,
        )

    def _regenerate_definition_field(
        self,
        *,
        job_id: str,
        item_id: str,
        field_name: str,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        request_id: str,
        expected_pointer_version: int,
        actor_id: str,
        generator_id: str,
        generator_version: str,
    ) -> RegenerateFieldResult:
        generate_definition = getattr(self.text_generation_service, "generate_definition", None)
        if not callable(generate_definition):
            raise ValueError("definition text generator is required")
        request = DefinitionGenerationRequest(
            display_form=candidate.display_form,
            lemma=candidate.lemma,
            source_language=deck_language.value,
            target_language=candidate.definition_language,
            part_of_speech=(candidate.korean_identity.part_of_speech if candidate.korean_identity else None),
            korean_identity=candidate.korean_identity,
        )
        generated = DefinitionGenerationResult.model_validate(generate_definition(request))
        return self._append_field_revision(
            actor_id=actor_id,
            request_id=request_id,
            job_id=job_id,
            item_id=item_id,
            field_name=field_name,
            value=generated.definitions_html,
            generator_id=generator_id,
            generator_version=generator_version,
            route_id=_route_id(generated.provenance, default="definition"),
            expected_pointer_version=expected_pointer_version,
        )

    def _regenerate_sentence_field(
        self,
        *,
        job_id: str,
        item_id: str,
        field_name: str,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        request_id: str,
        expected_pointer_version: int,
        actor_id: str,
        generator_id: str,
        generator_version: str,
        source_type: str | None,
        highlight_context: str | None,
    ) -> RegenerateFieldResult:
        generate_sentence = getattr(self.text_generation_service, "generate_sentence", None)
        if not callable(generate_sentence):
            raise ValueError("sentence text generator is required")
        request = SentenceGenerationRequest.from_candidate(
            candidate=candidate,
            deck_language=deck_language,
            source_type=source_type,
            highlight_context=highlight_context,
        )
        generated = SentenceGenerationResult.model_validate(generate_sentence(request))
        return self._append_field_revision(
            actor_id=actor_id,
            request_id=request_id,
            job_id=job_id,
            item_id=item_id,
            field_name=field_name,
            value=generated.sentence,
            generator_id=generator_id,
            generator_version=generator_version,
            route_id=_route_id(generated.provenance, default=field_name),
            expected_pointer_version=expected_pointer_version,
        )

    def _regenerate_translation_field(
        self,
        *,
        job_id: str,
        item_id: str,
        field_name: str,
        candidate: LexicalCardCandidate,
        request_id: str,
        expected_pointer_version: int,
        actor_id: str,
        generator_id: str,
        generator_version: str,
        sentence_text: str | None,
        intended_sense: str | None,
    ) -> RegenerateFieldResult:
        if not sentence_text:
            raise ValueError("sentence_text is required for translation regeneration")
        if self.translation_adapter is None:
            raise ValueError("translation adapter is required")
        translate_sentence = getattr(self.translation_adapter, "translate_sentence", None)
        if not callable(translate_sentence):
            raise ValueError("translation adapter is invalid")
        request = SentenceTranslationRequest(
            sentence=sentence_text,
            translation_target_language=candidate.translation_target_language,
            intended_sense=intended_sense,
        )
        generated = SentenceTranslationResult.model_validate(translate_sentence(request))
        return self._append_field_revision(
            actor_id=actor_id,
            request_id=request_id,
            job_id=job_id,
            item_id=item_id,
            field_name=field_name,
            value=generated.translation,
            generator_id=generator_id,
            generator_version=generator_version,
            route_id=_route_id(generated.provenance, default="translation"),
            expected_pointer_version=expected_pointer_version,
        )

    def _regenerate_audio_field(
        self,
        *,
        job_id: str,
        item_id: str,
        field_name: str,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        request_id: str,
        expected_pointer_version: int,
        field_revision_id: str | None,
        field_revision_value_sha256: str | None,
        authority_sha256: str | None,
        root_prestate_sha256: str | None,
        sentence_text: str | None,
        audio_format: str,
    ) -> RegenerateFieldResult:
        port = self.word_audio_port if field_name == "word_audio" else self.sentence_audio_port
        if port is None:
            raise ValueError("audio port is required")
        synthesize = getattr(port, "synthesize", None)
        if not callable(synthesize):
            raise ValueError("audio port is invalid")
        if not field_revision_id or not field_revision_value_sha256 or not authority_sha256 or not root_prestate_sha256:
            raise ValueError("audio regeneration requires exact revision, authority, and root hashes")
        text = candidate.spoken_form or candidate.display_form
        if field_name == "sentence_audio":
            if not sentence_text:
                raise ValueError("sentence_text is required for sentence audio regeneration")
            text = sentence_text
        request_sha256 = _stable_sha256(
            {
                "job_id": job_id,
                "item_id": item_id,
                "field_name": field_name,
                "field_revision_id": field_revision_id,
                "field_revision_value_sha256": field_revision_value_sha256,
                "text_sha256": _text_sha256(text),
                "deck_language": deck_language.value,
                "request_id": request_id,
            }
        )
        final_path = _audio_final_path(
            field_name=field_name,
            item_id=item_id,
            field_revision_id=field_revision_id,
            request_sha256=request_sha256,
            audio_format=audio_format,
        )
        reservation = self.review_repository.reserve_audio_publication(
            job_id=job_id,
            item_id=item_id,
            field_name=field_name,
            field_revision_id=field_revision_id,
            request_sha256=request_sha256,
            final_path=final_path,
            authority_sha256=authority_sha256,
            root_prestate_sha256=root_prestate_sha256,
            expected_pointer_version=expected_pointer_version,
        )
        audio_request = RegenerateAudioRequest(
            job_id=job_id,
            item_id=item_id,
            field_name=field_name,
            text=text,
            deck_language=deck_language,
            field_revision_id=field_revision_id,
            request_sha256=request_sha256,
            final_path=str(getattr(reservation, "final_path")),
            reservation_id=str(getattr(reservation, "reservation_id")),
        )
        synthesize(audio_request)
        return RegenerateFieldResult(
            field_name=field_name,
            value_sha256=field_revision_value_sha256,
            audio_reservation_id=str(getattr(reservation, "reservation_id")),
            final_path=str(getattr(reservation, "final_path")),
        )

    def _append_field_revision(
        self,
        *,
        actor_id: str,
        request_id: str,
        job_id: str,
        item_id: str,
        field_name: str,
        value: str,
        generator_id: str,
        generator_version: str,
        route_id: str | None,
        expected_pointer_version: int,
    ) -> RegenerateFieldResult:
        value_sha256 = _text_sha256(value)
        mutation = self.review_repository.create_candidate_revision(
            actor_id=actor_id,
            request_id=request_id,
            job_id=job_id,
            item_id=item_id,
            field_name=field_name,
            value_sha256=value_sha256,
            generator_id=generator_id,
            generator_version=generator_version,
            route_id=route_id,
            expected_pointer_version=expected_pointer_version,
        )
        revision = getattr(mutation, "revision")
        return RegenerateFieldResult(
            field_name=field_name,
            value_sha256=str(getattr(revision, "value_sha256")),
            revision_id=str(getattr(revision, "revision_id")),
            pointer_version=int(getattr(mutation, "pointer_version")),
            pointer_status=str(getattr(mutation, "pointer_status")),
        )

    def execute(
        self,
        *,
        job_id: str,
        deck_language: SupportedLanguage,
        missing_only: bool = False,
        max_items: int | None = None,
        progress_callback: GenerateTextProgressCallback | None = None,
        rate_limiter: RateLimiter | None = None,
        repair_only: bool = False,
        concurrency: int = 1,
    ) -> GenerateTextItemsResult:
        if max_items is not None and max_items < 1:
            raise ValueError("max_items must be greater than or equal to 1")

        started_at = monotonic()
        result = GenerateTextItemsResult()
        seen_sentences = self._normalize_sentences(self.text_repository.list_example_sentences_for_job(job_id))
        if concurrency < 1:
            raise ValueError("concurrency must be greater than or equal to 1")

        if repair_only:
            lister = getattr(self.text_repository, "list_repair_candidates")
            candidates = lister(job_id, max_items=max_items)
        else:
            claimer = getattr(self.text_repository, "claim_generation_candidates", None)
            if callable(claimer):
                candidates = claimer(job_id, missing_only=missing_only, limit=max_items)
            else:
                candidates = self.text_repository.list_generation_candidates(job_id, missing_only=missing_only)
        if repair_only:
            missing_item_keys = set()
        else:
            missing_item_keys = (
                {str(getattr(candidate, "item_key")) for candidate in candidates}
                if missing_only
                else {
                    str(getattr(candidate, "item_key"))
                    for candidate in self.text_repository.list_generation_candidates(job_id, missing_only=True)
                }
            )
        remaining_missing = len(missing_item_keys)
        if max_items is not None and not repair_only and not callable(getattr(self.text_repository, "claim_generation_candidates", None)):
            candidates = candidates[:max_items]

        # For dynamic Latin (la), use the LatinCardGenerationService + model so the AI fills
        # gramatica (and definition/sentence) using the structured schema + gramatica template.
        latin_cards_by_index: dict[int, Any] = {}
        if deck_language == SupportedLanguage.LA and self.latin_card_service is not None and candidates:
            seeds = []
            for i, c in enumerate(candidates):
                try:
                    seed = LatinCardGenerationSeed(
                        sequence=i + 1,
                        lemma=str(getattr(c, 'lemma', getattr(c, 'display_form', 'unknown'))),
                        target_form=str(getattr(c, 'display_form', getattr(c, 'lemma', 'unknown'))),
                        part_of_speech=str(getattr(c, 'part_of_speech', 'unknown')),
                    )
                    seeds.append(seed)
                except Exception:
                    pass
            if seeds:
                try:
                    # Generate for all candidates (structured + gramatica rules + internal validation+retry)
                    _cards = self.latin_card_service.generate(seeds)
                    for idx, card in enumerate(_cards):
                        latin_cards_by_index[idx] = card
                except Exception:
                    pass  # fall back to general mapping

        for candidate_index, persisted_candidate in enumerate(candidates):
            candidate_id = getattr(persisted_candidate, "id")
            item_key = getattr(persisted_candidate, "item_key")
            lexical_candidate = self._to_candidate(persisted_candidate)
            source_type = self._resolve_source_type(
                getattr(persisted_candidate, "source_type", None),
                candidate=lexical_candidate,
            )
            highlight_context = self._build_highlight_context(
                job_id=job_id,
                source_type=source_type,
                candidate=lexical_candidate,
            )

            korean_selection = None
            if deck_language is SupportedLanguage.KO:
                existing_record = self._get_existing_text_record(job_id, item_key)
                existing_history = korean_selector_history_from_record(existing_record)
                selector = KoreanTextGenerationSelector(
                    text_generation_service=self.text_generation_service,
                    validate_bundle=self._validate_bundle,
                )
                korean_selection = selector.select(
                    candidate=lexical_candidate,
                    deck_language=deck_language,
                    source_type=source_type,
                    highlight_context=highlight_context,
                    seen_sentences=seen_sentences,
                    job_id=job_id,
                    item_key=item_key,
                    rate_limiter=rate_limiter,
                    remaining_repair_budget=max(0, 1 - (existing_history.repair_attempt_count if existing_history else 0)),
                    existing_history=existing_history,
                )
                generated_bundle = korean_selection.bundle
                validation = korean_selection.validation
                generation_status = korean_selection.generation_status
                repair_attempt_count = korean_selection.repair_attempt_count
            else:
                generated_bundle = self.text_generation_service.generate_bundle(
                    candidate=lexical_candidate,
                    deck_language=deck_language,
                    source_type=source_type,
                    highlight_context=highlight_context,
                    rate_limiter=rate_limiter,
                )
                validation = None
                generation_status = TextGenerationStatus.GENERATED
                repair_attempt_count = 0

            # Use pre-generated high-quality Latin card (with correct gramatica + sentence) when available.
            # This is the main way to get low-error Latin output.
            if deck_language == SupportedLanguage.LA and candidate_index in latin_cards_by_index:
                lat_card = latin_cards_by_index[candidate_index]
                try:
                    lat_sentence = getattr(lat_card, "latin_sentence", None) or (lat_card.get("latin_sentence") if isinstance(lat_card, dict) else None)
                    if lat_sentence:
                        lat_gramatica = getattr(lat_card, "gramatica", None) or (lat_card.get("gramatica") if isinstance(lat_card, dict) else None)
                        # Carry the structured grammar through provenance metadata so it
                        # survives to export (the exported "Grammar" field reads it there).
                        # NOTE: GeneratedSentence.provenance is a TextProvenance, which
                        # requires a non-empty source; a bare dict here raised a swallowed
                        # ValidationError, silently dropping the structured sentence.
                        metadata: dict[str, Any] = {"via": "latin_card_service"}
                        if lat_gramatica:
                            metadata["gramatica"] = str(lat_gramatica)
                        provenance = TextProvenance(
                            source="latin-structured",
                            provider="latin-structured",
                            metadata=metadata,
                        )
                        new_sentence = GeneratedSentence(
                            text=str(lat_sentence),
                            target_language=deck_language.value,
                            provenance=provenance,
                        )
                        # The bundle translation was produced for the ORIGINAL
                        # generated sentence. Regenerate it for the structured
                        # Latin sentence BEFORE mutating the bundle so a failure
                        # leaves the original sentence+translation pair intact
                        # instead of pairing the new sentence with a stale one.
                        new_translation = self.text_generation_service.translate_sentence_text(
                            sentence=str(lat_sentence),
                            translation_target_language=generated_bundle.translation.target_language,
                            deck_language=deck_language,
                            rate_limiter=rate_limiter,
                        )
                        # Override sentence + translation together (better grammar control).
                        generated_bundle.sentence = new_sentence
                        generated_bundle.translation = new_translation
                except Exception:
                    pass
            if validation is None:
                validation = self._validate_bundle(
                    bundle=generated_bundle,
                    candidate=lexical_candidate,
                    seen_sentences=seen_sentences,
                    source_type=source_type,
                    deck_language=deck_language,
                )

            if deck_language is not SupportedLanguage.KO and validation.validation_status is ValidationStatus.FAILED:
                generation_status = TextGenerationStatus.REPAIRED
                generated_bundle, validation, repair_attempt_count = self._attempt_repair_chain(
                    candidate=lexical_candidate,
                    deck_language=deck_language,
                    generated_bundle=generated_bundle,
                    validation=validation,
                    seen_sentences=seen_sentences,
                    source_type=source_type,
                    highlight_context=highlight_context,
                    rate_limiter=rate_limiter,
                )

            record = self._build_record(
                job_id=job_id,
                item_key=item_key,
                lexical_candidate_id=candidate_id,
                bundle=generated_bundle,
                validation=validation,
                generation_status=generation_status,
                repair_attempt_count=repair_attempt_count,
            )
            if korean_selection is not None:
                record = with_korean_selector_history(record, korean_selection.history)
            self.text_repository.upsert_text_record(record)
            normalized_sentence = self._normalize_sentence_text(record.example_sentence)
            if normalized_sentence:
                seen_sentences.add(normalized_sentence)
            self.job_repository.record_item_success(
                job_id,
                item_key=item_key,
                completed_stage=JobStage.GENERATE_TEXT,
            )

            result.processed_items += 1
            result.processed_item_keys.append(item_key)
            if record.review_status is ReviewStatus.ACCEPTED:
                result.accepted_items += 1
            else:
                result.review_required_items += 1
            if item_key in missing_item_keys:
                remaining_missing -= 1
            if progress_callback is not None:
                progress_callback(
                    GenerateTextProgress(
                        processed_this_run=result.processed_items,
                        accepted_this_run=result.accepted_items,
                        review_this_run=result.review_required_items,
                        remaining_missing=max(remaining_missing, 0),
                        last_item_key=item_key,
                        elapsed_seconds=monotonic() - started_at,
                    )
                )

        return result

    def _validate_bundle(
        self,
        *,
        bundle: GeneratedTextBundle,
        candidate: LexicalCardCandidate,
        seen_sentences: set[str] | None = None,
        source_type: str | None = None,
        deck_language: SupportedLanguage,
    ) -> TextValidationResult:
        source_profile = get_source_profile(self._resolve_source_type(source_type, candidate=candidate))
        is_same_language_translation = candidate.translation_target_language == deck_language.value
        require_translation = (
            source_profile.requires_translation_validation
            and not is_same_language_translation
        )
        validation = self.text_validation_service.validate(
            sentence=bundle.sentence,
            translation=bundle.translation,
            display_form=candidate.display_form,
            lemma=candidate.lemma,
            definitions_html=candidate.definitions_html,
            disallowed_sentence_texts=set(seen_sentences or set()),
            require_translation=require_translation,
            min_sentence_tokens=source_profile.min_sentence_tokens,
            max_sentence_tokens=source_profile.max_sentence_tokens,
            korean_identity=candidate.korean_identity,
        )
        return _gate_local_templates(
            validation=validation,
            bundle=bundle,
            source_type=source_profile.source_type,
            deck_language=deck_language,
        )

    def _build_record(
        self,
        *,
        job_id: str,
        item_key: str,
        lexical_candidate_id: str,
        bundle: GeneratedTextBundle,
        validation: TextValidationResult,
        generation_status: TextGenerationStatus,
        repair_attempt_count: int,
    ) -> TextQualityRecord:
        review_status = (
            ReviewStatus.ACCEPTED
            if validation.validation_status is ValidationStatus.PASSED
            else ReviewStatus.REVIEW_REQUIRED
        )
        review_reason = None
        if review_status is ReviewStatus.REVIEW_REQUIRED and validation.validation_flags:
            review_reason = validation.validation_flags[0].code.value

        return TextQualityRecord(
            job_id=job_id,
            item_key=item_key,
            lexical_candidate_id=lexical_candidate_id,
            example_sentence=bundle.sentence.text,
            translation_text=bundle.translation.text,
            generation_status=generation_status,
            validation_status=validation.validation_status,
            review_status=review_status,
            repair_attempt_count=repair_attempt_count,
            confidence_score=validation.confidence_score,
            confidence_label=validation.confidence_label,
            validation_flags=validation.validation_flags,
            review_reason=review_reason,
            sentence_provenance=bundle.sentence.provenance,
            translation_provenance=bundle.translation.provenance,
        )

    def _attempt_repair_chain(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        generated_bundle: GeneratedTextBundle,
        validation: TextValidationResult,
        seen_sentences: set[str],
        source_type: str | None,
        highlight_context: str | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> tuple[GeneratedTextBundle, TextValidationResult, int]:
        retry_bundle = self.text_generation_service.generate_bundle(
            candidate=candidate,
            deck_language=deck_language,
            source_type=source_type,
            highlight_context=highlight_context,
            rate_limiter=rate_limiter,
        )
        retry_validation = self._validate_bundle(
            bundle=retry_bundle,
            candidate=candidate,
            seen_sentences=seen_sentences,
            source_type=source_type,
            deck_language=deck_language,
        )
        if retry_validation.validation_status is ValidationStatus.PASSED:
            return retry_bundle, retry_validation, 1

        fallback_bundle, fallback_validation = self._attempt_tatoeba_repair(
            candidate=candidate,
            deck_language=deck_language,
            generated_bundle=retry_bundle,
            validation=retry_validation,
            seen_sentences=seen_sentences,
            source_type=source_type,
            highlight_context=highlight_context,
            rate_limiter=rate_limiter,
        )
        fallback_used = fallback_bundle is not retry_bundle
        return fallback_bundle, fallback_validation, 2 if fallback_used else 1

    def _attempt_tatoeba_repair(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        generated_bundle: GeneratedTextBundle,
        validation: TextValidationResult,
        seen_sentences: set[str],
        source_type: str | None,
        highlight_context: str | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> tuple[GeneratedTextBundle, TextValidationResult]:
        if deck_language is SupportedLanguage.KO:
            return generated_bundle, validation

        fallback_sentence = self.tatoeba_sentence_source.select_sentence(
            display_form=candidate.display_form,
            lemma=candidate.lemma,
            target_language=deck_language.value,
            translation_target_language=candidate.translation_target_language,
        )
        if fallback_sentence is None:
            return generated_bundle, validation

        repaired_bundle = self.text_generation_service.generate_bundle_from_fallback(
            candidate=candidate,
            deck_language=deck_language,
            fallback=SentenceGenerationFallback(sentence_result=fallback_sentence),
            source_type=source_type,
            highlight_context=highlight_context,
            rate_limiter=rate_limiter,
        )
        repaired_validation = self._validate_bundle(
            bundle=repaired_bundle,
            candidate=candidate,
            seen_sentences=seen_sentences,
            source_type=source_type,
            deck_language=deck_language,
        )
        return repaired_bundle, repaired_validation

    @staticmethod
    def _normalize_sentence_text(value: str | None) -> str:
        if value is None:
            return ""
        return " ".join(GenerateTextItemsService._sentence_token_re.findall(value.casefold()))

    @classmethod
    def _normalize_sentences(cls, values: list[str]) -> set[str]:
        return {
            normalized
            for value in values
            if (normalized := cls._normalize_sentence_text(value))
        }

    def _to_candidate(self, persisted_candidate: Any) -> LexicalCardCandidate:
        if hasattr(persisted_candidate, "candidate"):
            return getattr(persisted_candidate, "candidate")

        persisted_korean_identity = getattr(
            persisted_candidate,
            "korean_identity",
            None,
        )
        korean_identity = (
            KoreanLexicalIdentity.model_validate(persisted_korean_identity)
            if persisted_korean_identity is not None
            else None
        )
        return LexicalCardCandidate(
            submitted_form=getattr(persisted_candidate, "submitted_form"),
            display_form=getattr(persisted_candidate, "display_form"),
            lemma=getattr(persisted_candidate, "lemma"),
            lemma_key=getattr(persisted_candidate, "lemma_key"),
            frequency_rank=getattr(persisted_candidate, "frequency_rank"),
            frequency_level=getattr(persisted_candidate, "frequency_level"),
            definitions_html=getattr(persisted_candidate, "definitions_html"),
            definition_language=getattr(persisted_candidate, "definition_language"),
            ipa=getattr(persisted_candidate, "ipa"),
            translation_target_language=getattr(persisted_candidate, "translation_target_language"),
            grounding_status=GroundingStatus(getattr(persisted_candidate, "grounding_status")),
            warning_code=getattr(persisted_candidate, "warning_code"),
            warning_detail=getattr(persisted_candidate, "warning_detail"),
            provenance=LexicalProvenance.model_validate(getattr(persisted_candidate, "provenance")),
            korean_identity=korean_identity,
        )

    @staticmethod
    def _resolve_source_type(source_type: str | None, *, candidate: LexicalCardCandidate) -> str:
        if source_type:
            return source_type
        if candidate.frequency_rank is not None or candidate.frequency_level is not None:
            return "frequency"
        return "word-list"

    def _build_highlight_context(
        self,
        *,
        job_id: str,
        source_type: str,
        candidate: LexicalCardCandidate,
    ) -> str | None:
        if source_type != "kindle-highlights" or self.highlight_import_repository is None:
            return None
        highlight_id = _provenance_note_value(candidate.provenance.notes, "first_highlight_id")
        if not highlight_id:
            return None
        record = self.highlight_import_repository.get_private_record(job_id, highlight_id)
        if record is None:
            return None
        normalized_text = str(getattr(record, "normalized_text", "") or "").strip()
        if not normalized_text:
            return None
        redacted = redact_sensitive_text(normalized_text)
        return _bounded_context_snippet(
            redacted,
            display_form=candidate.display_form,
            lemma=candidate.lemma,
        )

    def _get_existing_text_record(self, job_id: str, item_key: str) -> object | None:
        getter = getattr(self.text_repository, "get_text_record", None)
        if not callable(getter):
            return None
        return getter(job_id, item_key)


def _provenance_note_value(notes: list[str], key: str) -> str | None:
    prefix = f"{key}="
    for note in notes:
        if note.startswith(prefix):
            value = note.removeprefix(prefix).strip()
            if value:
                return value
    return None


def _bounded_context_snippet(text: str, *, display_form: str, lemma: str, max_tokens: int = 24) -> str:
    tokens = GenerateTextItemsService._sentence_token_re.findall(text)
    if not tokens:
        return ""
    match_keys = {display_form.casefold(), lemma.casefold()}
    center = 0
    for index, token in enumerate(tokens):
        if token.casefold() in match_keys:
            center = index
            break
    half_window = max_tokens // 2
    start = max(0, center - half_window)
    end = min(len(tokens), start + max_tokens)
    start = max(0, end - max_tokens)
    return " ".join(tokens[start:end])


def _gate_local_templates(
    *,
    validation: TextValidationResult,
    bundle: GeneratedTextBundle,
    source_type: str | None,
    deck_language: SupportedLanguage,
) -> TextValidationResult:
    if (
        source_type not in {"frequency", "word-list"}
        or deck_language is SupportedLanguage.EN
        or not _uses_generic_local_text(bundle)
    ):
        return validation

    flags = [
        *validation.validation_flags,
        ValidationFlag(
            code=ValidationFlagCode.BANNED_PATTERN,
            detail="non-English learner decks must not accept generic local text templates as learner-facing content",
        ),
    ]
    return validation.model_copy(
        update={
            "validation_status": ValidationStatus.FAILED,
            "validation_flags": flags,
            "confidence_score": min(validation.confidence_score, 0.45),
            "confidence_label": ConfidenceLabel.LOW,
        }
    )


def _uses_generic_local_text(bundle: GeneratedTextBundle) -> bool:
    return _is_generic_local_provenance(bundle.sentence.provenance) or _is_generic_local_provenance(
        bundle.translation.provenance
    )


def _is_generic_local_provenance(provenance: object) -> bool:
    provider = getattr(provenance, "provider", None)
    source = getattr(provenance, "source", None)
    metadata = getattr(provenance, "metadata", {}) or {}
    template_kind = str(metadata.get("template_kind") or "")
    local_source = str(metadata.get("source") or "")

    is_local = provider == "local" or source == "local" or local_source.startswith("runtime-local")
    if not is_local:
        return False
    return not template_kind.startswith("curated:")


def _route_id(provenance: dict[str, Any], *, default: str) -> str | None:
    route = provenance.get("route") or provenance.get("route_id") or provenance.get("provider") or default
    route_id = str(route).strip()
    return route_id or None


def _text_sha256(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _stable_sha256(payload: dict[str, object]) -> str:
    return canonical_json_sha256(payload)


def _audio_final_path(
    *,
    field_name: str,
    item_id: str,
    field_revision_id: str,
    request_sha256: str,
    audio_format: str,
) -> str:
    safe_field = _safe_path_part(field_name)
    safe_item = _safe_path_part(item_id)
    safe_revision = _safe_path_part(field_revision_id)
    safe_extension = _safe_path_part(audio_format).lstrip(".") or "mp3"
    return f"{safe_field}/{safe_item}/{safe_revision}/{request_sha256}.{safe_extension}"


def _safe_path_part(value: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in "._-" else "-" for character in value)
    cleaned = cleaned.strip(".-_")
    return cleaned[:160] or "item"


__all__ = [
    "GenerateTextItemsResult",
    "GenerateTextItemsService",
    "GenerateTextProgress",
    "GenerateTextProgressCallback",
    "RegenerateAudioRequest",
    "RegenerateFieldResult",
]
