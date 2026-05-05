---
phase: 11-highlight-pipeline-integration
plan: 01
subsystem: highlight identity
tags: [highlights, identity, privacy, jobs]
requires: [INGEST-04]
provides: [stable-highlight-candidate-keys, safe-highlight-manifest-contract]
affects: [highlight-candidate-extraction, input-fingerprints]
tech_stack:
  added: []
  patterns: [content-derived-sha256-identity, pydantic-contracts]
key_files:
  created: []
  modified:
    - src/multilang/domain/highlights.py
    - src/multilang/services/highlight_candidate_extraction.py
    - tests/services/test_highlight_candidate_extraction.py
    - tests/services/test_generate_job.py
decisions:
  - Highlight candidates use source content hash plus lemma hash instead of sequence-only keys.
metrics:
  tasks: 2
  completed: 2026-05-05
---

# Phase 11 Plan 01: Stable Content-Derived Highlight Import/Candidate Identity Summary

Stable SHA-256 highlight identity now makes reruns and reordered exports duplicate-safe without path or raw-text leakage.

## Completed Tasks

| Task | Status | Commit |
|------|--------|--------|
| Define stable highlight identity contracts | Complete | 9042e16 |
| Generate reorder-safe candidate keys and highlight fingerprints | Complete | a60eb98 |

## Verification

- `python -m pytest tests/services/test_highlight_candidate_extraction.py tests/services/test_generate_job.py -q` — passed.
- Phase suite: 63 passed.

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- Summary file created.
- Commits found: 1a3e3a5, 9042e16, c5c1430, a60eb98.
