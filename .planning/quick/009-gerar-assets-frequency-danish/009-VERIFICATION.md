# Quick Task 009 Verification: gerar assets frequency Danish

## Verdict
passed

## Goal Check
Danish (`da`) now has committed frequency assets, and no currently supported language is missing required frequency asset files.

## Evidence
- `assets/frequency/da/curated-v1.csv` exists with 3000 rows.
- `assets/frequency/da/rejections-v1.csv` exists and validates against the rejection schema.
- Danish curated rows are split into three 1000-row levels.
- `scripts/build_frequency_assets.py --language da --check` validates only Danish successfully.
- Full supported-language asset audit reports `missing=none`.

## Commands Run
- `uv run python scripts/build_frequency_assets.py --language en --check` -> passed
- `uv run python scripts/build_frequency_assets.py --language da` -> passed
- `uv run python scripts/build_frequency_assets.py --language da --check` -> passed
- `uv run python scripts/build_frequency_assets.py --check` -> passed
- `uv run pytest tests/services/test_frequency_decks.py -q` -> passed, 17 tests
- Missing asset audit command -> `missing=none`

## Residual Risk
- Danish assets are deterministic `wordfreq` seeds and have not received human lexical review beyond structural filtering.
- The broad full test suite was not run because this quick task only changed frequency asset generation and the codebase map documents known broad-suite drift.
