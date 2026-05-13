# Phase 18 Source Coverage Audit

## Sources Audited

- GOAL: `.planning/ROADMAP.md` Phase 18 — user receives corrected learner-facing text fields before cards are exported.
- REQ: `.planning/REQUIREMENTS.md` — IPA-01, DEF-01, DEF-02, TRNS-01.
- RESEARCH/PROJECT: `AGENTS.md`, `.planning/PROJECT.md`, existing Python/Pydantic/pytest stack and v1.3 text-quality decisions.
- CONTEXT: `.planning/STATE.md` v1.3 decisions and `card_issues_normalized.md` normalized defect catalog.

## Coverage Matrix

| Source Item | Covered By | Notes |
|-------------|------------|-------|
| GOAL: Correct learner-facing text fields before export | 18-01, 18-02, 18-03 | IPA, Definition, and Translation gates run before accepted export rows. |
| IPA-01: IPA only phonetic transcription or word fallback | 18-01 | Export rendering removes appended word/spoken form; grounding supplies word fallback when no confident IPA exists. |
| DEF-01: Semantic definitions for generated words/inflected forms | 18-02 | Remediation helper replaces grammar-only metadata when source meaning exists and blocks unresolved patterns. |
| DEF-02: Correct known wrong senses like `дости́чь` | 18-02 | Known correction map requires `verb: to achieve, to attain, to reach`. |
| TRNS-01: Translation translates Example Sentence, not Word | 18-03 | Text validation rejects isolated-word/gloss translations and pipeline tests prove repair/review routing. |
| `card_issues_normalized.md` §1 IPA | 18-01 | Exact normalized IPA repetition defect covered. |
| `card_issues_normalized.md` §2 Definition | 18-02 | Grammar case, `inflection of`, and known wrong-sense defects covered. |
| `card_issues_normalized.md` §3 Translation | 18-03 | Translation/example mismatch covered before export. |
| `card_issues_normalized.md` §4 Layout/Front of Card | Excluded from Phase 18 | Scoped to Phase 19 (`TMPL-01..03`). |
| `card_issues_normalized.md` §5 word_audio | Excluded from Phase 18 | Scoped to Phase 20/21 (`AUD-01`, `AUD-02`, `VAL-01`). |
| FUTURE-01 interactive repair workflow | Excluded | Explicit future requirement; no plan implements it. |

## Result

All Phase 18 source items are covered. Exclusions are roadmap-scoped to later phases or future requirements, not silent omissions.
