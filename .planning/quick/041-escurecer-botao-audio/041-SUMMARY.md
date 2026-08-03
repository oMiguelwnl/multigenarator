# Quick Task Summary: Escurecer Botao de Audio

## Result

Removed white audio-button backgrounds from the dark templates and regenerated `templates_preview.html`.

## Changed Files

- `src/multilang/templates/latin_mvp_card.md`
- `src/multilang/templates/japanese_card.md`
- `src/multilang/templates/japanese_kana_card.md`
- `src/multilang/templates/highlight_card.md`
- `tests/services/test_card_template_loader.py`
- `templates_preview.html`

## Notes

- Latin, Japanese frequency, and Kana now define `.replay-button` directly with `background: transparent`, `border: 0`, and no inherited box shadow.
- Highlight no longer uses the explicit white `#f8f8f2` audio button; it now uses a dark green background with a green play triangle.

## Verification

```bash
uv run pytest tests/services/test_card_template_loader.py tests/test_runtime_templates.py -q
```

Result: `29 passed`.

```bash
uv run pytest tests/services/test_latin_export.py tests/services/test_japanese_frequency_deck.py tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py -q
```

Result: `29 passed`.

Static preview validation: `ok preview_audio_buttons_dark=true templates=7 iframes=14`.
