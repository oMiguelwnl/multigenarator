# Quick Task 015 Summary: German POS And Display Normalization

## Status

Completed.

## What Changed

- Preserved valid provider POS labels when the asset POS is unknown and no deterministic override applies.
- Kept deterministic German function-word overrides higher priority than provider labels, so `die` remains `article:` even if the provider returns `noun:`.
- Added a deterministic German lexical override for `pause`, normalizing it to `Pause` with POS `noun` before definition, sentence, pronunciation, and export data are built.
- Added tests for:
  - German `die` article override.
  - German `blieb` preserving provider `verb:` label.
  - German `pause` becoming `Pause` with `noun:` definition.

## Verification

Passed:

- `uv run pytest tests/services/test_text_field_remediation.py tests/services/test_lexical_grounding.py tests/services/test_assemble_export_cards.py -q` -> `54 passed`.
- German provider-backed smoke regenerated with `litellm`, `deepl`, and `azure`.
- Exported APKG/CSV/TSV for job `9a72c2dc-1ec9-476d-a05c-3ff5ed429643`.
- CSV assertions passed:
  - `die,/diː/,article:` present.
  - `die,/diː/,noun:` absent.
  - `blieb,/bliːp/,verb:` present.
  - `Pause,` present.
  - `Pause,/paoːzə/,noun:` present.
- `uv run pytest` -> `831 passed, 3 warnings`.

## Generated German Smoke Artifacts

- APKG: `.multilang/test-decks/de-full-normalized-v3/exports/9a72c2dc-1ec9-476d-a05c-3ff5ed429643.apkg`
- CSV: `.multilang/test-decks/de-full-normalized-v3/exports/9a72c2dc-1ec9-476d-a05c-3ff5ed429643.csv`
- TSV: `.multilang/test-decks/de-full-normalized-v3/exports/9a72c2dc-1ec9-476d-a05c-3ff5ed429643.tsv`
- Audit: `.multilang/test-decks/de-full-normalized-v3/audit/deck-audit.md`

## Notes

- The APKG audit reports only expected partial-deck issues because the smoke intentionally generated 3/3000 frequency cards.
- This fixes the observed German smoke cards; broader high-quality German POS coverage still depends on enriching the frequency assets or adding more curated overrides.
