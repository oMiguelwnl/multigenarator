---
phase: 02-input-decks-lexical-grounding
plan: 01
subsystem: database
tags: [pydantic, sqlalchemy, alembic, lexical-grounding, repository]
requires:
  - phase: 01-job-orchestration-recovery
    provides: resumable generation jobs and persisted generation item state
provides:
  - Typed lexical candidate contracts for Phase 2 ingestion
  - ORM-backed lexical candidate persistence keyed by job and item identity
  - Verified lexical grounding schema migration for local and CI checks
affects: [frequency-ingestion, word-list-grounding, cli-runtime, phase-2]
tech-stack:
  added: []
  patterns: [pydantic domain contracts, repository upsert boundary, alembic-backed schema verification]
key-files:
  created: [src/multilang/domain/lexicon.py, src/multilang/repositories/lexical_repository.py, alembic/versions/20260419_02_lexical_grounding_tables.py, tests/domain/test_lexicon.py, tests/repositories/test_lexical_repository.py, .planning/phases/02-input-decks-lexical-grounding/02-01-SUMMARY.md]
  modified: [src/multilang/db/models.py, alembic/env.py]
key-decisions:
  - "Keep lexical candidates as one shared typed contract with explicit submitted, display, and lemma identities."
  - "Persist lexical candidates with a unique (job_id, item_key) key so reruns update rows instead of duplicating them."
  - "Resolve Alembic database URLs from runtime settings so schema verification honors MULTILANG_DATABASE_URL."
patterns-established:
  - "Lexical ingestion contracts use Pydantic models plus enums before service wiring."
  - "Repositories return domain models and own ORM upsert/query translation."
requirements-completed: [DECK-03, LEX-01, LEX-02, LEX-03]
duration: 15 min
completed: 2026-04-19
---

# Phase 2 Plan 1: Lexical contracts, persistence, and schema migration Summary

**Typed lexical candidates with explicit language-policy fields, repository-backed persistence, and a verified Phase 2 schema migration.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-04-19T15:55:00Z
- **Completed:** 2026-04-19T16:09:32Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- Added the Phase 2 lexical contract source of truth, including grounding status, provenance, and translation-target policy.
- Persisted lexical candidates with an ORM model, unique upsert behavior, and repository queries for downstream services.
- Verified the live schema against a disposable SQLite database so later plans can depend on the migration, not just metadata.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define lexical candidate contracts and language policy** - `4deb7ae` (test), `77162d8` (feat)
2. **Task 2: Add lexical candidate persistence and repository queries** - `9179583` (test), `aa7aa47` (feat)
3. **Task 3: [BLOCKING] Apply and verify the lexical schema migration** - `5395499` (fix)

**Plan metadata:** `docs(02-01)` metadata commit recorded in git history

## Files Created/Modified
- `src/multilang/domain/lexicon.py` - Typed lexical candidate, provenance, and deck language policy contracts.
- `tests/domain/test_lexicon.py` - TDD contract coverage for identity separation, language policy, and pending-state behavior.
- `src/multilang/db/models.py` - Adds the persisted lexical candidate ORM model and relation to generation jobs.
- `src/multilang/repositories/lexical_repository.py` - Repository upsert and query helpers for lexical candidates.
- `tests/repositories/test_lexical_repository.py` - TDD coverage for unique upserts, round trips, and pending counts.
- `alembic/versions/20260419_02_lexical_grounding_tables.py` - Migration creating the `lexical_candidates` table plus indexes.
- `alembic/env.py` - Uses runtime settings for Alembic database resolution during schema verification.

## Decisions Made
- Keep submitted text, study-facing display text, and normalized lemma identity as separate fields so later services cannot collapse learner-facing values into raw source strings.
- Encode `definition_language` and `translation_target_language` directly in the candidate contract so downstream phases inherit one deck-wide language policy.
- Treat migration verification as a live-schema concern and load Alembic URLs from settings so disposable DB checks behave the same locally and in CI.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Wired Alembic to runtime database settings**
- **Found during:** Task 3 (Apply and verify the lexical schema migration)
- **Issue:** `alembic upgrade head` ignored `MULTILANG_DATABASE_URL` because `alembic/env.py` only read `alembic.ini`, which would have made the required disposable-schema verification unreliable.
- **Fix:** Loaded `Settings().database_url` into Alembic configuration and imported ORM models so metadata-backed schema checks include the lexical table.
- **Files modified:** `alembic/env.py`
- **Verification:** `MULTILANG_DATABASE_URL=sqlite+pysqlite:////tmp/multilang-phase2-schema.db uv run alembic upgrade head && MULTILANG_DATABASE_URL=sqlite+pysqlite:////tmp/multilang-phase2-schema.db uv run python -c "from sqlalchemy import create_engine, inspect; from multilang.settings import Settings; engine=create_engine(Settings().database_url); print(sorted(inspect(engine).get_table_names()))"`
- **Committed in:** `5395499`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The auto-fix was required for deterministic schema verification and did not expand scope beyond the plan's migration goal.

## Issues Encountered
- The repo tool wrappers for `grep`/`glob` were unavailable in this environment, so acceptance checks were verified with Python and the planned test commands instead.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 2 now has a stable lexical candidate contract and persistence boundary for frequency curation and custom word-list grounding work.
- The live schema check passes against a disposable SQLite database, so later ingestion services can depend on the lexical table existing.

## Verification Results
- `uv run pytest tests/domain/test_lexicon.py tests/repositories/test_lexical_repository.py -q` ✅
- `MULTILANG_DATABASE_URL=sqlite+pysqlite:////tmp/multilang-phase2-schema.db uv run alembic upgrade head && MULTILANG_DATABASE_URL=sqlite+pysqlite:////tmp/multilang-phase2-schema.db uv run python -c "from sqlalchemy import create_engine, inspect; from multilang.settings import Settings; engine=create_engine(Settings().database_url); print(sorted(inspect(engine).get_table_names()))"` ✅ (`['alembic_version', 'generation_items', 'generation_jobs', 'lexical_candidates']`)

## Self-Check: PASSED
- Found summary file: `.planning/phases/02-input-decks-lexical-grounding/02-01-SUMMARY.md`
- Found task commits: `4deb7ae`, `77162d8`, `9179583`, `aa7aa47`, `5395499`

---
*Phase: 02-input-decks-lexical-grounding*
*Completed: 2026-04-19*
