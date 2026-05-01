---
created: 2026-05-01T19:34:11Z
title: Standardize card definition templates
area: general
files:
  - Ideia.md:1-4
  - src/multilang/services/lexical_grounding.py:101
  - src/multilang/services/assemble_export_cards.py:85-86
  - tests/services/test_lexical_grounding.py:28-49
  - tests/services/test_assemble_export_cards.py:173-187
---

## Problem

The user wants the generated `Definitions` field to follow a stricter, predictable template across cards. The current project has a deck-wide HTML/export convention for definitions, but the idea in `Ideia.md` asks for semantic standardization too: when the card item is a verb, the definition should state the meaning and immediately indicate the verb tense/form represented by the card.

Without a controlled definition template, generated cards can drift between short glosses, dictionary-style phrases, and grammar-aware explanations. That makes reviews harder and can produce inconsistent learner-facing cards, especially when the displayed form is not the lemma.

## Solution

Design a normalized definition contract before rendering/export. At minimum, capture `meaning`, `part_of_speech`, `grammatical_form` or `tense`, and provenance for each sense. Render the learner-facing field from that contract with one stable template per sense, joined with `<br>` for export compatibility.

Recommended initial template:

```text
[meaning] ([part of speech]; [tense/form when relevant])
```

For verbs, the formatter should put the meaning first and the tense/form immediately after it, for example `to wash (verb; infinitive)` or `washed (verb; past tense/past participle)` when the source metadata supports that distinction. Use authoritative lexical/conjugation metadata when available; if AI is used to fill gaps, persist fallback provenance and validate the output before export. Add tests around lexical grounding and export assembly so the definition template cannot regress.
