"""Typed boundaries and orchestration for Phase 3 text generation."""

from __future__ import annotations

from hashlib import sha256
from time import perf_counter
from typing import Any, Protocol

from pydantic import BaseModel, Field

from multilang.domain.text_quality import TextProvenance
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate
from multilang.services.rate_limit import RateLimiter
from multilang.services.provider_response_cache import ProviderCacheKey, ProviderResponseCacheService
from multilang.services.provider_retry import ProviderCircuitBreaker, ProviderRetryContext, retry_provider_call
from multilang.repositories.provider_call_log_repository import ProviderCallLogCreate


class SentenceGenerationRequest(BaseModel):
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    definitions_html: str | None = None
    target_language: str = Field(min_length=2)
    translation_target_language: str = Field(min_length=2)
    source_type: str | None = None
    highlight_context: str | None = None

    @classmethod
    def from_candidate(
        cls,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        source_type: str | None = None,
        highlight_context: str | None = None,
    ) -> "SentenceGenerationRequest":
        if candidate.grounding_status is not GroundingStatus.GROUNDED:
            raise ValueError("sentence generation requires a grounded lexical candidate")
        return cls(
            display_form=candidate.display_form,
            lemma=candidate.lemma,
            definitions_html=candidate.definitions_html,
            target_language=deck_language.value,
            translation_target_language=candidate.translation_target_language,
            source_type=source_type,
            highlight_context=highlight_context,
        )


class DefinitionGenerationRequest(BaseModel):
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    source_language: str = Field(min_length=2)
    target_language: str = Field(min_length=2)
    part_of_speech: str | None = None


class DefinitionGenerationResult(BaseModel):
    definitions_html: str = Field(min_length=1)
    provenance: dict[str, Any] = Field(default_factory=dict)


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
        provider_cache: ProviderResponseCacheService | None = None,
        provider_call_logger: Any | None = None,
        circuit_breaker: ProviderCircuitBreaker | None = None,
        prompt_version: str = "text-generation-v1",
    ) -> None:
        self._sentence_adapter = sentence_adapter
        self._translation_adapter = translation_adapter
        self._provider_cache = provider_cache
        self._provider_call_logger = provider_call_logger
        self._circuit_breaker = circuit_breaker
        self._prompt_version = prompt_version

    def generate_bundle(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        source_type: str | None = None,
        highlight_context: str | None = None,
        rate_limiter: RateLimiter | None = None,
        job_id: str | None = None,
    ) -> GeneratedTextBundle:
        sentence_request = SentenceGenerationRequest.from_candidate(
            candidate=candidate,
            deck_language=deck_language,
            source_type=source_type,
            highlight_context=highlight_context,
        )
        if rate_limiter is not None:
            rate_limiter.wait()
        sentence_result = self._generate_sentence(sentence_request, job_id=job_id, item_key=candidate.lemma_key)

        translation_request = SentenceTranslationRequest.from_sentence(
            sentence_result=sentence_result,
            translation_target_language=candidate.translation_target_language,
        )
        return self._build_bundle(
            sentence_result=sentence_result,
            candidate=candidate,
            deck_language=deck_language,
            translation_request=translation_request,
            rate_limiter=rate_limiter,
            job_id=job_id,
        )

    def generate_bundle_from_fallback(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        fallback: SentenceGenerationFallback,
        source_type: str | None = None,
        highlight_context: str | None = None,
        rate_limiter: RateLimiter | None = None,
        job_id: str | None = None,
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
            rate_limiter=rate_limiter,
            job_id=job_id,
        )

    def _build_bundle(
        self,
        *,
        sentence_result: SentenceGenerationResult,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        translation_request: SentenceTranslationRequest,
        rate_limiter: RateLimiter | None = None,
        job_id: str | None = None,
    ) -> GeneratedTextBundle:
        if candidate.translation_target_language == deck_language.value:
            translation_result = SentenceTranslationResult(
                translation=sentence_result.sentence,
                provenance={"source": "same-language-translator"},
            )
        else:
            if rate_limiter is not None:
                rate_limiter.wait()
            translation_result = self._translate_sentence(translation_request, job_id=job_id, item_key=candidate.lemma_key)

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

    def _generate_sentence(self, request: SentenceGenerationRequest, *, job_id: str | None = None, item_key: str | None = None) -> SentenceGenerationResult:
        key = _cache_key_for_request("sentence", request, adapter=self._sentence_adapter, prompt_version=self._prompt_version)
        if self._provider_cache is not None:
            cached = self._provider_cache.get(key)
            if cached is not None:
                return SentenceGenerationResult.model_validate(cached.response)
        result = self._call_with_telemetry(
            lambda: self._sentence_adapter.generate_sentence(request),
            operation="sentence",
            adapter=self._sentence_adapter,
            request_payload=request.model_dump(mode="json"),
            job_id=job_id,
            item_key=item_key,
        )
        if self._provider_cache is not None:
            self._provider_cache.put(key, result.model_dump(mode="json"), metadata={"provider": key.provider, "model": key.model})
        return result

    def _translate_sentence(self, request: SentenceTranslationRequest, *, job_id: str | None = None, item_key: str | None = None) -> SentenceTranslationResult:
        key = _cache_key_for_request("translation", request, adapter=self._translation_adapter, prompt_version=self._prompt_version)
        if self._provider_cache is not None:
            cached = self._provider_cache.get(key)
            if cached is not None:
                return SentenceTranslationResult.model_validate(cached.response)
        result = self._call_with_telemetry(
            lambda: self._translation_adapter.translate_sentence(request),
            operation="translation",
            adapter=self._translation_adapter,
            request_payload=request.model_dump(mode="json"),
            job_id=job_id,
            item_key=item_key,
        )
        if self._provider_cache is not None:
            self._provider_cache.put(key, result.model_dump(mode="json"), metadata={"provider": key.provider, "model": key.model})
        return result

    def _call_with_telemetry(
        self,
        operation_func: Any,
        *,
        operation: str,
        adapter: object,
        request_payload: object,
        job_id: str | None,
        item_key: str | None,
    ) -> Any:
        started = perf_counter()
        prompt_hash = _safe_hash(request_payload)
        provider = str(getattr(adapter, "provider", adapter.__class__.__name__))
        model = getattr(adapter, "model", getattr(adapter, "_model", None))
        try:
            retry_context = ProviderRetryContext(
                provider=provider,
                operation=operation,
                model=str(model) if model else None,
                job_id=job_id,
                item_key=item_key,
            )
            result = retry_provider_call(
                operation_func,
                context=retry_context,
                circuit_breaker=self._circuit_breaker,
                call_logger=self._provider_call_logger,
            )
        except Exception as exc:
            self._log_provider_call(
                operation=operation,
                provider=provider,
                model=str(model) if model else None,
                job_id=job_id,
                item_key=item_key,
                status="failure",
                latency_ms=_elapsed_ms(started),
                error_code=type(exc).__name__,
                error_summary=str(exc),
                prompt_hash=prompt_hash,
            )
            raise
        provenance = getattr(result, "provenance", {}) or {}
        self._log_provider_call(
            operation=operation,
            provider=str(provenance.get("provider") or provider),
            model=str(provenance.get("model") or model) if (provenance.get("model") or model) else None,
            job_id=job_id,
            item_key=item_key,
            status="success",
            latency_ms=_elapsed_ms(started),
            fallback_from=provenance.get("fallback_from"),
            prompt_hash=prompt_hash,
            response_hash=_safe_hash(getattr(result, "model_dump", lambda **_: str(result))(mode="json") if hasattr(result, "model_dump") else str(result)),
            input_tokens=provenance.get("input_tokens"),
            output_tokens=provenance.get("output_tokens"),
            total_tokens=provenance.get("total_tokens"),
            estimated_cost=provenance.get("estimated_cost"),
        )
        return result

    def _log_provider_call(self, **kwargs: Any) -> None:
        if self._provider_call_logger is None:
            return
        self._provider_call_logger.insert(ProviderCallLogCreate(**kwargs))


def _safe_hash(payload: object) -> str:
    return sha256(repr(payload).encode("utf-8")).hexdigest()


def _elapsed_ms(started: float) -> int:
    return max(0, int((perf_counter() - started) * 1000))


def _cache_key_for_request(task_type: str, request: BaseModel, *, adapter: object, prompt_version: str) -> ProviderCacheKey:
    provider = str(getattr(adapter, "provider", adapter.__class__.__name__))
    model = str(getattr(adapter, "model", "default"))
    language = str(getattr(request, "target_language", None) or getattr(request, "translation_target_language", ""))
    item_key = str(getattr(request, "lemma", "") or "") or None
    return ProviderCacheKey.from_prompt(
        provider=provider,
        model=model,
        task_type=task_type,
        language=language,
        prompt_version=prompt_version,
        prompt=request.model_dump(mode="json"),
        item_key=item_key,
    )


class SentenceGenerationAdapter(Protocol):
    def generate_sentence(self, request: SentenceGenerationRequest) -> SentenceGenerationResult: ...


class SentenceTranslationAdapter(Protocol):
    def translate_sentence(self, request: SentenceTranslationRequest) -> SentenceTranslationResult: ...


class DefinitionGenerationAdapter(Protocol):
    def generate_definition(self, request: DefinitionGenerationRequest) -> DefinitionGenerationResult: ...


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
    "DefinitionGenerationAdapter",
    "DefinitionGenerationRequest",
    "DefinitionGenerationResult",
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
