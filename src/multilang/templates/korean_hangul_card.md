# Korean Hangul Card Template

Standalone template for Korean Hangul foundation notes. It lays out frozen
learner fields only; curriculum evidence remains stored on the note and hidden.

## Fields

- SortIndex
- Category
- JamoOrBlock
- ReadingOrName
- Sound
- Mnemonic
- Picture
- Strokes
- Gif
- Audio
- TargetConceptId
- PrerequisiteConceptIds
- ObservedConceptIds
- UnknownConceptIds
- IPlusOnePolicy

## Front Template

```html
<div class="hangulCard hangulCard--front">
  <div class="hangulCategory">{{Category}}</div>
  <div class="hangulGlyph koFont">{{JamoOrBlock}}</div>
  <div class="hangulHint">Lembre a leitura ou o nome. Depois vire o card.</div>
</div>
```

## Back Template

```html
<div class="hangulCard hangulCard--back">
  <div class="hangulCategory">{{Category}}</div>
  <div class="hangulGlyph koFont">{{JamoOrBlock}}</div>

  {{#Gif}}<div class="hangulAnimation">{{Gif}}</div>{{/Gif}}

  <hr class="hangulDivider" />

  {{#ReadingOrName}}
  <div class="hangulReading">
    <div class="hangulLabel">Leitura ou nome</div>
    <div class="hangulReadingValue koFont">{{ReadingOrName}}</div>
  </div>
  {{/ReadingOrName}}

  {{#Sound}}
  <div class="hangulSound">
    <div class="hangulLabel">Som</div>
    <div class="hangulSoundValue">{{Sound}}</div>
  </div>
  {{/Sound}}

  {{#Audio}}<div class="hangulAudio">{{Audio}}</div>{{/Audio}}

  {{#Picture}}<div class="hangulPicture">{{Picture}}</div>{{/Picture}}

  {{#Strokes}}<div class="hangulStrokes">{{Strokes}}</div>{{/Strokes}}

  {{#Mnemonic}}
  <div class="hangulMnemonic">
    <div class="hangulLabel">Mnemônico</div>
    <div>{{Mnemonic}}</div>
  </div>
  {{/Mnemonic}}
</div>
```

## Styling (CSS)

```css
:root {
  --hangul-max-width-card: 460px;
  --hangul-font-size-glyph: 88px;
  --hangul-font-size-reading: 32px;
  --hangul-font-size-mnemonic: 17px;

  --hangul-color-page: #0b0716;
  --hangul-color-card: #171226;
  --hangul-color-text: #f3f1fb;
  --hangul-color-accent: #b8aef6;
  --hangul-color-muted: #9ca3af;
  --hangul-color-divider: #2c2a46;
}

* { box-sizing: border-box; }

body {
  margin: 0 !important;
  line-height: 1.4;
  overflow-wrap: break-word;
  overscroll-behavior: none;
}

body,
body.card,
body.nightMode,
.card {
  background: var(--hangul-color-page);
  color: var(--hangul-color-text);
}

.card { padding: 12px; }

.koFont,
.hangulCard {
  font-family: "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic",
    "맑은 고딕", "Segoe UI", Arial, sans-serif;
}

.hangulCard {
  margin: 0 auto;
  max-width: var(--hangul-max-width-card);
  width: 100%;
  overflow: hidden;
  background: var(--hangul-color-card);
  color: var(--hangul-color-text);
  border-radius: 12px;
  border-top: 4px solid var(--hangul-color-accent);
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.42);
  padding: 24px 20px 28px;
  text-align: center;
}

.nightMode .hangulCard {
  background: var(--hangul-color-card);
  color: var(--hangul-color-text);
  border-top-color: var(--hangul-color-accent);
}

.hangulCategory {
  margin-bottom: 6px;
  color: var(--hangul-color-accent);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hangulGlyph {
  font-size: var(--hangul-font-size-glyph);
  font-weight: 700;
  line-height: 1.1;
}

.hangulHint {
  margin-top: 16px;
  color: var(--hangul-color-muted);
  font-size: 13px;
  font-style: italic;
}

.hangulDivider {
  margin: 18px 0;
  border: 0;
  border-top: 1px solid var(--hangul-color-divider);
}

.hangulLabel {
  margin-bottom: 5px;
  color: var(--hangul-color-muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hangulReadingValue {
  color: var(--hangul-color-accent);
  font-size: var(--hangul-font-size-reading);
  font-weight: 700;
}

.hangulSound { margin-top: 12px; }
.hangulSoundValue { font-size: 20px; }
.hangulAudio { margin-top: 10px; }
.hangulAnimation { margin-top: 12px; }
.hangulPicture { margin-top: 16px; }
.hangulStrokes { margin-top: 12px; }

.hangulAnimation img,
.hangulPicture img,
.hangulStrokes img {
  display: block;
  max-width: 100%;
  max-height: 320px;
  width: auto;
  height: auto;
  margin: 0 auto;
  object-fit: contain;
  border-radius: 8px;
}

.hangulMnemonic {
  margin-top: 16px;
  font-size: var(--hangul-font-size-mnemonic);
  line-height: 1.5;
  text-align: left;
}

.replay-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: auto;
  height: auto;
  padding: 0;
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  border-radius: 0;
  box-shadow: none !important;
  line-height: 0;
  -webkit-appearance: none;
  appearance: none;
}

.replay-button svg { width: 24px; height: 24px; }
.replay-button svg path { fill: var(--hangul-color-accent) !important; }
.replay-button svg circle { fill: transparent !important; stroke: none !important; }

@media (max-width: 480px) {
  .card { padding: 8px; background: var(--hangul-color-page); }
  .hangulCard { padding: 20px 14px 24px; }
  .hangulGlyph { font-size: 72px; }
  .hangulReadingValue { font-size: 28px; }
  .hangulAnimation img,
  .hangulPicture img,
  .hangulStrokes img { max-height: 260px; }
}
```
