# Quick Task Summary: Corrigir Fundo do Card e Audio

## Result

Fixed the remaining white backgrounds by applying dark canvas backgrounds and stronger audio-button overrides.

## Changed Files

- `src/multilang/templates/latin_mvp_card.md`
- `src/multilang/templates/japanese_card.md`
- `src/multilang/templates/japanese_kana_card.md`
- `src/multilang/templates/highlight_card.md`
- `tests/services/test_card_template_loader.py`
- `templates_preview.html`

## Fix Details

- Added `--color-page-background: #0a1628` to Latin and Japanese frequency templates.
- Applied dark background to `body`, `body.card`, `body.nightMode`, and `.card` for Latin/Japanese.
- Added the same canvas coverage to Kana using `--kana-color-page`.
- Strengthened audio-button CSS with `background: transparent !important`, `background-color: transparent !important`, `border: 0 !important`, and `box-shadow: none !important`.
- Forced SVG audio circles to `fill: transparent !important` and `stroke: none !important`.
- Kept Highlight audio button dark with `#1f2a24 !important`.

## Verification

```bash
uv run pytest tests/services/test_card_template_loader.py tests/test_runtime_templates.py -q
```

Result: `30 passed`.

```bash
uv run pytest tests/services/test_latin_export.py tests/services/test_japanese_frequency_deck.py tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py -q
```

Result: `29 passed`.

Static preview validation: `ok preview_canvas_and_audio_dark=true iframes=14`.
