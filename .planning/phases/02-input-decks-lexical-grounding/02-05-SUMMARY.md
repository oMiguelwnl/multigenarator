---
phase: 02-input-decks-lexical-grounding
plan: 05
subsystem: runtime
tags: [cli, lexical-cache, kaikki, documentation, integration-testing]
requires:
  - phase: 02-input-decks-lexical-grounding/04
    provides: shipped lexical-ingestion wiring and the clean-runtime verification evidence that exposed the bootstrap gap
provides:
  - Shipped `multilang generate` lexical-cache prerequisite enforcement
  - Clean-runtime bootstrap and fail-fast coverage for Kaikki-backed grounding
  - Operator documentation for preparing and reusing lexical cache data
affects: [phase-03-sentence-quality, runtime-path, operator-workflows, testing]
tech-stack:
  added: []
  patterns: [single-command runtime bootstrap, fail-fast lexical prerequisites, authoritative-cache reuse]
key-files:
  created: [docs/lexical-data.md, .planning/phases/02-input-decks-lexical-grounding/02-05-SUMMARY.md]
  modified: [src/multilang/cli.py, tests/integration/test_lexical_job_flow.py, .planning/STATE.md, .planning/ROADMAP.md]
key-decisions:
  - "Keep lexical bootstrap on the existing `multilang generate` command via `--lexicon-source-file` instead of adding a second setup command."
  - "Abort before ingestion when the requested language cache is missing and no explicit Kaikki archive was provided."
patterns-established:
  - "Shipped-path prerequisite checks run only on the default runtime service, leaving injected test services free to stub lexical grounding."
  - "Local Kaikki archives bootstrap one reusable `<lexicon_data_dir>/<language>/kaikki-index.json` cache that later runs reuse unchanged."
requirements-completed: [DECK-02, DECK-03, LEX-02, LEX-03]
duration: 39 min
completed: 2026-04-21
---

# Phase 2 Plan 5: Clean-Runtime Lexical Bootstrap Gap Closure Summary

**Shipped `multilang generate` now either bootstraps Kaikki lexical cache data from an explicit local archive or stops immediately with a clear prerequisite message.**

## Performance

- **Duration:** 39 min
- **Started:** 2026-04-21T15:49:18Z
- **Completed:** 2026-04-21T16:28:07Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Enforced the lexical-cache prerequisite on the shipped runtime path while keeping injected test services free to provide their own grounding behavior.
- Added clean-runtime integration coverage that proves missing lexical data exits before any generation job or lexical candidate rows are created.
- Documented the one-time `--lexicon-source-file` bootstrap flow and the cache reuse path for later runs.

## Task Commits

No git commit was created in this session because the user did not request one.

## Files Created/Modified
- `src/multilang/cli.py` - bootstraps a language cache when `--lexicon-source-file` is provided and aborts early with a prerequisite diagnostic when it is not.
- `tests/integration/test_lexical_job_flow.py` - verifies both clean-runtime bootstrap success and fail-fast behavior before ingestion begins.
- `docs/lexical-data.md` - explains how to prepare and reuse local Kaikki lexical cache data.
- `.planning/phases/02-input-decks-lexical-grounding/02-05-SUMMARY.md` - records the completed gap-closure plan.
- `.planning/ROADMAP.md` - records the new Phase 2 gap-closure plan and marks Phase 2 as awaiting re-verification.
- `.planning/STATE.md` - updates session continuity and current focus for the next resume.

## Decisions Made
- Kept lexical bootstrap on `multilang generate` so operators still have one shipped entry point.
- Treated missing lexical data as a hard prerequisite failure instead of allowing frequency failures or pending-only word-list output on a clean checkout.

## Deviations from Plan

- `tests/cli/test_generate_command.py` already contained the expected bootstrap and fail-fast assertions in the worktree before resumption, so execution focused on making the shipped runtime satisfy those assertions and adding integration/doc coverage.
- The plan's full-suite verification command was intentionally not completed after targeted lexical suites passed because the user asked to skip the slow full `tests/` run.

## Issues Encountered
- `gsd-sdk` is unavailable in this environment, so resume/status tracking was reconstructed directly from `.planning` artifacts.
- The full regression suite is slow in this environment; targeted lexical suites were used instead for this plan after confirming with the user.

## Verification Results
- `uv run pytest tests/cli/test_generate_command.py -q` -> `10 passed`
- `uv run pytest tests/services/test_kaikki_lookup.py tests/integration/test_lexical_job_flow.py -q` -> `8 passed`
- `uv run pytest tests -q` -> aborted at user request after targeted suites passed

## User Setup Required

None - operators only need a local Kaikki `.jsonl.gz` archive when bootstrapping a language cache for the first time.

## Next Phase Readiness
- The clean-runtime lexical bootstrap gap from `02-VERIFICATION.md` is now addressed on the shipped path.
- The next logical step is Phase 2 re-verification; if it passes, the project can move on to Phase 3 planning.

---
*Phase: 02-input-decks-lexical-grounding*
*Completed: 2026-04-21*
