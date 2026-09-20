# Mandarin Anki Card Template

This template preserves the original Multilang normal-card layout. Sentence ruby
and tone classes are rendered at export from saved pinyin; field names and model
identity remain unchanged. Saved sentence pinyin supplies ruby only; Traditional
Sentence appears in its own section below the example and translation.

---

## Front Template

```html
<div class="customCard cardBack mandarinCard" lang="zh-Hans">
  <div class="horizontalPadding centerVertically targetWordContainer">
    <div class="wordBlock">
      <span class="targetWord">{{word}}</span>
      {{#Pinyin}}<span class="ipa">{{Pinyin}}</span>{{/Pinyin}}
      {{#Traditional}}<span class="traditional">{{Traditional}}</span>{{/Traditional}}
    </div>
    <span class="wordAudioButtonBack">{{word_audio}}</span>
  </div>

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">Definição:</div>
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
    <div class="header">Exemplo:</div>
    <div class="examplePanel">
      <div class="exampleSentenceLine">
        <span class="exampleSentenceText">{{Example Sentence}}</span>
        <span class="sentenceAudioButton">{{sentence_audio}}</span>
      </div>
      <div id="translation" class="sentenceTranslation" style="display:none;">
        {{Translation}}
      </div>
    </div>
  </div>

  {{#Traditional Sentence}}
  <div class="dividerLine"></div>
  <div class="horizontalPadding mandarinTraditionalSection">
    <div class="header" lang="pt-BR">Tradicional:</div>
    <div class="traditionalSentence" lang="zh-Hant">{{Traditional Sentence}}</div>
  </div>
  {{/Traditional Sentence}}
</div>
```

---

## Back Template

```html
{{FrontSide}}

<script>
  document.getElementById("translation").style.display = "block";
</script>
```

---

## Styling (CSS)

```css
.traditional {
  color: #93c5fd;
  font-size: 15px;
  font-weight: 400;
  line-height: 1.45;
}

.traditionalSentence {
  color: #93c5fd;
  font-size: 14px;
  font-weight: 400;
  line-height: 1.45;
}

.nightMode .traditional,
.nightMode .traditionalSentence {
  color: #93c5fd;
}

/* Reading support adds annotation space without replacing the original layout. */
.mandarinCard .exampleSentenceText {
  font-family: "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
  font-size: 26px;
  line-height: 2.1;
}

.mandarinCard .examplePanel {
  padding-top: 6px;
}

.mandarinCard .sentenceTranslation {
  font-size: 18px;
  line-height: 1.6;
}

.mandarinCard .traditionalSentence {
  font-family: "Noto Sans CJK TC", "Microsoft JhengHei", sans-serif;
  font-size: 17px;
  line-height: 1.6;
}

.mandarin-ruby {
  display: ruby;
  ruby-position: over;
  ruby-align: center;
  margin: 0 0.04em;
}

.mandarin-ruby rt {
  color: inherit;
  font-family: Arial, sans-serif;
  font-size: 0.6em;
  font-weight: 500;
  line-height: 1.2;
  text-align: center;
}

.mandarin-ruby.tone-1 { color: #ff8591; }
.mandarin-ruby.tone-2 { color: #f1d178; }
.mandarin-ruby.tone-3 { color: #82dbab; }
.mandarin-ruby.tone-4 { color: #8ebaff; }
.mandarin-ruby.tone-5 { color: #c1c7d3; }

```
