from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from multilang.db.base import Base
from multilang.repositories.text_repository import TextRepository
from multilang.services.provider_response_cache import ProviderCacheKey, ProviderResponseCacheService


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
