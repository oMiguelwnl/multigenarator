---
phase: 21-validation-fixtures-and-milestone-evidence
plan: 01
subsystem: validation
tags: [pytest, validators, audio-integrity, template-contracts, v1.3]

requires:
  - phase: 18-text-field-remediation
    provides: [definition and translation validators]
  - phase: 19-normal-card-export-and-responsive-template
    provides: [normal v1.3 export field contract and template reference validation]
  - phase: 20-word-audio-integrity-gate
    provides: [word-audio metadata integrity helper]
provides:
  - Shared v1.3 validation facade for VAL-01 issue categories
  - Stable normalized issue taxonomy for fixture and milestone evidence assertions
affects: [phase-21-fixtures, milestone-evidence, deck-validation]

tech-stack:
  added: []
  patterns: [facade-over-existing-validators, bounded-safe-validation-messages]

key-files:
  created: [src/multilang/services/v13_validation.py, tests/services/test_v13_validation.py]
  modified: []

key-decisions:
  - "Reuse existing text, template, and audio validators through a thin v1.3 facade instead of duplicating detection logic."
  - "Normalize validator output into bounded issue objects with stable enum values for downstream fixtures and evidence."

patterns-established:
  - "V13ValidationIssue messages stay field-specific and avoid raw private card excerpts or absolute paths."
  - "VAL-01 issue detection delegates to shipped remediation, text validation, template loader, and audio integrity boundaries."

requirements-completed: [VAL-01]

duration: 3min
completed: 2026-05-15
---

# Phase 21 Plan 01: Shared v1.3 Validation Surface Summary

**Deterministic v1.3 validator facade normalizing IPA repetition, Definition metadata, Translation mismatch, word-audio mismatch, and dangling template fields.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-15T13:14:28Z
- **Completed:** 2026-05-15T13:17:28Z
- **Tasks:** 2 completed
- **Files modified:** 2

## Accomplishments

- Added `V13ValidationIssueType`, immutable `V13ValidationIssue`, `validate_v13_card`, and `validate_v13_template_contract` as the shared VAL-01 validation surface.
- Covered normalized issue categories for IPA word repetition, banned Definition patterns, Translation/example mismatch, word_audio/Word mismatch, and dangling template fields.
- Reused existing validators from text remediation, text validation, template loading, and Phase 20 audio integrity rather than reimplementing divergent logic.

## Task Commits

1. **Task 1 RED: Normalize text-field validators for VAL-01** - `31047bd` (test)
2. **Task 1 GREEN: Normalize text-field validators for VAL-01** - `fbca99c` (feat)
3. **Task 2: Add audio and template validators for VAL-01** - `d4b8ca3` (test)

**Plan metadata:** committed after summary creation.

## Files Created/Modified

- `src/multilang/services/v13_validation.py` - Shared validator facade and stable normalized issue taxonomy.
- `tests/services/test_v13_validation.py` - Focused VAL-01 coverage for text, audio, and template issue branches.

## Decisions Made

- Reused existing validator boundaries to keep VAL-01 behavior consistent with shipped remediation/export gates.
- Kept normalized issue messages generic and bounded so evidence artifacts do not expose private deck excerpts or local absolute paths.

## Deviations from Plan

### Process Deviations

**1. Task 2 implementation existed before Task 2 RED tests**
- **Found during:** Task 2 (Add audio and template validators for VAL-01)
- **Issue:** The audio/template facade code was included in the Task 1 GREEN implementation commit, so Task 2 RED tests passed immediately instead of failing first.
- **Fix:** Added explicit Task 2 tests and verified the full planned suite; no additional production code change was required.
- **Files modified:** `tests/services/test_v13_validation.py`
- **Verification:** `python -m pytest tests/services/test_v13_validation.py tests/services/test_text_field_remediation.py tests/services/test_text_validation.py tests/services/test_audio_integrity.py tests/services/test_card_template_loader.py -q`
- **Committed in:** `d4b8ca3`

---

**Total deviations:** 0 auto-fixed code deviations; 1 TDD process deviation documented.
**Impact on plan:** VAL-01 functionality and coverage are complete; commit boundaries are less clean for Task 2 implementation because the production facade was introduced one commit early.

## TDD Gate Compliance

- Task 1: RED (`31047bd`) then GREEN (`fbca99c`) completed.
- Task 2: RED failed-fast condition was not met because Task 2 production behavior already existed in `fbca99c`; Task 2 coverage was committed in `d4b8ca3` and full verification passed.

## Issues Encountered

- Task 2 RED tests passed unexpectedly because the Task 1 implementation already included the audio and template facade branches. This was documented as a TDD process deviation and verified with the full planned suite.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - stub scan only found intentional empty test data/default lists, not user-facing placeholder behavior.

## Next Phase Readiness

- Ready for 21-02 to convert `card_issues_normalized.md` examples into executable fixtures using the stable issue enum values.
- No blockers for continuing Phase 21.

## Self-Check: PASSED

- Verified created files exist: `src/multilang/services/v13_validation.py`, `tests/services/test_v13_validation.py`, and this SUMMARY.
- Verified task commits exist: `31047bd`, `fbca99c`, `d4b8ca3`.
- Verified full planned test suite passes.

---
*Phase: 21-validation-fixtures-and-milestone-evidence*
*Completed: 2026-05-15*
