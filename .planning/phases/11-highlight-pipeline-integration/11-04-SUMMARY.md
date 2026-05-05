---
phase: 11-highlight-pipeline-integration
plan: 04
subsystem: public highlights CLI
tags: [highlights, cli, summary, privacy]
requires: [MODE-01, INGEST-04]
provides: [public-highlights-mode, count-only-lifecycle-summary]
affects: [cli, regression-tests]
tech_stack:
  added: []
  patterns: [public-alias-to-internal-source-profile, count-only-output]
key_files:
  created: []
  modified:
    - src/multilang/cli.py
    - tests/cli/test_generate_command.py
    - tests/cli/test_kindle_highlight_preview_command.py
    - tests/integration/test_v12_existing_mode_regression_boundary.py
    - tests/integration/test_kindle_local_normalization_flow.py
decisions:
  - Public CLI accepts `highlights` while internal profile remains `kindle-highlights`.
metrics:
  tasks: 2
  completed: 2026-05-05
---

# Phase 11 Plan 04: Public CLI Mode and Lifecycle Summary Output Summary

Users can run `generate --source highlights --input-file ...` and receive count-only lifecycle counters without exposing private highlight content.

## Completed Tasks

| Task | Status | Commit |
|------|--------|--------|
| Map public highlights source to internal profile | Complete | 94fe57d |
| Print count-only highlight lifecycle summary and update regressions | Complete | 94fe57d |

## Verification

- `python -m pytest tests/cli/test_generate_command.py tests/cli/test_kindle_highlight_preview_command.py tests/integration/test_v12_existing_mode_regression_boundary.py tests/integration/test_kindle_local_normalization_flow.py -q` — passed.
- Phase suite: 63 passed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated Phase 10 candidate-order regression expectation**
- **Found during:** Task 2 verification
- **Issue:** content-derived Plan 01 sorting changed the first-three candidate order asserted by a local normalization regression.
- **Fix:** Updated the regression to assert the new deterministic content-derived order set instead of obsolete first-seen sequence order.
- **Files modified:** tests/integration/test_kindle_local_normalization_flow.py
- **Commit:** 94fe57d

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- Summary file created.
- Commits found: dee07b3, 94fe57d.
