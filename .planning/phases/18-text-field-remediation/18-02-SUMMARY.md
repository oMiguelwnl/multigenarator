---
phase: 18-text-field-remediation
plan: 02
subsystem: definition-remediation
tags: [definitions, lexical-grounding, export-validation, tdd]
requires: [DEF-01, DEF-02]
provides: [definition-remediation-helper, export-definition-block]
affects: [src/multilang/services/text_field_remediation.py, src/multilang/services/lexical_grounding.py, src/multilang/services/assemble_export_cards.py]
tech-stack:
  added: []
  patterns: [pure-remediation-helper, fail-fast-export-validation]
key-files:
  created:
    - src/multilang/services/text_field_remediation.py
    - tests/services/test_text_field_remediation.py
  modified:
    - src/multilang/services/lexical_grounding.py
    - src/multilang/services/assemble_export_cards.py
    - tests/services/test_lexical_grounding.py
    - tests/services/test_assemble_export_cards.py
decisions:
  - Keep definition remediation deterministic and provider-free, correcting known senses or falling back to substantive lexical source definitions.
metrics:
  tasks: 2
  completed: 2026-05-13T17:23:04Z
---

# Phase 18 Plan 02: Definition Remediation Summary

One-liner: Learner-facing definitions are remediated to semantic meanings before persistence and blocked at export if morphology-only metadata remains.

## What Changed

- Added `text_field_remediation.py` with `remediate_definition_html` and `validate_definition_html`.
- Added the known corrected Russian sense for `дости́чь`: `verb: to achieve, to attain, to reach`.
- Lexical grounding now remediates generated definitions using part of speech and cached source definitions before creating candidates.
- Export assembly now validates each Definition segment and raises `AssembleExportCardsError` before writing unresolved morphology-only content.

## Verification

- `python -m pytest tests/services/test_text_field_remediation.py -q` → 7 passed
- `python -m pytest tests/services/test_text_field_remediation.py tests/services/test_lexical_grounding.py tests/services/test_assemble_export_cards.py -q` → 37 passed

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 RED | f2129f3 | Added failing definition remediation helper tests. |
| Task 1 GREEN | 118fe05 | Implemented deterministic remediation helpers. |
| Task 2 RED | 74018a3 | Added failing grounding/export integration tests. |
| Task 2 GREEN | da3a590 | Wired remediation into grounding and export validation. |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Updated stale normal export field-order expectation**
- **Found during:** Task 2 verification
- **Issue:** `tests/services/test_assemble_export_cards.py` still expected `Front of Card` in normal export order, while the current domain export contract has already removed it for v1.3 normal cards.
- **Fix:** Updated the focused test expectation to match the current normal export contract so Definition export validation can be verified.
- **Files modified:** `tests/services/test_assemble_export_cards.py`
- **Commit:** da3a590

## Known Stubs

None.

## Self-Check: PASSED

- Created files exist: `src/multilang/services/text_field_remediation.py`, `tests/services/test_text_field_remediation.py`.
- Commits exist in git history.
- Summary created at `.planning/phases/18-text-field-remediation/18-02-SUMMARY.md`.
