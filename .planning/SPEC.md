# Multilang Anki Card Generator

## Core Value

Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.

## Principles

- Prefer grounded, reviewable lexical and linguistic data over unverified generation.
- Fail closed when morphology, pronunciation, licensing, media, or export integrity is unresolved.
- Reuse stable deck contracts and templates unless a language has a concrete pedagogical need.
- Keep generated artifacts reproducible, versioned, auditable, and safe to export.
- Preserve existing language and source-mode behavior while adding language-specific capabilities.

## Current State

- **Milestone:** v3.0 Korean Learning System - IN PROGRESS
- **Phases:** 30-34 (1 of 5 complete)
- **Last completed milestone:** v2.1 Latin Google TTS Finalization
- **Active Phase:** Phase 31 - Hangul and Pronunciation i+1 (implementation in progress; Plan 31-10 complete; Phase 31 remains open).
- **Last Completed:** Plan 31-10 - fixed the pathless `korean-foundations` CLI, proved the temporary evidence-to-receipt-to-snapshot-to-activation-to-export workflow, reran write-poisoned verification with a Windows Python 3.12-compatible poison helper, and passed the complete offline isolated Python 3.12 pytest suite with unchanged `.venv` and canonical evidence/export state on 2026-08-17.
- **Decisions:** Keep the public Korean foundation CLI fixed to hash/enums-only state commands plus export destination output; use private temporary-root composition for tests only; require write-poisoned prepared verification, six-artifact export inspection, lock consistency, isolated Python 3.12, full offline pytest, unchanged shared `.venv`, and `canonical_mutation_count=0` before the first human checkpoint.
- **Blockers:** No Plan 31-10 engineering blocker. Genuine qualified reviews, Portuguese policy, rights dispositions, licensed exact media, playback evidence, the canonical receipt, canonical snapshot preparation/authorization/activation, production exports, and observed Anki acceptance remain unavailable and later-plan work. The Korean frequency source/redistribution decision remains a Phase 32 blocker.
- **Next:** Execute Plan 31-11 as the first human checkpoint to populate/validate the fixed canonical inbox and prepare an inactive canonical snapshot without activating or exporting production state.

## Validated Capabilities

- Users can generate modern-language frequency decks with three 1000-card levels.
- Users can generate cards from custom word lists and privacy-safe Kindle/WebDAV highlights.
- Generated cards support grounded lexical data, text generation and validation, review, word/sentence audio, and deterministic reruns.
- Users can export APKG, CSV, and TSV artifacts with stable note identities, templates, and media references.
- Azure-first synthesis, provider metadata, and audio integrity gates protect modern-language exports.
- Classical Latin has an isolated reviewed 50-card path with source, morphology, Portuguese translation, audio, review, and export gates.
- Japanese kana, Japanese frequency, and introductory Russian, Polish, and Greek phoneme deck patterns exist as reusable language-specific precedents.

## Must Have: v3.0 Korean Learning System

### Language And Morphology

- [x] **[KMODE-01]**: User can select Korean with canonical language code `ko` for frequency, word-list, and highlight generation, while `ko-KR` is used only as a provider or locale value. [Done-When: requests, settings, persistence, providers, runtime, and tags resolve one canonical Korean identity across all three modes.]
- [x] **[KMODE-02]**: User retains all existing language, source-mode, template, audio, and export behavior after Korean is added. [Done-When: focused regressions for existing modern, Japanese, Mandarin, Latin, highlight, and phoneme paths pass without contract drift.]
- [x] **[KNLP-01]**: User receives Korean content normalized to Unicode NFC and analyzed by lemma, part of speech, and morphology with a pinned Korean analyzer. [Done-When: deterministic golden cases cover nouns, attached particles, regular and irregular predicates, compound predicates, and canonically equivalent Hangul.]
- [x] **[KNLP-02]**: User receives example and highlight matches based on Korean morpheme signatures rather than whitespace, substring, or naive suffix stripping. [Done-When: inflected targets such as `먹다` in `먹었어요` match, noun/predicate homographs remain distinct, and unavailable or inconclusive analysis blocks acceptance.]

### Hangul Foundations

- [ ] **[KHAN-01]**: User receives a Hangul foundations deck covering modern jamo, syllable-block construction, stroke order, mnemonics, and reviewed audio through a Korean note type derived from the existing kana layout. [Done-When: the curated inventory exports with unique model/deck IDs, Korean fonts, complete required media, and no Japanese-specific field or label leakage.]
- [ ] **[KHAN-02]**: User receives Hangul cards in curriculum i+1 order after an explicit bootstrap. [Done-When: each note stores prerequisite, observed, and target concept IDs and introduces exactly one new orthographic concept while preserving NFC output.]

### Pronunciation

- [ ] **[KPRO-01]**: User receives a Korean pronunciation deck using the existing phoneme template fields for spelling, sound, short audio, example word, word audio/translation, example sentence, and sentence audio/translation. [Done-When: a Korean-specific note type reuses the shared HTML/CSS contract and all fields and media survive APKG, CSV, and TSV export.]
- [ ] **[KPRO-02]**: User receives a strict curriculum i+1 pronunciation sequence covering onset contrasts, batchim, liaison, tensification, nasalization, aspiration, palatalization, complex codas, contractions, and connected speech. [Done-When: every card has exactly one new phonological concept, all other active rules are prerequisites, and false i+1 labeling blocks approval.]

### Frequency, Text, And Audio

- [ ] **[KFREQ-01]**: User receives a Korean frequency inventory whose lemma, sense, rank, POS, source, license, analyzer version, and curation decision are auditable. [Done-When: the approved source permits the intended project use and the loader fails closed on missing provenance, license decision, analyzer version, or sequence integrity.]
- [ ] **[KFREQ-02]**: User receives three real Korean frequency subdecks with exactly 1000 unique lemma/sense cards per level. [Done-When: 3000 cards are partitioned 1000/1000/1000, inflectional duplicates are absent, and particles/endings are routed to grammar rather than ranked as standalone lexical vocabulary.]
- [ ] **[KFREQ-03]**: User receives frequency examples ordered with adaptive i+1 scoring. [Done-When: each card records known and incidental concepts, introduces the target lexeme, minimizes other novelty, and rejects unnatural examples created only to improve the score.]
- [ ] **[KTXT-01]**: User receives natural standard-Seoul Korean examples, context-matched Portuguese glosses, and Portuguese sentence translations. [Done-When: validation and review block English leakage, wrong senses, omitted-context inventions, mixed speech levels, unnatural wording, and translations that contradict the Korean sentence.]
- [ ] **[KAUD-01]**: User receives approved Azure `ko-KR` word and sentence audio plus specialist-reviewed audio for jamo and phonological rules. [Done-When: the exact Azure voice is verified from the live catalog, request/artifact/review hashes and metadata are persisted, jamo is not synthesized as an unexplained raw glyph, and only approved exact-text audio can be exported.]

### Grammar And Personal Sources

- [ ] **[KGRAM-01]**: User receives a Particles & Endings deck using the normal Multilang card layout and a curated progression of particles, endings, speech levels, connectors, and irregular paradigms. [Done-When: cards expose form, function, attachment/allomorph rule, register, example, translation, and audio in the approved sequence.]
- [ ] **[KGRAM-02]**: User receives grammar cards in strict curriculum i+1 order. [Done-When: each card introduces exactly one form-function-register construction and all lexical, orthographic, phonological, and morphological prerequisites are already present in its concept graph.]
- [ ] **[KPERS-01]**: User can generate Korean custom-list cards while preserving the submitted form, resolved lemma, sense, POS, and input order. [Done-When: inflected forms resolve deterministically and excessive or ambiguous prerequisites create bridge/defer decisions instead of fabricated analysis.]
- [ ] **[KPERS-02]**: User can generate Korean highlight cards with morphology-aware extraction and existing privacy guarantees. [Done-When: valid one-syllable words are retained, attached particles/endings are analyzed, exact source excerpts remain distinct from generated microexamples, and private paths or excessive reading context never enter exported or provider-visible artifacts.]

### Export, Review, And Evidence

- [ ] **[KEXP-01]**: User can export every Korean deck family to APKG, CSV, and TSV with stable fields, note identity, tags, real subdecks where required, and resolvable media. [Done-When: automated import-structure checks and representative Anki import/playback evidence pass for Hangul, pronunciation, frequency, grammar, custom, and highlight decks.]
- [ ] **[KEXP-02]**: User receives Korean-readable templates that preserve existing Multilang visual contracts and a blank `Image` field. [Done-When: Korean font stacks, responsive layouts, hidden/revealed fields, blank images, and Desktop/mobile rendering are reviewed without mutating unrelated note types.]
- [ ] **[KQA-01]**: User can inspect and manage Korean `needs_review`, `approved`, and `rejected` gates. [Done-When: unresolved morphology, false i+1, wrong register or sense, unapproved audio, text/media drift, or licensing uncertainty blocks learner-ready export with an actionable reason.]
- [ ] **[KQA-02]**: User receives reproducible evidence that Korean requirements are met without regressions. [Done-When: scanner-readable manifests, tests, reports, and review artifacts cover every v3.0 requirement exactly once and prove existing modes remain operational.]

## Typed Data Contracts

```text
KoreanConcept = {
  id: str,
  domain: "orthography" | "phonology" | "grammar" | "lexicon",
  prerequisite_ids: tuple[str, ...],
  sequence: int,
}

KoreanLexicalIdentity = {
  submitted_form: str | None,
  canonical_nfc: str,
  lemma: str,
  morpheme_signature: tuple[(form: str, pos: str), ...],
  part_of_speech: str,
  sense_id: str,
  register: str,
}

KoreanCurriculumEvidence = {
  target_concept_id: str,
  observed_concept_ids: tuple[str, ...],
  prerequisite_concept_ids: tuple[str, ...],
  unknown_concept_ids: tuple[str, ...],
  policy: "strict" | "adaptive" | "contextual",
}

KoreanPronunciationEvidence = {
  canonical_spelling: str,
  normative_pronunciation: str,
  surface_pronunciation: str,
  ipa: str | None,
  phonological_rule_ids: tuple[str, ...],
  review_status: "needs_review" | "approved" | "rejected",
}

KoreanFrequencyEntry = {
  language: "ko",
  version: str,
  level: 1 | 2 | 3,
  final_rank: int,
  lexical_identity: KoreanLexicalIdentity,
  source_rank: int,
  source_provenance: str,
  license_decision: str,
  analyzer_version: str,
  curation_flags: tuple[str, ...],
}
```

## Out Of Scope For v3.0

- Hanja curriculum or etymological decks.
- Regional dialect decks or a non-Seoul pronunciation policy.
- Romanization as pronunciation ground truth or as a persistent frequency-card dependency.
- Automatic approval of jamo, contrast, or phonological-rule TTS.
- Google Translate consumer TTS endpoints, which have no documented production API contract.
- Tatoeba as the default sentence source.
- Distribution of a Korean CSV derived from `wordfreq` before attribution and redistribution terms are approved.
- Automatic image generation or sourcing; `Image` remains blank.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Use `ko` internally and `ko-KR` only for locale/provider contracts | Prevents duplicate language identities. |
| Use Kiwi through `kiwipiepy` as the primary Korean analyzer | It provides local morpheme/POS analysis suitable for inflected-form matching on Python 3.12. |
| Reuse kana, phoneme, normal, and highlight layouts | Korean needs new data contracts and note identities, not unnecessary visual duplication. |
| Define project-specific curriculum i+1 | Linguistic `i+1` is not itself an executable exactly-one-unknown algorithm. |
| Keep frequency, custom, and authentic highlights adaptive rather than falsely strict | Natural Korean morphology and user-selected text can contain unavoidable incidental concepts. |
| Use Azure `ko-KR` as the only default TTS provider | It has documented Korean voices, locale, IPA support, and live voice discovery. |
| Require specialist review for jamo and phonological-rule audio | Raw glyph synthesis and automatic phoneme control are not reliable teaching evidence. |
| Gate the 3000-card asset on an explicit license decision | `wordfreq` is suitable for bootstrap but its own documentation warns against CSV extraction without preserved attribution. |

## Capability And Security Gates

- Do not make paid provider calls, publish decks, or upload private highlight content without explicit approval.
- Do not approve Korean pronunciation, morphology, translation, or strict-i+1 status solely from an LLM response.
- Do not commit redistributed lexical/corpus assets until their license and attribution path is documented.
- Do not overwrite approved curated fields during provider regeneration without an explicit forced review transition.
- Do not claim Desktop/mobile visual acceptance without an observed human or project-approved renderer proof.

---
*Last updated: 2026-08-17 - Phase 31 Plan 10 implemented; phase remains open for Plan 31-11*
