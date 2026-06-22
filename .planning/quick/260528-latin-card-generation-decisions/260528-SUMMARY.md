# Quick Task 260528 Summary: Latin Card Generation Decisions

## Status

Completed.

## Changes Made

- Updated `tests/integration/test_v20_latin_audio_evidence.py` to align Phase 27 audio evidence with the current approved Latin audio policy:
  - provider: `google-translate-tts`
  - voice: `la`
  - pronunciation policy: `google_translate_latin`
  - public provider count: `{"google-translate-tts": 100}`
- Removed stale evidence assertions that belonged to the earlier pre-translation/pre-export boundary:
  - translation gates are now expected to be `approved`
  - audio gates are now expected to be `approved`
  - the test still verifies Latin remains outside the modern `generate --language la --source frequency` path

## Provider Decision Captured

- `word_audio`: Google Translate TTS Latin (`la`) via the existing manifest policy.
- `sentence_audio`: Google Translate TTS Latin (`la`) via the existing manifest policy.
- fallback order: ElevenLabs Italian, then Azure Italian.
- FineVoice remains research-only, not production.

## Verification

- `uv run pytest tests/integration/test_v20_latin_audio_evidence.py tests/cli/test_generate_latin_mvp_command.py::test_generate_latin_mvp_audio_json_prints_public_audio_summary -q` -> passed, `7 passed`.

## Notes

- No source-pack data, audio files, translation assets, export code, or public CLI contracts were changed.
- Plan numbering was corrected to `260528` after detecting existing quick-task history.
