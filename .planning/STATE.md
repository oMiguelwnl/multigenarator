---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Kindle Highlights and Template Refresh
status: roadmap_created
stopped_at: Roadmap created; ready to plan Phase 09
last_updated: "2026-05-03T00:00:00Z"
last_activity: 2026-05-03 -- v1.2 roadmap created with Phases 09-16 and 24/24 requirements mapped.
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-03)

**Core value:** Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.  
**Current focus:** Phase 09: Source Profiles, Privacy, and Regression Boundary for v1.2 Kindle Highlights and Template Refresh

## Current Position

Phase: 09 - Source Profiles, Privacy, and Regression Boundary  
Plan: Not started  
Status: Roadmap created; ready for phase planning  
Last activity: 2026-05-03 - v1.2 roadmap created

Progress: [----------] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 38
- v1.0 plans completed: 34
- v1.1 plans completed: 4
- Best-effort task count from v1.0 summaries: 68
- v1.2 planned phases: 8
- v1.2 requirements mapped: 24/24

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
| 08-card-quality-refresh | 4 | complete | complete |

**Recent Trend:**

- Last completed milestone work: Phase 08 Card Quality Refresh completed 2026-05-02.
- Trend: v1.2 begins from a stable card-quality refresh but must protect existing frequency/custom flows while adding highlights.

## Accumulated Context

### Decisions

Full decision history is in `.planning/PROJECT.md` and `.planning/milestones/v1.0-ROADMAP.md`. Current carry-forward decisions:

- Keep the core value centered on trustworthy multilingual Anki card generation.
- Keep Python/uv as the implementation backbone.
- Keep Tatoeba secondary-only behind filtering, reranking, and validation.
- Keep Azure Speech as the primary audio direction with documented fallback behavior.
- Preserve existing frequency-deck and custom word-list behavior while adding highlights as a third input mode.
- Normalize Kindle highlights locally instead of depending on the external Kindle Formatter website.
- Treat WebDAV credentials, raw highlight exports, book metadata, and private reading text as sensitive data that must be redacted from logs, prompts, reports, artifacts, and commits.
- Use dedicated highlight export/template behavior rather than mutating the normal deck note type.
- Keep the phonetics template refresh isolated from normal and highlight deck generation.

### Pending Todos

- Plan Phase 09 with explicit source profile, regression, and privacy/redaction work.
- Keep v1.2 requirement coverage at 24/24 as phases are planned and executed.
- Preserve Phase 08 completion information until v1.1 is archived.

### Blockers/Concerns

- Full-suite collection drift remains in `tests/test_runtime.py` and `tests/test_runtime_templates.py`, which import removed private runtime template adapters. Focused milestone evidence suites passed; Phase 09 should address regression boundaries before relying on broad full-suite gating.
- Exact Kindle export shapes still need real fixture validation; Phase 10 should be fixture-driven and fail closed for malformed or unsafe highlight fragments.

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
Stopped at: v1.2 roadmap created; ready to plan Phase 09  
Resume file: None
