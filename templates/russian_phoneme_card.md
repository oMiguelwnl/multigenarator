# Russian Phoneme Card Template

Template used only by the introductory Russian phoneme deck.

## Fields

- Spellings
- Sound
- letter_audio
- Example Word
- word_audio
- Word Translation
- Example Sentence
- sentence_audio
- Sentence Translation

## Front Template

```html
<div class="customCard cardBack phonemeCard">
  <div class="targetWordContainer">
    <div class="targetWordBox">
      <div class="hint">The letter(s) is:</div>
      <span class="targetIPA"> {{Spellings}} </span>
    </div>
    <div class="row centerVertically" style="margin-bottom: -8px">
      <div class="hint">Sounds like:</div>
      <div class="indent centerVertically">
        <span class="targetIPA"> {{Sound}} </span>
        <span class="wordAudioButton"> {{letter_audio}} </span>
      </div>
    </div>
  </div>

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">example word:</div>
    <div class="centerVertically wrap" style="margin-top: -8px">
      <div class="indent centerVertically">
        <span class="exampleWord"> {{Example Word}} </span>
        <span class="wordAudioButton"> {{word_audio}} </span>
      </div>
      <div class="sentenceTranslation">{{Word Translation}}</div>
    </div>
  </div>

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">example sentence:</div>
    <div class="indent">
      <div class="centerVertically wrap">
        <span class="exampleWord">{{Example Sentence}}</span>
        <span class="wordAudioButton"> {{sentence_audio}} </span>
      </div>
      <div id="sentenceTranslation" class="sentenceTranslation backOnly" aria-hidden="true"></div>
    </div>
  </div>
</div>
```

## Back Template

```html
{{FrontSide}}

<script>
  (function () {
    var translation = document.getElementById("sentenceTranslation");
    if (translation) {
      translation.textContent = "{{Sentence Translation}}";
      translation.classList.remove("backOnly");
      translation.removeAttribute("aria-hidden");
    }
  })();
</script>
<noscript>
  <div class="customCard cardBack phonemeCard backRevealFallback">
    <div class="horizontalPadding">
      <div class="header">sentence translation:</div>
      <div class="sentenceTranslation">{{Sentence Translation}}</div>
    </div>
  </div>
</noscript>
```

## Styling (CSS)

```css
:root {
  --max-width-card: 400px;
  --font-size-card: 18px;
  --font-size-targetWord: 28px;
  --font-size-exampleWord: 22px;
  --font-size-targetIPA: 32px;
  --font-size-header: 16px;
  --color-multilang-primary: #2f5fbf;
  --color-multilang-secondary: #4a6fb3;
  --color-multilang-background: #fcfdff;
  --color-multilang-surface: #f2f6ff;
  --color-multilang-text: #16213b;
  --color-multilang-muted: #5d6d8d;
  --color-multilang-divider: #d8e2f6;
  --color-multilang-shadow: rgba(22, 55, 110, 0.16);
  --color-nightMode-multilang-primary: #87adff;
  --color-nightMode-multilang-secondary: #a9c3ff;
  --color-nightMode-multilang-background: #101a2f;
  --color-nightMode-multilang-surface: #14233f;
  --color-nightMode-multilang-text: #edf2ff;
  --color-nightMode-multilang-muted: #a6b9dd;
  --color-nightMode-multilang-divider: #2a3d61;
}

* { box-sizing: border-box; }

body {
  line-height: 1.187;
  margin: 0 !important;
  overflow-wrap: break-word;
  overscroll-behavior: none;
}

.card { padding: 16px; }

.customCard {
  margin: 0 auto;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--color-multilang-background);
  box-shadow: 0 5px 22px var(--color-multilang-shadow), 0 1px 4px rgba(22, 55, 110, 0.08);
  border-radius: 8px;
  border-top: 4px solid var(--color-multilang-primary);
  min-height: 200px;
  max-width: var(--max-width-card);
  font-weight: 500;
  font-size: var(--font-size-card);
  font-family: "Inter", sans-serif;
  color: var(--color-multilang-text);
}

.nightMode .customCard {
  color: var(--color-nightMode-multilang-text);
  background-color: var(--color-nightMode-multilang-background);
}

.cardBack {
  flex-direction: column;
  justify-content: flex-start;
  align-items: flex-start;
  padding-bottom: 8px;
}

.targetWordContainer {
  margin: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-self: stretch;
}

.targetWordBox {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  align-self: stretch;
  gap: 16px;
  padding: 16px;
  background-color: var(--color-multilang-surface);
  border: 1px solid var(--color-multilang-divider);
  border-radius: 8px;
}

.nightMode .targetWordBox {
  background-color: var(--color-nightMode-multilang-surface);
  border-color: var(--color-nightMode-multilang-divider);
}

.targetIPA {
  font-family: "Charis SIL", serif;
  font-size: var(--font-size-targetIPA);
  font-weight: 600;
  color: var(--color-multilang-primary);
}

.exampleWord {
  font-size: var(--font-size-exampleWord);
  font-weight: 600;
}

.header {
  color: var(--color-multilang-secondary);
  font-size: var(--font-size-header);
  font-weight: 400;
  margin-top: 8px;
  margin-bottom: 8px;
}

.hint {
  color: var(--color-multilang-muted);
  font-size: var(--font-size-header);
}

.sentenceTranslation {
  color: var(--color-multilang-secondary);
  font-weight: 400;
  font-style: italic;
  padding-right: 15px;
  padding-top: 8px;
}

.nightMode .targetIPA,
.nightMode .replay-button svg path { fill: var(--color-nightMode-multilang-primary); }

.nightMode .header,
.nightMode .sentenceTranslation { color: var(--color-nightMode-multilang-secondary); }
.nightMode .hint { color: var(--color-nightMode-multilang-muted); }

.dividerLine {
  width: 100%;
  border-bottom: 1px solid var(--color-multilang-divider);
  margin-top: 8px;
  margin-bottom: 8px;
}

.nightMode .dividerLine { border-color: var(--color-nightMode-multilang-divider); }

.horizontalPadding {
  width: 100%;
  padding-left: 16px;
  padding-right: 16px;
}

.row { display: flex; }
.indent { padding-left: 12px; }

.centerVertically {
  display: flex;
  align-items: center;
}

.wrap {
  flex-wrap: wrap;
  gap: 8px;
}

.wordAudioButton,
.wordAudioButtonBack,
.sentenceAudioButton { margin-left: 8px; }

.replay-button { padding: 9px; }
.replay-button svg { width: 26px; height: 26px; }
.replay-button svg path { fill: var(--color-multilang-primary); }
.replay-button svg circle { fill: none; stroke: none; }

.backOnly { display: none; }
.backRevealFallback { margin-top: 12px; }
```
