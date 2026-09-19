"""Bounded definition transport sharing the application's provider controls."""

from hashlib import sha256
from time import perf_counter

from pydantic import ValidationError

from multilang.repositories.provider_call_log_repository import ProviderCallLogCreate
from multilang.services.content.definition_policy import DEFINITION_POLICY_VERSION
from multilang.services.provider_response_cache import (
    ProviderCacheKey,
    ProviderResponseCacheService,
)
from multilang.services.provider_retry import (
    ProviderCircuitBreaker,
    ProviderRetryContext,
    retry_provider_call,
    safe_provider_error_summary,
)
from multilang.services.text_generation import (
    DefinitionGenerationAdapter,
    DefinitionGenerationRequest,
    DefinitionGenerationResult,
)


class DefinitionGenerationService:
    """Generate a draft; lexical admission separately checks independent evidence."""

    def __init__(
        self,
        *,
        adapter: DefinitionGenerationAdapter,
        provider_cache: ProviderResponseCacheService | None = None,
        provider_call_logger: object | None = None,
        circuit_breaker: ProviderCircuitBreaker | None = None,
        retry_attempts: int = 3,
        retry_base_delay_seconds: float = 1,
        retry_max_delay_seconds: float = 30,
        retry_jitter_ratio: float = 0,
        prompt_version: str = DEFINITION_POLICY_VERSION,
    ) -> None:
        if not 1 <= retry_attempts <= 5:
            raise ValueError("definition retry attempts must be between 1 and 5")
        self.adapter = adapter
        self.cache = provider_cache
        self.logger = provider_call_logger
        self.circuit = circuit_breaker
        self.attempts = retry_attempts
        self.base_delay = max(0, min(retry_base_delay_seconds, 30))
        self.max_delay = max(0, min(retry_max_delay_seconds, 30))
        self.jitter = max(0, min(retry_jitter_ratio, 1))
        self.prompt_version = prompt_version

    def generate_definition(
        self, request: DefinitionGenerationRequest
    ) -> DefinitionGenerationResult:
        provider = str(getattr(self.adapter, "provider", type(self.adapter).__name__))
        model = str(getattr(self.adapter, "model", "default"))
        schema_hash = sha256(
            str(DefinitionGenerationResult.model_json_schema()).encode()
        ).hexdigest()
        key = ProviderCacheKey.from_prompt(
            provider=provider,
            model=model,
            task_type="definition",
            language=request.target_language,
            prompt_version=self.prompt_version,
            item_key=request.lemma,
            prompt={"request": request.model_dump(mode="json"), "response_schema": schema_hash},
        )
        if self.cache is not None:
            cached = self.cache.get(key)
            if cached is not None:
                try:
                    return DefinitionGenerationResult.model_validate(cached.response)
                except ValidationError:
                    # Invalid/stale entries are misses; a successful call replaces them.
                    pass
        context = ProviderRetryContext(
            provider=provider,
            model=model,
            operation="definition",
            prompt_hash=key.prompt_hash,
            response_schema_sha256=schema_hash,
        )
        started = perf_counter()
        attempt = 0

        def produce() -> DefinitionGenerationResult:
            nonlocal attempt
            attempt += 1
            return DefinitionGenerationResult.model_validate(
                self.adapter.generate_definition(request), from_attributes=True
            )

        try:
            result = retry_provider_call(
                produce,
                attempts=self.attempts,
                base_delay_seconds=self.base_delay,
                max_delay_seconds=self.max_delay,
                jitter_ratio=self.jitter,
                context=context,
                circuit_breaker=self.circuit,
                call_logger=self.logger,
            )
        except Exception as exc:
            self._log(
                provider,
                model,
                key,
                started,
                attempt,
                "failure",
                error_code=type(exc).__name__,
                error_summary=safe_provider_error_summary(exc),
            )
            raise
        self._log(
            provider,
            model,
            key,
            started,
            attempt,
            "success",
            response_hash=sha256(result.model_dump_json().encode()).hexdigest(),
        )
        if self.cache is not None:
            self.cache.put(key, result.model_dump(mode="json"), metadata={"draft_only": True})
        return result

    def _log(self, provider, model, key, started, attempt, status, **kwargs):
        if self.logger is not None:
            self.logger.insert(
                ProviderCallLogCreate(
                    provider=provider,
                    model=model,
                    operation="definition",
                    status=status,
                    attempt=max(1, attempt),
                    latency_ms=int((perf_counter() - started) * 1000),
                    prompt_hash=key.prompt_hash,
                    **kwargs,
                )
            )
