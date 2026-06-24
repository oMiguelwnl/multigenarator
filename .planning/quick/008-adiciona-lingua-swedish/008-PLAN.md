# Quick Task 008 Plan: Add Swedish

## Objective

Add Swedish (`sv`) as a supported modern-language deck target with the same core registration, provider routing, audio voice selection, frequency assets, and focused regression coverage as the existing modern languages.

Approach context: No clarification required; Swedish maps to ISO 639-1 code `sv` and Azure/DeepL/TTS provider routes should be added where the project already maintains language-specific maps.

Planner note: `.planning/templates/roles/planner.md` is absent, so this plan follows the quick-task contract directly with reduced planner-template assurance.

No UI proof rationale: This task changes CLI/domain/provider configuration and data assets only; it has no rendered UI surface.

## Task 1: Register `sv` Across Language Contracts

<files>
- `src/multilang/domain/jobs.py`
- `src/multilang/settings.py`
- `src/multilang/runtime.py`
- `src/multilang/services/provider_text_adapters.py`
- `src/multilang/services/provider_pronunciation_adapters.py`
- `src/multilang/services/language_identifier.py`
- `src/multilang/services/highlight_candidate_extraction.py`
- `src/multilang/services/tatoeba_sentence_source.py`
- `src/multilang/services/text_validation.py`
- `src/multilang/services/local_text_adapter.py`
- `tests/services/test_local_text_adapter.py`
</files>

<action>
- Add `SupportedLanguage.SV = "sv"` to the modern language enum.
- Add `sv` to typed settings defaults and runtime language-name maps as "Swedish".
- Add `sv` to provider prompt language names, DeepL target mapping, pronunciation prompt names, Tatoeba API routing, and corpus language-id supported codes.
- Add Swedish highlight stopwords and text-validation language markers so Kindle/highlight and validation flows do not fail on language-key lookups.
- Add `sv` to local/offline text-generation support so local smoke paths can produce deterministic Swedish sentences/translations.
</action>

<done>
- `GenerationRequest(language="sv", ...)` parses to `SupportedLanguage.SV`.
- Default settings expose `sv` in the supported-language list.
- Swedish exists in all runtime/provider/local maps touched by this task without falling through to raw language codes or key errors.
</done>

<verify>
- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.settings import Settings; assert GenerationRequest(language='sv', source_type='frequency').language is SupportedLanguage.SV; assert 'sv' in Settings(_env_file=None).supported_languages"`
- `uv run python -c "from multilang.domain.jobs import SupportedLanguage; from multilang.services.provider_text_adapters import _DEEPL_TARGET_LANGUAGES, _LANGUAGE_NAMES as text_names; from multilang.services.provider_pronunciation_adapters import _LANGUAGE_NAMES as pronunciation_names; from multilang.services.language_identifier import SUPPORTED_LANGUAGE_CODES; from multilang.services.tatoeba_sentence_source import _TATOEBA_API_CODES; from multilang.services.text_validation import _LANGUAGE_MARKERS; from multilang.services.highlight_candidate_extraction import _STOPWORDS; assert text_names['sv'] == 'Swedish'; assert _DEEPL_TARGET_LANGUAGES['sv'] == 'SV'; assert pronunciation_names['sv'] == 'Swedish'; assert 'sv' in SUPPORTED_LANGUAGE_CODES; assert _TATOEBA_API_CODES['sv'] == 'swe'; assert _LANGUAGE_MARKERS['sv']; assert _STOPWORDS[SupportedLanguage.SV]"`
- `uv run pytest tests/services/test_local_text_adapter.py::test_local_adapter_supports_swedish -q`
</verify>

## Task 2: Add Audio Provider Routing For `sv`

<files>
- `src/multilang/services/audio_voice_registry.py`
- `src/multilang/services/elevenlabs_speech_adapter.py`
- `src/multilang/services/google_translate_speech_adapter.py`
- `tests/services/test_audio_voice_registry.py`
- `tests/services/test_elevenlabs_speech_adapter.py`
- `tests/services/test_google_translate_speech_adapter.py`
</files>

<action>
- Add an Azure voice plan for Swedish using `sv-SE` voices.
- Add ElevenLabs and Google Translate TTS locale/code routing for `sv`.
- Add focused tests proving Swedish voice/locale selection without changing broader unrelated audio behavior.
</action>

<done>
- Azure voice selection returns a deterministic Swedish `sv-SE` voice.
- ElevenLabs and Google Translate fallback adapters can select Swedish without key errors.
- Existing voice registry coverage still proves every `SupportedLanguage` has an approved Azure voice plan.
</done>

<verify>
- `uv run pytest tests/services/test_audio_voice_registry.py::test_voice_registry_selects_swedish_voice tests/services/test_elevenlabs_speech_adapter.py::test_elevenlabs_adapter_uses_default_voice_for_swedish tests/services/test_google_translate_speech_adapter.py::test_google_translate_adapter_selects_swedish_language -q`
</verify>

## Task 3: Add Frequency Assets And Contract Coverage For `sv`

<files>
- `assets/frequency/sv/curated-v1.csv`
- `assets/frequency/sv/rejections-v1.csv`
- `tests/domain/test_jobs.py`
- `tests/test_settings.py`
- `tests/cli/test_generate_command.py`
- `tests/services/test_frequency_decks.py`
</files>

<action>
- Create committed Swedish frequency assets with 3 levels of 1000 rows from `wordfreq` using the existing curated frequency schema and structural curation flags.
- Add/update focused tests proving `sv` is accepted as a supported language, appears in default settings, its curated assets validate, and CLI unsupported-language coverage uses a truly unsupported code.
- Avoid ROADMAP/SPEC updates because quick tasks do not modify phase-level artifacts.
</action>

<done>
- `assets/frequency/sv/curated-v1.csv` and `assets/frequency/sv/rejections-v1.csv` exist and pass the existing asset validators.
- Swedish has exactly 1000 curated rows in each frequency level.
- Tests no longer treat `sv` as unsupported; unsupported-language tests use another invalid code.
</done>

<verify>
- `uv run pytest tests/domain/test_jobs.py::test_generation_request_accepts_swedish tests/test_settings.py::test_default_supported_languages_include_swedish tests/services/test_frequency_decks.py::test_swedish_frequency_assets_validate tests/cli/test_generate_command.py::test_generate_command_rejects_unsupported_language -q`
- `uv run python scripts/build_frequency_assets.py --check`
</verify>
