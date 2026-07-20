# Quick Task 026 Summary: Japanese Furigana Generation

## Status

Completed.

## Implemented

- Added `fugashi>=1.3,<2.0` and `unidic-lite>=1.0,<2.0` to project dependencies and refreshed `uv.lock`.
- Added `src/multilang/services/japanese_furigana.py` with cached UniDic-backed tokenization, katakana-to-hiragana reading conversion, and Anki-native `漢字[かな]` formatting.
- Generated contextual `Word Reading` and `Sentence Furigana` values during Japanese frequency export assembly.
- Added optional `word_reading` and `sentence_furigana` values to `ExportCardRow` while preserving existing non-Japanese field behavior.
- Preserved natural Japanese sentence spacing, e.g. `学校[がっこう]に行[い]く。` instead of inserting artificial spaces.
- Covered kanji tokens, okurigana, numbers, kana-only text, the iteration mark `々`, and `ヶ`/`ヵ` counter-style forms in focused tests.

## Verification

- Passed: `uv run python -c "import fugashi, unidic_lite"`
- Passed: `uv run pytest tests/services/test_japanese_furigana.py -q` (`6 passed`)
- Passed: `uv run pytest tests/services/test_japanese_furigana.py tests/services/test_assemble_export_cards.py tests/services/test_export_anki_package.py` (`48 passed`)
- Passed: `uv run pytest tests/services/test_japanese_furigana.py tests/services/test_assemble_export_cards.py tests/services/test_export_anki_package.py tests/services/test_card_template_loader.py tests/services/test_japanese_frequency_deck.py tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py tests/services/test_text_validation.py tests/services/test_provider_text_adapters.py tests/services/test_frequency_decks.py tests/domain/test_jobs.py tests/test_settings.py -q` (`177 passed`)
- Passed: `uv run python scripts/build_frequency_assets.py --check --language ja`

## Deferred

- No UI proof required; this task changes backend export data only.
