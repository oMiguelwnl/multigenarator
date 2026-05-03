---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Kindle Highlights and Template Refresh
status: defining_requirements
stopped_at: Milestone v1.2 started; defining requirements and roadmap
last_updated: "2026-05-03T00:00:00Z"
last_activity: 2026-05-03 -- Milestone v1.2 started from alter_organizado.md goals.
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-03)

**Core value:** Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.  
**Current focus:** Define requirements and roadmap for v1.2 Kindle Highlights and Template Refresh

## Current Position

Phase: Not started (defining requirements)  
Plan: -  
Status: Defining requirements  
Last activity: 2026-05-03 - Milestone v1.2 started

Progress: [----------] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 34
- Best-effort task count from summaries: 68
- Average duration: 14 min
- Total execution time: 5h 58m

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-job-orchestration-recovery | 6 | 34 min | 6 min |
| 02-input-decks-lexical-grounding | 5 | 2h 7m | 25 min |
| 03-sentence-quality-review-loop | 5 | 1h 17m | 15 min |
| 04-audio-synthesis | 5 | 1h 3m | 13 min |
| 05-anki-safe-export-contract | 5 | 17 min | 3 min |
| 06-end-to-end-text-acceptance-pipeline | 4 | 40 min | 10 min |
| 07-milestone-evidence-audit-hygiene | 4 | 20 min | 5 min |

**Recent Trend:**

- Last 5 completed plans: 06-04, 07-01, 07-02, 07-03, 07-04 completed.
- Trend: Functional E2E gap closure and evidence/audit hygiene are complete; v1.0 milestone audit snapshot passed.

## Accumulated Context

### Decisions

Full decision history is in `.planning/PROJECT.md` and `.planning/milestones/v1.0-ROADMAP.md`. Current carry-forward decisions:

- Keep the core value centered on trustworthy multilingual Anki card generation.
- Keep Python/uv as the implementation backbone.
- Keep Tatoeba secondary-only behind filtering, reranking, and validation.
- Keep Azure Speech as the primary audio direction with documented fallback behavior.
- Keep Anki export contract stable around the requested ten fields.
- Add Kindle highlights as a new deck input mode rather than removing the shipped frequency-deck path.
- Normalize Kindle highlights locally instead of depending on the external Kindle Formatter website.

### Pending Todos

- Define v1.2 requirements for automatic Kindle highlights ingestion, local highlight normalization, highlight deck generation, highlight-specific template behavior, and phonetics template refresh.
- Create v1.2 roadmap starting at Phase 09.

### Blockers/Concerns

- Full-suite collection drift remains in `tests/test_runtime.py` and `tests/test_runtime_templates.py`, which import removed private runtime template adapters. Focused v1.0 milestone evidence suites passed.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260421-001 | implement Tatoeba as a filtered secondary sentence source with advanced reranking and validation, never as the raw default primary source | 2026-04-23 | b833e22 | Verified | [260421-001-tatoeba-filtered-secondary-source](./quick/260421-001-tatoeba-filtered-secondary-source/) |

## Deferred Items

Items acknowledged and carried forward from v1.0 milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| tests | full-suite runtime template adapter import drift | deferred | 2026-04-29 |

## Session Continuity

Last session: 2026-05-03T00:00:00Z  
Stopped at: v1.2 milestone started; requirements and roadmap definition in progress  
Resume file: None
