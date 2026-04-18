# Phase 1: Job Orchestration & Recovery - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-18
**Phase:** 01-job-orchestration-recovery
**Areas discussed:** Superfície do job, Progresso e falhas, Retomada de execuções, Rerun e duplicação

---

## Superfície do job

| Option | Description | Selected |
|--------|-------------|----------|
| CLI primeiro | Terminal como interface principal agora; API interna pode vir depois | ✓ |
| CLI + API já | Desenhar os dois desde a Fase 1 | |
| API primeiro | Priorizar endpoint/serviço desde o começo | |

**User's choice:** CLI primeiro
**Notes:** v1 deve começar com operação centrada em CLI.

| Option | Description | Selected |
|--------|-------------|----------|
| Um comando + flags | Menos comandos; um fluxo principal com opções claras | ✓ |
| Subcomandos | Comandos separados para start, status, resume, rerun | |
| Você decide | Deixar o detalhe para o planner | |

**User's choice:** Um comando + flags
**Notes:** a superfície do CLI deve ser mais enxuta no começo.

---

## Progresso e falhas

| Option | Description | Selected |
|--------|-------------|----------|
| Etapas + contadores | Mostrar estágio atual, quantos itens passaram/falharam e resumo claro | ✓ |
| Logs detalhados | Exibir eventos mais granulares durante a execução | |
| Quase silencioso | Mostrar só início, fim e erro final | |

**User's choice:** Etapas + contadores
**Notes:** o padrão do v1 deve priorizar visibilidade operacional sem virar stream verboso.

| Option | Description | Selected |
|--------|-------------|----------|
| Continuar e marcar | Seguir com o restante e registrar claramente o que falhou | |
| Parar no 1o erro | Interromper o job assim que a primeira falha aparecer | |
| Você decide | Deixar esse ponto para o planner fechar | |

**User's choice:** Retry automático no item; se ainda falhar, seguir o job e marcar como falho
**Notes:** a resposta veio em texto livre e foi confirmada explicitamente.

---

## Retomada de execuções

| Option | Description | Selected |
|--------|-------------|----------|
| Continuar do último ponto | Reaproveitar o que já concluiu e seguir só com o que falta | ✓ |
| Revalidar e reprocessar | Checar tudo de novo antes de continuar | |
| Reiniciar do zero | Resume só reenfileira o job inteiro | |

**User's choice:** Continuar do último ponto
**Notes:** resume deve preservar trabalho já concluído.

| Option | Description | Selected |
|--------|-------------|----------|
| Parar com diagnóstico | Não arriscar duplicação; explicar o problema e pedir nova ação | ✓ |
| Tentar reiniciar sozinho | O sistema decide um restart sem confirmação | |
| Você decide | Deixar esse fallback aberto para o planner | |

**User's choice:** Parar com diagnóstico
**Notes:** segurança e rastreabilidade importam mais do que heurísticas automáticas nesse caso.

---

## Rerun e duplicação

| Option | Description | Selected |
|--------|-------------|----------|
| Pular duplicados | Não criar de novo o que já existe; processar só o que falta | ✓ |
| Substituir existentes | Rerun atualiza o que já foi gerado anteriormente | |
| Versionar tudo | Cada rerun cria uma nova versão completa | |

**User's choice:** Pular duplicados
**Notes:** o padrão de rerun deve ser conservador e idempotente.

| Option | Description | Selected |
|--------|-------------|----------|
| Exigir confirmação | Só sobrescrever ou reprocessar itens existentes quando ficar explícito | ✓ |
| Sempre pular | Nunca mexer no que já existe em rerun manual | |
| Sempre substituir | Rerun manual já implica atualizar tudo que bater | |

**User's choice:** Exigir confirmação
**Notes:** conflitos em rerun manual não devem ser resolvidos silenciosamente.

---

## the agent's Discretion

- Nomes exatos dos flags e formato final do output no terminal.
- Número exato de retries automáticos por item.

## Deferred Ideas

None.
