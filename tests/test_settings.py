"""Settings contract tests."""

from pathlib import Path

from multilang.settings import Settings


def test_default_supported_languages(settings: Settings) -> None:
    assert settings.supported_languages == [
        "pt",
        "es",
        "en",
        "fr",
        "de",
        "it",
        "pl",
        "tr",
        "ro",
        "ru",
        "nl",
    ]


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
