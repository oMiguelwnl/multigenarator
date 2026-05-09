# Multilang Highlight Card Template

Dedicated Anki note type template for Kindle highlight vocabulary cards.

- **Source type:** `kindle-highlights`
- **Note type:** `Multilang::Highlight Card`
- **Fields:** `SortIndex, Word, IPA, Example Sentence, sentence_audio, Definition, Image`
- **Translation:** intentionally omitted for highlight decks

---

## Front Template

```html
<div class="card">
  <div class="word">{{Word}}</div>

  {{#IPA}}
  <div class="ipa">{{IPA}}</div>
  {{/IPA}}

  <hr class="divider">

  <div class="audio-controls" aria-label="Audio controls">
    {{#sentence_audio}}<span>{{sentence_audio}}</span>{{/sentence_audio}}
  </div>

  <div class="example">{{Example Sentence}}</div>
</div>
```

---

## Back Template

```html
<div class="back-card">
  {{FrontSide}}

  <hr id="answer" class="answer-divider">

  <div class="meaning">{{Definition}}</div>

  {{#Image}}
  <div class="image-container">{{Image}}</div>
  {{/Image}}
</div>
```

---

## Styling (CSS)

```css
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  overflow-x: hidden;
  overflow-y: auto;
  overflow-wrap: anywhere;
  background: transparent;
}

.card,
.back-card {
  text-align: center;
  color: #e0e0e0;
  background-color: #121212;
  padding: 18px 5px 5px;
  border-radius: 15px;
  border: 1px solid #222;
  width: 100%;
  font-family: serif;
  margin: 0 auto;
  box-sizing: border-box;
  overflow-x: hidden;
  overflow-y: auto;
}

.back-card > .card {
  background: transparent;
  border: 0;
  border-radius: 0;
  padding: 0;
}

.word {
  font-size: 35px;
  font-weight: bold;
  color: #4CAF50;
  margin: 10px 0;
  text-shadow: 0 0 8px rgba(76, 175, 80, 0.3);
  line-height: 1.2;
}

.ipa {
  font-size: 20px;
  color: #aaa;
  font-family: serif;
  margin-bottom: 8px;
}

.example {
  font-size: 20px;
  color: #00BCD4;
  font-style: italic;
  line-height: 1.5;
  margin: 15px 0;
  padding: 0 15px;
}

.meaning {
  font-size: 20px;
  color: #FF5252;
  line-height: 1.6;
  margin: 20px 0;
  text-align: center;
  padding: 0 15px;
}

.audio-controls {
  margin: 15px 0;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.replay-button {
  background: rgba(76, 175, 80, 0.2);
  border: none;
  color: #4CAF50;
  font-size: 24px;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  cursor: pointer;
}

.replay-button svg {
  width: 24px;
  height: 24px;
}

.replay-button svg path {
  fill: #4CAF50;
}

.image-container img {
  max-width: 100%;
  max-height: 280px;
  border-radius: 12px;
  border: 1px solid #333;
  box-shadow: 0 3px 10px rgba(0,0,0,0.2);
  margin: 15px 0;
}

.divider {
  border: none;
  height: 1px;
  background: linear-gradient(to right, transparent, #333, transparent);
  margin: 20px 10%;
}

.answer-divider {
  border: none;
  height: 2px;
  background: linear-gradient(to right, transparent, #4CAF50, transparent);
  margin: 25px 10%;
}
```

---

## Notes

- The front contains only prompt-side highlight fields: word, optional IPA, audio controls, and example sentence.
- The back wraps `{{FrontSide}}` and `Definition` in one `.back-card` shell so the background and border surround both sides without nesting a second `.card` border.
- The `Image` field renders below `Definition` only when populated so blank image exports do not create placeholders.
- `Translation` is not referenced because highlight decks use the dedicated `Multilang::Highlight Card` contract.
