---
phase: 03-sentence-quality-review-loop
plan: 05
subsystem: api
tags: [cli, runtime, text-generation, regeneration, sqlalchemy]
requires:
  - phase: 03-sentence-quality-review-loop
    provides: review state, text persistence, and validation contracts from Plans 03-01 through 03-04
provides:
  - shipped CLI wiring for lexical ingestion plus Phase 3 text generation
  - item-level text regeneration by stable job_id and item_key
  - repository-backed integration coverage for flagged-item reruns
affects: [phase-04-audio-generation, runtime, cli, review-loop]
tech-stack:
  added: []
  patterns: [repository-backed runtime composition, single-command item-level regeneration]
key-files:
  created:
    - .planning/phases/03-sentence-quality-review-loop/03-05-SUMMARY.md
    - src/multilang/services/regenerate_text_item.py
    - tests/services/test_regenerate_text_item.py
    - tests/integration/test_text_job_flow.py
  modified:
    - src/multilang/runtime.py
    - src/multilang/cli.py
    - src/multilang/services/ingest_lexical_items.py
    - src/multilang/repositories/job_repository.py
    - src/multilang/repositories/lexical_repository.py
    - tests/cli/test_generate_command.py
key-decisions:
  - "Keep regeneration on the existing multilang generate surface behind --resume plus --regenerate-item-key."
  - "Compose Phase 3 text services in the runtime layer instead of moving full text ownership into lexical ingestion."
patterns-established:
  - "Runtime composition: lexical ingestion advances the job to generate_text, then runtime-owned text services persist reviewable rows."
  - "Stable item repair: regeneration updates the existing (job_id, item_key) text row in place."
requirements-completed: [TEXT-05, TEXT-01, TEXT-02, TEXT-03, TEXT-04]
duration: 42 min
completed: 2026-04-21
---

# Phase 3 Plan 05: Sentence quality shipped-path completion Summary

**Repository-backed `multilang generate` now runs lexical ingestion, text generation, review reporting, and single-item regeneration on the same shipped CLI path.**

## Performance

- **Duration:** 42 min
- **Started:** 2026-04-21T18:06:00Z
- **Completed:** 2026-04-21T18:48:18Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Added `RegenerateTextItemService` for one-card text reruns keyed by `job_id` and `item_key`.
- Extended the runtime/CLI path to run lexical ingestion and Phase 3 text generation together, with review-report output.
- Added shipped-path CLI and integration tests covering both initial text generation and targeted flagged-item regeneration.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement item-level text regeneration against stable item identity** - `bef7716` (feat)
2. **Task 2: Wire Phase 3 runtime execution and shipped-path regeneration coverage** - `2fe7ad6` (feat)

**Plan metadata:** committed after summary creation.

## Files Created/Modified
- `src/multilang/services/regenerate_text_item.py` - reruns generate/validate/repair for one persisted text row.
- `src/multilang/runtime.py` - builds repository-backed Phase 3 runtime services and shipped-path text execution.
- `src/multilang/cli.py` - adds `--regenerate-item-key` and prints text/review diagnostics on the shipped command.
- `src/multilang/services/ingest_lexical_items.py` - advances completed lexical jobs to `JobStage.GENERATE_TEXT`.
- `src/multilang/repositories/job_repository.py` - preserves stage progression during text generation and regeneration.
- `src/multilang/repositories/lexical_repository.py` - loads one persisted lexical candidate by `job_id` and `item_key`.
- `tests/services/test_regenerate_text_item.py` - locks targeted row updates, lexical reuse, and failed rerun behavior.
- `tests/cli/test_generate_command.py` - covers shipped CLI regeneration flow.
- `tests/integration/test_text_job_flow.py` - verifies one-job text generation plus in-place flagged-item regeneration.

## Decisions Made
- Kept the operator surface on `multilang generate` and required `--resume` for `--regenerate-item-key` to preserve explicit auditability.
- Left lexical ingestion scoped to lexical persistence, while runtime composition owns the follow-on Phase 3 text stage.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed resume-state corruption during text-stage progression**
- **Found during:** Task 2 (runtime execution and regeneration wiring)
- **Issue:** marking items successful at `generate_text` left persisted item stage data stuck at `ingest`, so resume validation rejected regeneration requests.
- **Fix:** updated job success handling to advance existing items to the latest completed stage instead of treating text-stage writes as duplicates.
- **Files modified:** `src/multilang/repositories/job_repository.py`
- **Verification:** `uv run pytest tests/services/test_generate_text_items.py tests/services/test_text_review.py tests/services/test_regenerate_text_item.py tests/cli/test_generate_command.py tests/integration/test_text_job_flow.py -q`
- **Committed in:** `2fe7ad6`

**2. [Rule 3 - Blocking] Added repository helpers required for single-item regeneration**
- **Found during:** Task 2 (runtime execution and regeneration wiring)
- **Issue:** the runtime could not target one persisted lexical candidate or advance a lexical-only job into the text stage with the existing repository API.
- **Fix:** added lexical candidate lookup by `(job_id, item_key)` and explicit job-stage advancement after lexical ingestion.
- **Files modified:** `src/multilang/repositories/lexical_repository.py`, `src/multilang/repositories/job_repository.py`, `src/multilang/services/ingest_lexical_items.py`
- **Verification:** `uv run pytest tests/services/test_text_generation.py tests/services/test_text_validation.py tests/services/test_generate_text_items.py tests/services/test_text_review.py tests/integration/test_text_job_flow.py tests/cli/test_generate_command.py -q`
- **Committed in:** `2fe7ad6`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** both fixes were required to make shipped-path regeneration reliable; no user-visible scope expansion beyond the planned runtime flow.

## Issues Encountered
- Resume validation initially failed on regeneration because Phase 1 item-stage persistence assumed duplicate success writes instead of cross-stage progression. Updating the repository logic resolved the shipped-path flow.

## Known Stubs
- `src/multilang/runtime.py:32-54` - runtime uses deterministic local sentence/translation template adapters for shipped-path verification until provider-backed generation and translation adapters land in a later phase.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 3 shipped-path text generation and review regeneration are now wired on the default CLI runtime.
- Ready for Phase 4 work to consume accepted/flagged text rows without needing a separate text bootstrap command.

## Self-Check: PASSED

- Found `.planning/phases/03-sentence-quality-review-loop/03-05-SUMMARY.md`
- Found task commit `bef7716`
- Found task commit `2fe7ad6`
