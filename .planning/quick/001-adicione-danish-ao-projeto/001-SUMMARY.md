# Quick Task 001 Summary: adicione Danish ao projeto

## Status
completed

## What Changed
- Added Danish (`da`) to the `SupportedLanguage` enum and default supported language settings.
- Added Danish runtime/provider wiring for deck names, LiteLLM/DeepL language maps, corpus language identification, Azure voice selection, ElevenLabs fallback TTS, Google Translate TTS, and highlight stopwords.
- Added focused tests proving Danish request validation, settings exposure, Azure voice selection, and fallback TTS language selection.

## Files Changed
- `src/multilang/domain/jobs.py`
- `src/multilang/settings.py`
- `src/multilang/runtime.py`
- `src/multilang/services/provider_text_adapters.py`
- `src/multilang/services/language_identifier.py`
- `src/multilang/services/audio_voice_registry.py`
- `src/multilang/services/elevenlabs_speech_adapter.py`
- `src/multilang/services/google_translate_speech_adapter.py`
- `src/multilang/services/highlight_candidate_extraction.py`
- `tests/domain/test_jobs.py`
- `tests/test_settings.py`
- `tests/services/test_audio_voice_registry.py`
- `tests/services/test_elevenlabs_speech_adapter.py`
- `tests/services/test_google_translate_speech_adapter.py`

## Verification Commands
- `uv run pytest tests/domain/test_jobs.py tests/test_settings.py tests/services/test_audio_voice_registry.py -q` -> passed, 34 tests
- `uv run pytest tests/services/test_elevenlabs_speech_adapter.py tests/services/test_google_translate_speech_adapter.py -q` -> passed, 16 tests
- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.services.audio_voice_registry import select_voice; assert GenerationRequest(language='da', source_type='frequency').language is SupportedLanguage.DA; s=select_voice(SupportedLanguage.DA); assert (s.voice_id, s.locale)==('da-DK-ChristelNeural','da-DK'); print('danish_support_ok')"` -> passed

## Notes
- Frozen Danish frequency assets under `assets/frequency/da/` were not generated in this quick task. Frequency deck generation for Danish will still require curated `curated-v1.csv` and `rejected-v1.csv` assets before full frequency-mode production use.
- The workflow role template files referenced by the quick-task contract were not present in `.planning/templates/`, so execution followed the loaded `gsdd-quick` process directly.
