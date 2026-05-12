---
phase: 17-deck-quality-audit-and-issue-reports
plan: 01
subsystem: deck-audit
tags: [apkg, sqlite, anki, audit, definitions]
requires: []
provides:
  - Typed AuditCard/AuditIssue contracts
  - Read-only APKG note extraction
  - Definition issue detection for normalized grammar/inflection/wrong-sense defects
affects: [phase-17, audit-deck, deck-quality]
tech-stack:
  added: []
  patterns: [stdlib zipfile/sqlite APKG inspection, bounded issue evidence]
key-files:
  created:
    - src/multilang/domain/deck_audit.py
    - src/multilang/services/deck_audit_reader.py
    - tests/domain/test_deck_audit.py
    - tests/services/test_deck_audit_reader.py
  modified: []
key-decisions:
  - "Audit evidence is bounded and APKG source metadata uses basename-only paths."
  - "APKG reads copy only collection.anki2 into a TemporaryDirectory and verify pre/post input SHA-256."
patterns-established:
  - "Audit readers return stable domain rows before any report or CLI layer consumes them."
requirements-completed: [AUDIT-01, AUDIT-02, AUDIT-03]
duration: 25min
completed: 2026-05-12
---

# Phase 17 Plan 01: Non-mutating APKG reader + Definition issue detector Summary

**Read-only APKG card extraction with stable audit rows and normalized Definition defect detection**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-05-12T19:28:29Z
- **Completed:** 2026-05-12T19:55:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `AuditCard`, `AuditIssue`, `AuditIssueType`, and `detect_card_issues` for Definition-only normalized defects.
- Added read-only APKG extraction via `zipfile`, `sqlite3`, temporary collection copies, and SHA-256 non-mutation checks.
- Added regression coverage for synthetic APKG extraction, malformed APKG errors, and known `дости́чь` wrong-sense detection.

## Task Commits

1. **Task 1 RED:** `8495d2d` test(17-01): add failing Definition audit tests
2. **Task 1 GREEN:** `e33eda7` feat(17-01): implement Definition issue detection
3. **Task 2 RED:** `a179300` test(17-01): add failing APKG reader tests
4. **Task 2 GREEN:** `b5736f7` feat(17-01): implement read-only APKG audit reader

## Files Created/Modified

- `src/multilang/domain/deck_audit.py` - Typed audit rows/issues and Definition issue detection.
- `src/multilang/services/deck_audit_reader.py` - Non-mutating APKG reader for Anki note fields.
- `tests/domain/test_deck_audit.py` - Definition detector regression tests.
- `tests/services/test_deck_audit_reader.py` - APKG reader and non-mutation tests.

## Decisions Made

- Use basename-only `source_path_name` and bounded issue evidence to reduce private path/content exposure.
- Reject unsafe APKG archive members before reading `collection.anki2`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Used local Python pytest because `uv` is unavailable in the shell**
- **Found during:** Task 1 verification
- **Issue:** `uv run pytest ...` failed with `uv: command not found`.
- **Fix:** Ran equivalent `python -m pytest ...` commands for verification.
- **Files modified:** None
- **Verification:** Focused tests passed with `python -m pytest`.
- **Committed in:** N/A

**2. [Rule 1 - Bug] Closed SQLite connections explicitly on Windows**
- **Found during:** Task 2 verification
- **Issue:** TemporaryDirectory cleanup failed because sqlite connections remained open on Windows.
- **Fix:** Explicitly closed the connection in `deck_audit_reader.py`.
- **Files modified:** `src/multilang/services/deck_audit_reader.py`
- **Verification:** `python -m pytest tests/services/test_deck_audit_reader.py tests/domain/test_deck_audit.py -q` passed.
- **Committed in:** `b5736f7`

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)

## Issues Encountered

- No known APKG was available yet; this is handled by Plan 17-03 checkpoint.

## Known Stubs

None.

## User Setup Required

None for this plan.

## Next Phase Readiness

- Plan 17-02 can serialize the stable audit rows and issues into deterministic reports.

## Self-Check: PASSED

- Confirmed created files exist.
- Confirmed task commits exist: `8495d2d`, `e33eda7`, `a179300`, `b5736f7`.

---
*Phase: 17-deck-quality-audit-and-issue-reports*
*Completed: 2026-05-12*
