# Requirements: Multilang Anki Card Generator v2.0 Classical Latin MVP

**Defined:** 2026-06-01  
**Core Value:** Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.

## v2.0 Requirements

Requirements for the Classical Latin MVP. Each maps to roadmap phases.

### Latin Mode

- [x] **MODE-01**: User can generate a Classical Latin MVP through a separate Latin generation path that does not route through the existing modern-language frequency deck path.
- [x] **MODE-02**: User receives Latin deck metadata that identifies `language_code=la`, the Classical Latin variant, the MVP source pack version, and the 50-card MVP scope.
- [x] **MODE-03**: Existing modern-language frequency, custom word-list, highlight, phonetics, review, audio, and export flows remain operational after Latin mode is added.

### Latin Scope And Frequency

- [x] **FREQ-01**: User receives a reproducible 50-card Latin MVP manifest rather than an unbounded or full 3000-card Latin deck.
- [x] **FREQ-02**: Every Latin MVP card is ordered by lemma-level frequency with stored `lemma`, `frequency_rank`, `frequency_source`, and MVP asset version metadata.
- [x] **FREQ-03**: User can audit why each first-50 lemma was included, deferred, replaced, or reordered for Rafael Falcon-style didactic suitability.

### Latin Sources And Sentences

- [x] **SRC-01**: Every Latin MVP sentence has license-gated provenance metadata, including source type, citation/work reference when available, URL or local source identifier, and source/license note.
- [x] **SRC-02**: User can distinguish original Classical Latin text, adapted didactic Latin, and reference examples without adapted sentences being presented as original classical citations.
- [x] **SENT-01**: Every Latin MVP card includes the target form in the displayed Latin sentence, with validation for exact target-form presence or accepted orthographic/enclitic normalization.
- [x] **SENT-02**: User receives a first-50 sentence sequence that applies Rafael Falcon-style progression rules, favoring clearer early reading contexts and deferring overly complex poetic or ambiguous constructions.

### Latin Grammar

- [x] **GRAM-01**: Every Latin MVP card has morphology evidence for the target form, including lemma, part of speech, case or verbal analysis where applicable, number, and syntactic function.
- [x] **GRAM-02**: Every Latin MVP card has a short standardized `Gramatica` field using approved abbreviations such as `subst`, `adj`, `v`, `sg`, `pl`, `Suj`, `OD`, and `OI`.
- [x] **GRAM-03**: Final Latin grammar labels use `Genitivus` and the required case vocabulary: `Nominativus`, `Vocativus`, `Accusativus`, `Genitivus`, `Dativus`, and `Ablativus`.
- [x] **GRAM-04**: Ambiguous or uncertain Latin morphology cannot be exported as learner-ready unless the card is reviewed and approved with the final grammar analysis resolved.

### Portuguese Text

- [x] **PT-01**: Every Latin MVP card has a Portuguese short translation for the target lemma or target form that matches the selected sentence sense.
- [x] **PT-02**: Every Latin MVP card has a Portuguese translation of the displayed Latin sentence that corresponds to the selected source sentence and target form context.
- [x] **PT-03**: Portuguese learner-facing text is reviewed or validated to prevent English leakage, dictionary-only glosses that miss the sentence sense, and translations that contradict the Latin sentence.

### Latin Review

- [x] **REV-01**: Latin MVP cards support `needs_review`, `approved`, and `rejected` review states for source, translation, grammar, and audio readiness.
- [x] **REV-02**: User can export the final learner-ready Latin MVP only from cards whose required review gates are `approved`.
- [x] **REV-03**: User can inspect rejection, replacement, and uncertainty reasons for Latin MVP cards without losing the original source and frequency provenance.

### Latin Audio

- [x] **AUD-01**: User can compare or evaluate candidate Latin TTS providers for representative word and sentence samples before the final MVP audio policy is locked.
- [x] **AUD-02**: Every final exported Latin MVP card has approved playable word audio and sentence audio; missing, failed, or unapproved audio blocks learner-ready export.
- [x] **AUD-03**: Every Latin audio artifact stores provider, provider version, voice, pronunciation policy, generated text, text hash, audio kind, playback review status, and fallback reason when applicable.
- [x] **AUD-04**: Latin audio integrity validation blocks export when persisted audio text does not match the exported target form or Latin sentence.

### Latin Export

- [x] **EXP-01**: User receives a dedicated Latin Anki note type/template with stable field order for target form, Latin sentence, lemma, Portuguese translations, `Gramatica`, source, word audio, sentence audio, and blank `Image`.
- [x] **EXP-02**: Latin exports do not include a separate learner-facing `Classe` field while still allowing part-of-speech metadata internally or inside `Gramatica`.
- [ ] **EXP-03**: User can export approved Latin MVP cards to `.apkg`, CSV, and TSV with packaged media references and Anki import/playback evidence.

### Evidence And Regression

- [ ] **EVID-01**: User receives scanner-readable v2.0 evidence proving all Latin MVP requirements are covered by implementation, validation, or explicit review artifacts.
- [ ] **EVID-02**: User receives evidence that Latin source/license metadata and committed artifacts do not leak private paths, raw provider secrets, or unapproved source material.
- [ ] **EVID-03**: Existing frequency, custom word-list, highlight, and phonetics deck export contracts remain covered by focused regression evidence after Latin changes.

## Future Requirements

Deferred to future milestones. Tracked but not in the current roadmap.

### Latin Scale

- **SCALE-01**: User can generate a 300-card Latin pilot after the 50-card MVP contract is validated.
- **SCALE-02**: User can generate a full 3-level Latin deck with 1000 cards per level after source, morphology, review, and audio automation scale safely.
- **SCALE-03**: User can compute project-owned Latin corpus frequency from a curated corpus instead of relying on the DCC-seeded MVP list.

### Latin Variants And Study Modes

- **VAR-01**: User can generate ecclesiastical, medieval, neo-Latin, or other Latin variant decks with explicit source and pronunciation policies.
- **VAR-02**: User can add Greek as a separate future language milestone.
- **STUDY-01**: User can generate richer Latin grammar lessons, cloze drills, parsing drills, or an interactive reviewer UI after the MVP card contract is proven.
- **AUDIO-FUT-01**: User can switch to human-recorded or custom-voice Latin audio packs after pronunciation policy and recording workflow are defined.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Greek support | User explicitly scoped this milestone to Latin only. |
| Full 3000-card Latin deck | Source, morphology, translation, review, and audio risks must be validated with 50 cards first. |
| Unreviewed bulk Latin generation | Latin grammar and source quality are too risky for learner-ready export without review gates. |
| Untraceable generated Latin sentences | The MVP requires real, reliable, or clearly marked didactic sources with provenance. |
| Separate learner-facing `Classe` field | The user explicitly decided that class should not appear as its own study field. |
| Automatic image generation or sourcing | Existing product decision keeps `Image` blank for manual user images. |
| Google Cloud TTS provider integration | Research found no verified Classical Latin/`la` voice; adding it would add complexity without clear MVP value. |
| Python 3.13 migration for CLTK 2.x | The project baseline is Python 3.12; CLTK 2.x migration is a platform upgrade, not an MVP requirement. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MODE-01 | Phase 22 | Complete |
| MODE-02 | Phase 22 | Complete |
| MODE-03 | Phase 22 | Complete |
| FREQ-01 | Phase 23 | Complete |
| FREQ-02 | Phase 23 | Complete |
| FREQ-03 | Phase 23 | Complete |
| SRC-01 | Phase 23 | Complete |
| SRC-02 | Phase 23 | Complete |
| SENT-01 | Phase 23 | Complete |
| SENT-02 | Phase 23 | Complete |
| GRAM-01 | Phase 24 | Complete |
| GRAM-02 | Phase 24 | Complete |
| GRAM-03 | Phase 24 | Complete |
| GRAM-04 | Phase 24 | Complete |
| PT-01 | Phase 26 | Complete |
| PT-02 | Phase 26 | Complete |
| PT-03 | Phase 26 | Complete |
| REV-01 | Phase 25 | Complete |
| REV-02 | Phase 25 | Complete |
| REV-03 | Phase 25 | Complete |
| AUD-01 | Phase 27 | Complete |
| AUD-02 | Phase 27 | Complete |
| AUD-03 | Phase 27 | Complete |
| AUD-04 | Phase 27 | Complete |
| EXP-01 | Phase 28 | Complete |
| EXP-02 | Phase 28 | Complete |
| EXP-03 | Phase 28 | Pending |
| EVID-01 | Phase 28 | Pending |
| EVID-02 | Phase 28 | Pending |
| EVID-03 | Phase 28 | Pending |

**Coverage:**

- v2.0 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0
- Coverage: 30/30 mapped exactly once across Phases 22-28

---
*Requirements defined: 2026-06-01*  
*Last updated: 2026-06-01 after v2.0 roadmap creation*
