# Roadmap: Multilang Anki Card Generator

## Milestones

- [x] **v1.0 MVP** - Phases 1-7 shipped 2026-04-29.
- [x] **v1.1 Card Quality Refresh** - Phase 08 completed 2026-05-02.
- [x] **v1.2 Kindle Highlights and Template Refresh** - Phases 09-16 completed 2026-05-08.
- [x] **v1.3 Card Quality Remediation and Deck Validation** - Phases 17-21 shipped 2026-05-16.
- [x] **v2.0 Classical Latin MVP** - Phases 22-28 shipped 2026-06-08.
- [x] **v2.1 Latin Google TTS Finalization** - Phase 29 verified 2026-06-22.
- [ ] **v3.0 Korean Learning System** - Phases 30-34 in progress.

## Current Focus

Plan and execute v3.0 Korean Learning System after the active Mandarin quick-task changes on shared language/export surfaces are completed or reconciled.

## Archived Phases

<details>
<summary>v2.0-v2.1 Classical Latin (Phases 22-29) - COMPLETED 2026-06-22</summary>

- [x] Phase 22: Latin Mode Contracts and Isolation
- [x] Phase 23: Frozen 50-Card Source Pack and Sentence Sequence
- [x] Phase 24: Morphology Evidence and Gramatica Gate
- [x] Phase 25: Latin Review Gates and Curated Records
- [x] Phase 26: Portuguese Translation Quality
- [x] Phase 27: Latin Audio Policy and Integrity
- [x] Phase 28: Latin Export and Milestone Evidence
- [x] Phase 29: Latin Google TTS Finalization

Archives:
- `.planning/milestones/v2.0-ROADMAP.md`
- `.planning/milestones/v2.1-ROADMAP.md`
- `.planning/milestones/v2.0-REQUIREMENTS.md`
- `.planning/milestones/v2.1-REQUIREMENTS.md`

</details>

## v3.0 Korean Learning System

### Phase Overview

- [x] **Phase 30: Korean Contracts and Morphology** — [KMODE-01, KMODE-02, KNLP-01, KNLP-02]
- [-] **Phase 31: Hangul and Pronunciation i+1** — [KHAN-01, KHAN-02, KPRO-01, KPRO-02]
- [ ] **Phase 32: Frequency, Portuguese Text, and Audio** — [KFREQ-01, KFREQ-02, KFREQ-03, KTXT-01, KAUD-01]
- [ ] **Phase 33: Grammar and Personal Sources** — [KGRAM-01, KGRAM-02, KPERS-01, KPERS-02]
- [ ] **Phase 34: Export, Review, and Evidence** — [KEXP-01, KEXP-02, KQA-01, KQA-02]

### Phase 30: Korean Contracts and Morphology
**Status**: [x] Not started
**Goal**: Users can select Korean throughout the modern pipeline and receive deterministic NFC-normalized, morphology-aware processing without regressing existing modes.
**Depends on**: Active Mandarin quick task 027 completed or shared worktree reconciled.
**Requirements**: KMODE-01, KMODE-02, KNLP-01, KNLP-02
**Success Criteria**:
1. `ko` is the only public/internal Korean identity; `ko-KR` appears only in locale/provider contracts.
2. Frequency, word-list, and highlights route through a complete Korean language profile.
3. Kiwi-backed analysis resolves representative nouns, particles, regular/irregular predicates, and compound predicates.
4. Target-in-sentence validation uses morpheme signatures and fails closed when analysis is unavailable or ambiguous.
5. Existing language, source, template, audio, persistence, and export regressions remain green.

### Phase 31: Hangul and Pronunciation i+1
**Status**: [-] Not started
**Goal**: Users receive reviewed Hangul and Korean pronunciation foundation decks with explicit curriculum-i+1 sequencing.
**Depends on**: Phase 30
**Requirements**: KHAN-01, KHAN-02, KPRO-01, KPRO-02
**Success Criteria**:
1. Hangul uses a Korean note type derived from the kana layout with jamo, blocks, strokes, mnemonics, and approved media.
2. Pronunciation uses the shared phoneme layout with Korean-specific IDs and complete spelling/sound/word/sentence fields.
3. Every strict card records prerequisites, observed concepts, and exactly one target unknown after bootstrap.
4. The pronunciation sequence covers onset contrasts, batchim, connected-speech rules, alternations, and contractions in dependency order.
5. Jamo and phonological-rule audio cannot become approved through unreviewed raw-glyph TTS.

### Phase 32: Frequency, Portuguese Text, and Audio
**Status**: [ ] Not started
**Goal**: Users receive three license-approved 1000-card Korean frequency subdecks with natural standard-Seoul examples, Portuguese text, and approved Azure audio.
**Depends on**: Phase 31
**Requirements**: KFREQ-01, KFREQ-02, KFREQ-03, KTXT-01, KAUD-01
**Success Criteria**:
1. A documented frequency-source and redistribution decision precedes any committed 3000-entry asset.
2. The frozen inventory contains exactly 3000 unique lemma/sense entries, 1000 per real Anki subdeck, with full provenance.
3. Particles, endings, inflectional duplicates, script noise, and unresolved homographs do not enter the lexical ranks silently.
4. Examples are natural standard-Seoul Korean with adaptive-i+1 evidence and context-matched Portuguese glosses/translations.
5. An exact live-discovered Azure `ko-KR` voice produces approved, hash-aligned word and sentence audio with no silent fallback.

### Phase 33: Grammar and Personal Sources
**Status**: [ ] Not started
**Goal**: Users receive an i+1 Particles & Endings curriculum and morphology-aware Korean cards from personal word lists and reading highlights.
**Depends on**: Phase 32
**Requirements**: KGRAM-01, KGRAM-02, KPERS-01, KPERS-02
**Success Criteria**:
1. Particles, endings, speech levels, connectors, and irregular paradigms follow a reviewed dependency sequence.
2. Every strict grammar card introduces one form-function-register concept using already-known prerequisites.
3. Custom input preserves submitted form, resolved lemma/sense/POS, and user order, with bridge/defer handling for ambiguity.
4. Highlight extraction preserves valid one-syllable words and resolves attached morphology before deduplication.
5. Source excerpts, generated microexamples, redacted context, and private provenance remain explicitly separated.

### Phase 34: Export, Review, and Evidence
**Status**: [ ] Not started
**Goal**: Users can export all Korean deck families with stable contracts, approved content/media, and evidence that Korean and existing modes work end to end.
**Depends on**: Phase 33
**Requirements**: KEXP-01, KEXP-02, KQA-01, KQA-02
**Success Criteria**:
1. Hangul, pronunciation, frequency, grammar, custom, and highlight rows export to APKG, CSV, and TSV with stable identities and fields.
2. APKG frequency levels are real subdecks with resolvable approved media; all applicable card types retain blank `Image`.
3. Korean font stacks and responsive layouts receive static contract checks plus observed Anki Desktop/mobile review.
4. Review gates block unresolved morphology, false i+1, wrong sense/register, unapproved audio, license uncertainty, and text/media drift.
5. Scanner-readable milestone evidence maps every v3.0 requirement exactly once and proves existing modes did not regress.

## Coverage

All 21 v3.0 requirements are assigned exactly once across Phases 30-34.

---
*v3.0 roadmap initialized: 2026-07-20*
