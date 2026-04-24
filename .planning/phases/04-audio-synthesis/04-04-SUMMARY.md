---
phase: 04-audio-synthesis
plan: 04
subsystem: runtime
tags: [audio, cli, runtime, integration-testing, reuse]
requires:
  - phase: 04-audio-synthesis
    provides: persisted audio rows, synthesis service contracts, and deterministic voice-selection rules from Plans 04-01 through 04-03
provides:
  - shipped runtime orchestration for accepted-text audio generation and reuse
  - CLI counters for processed, reused, fallback, and failed audio assets
  - integration coverage proving resume reuses persisted audio rows and storage paths
affects: [phase-05-export, runtime, operator-workflows]
tech-stack:
  added: []
  patterns: [accepted-text-only audio stage orchestration, reuse-before-synthesis, CLI-visible audio lifecycle counters]
key-files:
  created:
    - .planning/phases/04-audio-synthesis/04-04-SUMMARY.md
    - src/multilang/services/generate_audio_items.py
    - tests/services/test_generate_audio_items.py
    - tests/integration/test_audio_job_flow.py
  modified:
    - src/multilang/runtime.py
    - src/multilang/cli.py
    - src/multilang/repositories/text_repository.py
    - src/multilang/services/audio_synthesis.py
    - tests/cli/test_generate_command.py
key-decisions:
  - "Keep audio work in the existing `JobStage.SYNTHESIZE_AUDIO` stage and run it immediately after accepted text generation on the shipped runtime path."
  - "Count reused, fallback, and failed audio assets explicitly on the CLI so missing or degraded audio never looks like silent success."
patterns-established:
  - "Runtime audio generation queries accepted text rows, checks deterministic reuse first, then synthesizes only missing assets."
  - "Resume runs preserve audio row identity and storage paths instead of duplicating media rows."
requirements-completed: []
duration: 18 min
completed: 2026-04-24
---

# Phase 4 Plan 4: Shipped-path audio runtime Summary

**The shipped runtime now orchestrates accepted-text audio generation with deterministic reuse and CLI-visible counters, while integration tests prove resume keeps one persisted row per word and sentence asset.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-04-24T15:18:00Z
- **Completed:** 2026-04-24T15:36:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Added `GenerateAudioItemsService` to load accepted text only, check reusable assets first, and synthesize missing word and sentence audio rows.
- Wired audio generation into the shipped runtime and CLI output with explicit processed, reused, fallback, and failed counters.
- Added shipped-path tests proving audio rows and storage paths are reused on resume instead of being duplicated.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add accepted-text audio orchestration with reusable asset lookup** - `0415a46` (test), `d273565` (feat)
2. **Task 2: Wire shipped-path audio generation, counters, and end-to-end reuse tests** - `e310b93` (feat)

**Plan metadata:** pending local summary/docs commit

## Files Created/Modified
- `src/multilang/services/generate_audio_items.py` - orchestrates accepted-text audio reuse and synthesis under `JobStage.SYNTHESIZE_AUDIO`.
- `src/multilang/runtime.py` - composes audio repository, synthesis, and orchestration services into the shipped runtime path.
- `src/multilang/cli.py` - prints explicit audio lifecycle counters after text generation.
- `src/multilang/repositories/text_repository.py` - adds accepted-text query support for audio-stage gating.
- `src/multilang/services/audio_synthesis.py` - exposes prepare-vs-synthesize steps needed for reuse-before-synthesis orchestration.
- `tests/services/test_generate_audio_items.py` - verifies reuse, accepted-text-only behavior, and fallback/failure accounting.
- `tests/cli/test_generate_command.py` - verifies shipped CLI audio counters.
- `tests/integration/test_audio_job_flow.py` - proves resume reuses persisted audio rows and storage paths.

## Decisions Made
- Ran audio generation immediately after accepted text generation on the existing shipped path instead of adding a separate audio command.
- Treated reuse as a first-class runtime decision driven by deterministic hashes and selected voice configuration before adapter calls.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added accepted-text query and prepare-before-synthesize support**
- **Found during:** Task 1 and Task 2
- **Issue:** The existing repositories and synthesis service could not support reuse-before-synthesis because there was no accepted-text query and no public way to prepare deterministic asset metadata without immediately synthesizing.
- **Fix:** Added `TextRepository.list_accepted_records()` plus prepare/synthesize split methods on `AudioSynthesisService`, then used them in the runtime orchestrator.
- **Files modified:** `src/multilang/repositories/text_repository.py`, `src/multilang/services/audio_synthesis.py`, `src/multilang/services/generate_audio_items.py`
- **Verification:** `uv run pytest tests/services/test_generate_audio_items.py tests/cli/test_generate_command.py tests/integration/test_audio_job_flow.py -q`
- **Committed in:** `d273565`, `e310b93`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The added query and preview boundary were required to make deterministic reuse possible on the shipped runtime path; no user-visible scope expansion beyond the planned audio flow.

## Issues Encountered
- `gsd-sdk` is unavailable in this environment, so automated state-handler updates could not be run.

## Known Stubs
- `src/multilang/runtime.py` - `_RuntimeAudioAdapter` writes deterministic local bytes for shipped-path verification instead of calling the real Azure Speech SDK. This keeps tests and runtime reuse coverage working, but live Azure synthesis still needs a provider-backed adapter and credential wiring to fully satisfy the Phase 4 product goal.

## User Setup Required

Azure Speech remains the intended live provider setup:
- `MULTILANG_AZURE_SPEECH_KEY`
- `MULTILANG_AZURE_SPEECH_REGION`

## Next Phase Readiness
- Runtime orchestration, reuse rules, and CLI counters are in place for Phase 4 audio.
- A real Azure SDK-backed runtime adapter is still needed before Phase 4 can be considered fully product-complete for live synthesis.

## Self-Check: PASSED

- Found `.planning/phases/04-audio-synthesis/04-04-SUMMARY.md`
- Found task commit `0415a46`
- Found task commit `d273565`
- Found task commit `e310b93`
