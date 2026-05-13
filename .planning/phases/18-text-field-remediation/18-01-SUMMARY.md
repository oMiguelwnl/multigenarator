---
phase: 18-text-field-remediation
plan: 01
subsystem: ipa-export-grounding
tags: [ipa, export, lexical-grounding, tdd]
requires: [IPA-01]
provides: [ipa-only-export-rendering, word-ipa-fallback]
affects: [src/multilang/services/assemble_export_cards.py, src/multilang/services/lexical_grounding.py]
tech-stack:
  added: []
  patterns: [deterministic-export-validation, provenance-notes]
key-files:
  created: []
  modified:
    - src/multilang/services/assemble_export_cards.py
    - src/multilang/services/lexical_grounding.py
    - tests/services/test_assemble_export_cards.py
    - tests/services/test_lexical_grounding.py
decisions:
  - Keep spoken_form available for audio/provenance but never append it to exported IPA.
metrics:
  tasks: 2
  completed: 2026-05-13T17:12:55Z
---

# Phase 18 Plan 01: IPA Export and Fallback Summary

One-liner: Normal export IPA now contains only phonetic transcription, with a word fallback recorded when no confident pronunciation exists.

## What Changed

- `_render_ipa` now emits only the IPA value and strips a trailing parenthetical display-word hint such as `[ˈɡromkə] (гро́мко)`.
- Lexical grounding now prefers authoritative IPA, then provider IPA, then the learner display form as a safe fallback.
- Pronunciation provenance notes distinguish authoritative, provider, and word-fallback paths without exposing private source data.

## Verification

- `python -m pytest tests/services/test_assemble_export_cards.py -q` → 14 passed
- `python -m pytest tests/services/test_lexical_grounding.py tests/services/test_assemble_export_cards.py -q` → 28 passed

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 RED | 86869f6 | Added failing IPA-only export rendering tests. |
| Task 1 GREEN | 4f0fff7 | Implemented IPA-only export rendering. |
| Task 2 RED | f13381a | Added failing IPA fallback grounding tests. |
| Task 2 GREEN | 28e1c7c | Implemented word IPA fallback and provenance notes. |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Empty provider IPA fallback guard**
- **Found during:** Task 2
- **Issue:** A configured pronunciation provider could theoretically return an empty IPA string, which would bypass the no-provider fallback path.
- **Fix:** Treat falsey provider IPA as unavailable and fall back to the learner display form.
- **Files modified:** `src/multilang/services/lexical_grounding.py`
- **Commit:** 28e1c7c

## Known Stubs

None.

## Self-Check: PASSED

- Created/modified files exist.
- Commits exist in git history.
- Summary created at `.planning/phases/18-text-field-remediation/18-01-SUMMARY.md`.
