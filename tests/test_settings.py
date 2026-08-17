"""Settings contract tests."""

from pathlib import Path

from pydantic import ValidationError
import pytest

import multilang.settings as settings_module
from multilang.settings import Settings


def test_default_supported_languages_preserve_existing_values_and_add_korean_once(
    settings: Settings,
) -> None:
    assert settings.supported_languages == [
        "pt",
        "es",
        "en",
        "fr",
        "de",
        "el",
        "it",
        "pl",
        "tr",
        "ro",
        "ru",
        "nl",
        "da",
        "nb",
        "sv",
        "fi",
        "hu",
        "cs",
        "hr",
        "la",
        "ja",
        "zh",
        "ko",
    ]
    assert settings.supported_languages.count("ko") == 1


def test_settings_accept_canonical_korean_and_reject_provider_locale() -> None:
    settings = Settings(_env_file=None, supported_languages=["ko"])

    assert settings.supported_languages == ["ko"]

    with pytest.raises(ValidationError):
        Settings(_env_file=None, supported_languages=["ko-KR"])


def test_approved_frequency_assets_remain_separate_from_selectable_languages() -> None:
    approved_languages = getattr(
        settings_module,
        "APPROVED_FREQUENCY_ASSET_LANGUAGES",
        None,
    )

    assert approved_languages is not None
    assert approved_languages == tuple(settings_module.DEFAULT_SUPPORTED_LANGUAGES[:-1])
    assert "ko" not in approved_languages


def test_default_retry_attempts(settings: Settings) -> None:
    assert settings.default_retry_attempts == 2


def test_settings_load_without_environment_overrides() -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+psycopg://postgres:postgres@localhost:5432/multilang"


def test_settings_load_local_dotenv_file(tmp_path: Path, monkeypatch) -> None:
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text(
        "MULTILANG_DATABASE_URL=sqlite+pysqlite:///dotenv.db\n"
        "MULTILANG_DEFAULT_RETRY_ATTEMPTS=7\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    settings = Settings()

    assert settings.database_url == "sqlite+pysqlite:///dotenv.db"
    assert settings.default_retry_attempts == 7


def test_webdav_settings_default_to_unconfigured() -> None:
    settings = Settings(_env_file=None)

    assert settings.webdav_url is None
    assert settings.webdav_username is None
    assert settings.webdav_secret is None
    assert settings.webdav_timeout_seconds == 30.0
    assert settings.webdav_cache_dir == Path(".multilang/highlights/cache")


def test_webdav_settings_load_multilang_environment(monkeypatch) -> None:
    monkeypatch.setenv("MULTILANG_WEBDAV_URL", "https://example.invalid/dav/")
    monkeypatch.setenv("MULTILANG_WEBDAV_USERNAME", "reader")
    monkeypatch.setenv("MULTILANG_WEBDAV_SECRET", "reader-secret")
    monkeypatch.setenv("MULTILANG_WEBDAV_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("MULTILANG_WEBDAV_CACHE_DIR", ".multilang/highlights/cache/custom")

    settings = Settings(_env_file=None)

    assert settings.webdav_url == "https://example.invalid/dav/"
    assert settings.webdav_username == "reader"
    assert settings.webdav_secret == "reader-secret"
    assert settings.webdav_timeout_seconds == 12.5
    assert settings.webdav_cache_dir == Path(".multilang/highlights/cache/custom")


def test_openrouter_uses_project_prefixed_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "global-old-key")
    monkeypatch.setenv("MULTILANG_OPENROUTER_API_KEY", "project-new-key")

    settings = Settings(_env_file=None)

    assert settings.openrouter_api_key == "project-new-key"


def test_openrouter_ignores_unprefixed_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "global-old-key")
    monkeypatch.delenv("MULTILANG_OPENROUTER_API_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.openrouter_api_key is None
