# Mandarin Anki Card Template

This template extends the Multilang normal card without reference-deck code or assets.

---

## Front Template

```html
<div class="customCard cardBack">
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
    <div class="indent exampleSentenceLine">
      <span class="exampleSentenceText">{{Example Sentence}}</span>
      <span class="sentenceAudioButton">{{sentence_audio}}</span>
    </div>
    {{#Sentence Pinyin}}<div class="sentencePinyin indent">{{Sentence Pinyin}}</div>{{/Sentence Pinyin}}
    {{#Traditional Sentence}}<div class="traditionalSentence indent">{{Traditional Sentence}}</div>{{/Traditional Sentence}}
    <div id="translation" class="sentenceTranslation indent" style="display:none;">
      {{Translation}}
    </div>
  </div>
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
.traditional,
.sentencePinyin,
.traditionalSentence {
  color: var(--color-divider);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.45;
  opacity: 0.78;
}

.sentencePinyin,
.traditionalSentence {
  padding-top: 4px;
}

.nightMode .traditional,
.nightMode .sentencePinyin,
.nightMode .traditionalSentence {
  color: var(--color-nightMode-header);
}
```
