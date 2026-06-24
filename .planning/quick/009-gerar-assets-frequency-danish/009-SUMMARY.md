# Quick Task 009 Summary: gerar assets frequency Danish

## Status
completed

## What Changed
- Added `--language` support to `scripts/build_frequency_assets.py` so one language can be generated or checked without rewriting unrelated asset directories.
- Generated Danish frequency assets from `wordfreq`:
  - `assets/frequency/da/curated-v1.csv`
  - `assets/frequency/da/rejections-v1.csv`
- Added a focused Danish frequency asset validation test.

## Missing-Language Audit
Before generation, `da` was the only supported language without a frequency asset directory.

After generation, the audit returned `missing=none`; every language in `DEFAULT_SUPPORTED_LANGUAGES` has both `curated-v1.csv` and `rejections-v1.csv`.

## Verification Commands
- `uv run python scripts/build_frequency_assets.py --language en --check` -> passed
- `uv run python scripts/build_frequency_assets.py --language da` -> passed
- `uv run python scripts/build_frequency_assets.py --language da --check` -> passed
- `uv run python scripts/build_frequency_assets.py --check` -> passed
- `uv run pytest tests/services/test_frequency_decks.py -q` -> passed, 17 tests
- `uv run python -c "from pathlib import Path; from multilang.settings import DEFAULT_SUPPORTED_LANGUAGES; base=Path('assets/frequency'); missing=[code for code in DEFAULT_SUPPORTED_LANGUAGES if not (base/code/'curated-v1.csv').is_file() or not (base/code/'rejections-v1.csv').is_file()]; print('missing=' + (','.join(missing) if missing else 'none'))"` -> `missing=none`

## Notes
- The generated Danish asset uses the same deterministic structural curation as the other `wordfreq`-seeded languages. It is structurally valid, but like the existing generated frequency assets, it is not a human-reviewed lexical curation pass.
