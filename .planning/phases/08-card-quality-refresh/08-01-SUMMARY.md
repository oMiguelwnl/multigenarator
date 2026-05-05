---
phase: 08-card-quality-refresh
plan: 01
status: complete
completed_at: "2026-05-02T19:10:43Z"
key_files:
  - src/multilang/services/audio_synthesis.py
  - src/multilang/services/azure_speech_adapter.py
  - tests/services/test_audio_synthesis.py
  - tests/services/test_azure_speech_adapter.py
---

# Phase 08 Plan 01: Azure Word Audio Prominence Summary

Word audio now receives Azure SSML prosody prominence while sentence audio keeps the plain speech shape.

## What Changed

- Added word-only `<prosody rate="-10%" pitch="+8%" volume="+20%">` wrapping in audio synthesis normalization.
- Preserved internally generated safe `<prosody>` SSML when the Azure adapter wraps legacy `<speak>` input in `<voice>`.
- Added regression tests for word-only prominence and Azure SSML preservation.

## Validation

- `uv run pytest tests/services/test_audio_synthesis.py tests/services/test_azure_speech_adapter.py -x` — passed.

## Deviations from Plan

- Commits were skipped because the user explicitly requested no commits unless explicitly requested.

## Self-Check: PASSED
