---
mode: quick
task: 031-persistir-plano-mestre-v4
subsystem: documentation
tags: [v4, multilingual, lexical-identity, anki, adaptive-queue, migration]
runtime: opencode
assurance: self_checked
requires:
  - active v3.0 Korean SPEC/ROADMAP/STATE as read-only context
  - user-approved locked decisions D-01 through D-15
provides:
  - Standalone Portuguese v4 lexical/adaptive master plan
  - Normative G0 and Phase 35-51 delivery sequence
  - Traceability, capability, cross-gate, and migration audit matrices
affects: [future-v4-planning]
tech-stack:
  added: []
  patterns: [fail-closed language profiles, stable lexical identity, evidence-bearing gates, previewed in-place migration]
key-files:
  created:
    - docs/multilingual-lexical-adaptive-plan-v4.md
  modified: []
key-decisions:
  - "Preserve v4 as a non-active proposal until v3.0 is completed, G0 passes, and a separate promotion action is approved."
  - "Keep exactly 22 modern-language profiles under the modern architecture and Classical Latin on its isolated Portuguese path."
  - "Treat forms, form-specific Definitions, exact-form audio, cards, examples, and media as relationships outside the 3000-identity Core quota."
  - "Keep the approved fixed ownership from Phase 35 contracts through Phase 50 rehearsal-only and Phase 51 confirmed apply/release."
requirements-completed: []
duration: 29min
completed: 2026-07-27
---

# Quick Task 031: Persistir o plano mestre lexical/adaptativo v4 — Resumo

**O plano mestre normativo de 857 linhas agora preserva fielmente a matriz individual dos 22 idiomas modernos mais Latim, os 12 contratos de card/forma/sentido/rota/carga/GUID e a ownership fixa de G0 e das Fases 35–51, sem ativar a v4.**

## Desempenho

- **Duração acumulada:** 29 min (12 min da execução inicial + 17 min da revisão de fidelidade)
- **Início:** 2026-07-27T17:23:44Z
- **Início da revisão de fidelidade:** 2026-07-27T17:39:30Z
- **Primeira conclusão verificada da revisão:** 2026-07-27T17:50:43Z
- **Conclusão final da revisão:** 2026-07-27T17:56:28Z
- **Tarefas:** 2 de 2
- **Artefato substantivo revisado:** 1 arquivo, 857 linhas, 11.823 palavras e 85.310 bytes
- **Ações Git:** nenhuma; nenhum arquivo foi staged, committed, amended ou pushed

## Trabalho concluído

### Tarefa 1 — Contratos canônicos e sequência G0–51

- Criado `docs/multilingual-lexical-adaptive-plan-v4.md` como proposta v4 autônoma e explicitamente não ativa.
- Registrada a matriz exata de 22 idiomas modernos mais um Latim clássico isolado, incluindo as quatro políticas literais de idioma das explicações.
- Adicionada a matriz individual de 23 códigos com variante/locale, escrita, segmentação, identidade, morfologia, MWE/funções, matching, áudio e goldens; ela preserva explicitamente capitalização alemã, `hr` sem `sh`, `nb`, `е/ё`/stress/aspecto russo, `ș/ț` romeno, UniDic japonês, segmentação/scripts/polifonia chinesa, NFC/Kiwi coreano e Latim clássico isolado.
- Definidos `LanguageProfile`, identidade `language + normalized lemma + POS + sense`, `Core 3x1000`, `Optional expansion 0-3000`, `SurfaceForms`, `Important Forms`, `Definitions`, `Exact-form audio`, MWE, rotas e papéis de card.
- Fixados os 12 contratos `CARD-01`, `FORM-01..03`, `SENSE-01`, `MWE-01`, `ROUTE-01`, `DEF-01`, `AUDIO-01`, `LOAD-01`, `DEPEND-01` e `GUID-01`.
- Fixados um reconhecimento por identidade por padrão; reverse/listening/cloze desabilitados; seleção limitada de Important Forms; formas fora do Core; pré-requisito do lema, sibling burying, GUID semântico e workload por deck extra.
- Incluídos exemplos contextuais de `be/is/was/were`, distinguindo passado indicativo e irrealis de `were`, definição contextual e áudio da forma exata.
- Conectados custom lists, highlights, `read-only APKG history`, `adaptive queue`, `real subdecks` e `in-place Multilang migration` em um fluxo versionado, determinístico, recuperável e fail-closed.
- Corrigida a ownership fixa: 35 contratos; 36 persistência; 37 fontes/cobertura; 38 morfologia/curadoria; 39 piloto; 40–44 rollouts por família; 45 freeze; 46 edições/export; 47 histórico; 48 ranking; 49 conteúdo/áudio; 50 ensaio somente; 51 preflight/apply/release.
- Formalizados gates transversais de privacidade, licença, custo e qualidade, além do grafo de dependências e das duas decisões separadas de promoção/release.

### Tarefa 2 — Auditoria de rastreabilidade e isolamento

- Auditadas e marcadas como `Coberto` todas as decisões D-01–D-15.
- Atualizadas as quatro tabelas finais — decisões, capacidades, gates por G0/Fase e invariantes da migração — para a nova ownership, sem linha antiga remanescente.
- Tornadas explícitas as ambiguidades críticas: unidade de 3000 é identidade lexical; expansão é opcional/adicional; formas/cards não consomem Core; definição e áudio ligam-se à forma exibida; MWE/sentidos mantêm identidade/rota; dados pessoais não mudam ranks; APKG/fila nunca mutam Anki; níveis/papéis são subdecks reais; migração exige `prévia -> backup -> confirmação explícita`.
- Mantidas fontes, licenças, providers, budgets e limiares ainda desconhecidos como gates bloqueantes, sem aprovação inventada.
- Separado o ensaio clone-only da Fase 50 do preflight, confirmação hash-bound, apply transacional e release da Fase 51.

## Resultados exatos da verificação do plano

`rg` não está instalado no shell (`/usr/bin/bash: line 1: rg: command not found`). Conforme autorizado pelo plano para portabilidade, os checks de busca/contagem foram executados com Python 3 lendo o mesmo arquivo em UTF-8 e aplicando as mesmas condições.

### Verificações da Tarefa 1

1. Existência e headings: **PASS** — `file exists; G0 and Fases 35-51 headings found`.
2. Matriz por família: **PASS** — `Moderno=22; Latim isolado=1`.
3. Linhas exatas dos idiomas: **PASS** — `all 23 required language rows found`.
4. Contratos e features: **PASS** — `13 contract labels and 8 form features found`.

### Verificações da Tarefa 2

1. Marcadores por etapa: **PASS** — `Resultado=18, Depende de=18, Entregáveis=18, Critérios de saída=18`.
2. Políticas e sequência de migração: **PASS** — `all 5 policy/migration phrases found`.
3. Gates e decisões: **PASS** — `4 gate headings and D-01..D-15 rows found`.
4. Linhas de auditoria: **PASS** — `G0 and Fases 35-51 audit rows found`.
5. `git diff --check`: **PASS**. O Git emitiu avisos LF→CRLF para sete arquivos sujos preexistentes (`.planning/quick/LOG.md`, três templates e três testes), sem erro de whitespace.
6. Whitespace UTF-8 do documento: **PASS** — saída exata `v4 master-plan Markdown whitespace OK`.
7. `git diff --exit-code -- .planning/SPEC.md .planning/ROADMAP.md .planning/STATE.md`: **PASS**, sem saída de diff.

### Verificações adicionais de fidelidade

1. **PASS** — `REVISED FIDELITY CHECK PASS: exact Phase 35-51 allocation, 11 dependency edges, 23 language requirement rows, 12 contracts, and locked language/card/form examples found`.
2. **PASS** — `STALE OWNERSHIP CHECK PASS: no former Phase 35-51 headings, dependency edges, or audit ownership rows remain`.
3. **PASS** — `PHASE OWNERSHIP CONTENT CHECK PASS: every Phase 35-51 block contains its locked owner-specific evidence`.

### Provas adicionais de escopo

- **PASS** — `REVISION BASELINE ISOLATION PASS: 26 protected pre-existing files byte-identical; 2 pre-existing deletions preserved; only target document and SUMMARY changed`.
- **PASS** — `REVISION STATUS PATH COUNT=30; PROTECTED BASELINE PATH COUNT=28; ALLOWED WRITE PATH COUNT=2`.
- **PASS** — staging vazio (`git diff --cached --quiet`).
- `.planning/quick/LOG.md` permaneceu com o SHA-256 inicial `f31539b1f5de4dc6549cd4a0adc411aa9b59dae6e829f1cb2b8e8d869396441d`.
- `.planning/SPEC.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, código-fonte, testes, templates, configs, assets e exports não foram modificados por esta execução.
- Nenhum artefato de UI/prova de browser foi criado ou alegado.

## Decisões tomadas

Nenhuma nova decisão de fonte, licença, provider, orçamento ou limiar foi tomada. A revisão restaurou a última alocação de fases aprovada pelo usuário e explicitou contratos já exigidos; escolhas externas continuam nos gates.

## Desvios e correções

### Auto-fixed Issues

**1. [Rule 1 — Fidelidade documental] Corrigida a redistribuição indevida da ownership das Fases 35–51**

- **Encontrado por:** revisão de fidelidade do usuário após a primeira execução.
- **Problema:** a primeira versão atribuiu identidade, fontes, forms, conteúdo, áudio, export e migração a fases diferentes da última sequência aprovada.
- **Correção:** substituída toda a seção 35–51, o grafo, os mappings D-01–D-15, a tabela de capacidades, a matriz de gates e as invariantes da migração pela alocação fixa revisada.
- **Verificação:** checks de fidelidade, conteúdo por fase e ausência de ownership antiga passaram.

**2. [Rule 2 — Contrato crítico omitido] Adicionadas especificidade por idioma e regras normativas de card/forma**

- **Encontrado por:** mesma revisão de fidelidade.
- **Problema:** faltavam a matriz individual de 22 códigos modernos + Latim e os contratos CARD/FORM/SENSE/MWE/ROUTE/DEF/AUDIO/LOAD/DEPEND/GUID.
- **Correção:** adicionadas 23 linhas linguísticas, 12 contratos, defaults de card, seleção/quotas/dependências de formas, GUID/workload e exemplos `is/was/were`.
- **Verificação:** o check revisado encontrou 23 linhas, 12 contratos e todos os detalhes linguísticos/card exigidos.

### Diferenças recuperáveis de ambiente

1. O arquivo solicitado na execução inicial `.planning/templates/roles/executor.md` não existe; foi usado o skill versionado `gsdd-execute` sem alterar templates.
2. `rg` não existe no shell; Python reproduziu as mesmas buscas, contagens, case-folding e word boundaries.

## Problemas encontrados

- Dois helpers de verificação adicionais precisaram de quoting seguro para backticks/newlines no Bash; as versões corrigidas passaram. As tentativas foram somente leitura e não tocaram arquivos.

## Stubs conhecidos

Nenhum. A busca por `TODO`, `FIXME`, placeholders e valores vazios de implementação não encontrou stub no documento; menções ao campo `Image` vazio são invariantes deliberados do produto, não conteúdo incompleto.

## Superfície de ameaça

Nenhuma superfície executável foi introduzida. O documento futuro cobre explicitamente os limites de confiança de dados pessoais, fontes/providers, parser APKG e migração in-place, com mitigação e falha fechada.

## Limites da afirmação

O arquivo preserva uma proposta, não comprova a implementação da v4. Nenhuma fonte, licença, voz/provider, budget, limiar de qualidade, profile/capability, migração ou release foi aprovado pela documentação. A v3.0 permanece ativa e inalterada.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Todos os 11 comandos do plano e os três checks adicionais de fidelidade passaram; a alocação 35-51, 23 requisitos linguísticos, 12 contratos e ausência de ownership antiga foram verificados.
</executor_check>
</checks>

<handoff>
plan_runtime: opencode
plan_assurance: self_checked
plan_check_status: unknown
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: false
</handoff>

<deltas>
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: A revisão do usuário demonstrou que a primeira versão divergia da ownership aprovada e omitia especificidade/contratos; documento e resumo foram corrigidos integralmente dentro do write set permitido.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: O arquivo .planning/templates/roles/executor.md solicitado não existe; o executor usou o skill gsdd-execute versionado e não alterou templates.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: O binário rg não está instalado; equivalentes Python reproduziram todas as condições e contagens do plano.
</deltas>

<judgment>
<active_constraints>
Manter v3.0 e seus artefatos ativos imutáveis; não iniciar v4; preservar a árvore suja; não selecionar fontes/providers/licenças/limiares sem evidência; manter Latim isolado.
</active_constraints>
<unresolved_uncertainty>
Fontes, direitos de redistribuição, providers, budgets e limiares numéricos de qualidade continuam deliberadamente pendentes para G0 e os gates responsáveis.
</unresolved_uncertainty>
<decision_posture>
Tratar o plano v4 como contrato preservado e fail-closed, com ownership fixa: contratos 35, persistência 36, fontes 37, morfologia 38, piloto 39, famílias 40–44, freeze 45, export 46, histórico 47, ranking 48, conteúdo 49, ensaio 50 e apply/release 51.
</decision_posture>
<anti_regression>
Não redistribuir a ownership 35–51; não remover a matriz individual ou os 12 contratos; não reduzir 3000 a cards/formas; manter opcionais disabled, forms fora do Core, sequencing/burying/GUID/workload; não escrever no Anki; não aplicar migração na Fase 50; não executar a Fase 51 sem prévia, backup e confirmação hash-bound; manter Latim isolado.
</anti_regression>
</judgment>

## Self-Check: PASSED

- O documento e este resumo existem, são UTF-8, terminam em newline e não têm whitespace final.
- Os 11 checks revisados do plano e os três checks adicionais de fidelidade passaram.
- O documento contém 857 linhas, 11.823 palavras e 85.310 bytes.
- A alocação exata 35–51, as 11 arestas, as 23 linhas linguísticas, os 12 contratos e os exemplos/regras de card/forma foram encontrados.
- Nenhum heading, aresta ou ownership de auditoria da versão incorreta permaneceu.
- Os 26 arquivos preexistentes protegidos conservaram seus hashes; as duas deleções preexistentes permaneceram; somente documento e resumo mudaram.
- `.planning/SPEC.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` e `.planning/quick/LOG.md` permaneceram intactos.
- O index Git permaneceu vazio; nenhum stage, commit, amend ou push foi executado.
