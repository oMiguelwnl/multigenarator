"""Persisted cache for normalized provider responses."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderCacheKey:
    provider: str
    model: str
    task_type: str
    language: str
    prompt_version: str
    item_key: str | None = None
    prompt_hash: str | None = None

    @classmethod
    def from_prompt(
        cls,
        *,
        provider: str,
        model: str,
        task_type: str,
        language: str,
        prompt_version: str,
        prompt: object,
        item_key: str | None = None,
    ) -> "ProviderCacheKey":
        prompt_hash = hashlib.sha256(_stable_json(prompt).encode("utf-8")).hexdigest()
        return cls(
            provider=provider,
            model=model,
            task_type=task_type,
            language=language,
            prompt_version=prompt_version,
            item_key=item_key,
            prompt_hash=prompt_hash,
        )


@dataclass(frozen=True, slots=True)
class ProviderCachedResponse:
    key: ProviderCacheKey
    response: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderResponseCacheService:
    def __init__(self, repository: object) -> None:
        self.repository = repository

    def get(self, key: ProviderCacheKey) -> ProviderCachedResponse | None:
        getter = getattr(self.repository, "get_provider_response", None)
        return getter(key) if callable(getter) else None

    def put(self, key: ProviderCacheKey, response: dict[str, Any], *, metadata: dict[str, Any] | None = None) -> ProviderCachedResponse:
        record = ProviderCachedResponse(key=key, response=dict(response), metadata=dict(metadata or {}))
        writer = getattr(self.repository, "upsert_provider_response", None)
        return writer(record) if callable(writer) else record

    def get_or_create(self, key: ProviderCacheKey, producer: object) -> ProviderCachedResponse:
        cached = self.get(key)
        if cached is not None:
            return cached
        produced = producer()
        return self.put(key, produced, metadata={"cache": "miss"})


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))


__all__ = ["ProviderCacheKey", "ProviderCachedResponse", "ProviderResponseCacheService"]
