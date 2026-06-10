"""Runtime settings for Multilang."""

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from multilang.services.audio_voice_registry import VOICE_REGISTRY_VERSION

SupportedLanguageCode = Literal["pt", "es", "en", "fr", "de", "it", "pl", "tr", "ro", "ru", "nl"]
TextGenerationProvider = Literal["litellm", "local"]
TranslationProvider = Literal["deepl", "google", "local"]
AudioProviderName = Literal["azure", "elevenlabs", "google_translate"]
AudioOutputFormat = Literal["audio-24khz-48kbitrate-mono-mp3"]
ElevenLabsOutputFormat = Literal["mp3_44100_128"]

DEFAULT_SUPPORTED_LANGUAGES: tuple[SupportedLanguageCode, ...] = (
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
)


class Settings(BaseSettings):
    """Typed runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MULTILANG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/multilang"
    default_retry_attempts: int = 2
    frequency_assets_dir: Path = Path("assets/frequency")
    frequency_list_version: str = "v1"
    provider_retry_base_delay_seconds: float = 1.0
    provider_retry_max_delay_seconds: float = 30.0
    provider_retry_jitter_ratio: float = 0.1
    provider_circuit_failure_threshold: int = 3
    provider_circuit_cooldown_seconds: float = 60.0
    lexicon_data_dir: Path = Path(".multilang/lexicon")
    text_generation_provider: TextGenerationProvider = "litellm"
    text_generation_model: str = "openai/gpt-4o-mini"
    translation_provider: TranslationProvider = "deepl"
    litellm_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MULTILANG_LITELLM_API_KEY", "LITELLM_API_KEY"),
    )
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MULTILANG_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )
    openrouter_api_key: str | None = None
    deepl_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MULTILANG_DEEPL_API_KEY", "DEEPL_API_KEY"),
    )
    audio_provider: AudioProviderName = "azure"
    azure_speech_key: str | None = None
    azure_speech_region: str | None = None
    azure_speech_output_format: AudioOutputFormat = "audio-24khz-48kbitrate-mono-mp3"
    audio_fallback_providers: list[AudioProviderName] = Field(default_factory=list)
    elevenlabs_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MULTILANG_ELEVENLABS_API_KEY", "ELEVENLABS_API_KEY"),
    )
    elevenlabs_api_key_2: str | None = None
    elevenlabs_api_key_3: str | None = None
    elevenlabs_api_key_4: str | None = None
    elevenlabs_api_keys: list[str] = Field(default_factory=list)
    elevenlabs_voice_id: str | None = None
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    elevenlabs_output_format: ElevenLabsOutputFormat = "mp3_44100_128"
    audio_storage_dir: Path = Path(".multilang/audio")
    export_output_dir: Path = Path(".multilang/exports")
    webdav_url: str | None = None
    webdav_username: str | None = None
    webdav_secret: str | None = None
    webdav_timeout_seconds: float = 30.0
    webdav_cache_dir: Path = Path(".multilang/highlights/cache")
    audio_voice_registry_version: str = VOICE_REGISTRY_VERSION
    tatoeba_enabled: bool = True
    supported_languages: list[SupportedLanguageCode] = Field(
        default_factory=lambda: list(DEFAULT_SUPPORTED_LANGUAGES)
    )
