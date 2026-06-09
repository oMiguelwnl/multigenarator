# Technology Stack

**Analysis Date:** 2026-06-09

## Mapper Inputs and Safety Notes

- Requested delegate template `.planning/templates/delegates/mapper-tech.md` is not present in this repository; this map follows the live repository plus `.agents/skills/gsdd-map-codebase/SKILL.md` safety and artifact requirements.
- `.env` is present at repository root and is ignored by `.gitignore`; do not read, print, commit, or summarize its contents.
- `.gitignore` also excludes `.env.*`, `webdav-secrets*.json`, `.multilang/`, `*.apkg`, `*.mp3`, `*.wav`, `*.db`, `*.sqlite`, Kindle highlight imports, and `.planning/.local/`; treat these as local/private/generated unless a plan explicitly says otherwise.
- Local binary/media/database artifacts exist (`multilang.db`, `Disticha Catonis.pdf`, generated Latin `.wav` files under `data/latin_mvp/audio/`); inspect metadata/path existence only unless the task is explicitly about media validation.

## Languages and Runtime

- **Python**: `pyproject.toml` declares `requires-python = ">=3.12"`; current shell reports Python `3.13.7`. Code uses modern typing, Pydantic v2 models, dataclasses, Typer, SQLAlchemy ORM, and stdlib `urllib`/`subprocess` adapters.
- **Project package**: `multilang` version `0.1.0` in `pyproject.toml`; source code lives under `src/multilang/` and tests under `tests/`.
- **Package/build backend**: Hatchling `>=1.25` configured in `pyproject.toml`; `uv.lock` currently resolves `hatchling` as the build path through the lockfile.
- **Package manager**: `uv` is used with lockfile `uv.lock`; current shell reports `uv 0.11.14`.
- **CLI entry**: `src/multilang/cli.py` defines Typer `app = create_app()` and can be run as a module/file; `pyproject.toml` does not define a `[project.scripts]` console entry point.

## Core Dependencies from `uv.lock`

- **Typer `0.23.1` + Rich `13.9.4`**: CLI command framework and terminal output; main surface is `src/multilang/cli.py`.
- **Pydantic `2.12.5` + pydantic-settings `2.13.1`**: domain contracts and environment settings; examples include `src/multilang/domain/jobs.py`, `src/multilang/domain/exporting.py`, `src/multilang/domain/latin.py`, and `src/multilang/settings.py`.
- **SQLAlchemy `2.0.49` + Alembic `1.18.4` + psycopg `3.3.3`**: persistence stack; ORM models are in `src/multilang/db/models.py`, migrations in `alembic/versions/`, and Alembic config in `alembic.ini` / `alembic/env.py`.
- **LiteLLM `1.83.10`**: provider abstraction for sentence/definition generation through `src/multilang/services/provider_text_adapters.py`.
- **PydanticAI `1.5.0`**: installed dependency in `pyproject.toml`/`uv.lock`; no live `pydantic_ai` imports detected in `src/multilang/`.
- **DeepL `1.30.0` + deep-translator `1.11.4`**: translation providers in `src/multilang/services/provider_text_adapters.py`; DeepL is preferred when configured, Google Translate fallback is available via `deep-translator`.
- **wordfreq `3.1.1`**: modern-language frequency candidate source in `src/multilang/services/frequency_decks.py`, with curated CSV assets under `assets/frequency/{language}/`.
- **azure-cognitiveservices-speech `1.49.1`**: Azure Speech SDK dependency used by `src/multilang/services/azure_speech_adapter.py` for modern-language TTS.
- **genanki `0.13.1`**: APKG generation for normal and Latin decks; Latin export uses it directly in `src/multilang/services/latin_export.py`.
- **pytest `8.4.2` + pytest-asyncio `0.26.0`**: test runner stack configured in `pyproject.toml` with `testpaths = ["tests"]` and `asyncio_mode = "auto"`.

## Persistence and Data Storage

- **Default production-style DB**: `src/multilang/settings.py` defines `database_url` with a PostgreSQL+psycopg scheme by default; use `MULTILANG_DATABASE_URL` to override without editing source.
- **Local migration default**: `alembic.ini` points Alembic at a local SQLite database path for development; `alembic/env.py` overrides this when `MULTILANG_DATABASE_URL` is set.
- **ORM tables**: `src/multilang/db/models.py` includes generation jobs/items, lexical candidates, text quality records, provider response cache, provider call logs, highlight import records/manifests, audio assets, card exports, and deck exports.
- **Runtime bootstrap**: `src/multilang/runtime.py` creates a SQLAlchemy engine from `Settings.database_url`, calls `Base.metadata.create_all(engine)`, creates a `Session`, and wires repositories/services.
- **Local/private runtime dirs**: `.multilang/` is the default runtime workspace for lexicon cache, audio, exports, highlights cache, and live smoke outputs; it is gitignored and should not be treated as committed source of truth.
- **Committed frequency assets**: `assets/frequency/` contains curated and rejection CSVs for `pt`, `es`, `en`, `fr`, `de`, `it`, `pl`, `tr`, `ro`, `ru`, and `nl`.
- **Committed Latin MVP assets**: `data/latin_mvp/latin-mvp-50-v1.json`, `latin-mvp-50-v1-curation.json`, `latin-mvp-50-v1-pt.json`, and `latin-mvp-50-v1-audio.json` are the reviewed/frozen Latin MVP data surfaces; audio files are present under `data/latin_mvp/audio/latin-mvp-50-v1/`.

## CLI and Application Shape

- The app is **CLI-first/batch-oriented**, not a web service. Main CLI construction is in `src/multilang/cli.py`.
- Modern-language generation uses `generate`, `generate-text`, `synthesize-audio`, `export`, review/audit, Kindle/WebDAV highlight, and phonetics-related commands in `src/multilang/cli.py`.
- Latin MVP has dedicated commands in `src/multilang/cli.py`: `generate-latin-mvp`, `review-latin-mvp`, and `export-latin-mvp`.
- The standard orchestration service is `RuntimeGenerateService` in `src/multilang/runtime.py`, composed from repositories plus lexical grounding, text generation, audio synthesis, review, and export services.
- Latin MVP generation intentionally bypasses the modern `SupportedLanguage` enum: `src/multilang/domain/jobs.py` supports 11 modern languages, while `src/multilang/domain/source_profiles.py` adds source type `latin-mvp` and Latin-specific services live under `src/multilang/services/latin_*.py`.

## AI and Text Providers

- **LiteLLM**: `src/multilang/services/provider_text_adapters.py` uses `litellm.completion()` with JSON response format for sentence and definition generation.
- **Configured model**: `src/multilang/settings.py` defaults `text_generation_model` to `openai/gpt-4o-mini`; provider routing can use LiteLLM/OpenAI/OpenRouter API keys through environment variables.
- **Local provider mode**: `src/multilang/runtime.py` selects `LocalSentenceAdapter` and `LocalTranslationAdapter` when settings choose local providers, keeping tests and offline flows deterministic.
- **Provider caching/logging**: `ProviderResponseCacheService` and `ProviderCallLogRepository` are wired in `src/multilang/runtime.py`; ORM backing tables are `provider_response_cache` and `provider_call_logs` in `src/multilang/db/models.py`.
- **Prompt privacy**: highlight prompt construction in `src/multilang/services/provider_text_adapters.py` redacts highlight context via `src/multilang/security/redaction.py`; keep this pattern for any source-derived prompt expansion.

## Translation Providers

- **DeepL primary**: `DeepLTranslationAdapter` in `src/multilang/services/provider_text_adapters.py` requires `MULTILANG_DEEPL_API_KEY` or `DEEPL_API_KEY` and maps project languages to DeepL target codes.
- **Google Translate fallback**: `GoogleTranslateAdapter` uses `deep_translator.GoogleTranslator` when `translation_provider` is set to `google` in settings.
- **Local translation**: `LocalTranslationAdapter` is selected for deterministic/offline operation when `translation_provider = "local"`.
- **Latin Portuguese text**: v2.0 Latin translations are committed/reviewed assets in `data/latin_mvp/latin-mvp-50-v1-pt.json` and validated through `src/multilang/services/latin_translation_quality.py`, not live DeepL Latin translation.

## Audio and TTS Providers

- **Azure Speech**: primary modern-language TTS adapter is `src/multilang/services/azure_speech_adapter.py`, using `azure.cognitiveservices.speech`, Azure voice inventory calls, SSML generation, and output format `audio-24khz-48kbitrate-mono-mp3`.
- **Azure config**: requires `MULTILANG_AZURE_SPEECH_KEY` and `MULTILANG_AZURE_SPEECH_REGION`; never log or commit values.
- **ElevenLabs fallback**: `src/multilang/services/elevenlabs_speech_adapter.py` calls the ElevenLabs REST endpoint using `urllib`, supports multiple API keys, model `eleven_multilingual_v2`, and output format `mp3_44100_128`.
- **Fallback composition**: `src/multilang/runtime.py` builds a `FallbackAudioAdapter` when `audio_fallback_providers` are configured.
- **Latin eSpeak NG**: `src/multilang/services/espeak_ng_speech_adapter.py` shells out to `espeak-ng`, requires voice `la`, locale `la`, WAV output, and pronunciation policy `classical_approx`.
- **Latin audio policy**: `src/multilang/services/latin_audio_samples.py` records eSpeak NG as the local sample provider and marks Azure Latin as blocked because no verified native Classical Latin/`la` Azure TTS locale is available.
- **Audio integrity**: normal exports use exact word-audio checks in `src/multilang/services/audio_integrity.py` via `src/multilang/runtime.py`; Latin exports use manifest readiness and exact media path checks in `src/multilang/services/latin_audio.py` and `src/multilang/services/latin_export.py`.

## External Services and Network Boundaries

- **Tatoeba**: `src/multilang/services/tatoeba_sentence_source.py` can query `https://tatoeba.org/en/api_v0/search` as a filtered fallback; settings include `tatoeba_enabled`, and disabled/tests use `StaticTatoebaCandidateProvider`.
- **WebDAV**: `src/multilang/services/webdav_highlight_fetch.py` fetches Kindle highlight exports using operator-provided WebDAV URL/username/secret, Basic Auth, and local cache paths under `.multilang/highlights/cache`.
- **Azure voice inventory**: `src/multilang/services/azure_speech_adapter.py` calls the regional Azure voice-list endpoint when credentials exist.
- **ElevenLabs API**: `src/multilang/services/elevenlabs_speech_adapter.py` posts text to `https://api.elevenlabs.io/v1/text-to-speech/{voice_id}` when configured.
- **DeepL API**: `src/multilang/services/provider_text_adapters.py` instantiates `deepl.Translator` with the configured API key.
- **LiteLLM upstreams**: actual network endpoint depends on the LiteLLM model/API-key configuration; keep provider-specific keys in environment only.

## Environment Configuration

- Settings class: `src/multilang/settings.py` uses `pydantic_settings.BaseSettings` with `env_prefix="MULTILANG_"`, reads `.env`, ignores extra variables, and supports selected non-prefixed aliases.
- Important environment variable names: `MULTILANG_DATABASE_URL`, `MULTILANG_LITELLM_API_KEY`, `LITELLM_API_KEY`, `MULTILANG_OPENAI_API_KEY`, `OPENAI_API_KEY`, `MULTILANG_OPENROUTER_API_KEY`, `MULTILANG_DEEPL_API_KEY`, `DEEPL_API_KEY`, `MULTILANG_AZURE_SPEECH_KEY`, `MULTILANG_AZURE_SPEECH_REGION`, `MULTILANG_ELEVENLABS_API_KEY`, `ELEVENLABS_API_KEY`, `MULTILANG_WEBDAV_URL`, `MULTILANG_WEBDAV_USERNAME`, and `MULTILANG_WEBDAV_SECRET`.
- Do not write real API keys, database passwords, WebDAV secrets, provider response payloads, or raw private Kindle text into `.planning/`, tests, logs, committed fixtures, or generated maps.
- Prefer local/offline settings and fake adapters in tests; provider-backed paths must be gated by explicit env vars and should redact exceptions via `src/multilang/security/redaction.py`.

## Export and Anki Packaging

- **Normal/manual/highlight/phonetics templates**: package templates live in `src/multilang/templates/normal_card.md`, `highlight_card.md`, and `russian_phoneme_card.md` and are force-included by `pyproject.toml`.
- **Normal APKG export**: `src/multilang/services/export_anki_package.py` uses genanki for normal/manual decks and media packaging.
- **Tabular export**: `src/multilang/services/export_tabular_bundle.py` writes CSV/TSV artifacts for Anki import workflows.
- **Latin APKG export**: `src/multilang/services/latin_export.py` defines `LATIN_EXPORT_FIELD_NAMES`, `LATIN_NOTE_TYPE_NAME = "Multilang::Classical Latin MVP"`, stable model/deck IDs, inline Latin card CSS/template, deterministic note GUIDs, and CSV/TSV/APKG writers.
- **Media safety**: exports validate that sound tags are `[sound:{basename}]`, media files exist, and path basenames match; do not construct audio references from untrusted full paths.

## Testing Stack and Commands

- Run focused tests with `uv run pytest <path>` or `python -m pytest <path>` depending on active environment. `pyproject.toml` configures `pythonpath = ["src"]` and `testpaths = ["tests"]`.
- Use targeted test files for stack-sensitive changes: `tests/services/test_azure_speech_adapter.py`, `tests/services/test_elevenlabs_speech_adapter.py`, `tests/services/test_espeak_ng_speech_adapter.py`, `tests/services/test_latin_export.py`, `tests/services/test_frequency_decks.py`, and relevant `tests/integration/test_v20_*.py` evidence tests.
- Broad full-suite drift is documented in `.planning/STATE.md`; prefer focused regression suites for authoritative verification until the broad suite is repaired.

## Development and Production Requirements

- Development requires Python compatible with `pyproject.toml` (`>=3.12`), `uv`, and a local virtual environment such as `.venv/` (gitignored).
- For live modern-language generation, provide configured LiteLLM/OpenAI/OpenRouter and DeepL/local translation settings; for offline tests use local/fake adapters.
- For live modern-language audio, provide Azure Speech credentials or configure ElevenLabs fallback credentials; for Latin MVP sample generation install `espeak-ng` with voice `la` available on PATH.
- Production-like persistence should use PostgreSQL through `MULTILANG_DATABASE_URL`; local Alembic/dev defaults use SQLite and should not be treated as production storage.
- Generated exports, local audio, provider caches, highlight caches, and local databases should remain outside committed source unless a phase explicitly promotes safe, reviewed evidence artifacts.

---

*Stack analysis: 2026-06-09*
