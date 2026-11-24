from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.repositories.text_repository import TextRepository
from multilang.services.provider_response_cache import (
    ProviderCacheKey,
    ProviderResponseCacheService,
)


def test_provider_response_cache_reuses_identical_key_and_misses_prompt_version() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = ProviderResponseCacheService(TextRepository(Session(engine)))
    key = ProviderCacheKey.from_prompt(
        provider="fake", model="m", task_type="sentence", language="pl", item_key="w", prompt_version="v1", prompt={"x": 1}
    )

    service.put(key, {"sentence": "W domu.", "provenance": {}})

    assert service.get(key).response["sentence"] == "W domu."
    changed = ProviderCacheKey.from_prompt(
        provider="fake", model="m", task_type="sentence", language="pl", item_key="w", prompt_version="v2", prompt={"x": 1}
    )
    assert service.get(changed) is None


def test_long_prompt_versions_fit_persisted_cache_key_without_collisions() -> None:
    version = "text-generation-v1/vocabulary-entry-v1/word-list-short-sentence-v1"
    parameters = dict(
        provider="fake", model="m", task_type="sentence", language="en",
        item_key="harbor", prompt={"word": "harbor"},
    )
    first = ProviderCacheKey.from_prompt(**parameters, prompt_version=version)
    repeat = ProviderCacheKey.from_prompt(**parameters, prompt_version=version)
    changed = ProviderCacheKey.from_prompt(**parameters, prompt_version=version + "-revised")

    assert len(first.prompt_version) <= 64
    assert first.prompt_version == repeat.prompt_version
    assert first.prompt_version != changed.prompt_version

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    cache = ProviderResponseCacheService(TextRepository(Session(engine)))
    cache.put(first, {"sentence": "The harbor is quiet."})
    assert cache.get(repeat).response["sentence"] == "The harbor is quiet."
    assert cache.get(changed) is None
