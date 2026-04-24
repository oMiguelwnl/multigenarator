"""Runtime settings for Multilang."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from multilang.services.audio_voice_registry import VOICE_REGISTRY_VERSION

SupportedLanguageCode = Literal["pt", "es", "en", "fr", "de", "ru", "nl"]
TextGenerationProvider = Literal["litellm"]
TranslationProvider = Literal["deepl"]
AudioOutputFormat = Literal["audio-24khz-48kbitrate-mono-mp3"]

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
    azure_speech_key: str | None = None
    azure_speech_region: str | None = None
    azure_speech_output_format: AudioOutputFormat = "audio-24khz-48kbitrate-mono-mp3"
    audio_storage_dir: Path = Path(".multilang/audio")
    audio_voice_registry_version: str = VOICE_REGISTRY_VERSION
    tatoeba_enabled: bool = True
    supported_languages: list[SupportedLanguageCode] = Field(
        default_factory=lambda: list(DEFAULT_SUPPORTED_LANGUAGES)
    )
