# Quick Task 028 Summary: Japanese Deck Smoke Validation

## Status

Completed.

## Generated Artifacts

- `exports/japanese_validation/japanese-frequency-smoke.apkg`
  - Cards: 12
  - Note type: `Multilang::Japanese Card`
  - Media files: 24
  - Sound references: 24
  - First inspected reading: `何[なに]`
- `exports/japanese_validation/japanese-kana-generated-smoke.apkg`
  - Cards: 208
  - Note type: `Multilang::Japanese Kana`
  - Hiragana cards: 104
  - Katakana cards: 104
  - Media files: 208
  - Sound references: 208
- `exports/japanese_validation/japanese-dynamic-frequency-smoke.apkg`
  - Cards: 3
  - Note type: `Multilang::Japanese Card`
  - Media files: 6
  - Sound references: 6
  - First inspected dynamic furigana: `学校[がっこう]に行[い]く。`

## Verification

- Passed: all generated APKG files were readable through `read_apkg_cards()` and contained matching media manifests/sound references.
- Passed: `uv run python scripts/build_frequency_assets.py --check --language ja`
- Passed: `uv run pytest tests/services/test_japanese_frequency_deck.py tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py tests/services/test_japanese_furigana.py tests/services/test_assemble_export_cards.py::test_assemble_export_cards_builds_japanese_row_without_ipa tests/services/test_export_anki_package.py::test_build_japanese_frequency_model_uses_japanese_note_type_and_template tests/services/test_export_anki_package.py::test_build_multilang_note_maps_japanese_frequency_fields -q` (`27 passed`)

## Notes

- Audio bytes in these smoke artifacts are deterministic local fake MP3 markers, not live Azure TTS output.
- The dynamic frequency smoke package validates the main Japanese export field/template/furigana path, but it is intentionally a 3-card smoke sample rather than a full provider-generated 3000-card deck.
