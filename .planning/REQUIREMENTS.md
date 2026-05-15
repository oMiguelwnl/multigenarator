# Requirements: Multilang Anki Card Generator v1.3

**Defined:** 2026-05-12  
**Milestone:** v1.3 Card Quality Remediation and Deck Validation  
**Core Value:** Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.  
**Source:** `card_issues_normalized.md`, milestone questioning, and existing v1.2 planning context

## v1.3 Requirements

Requirements for the current milestone. Each requirement maps to exactly one roadmap phase.

### Deck Quality Audit

- [x] **AUDIT-01**: User can audit a generated APKG, including `dbda4eb2-f0ec-402b-864f-48cdcf982b09.apkg`, and receive a report of normalized card-quality defects by note/card identifier and field.
- [x] **AUDIT-02**: User can identify every card in the audited deck whose `Definition` is grammatical metadata, an inflection description, or an incorrect semantic sense.
- [x] **AUDIT-03**: User can run the deck audit without mutating the original deck, with reproducible human-readable and machine-readable output.

### Text Field Correctness

- [x] **IPA-01**: User receives `IPA` values that contain only the phonetic transcription, or the word itself as a fallback when pronunciation cannot be determined confidently.
- [x] **DEF-01**: User receives English semantic definitions for generated words, including inflected forms, instead of case descriptions or `inflection of`-style metadata.
- [x] **DEF-02**: User receives corrected definitions for known wrong senses, including cases like `дости́чь` meaning "to achieve, to attain, to reach".
- [x] **TRNS-01**: User receives `Translation` values that translate the `Example Sentence`, not the isolated `Word`.

### Template and Export Contract

- [x] **TMPL-01**: User receives normal generated card exports without the redundant `Front of Card` field in APKG, CSV, TSV, or template references.
- [x] **TMPL-02**: User sees `sentence_audio` beside `Example Sentence` on normal cards across desktop and mobile card widths.
- [x] **TMPL-03**: User keeps highlight and phonetics template behavior isolated from normal-card schema and CSS changes.

### Audio Integrity

- [x] **AUD-01**: User can detect `word_audio` assets whose synthesis text or stored manifest does not exactly match the card `Word`.
- [x] **AUD-02**: User receives exported cards only when `word_audio` matches `Word`, with mismatches repaired, regenerated, or blocked with a clear validation error.

### Validation and Evidence

- [x] **VAL-01**: User can run validators for IPA word repetition, banned Definition patterns, Translation/example mismatch, `word_audio`/`Word` mismatch, and dangling template fields.
- [x] **VAL-02**: User gets regression fixtures covering the normalized issue examples from `card_issues_normalized.md`.
- [ ] **VAL-03**: User gets final milestone evidence proving the audit, corrections, normal-card export contract, and unaffected existing deck modes.

## Future Requirements

Deferred to future milestones. Tracked but not in the current roadmap.

### Deck Review and Repair Workflow

- **FUTURE-01**: User can interactively approve, reject, or manually edit each audited card issue before repair.
- **FUTURE-02**: User can run bulk semantic judging over all generated decks with provider-backed confidence scores and human review queues.
- **FUTURE-03**: User can preserve backward-compatible exports for older decks that still require the legacy `Front of Card` field.
- **FUTURE-04**: User can attach provenance metadata to every generated field so future audits can trace source, provider, prompt, and validation status.

## Out of Scope

Explicitly excluded from v1.3 to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Automatic image generation or sourcing | The project decision remains that `Image` is blank by default for manual user population. |
| New supported languages | v1.3 fixes quality for the existing supported-language scope instead of expanding language coverage. |
| Replacing Anki as the study target | The product remains an Anki deck generator, not a standalone SRS app. |
| Reworking highlight or phonetics note types beyond regression safety | v1.3 changes the normal generated-card contract and must keep existing highlight/phonetics behavior isolated. |
| Live TTS provider calls as the only way to validate audio integrity | Validation must be deterministic and testable with stored synthesis metadata and fakes; live Azure calls remain optional integration evidence. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUDIT-01 | Phase 17 | Complete |
| AUDIT-02 | Phase 17 | Complete |
| AUDIT-03 | Phase 17 | Complete |
| IPA-01 | Phase 18 | Complete |
| DEF-01 | Phase 18 | Complete |
| DEF-02 | Phase 18 | Complete |
| TRNS-01 | Phase 18 | Complete |
| TMPL-01 | Phase 19 | Complete |
| TMPL-02 | Phase 19 | Complete |
| TMPL-03 | Phase 19 | Complete |
| AUD-01 | Phase 20 | Complete |
| AUD-02 | Phase 20 | Complete |
| VAL-01 | Phase 21 | Complete |
| VAL-02 | Phase 21 | Complete |
| VAL-03 | Phase 21 | Pending |

**Coverage:**

- v1.3 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0

---
*Requirements defined: 2026-05-12*  
*Last updated: 2026-05-12 after v1.3 roadmap creation*
