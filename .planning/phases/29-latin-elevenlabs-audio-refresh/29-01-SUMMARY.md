---
phase: 29-latin-elevenlabs-audio-refresh
plan: 01
status: completed
completed_at: 2026-06-22T00:00:00Z
selected_provider: google-translate-tts
selected_voice: la
provider_version: google-translate-tts-la
pronunciation_policy: google_translate_latin
---

# Phase 29 Plan 01 Summary

## Outcome

Phase 29 is complete. The current 50-card Classical Latin MVP audio pack is finalized on Google Translate TTS (`la`). ElevenLabs Italian is deferred after configured keys returned `HTTP 402 Payment Required`, Azure Italian remains fallback, FineVoice remains research-only, and no system-level eSpeak NG uninstall is requested.

## Changes

- Reconciled Latin audio provider policy so Google TTS is final for current export and ElevenLabs is optional/deferred.
- Added scanner-readable provider review evidence in `29-GOOGLE-TTS-FINAL-REVIEW.md`.
- Added executable v2.1 evidence in `tests/integration/test_v21_latin_google_tts_final_audio.py`.
- Strengthened export evidence to assert 100 Google TTS artifacts and stable Latin media packaging.
- Added `multilang` console script so planned CLI export commands run directly through `uv run multilang ...`.
- Updated current Latin docs/state to describe Google TTS finalization and bound old eSpeak mentions as historical/superseded context.
- Added `29-SECOND-PASS-REVIEW.md` with the final high-leverage review.

## Verification

- `uv run pytest tests/services/test_latin_audio.py tests/services/test_latin_audio_generation.py tests/services/test_latin_audio_refresh.py tests/services/test_latin_audio_samples.py -q` -> 23 passed
- `uv run pytest tests/integration/test_v21_latin_google_tts_final_audio.py tests/integration/test_v20_latin_audio_asset.py tests/integration/test_v20_latin_audio_evidence.py -q` -> 21 passed
- `uv run pytest tests/services/test_latin_mvp.py tests/cli/test_generate_latin_mvp_command.py tests/services/test_latin_export.py tests/integration/test_v20_latin_export_evidence.py tests/integration/test_v20_final_milestone_evidence.py -q` -> 50 passed
- `uv run pytest tests/integration/test_v20_existing_modes_regression_evidence.py tests/integration/test_v13_existing_modes_regression_evidence.py -q` -> 8 passed
- `uv run pytest tests/integration/test_v21_latin_google_tts_final_audio.py -q` -> 7 passed after final review update
- `uv run multilang export-latin-mvp --format apkg --output-dir exports/latin_mvp` -> completed; 50 cards, 100 media
- `uv run multilang export-latin-mvp --format csv --output-dir exports/latin_mvp` -> completed; 50 cards
- `uv run multilang export-latin-mvp --format tsv --output-dir exports/latin_mvp` -> completed; 50 cards
- `rg "espeak|eSpeak|espeak-ng|ElevenLabs" ...` could not run because shell `rg` is unavailable; equivalent workspace grep showed remaining hits are adapters, fallback/deferred tests, or historical/superseded context.

## Notes

- No live provider calls were made during finalization.
- No source pack entries, translations, grammar fields, card count, or Anki field order were changed.
- The generated export files in `exports/latin_mvp/` were refreshed by the verification commands.
