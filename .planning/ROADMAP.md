# Roadmap: Multilang Anki Card Generator

## Overview

Multilang v1 should ship as a trust-first Python batch pipeline that turns either curated frequency inputs or user word lists into reviewable, audio-backed, Anki-safe cards. The roadmap therefore moves from job orchestration and grounded lexical inputs into text quality, then audio, then final export hardening so the product earns trust at the card boundary instead of only generating broad but unreliable output.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Job Orchestration & Recovery** - Start supported-language jobs with visible progress, resumability, and duplicate-safe reruns.
- [ ] **Phase 2: Input Decks & Lexical Grounding** - Turn frequency sources or custom word lists into normalized lexical card records.
- [ ] **Phase 3: Sentence Quality & Review Loop** - Produce trustworthy example sentences and translations with reviewable regeneration.
- [ ] **Phase 4: Audio Synthesis** - Add reliable word and sentence audio with Azure-first fallback handling.
- [ ] **Phase 5: Anki-Safe Export Contract** - Freeze the card schema and export clean decks that import into Anki without repair.

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
**Plans**: TBD

### Phase 2: Input Decks & Lexical Grounding
**Goal**: Users can generate grounded card candidates from either built-in frequency decks or their own word lists.
**Depends on**: Phase 1
**Requirements**: DECK-02, DECK-03, LEX-01, LEX-02, LEX-03
**Success Criteria** (what must be TRUE):
  1. User can generate a 3-level frequency deck with 1000 cards per level for the selected language.
  2. User can submit a custom word list and receive generated card candidates for those words instead of the built-in frequency deck.
  3. User receives every candidate card with a normalized base word and frequency rank where applicable.
  4. User receives IPA and definitions in one consistent deck-wide format.
**Plans**: TBD

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
**Plans**: TBD

### Phase 4: Audio Synthesis
**Goal**: Users receive playable pronunciation audio for both the headword and the example sentence.
**Depends on**: Phase 3
**Requirements**: AUDI-01, AUDI-02
**Success Criteria** (what must be TRUE):
  1. User receives `word_audio` for generated cards using Azure TTS or a documented fallback when a preferred voice is unavailable.
  2. User receives `sentence_audio` for generated cards using Azure TTS or a documented fallback when a preferred voice is unavailable.
  3. User can rerun interrupted jobs without silently losing already generated audio assets.
**Plans**: TBD

### Phase 5: Anki-Safe Export Contract
**Goal**: Users receive complete cards in a fixed schema and can export them into Anki safely.
**Depends on**: Phase 4
**Requirements**: CARD-01, CARD-02, EXPT-01, EXPT-02
**Success Criteria** (what must be TRUE):
  1. User receives every generated card in the fixed schema with the requested fields in a consistent order and format.
  2. User receives `Image` as an empty field on every exported card.
  3. User can export an `.apkg` deck that imports into Anki without manual field remapping.
  4. User can export the same cards as a UTF-8-safe CSV or TSV fallback.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Job Orchestration & Recovery | 0/TBD | Not started | - |
| 2. Input Decks & Lexical Grounding | 0/TBD | Not started | - |
| 3. Sentence Quality & Review Loop | 0/TBD | Not started | - |
| 4. Audio Synthesis | 0/TBD | Not started | - |
| 5. Anki-Safe Export Contract | 0/TBD | Not started | - |
