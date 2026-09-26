# notedfa — compact dark refinement

Based on the supplied notedfa.apkg. Not registered as a replacement for other deck templates.

## Front Template

```html
<div class="customCard cardBack">
  <div class="horizontalPadding centerVertically targetWordContainer">
    <div class="wordBlock">
      <span class="targetWord">{{Front of Card}}</span>
      {{#IPA}}<span class="ipa">{{IPA}}</span>{{/IPA}}
    </div>
    <span class="wordAudioButtonBack">{{word_audio}}</span>
  </div>

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">Definition:</div>
    <div class="indent">
      <ul class="definitionsList">
        <li>{{Definitions}}</li>
      </ul>
    </div>
  </div>

  {{#Image}}
  <div class="image">{{Image}}</div>
  {{/Image}}

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">example:</div>
    <div class="examplePanel indent">
      <div class="exampleSentenceLine">
        <span class="exampleSentenceText">{{Example Sentence}}</span>
        <span class="sentenceAudioButton">{{sentence_audio}}</span>
      </div>
      <div id="translation" class="sentenceTranslation" style="display:none;">
        {{Translation}}
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
  --max-width-card: 400px;
  --font-size-card: 18px;
  --font-size-targetWord: 26px;
  --font-size-header: 14px;
  --font-size-irregular-form: 15px;

  --color-text-primary: #edf3f7;
  --color-nightMode-text-primary: #edf3f7;
  --color-card-background: #151b22;
  --color-nightMode-card-background: #151b22;
  --color-box-shadow: rgba(0, 0, 0, 0.24);
  --color-audio-button: #79bbf4;
  --color-list-bullets: #6f9fca;
  --color-irregular-form-background: #eff6ff;
  --color-nightMode-irregular-form-background: #1e3a5f;
  --color-irregular-form-border: #bfdbfe;
  --color-nightMode-irregular-form-border: #2563eb;
  --color-nightMode-irregular-form-text: rgba(219, 234, 254, 0.85);
  --color-hint: #60a5fa;
  --color-nightMode-hint: #93c5fd;
  --color-sentence-translation: #a8c9e5;
  --color-nightMode-sentence-translation: #a8c9e5;
  --color-header: #8faec7;
  --color-nightMode-header: #8faec7;
  --color-divider: #2b3743;
  --color-nightMode-divider: #2b3743;
}

/* Chrome Base Styles */
p {
  display: block;
  margin-block-start: 1em;
  margin-block-end: 1em;
  margin-inline-start: 0px;
  margin-inline-end: 0px;
}

div { display: block; }

body {
  display: block;
  line-height: 1.187;
}

html { display: block; }

span, applet, object, iframe,
h1, h2, h3, h4, h5, h6,
blockquote, pre, a, abbr, acronym, address, big, cite, code,
del, dfn, em, img, ins, kbd, q, s, samp, small, strike, strong,
sub, sup, tt, var, b, u, i, center,
dl, dt, dd, ol, ul, li,
fieldset, form, label, legend,
table, caption, tbody, tfoot, thead, tr, th, td,
article, aside, canvas, details, embed,
figure, figcaption, footer, header, hgroup,
menu, nav, output, ruby, section, summary,
time, mark, audio, video {
  margin: 0;
  padding: 0;
  border: 0;
  font-size: 100%;
  font: inherit;
  vertical-align: baseline;
}

article, aside, details, figcaption, figure,
footer, header, hgroup, menu, nav, section {
  display: block;
}

ol, ul { list-style: none; }

blockquote, q { quotes: none; }

blockquote:before, blockquote:after,
q:before, q:after {
  content: "";
  content: none;
}

table {
  border-collapse: collapse;
  border-spacing: 0;
}

* { box-sizing: border-box; }

/* ========== NIGHT MODE SCROLLBAR ========== */

body.nightMode::-webkit-scrollbar {
  background: #0b1016;
}
body.nightMode::-webkit-scrollbar:horizontal { height: 12px; }
body.nightMode::-webkit-scrollbar:vertical { width: 12px; }
body.nightMode::-webkit-scrollbar-thumb {
  background: #2563eb;
  border-radius: 8px;
}
body.nightMode::-webkit-scrollbar-thumb:horizontal { min-width: 50px; }
body.nightMode::-webkit-scrollbar-thumb:vertical { min-height: 50px; }

/* ========== BASE ========== */

body {
  overscroll-behavior: none;
  margin: 0 !important;
  overflow-wrap: break-word;
}

#_flag {
  position: fixed;
  right: 10px;
  top: 0;
  font-size: 30px;
  display: none;
  -webkit-text-stroke-width: 1px;
  -webkit-text-stroke-color: black;
}

#_mark {
  position: fixed;
  left: 10px;
  top: 0;
  font-size: 30px;
  color: yellow;
  display: none;
  -webkit-text-stroke-width: 1px;
  -webkit-text-stroke-color: black;
}

#typeans {
  width: 100%;
  box-sizing: border-box;
}

.typeGood { background: #0f0; }
.typeBad { background: #f00; }
.typeMissed { background: #ccc; }
.nightMode .latex { filter: invert(100%); }
.drawing { zoom: 50%; }
.nightMode img.drawing { filter: invert(1) hue-rotate(180deg); }

/* ========== CARD STYLES ========== */

.card {
  padding: 16px;
}

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
  border-top: 4px solid #4d93ca;
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
  color: #c7e3f9;
  letter-spacing: -0.5px;
}

.wordBlock {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ipa {
  font-size: 14px;
  color: #a0b2c2;
  margin-left: 2px;
  font-weight: 400;
  letter-spacing: 0.03em;
  opacity: 1;
}

.nightMode .targetWord {
  color: #c7e3f9;
}

.definitionsList {
  list-style: none;
  margin: 0;
  padding: 0;
  padding-left: 16px;
}

.definitionsList li {
  margin-bottom: 6px;
  line-height: 1.5;
}

.definitionsList li::before {
  content: "\2022";
  color: var(--color-list-bullets);
  display: inline-block;
  width: 8px;
  margin-right: 5px;
  margin-left: -16px;
  font-size: 22px;
}

.wordAudioButtonFront {
  position: absolute;
  top: 21px;
  right: 22px;
}

.wordAudioButtonBack {
  margin-left: 8px;
}

.replay-button svg {
  width: 20px;
  height: 20px;
}

.replay-button svg path {
  fill: var(--color-audio-button);
}

.replay-button svg circle {
  fill: none;
  stroke: none;
}

.irregularFormsContainer {
  display: flex;
  flex-wrap: wrap;
  margin-top: 12px;
}

.irregularForm {
  background-color: var(--color-irregular-form-background);
  border: 1px solid var(--color-irregular-form-border);
  border-radius: 40px;
  font-size: var(--font-size-irregular-form);
  color: #1d4ed8;
  font-weight: 600;
  padding: 3px 12px 5px;
  margin-right: 10px;
  margin-bottom: 8px;
}

.nightMode .irregularForm {
  color: var(--color-nightMode-irregular-form-text);
  background-color: var(--color-nightMode-irregular-form-background);
  border-color: var(--color-nightMode-irregular-form-border);
}

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

.hint { color: var(--color-hint); }
.nightMode .hint { color: var(--color-nightMode-hint); }

.sentenceTranslation {
  color: var(--color-sentence-translation);
  font-weight: 400;
  font-style: italic;
  padding-right: 15px;
  padding-top: 8px;
}

.nightMode .sentenceTranslation {
  color: var(--color-nightMode-sentence-translation);
}

.reportIconContainer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.header {
  color: var(--color-header);
  font-size: var(--font-size-header);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-top: 8px;
  margin-bottom: 8px;
}

.nightMode .header {
  color: var(--color-nightMode-header);
}

.dividerLine {
  width: 100%;
  border-bottom: 1px solid var(--color-divider);
  margin-top: 8px;
  margin-bottom: 8px;
}

.nightMode .dividerLine {
  border-color: var(--color-nightMode-divider);
}

.horizontalPadding {
  width: 100%;
  padding-left: 16px;
  padding-right: 16px;
}

.indent {
  padding-left: 12px;
}

.centerVertically {
  display: flex;
  align-items: center;
}

/* Refine the supplied compact layout; original font sizes stay unchanged. */
html,
.card,
.nightMode.card,
body.nightMode {
  background: #0b1016;
  color: var(--color-text-primary);
}

#qa { min-width: 0; }
.customCard { width: 100%; min-width: 0; }
.wordBlock { min-width: 0; }
.targetWord { overflow-wrap: anywhere; }
.targetWordContainer { gap: 12px; }

.examplePanel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 32px;
  column-gap: 8px;
  min-width: 0;
}
.exampleSentenceLine {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 32px;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.exampleSentenceText { min-width: 0; line-height: 1.5; }
.sentenceTranslation {
  grid-column: 1;
  padding-top: 8px;
  padding-right: 0;
  line-height: 1.5;
  min-width: 0;
}
.wordAudioButtonBack,
.sentenceAudioButton { flex: 0 0 32px; width: 32px; margin: 0; }
.replay-button,
.soundLink {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  margin: 0;
  background: transparent;
  border: 0;
  border-radius: 0;
  color: var(--color-audio-button);
  vertical-align: middle;
}
.replay-button:focus-visible,
.soundLink:focus-visible { outline: 2px solid #79bbf4; outline-offset: 2px; }
.image { height: auto; padding: 12px 16px; }
.image img { max-height: 210px !important; height: auto !important; display: block; }

```
