# Phase 21 Source Coverage Audit

## Sources Audited

| Source Type | Artifact | Items |
|-------------|----------|-------|
| GOAL | `.planning/ROADMAP.md` Phase 21 goal and success criteria | Repeatable validation/evidence; validator categories; normalized fixtures; final milestone evidence; existing deck mode safety |
| REQ | `.planning/REQUIREMENTS.md` | VAL-01, VAL-02, VAL-03 |
| RESEARCH | Project stack/research in `AGENTS.md` | Python/pytest deterministic validation; no new external dependencies; avoid live provider-only validation |
| CONTEXT | Phase discussion context | No Phase 21 CONTEXT.md exists; carry-forward decisions from `.planning/STATE.md` apply |

## Coverage Matrix

| Item | Covered By | Notes |
|------|------------|-------|
| GOAL: repeatable validation and evidence | 21-01, 21-02, 21-03 | Validator facade, normalized fixtures, and final evidence artifact |
| GOAL: validators for IPA word repetition | 21-01, 21-02 | IPA repetition validator and fixture cases from `card_issues_normalized.md` |
| GOAL: banned Definition patterns | 21-01, 21-02 | Reuses `validate_definition_html`; fixtures include grammar metadata and relation-only patterns |
| GOAL: Translation/example mismatch | 21-01, 21-02 | Reuses `TextValidationService`; fixtures include isolated-word vs full-sentence translations |
| GOAL: word_audio/Word mismatch | 21-01, 21-02, 21-03 | Reuses Phase 20 `audio_integrity`; fixtures and mode evidence assert normal-only word_audio behavior |
| GOAL: dangling template fields | 21-01, 21-02, 21-03 | Reuses template reference validation; evidence asserts revised normal contract and source-profile isolation |
| GOAL: normalized issue fixtures | 21-02 | Fixture JSON covers the normalized examples and summary action groups |
| GOAL: final milestone evidence | 21-03 | Scanner-readable evidence file and test |
| GOAL: frequency/custom/highlight/phonetics unaffected | 21-03 | Existing-mode regression evidence across deck modes |
| REQ VAL-01 | 21-01 | Validators for all required categories |
| REQ VAL-02 | 21-02 | Regression fixtures for normalized issue examples |
| REQ VAL-03 | 21-03 | Final evidence and existing-mode regression proof |
| RESEARCH: Python/pytest deterministic validation | 21-01, 21-02, 21-03 | All verification uses focused pytest suites and JSON validation |
| RESEARCH: avoid live provider-only validation | 21-01, 21-02, 21-03 | Uses synthetic rows/assets/templates and Phase 20 metadata checks |
| STATE: privacy-safe evidence | 21-02, 21-03, 21-04 | No raw private APKG excerpts; scanner blocks private markers; gap fixture remains synthetic template markup |
| STATE: keep normal/highlight/phonetics isolated | 21-03 | Dedicated existing-mode regression file |
| VERIFICATION GAP: whitespace-formatted `sentence_audio` reference bypass | 21-04 | Gap-closure plan adds a whitespace-tolerant detector and regression fixture for valid Anki reference formatting |

## Deferred / Excluded Items

| Item | Reason |
|------|--------|
| Automatic image generation or sourcing | Out of scope in `.planning/REQUIREMENTS.md` |
| New supported languages | Out of scope for v1.3 |
| Replacing Anki as the study target | Out of scope for v1.3 |
| Reworking highlight or phonetics note types beyond regression safety | Out of scope; Phase 21 only proves isolation |
| Live TTS provider calls as the only audio validation evidence | Explicitly excluded; Phase 21 uses deterministic metadata and fakes |

## Result

All GOAL, REQ, RESEARCH, CONTEXT carry-forward items, and the Phase 21 verification gap are covered by the Phase 21 plan set. No unplanned source items remain.
