# Quick Task Summary: Escurecer Templates de Japones e Latim

## Result

Updated the Japanese frequency, Japanese Kana, and Latin MVP Anki templates to render in dark mode by default instead of relying on Anki `nightMode`.

## Changed Files

- `src/multilang/templates/latin_mvp_card.md`
- `src/multilang/templates/japanese_card.md`
- `src/multilang/templates/japanese_kana_card.md`
- `tests/services/test_card_template_loader.py`
- `templates_preview.html`

## Notes

- Latin and Japanese frequency now use dark card/background/text defaults matching their existing night-mode palette.
- Japanese Kana now uses its night-mode page/card/text/accent palette as the default palette.
- `templates_preview.html` was regenerated from the current templates.

## Verification

```bash
uv run pytest tests/services/test_card_template_loader.py tests/test_runtime_templates.py -q
```

Result: `28 passed`.

```bash
uv run pytest tests/services/test_latin_export.py -q
```

Result: `11 passed`.

```bash
uv run pytest tests/services/test_japanese_frequency_deck.py tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py -q
```

Result: `18 passed`.

Static validation result: `ok dark_defaults=true templates=7 iframes=14`.
