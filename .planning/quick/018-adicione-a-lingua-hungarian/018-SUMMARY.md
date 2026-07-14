# Quick Task 018 Summary: Add Hungarian

## Status

Completed.

## Changes

- Added Hungarian (`hu`) to `SupportedLanguage`, typed settings defaults, runtime deck naming, language identification, provider text/pronunciation language maps, DeepL target mapping, Tatoeba routing, text validation markers, highlight stopwords, and local deterministic sentence/translation templates.
- Added Hungarian support to deterministic pronunciation library resolver maps and function-word POS inference.
- Added Hungarian Azure voice routing with `hu-HU-NoemiNeural` preferred and `hu-HU-TamasNeural` alternate, plus ElevenLabs and Google Translate fallback TTS routing.
- Generated `assets/frequency/hu/curated-v1.csv` and `assets/frequency/hu/rejections-v1.csv` from the existing `wordfreq` asset builder.
- Added focused regression tests for Hungarian contract parsing, settings defaults, local text generation, TTS selection, frequency assets, and POS inference.

## Verification

- Passed map/import checks for `hu` contracts, provider maps, pronunciation resolvers, POS inference, Tatoeba code, validation markers, and stopwords.
- Passed focused pytest selection: `20 passed in 1.26s`.
- Passed `uv run python scripts/build_frequency_assets.py --check`.
- Passed `git diff --check`; Git emitted only CRLF normalization warnings on Windows.

## Notes

- Planner/checker templates referenced by the quick workflow are absent, so plan-check assurance is reduced to the persisted quick plan and focused verification above.
- Full test suite was not run; verification was limited to the language-support surfaces touched by this task.
