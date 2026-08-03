# Quick Task Summary: Preview Todos os Templates

## Result

Created `templates_preview.html`, a local HTML preview page for all Anki card templates in `src/multilang/templates/`.

## Coverage

- `normal_card.md`
- `highlight_card.md`
- `latin_mvp_card.md`
- `russian_phoneme_card.md`
- `mandarin_card.md`
- `japanese_card.md`
- `japanese_kana_card.md`

Each template is shown as front and back, using isolated iframes so template CSS does not bleed between previews.

## Verification Command

```bash
python - <<'PY'
from pathlib import Path
html = Path('templates_preview.html').read_text(encoding='utf-8')
expected = [
    'normal_card.md',
    'highlight_card.md',
    'latin_mvp_card.md',
    'russian_phoneme_card.md',
    'mandarin_card.md',
    'japanese_card.md',
    'japanese_kana_card.md',
]
missing = [name for name in expected if name not in html]
iframe_count = html.count('<iframe ')
if missing:
    raise SystemExit(f'missing templates: {missing}')
if iframe_count != 14:
    raise SystemExit(f'expected 14 iframes, found {iframe_count}')
print('ok templates=7 iframes=14 path=templates_preview.html')
PY
```

Result: `ok templates=7 iframes=14 path=templates_preview.html`
