# Multilang Highlight Card Template

Dedicated Anki note type template for Kindle highlight vocabulary cards.

---

## Front Template

```html
<div class="highlight-card highlight-card-front">
  <section class="highlight-word-row" aria-label="Prompt word">
    <div class="highlight-word-stack">
      <div class="highlight-word">{{Word}}</div>
      {{#IPA}}{{IPA}}{{/IPA}}
    </div>
    <div class="highlight-audio highlight-word-audio">{{word_audio}}</div>
  </section>

  <section class="highlight-example" aria-label="Example sentence">
    <div class="highlight-example-text">{{Example Sentence}}</div>
    <div class="highlight-audio highlight-sentence-audio">{{sentence_audio}}</div>
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
  <div class="highlight-answer-label">Definition</div>
  <div id="highlight-definition-source" class="highlight-definition-source">{{Definition}}</div>
  <ul id="highlight-definition-list" class="highlight-definition-list"></ul>
</section>

<script>
  (function () {
    var source = document.getElementById("highlight-definition-source");
    var list = document.getElementById("highlight-definition-list");
    if (!source || !list) {
      return;
    }
    var definitions = source.innerHTML
      .split(/<br\s*\/?\s*>/i)
      .map(function (item) { return item.trim(); })
      .filter(Boolean);
    if (definitions.length <= 1) {
      list.style.display = "none";
      return;
    }
    source.style.display = "none";
    definitions.forEach(function (definition) {
      var item = document.createElement("li");
      item.innerHTML = definition;
      list.appendChild(item);
    });
  })();
</script>
```

---

## Styling (CSS)

```css
:root {
  --multilang-blue: #2563eb;
  --multilang-blue-dark: #1d4ed8;
  --multilang-blue-soft: #dbeafe;
  --multilang-blue-wash: #eff6ff;
  --multilang-text: #0f172a;
  --multilang-muted: #475569;
  --multilang-surface: #ffffff;
  --multilang-shadow: rgba(37, 99, 235, 0.16);
  --multilang-night-surface: #0a1628;
  --multilang-night-text: #e8f0fe;
  --multilang-night-muted: #bfdbfe;
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
  font-family: "Segoe UI", "Noto Sans", Arial, sans-serif;
  color: var(--multilang-text);
}

.highlight-card {
  width: min(100%, 520px);
  max-width: 520px;
  margin: 0 auto;
  padding: clamp(20px, 5vw, 32px);
  border-radius: 22px;
  border: 1px solid var(--multilang-blue-soft);
  border-top: 5px solid var(--multilang-blue);
  background: var(--multilang-surface);
  box-shadow: 0 18px 42px var(--multilang-shadow);
  overflow-x: hidden;
  overflow-y: auto;
}

.highlight-word-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.highlight-word-stack {
  min-width: 0;
}

.highlight-word {
  color: var(--multilang-blue-dark);
  font-size: clamp(2rem, 9vw, 3rem);
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -0.04em;
}

.ipa {
  display: block;
  margin-top: 8px;
  color: var(--multilang-muted);
  font-size: 1rem;
  line-height: 1.35;
}

.highlight-audio {
  flex: 0 0 auto;
  color: var(--multilang-blue);
}

.replay-button svg {
  width: 24px;
  height: 24px;
}

.replay-button svg path {
  fill: var(--multilang-blue);
}

.highlight-example {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
  padding: 18px;
  border-radius: 18px;
  background: var(--multilang-blue-wash);
  color: var(--multilang-text);
  font-size: clamp(1.05rem, 4vw, 1.25rem);
  line-height: 1.55;
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
  width: min(100%, 520px);
  max-width: 520px;
  margin: 18px auto;
  border: 0;
  border-top: 2px solid var(--multilang-blue-soft);
}

.highlight-definition-answer {
  width: min(100%, 520px);
  max-width: 520px;
  margin: 0 auto;
  padding: 20px clamp(18px, 5vw, 28px);
  border-radius: 18px;
  background: var(--multilang-surface);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
  overflow-x: hidden;
  overflow-y: auto;
}

.highlight-answer-label {
  margin-bottom: 12px;
  color: var(--multilang-blue-dark);
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.highlight-definition-source,
.highlight-definition-list {
  color: var(--multilang-text);
  font-size: 1.05rem;
  line-height: 1.55;
}

.highlight-definition-list {
  margin: 0;
  padding-left: 1.25rem;
}

.highlight-definition-list li {
  margin: 0 0 0.5rem;
  padding-left: 0.25rem;
}

.highlight-definition-list li::marker {
  color: var(--multilang-blue);
}

.nightMode.card,
.nightMode .card {
  color: var(--multilang-night-text);
}

.nightMode .highlight-card,
.nightMode .highlight-definition-answer {
  color: var(--multilang-night-text);
  background: var(--multilang-night-surface);
  border-color: rgba(147, 197, 253, 0.35);
}

.nightMode .highlight-word,
.nightMode .highlight-answer-label {
  color: #93c5fd;
}

.nightMode .ipa,
.nightMode .highlight-definition-source,
.nightMode .highlight-definition-list {
  color: var(--multilang-night-muted);
}

.nightMode .highlight-example {
  color: var(--multilang-night-text);
  background: rgba(37, 99, 235, 0.18);
}

@media (max-width: 420px) {
  .card {
    padding: 10px;
  }

  .highlight-card {
    padding: 20px 16px;
  }

  .highlight-word-row {
    gap: 10px;
  }

  .highlight-example {
    grid-template-columns: 1fr;
  }
}
```

---

## Notes

- The front contains only prompt-side highlight fields: word, optional IPA, word audio, example sentence, sentence audio, and optional image.
- The back reuses `{{FrontSide}}`, then reveals a Definition answer area after a single answer divider.
- The `Image` field renders only when populated so blank image exports do not create placeholders.
