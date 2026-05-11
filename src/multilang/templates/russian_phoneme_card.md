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
    <div class="row centerVertically soundRow">
      <div class="hint">Sounds like:</div>
      <span class="targetIPA indent"> {{Sound}} </span>
      <span class="wordAudioButton"> {{letter_audio}} </span>
    </div>
  </div>

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">example word:</div>
    <div class="centerVertically wrap exampleWordLine">
      <span class="exampleWord indent"> {{Example Word}} </span>
      <span class="wordAudioButton"> {{word_audio}} </span>
      <div class="sentenceTranslation">{{Word Translation}}</div>
    </div>
  </div>

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">example sentence:</div>
    <div class="indent">
      <div class="exampleSentenceLine">
        <span class="exampleWord">{{Example Sentence}}</span>
        <span class="wordAudioButton"> {{sentence_audio}} </span>
      </div>
      <div id="sentenceTranslation" class="sentenceTranslation" style="display:none;">
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
  --font-size-targetWord: 30px;
  --font-size-exampleWord: 22px;
  --font-size-targetIPA: 32px;
  --font-size-header: 16px;
  --color-text-primary: #fbfafe;
  --color-card-background: #0b0716;
  --color-page-background: #07040d;
  --color-box-shadow: rgba(0, 0, 0, 0.35);
  --color-audio-button: #8b6cff;
  --color-hint: #aebbd1;
  --color-sentence-translation: #a9a4bb;
  --color-header: #8f93a8;
  --color-divider: #272236;
  --color-box-background: #10091e;
  --color-box-border: #2c2a46;
}

* { box-sizing: border-box; }

body {
  line-height: 1.2;
  margin: 0 !important;
  overflow-wrap: break-word;
  overscroll-behavior: none;
  background: var(--color-page-background);
}

.card {
  padding: 6px 0 0;
  background: var(--color-page-background);
}

.customCard {
  margin: 0 auto;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--color-card-background);
  box-shadow: none;
  border-radius: 6px;
  min-height: 200px;
  max-width: var(--max-width-card);
  width: 100%;
  font-weight: 500;
  font-size: var(--font-size-card);
  font-family: "Inter", "Segoe UI", Arial, sans-serif;
  color: var(--color-text-primary);
  overflow: hidden;
}

.nightMode .customCard {
  color: var(--color-text-primary);
  background-color: var(--color-card-background);
}

.cardBack {
  flex-direction: column;
  justify-content: flex-start;
  align-items: flex-start;
  padding-bottom: 14px;
}

.targetWordContainer {
  margin: 16px 20px 6px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  align-self: stretch;
}

.targetWordBox {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  align-self: stretch;
  gap: 20px;
  padding: 16px;
  min-height: 112px;
  background-color: var(--color-box-background);
  border: 1px solid var(--color-box-border);
  border-radius: 6px;
}

.nightMode .targetWordBox {
  background-color: var(--color-box-background);
  border-color: var(--color-box-border);
}

.targetIPA {
  font-family: "Charis SIL", Georgia, "Times New Roman", serif;
  font-size: var(--font-size-targetIPA);
  font-weight: 700;
  line-height: 1;
  color: #ffffff;
}

.exampleWord {
  font-size: var(--font-size-exampleWord);
  font-weight: 700;
  line-height: 1.25;
  color: #ffffff;
}

.header {
  color: var(--color-header);
  font-size: var(--font-size-header);
  font-weight: 400;
  margin-top: 8px;
  margin-bottom: 10px;
}

.hint {
  color: var(--color-hint);
  font-size: 18px;
  font-weight: 400;
}

.sentenceTranslation {
  color: var(--color-sentence-translation);
  font-size: 18px;
  font-weight: 400;
  font-style: italic;
  padding-right: 15px;
  padding-top: 6px;
  line-height: 1.25;
}

.nightMode .header,
.nightMode .sentenceTranslation { color: var(--color-sentence-translation); }
.nightMode .hint { color: var(--color-hint); }

.dividerLine {
  width: 100%;
  border-bottom: 1px solid var(--color-divider);
  margin-top: 12px;
  margin-bottom: 12px;
}

.nightMode .dividerLine { border-color: var(--color-divider); }

.horizontalPadding {
  width: 100%;
  padding-left: 20px;
  padding-right: 20px;
}

.row { display: flex; }
.indent { padding-left: 12px; }
.soundRow { margin-bottom: 0; }
.exampleWordLine { margin-top: -2px; }
.exampleWordLine .sentenceTranslation {
  margin-left: 6px;
  padding-top: 0;
}

.exampleSentenceLine {
  line-height: 1.25;
}

.exampleSentenceLine .exampleWord {
  display: inline;
}

.exampleSentenceLine .wordAudioButton {
  vertical-align: middle;
}

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
.sentenceAudioButton {
  display: inline-flex;
  align-items: center;
  margin-left: 8px;
  line-height: 0;
}

.replay-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  padding: 0;
  margin: 0;
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
  font-size: 0;
  line-height: 0;
}

.replay-button svg { display: none; }

.replay-button::before {
  content: "";
  display: block;
  width: 0;
  height: 0;
  border-top: 9px solid transparent;
  border-bottom: 9px solid transparent;
  border-left: 16px solid var(--color-audio-button);
}

.backRevealFallback { margin-top: 12px; }
```
