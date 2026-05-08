---
phase: 16-end-to-end-v12-audit
plan: 02
subsystem: testing
tags: [pytest, integration, phonetics, regression, source-isolation]

requires:
  - phase: 13-highlight-export-and-template
    provides: Distinct normal/manual/highlight export field and note-type contracts
  - phase: 15-phonetics-template-refresh
    provides: Refreshed Russian phonetics template, field set, audio references, and APKG evidence
provides:
  - Phase 16 wrapper evidence for refreshed Russian phonetics APKG/template/audio behavior
  - Phase 16 wrapper evidence for frequency, custom word-list, CLI source, and highlight privacy regressions
  - Direct assertions that frequency/manual/highlight export contracts remain isolated
affects: [phase-16-audit, phonetics-export, existing-mode-regressions, v1.2-evidence]

tech-stack:
  added: []
  patterns: [audit wrapper tests, path-loaded integration evidence modules, direct contract assertions]

key-files:
  created:
    - tests/integration/test_v12_phonetics_and_existing_modes_audit.py
  modified: []

key-decisions:
  - "Phase 16 audit wrappers re-execute prior evidence functions and add local direct assertions instead of duplicating the full fixture setup."
  - "Integration evidence modules are loaded by file path so wrapper execution uses the checked-out test files unambiguously."

patterns-established:
  - "Final audit tests can aggregate prior phase evidence while adding explicit field/note-type assertions for milestone-level traceability."

requirements-completed: [EVID-01]

duration: 4min
completed: 2026-05-08
---

# Phase 16 Plan 02: Phonetics and Existing-Mode Audit Summary

**Phase 16 now re-runs refreshed phonetics export evidence plus frequency, custom, highlight CLI, and privacy regression boundaries from one audit surface.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-08T12:40:04Z
- **Completed:** 2026-05-08T12:44:04Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Added `tests/integration/test_v12_phonetics_and_existing_modes_audit.py` to call Phase 15 Russian phonetics APKG/template/audio evidence and assert the exact nine-field phonetics contract directly.
- Added audit coverage that re-runs frequency deck, custom word-list, public/internal source CLI, and highlight privacy-safe QA regression evidence.
- Asserted frequency/manual exports still include `Translation`, highlight exports still exclude it, and normal/manual/highlight note type names remain distinct.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add phonetics export audit wrapper** - `ac53a28` (test)
2. **Task 2: Add existing-mode regression audit wrapper** - `8480e32` (test)

**Plan metadata:** pending final docs commit

## Files Created/Modified

- `tests/integration/test_v12_phonetics_and_existing_modes_audit.py` - Phase 16 regression wrapper for phonetics export evidence, existing-mode behavior, highlight CLI/privacy boundaries, and direct field/note-type isolation assertions.

## Decisions Made

- Reused existing evidence functions from Phase 15 and v1.2 regression tests to keep the Phase 16 audit tied to already-maintained product evidence.
- Loaded integration modules by file path in the wrapper so Python import/package ambiguity cannot execute stale installed test modules.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Loaded audit evidence modules by file path**
- **Found during:** Task 2 (existing-mode regression audit wrapper)
- **Issue:** Package-style importing of `tests.integration` could resolve ambiguously during wrapper execution, causing the wrapper to call stale phonetics evidence instead of the checked-out test file.
- **Fix:** Added a small file-path loader in the audit wrapper and used it for both phonetics and existing-mode evidence modules.
- **Files modified:** `tests/integration/test_v12_phonetics_and_existing_modes_audit.py`
- **Verification:** `python -m pytest tests/integration/test_v12_phonetics_and_existing_modes_audit.py tests/integration/test_v12_existing_mode_regression_boundary.py -q` passed.
- **Committed in:** `8480e32`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The fix keeps the wrapper deterministic without changing production behavior or expanding scope.

## Issues Encountered

- Existing repository worktree contains unrelated uncommitted phonetics/CLI changes from outside this plan; they were not staged or committed by this plan.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Verification

- `python -m pytest tests/integration/test_v12_phonetics_and_existing_modes_audit.py tests/integration/test_russian_phoneme_template_refresh_flow.py -q` — passed
- `python -m pytest tests/integration/test_v12_phonetics_and_existing_modes_audit.py tests/integration/test_v12_existing_mode_regression_boundary.py -q` — passed
- `python -m pytest tests/integration/test_v12_phonetics_and_existing_modes_audit.py tests/integration/test_russian_phoneme_template_refresh_flow.py tests/integration/test_v12_existing_mode_regression_boundary.py -q` — passed

## Next Phase Readiness

- Phase 16 Plan 03 can assemble final v1.2 audit evidence from completed local-highlight, phonetics, and existing-mode audit surfaces.
- No blockers remain for the Phase 16 regression/phonetics audit wrapper.

## Self-Check: PASSED

- Found `tests/integration/test_v12_phonetics_and_existing_modes_audit.py`.
- Found `.planning/phases/16-end-to-end-v12-audit/16-02-SUMMARY.md`.
- Found task commit `ac53a28`.
- Found task commit `8480e32`.

---
*Phase: 16-end-to-end-v12-audit*
*Completed: 2026-05-08*
