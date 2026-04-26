# Roadmap: Multilang Anki Card Generator

## Overview

Multilang v1 should ship as a trust-first Python batch pipeline that turns either curated frequency inputs or user word lists into reviewable, audio-backed, Anki-safe cards. The roadmap therefore moves from job orchestration and grounded lexical inputs into text quality, then audio, then final export hardening so the product earns trust at the card boundary instead of only generating broad but unreliable output.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Job Orchestration & Recovery** - Start supported-language jobs with visible progress, resumability, and duplicate-safe reruns. _(gap closure completed after 6/6 plans)_
- [x] **Phase 2: Input Decks & Lexical Grounding** - Turn frequency sources or custom word lists into normalized lexical card records.
- [x] **Phase 3: Sentence Quality & Review Loop** - Produce trustworthy example sentences and translations with reviewable regeneration.
- [x] **Phase 4: Audio Synthesis** - Add reliable word and sentence audio with Azure-first fallback handling. _(gap closure completed after 5/5 plans)_
- [ ] **Phase 5: Anki-Safe Export Contract** - Freeze the card schema, template behavior, and export clean decks that import into Anki without repair.

## Phase Details

### Phase 1: Job Orchestration & Recovery
**Goal**: Users can start a generation run for a supported language and trust the job lifecycle even when runs fail or are repeated.
**Depends on**: Nothing (first phase)
**Requirements**: DECK-01, JOB-01, JOB-02, JOB-03
**Success Criteria** (what must be TRUE):
  1. User can choose one of the 7 supported target languages before a job starts.
  2. User can see batch-level progress and failures while generation is running.
  3. User can resume an interrupted generation run without losing cards that already completed.
  4. User can rerun the same input without silent duplicate card creation.
**Plans**: 6 plans

Plans:
- [x] 01-01-PLAN.md — Bootstrap the Python project shell and typed job contracts.
- [x] 01-02-PLAN.md — Add persisted job/item state and duplicate-safe repository rules.
- [x] 01-03-PLAN.md — Implement the single-command CLI with start, resume, and rerun orchestration.
- [x] 01-04-PLAN.md — Add progress rendering, bounded retry behavior, and lifecycle smoke coverage.
- [x] 01-05-PLAN.md — Restore repository-backed runtime bootstrap for the shipped CLI path.
- [x] 01-06-PLAN.md — Verify shipped-app progress, resume, rerun, and lifecycle summary behavior.

**Verification:** passed on 2026-04-19 after gap-closure Plans 01-05 and 01-06 restored the shipped CLI runtime path and verified visible progress, resume, and duplicate-safe reruns.

### Phase 2: Input Decks & Lexical Grounding
**Goal**: Users can generate grounded card candidates from either built-in frequency decks or their own word lists.
**Depends on**: Phase 1
**Requirements**: DECK-02, DECK-03, LEX-01, LEX-02, LEX-03
**Success Criteria** (what must be TRUE):
  1. User can generate a 3-level frequency deck with 1000 cards per level for the selected language.
  2. User can submit a custom word list and receive generated card candidates for those words instead of the built-in frequency deck.
  3. User receives every candidate card with a normalized base word and frequency rank where applicable.
  4. User receives IPA and definitions in one consistent deck-wide format.
**Plans**: 5 plans

Plans:
- [x] 02-01-PLAN.md — Define lexical candidate contracts, persistence, and the Phase 2 schema migration.
- [x] 02-02-PLAN.md — Build the deterministic `wordfreq`-based frequency deck curation and level selector.
- [x] 02-03-PLAN.md — Implement plain-text word-list parsing, cached Kaikki lookup, and trust-first lexical grounding.
- [x] 02-04-PLAN.md — Wire the lexical ingestion pipeline into the shipped CLI/runtime path with integration coverage.
- [x] 02-05-PLAN.md — Close the clean-runtime lexical-cache bootstrap gap on the shipped `multilang generate` path.

**Verification:** Plans 02-01 through 02-04 passed on 2026-04-20 with lexical contract tests, repository persistence tests, disposable SQLite schema verification, deterministic frequency deck service coverage, fixture-backed Kaikki lookup tests, trust-first grounding coverage, and shipped-path lexical-ingestion integration tests. Gap-closure Plan 02-05 completed on 2026-04-21, and Phase 2 re-verification passed on 2026-04-21.

### Phase 3: Sentence Quality & Review Loop
**Goal**: Users can trust the meaning-bearing text on each card and repair weak cards without rerunning the full batch.
**Depends on**: Phase 2
**Requirements**: TEXT-01, TEXT-02, TEXT-03, TEXT-04, TEXT-05
**Success Criteria** (what must be TRUE):
  1. User receives an example sentence that contains the target word and matches the intended meaning of the card.
  2. User receives example sentences that pass the project's quality rules for length, naturalness, and readability.
  3. User receives a translation that matches the displayed example sentence.
  4. User can review low-confidence cards before final export.
  5. User can regenerate a flagged card from the review flow without rerunning the full batch.
**Plans**: 5 plans

Plans:
- [x] 03-01-PLAN.md — Define text-quality contracts, persistence, and the Phase 3 schema migration.
- [x] 03-02-PLAN.md — Add sentence-generation and sentence-translation adapter/service boundaries.
- [x] 03-03-PLAN.md — Implement validation, confidence scoring, and the one-repair text pipeline.
- [x] 03-04-PLAN.md — Add the CLI-first review queue and report flow on `multilang generate`.
- [x] 03-05-PLAN.md — Wire item-level regeneration and shipped-path runtime verification.

**Verification:** Phase 3 implementation completed on 2026-04-21 across Plans 03-01 through 03-05. Automated re-verification, review-fix closure, and recorded human UAT/report-usability sign-off closed the remaining gaps on 2026-04-21.

### Phase 4: Audio Synthesis
**Goal**: Users receive playable pronunciation audio for both the headword and the example sentence.
**Depends on**: Phase 3
**Requirements**: AUDI-01, AUDI-02
**Success Criteria** (what must be TRUE):
  1. User receives `word_audio` for generated cards using Azure TTS or a documented fallback when a preferred voice is unavailable.
  2. User receives `sentence_audio` for generated cards using Azure TTS or a documented fallback when a preferred voice is unavailable.
  3. User can rerun interrupted jobs without silently losing already generated audio assets.
**Plans**: 5 plans

Plans:
- [x] 04-01-PLAN.md — Define audio contracts, the Azure voice registry, and typed speech settings.
- [x] 04-02-PLAN.md — Add audio persistence, repository reuse rules, and the Phase 4 schema migration.
- [x] 04-03-PLAN.md — Implement Azure-first synthesis, TTS normalization, and media-integrity validation.
- [x] 04-04-PLAN.md — Wire shipped-path audio generation, reuse, and CLI/integration verification.
- [x] 04-05-PLAN.md — Close the shipped runtime Azure adapter and playable-media verification gaps.

**Verification:** Gap-closure Plan 04-05 completed on 2026-04-24 with a real Azure Speech adapter, shipped-path runtime wiring, and passing fallback/reuse/playable-media coverage on the default `multilang generate` path. Human verification of live Azure synthesis and playback quality was later recorded on 2026-04-26, closing Phase 4 completely.

### Phase 5: Anki-Safe Export Contract
**Goal**: Users receive complete cards in a fixed schema with the expected template behavior and can export them into Anki safely.
**Depends on**: Phase 4
**Requirements**: CARD-01, CARD-02, CARD-03, CARD-04, EXPT-01, EXPT-02, EXPT-03
**Success Criteria** (what must be TRUE):
  1. User receives every generated card in the fixed schema with the requested fields in a consistent order and format.
  2. User receives `Image` as an empty field on every exported card, and `Translation` stays hidden on the front and is revealed on the back according to the provided template.
  3. User receives `Definitions` as one template-compatible field value, with multiple senses rendered inside the same field using `<br>` separators instead of nested list markup.
  4. User can export an `.apkg` deck that imports into Anki without manual field remapping.
  5. User can export the same cards as a UTF-8-safe CSV or TSV fallback.
  6. User receives packaged audio media and Anki-compatible sound references that play correctly after import.
**Plans**: 5 plans

Plans:
- [x] 05-01-PLAN.md — Freeze the export contract, persistence, and Phase 5 schema migration.
- [ ] 05-02-PLAN.md — Assemble fixed-schema export cards and UTF-8-safe CSV/TSV fallback bundles.
- [ ] 05-03-PLAN.md — Add `genanki` packaging with stable note identity and bundled media.
- [ ] 05-04-PLAN.md — Wire the shipped CLI/runtime export flow and end-to-end artifact tests.
- [ ] 05-05-PLAN.md — Verify real Anki import behavior, translation reveal rules, and audio playback.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Job Orchestration & Recovery | 6/6 | Complete | 2026-04-19 |
| 2. Input Decks & Lexical Grounding | 5/5 | Complete | 2026-04-21 |
| 3. Sentence Quality & Review Loop | 5/5 | Complete | 2026-04-21 |
| 4. Audio Synthesis | 5/5 | Complete | 2026-04-26 |
| 5. Anki-Safe Export Contract | 1/5 | In progress | 2026-04-26 |
