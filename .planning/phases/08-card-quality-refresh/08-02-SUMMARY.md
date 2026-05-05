---
phase: 08-card-quality-refresh
plan: 02
status: complete
completed_at: "2026-05-02T19:10:43Z"
key_files:
  - src/multilang/domain/lexicon.py
  - src/multilang/services/provider_pronunciation_adapters.py
  - src/multilang/services/lexical_grounding.py
  - tests/services/test_provider_pronunciation_adapters.py
  - tests/services/test_lexical_grounding.py
---

# Phase 08 Plan 02: AI Pronunciation Generation Summary

Grounded card candidates can now use provider-generated IPA and readable spoken forms instead of trusting Kaikki IPA as final output.

## What Changed

- Added `LiteLLMPronunciationAdapter` with request/result contracts, JSON response enforcement, and non-empty IPA/spoken-form validation.
- Added `spoken_form` to `LexicalCardCandidate`.
- Integrated optional pronunciation generation into lexical grounding for frequency and custom word-list candidates.

## Validation

- `uv run pytest tests/services/test_lexical_grounding.py tests/services/test_provider_pronunciation_adapters.py -x` — passed.

## Deviations from Plan

- Commits were skipped because the user explicitly requested no commits unless explicitly requested.

## Self-Check: PASSED
