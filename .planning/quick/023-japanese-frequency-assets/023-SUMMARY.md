# Quick Task 023 Summary: Add Japanese Frequency Assets

## Status

Completed.

## Implemented

- Generated `assets/frequency/ja/curated-v1.csv` with 3000 Japanese rows from `wordfreq:ja`.
- Generated `assets/frequency/ja/rejections-v1.csv` with deterministic rejection rows.
- Removed the old `SupportedLanguage.JA` skip from all-supported frequency asset validation.
- Added focused Japanese frequency asset validation in `tests/services/test_frequency_decks.py`.

## Verification

- Passed: `uv run python scripts/build_frequency_assets.py --check --language ja`
- Passed: `uv run pytest tests/services/test_frequency_decks.py::test_all_supported_frequency_assets_validate tests/services/test_frequency_decks.py::test_japanese_frequency_assets_validate -q` (`2 passed`)

## Deferred

- Stage 3: Japanese local/Tatoeba/TTS fallback maps and Japanese-aware text validation.
- Stage 4: Japanese export routing to `Multilang::Japanese Card`.
