---
phase: 04-audio-synthesis
plan: 03
subsystem: api
tags: [audio, azure-speech, tts, storage, testing]
requires:
  - phase: 04-audio-synthesis
    provides: typed audio contracts, voice registry, and persisted audio repository rules from Plans 04-01 and 04-02
provides:
  - accepted-text-only audio synthesis service for word and sentence assets
  - deterministic storage-path construction from normalized input hashes and voice choice
  - fallback-aware media integrity validation before audio is accepted
affects: [phase-04-runtime, resume-reuse, export]
tech-stack:
  added: []
  patterns: [prepare-then-synthesize audio planning, deterministic storage by hash and voice, failed-asset records instead of silent drops]
key-files:
  created:
    - .planning/phases/04-audio-synthesis/04-03-SUMMARY.md
    - src/multilang/services/audio_synthesis.py
    - tests/services/test_audio_synthesis.py
  modified: []
key-decisions:
  - "Have the synthesis service return failed asset records instead of silently skipping invalid media so later orchestration can persist and count failures explicitly."
  - "Split audio planning from synthesis execution so runtime orchestration can check deterministic reuse before making provider calls."
patterns-established:
  - "Accepted text is normalized into `tts_text` and SSML-safe input without mutating learner-facing text."
  - "Storage paths are derived from asset kind, registry version, selected voice, and normalized hashes."
requirements-completed: []
duration: 6 min
completed: 2026-04-24
---

# Phase 4 Plan 3: Audio synthesis service Summary

**Phase 4 now has an accepted-text-only synthesis boundary that normalizes TTS input safely, persists fallback choice, and rejects invalid media before audio records are treated as successful.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-24T15:10:00Z
- **Completed:** 2026-04-24T15:16:00Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Added `AudioSynthesisService` with injectable adapter support for deterministic voice selection and separate word/sentence asset synthesis.
- Enforced accepted-text gating, safe TTS normalization, deterministic storage keys, and media-integrity validation in one service boundary.
- Added service tests covering review-required rejection, fallback persistence, deterministic storage reuse, and invalid-media failure behavior.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build the Azure-first audio synthesis and integrity service** - `0cba94a` (test), `9d72e43` (feat)

**Plan metadata:** pending local summary/docs commit

## Files Created/Modified
- `src/multilang/services/audio_synthesis.py` - prepares and synthesizes separate word and sentence assets with deterministic voice and storage rules.
- `tests/services/test_audio_synthesis.py` - locks accepted-text gating, fallback handling, integrity checks, and separate asset synthesis.

## Decisions Made
- Returned failed audio records with explicit provenance instead of dropping unsuccessful synthesis attempts so later runtime layers can persist and report failures.
- Exposed audio preparation separately from final synthesis so reuse checks can happen before adapter calls.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `gsd-sdk` is unavailable in this environment, so automated state-handler updates could not be run.

## User Setup Required

Azure Speech credentials are still the intended live provider setup for later runtime wiring:
- `MULTILANG_AZURE_SPEECH_KEY`
- `MULTILANG_AZURE_SPEECH_REGION`

## Next Phase Readiness
- Ready for Plan 04-04 to reuse prepared audio metadata on the shipped runtime path and expose CLI-visible audio counters.
- The service boundary now gives orchestration code enough deterministic data to decide reuse before synthesis.

## Self-Check: PASSED

- Found `.planning/phases/04-audio-synthesis/04-03-SUMMARY.md`
- Found task commit `0cba94a`
- Found task commit `9d72e43`
