# Quick Task 009 Plan: gerar assets frequency Danish

## Objective
Generate Danish (`da`) frequency assets and verify whether any currently supported language lacks frequency asset coverage.

## Context
- Current supported languages include `pt`, `es`, `en`, `fr`, `de`, `it`, `pl`, `tr`, `ro`, `ru`, `nl`, `da`, `nb`, `sv`, and `la` after quick task 001.
- Existing frequency asset directories cover `de`, `en`, `es`, `fr`, `it`, `la`, `nb`, `nl`, `pl`, `pt`, `ro`, `ru`, `sv`, and `tr`; `da` is the missing supported language directory.
- `scripts/build_frequency_assets.py` currently loops over all default supported languages, so it needs a single-language option to avoid rewriting unrelated assets.
- This is backend/data generation only; no rendered UI proof is required.

## no_ui_proof_rationale
This task generates CSV data assets and updates backend tests/scripts only. It does not make UI claims.

## Tasks

### Task 1: Add single-language frequency asset generation
<files>
- `scripts/build_frequency_assets.py`
</files>
<action>
Refactor the existing builder so it can build/check one language via a `--language` option while preserving default all-language behavior.
</action>
<done>
The script supports `--language da` for both generation and `--check` without rewriting unrelated language directories.
</done>
<verify>
- `uv run python scripts/build_frequency_assets.py --language en --check`
</verify>

### Task 2: Generate and validate Danish assets
<files>
- `assets/frequency/da/curated-v1.csv`
- `assets/frequency/da/rejections-v1.csv`
</files>
<action>
Generate Danish frequency assets from `wordfreq` using the existing deterministic filtering and schema.
</action>
<done>
Danish has 3000 curated rows split into three 1000-card levels plus a valid rejection CSV.
</done>
<verify>
- `uv run python scripts/build_frequency_assets.py --language da --check`
</verify>

### Task 3: Add focused asset coverage test and record evidence
<files>
- `tests/services/test_frequency_decks.py`
- `.planning/quick/009-gerar-assets-frequency-danish/009-SUMMARY.md`
- `.planning/quick/009-gerar-assets-frequency-danish/009-VERIFICATION.md`
- `.planning/quick/LOG.md`
</files>
<action>
Add a focused Danish asset validation test, run frequency tests, report missing-language audit result, and persist quick-task evidence.
</action>
<done>
Focused tests pass, quick summary/verifier files exist, and the log records the final status.
</done>
<verify>
- `uv run pytest tests/services/test_frequency_decks.py -q`
- `test -f .planning/quick/009-gerar-assets-frequency-danish/009-SUMMARY.md`
- `test -f .planning/quick/009-gerar-assets-frequency-danish/009-VERIFICATION.md`
</verify>
