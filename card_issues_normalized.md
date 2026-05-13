# Correções e Padrões para Geração de Cards

Documento de referência com todos os erros identificados, regras de correção e padrões a serem aplicados em todos os decks.

---

## 1. Campo IPA

### Problema
O IPA está repetindo a palavra em vez de apresentar a transcrição fonética correta. O trecho entre parênteses que acompanha a transcrição é apenas uma repetição da palavra original, o que não representa a pronúncia.

**Exemplo do erro:**
- Word: `громко`
- IPA incorreto: `[ˈɡromkə] (гро́мко)` ← o `(гро́мко)` apenas repete a palavra

**Correção esperada:**
- IPA correto: `[ˈɡromkə]` ← apenas a transcrição fonética, sem repetir a palavra

### Regras
1. O campo IPA deve conter **somente** a transcrição fonética da palavra.
2. Nunca adicionar a palavra original (nem em forma acentuada) ao lado da transcrição.
3. Caso a transcrição fonética não possa ser determinada com certeza, utilizar a própria palavra como valor do campo IPA.

---

## 2. Campo Definition

### Problema 1 — Descrição de caso gramatical no lugar do significado

Alguns cards apresentam no campo Definition a descrição do caso gramatical da palavra em vez de seu significado semântico. Isso não é útil para o aprendizado de vocabulário.

**Exemplos do erro:**
- Word: `дальнего` → Definition: `adjective: masculine animate accusative singular`
- Word: `местности` → Definition: `noun: genitive/dative/prepositional singular`
- Word: `поги́бли` → Definition: `verb: short plural past indicative perfective of поги́бнуть (pogíbnutʹ)`

**Correção esperada:**
- O campo Definition deve sempre descrever o **significado** da palavra em inglês (ou no idioma padrão do projeto), de forma clara e direta.

### Problema 2 — Definition indicando "inflection" de outra palavra

Alguns cards informam que a palavra é uma inflexão de outra, em vez de apresentar o significado.

**Exemplo do erro:**
- Word: `заболевания` → Definition: `noun: inflection of заболева́ние (zabolevánije)`

**Correção esperada:**
- Nunca usar `inflection of` como valor da Definition.
- Apresentar o significado semântico da palavra, mesmo que ela seja uma forma flexionada.

### Problema 3 — Definition semanticamente incorreta

Alguns cards apresentam definições que não correspondem ao significado real da palavra.

**Exemplo do erro:**
- Word: `дости́чь` → Definition: `verb: to amount to, to come to`
- Significado correto: `verb: to achieve, to attain, to reach`

**Correção esperada:**
- Verificar a precisão semântica de cada Definition.
- Corrigir todos os casos onde o significado apresentado está errado ou impreciso.

### Regras
1. O campo Definition deve sempre descrever o **significado** da palavra, nunca seu caso gramatical.
2. Nunca utilizar as expressões `inflection of`, `genitive of`, `accusative of` ou similares como Definition.
3. Definições semanticamente incorretas devem ser corrigidas com o significado real da palavra.
4. Realizar análise completa do deck `dbda4eb2-f0ec-402b-864f-48cdcf982b09.apkg` para identificar todos os casos fora do padrão e criar regras de validação adicionais.

---

## 3. Campo Translation

### Problema
Em alguns cards, o campo Translation não corresponde ao Example Sentence — ele traduz a word isolada em vez de traduzir a frase de exemplo.

### Regras
1. O campo Translation deve ser a tradução direta do **Example Sentence**, não da word isolada.
2. Verificar e corrigir todos os decks para garantir essa correspondência.

---

## 4. Layout dos Cards

### Mudança 1 — Remoção do campo "Front of Card"

O campo `Front of Card` deve ser removido de todos os cards, pois seu conteúdo é idêntico ao campo `Word`, tornando-o redundante.

**Ação necessária:**
- Remover o campo `Front of Card` do template dos cards.
- Ajustar o CSS dos cards para que o layout não quebre após a remoção do campo.

### Mudança 2 — Posicionamento do ícone `sentence_audio`

O ícone/imagem do `sentence_audio` deve estar sempre posicionado **ao lado** do Example Sentence, independentemente do tamanho da tela. Atualmente, em telas maiores ele é exibido abaixo do texto.

**Comportamento atual:**
- Telas pequenas: `sentence_audio` ao lado do Example Sentence ✓
- Telas grandes: `sentence_audio` abaixo do Example Sentence ✗

**Comportamento esperado:**
- Todos os tamanhos de tela: `sentence_audio` ao lado do Example Sentence ✓

**Ação necessária:**
- Ajustar o CSS para que o `sentence_audio` fique sempre posicionado ao lado do Example Sentence, utilizando `flexbox` ou equivalente com `flex-wrap: nowrap` ou regras de breakpoint adequadas.

---

## 5. Áudio

### Problema
Em alguns cards, o `word_audio` não corresponde à palavra exibida no campo `Word` — o áudio reproduz uma palavra diferente da que está sendo estudada.

### Regras
1. O áudio do campo `word_audio` deve corresponder **exatamente** à palavra exibida no campo `Word`.
2. Identificar e corrigir todos os cards com divergência entre `word_audio` e `Word`.

---

## Resumo das Ações

| # | Campo | Tipo | Ação |
|---|-------|------|------|
| 1 | IPA | Correção | Remover repetição da palavra; manter apenas a transcrição fonética |
| 2 | Definition | Correção | Substituir descrições de caso gramatical e "inflection of" pelo significado real |
| 3 | Definition | Correção | Corrigir definições semanticamente incorretas |
| 4 | Definition | Análise | Auditar deck `dbda4eb2...apkg` e criar regras de validação |
| 5 | Translation | Correção | Garantir que a tradução corresponde ao Example Sentence |
| 6 | Front of Card | Remoção | Remover campo e ajustar CSS |
| 7 | sentence_audio | Layout | Fixar posicionamento ao lado do Example Sentence em todas as telas |
| 8 | word_audio | Correção | Garantir que o áudio corresponde ao campo Word |
