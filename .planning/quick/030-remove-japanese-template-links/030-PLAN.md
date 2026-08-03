# Quick Task 030 Plan: Remove Japanese Template Links

## Objective

Remove the final Jisho/Weblio link block from the Japanese frequency template while preserving the preview-based card structure and field contract.

No UI proof rationale: this task changes an Anki template and validates template/APKG structure through tests and package inspection.

## Task 1: Remove Final Link Block

<files>
- `src/multilang/templates/japanese_card.md`
</files>

<action>
- Remove the final `jpLinks` blocks from front and back templates.
- Remove unused `jpLinks` CSS.
- Keep all Japanese fields and furigana rendering unchanged.
</action>

<verify>
- Template references still validate against `JAPANESE_EXPORT_CARD_FIELD_NAMES`.
</verify>

## Task 2: Update Tests And Smoke Artifact

<files>
- `tests/services/test_card_template_loader.py`
- `tests/services/test_japanese_frequency_deck.py`
- `exports/japanese_validation/japanese-frequency-smoke.apkg`
</files>

<action>
- Update tests to assert Jisho/Weblio links are absent from the Japanese frequency template.
- Regenerate the Japanese frequency smoke APKG with the updated template.
</action>

<verify>
- `uv run pytest tests/services/test_card_template_loader.py::test_project_japanese_template_uses_japanese_fields_and_furigana_filter tests/services/test_japanese_frequency_deck.py::test_build_japanese_model_uses_template_and_field_order tests/services/test_export_anki_package.py::test_build_japanese_frequency_model_uses_japanese_note_type_and_template -q`
