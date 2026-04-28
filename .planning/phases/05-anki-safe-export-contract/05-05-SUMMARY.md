---
phase: 05-anki-safe-export-contract
plan: 05
subsystem: verification
tags: [anki, apkg, template, audio, human-verification]
requires:
  - phase: 05-04
    provides: shipped `multilang export` command and generated Anki package artifacts
provides:
  - human-approved Anki Desktop import verification for the generated `.apkg`
  - confirmation that `Translation` is hidden on the front and revealed on the back
  - confirmation that packaged word and sentence audio play after import
  - clean Phase 5 code-review gate after fixing export media and identity consistency warnings
affects: [phase-05-completion, anki-export, product-readiness]
tech-stack:
  added: []
  patterns: [human checkpoint closes real-product behavior that automated package tests cannot fully prove]
key-files:
  created:
    - .planning/phases/05-anki-safe-export-contract/05-05-SUMMARY.md
    - .planning/phases/05-anki-safe-export-contract/05-REVIEW.md
  modified:
    - src/multilang/runtime.py
    - src/multilang/domain/exporting.py
    - tests/integration/test_export_job_flow.py
    - tests/domain/test_exporting.py
key-decisions:
  - "Treat Anki Desktop import behavior and packaged audio playback as the final release gate for the export contract."
patterns-established:
  - "Automated export artifact tests are necessary but not sufficient; Anki package behavior must be confirmed in the real desktop app."
  - "All export formats validate media references before writing artifacts, not only `.apkg` packages."
requirements-completed: [CARD-03, EXPT-01, EXPT-03]
duration: 7min
completed: 2026-04-28
---

# Phase 5 Plan 05: Real Anki Import Verification Summary

**Anki Desktop verification confirms import-safe `.apkg` behavior, correct translation reveal rules, and playable packaged audio**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-28T12:37:00Z
- **Completed:** 2026-04-28T12:44:50Z
- **Tasks:** 1
- **Files modified:** 6

## Accomplishments
- Confirmed the refreshed `.apkg` imports into Anki Desktop without manual field remapping.
- Confirmed `Translation` stays hidden on the card front and appears on the back with the expected template behavior.
- Confirmed both packaged word audio and sentence audio play successfully after import.
- Resolved code-review warnings so CSV/TSV exports fail loudly on missing media and visible `SortIndex` cannot diverge from stable note identity.
- Re-ran the Phase 5 export verification tests after human approval and review fixes.

## Task Commits

1. **Task 1: Verify real Anki import, template reveal behavior, and audio playback** - human checkpoint approved.
2. **Review gate fix: Enforce export media and identity consistency** - `8b9a241` (fix)

**Plan metadata:** pending

## Files Created/Modified
- `.planning/phases/05-anki-safe-export-contract/05-05-SUMMARY.md` - records the final human Anki verification result and automated pre-check outcome.
- `.planning/phases/05-anki-safe-export-contract/05-REVIEW.md` - records the clean re-review after warning fixes.
- `src/multilang/runtime.py` - validates media references for every export format before artifacts are written.
- `src/multilang/domain/exporting.py` - rejects visible `SortIndex` values that do not match stable row identity.
- `tests/integration/test_export_job_flow.py` - covers missing-media failures for `.apkg`, CSV, and TSV exports.
- `tests/domain/test_exporting.py` - covers rejection of mismatched visible sort indexes.

## Decisions Made
- Accepted the user's explicit checkpoint approval as the final real-product signal for Anki import, reveal behavior, and audio playback.
- Kept this plan documentation-only because the verification did not require code changes after the earlier template and review-fixture gap fixes.

## Deviations from Plan

The human checkpoint executed as written. The required code-review gate found two warning-level correctness gaps, which were fixed before phase closure.

### Auto-fixed Issues

**1. Missing media validation on CSV/TSV exports**
- **Found during:** Phase 5 code-review gate
- **Issue:** CSV and TSV exports could be written with stale `[sound:...]` references after media files were deleted.
- **Fix:** Runtime export now builds and validates the media index before dispatching any export format.
- **Files modified:** `src/multilang/runtime.py`, `tests/integration/test_export_job_flow.py`
- **Verification:** Missing-media integration test now runs across `apkg`, `csv`, and `tsv`.
- **Committed in:** `8b9a241`

**2. Visible `SortIndex` could diverge from stable row identity**
- **Found during:** Phase 5 code-review gate
- **Issue:** A caller could construct a row where exported `SortIndex` differed from the value used for deterministic note GUID identity.
- **Fix:** `ExportCardRow` now rejects explicit `SortIndex` values that do not match `identity.sort_index`.
- **Files modified:** `src/multilang/domain/exporting.py`, `tests/domain/test_exporting.py`
- **Verification:** Domain test confirms mismatched sort indexes raise validation errors.
- **Committed in:** `8b9a241`

## Issues Encountered
- `gsd-sdk` is not available in this shell, so tracking updates were applied directly instead of through `gsd-sdk query` helpers.
- The first code-review pass found two warning-level issues. Both were fixed and the re-review status is clean.

## Verification
- Human checkpoint: approved by the user for import without remapping, hidden front-side translation, back-side translation reveal, and playable word/sentence audio.
- Automated check before review fixes: `uv run pytest tests/services/test_export_anki_package.py tests/cli/test_export_command.py tests/integration/test_export_job_flow.py -q`
- Result before review fixes: `9 passed in 6.88s`
- Automated check after review fixes: `uv run pytest tests/services/test_export_anki_package.py tests/cli/test_export_command.py tests/integration/test_export_job_flow.py -q`
- Result after review fixes: `11 passed in 14.91s`
- Code review re-check: clean, with `9 passed in 12.03s` on the targeted review suite.

## User Setup Required

None - the user already completed the required Anki Desktop validation.

## Next Phase Readiness
- Phase 5 has completed all planned implementation and real-product verification gates.
- Phase 5 code-review warnings are closed.
- The milestone is ready for final phase-level verification and closure.

## Self-Check: PASSED
- Created `05-05-SUMMARY.md`.
- Captured explicit human approval for all checkpoint acceptance criteria.
- Re-ran the required Phase 5 export test subset successfully.

---
*Phase: 05-anki-safe-export-contract*
*Completed: 2026-04-28*
