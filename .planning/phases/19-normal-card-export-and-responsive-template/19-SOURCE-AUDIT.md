# Phase 19 Source Coverage Audit

Phase: 19-normal-card-export-and-responsive-template  
Mode: standard planning without CONTEXT.md  
Research/discovery: Level 0 — existing export/template patterns only; no new dependency or external API.

## Source Items

| Source | Item | Coverage |
|--------|------|----------|
| GOAL | Normal generated-card exports use the revised field contract and responsive layout without affecting highlight or phonetics cards. | Covered by 19-01, 19-02, 19-03 |
| REQ | TMPL-01: normal APKG, CSV, TSV, and template references omit redundant `Front of Card`. | Covered by 19-01 |
| REQ | TMPL-02: `sentence_audio` appears beside `Example Sentence` at desktop and mobile card widths. | Covered by 19-02 |
| REQ | TMPL-03: highlight and phonetics behavior remains isolated from normal-card schema/CSS changes. | Covered by 19-03, with regression checks in 19-01 and 19-02 |
| RESEARCH | Existing stack uses Python, genanki, typed Pydantic export rows, and golden/focused tests for APKG/CSV/TSV contracts. | Covered by 19-01 and 19-03 |
| RESEARCH | Do not leak export logic into generation logic; preserve stable internal card schema and source-profile routing. | Covered by 19-01 |
| RESEARCH | Template validation must reject dangling field references and keep `FrontSide` as the only non-field helper. | Covered by 19-01 and 19-03 |
| CONTEXT | No phase CONTEXT.md exists; user explicitly chose to continue without context. Locked decisions: none. Deferred ideas: none. | N/A |

## Exclusions

- Phase 18 text remediation (`IPA`, `Definition`, `Translation`) is a dependency and not re-planned here.
- Phase 20 word-audio integrity is out of scope.
- Future backward compatibility for legacy `Front of Card` decks is explicitly future scope in REQUIREMENTS.md.

## Audit Result

All GOAL, REQ, RESEARCH, and available CONTEXT source items are covered by the plan set. No unplanned source items found.
