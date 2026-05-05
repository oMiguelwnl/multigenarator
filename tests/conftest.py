"""Shared pytest fixtures for Multilang."""

import pytest

from multilang.settings import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None)


@pytest.fixture(autouse=True)
def local_text_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MULTILANG_TEXT_GENERATION_PROVIDER", "local")
    monkeypatch.setenv("MULTILANG_TRANSLATION_PROVIDER", "local")
