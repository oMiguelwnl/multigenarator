# Prompt Para Implementar O Restante Das Melhorias De Geracao

Use este arquivo como mensagem para uma IA/agente de codigo continuar a implementacao do pipeline de geracao de decks.

## Mensagem Para A IA

```text
Continue a implementacao do plano em docs/generation-process-improvement-plan.md, usando docs/polish-deck-generation-analysis-2a7473ce.md como caso concreto de falha.

Ja foram implementados e devem ser preservados:
- Bloqueio de export parcial por padrao.
- Flag explicita --allow-partial.
- Status de job/export como blocked, partial e completed.
- Validacao contra traducoes invalidas como Error 500, HTML, quota/captcha/server error.
- Remocao do fallback silencioso DeepL -> Google quando translation_provider=deepl.
- audit-deck expandido para deck incompleto, nivel incompleto, traducao invalida, duplicatas e midia ausente.
- Relatorio final basico de geracao.
- Testes direcionados desses pontos.

Nao reimplemente esses itens do zero. Leia o codigo atual e avance a partir dele.

Objetivo agora:
Implementar o restante necessario para reduzir geracao ruim antes do export, melhorar rastreabilidade do APKG, melhorar observabilidade, e preparar o pipeline para decks completos confiaveis em todas as linguas suportadas.

Linguas suportadas no escopo:
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

Prioridade 1: Curadoria global das listas de frequencia para todas as linguas
- Usar wordfreq apenas como bootstrap, nao como fonte final ao vivo.
- Criar pipeline de curadoria por lingua.
- Gerar candidatos acima de 3000 por lingua, por exemplo 5000 a 10000.
- Normalizar Unicode, caixa, pontuacao, espacos e variantes.
- Remover tokens ruins: URLs, emails, hashtags, handles, emojis, emoticons, tokens numericos puros, pontuacao, letras isoladas sem aprovacao, marcas, nomes proprios sensiveis, abreviacoes ruins e palavras estrangeiras obvias.
- Deduplicar por lingua, forma normalizada, lemma e rank.
- Separar exatamente 3 niveis de 1000 itens por lingua.
- Implementar backfill sem repetir itens ja usados em outro nivel.
- Registrar rejeicoes com motivo rastreavel.
- Congelar listas versionadas em artefatos ou tabelas.
- Garantir que a geracao final use listas curadas congeladas, nao wordfreq cru.

Artefatos sugeridos:
.multilang/sources/frequency/{language}/candidates-wordfreq-v1.csv
.multilang/sources/frequency/{language}/curated-v1.csv
.multilang/sources/frequency/{language}/rejections-v1.csv
.multilang/sources/frequency/{language}/curation-report-v1.md

Campos minimos da lista curada:
- language
- frequency_list_version
- level
- rank
- source_rank
- display_form
- lemma
- lemma_key
- part_of_speech
- definition_seed
- source_provenance
- curation_flags

Prioridade 2: Deduplicacao global entre niveis
- Garantir que nenhuma forma/lemma apareca em mais de um nivel do mesmo deck de frequencia.
- Adicionar validacao antes de persistir lexical_candidates.
- Adicionar testes com duplicatas nas fronteiras Level 1/2 e Level 2/3.
- O caso observado no deck polones tinha duplicatas como wspolnego, cokolwiek, komisja, narodu etc. Esse padrao deve ser impedido.

Prioridade 3: Rastreabilidade no APKG
- Preservar o schema de campos atual, a menos que haja decisao explicita em contrario.
- Adicionar tags Anki por nota com job_id, language, source_type, level, rank e item_key.
- Exemplo de tags: multilang, pl, frequency, level_1, rank_0001, job_2a7473ce.
- Se viavel, separar o deck em subdecks por nivel: Multilang Polish::Level 1, Multilang Polish::Level 2, Multilang Polish::Level 3.
- Atualizar audit-deck para validar tags ou subdecks por nivel.
- Adicionar testes de export APKG garantindo que tags/rastreabilidade existem.

Prioridade 4: Language-id e validacao linguistica
- Adicionar validacao de idioma para exemplos e traducoes.
- Rejeitar exemplos com tokens estrangeiros indevidos para a lingua alvo.
- Rejeitar frases polonesas com tokens como the, le, a usados como tokens estrangeiros, salvo se a lingua/entrada justificar.
- Validar que a traducao esta no idioma esperado.
- Usar uma ferramenta leve inicialmente, como lingua-language-detector ou fastText, com fallback deterministico em testes.
- Adicionar testes para frases com lingua errada e traducao em idioma errado.

Prioridade 5: Validacao morfologica por lingua
- Criar interface de validacao morfologica por lingua.
- Inicialmente implementar validadores simples com fallback, sem bloquear desenvolvimento das 11 linguas.
- Para polones, preferir Morfeusz2 ou Stanza Polish quando disponivel.
- Para russo, considerar pymorphy3 ou Stanza Russian.
- Para as demais linguas, usar spaCy/Stanza quando adequado.
- A validacao deve confirmar que a sentenca contem o lemma ou uma forma flexionada aceitavel.
- Reduzir falsos positivos de missing_target_lemma em linguas flexivas.

Prioridade 6: Telemetria estruturada por chamada externa
- Criar tabela ou log estruturado provider_call_logs.
- Registrar chamadas para LLM, traducao e TTS.
- Campos recomendados: job_id, item_key, task_type, provider, model, attempt, latency_ms, status, error_code, error_summary, fallback_from, prompt_hash, response_hash, tokens, estimated_cost, created_at.
- Atualizar generation-report para incluir tempos, falhas, retries, provedores, custo estimado e volume de chamadas.
- Nao registrar prompts completos com dados sensiveis; usar hash e redacao.

Prioridade 7: Retry, backoff e circuit breaker
- Melhorar src/multilang/services/provider_retry.py.
- Implementar exponential backoff com jitter.
- Respeitar Retry-After quando disponivel.
- Classificar 403, 429, timeout, network e quota.
- Adicionar circuit breaker por provider/model para evitar bloqueios como o 403 do OpenRouter.
- Quando provider bloquear, marcar job como blocked com motivo claro e permitir resume posterior.
- Adicionar testes deterministas com sleeper fake.

Prioridade 8: Politica de fallback de audio
- Definir gate para fallback TTS.
- Para deck final, bloquear fallback TTS nao aprovado ou marcar partial/warning conforme flag explicita.
- Registrar provider e voz por item no relatorio.
- Permitir regenerar apenas audios que usaram fallback.
- Validar MP3 com byte_size e, se possivel, duracao real.

Prioridade 9: Expandir relatorio final de geracao
- O relatorio atual e basico. Expandir com:
  - tempo por etapa
  - chamadas por provider
  - latencia media por provider
  - retries
  - falhas normalizadas
  - fallbacks usados
  - custo estimado
  - tokens quando disponivel
  - contagem por nivel
  - duplicatas detectadas
  - invalid translations
  - audio fallback count
  - APKG sha256
  - lista de gates que passaram/falharam

Prioridade 10: Testes de regressao
Adicionar testes para:
- Curadoria remove tokens estrangeiros e lixo por lingua.
- Curadoria gera 3 niveis de 1000 sem duplicatas.
- Backfill nao repete itens entre niveis.
- Export APKG contem tags de rastreabilidade.
- audit-deck valida tags/subdecks por nivel.
- Language-id rejeita exemplo em idioma errado.
- Language-id rejeita traducao no idioma errado.
- Retry usa backoff e para em circuit breaker.
- Relatorio final inclui provider_call_logs agregados.
- Audio fallback e bloqueado ou reportado conforme politica.

Restrições de implementação:
- Faça mudanças pequenas e verificaveis.
- Preserve os gates ja implementados.
- Nao remova testes existentes.
- Evite depender de APIs externas em testes.
- Use fixtures/fakes deterministicas.
- Se uma dependencia pesada for opcional, implemente fallback e testes sem depender dela instalada.
- Nao coloque secrets em logs ou fixtures.

Comandos de verificacao esperados:
python -m pytest tests/services/test_text_validation.py tests/domain/test_deck_audit.py tests/cli/test_export_command.py tests/integration/test_frequency_e2e_export_flow.py
python -m pytest

Entregavel esperado:
- Codigo implementado.
- Testes adicionados/atualizados.
- Documentacao atualizada em docs/ quando houver mudanca de fluxo.
- Resumo final indicando o que foi implementado, o que ficou pendente e quais testes foram executados.
```

## Observacao

Este prompt intencionalmente nao pede para refazer os gates de export ja implementados. O foco e impedir que conteudo ruim chegue tao longe no pipeline, melhorar rastreabilidade e tornar diagnostico/custos/falhas observaveis.
