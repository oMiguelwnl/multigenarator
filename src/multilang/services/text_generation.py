"""Typed boundaries and orchestration for Phase 3 text generation."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from multilang.domain.text_quality import TextProvenance
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate


class SentenceGenerationRequest(BaseModel):
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    definitions_html: str | None = None
    target_language: str = Field(min_length=2)
    translation_target_language: str = Field(min_length=2)

    @classmethod
    def from_candidate(
        cls,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
    ) -> "SentenceGenerationRequest":
        if candidate.grounding_status is not GroundingStatus.GROUNDED:
            raise ValueError("sentence generation requires a grounded lexical candidate")
        return cls(
            display_form=candidate.display_form,
            lemma=candidate.lemma,
            definitions_html=candidate.definitions_html,
            target_language=deck_language.value,
            translation_target_language=candidate.translation_target_language,
        )


class SentenceGenerationResult(BaseModel):
    sentence: str = Field(min_length=1)
    intended_sense: str | None = None
    uncertainty_notes: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class SentenceTranslationRequest(BaseModel):
    sentence: str = Field(min_length=1)
    translation_target_language: str = Field(min_length=2)
    intended_sense: str | None = None
    template_kind: str | None = None

    @classmethod
    def from_sentence(
        cls,
        *,
        sentence_result: SentenceGenerationResult,
        translation_target_language: str,
    ) -> "SentenceTranslationRequest":
        return cls(
            sentence=sentence_result.sentence,
            translation_target_language=translation_target_language,
            intended_sense=sentence_result.intended_sense,
            template_kind=str(sentence_result.provenance.get("template_kind"))
            if sentence_result.provenance.get("template_kind")
            else None,
        )


class SentenceTranslationResult(BaseModel):
    translation: str = Field(min_length=1)
    provenance: dict[str, Any] = Field(default_factory=dict)


class SentenceGenerationFallback(BaseModel):
    sentence_result: SentenceGenerationResult


class GeneratedSentence(BaseModel):
    text: str = Field(min_length=1)
    target_language: str = Field(min_length=2)
    intended_sense: str | None = None
    uncertainty_notes: list[str] = Field(default_factory=list)
    provenance: TextProvenance


class GeneratedTranslation(BaseModel):
    text: str = Field(min_length=1)
    target_language: str = Field(min_length=2)
    provenance: TextProvenance


class GeneratedTextBundle(BaseModel):
    sentence: GeneratedSentence
    translation: GeneratedTranslation


class TextGenerationService:
    """Generate a sentence first, then a sentence-faithful translation."""

    def __init__(
        self,
        *,
        sentence_adapter: SentenceGenerationAdapter,
        translation_adapter: SentenceTranslationAdapter,
    ) -> None:
        self._sentence_adapter = sentence_adapter
        self._translation_adapter = translation_adapter

    def generate_bundle(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
    ) -> GeneratedTextBundle:
        sentence_request = SentenceGenerationRequest.from_candidate(
            candidate=candidate,
            deck_language=deck_language,
        )
        sentence_result = self._sentence_adapter.generate_sentence(sentence_request)

        translation_request = SentenceTranslationRequest.from_sentence(
            sentence_result=sentence_result,
            translation_target_language=candidate.translation_target_language,
        )
        return self._build_bundle(
            sentence_result=sentence_result,
            candidate=candidate,
            deck_language=deck_language,
            translation_request=translation_request,
        )

    def generate_bundle_from_fallback(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        fallback: SentenceGenerationFallback,
    ) -> GeneratedTextBundle:
        sentence_result = fallback.sentence_result
        translation_request = SentenceTranslationRequest.from_sentence(
            sentence_result=sentence_result,
            translation_target_language=candidate.translation_target_language,
        )
        return self._build_bundle(
            sentence_result=sentence_result,
            candidate=candidate,
            deck_language=deck_language,
            translation_request=translation_request,
        )

    def _build_bundle(
        self,
        *,
        sentence_result: SentenceGenerationResult,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        translation_request: SentenceTranslationRequest,
    ) -> GeneratedTextBundle:
        translation_result = self._translation_adapter.translate_sentence(translation_request)

        return GeneratedTextBundle(
            sentence=GeneratedSentence(
                text=sentence_result.sentence,
                target_language=deck_language.value,
                intended_sense=sentence_result.intended_sense,
                uncertainty_notes=[note.strip() for note in sentence_result.uncertainty_notes if note.strip()],
                provenance=_normalize_provenance(sentence_result.provenance),
            ),
            translation=GeneratedTranslation(
                text=translation_result.translation,
                target_language=candidate.translation_target_language,
                provenance=_normalize_provenance(translation_result.provenance),
            ),
        )


class SentenceGenerationAdapter(Protocol):
    def generate_sentence(self, request: SentenceGenerationRequest) -> SentenceGenerationResult: ...


class SentenceTranslationAdapter(Protocol):
    def translate_sentence(self, request: SentenceTranslationRequest) -> SentenceTranslationResult: ...


def _normalize_provenance(payload: dict[str, Any]) -> TextProvenance:
    metadata = dict(payload)
    provider = metadata.pop("provider", None)
    model = metadata.pop("model", None)
    version = metadata.pop("version", None)
    source = provider or metadata.pop("source", "adapter")
    return TextProvenance(
        source=str(source),
        provider=provider,
        model=model,
        version=version,
        metadata=metadata,
    )


__all__ = [
    "GeneratedSentence",
    "SentenceGenerationFallback",
    "GeneratedTextBundle",
    "GeneratedTranslation",
    "SentenceGenerationAdapter",
    "SentenceGenerationRequest",
    "SentenceGenerationResult",
    "SentenceTranslationAdapter",
    "SentenceTranslationRequest",
    "SentenceTranslationResult",
    "TextGenerationService",
]
