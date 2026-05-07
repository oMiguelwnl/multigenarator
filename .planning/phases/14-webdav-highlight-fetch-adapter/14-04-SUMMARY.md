---
phase: 14-webdav-highlight-fetch-adapter
plan: 04
subsystem: cli/integration
tags: [webdav, highlights, ingest, idempotency, evidence]
requires:
  - phase: 14-03
    provides: WebDAV fetch command and service seam
provides:
  - `generate --source highlights --webdav-remote-path` handoff
  - Synthetic WebDAV fetch-to-ingest idempotency evidence
affects: [generate-cli, v1.2-audit]
tech-stack:
  added: []
  patterns: [content-hash handoff, privacy-safe evidence artifact]
key-files:
  created: [tests/cli/test_generate_webdav_highlights_command.py, tests/integration/test_webdav_highlight_fetch_flow.py, .planning/phases/14-webdav-highlight-fetch-adapter/14-WEBDAV-EVIDENCE.md]
  modified: [src/multilang/cli.py]
key-decisions:
  - "`--webdav-remote-path` is allowed only for public `--source highlights` and is mutually exclusive with `--input-file`."
requirements-completed: [INGEST-01, INGEST-02]
duration: 25min
completed: 2026-05-07T13:52:31Z
---

# Phase 14 Plan 04: Generate Handoff and Evidence Summary

**WebDAV-fetched highlight exports now feed `generate --source highlights` through private content-hash cache files with idempotency evidence.**

## Performance
- **Duration:** 25 min
- **Started:** 2026-05-07T13:27:53Z
- **Completed:** 2026-05-07T13:52:31Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added `--webdav-remote-path` to `generate` and wired fetched cache files into `GenerationRequest.input_file`.
- Enforced source-only and mutual-exclusion validation before generation starts.
- Added synthetic integration evidence proving cached WebDAV bytes parse and ingest idempotently without private data in evidence.

## Task Commits
1. **Task 1: Add generate WebDAV remote-path handoff** - `48c7f1c` (test), `f66a6bd` (feat)
2. **Task 2: Prove idempotent WebDAV fetch-to-ingest evidence** - `83b6726` (test/evidence)

## Files Created/Modified
- `src/multilang/cli.py` - `--webdav-remote-path` validation and fetch handoff.
- `tests/cli/test_generate_webdav_highlights_command.py` - Generate handoff tests.
- `tests/integration/test_webdav_highlight_fetch_flow.py` - Synthetic fetch-to-ingest idempotency test.
- `.planning/phases/14-webdav-highlight-fetch-adapter/14-WEBDAV-EVIDENCE.md` - Privacy-safe evidence artifact.

## Decisions Made
- Keep the user-facing source as `highlights`; the internal request remains `kindle-highlights` after fetch handoff.

## Deviations from Plan
### Auto-fixed Issues
**1. [Rule 3 - Blocking] RED gate for integration evidence passed because service/generate implementation already existed**
- **Found during:** Task 2
- **Issue:** The integration evidence test passed immediately after Task 1/Plan 02 implementation, so a separate RED failure was not possible without fabricating a broken assertion.
- **Fix:** Kept the meaningful integration test and documented TDD gate caveat instead of weakening coverage.
- **Files modified:** `tests/integration/test_webdav_highlight_fetch_flow.py`
- **Verification:** `uv run pytest tests/integration/test_webdav_highlight_fetch_flow.py tests/services/test_highlight_ingest_lexical_items.py -q`
- **Committed in:** `83b6726`

## Known Stubs
None.

## Threat Flags
None.

## Issues Encountered
None.

## Self-Check: PASSED
- Created files exist: `tests/cli/test_generate_webdav_highlights_command.py`, `tests/integration/test_webdav_highlight_fetch_flow.py`, `14-WEBDAV-EVIDENCE.md`.
- Commits found: `48c7f1c`, `f66a6bd`, `83b6726`.

---
*Phase: 14-webdav-highlight-fetch-adapter*
*Completed: 2026-05-07*
