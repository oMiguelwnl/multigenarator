# Prompts para Implementar Melhorias de Geracao

Use este arquivo para pedir que a AI implemente as melhorias em etapas separadas. Execute um prompt por vez, valide os testes e so depois avance para o proximo.

## Regras Gerais

Inclua estas regras em qualquer prompt abaixo se quiser reforcar o escopo:

```text
Faca mudancas pequenas e testadas. Preserve compatibilidade com os comandos atuais. Nao implemente melhorias fora do escopo pedido. Rode testes focados e explique os arquivos alterados.
```

## Etapa 1: `--max-items`

```text
Leia docs/generation-performance-improvements.md e implemente apenas a proxima melhoria: adicionar --max-items ao comando generate.

Requisitos:
- --max-items deve limitar quantos candidatos elegiveis sao processados nesta execucao.
- Deve funcionar junto com --missing-only.
- Sem --max-items, o comportamento atual deve permanecer igual.
- Aplique o limite depois da filtragem de candidatos elegiveis.
- Adicione testes focados para frequency resume e missing-only + max-items.
- Nao implemente concorrencia, batch generation, cache provider, rate limit ou comandos novos nesta etapa.

Depois rode testes focados e informe o comando recomendado para continuar o job de polones em lotes.
```

## Etapa 2: Progresso Granular

```text
Implemente progresso granular para o comando generate.

Requisitos:
- Exibir progresso periodico durante generate_text.
- Mostrar processed_this_run, accepted_this_run, review_this_run, remaining_missing, last_item_key e elapsed_seconds quando possivel.
- Nao vazar texto privado de cards, frases, traducoes ou highlights.
- Manter saida atual de resumo final.
- Adicionar testes focados para garantir que os novos contadores aparecem e que nao vazam conteudo privado.
- Nao implemente rate limit, concorrencia ou batch generation nesta etapa.
```

## Etapa 3: Rate Limit Simples

```text
Implemente rate limit simples para chamadas de provider durante a geracao.

Requisitos:
- Adicionar opcao --rate-limit-per-minute ao comando generate.
- O limite deve controlar chamadas LLM/provedor usadas na geracao textual e pronuncia quando aplicavel.
- Sem a flag, preservar comportamento atual.
- O rate limit deve ser simples e deterministico, suficiente para evitar rajadas excessivas.
- Adicionar testes sem fazer chamadas reais ao provider.
- Nao implemente concorrencia nem batch generation nesta etapa.
```

## Etapa 4: Backoff em Erro Temporario

```text
Implemente backoff para erros temporarios de provider.

Requisitos:
- Tratar como temporarios: 403 temporario, 429, timeout e erro de rede.
- Aguardar antes de tentar novamente.
- Ter limite de tentativas configuravel ou constante pequena.
- Se esgotar tentativas, registrar falha clara sem corromper o progresso ja salvo.
- Redigir mensagens para nao expor chaves ou payloads sensiveis.
- Adicionar testes com providers falsos que falham e depois recuperam.
- Nao implemente concorrencia nem batch generation nesta etapa.
```

## Etapa 5: `--refresh-snapshots` no Export

```text
Implemente --refresh-snapshots no comando export.

Requisitos:
- Quando --refresh-snapshots for usado, recriar os card_exports a partir dos dados atuais antes de escrever o arquivo final.
- Deve funcionar para apkg, csv e tsv se o fluxo de exportacao suportar esses formatos.
- Sem --refresh-snapshots, preservar comportamento atual.
- Adicionar testes garantindo que alteracoes recentes de IPA/Definitions entram no export quando a flag e usada.
- Nao altere templates de card nesta etapa.
```

## Etapa 6: Separar Reparo de Texto

```text
Implemente uma forma separada de reparar cards review_required.

Preferencia:
- Criar comando repair-text --job-id <JOB_ID> --max-items N.

Requisitos:
- O comando deve processar apenas text_quality_records com review_status diferente de accepted.
- Deve respeitar --max-items se informado.
- Deve manter generate --missing-only focado apenas em cards sem texto.
- Adicionar testes focados para selecionar apenas review_required.
- Nao implemente concorrencia nem batch generation nesta etapa.
```

## Etapa 7: Function Words de Polones

```text
Implemente dados fixos para function words de polones.

Requisitos:
- Criar uma fonte pequena e versionada para palavras como w, i, nie, do, to, jak, co, czy.
- Usar esses dados antes de chamar provider para definicao/POS/IPA quando a palavra estiver nessa lista.
- Preservar fallback atual para palavras fora da lista.
- Adicionar testes garantindo definicoes corretas para palavras curtas frequentes.
- Nao expanda para todas as linguas nesta etapa.
```

## Etapa 8: Cache de Provider

```text
Implemente cache de respostas do provider.

Requisitos:
- Cachear por provider, model, task_type, language, item_key ou prompt hash, e prompt_version.
- Reutilizar resposta quando a chave for identica.
- Invalidar naturalmente quando prompt_version mudar.
- Persistir resposta normalizada e metadados basicos.
- Adicionar testes garantindo que reruns nao chamam o provider novamente para a mesma chave.
- Nao implemente batch generation nesta etapa.
```

## Etapa 9: Audio Separado

```text
Separe sintese de audio em comando proprio.

Requisitos:
- Criar comando synthesize-audio --job-id <JOB_ID>.
- Suportar --missing-only para gerar apenas audio ausente.
- Suportar --max-items se ja existir no projeto.
- Nao misturar geracao textual com audio neste comando.
- Adicionar testes focados para audio ausente e audio ja existente.
```

## Etapa 10: Concorrencia Controlada

```text
Implemente concorrencia controlada para geracao, somente depois que --missing-only, --max-items, rate limit e backoff estiverem estaveis.

Requisitos:
- Adicionar --concurrency com default 1.
- Evitar dois workers processando o mesmo item.
- Manter uma sessao de banco segura por worker ou mecanismo equivalente.
- Respeitar rate limit global.
- Adicionar testes com providers falsos.
- Documentar riscos com SQLite e recomendar Postgres para concorrencia real.
```

## Etapa 11: Batch Generation

```text
Planeje e implemente batch generation apenas depois que o fluxo por item estiver robusto.

Requisitos:
- Gerar multiplos cards por chamada com resposta JSON estruturada.
- Validar cada item individualmente.
- Reenfileirar apenas itens que falharem.
- Manter caminho por item como fallback.
- Adicionar testes de JSON parcial, item invalido e retry por item.
```

## Prompt de Retomada do Job de Polones

Use depois de implementar `--max-items`:

```text
Retome o job de polones em lote seguro usando --missing-only e --max-items. Primeiro verifique se nao existe outro processo ativo. Depois rode um lote, confira os contadores no banco e informe missing, text_total, text_accepted e text_review.

Job ID:
2a7473ce-241a-4ecb-83b8-429d66b97542

Comando esperado:
python -m multilang.cli generate --language pl --source frequency --resume 2a7473ce-241a-4ecb-83b8-429d66b97542 --missing-only --max-items 100
```
