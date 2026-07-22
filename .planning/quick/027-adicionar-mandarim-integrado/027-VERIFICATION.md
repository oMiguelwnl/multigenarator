---
phase: quick-027-adicionar-mandarim-integrado
task: "027"
runtime: opencode
assurance: self_checked
verified: 2026-07-22T18:43:42Z
status: human_needed
score: 7/7 must-haves automated/static verified; human render gate pending
overrides_applied: 0
delivery_posture: repo_only
evidence_contract:
  required_kinds: [code]
  recommended_kinds: [test, runtime, human]
  observed_kinds: [code, test, runtime]
  missing_kinds: []
reduced_assurance: true
reduced_assurance_reasons:
  - ".planning/templates/roles/verifier.md não existe."
  - "O SUMMARY não registra runtime/assurance nem blocos estruturados handoff/deltas."
  - "A verificação executou em Python 3.13.7; o baseline recomendado do projeto é Python 3.12."
gaps: []
closed_gaps:
  - truth: "Cada card Mandarim exportável contém pinyin tonal válido e Tradicional para palavra e frase, persistidos no snapshot."
    closed_at: 2026-07-22T18:43:42Z
    evidence:
      - "src/multilang/services/mandarin_orthography.py rejeita fallback Han, kana e letras não latinas na saída de pinyin."
      - "src/multilang/domain/exporting.py rejeita ExportCardRow Mandarim com Pinyin/Sentence Pinyin contendo letras não-pinyin."
      - "tests/services/test_mandarin_orthography.py cobre U+3402 e Han+cyrillic."
      - "tests/services/test_assemble_export_cards.py prova que o snapshot inválido não é persistido."
      - "tests/domain/test_exporting.py prova que rows Mandarim malformadas falham no contrato de domínio."
git_delivery_check:
  branch: "Monarch"
  commits_ahead_of_main: unknown
  pr_state: unknown
  dirty_worktree: true
  notes:
    - "A ref main não existe, então git rev-list main..HEAD falhou."
    - "gh não está instalado, então o estado de PR não pôde ser consultado."
    - "O worktree contém mudanças da task e mudanças Danish/Japanese alheias; nenhuma foi alterada pela verificação."
ui_proof:
  mandarin-anki-static-contract: satisfied
  mandarin-anki-desktop-mobile-render: missing_human_observation
  claim_limit: "Automação prova schema/template/APKG/mídia, não posicionamento, overflow ou legibilidade real em Anki."
---

# Quick Task 027: Adicionar Mandarim Integrado — Verification Report

**Goal:** Adicionar Mandarim Simplificado como idioma completo dos fluxos modernos `frequency` e `word-list`, com identidade canônica `zh`, ortografia derivada/persistida, dois áudios e export APKG/CSV/TSV dedicado sem usar o APKG de referência.

**Verified:** 2026-07-22T18:43:42Z
**Status:** `human_needed`
**Re-verification:** Sim — o gap técnico de pinyin foi fechado; permanece somente a gate humana de renderização Anki Desktop/mobile.

## Re-verification Update

- O blocker anterior de pinyin foi corrigido na origem e no contrato de exportação.
- `validate_simplified_mandarin` agora rejeita letras não suportadas como cirílico misturado a Han.
- `tonal_pinyin` agora rejeita fallback Han/kana/letra não latina que volte da biblioteca em vez de pinyin real.
- `ExportCardRow` agora falha fechado se `Pinyin` ou `Sentence Pinyin` contiver letras não-pinyin, mesmo quando instanciado diretamente.
- Novas regressões provam que U+3402 não vira snapshot/export row e que Han+cyrillic falha antes de exportar.
- Resultado atual: tecnicamente verificado; estado final da quick task continua `human_needed` por causa da revisão visual humana no Anki.

## Verification Basis

- Fonte de must-haves: frontmatter de `027-PLAN.md` — 7 truths, 7 artifacts e 8 key links.
- Quick task sem requirement IDs; `ROADMAP.md`/`SPEC.md` não reduzem nem ampliam este escopo.
- Não havia `027-VERIFICATION.md` anterior nem overrides aceitos.
- As decisões e as três deviations do SUMMARY foram revisadas. O SUMMARY não contém `<handoff>`/`<deltas>` nem provenance de runtime/assurance; por isso a cadeia de assurance permanece incompleta.
- Plan: `opencode / self_checked`; verifier: `opencode / self_checked`. Como é o mesmo runtime e o role template de verifier está ausente, a assurance não excede `self_checked`.
- Delivery posture: `repo_only`; a task não alega release/publicação. O APKG persistente é evidência local e está marcado `safe_to_publish: false`.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Usuário pode selecionar `zh` em `frequency` e `word-list` e obter Simplificado validado com word/sentence audio. | ✓ VERIFIED | `SupportedLanguage.ZH`, settings e adapters estão ligados; o E2E CLI/repository dos dois source types passou dentro da suíte Mandarin (`56 passed`). Os testes observam `zh`, locale Azure `zh-CN` e 2 áudios/card. |
| 2 | O asset `zh` contém exatamente 3000 entradas, 1000 por nível, provenientes de `wordfreq:zh` e normalizadas para Simplificado/Han. | ✓ VERIFIED | `--check` passou; auditoria independente confirmou ranks 1..3000, 3x1000, script e provenance. Regeneração em diretório temporário com scan limit 25000 foi byte-idêntica aos dois assets persistidos. |
| 3 | Cada card exportável contém pinyin tonal válido e Tradicional para palavra/frase, persistidos no snapshot. | ✓ VERIFIED | Casos normais e round-trip DB passam. Regressões agora rejeitam U+3402 quando `pypinyin` devolve fallback Han, rejeitam Han+cyrillic na entrada e impedem `ExportCardRow` Mandarim com Pinyin/Sentence Pinyin contendo letras não-pinyin. |
| 4 | APKG, CSV e TSV compartilham field order estável, dois áudios e `Image` vazio. | ✓ VERIFIED | Tuple de 12 campos único, suíte export/persistence coberta, E2E dos 3 formatos verde e APKG persistente inspecionado independentemente: 1 note, 12 fields, 2 mídias e Image vazio. |
| 5 | O template preserva a base visual Multilang e a hierarquia planejada, com Translation apenas no verso. | ✓ VERIFIED (static) | Loader concatena o CSS completo de `normal_card.md`; markers do qfmt estão na ordem planejada; Translation está `display:none` e o verso usa o reveal script fixo. Render/legibilidade permanecem humanos. |
| 6 | Nenhum conteúdo, mídia, CSS ou JavaScript do APKG de referência foi incorporado. | ✓ VERIFIED | Nenhuma referência ao nome do arquivo/Migaku/banned identifiers em `src/`, `scripts/` ou testes; o template declara e demonstra composição apenas a partir de `normal_card.md`; a mídia do proof é fixture `ID3-offline-*`. O APKG de referência não foi aberto. |
| 7 | Fluxos e exports não Mandarim mantêm seus contratos. | ✓ VERIFIED | Regressões frequency/word-list existentes: `3 passed`; suíte agregada: `976 passed, 1 deselected` após ignorar o arquivo baseline Japanese e deselecionar o teste assembly atingido pelo mesmo defeito Fugashi Windows já presente no HEAD. |

**Score:** 7/7 truths automated/static verified; human render gate remains pending.

## Required Artifacts

| Artifact | Exists | Substantive | Wired / Data | Status | Details |
|---|---:|---:|---:|---|---|
| `src/multilang/services/mandarin_orthography.py` | ✓ | ✓ | ✓ | ✓ VERIFIED | Chamado uma vez pelo assembler e persistido; entrada e saída pinyin agora rejeitam fallback Han/kana/letras não latinas. |
| `assets/frequency/zh/curated-v1.csv` | ✓ | ✓ | ✓ | ✓ VERIFIED | 3000 rows, 3x1000, byte-idêntico à regeneração determinística. |
| `alembic/versions/20260720_15_mandarin_export_fields.py` | ✓ | ✓ | ✓ | ✓ VERIFIED | Head único; fresh SQLite upgrade; quatro colunas espelhadas em ORM/repository. |
| `src/multilang/templates/mandarin_card.md` | ✓ | ✓ | ✓ | ✓ VERIFIED (static) | Loader seleciona para ambos os source types e exporter incorpora qfmt/afmt/CSS. |
| `tests/integration/test_mandarin_modern_flow.py` | ✓ | ✓ | ✓ | ✓ VERIFIED | Exercita CLI, DB reload, áudio e três exporters offline; incluído e verde no pytest. |
| `.planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg` | ✓ | ✓ | ✓ | ✓ VERIFIED | 66024 bytes; SHA-256 e conteúdo SQLite/media conferidos. |
| `.planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md` | ✓ | ✓ | ✓ | ✓ VERIFIED (bundle) | Campos/privacy/6 observações estáticas válidos; resultado honestamente `human_needed`. |

`gsd-tools verify artifacts` reportou `7/7`. Nenhum artifact é stub ou órfão.

## Key Link Verification

| From | To | Via | Status | Evidence |
|---|---|---|---|---|
| `scripts/build_frequency_assets.py` | `assets/frequency/zh/curated-v1.csv` | `zh`, wordfreq e normalização | ✓ WIRED | Builder temporário reproduziu os assets persistidos byte por byte. |
| `assemble_export_cards.py` | `mandarin_orthography.py` | derivação antes do snapshot | ✓ WIRED | Import e chamada em linhas 22-26/106-141; resultados escapados e enviados ao repository. |
| `export_repository.py` | `db/models.py` | quatro campos round-trip | ✓ WIRED | `_card_payload` e `_to_card_domain` espelham as quatro colunas; teste expire/reload passa. |
| `generate_audio_items.py` | `domain/exporting.py` | fields por language + source | ✓ WIRED | Helper decide word/sentence assets; word-list não Mandarim continua sentence-only pelos testes. |
| `export_anki_package.py` | `mandarin_card.md` | model/loader dedicado | ✓ WIRED | Exporter chama loader, que resolve `mandarin_card`; modelo APKG observado usa id/nome/fields corretos. |
| `runtime.py` | APKG/CSV/TSV exporters | snapshots e routing | ✓ WIRED | `export_job` reutiliza snapshots, constrói media index e despacha para APKG/tabular. |
| E2E Mandarin | proof APKG | `write_mandarin_proof_artifact(output_path)` | ✓ WIRED | Helper gera/valida em path fornecido; teste em temp passa; artifact persistente corresponde ao bundle. |
| `UI-PROOF.md` | proof APKG | path/size/SHA-256 | ✓ WIRED | 66024 bytes e SHA-256 `63712333c79acd2e42002d8c7465d45257cac99dd06df83a4764932f89a4433c`. |

O verificador textual de key links do `gsd-tools` marcou apenas `1/8` porque procura o path-alvo literal; imports Python sem `.py`, paths compostos e o loader indireto não correspondem a essa heurística. Todos os oito links foram portanto conferidos manualmente e por execução.

## Data-Flow Trace (Level 4)

| Artifact / Data | Source | Consumer | Produces real data? | Status |
|---|---|---|---:|---|
| Frequency rows `zh` | CSV congelado reproduzido de `wordfreq:zh` | `load_curated_frequency_entries` → lexical candidates | ✓ | ✓ FLOWING |
| Ortografia comum | accepted Simplified word/sentence | assembler → `ExportCardRow` → DB reload → exporters | ✓ | ✓ FLOWING |
| Ortografia com fallback desconhecido | pypinyin devolve caractere inalterado | `tonal_pinyin` / assembler / row validator | ✗ | ✓ BLOCKED BEFORE SNAPSHOT |
| Word/sentence audio | audio repository com locale/voice `zh-CN` | rows → runtime media index → APKG/CSV/TSV tags | ✓ | ✓ FLOWING |
| Proof APKG | snapshot fixture + dois payloads offline | `collection.anki2` e media map | ✓ | ✓ FLOWING |

Nenhum exporter importa ou chama o serviço ortográfico; os quatro valores são consumidos do snapshot persistido, sem recomputação silenciosa.

## Behavioral Spot-Checks

| Behavior | Command / Probe | Result | Status |
|---|---|---|---|
| Lock consistente | `uv lock --check` | resolved 195 packages | ✓ PASS |
| pypinyin/OpenCC instalados | probe `银行` / `中国→中國` | valores exatos | ✓ PASS |
| Asset válido e determinístico | `--check` + regeneração temp/byte compare | 3000, 3x1000; curated/rejections iguais | ✓ PASS |
| Migration aplicável | Alembic heads + fresh SQLite upgrade | head `20260720_15`; upgrade completo | ✓ PASS |
| Providers/ortografia/Mandarin E2E | focused pytest | `56 passed` | ✓ PASS |
| Domain/persistence/export suites | focused pytest | `186 passed`, 1 falha Fugashi Japanese preexistente | ⚠ BASELINE |
| E2E não Mandarim | focused pytest | `3 passed` | ✓ PASS |
| Regressão agregada | pytest ignorando o arquivo baseline Fugashi e deselecionando o teste assembly afetado | `976 passed, 1 deselected` | ✓ PASS |
| Proof artifact | hash + ZIP + SQLite + media inspection | id/nome/12 fields/1 note/2 media/Image vazio | ✓ PASS |
| UI proof | CLI planejado + fallback local | CLI não oferece `ui-proof`; fallback validou 12 top-level fields, privacy e 6 observações | ⚠ FALLBACK PASS |
| Pinyin sempre válido | U+3402, Han+Cirílico e row com Pinyin residual | serviço e row validator rejeitam; snapshot inválido não é persistido | ✓ PASS |
| Diff whitespace | `git diff --check` | exit 0; somente warnings LF→CRLF | ✓ PASS |

## Requirements / Decision Coverage

Não há requirement IDs nesta quick task. As decisões bloqueadas do plano foram usadas como contrato equivalente:

| Decision | Status | Evidence |
|---|---|---|
| D-01 — `zh` canônico; `zh-CN` apenas locale/provider | ✓ SATISFIED | Enum/request/assets/DB usam `zh`; source matches de `zh-CN` estão limitados a adapters/voz e teste de rejeição. |
| D-02 — pinyin tonal + Tradicional para palavra/frase | ✓ SATISFIED | Casos comuns e persistência passam; fallback Han/letra não latina é rejeitado antes do snapshot e no contrato de row. |
| D-03 — template baseado em `normal_card` | ✓ STATIC / HUMAN PENDING | Código/modelo verificados; pixels e legibilidade não. |
| D-04 — Image vazio | ✓ SATISFIED | Validator, formatos e proof APKG confirmam vazio. |
| D-05 — reference APKG não é fonte | ✓ SATISFIED | Scan limpo e nenhuma leitura/importação no código. |
| D-06 — ambos os flows, áudios, formatos e regressões | ✓ SATISFIED | E2E e suites direcionadas passam offline. |

O roadmap posterior contém somente as Phases 30-34 de Korean; a validação de pinyin Mandarim foi fechada nesta quick task, sem defer para roadmap.

## Anti-Patterns and Warnings

| Location | Finding | Severity | Impact |
|---|---|---|---|
| `mandarin_orthography.py:146-168` | A validação de sílaba pinyin foi estreitada para letras latinas/marks, e a saída renderizada bloqueia Han/kana/letras não latinas. | ✓ Closed | Han desconhecido e letras não latinas não chegam mais ao deck como “Pinyin”. |
| `test_mandarin_orthography.py` | Fallback/error path do pypinyin agora tem regressões para U+3402 e Han+cyrillic. | ✓ Closed | A suíte protege a garantia contra o bug original. |
| UI proof tooling | `gsdd-cli ui-proof validate` não existe na versão instalada. | ⚠ Warning | Bundle foi validado por fallback local, com reduced assurance. |
| Japanese Fugashi on Windows | O arquivo baseline e o teste assembly falham pelo path `-d` sem quoting; o teste assembly já existe no HEAD. | ℹ Info | Baseline não causado por Mandarim; não usado como evidência positiva. |
| Runtime de teste | Python 3.13.7, não 3.12. | ⚠ Warning | Compatibilidade declarada com 3.12 não foi executada neste host. |
| Git delivery | Worktree sujo; `main` e `gh` indisponíveis. | ℹ Info | Delivery metadata incompleta, sem alterar o resultado técnico. |

Não foram encontrados TODO/FIXME/placeholder, handler vazio, mock estático em runtime ou artifact órfão na implementação Mandarim. Retornos vazios encontrados são guards/optional paths ou test doubles intencionais.

## Human Verification Still Required

Estas gates permanecem pendentes após a correção do gap automático:

### 1. Anki Desktop 1280x800

**Test:** Importar o APKG cujo SHA-256 está acima e observar frente/verso.
**Expected:** Simplificado no topo, pinyin imediatamente abaixo, Tradicional discreto, sentence/áudio agrupados, sentence pinyin/Tradicional abaixo e Translation somente após flip, sem overflow/colisão.
**Why human:** Não há renderer Anki no workspace; markup/CSS não provam pixels nem legibilidade.

### 2. AnkiDroid / Google Pixel 7 412x915 portrait

**Test:** Importar o mesmo hash e repetir frente/verso.
**Expected:** Mesma hierarquia, sem clipping/overflow/colisão e com texto legível.
**Why human:** Comportamento/layout do cliente móvel exige observação real.

Como o gap de pinyin foi fechado e nenhuma regressão focada surgiu, o estado esperado é `human_needed` até essas duas observações serem aprovadas.

## Gaps Summary

Nenhum gap técnico permanece aberto para o contrato automatizado desta quick task. O antigo blocker de pinyin foi fechado com validação fail-closed na ortografia, validação adicional no `ExportCardRow` e regressões cobrindo U+3402, Han+cyrillic e snapshot inválido.

A revisão visual continua sendo uma gate humana separada: importar o APKG persistente em Anki Desktop e AnkiDroid/Pixel 7 para confirmar posicionamento, overflow e legibilidade reais.

---

_Verified: 2026-07-22T18:43:42Z_
_Verifier: OpenCode gsd-verifier (reduced assurance)_
