# Japanese Frequency — Herói azul escuro

Frequency-only reading layout. CSS inherits frequency_card.md.

## Front Template

```html
<div class="customCard cardBack jpFront" lang="ja">
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
    <div class="examplePanel indent">
      <div class="exampleSentenceLine">
        <span class="exampleSentenceText jpFont">
          <span class="jPlain">{{Sentence}}</span>
          <span class="jReading" style="display:none;">{{furigana:Sentence Furigana}}</span>
        </span>
        <span class="sentenceAudioButton">{{sentence_audio}}</span>
      </div>
      <div id="translation" class="sentenceTranslation" style="display:none;">
        {{Sentence Translation}}
      </div>
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
<div class="customCard cardBack jpBack" lang="ja">
  <div class="horizontalPadding centerVertically targetWordContainer">
    <div class="wordBlock">
      <span class="targetWord jpFont">
        <span class="jPlain" style="display:none;">{{Target Word}}</span>
        <span class="jReading">{{furigana:Word Reading}}</span>
      </span>
      <div class="wordRomaji">{{Word Romaji}}</div>
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
    <div class="examplePanel indent">
      <div class="exampleSentenceLine">
        <span class="exampleSentenceText jpFont">
          <span class="jPlain" style="display:none;">{{Sentence}}</span>
          <span class="jReading">{{furigana:Sentence Furigana}}</span>
        </span>
        <span class="sentenceAudioButton">{{sentence_audio}}</span>
      </div>
      <div class="sentenceRomaji">{{Sentence Romaji}}</div>
      <div id="translation" class="sentenceTranslation">
        {{Sentence Translation}}
      </div>
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
/* Composed after frequency_card.md; reading annotations retain extra room. */
.jpFont {
  font-family: "Noto Serif JP", "Yu Mincho", "Hiragino Mincho ProN", serif;
}
.targetWord.jpFont { font-size: 32px; line-height: 1.8; }
.jpFont ruby { ruby-position: over; ruby-align: center; }
.jpFont rt { font-size: 0.55em; line-height: 1; }
.exampleSentenceText.jpFont { font-size: 22px; line-height: 2; }
.wordRomaji,
.sentenceRomaji {
  color: var(--color-text-primary);
  opacity: 0.7;
  font-size: 14px;
  font-weight: 400;
  line-height: 1.4;
  overflow-wrap: anywhere;
}
.nightMode .wordRomaji,
.nightMode .sentenceRomaji { color: var(--color-nightMode-text-primary); }
.sentenceRomaji { grid-column: 1; padding-top: 4px; }
.wordControls { display: flex; align-items: center; gap: 8px; flex: 0 0 auto; }
.targetWordContainer { flex-wrap: wrap; }
.furiganaToggle {
  border: 1px solid var(--color-audio-button);
  color: var(--color-audio-button);
  background: transparent;
  border-radius: 999px;
  padding: 4px 12px;
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.nightMode .furiganaToggle {
  color: var(--color-nightMode-hint);
  border-color: var(--color-nightMode-hint);
}
.replay-button {
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
```
