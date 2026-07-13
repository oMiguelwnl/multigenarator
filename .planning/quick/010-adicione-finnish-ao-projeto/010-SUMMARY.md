# Quick Task 010 Summary: Add Finnish

## Status

Completed.

## What Changed

- Added `SupportedLanguage.FI = "fi"` and included `fi` in default supported settings.
- Added Finnish language names/routes for runtime display, LiteLLM prompts, DeepL target mapping, pronunciation prompts, Tatoeba API codes, corpus language identification, text validation markers, and highlight stopwords.
- Added Finnish deterministic local text/translation templates for offline/runtime smoke paths.
- Added Finnish Azure voice selection with `fi-FI-NooraNeural` and `fi-FI-HarriNeural` fallback, plus ElevenLabs and Google Translate TTS routing.
- Generated Finnish frequency assets:
  - `assets/frequency/fi/curated-v1.csv` with 3000 curated rows across three 1000-card levels.
  - `assets/frequency/fi/rejections-v1.csv` with structural rejection metadata.
- Updated focused tests for Finnish support across contracts, settings, local text, audio adapters, and frequency assets.

## Verification

Passed:

- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.settings import Settings; assert GenerationRequest(language='fi', source_type='frequency').language is SupportedLanguage.FI; assert 'fi' in Settings(_env_file=None).supported_languages"`
- `uv run python -c "from multilang.domain.jobs import SupportedLanguage; from multilang.services.provider_text_adapters import _DEEPL_TARGET_LANGUAGES, _LANGUAGE_NAMES as text_names; from multilang.services.provider_pronunciation_adapters import _LANGUAGE_NAMES as pronunciation_names; from multilang.services.language_identifier import SUPPORTED_LANGUAGE_CODES; from multilang.services.tatoeba_sentence_source import _TATOEBA_API_CODES; from multilang.services.text_validation import _LANGUAGE_MARKERS; from multilang.services.highlight_candidate_extraction import _STOPWORDS; assert text_names['fi'] == 'Finnish'; assert _DEEPL_TARGET_LANGUAGES['fi'] == 'FI'; assert pronunciation_names['fi'] == 'Finnish'; assert 'fi' in SUPPORTED_LANGUAGE_CODES; assert _TATOEBA_API_CODES['fi'] == 'fin'; assert _LANGUAGE_MARKERS['fi']; assert _STOPWORDS[SupportedLanguage.FI]"`
- `uv run pytest tests/services/test_local_text_adapter.py::test_local_adapter_supports_finnish tests/services/test_audio_voice_registry.py::test_voice_registry_selects_finnish_voice tests/services/test_elevenlabs_speech_adapter.py::test_elevenlabs_adapter_uses_default_voice_for_finnish tests/services/test_google_translate_speech_adapter.py::test_google_translate_adapter_selects_finnish_language tests/domain/test_jobs.py::test_generation_request_accepts_finnish tests/test_settings.py::test_default_supported_languages_include_finnish tests/services/test_frequency_decks.py::test_finnish_frequency_assets_validate tests/cli/test_generate_command.py::test_generate_command_rejects_unsupported_language -q`
- `uv run python scripts/build_frequency_assets.py --check --language fi`
- `uv run python scripts/build_frequency_assets.py --check`
- `uv run pytest tests/domain/test_jobs.py tests/test_settings.py tests/services/test_audio_voice_registry.py tests/services/test_elevenlabs_speech_adapter.py tests/services/test_google_translate_speech_adapter.py tests/services/test_local_text_adapter.py tests/services/test_frequency_decks.py -q`

## Notes

- Plan check passed with no issues.
- `.planning/templates/roles/planner.md` was absent, so the quick plan followed the embedded quick-task contract directly.
