---
mode: quick
task: 037-compactar-espacamento-fields
plan: 037
runtime: opencode
assurance: self_checked
verified: 2026-08-02T20:24:38Z
status: human_needed
score: 6/6 must-haves verified
overrides_applied: 0
delivery_posture: delivery_sensitive
evidence_contract:
  required_kinds: [code, runtime, delivery]
  recommended_kinds: [test, human]
  observed_kinds: [code, test, runtime, delivery]
  missing_kinds: []
ui_proof_comparison:
  compact-fields-code-test-apkg: satisfied
  compact-fields-native-anki-recheck: partial
  native_partial_reason: deferred human acceptance only
human_verification:
  - test: "Importar german_frequency_template_dummy.apkg e inspecionar a frente de um card curto."
    expected: "O painel continua alto e centralizado, enquanto os fields ficam compactos e sem grandes vazios artificiais."
    why_human: "Aparência e espaçamento no WebView nativo do Anki são julgamentos visuais."
  - test: "Revelar o verso no Anki."
    expected: "Translation, definição, imagem vazia e controles de áudio permanecem visualmente corretos."
    why_human: "A integração visual nativa não pode ser concluída por inspeção estática do CSS/APKG."
  - test: "Inspecionar no Anki o card de conteúdo longo."
    expected: "O conteúdo permanece legível e cresce ou rola naturalmente, sem clipping."
    why_human: "Overflow e sensação de uso dependem do renderer e do tamanho real usados pelo usuário."
git_delivery_check:
  branch: Monarch
  commits_ahead_of_main: unknown
  pr_state: unknown
  staged_changes: false
  note: "A ref main não existe localmente; consulta de PR não foi feita nesta verificação focada/offline."
---

# Quick 037: Compactar espaçamento entre fields — Verification Report

**Objetivo:** remover do painel o flex com `space-between` rejeitado pelo usuário, mantendo o shell alto/responsivo, a herança Mandarin e um novo APKG alemão com identidades Quick 037.

**Status:** `human_needed`. Não há gap automatizável; falta somente a aceitação visual do novo pacote no Anki nativo.

## Verification Basis

- Verificação inicial: não existia `037-VERIFICATION.md`.
- Contrato: seis truths, cinco artifacts e três key links do frontmatter de `037-PLAN.md`; `requirements: []`.
- `037-SUMMARY.md` foi tratado como alegação. Código, diff, testes, APKG e bundles foram verificados independentemente.
- Runtime de execução e verificação: `opencode`; assurance limitada a `self_checked`.
- Escopo deliberadamente focado: somente o teste nominal, os dois arquivos pytest autorizados, probes de CSS/APKG, validação/comparação dos bundles e diff pertinente. Nenhuma suíte ampla foi executada.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidência |
|---|---|---|---|
| 1 | Os fields voltam ao fluxo vertical compacto, sem distribuir a altura livre entre os filhos do painel. | ✓ VERIFIED | O último bloco carregado para `.customCard` resolve `display: block`; não contém `flex-direction`, `justify-content` ou `align-items`. O probe percorreu normal e as duas rotas Mandarin. |
| 2 | O painel continua alto, responsivo e centralizado externamente, sem regressão na geometria existente. | ✓ VERIFIED | `normal_card.md:473-500` mantém `.card` como flex/center/100vh e o painel com `min-height: min(760px, calc(100vh - 80px))`, padding responsivo, `width: 100%` e `max-width: 460px`. |
| 3 | O bloco final vencedor de `.customCard` é exatamente block e não reintroduz propriedades flex do painel. | ✓ VERIFIED | Bloco final em `normal_card.md:482-500`; o teste e o probe selecionam a última ocorrência, não uma ocorrência antiga. `space-between` remanescente pertence a linhas internas, não ao painel. |
| 4 | Mandarin herda a correção pela composição CSS normal existente, sem alteração do template Mandarin. | ✓ VERIFIED | `card_template_loader.py:62-80` antepõe `base_template.css`; `mandarin_card.md` não possui override `.customCard`. Frequency e word-list Mandarin foram carregados e produziram o mesmo contrato final. |
| 5 | O novo APKG alemão contém sete cards, o CSS corrigido e somente IDs `1995037001`/`1995037002`. | ✓ VERIFIED | Inspeção ZIP/SQLite: 7 notes/7 cards, modelo/deck Q037, conjuntos de IDs exatos, IDs de produção ausentes, nove fields válidos e CSS embutido byte a byte igual ao modelo German frequency live. |
| 6 | O UAT anterior rejeitado e a nova aceitação pendente estão registrados honestamente. | ✓ VERIFIED | `NATIVE-ANKI-RECHECK.md:124-130` registra o UAT anterior `failed` por espaçamento excessivo e o atual `human_needed`, sem observação nova marcada como passed. |

**Score:** 6/6 must-haves verificados. A inspeção visual nativa é um gate humano separado e, por contrato, não reduz esse score nem vira gap automatizável.

## Diff Real e Preservação de Escopo

- `git diff` atual é cumulativo porque as Quicks 035/036 já estavam no worktree sem commit. Contra `HEAD`, `normal_card.md` mostra apenas a geometria alta/responsiva da Quick 035 (`min-height`, padding e remoção do override `.cardBack`); a Quick 037 devolveu `display: block` e removeu as três declarações flex, portanto essas quatro linhas voltaram ao estado de `HEAD` e não aparecem como delta líquido.
- A comparação com o predecessor imediato é inequívoca: o proof verificado da Quick 035 registrava o bloco vencedor com `display: flex`, `flex-direction: column`, `justify-content: space-between` e `align-items: stretch`; o bloco live atual usa `display: block` e nenhuma das três propriedades. Assim, o delta funcional Quick 037 é exatamente a troca de `display` e a remoção dessas três declarações.
- O diff cumulativo de teste adiciona o contrato compartilhado normal/Mandarin e agora verifica o estado block vencedor e a ausência das três propriedades.
- `git diff --exit-code` confirmou ausência de alterações em `card_template_loader.py`, `mandarin_card.md`, `japanese_card.md`, `latin_mvp_card.md` e no teste de integração verification-only.
- `git diff --cached` ficou vazio: nada foi staged. O worktree continua contendo `LOG.md` e diretórios 035/036 preexistentes; isso é contexto sujo aceito, não evidência de um gap da Quick 037.

## Artifact Verification

| Artifact | Exists | Substantive | Wired | Status |
|---|---:|---:|---:|---|
| `tests/services/test_card_template_loader.py` | ✓ | ✓ | ✓ | VERIFIED — usa o loader real, seleciona o último bloco e cobre normal + Mandarin frequency/word-list. |
| `src/multilang/templates/normal_card.md` | ✓ | ✓ | ✓ | VERIFIED — override final efetivo, sem stub e preservando a geometria aprovada. |
| `german_frequency_template_dummy.apkg` | ✓ | ✓ | ✓ | VERIFIED — 69.850 bytes, 7 notes/cards, CSS live embutido, IDs `1995037001`/`1995037002`; arquivo continua gitignored. |
| `UI-PROOF.md` | ✓ | ✓ | ✓ | VERIFIED — bundle válido, somente slot automático, `passed`/`satisfied`, sem warnings ou issues. |
| `NATIVE-ANKI-RECHECK.md` | ✓ | ✓ | ✓ | VERIFIED AS DEFERRED — bundle válido, somente slot humano, UAT anterior falho e novo aceite honestamente pendente. |

## Key Link Verification

| From | To | Via | Status | Evidência |
|---|---|---|---|---|
| Teste do loader | Template normal | Assertions sobre o último bloco `.customCard` | ✓ WIRED | Teste nominal passou e falharia se um override posterior restaurasse flex/space-between. |
| Template normal | Normal e Mandarin | `load_card_template` concatena CSS normal antes do CSS Mandarin | ✓ WIRED | Probe confirmou prefixo completo; CSS Mandarin não redefine `.customCard`. |
| Template normal | APKG alemão | `build_multilang_model` / modelo preview Q037 | ✓ WIRED | CSS do APKG é exatamente igual ao CSS do modelo German frequency live atual. |
| Slots planejados | Dois proof bundles | `gsdd ui-proof compare` | ✓ WIRED | Automático `satisfied` sem issues; nativo `partial` somente pelos seis códigos esperados de aceite humano deferred. |

## Focused Tests and Behavioral Checks

| Check | Resultado independente | Status |
|---|---|---|
| RED histórico antes da produção | `UI-PROOF.md` registra exit 1 por live `display: flex`; o predecessor Quick 035 confirma essa condição. A ordem histórica não foi recriada porque exigiria reverter código. | ✓ CONSISTENT |
| Teste nominal atual | `1 passed in 3.01s` | ✓ PASS |
| Loader + contrato de export autorizados | `30 passed in 2.49s` | ✓ PASS |
| CSS live normal/Mandarin + APKG ZIP/SQLite | `CSS/APKG OK: live=embedded; 7 notes/cards; size=69850; IDs 1995037001/1995037002` | ✓ PASS |
| `UI-PROOF.md` validate | `valid: true`, sem errors/warnings | ✓ PASS |
| `NATIVE-ANKI-RECHECK.md` validate | `valid: true`, sem errors/warnings | ✓ PASS |
| Comparação determinística dos bundles | Auto `satisfied`/sem issues; nativo `partial` somente por evidência humana deferred | ✓ PASS |
| Input temporário do comparador | Path fixo workspace-relative criado e removido em `finally`; ausência confirmada após a execução | ✓ PASS |
| Diff whitespace/scope | `git diff --check` e checks dos arquivos verification-only sem saída | ✓ PASS |

Os seis códigos do slot nativo foram exatamente: `unsatisfied_observed_claim_status`, `unsatisfied_observed_comparison_status`, `missing_supporting_observation_evidence_kind`, `unsatisfied_proof_step`, `missing_manual_acceptance_observation` e `unsatisfied_observation_result`. Não houve erro de parsing, metadata, texto de observação, artifact type, rota ou claim limit.

O risco de path foi corrigido de forma aceitável: o comparador recebeu um path estático dentro do workspace, sem entrada de usuário, e o arquivo efêmero foi removido em `finally`. Nenhum arquivo temporário permaneceu.

## Requirements Coverage

Não há IDs de requisito para esta quick task (`requirements: []`). Os seis must-haves do plano são a cobertura normativa e todos foram verificados.

## Anti-Patterns

- Nenhum `TODO`, `FIXME`, `HACK`, `XXX`, placeholder ou stub bloqueante nos arquivos alterados.
- Nenhum novo acesso a rede/provider, endpoint, schema ou fluxo de dados de usuário.
- Ocorrências de flex/`space-between` em linhas internas (`targetWordContainer`/`exampleSentenceLine`) não controlam a distribuição vertical dos filhos diretos do painel e não contradizem a correção.

## Human Verification Required

### 1. Frente curta no Anki

**Test:** importar `german_frequency_template_dummy.apkg` e abrir um card curto.

**Expected:** painel alto/centralizado, com fields compactos e sem os grandes vazios artificiais rejeitados no APKG anterior.

**Why human:** aparência e espaçamento no WebView nativo exigem julgamento visual.

### 2. Verso e campos auxiliares

**Test:** revelar o verso.

**Expected:** Translation aparece; definição, imagem vazia e controles de áudio continuam visualmente corretos.

**Why human:** integração visual do renderer nativo não é provada por CSS/SQLite.

### 3. Card longo

**Test:** abrir o card de conteúdo longo.

**Expected:** conteúdo legível, crescimento ou rolagem natural e nenhum clipping.

**Why human:** overflow real depende do renderer e do viewport usados pelo usuário.

## Gaps Summary

Nenhum gap automatizado encontrado. O único gate restante é a aceitação visual nativa explicitamente prevista pelo plano; ela deve permanecer `human_needed` até o usuário inspecionar o APKG Q037.

---

_Verified: 2026-08-02T20:24:38Z_
_Verifier: the agent (gsd-verifier, quick mode)_
