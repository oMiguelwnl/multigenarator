---
phase: 03-sentence-quality-review-loop
plan: 01
subsystem: database
tags: [phase-3, text-quality, pydantic, sqlalchemy, alembic, sqlite]

# Dependency graph
requires:
  - phase: 02-input-decks-lexical-grounding
    provides: stable lexical candidate identities and persisted job items
provides:
  - typed text-quality contracts for persisted sentence and translation rows
  - repository-backed text-quality storage keyed by stable job item identity
  - verified Phase 3 schema migration for review and regeneration work
affects: [phase-3-services, review-flow, regeneration, migration-verification]

# Tech tracking
tech-stack:
  added: []
  patterns: [pydantic text-quality contracts, repository upsert by job_id and item_key, sqlite migration verification]

key-files:
  created:
    - src/multilang/domain/text_quality.py
    - src/multilang/repositories/text_repository.py
    - alembic/versions/20260421_03_text_quality_tables.py
    - tests/domain/test_text_quality.py
    - tests/repositories/test_text_repository.py
  modified:
    - src/multilang/db/models.py

key-decisions:
  - "Persist sentence text, translation text, confidence, and provenance as one typed TextQualityRecord instead of overloading lexical candidate payloads."
  - "Use one unique text_quality_records row per (job_id, item_key) so review and regeneration can target a stable record identity."
  - "Keep generation candidate lookup on lexical_candidates joined against text_quality_records so downstream services can fetch pending or flagged items without mutating lexical payloads."

patterns-established:
  - "Phase 3 persists meaning-bearing text state in a dedicated repository boundary with enum-backed lifecycle fields."
  - "Schema work is verified against a disposable SQLite database before downstream runtime wiring continues."

requirements-completed: [TEXT-01, TEXT-03, TEXT-04, TEXT-05]

# Metrics
duration: 6 min
completed: 2026-04-21
---

# Phase 3 Plan 01: Text-quality contracts and persistence summary

**Typed sentence-quality records with stable per-item persistence, review flags, and a verified SQLite migration for Phase 3.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-21T17:42:00Z
- **Completed:** 2026-04-21T17:48:54Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Added a Phase 3 text-quality domain contract with separate sentence, translation, confidence, validation, and provenance fields.
- Persisted one text-quality row per `(job_id, item_key)` with repository queries for accepted, flagged, and generation-candidate records.
- Verified the new schema against a disposable SQLite database and confirmed prior Phase 1/2 tables remained present.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define text-quality contracts and machine-readable flags** - `d5cd398`, `2037753` (test, feat)
2. **Task 2: Add text-quality ORM storage and repository queries** - `def5c01`, `8dfc1e0` (test, feat)
3. **Task 3: [BLOCKING] Apply and verify the Phase 3 schema migration** - `746d3c1` (chore)

**Plan metadata:** pending summary commit at execution time

## Files Created/Modified
- `src/multilang/domain/text_quality.py` - Phase 3 typed contracts, enums, provenance, and repair/review helpers
- `src/multilang/db/models.py` - ORM relationships plus `TextQualityRecordModel`
- `src/multilang/repositories/text_repository.py` - Text-quality upsert, retrieval, flagged-review, and generation-candidate queries
- `alembic/versions/20260421_03_text_quality_tables.py` - Migration creating `text_quality_records`
- `tests/domain/test_text_quality.py` - Domain contract tests for provenance, flags, and lifecycle helpers
- `tests/repositories/test_text_repository.py` - Repository tests for upserts, review queries, and structured round-trips

## Decisions Made
- Persisted text-quality state separately from lexical grounding so downstream review/regeneration work targets a stable meaning-bearing record boundary.
- Stored validation flags as structured JSON objects with enum-backed codes instead of a free-form string.
- Queried generation candidates by joining lexical candidates to text rows so pending and review-required items remain discoverable before service wiring.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for `03-02-PLAN.md` to add sentence-generation and translation service boundaries on top of the new contracts and repository.
- Migration verification passed against disposable SQLite, so downstream Phase 3 work can rely on live schema state.

## Self-Check: PASSED

- Found `.planning/phases/03-sentence-quality-review-loop/03-01-SUMMARY.md`
- Verified task commits `d5cd398`, `2037753`, `def5c01`, `8dfc1e0`, and `746d3c1`

---
*Phase: 03-sentence-quality-review-loop*
*Completed: 2026-04-21*
