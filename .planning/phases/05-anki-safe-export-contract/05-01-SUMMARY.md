---
phase: 05-anki-safe-export-contract
plan: 01
subsystem: database
tags: [anki, export, pydantic, sqlalchemy, alembic]
requires:
  - phase: 04-audio-synthesis
    provides: persisted word and sentence audio assets for export snapshots
provides:
  - frozen export-card contract with fixed field order and stable note GUIDs
  - job-scoped card snapshot and artifact persistence tables
  - verified Phase 5 migration for export contract storage
affects: [phase-05-plan-02, phase-05-plan-03, export, anki]
tech-stack:
  added: []
  patterns: [typed export boundary contracts, job-scoped export repositories, verified disposable-schema migrations]
key-files:
  created:
    - src/multilang/repositories/export_repository.py
    - tests/domain/test_exporting.py
    - tests/repositories/test_export_repository.py
    - alembic/versions/20260426_05_export_contract_tables.py
  modified:
    - src/multilang/domain/exporting.py
    - src/multilang/db/models.py
key-decisions:
  - "Freeze export field order in one Pydantic model using aliases so every serializer emits the same ten columns."
  - "Persist card snapshots by (job_id, item_key) and deck artifacts by (job_id, export_format) to keep reruns deterministic."
  - "Store deterministic note GUIDs in the export snapshot layer before any CSV or Anki packaging code lands."
patterns-established:
  - "Export contracts follow the same typed-domain pattern as lexical, text, and audio phases."
  - "New persistence phases ship ORM models, repository tests, and an Alembic migration together."
requirements-completed: []
duration: 7min
completed: 2026-04-26
---

# Phase 5 Plan 01: Freeze the export contract, persistence, and Phase 5 schema migration Summary

**Fixed-schema export rows with stable note GUIDs, job-scoped snapshot persistence, and a verified export migration for later CSV/TSV and `.apkg` work**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-26T19:53:50Z
- **Completed:** 2026-04-26T20:00:27Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Added one canonical export-card contract with the exact ten required fields and deterministic GUID generation.
- Added `card_exports` and `deck_exports` persistence with deterministic upsert and read ordering rules.
- Verified the new Phase 5 schema against a disposable SQLite database before downstream export work.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define the frozen export-card contract** - `228c7d7` (test), `fecea68` (feat)
2. **Task 2: Persist frozen card snapshots and artifact manifests** - `7cde91b` (test), `e61fab2` (feat)
3. **Task 3: Apply and verify the Phase 5 export schema migration** - `9731346` (feat)

**Plan metadata:** pending

_Note: TDD tasks used RED → GREEN commits._

## Files Created/Modified
- `src/multilang/domain/exporting.py` - frozen export contract, stable identity, note GUID, and artifact metadata models
- `tests/domain/test_exporting.py` - field-order, GUID-stability, and blank-image contract coverage
- `src/multilang/db/models.py` - `CardExportModel` and `DeckExportModel` ORM tables plus job relationships
- `src/multilang/repositories/export_repository.py` - job-scoped snapshot and artifact upsert/list helpers
- `tests/repositories/test_export_repository.py` - deterministic upsert and retrieval-order coverage for export persistence
- `alembic/versions/20260426_05_export_contract_tables.py` - Phase 5 migration for export snapshot and artifact tables

## Decisions Made
- Used alias-backed Pydantic fields to hard-freeze the external export column names while keeping Python-friendly attribute names internally.
- Stored export snapshots per `(job_id, item_key)` and artifact manifests per `(job_id, export_format)` so reruns update in place instead of duplicating records.
- Persisted `lemma_key` alongside the fixed card fields so stable export identity can round-trip correctly through the repository layer.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Persisted `lemma_key` with export snapshots**
- **Found during:** Task 2 (Persist frozen card snapshots and artifact manifests)
- **Issue:** The initial ORM draft stored the ten visible card fields but not the stable lemma identity needed to round-trip deterministic note identity safely.
- **Fix:** Added a `lemma_key` column and repository mapping so snapshot reads preserve the stable identity inputs used for note GUID generation.
- **Files modified:** `src/multilang/db/models.py`, `src/multilang/repositories/export_repository.py`
- **Verification:** `uv run pytest tests/domain/test_exporting.py tests/repositories/test_export_repository.py -q`
- **Committed in:** `e61fab2`

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** The deviation was required for deterministic identity correctness and did not expand scope beyond the export contract foundation.

## Issues Encountered
- `gsd-sdk` was not available in the shell environment, so planning-state updates and the final docs commit were applied manually instead of through SDK helpers.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Plan 02 can now assemble export rows from persisted lexical, text, and audio data against one fixed contract.
- Plan 03 can package `.apkg` artifacts against stable note GUIDs and stored export snapshots.
- No functional blockers remain for the next export phase.

## TDD Gate Compliance
- RED gate commit present: `228c7d7`
- GREEN gate commit present: `fecea68`
- Additional RED/GREEN pair for repository persistence: `7cde91b` → `e61fab2`

## Self-Check: PASSED
- Found `.planning/phases/05-anki-safe-export-contract/05-01-SUMMARY.md`
- Verified task commits `228c7d7`, `fecea68`, `7cde91b`, `e61fab2`, and `9731346`

---
*Phase: 05-anki-safe-export-contract*
*Completed: 2026-04-26*
