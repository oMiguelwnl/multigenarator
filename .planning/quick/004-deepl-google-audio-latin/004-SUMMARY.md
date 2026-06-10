# Quick Task 004 Summary

## Status

Completed.

## Changes

- Kept `DeepL` as the default runtime translation provider in `src/multilang/settings.py`.
- Updated Latin provider policy metadata so:
  - `deepl` is `primary_translation`.
  - `google-translate` is `translation_candidate`.
  - `google-translate-tts` is `primary_audio_candidate`.
  - `elevenlabs-italian` and `finevoice` remain reserve audio candidates.
- Added `google_translate` to the audio provider contract in `src/multilang/domain/audio.py`.
- Added generic `mp3` as an audio format for Google Translate TTS output.
- Added `src/multilang/services/google_translate_speech_adapter.py`, an injectable Google Translate TTS adapter using the `translate_tts` endpoint and no new dependency.
- Wired `google_translate` into runtime audio provider selection in `src/multilang/runtime.py`.
- Added offline/fake tests for Google Translate TTS request construction, SSML stripping, MP3 writes, error handling, and runtime wiring.

## Verification Commands

- `python -m pytest -q tests/services/test_latin_audio_samples.py tests/services/test_provider_text_adapters.py tests/test_settings.py tests/services/test_google_translate_speech_adapter.py tests/test_runtime.py tests/services/test_audio_synthesis.py` -> passed, 45 tests.
- `python -m pytest -q tests/services/test_text_generation.py tests/services/test_elevenlabs_speech_adapter.py tests/services/test_latin_audio.py tests/cli/test_generate_latin_mvp_command.py tests/services/test_latin_mvp.py` -> passed, 65 tests.
- `python -m pytest -q tests/domain/test_audio.py tests/repositories/test_audio_repository.py tests/services/test_google_translate_speech_adapter.py tests/services/test_audio_synthesis.py` -> passed, 19 tests.

## Notes

- Google Translate TTS is implemented as an adapter, but live synthesis still depends on Google serving the public `translate_tts` endpoint.
- FineVoice remains candidate/policy-only; no FineVoice API adapter was added in this quick task.
