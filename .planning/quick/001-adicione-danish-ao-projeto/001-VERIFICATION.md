# Quick Task 001 Verification: adicione Danish ao projeto

## Verdict
passed

## Goal Check
The project now accepts Danish (`da`) as a supported language in the main domain contract, default settings, runtime naming, provider maps, language identification, and TTS selection surfaces.

## Evidence
- `GenerationRequest(language="da", source_type="frequency")` validates as `SupportedLanguage.DA`.
- `Settings(_env_file=None).supported_languages` includes `"da"` in the default list.
- Azure voice registry resolves Danish to `da-DK-ChristelNeural` with locale `da-DK`.
- ElevenLabs fallback TTS maps Danish to locale `da-DK`.
- Google Translate TTS maps Danish to code/locale `da`.

## Commands Run
- `uv run pytest tests/domain/test_jobs.py tests/test_settings.py tests/services/test_audio_voice_registry.py -q` -> passed, 34 tests
- `uv run pytest tests/services/test_elevenlabs_speech_adapter.py tests/services/test_google_translate_speech_adapter.py -q` -> passed, 16 tests
- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.services.audio_voice_registry import select_voice; assert GenerationRequest(language='da', source_type='frequency').language is SupportedLanguage.DA; s=select_voice(SupportedLanguage.DA); assert (s.voice_id, s.locale)==('da-DK-ChristelNeural','da-DK'); print('danish_support_ok')"` -> passed

## Residual Risk
- Full frequency-mode Danish decks need curated frequency assets in `assets/frequency/da/`. This quick task added language support wiring, not the 3000-card Danish asset set.
- The full test suite was not run because the codebase map documents known broad-suite drift; focused tests were used as the authoritative quick-task gate.
