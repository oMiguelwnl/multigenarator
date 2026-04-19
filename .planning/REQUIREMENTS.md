# Requirements: Multilang Anki Card Generator

**Defined:** 2026-04-18
**Core Value:** Generate reliable, high-quality Anki cards for frequent vocabulary in the chosen language so the learner can study real words with accurate definitions, examples, translations, and audio.

## v1 Requirements

### Deck Scope

- [x] **DECK-01**: User can choose one of these target languages before generation starts: Portuguese, Spanish, English, French, German, Russian, or Dutch. _(Plan 01-01 foundation)_
- [ ] **DECK-02**: User can generate a frequency deck for the selected language with 3 levels of 1000 cards each.
- [ ] **DECK-03**: User can generate cards from a custom user-provided word list instead of the built-in frequency deck.

### Card Contract

- [ ] **CARD-01**: User receives every generated card with these fields in a fixed schema: `SortIndex`, `word`, `Front of Card`, `IPA`, `Definitions`, `Example Sentence`, `Translation`, `word_audio`, `sentence_audio`, and `Image`.
- [ ] **CARD-02**: User receives `Image` as an empty field in every generated card so images can be added manually later.
- [ ] **CARD-03**: User sees `Translation` hidden on the front of the Anki card and revealed on the back, matching the provided card template behavior.
- [ ] **CARD-04**: User receives `Definitions` as one template-compatible field value; if multiple senses are present they are separated with `<br>` inside the same field, not nested `<ul>` or `<li>` markup.

### Lexical Enrichment

- [ ] **LEX-01**: User receives a normalized base word and frequency rank for every generated card.
- [ ] **LEX-02**: User receives IPA for every generated card in one consistent display format.
- [ ] **LEX-03**: User receives definitions that follow one deck-wide template so meaning fields stay consistent across cards.

### Text Quality

- [ ] **TEXT-01**: User receives an example sentence that contains the target word and matches the intended meaning of the card.
- [ ] **TEXT-02**: User receives an example sentence that passes project quality rules for length, naturalness, and readability.
- [ ] **TEXT-03**: User receives a translation that matches the displayed example sentence rather than only the isolated headword meaning.
- [ ] **TEXT-04**: User can review flagged low-confidence cards before final export.
- [ ] **TEXT-05**: User can regenerate a flagged card from the review workflow without rerunning the full batch.

### Audio

- [ ] **AUDI-01**: User receives `word_audio` for the target word using Azure TTS or a documented fallback when the preferred voice is unavailable.
- [ ] **AUDI-02**: User receives `sentence_audio` for the example sentence using Azure TTS or a documented fallback when the preferred voice is unavailable.

### Export and Jobs

- [ ] **EXPT-01**: User can export generated cards as an `.apkg` deck that imports into Anki without manual field remapping.
- [ ] **EXPT-02**: User can export the same generated cards as a UTF-8-safe CSV or TSV fallback.
- [ ] **EXPT-03**: User receives Anki-compatible audio references for `word_audio` and `sentence_audio`, with bundled media files that play correctly after import.
- [x] **JOB-01**: User can resume an interrupted generation job without losing already completed cards. _(Completed by Plans 01-02, 01-05, and 01-06.)_
- [x] **JOB-02**: User can see per-batch progress and failures while generation is running. _(Completed by Plans 01-04, 01-05, and 01-06.)_
- [x] **JOB-03**: User can rerun the same deck or custom word list without silent duplicate card creation. _(Completed by Plans 01-02, 01-04, 01-05, and 01-06.)_

## v2 Requirements

### Language Quality

- **LANG-01**: User receives language-specific generation and rendering rules for each supported language.
- **LANG-02**: User receives sense-aware disambiguation for polysemous words before export.

### Review and Quality

- **REVW-01**: User can regenerate individual fields such as translation or audio without regenerating the whole card.
- **QUAL-01**: User can run deck linting that checks for missing audio, malformed IPA, repeated sentence patterns, and translation mismatch before export.

### Provenance and Consistency

- **META-01**: User can inspect provenance for each generated field, including whether it came from lexical data, AI generation, translation, or TTS.
- **TERM-01**: User can keep a reusable glossary or translation memory across decks and custom word lists.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Automatic image generation or sourcing | The user wants the `Image` field to stay blank and add images manually later. |
| Browser-extension or web-capture workflows | Useful later, but v1 should stay focused on frequency decks and custom word lists. |
| Full spaced-repetition app or AI tutor | Anki remains the destination study tool; the product should focus on card generation quality. |
| Languages beyond Portuguese, Spanish, English, French, German, Russian, and Dutch | Expanding language scope early would multiply QA and language-specific edge cases. |
| Deck styling/theme builder or card marketplace | Not part of the core value of trustworthy multilingual card generation. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DECK-01 | Phase 1 | Completed in Plan 01-01 |
| JOB-01 | Phase 1 | Completed in Plans 01-02, 01-05, and 01-06 |
| JOB-02 | Phase 1 | Completed in Plans 01-04, 01-05, and 01-06 |
| JOB-03 | Phase 1 | Completed in Plans 01-02, 01-04, 01-05, and 01-06 |
| DECK-02 | Phase 2 | Pending |
| DECK-03 | Phase 2 | Pending |
| LEX-01 | Phase 2 | Pending |
| LEX-02 | Phase 2 | Pending |
| LEX-03 | Phase 2 | Pending |
| TEXT-01 | Phase 3 | Pending |
| TEXT-02 | Phase 3 | Pending |
| TEXT-03 | Phase 3 | Pending |
| TEXT-04 | Phase 3 | Pending |
| TEXT-05 | Phase 3 | Pending |
| AUDI-01 | Phase 4 | Pending |
| AUDI-02 | Phase 4 | Pending |
| CARD-01 | Phase 5 | Pending |
| CARD-02 | Phase 5 | Pending |
| CARD-03 | Phase 5 | Pending |
| CARD-04 | Phase 5 | Pending |
| EXPT-01 | Phase 5 | Pending |
| EXPT-02 | Phase 5 | Pending |
| EXPT-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-18*
*Last updated: 2026-04-19 after Phase 1 gap closure was completed*
