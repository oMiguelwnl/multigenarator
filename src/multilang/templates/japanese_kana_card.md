# Japanese Kana Card Template

Template used by the Japanese kana deck. It teaches the syllabary itself
(hiragana / katakana) through recognition plus mnemonics and stroke order.

The front shows a single kana glyph; the back reveals its romaji, a
stroke-order animation, a mnemonic picture and text, and audio. Content and
media are supplied by the importer at build time (see `japanese_kana_deck`),
so this template only lays out the fields.

## Fields

- SortIndex
- Script
- Kana
- Romaji
- Mnemonic
- Picture
- Strokes
- Gif
- Audio

## Front Template

```html
<div class="kanaCard kanaCard--front">
  <div class="kanaScript">{{Script}}</div>
  <div class="kanaGlyph jpFont">{{Kana}}</div>
  <div class="kanaHint">Lembre a leitura (romaji). Depois vire o card.</div>
</div>
```

## Back Template

```html
<div class="kanaCard kanaCard--back">
  <div class="kanaScript">{{Script}}</div>
  <div class="kanaGlyph jpFont">{{Kana}}</div>

  {{#Gif}}<div class="kanaStrokeAnim">{{Gif}}</div>{{/Gif}}

  <hr class="kanaDivider" />

  <div class="kanaRomaji">{{Romaji}}</div>
  <div class="kanaAudio">{{Audio}}</div>

  {{#Picture}}<div class="kanaPicture">{{Picture}}</div>{{/Picture}}

  {{#Strokes}}<div class="kanaStrokes">{{Strokes}}</div>{{/Strokes}}

  {{#Mnemonic}}<div class="kanaMnemonic">{{Mnemonic}}</div>{{/Mnemonic}}
</div>
```

## Styling (CSS)

```css
:root {
  --kana-max-width-card: 460px;
  --kana-font-size-glyph: 88px;
  --kana-font-size-romaji: 34px;
  --kana-font-size-mnemonic: 17px;

  --kana-color-page: #fdf6e3;
  --kana-color-card: #ffffff;
  --kana-color-text: #1f2430;
  --kana-color-accent: #524c9e;
  --kana-color-muted: #6b7280;
  --kana-color-divider: #e5e7eb;

  --kana-color-nightMode-page: #0b0716;
  --kana-color-nightMode-card: #171226;
  --kana-color-nightMode-text: #f3f1fb;
  --kana-color-nightMode-accent: #b8aef6;
  --kana-color-nightMode-muted: #9ca3af;
  --kana-color-nightMode-divider: #2c2a46;
}

* { box-sizing: border-box; }

body {
  margin: 0 !important;
  line-height: 1.4;
  overflow-wrap: break-word;
  overscroll-behavior: none;
  background: var(--kana-color-page);
}

.nightMode body,
body.nightMode { background: var(--kana-color-nightMode-page); }

.card {
  padding: 12px;
  background: var(--kana-color-page);
}

.nightMode .card { background: var(--kana-color-nightMode-page); }

.jpFont {
  font-family: "Yu Mincho", "YuMincho", "Hiragino Mincho ProN", "Noto Serif JP",
    "Noto Sans JP", "Segoe UI", serif;
}

.kanaCard {
  margin: 0 auto;
  max-width: var(--kana-max-width-card);
  width: 100%;
  background: var(--kana-color-card);
  color: var(--kana-color-text);
  border-radius: 12px;
  border-top: 4px solid var(--kana-color-accent);
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.12);
  padding: 24px 20px 28px;
  text-align: center;
  font-family: "Segoe UI", "Noto Sans JP", Arial, sans-serif;
}

.nightMode .kanaCard {
  background: var(--kana-color-nightMode-card);
  color: var(--kana-color-nightMode-text);
  border-top-color: var(--kana-color-nightMode-accent);
}

.kanaScript {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--kana-color-accent);
  margin-bottom: 6px;
}

.nightMode .kanaScript { color: var(--kana-color-nightMode-accent); }

.kanaGlyph {
  font-size: var(--kana-font-size-glyph);
  font-weight: 700;
  line-height: 1.1;
}

.kanaHint {
  margin-top: 16px;
  font-size: 13px;
  font-style: italic;
  color: var(--kana-color-muted);
}

.nightMode .kanaHint { color: var(--kana-color-nightMode-muted); }

.kanaDivider {
  border: 0;
  border-top: 1px solid var(--kana-color-divider);
  margin: 18px 0;
}

.nightMode .kanaDivider { border-top-color: var(--kana-color-nightMode-divider); }

.kanaRomaji {
  font-size: var(--kana-font-size-romaji);
  font-weight: 700;
  color: var(--kana-color-accent);
}

.nightMode .kanaRomaji { color: var(--kana-color-nightMode-accent); }

.kanaAudio { margin-top: 8px; }

.kanaStrokeAnim img,
.kanaPicture img,
.kanaStrokes img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}

.kanaStrokeAnim { margin-top: 12px; }
.kanaPicture { margin-top: 16px; }
.kanaStrokes { margin-top: 12px; }

.kanaMnemonic {
  margin-top: 16px;
  font-size: var(--kana-font-size-mnemonic);
  text-align: left;
  line-height: 1.5;
}

.kanaMnemonic code {
  font-weight: 600;
  color: var(--kana-color-accent);
}

.nightMode .kanaMnemonic code { color: var(--kana-color-nightMode-accent); }

.replay-button svg { width: 24px; height: 24px; }
.replay-button svg path { fill: var(--kana-color-accent); }
.nightMode .replay-button svg path { fill: var(--kana-color-nightMode-accent); }
.replay-button svg circle { fill: none; stroke: none; }
```
