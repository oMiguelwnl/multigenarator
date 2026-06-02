# Roadmap: Multilang Anki Card Generator

## Milestones

- [x] **v1.0 MVP** - Phases 1-7 shipped 2026-04-29. Archive: [v1.0-ROADMAP.md](./milestones/v1.0-ROADMAP.md). Requirements: [v1.0-REQUIREMENTS.md](./milestones/v1.0-REQUIREMENTS.md).
- [x] **v1.1 Card Quality Refresh** - Phase 08 completed 2026-05-02 with audio prominence, AI-generated pronunciation, spoken-form display, and normal deck CSS refresh from `total.md`.
- [x] **v1.2 Kindle Highlights and Template Refresh** - Phases 09-16 completed 2026-05-08 with local Kindle highlights, highlight export, WebDAV fetch, phonetics template refresh, and end-to-end evidence.
- [x] **v1.3 Card Quality Remediation and Deck Validation** - Phases 17-21 shipped 2026-05-16. Archive: [v1.3-ROADMAP.md](./milestones/v1.3-ROADMAP.md). Requirements: [v1.3-REQUIREMENTS.md](./milestones/v1.3-REQUIREMENTS.md).
- [ ] **v2.0 Classical Latin MVP** - Phases 22-28 planned for a reviewed 50-card Classical Latin deck; scale beyond 50 cards is deferred.

## Current Focus

Plan and execute v2.0 Classical Latin MVP starting at Phase 22 without resetting phase numbers.

## Overview

v2.0 adds a separate Classical Latin generation path that produces a reviewed, reproducible 50-card MVP rather than extending the modern-language frequency deck flow. The milestone starts by isolating Latin contracts and source-profile behavior, then freezes the source/frequency/sentence assets, validates morphology and short `Gramatica` output, gates curated records through review, validates Portuguese text, approves word and sentence audio, and finishes with dedicated Latin `.apkg`/CSV/TSV export plus scanner-readable evidence. Full 300-card, 1000-card, and 3000-card Latin scale remains explicitly deferred until the 50-card contract is proven.

## Phases

**Phase Numbering:** Continuous from v1.3; v2.0 starts at Phase 22.

- [x] **Phase 22: Latin Mode Contracts and Isolation** - Users can start Classical Latin MVP generation through isolated contracts without breaking existing deck modes. (completed 2026-06-01)
- [x] **Phase 23: Frozen 50-Card Source Pack and Sentence Sequence** - Users receive a reproducible first-50 Latin manifest with licensed sources, lemma frequency, and didactic ordering. (completed 2026-06-01)
- [ ] **Phase 24: Morphology Evidence and Gramatica Gate** - Users receive reviewed Latin morphology and short standardized `Gramatica` notes that block unresolved ambiguity.
- [ ] **Phase 25: Latin Review Gates and Curated Records** - Users can approve, reject, and inspect curated Latin records before learner-ready export.
- [ ] **Phase 26: Portuguese Translation Quality** - Users receive Portuguese lemma and sentence translations that match the chosen Latin context.
- [ ] **Phase 27: Latin Audio Policy and Integrity** - Users receive approved playable Latin word and sentence audio with provider metadata and exact-text checks.
- [ ] **Phase 28: Latin Export and Milestone Evidence** - Users can export approved Latin MVP cards and inspect evidence proving Latin coverage and existing-mode safety.

## Phase Details

### Phase 22: Latin Mode Contracts and Isolation
**Goal**: Users can generate Classical Latin MVP data through a separate `la` / Classical Latin path while existing modern-language, custom, highlight, phonetics, review, audio, and export flows remain operational.
**Depends on**: Phase 21
**Requirements**: MODE-01, MODE-02, MODE-03
**Success Criteria** (what must be TRUE):
  1. User can choose a Classical Latin MVP path that does not route through the modern-language frequency generator.
  2. User receives Latin deck metadata showing `language_code=la`, Classical Latin variant, MVP source pack version, and explicit 50-card scope.
  3. Existing frequency, custom word-list, highlight, phonetics, review, audio, and export flows still run through their prior profiles after Latin mode is introduced.
  4. Latin-specific contracts and enums exist without mutating shipped normal, highlight, or phonetics note contracts.
**Plans:** 3/3 plans complete
Plans:
- [x] 22-01-PLAN.md — Define isolated Classical Latin contracts and source profile.
- [x] 22-02-PLAN.md — Add separate Latin MVP start service and CLI command.
- [x] 22-03-PLAN.md — Add focused mode-isolation regression evidence.

### Phase 23: Frozen 50-Card Source Pack and Sentence Sequence
**Goal**: Users receive a reproducible 50-card Classical Latin MVP source pack ordered by lemma frequency and Rafael Falcon-style didactic suitability, with every sentence traceable and license-gated.
**Depends on**: Phase 22
**Requirements**: FREQ-01, FREQ-02, FREQ-03, SRC-01, SRC-02, SENT-01, SENT-02
**Success Criteria** (what must be TRUE):
  1. User can inspect a frozen 50-card MVP manifest instead of an unbounded or full 3000-card Latin deck.
  2. Every MVP candidate shows lemma, frequency rank, frequency source, source pack version, and inclusion/defer/replacement rationale.
  3. Every displayed Latin sentence includes provenance metadata with source type, citation or work reference when available, URL or local source identifier, and license note.
  4. User can tell whether each sentence is original Classical Latin, adapted didactic Latin, or a reference example, with adapted text never presented as an original citation.
  5. The first-50 sequence favors clearer early reading contexts and defers overly complex poetic or ambiguous constructions while confirming the displayed target word appears in the sentence.
**Plans:** 4/4 plans complete
Plans:
- [x] 23-01-PLAN.md — Define Latin source-pack contracts and loader validation.
- [x] 23-02-PLAN.md — Commit the frozen 50-entry source/frequency/sentence manifest.
- [x] 23-03-PLAN.md — Wire the Latin MVP service and CLI to the frozen manifest.
- [x] 23-04-PLAN.md — Add scanner-readable Phase 23 evidence and isolation checks.

### Phase 24: Morphology Evidence and Gramatica Gate
**Goal**: Users receive Latin cards whose target word has resolved morphology evidence and a short standardized Portuguese-facing `Gramatica` note using approved abbreviations and Latin case labels.
**Depends on**: Phase 23
**Requirements**: GRAM-01, GRAM-02, GRAM-03, GRAM-04
**Success Criteria** (what must be TRUE):
  1. Every MVP card records morphology evidence for lemma, part of speech, case or verbal analysis where applicable, number, and syntactic function.
  2. Every MVP card has a concise `Gramatica` field using approved short abbreviations such as `subst`, `adj`, `v`, `sg`, `pl`, `Suj`, `OD`, and `OI`.
  3. Final grammar labels use `Genitivus` plus the required case vocabulary: `Nominativus`, `Vocativus`, `Accusativus`, `Genitivus`, `Dativus`, and `Ablativus`.
  4. Cards with ambiguous or uncertain morphology cannot become learner-ready until the final grammar analysis is reviewed and resolved.
**Plans:** 4 plans
Plans:
- [ ] 24-01-PLAN.md — Define fail-closed morphology evidence and `Gramatica` validation contracts.
- [ ] 24-02-PLAN.md — Add approved morphology evidence and standardized `Gramatica` to all 50 frozen Latin MVP entries.
- [ ] 24-03-PLAN.md — Expose grammar readiness through the Latin MVP service and CLI summary.
- [ ] 24-04-PLAN.md — Add scanner-readable Phase 24 grammar evidence and no-scope-creep checks.

### Phase 25: Latin Review Gates and Curated Records
**Goal**: Users can manage Classical Latin MVP cards through review states that protect source, translation, grammar, and audio readiness before final export.
**Depends on**: Phase 24
**Requirements**: REV-01, REV-02, REV-03
**Success Criteria** (what must be TRUE):
  1. User can mark Latin MVP records as `needs_review`, `approved`, or `rejected` for source, translation, grammar, and audio readiness.
  2. User can export learner-ready Latin MVP cards only when all required review gates are `approved`.
  3. User can inspect rejection, replacement, and uncertainty reasons while preserving original source and frequency provenance.
  4. Approved curated fields are protected from accidental provider or regeneration overwrites.
**Plans:** 4 plans
Plans:
- [ ] 25-01-PLAN.md — Define Latin review gate contracts and export-readiness validation.
- [ ] 25-02-PLAN.md — Commit loader-validated 50-record Latin MVP curation asset.
- [ ] 25-03-PLAN.md — Add CLI inspection/update commands with approved-field overwrite protection.
- [ ] 25-04-PLAN.md — Add scanner-readable review-gate evidence and phase-boundary checks.

### Phase 26: Portuguese Translation Quality
**Goal**: Users receive Portuguese learner-facing text that matches the selected Latin sense and sentence context without English leakage or dictionary-only mismatches.
**Depends on**: Phase 25
**Requirements**: PT-01, PT-02, PT-03
**Success Criteria** (what must be TRUE):
  1. Every MVP card has a Portuguese short translation for the target lemma or displayed Latin word that matches the selected sentence sense.
  2. Every MVP card has a Portuguese sentence translation corresponding to the chosen Latin sentence and target-word context.
  3. Portuguese learner-facing text is reviewed or validated to prevent English leakage, context-missing dictionary glosses, and translations that contradict the Latin sentence.
  4. User can see translation QA evidence before cards are approved for learner-ready export.
**Plans**: TBD

### Phase 27: Latin Audio Policy and Integrity
**Goal**: Users receive approved playable word and sentence audio for every final Latin MVP card, with provider metadata, fallback reasons, and export-blocking integrity checks.
**Depends on**: Phase 26
**Requirements**: AUD-01, AUD-02, AUD-03, AUD-04
**Success Criteria** (what must be TRUE):
  1. User can compare candidate Latin TTS samples for representative words and sentences before the final MVP audio policy is locked.
  2. Every final exported Latin MVP card has approved playable word audio and sentence audio; missing, failed, or unapproved audio blocks learner-ready export.
  3. Every Latin audio artifact records provider, provider version, voice, pronunciation policy, generated text, text hash, audio kind, playback review status, and fallback reason when applicable.
  4. Export is blocked when persisted audio text does not match the exported target word or Latin sentence.
**Plans**: TBD

### Phase 28: Latin Export and Milestone Evidence
**Goal**: Users can export approved Classical Latin MVP cards to `.apkg`, CSV, and TSV with stable Latin fields, packaged media, source/privacy safeguards, and scanner-readable evidence for all v2.0 requirements.
**Depends on**: Phase 27
**Requirements**: EXP-01, EXP-02, EXP-03, EVID-01, EVID-02, EVID-03
**Success Criteria** (what must be TRUE):
  1. User receives a dedicated Latin Anki note type/template with stable field order for displayed Latin word, Latin sentence, lemma, Portuguese translations, `Gramatica`, source, word audio, sentence audio, and blank `Image`.
  2. Latin exports omit a separate learner-facing `Classe` field while preserving part-of-speech metadata internally or inside `Gramatica`.
  3. User can export approved Latin MVP cards to `.apkg`, CSV, and TSV with packaged media references plus Anki import/playback evidence.
  4. User receives scanner-readable evidence proving all 30 v2.0 requirements are covered by implementation, validation, or explicit review artifacts.
  5. Evidence proves source/license metadata and committed artifacts do not leak private paths, raw provider secrets, unapproved source material, or existing deck-mode regressions.
**Plans**: TBD

## Progress

**Execution Order:** Phase 22 → Phase 23 → Phase 24 → Phase 25 → Phase 26 → Phase 27 → Phase 28

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 22. Latin Mode Contracts and Isolation | v2.0 | 3/3 | Complete   | 2026-06-01 |
| 23. Frozen 50-Card Source Pack and Sentence Sequence | v2.0 | 4/4 | Complete   | 2026-06-01 |
| 24. Morphology Evidence and Gramatica Gate | v2.0 | 0/TBD | Not started | - |
| 25. Latin Review Gates and Curated Records | v2.0 | 0/TBD | Not started | - |
| 26. Portuguese Translation Quality | v2.0 | 0/TBD | Not started | - |
| 27. Latin Audio Policy and Integrity | v2.0 | 0/TBD | Not started | - |
| 28. Latin Export and Milestone Evidence | v2.0 | 0/TBD | Not started | - |

## Coverage

| Requirement | Phase |
|-------------|-------|
| MODE-01 | Phase 22 |
| MODE-02 | Phase 22 |
| MODE-03 | Phase 22 |
| FREQ-01 | Phase 23 |
| FREQ-02 | Phase 23 |
| FREQ-03 | Phase 23 |
| SRC-01 | Phase 23 |
| SRC-02 | Phase 23 |
| SENT-01 | Phase 23 |
| SENT-02 | Phase 23 |
| GRAM-01 | Phase 24 |
| GRAM-02 | Phase 24 |
| GRAM-03 | Phase 24 |
| GRAM-04 | Phase 24 |
| PT-01 | Phase 26 |
| PT-02 | Phase 26 |
| PT-03 | Phase 26 |
| REV-01 | Phase 25 |
| REV-02 | Phase 25 |
| REV-03 | Phase 25 |
| AUD-01 | Phase 27 |
| AUD-02 | Phase 27 |
| AUD-03 | Phase 27 |
| AUD-04 | Phase 27 |
| EXP-01 | Phase 28 |
| EXP-02 | Phase 28 |
| EXP-03 | Phase 28 |
| EVID-01 | Phase 28 |
| EVID-02 | Phase 28 |
| EVID-03 | Phase 28 |

**Coverage status:** 30/30 v2.0 requirements mapped exactly once. No orphaned requirements. No duplicate mappings.

**Deferred beyond v2.0:** Latin scale beyond 50 cards, including 300-card pilot, full 3-level 3000-card Latin deck, and project-owned corpus-frequency engine.
