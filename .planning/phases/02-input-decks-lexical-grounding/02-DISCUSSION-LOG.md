# Phase 2: Input Decks & Lexical Grounding - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `02-CONTEXT.md`.

**Date:** 2026-04-19
**Phase:** 02-input-decks-lexical-grounding
**Areas discussed:** Lexical identity, Frequency deck curation, Custom word-list ingestion, Missing lexical data, Output language policy

---

## Lexical identity

| Option | Description | Selected |
|--------|-------------|----------|
| Form + lemma | Keep a study-facing display form while also persisting normalized `lemma` and lexical grounding metadata. | ✓ |
| Lemma only | Model cards around the bare lemma only. | |
| Rich lexical entry | Push more POS and sense structure into Phase 2 immediately. | |

**User's choice:** Form + lemma
**Notes:** The visible card form should be the pedagogically appropriate study form for the language, not the bare lemma and not just the raw input string.

---

## Frequency deck curation

| Option | Description | Selected |
|--------|-------------|----------|
| Light curation | Start from deterministic frequency ranking, then apply filters for bad candidates. | ✓ |
| Raw ranking | Ship the ranking almost as-is. | |
| Heavy curation | Require a more manual pedagogical pass before Phase 2 can land. | |

**User's choice:** Light curation
**Notes:** Mandatory removals include corpus noise, obvious names, broken abbreviations or symbols, and clearly bad study items. Legitimate high-frequency function words should stay.

---

## Custom word-list ingestion

| Option | Description | Selected |
|--------|-------------|----------|
| Preserve + normalize | Keep the submitted form and also resolve a normalized lexical target. | ✓ |
| Lemma only | Convert everything to lemma and discard the original form. | |
| Preserve raw | Treat each submitted string as the final card identity. | |

**User's choice:** Preserve + normalize
**Notes:** Phase 2 should prioritize plain-text input with one item per line. CSV or TSV input is not required yet.

---

## Missing lexical data

| Option | Description | Selected |
|--------|-------------|----------|
| Trust first | Do not invent IPA, use controlled fallback only where justified, and keep weak items visibly flagged. | ✓ |
| Marked fallback | Fill most gaps through fallback sources as long as they are labeled. | |
| Maximum coverage | Prefer filling every field even when confidence is weaker. | |

**User's choice:** Trust first
**Notes:** If a frequency candidate still fails grounding, backfill from the next valid candidate. If a custom-list item still fails grounding, keep it and mark it as insufficient instead of silently replacing it.

---

## Output language policy

| Option | Description | Selected |
|--------|-------------|----------|
| English across all supporting text | Keep definitions and sentence translations in English for every deck. | |
| English support with English-deck exception | Keep definitions in English, keep sentence translations in English for non-English decks, and use Portuguese for the English deck translation field. | ✓ |

**User's choice:** English support with English-deck exception
**Notes:** The user explicitly clarified that `Definitions` stay in English, while the English target deck should translate example sentences into Portuguese.

---

## the agent's Discretion

- Exact lexical source ordering and adapter shape.
- Exact metadata column set beyond the locked display-form, lemma, ranking, and provenance requirements.
- Exact CLI wording for warnings and rejected-item messages.

## Deferred Ideas

- CSV or TSV custom word-list support after plain-text ingestion is stable.
- Stronger pedagogical curation after the first deterministic frequency pipeline exists.
