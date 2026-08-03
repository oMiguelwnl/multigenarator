---
quick: 039-preview-melhorado-anki
phase: quick-039-preview-melhorado-anki
plan: 039
runtime: opencode
assurance: self_checked
verified: 2026-07-29T17:26:51Z
status: human_needed
score: "11/12 must-haves verified"
overrides_applied: 0
delivery_posture: delivery_sensitive
evidence_contract:
  required_kinds: [code, runtime, delivery]
  recommended_kinds: [test, human]
  observed_kinds: [code, test, runtime, delivery]
  missing_required_kinds: []
ui_proof_slots:
  improved-normal-card-preview-source: satisfied
  improved-normal-card-apkg-structure: satisfied
  improved-normal-card-native-anki-appearance: partial
human_verification:
  - test: "Importar exports/anki_previews/normal-card-improved-test.apkg no Anki Desktop"
    expected: "A importação conclui sem substituir produção e cria o note type Multilang::Card Improved Preview, o deck Multilang Improved Card Test e somente os três cards esperados."
    why_human: "ZIP e SQLite provam importabilidade estrutural, mas não executam o importador nativo do Anki."
  - test: "Revisar Buch, Wasser e lernen na frente e no verso, com o reviewer amplo e reduzido a 420px ou menos"
    expected: "Shell full-width e de altura natural, conteúdo central de até 900px, hierarquia dark legível, tradução revelada apenas no verso, sem overflow nem controles/mídia vazios."
    why_human: "CSS estático não prova layout computado, legibilidade ou comportamento do WebView do Anki."
git_delivery_check:
  branch: Monarch
  head: 0664390fec7aa1d210438b3f7baa599f84cbbe01
  commits_ahead_of_main: unknown
  pr_state: unknown
  staged_diff_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  note: "main não existe localmente; PR não foi consultado para respeitar a execução totalmente offline."
---

# Quick 039: Preview melhorado Anki — Verification Report

**Objetivo:** preview melhorado standalone e APKG experimental importável, sem alterar produção.

**Veredito:** `human_needed`. Todos os contratos automatizáveis de source, ZIP/SQLite, TSV, isolamento e integridade passaram. A importação e a aparência no renderer nativo do Anki continuam pendentes, como exigido pelo limite de alegação do plano.

## Base da verificação

- Verificação inicial: não existia `039-VERIFICATION.md` anterior.
- Fontes de must-haves: 11 truths e 3 UI-proof slots do frontmatter de `039-PLAN.md`; o slot nativo acrescenta a 12ª verdade observável.
- `039-SUMMARY.md`, `<handoff>`, `<deltas>`, `<judgment>` e `UI-PROOF.md` foram lidos como contexto, não aceitos como prova por si só.
- Plano e execução foram feitos em `opencode`; esta passagem também usa `opencode`, portanto a assurance máxima honesta é `self_checked`, apesar dos validadores independentes.
- Quick sem requirement IDs de ROADMAP (`requirements: []`); não há requisito órfão de fase a avaliar.

## Goal Achievement

### Verdades observáveis

| # | Verdade | Status | Evidência independente |
|---|---|---|---|
| 1 | Preview offline contém exatamente uma frente e um verso | ✓ VERIFIED | `HTMLParser` encontrou janelas e articles na ordem `front`, `back`; os bodies ficam idênticos após normalizar somente o estado da tradução. |
| 2 | Preview não possui script, rede ou asset externo | ✓ VERIFIED | Zero `script/link/base/img/audio/video/iframe/object/embed`, zero `src/href/srcset`, event handlers, HTTP(S), `@import`, `url()` ou Mustache. |
| 3 | Shell é full-width/natural-height e `.cardContent` limita a 900px | ✓ VERIFIED | `.card`, `#qa` e `.customCard` usam 100%/min-width 0; shell tem `min-height: 0`, sem `height`; wrapper usa `width: 100%`, `max-width: 900px`, `margin: 0 auto`. |
| 4 | Clamps, hierarquia, áudio 34px/focus e breakpoint 420px estão declarados | ✓ VERIFIED | Clamps por seletor, painel/heading/tradução, quatro botões inertes acessíveis, mínimos 34×34px, foco 3px e regras internas ao media query foram validados. |
| 5 | APKG experimental é estruturalmente importável e isolado | ✓ VERIFIED | ZIP íntegro, SQLite `integrity_check=ok`, model `1762801039`/deck `1762801040` e nomes exclusivos; nenhuma colisão dos IDs em 753 arquivos UTF-8 fora da quick. Importação nativa fica no item 12. |
| 6 | APKG contém somente Buch, Wasser e lernen, com 9 fields em ordem | ✓ VERIFIED | Exatamente 3 notes/3 cards; rows exatas; `word_audio`, `sentence_audio` e `Image` vazios. |
| 7 | Notes e cards têm identidades distintas e GUIDs explícitos esperados | ✓ VERIFIED | Três `notes.id`, três `cards.nid` e três GUIDs distintos; GUIDs recalculados: `HtYJ}S^5Rf`, `JPd<d]p+7?`, `Ll0a&a<R0n`. |
| 8 | Um único `Card 1` ord 0 possui qfmt/afmt seguros | ✓ VERIFIED | Todos os cards e o template usam `ord=0`; qfmt sem script e com IPA/Image condicionais, áudio e Translation oculta; afmt é exatamente `FrontSide` + reveal fixo, sem field em script, `innerHTML`, `eval`, URL ou field desconhecido. |
| 9 | CSS do APKG é igual ao preview e o pacote contém zero mídia | ✓ VERIFIED | Igualdade textual após `strip`; ZIP contém somente `collection.anki2` e `media`; manifesto `media == {}` e nenhum membro numérico. |
| 10 | TSV é UTF-8/no-BOM/LF-only e exatamente igual às notes | ✓ VERIFIED | 479 bytes, UTF-8 estrito, 4 LF, 0 CR, header + 3 rows byte a byte iguais aos fields SQLite ordenados por `SortIndex`. |
| 11 | Outputs existem e produção/trabalho concorrente foram preservados | ✓ VERIFIED | HTML 12.836 B, APKG 61.658 B, TSV 479 B e proof não vazios. Baseline, after, live e recomputação atual coincidem; source/tests aparecem antes e agora somente como os mesmos 3 `M`, sem `A`/`??`. |
| 12 | Importação e aparência no Anki nativo foram observadas | ? HUMAN NEEDED | Nenhum Anki/browser foi aberto. O bundle registra corretamente 4 observações `human_needed`; source/SQLite não substituem esse teste. |

**Score:** 11/12 verdades verificadas; a única pendência é humana, não um gap estrutural conhecido.

## Artefatos (L1–L3)

| Artefato | Existe | Substantivo | Wired | Resultado |
|---|---:|---:|---:|---|
| `normal_card_improved_preview.html` | ✓ | ✓ — 12.836 B, HTML/CSS completo | ✓ — bloco CSS é exatamente o `model.css` | VERIFIED |
| `exports/anki_previews/normal-card-improved-test.apkg` | ✓ | ✓ — ZIP/SQLite íntegros, 3 notes/cards | ✓ — model, deck, cards, templates e notes conectados | VERIFIED estruturalmente |
| `exports/anki_previews/normal-card-improved-test.tsv` | ✓ | ✓ — header + 3 rows | ✓ — bytes correspondem às `notes.flds` | VERIFIED |
| `.planning/quick/039-preview-melhorado-anki/UI-PROOF.md` | ✓ | ✓ — JSON válido, 20 observações | ✓ — 8 source pass, 8 APKG pass, 4 native human-needed | VERIFIED com handoff humano |

### Hashes observados

| Artefato | SHA-256 |
|---|---|
| Preview | `b45e89603c1aba172d0edd730f1b51bf6327efd741db173902893fab31548c4d` |
| APKG | `6aae7f3ac61ef9ac79e0ff45856f1a24be00e95982a6da2c6c75ce2c206d7fbf` |
| TSV | `a52fc303b03900f44531db3e5a9ace543f91cf34c2cbdc5daa1219432d07bc18` |
| CSS compartilhado normalizado | `7acca4c8222203d0e25387a55431e39752876d861dbb2993490a4fcd11287329` |

## Key Links

| De | Para | Via | Status |
|---|---|---|---|
| Bloco CSS marcado do preview | `model.css` do model `1762801039` | igualdade textual | ✓ WIRED |
| qfmt | 9 fields | Mustache allowlisted; IPA/Image condicionais e slots de áudio | ✓ WIRED |
| afmt | `#translation` do qfmt | `FrontSide` + `getElementById` fixo | ✓ WIRED no template; execução nativa pendente |
| `notes.flds` | TSV | igualdade exata de header/rows/ordem | ✓ WIRED |
| Identidade note type/model/SortIndex/word | `notes.guid` | `genanki.guid_for(...)` recalculado | ✓ WIRED |
| APKG/TSV/preview | UI proof | hashes, tamanhos e observações por slot | ✓ WIRED |

## Verificações offline executadas

Todos os validadores Python foram executados com o prefixo obrigatório `uv run --offline --no-sync --frozen --no-env-file python -c`.

| Check | Resultado |
|---|---|
| Parser HTML + contrato CSS independente | PASS — 2 estados, 4 controles, zero dependências externas, shell/wrapper/clamps/focus/420px válidos |
| Leitura ZIP por `ZipFile.read` + SQLite em memória por `deserialize` | PASS — ZIP íntegro, SQLite ok, 3/3, IDs/GUIDs/template/CSS/media exatos; nunca `extractall` |
| Comparação TSV byte a byte com SQLite | PASS — UTF-8 sem BOM, LF-only, 9 fields e rows exatas |
| Parser independente do UI proof | PASS — JSON válido, slots 8/8/4, hashes atuais e classificação `human_needed` |
| Scan de escopo/IDs | PASS — 753 textos UTF-8; zero colisões; zero source/test adicionado ou untracked |
| Snapshot global e baselines externos | PASS — original preservado; rebaseline `before == after == live`; recomputação atual igual |
| Git read-only | PASS — HEAD preservado e staged diff vazio; nenhuma operação mutável executada |

Nenhuma rede, provider, `.env`, extração de ZIP ou importação no Anki foi usada. O APKG foi lido sem gravar sua collection no worktree.

## Integridade e mudanças concorrentes

- Snapshot filtrando apenas os outputs autorizados (incluindo este report): HEAD `0664390...`, staged diff SHA vazio, 41 entradas concorrentes e digest de 863 paths `9ff49dd6...ac0be`, idênticos antes e depois da escrita do report.
- `uv.lock` permanece `6e73a05c...b5ae5f`; `pyproject.toml`, `ad086568...04f68`.
- As mudanças atuais em `src/multilang/templates/normal_card.md` e nos dois testes aparecem tanto no baseline pré-output quanto no estado atual como `M`; não há arquivo `A`/`??` em `src/` ou `tests/` associado à quick.
- `LOG.md` e demais mudanças concorrentes já estavam fora do write set e não foram editados por esta verificação.

## Anti-patterns e segurança

Nenhum blocker encontrado. O único `<script>` está no `afmt` e corresponde exatamente ao reveal fixo permitido; o preview e o qfmt não têm script. Campos de áudio/imagem vazios são parte deliberada do experimento e significam que o APKG não prova playback nem renderiza esses controles — não são stubs de produção.

Uma primeira asserção auxiliar do verifier esperava duas ocorrências globais de `Buch`; o diagnóstico mostrou quatro ocorrências legítimas (palavra e frase, em front/back), enquanto os bodies normalizados eram idênticos. O check foi corrigido para contar especificamente `.targetWord`; nenhum artefato foi alterado.

## Pendência humana

### 1. Importação nativa

**Teste:** importar o APKG no Anki Desktop.

**Esperado:** criação isolada do note type/deck e dos três cards, sem substituir produção nem gerar erro de importação.

### 2. Aparência e comportamento do reviewer

**Teste:** revisar frente/verso dos três cards em largura ampla e até 420px ou menos.

**Esperado:** largura total, altura natural, wrapper central, hierarquia/contraste legíveis, tradução revelada somente no verso e ausência de overflow ou mídia vazia.

**Por que humana:** estrutura e CSS não observam pixels computados, WebView, importador ou julgamento visual. Até essa confirmação, o veredito não pode ser promovido para `passed`.

## Findings

- **Automated source/structure:** PASS.
- **Produção e mudanças concorrentes:** preservadas nos checks executados.
- **Gap automatizado:** nenhum.
- **Pendência:** importação e aparência no Anki nativo.

---

_Verified: 2026-07-29T17:26:51Z_
_Verifier: gsd-verifier (independent offline pass)_
