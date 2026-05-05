---
phase: 10-local-kindle-normalization-and-candidate-extraction
plan: 01
subsystem: local-kindle-parser
tags: [kindle, normalization, parser, privacy]
requires: []
provides: [HighlightProvenance, NormalizedHighlight, RejectedHighlight, KindleParseResult, parse_kindle_highlight_export]
affects: [src/multilang/domain/highlights.py, src/multilang/services/kindle_highlight_parser.py]
tech_stack:
  added: []
  patterns: [pydantic-contracts, stdlib-parser, privacy-safe-diagnostics]
key-files:
  created:
    - src/multilang/domain/highlights.py
    - src/multilang/services/kindle_highlight_parser.py
    - tests/fixtures/kindle_highlights/local_export.html
    - tests/fixtures/kindle_highlights/local_export.txt
    - tests/services/test_kindle_highlight_parser.py
  modified: []
decisions:
  - Store provenance source paths as fixture/file names instead of absolute paths to avoid leaking private local paths.
metrics:
  tasks: 2
  completed: 2026-05-05T00:00:00Z
  duration: unknown
---

# Phase 10 Plan 01: Local Kindle Normalization Parser Summary

Local Kindle HTML/text exports now normalize into typed, deterministic highlight records with privacy-safe rejection diagnostics.

## What Changed

- Added Pydantic contracts for normalized highlights, provenance, rejected rows, and parse results.
- Added synthetic Kindle-like HTML/text fixtures containing learner-safe Unicode examples.
- Implemented `parse_kindle_highlight_export()` for local `.html`, `.htm`, and `.txt` exports.
- Added rejection paths for unsupported formats, empty exports, malformed exports, and unsafe script/control fragments.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | b621a69 | Added RED parser contract tests and fixtures |
| 2 | 3104ff4 | Implemented deterministic local parser |

## Verification

```bash
python -m pytest tests/services/test_kindle_highlight_parser.py -q
```

Result: `6 passed`.

Note: `uv` was unavailable in this environment, so verification used `python -m pytest` after installing project dependencies with `python -m pip install -e ".[dev]"`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Used Python pytest fallback because `uv` is not installed**
- **Found during:** Task 1 verification
- **Issue:** `uv run pytest ...` failed with `uv: command not found`.
- **Fix:** Installed project dependencies and used `python -m pytest` for verification.
- **Files modified:** None
- **Commit:** N/A

## Auth Gates

None.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- Created files exist.
- Commits `b621a69` and `3104ff4` exist.
- Parser diagnostics avoid raw highlight text and absolute unsafe paths.
