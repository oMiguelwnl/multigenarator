---
phase: quick-032-adaptar-template-normal-gemini
runtime: opencode
assurance: self_checked
verified: 2026-07-27T19:34:50Z
status: human_needed
score: 4/4 must-haves verified
overrides_applied: 0
re_verification: false
delivery_posture: repo_only
evidence_contract:
  required_kinds: [code, test]
  recommended_kinds: [human]
  observed_kinds: [code, test]
  missing_kinds: []
ui_proof_slots:
  - slot_id: normal-gemini-source-contract
    status: satisfied
  - slot_id: normal-gemini-native-anki-acceptance
    status: missing
    missing_evidence: [human]
accepted_risks:
  - id: plan-checker-verification-only-suite
    disposition: non_blocking
    reason: "The pre-existing integration suite was executed only; both staged and unstaged diffs for tests/integration/test_v13_normal_template_export_contract.py are empty."
git_delivery_check:
  branch: Monarch
  commits_ahead_of_main: unknown
  pr_state: unknown
  staged_changes: false
human_verification:
  - test: "Anki Desktop — frente"
    expected: "O card normal exibe o shell escuro Gemini, tipografia/hierarquia legíveis, IPA e áudio corretos, imagem opcional contida e Translation oculta."
    why_human: "pytest e inspeção de CSS não reproduzem fontes, controles de replay nem o WebView nativo do Anki Desktop."
  - test: "Anki Desktop — verso"
    expected: "O mesmo layout da frente permanece via FrontSide; Translation é revelada na seção de exemplo e áudio/imagem continuam aceitáveis."
    why_human: "O script e a estrutura foram verificados, mas não executados no WebView nativo."
  - test: "Cliente Anki mobile em portrait — frente"
    expected: "O layout envolve e contém palavra, IPA, áudio e imagem sem overflow; Translation permanece oculta."
    why_human: "Não há observação de viewport ou WebView mobile nativo."
  - test: "Cliente Anki mobile em portrait — verso"
    expected: "O mesmo layout é preservado, Translation aparece de forma legível e imagem/áudio mantêm renderização aceitável."
    why_human: "A aparência e a interação no cliente mobile não podem ser provadas por inspeção estática."
---

# Quick Task 032: Verificação do template normal Gemini

**Objetivo:** adaptar somente o card normal ao modelo visual de `gemini-code-1785178063558.html`, com o mesmo layout nos dois lados, tradução oculta na frente e revelada no verso, preservando campos, condicionais, áudio e imagem opcional.

**Status:** `human_needed`
**Modo:** verificação inicial, goal-backward e independente do resumo.

## Base da verificação

- Não havia `032-VERIFICATION.md`; esta é a primeira verificação.
- Os must-haves foram extraídos de `032-PLAN.md` e conferidos contra o template, loader, exportador, testes e referência visual atuais.
- O plano não declara IDs de requisitos de roadmap; quick mode foi verificado sem ampliar escopo para o milestone.
- O plano tem `reduced_assurance: true` pela ausência do role contract. A verificação aplicou diretamente o contrato quick solicitado. Como execução e verificação usam o mesmo runtime, a assurance permanece `self_checked`.
- O worktree contém alterações preexistentes de outras quick tasks. Nenhuma delas foi revertida, staged ou incluída como prova automática desta tarefa.

## Goal Achievement

### Observable Truths

| # | Verdade observável | Status | Evidência independente |
|---|---|---|---|
| 1 | O card normal usa o layout escuro ergonômico da referência Gemini nos dois lados. | ✓ VERIFIED no limite code/test | A referência define paleta e métricas em `gemini-code-1785178063558.html:9-128`. O bloco canônico final de `normal_card.md:456-685` implementa essas métricas. Uma inspeção independente validou 29 declarações efetivas, e o verso reutiliza `{{FrontSide}}` (`normal_card.md:58`). Aparência nativa ainda está no gate humano. |
| 2 | Translation fica oculta na frente e é revelada no verso sem substituir o layout. | ✓ VERIFIED | A frente contém `id="translation"` e `style="display:none;"` (`normal_card.md:44-46`); o verso contém apenas `{{FrontSide}}` e o reveal fixo (`normal_card.md:58-62`). O parser encontrou exatamente um script, sem placeholders de campos. |
| 3 | Campos, ordem, condicionais IPA/Image, áudios, labels e imagem opcional permanecem intactos. | ✓ VERIFIED | Inspeção gerada retornou exatamente `word`, três referências condicionais de IPA, `word_audio`, `Definitions`, três de Image, `Example Sentence`, `sentence_audio`, `Translation`, `FrontSide`. A integração APKG/CSV/TSV preserva os nove campos, incluindo `SortIndex` não renderizado; 29 testes passaram. |
| 4 | Mandarin continua compondo o CSS normal completo antes de seu CSS próprio, sem depender de mudança nova em markup/CSS Mandarin. | ✓ VERIFIED | `card_template_loader.py:63-81` parseia ambos e concatena `base_template.css` antes do CSS Mandarin. A inspeção independente provou igualdade exata `normal.css + "\n\n" + mandarin.css`; frequency e word-list também são cobertos pela suíte verde. |

**Score automatizado:** 4/4 must-haves verificados. O status não é `passed` porque a aceitação visual nativa continua pendente.

## Verificação de artefatos

| Artefato | Existe | Substantivo | Wired | Status / detalhes |
|---|---:|---:|---:|---|
| `src/multilang/templates/normal_card.md` | Sim | Sim | Sim | ✓ O loader parseia Front/Back/CSS e o exportador usa o resultado em `qfmt`, `afmt` e `css`. |
| `tests/services/test_card_template_loader.py` | Sim | Sim | Sim | ✓ Testes selector-aware verificam último valor CSS, estrutura balanceada, contrato exato e composição Mandarin; o arquivo foi coletado pela execução pytest. |
| `.planning/quick/032-adaptar-template-normal-gemini/UI-PROOF.md` | Sim | Sim | Sim | ✓ Fence JSON parseado localmente; 12 campos top-level, 11 observações e 4 artifacts com metadados de privacidade. O resultado permanece `human_needed`. |
| `tests/integration/test_v13_normal_template_export_contract.py` | Sim | Sim | Sim | ✓ Input verification-only: executado e sem diff staged ou unstaged. Não foi contado como artefato produzido. |

## Key Links e fluxo de dados

| De | Para | Via | Status | Evidência |
|---|---|---|---|---|
| `normal_card.md` | `card_template_loader.py` | Parser dos fences Front/Back/CSS | ✓ WIRED | `_TEMPLATE_FILES["normal_card"]` e `_parse_card_template()` carregam o arquivo. |
| `card_template_loader.py` | `export_anki_package.py` | `load_card_template()` em `build_multilang_model()` | ✓ WIRED | O exportador atribui `template.front`, `template.back` e `template.css` ao modelo genanki (`export_anki_package.py:51-93`). |
| Frente normal | Verso normal | `{{FrontSide}}` + reveal fixo | ✓ WIRED | Mesmo DOM é reutilizado; apenas `display` de `#translation` muda. |
| CSS normal | Template Mandarin | Concatenação do loader | ✓ WIRED | Inspeção independente confirmou prefixo e sufixo exatos. |

O fluxo é estático: placeholders de campos → template parseado → `genanki.Model` → APKG. A suíte de integração inspecionou o modelo exportado real; substituição/renderização no WebView nativo continua no gate humano.

## Behavioral Spot-Checks

| Comportamento | Comando | Resultado | Status |
|---|---|---|---|
| Loader + contrato de exportação | `uv run pytest tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py -q` | `29 passed in 0.57s` | ✓ PASS |
| Higiene do patch solicitado | `git diff --check -- "src/multilang/templates/normal_card.md" "tests/services/test_card_template_loader.py" ".planning/quick/032-adaptar-template-normal-gemini/UI-PROOF.md"` | Exit 0; apenas avisos informativos LF→CRLF nos dois arquivos rastreados | ✓ PASS |
| JSON fenced do UI proof | Parser Python local com `json.loads` | JSON válido; 12 campos top-level, 11 observações, 4 artifacts, `result=human_needed` | ✓ PASS |
| CSS efetivo e composição Mandarin | Parser CSS independente + templates carregados | 29 declarações conferidas; prefixo/sufixo Mandarin exatos | ✓ PASS |
| Referências e active content | Inspeção independente do template gerado | Lista exata de referências; 1 reveal fixo; 0 `innerHTML`; 0 asset externo; 0 script derivado de campo | ✓ PASS |
| Suíte integration verification-only | `git diff --exit-code` e `git diff --cached --exit-code` no arquivo | Ambos limpos | ✓ PASS |

## Segurança, anti-patterns e limites

| Verificação | Resultado | Severidade | Impacto |
|---|---|---|---|
| Novas referências Anki | Nenhuma; a sequência atual coincide exatamente com o contrato esperado. | — | Nenhum drift de schema/template. |
| `innerHTML` | Ausente no template gerado. | — | Nenhum novo sink DOM. |
| Assets externos | Nenhum `src`/`href` remoto, `@import`, `url(http...)`, `link` ou `iframe`. | — | Nenhuma dependência externa nova. |
| Scripts derivados de campos | Ausentes; o único script é o reveal literal de `#translation` e não contém `{{...}}`. | — | Nenhuma nova execução controlada por conteúdo de campo. |
| TODO/FIXME/HACK/placeholders | Nenhum match nos três artefatos da tarefa. | — | Nenhum stub detectado. |
| Campos HTML existentes | Continuam sendo renderizados pelo contrato Anki preexistente. | ℹ Info | Risco preexistente aceito pelo plano; a tarefa visual não adiciona sink nem amplia a trust boundary. |

### Disconfirmation pass

- Os testes provam declarações CSS e contratos exportados, não pixels calculados por Anki.
- O teste verde do reveal verifica o script como texto; não executa o JavaScript em Desktop/mobile.
- Fontes instaladas, replay nativo, imagem opcional e wrapping real continuam sem evidência de WebView. Esses limites impedem um falso `passed`.

## Escopo e risco aceito do plan-checker

- `tests/integration/test_v13_normal_template_export_contract.py` está limpo no índice e no worktree. Portanto, a objeção do plan-checker a uma suíte preexistente é registrada como **risco aceito não impeditivo**: ela foi apenas executada.
- `card_template_loader.py` e `export_anki_package.py` também não têm diff staged/unstaged; o wiring foi inspecionado, não alterado.
- O worktree possui diffs preexistentes em Mandarin/phoneme. Seus mtimes são `2026-07-23`, enquanto `normal_card.md`, o teste e o UI proof foram gravados em `2026-07-27`; quick-030 também já documentava esses arquivos como seu escopo. Eles não são tratados como produção nova da quick 032.
- Nada está staged. O repositório não possui ref local `main`, e `gh` está indisponível; por isso commits-ahead e PR permanecem `unknown`. Isso é aviso de delivery, não gap de implementação.

## Requirements Coverage

Quick task 032 declara `requirements: []`. Não há requisito de roadmap a satisfazer ou requisito órfão nesta verificação. Os quatro must-haves do plano cobrem integralmente o pedido da quick task.

## Human Verification Required

### 1. Anki Desktop — frente

**Teste:** abrir um card normal representativo com IPA, dois áudios, definições, exemplo, tradução e imagem opcional.
**Esperado:** visual Gemini escuro e legível; Translation oculta; áudio e imagem contidos.
**Por que humano:** o WebView, fontes e controles nativos não são reproduzidos por pytest.

### 2. Anki Desktop — verso

**Teste:** revelar o mesmo card.
**Esperado:** layout idêntico preservado e Translation revelada na seção de exemplo, sem regressão de áudio/imagem.
**Por que humano:** o reveal não foi executado em Anki Desktop.

### 3. Mobile portrait — frente

**Teste:** abrir o card em cliente Anki mobile em orientação portrait.
**Esperado:** wrapping e contenção corretos; Translation oculta; controles e imagem utilizáveis.
**Por que humano:** não há viewport/WebView mobile observado.

### 4. Mobile portrait — verso

**Teste:** revelar o card no mesmo cliente.
**Esperado:** mesmo layout, Translation legível e mídia aceitável.
**Por que humano:** aparência e interação mobile exigem observação nativa.

## Conclusão

Não foram encontrados gaps automatizados: implementação, contratos, wiring, exportação, composição Mandarin, segurança delimitada e UI-proof JSON passaram. A meta ainda não pode receber `passed` porque a aparência em Anki Desktop/mobile é explicitamente humana e permanece sem observação. O Escalation Gate fica aberto com status **`human_needed`**.

---

_Verified: 2026-07-27T19:34:50Z_
_Verifier: the agent (gsd-verifier)_
