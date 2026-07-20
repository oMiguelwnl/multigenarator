# Quick Task 030 Summary: Remove Japanese Template Links

## Status

Completed.

## Implemented

- Removed the final Jisho/Weblio link blocks from the Japanese frequency front and back templates.
- Removed unused `jpLinks` CSS from `src/multilang/templates/japanese_card.md`.
- Kept all Japanese frequency fields unchanged.
- Regenerated `exports/japanese_validation/japanese-frequency-smoke.apkg` with the updated template.

## Verification

- Passed: `uv run pytest tests/services/test_card_template_loader.py::test_project_japanese_template_uses_japanese_fields_and_furigana_filter tests/services/test_japanese_frequency_deck.py::test_build_japanese_model_uses_template_and_field_order tests/services/test_export_anki_package.py::test_build_japanese_frequency_model_uses_japanese_note_type_and_template -q` (`3 passed`)
- Passed: `uv run python scripts/build_frequency_assets.py --check --language ja`
- Passed: embedded APKG model inspection for `exports/japanese_validation/japanese-frequency-smoke.apkg` confirmed `jisho.org`, `weblio.jp`, and `jpLinks` are absent.

## Deferred

- None.
