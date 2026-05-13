---
phase: 18-text-field-remediation
plan: 03
subsystem: text-validation
tags: [translation, validation, repair-review, tdd]
requires: [TRNS-01]
provides: [translation-mismatch-gate, repair-review-proof]
affects: [src/multilang/services/text_validation.py, tests/services/test_text_validation.py, tests/services/test_generate_text_items.py]
tech-stack:
  added: []
  patterns: [deterministic-validation, conservative-heuristics]
key-files:
  created: []
  modified:
    - src/multilang/services/text_validation.py
    - tests/services/test_text_validation.py
    - tests/services/test_generate_text_items.py
decisions:
  - Use conservative length and definition-gloss heuristics to reject isolated-word translations only when the source sentence has enough context.
metrics:
  tasks: 2
  completed: 2026-05-13T17:17:18Z
---

# Phase 18 Plan 03: Translation Validation Summary

One-liner: Translation validation now rejects isolated word/gloss translations and routes failed generated text through repair or review.

## What Changed

- `TextValidationService` now flags short translations that match only the target term or a definition gloss while the source sentence contains multiple tokens.
- Existing checks for empty, definition-copied, and source-copied translations remain intact.
- `GenerateTextItemsService` tests now prove isolated-word translations become `translation_mismatch` review records unless repair supplies a full-sentence translation.

## Verification

- `python -m pytest tests/services/test_text_validation.py -q` → 18 passed
- `python -m pytest tests/services/test_text_validation.py tests/services/test_generate_text_items.py -q` → 33 passed

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 RED | 6ffdbaa | Added failing isolated-word translation validation tests. |
| Task 1 GREEN | 30b4d9b | Implemented conservative translation mismatch heuristics. |
| Task 2 TEST | 8911fed | Added pipeline proof for repair/review routing. |

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written.

### TDD Note

Task 2 pipeline tests passed immediately because Task 1 had already implemented the underlying validation behavior. The tests were still committed separately as focused pipeline evidence.

## Known Stubs

None.

## Self-Check: PASSED

- Created/modified files exist.
- Commits exist in git history.
- Summary created at `.planning/phases/18-text-field-remediation/18-03-SUMMARY.md`.
