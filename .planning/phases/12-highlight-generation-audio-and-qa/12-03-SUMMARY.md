---
phase: 12-highlight-generation-audio-and-qa
plan: 03
subsystem: highlight-audio-export-assembly
tags: [highlight-cards, audio, export-rows, integration-tests, tdd]
requires:
  - phase: 12-highlight-generation-audio-and-qa
    provides: Plans 01-02 source-aware highlight text generation
provides:
  - Highlight card assembly with blank Translation and Image
  - Word and sentence audio evidence for accepted highlight rows
  - Integration proof for highlight text, audio, and assembled card rows
affects: [highlight-export, audio-synthesis, phase-13]
tech-stack:
  added: []
  patterns: [source-profile-card-assembly, source-agnostic-audio-item-keys]
key-files:
  created:
    - tests/integration/test_highlight_generation_audio_flow.py
  modified:
    - src/multilang/services/assemble_export_cards.py
    - tests/services/test_assemble_export_cards.py
    - tests/services/test_generate_audio_items.py
key-decisions:
  - "Highlight export rows use source profile export policy to blank Translation while preserving audio, IPA/spoken form, definitions, sentence, and Image."
patterns-established:
  - "Audio generation remains source-agnostic and operates on accepted item keys for highlight rows."
requirements-completed: [GEN-01]
duration: 15min
completed: 2026-05-05
---

# Phase 12 Plan 03: Highlight Audio and Card Assembly Summary

**Accepted highlight text now flows into word audio, sentence audio, and highlight export rows with blank Translation and Image.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-05T18:40:00Z
- **Completed:** 2026-05-05T18:55:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Updated card assembly to resolve source profiles and blank `Translation` for highlight rows.
- Added service-level proof that accepted highlight rows generate word and sentence audio assets through the existing audio path.
- Added integration evidence that a highlight fixture assembles into a `kindle-highlights` card with audio tags, IPA/spoken form, definitions, example sentence, and blank Image.

## Task Commits

1. **Task 1 RED: Highlight card assembly test** - `1db55e9` (test)
2. **Task 1 GREEN: Highlight assembly implementation** - `cdda03d` (feat)
3. **Task 2 Evidence: Highlight audio/integration tests** - `f36f2f2` (test)

## Files Created/Modified

- `src/multilang/services/assemble_export_cards.py` - Uses source profile export policy to blank highlight Translation.
- `tests/services/test_assemble_export_cards.py` - Covers highlight ordered fields, audio tags, blank Translation, and blank Image.
- `tests/services/test_generate_audio_items.py` - Covers accepted highlight word/sentence audio and review-required skips.
- `tests/integration/test_highlight_generation_audio_flow.py` - End-to-end deterministic highlight text/audio/card evidence.

## Decisions Made

- Keep audio generation source-agnostic because existing accepted-record item-key handling already supports highlight keys.

## Deviations from Plan

None - plan executed as written.

## TDD Gate Compliance

- Task 2 audio/integration tests passed on first run because existing `GenerateAudioItemsService` was already source-agnostic. No production code change was needed for Task 2; the evidence commit documents this explicitly.

## Issues Encountered

- `uv` is not installed in this environment, so verification was run with `python -m pytest`.

## User Setup Required

None - no live Azure or provider calls were used.

## Known Stubs

None.

## Next Phase Readiness

- Plan 04 can build QA reports and phase evidence using the highlight audio/card integration proof.

## Self-Check: PASSED

- Verified created integration test file exists.
- Verified commits exist in git history.
- Verification passed: `python -m pytest tests/services/test_generate_audio_items.py tests/services/test_assemble_export_cards.py tests/integration/test_highlight_generation_audio_flow.py -q` (18 passed).

---
*Phase: 12-highlight-generation-audio-and-qa*
*Completed: 2026-05-05*
