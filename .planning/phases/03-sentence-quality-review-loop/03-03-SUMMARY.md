---
phase: 03-sentence-quality-review-loop
plan: 03
subsystem: testing
tags: [phase-3, text-validation, repair-loop, confidence-scoring, pytest]
requires:
  - phase: 03-01
    provides: text-quality persistence contracts for generated sentence records
  - phase: 03-02
    provides: sentence and translation generation services for grounded lexical candidates
provides:
  - deterministic text validation with machine-readable failure flags
  - one-repair generate/validate pipeline for accepted and review-required text rows
  - regression coverage for lemma checks, translation guardrails, and repair routing
affects: [phase-3-review-flow, cli-review-reporting, text-generation]
tech-stack:
  added: []
  patterns: [structured validation results, bounded single-repair retries]
key-files:
  created:
    - src/multilang/services/text_validation.py
    - src/multilang/services/generate_text_items.py
    - tests/services/test_text_validation.py
    - tests/services/test_generate_text_items.py
  modified: []
key-decisions:
  - "Represent validation outcomes as structured flags plus confidence score/label instead of one free-form error string."
  - "Mark JobStage.GENERATE_TEXT successful only after the accepted or review-required text record has been persisted."
patterns-established:
  - "Phase 3 services validate generated text deterministically before learner-facing acceptance."
  - "Repair loops are capped at one retry, then persisted as review-required with machine-readable reasons."
requirements-completed: [TEXT-01, TEXT-02, TEXT-03, TEXT-04]
duration: 13 min
completed: 2026-04-21
---

# Phase 3 Plan 03: Sentence validation and repair loop Summary

**Deterministic sentence validation with confidence scoring and a one-repair generate/validate pipeline for persisted review routing.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-04-21T17:50:30Z
- **Completed:** 2026-04-21T18:03:30Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added `TextValidationService` with lemma/form checks, learner-friendly sentence limits, banned-pattern heuristics, and translation guardrails.
- Added `GenerateTextItemsService` to generate, validate, retry once, and persist accepted or review-required text outcomes.
- Locked the Phase 3 behavior with focused pytest coverage for deterministic validation and bounded repair routing.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build deterministic text validation and confidence scoring** - `2780dbb` (test), `e37f5db` (feat)
2. **Task 2: Implement the one-repair generate-text pipeline** - `1f8e316` (test), `b68bf2c` (feat)

**Plan metadata:** pending

## Files Created/Modified
- `src/multilang/services/text_validation.py` - Deterministic validator returning structured flags and confidence scoring.
- `src/multilang/services/generate_text_items.py` - Coordinator for generate/validate/repair-once persistence flow.
- `tests/services/test_text_validation.py` - Regression coverage for lemma omission, banned patterns, translation mismatch, and confidence downgrade.
- `tests/services/test_generate_text_items.py` - Regression coverage for repair-once acceptance and review-required fallback.

## Decisions Made
- Used structured `TextValidationResult` output so downstream review/report code can persist reasons directly.
- Persisted the final text row before recording `JobStage.GENERATE_TEXT` success to keep job state aligned with saved text artifacts.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 3 now has deterministic sentence-quality gates and persisted review reasons ready for review/report work.
- CLI/report surfaces can consume the saved `review_status`, `review_reason`, and `validation_flags` without adding another repair loop.

## Verification

- `uv run pytest tests/services/test_text_validation.py -q`
- `uv run pytest tests/services/test_text_validation.py tests/services/test_generate_text_items.py -q`

## Self-Check: PASSED

- Verified `.planning/phases/03-sentence-quality-review-loop/03-03-SUMMARY.md` exists.
- Verified commits `2780dbb`, `e37f5db`, `1f8e316`, and `b68bf2c` exist in git history.

---
*Phase: 03-sentence-quality-review-loop*
*Completed: 2026-04-21*
