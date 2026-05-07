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
      <div id="sentenceTranslation" class="sentenceTranslation indent" style="display:none;">
        {{Sentence Translation}}
      </div>
    </div>
  </div>
</div>
```

## Back Template

```html
{{FrontSide}}

<script>
  (function () {
    document.getElementById("sentenceTranslation").style.display = "block";
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
  --color-text-primary: #18191f;
  --color-nightMode-text-primary: #fbfafe;
  --color-card-background: #ffffff;
  --color-nightMode-card-background: #0b0716;
  --color-box-shadow: rgba(18, 62, 119, 0.1);
  --color-audio-button: #8369ed;
  --color-hint: #6b7280;
  --color-nightMode-hint: #9ca3af;
  --color-sentence-translation: #6b7280;
  --color-nightMode-sentence-translation: #9ca3af;
  --color-header: #9ca3af;
  --color-nightMode-header: rgba(255, 255, 255, 0.5);
  --color-divider: #e5e7eb;
  --color-nightMode-divider: #1f2937;
  --color-box-background: #f3f4f6;
  --color-nightMode-box-background: #130c22;
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
  background-color: var(--color-card-background);
  box-shadow: 1px 3px 10px var(--color-box-shadow);
  border-radius: 8px;
  min-height: 200px;
  max-width: var(--max-width-card);
  font-weight: 500;
  font-size: var(--font-size-card);
  font-family: "Inter", sans-serif;
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
  background-color: var(--color-box-background);
  border: 1px solid var(--color-divider);
  border-radius: 8px;
}

.nightMode .targetWordBox {
  background-color: var(--color-nightMode-box-background);
  border-color: var(--color-nightMode-divider);
}

.targetIPA {
  font-family: "Charis SIL", serif;
  font-size: var(--font-size-targetIPA);
  font-weight: 600;
}

.exampleWord {
  font-size: var(--font-size-exampleWord);
  font-weight: 600;
}

.header {
  color: var(--color-header);
  font-size: var(--font-size-header);
  font-weight: 400;
  margin-top: 8px;
  margin-bottom: 8px;
}

.hint {
  color: var(--color-hint);
  font-size: var(--font-size-header);
}

.sentenceTranslation {
  color: var(--color-sentence-translation);
  font-weight: 400;
  font-style: italic;
  padding-right: 15px;
  padding-top: 8px;
}

.nightMode .replay-button svg path { fill: var(--color-audio-button); }

.nightMode .header,
.nightMode .sentenceTranslation { color: var(--color-nightMode-sentence-translation); }
.nightMode .hint { color: var(--color-nightMode-hint); }

.dividerLine {
  width: 100%;
  border-bottom: 1px solid var(--color-divider);
  margin-top: 8px;
  margin-bottom: 8px;
}

.nightMode .dividerLine { border-color: var(--color-nightMode-divider); }

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
.replay-button svg path { fill: var(--color-audio-button); }
.replay-button svg circle { fill: none; stroke: none; }

.backRevealFallback { margin-top: 12px; }
```
