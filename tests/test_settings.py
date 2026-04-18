"""Settings contract tests."""

from multilang.settings import Settings


def test_default_supported_languages(settings: Settings) -> None:
    assert settings.supported_languages == ["pt", "es", "en", "fr", "de", "ru", "nl"]


def test_default_retry_attempts(settings: Settings) -> None:
    assert settings.default_retry_attempts == 2


def test_settings_load_without_environment_overrides() -> None:
    settings = Settings()

    assert settings.database_url == "postgresql+psycopg://postgres:postgres@localhost:5432/multilang"
