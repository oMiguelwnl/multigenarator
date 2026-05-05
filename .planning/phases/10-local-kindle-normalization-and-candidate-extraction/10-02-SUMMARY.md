---
phase: 10-local-kindle-normalization-and-candidate-extraction
plan: 02
subsystem: highlight-candidate-extraction
tags: [kindle, candidates, normalization, filtering]
requires: [10-01]
provides: [HighlightCandidate, HighlightCandidateExtractionResult, extract_highlight_candidates]
affects: [src/multilang/domain/highlights.py, src/multilang/services/highlight_candidate_extraction.py]
tech_stack:
  added: []
  patterns: [deterministic-tokenization, language-stopwords, first-seen-ordering]
key-files:
  created:
    - src/multilang/services/highlight_candidate_extraction.py
    - tests/services/test_highlight_candidate_extraction.py
  modified:
    - src/multilang/domain/highlights.py
decisions:
  - Keep candidate extraction provider-free and DB-free with in-module stopword sets for the supported language fixtures.
metrics:
  tasks: 2
  completed: 2026-05-05T00:00:00Z
  duration: unknown
---

# Phase 10 Plan 02: Highlight Candidate Extraction Summary

Normalized Kindle highlights now produce deterministic, reviewable vocabulary candidates without turning every raw token into a card.

## What Changed

- Added candidate and extraction result contracts to `domain/highlights.py`.
- Implemented Unicode token extraction with URL/digit/noise filtering and per-language stopword sets.
- Preserved first-seen ordering and provenance while incrementing duplicate occurrence counts.
- Added tests covering all 11 supported languages, duplicates, rejected token counts, and accented/Cyrillic preservation.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | dcd2187 | Added RED candidate extraction contracts and behavior tests |
| 2 | 8d5dc1d | Implemented deterministic candidate extraction |

## Verification

```bash
python -m pytest tests/services/test_kindle_highlight_parser.py tests/services/test_highlight_candidate_extraction.py -q
```

Result: `19 passed`.

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written, with the Phase 10 environment continuing to use `python -m pytest` because `uv` is unavailable.

## Auth Gates

None.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- Created files exist.
- Commits `dcd2187` and `8d5dc1d` exist.
- Candidate output stores candidate forms and highlight IDs, not full raw highlight text.
