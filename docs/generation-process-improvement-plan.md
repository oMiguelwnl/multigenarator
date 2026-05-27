# Plano De Melhoria Do Processo De Geracao

Este plano detalha as melhorias necessarias para transformar o pipeline atual em um processo confiavel para gerar decks Anki completos e auditaveis para todas as linguas suportadas.

Linguas alvo v1:

- Portugues
- Espanhol
- Ingles
- Frances
- Alemao
- Italiano
- Polones
- Turco
- Romeno
- Russo
- Holandes

## Objetivo

Garantir que cada deck final tenha:

- `3000` cartoes quando a fonte for frequencia.
- `3` niveis com `1000` cartoes por nivel.
- Conteudo lexical confiavel.
- Exemplos naturais no idioma alvo.
- Traducoes corretas.
- Audio consistente.
- Export Anki reproduzivel.
- Relatorios claros de tempo, custo, falhas, provedores e qualidade.
- Bloqueio automatico quando a qualidade minima nao for atingida.

## Parte 1: Quality Gate De Export

Problema atual:

- O sistema exportou `2740` cartoes mesmo o job tendo `3000` candidatos planejados.
- O Level 3 saiu com `740` cartoes.
- O export parcial foi registrado como `completed`.

Mudancas propostas:

- Adicionar gate antes do export para validar contagem esperada.
- Para decks de frequencia, exigir exatamente `1000` cartoes por nivel.
- Exigir `0` itens em `review_required` por padrao.
- Exigir `0` traducoes invalidas.
- Exigir `0` referencias de audio ausentes.
- Exigir `0` audio com status diferente de `synthesized`.
- Permitir export parcial apenas com flag explicita `--allow-partial`.

Arquivos-alvo:

- `src/multilang/runtime.py`
- `src/multilang/cli.py`
- `src/multilang/services/assemble_export_cards.py`
- `src/multilang/domain/exporting.py`

CLI sugerida:

```bash
multilang export --job-id JOB_ID --format apkg
multilang export --job-id JOB_ID --format apkg --allow-partial
```

Criterios de aceite:

- Export sem `--allow-partial` falha se houver menos de `3000` cartoes em deck de frequencia completo.
- A mensagem de erro lista quantos itens faltam por nivel.
- O export concluido registra status consistente no job e no deck export.

## Parte 2: Estado Correto Do Job

Problema atual:

- O job permaneceu `pending` apos export.
- `completed_items=3000`, mas apenas `2740` itens foram exportaveis.
- Itens em revisao foram tratados como sucesso de item.

Mudancas propostas:

- Separar sucesso de etapa tecnica de sucesso de qualidade.
- Adicionar estados finais mais precisos: `completed`, `completed_with_warnings`, `failed`, `partial`, `blocked`.
- Atualizar `GenerationItem` para distinguir `text_generated`, `text_accepted`, `audio_synthesized`, `exported`.
- Nao contar `review_required` como item completamente concluido.
- Atualizar job para `completed` somente quando a qualidade final passar.

Arquivos-alvo:

- `src/multilang/domain/jobs.py`
- `src/multilang/repositories/job_repository.py`
- `src/multilang/services/generate_text_items.py`
- `src/multilang/services/generate_audio_items.py`
- `src/multilang/runtime.py`

Criterios de aceite:

- Um job com itens em revisao nao pode aparecer como completo.
- `failed_items` ou novo contador equivalente reflete itens bloqueantes.
- Resume nao confunde itens aceitos com itens apenas processados.

## Parte 3: Relatorio Final De Geracao

Problema atual:

- Nao existe relatorio final consolidado com tempo, falhas, provedores, custo, retries e qualidade.
- O relatorio de revisao pode ficar defasado em relacao ao banco.

Mudancas propostas:

- Criar `generation-report.json` e `generation-report.md` por job.
- Registrar resumo de cada etapa.
- Incluir contagem por nivel.
- Incluir contagem de accepted/review_required/failed.
- Incluir uso de provedores por etapa.
- Incluir falhas e mensagens redigidas.
- Incluir tempo por etapa e duracao total.
- Incluir arquivos gerados e hash do APKG.

Novo arquivo sugerido:

- `src/multilang/services/generation_report.py`

CLI sugerida:

```bash
multilang report --job-id JOB_ID
```

Criterios de aceite:

- Cada export completo gera automaticamente um relatorio.
- O relatorio e derivado do banco no momento da geracao.
- O relatorio inclui hashes e caminhos dos artefatos.

## Parte 4: Observabilidade E Telemetria

Problema atual:

- Nao da para medir tempo real por chamada.
- Nao ha custo, tokens, request id, erro normalizado ou latencia por provider.
- Logs de erro sao tracebacks longos, nao eventos estruturados.

Mudancas propostas:

- Criar tabela `provider_call_logs`.
- Registrar cada chamada externa: LLM, traducao, TTS e fallback.
- Registrar `job_id`, `item_key`, `task_type`, `provider`, `model`, `attempt`, `latency_ms`, `status`, `error_code`, `error_summary`, `fallback_from`, `prompt_hash`, `response_hash`, `tokens`, `estimated_cost`.
- Registrar eventos estruturados no console e em arquivo JSONL.

Ferramentas recomendadas:

- `structlog` para logs estruturados.
- OpenTelemetry em etapa posterior.
- Tabela SQL propria para analise offline.

Arquivos-alvo:

- `src/multilang/db/models.py`
- nova migration Alembic
- `src/multilang/services/text_generation.py`
- `src/multilang/services/provider_text_adapters.py`
- `src/multilang/services/audio_synthesis.py`

Criterios de aceite:

- Uma geracao permite responder quanto tempo cada provider levou.
- Falhas externas aparecem como eventos normalizados.
- O relatorio final mostra custo e volume aproximados por provider.

## Parte 5: Retry, Backoff E Circuit Breaker

Problema atual:

- O retry atual reconhece erros temporarios, mas usa `wait_seconds=0.0`.
- O OpenRouter retornou 403 por comportamento incomum.
- Repetir imediatamente chamadas apos 403/429 aumenta risco de bloqueio.

Mudancas propostas:

- Implementar exponential backoff com jitter.
- Respeitar `Retry-After` quando disponivel.
- Classificar erros `403`, `429`, timeout, network e quota.
- Adicionar circuit breaker por provider/model.
- Pausar o job em status `blocked` quando provider bloquear.
- Permitir resume apos janela de cooldown.

Ferramentas recomendadas:

- `tenacity`, ou implementacao propria pequena para manter controle.

Arquivo-alvo:

- `src/multilang/services/provider_retry.py`

Criterios de aceite:

- Um 403 temporario nao dispara dezenas de chamadas imediatas.
- O job registra cooldown e motivo.
- O usuario ve instrucao clara de quando retentar.

## Parte 6: Selecao E Fallback De LLM

Problema atual:

- O processo usou `openrouter/openai/gpt-4o-mini` via LiteLLM.
- O OpenRouter retornou 403.
- Nao ha roteamento robusto de modelos.

Mudancas propostas:

- Usar `LiteLLM Router` com prioridades explicitas.
- Preferir provider direto quando possivel.
- Configurar fallback por tarefa: definicao, exemplo, reparo e juiz.
- Separar modelo de geracao e modelo de validacao/julgamento.
- Registrar provider final usado por item.

Arquivos-alvo:

- `src/multilang/runtime.py`
- `src/multilang/services/provider_text_adapters.py`
- `src/multilang/settings.py`

Configuracao sugerida:

```env
MULTILANG_TEXT_GENERATION_PROVIDER=litellm
MULTILANG_TEXT_GENERATION_MODEL=openai/gpt-4o-mini
MULTILANG_TEXT_REPAIR_MODEL=openai/gpt-4.1-mini
MULTILANG_TEXT_JUDGE_MODEL=openai/gpt-4.1-mini
MULTILANG_LITELLM_FALLBACK_MODELS=openrouter/openai/gpt-4o-mini,azure/gpt-4o-mini
```

Criterios de aceite:

- O processo consegue trocar de provider sem alterar logica de dominio.
- Falhas de um provider nao corrompem a qualidade final.
- Fallback e visivel no relatorio.

## Parte 7: Traducao E Qualidade De Traducao

Problema atual:

- DeepL excedeu quota.
- O fallback para Google gerou pelo menos 3 traducoes com `Error 500` aceitas.
- O validador nao detectou paginas de erro como traducao invalida.

Mudancas propostas:

- Validar padroes de erro: `Error 500`, `That's an error`, HTML, quota, captcha, server error, request blocked.
- Validar idioma da traducao.
- Validar comprimento minimo e maximo relativo a sentenca.
- Validar que a traducao nao e uma pagina de erro ou mensagem de sistema.
- Remover fallback Google silencioso para deck final.
- Se DeepL exceder quota, pausar job em `blocked` ou usar fallback LLM julgado.

Ferramentas recomendadas:

- DeepL como primario.
- LLM judge/rewrite como fallback controlado.
- `lingua-language-detector` ou fastText para language-id.

Arquivos-alvo:

- `src/multilang/services/text_validation.py`
- `src/multilang/services/provider_text_adapters.py`
- `src/multilang/services/text_generation.py`

Criterios de aceite:

- Nenhuma traducao com mensagem de erro pode ser aceita.
- Quota excedida nao gera deck degradado silenciosamente.
- O relatorio mostra quantas traducoes usaram fallback.

## Parte 8: Curadoria Das Listas Para Todas As Linguas

Problema atual:

- `wordfreq` esta sendo usado como fonte final de candidatos.
- Isso permite tokens ruins, duplicatas, homografos estrangeiros, letras isoladas, marcas, abreviacoes e formas indesejadas.

Escopo correto:

- A curadoria nao deve ser especifica do polones.
- Todas as linguas suportadas precisam de listas curadas, congeladas, versionadas e auditaveis.

Linguas no escopo:

- Portugues
- Espanhol
- Ingles
- Frances
- Alemao
- Italiano
- Polones
- Turco
- Romeno
- Russo
- Holandes

Mudancas propostas:

- Usar `wordfreq` apenas como bootstrap.
- Criar pipeline de curadoria por lingua.
- Congelar listas finais em arquivos versionados e/ou tabelas do banco.
- Deduplicar globalmente por lingua, lemma, forma normalizada e rank.
- Validar scripts e caracteres permitidos por lingua.
- Remover tokens estrangeiros obvios.
- Remover letras isoladas quando nao forem vocabulario pedagogico aprovado.
- Remover marcas, URLs, emojis, emoticons e artefatos de corpus.
- Remover abreviacoes sem valor pedagogico para deck frequente.
- Separar nomes proprios, siglas e entidades em lista opcional, nao no deck principal.
- Registrar motivo de rejeicao para cada token removido.

Ferramentas recomendadas por familia linguistica:

| Lingua | Ferramentas sugeridas |
|---|---|
| Portugues | spaCy `pt`, wordfreq, Wiktionary/Kaikki, listas SUBTLEX/opensubtitles quando licenciadas |
| Espanhol | spaCy `es`, wordfreq, Wiktionary/Kaikki, Freeling se necessario |
| Ingles | wordfreq, wordfreq/SUBTLEX, wordnet, spaCy `en` |
| Frances | spaCy `fr`, wordfreq, Wiktionary/Kaikki, Lefff se aplicavel |
| Alemao | spaCy `de`, wordfreq, Wiktionary/Kaikki, compound handling |
| Italiano | spaCy `it`, wordfreq, Wiktionary/Kaikki |
| Polones | Morfeusz2, Stanza Polish, Wiktionary/Kaikki, plWordNet |
| Turco | Stanza Turkish, Zemberek quando viavel, Wiktionary/Kaikki |
| Romeno | spaCy/Stanza Romanian, Wiktionary/Kaikki |
| Russo | pymorphy3, Stanza Russian, Wiktionary/Kaikki |
| Holandes | spaCy `nl`, wordfreq, Wiktionary/Kaikki |

Pipeline sugerido:

1. Gerar candidatos por lingua via `wordfreq` em quantidade maior que a final, por exemplo `5000` a `10000`.
2. Normalizar Unicode, caixa, espacos, pontuacao e variantes.
3. Aplicar filtros por script e idioma.
4. Remover lixo de corpus: letras soltas, emojis, URLs, handles, marcas, nomes proprios nao desejados, abreviacoes ruins.
5. Fazer lookup lexical em fontes confiaveis.
6. Resolver lemma, POS e definicao base.
7. Deduplicar por lemma e forma de estudo.
8. Dividir em niveis 1, 2 e 3 com `1000` itens cada.
9. Backfill sem repetir itens ja usados.
10. Gerar relatorio de candidatos aceitos/rejeitados.
11. Congelar lista com versao.
12. Usar apenas a lista congelada na geracao de deck final.

Artefatos sugeridos:

```text
.multilang/sources/frequency/{language}/candidates-wordfreq-v1.csv
.multilang/sources/frequency/{language}/curated-v1.csv
.multilang/sources/frequency/{language}/rejections-v1.csv
.multilang/sources/frequency/{language}/curation-report-v1.md
```

Campos minimos da lista curada:

| Campo | Descricao |
|---|---|
| `language` | Codigo da lingua. |
| `frequency_list_version` | Versao congelada. |
| `level` | 1, 2 ou 3. |
| `rank` | Rank dentro da lista final. |
| `source_rank` | Rank original da fonte. |
| `display_form` | Forma exibida no card. |
| `lemma` | Lemma validado. |
| `lemma_key` | Chave normalizada. |
| `part_of_speech` | POS quando conhecido. |
| `definition_seed` | Definicao/grounding base. |
| `source_provenance` | Fonte e versao. |
| `curation_flags` | Flags de decisao. |

Regras globais de rejeicao:

- Token vazio.
- Token com caracteres inesperados para a lingua.
- Token composto so por pontuacao, numero ou simbolo.
- Token com URL, email, handle ou hashtag.
- Emoji/emoticon.
- Marca ou plataforma sem aprovacao.
- Nome proprio sensivel ou politico em deck geral.
- Palavra de outro idioma detectada com alta confianca.
- Letra isolada sem valor lexical aprovado.
- Abreviacao nao pedagogica.
- Duplicata de lemma/forma ja selecionada.
- Forma que nao tem grounding lexical confiavel.

Criterios de aceite:

- Cada lingua tem `3000` itens curados e versionados.
- Cada nivel tem exatamente `1000` itens.
- Nao existem duplicatas entre niveis.
- Cada rejeicao tem motivo rastreavel.
- A geracao de deck usa listas congeladas, nao `wordfreq` ao vivo.

## Parte 9: Validacao Linguistica E Morfologica

Problema atual:

- A validacao de alvo usa matching textual simples.
- Isso falha para linguas com flexao rica.
- Tambem permite tokens estrangeiros em exemplos.

Mudancas propostas:

- Adicionar validadores por lingua.
- Validar se a sentenca contem lemma ou forma flexionada aceitavel.
- Validar idioma da sentenca.
- Validar POS quando disponivel.
- Rejeitar tokens estrangeiros inesperados.
- Criar whitelists para palavras funcionais e abreviacoes pedagogicas.

Ferramentas recomendadas:

- `spaCy` para linguas com bom suporte.
- `Stanza` para cobertura multilingual.
- `Morfeusz2` para polones.
- `pymorphy3` para russo.
- `lingua-language-detector` ou fastText para language-id.

Arquivos-alvo:

- `src/multilang/services/text_validation.py`
- novo `src/multilang/services/language_validation.py`
- novo `src/multilang/services/morphology/`

Criterios de aceite:

- Exemplos com `the`, `le`, `a` indevidos em decks nao ingleses/franceses sao rejeitados.
- Exemplos sem o alvo lexical real sao rejeitados.
- Falsos negativos em palavras flexionadas diminuem com validacao morfologica.

## Parte 10: Geracao De Exemplos

Problema atual:

- Muitos exemplos falham por `missing_target_lemma`, `duplicate_sentence` e `banned_pattern`.
- O fallback por Tatoeba foi usado em `242` itens, apesar de Tatoeba ser uma preocupacao conhecida de qualidade.

Mudancas propostas:

- Pedir multiplas opcoes estruturadas por item, por exemplo 3 candidatas.
- Validar localmente todas as candidatas e escolher a melhor.
- Passar para o prompt exemplos ja usados proximos para evitar duplicatas.
- Incluir constraints por POS e lemma.
- Remover Tatoeba como fallback automatico para deck final.
- Usar Tatoeba apenas como fonte opcional de referencia, com validacao forte.

Arquivos-alvo:

- `src/multilang/services/text_generation.py`
- `src/multilang/services/provider_text_adapters.py`
- `src/multilang/services/generate_text_items.py`

Criterios de aceite:

- Reduzir taxa de `review_required` para abaixo de 1% antes de qualquer revisao manual.
- Nao aceitar exemplos genericos, perguntas banais ou comandos curtos sem justificativa.
- Duplicatas exatas e quase duplicatas sao rejeitadas.

## Parte 11: Definicoes E Grounding Lexical

Problema atual:

- Definicoes incorretas ou muito gramaticais foram exportadas.
- Ha homografos tratados como palavras inglesas dentro do deck polones.
- O audit encontrou `76` problemas de definicao.

Mudancas propostas:

- Normalizar grounding lexical antes da geracao de exemplos.
- Validar idioma da definicao.
- Validar POS e sentido contra a lingua alvo.
- Rejeitar definicoes que descrevem apenas flexao sem significado pedagogico.
- Adicionar juiz LLM ou regras para homografos suspeitos.
- Manter cache lexical revisavel por lingua.

Ferramentas recomendadas:

- Kaikki/Wiktionary como fonte base.
- plWordNet para polones.
- WordNet para ingles.
- Validadores por lingua para POS/lemma.

Arquivos-alvo:

- `src/multilang/services/lexical_grounding.py`
- `src/multilang/services/text_field_remediation.py`
- `src/multilang/domain/deck_audit.py`

Criterios de aceite:

- Definicoes em idioma errado sao bloqueadas.
- Homografos estrangeiros sao rejeitados ou revisados.
- O audit de definicoes vira gate obrigatorio.

## Parte 12: Audio E TTS

Problema atual:

- O deck mistura Azure e ElevenLabs.
- A integridade de arquivo esta boa, mas a consistencia de voz nao e garantida.

Mudancas propostas:

- Definir politica explicita de fallback de audio.
- Para deck final, bloquear se houver fallback TTS nao aprovado.
- Registrar provider e voz no relatorio final.
- Validar MP3 com ferramenta propria.
- Medir duracao real do audio.
- Permitir regenerar apenas audios fallback.

Ferramentas recomendadas:

- Azure Speech como primario.
- `ffprobe`, `mutagen` ou `pydub` para validacao de MP3.

Arquivos-alvo:

- `src/multilang/services/audio_synthesis.py`
- `src/multilang/services/generate_audio_items.py`
- `src/multilang/services/azure_speech_adapter.py`
- `src/multilang/services/elevenlabs_speech_adapter.py`

Criterios de aceite:

- O relatorio informa todos os fallbacks de TTS.
- Export final pode exigir `0` fallback por padrao.
- Nenhum audio com byte size zero ou duracao ausente e exportado.

## Parte 13: Auditoria De Deck

Problema atual:

- O audit atual e limitado principalmente a problemas de definicao.
- O APKG gerado tinha varias falhas que o audit atual nao bloqueou.

Mudancas propostas:

- Expandir `audit-deck` para validar o pacote completo.
- Checar contagem por nivel.
- Checar duplicatas de palavra, lemma, exemplo e traducao.
- Checar traducoes com padrao de erro.
- Checar idioma dos exemplos e traducoes.
- Checar definicoes.
- Checar midia e audio provider.
- Checar tags/rastreabilidade.
- Retornar exit code nao-zero em problemas bloqueantes.

Arquivos-alvo:

- `src/multilang/domain/deck_audit.py`
- `src/multilang/services/deck_audit_reader.py`
- `src/multilang/services/deck_audit_reports.py`
- `src/multilang/cli.py`

Criterios de aceite:

- `audit-deck` detecta deck parcial.
- `audit-deck` detecta `Error 500` em traducao.
- `audit-deck` detecta duplicatas entre niveis.
- `audit-deck` detecta midia ausente.

## Parte 14: Rastreabilidade No APKG

Problema atual:

- O APKG nao contem `job_id`, `item_key`, `level` ou `rank` de forma facilmente auditavel.

Mudancas propostas:

- Adicionar tags Anki por nota.
- Preservar o schema de campos atual.
- Tags sugeridas: `multilang`, `pl`, `frequency`, `level_1`, `rank_0001`, `job_2a7473ce`.
- Opcionalmente adicionar um campo tecnico apenas se o contrato de deck permitir.

Arquivo-alvo:

- `src/multilang/services/export_anki_package.py`

Criterios de aceite:

- Um APKG isolado pode ser auditado sem depender do banco externo.
- O usuario consegue filtrar cards por nivel no Anki.

## Parte 15: Banco E Execucao Em Larga Escala

Problema atual:

- A geracao completa usou SQLite dev DB.
- SQLite nao e ideal para jobs longos, concorrencia e resume robusto.

Mudancas propostas:

- Usar PostgreSQL para geracoes completas.
- Manter SQLite apenas para dev/testes pequenos.
- Adicionar fila para tarefas externas.
- Separar workers de texto, traducao, audio e export.

Ferramentas recomendadas:

- PostgreSQL 17+.
- Redis + RQ, Dramatiq ou Celery.
- Alembic para migrations.

Criterios de aceite:

- Geracao completa roda com concorrencia segura.
- Resume nao corrompe estado.
- Falhas de provider nao travam todo o processo sem registro.

## Parte 16: Testes De Regressao

Testes obrigatorios:

- Export bloqueia deck parcial por padrao.
- Export com `--allow-partial` registra warning explicito.
- Traducao contendo `Error 500` falha validacao.
- DeepL quota excedida nao usa fallback silencioso sem gate.
- Duplicata entre niveis falha na curadoria.
- Palavra estrangeira indevida falha na curadoria.
- Exemplo sem lemma/forma valida falha.
- Job com review_required nao fica `completed`.
- `audit-deck` retorna erro para deck incompleto.
- APKG final contem `3000` cartoes e `6000` referencias de audio quando esperado.

Arquivos-alvo:

- `tests/services/test_text_validation.py`
- `tests/services/test_assemble_export_cards.py`
- `tests/services/test_export_anki_package.py`
- `tests/integration/test_frequency_e2e_export_flow.py`
- novos testes de curadoria por lingua.

## Parte 17: Ordem Recomendada De Implementacao

1. Bloquear export parcial e corrigir status do job.
2. Adicionar validacao de traducao para mensagens de erro.
3. Criar relatorio final de geracao.
4. Implementar logs estruturados por provider.
5. Melhorar retry/backoff/circuit breaker.
6. Remover fallback Google silencioso.
7. Expandir `audit-deck`.
8. Adicionar rastreabilidade por tags no APKG.
9. Criar pipeline de curadoria para todas as linguas.
10. Integrar validadores morfologicos por lingua.
11. Melhorar geracao de exemplos com multiplas opcoes.
12. Padronizar politica de audio fallback.
13. Migrar geracoes completas para PostgreSQL/fila.
14. Criar testes de regressao completos.

## Parte 18: Gates Minimos Para Aceitar Um Deck Final

Um deck de frequencia so deve ser aceito se cumprir:

| Gate | Criterio |
|---|---|
| Contagem total | `3000` cartoes |
| Nivel 1 | `1000` cartoes |
| Nivel 2 | `1000` cartoes |
| Nivel 3 | `1000` cartoes |
| Review required | `0` |
| Traducoes invalidas | `0` |
| Exemplos vazios | `0` |
| Traducoes vazias | `0` |
| Audio ausente | `0` |
| Audio failed | `0` |
| Duplicata de palavra/lemma | `0`, salvo excecao aprovada |
| Duplicata de exemplo | `0` |
| Tokens estrangeiros indevidos | `0` |
| Definicoes auditadas com erro | `0` |
| Job status | `completed` |
| Export status | `completed` |
| Relatorio final | gerado |
| Hash do APKG | registrado |

## Parte 19: Resultado Esperado Apos As Melhorias

Depois dessas mudancas, o processo deve produzir decks finais com:

- Qualidade lexical mais alta.
- Menos falhas de exemplo.
- Traducoes protegidas contra paginas de erro e fallback ruim.
- Audio consistente e auditavel.
- Export bloqueado quando incompleto.
- Jobs com estado confiavel.
- Relatorios completos para diagnostico.
- Curadoria reutilizavel para todas as linguas suportadas.

O objetivo final e que uma geracao completa nao dependa de inspecao manual do banco para saber se o deck e confiavel. O sistema deve dizer claramente se o deck passou ou falhou, por que falhou e qual acao tomar em seguida.
