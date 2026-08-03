# Quick Task 031 Summary: Japanese Definition English Format

## Status

Completed.

## Implemented

- Added explicit provider prompt rules for Japanese definitions:
  - use English part-of-speech labels;
  - do not use Japanese labels such as `名詞`, `動詞`, `形容詞`, or `副詞`;
  - use examples such as `noun: father`, `verb: to eat`, `adjective: cold`, and `particle: topic marker`;
  - keep the meaning after the colon in English.
- Enforced the English definition-label template only for Japanese deck assembly.
- Preserved existing non-Japanese behavior, including accepted Portuguese labels in current tests.
- Added tests for the Japanese provider prompt and export-time rejection of `名詞: ...`.

## Verification

- Passed: `uv run pytest tests/services/test_provider_text_adapters.py::test_litellm_definition_prompt_for_japanese_requires_english_format tests/services/test_assemble_export_cards.py::test_assemble_export_cards_rejects_non_english_definition_label -q` (`2 passed`)
- Passed: `uv run pytest tests/services/test_provider_text_adapters.py tests/services/test_assemble_export_cards.py tests/services/test_export_anki_package.py::test_build_japanese_frequency_model_uses_japanese_note_type_and_template tests/services/test_japanese_frequency_deck.py::test_build_japanese_model_uses_template_and_field_order tests/services/test_card_template_loader.py::test_project_japanese_template_uses_japanese_fields_and_furigana_filter -q` (`37 passed`)
- Passed: `git diff --check`

## Deferred

- None.
