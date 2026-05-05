---
phase: 10-local-kindle-normalization-and-candidate-extraction
plan: 03
subsystem: highlight-import-preview
tags: [kindle, cli, preview, privacy]
requires: [10-01, 10-02]
provides: [HighlightImportPreview, build_highlight_import_preview, preview-kindle-highlights]
affects: [src/multilang/domain/highlights.py, src/multilang/services/highlight_import_preview.py, src/multilang/cli.py]
tech_stack:
  added: []
  patterns: [count-only-cli-output, preview-only-side-effect-boundary]
key-files:
  created:
    - src/multilang/services/highlight_import_preview.py
    - tests/services/test_highlight_import_preview.py
    - tests/cli/test_kindle_highlight_preview_command.py
  modified:
    - src/multilang/domain/highlights.py
    - src/multilang/cli.py
decisions:
  - Add a preview-only Kindle command while keeping kindle-highlights unavailable in the generation source flow until Phase 11.
metrics:
  tasks: 2
  completed: 2026-05-05T00:00:00Z
  duration: unknown
---

# Phase 10 Plan 03: Kindle Import Preview Summary

Operators can now preview local Kindle import/candidate counts from the CLI without invoking generation, export, text, translation, or audio work.

## What Changed

- Added a `HighlightImportPreview` count contract.
- Implemented `build_highlight_import_preview()` to combine parser and candidate extraction counts.
- Added `preview-kindle-highlights` CLI command with stable `key=value` count output.
- Preserved the existing `generate --source` boundary so `kindle-highlights` remains blocked until Phase 11.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | a9e3c68 | Added RED import preview service tests |
| 1 | 3a8eaf0 | Implemented import preview service |
| 2 | 367e2b4 | Added RED preview CLI tests |
| 2 | 3b1b4df | Implemented preview-only CLI command |

## Verification

```bash
python -m pytest tests/services/test_kindle_highlight_parser.py tests/services/test_highlight_candidate_extraction.py tests/services/test_highlight_import_preview.py tests/cli/test_kindle_highlight_preview_command.py -q
```

Result: `26 passed`.

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written, with `python -m pytest` used because `uv` is unavailable.

## Auth Gates

None.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- Created files exist.
- Commits `a9e3c68`, `3a8eaf0`, `367e2b4`, and `3b1b4df` exist.
- CLI output is count-only and does not call generation/export services.
