---
phase: 09-source-profiles-privacy-regression-boundary
plan: 02
subsystem: export
tags: [anki-export, source-profiles, highlight-isolation]
requires:
  - phase: 09-source-profiles-privacy-regression-boundary
    provides: SourceProfile and SourceType contracts
provides:
  - source-aware export field resolution
  - dedicated highlight note model identity
  - mixed-source export rejection
affects: [phase-13-highlight-template, phase-15-highlight-export]
tech-stack:
  added: []
  patterns: [exact source-type model selection, mixed-source fail-closed guard]
key-files:
  created: []
  modified: [src/multilang/domain/exporting.py, src/multilang/services/export_anki_package.py, src/multilang/runtime.py, tests/domain/test_exporting.py, tests/services/test_export_anki_package.py]
key-decisions:
  - "Highlight exports use a dedicated no-Translation field tuple without changing ExportCardRow storage shape."
  - "APKG and tabular export reject mixed source rows before selecting a note model."
patterns-established:
  - "Export field lists are derived through source profiles and exact source sets."
requirements-completed: [MODE-02, SEC-02]
duration: 15min
completed: 2026-05-04
---

# Phase 09 Plan 02: Export Source Isolation Summary

**Source-profile-aware export fields and Anki model selection with highlight Translation omission**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-04T11:54:52Z
- **Completed:** 2026-05-04T12:09:23Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `HIGHLIGHT_EXPORT_CARD_FIELD_NAMES` with `Word`/`Definition` aliases and no `Translation`.
- Added `HIGHLIGHT_MODEL_ID` and `Multilang::Highlight Card` note type selection.
- Replaced non-word-list fallback behavior with exact source-type resolution and mixed-source guards.

## Task Commits

1. **TDD RED: export isolation tests** - `26b2ceb` (test)
2. **Tasks 1-2 GREEN: source-aware export implementation** - `0ad4aa6` (feat)

## Files Created/Modified

- `src/multilang/domain/exporting.py` - Source-aware field tuple resolution and highlight aliases.
- `src/multilang/services/export_anki_package.py` - Dedicated model IDs/names and mixed-source rejection.
- `src/multilang/runtime.py` - Tabular note type resolution via source profiles.
- `tests/domain/test_exporting.py` - Field tuple and mapping tests.
- `tests/services/test_export_anki_package.py` - Model and mixed-source APKG tests.

## Deviations from Plan

None - plan executed as specified.

## Verification

- `uv run pytest tests/domain/test_exporting.py tests/services/test_export_anki_package.py -q` — 19 passed.

## Known Stubs

None.

## Self-Check: PASSED

Files and commits verified during execution.
