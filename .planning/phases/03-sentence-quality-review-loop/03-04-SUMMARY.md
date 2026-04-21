---
phase: 03-sentence-quality-review-loop
plan: 04
subsystem: testing
tags: [cli, review-report, text-quality, typer, json]

# Dependency graph
requires:
  - phase: 03-03
    provides: bounded text generation, validation, and review-required persistence
provides:
  - CLI-first flagged text review reports with stable `job_id` and `item_key` identity
  - `multilang generate` review diagnostics for flagged cards and saved report paths
affects: [phase-03-plan-05, export, regeneration]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Persist flagged text review output as deterministic JSON", "Keep review diagnostics on the existing multilang generate command"]

key-files:
  created: [src/multilang/services/text_review.py, tests/services/test_text_review.py]
  modified: [src/multilang/cli.py, tests/cli/test_generate_command.py]

key-decisions:
  - "Review reports stay on the shipped `multilang generate` path via summary lines instead of a new command tree."
  - "Empty flagged queues print `flagged_cards=0` and do not write a placeholder artifact."

patterns-established:
  - "Review artifacts serialize stable job and item identifiers for later item-level regeneration targeting."
  - "CLI verification can inject a review-report builder without changing the shipped operator surface."

requirements-completed: [TEXT-04, TEXT-05]

# Metrics
duration: 11 min
completed: 2026-04-21
---

# Phase 3 Plan 04: Sentence-quality review queue summary

**CLI-first flagged text review reports with stable identifiers and `multilang generate` diagnostics for review-required cards.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-04-21T18:10:37Z
- **Completed:** 2026-04-21T18:21:31Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added a `TextReviewService` that serializes flagged text rows into deterministic JSON review artifacts.
- Ordered flagged review items by operator risk and preserved `job_id` / `item_key` identity for later regeneration.
- Extended `multilang generate` to print `flagged_cards` and `review_report` without introducing a second top-level command.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build the flagged-text review queue and report serializer** - `7688ad9` (test), `8faab9f` (feat)
2. **Task 2: Surface flagged-card review output on `multilang generate`** - `83b60ab` (test), `4972418` (feat)

**Plan metadata:** pending

_Note: TDD tasks used separate RED and GREEN commits._

## Files Created/Modified
- `src/multilang/services/text_review.py` - Builds deterministic persisted review reports for flagged text rows.
- `tests/services/test_text_review.py` - Covers risk ordering, stable identity, and JSON artifact output.
- `src/multilang/cli.py` - Prints review counters and optional report paths on `multilang generate`.
- `tests/cli/test_generate_command.py` - Verifies shipped-path review output and empty-artifact suppression.

## Decisions Made
- Kept review/report diagnostics on `multilang generate` so Phase 3 preserves the single shipped operator surface from earlier plans.
- Suppressed empty review report files so accepted runs still emit `flagged_cards=0` without producing misleading placeholder artifacts.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 3 now has a persisted review queue and CLI-visible flagged-card diagnostics.
- Ready for 03-05 item-level regeneration work to target saved `job_id` / `item_key` review entries.

## Self-Check: PASSED
- Found `.planning/phases/03-sentence-quality-review-loop/03-04-SUMMARY.md` on disk.
- Verified task commits `7688ad9`, `8faab9f`, `83b60ab`, and `4972418` exist in git history.
