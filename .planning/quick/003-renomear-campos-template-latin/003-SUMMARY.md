# Quick Task 003 Summary: Renomear Campos e Template Latin

## Status

Completed with verification limitation.

## What Changed

- Renamed Latin export field names in `src/multilang/domain/exporting.py`:
  - `Latin Word` -> `Word`
  - `Latin Sentence` -> `Sentence`
  - `Gramatica` -> `Grammar`
- Updated `src/multilang/services/latin_export.py` so `LatinExportRow.ordered_field_mapping()` emits the renamed fields.
- Updated `src/multilang/templates/latin_mvp_card.md` to reference `{{Word}}`, `{{Sentence}}`, and `{{Grammar}}` while preserving the frequency-card visual structure/classes.
- Updated focused tests in:
  - `tests/services/test_card_template_loader.py`
  - `tests/services/test_latin_export.py`
  - `tests/integration/test_v20_existing_modes_regression_evidence.py`

## New Latin Field Order

1. `SortIndex`
2. `Word`
3. `Sentence`
4. `Sentence Translation`
5. `Grammar`
6. `word_audio`
7. `sentence_audio`
8. `Image`

## Scope Guardrails

- eSpeak NG was not removed.
- Audio provider code and manifests were not changed.
- Source-pack, translation, review, and audio assets were not changed.
- Modern-language export contracts were not changed.

## Verification Run

- `python -m pytest tests/services/test_card_template_loader.py tests/integration/test_v20_existing_modes_regression_evidence.py -q` passed: `22 passed`.
- `python -m pytest tests/services/test_latin_export.py -q -k "field_order or row_mapping or rejects_nonblank_image or anki_model"` passed: `4 passed, 7 deselected`.
- Source grep for old Latin template/export references found no matches under `src/`.

## Verification Limitation

`python -m pytest tests/services/test_latin_export.py -q` could not complete because this worktree does not contain the committed Latin MVP asset files under `data/latin_mvp/`, including `latin-mvp-50-v1.json`, `latin-mvp-50-v1-pt.json`, and `latin-mvp-50-v1-curation.json`. The failures occurred before exercising the renamed-field assertions that require committed assets.
