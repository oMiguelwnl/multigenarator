# Quick Task 008 Summary: Add Swedish

## Status

Completed.

## What Changed

- Added `SupportedLanguage.SV = "sv"` and included `sv` in default supported settings.
- Added Swedish language names/routes for runtime display, LiteLLM prompts, DeepL target mapping, pronunciation prompts, Tatoeba API codes, corpus language identification, text validation markers, and highlight stopwords.
- Added Swedish deterministic local text/translation templates for offline/runtime smoke paths.
- Added Swedish Azure voice selection with `sv-SE-SofieNeural` and `sv-SE-MattiasNeural` fallback, plus ElevenLabs and Google Translate TTS routing.
- Generated Swedish frequency assets:
  - `assets/frequency/sv/curated-v1.csv` with 3000 curated rows across three 1000-card levels.
  - `assets/frequency/sv/rejections-v1.csv` with structural rejection metadata.
- Updated tests so Swedish is accepted and unsupported-language checks use `zz` instead of `sv`.
- Made the CLI audio-counter test explicitly use Azure so local `MULTILANG_AUDIO_PROVIDER` environment overrides do not bypass its FakeAzure adapter.

## Verification

Passed:

- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.settings import Settings; assert GenerationRequest(language='sv', source_type='frequency').language is SupportedLanguage.SV; assert 'sv' in Settings(_env_file=None).supported_languages"`
- `uv run python -c "from multilang.domain.jobs import SupportedLanguage; from multilang.services.provider_text_adapters import _DEEPL_TARGET_LANGUAGES, _LANGUAGE_NAMES as text_names; from multilang.services.provider_pronunciation_adapters import _LANGUAGE_NAMES as pronunciation_names; from multilang.services.language_identifier import SUPPORTED_LANGUAGE_CODES; from multilang.services.tatoeba_sentence_source import _TATOEBA_API_CODES; from multilang.services.text_validation import _LANGUAGE_MARKERS; from multilang.services.highlight_candidate_extraction import _STOPWORDS; assert text_names['sv'] == 'Swedish'; assert _DEEPL_TARGET_LANGUAGES['sv'] == 'SV'; assert pronunciation_names['sv'] == 'Swedish'; assert 'sv' in SUPPORTED_LANGUAGE_CODES; assert _TATOEBA_API_CODES['sv'] == 'swe'; assert _LANGUAGE_MARKERS['sv']; assert _STOPWORDS[SupportedLanguage.SV]"`
- `uv run pytest tests/services/test_local_text_adapter.py::test_local_adapter_supports_swedish tests/services/test_audio_voice_registry.py::test_voice_registry_selects_swedish_voice tests/services/test_elevenlabs_speech_adapter.py::test_elevenlabs_adapter_uses_default_voice_for_swedish tests/services/test_google_translate_speech_adapter.py::test_google_translate_adapter_selects_swedish_language tests/domain/test_jobs.py::test_generation_request_accepts_swedish tests/test_settings.py::test_default_supported_languages_include_swedish tests/services/test_frequency_decks.py::test_swedish_frequency_assets_validate tests/cli/test_generate_command.py::test_generate_command_rejects_unsupported_language -q`
- `uv run python scripts/build_frequency_assets.py --check`
- `uv run pytest tests/cli/test_generate_command.py::test_generate_command_default_runtime_reports_audio_counters -q`
- `uv run pytest tests/domain/test_jobs.py tests/test_settings.py tests/services/test_audio_voice_registry.py tests/services/test_elevenlabs_speech_adapter.py tests/services/test_google_translate_speech_adapter.py tests/services/test_local_text_adapter.py tests/services/test_frequency_decks.py tests/services/test_provider_text_adapters.py tests/services/test_tatoeba_sentence_source.py tests/services/test_text_validation.py tests/cli/test_generate_command.py -q`

## Notes

- Plan check passed after adding explicit done criteria to each task.
- `.planning/templates/roles/planner.md` and `.planning/templates/delegates/plan-checker.md` were absent, so the quick plan followed the embedded quick-task contract directly plus the available `gsdd-plan-checker` agent.
