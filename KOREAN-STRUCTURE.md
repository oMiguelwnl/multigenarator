# Coreano: estrutura do milestone v3.0

Este documento registra a direção de produto e implementação para integrar coreano moderno padrão ao Multilang. A especificação normativa está em `.planning/SPEC.md`; as Fases 30-34 estão em `.planning/ROADMAP.md`.

## Direção Geral

- Idioma interno: `ko`.
- Locale de conteúdo, tradução e TTS: `ko-KR` quando o provider exigir locale.
- Variante: coreano moderno padrão de Seul.
- Traduções e explicações: português.
- Forma de escrita principal: Hangul normalizado em Unicode NFC.
- Áudio padrão: Azure Speech com uma voz `ko-KR` explicitamente qualificada.
- Unidade lexical: lema + classe gramatical + sentido.
- Imagem: campo `Image` vazio para preenchimento manual.
- Romanização: orientação temporária, nunca fonte de pronúncia nem dependência dos decks de frequência.

## Famílias De Deck

```text
Multilang Korean::Foundations::Hangul
Multilang Korean::Foundations::Pronunciation i+1
Multilang Korean::Vocabulary::Frequency::Level 1
Multilang Korean::Vocabulary::Frequency::Level 2
Multilang Korean::Vocabulary::Frequency::Level 3
Multilang Korean::Grammar::Particles & Endings
Multilang Korean::Personal::Custom
Multilang Korean::Personal::Highlights
```

| Deck | Unidade nova | Política i+1 | Template-base |
|------|--------------|--------------|---------------|
| Hangul | jamo, bloco ou regra ortográfica | estrita após bootstrap | `japanese_kana_card.md` |
| Pronunciation | contraste ou regra fonológica | estrita | `russian_phoneme_card.md` |
| Frequency | lema/sentido | adaptativa | `normal_card.md` |
| Particles & Endings | construção forma-função-registro | estrita | `normal_card.md` |
| Custom | item fornecido pelo usuário | adaptativa | contrato manual existente |
| Highlights | item extraído da leitura | contextual/adaptativa | `highlight_card.md` |

Os nomes representam subdecks Anki reais. Apenas adicionar tags de nível dentro de um único deck não satisfaz o contrato final de três níveis.

## Contrato i+1

O uso de `i+1` neste projeto é uma regra curricular executável, não uma alegação de que a hipótese linguística original define exatamente um item desconhecido por flashcard.

```text
observed = orthography ∪ phonology ∪ grammar ∪ lexicon
unknown = observed - mastered_or_curriculum_known
strict_i_plus_1 = unknown == {target_concept_id}
```

Cada nota curricular armazena:

```text
target_concept_id
prerequisite_concept_ids
observed_concept_ids
unknown_concept_ids
i_plus_1_policy: strict | adaptive | contextual
sequence
```

`curriculum_i_plus_1` significa que os pré-requisitos aparecem antes na sequência. Isso não prova que um aluno específico já dominou esses itens. Uma futura integração com estado de revisão poderá distinguir `learner_i_plus_1`.

### Onde i+1 é estrito

- Hangul: uma única relação grafema-som, composição de bloco ou regra ortográfica nova.
- Pronunciation: um único contraste, alofone contextual ou processo fonológico novo.
- Particles & Endings: uma única construção forma-função-registro nova.

### Onde i+1 é adaptativo

- Frequency: o lema-alvo é novo e a frase minimiza outros conceitos desconhecidos.
- Custom: a prioridade do usuário é preservada; cards podem receber bridge/defer.
- Highlights: o trecho autêntico pode ser `i+n`; um microexemplo controlado reduz a novidade.

## Deck Hangul

O deck reaproveita a estrutura visual do template de kana, mas usa note type, IDs, labels e fontes próprios para coreano.

### Campos pedagógicos

```text
SortIndex
Category
JamoOrBlock
ReadingOrName
Sound
Mnemonic
Picture
Strokes
Gif
Audio
TargetConceptId
PrerequisiteConceptIds
```

### Sequência

| Etapa | Conteúdo |
|-------|----------|
| H0 | Orientação: jamo, bloco silábico, arranjo C(G)V(C), vogais horizontais e verticais |
| H1 | Vogais básicas `ㅏ ㅓ ㅗ ㅜ ㅡ ㅣ` |
| H2 | Ataque nulo `ㅇ` e composição de blocos com vogais conhecidas |
| H3 | Ataques básicos `ㄴ ㅁ ㄹ ㄱ ㄷ ㅂ ㅈ ㅅ ㅎ` |
| H4 | Vogais iotizadas e distinções ortográficas `ㅑ ㅕ ㅛ ㅠ ㅐ ㅔ ㅒ ㅖ` |
| H5 | Consoantes aspiradas `ㅋ ㅌ ㅍ ㅊ` e tensas `ㄲ ㄸ ㅃ ㅆ ㅉ` |
| H6 | Vogais compostas `ㅘ ㅝ ㅙ ㅞ ㅚ ㅟ ㅢ` |
| H7 | Posição batchim e sete categorias de coda `[ㄱ ㄴ ㄷ ㄹ ㅁ ㅂ ㅇ]` |
| H8 | Grafias alternativas de coda e encontros consonantais |
| H9 | Ortografia morfofonêmica e espaçamento básico |
| H10 | NFC/NFD, teclado, pontuação, números e texto misto |

Os nomes tradicionais dos jamo só entram quando sua grafia já puder ser decodificada. Compatibility Jamo e halfwidth Hangul não são aceitos silenciosamente como conteúdo canônico.

## Deck Pronunciation i+1

O deck reutiliza exatamente o contrato visual fonético existente:

```text
Spellings
Sound
letter_audio
Example Word
word_audio
Word Translation
Example Sentence
sentence_audio
Sentence Translation
```

Metadados curriculares e fonológicos ficam no registro-fonte mesmo quando não aparecem como campos de estudo.

### Exemplo

```text
Spellings: ㄱ + ㅁ
Sound: /ŋm/ - nasalização
Example Word: 국물
Word Translation: caldo
Example Sentence: 국물이 뜨거워요.
Sentence Translation: O caldo está quente.
Surface Pronunciation: [궁무리 뜨거워요]
```

Nesse ponto da sequência, liaison já deve ser conhecida. A única novidade curricular é a nasalização.

### Sequência fonológica

| Etapa | Conteúdo |
|-------|----------|
| P0 | Ritmo silábico, vogais, ataque nulo e sonorantes; `ㄹ` intervocálico versus coda |
| P1 | Contrastes de ataque `ㅂ/ㅃ/ㅍ`, `ㄷ/ㄸ/ㅌ`, `ㄱ/ㄲ/ㅋ`, `ㅈ/ㅉ/ㅊ`, `ㅅ/ㅆ`, `ㅎ` |
| P2 | Batchim simples, codas não liberadas e neutralização em sete categorias |
| P3 | Liaison antes de morfema iniciado por vogal: `옷이 [오시]`, `먹어 [머거]` |
| P4 | Tensificação pós-obstruinte: `먹다 [먹따]`, `학교 [학꾜]` |
| P5 | Nasalização: `국물 [궁물]`, `받는 [반는]`, `앞문 [암문]` |
| P6 | Aspiração envolvendo `ㅎ`: `좋다 [조타]`, `입학 [이팍]` |
| P7 | Palatalização: `굳이 [구지]`, `같이 [가치]` |
| P8 | Assimilação líquida, processos relacionados e inserção de `ㄴ` |
| P9 | Codas complexas e alternâncias: `읽다 [익따]` versus `읽어 [일거]` |
| P10 | Contrações regulares: `보아요→봐요`, `주어요→줘요`, `되어요→돼요`, `하여요→해요` |
| P11 | Reduções conversacionais opcionais, sempre marcadas por registro |
| P12 | Frase acentual, foco, entonação e efeitos de velocidade |
| P13 | Interação e ordenação cumulativa de regras já conhecidas |

As oclusivas coreanas não são ensinadas como uma simples oposição surda/sonora do inglês. Contrastes modernos de Seul envolvem VOT, F0 e qualidade fonatória.

### Política de áudio fonético

- Não enviar um jamo cru ao TTS e assumir que o resultado é o fonema.
- Para nome de letra, sintetizar o nome coreano aprovado ou usar gravação humana.
- Para som consonantal, usar contexto explícito de sílaba/coda ou gravação humana.
- Para contraste e regra fonológica, preferir gravação humana revisada.
- TTS de regra permanece `needs_review` até aprovação de especialista e falante nativo independente.
- Mudança de provider, voz, SSML, prosódia ou forma esperada cria nova versão de asset.

## Deck Frequency

### Estrutura final

- Level 1: ranks 1-1000.
- Level 2: ranks 1001-2000.
- Level 3: ranks 2001-3000.
- Unidade: lema + POS + sentido, não eojeol nem forma flexionada.
- Partículas e terminações produtivas são encaminhadas ao deck gramatical.

### Card

O template inicial é `normal_card.md`:

```text
SortIndex
word
IPA
Definitions
Example Sentence
Translation
word_audio
sentence_audio
Image
```

Mapeamento coreano:

```text
word = lema Hangul na forma de dicionário
IPA = pronúncia normativa validada
Definitions = classe + glossa contextual em português
Example Sentence = frase padrão de Seul contendo uma realização do lema
Translation = tradução contextual da frase em português
Image = ""
```

O lema e a forma exibida/sonorizada devem ter contrato explícito. O áudio da palavra não pode ser sintetizado para uma forma e validado/exportado contra outra.

### Frequência e licença

`wordfreq("ko")` pode gerar candidatos, mas não é fonte de verdade final:

- a lista é tokenizada, não um currículo por lema;
- formas flexionadas e morfemas ligados exigem análise;
- homógrafos exigem POS/sentido;
- a documentação do projeto alerta contra extração para CSV sem preservar atribuição/licença.

Antes de congelar `assets/frequency/ko/curated-vN.csv`, o projeto precisa registrar uma decisão de fonte e redistribuição. Opções:

1. uso interno de `wordfreq` com revisão jurídica/atribuição adequada;
2. geração local sem redistribuir o asset derivado;
3. corpus com termos compatíveis com distribuição do resultado;
4. permissão explícita para o derivado curado.

### Pipeline de curadoria

1. Normalizar candidato em NFC.
2. Analisar com versão fixada de Kiwi.
3. Rejeitar símbolos, URLs, dígitos, jamo isolado e script misto inadequado.
4. Separar partículas, terminações, nomes próprios, OOV e análises ambíguas.
5. Converter verbos/adjetivos simples para forma de dicionário terminada em `다`.
6. Preservar assinatura de predicados compostos como `공부/NNG + 하/XSV`.
7. Aterrar lema, POS e sentido em fonte lexical aprovada.
8. Agregar formas somente quando a identidade lexical for inequívoca.
9. Ordenar deterministicamente e manter reserva para substituições.
10. Revisar e congelar exatamente 3000 entradas.

### i+1 adaptativo

O ranking lexical continua sendo o eixo do deck. A escolha da frase recebe um score secundário:

- lema-alvo novo;
- cobertura máxima por conceitos anteriores;
- poucas regras gramaticais/fonológicas incidentais;
- comprimento curto;
- naturalidade obrigatória;
- registro consistente;
- nenhuma frase deformada apenas para atingir a métrica.

## Deck Particles & Endings

Esse deck ensina morfemas ligados e construções que não devem ocupar ranks do deck lexical.

### Card

```text
word: 은/는
Definitions: marcador de tópico; 은 após consoante, 는 após vogal
Example Sentence: 저는 학생이에요.
Translation: Eu sou estudante.
word_audio: amostra aprovada da construção
sentence_audio: frase completa
Image: ""
```

### Sequência gramatical

| Etapa | Conteúdo |
|-------|----------|
| G0 | Ordem predicado-final, omissão de argumento, forma `-다`, stem, noun/verb/adjective, `이에요/예요` |
| G1 | `은/는`, `이/가`, `을/를`, presente `-아요/어요`, `하다→해요` |
| G2 | `에`, `에서`, `있다/없다`, posse `의` |
| G3 | `도`, `만`, `와/과`, `하고`, `(이)랑` |
| G4 | `에게/한테`, `(으)로`, `부터/까지`, `보다` |
| G5 | `안`, `못`, `-지 않다`, passado, futuro/intenção, progressivo |
| G6 | Desejo, capacidade, pedido e honorífico |
| G7 | Paradigmas irregulares `ㅡ`, `ㄹ`, `ㅂ`, `ㄷ`, `르`, `ㅅ`, `ㅎ` |
| G8 | Conectores `-고`, `-아/어서`, `-지만`, `-(으)면`, `-(으)니까`, `-는데` |
| G9 | Formas adnominais de adjetivo, verbo e nome |
| G10 | Nominalização e substantivos dependentes como `것` e `수` |
| G11 | Estilos formal, polido, informal e escrito/plain |
| G12 | Obrigação, permissão, proibição, tentativa, experiência e conjectura |
| G13 | Discurso reportado, passivo/causativo e formas discursivas avançadas |

Cada card estrito apresenta uma construção forma-função-registro. Um par alomórfico como `은/는` conta como um conceito quando as condições de seleção são apresentadas juntas.

## Deck Custom

O modo preserva:

```text
submitted_form
canonical_nfc
resolved_lemma
part_of_speech
sense_id
input_order
```

Exemplos:

- `먹었어요` pode resolver para `먹다`, preservando a forma enviada.
- `공부하다` não pode ser reduzido silenciosamente ao substantivo `공부`.
- Ambiguidade de homógrafo/POS entra em `needs_review`.
- Item com pré-requisitos excessivos pode receber bridge cards ou ser deferido.

## Deck Highlights

O parser de arquivo/WebDAV e os controles de privacidade existentes são reutilizados. A extração precisa ser coreana:

- não descartar palavras válidas de uma sílaba como `물`, `집` e `말`;
- não tratar eojeol com partícula/terminação como lema final;
- deduplicar por lema + POS + sentido;
- preservar expressões multiword relevantes;
- distinguir trecho autêntico de microexemplo gerado;
- enviar ao provider apenas contexto redigido e limitado;
- nunca exportar caminho local privado ou texto-fonte excessivo.

O trecho autêntico é classificado como contextual `i+n`. O microexemplo pode receber score adaptativo i+1, mas não alegação estrita sem satisfazer o grafo completo.

## Morfologia E Validação

### Analisador principal

Recomendação: `kiwipiepy`/Kiwi fixado em versão compatível com Python 3.12. Stanza pode atuar como validador secundário de sintaxe; KoNLPy não é recomendado como nova base devido a stack JVM/metadados antigos.

### Assinaturas

| Alvo | Assinatura lexical | Frase válida |
|------|--------------------|--------------|
| `학교` | `학교/NNG` | `학교에서 공부해요` |
| `먹다` | `먹/VV` | `밥을 먹었어요` |
| `예쁘다` | `예쁘/VA` | `꽃이 예뻐요` |
| `공부하다` | `공부/NNG + 하/XSV` | `매일 한국어를 공부해요` |

Regras:

- retirar partículas e terminações inflexionais da comparação;
- preservar morfemas derivacionais `XSV`/`XSA`;
- normalizar variantes de tag regular/irregular;
- exigir predicados compostos dentro do mesmo eojeol;
- usar POS lexical para resolver homógrafos;
- OOV ou ambiguidade não resolvida exige retry/review;
- indisponibilidade do Kiwi falha fechada para coreano.

### Unicode

- Normalizar entradas, lookup keys, frequência, persistência e comparação em NFC.
- Não usar NFKC indiscriminadamente no conteúdo do aluno.
- Rejeitar Compatibility Jamo e halfwidth Hangul no conteúdo canônico.
- Tratar equivalência NFC/NFD nos testes de deduplicação.

## Texto E Tradução

- Frases em coreano moderno padrão de Seul.
- Classe e sentido do alvo explícitos na geração.
- Tradução da glossa e frase em português.
- DeepL `KO` como tradutor primário quando o inventário vivo confirmar source/target utilizáveis.
- LLM somente para geração aterrada, QA ou reparo controlado.
- Sem Tatoeba como fonte padrão; qualquer uso de referência preserva licença/proveniência e passa revisão.
- Bloquear vazamento de inglês, sujeito inventado na tradução, sentido incompatível, mistura de níveis de fala e padrão repetitivo/artificial.

## Áudio

### Provider padrão

- Azure Speech.
- Locale: `ko-KR`.
- Voz: uma `ShortName` GA selecionada por inventário vivo e review auditivo.
- Não selecionar automaticamente voz preview/HD apenas por ser mais nova.
- Sem fallback silencioso após esgotar retries.
- Google Translate consumer TTS não entra no caminho de produção.
- Google Cloud ou ElevenLabs só podem virar profiles explícitos depois de qualificação coreana própria.

### Metadados mínimos

```text
audio_kind
language=ko
locale=ko-KR
display_text
spoken_text
text_nfc
text_hash
provider
provider_version
voice_short_name
voice_catalog_status
voice_catalog_checked_at
ssml_hash
output_format
artifact_hash
duration
storage_path
review_status
reviewed_artifact_hash
reviewer_role
generation_or_rejection_reason
```

Somente artifacts `approved` e alinhados ao texto exato entram no export.

## Templates E Export

| Família | Estratégia |
|---------|------------|
| Hangul | Derivar layout de kana, trocar note type/IDs/labels/fontes e adicionar dados coreanos |
| Pronunciation | Reutilizar template fonético sem novo layout; generalizar nomes internos russos |
| Frequency | Reutilizar normal card e resolver schema por `(language, source_type)` |
| Grammar | Reutilizar normal card com definição forma-função-registro |
| Custom | Preservar contrato manual, com decisões coreanas explícitas no routing |
| Highlights | Reutilizar highlight template e privacidade, com extração coreana |

Todos os note types novos recebem IDs exclusivos. APKG empacota mídia; CSV/TSV preservam sound tags e manifest resolvível. Campos e templates não podem recalcular dados linguísticos congelados depois do snapshot.

## Gates De Revisão

Status:

```text
needs_review
approved
rejected
```

Bloqueios de export:

- morfologia ou sentido ambíguo;
- forma-alvo ausente segundo assinatura morfológica;
- pronúncia normativa/superficial incorreta;
- falso i+1;
- registro ou nível de fala inconsistente;
- tradução incompatível;
- áudio ausente, não aprovado ou divergente;
- asset lexical sem fonte/licença aprovada;
- mídia/campo/template incompleto;
- vazamento de contexto privado.

Review humano obrigatório:

- 100% do inventário Hangul;
- 100% do deck Pronunciation;
- 100% do deck Particles & Endings;
- todos os itens lexicais marcados por homografia, OOV, irregularidade ou baixa confiança;
- amostra estratificada de cada lote de frequência e toda mudança de provider/voz/prompt/policy.

## Estratégia De Entrega

### Gate MVP interno

- Hangul completo.
- Sequência inicial de Pronunciation.
- 100 lemas de frequência.
- Aproximadamente 30 construções gramaticais.
- Áudio, tradução, review e export reais.

Esse gate valida os contratos; ele não reduz o objetivo final do milestone.

### Objetivo final v3.0

- Hangul completo.
- Pronunciation i+1 completo no inventário aprovado.
- Frequency com três subdecks de 1000 cards.
- Particles & Endings completo no inventário aprovado.
- Custom e Highlights operacionais.
- APKG/CSV/TSV, revisão, mídia e evidência de não regressão.

## Fases

- Phase 30: contratos, registries, Kiwi, Unicode e target matching.
- Phase 31: Hangul e Pronunciation i+1.
- Phase 32: frequência, texto em português e Azure `ko-KR`.
- Phase 33: Particles & Endings, Custom e Highlights.
- Phase 34: export, revisão, renderização e evidência final.

## Dependência De Execução

O quick task 027 de Mandarim altera registries, persistência, áudio, templates e exporters compartilhados. A Fase 30 não deve ser executada sobre uma versão parcialmente concluída desse trabalho. Primeiro é necessário concluir, separar ou reconciliar a integração Mandarim e então planejar a Fase 30 contra a verdade resultante.

## Fontes Principais

- NIKL Hangul Orthography: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0001
- NIKL Standard Language/Pronunciation: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0002
- Korean Basic Dictionary/API: https://krdict.korean.go.kr/eng/openApi/openApiInfo
- NIKL Modu Corpus: https://kli.korean.go.kr/corpus/main/requestMain.do
- Kiwi/kiwipiepy: https://bab2min.github.io/kiwipiepy/v0.23.2/kr/
- Unicode normalization: https://www.unicode.org/reports/tr15/
- Azure Speech language/voice support: https://learn.microsoft.com/azure/ai-services/speech-service/language-support?tabs=tts
- Azure Korean phonetic set: https://learn.microsoft.com/azure/ai-services/speech-service/speech-ssml-phonetic-sets#ko-kr
- DeepL supported languages: https://developers.deepl.com/docs/getting-started/supported-languages
- wordfreq: https://github.com/rspeer/wordfreq

## Deferidos

- Hanja.
- Dialetos regionais.
- Romanização persistente no deck lexical.
- Aprovação automática de áudio fonético.
- Mineração/distribuição de corpus sem contrato de licença aprovado.
- Tutor interativo ou sincronização de mastery individual com o scheduler do Anki.

---
*Decisões aprovadas e formalizadas em 2026-07-20.*
