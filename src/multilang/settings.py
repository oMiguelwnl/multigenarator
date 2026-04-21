"""Runtime settings for Multilang."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

SupportedLanguageCode = Literal["pt", "es", "en", "fr", "de", "ru", "nl"]
TextGenerationProvider = Literal["litellm"]
TranslationProvider = Literal["deepl"]

DEFAULT_SUPPORTED_LANGUAGES: tuple[SupportedLanguageCode, ...] = (
    "pt",
    "es",
    "en",
    "fr",
    "de",
    "ru",
    "nl",
)


class Settings(BaseSettings):
    """Typed runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="MULTILANG_", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/multilang"
    default_retry_attempts: int = 2
    lexicon_data_dir: Path = Path(".multilang/lexicon")
    text_generation_provider: TextGenerationProvider = "litellm"
    text_generation_model: str = "openai/gpt-4o-mini"
    translation_provider: TranslationProvider = "deepl"
    deepl_api_key: str | None = None
    supported_languages: list[SupportedLanguageCode] = Field(
        default_factory=lambda: list(DEFAULT_SUPPORTED_LANGUAGES)
    )
