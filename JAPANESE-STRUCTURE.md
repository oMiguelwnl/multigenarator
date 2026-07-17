# Japonês: base para discussão do milestone

Este arquivo serve como base para discutir um novo milestone GSD sobre suporte a
**Japonês no pipeline principal `generate`** do Multilang. Ele segue o mesmo
espírito do `LATIN-STRUCTURE.md`: registrar direção, decisões já tomadas,
desafios específicos, ferramentas candidatas e uma proposta de fases com
requisitos e critérios de sucesso.

## Situação atual (o que já existe)

O japonês já entrou no projeto como **decks isolados**, no mesmo padrão dos decks
de fonema e do Latim MVP — **fora** do pipeline `generate`:

- `SupportedLanguage.JA = "ja"` e voz Azure `ja-JP-NanamiNeural` registrados.
- Note type `Multilang::Japanese Card` + template `japanese_card.md` (frente
  sentence-first com toggle de furigana, verso em português, Jisho/Weblio).
- `japanese_frequency_deck` — 12 cards curados de exemplo (`export-japanese`).
- `japanese_kana_deck` — importador de kana a partir de `.apkg` (`export-kana --from`).
- `japanese_kana_generated_deck` — kana 100% gerado, 208 cards (`export-kana`).

**O gap que este milestone resolve:** `generate --language ja` ainda **não**
produz um deck de frequência japonês real. Falta lista de frequência congelada,
furigana automática, mineração/geração de frases, tradução PT validada e
roteamento do `generate`/`card_template_loader`/`exporting` para o note type
japonês (como o `la` é tratado hoje).

Os decks de kana (isolados) **não** fazem parte deste milestone e continuam como
estão.

## Direção geral

Gerar decks Anki de japonês por **frequência de lemas**, com:

- palavra-alvo com leitura (furigana);
- frase-exemplo natural contendo a palavra-alvo;
- furigana da frase inteira;
- tradução curta da palavra e da frase em **português**;
- áudio da palavra e da frase (Azure `ja-JP`);
- campo de imagem vazio para preenchimento manual.

Modelo de card já decidido: **FRPG+ (português) + toggle de furigana do JP1K**,
que já é o `japanese_card.md`. Este milestone reaproveita esse note type/template.

## Decisões já tomadas

- Idioma alvo: Japonês moderno padrão.
- Tradução e explicações: Português.
- Organização principal: por frequência de lema.
- Unidade principal: lema (palavra de dicionário), com leitura.
- Modelo de card: `Multilang::Japanese Card` (FRPG+ + furigana toggle).
- Áudio: palavra e frase, Azure `ja-JP`.
- Furigana: formato nativo do Anki `漢字[かな]`, renderizado via `{{furigana:...}}`.
- Kana e frequência são coisas separadas; kana já está pronto e fora deste milestone.

## Desafios específicos do japonês (o que difere do Latim/línguas europeias)

1. **Sem espaços entre palavras** → é obrigatório um tokenizador morfológico
   para segmentar, achar o lema e a classe gramatical.
2. **Leituras (furigana)** → cada palavra com kanji precisa da leitura correta
   *no contexto*; a mesma grafia pode ter leituras diferentes.
3. **Alinhamento furigana** → transformar "leitura da palavra" em brackets por
   run de kanji (`父親[ちちおや]`, `今年[ことし]`) exige alinhar superfície×leitura.
4. **Frequência por lema** → contar por lema, não por forma de superfície.
5. **Pitch accent** (opcional) → o deck FRPG+ original tinha; exige dicionário
   de pitch. **Proposta: deferir** para um milestone futuro.

## Ferramentas candidatas

| Necessidade | Candidata principal | Alternativa | Confiança |
|---|---|---|---|
| Frequência (bootstrap) | `wordfreq` (`ja`) | lista curada de corpus | ALTA |
| Tokenização + lema + leitura | `fugashi` + `unidic-lite` | `SudachiPy` | ALTA |
| Furigana (alinhamento) | formatador próprio sobre leituras do fugashi | `pykakasi` (menos preciso em contexto) | MÉDIA |
| Tradução PT | DeepL (`JA`→`PT`) | LLM como fallback/QA | ALTA |
| Áudio | Azure Speech `ja-JP` (já registrado) | — | ALTA |
| Frases-exemplo | geração LLM aterrada + validação | frases curadas/reference | MÉDIA |

Ponto para discutir: `fugashi+unidic-lite` (leve, padrão) vs `SudachiPy` (formas
normalizadas). Recomendação inicial: **fugashi + unidic-lite**.

## Schema do card (reaproveitado)

Campos do note type `Multilang::Japanese Card` já existentes:

```json
{
  "language_code": "ja",
  "sort_index": 1,
  "target_word": "父親",
  "word_reading": "父親[ちちおや]",
  "definition_pt": "pai",
  "sentence": "父親は今年50歳になる。",
  "sentence_furigana": "父親[ちちおや]は 今年[ことし]50 歳[さい]になる。",
  "sentence_translation_pt": "Meu pai faz 50 anos este ano.",
  "word_audio": "...mp3",
  "sentence_audio": "...mp3",
  "frequency_rank": 1,
  "frequency_source": "wordfreq-ja + curadoria",
  "review_status": "needs_review"
}
```

## Escopo: começar por um MVP

Assim como o Latim começou com 50 cards revisados (não 3000), a recomendação é
**começar pequeno e verificável**:

- **Opção A (recomendada): MVP de 100 cards** (nível 1 parcial) para validar
  furigana, frases, tradução, áudio e o roteamento no `generate`.
- Opção B: piloto de 300–1000 cards (nível 1 completo).
- Opção C: estrutura final 3 níveis × 1000 (deferida até o MVP provar o pipeline).

## Proposta de milestone: v2.2 — Japanese Frequency Deck via `generate`

Numeração de fases contínua a partir da Fase 29 (Latim). Milestone **v2.2**.

### Fase 30: Contratos e roteamento do modo Japonês
**Objetivo**: `generate --language ja` roteia para um caminho japonês dedicado
(note type/field set japonês), sem quebrar frequency/word-list/highlight/
phonetics/latin/export existentes.
**Requisitos**: JMODE-01, JMODE-02, JMODE-03
**Critérios de sucesso**:
  1. `generate --language ja` seleciona o note type/template japonês, não o `normal_card`.
  2. `card_template_loader` e `exporting` reconhecem o field set japonês (como fazem com `la`).
  3. Todos os modos e idiomas existentes continuam funcionando (regressão isolada).
  4. Contratos/enums japoneses adicionados sem mutar contratos shipados.

### Fase 31: Lista de frequência e lemas
**Objetivo**: lista de frequência japonesa congelada, por lema, com leitura.
**Requisitos**: JFREQ-01, JFREQ-02, JFREQ-03
**Critérios de sucesso**:
  1. Bootstrap com `wordfreq(ja)` + tokenização (`fugashi`) gera candidatos por lema.
  2. Asset congelado `assets/frequency/ja/curated-vN.csv` com lema, leitura, rank e nível.
  3. Filtragem de ruído (pontuação, partículas isoladas, duplicatas de superfície) documentada.
  4. Tamanho do MVP (ex.: 100) fixado e validado pelo loader (fail-closed em contagem/ordem).

### Fase 32: Furigana e leituras
**Objetivo**: leitura da palavra-alvo e furigana da frase inteira, no formato Anki.
**Requisitos**: FUR-01, FUR-02, FUR-03
**Critérios de sucesso**:
  1. `fugashi+unidic` produz leitura contextual; conversor katakana→hiragana.
  2. Alinhamento superfície×leitura gera `漢字[かな]` por run de kanji, com espaçamento correto.
  3. Gate de validação: toda palavra com kanji tem leitura; ambiguidade é sinalizada e bloqueia até revisão.
  4. Cobertura de kanji verificada (nenhum kanji sem leitura no campo furigana).

### Fase 33: Frases-exemplo e ordenação
**Objetivo**: cada card tem uma frase natural contendo a palavra-alvo.
**Requisitos**: JSENT-01, JSENT-02, JSENT-03
**Critérios de sucesso**:
  1. Frase gerada/curada contém exatamente a palavra-alvo (verificado por token).
  2. Limites de tamanho (em tokens/caracteres) aplicados; frases longas/ambíguas rejeitadas.
  3. Proveniência da frase registrada (gerada/curada/reference), sem apresentar gerada como citação.
  4. (Opcional) ordenação i+1: priorizar frases que introduzem pouco vocabulário novo.

### Fase 34: Qualidade da tradução em português
**Objetivo**: glossa da palavra e tradução da frase em PT que combinam com o contexto.
**Requisitos**: JPT-01, JPT-02, JPT-03
**Critérios de sucesso**:
  1. DeepL `JA`→`PT` para palavra e frase; LLM só como QA/reparo.
  2. Validador determinístico: sem vazamento de inglês, sem glossa fora de contexto.
  3. Evidência de QA de tradução visível antes de aprovar o card.

### Fase 35: Política e integridade de áudio japonês
**Objetivo**: áudio de palavra e frase Azure `ja-JP`, com metadados e checagem exata.
**Requisitos**: JAUD-01, JAUD-02, JAUD-03
**Critérios de sucesso**:
  1. Todo card final tem áudio de palavra e de frase reproduzíveis; ausência bloqueia export.
  2. Cada artefato registra provider, versão, voz, texto gerado, hash e tipo de áudio.
  3. Export bloqueado quando o texto do áudio não bate com a palavra/frase exportada.

### Fase 36: Export e evidência do milestone
**Objetivo**: `generate --language ja` ponta a ponta → export `.apkg`/CSV/TSV.
**Requisitos**: JEXP-01, JEXP-02, JEVID-01, JEVID-02
**Critérios de sucesso**:
  1. Export usa o note type japonês com ordem de campos estável e mídia empacotada.
  2. Evidência de import/playback no Anki para um lote MVP.
  3. Evidência scanner-readable cobrindo todos os requisitos do milestone.
  4. Evidência de que nenhum modo/idioma existente regrediu.

## Cobertura de requisitos (proposta)

| Requisito | Fase |
|-----------|------|
| JMODE-01..03 | 30 |
| JFREQ-01..03 | 31 |
| FUR-01..03 | 32 |
| JSENT-01..03 | 33 |
| JPT-01..03 | 34 |
| JAUD-01..03 | 35 |
| JEXP-01..02, JEVID-01..02 | 36 |

## Dependências novas previstas

- `fugashi` + `unidic-lite` (tokenização, lema, leitura).
- `wordfreq` já está no projeto (`ja` suportado).
- DeepL já está no projeto (checar cota/`JA`→`PT`).
- Azure `ja-JP` já registrado.

## Deferidos deste milestone

- Pitch accent (precisa de dicionário de pitch; futuro).
- Escala além do MVP (300 / 1000 / 3×1000).
- Múltiplos cards por lema (uma frase por sentido/leitura).
- Mineração de frases de corpus real (o MVP pode usar geração aterrada + revisão).

## Decisões padrão adotadas (defaults recomendados)

Estas ficam como padrão de execução; podem ser revistas antes de cada fase.

1. **Tokenizador:** `fugashi + unidic-lite` (leve, padrão, leitura contextual).
2. **Tamanho do MVP:** **100 cards** revisados, para provar o pipeline antes de escalar.
3. **Frases:** **geração LLM aterrada + validação** (palavra-alvo presente, tamanho,
   furigana), com revisão humana no MVP.
4. **Ordenação i+1:** **deferida** para depois do MVP (entra como heurística de
   ordenação, não como bloqueio).
5. **Revisão humana:** obrigatória para furigana e tradução no MVP (gates fail-closed).
6. **Fonte no `generate`:** reutilizar `--source frequency` com roteamento por
   `--language ja` (como o `la` faz), sem criar um `--source` novo.
7. **Pitch accent:** deferido (precisa de dicionário de pitch; milestone futuro).

## Pontos ainda abertos (não bloqueiam iniciar a Fase 30)

- Escala pós-MVP (300 / 1000 / 3×1000) e política de múltiplos cards por lema.
- Uso futuro de corpus real para mineração de frases além da geração aterrada.
