---
phase: 21-validation-fixtures-and-milestone-evidence
plan: 03
subsystem: validation
tags: [pytest, milestone-evidence, v1.3, mode-isolation, privacy]

requires:
  - phase: 21-validation-fixtures-and-milestone-evidence
    provides: [VAL-01 validation facade, VAL-02 normalized issue fixtures]
  - phase: 17-deck-quality-audit-and-issue-reports
    provides: [APKG audit evidence]
  - phase: 18-text-field-remediation
    provides: [IPA, Definition, and Translation remediation evidence]
  - phase: 19-normal-card-export-and-responsive-template
    provides: [normal export/template contract evidence]
  - phase: 20-word-audio-integrity-gate
    provides: [word-audio integrity gate evidence]
provides:
  - Final scanner-readable v1.3 milestone evidence artifact
  - VAL-03 integration scanner for requirement coverage and privacy safety
  - Existing-mode regression evidence for frequency, word-list, highlight, and Russian phonetics contracts
affects: [milestone-closeout, v1.3-audit, regression-evidence]

tech-stack:
  added: []
  patterns: [scanner-readable-evidence, mode-contract-regression-tests, privacy-marker-scanning]

key-files:
  created:
    - .planning/phases/21-validation-fixtures-and-milestone-evidence/21-V13-MILESTONE-EVIDENCE.md
    - tests/integration/test_v13_existing_modes_regression_evidence.py
    - tests/integration/test_v13_final_milestone_evidence.py
  modified: []

key-decisions:
  - "Use focused scanner-readable command references for milestone closeout instead of embedding private audit report contents."
  - "Assert existing deck-mode safety through exported field tuples and note/template boundaries rather than duplicating validation logic."

patterns-established:
  - "Milestone evidence rows expose requirement id, phase, status, and runnable evidence references for automated scanners."
  - "VAL-03 regression tests prove normal frequency changes do not leak into manual, highlight, or Russian phonetics contracts."

requirements-completed: [VAL-03]

duration: 7min
completed: 2026-05-15
---

# Phase 21 Plan 03: Final v1.3 Milestone Evidence Summary

**Privacy-safe scanner evidence now ties all 15 v1.3 requirements to runnable suites and proves frequency, word-list, highlight, and Russian phonetics modes remain isolated.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-15T13:27:41Z
- **Completed:** 2026-05-15T13:35:05Z
- **Tasks:** 2 completed
- **Files modified:** 3

## Accomplishments

- Added `21-V13-MILESTONE-EVIDENCE.md` with 15/15 requirement coverage, command references, pass signals, mode isolation, privacy checks, and remaining caveats.
- Added scanner-readable final evidence tests that reject missing requirement rows, missing command references, and private marker leakage.
- Added existing-mode regression tests proving normal frequency, custom word-list/manual, Kindle highlight, and Russian phonetics contracts remain isolated after v1.3 normal-card changes.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Prove existing deck modes remain isolated per VAL-03** - `ca8dee0` (test)
2. **Task 1 GREEN: Complete existing deck mode isolation evidence** - `45b3390` (test)
3. **Task 2 RED: Write final v1.3 milestone evidence scanner** - `1b27d0c` (test)
4. **Task 2 GREEN: Add final v1.3 milestone evidence** - `34f6f73` (feat)

**Plan metadata:** committed after summary creation.

## Files Created/Modified

- `.planning/phases/21-validation-fixtures-and-milestone-evidence/21-V13-MILESTONE-EVIDENCE.md` - Final v1.3 requirement, command, pass-signal, mode-isolation, and privacy evidence artifact.
- `tests/integration/test_v13_existing_modes_regression_evidence.py` - VAL-03 regression tests for frequency, word-list/manual, highlight, and Russian phonetics export/template boundaries.
- `tests/integration/test_v13_final_milestone_evidence.py` - Scanner-readable tests for final evidence coverage, command references, pass signals, mode coverage, and private marker exclusions.

## Decisions Made

- Used focused command references and summaries for milestone evidence instead of copying local audit report contents, because deck-specific reports can contain private card text.
- Reused source-of-truth export constants and template/model builders in regression evidence rather than reimplementing validation logic.

## Deviations from Plan

### Process Deviations

**1. Task 1 RED assertion was refined before GREEN**
- **Found during:** Task 1 (Prove existing deck modes remain isolated per VAL-03)
- **Issue:** The initial RED test over-constrained Russian phonetics by requiring complete disjointness from normal/highlight field labels, but phonetics intentionally shares generic audio/example labels while keeping learner-facing normal/highlight fields isolated.
- **Fix:** Refined the assertion to block learner-facing field leakage (`word`, `Word`, `IPA`, `Definitions`, `Definition`, `Translation`, `Image`) while allowing the dedicated phonetics `word_audio`, `sentence_audio`, and `Example Sentence` fields.
- **Files modified:** `tests/integration/test_v13_existing_modes_regression_evidence.py`
- **Verification:** `python -m pytest tests/integration/test_v13_existing_modes_regression_evidence.py tests/integration/test_v13_normal_template_export_contract.py tests/integration/test_russian_phoneme_template_refresh_flow.py tests/integration/test_highlight_export_artifacts.py -q`
- **Committed in:** `45b3390`

---

**Total deviations:** 0 auto-fixed code deviations; 1 TDD process refinement documented.
**Impact on plan:** The final regression evidence matches the existing source-profile contracts and does not weaken VAL-03 coverage.

## TDD Gate Compliance

- Task 1 RED commit `ca8dee0` failed on an over-strict phonetics isolation assertion; GREEN commit `45b3390` refined the assertion and passed the full planned mode suite.
- Task 2 RED commit `1b27d0c` failed because the final evidence artifact did not exist; GREEN commit `34f6f73` added the artifact and passed the planned final evidence suite.

## Issues Encountered

- The first Task 1 full verification attempt timed out at 120 seconds while running the phoneme export flow; re-running the same suite with a 300-second timeout passed in 23.80 seconds.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - stub/privacy scan found no placeholder user-facing evidence. Private-marker strings appear only in the scanner test's forbidden-marker list by design.

## Threat Flags

None - no new network endpoints, auth paths, file-access trust boundaries, or schema changes were introduced. The committed evidence intentionally avoids private runtime audit contents.

## Next Phase Readiness

- VAL-03 is complete, and Phase 21 now has final scanner-readable milestone evidence.
- v1.3 can proceed to milestone completion/verification with focused suites as authoritative evidence while known broad full-suite collection drift remains tracked separately.

## Self-Check: PASSED

- Verified created files exist: `.planning/phases/21-validation-fixtures-and-milestone-evidence/21-V13-MILESTONE-EVIDENCE.md`, `tests/integration/test_v13_existing_modes_regression_evidence.py`, `tests/integration/test_v13_final_milestone_evidence.py`, and this SUMMARY.
- Verified task commits exist: `ca8dee0`, `45b3390`, `1b27d0c`, `34f6f73`.
- Verified plan command passes: `python -m pytest tests/integration/test_v13_final_milestone_evidence.py tests/integration/test_v13_existing_modes_regression_evidence.py tests/integration/test_v13_normalized_issue_fixtures.py -q`.

---
*Phase: 21-validation-fixtures-and-milestone-evidence*
*Completed: 2026-05-15*
