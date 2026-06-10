# Quick Task 002 Verification: Remover Campos Latin Export

## Status

passed

## Goal Check

Task goal: remove `Translation`, `Lemma`, and `Source` from the Latin card/export generation so those fields do not exist.

Result: achieved.

## Evidence

- `LATIN_EXPORT_FIELD_NAMES` no longer contains `Translation`, `Lemma`, or `Source`.
- `LatinExportRow` no longer has `translation`, `lemma`, or `source` attributes.
- `ordered_field_mapping()` no longer emits `Translation`, `Lemma`, or `Source`.
- `build_latin_anki_model()` no longer defines those fields or renders `{{Translation}}`, `{{Lemma}}`, or `{{Source}}`.
- CSV and TSV headers are derived from the new field tuple and exclude those exact field names.
- APKG model inspection tests verify the new model field list.
- `Sentence Translation` remains intentionally present.

## Commands Run

- `python -m pytest tests/services/test_latin_export.py -q` — passed: `11 passed`.
- `python -m pytest tests/services/test_latin_export.py tests/integration/test_v20_latin_export_evidence.py tests/integration/test_v20_existing_modes_regression_evidence.py -q` — passed: `18 passed`.
- `python -m pytest tests/integration/test_v20_final_milestone_evidence.py -q` — passed: `3 passed`.

## Scope Check

- No modern-language export files were changed.
- No source-pack, translation JSON, curation JSON, audio manifest, provider adapter, runtime, ROADMAP, or SPEC files were changed.
- This verification is quick-scoped and does not claim the known-red broad full suite is repaired.
