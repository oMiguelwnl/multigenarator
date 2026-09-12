"""Runtime settings for Multilang."""

import os
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from multilang.services.audio_voice_registry import VOICE_REGISTRY_VERSION

SupportedLanguageCode = Literal[
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
TextGenerationProvider = Literal["litellm", "local"]
TranslationProvider = Literal["deepl", "google", "local"]
AudioProviderName = Literal["azure", "elevenlabs", "google_translate"]
AudioOutputFormat = Literal["audio-24khz-48kbitrate-mono-mp3"]
ElevenLabsOutputFormat = Literal["mp3_44100_128"]

APPROVED_FREQUENCY_ASSET_LANGUAGES: tuple[SupportedLanguageCode, ...] = (
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
)

DEFAULT_SUPPORTED_LANGUAGES: tuple[SupportedLanguageCode, ...] = (
    *APPROVED_FREQUENCY_ASSET_LANGUAGES,
    "ko",
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
    roadmap_4_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("MULTILANG_ROADMAP_4_ENABLED", "ROADMAP_4_ENABLED"),
    )
    native_api_credentials: SecretStr = SecretStr("{}")
    native_api_requests_per_minute: int = Field(default=60, ge=1, le=10000)
    native_api_max_body_bytes: int = Field(default=1048576, ge=1024, le=16777216)
    native_worker_lease_seconds: int = Field(default=120, ge=10, le=3600)
    native_worker_poll_seconds: float = Field(default=1.0, ge=0.1, le=60)
    native_task_max_attempts: int = Field(default=3, ge=1, le=10)
    native_telemetry_enabled: bool = False
    native_provider_calls_enabled: bool = False
    native_audio_model_version: str = "azure-speech-sdk-1"
    native_evidence_dir: Path = Path(".multilang/evidence")
    native_evidence_signing_key: SecretStr | None = None
    native_language_models_dir: Path = Path(".multilang/models/stanza-1.10.0")
    native_contextual_bindings_dir: Path = Path(".multilang/contextual-bindings")
    native_content_drafts_dir: Path = Path(".multilang/content-drafts")
    native_max_provider_items: int = Field(default=100, ge=1, le=10000)
    default_retry_attempts: int = 2
    frequency_assets_dir: Path = Path("assets/frequency")
    frequency_list_version: str = "v1"
    provider_retry_base_delay_seconds: float = 1.0
    provider_retry_max_delay_seconds: float = 30.0
    provider_retry_jitter_ratio: float = 0.1
    provider_circuit_failure_threshold: int = 3
    provider_circuit_cooldown_seconds: float = 60.0
    korean_provider_policy_version: str = "korean-provider-policy-v1"
    korean_provider_max_attempts: int = Field(default=1, ge=1, le=5)
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
    supported_languages: Annotated[list[SupportedLanguageCode], NoDecode] = Field(
        default_factory=lambda: list(DEFAULT_SUPPORTED_LANGUAGES)
    )

    @field_validator("supported_languages", mode="before")
    @classmethod
    def parse_supported_languages(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            return []
        if normalized.startswith("[") and normalized.endswith("]"):
            normalized = normalized[1:-1]
        return [item.strip().strip('"').strip("'") for item in normalized.split(",") if item.strip()]

    def __init__(self, **values: object) -> None:
        if (
            os.environ.get("MULTILANG_FORBID_PROVIDERS") == "1"
            or os.environ.get("MULTILANG_FORBID_NETWORK") == "1"
        ):
            values.setdefault("_env_file", None)
        super().__init__(**values)
