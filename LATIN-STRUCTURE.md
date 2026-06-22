# Latim classico: base para discussao do milestone

Este arquivo serve como base para discutir um novo milestone GSD sobre suporte a Latim no Multilang.

O escopo atual e somente Latim. Grego fica fora deste milestone.

## Direcao geral

O objetivo e criar decks Anki de Latim classico com vocabulario frequente, frases reais ou confiaveis, traducao em Portugues, audio da palavra e da frase, e um campo direto de gramatica que explique a forma da palavra dentro da frase.

O deck nao deve ser apenas uma lista de palavras. Ele deve ajudar o aluno a ler Latim dentro de frases, seguindo o metodo do Rafael Falcon como referencia didatica obrigatoria.

## Decisoes ja tomadas

- Idioma alvo: Latim.
- Variante: Latim classico.
- Traducao e explicacoes: Portugues.
- Metodo obrigatorio: Rafael Falcon.
- Organizacao principal: por frequencia.
- Unidade principal: lema.
- Exemplos: textos classicos e/ou fontes confiaveis com frases em Latim.
- Audio: palavra e frase.
- Campo `Classe` separado: nao precisa.
- Campo `Gramatica`: obrigatorio, curto e direto.
- Casos a reconhecer: `Nominativus`, `Vocativus`, `Accusativus`, `Genitivus`, `Dativus`, `Ablativus`.

Observacao: usar `Genitivus` como forma padrao no deck. `Genetivus` pode aparecer em anotacoes do usuario, mas a nomenclatura recomendada para o campo final e `Genitivus`.

## Metodo Rafael Falcon

O metodo Rafael Falcon deve guiar a progressao e o estilo do card.

Principios que o deck deve seguir:

- palavra sempre em contexto;
- frase em Latim como base de estudo;
- traducao contextual;
- foco em leitura real;
- explicacao gramatical objetiva;
- declinacao e caso claros;
- funcao sintatica clara;
- progresso do simples para o complexo;
- evitar cards soltos que nao ajudam a ler uma frase.

Ponto para discutir: como transformar o metodo Rafael Falcon em regras implementaveis no gerador.

Possiveis regras:

- comecar por frases com estrutura simples;
- priorizar nominativo, acusativo e verbos principais no primeiro lote;
- introduzir genitivo, dativo e ablativo gradualmente;
- evitar poesia muito complexa no primeiro nivel;
- usar textos classicos, mas selecionar frases didaticas;
- permitir frases adaptadas apenas se forem claramente marcadas como didaticas.

## Proposta de card

### Frente

- Palavra alvo na forma em que aparece na frase.
- Frase em Latim.
- Audio da palavra.
- Audio da frase.

### Verso

- Lema.
- Traducao curta da palavra em Portugues.
- Traducao da frase em Portugues.
- Gramatica.
- Fonte da frase.

Campo `Classe` separado nao entra no card. Se for necessario para processamento interno, pode existir no schema tecnico, mas nao precisa aparecer como campo de estudo.

## Campo `Gramatica`

O campo deve ser curto, direto e padronizado.

Formato preferido:

```text
virum: subst masc, 2a declinacao, Accusativus singularis, OD.
```

Esse campo deve dizer o que a palavra e naquela frase, nao fazer uma explicacao longa.

### Abreviacoes sugeridas

- `subst`: substantivo.
- `adj`: adjetivo.
- `pron`: pronome.
- `v`: verbo.
- `prep`: preposicao.
- `conj`: conjuncao.
- `adv`: adverbio.
- `masc`: masculino.
- `fem`: feminino.
- `neut`: neutro.
- `sg`: singular, se preferirmos abreviar.
- `pl`: plural, se preferirmos abreviar.
- `OD`: objeto direto.
- `OI`: objeto indireto.
- `Suj`: sujeito.
- `CN`: complemento nominal, se fizer sentido no modelo final.
- `Adj Adv`: adjunto adverbial, se fizer sentido no modelo final.

Ponto para discutir: manter `singularis/pluralis` por estilo latino ou usar `sg/pl` por brevidade.

### Casos obrigatorios

- `Nominativus`.
- `Vocativus`.
- `Accusativus`.
- `Genitivus`.
- `Dativus`.
- `Ablativus`.

### Exemplos de gramatica curta

```text
virum: subst masc, 2a declinacao, Accusativus singularis, OD.
```

```text
puella: subst fem, 1a declinacao, Nominativus singularis, Suj.
```

```text
Romae: subst fem, 1a declinacao, Genitivus singularis ou locativo, revisar contexto.
```

```text
cano: v, 3a conjugacao, 1a pessoa singular, praesens indicativus activus, verbo principal.
```

```text
cum: prep + Ablativus, introduz complemento circunstancial.
```

Ponto para discutir: se a gramatica deve usar termos latinos (`praesens indicativus activus`) ou portugueses (`presente do indicativo ativo`).

## Schema proposto do card

Campo de classe nao aparece como campo final do card.

```json
{
  "language_code": "la",
  "lemma": "vir",
  "target_form": "virum",
  "short_translation_pt": "homem",
  "latin_sentence": "Arma virumque cano.",
  "sentence_translation_pt": "Canto as armas e o homem.",
  "grammar": "virum: subst masc, 2a declinacao, Accusativus singularis, OD.",
  "source": "Vergil, Aeneid 1.1",
  "word_audio": "virum.mp3",
  "sentence_audio": "arma-virumque-cano.mp3",
  "frequency_rank": 1,
  "frequency_source": "pending",
  "review_status": "needs_review"
}
```

Ponto para discutir: se `lemma` deve aparecer na frente, no verso, ou ficar apenas como dado tecnico.

## Frequencia

O deck deve ser organizado por frequencia.

Como `wordfreq` nao cobre Latim, precisamos buscar outra ferramenta ou montar nossa propria frequencia a partir de corpus.

### Estrategia recomendada

1. Escolher corpus latino confiavel.
2. Lematizar as formas.
3. Contar frequencia por lema.
4. Selecionar frases boas para cada lema frequente.
5. Organizar cards por nivel.

### Ferramentas candidatas para frequencia e lematizacao

- CLTK: toolkit de linguas classicas; candidato para tokenizacao, corpus, lematizacao e processamento latino.
- Perseus Morph / Morpheus: candidato forte para analise morfologica de formas latinas.
- Collatinus: candidato para lematizacao e dados lexicais latinos.
- Whitaker's Words: candidato para analise morfologica e formas latinas.
- LemLat: candidato a avaliar para lematizacao latina.
- Universal Dependencies Latin treebanks: candidato para corpus anotado e avaliacao morfologica.
- Dickinson College Core Latin Vocabulary: candidato como lista pedagogica/frequencial de apoio.

Ponto para discutir: escolher uma ferramenta principal ou combinar varias com fallback.

Proposta inicial:

```text
CLTK/Perseus para corpus e morfologia + Collatinus/Whitaker como validadores + lista final curada pelo projeto.
```

## Fontes de frases

O usuario quer gerar a partir de textos classicos e tambem procurar algum site/lib que tenha frases em Latim.

### Fontes classicas ja discutidas

- Eneida / `VIRGILII AENEIS`.
- Disticha Catonis.

### Fontes candidatas para buscar frases

- Perseus.
- Dickinson College Commentaries.
- Latin Library.
- The Latin Library, se licenca/uso forem aceitaveis.
- DCC Core Vocabulary, como apoio de vocabulario.
- Corpus proprio criado a partir de textos classicos.

Ponto para discutir: se frases podem ser adaptadas para ficarem mais didaticas ou se devem ser sempre texto original.

## Audio

O requisito atual e audio da palavra e audio da frase.

### Provedor atual aprovado para o MVP 50

O pacote Latin MVP atual usa Google Translate TTS com codigo `la` para audio da palavra e da frase.

Estado atual:

- provedor final do MVP 50: `google-translate-tts`;
- voz/codigo: `la`;
- politica de pronuncia: `google_translate_latin`;
- manifest: `data/latin_mvp/latin-mvp-50-v1-audio.json`;
- midia: 100 arquivos MP3 em `data/latin_mvp/audio/latin-mvp-50-v1/`;
- status de review: aprovado para o escopo `latin-mvp-50-v1`.

### Candidatos deferidos

ElevenLabs italiano permanece deferido depois de falha de billing/quota (`HTTP 402 Payment Required`) nas chaves configuradas. Ele nao e requisito para exportar o MVP 50 atual.

Azure italiano permanece fallback, nao provider final. FineVoice permanece somente pesquisa e nao deve ser ligado como provider ativo sem plano futuro.

### Ferramentas futuras a pesquisar

- Azure TTS com voz multilingual ou voz adequada, se aceitar Latim de forma convincente.
- Google Cloud TTS com voz multilingual, se aceitar Latim de forma convincente e qualidade superior ao pacote atual.
- servicos comerciais com TTS em Latim.
- gravacao humana ou voz custom, se TTS automatico for ruim.

Ponto para discutir: a pronuncia deve ser estritamente eclesiastica/tradicional ou aceitamos pronuncia latina aproximada no MVP.

Ponto para discutir: se audio ruim deve bloquear o milestone ou se pode entrar como experimental.

## Pipeline proposto

### 1. Selecionar corpus

Escolher textos classicos e/ou fontes de frases.

Aberto para discutir:

- comecar pela Eneida;
- comecar por Disticha Catonis;
- comecar por frases didaticas alinhadas ao Rafael Falcon;
- misturar textos classicos com frases didaticas.

### 2. Extrair frases

Selecionar frases curtas e estudaveis.

Criterios:

- frase nao muito longa;
- uma palavra alvo clara;
- estrutura gramatical explicavel;
- fonte rastreavel;
- utilidade didatica.

### 3. Lematizar

Transformar formas em lemas.

Exemplo:

```text
virum -> vir
cano -> cano
arma -> arma
```

### 4. Calcular frequencia

Contar por lema, nao por forma superficial.

Exemplo:

```text
amo, amas, amat, amamus, amatis, amant -> amo
```

### 5. Escolher palavra alvo

Para cada lema frequente, escolher uma frase boa.

Aberto para discutir:

- um card por lema;
- varios cards por lema se houver usos gramaticais diferentes;
- uma frase por caso importante;
- uma frase por sentido importante.

### 6. Gerar gramatica curta

Gerar a nota no formato direto.

Exemplo:

```text
virum: subst masc, 2a declinacao, Accusativus singularis, OD.
```

### 7. Gerar audio

Gerar dois audios:

- audio da palavra;
- audio da frase.

### 8. Revisar

Revisar especialmente:

- caso;
- declinacao;
- funcao sintatica;
- traducao;
- qualidade da frase;
- qualidade do audio.

## Niveis do deck

A ideia original do projeto e 3 niveis com 1000 cards cada.

Para Latim, ainda precisa discutir se o milestone inicial ja mira essa estrutura ou se comeca menor.

### Opcao A: MVP pequeno

- 50 cards.
- Validar formato.
- Validar gramatica curta.
- Validar audio.
- Validar pipeline.

### Opcao B: piloto medio

- 300 cards.
- Ja testar frequencia real.
- Cobrir casos principais.
- Cobrir verbos comuns.

### Opcao C: estrutura final

- 3 niveis.
- 1000 cards por nivel.
- Frequencia por lema.
- Revisao mais pesada.

Recomendacao inicial: comecar com MVP pequeno de 50 cards antes de prometer 3000 cards.

## Qualidade minima do card

Cada card latino deve ter:

- palavra alvo;
- lema;
- frase latina;
- traducao curta da palavra;
- traducao da frase;
- gramatica curta;
- fonte;
- audio da palavra;
- audio da frase;
- status de revisao.

O card nao deve ser aceito se:

- a gramatica estiver incerta e nao marcada como incerta;
- o caso estiver errado;
- a traducao nao corresponder ao contexto;
- a frase for longa demais;
- a fonte nao estiver registrada;
- o audio estiver ausente quando o milestone decidir que audio e obrigatorio.

## Pontos abertos para discutir no GSD new milestone

### Escopo

1. O milestone inicial deve ser 50, 100, 300 ou 1000 cards?
2. O objetivo do milestone e prototipo, piloto utilizavel ou deck nivel 1 completo?
3. O milestone deve incluir exportacao `.apkg` ou apenas gerar dados estruturados?

### Frequencia

4. A frequencia deve vir de qual corpus?
5. A frequencia deve ser geral do Latim classico ou focada nos textos escolhidos?
6. Devemos usar DCC Core Vocabulary como guia pedagogico junto com frequencia?
7. O ranking deve ser somente por lema ou ponderado por utilidade didatica?
8. Como tratar palavras muito frequentes mas gramaticalmente complexas?

### Fontes

9. Comecar por Eneida, Disticha Catonis ou frases didaticas?
10. Frases adaptadas sao permitidas ou somente frases originais?
11. Quais fontes podem ser usadas legalmente como corpus?
12. Como registrar fonte: obra/linha, URL, autor, edicao?

### Metodo Rafael Falcon

13. Como mapear o metodo para uma ordem concreta de cards?
14. O nivel 1 deve seguir ordem gramatical do metodo ou frequencia pura?
15. Quais construcoes gramaticais devem aparecer primeiro?
16. Quais construcoes devem ser bloqueadas no MVP por serem complexas demais?

### Card

17. A frente deve mostrar a palavra alvo ou apenas a frase?
18. O lema aparece na frente ou no verso?
19. A traducao da palavra deve ser literal, contextual ou ambas?
20. A traducao da frase deve ser mais literal ou mais natural?
21. O campo `Gramatica` deve usar `singularis/pluralis` ou `sg/pl`?
22. O campo `Gramatica` deve usar termos latinos ou portugueses para tempo/modo/voz?

### Gramatica

23. Como padronizar funcoes sintaticas: `OD`, `OI`, `Suj`, etc.?
24. Como marcar analise incerta?
25. Como tratar formas ambiguas?
26. Como tratar locativo?
27. Como tratar vocativo em frases reais?
28. Como tratar particulas encliticas como `-que`, `-ve`, `-ne`?

### Audio

29. Audio deve ser obrigatorio no MVP?
30. Audio da palavra e da frase entram sempre?
31. Google Translate TTS `la` continua aceitavel para o MVP 50 apos review?
32. Pronuncia deve ser eclesiastica/tradicional desde o primeiro milestone?
33. Se nao houver TTS bom, devemos permitir audio vazio temporariamente?

### Revisao

34. Todo card precisa de revisao humana?
35. Quais campos podem ser gerados automaticamente?
36. Quais campos precisam ser obrigatoriamente revisados?
37. Como marcar `needs_review`, `approved`, `rejected`?

## Recomendacao para o milestone

Comecar com um milestone pequeno e verificavel.

Proposta:

- gerar 50 cards de Latim classico;
- usar frequencia por lema, mesmo que inicial/manual;
- usar frases reais ou didaticas rastreaveis;
- seguir metodo Rafael Falcon na selecao e ordem;
- incluir campo `Gramatica` curto;
- incluir audio da palavra e da frase com Google Translate TTS `la` no MVP 50 aprovado;
- exportar `.apkg` de teste;
- registrar incertezas para discussao antes de escalar.
