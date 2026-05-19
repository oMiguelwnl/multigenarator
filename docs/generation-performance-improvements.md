# Plano de Melhorias da Geracao

Este arquivo resume as mudancas recomendadas para tornar a geracao de decks mais rapida, mais confiavel e com melhor qualidade. Ele e um plano de propostas, nao uma lista de mudancas ja implementadas.

## Problema Atual

O fluxo atual consegue gerar decks grandes, mas fica lento porque:

- Processa cards de forma sequencial.
- Reprocessa cards `review_required` durante o resume.
- Faz muitas chamadas ao provider por card.
- Depende muito do LLM quando nao existe cache lexical/IPA.
- Pode sofrer bloqueio temporario do provider em execucoes longas.
- Nao mostra progresso granular suficiente durante jobs grandes.

## Prioridade Alta

### 1. Adicionar `--missing-only`

Objetivo:

Processar apenas cards que ainda nao tem texto gerado.

Problema que resolve:

O resume atual tenta reprocessar cards `review_required`, o que faz o job gastar tempo em palavras problematicas antes de completar os cards restantes.

Comando desejado:

```bash
python -m multilang.cli generate --language pl --source frequency --resume <JOB_ID> --missing-only
```

Resultado esperado:

- Pula cards aceitos.
- Pula cards em review.
- Gera somente cards sem texto.
- Ajuda a completar os 3000 cards mais rapido.

### 2. Adicionar `--max-items`

Objetivo:

Permitir rodar geracao em lotes pequenos.

Comando desejado:

```bash
python -m multilang.cli generate --language pl --source frequency --resume <JOB_ID> --missing-only --max-items 100
```

Resultado esperado:

- Processa no maximo N itens por execucao.
- Reduz risco de bloqueio do provider.
- Facilita debug e acompanhamento.

### 3. Melhorar progresso no terminal

Objetivo:

Mostrar progresso real enquanto o job roda.

Saida desejada:

```text
stage=generate_text processed=120 accepted=108 review=12 remaining=890 rate=3.2/min last_item=level-2-rank-0144
```

Resultado esperado:

- Fica claro se o processo esta andando.
- Fica mais facil decidir se deve continuar, pausar ou trocar provider.

### 4. Adicionar rate limit simples

Objetivo:

Evitar bloqueios temporarios do provider.

Comando desejado:

```bash
python -m multilang.cli generate --language pl --source frequency --resume <JOB_ID> --rate-limit-per-minute 30
```

Resultado esperado:

- Reduz chance de erro `403` ou rate limit.
- Torna execucoes longas mais estaveis.

### 5. Adicionar backoff em erro de provider

Objetivo:

Quando o provider falhar temporariamente, esperar e tentar de novo em vez de encerrar o job imediatamente.

Erros que devem acionar backoff:

- `403` temporario
- `429`
- timeout
- erro de rede
- erro temporario do provider

Resultado esperado:

- Menos interrupcoes manuais.
- Melhor aproveitamento de jobs longos.

## Prioridade Media

### 6. Separar geracao inicial de reparo

Objetivo:

Completar primeiro todos os cards sem texto, depois reparar os cards ruins.

Comandos desejados:

```bash
python -m multilang.cli generate --language pl --source frequency --resume <JOB_ID> --missing-only
python -m multilang.cli repair-text --job-id <JOB_ID> --max-items 100
```

Resultado esperado:

- O deck chega mais rapido a cobertura completa.
- Cards problematicos nao bloqueiam cards ainda nao gerados.

### 7. Criar cache de respostas do provider

Objetivo:

Evitar chamadas repetidas para o mesmo item, prompt e modelo.

Chave sugerida:

```text
provider + model + task_type + language + item_key + prompt_version
```

Resultado esperado:

- Menos custo.
- Reruns mais rapidos.
- Menos risco de bloqueio por chamadas repetidas.

### 8. Criar cache lexical/IPA para polones

Objetivo:

Reduzir dependencia do LLM para definicao, classe gramatical e IPA.

Caminho esperado:

```text
.multilang/lexicon/pl/lexical-index.json
```

Campos desejados:

```json
{
  "w": {
    "term": "w",
    "display_form": "w",
    "lemma": "w",
    "definitions": ["in; at; on"],
    "part_of_speech": "preposition",
    "ipa": "/v/",
    "source": "manual-or-wiktionary"
  }
}
```

Resultado esperado:

- Melhor qualidade para palavras ambiguas.
- Menos chamadas ao provider.
- IPA mais confiavel.

### 9. Tratar function words com dados fixos

Objetivo:

Evitar que palavras muito frequentes e curtas gerem definicoes ruins ou fiquem presas em review.

Exemplos:

```text
w -> preposition: in, at, on
i -> conjunction: and
nie -> adverb: not
do -> preposition: to, into, until
to -> pronoun/particle: this, it, that
```

Resultado esperado:

- Mais cards aceitos de primeira.
- Melhor qualidade nos cards mais frequentes.
- Menos custo com LLM.

## Prioridade Baixa

### 10. Adicionar concorrencia controlada

Objetivo:

Processar varios cards ao mesmo tempo.

Comando desejado:

```bash
python -m multilang.cli generate --language pl --source frequency --resume <JOB_ID> --missing-only --concurrency 3
```

Resultado esperado:

- Reduz tempo total.

Riscos:

- Pode aumentar bloqueios do provider se nao houver rate limit.
- Pode causar problemas com SQLite.
- Funciona melhor com Postgres.

Recomendacao:

Implementar somente depois de `--missing-only`, `--max-items` e rate limit.

### 11. Geracao em lote por prompt

Objetivo:

Gerar varios cards em uma unica chamada LLM.

Exemplo:

```text
Generate definitions, IPA and example sentences for these 20 Polish words.
Return strict JSON.
```

Resultado esperado:

- Pode acelerar muito.

Riscos:

- JSON pode vir quebrado.
- Uma resposta ruim afeta varios cards.
- Reparos ficam mais complexos.

Recomendacao:

Implementar depois que o fluxo por item estiver robusto.

### 12. Separar audio em comando proprio

Objetivo:

Gerar texto primeiro, audio depois.

Comando desejado:

```bash
python -m multilang.cli synthesize-audio --job-id <JOB_ID> --missing-only --max-items 300
```

Resultado esperado:

- Melhor controle de progresso.
- Menos mistura entre falhas de texto e falhas de audio.
- Retry de audio mais simples.

### 13. Adicionar `--refresh-snapshots` no export

Objetivo:

Garantir que o APKG usa os dados mais recentes de IPA, definicoes e frases.

Comando desejado:

```bash
python -m multilang.cli export --job-id <JOB_ID> --format apkg --deck-name "Multilang Polish" --refresh-snapshots
```

Resultado esperado:

- Evita exportar snapshot antigo.
- Torna o export mais previsivel.

## Ordem Recomendada de Implementacao

1. `--missing-only`
2. `--max-items`
3. Progresso granular
4. Rate limit simples
5. Backoff em erro temporario
6. Separar `repair-text`
7. Cache de provider
8. Function words de polones
9. Cache lexical/IPA de polones
10. `--refresh-snapshots`
11. Audio separado
12. Concorrencia controlada
13. Geracao em lote

## Fluxo Ideal Futuro

```bash
python -m multilang.cli generate --language pl --source frequency --missing-only --max-items 200 --rate-limit-per-minute 30
python -m multilang.cli generate --language pl --source frequency --resume <JOB_ID> --missing-only --max-items 200 --rate-limit-per-minute 30
python -m multilang.cli repair-text --job-id <JOB_ID> --max-items 100
python -m multilang.cli synthesize-audio --job-id <JOB_ID> --missing-only --max-items 300
python -m multilang.cli export --job-id <JOB_ID> --format apkg --deck-name "Multilang Polish" --refresh-snapshots
```

## Recomendacao Imediata

Implementar primeiro:

```text
--missing-only
--max-items
progresso granular
rate limit simples
```

Essas quatro mudancas devem destravar o job atual sem reescrever a arquitetura inteira.
