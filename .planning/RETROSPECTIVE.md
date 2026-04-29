# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 - MVP

**Shipped:** 2026-04-29  
**Phases:** 7 | **Plans:** 34 | **Tasks:** 68 best-effort

### What Was Built

- CLI-first job orchestration with supported-language validation, progress counters, resume, retry, overwrite, and duplicate-safe reruns.
- Lexical grounding for frequency decks and custom word lists using deterministic candidates, `wordfreq` level windows, and cached Kaikki lookup.
- Text quality pipeline with generation boundaries, validation, confidence/review state, report output, item regeneration, and filtered Tatoeba fallback.
- Azure-first word/sentence audio synthesis with repository reuse, media validation, fallback accounting, and live playback verification.
- Fixed Anki export contract with `.apkg`, CSV, TSV, stable note identity, blank `Image`, translation reveal behavior, and packaged audio.
- End-to-end evidence for custom word-list and frequency-deck generation through accepted text, audio, and export.

### What Worked

- Phase-by-phase contracts kept downstream export work from leaking into generation logic.
- Repository-backed state and deterministic keys made resume/rerun behavior testable instead of anecdotal.
- Human UAT was useful at the product boundary: sentence naturalness, review report actionability, Azure playback, and Anki import behavior.
- The milestone audit exposed stale evidence and forced end-to-end proof instead of relying on individual phase completion.

### What Was Inefficient

- Some verification artifacts became stale after later gap-closure work and needed Phase 7 cleanup.
- `gsd-sdk` was not available on PATH, so some planned workflow automation had to be replaced with direct artifact edits.
- Full-suite drift in runtime-template tests remained after private adapter symbols were removed; focused suites passed but broad collection is not clean yet.

### Patterns Established

- Keep one shipped CLI path and wire capabilities into it instead of adding separate setup commands for each phase.
- Persist normalized domain outputs and metadata before export so reruns are auditable and deterministic.
- Treat external providers as adapter boundaries with deterministic fake/local substitutes for tests.
- Validate card usefulness at the Anki import boundary, not only at schema serialization.

### Key Lessons

1. E2E evidence should be added as soon as a feature spans text, audio, and export; otherwise phase-local success can hide stalled product flows.
2. Scanner-facing metadata needs to match the actual scanner contract, not just human-readable status labels.
3. Frozen export contracts are valuable only after upstream text and audio have stabilized enough to assemble real card rows.
4. Human verification belongs at quality boundaries that automation cannot judge, such as pronunciation quality and Anki presentation behavior.

### Cost Observations

- Model mix: not tracked.
- Sessions: not tracked.
- Notable: focused GSD phases kept scope controlled, but missing SDK automation increased closeout manual work.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | not tracked | 7 | Established trust-first phase sequencing from job lifecycle through export and audit hygiene. |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | Focused final evidence suite: 25 passed | Not measured | Not tracked |

### Top Lessons (Verified Across Milestones)

1. Product-quality gates need both deterministic automated tests and selective human verification.
2. Planning artifacts must be maintained as executable evidence, not just narrative documentation.
