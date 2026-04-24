---
phase: 04-audio-synthesis
plan: 01
subsystem: api
tags: [audio, azure-speech, tts, settings, testing]
requires:
  - phase: 03-sentence-quality-review-loop
    provides: accepted text records, supported language contracts, and the shipped runtime/settings foundation
provides:
  - typed Phase 4 audio asset and provenance contracts
  - deterministic Azure voice registry coverage for all seven supported languages
  - typed Azure speech settings and local audio storage defaults
affects: [phase-04-persistence, phase-04-synthesis, runtime, export]
tech-stack:
  added: []
  patterns: [separate display-vs-tts modeling, versioned in-repo voice registry, typed speech runtime settings]
key-files:
  created:
    - .planning/phases/04-audio-synthesis/04-01-SUMMARY.md
    - src/multilang/domain/audio.py
    - src/multilang/services/audio_voice_registry.py
    - tests/domain/test_audio.py
    - tests/services/test_audio_voice_registry.py
  modified:
    - src/multilang/settings.py
key-decisions:
  - "Keep learner-facing text and normalized TTS input separate in the audio contract so later synthesis normalization never mutates visible card text."
  - "Ship a versioned in-repo Azure voice matrix with ordered same-locale then approved cross-locale fallback instead of relying on provider defaults."
patterns-established:
  - "Audio identity is `(job_id, item_key, asset_kind)` with explicit `word` and `sentence` asset kinds."
  - "Azure voice selection resolves through a registry constant that runtime settings expose by version."
requirements-completed: []
duration: 3 min
completed: 2026-04-24
---

# Phase 4 Plan 1: Audio contracts and voice registry Summary

**Typed audio records now separate learner-visible text from normalized TTS input while a versioned Azure voice registry resolves deterministic word and sentence voices for all seven supported languages.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-24T14:41:53Z
- **Completed:** 2026-04-24T14:44:36Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Added Phase 4 domain contracts for audio asset identity, normalized TTS input, and persisted provenance metadata.
- Added a versioned Azure voice registry with deterministic fallback order for Portuguese, Spanish, English, French, German, Russian, and Dutch.
- Extended typed runtime settings with Azure Speech credentials, output format, local audio storage, and registry version exposure.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define typed audio contracts for separate word and sentence assets** - `90db7b3` (test), `9215e9a` (feat)
2. **Task 2: Add the versioned Azure voice registry and speech settings** - `7c4ba94` (test), `ffc22f4` (feat)

**Plan metadata:** pending local summary/docs commit

## Files Created/Modified
- `src/multilang/domain/audio.py` - defines audio asset kinds, synthesis status/provider enums, normalized TTS input, provenance, and the `AudioAssetRecord` contract.
- `src/multilang/services/audio_voice_registry.py` - hard-codes the approved Azure voice matrix and deterministic fallback resolution path.
- `src/multilang/settings.py` - exposes Azure Speech credentials, output format, local audio storage, and registry version settings.
- `tests/domain/test_audio.py` - locks the persisted audio identity, provenance, and display-vs-TTS separation contract.
- `tests/services/test_audio_voice_registry.py` - verifies supported-language coverage, deterministic fallback order, and typed Azure settings.

## Decisions Made
- Kept `display_text` separate from `tts_text` and SSML-oriented input so later normalization stays on the synthesis boundary instead of mutating learner-facing card text.
- Used a versioned registry constant as the shipping Azure voice contract so later runtime code cannot drift to implicit provider defaults.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `gsd-sdk` is unavailable in this environment, so automated state-handler updates could not be used.

## User Setup Required

None - this plan only added typed settings and test-covered registry/contracts.

## Next Phase Readiness
- Ready for Plan 04-02 to add audio persistence, repository reuse rules, and the Phase 4 schema migration on top of the new audio contracts.
- The Azure-first fallback policy, including the Dutch `nl-NL` to `nl-BE` path called out in Phase 4 planning, is now explicit in code.

## Self-Check: PASSED

- Found `.planning/phases/04-audio-synthesis/04-01-SUMMARY.md`
- Found task commit `90db7b3`
- Found task commit `9215e9a`
- Found task commit `7c4ba94`
- Found task commit `ffc22f4`
