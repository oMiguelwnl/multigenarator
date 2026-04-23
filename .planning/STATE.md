---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: in_progress
stopped_at: Quick task 260421-001 verified; Phase 3 execution remains the primary roadmap work
last_updated: "2026-04-23T17:45:52Z"
last_activity: 2026-04-23 -- Completed quick task 260421-001: implement Tatoeba as a filtered secondary sentence source with advanced reranking and validation, never as the raw default primary source.
progress:
  total_phases: 5
  completed_phases: 2
  total_plans: 16
  completed_plans: 11
  percent: 69
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-18)

**Core value:** Generate reliable, high-quality Anki cards for frequent vocabulary in the chosen language so the learner can study real words with accurate definitions, examples, translations, and audio.
**Current focus:** Phase 03 execution, with Plan 03-01 ready to start

## Current Position

Phase: 03 (sentence-quality-review-loop) — READY TO START
Plan: 0 of 5 executed
Status: Phase 2 is verified complete; Phase 3 planning is complete and execution can begin
Last activity: 2026-04-23 -- Completed quick task 260421-001: implement Tatoeba as a filtered secondary sentence source with advanced reranking and validation, never as the raw default primary source.

Progress: [███████---] 69%

## Performance Metrics

**Velocity:**

- Total plans completed: 11
- Average duration: 15 min
- Total execution time: 2.7 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-job-orchestration-recovery | 6 | 34 min | 6 min |
| 02-input-decks-lexical-grounding | 5 | 2h 7m | 25 min |

**Recent Trend:**

- Last 5 plans: 02-01 (15 min), 02-02 (4 min), 02-03 (4 min), 02-04 (1h 5m), 02-05 (39 min)
- Trend: Phase 2 is now closed; the next active work is Phase 3 execution

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Phase 1]: Keep v1 centered on supported-language job orchestration, resumability, and duplicate-safe reruns.
- [Phase 2]: Treat frequency decks and custom word lists as one lexical-ingestion capability.
- [Phase 3]: Put review/regeneration inside the text-quality phase because trust depends on fixing weak cards before export.
- [Phase 3]: Treat Tatoeba as a secondary sentence source only when advanced filtering/reranking and validation are applied; do not use it as the raw default source.
- [Phase 5]: Freeze the card contract and Anki export semantics only after upstream text and audio stabilize.
- [Plan 01-01]: Use a uv-managed src-layout Python package with typed settings and explicit resume diagnostics as the foundation for Phase 1.
- [Plan 01-02]: Store run-level and item-level state separately so resume validation can compare stage pointers against item rows.
- [Plan 01-02]: Treat repeated successful item writes for the same run_key/item_key as duplicate reuse and count them in skipped_duplicates.
- [Plan 01-03]: Keep the operator surface to one `multilang generate` command with source-specific validation and explicit overwrite confirmation.
- [Plan 01-03]: Build run keys from normalized requested items so resume and rerun decisions remain deterministic across repeated requests.
- [Plan 01-04]: Track retried and overwritten items in execution metadata so lifecycle summaries can report successful retries and explicit overwrites accurately.
- [Plan 01-04]: Keep the default terminal UX counter-based and stage-scoped, leaving per-item details for summaries and tests.
- [Plan 01-05]: Build the shipped CLI runtime service lazily so environment overrides and persisted-state wiring both apply on the default app path.
- [Plan 01-05]: Move JobExecutionReport into a shared services module so lifecycle summary wiring stays import-safe.
- [Plan 01-06]: Print explicit lifecycle counters on the shipped CLI path so operators can audit completed, failed, skipped, resumed, and overwritten work.
- [Plan 01-06]: Abort resume attempts when persisted state validation reports inconsistencies instead of continuing unsafely.
- [Plan 02-01]: Keep lexical candidates as one shared typed contract with submitted, display, and lemma identities separated for downstream grounding work.
- [Plan 02-01]: Persist lexical candidates with a unique `(job_id, item_key)` key so reruns update one candidate row instead of duplicating it.
- [Plan 02-01]: Resolve Alembic database URLs from runtime settings so schema verification honors `MULTILANG_DATABASE_URL` in local and CI checks.
- [Plan 02-02]: Use `wordfreq` plus explicit teachability filters as the deterministic source for built-in frequency decks.
- [Plan 02-02]: Keep level windows explicit at ranks 1-1000, 1001-2000, and 2001-3000, with bounded backfill beyond the window when candidates are rejected.
- [Plan 02-03]: Preserve submitted custom-list text while deduping on whitespace-normalized casefolded keys so diagnostics stay deterministic.
- [Plan 02-03]: Distinguish pending custom lookup misses from `backfill_required` frequency misses so the system never silently swaps away requested words.
- [Plan 02-05]: Keep lexical bootstrap on the shipped `multilang generate` command via `--lexicon-source-file` instead of adding a second setup command.
- [Plan 02-05]: Abort before ingestion when the requested language cache is missing and no explicit Kaikki archive was provided.

### Pending Todos

- Execute Phase 3 Plan 03-01 on top of the now-verified lexical grounding baseline.

### Blockers/Concerns

- Voice inventory for all 7 languages still needs validation, especially Dutch fallbacks.
- Phase 3 now has a locked short learner-friendly direction, but language-specific sentence bands and benchmark fixtures still need concrete execution-time rules.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260421-001 | implement Tatoeba as a filtered secondary sentence source with advanced reranking and validation, never as the raw default primary source | 2026-04-23 | b833e22 | Verified | [260421-001-tatoeba-filtered-secondary-source](./quick/260421-001-tatoeba-filtered-secondary-source/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-04-21T17:32:43Z
Stopped at: Phase 2 re-verification passed; start Phase 3 at Plan 03-01
Resume file: None
