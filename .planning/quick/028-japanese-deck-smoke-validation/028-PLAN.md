# Quick Task 028 Plan: Japanese Deck Smoke Validation

## Objective

Generate and inspect Japanese deck artifacts locally to validate the current Japanese frequency, furigana, and kana deck surfaces without requiring live provider credentials.

No UI proof rationale: this task validates backend/export artifacts and Anki package structure, not rendered UI.

## Task 1: Export Local Japanese APKG Samples

<files>
- `exports/japanese_validation/`
</files>

<action>
- Export the curated Japanese frequency sample deck with deterministic local fake MP3 media.
- Export the fully generated kana deck with deterministic local fake MP3 media.
</action>

<verify>
- Confirm both APKG files exist and contain `collection.anki2`.
</verify>

## Task 2: Audit Japanese Package Structure

<files>
- `exports/japanese_validation/`
</files>

<action>
- Read both generated APKG files.
- Confirm Japanese frequency deck card count, field count, furigana fields, and media references.
- Confirm kana deck card count and Hiragana/Katakana split.
</action>

<verify>
- Record package names, card counts, and key inspected fields in the summary.
</verify>

## Task 3: Run Focused Regression Checks

<files>
- Existing tests only.
</files>

<action>
- Run focused Japanese tests and frequency asset validation.
</action>

<verify>
- `uv run python scripts/build_frequency_assets.py --check --language ja`
- `uv run pytest tests/services/test_japanese_frequency_deck.py tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py tests/services/test_japanese_furigana.py tests/services/test_assemble_export_cards.py::test_assemble_export_cards_builds_japanese_row_without_ipa tests/services/test_export_anki_package.py::test_build_japanese_frequency_model_uses_japanese_note_type_and_template tests/services/test_export_anki_package.py::test_build_multilang_note_maps_japanese_frequency_fields -q`
</verify>
