---
phase: 20-word-audio-integrity-gate
plan: 02
subsystem: audio-generation
tags: [audio, cache-reuse, validation, pytest]
requires:
  - phase: 20-01
    provides: Strict word-audio integrity helper
provides:
  - Generation-time rejection of mismatched reusable word audio
  - Regeneration path for corrupted word-audio cache hits
affects: [audio-generation, export-assembly]
tech-stack:
  added: []
  patterns: [module-private reuse guard, exact word-audio cache validation]
key-files:
  created: []
  modified: [src/multilang/services/generate_audio_items.py, tests/services/test_generate_audio_items.py]
key-decisions:
  - "Reusable WORD audio is accepted only after passing the Phase 20 exact Word integrity helper; mismatches are regenerated and not counted as reused."
patterns-established:
  - "Sentence audio cache reuse remains outside the word-audio exact Word gate."
requirements-completed: [AUD-01, AUD-02]
duration: 4min
completed: 2026-05-13
---

# Phase 20 Plan 02: Word Audio Cache Regeneration Summary

**Generation-time cache guard that regenerates corrupted reusable word audio instead of carrying stale metadata into new jobs**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-13T17:44:20Z
- **Completed:** 2026-05-13T17:48:01Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added a private reuse guard in `GenerateAudioItemsService` that applies `word_audio_matches_word` to WORD cache hits.
- Ensured mismatched reusable WORD assets are ignored, regenerated through `synthesize_prepared_asset`, and not counted in `reused_items`.
- Added regression coverage proving sentence audio reuse and highlight sentence-only behavior remain unchanged.

## Task Commits

1. **Task 1: Regenerate mismatched reusable word audio per AUD-02** - `dc7330f` (test), `bea459b` (feat)
2. **Task 2: Keep sentence audio reuse and valid word reuse unchanged per AUD-02** - `545cf19` (test)

## Files Created/Modified

- `src/multilang/services/generate_audio_items.py` - Validates reusable WORD assets before accepting cache hits.
- `tests/services/test_generate_audio_items.py` - Covers mismatched word cache regeneration and scoped sentence reuse behavior.

## Decisions Made

- Mismatched reusable word-audio assets are treated as cache misses rather than hard failures during generation, allowing safe regeneration before export.

## Deviations from Plan

None - plan executed as written.

## Issues Encountered

- TDD red phase failed as expected because the service previously reused corrupted word-audio cache hits and incremented `reused_items`.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Next Phase Readiness

- Plan 20-03 can treat any remaining mismatch as unrepaired and block export deterministically.

## Self-Check: PASSED

- Modified files exist: `src/multilang/services/generate_audio_items.py`, `tests/services/test_generate_audio_items.py`.
- Commits exist: `dc7330f`, `bea459b`, `545cf19`.
- Verification passed: `python -m pytest tests/services/test_generate_audio_items.py tests/services/test_audio_integrity.py -q` (15 passed).

---
*Phase: 20-word-audio-integrity-gate*
*Completed: 2026-05-13*
