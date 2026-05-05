# Alterações e Novas Ideias

---

## 1. Nova fonte de palavras — Highlights do Kindle

- Os highlights dos livros que estou lendo são exportados para: `https://otaru.infini-cloud.net/dav/`
- Os highlights serão a nova base para gerar os cards, substituindo o `wordfreq`
- Uso o Kindle Formatter (https://pch.github.io/kindle-formatter/) para normalizar os highlights — ele separa cada highlight por vírgula, e a IA consegue entender as palavras a partir disso

**Dúvida em aberto:** Tem como o sistema fazer isso automaticamente? Ir até onde estão os highlights, formatar e gerar o deck?

---

## 2. Novo template para o deck de highlights

O template atual (usado no deck gerado pelo `wordfreq`) não serve para esse novo tipo de card.

**Problema com o template atual:**
- Front: palavra, IPA, definition, example sentence
- Back: tudo do front + translation

**O que muda no novo deck:**
- `Definition` passa para o back
- Não há campo `Translation`

**Opções disponíveis:**

Opção A — Criar um novo template com base no template atual do wordfreq

Opção B — Modificar o template abaixo, que já atende os requisitos de layout mas tem dois problemas:
- O conteúdo fica muito no topo, não está centralizado
- Não tem a mesma responsividade do template atual

**Template (Opção B):**

Front:
```html
<div class="card front">
  <div class="word">{{Palavra}}</div>

  {{#IPA}}<div class="ipa">{{IPA}}</div>{{/IPA}}

  <hr class="divider">

  {{#Audio}}
  <div class="audio-controls">
    {{Audio}}
  </div>
  {{/Audio}}

  {{#Exemplo}}<div class="example">{{Exemplo}}</div>{{/Exemplo}}

  <script>
    const audio = document.querySelector('audio');
    if (audio) {
      audio.play().catch(e => console.log("Auto-play bloqueado pelo navegador"));
    }

    document.querySelector('.replay-button')?.addEventListener('click', () => {
      if (audio) {
        audio.currentTime = 0;
        audio.play();
      }
    });
  </script>
</div>
```

Back:
```html
<div class="card back">
  {{FrontSide}}

  <hr class="answer-divider">

  <div class="meaning">{{Significado}}</div>

  {{#Imagem}}<div class="image-container">{{Imagem}}</div>{{/Imagem}}
</div>
```

Style:
```css
.card {
  text-align: center;
  color: #e0e0e0;
  background-color: #121212;
  padding: 5px;
  border-radius: 15px;
  border: 1px solid #222;
  width: 100%;
  font-family: serif;
  margin: 0 auto;
  box-sizing: border-box;
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

**Se for usar a Opção B, as seguintes alterações são necessárias:**
- Renomear os fields para inglês (impacta front, back e style)
- Corrigir o alinhamento/centralização
- Melhorar a responsividade

---

## 3. Geração das frases

- As frases podem ter composição gramatical mais complexa
- Não devem ser muito extensas

---

## 4. Template para cards de fonética

**O que muda:**
- Usar o HTML abaixo como front
- No back: mostrar o `Sentence Translation` (igual ao card normal)
- Remover os campos: `Notes`, `is_priming`, `is_sentence`
- Mudar o style para as mesmas cores do card multilang

**Template do front:**
```html
<div class="customCard cardBack">
  <div class="targetWordContainer">
    <div class="targetWordBox">
      <div class="hint">The letter(s) is:</div>
      <span class="targetIPA"> {{Spellings}} </span>
    </div>
    <div class="row centerVertically" style="margin-bottom: -8px">
      <div class="hint">Sounds like:</div>
      <div class="indent centerVertically">
        <span class="targetIPA"> {{Sound}} </span>
        <span class="wordAudioButton"> {{letter_audio}} </span>
      </div>
    </div>
  </div>

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">example word:</div>
    <div class="centerVertically" style="margin-top: -8px">
      <div class="indent centerVertically">
        <span class="exampleWord"> {{Example Word}} </span>
        <span class="wordAudioButton"> {{word_audio}} </span>
      </div>
      <div class="sentenceTranslation">{{Word Translation}}</div>
    </div>
  </div>

  <div class="dividerLine"></div>

  <div class="horizontalPadding">
    <div class="header">example sentence:</div>
    <div class="indent">
      <div class="centerVertically">
        <span class="exampleWord">{{Example Sentence}}</span>
        <span class="wordAudioButton"> {{sentence_audio}} </span>
      </div>
      <div id="sentenceTranslation" class="sentenceTranslation">
        {{hint:Sentence Translation}}
      </div>
    </div>
  </div>

  {{#Notes}}
  <div class="dividerLine"></div>
  <div class="horizontalPadding">
    <div class="header">additional notes:</div>
    <div class="indent">
      <div class="centerVertically">
        <span class="exampleWord">{{Notes}}</span>
      </div>
    </div>
  </div>
  {{/Notes}}

</div>
```
