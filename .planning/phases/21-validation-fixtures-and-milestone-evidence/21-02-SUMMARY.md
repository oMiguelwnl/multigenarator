---
phase: 21-validation-fixtures-and-milestone-evidence
plan: 02
subsystem: validation
tags: [pytest, fixtures, v1.3, validation, milestone-evidence]

requires:
  - phase: 21-validation-fixtures-and-milestone-evidence
    provides: [shared v1.3 validation facade from plan 21-01]
provides:
  - Scanner-readable VAL-02 fixture catalog for normalized issue examples
  - Integration tests that execute fixture rows through the shared v1.3 validators
  - Additional facade coverage for wrong-sense Definition and sentence_audio layout regressions
affects: [milestone-evidence, deck-validation, v1.3-quality-gates]

tech-stack:
  added: []
  patterns: [json-fixture-catalog, facade-backed-regression-fixtures, source-line-traceability]

key-files:
  created:
    - tests/fixtures/v13/card_issues_normalized_cases.json
    - tests/integration/test_v13_normalized_issue_fixtures.py
  modified:
    - src/multilang/services/v13_validation.py
    - src/multilang/services/text_field_remediation.py

key-decisions:
  - "Use the shared v1.3 validation facade for fixture execution while extending existing validator boundaries where fixtures exposed missing correctness checks."
  - "Keep fixture data synthetic and traceable to card_issues_normalized.md source lines instead of private APKG excerpts."

patterns-established:
  - "VAL-02 fixtures include source_document, source_lines, coverage metadata, and expected normalized issue types for scanner-readable milestone evidence."
  - "Fixture tests compare stable issue_type values rather than implementation-specific error text."

requirements-completed: [VAL-02]

duration: 4min
completed: 2026-05-15
---

# Phase 21 Plan 02: Normalized Issue Fixture Evidence Summary

**Executable VAL-02 regression fixtures now prove normalized IPA, Definition, Translation, template, and word-audio defects through the shared v1.3 validator facade.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-15T13:20:54Z
- **Completed:** 2026-05-15T13:24:59Z
- **Tasks:** 2 completed
- **Files modified:** 4

## Accomplishments

- Created `card_issues_normalized_cases.json` with bad and corrected/pass examples mapped to source lines and all eight summary action groups.
- Added an integration fixture runner that builds synthetic `ExportCardRow`, `AudioAssetRecord`, and `CardTemplate` inputs and asserts stable normalized issue-type output.
- Extended existing validation boundaries to reject the known `дости́чь` wrong-sense Definition, grammar-only perfective metadata, and missing normal sentence-audio layout selectors.

## Task Commits

Each task was committed atomically:

1. **Task 1: Encode normalized bad and corrected examples for VAL-02** - `791bb4d` (test)
2. **Task 2 RED: Run normalized fixtures through validators per VAL-02** - `8225cf7` (test)
3. **Task 2 GREEN: Implement VAL-02 fixture validation gaps** - `16a8489` (feat)

**Plan metadata:** committed after summary creation.

## Files Created/Modified

- `tests/fixtures/v13/card_issues_normalized_cases.json` - Scanner-readable normalized issue fixture catalog with source-line and coverage metadata.
- `tests/integration/test_v13_normalized_issue_fixtures.py` - Integration tests loading each fixture row into the shared v1.3 validators.
- `src/multilang/services/v13_validation.py` - Added normalized sentence-audio layout issue detection in the existing template facade.
- `src/multilang/services/text_field_remediation.py` - Tightened existing Definition validation for known corrected meanings and grammar-only perfective metadata.

## Decisions Made

- Used stable `issue_type.value` comparisons in integration tests to keep fixtures independent from bounded human-readable messages.
- Kept every fixture synthetic while preserving traceability to `card_issues_normalized.md` through `source_document`, `source_lines`, and coverage group metadata.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added missing validator coverage required by VAL-02 fixtures**
- **Found during:** Task 2 (Run normalized fixtures through validators per VAL-02)
- **Issue:** The shared facade did not yet emit normalized issues for sentence-audio layout defects or the known `дости́чь` wrong-sense Definition example, and existing grammar-only validation missed `short plural past indicative perfective of ...` metadata.
- **Fix:** Extended the v1.3 template facade with `sentence_audio_layout`, and tightened existing Definition validation to reject known wrong-sense and perfective metadata examples.
- **Files modified:** `src/multilang/services/v13_validation.py`, `src/multilang/services/text_field_remediation.py`
- **Verification:** `python -m pytest tests/integration/test_v13_normalized_issue_fixtures.py tests/services/test_v13_validation.py -q`
- **Committed in:** `16a8489`

---

**Total deviations:** 1 auto-fixed (1 missing critical functionality)
**Impact on plan:** The auto-fix was necessary for VAL-02 correctness and stayed within the existing validator facade/remediation boundaries.

## TDD Gate Compliance

- Task 2 RED commit `8225cf7` added the executable fixture suite and failed before implementation on missing normalized validation behavior.
- Task 2 GREEN commit `16a8489` implemented the minimal validator changes and made the planned suite pass.

## Issues Encountered

- The RED fixture suite first failed on a grammar-only Definition example (`definition_banned_pattern_bad_pogibli`), revealing an existing validation gap that was fixed in the GREEN commit alongside the additional missing fixture branches.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - stub scan found only intentional test/default empty values such as blank `Image` and empty expected issue lists for corrected pass cases.

## Next Phase Readiness

- Ready for 21-03 to assemble milestone evidence using the VAL-01 facade and VAL-02 executable fixtures.
- No blockers for continuing Phase 21.

## Self-Check: PASSED

- Verified created files exist: `tests/fixtures/v13/card_issues_normalized_cases.json`, `tests/integration/test_v13_normalized_issue_fixtures.py`, and this SUMMARY.
- Verified task commits exist: `791bb4d`, `8225cf7`, `16a8489`.
- Verified plan commands pass: `python -m json.tool tests/fixtures/v13/card_issues_normalized_cases.json` and `python -m pytest tests/integration/test_v13_normalized_issue_fixtures.py tests/services/test_v13_validation.py -q`.

---
*Phase: 21-validation-fixtures-and-milestone-evidence*
*Completed: 2026-05-15*
