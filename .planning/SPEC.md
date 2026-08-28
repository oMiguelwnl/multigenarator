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

- **Milestone:** v3.0 Korean Learning System and Shared Generation Hardening - IN PROGRESS
- **Phases:** 30-34 (1 of 5 complete)
- **Last completed milestone:** v2.1 Latin Google TTS Finalization
- **Active Phase:** Phase 32 - Frequency, Portuguese Text, and Audio (Plan 32-03 implemented with verification passing; Phase 31 remains open and production Phase 32 joins still wait for exact Phase 31 active output).
- **Last Completed:** Plan 32-03 - added canonical authority locator hashing, staged Korean job authority CAS/attempt guards, and strict lexical/text/audio evidence round trips for offline repository contracts on 2026-08-28.
- **Decisions:** Keep Korean foundation production defaults bound to one atomic `current-candidate` bundle while preserving immutable explicit v1 history; adopt `.planning/AI-LINGUISTIC-REVIEW-POLICY.md` for every language; AI review is explicit, hash-bound, multi-pass, and never impersonates a human; human linguistic review is optional rather than blocking; legal rights, provider spend, private-content processing, source transformation, production database mutation, and publication authority remain separate; execute disjoint plans as a dependency DAG in isolated parallel lanes.
- **Reconciliation:** Preserve the verified Korean Phase 30 implementation and distribute the restored shared-hardening requirements across Phases 32-34 rather than overlaying the alternate local Phase 30 implementation.
- **Blockers:** Human linguistic availability is no longer a blocker. Remaining Phase 31 blockers are exact media creation/integrity, applicable rights/provider authority, AI review disagreement or uncertainty, canonical snapshot activation, and exports. Phase 32 production source transformation, provider use, Azure catalog/synthesis, asset commit, and publication remain blocked until their exact checkpoint authority exists. The real shared `.venv` remains `venv_unsafe` and must not be silently repaired.
- **Next:** Continue Phase 32 offline lanes that do not consume the inactive Phase 31 output or require live/provider authority; production generation still requires exact Phase 31 active snapshot plus source/license/provider/Azure checkpoint authority, and Phase 32 remains verification-pending until `/gsdd-verify` passes.

## Validated Capabilities

- Users can generate modern-language frequency decks with three 1000-card levels.
- Users can generate cards from custom word lists and privacy-safe Kindle/WebDAV highlights.
- Generated cards support grounded lexical data, text generation and validation, review, word/sentence audio, and deterministic reruns.
- Users can export APKG, CSV, and TSV artifacts with stable note identities, templates, and media references.
- Azure-first synthesis, provider metadata, and audio integrity gates protect modern-language exports.
- Classical Latin has an isolated reviewed 50-card path with source, morphology, Portuguese translation, audio, review, and export gates.
- Japanese kana, Japanese frequency, and introductory Russian, Polish, and Greek phoneme deck patterns exist as reusable language-specific precedents.

## Must Have: v3.0 Korean Learning System and Shared Generation Hardening

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
- [ ] **[KAUD-01]**: User receives approved Azure `ko-KR` word and sentence audio plus AI-policy-reviewed audio for jamo and phonological rules. [Done-When: the exact Azure voice is verified from the live catalog, request/artifact/review hashes and metadata are persisted, jamo is not synthesized as an unexplained raw glyph, and only exact-text audio that passes deterministic integrity plus AI acoustic review can be exported.]

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

### Shared Generation Hardening

- [ ] **[GLEX-01]**: User receives frequency candidates from frozen, versioned, provenance-aware assets rather than live `wordfreq` fallback during final generation. [Done-When: the final runtime loads the configured asset version, rejects missing or insufficient assets, and a curated/rejection report proves 3000 entries, 1000 per level, no cross-level duplicates, and no unresolved final candidates.]
- [ ] **[GLEX-02]**: User receives lexical candidates with enough metadata to validate the intended word before text generation. [Done-When: persisted candidates carry POS, sense hint or source sense, lexical source/version, grounding confidence, and ambiguity is blocked or routed to review instead of silently selecting the first match.]
- [ ] **[GMOR-01]**: User receives target matching based on a language-specific morphology adapter. [Done-When: supported adapters distinguish reliable match, mismatch, and inconclusive analysis; final frequency acceptance never relies on generic suffix stripping when the adapter is unavailable or ambiguous.]
- [ ] **[GTXT-01]**: User receives the best validated example available for each item instead of the first provider response. [Done-When: generation returns a bounded candidate set, deterministic validation and scoring select one candidate, repair cache keys differ from initial generation, and Tatoeba is never an automatic final-deck fallback.]
- [ ] **[GPRO-01]**: User receives observable and policy-controlled provider execution. [Done-When: generation, repair, translation, judge, definition, and audio calls use explicit task routes, retries/fallbacks are visible, and every provider attempt has sanitized job/item/task/latency/status/hash/token/cost telemetry.]
- [ ] **[GJOB-01]**: User can resume generation without losing the distinction between processed, accepted, failed, and review-required items. [Done-When: failures are isolated per item, stage status is persisted accurately, review/audio failures never count as completed, and a provider exception cannot silently abort the remaining batch.]
- [ ] **[GAUD-01]**: User receives audio governed by an explicit provider and fallback policy. [Done-When: required word/sentence assets validate exact text, provider/voice metadata and fallback status are reported, unapproved fallback blocks final frequency export, and failed assets cannot advance the item to audio success.]
- [ ] **[GREV-01]**: User can manage generated content at field level after automatic validation. [Done-When: review commands can list, approve, reject, edit, and regenerate a selected definition, sentence, translation, or audio field while preserving approved fields and an auditable before/after event.]
- [ ] **[GEXP-01]**: User receives frequency exports separated into real Level 1, Level 2, and Level 3 subdecks without changing current note GUID semantics. [Done-When: APKG export routes every frequency row to the real level deck, preserves existing fields/tags/GUID formula, and import-structure tests pass for existing and Korean frequency paths.]
- [ ] **[GOPS-01]**: User can run bounded large generation without duplicate claims or unsafe parallel state. [Done-When: PostgreSQL uses atomic leases/claims, concurrency and batch execution are bounded by provider policy, malformed batch rows fall back individually, SQLite remains safe at concurrency one, and interrupted work resumes idempotently.]
- [ ] **[GEVAL-01]**: User receives evidence that generation hardening improves release safety without claiming unmeasured linguistic quality. [Done-When: focused tests, deterministic goldens, Polish failure replay, APKG structure checks, provider telemetry checks, and a report with numerator/denominator metrics cover all shared hardening gates.]

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
- v4 semantic GUID migration, `SurfaceForms`, `Important Forms`, canonical editions, APKG history import, adaptive queues, and v4 Anki topology experiments.
- Replacing the current note identity formula while adding real level subdecks.
- Treating an untracked single-pass model verdict as approval without the versioned AI policy, independent passes, deterministic validators, exact hashes, and fail-closed disagreement handling.

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Use `ko` internally and `ko-KR` only for locale/provider contracts | Prevents duplicate language identities. |
| Use Kiwi through `kiwipiepy` as the primary Korean analyzer | It provides local morpheme/POS analysis suitable for inflected-form matching on Python 3.12. |
| Reuse kana, phoneme, normal, and highlight layouts | Korean needs new data contracts and note identities, not unnecessary visual duplication. |
| Define project-specific curriculum i+1 | Linguistic `i+1` is not itself an executable exactly-one-unknown algorithm. |
| Keep frequency, custom, and authentic highlights adaptive rather than falsely strict | Natural Korean morphology and user-selected text can contain unavoidable incidental concepts. |
| Use Azure `ko-KR` as the only default TTS provider | It has documented Korean voices, locale, IPA support, and live voice discovery. |
| Require AI-policy linguistic and acoustic review for jamo and phonological-rule audio | Raw glyph synthesis and provider success are not reliable teaching evidence; exact deterministic and multi-pass AI evidence is required. |
| Gate the 3000-card asset on an explicit license decision | `wordfreq` is suitable for bootstrap but its own documentation warns against CSV extraction without preserved attribution. |
| Preserve verified Korean Phase 30 and distribute shared hardening across Phases 32-34 | Avoids replacing stronger Korean identity/morphology contracts while restoring the user-approved cross-language scope. |
| Use manifest-bound frozen assets for final frequency generation | Final generation must be reproducible and must never replace rejected or missing entries with live `wordfreq` candidates. |
| Require conclusive selected-adapter morphology for every final frequency candidate | Inconclusive or mismatched analysis must block rather than fall through to generic suffix heuristics. |

## Capability And Security Gates

- Do not make paid provider calls, publish decks, or upload private highlight content without explicit approval.
- Do not approve linguistic content from an unversioned or single-pass LLM response; require `.planning/AI-LINGUISTIC-REVIEW-POLICY.md` evidence and deterministic validators.
- Do not commit redistributed lexical/corpus assets until their license and attribution path is documented.
- Do not overwrite approved curated fields during provider regeneration without an explicit forced review transition.
- Do not claim Desktop/mobile visual acceptance without an instrumented project-approved renderer/device proof bound to the exact artifact and environment.

---
*Last updated: 2026-08-18 - remote/local reconciliation restored shared hardening across Phases 32-34*
