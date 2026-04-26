---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: in_progress
stopped_at: Completed Phase 5 Plan 03 genanki package service; Plan 04 shipped export wiring is next
last_updated: "2026-04-26T20:16:31Z"
last_activity: 2026-04-26 -- Completed Phase 5 Plan 03 with stable genanki packaging and bundled-media validation.
progress:
  total_phases: 5
  completed_phases: 4
  total_plans: 26
  completed_plans: 24
  percent: 92
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-18)

**Core value:** Generate reliable, high-quality Anki cards for frequent vocabulary in the chosen language so the learner can study real words with accurate definitions, examples, translations, and audio.
**Current focus:** Phase 05 execution for the Anki-safe export contract, with `.apkg` packaging now complete

## Current Position

Phase: 05 (anki-safe-export-contract) — NEXT UP
Plan: 3 of 5 executed
Status: Phases 01, 02, 03, and 04 are verified complete; Phase 5 now has frozen export rows, tabular fallbacks, and `.apkg` packaging ready for shipped CLI wiring
Last activity: 2026-04-26 -- Completed Plan 05-03 and verified stable Anki package generation.

Progress: [████████--] 80%

## Performance Metrics

**Velocity:**

- Total plans completed: 24
- Average duration: 14 min
- Total execution time: 5h 1m

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-job-orchestration-recovery | 6 | 34 min | 6 min |
| 02-input-decks-lexical-grounding | 5 | 2h 7m | 25 min |
| 03-sentence-quality-review-loop | 5 | 1h 17m | 15 min |
| 04-audio-synthesis | 5 | 1h 3m | 13 min |

**Recent Trend:**

- Last 5 plans: 04-04, 04-05, 05-01, 05-02, 05-03 completed; export work has reached real package generation
- Trend: Phase 5 now has end-to-end export building blocks, leaving shipped CLI wiring and final human Anki validation

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Phase 1]: Keep v1 centered on supported-language job orchestration, resumability, and duplicate-safe reruns.
- [Phase 2]: Treat frequency decks and custom word lists as one lexical-ingestion capability.
- [Phase 3]: Put review/regeneration inside the text-quality phase because trust depends on fixing weak cards before export.
- [Phase 3]: Treat Tatoeba as a secondary sentence source only when advanced filtering/reranking and validation are applied; do not use it as the raw default source.
- [Phase 3]: Human UAT closed the remaining naturalness and report-actionability checks, so Phase 3 is verified complete.
- [Phase 4]: Human verification closed the remaining live Azure synthesis and playback-quality checks, so Phase 4 is verified complete.
- [Phase 5]: Freeze the card contract and Anki export semantics only after upstream text and audio stabilize.
- [Plan 05-01]: Freeze export field order in one alias-backed Pydantic contract so every downstream serializer emits the same ten fields.
- [Plan 05-01]: Persist card snapshots by `(job_id, item_key)` and deck artifacts by `(job_id, export_format)` so reruns update deterministically instead of duplicating exports.
- [Plan 05-01]: Store `lemma_key` with export snapshots because stable note identity must round-trip through persistence, not just visible card fields.
- [Plan 05-02]: Assemble export rows only from accepted text plus synthesized audio, and fail fast instead of emitting broken fallback artifacts.
- [Plan 05-02]: Normalize multiline CSV/TSV fields to `<br>` so UTF-8 text imports preserve one field per column in Anki-safe form.
- [Plan 05-03]: Hardcode one Multilang model and deck id pair so `.apkg` imports remain structurally stable across reruns.
- [Plan 05-03]: Validate packaged media before archive write so export failures happen before users import broken audio references.
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

- Execute Phase 5 Plan 04 for the Anki-safe export contract.

### Blockers/Concerns

- No current blockers; Phase 5 Plan 04 should wire the finished export services onto the shipped runtime and CLI path.

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

Last session: 2026-04-26T20:16:31Z
Stopped at: Completed Phase 5 Plan 03; resume at Plan 04 shipped export wiring
Resume file: None
