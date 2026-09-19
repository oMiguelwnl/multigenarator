# Qualificação por IA — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox syntax for tracking.

**Goal:** Conectar fontes reais a propostas e julgamentos de IA rastreáveis, com rascunhos reaproveitáveis e fila de incerteza.

**Architecture:** Reutilizar os serviços de preparação, observações e pacotes existentes. Separar contratos de máquina, transporte limitado, execução retomável e projeções de rascunho; integrar tudo à CLI de qualificação.

**Tech Stack:** Python, Pydantic, Typer, LiteLLM, pytest; sem dependências novas.

**Spec:** `docs/superpowers/specs/2026-09-13-ai-qualification.md`

## Global Constraints

- Nenhum deploy, push ou merge.
- Nenhuma alteração dos nove campos Anki ou do campo Image vazio.
- Nenhuma alteração ou incorporação da refatoração concorrente.
- Sem dependências novas; Python/Pydantic/LiteLLM/CLI e validadores existentes.
- Sem ativação automática de perfis, redistribuição ou produção.
- Verificar software offline e executar um piloto real de fonte com revisões de agentes identificadas honestamente; exemplos de teste permanecem rotulados como mock.

## Passo 1 — Contratos, evidências e reconciliação

Arquivos: `services/qualification_machine.py`, `tests/services/test_qualification_machine.py`.
Interfaces: `MachineActor`, `MachineDecision`, `MachineReviewRequest`, `MachineReviewResponse`, `MachineReviewSubmission`, `MachineQualificationResult`; `build_machine_request`, `accept_machine_response`, `reconcile_machine_reviews`.

- [x] Escrever testes de vínculos adulterados, fontes estranhas, offsets, POS, divergência e mesmo contexto.
- [x] Confirmar falha antes da implementação.
- [x] Implementar decisões lexical/form/case fechadas, projeção de instruções/fontes, revisão e consenso determinístico.
- [x] Confirmar testes e inspecionar a separação dos contratos humanos.

```python
request = build_machine_request(packet, actor=actor, run_id="proposal-1")
submission = accept_machine_response(request, response, metadata=metadata)
judgment = build_machine_request(packet, actor=judge, run_id="judge-1", proposal=submission)
result = reconcile_machine_reviews(packet, submission, judged_submission)
assert result.production_eligible is False
```

## Passo 2 — Transporte limitado e reserva de orçamento

Arquivos: `services/qualification_ai_transport.py`, `tests/services/test_qualification_ai_transport.py`.
Interfaces: `AITransportLimits`, `AITransportResult`, `QualificationAITransport.complete(messages, response_schema)`; `MachineRunBudget` e reserva persistida pelo executor.

- [x] Testar JSON duplicado, resposta extensa, timeout, ausência de ferramentas, tokens, segredo em erro e teto monetário.
- [x] Confirmar falha inicial e implementar adaptador LiteLLM injetável, sem retries ocultos.
- [x] Exigir preços e limites explícitos, contabilizando tentativas incertas integralmente.
- [x] Verificar chamadas mock e ausência de chamadas reais durante testes.

```python
transport = QualificationAITransport(model="openai/model", limits=limits, completion_func=fake)
answer = transport.complete(messages=messages, response_schema=schema)
assert answer.input_tokens >= 0
```

## Passo 3 — Pipeline de fontes local, retomável, para 22 idiomas

Arquivos: `services/qualification_pipeline.py`, `tests/services/test_qualification_pipeline.py`.
Interfaces: `QualificationPipelineRequest`, `run_qualification_pipeline(request, output)`.

- [x] Testar pacote real mínimo, retomada íntegra, fonte/saída adulterada, referências explícitas e NFC.
- [x] Confirmar falha inicial; implementar verificação de preparados/observações e chamada de `prepare_qualification_pilot`.
- [x] Registrar seleção de sementes e limitações linguísticas; promover sidecar de categorias quando necessário.
- [x] Verificar configuração de todos os idiomas sem reexecutar seus modelos.
- [x] Acrescentar `services/qualification_machine_evidence.py` e teste correspondente: `enrich_machine_packet(packet, pipeline, manifest_sha256)` deve ligar cada item ao pacote fonte, expor as ocorrências já verificadas e os detalhes lexicais disponíveis, preservar medidas e indicar cobertura incompleta. Regressão: três ocorrências da mesma fonte não podem aparecer como evidência completa de apenas uma frase.

```python
first = run_qualification_pipeline(request, output)
assert run_qualification_pipeline(request, output) == first
```

## Passo 4 — Execução, rascunho e calibração de máquina

Arquivos: `services/qualification_machine_runner.py`, `services/qualification_machine_draft.py`, `services/qualification_machine_calibration.py` e testes correspondentes.

- [x] Escrever testes de rodada proposta/julgamento, importação offline, retomada e reserva interrompida.
- [x] Implementar execução sequencial, manifesto e hash de cada artefato; cache só para a mesma execução exata.
- [x] Produzir mapeamentos de sentido/formas com evidências e fila de incerteza, preservando candidatos.
- [x] Implementar calibração e avaliação identificadas como máquina, reutilizando `score_evidence`, com grade limitada, replay e separação de fontes.
- [x] Verificar que contratos humanos e importação nativa não aceitam o artefato de máquina como aprovação.

```python
assert draft.origin == "machine"
assert draft.production_eligible is False
assert calibration.label_origin == "machine"
```

## Passo 5 — CLI, piloto PT20, documentação e entrega

Arquivos: `qualification_machine_cli.py`, montagem em `qualification_cli.py`, `tests/test_qualification_machine_cli.py`, `docs/ai-linguistic-qualification.md`, links na documentação existente.

- [x] Integrar `qualification ai` com pipeline, pedidos offline, importação, reconciliação, rascunho, calibração e execução de API limitada.
- [x] Testar fluxo pela CLI com provedores mock e fontes verificadas.
- [x] Preparar 20 grafias candidatas explícitas de PT; exportar pedidos e realizar revisão de agentes com contexto separado, sem API paga do repositório.
- [x] Validar respostas e produzir relatório de cobertura, decisões e incertezas; não representar opiniões de IA como frequência medida.
- [x] Revisar segurança e integração; rodar regressões relevantes em cópia isolada de HEAD mais arquivos próprios.
- [x] Documentar comandos, resultados reais e limites; atualizar este plano e registrar somente alterações próprias em commits por domínio.

## Registro de decisões

- O usuário já aprovou a proposta e sua implementação; não haverá nova pergunta sobre executar o plano.
- A branch de feature existente é mantida. A verificação isolada usa arquivo de HEAD mais arquivos próprios para não capturar as 326 alterações concorrentes registradas em `.multilang/verification/ai-qualification/before.json`.
- Revisões por agentes desta sessão podem exercitar o caminho offline sem gasto de API do repositório. A identidade exata de modelo/revisão só será registrada quando fornecida pelo ambiente; informação ausente continuará desconhecida.
- A revisão real revelou que o pacote original apresentava só uma ocorrência por fonte. A projeção enriquecida é um novo artefato verificável, sem mudar os resultados da primeira revisão nem solicitar ao usuário trechos que já existem no projeto.

## Resultado da execução

- Contratos, transporte, pipeline, enriquecimento, lotes, execução retomável, rascunho, relatório, calibração e avaliação estão integrados à CLI. Não foram acrescentadas dependências.
- Piloto real: 20 grafias, 129 candidatos lexicais, 761 propostas de formas de dicionário, 15 grupos medidos e 200 casos. As fontes produziram 1.105 itens para revisão, exportados em 57 pedidos enriquecidos verificáveis.
- Dois agentes em contextos distintos revisaram os mesmos 144 itens lexicais/medidos: 102 mapeamentos lexicais em acordo e 42 itens com incerteza. A identidade exata dos modelos permaneceu desconhecida, sem alegação de modelos independentes.
- Nenhuma forma adicional foi aprovada; não há rótulos suficientes para calibrar uma política real de importância. A implementação preserva essa insuficiência no relatório.
- Os pacotes enriquecidos acrescentam contextos e dados lexicais existentes para outra revisão. Não reescrevem as decisões reais da primeira rodada nem alegam nova revisão concluída.
- Verificação isolada: 318 casos de teste distintos aprovados, contabilizando a união das suítes focada, de regressão e de enriquecimento. O XML intermediário com falha no teste recém-adicionado é histórico; a execução final passou os 17 casos do incremento.
- Evidências e artefatos locais: `.multilang/verification/ai-qualification/`; relatório: `pt20-result/report.html`; rascunho: `pt20-draft/draft.json`. Não houve chamadas de API do repositório, deploy ou alterações nos campos Anki.

- A CLI foi novamente verificada com somente a integração desta entrega sobre HEAD: 15 casos passaram. As alterações concorrentes de seleção de modelos permanecem no diretório de trabalho e não integram estes commits.
- A inspeção visual em navegador não foi concluída neste ambiente; o HTML tem testes automatizados de conteúdo e segurança.
