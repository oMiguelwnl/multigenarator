# Multilang Frequency Card — Minimal Dark · Carvão

Frequency-only presentation. Field order, note/model IDs, audio references and
the translation reveal follow the existing frequency export contract.
Korean grammar continues to use `normal_card.md`.

## Front Template

```html
<div class="customCard cardBack">
  <div class="targetWordContainer">
    <div class="wordBlock">
      <span class="targetWord">{{word}}</span>
      {{#IPA}}<span class="ipa">{{IPA}}</span>{{/IPA}}
    </div>
    <span class="wordAudioButtonBack">{{word_audio}}</span>
  </div>

  <div class="definitionSection">
    <div class="header">Definition:</div>
    <div class="definitionsList">{{Definitions}}</div>
  </div>

  {{#Image}}
  <div class="image">{{Image}}</div>
  {{/Image}}

  <div class="exampleSection">
    <div class="header">example:</div>
    <div class="examplePanel">
      <div class="exampleSentenceLine">
        <span class="exampleSentenceText">{{Example Sentence}}</span>
        <span class="sentenceAudioButton">{{sentence_audio}}</span>
      </div>
      <div id="translation" class="sentenceTranslation" style="display:none;">
        <div class="translationText">{{Translation}}</div>
      </div>
    </div>
  </div>
</div>
```

## Back Template

```html
{{FrontSide}}

<script>
  document.getElementById("translation").style.display = "block";
</script>
```

## Styling (CSS)

```css
:root {
  color-scheme: dark;
  --max-width-card: 620px;
  --color-page-background: #151719;
  --color-card-background: #252a2f;
  --color-nightMode-card-background: #252a2f;
  --color-text-primary: #edf3f5;
  --color-nightMode-text-primary: #edf3f5;
  --color-text-muted: #aebac0;
  --color-word: #b6dbe3;
  --color-label: #a8c9d0;
  --color-translation: #c6d4d8;
  --color-divider: #434d53;
  --color-accent: #abd1d8;
  --color-audio-button: #abd1d8;
  --color-audio-background: #303b42;
  --color-audio-border: #6c7f89;
  --frequency-font: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Arial, sans-serif;
}

* { box-sizing: border-box; }

body { margin: 0; }

.card,
.nightMode.card,
body.nightMode {
  background: var(--color-page-background);
  color: var(--color-text-primary);
  font-family: var(--frequency-font);
  font-size: 18px;
  font-weight: 400;
  line-height: 1.65;
  text-align: left;
  padding: 24px;
  overflow-wrap: anywhere;
}

#qa {
  width: 100%;
  max-width: var(--max-width-card);
  min-width: 0;
  margin: 0 auto;
}

.customCard,
.nightMode .customCard {
  display: block;
  width: 100%;
  max-width: var(--max-width-card);
  min-width: 0;
  margin: 0 auto;
  padding: 32px;
  background-color: var(--color-card-background);
  background-image: linear-gradient(145deg, #2c3137 0%, #252a2f 55%, #21262a 100%);
  color: var(--color-text-primary);
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  font-family: var(--frequency-font);
  font-weight: 400;
  text-align: left;
  overflow-wrap: anywhere;
}

.targetWordContainer,
.exampleSentenceLine {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 44px;
  align-items: center;
  gap: 16px;
}

.wordBlock {
  display: flex;
  flex-direction: column;
  gap: 9px;
  min-width: 0;
}

.targetWord {
  color: var(--color-word);
  font-size: clamp(32px, 5vw, 42px);
  font-weight: 500;
  line-height: 1.15;
  letter-spacing: -0.035em;
  overflow-wrap: anywhere;
}

.ipa {
  color: var(--color-text-muted);
  font-size: 16px;
  font-weight: 400;
  line-height: 1.5;
}

.definitionSection {
  margin-top: 28px;
  padding-top: 28px;
  border-top: 1px solid var(--color-divider);
}

.header {
  color: var(--color-label);
  font-size: 12px;
  font-weight: 500;
  line-height: 1.5;
  letter-spacing: 0.075em;
  text-transform: uppercase;
  margin: 0 0 9px;
}

.definitionsList,
.exampleSentenceText {
  font-size: 18px;
  font-weight: 400;
  line-height: 1.65;
  min-width: 0;
  margin: 0;
  padding: 0;
  overflow-wrap: anywhere;
}

.exampleSection { margin-top: 28px; }

.examplePanel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 44px;
  column-gap: 16px;
  min-width: 0;
}

.exampleSentenceLine { grid-column: 1 / -1; }

.sentenceTranslation {
  grid-column: 1;
  min-width: 0;
  color: var(--color-translation);
  margin-top: 12px;
  padding: 2px 0;
  font-size: 16px;
  font-weight: 400;
  line-height: 1.6;
}

.wordAudioButtonBack,
.sentenceAudioButton {
  display: block;
  grid-column: 2;
  width: 44px;
  min-width: 44px;
  margin: 0;
}

.replay-button,
.soundLink {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 44px;
  height: 44px;
  padding: 0;
  margin: 0;
  color: var(--color-audio-button);
  background: transparent;
  border: 0;
  border-radius: 0;
  text-decoration: none;
  line-height: 1;
}

.replay-button:focus-visible,
.soundLink:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 3px;
}

.replay-button svg {
  width: 18px;
  height: 18px;
}

.replay-button svg path { fill: var(--color-audio-button); }
.replay-button svg circle { fill: none; stroke: none; }

.image {
  width: 100%;
  max-width: 100%;
  margin-top: 28px;
}

.image img {
  display: block;
  width: auto;
  height: auto;
  max-width: 100% !important;
  max-height: 260px;
  object-fit: contain;
  border-radius: 8px;
  margin: 0 auto;
}

/* Shared by the Mandarin markup when frequency is its source. */
.horizontalPadding { width: 100%; }
.dividerLine {
  border: 0;
  border-top: 1px solid var(--color-divider);
  margin: 28px 0;
}

@media (max-width: 480px) {
  .card,
  .nightMode.card,
  body.nightMode { padding: 16px 12px; }

  .customCard,
  .nightMode .customCard { padding: 22px; }

  .targetWordContainer,
  .exampleSentenceLine { gap: 12px; }

  .examplePanel { column-gap: 12px; }

}
```

## Notes

- The English frequency model localizes the visible labels into Portuguese.
- The image and IPA remain optional. Media use Anki's native sound references.
- The answer reveals the sentence translation; definitions remain on the front.
- The translation has no heading and shares the example sentence's text
  column, including on narrow screens. The example heading retains its original
  position and typography, outside that column layout.
- The approved Carvão palette uses a charcoal gradient, pale ice-blue word and
  audio accents, cool white body text and a silver-blue translation.
- Typography and section spacing follow the original minimalist preview,
  with the requested shorter 12px gap before the translation.
- Audio icons have no surrounding circle or background; the 44px click
  targets remain available.
- The regular Anki answer button is used. The preview's switch is not embedded
  into exported cards.
