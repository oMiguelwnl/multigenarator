# Analise Da Geracao Do Deck Polones

Arquivo analisado: `.multilang/exports/2a7473ce-241a-4ecb-83b8-429d66b97542.apkg`

Job analisado: `2a7473ce-241a-4ecb-83b8-429d66b97542`

Data da analise: `2026-05-26`

## Veredito

O deck foi exportado com sucesso tecnico, mas nao atende ao objetivo do produto para um deck polones completo e confiavel.

O pacote `.apkg` e importavel pelo Anki, contem midias MP3 consistentes e nao possui referencias de audio ausentes. Porem, o conteudo e o processo de geracao apresentam problemas graves:

- O deck tem `2740` cartoes, nao os `3000` esperados.
- O terceiro nivel tem apenas `740` cartoes, nao `1000`.
- O APKG nao separa os cartoes em 3 niveis de 1000 cartoes.
- O job ficou com status `pending`, mesmo apos um export `completed`.
- `260` itens ficaram em revisao e nao foram exportados.
- Existem traducoes invalidas aceitas como se fossem traducoes reais.
- Existem problemas de vocabulario, exemplos, definicoes, duplicatas e uso de provedores fallback.
- A observabilidade atual nao permite medir com precisao tempo real, latencia por ferramenta, custo, tokens ou numero de tentativas por chamada.

Este APKG nao deve ser tratado como deck final de producao.

## Artefatos Analisados

| Artefato | Caminho |
|---|---|
| APKG | `.multilang/exports/2a7473ce-241a-4ecb-83b8-429d66b97542.apkg` |
| Banco da geracao | `.multilang/dev.db` |
| Relatorio de revisao | `.multilang/review-reports/2a7473ce-241a-4ecb-83b8-429d66b97542.json` |
| Log principal | `.multilang/polish-full-generation.log` |
| Log de resume | `.multilang/polish-full-generation-resume-2.log` |
| Log missing-only | `.multilang/polish-full-generation-missing-only.log` |

## Resumo Do APKG

| Metrica | Resultado |
|---|---:|
| Tamanho | `90.48 MB` |
| SHA256 | `ed7e2438fbff3f956bf25e32187230f85730d29634259eb3734aa7250e4fef01` |
| Modificado em UTC | `2026-05-25T19:27:22` |
| Entradas ZIP | `5464` |
| Banco Anki interno | `collection.anki2` |
| Decks internos | `Default`, `Multilang Polish` |
| Notas | `2740` |
| Cartoes | `2740` |
| Arquivos de midia | `5462` |
| Tipo de midia | `.mp3` |
| Referencias de audio nos campos | `5480` |
| Referencias de audio ausentes | `0` |
| Campo `Image` vazio | `2740` |

Campos do modelo `Multilang::Card`:

| Ordem | Campo |
|---:|---|
| 1 | `SortIndex` |
| 2 | `word` |
| 3 | `IPA` |
| 4 | `Definitions` |
| 5 | `Example Sentence` |
| 6 | `Translation` |
| 7 | `word_audio` |
| 8 | `sentence_audio` |
| 9 | `Image` |

Pontos tecnicamente positivos:

- O APKG e um ZIP valido.
- O banco `collection.anki2` e legivel.
- Todas as referencias `[sound:...]` apontam para arquivos existentes.
- Nao foram encontradas referencias de audio malformadas.
- O campo `Image` esta vazio em todos os cartoes, conforme o contrato esperado.
- O export final criou um APKG funcional para importacao no Anki.

## Problema Estrutural Principal

O requisito central do produto define 3 niveis com 1000 cartoes por nivel. O deck exportado nao cumpre isso.

Distribuicao inferida pelo `SortIndex`:

| Nivel | Cartoes exportados | Esperado | Deficit |
|---|---:|---:|---:|
| Level 1 | `1000` | `1000` | `0` |
| Level 2 | `1000` | `1000` | `0` |
| Level 3 | `740` | `1000` | `260` |
| Total | `2740` | `3000` | `260` |

O APKG tambem nao cria subdecks separados por nivel. Ha apenas o deck `Multilang Polish`. Isso reduz a utilidade pratica para estudo progressivo e viola a estrutura planejada do produto.

Outro problema de rastreabilidade: o APKG nao expoe `item_key`, `frequency_rank`, `frequency_level` ou `job_id` como campos ou tags uteis. A analise por item depende do banco externo, nao do pacote final.

## Estado Do Job

Registro em `generation_jobs`:

| Campo | Valor |
|---|---|
| `id` | `2a7473ce-241a-4ecb-83b8-429d66b97542` |
| `run_key` | `pl:frequency:levels:1-3:cards:1000` |
| `language` | `pl` |
| `source_type` | `frequency` |
| `source_fingerprint` | `levels:1-3:cards:1000` |
| `status` | `pending` |
| `current_stage` | `synthesize_audio` |
| `last_completed_stage` | `synthesize_audio` |
| `total_items` | `3000` |
| `completed_items` | `3000` |
| `failed_items` | `0` |
| `retrying_items` | `0` |
| `skipped_duplicates` | `3420` |
| `created_at` | `2026-05-18 19:28:18` |
| `updated_at` | `2026-05-25 19:18:01` |

Registro em `deck_exports`:

| Campo | Valor |
|---|---|
| `export_format` | `apkg` |
| `deck_name` | `Multilang Polish` |
| `output_path` | `.multilang\exports\2a7473ce-241a-4ecb-83b8-429d66b97542.apkg` |
| `card_count` | `2740` |
| `status` | `completed` |
| `created_at` | `2026-05-25 19:27:22` |

Diagnostico:

- O job ficou `pending`, mesmo apos export concluido.
- O job contabiliza `3000` itens completos, mas apenas `2740` foram aceitos, sintetizados e exportados.
- Os `260` itens em revisao foram tratados como sucesso de item em alguma parte do fluxo.
- A metrica `completed_items` nao significa "cartoes finais exportaveis".
- `failed_items=0` e enganoso, porque existem `260` itens nao exportados por falha de validacao.

## Linha Do Tempo

Nao existe telemetria suficiente para medir tempo real de execucao por chamada externa. A linha do tempo abaixo vem de timestamps persistidos no banco.

| Etapa | Inicio | Fim |
|---|---|---|
| Job criado | `2026-05-18 19:28:18` | - |
| `generation_items` | `2026-05-18 20:02:22` | `2026-05-20 20:02:27` |
| `lexical_candidates` | `2026-05-18 20:02:22` | `2026-05-18 21:13:31` |
| `text_quality_records` | `2026-05-18 21:13:33` | `2026-05-20 17:43:04` |
| `audio_assets` | `2026-05-20 17:14:06` | `2026-05-25 19:18:01` |
| `card_exports` | `2026-05-25 19:27:04` | `2026-05-25 19:27:04` |
| `deck_exports` | `2026-05-25 19:27:22` | `2026-05-25 19:27:22` |

Interpretacao:

- A duracao calendario foi de aproximadamente 7 dias entre criacao do job e export.
- O tempo real continuo nao e mensuravel com os dados atuais.
- A etapa final de snapshot/export foi rapida, cerca de segundos.
- O gargalo operacional esta nas chamadas externas: LLM, traducao e TTS.
- O processo precisa registrar duracao por chamada, por item e por etapa.

## Geracao Lexical

Resumo:

| Metrica | Resultado |
|---|---:|
| Candidatos grounded | `3000` |
| Pending groundings | `0` |
| Rejected rows | `0` |
| Level 1 candidates | `1000` |
| Level 2 candidates | `1000` |
| Level 3 candidates | `1000` |
| Backfilled candidates | `27` |
| Fonte de todos os candidatos | `wordfreq` |
| `grounding_status` | `grounded` para `3000` |

Apesar de todos os candidatos terem sido marcados como `grounded`, ha sinais claros de baixa qualidade lexical.

Duplicatas entre niveis:

| Palavra | Item keys | Ranks |
|---|---|---|
| `wspolnego` | `level-1-rank-0984`, `level-2-rank-0001` | `1001`, `1001` |
| `wziac` | `level-1-rank-0985`, `level-2-rank-0002` | `1002`, `1002` |
| `cokolwiek` | `level-1-rank-0990`, `level-2-rank-0007` | `1007`, `1007` |
| `komisja` | `level-2-rank-0995`, `level-3-rank-0001` | `2001`, `2001` |
| `narodu` | `level-2-rank-1000`, `level-3-rank-0006` | `2006`, `2006` |

No APKG exportado foram detectadas `18` palavras duplicadas.

Exemplos de candidatos problematicos para um deck de frequencia polones:

| Palavra | Problema |
|---|---|
| `a` | Definida como artigo indefinido ingles; nao deveria entrar como vocabulario polones nesse sentido. |
| `the` | Artigo ingles em deck polones. |
| `le` | Artigo frances em deck polones. |
| `go` | Definida como verbo ingles "to go", mas em polones e pronome/clitico. |
| `we` | Definida como pronome ingles "we", mas em polones e variante de preposicao. |
| `on` | Definicao incorreta ou em idioma errado para a funcao real em polones. |
| `ja` | Definida como "yes", mas em polones e "I". |
| `no` | Definicao em polones e exemplo artificial. |
| `xd` | Item de baixa qualidade para deck de vocabulario frequente. |
| `youtube` | Marca/plataforma, nao vocabulario geral ideal. |
| letras isoladas | `d`, `s`, `p`, `c`, `e`, `l`, entre outras. |

Isso indica que `wordfreq` sozinho nao deve ser fonte final. Ele pode continuar sendo uma fonte de bootstrap, mas a lista final precisa ser curada, congelada e versionada.

## Geracao De Texto

Resumo da tabela `text_quality_records`:

| Metrica | Resultado |
|---|---:|
| Registros de texto | `3000` |
| `generation_status=generated` | `2373` |
| `generation_status=repaired` | `627` |
| `validation_status=passed` | `2740` |
| `validation_status=failed` | `260` |
| `review_status=accepted` | `2740` |
| `review_status=review_required` | `260` |
| `confidence_label=high` | `2740` |
| `confidence_label=low` | `260` |

Tentativas de reparo:

| Reparos | Itens |
|---:|---:|
| `0` | `2373` |
| `1` | `385` |
| `2` | `242` |

Itens com problemas:

| Problema | Contagem |
|---|---:|
| `missing_target_lemma` | `160` |
| `banned_pattern` | `100` |
| `duplicate_sentence` | `84` |

Combinacoes de flags:

| Flags | Itens |
|---|---:|
| nenhuma | `2740` |
| `missing_target_lemma` | `119` |
| `banned_pattern` | `51` |
| `banned_pattern`, `duplicate_sentence` | `39` |
| `duplicate_sentence`, `missing_target_lemma` | `31` |
| `duplicate_sentence` | `10` |
| `banned_pattern`, `missing_target_lemma` | `6` |
| `banned_pattern`, `duplicate_sentence`, `missing_target_lemma` | `4` |

Itens rejeitados por nivel:

| Nivel | Itens rejeitados |
|---|---:|
| Level 1 | `74` |
| Level 2 | `64` |
| Level 3 | `122` |

Exemplos de itens rejeitados:

| Item | Palavra | Exemplo | Problema |
|---|---|---|---|
| `level-1-rank-0006` | `to` | `Ide do sklepu po chleb.` | Nao contem o alvo `to`; duplicado. |
| `level-1-rank-0008` | `do` | `Ide do sklepu po chleb.` | Sentenca duplicada. |
| `level-1-rank-0012` | `jak` | `Jak sie masz dzisiaj?` | Padrao banido/repetitivo. |
| `level-1-rank-0016` | `tak` | `Czy chcesz isc na spacer? Tak, chetnie!` | Duplicada/padrao banido. |
| `level-1-rank-0030` | `mnie` | `Czy mozesz mi pomoc w tej sprawie?` | Nao contem o alvo `mnie`. |

## Provedores De Texto E Traducao

Geracao de sentencas:

| Fonte | Itens |
|---|---:|
| LiteLLM | `2758` |
| Tatoeba | `242` |

Modelo LLM detectado:

| Modelo | Itens |
|---|---:|
| `openrouter/openai/gpt-4o-mini` | `2758` |

Traducao:

| Provider | Itens |
|---|---:|
| DeepL | `2501` |
| Google Translate fallback | `499` |

O fallback para Google aconteceu porque a quota do DeepL foi excedida:

```text
Quota for this billing period has been exceeded, message: Quota exceeded
```

Problema critico: `3` traducoes de erro HTTP foram aceitas como se fossem traducoes validas.

| SortIndex | Palavra | Traducao exportada |
|---:|---|---|
| `2553` | `polaczenia` | `Error 500 (Server Error)!!1500.That's an error.There was an error. Please try again later.That's all we know.` |
| `2690` | `dziwnego` | `Error 500 (Server Error)!!1500.That's an error.There was an error. Please try again later.That's all we know.` |
| `2702` | `kaczynski` | `Error 500 (Server Error)!!1500.That's an error.There was an error. Please try again later.That's all we know.` |

Esses itens passaram por `validation_status=passed`, `review_status=accepted` e foram exportados. Isso mostra que a validacao atual de traducao e insuficiente.

## Falhas Registradas Em Logs

Os logs `polish-full-generation.log` e `polish-full-generation-missing-only.log` registram falha no OpenRouter:

```text
403 Forbidden
Your resource has been temporarily blocked because we detected unusual behavior.
provider_name: Azure
```

Diagnostico:

- O provedor OpenRouter bloqueou temporariamente a conta/recurso por comportamento incomum.
- O retry atual existe, mas nao aplica backoff real (`wait_seconds=0.0`).
- Repetir chamadas rapidamente apos 403/429 pode piorar bloqueios.
- O processo nao registra tentativas, latencia, request id, custo, token ou retry por item.

## Audio

Resumo de audio:

| Metrica | Resultado |
|---|---:|
| Assets de audio | `5480` |
| Audio de palavra | `2740` |
| Audio de sentenca | `2740` |
| Status `synthesized` | `5480` |
| Arquivos no APKG | `5462` |
| Referencias de audio no APKG | `5480` |
| Referencias ausentes | `0` |

Provedores:

| Provider | Assets |
|---|---:|
| Azure | `5259` |
| ElevenLabs | `221` |

Vozes:

| Voz | Assets |
|---|---:|
| `pl-PL-AgnieszkaNeural` | `5254` |
| `fallback-pl-c20742d4e6d8` | `137` |
| `ErXwobaYiN019PkySvjV` | `89` |

Estatisticas aproximadas:

| Tipo | Count | Duracao media | Tamanho medio |
|---|---:|---:|---:|
| Palavra | `2740` | `1905 ms` | `12053 bytes` |
| Sentenca | `2740` | `3372 ms` | `21411 bytes` |

Diagnostico:

- A integridade tecnica da midia no APKG esta boa.
- O deck mistura Azure e ElevenLabs.
- Para um deck final, a mistura de provedores/vozes deve ser uma decisao explicita ou um warning bloqueante.
- Se Azure e o provedor preferido, a geracao final deveria bloquear ou exigir aprovacao quando usar fallback.

## Qualidade Do Conteudo Exportado

Pontos positivos:

- `0` exemplos vazios.
- `0` traducoes vazias.
- `0` referencias de audio ausentes.
- `0` exemplos duplicados exatos dentro do APKG.

Problemas detectados:

| Problema | Evidencia |
|---|---:|
| Deck incompleto | `2740/3000` cartoes |
| Level 3 incompleto | `740/1000` cartoes |
| Palavras duplicadas | `18` palavras duplicadas no export |
| Traducoes duplicadas | `63` valores duplicados |
| Traducoes Error 500 aceitas | `3` |
| Definicoes com problema pelo audit interno | `76` |
| Mistura de TTS providers | Azure + ElevenLabs |
| Falta de tags de rastreabilidade | APKG nao inclui `item_key`, `rank`, `level`, `job_id` |

Exemplos de conteudo ruim exportado:

| Palavra | Exemplo | Problema |
|---|---|---|
| `a` | `Chcialbym kupic a nowa ksiazke.` | Palavra/definicao de artigo ingles em frase polonesa. |
| `the` | `Ksiazka lezy na stole obok the krzesla.` | Token ingles dentro de exemplo polones. |
| `on` | `Ksiazka lezy on stole w salonie.` | Uso incorreto do token alvo. |
| `we` | `Myslimy, ze we powinnismy to zrobic razem.` | Usa `we` como se fosse pronome ingles. |
| `ii` | `Ja jestem tutaj, a ty ii tam.` | Token estranho/artificial. |
| `wspaniale` | `Wlasnie wrzucilem wspaniale zdjecie wombata na flickra.` | Conteudo estranho e marca/servico informal. |

## Auditoria De Definicoes

O audit interno `detect_card_issues` encontrou `76` problemas de definicao, todos do tipo `grammar_metadata`.

Exemplos:

| SortIndex | Definicao | Problema |
|---:|---|---|
| `18` | `pronoun: this (genitive case)` | Define informacao gramatical em vez de significado claro. |
| `27` | `pronoun: this (masculine singular)` | Definicao muito gramatical. |
| `77` | `pronoun: those (plural, genitive case)` | Definicao centrada em metadata. |
| `110` | `verb: you are (singular, informal)` | Forma flexionada sem explicacao semantica adequada. |
| `337` | `verb: (1st person plural present) we have` | Descricao gramatical como definicao. |

Isso reforca que a geracao/normalizacao lexical precisa ser mais forte antes da etapa de exemplos e export.

## Causas Raiz

| Area | Causa raiz provavel |
|---|---|
| Deck incompleto | O export usa apenas registros aceitos, mas nao bloqueia export parcial. |
| Estado inconsistente | Itens em revisao sao contabilizados como sucesso de job/item. |
| Falha OpenRouter | Volume alto sem backoff/circuit breaker real. |
| Quota DeepL | Fallback automatico para Google sem gate de qualidade suficiente. |
| Traducao `Error 500` aceita | Validacao de traducao checa pouco alem de vazio/igualdade. |
| Vocabulos ruins | `wordfreq` cru usado como base final, sem curadoria global suficiente. |
| Duplicatas entre niveis | Backfill/partitioning nao deduplica globalmente por forma/lemma/rank. |
| Exemplos poloneses incorretos | Falta validacao morfologica e language-id especifica para polones. |
| Definicoes erradas | LLM/lexicon sem validacao forte de homografos, POS e idioma. |
| Audio inconsistente | Fallback TTS permitido sem politica de bloqueio/aceite. |
| Observabilidade | Falta telemetria estruturada por chamada, provider, custo, erro e latencia. |

## Conclusao

O deck atual serve como evidencia de que o pipeline ja consegue atravessar todas as etapas tecnicas: ingestao, grounding, geracao de texto, traducao, audio e export `.apkg`.

Porem, ele nao deve ser usado como produto final. Antes de gerar decks completos para qualquer lingua suportada, o processo precisa de quality gates obrigatorios, curadoria global de listas, validacao linguistica, controle de provedores, telemetria e bloqueio de export parcial.

O plano de melhoria detalhado esta em `docs/generation-process-improvement-plan.md`.
