# Quick Task 002 Summary: Remover Campos Latin Export

## Status

Completed.

## What Changed

- Removed `Translation`, `Lemma`, and `Source` from the Latin MVP export field contract in `src/multilang/services/latin_export.py`.
- Removed those fields from `LatinExportRow`, ordered row mappings, APKG note model fields, CSV/TSV headers, and the Anki back template.
- Preserved `Sentence Translation`, `Gramatica`, `word_audio`, `sentence_audio`, and blank `Image`.
- Kept translation/source/audio review gates and asset loaders intact; no provider, runtime, source-pack, translation asset, audio manifest, roadmap, or spec behavior was changed.
- Updated focused service and integration evidence tests for the new Latin field order.

## New Latin Field Order

1. `SortIndex`
2. `Latin Word`
3. `Latin Sentence`
4. `Sentence Translation`
5. `Gramatica`
6. `word_audio`
7. `sentence_audio`
8. `Image`

## Verification

- `python -m pytest tests/services/test_latin_export.py -q` passed: `11 passed`.
- `python -m pytest tests/services/test_latin_export.py tests/integration/test_v20_latin_export_evidence.py tests/integration/test_v20_existing_modes_regression_evidence.py -q` passed: `18 passed`.
- `python -m pytest tests/integration/test_v20_final_milestone_evidence.py -q` passed: `3 passed`.

## Notes

- The planner and checker delegates failed with an internal tool storage error (`session_message.seq`), so the plan/check were completed manually before user approval.
- The change intentionally alters the public Latin Anki note field contract because the user confirmed the fields should not exist anywhere in generation/export.
