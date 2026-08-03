---
mode: quick
phase: quick-039-preview-melhorado-anki
task: 039-preview-melhorado-anki
plan: 039
subsystem: ui
tags: [anki, genanki, html, css, sqlite, offline, ui-proof]
runtime: opencode
assurance: self_checked
status: complete_with_human_needed
requires:
  - phase: quick-037-preview-card-anki-corrigido
    provides: Preview front/back anterior e limites honestos de evidência source-only
provides:
  - Preview standalone dark, responsivo, com shell full-width e conteúdo interno de 900px
  - APKG experimental isolado com três cards alemães e zero mídia
  - TSV LF correspondente às notes do APKG
  - UI proof com 8 observações source pass, 8 APKG pass e 4 native human_needed
affects: [normal-card-visual-review, anki-template-experiment]
tech-stack:
  added: []
  patterns: [CSS compartilhado extraído por marcadores, APKG inspecionado por ZipFile.read e SQLite temporário, GUID explícito por identidade experimental]
key-files:
  created:
    - normal_card_improved_preview.html
    - exports/anki_previews/normal-card-improved-test.apkg
    - exports/anki_previews/normal-card-improved-test.tsv
    - .planning/quick/039-preview-melhorado-anki/UI-PROOF.md
    - .planning/quick/039-preview-melhorado-anki/039-SUMMARY.md
  modified: []
key-decisions:
  - "Manter model 1762801039 e deck 1762801040 isolados de Multilang::Card e dos decks de produção."
  - "Tratar source/ZIP/SQLite/TSV como pass automatizado e manter aparência no Anki como human_needed."
  - "Aplicar o rebaseline explicitamente autorizado sem alterar, reverter ou absorver drift concorrente fora do write set."
patterns-established:
  - "Preview/APKG parity: model.css é extraído literalmente do bloco CSS marcado no preview."
  - "Offline fail-closed: uv usa offline/no-sync/frozen/no-env-file e o inspector usa ZipFile.read, nunca extractall."
requirements-completed: []
duration: 20h44m elapsed (approximately 37m active; checkpoint wait included)
completed: 2026-07-29
---

# Quick Task 039 Summary: Preview melhorado e APKG experimental

**Card normal experimental com shell full-width, wrapper de 900px, tipografia fluida e APKG offline isolado de três notes, validado por ZIP/SQLite/TSV sem tocar em produção.**

## Performance

- **Started:** 2026-07-28T20:27:48Z
- **Completed:** 2026-07-29T17:11:30Z
- **Elapsed:** 20h44m, incluindo espera no checkpoint de integridade
- **Active execution:** aproximadamente 37 minutos
- **Tasks:** 2/2
- **Files created:** 5, incluindo este SUMMARY
- **Git actions:** nenhuma; sem stage, commit ou push

## Accomplishments

- Criado preview HTML5 inerte com exatamente frente/verso, shell de largura total/altura natural, conteúdo central de 900px, `clamp()`, painel hierárquico, botões circulares de 34px e breakpoint 420px.
- Gerado `normal-card-improved-test.apkg` com note type `Multilang::Card Improved Preview`, deck `Multilang Improved Card Test`, três GUIDs explícitos, um único `Card 1` e zero mídia.
- Gerado TSV UTF-8 sem BOM, somente LF, com os nove fields e as mesmas três rows armazenadas no APKG.
- Registrado `UI-PROOF.md` com 20 observações: 8 source `pass`, 8 APKG `pass` e 4 aparência nativa `human_needed`.
- Preservado o baseline original e criado rebaseline autorizado que prova estabilidade global a partir do novo ponto, filtrando somente os cinco outputs permitidos.

## Task Results

| Task | Resultado | Git |
|---|---|---|
| 039-01 — Criar preview e gerar APKG/TSV | Complete; validadores source e delivery passaram | Nenhum commit/stage, por instrução do usuário |
| 039-02 — Inspecionar ZIP/SQLite/TSV e registrar UI proof | Complete; estrutura e proof passaram; aparência nativa permanece human_needed | Nenhum commit/stage, por instrução do usuário |

## Files Created

| Path | Resultado |
|---|---|
| `normal_card_improved_preview.html` | 12,836 bytes; SHA-256 `b45e89603c1aba172d0edd730f1b51bf6327efd741db173902893fab31548c4d` |
| `exports/anki_previews/normal-card-improved-test.apkg` | 61,658 bytes; SHA-256 `6aae7f3ac61ef9ac79e0ff45856f1a24be00e95982a6da2c6c75ce2c206d7fbf` |
| `exports/anki_previews/normal-card-improved-test.tsv` | 479 bytes; SHA-256 `a52fc303b03900f44531db3e5a9ace543f91cf34c2cbdc5daa1219432d07bc18` |
| `.planning/quick/039-preview-melhorado-anki/UI-PROOF.md` | Bundle local-only com source/APKG pass e Anki native human_needed |
| `.planning/quick/039-preview-melhorado-anki/039-SUMMARY.md` | Registro desta execução e do rebaseline autorizado |

## APKG Contract

- **Model:** `1762801039` — `Multilang::Card Improved Preview`
- **Deck:** `1762801040` — `Multilang Improved Card Test`
- **Cards:** `Buch`, `Wasser`, `lernen`
- **Fields:** `SortIndex`, `word`, `IPA`, `Definitions`, `Example Sentence`, `Translation`, `word_audio`, `sentence_audio`, `Image`
- **GUIDs SQLite:** `HtYJ}S^5Rf`, `JPd<d]p+7?`, `Ll0a&a<R0n`
- **Media:** `{}`; áudio e imagem vazios por decisão explícita do plano
- **Template:** um único `Card 1`, `qfmt` sem script e `afmt` limitado ao reveal fixo por `getElementById`

## Verification

| Check | Result |
|---|---|
| Baseline global original | PASS — 861 paths, HEAD/stage/status/repository/locks capturados antes dos outputs |
| Scan dinâmico de IDs | PASS — 751 arquivos UTF-8 no preflight; nenhum ID fora de quick039/outputs |
| Preview source validator | PASS — full-width, hierarquia, clamp, áudio/focus e mobile vinculados a seletores |
| Delivery validator | PASS — APKG não vazio; TSV UTF-8/no-BOM/LF-only e rows exatas |
| Rebaseline explícito | PASS — 863 paths; original preservado separadamente; quatro paths concorrentes registrados |
| Preview source slot | PASS — `preview source slot PASS` |
| APKG structure slot | PASS — `APKG structure slot PASS` |
| Inspector completo ZIP/SQLite/TSV | PASS — IDs/GUIDs/nids/ord/template/CSS/TSV/mídia exatos |
| UI-PROOF parser | PASS — mínimos 8/8/4, integridade global rebased e native human_needed |
| Whitespace checks do plano | PASS — `git diff --check` e `diff --no-index --check` sem saída |

Todos os comandos Python usaram `uv run --offline --no-sync --frozen --no-env-file python`. Nenhum `.env`, provider, rede, `extractall`, `innerHTML` ou asset externo foi usado.

## Concurrent Worktree Integrity

O primeiro preproof detectou drift fora do write set e interrompeu fail-closed. Após autorização explícita do usuário:

- O baseline original foi preservado byte a byte em `%LOCALAPPDATA%/Temp/opencode/quick-039-integrity-baseline-original.json`.
- `docs/multilingual-lexical-adaptive-plan-v4.md` mudou entre o baseline original e o primeiro preproof; esta execução não alterou, reverteu nem absorveu o arquivo.
- Também surgiram externamente `.planning/quick/039-fechar-gaps-geracao-v4/039-SUMMARY.md` e `039-VERIFICATION.md`, e `.planning/quick/LOG.md` mudou; todos permaneceram fora de escopo e intocados.
- O rebaseline autorizado manteve HEAD `0664390fec7aa1d210438b3f7baa599f84cbbe01`, staged diff vazio, `uv.lock` SHA-256 `6e73a05c...b5ae5f` e `pyproject.toml` SHA-256 `ad086568...04f68`.
- Do rebaseline em diante, `before == after == live`: 41 entradas de status filtrado e 863 paths fora dos cinco outputs permitidos, com repository digest `9ff49dd653397d6d32022e513c3b4f9b5548819ecbf783eee5840031017ac0be`.

## Decisions Made

- Mantida a variante estritamente experimental; nenhum template, serviço ou teste de produção foi modificado.
- IDs, nomes e GUIDs próprios evitam substituir o note type/deck de produção.
- A aparência no Anki não recebe aprovação automática: somente source e estrutura são `pass`.
- O drift concorrente foi preservado e documentado; o rebaseline autorizado estabelece uma nova âncora sem reescrever a história do baseline original.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Preview mirror bug] Removido `aria-hidden` redundante dos SVGs inertes**
- **Found during:** Task 039-01, primeiro preview source validator.
- **Issue:** A normalização prevista para a Translation também transformava `aria-hidden` dos SVGs no body frontal, quebrando a igualdade front/back.
- **Fix:** Removido somente o atributo redundante dos quatro SVGs; os botões mantêm labels acessíveis e bodies espelhados.
- **Files modified:** `normal_card_improved_preview.html`.
- **Verification:** Preview source validator passou integralmente.

**2. [Rule 3 - Windows SQLite cleanup] Fechada explicitamente a conexão antes do TemporaryDirectory**
- **Found during:** Task 039-02, inspector completo do plano.
- **Issue:** O context manager de `sqlite3.Connection` não fecha o handle; no Windows o cleanup falhou com `WinError 32` apesar das queries terem concluído.
- **Fix:** O mesmo inspector foi reexecutado com `connection.close()` antes do cleanup, sem alterar os artefatos ou usar `extractall`.
- **Files modified:** nenhum.
- **Verification:** `APKG-STRUCTURE PASS`.

**3. [Rule 3 - Shell-safe validator invocation] Neutralizados backticks e backslash do Python `-c`**
- **Found during:** Preflight e parser do UI-PROOF.
- **Issue:** Bash consumiu o literal de backslash e tentou command substitution no fenced JSON.
- **Fix:** Invocações equivalentes usaram `chr(92)` para normalização de path e `chr(96) * 3` para o fence, preservando todas as assertions do plano.
- **Files modified:** nenhum.
- **Verification:** Preflight/rebaseline e UI-PROOF parser passaram.

**4. [Rule 1 - Proof snapshot transcription] Corrigido `filtered_status_b64` de after/live**
- **Found during:** Task 039-02, primeiro UI-PROOF parser shell-safe.
- **Issue:** A transcrição manual de dois valores base64 divergiu do baseline rebased.
- **Fix:** Os valores foram substituídos via `apply_patch` pelos bytes exatos lidos do baseline; nenhuma comparação foi enfraquecida.
- **Files modified:** `.planning/quick/039-preview-melhorado-anki/UI-PROOF.md`.
- **Verification:** Parser provou `integrity.before == integrity.after == integrity.live == baseline.after`.

### Authorized Scope Adjustment

**Rebaseline explícito após drift concorrente externo**
- O plano original exigia igualdade com o snapshot pré-write; isso se tornou impossível quando um writer concorrente alterou paths fora do escopo.
- O usuário autorizou preservar o snapshot original, registrar cada drift conhecido e estabelecer novo baseline sem tocar nos paths externos.
- A garantia resultante é honesta: o baseline original mostra o drift anterior; o baseline rebased prova que somente outputs permitidos mudaram a partir da autorização.

**Total deviations:** 4 auto-fixed e 1 ajuste explicitamente autorizado. Nenhuma ampliou o produto ou alterou produção/testes.

## Known Stubs

None. `word_audio`, `sentence_audio` e `Image` vazios são dados intencionais de D-04 para este deck offline, não stubs; por isso o APKG não demonstra playback ou mídia.

## Human Needed

1. Abrir `exports/anki_previews/` no Explorer.
2. Importar `normal-card-improved-test.apkg` no Anki Desktop.
3. Abrir `Multilang Improved Card Test` e revisar `Buch`, `Wasser` e `lernen` na frente e no verso.
4. Observar o reviewer em largura ampla e reduzida até 420px ou menos.
5. Informar aprovação ou problemas de largura, altura natural, hierarquia, contraste, tipografia e tradução.

A aparência nativa permanece `human_needed`; nenhuma inspeção source/SQLite é apresentada como aprovação visual.

## Git and Scope Preservation

- Nenhum stage, commit, push, reset, restore, clean ou operação Git mutável foi executado.
- `src/`, `tests/`, `normal_card_anki_corrected_preview.html`, `LOG.md`, `ROADMAP.md`, `SPEC.md` e todo trabalho concorrente permaneceram fora do write set.
- O único write set no repositório foi formado pelos quatro artefatos do plano e este SUMMARY.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Validadores source, delivery, ZIP/SQLite/TSV, slots, UI-PROOF e whitespace passaram; aparência no Anki continua human_needed.
</executor_check>
</checks>

<handoff>
plan_runtime: opencode
plan_assurance: self_checked
plan_check_status: passed
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: false
</handoff>

<deltas>
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Drift concorrente mudou docs/multilingual-lexical-adaptive-plan-v4.md e outros três paths fora de escopo; o usuário autorizou rebaseline com snapshot original preservado.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: sqlite3.Connection precisava de close explícito antes do cleanup no Windows.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Backticks e backslash nos comandos Python -c exigiram formas shell-safe semanticamente equivalentes.
</deltas>

<judgment>
<active_constraints>
Somente preview, APKG, TSV, UI-PROOF e SUMMARY podem ser escritos; produção, testes, lifecycle docs e trabalho concorrente permanecem intocados; toda execução é offline e sem .env/providers.
</active_constraints>
<unresolved_uncertainty>
A aparência, legibilidade, responsividade e reveal no renderer nativo do Anki ainda não foram observados e exigem revisão humana.
</unresolved_uncertainty>
<decision_posture>
Manter a variante isolada e experimental; aceitar prova automatizada somente para source e estrutura; não promover o CSS para produção antes da decisão humana.
</decision_posture>
<anti_regression>
Preservar IDs/GUIDs exclusivos, nove fields em ordem, zero mídia, shell full-width de altura natural, wrapper 900px, CSS preview/APKG idêntico e ausência de rede/assets externos.
</anti_regression>
</judgment>

## Self-Check: PASSED

- Os cinco artefatos existem, são não vazios e permanecem dentro do write set autorizado.
- O backup externo preserva exatamente o `before` original; o baseline principal preserva `original_before` e mantém o snapshot rebased `before == after`.
- O UI proof contém exatamente 20 observações e resultado geral `human_needed`, limitado somente à aparência no Anki.
- O APKG continua íntegro e com manifesto de mídia `{}`.
- HEAD permanece `0664390fec7aa1d210438b3f7baa599f84cbbe01` e o staged diff continua vazio.
