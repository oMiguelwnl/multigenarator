---
mode: quick
phase: quick-037-preview-card-anki-corrigido
task: 037-preview-card-anki-corrigido
plan: 037
verified: 2026-07-28T18:40:24Z
runtime: opencode
assurance: self_checked
reduced_assurance: true
reduced_assurance_reason: ".planning/templates/roles/ está vazio; a verificação quick foi executada diretamente e no mesmo runtime do plano e da execução."
status: passed
score: "8/8 must-haves source-only verificados"
delivery_posture: repo_only
evidence_contract:
  required_kinds: [code, test]
  observed_kinds: [code, test]
  missing_kinds: []
overrides_applied: 0
gaps: []
human_verification: []
claim_scope: source_only
ui_proof:
  slot_id: normal-card-anki-corrected-source-proof
  result: pass
  observations: 14
  artifacts: 3
production_integrity:
  path: src/multilang/templates/normal_card.md
  algorithm: sha256
  recorded_before: e1b50774e804302e8dc2a1ff4d8b59eb9a537a05a9e891d1a388b2e589d99b97
  recorded_after: e1b50774e804302e8dc2a1ff4d8b59eb9a537a05a9e891d1a388b2e589d99b97
  recorded_live_final: e1b50774e804302e8dc2a1ff4d8b59eb9a537a05a9e891d1a388b2e589d99b97
  verifier_live: e1b50774e804302e8dc2a1ff4d8b59eb9a537a05a9e891d1a388b2e589d99b97
git_delivery_check:
  branch: Monarch
  head: 0664390fec7aa1d210438b3f7baa599f84cbbe01
  commits_ahead_of_main: unknown
  commits_ahead_note: "A referência local main não existe."
  pr_state: not_checked
  staged_changes: false
  worktree_clean: false
---

# Quick Task 037: Preview do card Anki corrigido — Verification Report

**Goal:** entregar preview standalone mostrando card normal corrigido com largura fluida, altura natural e background de viewport abaixo.

**Status:** `passed`

## Escopo e base da verificação

- Verificação inicial: não havia `037-VERIFICATION.md` anterior.
- Autoridade de escopo: goal fornecido, `037-PLAN.md` e seus oito must-haves; `037-SUMMARY.md` foi tratado apenas como claim a conferir.
- Quick mode: `requirements: []`; alinhamento com ROADMAP e integração entre fases não se aplicam.
- Postura de evidência: `repo_only`, estritamente source-only. Os tipos exigidos pelo slot (`code`, `test`) foram encontrados.
- O diretório `.planning/templates/roles/` está vazio. Plano, execução e verificação usam `opencode`; portanto a assurance permanece `self_checked`, não cross-runtime.

## Goal Achievement

| # | Must-have | Status | Evidência independente |
|---|---|---|---|
| 1 | Um HTML standalone permite comparar exatamente uma frente e um verso em duas janelas/cards. | ✓ VERIFIED | `normal_card_anki_corrected_preview.html:1-7,275-353` contém documento HTML5 completo, exatamente duas `.anki-window` em ordem `front/back`, duas `.anki-viewport` e dois `article.customCard` em ordem `front/back`. O parser independente confirmou todas as contagens. |
| 2 | O contrato responsivo declara duas colunas no desktop e uma em largura estreita, sem largura mínima rígida do card. | ✓ VERIFIED | `.preview-grid` usa `repeat(2, minmax(0, 1fr))`, `width: 100%` e `min-width: 0` (`:52-59`); em `max-width: 980px` passa a `1fr` (`:254-258`). Em `420px`, os paddings passam a 8px e `22px 18px` (`:260-268`). Esta é uma verificação do CSS declarado, não de viewport renderizada. |
| 3 | A viewport alta mantém o background da página separado do card de altura natural. | ✓ VERIFIED | `.anki-viewport` declara `display: block`, `min-height: 620px`, `padding: 12px` e `background: var(--color-page-background)` (`:99-104`), e cada uma contém diretamente um card (`:280-312`, `:320-352`). O card não é esticado à altura da viewport. A área visual resultante não foi medida. |
| 4 | `.customCard` é fluido e usa `width: 100%`, `max-width: none`, `min-height: 0` e `border-box`, sem altura de viewport. | ✓ VERIFIED | Regra base em `:106-124` declara os quatro valores exigidos. A única regra mobile do card altera apenas padding (`:265-267`). O validador exato do plano e um validador independente rejeitaram `height`, `100vh`/`100dvh`, `calc(...vh)` ou outro `min-height` no card; `body { min-height: 100vh; }` permanece corretamente fora do card (`:27-36`). |
| 5 | Frente e verso têm conteúdo alemão espelhado; somente a tradução muda de estado. | ✓ VERIFIED | Os dois corpos trazem `Buch`, `/buːx/`, `noun: book`, `Das Buch liegt auf dem Tisch.`, a tradução portuguesa e quatro `▶` ao todo (`:281-311`, `:321-351`). Após normalizar somente `is-hidden/is-visible`, `hidden/visible` e `aria-hidden=true/false`, os corpos são textualmente idênticos. `.is-hidden/.is-visible` mapeiam para `display: none/block` (`:246-252`). |
| 6 | O preview espelha no source os tokens e a hierarquia Gemini efetivos da produção. | ✓ VERIFIED | O preview declara a paleta em `:8-15`, tipografia e métricas em `:106-243`. A fonte live confirma os mesmos tokens em `src/multilang/templates/normal_card.md:70-100` e as declarações canônicas finais de largura, padding, borda, raio, sombra e hierarquia em `:456-500,516-645,688-699`. O validador exato do plano passou. Nenhuma equivalência de pixels ou fonte instalada é alegada. |
| 7 | O preview permanece inerte, offline e sem dependências/assets externos. | ✓ VERIFIED | Há um único `<style>` inline e nenhum `script`, `link`, `img`, `audio`, `video`, `iframe`, `object` ou `embed`; o scan também encontrou zero `src`, `href`, `@import`, `url(...)`, HTTP(S), event handlers ou templates Anki. O conteúdo é fixo, sem entrada não confiável ou superfície ativa de XSS. |
| 8 | A quick preservou a fonte de produção no limite demonstrável pela prova source-only e não alterou staging. | ✓ VERIFIED | O plano registra que `normal_card.md` já estava modificado antes da execução (`037-PLAN.md:83-85`). O proof registra hashes before/after/live iguais; o verificador recalculou o live e obteve o mesmo SHA-256. `git status --short` ainda mostra o arquivo como modificado e `git diff` mostra 17 adições/4 remoções contra HEAD, enquanto `git diff --cached --exit-code` passou sem delta staged. Isso prova ausência de drift em relação ao baseline registrado pela quick, não autoria histórica nem worktree limpo. |

**Score:** 8/8 must-haves source-only verificados.

## Artifact Verification

| Artifact | Existe | Substantivo | Wired | Resultado |
|---|---:|---:|---:|---|
| `normal_card_anki_corrected_preview.html` | Sim, 357 linhas | Sim — HTML/CSS e dois estados completos, sem placeholder | Sim — CSS inline, duas viewports e seus cards formam o artefato standalone | ✓ VERIFIED |
| `.planning/quick/037-preview-card-anki-corrigido/UI-PROOF.md` | Sim, 341 linhas | Sim — JSON válido, 14 observações e 3 artefatos | Sim — slot, paths, comandos, resultados e hash apontam para o preview e a fonte live | ✓ VERIFIED |

Não há data-flow dinâmico: o preview é deliberadamente estático e offline. Level 4 é, portanto, não aplicável.

## Key Links

| From | To | Via | Status | Evidência |
|---|---|---|---|---|
| `.anki-viewport` | `.customCard` | Contenção em cada janela e backgrounds distintos | ✓ WIRED | Duas relações estruturais em `:280-312` e `:320-352`; viewport `#121212`, card `#1E1E1E`. |
| `article[data-card-state=front]` | `article[data-card-state=back]` | Corpo espelhado com delta somente na visibilidade da tradução | ✓ WIRED | Comparação normalizada dos corpos passou. |
| Preview | `UI-PROOF.md` | Slot, artifact paths, validadores e source integrity | ✓ WIRED | Slot `normal-card-anki-corrected-source-proof`, `result: pass`, 14 observações completas e hash live correspondente. |

## UI Proof

| Check | Resultado |
|---|---|
| Um único fenced JSON válido | ✓ PASS |
| Campos de topo exigidos | ✓ PASS — inclui `proof_bundle_version`, escopo, route state, ambiente, viewport, inputs, passos, observações, artefatos, privacidade, resultado, limites e integridade |
| Slot planejado × observado | ✓ PASS — ID e claim source-only correspondem |
| Evidência mínima | ✓ PASS — 14 observações (mínimo 10), todas com campos exigidos e `result: pass` |
| Metadados de artefato | ✓ PASS — 3 artefatos com visibility, retention, sensitivity e safe_to_publish |
| Hash live | ✓ PASS — before = after = recorded live = verifier live |
| Limites de claim | ✓ PASS — excluem Anki nativo, pixels, aparência computada, fontes instaladas e áudio |

## Behavioral Spot-Checks

| Check | Resultado | Status |
|---|---|---|
| Validador source independente (estrutura, mirror, CSS, responsividade, conteúdo e offline) | `independent source validator: PASS` | ✓ PASS |
| Primeiro `<automated>` exato do plano, extraído e executado sem shell expansion | `corrected preview contract OK: 2 windows/cards, content-height fluid cards, separate viewport background, front/back translation, responsive and offline` | ✓ PASS |
| Parser independente do fenced JSON e recomputação SHA-256 | 14 observações, 3 artefatos, todos os checks true; hash live `e1b507...9b97` | ✓ PASS |
| Segundo `<automated>` exato do plano | `UI proof OK: complete, source integrity preserved, claim source-only` | ✓ PASS |
| `git diff --check` | Exit 0; apenas avisos informativos LF/CRLF em arquivos concorrentes | ✓ PASS |
| `git diff --cached --exit-code` | Exit 0, sem delta staged | ✓ PASS |

## Git / Production Claim Boundary

O worktree **não está limpo**: há alterações tracked e untracked concorrentes, inclusive `src/multilang/templates/normal_card.md` modificado contra HEAD e os artefatos da quick ainda untracked. Logo, este relatório não afirma limpeza global, não atribui mudanças concorrentes à quick e não afirma que produção coincide com HEAD.

A conclusão permitida é mais estreita: o SHA-256 live observado pelo verificador coincide com os três hashes registrados no proof, e o baseline documental anterior à execução já classificava `normal_card.md` como modificado. Assim, a evidência disponível sustenta que a quick 037 não introduziu mudança byte a byte nessa fonte entre seus captures registrados e esta verificação. O estado histórico anterior aos captures não é demonstrável apenas pelo worktree atual.

## Requirements Coverage

Não aplicável: quick 037 declara `requirements: []` e não reivindica requisito de ROADMAP.

## Anti-Patterns

Nenhum blocker encontrado: sem TODO/FIXME/placeholder, handler vazio, script, dependência externa ou mock conectado ao resultado. Os dados fixos alemães são conteúdo representativo exigido, não stub.

## Human Verification

Nenhuma é necessária para encerrar a claim source-only aprovada. Browser, pixels, aparência visual, fontes instaladas, áudio e Anki nativo permanecem explicitamente **fora do escopo**, não como evidência pendente.

## Conclusion

Os dois artefatos exigidos existem, são substantivos e estão conectados; os validadores independentes e os validadores exatos do plano passaram; o UI proof está completo; e a integridade live da fonte protegida coincide com o baseline registrado. Dentro dos limites source-only definidos pelo goal, a quick task 037 atingiu o objetivo.

---

_Verified: 2026-07-28T18:40:24Z_
_Verifier: gsd-verifier (quick fallback, same-runtime)_
