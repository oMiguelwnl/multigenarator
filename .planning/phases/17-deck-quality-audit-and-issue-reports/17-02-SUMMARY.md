---
phase: 17-deck-quality-audit-and-issue-reports
plan: 02
subsystem: deck-audit
tags: [json, markdown, audit, reproducibility]
requires:
  - phase: 17-01
    provides: Typed audit rows and Definition issues
provides:
  - Deterministic deck-audit JSON report writer
  - Grouped Markdown deck-audit issue report writer
affects: [phase-17, audit-deck, deck-quality]
tech-stack:
  added: []
  patterns: [fixed report filenames, deterministic issue sorting]
key-files:
  created:
    - src/multilang/services/deck_audit_reports.py
    - tests/services/test_deck_audit_reports.py
  modified: []
key-decisions:
  - "Reports write only fixed filenames deck-audit.json and deck-audit.md inside the requested output directory."
  - "Issue ordering is card_identifier, field_name, issue_type, then note_id for reproducible reruns."
patterns-established:
  - "Audit reports consume bounded AuditIssue evidence without re-reading private APKG content."
requirements-completed: [AUDIT-01, AUDIT-02, AUDIT-03]
duration: 15min
completed: 2026-05-12
---

# Phase 17 Plan 02: Deterministic JSON/Markdown audit reports Summary

**Reproducible deck-audit JSON and grouped Markdown reports with stable issue ordering**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-12T19:55:00Z
- **Completed:** 2026-05-12T20:10:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `DeckAuditReportResult` and `write_deck_audit_reports`.
- JSON reports include source basename, input hash, card count, issue count, and sorted issue payloads.
- Markdown reports group issues by card and field, with severity, evidence, and recommended next action.

## Task Commits

1. **Task 1/2 RED:** `eb8519a` test(17-02): add failing audit report tests
2. **Task 1/2 GREEN:** `43f9ca2` feat(17-02): implement deterministic audit reports

## Files Created/Modified

- `src/multilang/services/deck_audit_reports.py` - Deterministic JSON/Markdown report writer.
- `tests/services/test_deck_audit_reports.py` - Stable ordering and grouped report tests.

## Decisions Made

- Keep report writer scoped to audit findings only; no repair workflow language or mutation behavior was introduced.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Used local Python pytest because `uv` is unavailable in the shell**
- **Found during:** Task verification
- **Issue:** `uv run pytest ...` is unavailable in this environment.
- **Fix:** Ran equivalent `python -m pytest ...` commands.
- **Files modified:** None
- **Verification:** `python -m pytest tests/services/test_deck_audit_reports.py tests/domain/test_deck_audit.py -q` passed.
- **Committed in:** N/A

**Total deviations:** 1 auto-fixed (1 blocking)

## Issues Encountered

None.

## Known Stubs

None.

## User Setup Required

None for this plan.

## Next Phase Readiness

- Plan 17-03 can wire the reader, detector, and report writer into `audit-deck`.

## Self-Check: PASSED

- Confirmed created files exist.
- Confirmed task commits exist: `eb8519a`, `43f9ca2`.

---
*Phase: 17-deck-quality-audit-and-issue-reports*
*Completed: 2026-05-12*
