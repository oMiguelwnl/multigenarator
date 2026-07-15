# Quick Task 021 Summary: Add Greek With Phonetic Deck

## Status

Completed.

## Changes

- Added Modern Greek (`el`) to `SupportedLanguage`, typed settings defaults, runtime deck naming, provider text/pronunciation maps, DeepL target mapping, Tatoeba routing, corpus language-id support, text validation markers, highlight stopwords, function-word POS inference, and deterministic local text templates.
- Added Greek audio routing for Azure (`el-GR-AthinaNeural`, alternate `el-GR-NestorasNeural`), ElevenLabs (`el-GR`), and Google Translate TTS (`el`).
- Generated `assets/frequency/el/curated-v1.csv` and `assets/frequency/el/rejections-v1.csv` with 3000 curated rows from `wordfreq:el`.
- Added a dedicated Greek introductory phoneme deck using the existing phoneme field contract/template, plus `export-greek-phonemes` CLI support.
- Added focused regression tests for Greek parsing, settings, providers, frequency assets, local text, POS inference, phoneme model/export, and CLI export.

## Verification

- Passed Greek contract/provider import checks.
- Passed `uv run python scripts/build_frequency_assets.py --check --language el`.
- Passed `uv run python scripts/build_frequency_assets.py --check`.
- Passed `uv run pytest tests/services/test_frequency_decks.py -q` (`22 passed`).
- Passed affected focused sweep: `129 passed in 3.81s`.
- Passed CLI smoke: `uv run python -m multilang.cli export-greek-phonemes --output-path .multilang/exports/greek-phonemes-smoke.apkg --limit 2`.

## Notes

- Azure and DeepL official docs were checked before choosing `el-GR` voices and DeepL `EL`.
- Full repository test suite was not run; `.planning/codebase/CONCERNS.md` documents known broad-suite drift.
- Existing Croatian quick-task changes were already present in the worktree and were preserved.
