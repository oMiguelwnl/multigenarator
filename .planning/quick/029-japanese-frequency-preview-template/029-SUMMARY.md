# Quick Task 029 Summary: Japanese Frequency Preview Template

## Status

Completed.

## Implemented

- Replaced the Japanese frequency template with the `ja_freq_v3_preview.html` visual structure.
- Preserved the existing Japanese frequency field contract:
  `SortIndex`, `Target Word`, `Word Reading`, `Definition`, `Sentence`, `Sentence Furigana`, `Sentence Translation`, `word_audio`, `sentence_audio`, `Image`.
- Front/back now use preview-based classes including `customCard`, `cardBack`, `targetWordContainer`, `targetWord`, `jPlain`, `jReading`, `furiganaToggle`, `definitionsList`, `exampleSentenceLine`, `sentenceTranslation`, and `jpLinks`.
- Kept Anki-native `{{furigana:Word Reading}}` and `{{furigana:Sentence Furigana}}` rendering.
- Regenerated Japanese smoke APKGs so the frequency packages embed the preview-based template.

## Verification

- Passed: `uv run pytest tests/services/test_card_template_loader.py::test_project_japanese_template_uses_japanese_fields_and_furigana_filter tests/services/test_export_anki_package.py::test_build_japanese_frequency_model_uses_japanese_note_type_and_template tests/services/test_japanese_frequency_deck.py::test_build_japanese_model_uses_template_and_field_order -q` (`3 passed`)
- Passed: `uv run pytest tests/services/test_japanese_frequency_deck.py tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py tests/services/test_japanese_furigana.py tests/services/test_assemble_export_cards.py::test_assemble_export_cards_builds_japanese_row_without_ipa tests/services/test_export_anki_package.py::test_build_japanese_frequency_model_uses_japanese_note_type_and_template tests/services/test_export_anki_package.py::test_build_multilang_note_maps_japanese_frequency_fields tests/services/test_card_template_loader.py::test_project_japanese_template_uses_japanese_fields_and_furigana_filter -q` (`28 passed`)
- Passed: `uv run python scripts/build_frequency_assets.py --check --language ja`
- Passed: APKG embedded-template inspection for `japanese-frequency-smoke.apkg` and `japanese-dynamic-frequency-smoke.apkg` found `customCard cardBack jpFront`, `customCard cardBack jpBack`, `furiganaToggle`, `definitionsList`, `exampleSentenceLine`, `jpLinks`, `jisho.org`, and `weblio.jp`.

## Generated Artifacts Refreshed

- `exports/japanese_validation/japanese-frequency-smoke.apkg`
- `exports/japanese_validation/japanese-dynamic-frequency-smoke.apkg`
- `exports/japanese_validation/japanese-kana-generated-smoke.apkg`

## Deferred

- Live provider generation/audio quality review remains separate from this template update.
