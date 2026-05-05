---
phase: 12-highlight-generation-audio-and-qa
plan: 01
subsystem: generation-validation
tags: [highlight-generation, source-profiles, text-validation, tdd]
requires:
  - phase: 11-highlight-pipeline-integration
    provides: Highlight source mode and source profile contracts
provides:
  - Highlight source-profile validation using 6-16 token sentence bounds
  - Translation-optional validation path for highlight examples
  - Regression coverage for existing frequency and word-list validation behavior
affects: [highlight-generation, text-quality, phase-12]
tech-stack:
  added: []
  patterns: [source-profile-driven-validation, tdd-red-green]
key-files:
  created: []
  modified:
    - src/multilang/services/text_validation.py
    - src/multilang/services/generate_text_items.py
    - tests/services/test_text_validation.py
    - tests/services/test_generate_text_items.py
key-decisions:
  - "Validation behavior is resolved through SourceProfile contracts before deterministic checks, including translation-required and sentence-token policies."
patterns-established:
  - "GenerateTextItemsService resolves a safe source profile before calling TextValidationService."
  - "TextValidationService keeps class defaults while accepting per-call sentence bounds."
requirements-completed: [GEN-01, GEN-02]
duration: 18min
completed: 2026-05-05
---

# Phase 12 Plan 01: Highlight Source-Profile Validation Summary

**Source-profile-driven text validation lets highlight examples use richer 6-16 token sentences without requiring Translation validation.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-05-05T17:59:54Z
- **Completed:** 2026-05-05T18:18:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added configurable sentence-token bounds to deterministic text validation while preserving the default 4-12 token behavior.
- Routed generated text validation through `get_source_profile`, including `kindle-highlights` translation-optional validation and 6-16 token bounds.
- Added TDD coverage for highlight profile behavior, existing frequency/word-list behavior, and inferred source defaults.

## Task Commits

1. **Task 1 RED: Configurable validation limits tests** - `cc3ecd2` (test)
2. **Task 1 GREEN: Configurable validation limits implementation** - `6774fcf` (feat)
3. **Task 2 RED: Source-profile routing tests** - `c24a822` (test)
4. **Task 2 GREEN: Source-profile validation routing** - `11387aa` (feat)

_Note: TDD tasks used separate test and implementation commits._

## Files Created/Modified

- `src/multilang/services/text_validation.py` - Added optional per-call `min_sentence_tokens` and `max_sentence_tokens` parameters.
- `src/multilang/services/generate_text_items.py` - Resolves source profiles and passes validation policy into deterministic validation.
- `tests/services/test_text_validation.py` - Covers configurable highlight bounds and unchanged default bounds.
- `tests/services/test_generate_text_items.py` - Covers highlight, frequency, word-list, and inferred profile routing.

## Decisions Made

- Use `SourceProfile` as the single policy source for translation validation and sentence length limits.
- Infer absent source types as `frequency` when rank/level exists and `word-list` otherwise, preserving existing candidate semantics.

## Deviations from Plan

None - plan executed as written.

## Issues Encountered

- `uv` is not installed in this execution environment, so verification was run with `python -m pytest` instead of `uv run pytest`.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Next Phase Readiness

- Plan 02 can now attach privacy-safe highlight context and rely on source-profile validation for richer highlight examples.

## Self-Check: PASSED

- Verified modified files exist.
- Verified commits exist in git history.
- Verification passed: `python -m pytest tests/services/test_generate_text_items.py tests/services/test_text_validation.py -q` (26 passed).

---
*Phase: 12-highlight-generation-audio-and-qa*
*Completed: 2026-05-05*
