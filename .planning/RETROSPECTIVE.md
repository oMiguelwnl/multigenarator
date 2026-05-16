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

## Milestone: v1.3 - Card Quality Remediation and Deck Validation

**Shipped:** 2026-05-16  
**Phases:** 5 | **Plans:** 16 | **Tasks:** 27 best-effort

### What Was Built

- Non-mutating APKG audit reports for normalized generated-card defects.
- Text remediation for IPA-only output, semantic Definitions, known wrong senses, and sentence-level Translation validation.
- Revised normal generated-card export/template contract with no redundant `Front of Card` and responsive sentence-audio layout.
- Exact word-audio integrity checks across reuse, assembly, and APKG/CSV/TSV export boundaries.
- Shared v1.3 validator facade, executable normalized issue fixtures, and final scanner-readable milestone evidence covering 15/15 requirements.

### What Worked

- Converting the normalized issue catalog into executable fixtures exposed real validator gaps before milestone close.
- Focused mode-isolation tests protected highlight, word-list/manual, and Russian phonetics behavior while normal-card contracts changed.
- Treating audio metadata as exact-match provenance prevented stale reusable assets from silently reaching exports.

### What Was Inefficient

- The milestone audit file was not generated before closeout, so closeout relied on Phase 21 final evidence and explicit user acknowledgement.
- The broad full-suite still has known drift outside the focused v1.3 gate, which creates noise during final verification.
- GSD metadata still reported an older milestone version during transition, requiring manual safety checks before archive.

### Patterns Established

- Keep a thin milestone-specific validation facade over source-of-truth validators instead of duplicating detection logic.
- Store fixture catalogs as scanner-readable JSON tied back to source issue lines and synthetic examples.
- Use final evidence tests to prove both requirement coverage and mode isolation at milestone boundaries.

### Key Lessons

1. A narrative defect catalog should become runnable fixtures before a remediation milestone is considered done.
2. Template validators must accept valid Anki field-reference formatting variants, not only exact literal strings.
3. Focused milestone gates are useful, but broad-suite drift should be resolved before it becomes normalized debt.

### Cost Observations

- Model mix: not tracked.
- Sessions: not tracked.
- Notable: gap closure was fast once the verifier reduced the issue to one concrete validator bypass.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | not tracked | 7 | Established trust-first phase sequencing from job lifecycle through export and audit hygiene. |
| v1.3 | not tracked | 5 | Shifted card-quality defects from ad hoc deck observations into deterministic validators, fixtures, and final evidence. |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | Focused final evidence suite: 25 passed | Not measured | Not tracked |
| v1.3 | Focused closeout regression gate: 175 passed | 15/15 requirements | Shared validator facade and JSON fixture catalog |

### Top Lessons (Verified Across Milestones)

1. Product-quality gates need both deterministic automated tests and selective human verification.
2. Planning artifacts must be maintained as executable evidence, not just narrative documentation.
3. Milestone evidence should include regression checks for unchanged modes, not only the mode being modified.
