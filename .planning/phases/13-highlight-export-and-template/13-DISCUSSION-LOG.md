# Phase 13: Highlight Export and Template - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-06
**Phase:** 13-Highlight Export and Template
**Areas discussed:** Front card, Back definition, Visual style, Export safety

---

## Front Card

| Option | Description | Selected |
|--------|-------------|----------|
| Word first | Palavra em destaque, com IPA e áudio; mais direto para estudo. | |
| Sentence first | Exemplo como prompt principal, palavra menos dominante. | |
| Balanced | Palavra e exemplo com peso parecido na frente. | |
| User free-text | Palavra, IPA, audio, frase. | yes |

**User's choice:** Front should show word, IPA, audio, and sentence.
**Notes:** User also selected showing the example with `sentence_audio`, conditional blank `Image`, and minimal labels.

---

## Back Definition

| Option | Description | Selected |
|--------|-------------|----------|
| Divider then definition | `{{FrontSide}}`, divisor visual, depois `Definition`; recomendado pelo requisito. | yes |
| Definition card block | Bloco destacado separado, com título mais forte. | |
| Inline definition | Definição logo abaixo, layout mais simples. | |
| You decide | Deixar o planner escolher dentro do requisito. | |

**User's choice:** Use `{{FrontSide}}`, then divider, then a clearly labeled `Definition` area.
**Notes:** User selected `Definition` label and bullet list for multiple definitions. User clarified no repeated audio or autoplay should be added on the back; the required `FrontSide` remains.

---

## Visual Style

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse blue style | Reusar visual Multilang azul atual; consistente e mais rápido. | |
| Softer reading card | Visual mais leve de leitura, ainda com cores Multilang. | |
| Distinct highlight | Mais diferente do deck normal para destacar que veio de leitura. | |
| You decide | Deixar o planner escolher. | yes |

**User's choice:** Visual direction is agent discretion, with constraints.
**Notes:** User selected centered card, comfortable density, and confirmed mobile may scroll vertically for long content while avoiding horizontal scroll.

---

## Export Safety

| Option | Description | Selected |
|--------|-------------|----------|
| Fail closed | Bloquear export misto com erro claro; recomendado e já alinhado ao código. | interpreted yes |
| Split exports | Gerar arquivos separados por source type automaticamente. | |
| Allow mixed | Permitir mistura se os campos forem compatíveis. | |
| Strict headers | Incluir `#notetype`, `#deck`, `#columns` com campos exatos. | yes |

**User's choice:** Highlight export should be highlight-only, strict, and safe.
**Notes:** User clarified that highlight cards are generated from highlight words, expects Azure TTS for audio, and selected strict CSV/TSV headers. The discussion clarified that `frequency`, `word-list`, and `highlights` are separate modes.

---

## the agent's Discretion

- Exact highlight visual direction within Multilang branding.
- Exact CSS details and responsive breakpoints.
- Exact implementation shape for template selection and validation.

## Deferred Ideas

- Apply the new highlight-style template to manual `word-list` decks too. Deferred because Phase 13 is scoped to highlight export/template and must preserve existing `word-list` behavior.
