# Quick Task 019 Summary: Add Czech

## Status

Completed.

## Changes

- Added Czech (`cs`) to `SupportedLanguage`, typed settings defaults, runtime deck naming, language identification, provider text/pronunciation language maps, DeepL target mapping, Tatoeba routing, text validation markers, highlight stopwords, and local deterministic sentence/translation templates.
- Added Czech support to deterministic pronunciation library resolver maps and function-word POS inference.
- Added Czech Azure voice routing with `cs-CZ-VlastaNeural` preferred and `cs-CZ-AntoninNeural` alternate, plus ElevenLabs and Google Translate fallback TTS routing.
- Generated `assets/frequency/cs/curated-v1.csv` and `assets/frequency/cs/rejections-v1.csv` from the existing `wordfreq` asset builder.
- Added focused regression tests for Czech contract parsing, settings defaults, local text generation, TTS selection, frequency assets, and POS inference.

## Verification

- Passed map/import checks for `cs` contracts, provider maps, pronunciation resolvers, POS inference, Tatoeba code, validation markers, and stopwords.
- Passed focused pytest selection: `21 passed in 0.98s`.
- Passed broader affected test-file sweep: `125 passed in 3.22s`.
- Passed `uv run python scripts/build_frequency_assets.py --check --language cs`.
- Passed `uv run python scripts/build_frequency_assets.py --check`.
- Passed `git diff --check`; Git emitted only LF/CRLF normalization warnings on Windows.

## Notes

- Planner/checker templates referenced by the quick workflow are absent, so plan-check assurance is reduced to the persisted quick plan and focused verification above.
- Full test suite was not run; `.planning/codebase/CONCERNS.md` documents known broad-suite drift, so verification was limited to the language-support surfaces touched by this task.
- During verification, the Czech POS map initially had a diacritic-normalization collision between `ze` and `že`; `ze` was removed from the preposition inference map to keep POS inference deterministic.
