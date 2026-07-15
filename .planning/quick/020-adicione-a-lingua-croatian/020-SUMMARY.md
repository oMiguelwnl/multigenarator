# Quick Task 020 Summary: Add Croatian

## Status

Completed.

## Changes

- Added Croatian (`hr`) to `SupportedLanguage`, typed settings defaults, runtime deck naming, language identification, provider text/pronunciation language maps, DeepL target mapping, Tatoeba routing, text validation markers, highlight stopwords, and local deterministic sentence/translation templates.
- Added Croatian support to deterministic pronunciation library resolver maps and function-word POS inference.
- Added Croatian Azure voice routing with `hr-HR-GabrijelaNeural` preferred and `hr-HR-SreckoNeural` alternate, plus ElevenLabs and Google Translate fallback TTS routing.
- Generated `assets/frequency/hr/curated-v1.csv` and `assets/frequency/hr/rejections-v1.csv` with 3000 curated rows. `wordfreq` uses the nearest corpus code `sh` for Croatian, so the builder now records Croatian asset provenance as `wordfreq:sh` explicitly.
- Added focused regression tests for Croatian contract parsing, settings defaults, local text generation, TTS selection, frequency assets, and POS inference.

## Verification

- Passed map/import checks for `hr` contracts, provider maps, pronunciation resolvers, POS inference, Tatoeba code, validation markers, and stopwords.
- Passed focused affected test-file sweep: `178 passed in 3.39s`.
- Passed `uv run python scripts/build_frequency_assets.py --check --language hr`.
- Passed `uv run python scripts/build_frequency_assets.py --check`.
- Passed `git diff --check`; Git emitted only LF/CRLF normalization warnings on Windows.

## Notes

- DeepL documentation was checked during execution and confirms `HR` / Croatian is a supported translation target.
- Planner/checker templates referenced by the quick workflow are absent, so plan-check assurance is reduced to the persisted quick plan and focused verification above.
- Full test suite was not run; `.planning/codebase/CONCERNS.md` documents known broad-suite drift, so verification was limited to the language-support surfaces touched by this task.
