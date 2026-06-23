# Quick Task 007 Summary: Add Norwegian Bokmal

## Status

completed

## Description

Adicionar ao projeto a lingua Norueguesa.

Confirmed approach: Norwegian means Bokmal (`nb`).

## Changes

- Added `SupportedLanguage.NB = "nb"` and included `nb` in typed settings defaults.
- Added Norwegian Bokmal display names and provider routing for runtime deck names, LLM text prompts, pronunciation prompts, DeepL target code `NB`, Tatoeba code `nob`, corpus language identification, language markers, and highlight stopwords.
- Added Azure voice routing for `nb-NO-PernilleNeural` with `nb-NO-FinnNeural` fallback and bumped `VOICE_REGISTRY_VERSION` to `2026-06-23a`.
- Added ElevenLabs routing for `nb-NO` and Google Translate TTS routing through code `no`.
- Added local/offline sentence, translation, and definition support for `nb` so test/runtime local providers do not fail.
- Added `assets/frequency/nb/curated-v1.csv` with 3000 structurally curated `wordfreq:nb` rows across 3 levels of 1000 cards.
- Added `assets/frequency/nb/rejections-v1.csv` with deterministic rejected source tokens encountered during asset generation.
- Added focused regression tests for `nb` language acceptance, settings, frequency assets, audio routing, and local text generation.
- Updated existing language contract tests to reflect the live code's pre-existing `la` enum member while adding `nb`.

## Files Changed

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
- `src/multilang/services/audio_voice_registry.py`
- `src/multilang/services/elevenlabs_speech_adapter.py`
- `src/multilang/services/google_translate_speech_adapter.py`
- `src/multilang/services/frequency_decks.py`
- `assets/frequency/nb/curated-v1.csv`
- `assets/frequency/nb/rejections-v1.csv`
- `tests/domain/test_jobs.py`
- `tests/test_settings.py`
- `tests/services/test_frequency_decks.py`
- `tests/services/test_audio_voice_registry.py`
- `tests/services/test_elevenlabs_speech_adapter.py`
- `tests/services/test_google_translate_speech_adapter.py`
- `tests/services/test_local_text_adapter.py`

## Verification

- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.settings import Settings; assert GenerationRequest(language='nb', source_type='frequency').language is SupportedLanguage.NB; assert 'nb' in Settings(_env_file=None).supported_languages"` passed.
- `uv run pytest tests/services/test_audio_voice_registry.py::test_voice_registry_selects_norwegian_bokmal_voice tests/services/test_elevenlabs_speech_adapter.py::test_elevenlabs_adapter_uses_default_voice_for_norwegian_bokmal tests/services/test_google_translate_speech_adapter.py::test_google_translate_adapter_selects_norwegian_bokmal_language -q` passed, 3 tests.
- `uv run pytest tests/domain/test_jobs.py::test_generation_request_accepts_norwegian_bokmal tests/test_settings.py::test_default_supported_languages_include_norwegian_bokmal tests/services/test_frequency_decks.py::test_norwegian_bokmal_frequency_assets_validate tests/services/test_frequency_decks.py::test_iterator_rejects_unicode_replacement_character tests/services/test_local_text_adapter.py::test_local_runtime_supports_norwegian_bokmal_without_live_providers -q` passed, 5 tests.
- `uv run pytest tests/domain/test_jobs.py tests/test_settings.py tests/services/test_frequency_decks.py tests/services/test_audio_voice_registry.py tests/services/test_elevenlabs_speech_adapter.py tests/services/test_google_translate_speech_adapter.py tests/services/test_local_text_adapter.py -q` passed, 66 tests.
- `uv run pytest tests/services/test_tatoeba_sentence_source.py tests/services/test_text_validation.py -q` passed, 28 tests.

## Notes

- Scope warning was accepted before execution because the language addition touched more than 8 files and added a new supported language value.
- Reduced template assurance: `.planning/templates/roles/planner.md`, `.planning/templates/roles/executor.md`, and `.planning/templates/delegates/plan-checker.md` were absent/empty, so the quick workflow contracts were followed directly.
- Full-suite execution was not run; `.planning/codebase/CONCERNS.md` records broad-suite drift as pre-existing.
