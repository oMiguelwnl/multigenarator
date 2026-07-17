# Japanese Card Template

Template used by the Japanese frequency deck. It adapts the sentence-mining
"FRPG+" model (Portuguese content, sentence-first) and adds the JP1K-style
furigana reveal toggle so the learner can recall the reading before seeing it.

Furigana is rendered with Anki's built-in `{{furigana:...}}` filter, so the
`Word Reading` and `Sentence Furigana` fields hold bracketed readings such as
`父親[ちちおや]` / `父親[ちちおや]は 今年[ことし]50 歳[さい]になる。`.

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
<div class="jpCard jpCard--front">
  <div class="jpCardContent">
    <div class="jpTargetWord jpFont">
      <span class="jpPlain">{{Target Word}}</span>
      <span class="jpReading" style="display:none;">{{furigana:Word Reading}}</span>
    </div>

    <div class="jpSentence jpFont">
      <span class="jpPlain">{{Sentence}}</span>
      <span class="jpReading" style="display:none;">{{furigana:Sentence Furigana}}</span>
    </div>

    <div class="jpControls">
      <button type="button" class="jpEyeButton" onclick="toggleFurigana()">
        <span class="jpEyeGlyph">👁</span>
        <span class="jpEyeLabel">leitura</span>
      </button>
      <span class="jpAudio jpWordAudio">{{word_audio}}</span>
      <span class="jpAudio jpSentenceAudio">{{sentence_audio}}</span>
    </div>

    <div class="jpInstruction">
      Lembre a leitura e o significado. Depois vire o card.
    </div>
  </div>
</div>

<script>
  function toggleFurigana() {
    var readings = document.querySelectorAll(".jpCard--front .jpReading");
    var plains = document.querySelectorAll(".jpCard--front .jpPlain");
    var revealed = readings.length > 0 && readings[0].style.display !== "none";
    for (var i = 0; i < readings.length; i++) {
      readings[i].style.display = revealed ? "none" : "";
    }
    for (var j = 0; j < plains.length; j++) {
      plains[j].style.display = revealed ? "" : "none";
    }
  }
</script>
```

## Back Template

```html
<div class="jpCard jpCard--back">
  {{#Image}}<div class="jpImage">{{Image}}</div>{{/Image}}

  <div class="jpCardContent">
    <div class="jpTargetWord jpFont">{{furigana:Word Reading}}</div>
    <div class="jpAudioRow">{{word_audio}}</div>

    <div class="jpSentence jpFont">{{furigana:Sentence Furigana}}</div>
    <div class="jpAudioRow">{{sentence_audio}}</div>

    <div class="jpDividerLine"></div>

    <div class="jpMeaningRow">
      <span class="jpMeaningLabel">Palavra:</span>
      <span class="jpMeaningText">{{Definition}}</span>
    </div>
    <div class="jpMeaningRow">
      <span class="jpMeaningLabel">Frase:</span>
      <span class="jpMeaningText">{{Sentence Translation}}</span>
    </div>
  </div>

  <footer class="jpFooter">
    <a href="https://jisho.org/search?keyword={{Target Word}}" title="Ver no Jisho">Jisho</a>
    <span class="jpFooterDot">•</span>
    <a href="https://www.google.co.jp/search?q={{Target Word}}&amp;tbm=isch" title="Buscar imagens">Imagens</a>
    <span class="jpFooterDot">•</span>
    <a href="https://www.weblio.jp/content/{{Target Word}}" title="Ver no Weblio">Weblio</a>
  </footer>
</div>
```

## Styling (CSS)

```css
:root {
  --jp-max-width-card: 460px;
  --jp-font-size-word: 40px;
  --jp-font-size-sentence: 30px;
  --jp-font-size-meaning: 20px;
  --jp-font-size-label: 15px;

  --jp-color-page: #fdf6e3;
  --jp-color-card: #ffffff;
  --jp-color-text: #1f2430;
  --jp-color-accent: #524c9e;
  --jp-color-audio-button: #524c9e;
  --jp-color-label: #6b7280;
  --jp-color-divider: #e5e7eb;

  --jp-color-nightMode-page: #0b0716;
  --jp-color-nightMode-card: #171226;
  --jp-color-nightMode-text: #f3f1fb;
  --jp-color-nightMode-accent: #b8aef6;
  --jp-color-nightMode-label: #9ca3af;
  --jp-color-nightMode-divider: #2c2a46;
}

* { box-sizing: border-box; }

body {
  margin: 0 !important;
  line-height: 1.35;
  overflow-wrap: break-word;
  overscroll-behavior: none;
  background: var(--jp-color-page);
}

.nightMode body,
body.nightMode { background: var(--jp-color-nightMode-page); }

.card {
  padding: 12px;
  background: var(--jp-color-page);
}

.nightMode .card { background: var(--jp-color-nightMode-page); }

.jpFont {
  font-family: "Yu Mincho", "YuMincho", "Hiragino Mincho ProN", "Noto Serif JP",
    "Noto Sans JP", "Segoe UI", serif;
}

.jpCard {
  margin: 0 auto;
  max-width: var(--jp-max-width-card);
  width: 100%;
  background: var(--jp-color-card);
  color: var(--jp-color-text);
  border-radius: 12px;
  border-top: 4px solid var(--jp-color-accent);
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  font-family: "Segoe UI", "Noto Sans JP", Arial, sans-serif;
}

.nightMode .jpCard {
  background: var(--jp-color-nightMode-card);
  color: var(--jp-color-nightMode-text);
  border-top-color: var(--jp-color-nightMode-accent);
}

.jpCardContent { padding: 22px 20px; text-align: center; }

.jpTargetWord {
  font-size: var(--jp-font-size-word);
  font-weight: 700;
  line-height: 1.2;
}

.jpSentence {
  font-size: var(--jp-font-size-sentence);
  margin-top: 16px;
  line-height: 1.5;
}

.jpControls {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 20px;
}

.jpEyeButton {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--jp-color-accent);
  border-radius: 999px;
  background: transparent;
  color: var(--jp-color-accent);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.nightMode .jpEyeButton {
  border-color: var(--jp-color-nightMode-accent);
  color: var(--jp-color-nightMode-accent);
}

.jpEyeGlyph { font-size: 16px; line-height: 1; }

.jpInstruction {
  margin-top: 18px;
  font-size: 13px;
  font-style: italic;
  color: var(--jp-color-label);
}

.nightMode .jpInstruction { color: var(--jp-color-nightMode-label); }

.jpImage {
  width: 100%;
  max-height: 320px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #000;
}

.jpImage img {
  width: 100%;
  height: auto;
  max-height: 320px;
  object-fit: contain;
}

.jpAudioRow { margin-top: 8px; }

.jpDividerLine {
  border-bottom: 1px solid var(--jp-color-divider);
  margin: 18px 0;
}

.nightMode .jpDividerLine { border-color: var(--jp-color-nightMode-divider); }

.jpMeaningRow {
  text-align: left;
  font-size: var(--jp-font-size-meaning);
  margin: 10px 0;
}

.jpMeaningLabel {
  font-weight: 700;
  font-size: var(--jp-font-size-label);
  color: var(--jp-color-accent);
  margin-right: 8px;
}

.nightMode .jpMeaningLabel { color: var(--jp-color-nightMode-accent); }

.jpFooter {
  padding: 12px 20px 18px;
  text-align: center;
  font-size: 14px;
  color: var(--jp-color-label);
}

.jpFooter a { color: var(--jp-color-accent); text-decoration: none; }
.nightMode .jpFooter a { color: var(--jp-color-nightMode-accent); }
.jpFooterDot { margin: 0 8px; opacity: 0.6; }

.replay-button svg { width: 22px; height: 22px; }
.replay-button svg path { fill: var(--jp-color-audio-button); }
.nightMode .replay-button svg path { fill: var(--jp-color-nightMode-accent); }
.replay-button svg circle { fill: none; stroke: none; }
```
