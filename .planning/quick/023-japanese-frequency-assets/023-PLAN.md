# Quick Task 023 Plan: Add Japanese Frequency Assets

## Objective

Add Japanese (`ja`) curated frequency assets using the existing `wordfreq` asset builder and enable frequency-asset validation coverage for Japanese.

Approach context: This is stage 2 of the split Japanese pipeline work. Stage 1 already added `ja` to default settings and provider text routing. This task is intentionally limited to committed frequency assets and validation tests; Japanese text validation and export routing remain separate follow-ups.

No UI proof rationale: This task changes data assets and backend tests only; it has no rendered UI surface.

## Task 1: Build And Validate Japanese Frequency Assets

<files>
- `assets/frequency/ja/curated-v1.csv`
- `assets/frequency/ja/rejections-v1.csv`
- `tests/services/test_frequency_decks.py`
</files>

<action>
- Generate `assets/frequency/ja/curated-v1.csv` and `assets/frequency/ja/rejections-v1.csv` with the existing `scripts/build_frequency_assets.py --language ja` command.
- Stop treating Japanese as an isolated exception in the all-supported frequency asset validation test now that the curated asset exists.
- Add a focused Japanese asset validation test mirroring recent language additions.
</action>

<done>
- Japanese has exactly 3000 curated rows split into 3 levels of 1000 rows.
- Japanese rejection rows exist and validate against the shared rejection schema.
- `scripts/build_frequency_assets.py --check --language ja` passes.
</done>

<verify>
- `uv run python scripts/build_frequency_assets.py --check --language ja`
- `uv run pytest tests/services/test_frequency_decks.py::test_all_supported_frequency_assets_validate tests/services/test_frequency_decks.py::test_japanese_frequency_assets_validate -q`
</verify>

## Deferred Follow-Up Tasks

- Stage 3: Japanese local/Tatoeba/TTS fallback maps and Japanese-aware text validation.
- Stage 4: Japanese export routing to `Multilang::Japanese Card`.
