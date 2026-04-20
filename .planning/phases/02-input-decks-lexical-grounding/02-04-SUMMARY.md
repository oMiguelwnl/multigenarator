---
phase: 02-input-decks-lexical-grounding
plan: 04
subsystem: runtime
tags: [cli, runtime, lexical-ingestion, frequency-decks, pytest]
requires:
  - phase: 01-job-orchestration-recovery
    provides: single-command generation flow with persisted job and item lifecycle state
provides:
  - Runtime lexical-ingestion coordinator for frequency decks and custom word lists
  - Shipped `multilang generate` wiring with grounded, pending, rejected, and backfill counters
  - Integration coverage for persisted three-level frequency decks and pending-preserving word-list reruns
affects: [phase-03-sentence-quality, phase-04-audio-synthesis, phase-05-anki-export]
tech-stack:
  added: []
  patterns: [repository-backed lexical ingestion coordinator, full-deck frequency default, pending-preserving rerun semantics]
key-files:
  created:
    - src/multilang/services/ingest_lexical_items.py
    - tests/integration/test_lexical_job_flow.py
  modified:
    - src/multilang/runtime.py
    - src/multilang/cli.py
    - src/multilang/services/input_fingerprint.py
    - src/multilang/services/kaikki_lookup.py
    - src/multilang/services/lexical_grounding.py
    - tests/cli/test_generate_command.py
key-decisions:
  - "Treat frequency runs with no explicit level as one stable full-deck request so reruns and resume use a deterministic `levels:1-3` fingerprint."
  - "Count only grounded custom-list items as completed work while still persisting pending lexical rows so resume and rerun flows never drop requested words."
patterns-established:
  - "Coordinator-first runtime wiring: the shipped CLI resolves one ingestion service that owns job orchestration, grounding, persistence, and lexical diagnostics."
  - "Frequency level persistence uses stable synthetic item keys (`level-{n}-rank-{position}`) so three-level deck reruns update rows instead of duplicating them."
requirements-completed: [DECK-02, DECK-03, LEX-01, LEX-02, LEX-03]
duration: 1h 5m
completed: 2026-04-20
---

# Phase 2 Plan 4: CLI/runtime lexical ingestion wiring Summary

**`multilang generate` now drives repository-backed lexical ingestion for full three-level frequency decks and custom word lists, with persisted grounding diagnostics on the shipped runtime path.**

## Performance

- **Duration:** 1h 5m
- **Started:** 2026-04-20T12:05:57Z
- **Completed:** 2026-04-20T13:11:25Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added `IngestLexicalItemsService` so the shipped runtime can build grounded frequency decks with per-level backfill and preserve pending custom-list candidates.
- Rewired `multilang generate` to print lexical counters alongside the existing lifecycle summary without adding a second operator entry point.
- Added shipped-path CLI and integration coverage that verifies 3000 grounded frequency candidates across three levels plus pending-preserving custom-list rerun and resume behavior.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create the lexical ingestion coordinator for the shipped runtime path** - `75738e8` (feat)
2. **Task 2: Wire `multilang generate` to the lexical coordinator and surface diagnostics** - `099b063` (feat)

**Plan metadata:** _pending at summary creation time_

## Files Created/Modified
- `src/multilang/services/ingest_lexical_items.py` - coordinates frequency and word-list ingestion, persistence, and lexical counters
- `src/multilang/runtime.py` - builds the shipped runtime around the lexical ingestion coordinator
- `src/multilang/cli.py` - routes `multilang generate` through lexical ingestion and prints lexical diagnostics plus lifecycle summary fields
- `src/multilang/services/input_fingerprint.py` - gives full-deck frequency runs a stable run fingerprint for rerun and resume safety
- `src/multilang/services/kaikki_lookup.py` - caches loaded per-language lexical indexes for repeated runtime lookups
- `src/multilang/services/lexical_grounding.py` - exports the runtime grounding-service builder used by the coordinator
- `tests/cli/test_generate_command.py` - locks the CLI diagnostics for full-deck frequency and pending custom-list runs
- `tests/integration/test_lexical_job_flow.py` - verifies shipped-path persistence for three grounded levels and pending-preserving rerun/resume flows

## Decisions Made
- Defaulted frequency runs with no `--level` to the full three-level deck while retaining `--level` for targeted reruns and tests.
- Reused the Phase 1 job repository and lexical-candidate upsert path so `(job_id, item_key)` remains the duplicate-safety boundary for reruns and resume.

## Deviations from Plan

None - plan executed as written.

## Issues Encountered
- The executor produced the implementation commits but returned without creating `02-04-SUMMARY.md`, so the orchestrator resumed from disk state, re-ran the plan verification commands, and completed the summary step manually.
- `gsd-sdk` is unavailable in this environment, so workflow tracking and verification steps were reconstructed directly from `.planning` artifacts and the git/worktree state.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 2 now delivers grounded lexical candidates from either built-in frequency decks or custom word lists through the shipped CLI path.
- Phase 3 can build on persisted lemma, IPA, definition, pending, and backfill semantics instead of re-solving lexical ingestion.

## Self-Check: PASSED

- Found `.planning/phases/02-input-decks-lexical-grounding/02-04-SUMMARY.md` on disk.
- Verified commits `75738e8` and `099b063` exist in `git log --oneline --all`.
- Verified `uv run pytest tests/cli/test_generate_command.py tests/integration/test_lexical_job_flow.py -q` passes.
- Verified `uv run pytest tests -q` passes.
