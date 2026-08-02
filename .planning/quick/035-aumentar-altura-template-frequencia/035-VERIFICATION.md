---
quick_task: 035-aumentar-altura-template-frequencia
runtime: opencode
assurance: self_checked
verified: 2026-08-02T19:22:07Z
status: human_needed
score: 5/5 implementation must-haves verified
overrides_applied: 0
delivery_posture: repo_only
evidence_contract:
  required_kinds: [code]
  recommended_kinds: [test, human]
  observed_kinds: [code, test]
  missing_kinds: []
re_verification:
  previous_status: gaps_found
  previous_score: 5/5
  gaps_closed:
    - "O slot automatizado agora possui bundle individual e retorna satisfied sem issues no helper local após compatibilização dos bugs de schema/case-fold."
  gaps_remaining: []
  regressions: []
ui_proof_comparison:
  automated_slot:
    slot_id: frequency-panel-responsive-css-contract
    bundle_validation: passed
    helper_status: satisfied
    issues: []
    observations: 7
    evidence_kinds: [code, test]
  native_slot:
    slot_id: frequency-panel-native-anki-acceptance
    bundle_validation: passed
    bundle_status: deferred
    acceptance: human_needed
    manual_steps_deferred: 8
  tooling_schema_mismatches:
    - "O plano confirmado usa minimum_observations numérico 7/8; o helper atual exige lista. Os números foram compatibilizados somente em memória para a comparação e as quantidades reais foram verificadas."
    - "O helper faz case-fold somente dos artifact types observados. Os valores literais plano/bundle são iguais; os esperados foram case-folded somente em memória para exercer a comparação sem falso positivo."
native_acceptance_status: human_needed
human_verification:
  - test: "Anki Desktop: normal frequency e Mandarin, frente/verso, com conteúdo curto e longo, aproximadamente 1280x800."
    expected: "Painel alto, centralizado e bem distribuído; conteúdo longo cresce sem clipping; Translation reveal e mídia permanecem funcionais."
    why_human: "Nenhum WebView nativo do Anki Desktop foi observado."
  - test: "Cliente Anki mobile nativo: normal frequency e Mandarin, frente/verso, conteúdo curto/longo, aproximadamente 390x667 e uma tela baixa disponível."
    expected: "A min-height não cria rolagem sozinha; conteúdo longo usa rolagem natural sem corte."
    why_human: "CSS estático e pytest não provam layout, clipping nem scrolling no WebView mobile nativo."
git_delivery_check:
  branch: Monarch
  head: 9e6d05280306d55ecc8f668a2ee5e25278cc8459
  commits_ahead_of_main: unknown
  pr_state: unknown
  index_clean: true
  warnings:
    - "A referência main não existe localmente, portanto a contagem main..HEAD não pôde ser calculada."
    - "gh não está instalado, portanto o estado de PR não pôde ser consultado."
---

# Quick Task 035 Re-verification Report

**Objetivo:** melhorar somente o template dos decks de frequência normal, com herança Mandarin, para um painel alto, responsivo, centralizado e melhor distribuído verticalmente, sem altura rígida nem rolagem imposta em telas pequenas, preservando japonês, latim e contratos de export.

**Status final:** `human_needed`. A implementação e a prova automatizada estão completas; o único item restante é a aceitação visual/scrolling nos WebViews nativos do Anki Desktop/mobile.

## Verification Basis

- Re-verificação após o relatório anterior `gaps_found`.
- Foram relidos plano, resumo, `UI-PROOF.md`, o novo `NATIVE-ANKI-ACCEPTANCE.md`, código, testes e o relatório anterior.
- O gap anterior foi verificado por completo; itens anteriormente aprovados receberam checks rápidos de regressão.
- Resumo foi tratado como alegação, não como prova. Os dois bundles, o comparador local, o diff e os testes foram inspecionados/reexecutados independentemente.
- Runtime de execução e verificação: `opencode`; assurance permanece `self_checked`.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidência |
|---|---|---|---|
| 1 | O painel normal tem contrato CSS alto, responsivo, centralizado e sem altura fixa rígida. | ✓ VERIFIED | `.card` efetiva continua flex/center/100vh e `.customCard` continua flex-column com `min-height: min(760px, calc(100vh - 80px))`; probe confirmou ausência de `height` e `max-height` rígidas. |
| 2 | O contrato calcula 720px em 1280x800 e 587px em 390x667. | ✓ VERIFIED | Probe independente e teste focado confirmaram 720 e 587, com desconto dos 80px de padding externo e teto de 760px. |
| 3 | Espaço excedente é distribuído e conteúdo longo pode crescer naturalmente. | ✓ VERIFIED (CSS semantics) | `flex-direction: column`, `justify-content: space-between`, `align-items: stretch` e somente min-height; nenhum novo overflow vertical forçado. |
| 4 | Mandarin frequency e word-list herdam o CSS normal atualizado. | ✓ VERIFIED | Loader concatena `base_template.css`; probe confirmou rotas iguais e CSS Mandarin iniciado pelo CSS normal completo. |
| 5 | Japonês, latim, campos, markup e export permanecem preservados. | ✓ VERIFIED | Arquivos verification-only seguem sem diff e a suíte focada inteira passou. |

**Score:** 5/5 must-haves de implementação verificados.

O score cobre o contrato code/test permitido pelo plano. Ele não promove aparência nativa a passe.

## Artifact Verification

| Artifact | Exists | Substantive | Wired | Status |
|---|---:|---:|---:|---|
| `tests/services/test_card_template_loader.py` | ✓ | ✓ | ✓ | VERIFIED — exerce loader real, CSS vencedor, aritmética e Mandarin. |
| `src/multilang/templates/normal_card.md` | ✓ | ✓ | ✓ | VERIFIED — override final efetivo no fluxo frequency. |
| `UI-PROOF.md` | ✓ | ✓ | ✓ | VERIFIED — bundle exclusivo do slot automatizado, válido e `satisfied`. |
| `NATIVE-ANKI-ACCEPTANCE.md` | ✓ | ✓ | ✓ | DEFERRED/HUMAN_NEEDED — sidecar válido com oito passos humanos pendentes; não é gap automatizável. |
| `src/multilang/services/card_template_loader.py` | ✓ | ✓ | ✓ | VERIFIED — seleção normal e composição Mandarin preservadas. |
| Templates Mandarin/japonês/latim | ✓ | ✓ | ✓ | VERIFIED — sem diff e cobertos por regressão. |

## Key Links

| Link | Status | Evidência |
|---|---|---|
| `.card` → `.customCard` | ✓ WIRED | 100vh + padding 40px/40px alimentam `calc(100vh - 80px)`; box sizing permanece border-box. |
| Normal template → frequency loader | ✓ WIRED | Seleção por `_TEMPLATE_FILES`/source profile no loader real. |
| Normal CSS → Mandarin frequency/word-list | ✓ WIRED | Concatenação em `card_template_loader.py:57-80`; igualdade/prefixo confirmados. |
| Template → APKG export | ✓ WIRED | Contrato de export gerou/leu APKG e preservou fields/markup. |

## UI Proof Re-verification

### Bundle validation

```text
UI-PROOF.md                 valid: true, errors: [], warnings: []
NATIVE-ANKI-ACCEPTANCE.md  valid: true, errors: [], warnings: []
```

### Automated slot

Os slots foram novamente extraídos do frontmatter do plano e passados individualmente ao módulo local `compareUiProofSlots`. Para neutralizar apenas incompatibilidades comprovadas do helper, a cópia em memória representou o mínimo numérico pelas sete observações existentes e aplicou case-fold aos tipos planejados.

Resultado:

```text
slot_id: frequency-panel-responsive-css-contract
status: satisfied
issues: []
errors: []
```

Confirmações independentes, sem depender do resultado declarado no bundle:

- claim literal: igual ao plano;
- route_state literal: igual ao plano;
- environment literal: igual ao plano;
- viewport literal: igual ao plano;
- claim limit literal: presente;
- quatro artifact types: iguais, na mesma ordem, aos planejados;
- sete observações: todas `passed`, cobrindo `code` e `test`;
- comando automatizado: `passed`;
- nenhum issue de claim, route, environment, viewport, artifact ou command.

### Native slot

O sidecar nativo também tem claim, route, environment, viewport, claim limit e artifact type literais. Ele contém oito passos, todos `deferred`, e declara:

```text
claim_status: deferred
comparison_status_by_slot: deferred
native_acceptance_status: human_needed
```

O helper expressa esse estado como `partial` porque exige evidência humana passada para produzir `satisfied`; os únicos issues remanescentes são exatamente claim/observação/passos humanos deferred. Não há mismatch de metadados nem evidência code/test ausente. Conforme o plano e a instrução de re-verificação, isto é `human_needed`, não gap automatizável, e não se exige tornar o slot humano `satisfied` agora.

### Tooling/schema mismatch

`minimum_observations: 7/8` é numérico no plano confirmado, enquanto a versão local de `validateUiProofSlots` espera listas. O conteúdo real cumpre a intenção: sete observações automatizadas passadas e oito passos nativos deferred. A incompatibilidade fica documentada como tooling/schema mismatch, sem downgrade de produto.

O helper também lowercases tipos observados, mas não os planejados. A igualdade literal plano/bundle foi confirmada antes do case-fold somente em memória. Nenhum artifact está faltando.

## Behavioral and Regression Checks

| Check | Resultado |
|---|---|
| `uv run pytest tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py -q` | ✓ `30 passed in 2.28s` |
| Probe CSS/aritmética | ✓ min-height exata; sem height/max-height; 720/587 |
| Probe Mandarin | ✓ frequency = word-list; CSS normal é prefixo completo |
| Cinco arquivos verification-only | ✓ diff zero |
| ROADMAP/SPEC/STATE/LOG | ✓ diff zero |
| Índice Git | ✓ vazio |
| `git diff --check` dos arquivos rastreados | ✓ sem erros |

O diff de produto permanece limitado ao override CSS aprovado. Nenhum script, field reference, `innerHTML`, URL/asset, input ou boundary novo foi introduzido; a análise de segurança anterior não regrediu.

## TDD Evidence Regression Check

- O diff ainda mostra primeiro as expectativas novas e o teste focado contra o estado HEAD anterior (`display: block`, `min-height: 0`, padding antigo).
- A evidência RED persistida continua consistente com esse estado anterior.
- O GREEN atual foi reexecutado: 30 testes passaram.
- Não há commit transacional por proibição do plano; a força da alegação TDD continua limitada à evidência persistida + diff recuperável + GREEN atual.

## Requirements Coverage

Quick 035 não declara IDs formais. Todos os contratos derivados da descrição/decisões D-01–D-04 estão cobertos:

| Contrato | Status |
|---|---|
| Normal + Mandarin herdado | ✓ SATISFIED |
| Painel alto/responsivo/centralizado | ✓ SATISFIED no contrato CSS |
| Distribuição vertical e crescimento natural | ✓ SATISFIED no contrato CSS |
| Aritmética 800/667 sem mínimo excedente | ✓ SATISFIED no contrato CSS; scrolling nativo requer humano |
| Preservação japonês/latim/fields/markup/export | ✓ SATISFIED |

## Human Verification Required

### 1. Anki Desktop — normal e Mandarin

**Test:** Importar decks representativos; observar frente/verso em aproximadamente 1280x800, com conteúdo curto e longo.

**Expected:** Painel alto, centralizado e bem espaçado; conteúdo longo cresce sem clipping; reveal, áudio e imagem mantêm o contrato.

**Why human:** Nenhum WebView nativo do Anki Desktop foi executado.

### 2. Anki mobile — normal e Mandarin

**Test:** Observar frente/verso em aproximadamente 390x667 e uma tela baixa disponível, com conteúdo curto e longo.

**Expected:** O mínimo de 587px não causa rolagem sozinho; conteúdo longo usa rolagem natural e não é cortado.

**Why human:** CSS/testes estáticos não comprovam scrolling, clipping ou viewport handling do cliente nativo.

## Re-verification Conclusion

O gap automatizável anterior foi fechado. Não há gaps de implementação, regressão, wiring ou prova code/test. A quick 035 permanece aberta somente para aceitação humana nativa, portanto o status correto é `human_needed`.

---

_Re-verified: 2026-08-02T19:22:07Z_
_Verifier: gsd-verifier (opencode)_
