---
phase: 08-card-quality-refresh
plan: 03
status: complete
completed_at: "2026-05-02T19:10:43Z"
key_files:
  - src/multilang/db/models.py
  - src/multilang/repositories/lexical_repository.py
  - src/multilang/services/assemble_export_cards.py
  - alembic/versions/20260502_08_spoken_form.py
  - tests/repositories/test_lexical_repository.py
  - tests/services/test_assemble_export_cards.py
---

# Phase 08 Plan 03: Spoken Form Persistence and Export Summary

AI-generated spoken forms now persist with lexical candidates and export as `/ipa/ (spoken-form)` for generated cards.

## What Changed

- Added nullable `spoken_form` storage to the lexical candidate ORM model and Alembic migration.
- Round-tripped `spoken_form` through `LexicalRepository`.
- Changed export assembly to require both IPA and spoken form, escaping both before rendering.

## Validation

- `uv run pytest tests/services/test_assemble_export_cards.py tests/repositories/test_lexical_repository.py -x` — passed.

## Deviations from Plan

- Commits were skipped because the user explicitly requested no commits unless explicitly requested.

## Self-Check: PASSED
