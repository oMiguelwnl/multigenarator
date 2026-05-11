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
  background: #121212;
  padding: 18px 12px 20px;
  border-radius: 15px;
  border: 1px solid #242424;
  width: min(100%, 480px);
  font-family: Georgia, "Times New Roman", serif;
  margin: 0 auto;
  box-sizing: border-box;
  overflow-x: hidden;
  overflow-y: auto;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.32);
}

.back-card > .card {
  background: transparent;
  border: 0;
  border-radius: 0;
  padding: 0;
  width: 100%;
  box-shadow: none;
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
  font-family: Georgia, "Times New Roman", serif;
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
  margin: 20px 0 18px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.audio-controls span {
  display: inline-flex;
  line-height: 0;
}

.audio-controls .replay-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f8f8f2;
  border: 2px solid rgba(76, 175, 80, 0.28);
  color: #263128;
  font-size: 0;
  line-height: 0;
  width: 40px;
  height: 40px;
  padding: 0;
  margin: 0;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
}

.audio-controls .replay-button svg {
  display: none;
}

.audio-controls .replay-button::before {
  content: "";
  display: block;
  width: 0;
  height: 0;
  border-top: 10px solid transparent;
  border-bottom: 10px solid transparent;
  border-left: 15px solid #263128;
  margin-left: 4px;
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
  margin: 20px 10% 22px;
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
