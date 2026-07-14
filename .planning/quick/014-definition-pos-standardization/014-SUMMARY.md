# Quick Task 014 Summary: Definition POS Standardization

## Status

Completed.

## What Changed

- Standardized learner definition labels after provider generation.
- Trusted POS aliases are canonicalized, for example `prep:` becomes `preposition:` and `adj:` becomes `adjective:`.
- Generic or unknown POS no longer preserves provider-invented grammatical labels such as `noun:`; it falls back to neutral `term:`.
- Added deterministic German function-word inference for common articles, conjunctions, prepositions, and pronouns.
- Fixed the observed German `die` case so an LLM output like `noun: the definite article...` is normalized to `article: the definite article...`.
- Passed source language into definition remediation from lexical grounding.
- Added focused tests for German `die`, unknown POS neutral labeling, and trusted POS canonicalization.

## Verification

Passed:

- `uv run pytest tests/services/test_text_field_remediation.py tests/services/test_lexical_grounding.py -q` -> `32 passed`.
- `uv run pytest tests/services/test_text_field_remediation.py tests/services/test_lexical_grounding.py tests/services/test_assemble_export_cards.py -q` -> `51 passed`.
- `uv run pytest tests/services/test_assemble_export_cards.py tests/services/test_text_validation.py tests/services/test_generate_text_items.py -q` -> `65 passed`.
- German provider-backed smoke regenerated with `litellm`, `deepl`, and `azure`.
- Exported APKG/CSV/TSV for job `42416e19-f546-41c6-8b5d-f2b4031f68c0`.
- CSV assertion passed: contains `die,/diː/,article:` and does not contain `die,/diː/,noun:`.
- `uv run pytest` -> `828 passed, 3 warnings`.

## Generated German Smoke Artifacts

- APKG: `.multilang/test-decks/de-full-standardized-v2/exports/42416e19-f546-41c6-8b5d-f2b4031f68c0.apkg`
- CSV: `.multilang/test-decks/de-full-standardized-v2/exports/42416e19-f546-41c6-8b5d-f2b4031f68c0.csv`
- TSV: `.multilang/test-decks/de-full-standardized-v2/exports/42416e19-f546-41c6-8b5d-f2b4031f68c0.tsv`
- Audit: `.multilang/test-decks/de-full-standardized-v2/audit/deck-audit.md`

## Notes

- The APKG audit reports only expected partial-deck issues because the smoke intentionally generated 3/3000 frequency cards.
- German noun capitalization remains a separate quality issue: `pause` should be `Pause`, and generated sentences should use `eine Pause`.
