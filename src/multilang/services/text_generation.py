"""Typed boundaries and orchestration for Phase 3 text generation."""

from __future__ import annotations

from hashlib import sha256
import re
from time import perf_counter
from typing import Any, Callable, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multilang.domain.korean import KoreanLexicalIdentity, KoreanTextError, canonicalize_korean
from multilang.domain.private_processing import (
    PrivateProcessingReceipt,
    PrivateProcessingRefusalReason,
    private_text_sha256,
)
from multilang.domain.text_quality import TextProvenance
from multilang.domain.jobs import SupportedLanguage
from multilang.domain.lexicon import GroundingStatus, LexicalCardCandidate
from multilang.security.redaction import redact_sensitive_text
from multilang.services.private_context import (
    PrivateContextBroker,
    PrivateContextDisclosureRequest,
    PrivateProviderCallbackResult,
    PrivateProviderContextRequest,
)
from multilang.services.rate_limit import RateLimiter
from multilang.services.provider_response_cache import ProviderCacheKey, ProviderResponseCacheService
from multilang.services.provider_retry import ProviderCircuitBreaker, ProviderRetryContext, retry_provider_call
from multilang.repositories.provider_call_log_repository import ProviderCallLogCreate

_CONTEXT_TOKEN_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
_PRIVATE_PATH_RE = re.compile(
    r"(?i)(?:\b[A-Z]:\\(?:[^\s\\]+\\)*[^\s\\]+|(?:file://)?/(?:Users|home)/[^\s]+)"
)
_ANALYZER_DUMP_RE = re.compile(
    r"(?is)\b(?:Token|Korean(?:AnalysisAlternative|MorphemeEvidence|MorphologyResult|WordAnalysis))\s*\([^)]*\)"
)
_PROMPT_INJECTION_RE = re.compile(
    r"(?i)\b(?:ignore|disregard)\s+(?:all|previous|above)\s+instructions?\b"
    r"|\b(?:override|replace|change|set)\s+(?:the\s+)?"
    r"(?:lemma|part[_ -]?of[_ -]?speech|pos|sense(?:_id)?|morpheme[_ -]?signature|"
    r"analyzer[_ -]?fingerprint|approval(?:_status)?)[^\n.!?]*"
)
_IDENTITY_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?:lemma|part[_ -]?of[_ -]?speech|pos|sense(?:_id)?|"
    r"morpheme[_ -]?signature|analyzer[_ -]?fingerprint|approval(?:_status)?)"
    r"\s*[:=]\s*[^\s,;]+"
)
_HEX = frozenset("0123456789abcdef")
KOREAN_HIGHLIGHT_PRIVATE_ROUTE_ID = "korean-highlight-microexample"
KOREAN_HIGHLIGHT_PRIVATE_PURPOSE = "highlight_microexample_context"
PrivateContextBrokerFactory = Callable[[Callable[[PrivateProviderContextRequest], object]], PrivateContextBroker]


class PrivateContextAuthorizationError(KoreanTextError):
    """Content-free refusal for Korean private highlight provider context."""

    def __init__(self, reason_code: str | PrivateProcessingRefusalReason, *, status: str = "refused") -> None:
        self.reason_code = reason_code.value if isinstance(reason_code, PrivateProcessingRefusalReason) else reason_code
        self.status = status
        super().__init__(f"Korean private context unavailable: {self.reason_code}")


class KoreanSelectorAttemptContext(BaseModel):
    """Trusted orchestration metadata for one bounded Korean provider attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    stage: Literal["initial", "repair"]
    ordinal: int = Field(ge=1, le=3)
    cache_identity: str = Field(min_length=64, max_length=64)
    rejected_candidate_sha256s: tuple[str, ...] = Field(default_factory=tuple, max_length=2)
    rejection_codes: tuple[str, ...] = Field(default_factory=tuple, max_length=16)

    @field_validator("cache_identity", "rejected_candidate_sha256s")
    @classmethod
    def hashes_must_be_sha256(cls, value: str | tuple[str, ...]) -> str | tuple[str, ...]:
        values = (value,) if isinstance(value, str) else value
        for item in values:
            if len(item) != 64 or any(character not in _HEX for character in item):
                raise ValueError("Korean selector hashes must be lowercase SHA-256")
        return value

    @field_validator("rejection_codes")
    @classmethod
    def rejection_codes_must_be_controlled(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(item.strip() for item in value)
        if normalized != value or len(normalized) != len(set(normalized)):
            raise ValueError("Korean selector rejection codes must be controlled")
        if any(
            not item
            or len(item) > 64
            or any(not (character.isascii() and (character.isalnum() or character in "._:-")) for character in item)
            for item in normalized
        ):
            raise ValueError("Korean selector rejection codes must be controlled")
        return value


class SentenceGenerationRequest(BaseModel):
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    definitions_html: str | None = None
    target_language: str = Field(min_length=2)
    translation_target_language: str = Field(min_length=2)
    source_type: str | None = None
    highlight_context: str | None = None
    korean_identity: KoreanLexicalIdentity | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    korean_selector_attempt: KoreanSelectorAttemptContext | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @model_validator(mode="before")
    @classmethod
    def sanitize_private_korean_context(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        context = data.get("highlight_context")
        display_form = data.get("display_form")
        lemma = data.get("lemma")
        if (
            data.get("target_language") == SupportedLanguage.KO.value
            and data.get("source_type") == "kindle-highlights"
            and isinstance(context, str)
            and isinstance(display_form, str)
            and isinstance(lemma, str)
        ):
            data["highlight_context"] = _sanitize_korean_highlight_context(
                context,
                display_form=display_form,
                lemma=lemma,
            )
        return data

    @model_validator(mode="after")
    def korean_identity_must_match_language(self) -> "SentenceGenerationRequest":
        if self.target_language == SupportedLanguage.KO.value:
            if self.korean_identity is None:
                raise ValueError("Korean sentence request requires a persisted Korean identity")
            if self.lemma != self.korean_identity.lemma:
                raise ValueError("Korean sentence request must match persisted Korean identity")
            if self.translation_target_language != SupportedLanguage.PT.value:
                raise ValueError("Korean sentence translation target must be Portuguese")
        elif self.korean_identity is not None:
            raise ValueError("non-Korean sentence request must not carry Korean identity")
        if self.target_language != SupportedLanguage.KO.value and self.korean_selector_attempt is not None:
            raise ValueError("non-Korean sentence request must not carry Korean selector attempt")
        if (
            self.target_language == SupportedLanguage.KO.value
            and self.source_type == "kindle-highlights"
            and self.highlight_context
        ):
            self.highlight_context = _sanitize_korean_highlight_context(
                self.highlight_context,
                display_form=self.display_form,
                lemma=self.lemma,
            )
        return self

    @classmethod
    def from_candidate(
        cls,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        source_type: str | None = None,
        highlight_context: str | None = None,
        korean_selector_attempt: KoreanSelectorAttemptContext | None = None,
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
            korean_identity=candidate.korean_identity,
            korean_selector_attempt=korean_selector_attempt,
        )


class DefinitionGenerationRequest(BaseModel):
    display_form: str = Field(min_length=1)
    lemma: str = Field(min_length=1)
    source_language: str = Field(min_length=2)
    target_language: str = Field(min_length=2)
    part_of_speech: str | None = None
    korean_identity: KoreanLexicalIdentity | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @model_validator(mode="after")
    def korean_identity_must_match_language(self) -> "DefinitionGenerationRequest":
        if self.source_language == SupportedLanguage.KO.value:
            identity = self.korean_identity
            if identity is None:
                raise ValueError("Korean definition request requires a persisted Korean identity")
            if self.lemma != identity.lemma or (
                self.part_of_speech is not None
                and self.part_of_speech != identity.part_of_speech
            ):
                raise ValueError("Korean definition request must match persisted Korean identity")
            if self.target_language != SupportedLanguage.PT.value:
                raise ValueError("Korean definition target must be Portuguese")
        elif self.korean_identity is not None:
            raise ValueError("non-Korean definition request must not carry Korean identity")
        return self


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
        retry_attempts: int = 3,
        retry_base_delay_seconds: float = 1.0,
        retry_max_delay_seconds: float = 30.0,
        retry_jitter_ratio: float = 0.0,
        prompt_version: str = "text-generation-v1",
        private_context_broker_factory: PrivateContextBrokerFactory | None = None,
    ) -> None:
        self._sentence_adapter = sentence_adapter
        self._translation_adapter = translation_adapter
        self._provider_cache = provider_cache
        self._provider_call_logger = provider_call_logger
        self._circuit_breaker = circuit_breaker
        self._retry_attempts = retry_attempts
        self._retry_base_delay_seconds = retry_base_delay_seconds
        self._retry_max_delay_seconds = retry_max_delay_seconds
        self._retry_jitter_ratio = retry_jitter_ratio
        self._prompt_version = prompt_version
        self._private_context_broker_factory = private_context_broker_factory

    def generate_bundle(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        source_type: str | None = None,
        highlight_context: str | None = None,
        rate_limiter: RateLimiter | None = None,
        job_id: str | None = None,
        korean_selector_attempt: KoreanSelectorAttemptContext | None = None,
        private_context_request: PrivateContextDisclosureRequest | None = None,
    ) -> GeneratedTextBundle:
        if _requires_korean_private_context(
            deck_language=deck_language,
            source_type=source_type,
            highlight_context=highlight_context,
        ):
            sentence_result = self._generate_private_korean_highlight_sentence(
                candidate=candidate,
                deck_language=deck_language,
                source_type=source_type,
                highlight_context=highlight_context or "",
                private_context_request=private_context_request,
                rate_limiter=rate_limiter,
                job_id=job_id,
                korean_selector_attempt=korean_selector_attempt,
            )
        else:
            sentence_request = SentenceGenerationRequest.from_candidate(
                candidate=candidate,
                deck_language=deck_language,
                source_type=source_type,
                highlight_context=highlight_context,
                korean_selector_attempt=korean_selector_attempt,
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
        if deck_language is SupportedLanguage.KO:
            identity = candidate.korean_identity
            if identity is None:
                raise ValueError("Korean sentence handoff requires persisted identity")
            sentence_result = _canonicalize_korean_sentence_result(
                sentence_result,
                identity=identity,
            )
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

    def translate_sentence_text(
        self,
        *,
        sentence: str,
        translation_target_language: str,
        deck_language: SupportedLanguage,
        intended_sense: str | None = None,
        rate_limiter: RateLimiter | None = None,
        job_id: str | None = None,
        item_key: str | None = None,
    ) -> GeneratedTranslation:
        """Translate a specific sentence.

        Used when the generated sentence is replaced after ``generate_bundle``
        (e.g. the structured Latin sentence override) so the bundle translation
        is regenerated for the new sentence instead of staying tied to the old
        one.
        """

        if translation_target_language == deck_language.value:
            return GeneratedTranslation(
                text=sentence,
                target_language=translation_target_language,
                provenance=_normalize_provenance({"source": "same-language-translator"}),
            )
        request = SentenceTranslationRequest(
            sentence=sentence,
            translation_target_language=translation_target_language,
            intended_sense=intended_sense,
        )
        if rate_limiter is not None:
            rate_limiter.wait()
        translation_result = self._translate_sentence(request, job_id=job_id, item_key=item_key)
        return GeneratedTranslation(
            text=translation_result.translation,
            target_language=translation_target_language,
            provenance=_normalize_provenance(translation_result.provenance),
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
        if deck_language is SupportedLanguage.KO:
            identity = candidate.korean_identity
            if identity is None:
                raise ValueError("Korean sentence handoff requires persisted identity")
            sentence_result = _canonicalize_korean_sentence_result(
                sentence_result,
                identity=identity,
            )
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
                cached_result = SentenceGenerationResult.model_validate(cached.response)
                return (
                    _canonicalize_korean_sentence_result(
                        cached_result,
                        identity=request.korean_identity,
                    )
                    if request.target_language == SupportedLanguage.KO.value
                    else cached_result
                )

        result = self._call_with_telemetry(
            lambda: self._sentence_adapter.generate_sentence(request),
            operation="sentence",
            adapter=self._sentence_adapter,
            request_payload=request.model_dump(mode="json"),
            job_id=job_id,
            item_key=item_key,
        )
        if request.target_language == SupportedLanguage.KO.value:
            result = _canonicalize_korean_sentence_result(
                result,
                identity=request.korean_identity,
            )
        if self._provider_cache is not None:
            self._provider_cache.put(key, result.model_dump(mode="json"), metadata={"provider": key.provider, "model": key.model})
        return result

    def _generate_private_korean_highlight_sentence(
        self,
        *,
        candidate: LexicalCardCandidate,
        deck_language: SupportedLanguage,
        source_type: str | None,
        highlight_context: str,
        private_context_request: PrivateContextDisclosureRequest | None,
        rate_limiter: RateLimiter | None = None,
        job_id: str | None = None,
        korean_selector_attempt: KoreanSelectorAttemptContext | None = None,
    ) -> SentenceGenerationResult:
        if private_context_request is None or self._private_context_broker_factory is None:
            raise PrivateContextAuthorizationError(PrivateProcessingRefusalReason.MISSING_CAPABILITY)
        _validate_private_text_generation_request(
            private_context_request,
            candidate=candidate,
            adapter=self._sentence_adapter,
            highlight_context=highlight_context,
            job_id=job_id,
        )

        captured_result: SentenceGenerationResult | None = None
        captured_provider_request: PrivateProviderContextRequest | None = None

        def disclose_callback(provider_request: PrivateProviderContextRequest) -> PrivateProviderCallbackResult:
            nonlocal captured_result, captured_provider_request
            _validate_private_provider_request(provider_request, adapter=self._sentence_adapter)
            captured_provider_request = provider_request
            sentence_request = SentenceGenerationRequest.from_candidate(
                candidate=candidate,
                deck_language=deck_language,
                source_type=source_type,
                highlight_context=provider_request.context,
                korean_selector_attempt=korean_selector_attempt,
            )
            key = _cache_key_for_request(
                "sentence",
                sentence_request,
                adapter=self._sentence_adapter,
                prompt_version=self._prompt_version,
            )
            if self._provider_cache is not None:
                cached = self._provider_cache.get(key)
                if cached is not None:
                    cached_result = SentenceGenerationResult.model_validate(cached.response)
                    captured_result = _canonicalize_korean_sentence_result(
                        cached_result,
                        identity=sentence_request.korean_identity,
                    )
                    return PrivateProviderCallbackResult(
                        status="success",
                        output_sha256=private_text_sha256(captured_result.sentence),
                    )

            if rate_limiter is not None:
                rate_limiter.wait()
            result = self._call_private_sentence_adapter_once(
                sentence_request,
                provider_request=provider_request,
                job_id=job_id,
                item_key=candidate.lemma_key,
            )
            captured_result = _canonicalize_korean_sentence_result(
                result,
                identity=sentence_request.korean_identity,
            )
            if self._provider_cache is not None:
                self._provider_cache.put(
                    key,
                    captured_result.model_dump(mode="json"),
                    metadata={
                        "provider": key.provider,
                        "model": key.model,
                        "private_context_sha256": provider_request.context_sha256,
                    },
                )
            return PrivateProviderCallbackResult(
                status="success",
                output_sha256=private_text_sha256(captured_result.sentence),
            )

        try:
            broker = self._private_context_broker_factory(disclose_callback)
            disclosure = broker.disclose(private_context_request)
        except Exception as exc:
            raise PrivateContextAuthorizationError(
                PrivateProcessingRefusalReason.PROVIDER_UNKNOWN_RESULT,
                status="failed_unknown",
            ) from exc

        if disclosure.status != "disclosed" or disclosure.receipt is None:
            raise PrivateContextAuthorizationError(
                _private_disclosure_failure_reason(disclosure),
                status=disclosure.status,
            )
        if captured_result is None or captured_provider_request is None:
            raise PrivateContextAuthorizationError(
                PrivateProcessingRefusalReason.REPLAY_OR_CLOSED_STATE,
                status=disclosure.status,
            )
        return _annotate_private_korean_microexample(
            captured_result,
            provider_request=captured_provider_request,
            receipt=disclosure.receipt,
            prompt_version=self._prompt_version,
        )

    def _call_private_sentence_adapter_once(
        self,
        request: SentenceGenerationRequest,
        *,
        provider_request: PrivateProviderContextRequest,
        job_id: str | None,
        item_key: str | None,
    ) -> SentenceGenerationResult:
        started = perf_counter()
        prompt_hash = _safe_hash(request.model_dump(mode="json"))
        try:
            idempotent_method = getattr(self._sentence_adapter, "generate_sentence_with_idempotency", None)
            if provider_request.idempotency_key is not None:
                if not callable(idempotent_method):
                    raise RuntimeError("private idempotency route unsupported")
                result = idempotent_method(request, idempotency_key=provider_request.idempotency_key)
            else:
                result = self._sentence_adapter.generate_sentence(request)
        except Exception as exc:
            self._log_provider_call(
                operation="sentence",
                provider=provider_request.provider,
                model=provider_request.model,
                job_id=job_id,
                item_key=item_key,
                status="failure",
                latency_ms=_elapsed_ms(started),
                error_code=type(exc).__name__,
                error_summary=f"{type(exc).__name__}: redacted private provider failure",
                prompt_hash=prompt_hash,
                route_policy_sha256=provider_request.policy_sha256,
            )
            raise
        provenance = result.provenance or {}
        self._log_provider_call(
            operation="sentence",
            provider=provider_request.provider,
            model=provider_request.model,
            job_id=job_id,
            item_key=item_key,
            status="success",
            attempt=1,
            latency_ms=_elapsed_ms(started),
            prompt_hash=prompt_hash,
            response_hash=_safe_hash(result.model_dump(mode="json")),
            route_policy_sha256=provider_request.policy_sha256,
            input_tokens=provenance.get("input_tokens"),
            output_tokens=provenance.get("output_tokens"),
            total_tokens=provenance.get("total_tokens"),
            estimated_cost=provenance.get("estimated_cost"),
        )
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
            success_attempt = 1

            def record_success_attempt(attempt: int) -> None:
                nonlocal success_attempt
                success_attempt = attempt

            retry_context = ProviderRetryContext(
                provider=provider,
                operation=operation,
                model=str(model) if model else None,
                job_id=job_id,
                item_key=item_key,
            )
            result = retry_provider_call(
                operation_func,
                attempts=self._retry_attempts,
                base_delay_seconds=self._retry_base_delay_seconds,
                max_delay_seconds=self._retry_max_delay_seconds,
                jitter_ratio=self._retry_jitter_ratio,
                context=retry_context,
                circuit_breaker=self._circuit_breaker,
                call_logger=self._provider_call_logger,
                success_attempt_callback=record_success_attempt,
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
            attempt=success_attempt,
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


def _requires_korean_private_context(
    *,
    deck_language: SupportedLanguage,
    source_type: str | None,
    highlight_context: str | None,
) -> bool:
    return (
        deck_language is SupportedLanguage.KO
        and source_type == "kindle-highlights"
        and bool((highlight_context or "").strip())
    )


def _validate_private_text_generation_request(
    request: PrivateContextDisclosureRequest,
    *,
    candidate: LexicalCardCandidate,
    adapter: object,
    highlight_context: str,
    job_id: str | None,
) -> None:
    if request.capability is None:
        raise PrivateContextAuthorizationError(PrivateProcessingRefusalReason.MISSING_CAPABILITY)
    if job_id is not None and request.job_id != job_id:
        raise PrivateContextAuthorizationError(PrivateProcessingRefusalReason.BINDING_MISMATCH)
    if private_text_sha256(highlight_context) != request.excerpt_sha256:
        raise PrivateContextAuthorizationError(PrivateProcessingRefusalReason.STALE_EXCERPT)
    candidate_targets = {
        value
        for value in (candidate.submitted_form, candidate.display_form, candidate.lemma)
        if isinstance(value, str) and value.strip()
    }
    if request.target_text_sha256 not in {private_text_sha256(value) for value in candidate_targets}:
        raise PrivateContextAuthorizationError(PrivateProcessingRefusalReason.TARGET_MISMATCH)
    _validate_private_route_binding(
        provider=request.provider,
        model=request.model,
        route_id=request.route_id,
        provider_route_sha256=request.provider_route_sha256,
        adapter=adapter,
    )
    capability = request.capability
    if (
        capability.provider != request.provider
        or capability.model != request.model
        or capability.route_id != request.route_id
        or capability.provider_route_sha256 != request.provider_route_sha256
        or capability.purpose != KOREAN_HIGHLIGHT_PRIVATE_PURPOSE
        or request.purpose != KOREAN_HIGHLIGHT_PRIVATE_PURPOSE
    ):
        raise PrivateContextAuthorizationError(PrivateProcessingRefusalReason.BINDING_MISMATCH)


def _validate_private_provider_request(
    request: PrivateProviderContextRequest,
    *,
    adapter: object,
) -> None:
    _validate_private_route_binding(
        provider=request.provider,
        model=request.model,
        route_id=request.route_id,
        provider_route_sha256=request.provider_route_sha256,
        adapter=adapter,
    )
    if request.purpose != KOREAN_HIGHLIGHT_PRIVATE_PURPOSE:
        raise PrivateContextAuthorizationError(PrivateProcessingRefusalReason.BINDING_MISMATCH)


def _validate_private_route_binding(
    *,
    provider: str,
    model: str,
    route_id: str,
    provider_route_sha256: str,
    adapter: object,
) -> None:
    expected_provider = _adapter_provider(adapter)
    expected_model = _adapter_model(adapter)
    expected_hash = _private_provider_route_sha256(
        provider=expected_provider,
        model=expected_model,
        route_id=KOREAN_HIGHLIGHT_PRIVATE_ROUTE_ID,
    )
    if (
        provider != expected_provider
        or model != expected_model
        or route_id != KOREAN_HIGHLIGHT_PRIVATE_ROUTE_ID
        or provider_route_sha256 != expected_hash
    ):
        raise PrivateContextAuthorizationError(PrivateProcessingRefusalReason.BINDING_MISMATCH)


def _private_disclosure_failure_reason(disclosure: object) -> PrivateProcessingRefusalReason:
    refusal = getattr(disclosure, "refusal", None)
    reason = getattr(refusal, "reason_code", None)
    if isinstance(reason, PrivateProcessingRefusalReason):
        return reason
    if isinstance(reason, str):
        try:
            return PrivateProcessingRefusalReason(reason)
        except ValueError:
            pass
    return PrivateProcessingRefusalReason.REPLAY_OR_CLOSED_STATE


def _annotate_private_korean_microexample(
    result: SentenceGenerationResult,
    *,
    provider_request: PrivateProviderContextRequest,
    receipt: PrivateProcessingReceipt,
    prompt_version: str,
) -> SentenceGenerationResult:
    microexample: dict[str, object] = {
        "microexample_sha256": private_text_sha256(result.sentence),
        "context_sha256": provider_request.context_sha256,
        "tokenization_rule_id": provider_request.tokenization_rule_id,
        "context_token_count": provider_request.token_count,
        "evidence_policy": "contextual",
        "review_state": "needs_review",
    }
    if _private_microexample_copy_policy_violation(result.sentence, provider_request.context):
        microexample["review_reason"] = "source_copy_policy_violation"
    provenance: dict[str, Any] = {
        "source": "provider-text-generator",
        "provider": provider_request.provider,
        "model": provider_request.model,
        "version": prompt_version,
        "private_context_receipt_sha256": receipt.receipt_sha256,
        "private_microexample": microexample,
    }
    for key in ("input_tokens", "output_tokens", "total_tokens", "estimated_cost"):
        value = result.provenance.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            provenance[key] = value
    return result.model_copy(update={"provenance": provenance})


def _private_microexample_copy_policy_violation(sentence: str, context: str) -> bool:
    normalized_sentence = " ".join(canonicalize_korean(sentence).split())
    normalized_context = " ".join(canonicalize_korean(context).split())
    if not normalized_sentence or not normalized_context:
        return False
    if normalized_sentence == normalized_context:
        return True
    if len(normalized_context) >= 12 and normalized_context in normalized_sentence:
        return True
    sentence_tokens = _CONTEXT_TOKEN_RE.findall(normalized_sentence)
    context_tokens = _CONTEXT_TOKEN_RE.findall(normalized_context)
    if len(sentence_tokens) < 4 or len(context_tokens) < 4:
        return False
    sentence_windows = {
        tuple(sentence_tokens[index : index + 4])
        for index in range(0, len(sentence_tokens) - 3)
    }
    return any(
        tuple(context_tokens[index : index + 4]) in sentence_windows
        for index in range(0, len(context_tokens) - 3)
    )


def _adapter_provider(adapter: object) -> str:
    return str(getattr(adapter, "provider", adapter.__class__.__name__))


def _adapter_model(adapter: object) -> str:
    return str(getattr(adapter, "model", "default"))


def _private_provider_route_sha256(*, provider: str, model: str, route_id: str) -> str:
    return sha256(f"{provider}\n{model}\n{route_id}".encode("utf-8")).hexdigest()


def _canonicalize_korean_sentence_result(
    result: SentenceGenerationResult,
    *,
    identity: KoreanLexicalIdentity | None,
) -> SentenceGenerationResult:
    if identity is None:
        raise ValueError("Korean sentence result requires persisted identity")
    uncertainty_notes = [
        canonicalize_korean(note) if note.strip() else note
        for note in result.uncertainty_notes
    ]
    return result.model_copy(
        update={
            "sentence": canonicalize_korean(result.sentence),
            "intended_sense": identity.sense_id,
            "uncertainty_notes": uncertainty_notes,
        }
    )


def _sanitize_korean_highlight_context(
    value: str,
    *,
    display_form: str,
    lemma: str,
    max_tokens: int = 24,
) -> str:
    sanitized = redact_sensitive_text(value)
    sanitized = _PRIVATE_PATH_RE.sub("[REDACTED]", sanitized)
    sanitized = _ANALYZER_DUMP_RE.sub("[REDACTED]", sanitized)
    sanitized = _PROMPT_INJECTION_RE.sub("[REDACTED]", sanitized)
    sanitized = _IDENTITY_ASSIGNMENT_RE.sub("[REDACTED]", sanitized)
    tokens = _CONTEXT_TOKEN_RE.findall(sanitized)
    if not tokens:
        return ""
    match_keys = {display_form.casefold(), lemma.casefold()}
    center = next(
        (index for index, token in enumerate(tokens) if token.casefold() in match_keys),
        0,
    )
    half_window = max_tokens // 2
    start = max(0, center - half_window)
    end = min(len(tokens), start + max_tokens)
    start = max(0, end - max_tokens)
    return " ".join(tokens[start:end])


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
    "PrivateContextAuthorizationError",
    "SentenceGenerationAdapter",
    "SentenceGenerationRequest",
    "SentenceGenerationResult",
    "SentenceTranslationAdapter",
    "SentenceTranslationRequest",
    "SentenceTranslationResult",
    "TextGenerationService",
]
