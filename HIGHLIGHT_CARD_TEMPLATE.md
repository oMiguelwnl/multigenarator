# Multilang Highlight Card Template

Dedicated Anki note type template for Kindle highlight vocabulary cards.

---

## Front Template

```html
<div class="highlight-card highlight-card-front">
  <section class="highlight-prompt" aria-label="Prompt word">
    <div class="highlight-word">{{Word}}</div>
    {{#IPA}}<div class="highlight-ipa">{{IPA}}</div>{{/IPA}}
  </section>

  <div class="highlight-rule" aria-hidden="true"></div>

  <section class="highlight-audio-row" aria-label="Audio controls">
    {{#word_audio}}<span class="highlight-audio highlight-word-audio">{{word_audio}}</span>{{/word_audio}}
    {{#sentence_audio}}<span class="highlight-audio highlight-sentence-audio">{{sentence_audio}}</span>{{/sentence_audio}}
  </section>

  <section class="highlight-example" aria-label="Example sentence">
    <div class="highlight-example-text">{{Example Sentence}}</div>
  </section>

  {{#Image}}
  <figure class="highlight-image">{{Image}}</figure>
  {{/Image}}
</div>
```

---

## Back Template

```html
{{FrontSide}}

<hr id="answer" class="highlight-answer-divider">

<section class="highlight-definition-answer" aria-label="Definition answer">
  <div class="highlight-definition-source">{{Definition}}</div>
</section>
```

---

## Styling (CSS)

```css
:root {
  --multilang-blue: #00f0ff;
  --highlight-bg: #111111;
  --highlight-shell: #202020;
  --highlight-border: #2d2d2d;
  --highlight-rule: #202020;
  --highlight-green: #43c95d;
  --highlight-ipa: #f2f5ff;
  --highlight-example: #00e5ff;
  --highlight-definition: #ff4444;
  --highlight-shadow: rgba(0, 0, 0, 0.45);
}

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

.card {
  margin: 0;
  padding: 16px;
  overflow-x: hidden;
  overflow-y: auto;
  font-family: Georgia, "Times New Roman", serif;
  color: var(--highlight-ipa);
  background: transparent;
  text-align: center;
}

.highlight-card {
  width: min(100%, 520px);
  max-width: 520px;
  margin: 0 auto;
  padding: clamp(20px, 5vw, 28px) clamp(22px, 6vw, 42px);
  border-radius: 16px;
  border: 1px solid var(--highlight-border);
  background: var(--highlight-bg);
  box-shadow: 0 0 0 6px var(--highlight-shell), 0 14px 32px var(--highlight-shadow);
  overflow-x: hidden;
  overflow-y: auto;
}

.highlight-prompt {
  text-align: center;
}

.highlight-word {
  color: var(--highlight-green);
  font-size: clamp(2.1rem, 10vw, 3.1rem);
  font-weight: 700;
  line-height: 1.05;
  letter-spacing: 0.01em;
  text-align: center;
  text-shadow: 0 0 8px rgba(67, 201, 93, 0.35);
}

.highlight-ipa {
  display: block;
  margin-top: 12px;
  color: var(--highlight-ipa);
  font-size: clamp(1.15rem, 4vw, 1.45rem);
  line-height: 1.35;
  text-align: center;
}

.highlight-rule {
  height: 1px;
  margin: 18px 0 26px;
  background: var(--highlight-rule);
}

.highlight-audio-row {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 14px;
  min-height: 44px;
  margin: 0 0 22px;
  text-align: center;
}

.highlight-audio {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--highlight-green);
}

.replay-button svg {
  width: 42px;
  height: 42px;
  filter: drop-shadow(0 0 4px rgba(67, 201, 93, 0.5));
}

.replay-button svg path {
  fill: var(--highlight-green);
}

.highlight-example {
  margin: 0;
  padding: 0;
  color: var(--highlight-example);
  background: transparent;
  font-size: clamp(1.25rem, 5vw, 1.55rem);
  font-style: italic;
  line-height: 1.35;
  text-align: center;
}

.highlight-example-text {
  min-width: 0;
}

.highlight-image {
  margin: 22px 0 0;
  padding: 0;
  max-width: 100%;
  text-align: center;
}

.highlight-image img {
  max-width: 100% !important;
  height: auto !important;
  border-radius: 14px;
}

.highlight-answer-divider {
  width: min(76%, 360px);
  max-width: 360px;
  margin: 28px auto 30px;
  border: 0;
  border-top: 1px solid rgba(67, 201, 93, 0.45);
}

.highlight-definition-answer {
  width: min(100%, 520px);
  max-width: 520px;
  margin: 0 auto;
  padding: 0 clamp(20px, 6vw, 42px) clamp(22px, 5vw, 30px);
  background: transparent;
  box-shadow: none;
  overflow-x: hidden;
  overflow-y: auto;
  text-align: center;
}

.highlight-definition-source {
  margin: 0;
  color: var(--highlight-definition);
  font-size: clamp(1.25rem, 5vw, 1.55rem);
  font-weight: 700;
  line-height: 1.35;
  text-align: center;
}

@media (max-width: 420px) {
  .card {
    padding: 10px;
  }

  .highlight-card {
    padding: 20px 18px;
  }
}
```

---

## Notes

- The front contains only prompt-side highlight fields: word, optional IPA, audio controls, example sentence, and optional image.
- The back reuses `{{FrontSide}}`, then reveals a centered Definition answer area after a single answer divider.
- The `Image` field renders only when populated so blank image exports do not create placeholders.
