# Phase 17 Source Coverage Audit

## Sources Audited

- GOAL: `.planning/ROADMAP.md` Phase 17 — inspect generated APKG decks for known normalized quality defects without changing the original deck.
- REQ: `.planning/REQUIREMENTS.md` — AUDIT-01, AUDIT-02, AUDIT-03.
- RESEARCH/PROJECT: `AGENTS.md`, `.planning/PROJECT.md`, existing Python/Typer/genanki/pytest stack and APKG zip/sqlite patterns.
- CONTEXT: `.planning/STATE.md` v1.3 decisions and `card_issues_normalized.md` normalized defect catalog.

## Coverage Matrix

| Source Item | Covered By | Notes |
|-------------|------------|-------|
| GOAL: Audit generated APKG non-destructively | 17-01, 17-02, 17-03 | Reader computes before/after hash, reports serialize findings, CLI exposes command. |
| AUDIT-01: Report normalized defects by note/card identifier and field | 17-01, 17-02, 17-03 | `AuditCard` identifiers + grouped Markdown/JSON reports + CLI command. |
| AUDIT-02: Identify Definition grammar metadata, inflection descriptions, wrong senses | 17-01, 17-02 | Detector implements normalized Definition issue rules and reports carry them. |
| AUDIT-03: No mutation, reproducible human/machine output | 17-01, 17-02, 17-03 | Hash non-mutation tests, deterministic report sorting/bytes, CLI rerun tests. |
| `card_issues_normalized.md` §1 IPA | Excluded from Phase 17 | Scoped to Phase 18/21 by ROADMAP (`IPA-01`, `VAL-01`). |
| `card_issues_normalized.md` §2 Definition audit | 17-01, 17-02, 17-03 | Phase 17 specifically covers Definition audit, not correction. |
| `card_issues_normalized.md` §3 Translation | Excluded from Phase 17 | Scoped to Phase 18/21 (`TRNS-01`, `VAL-01`). |
| `card_issues_normalized.md` §4 Layout/Front of Card | Excluded from Phase 17 | Scoped to Phase 19 (`TMPL-01..03`). |
| `card_issues_normalized.md` §5 word_audio | Excluded from Phase 17 | Scoped to Phase 20/21 (`AUD-01`, `AUD-02`, `VAL-01`). |
| STATE blocker: locate/supply `dbda4eb2...apkg` | 17-03 | Human-action checkpoint only if workspace search cannot find the local APKG. |
| FUTURE-01 interactive repair workflow | Excluded | Explicit future requirement; no plan implements it. |

## Result

All Phase 17 source items are covered. Exclusions are roadmap-scoped to later phases or future requirements, not silent omissions.
