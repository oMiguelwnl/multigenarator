# Roadmap: Multilang Anki Card Generator

## Milestones

- [x] **v1.0 MVP** - Phases 1-7 shipped 2026-04-29. Archive: [v1.0-ROADMAP.md](./milestones/v1.0-ROADMAP.md). Requirements: [v1.0-REQUIREMENTS.md](./milestones/v1.0-REQUIREMENTS.md).
- [x] **v1.1 Card Quality Refresh** - Phase 08 completed 2026-05-02 with audio prominence, AI-generated pronunciation, spoken-form display, and normal deck CSS refresh from `total.md`.
- [x] **v1.2 Kindle Highlights and Template Refresh** - Phases 09-16 completed 2026-05-08 with local Kindle highlights, highlight export, WebDAV fetch, phonetics template refresh, and end-to-end evidence.
- [ ] **v1.3 Card Quality Remediation and Deck Validation** - Phases 17-21 fix known generated-card defects and harden deck validation before export.

## Current Focus

Phase 17: Deck Quality Audit and Issue Reports.

## Phases

- [x] **Phase 17: Deck Quality Audit and Issue Reports** - Generated APKGs can be audited non-destructively for normalized card-quality defects with actionable reports. (completed 2026-05-12)
- [x] **Phase 18: Text Field Remediation** - IPA, Definition, and Translation values are corrected to learner-safe meanings, pronunciations, and sentence translations. (completed 2026-05-13)
- [x] **Phase 19: Normal Card Export and Responsive Template** - Normal card exports remove `Front of Card` while preserving responsive sentence-audio layout and isolating other templates. (completed 2026-05-13)
- [x] **Phase 20: Word Audio Integrity Gate** - Word audio mismatches are detected and repaired, regenerated, or blocked before exported cards reach the user. (completed 2026-05-13)
- [ ] **Phase 21: Validation Fixtures and Milestone Evidence** - Validators, normalized issue fixtures, and final evidence prove defects do not recur across deck modes.

## Phase Details

### Phase 17: Deck Quality Audit and Issue Reports

**Goal**: User can inspect generated APKG decks for known normalized quality defects without changing the original deck.  
**Depends on**: Phase 16  
**Requirements**: AUDIT-01, AUDIT-02, AUDIT-03  
**Success Criteria** (what must be TRUE):
  1. User can audit a generated APKG, including `dbda4eb2-f0ec-402b-864f-48cdcf982b09.apkg`, and see defects grouped by note/card identifier and field.
  2. User can identify every audited card whose `Definition` is grammatical metadata, an inflection description, or an incorrect semantic sense.
  3. User receives both human-readable and machine-readable audit output that is reproducible across reruns.
  4. User can run the audit with confidence that the original APKG is not mutated.
**Plans**: 3 plans
Plans:
- [x] 17-01-PLAN.md — Build non-mutating APKG reader and Definition issue detector.
- [x] 17-02-PLAN.md — Write reproducible JSON and Markdown audit reports.
- [x] 17-03-PLAN.md — Add `audit-deck` CLI command and deck-specific evidence gate.

### Phase 18: Text Field Remediation

**Goal**: User receives corrected learner-facing text fields before cards are exported.  
**Depends on**: Phase 17  
**Requirements**: IPA-01, DEF-01, DEF-02, TRNS-01  
**Success Criteria** (what must be TRUE):
  1. User sees `IPA` values containing only phonetic transcription, or the word itself only when pronunciation cannot be determined confidently.
  2. User receives English semantic definitions for generated words and inflected forms instead of grammatical case or `inflection of` metadata.
  3. User receives corrected definitions for known wrong senses, including `дости́чь` as “to achieve, to attain, to reach”.
  4. User sees `Translation` values that translate the full `Example Sentence`, not the isolated `Word`.
**Plans**: 3 plans
Plans:
- [x] 18-01-PLAN.md — Correct IPA fallback and IPA-only export rendering.
- [x] 18-02-PLAN.md — Remediate semantic Definitions and block unresolved morphology-only values.
- [x] 18-03-PLAN.md — Reject isolated-word Translations before acceptance/export.

### Phase 19: Normal Card Export and Responsive Template

**Goal**: Normal generated-card exports use the revised field contract and responsive layout without affecting highlight or phonetics cards.  
**Depends on**: Phase 18  
**Requirements**: TMPL-01, TMPL-02, TMPL-03  
**Success Criteria** (what must be TRUE):
  1. User receives normal APKG, CSV, and TSV exports with no redundant `Front of Card` field or dangling template reference.
  2. User sees `sentence_audio` visually beside `Example Sentence` on normal cards at desktop and mobile card widths.
  3. User keeps highlight template behavior unchanged after the normal-card schema and CSS changes.
  4. User keeps phonetics template behavior unchanged after the normal-card schema and CSS changes.
**Plans**: 3 plans
Plans:
- [x] 19-01-PLAN.md — Remove `Front of Card` from normal APKG, CSV, TSV, and template references.
- [x] 19-02-PLAN.md — Make normal `sentence_audio` render beside `Example Sentence` responsively.
- [x] 19-03-PLAN.md — Add integrated normal export evidence and highlight/phonetics isolation checks.
**UI hint**: yes

### Phase 20: Word Audio Integrity Gate

**Goal**: User only receives exported cards whose `word_audio` matches the card `Word`, or a clear validation block when it cannot be fixed.  
**Depends on**: Phase 19  
**Requirements**: AUD-01, AUD-02  
**Success Criteria** (what must be TRUE):
  1. User can detect cards where the `word_audio` synthesis text or stored manifest does not exactly match the card `Word`.
  2. User receives repaired or regenerated `word_audio` when a mismatch can be safely corrected.
  3. User receives a clear validation error that blocks export when a word-audio mismatch cannot be repaired.
**Plans**: 3 plans
Plans:
- [x] 20-01-PLAN.md — Define exact word-audio integrity checks for synthesis text and stored manifests.
- [x] 20-02-PLAN.md — Regenerate mismatched reusable word audio during audio generation.
- [x] 20-03-PLAN.md — Block unrepairable word-audio mismatches during assembly and export.

### Phase 21: Validation Fixtures and Milestone Evidence

**Goal**: User receives repeatable validation and evidence that the normalized issue catalog is covered and existing deck modes remain safe.  
**Depends on**: Phase 20  
**Requirements**: VAL-01, VAL-02, VAL-03  
**Success Criteria** (what must be TRUE):
  1. User can run validators for IPA word repetition, banned Definition patterns, Translation/example mismatch, `word_audio`/`Word` mismatch, and dangling template fields.
  2. User gets regression fixtures covering the normalized examples from `card_issues_normalized.md`.
  3. User receives final milestone evidence proving audit behavior, text corrections, normal-card export contract, and word-audio integrity.
  4. User receives regression evidence that frequency, custom word-list, highlight, and phonetics deck behavior remains unaffected outside the intended normal-card changes.
**Plans**: 3 plans
Plans:
- [x] 21-01-PLAN.md — Create shared validators for all normalized v1.3 issue categories.
- [ ] 21-02-PLAN.md — Convert `card_issues_normalized.md` examples into executable regression fixtures.
- [ ] 21-03-PLAN.md — Add final milestone evidence and existing-mode regression proof.
**UI hint**: yes

## Progress

| Milestone | Phases | Plans | Status | Shipped |
|-----------|--------|-------|--------|---------|
| v1.0 MVP | 1-7 | 34/34 | Complete | 2026-04-29 |
| v1.1 Card Quality Refresh | 8 | 4/4 | Complete | 2026-05-02 |
| v1.2 Kindle Highlights and Template Refresh | 9-16 | 29/29 | Complete | 2026-05-08 |
| v1.3 Card Quality Remediation and Deck Validation | 17-21 | TBD | Not started | - |

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 17. Deck Quality Audit and Issue Reports | 3/3 | Complete   | 2026-05-12 |
| 18. Text Field Remediation | 3/3 | Complete    | 2026-05-13 |
| 19. Normal Card Export and Responsive Template | 3/3 | Complete    | 2026-05-13 |
| 20. Word Audio Integrity Gate | 3/3 | Complete    | 2026-05-13 |
| 21. Validation Fixtures and Milestone Evidence | 1/3 | In Progress|  |

## Coverage

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUDIT-01 | Phase 17 | Pending |
| AUDIT-02 | Phase 17 | Pending |
| AUDIT-03 | Phase 17 | Pending |
| IPA-01 | Phase 18 | Pending |
| DEF-01 | Phase 18 | Pending |
| DEF-02 | Phase 18 | Pending |
| TRNS-01 | Phase 18 | Pending |
| TMPL-01 | Phase 19 | Complete |
| TMPL-02 | Phase 19 | Complete |
| TMPL-03 | Phase 19 | Complete |
| AUD-01 | Phase 20 | Pending |
| AUD-02 | Phase 20 | Pending |
| VAL-01 | Phase 21 | Complete |
| VAL-02 | Phase 21 | Pending |
| VAL-03 | Phase 21 | Pending |

Coverage: 15/15 v1.3 requirements mapped exactly once.
