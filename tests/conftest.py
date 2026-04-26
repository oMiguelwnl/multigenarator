"""Shared pytest fixtures for Multilang."""

import pytest

from multilang.settings import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None)
