---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Classical Latin MVP
status: ready_to_plan
stopped_at: Completed 22-03-PLAN.md
last_updated: "2026-06-01T18:14:10.571Z"
last_activity: 2026-06-01 - Created v2.0 Classical Latin MVP roadmap with Phases 22-28 and 30/30 requirements mapped.
progress:
  total_phases: 7
  completed_phases: 1
  total_plans: 3
  completed_plans: 3
  percent: 14
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-01)

**Core value:** Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.  
**Current focus:** Phase 23: Frozen 50-Card Source Pack and Sentence Sequence.

## Current Position

Phase: 23 of 28 (Frozen 50-Card Source Pack and Sentence Sequence)
Plan: TBD in current phase
Status: Ready to plan
Last activity: 2026-06-01 - Completed Phase 22 Latin mode contracts, isolated CLI, and focused regression evidence.

Progress: [█---------] 14%

## Performance Metrics

**Velocity:**

- Total plans completed: 68 from shipped/previous milestones
- v2.0 plans completed: 3
- Average duration: 7min for v2.0
- Total v2.0 execution time: 0.35 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 22. Latin Mode Contracts and Isolation | 3 | 21min | 7min |
| 23. Frozen 50-Card Source Pack and Sentence Sequence | 0 | TBD | N/A |
| 24. Morphology Evidence and Gramatica Gate | 0 | TBD | N/A |
| 25. Latin Review Gates and Curated Records | 0 | TBD | N/A |
| 26. Portuguese Translation Quality | 0 | TBD | N/A |
| 27. Latin Audio Policy and Integrity | 0 | TBD | N/A |
| 28. Latin Export and Milestone Evidence | 0 | TBD | N/A |

**Recent Trend:**

- Last shipped milestone: v1.3 completed through Phase 21 with focused evidence passing.
- Trend: v2.0 starts from approved Latin requirements and a standard-granularity 7-phase roadmap.

| Phase 22-latin-mode-contracts-and-isolation P1 | 7min | 3 tasks | 5 files |
| Phase 22-latin-mode-contracts-and-isolation P2 | 7min | 3 tasks | 4 files |
| Phase 22-latin-mode-contracts-and-isolation P3 | 7min | 3 tasks | 1 files |

## Accumulated Context

### Decisions

Full decision history is in `.planning/PROJECT.md`. Current v2.0 decisions affecting execution:

- v2.0 is Classical Latin only; Greek and other Latin variants are out of scope.
- MVP scope is exactly 50 reviewed cards; 300/1000/3000-card Latin scale is deferred.
- Latin uses a separate `la` / Classical Latin generation path, not the modern-language frequency path.
- All MVP groups are included: mode, frequency, source/sentence, grammar, Portuguese text, review, audio, export, evidence/regression.
- Final learner-ready export is approved-only, including source, grammar, translation, and audio readiness gates.
- Source mix is license-gated and must distinguish original Classical Latin, adapted didactic Latin, and reference examples.
- `Gramatica` uses short abbreviations (`sg`, `pl`) with Latin case labels including `Genitivus`.
- [Phase 22-latin-mode-contracts-and-isolation]: Kept Classical Latin out of SupportedLanguage and represented it through LatinGenerationRequest.
- [Phase 22-latin-mode-contracts-and-isolation]: Added a separate generate-latin-mvp command instead of extending generate --source.
- [Phase 22-latin-mode-contracts-and-isolation]: Kept Phase 22 evidence offline and import-only for review/audio boundaries.

### Pending Todos

- Plan Phase 23 with `/gsd-plan-phase 23`.
- Repair broad-suite drift before treating full `python -m pytest -q` as authoritative again.

### Blockers/Concerns

- Latin TTS quality remains a caveat until Phase 27 sample comparison and playback review lock the approved-only audio policy.
- Source licensing must be resolved in Phase 23 before production sentence fixtures are treated as redistributable.
- Broad-suite drift remains known debt; focused regression evidence should stay authoritative until repaired.
- Plan 22-02 listed verification exposes existing CLI/audio drift: `tests/cli/test_generate_command.py::test_generate_command_default_runtime_reports_audio_counters` expects `fallback_audio_items=1`, but current runtime output omits it.

## Deferred Items

Items acknowledged and carried forward:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Latin scale | 300-card pilot and 3000-card Latin deck | Deferred beyond 50-card MVP | v2.0 roadmap |
| Test suite drift | Full-suite collection drift in tests importing removed private runtime template adapters | Known debt | Pre-v1.3 |
| quick_task | 260430-001-russian-card-quality-regression | Missing | v1.3 closeout 2026-05-16 |
| CLI/audio drift | `test_generate_command_default_runtime_reports_audio_counters` missing `fallback_audio_items=1` output | Deferred; unrelated to Phase 22 Latin changes | Phase 22 Plan 22-02 verification |

## Session Continuity

Last session: 2026-06-01T18:14:10.566Z
Stopped at: Completed 22-03-PLAN.md
Resume file: None
