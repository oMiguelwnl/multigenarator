# Japanese Card Template

Template used by the Japanese frequency deck. It follows the visual structure of
`ja_freq_v3_preview.html`: the blue frequency-card shell, front-side furigana
toggle, and Portuguese definition/translation labels.

Furigana is rendered with Anki's built-in `{{furigana:...}}` filter, so the
`Word Reading` and `Sentence Furigana` fields hold bracketed readings such as
`父親[ちちおや]` / `父親[ちちおや]は今年[ことし]50歳[さい]になる。`.

## Fields

- SortIndex
- Target Word
- Word Reading
- Definition
- Sentence
- Sentence Furigana
- Sentence Translation
- word_audio
- sentence_audio
- Image

## Front Template

```html
<div class="customCard cardBack jpFront">
  <div class="horizontalPadding centerVertically targetWordContainer">
    <div class="wordBlock">
      <span class="targetWord jpFont">
        <span class="jPlain">{{Target Word}}</span>
        <span class="jReading" style="display:none;">{{furigana:Word Reading}}</span>
      </span>
    </div>
    <div class="wordControls">
      <button type="button" class="furiganaToggle" onclick="toggleFurigana()">furigana</button>
      <span class="wordAudioButtonBack">{{word_audio}}</span>
    </div>
  </div>

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">Definição:</div>
    <div class="indent">
      <ul class="definitionsList">
        <li>{{Definition}}</li>
      </ul>
    </div>
  </div>

  {{#Image}}
  <div class="horizontalPadding">
    <div class="image">{{Image}}</div>
  </div>
  {{/Image}}

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">Exemplo:</div>
    <div class="indent exampleSentenceLine">
      <span class="exampleSentenceText jpFont">
        <span class="jPlain">{{Sentence}}</span>
        <span class="jReading" style="display:none;">{{furigana:Sentence Furigana}}</span>
      </span>
      <span class="sentenceAudioButton">{{sentence_audio}}</span>
    </div>
    <div id="translation" class="sentenceTranslation indent" style="display:none;">
      {{Sentence Translation}}
    </div>
  </div>
</div>

<script>
  function toggleFurigana() {
    var readings = document.querySelectorAll(".jReading");
    var plains = document.querySelectorAll(".jPlain");
    var showing = readings.length && readings[0].style.display !== "none";
    for (var i = 0; i < readings.length; i++) readings[i].style.display = showing ? "none" : "";
    for (var j = 0; j < plains.length; j++) plains[j].style.display = showing ? "" : "none";
  }
</script>
```

## Back Template

```html
<div class="customCard cardBack jpBack">
  <div class="horizontalPadding centerVertically targetWordContainer">
    <div class="wordBlock">
      <span class="targetWord jpFont">
        <span class="jPlain" style="display:none;">{{Target Word}}</span>
        <span class="jReading">{{furigana:Word Reading}}</span>
      </span>
    </div>
    <div class="wordControls">
      <button type="button" class="furiganaToggle" onclick="toggleFurigana()">furigana</button>
      <span class="wordAudioButtonBack">{{word_audio}}</span>
    </div>
  </div>

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">Definição:</div>
    <div class="indent">
      <ul class="definitionsList">
        <li>{{Definition}}</li>
      </ul>
    </div>
  </div>

  {{#Image}}
  <div class="horizontalPadding">
    <div class="image">{{Image}}</div>
  </div>
  {{/Image}}

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">Exemplo:</div>
    <div class="indent exampleSentenceLine">
      <span class="exampleSentenceText jpFont">
        <span class="jPlain" style="display:none;">{{Sentence}}</span>
        <span class="jReading">{{furigana:Sentence Furigana}}</span>
      </span>
      <span class="sentenceAudioButton">{{sentence_audio}}</span>
    </div>
    <div id="translation" class="sentenceTranslation indent">
      {{Sentence Translation}}
    </div>
  </div>
</div>

<script>
  function toggleFurigana() {
    var readings = document.querySelectorAll(".jReading");
    var plains = document.querySelectorAll(".jPlain");
    var showing = readings.length && readings[0].style.display !== "none";
    for (var i = 0; i < readings.length; i++) readings[i].style.display = showing ? "none" : "";
    for (var j = 0; j < plains.length; j++) plains[j].style.display = showing ? "" : "none";
  }
</script>
```

## Styling (CSS)

```css
:root {
  --max-width-card: 400px;
  --font-size-card: 18px;
  --font-size-targetWord: 26px;
  --font-size-header: 14px;

  --color-text-primary: #0f1b2d;
  --color-nightMode-text-primary: #e8f0fe;
  --color-card-background: #ffffff;
  --color-nightMode-card-background: #0a1628;
  --color-box-shadow: rgba(29, 78, 216, 0.12);
  --color-audio-button: #2563eb;
  --color-list-bullets: #3b82f6;
  --color-hint: #60a5fa;
  --color-nightMode-hint: #93c5fd;
  --color-sentence-translation: #3b82f6;
  --color-nightMode-sentence-translation: #93c5fd;
  --color-header: #1d4ed8;
  --color-nightMode-header: rgba(147, 197, 253, 0.7);
  --color-divider: #dbeafe;
  --color-nightMode-divider: #1e3a5f;
}

* { box-sizing: border-box; }

p { margin-block-start: 1em; margin-block-end: 1em; }
ol, ul { list-style: none; }

body {
  line-height: 1.187;
  overscroll-behavior: none;
  margin: 0 !important;
  overflow-wrap: break-word;
}

body.nightMode::-webkit-scrollbar { background: #0a1628; }
body.nightMode::-webkit-scrollbar-thumb { background: #2563eb; border-radius: 8px; }

.card { padding: 16px; }

.customCard {
  margin: 0 auto;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--color-card-background);
  box-shadow:
    0 4px 24px var(--color-box-shadow),
    0 1px 4px rgba(37, 99, 235, 0.08);
  border-radius: 16px;
  border-top: 4px solid #2563eb;
  min-height: 200px;
  max-width: var(--max-width-card);
  font-weight: 500;
  font-size: var(--font-size-card);
  font-family: "Segoe UI", "Noto Sans", Arial, sans-serif;
  color: var(--color-text-primary);
}

.nightMode .customCard {
  color: var(--color-nightMode-text-primary);
  background-color: var(--color-nightMode-card-background);
}

.cardBack {
  flex-direction: column;
  justify-content: flex-start;
  align-items: flex-start;
  padding-top: 24px;
  padding-bottom: 8px;
}

.targetWordContainer {
  margin-top: 8px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.targetWord {
  font-size: var(--font-size-targetWord);
  font-weight: 700;
  color: #1e3a8a;
  letter-spacing: -0.5px;
}

.targetWord.jpFont { font-size: 32px; }
.nightMode .targetWord { color: #93c5fd; }

.wordBlock { display: flex; flex-direction: column; gap: 4px; }

.jpFont {
  font-family: "Yu Mincho", "YuMincho", "Hiragino Mincho ProN",
    "Noto Serif JP", "Noto Sans JP", "Segoe UI", serif;
}

.wordControls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 0 0 auto;
}

.furiganaToggle {
  border: 1px solid var(--color-audio-button);
  color: var(--color-audio-button);
  background: transparent;
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.nightMode .furiganaToggle {
  color: var(--color-nightMode-hint);
  border-color: var(--color-nightMode-hint);
}

.definitionsList { list-style: none; margin: 0; padding: 0; padding-left: 16px; }
.definitionsList li { margin-bottom: 6px; line-height: 1.5; }
.definitionsList li::before {
  content: "\2022";
  color: var(--color-list-bullets);
  display: inline-block;
  width: 8px;
  margin-right: 5px;
  margin-left: -16px;
  font-size: 22px;
}

.wordAudioButtonBack { margin-left: 8px; }

.exampleSentenceLine { display: flex; align-items: center; gap: 8px; }
.exampleSentenceText { flex: 1 1 auto; min-width: 0; font-size: 22px; }
.sentenceAudioButton { flex: 0 0 auto; margin-left: 8px; }

.replay-button svg { width: 20px; height: 20px; }
.replay-button svg path { fill: var(--color-audio-button); }
.replay-button svg circle { fill: none; stroke: none; }

.image {
  border-top: 1px solid var(--color-divider);
  border-bottom: 1px solid var(--color-divider);
  margin-top: 16px;
  width: 100%;
  height: 210px;
}

.image img {
  object-fit: contain;
  width: 100% !important;
  height: 100% !important;
  max-width: 100% !important;
  max-height: 100% !important;
}

.sentenceTranslation {
  color: var(--color-sentence-translation);
  font-weight: 400;
  font-style: italic;
  padding-right: 15px;
  padding-top: 8px;
}

.nightMode .sentenceTranslation { color: var(--color-nightMode-sentence-translation); }

.header {
  color: var(--color-header);
  font-size: var(--font-size-header);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-top: 8px;
  margin-bottom: 8px;
}

.nightMode .header { color: var(--color-nightMode-header); }

.dividerLine {
  width: 100%;
  border-bottom: 1px solid var(--color-divider);
  margin-top: 8px;
  margin-bottom: 8px;
}

.nightMode .dividerLine { border-color: var(--color-nightMode-divider); }

.horizontalPadding { width: 100%; padding-left: 16px; padding-right: 16px; }
.indent { padding-left: 12px; }
.centerVertically { display: flex; align-items: center; }

```
