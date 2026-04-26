---
phase: 05-anki-safe-export-contract
plan: 03
subsystem: export
tags: [anki, apkg, genanki, media, guid]
requires:
  - phase: 05-02
    provides: frozen export rows and basename-only sound references
provides:
  - genanki-backed Multilang note model and deck package service
  - deterministic note GUID reuse across mutable content changes
  - packaged-media validation before apkg export
affects: [phase-05-plan-04, phase-05-plan-05, export, anki]
tech-stack:
  added: [genanki]
  patterns: [stable model and deck ids, custom genanki note subclass for deterministic guid, fail-fast media validation]
key-files:
  created:
    - src/multilang/services/export_anki_package.py
    - tests/services/test_export_anki_package.py
  modified:
    - pyproject.toml
    - uv.lock
key-decisions:
  - "Use one stable Multilang note type with hardcoded model and deck ids so Anki package structure cannot drift between reruns."
  - "Validate every referenced media file before writing the package instead of producing a broken `.apkg`."
patterns-established:
  - "Anki package notes derive GUIDs from the frozen export contract, not from mutable rendered content."
requirements-completed: []
duration: 6min
completed: 2026-04-26
---

# Phase 5 Plan 03: Generate real `.apkg` packages with stable note identity Summary

**The export layer now builds real `genanki` packages with a stable Multilang note model, deterministic GUIDs, and validated bundled media**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-26T20:10:36Z
- **Completed:** 2026-04-26T20:16:31Z
- **Tasks:** 1
- **Files modified:** 4

## Accomplishments
- Added the `genanki` runtime dependency and locked it in the project.
- Added a stable Multilang note model and custom note class that reuse deterministic GUIDs.
- Added fail-fast media validation before `.apkg` artifacts are written.

## Task Commits

1. **Task 1: Add the `genanki` dependency and stable note-type package service** - `efca192` (test), `d3d966b` (feat)

**Plan metadata:** pending

## Files Created/Modified
- `pyproject.toml` - adds the `genanki` runtime dependency
- `uv.lock` - locks `genanki` and its transitive dependencies
- `src/multilang/services/export_anki_package.py` - builds the stable model, deterministic notes, and `.apkg` packages
- `tests/services/test_export_anki_package.py` - covers template behavior, GUID reuse, bundled media, and missing-media failure

## Decisions Made
- Chose one export-specific note model with explicit field names rather than generating deck structure dynamically.
- Kept media validation inside the package writer so later CLI/runtime code can fail with one clear export error source.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- None

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness
- Plan 04 can now route shipped CLI exports to `.apkg`, CSV, and TSV writers from one runtime surface.
- Plan 05 can verify real Anki template behavior against the new stable note type once a sample artifact is generated.

## Self-Check: PASSED
- Found `.planning/phases/05-anki-safe-export-contract/05-03-SUMMARY.md`
- Verified task commits `efca192` and `d3d966b`

---
*Phase: 05-anki-safe-export-contract*
*Completed: 2026-04-26*
