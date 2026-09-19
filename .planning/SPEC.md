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

- **Milestone:** v3.0 Korean Learning System and Shared Generation Hardening — implementation complete 2026-09-19.
- **Scope:** `repo_only` / `repo_closeout`; five implementation phases complete, 32/32 implementation contracts mapped to code and tests.
- **Implementation commit:** `3c7c91a`; completed directly at the user's request without replaying legacy GSD plans.
- **Verification:** isolated regression runs consolidate to 452 distinct passed cases and two skipped PostgreSQL cases; the final integration run passed 89 tests. This is not a full-repository or production acceptance result.
- **Production/delivery:** pending; see `.planning/KOREAN-PRODUCTION-BACKLOG.md` for 3000 cards, 6000 audio assets, grammar, personal samples, actual environment and Anki acceptance.
- **Historical record:** failed/waived production attempts are preserved. Old plan execution counts are not presented as completed implementation counts.
- **Archive:** `.planning/milestones/v3.0-ROADMAP.md` and `.planning/milestones/v3.0-REQUIREMENTS.md`.
- **Next:** production backlog only when requested, with fresh bounded authority and exact current evidence; no implementation phase remains open.

## Validated Capabilities

- Users can generate modern-language frequency decks with three 1000-card levels.
- Users can generate cards from custom word lists and privacy-safe Kindle/WebDAV highlights.
- Generated cards support grounded lexical data, text generation and validation, review, word/sentence audio, and deterministic reruns.
- Users can export APKG, CSV, and TSV artifacts with stable note identities, templates, and media references.
- Azure-first synthesis, provider metadata, and audio integrity gates protect modern-language exports.
- Classical Latin has an isolated reviewed 50-card path with source, morphology, Portuguese translation, audio, review, and export gates.
- Japanese kana, Japanese frequency, and introductory Russian, Polish, and Greek phoneme deck patterns exist as reusable language-specific precedents.

### v3.0 implementation contracts — completed

The checkboxes below mean **implemented and covered by repository tests**.
They do not mark the original learner-delivery Done-When criteria as satisfied.
Those original texts and their prior statuses are retained in
`.planning/milestones/v3.0-REQUIREMENTS.md`; outstanding runtime/delivery outcomes
are explicit in `.planning/KOREAN-PRODUCTION-BACKLOG.md`.
The exact code/test mapping is `docs/korean-implementation.json` at `3c7c91a`.

- [x] **[KMODE-01]**: Canonical Korean routing and provider locale separation.
- [x] **[KMODE-02]**: Existing-mode compatibility contracts and regression coverage.
- [x] **[KNLP-01]**: NFC normalization and pinned lemma/POS/morphology analysis.
- [x] **[KNLP-02]**: Morpheme-signature matching with fail-closed ambiguity.
- [x] **[KHAN-01]**: Hangul inventory, note schema and reviewed-media export.
- [x] **[KHAN-02]**: Explicit bootstrap and strict orthographic concept sequencing.
- [x] **[KPRO-01]**: Korean pronunciation note fields and export contracts.
- [x] **[KPRO-02]**: Strict phonological prerequisite and concept validation.
- [x] **[KFREQ-01]**: Provenance, license and frozen inventory validation.
- [x] **[KFREQ-02]**: Three real 1000-card levels and lexical deduplication contracts.
- [x] **[KFREQ-03]**: Adaptive i+1 candidate scoring and validation.
- [x] **[KTXT-01]**: Korean/Portuguese generation and linguistic review gates.
- [x] **[KAUD-01]**: Bounded Azure synthesis and exact-text acoustic evidence gates.
- [x] **[KGRAM-01]**: Particles and endings curriculum import and card export.
- [x] **[KGRAM-02]**: Strict grammar graph and reviewed lexical bootstrap.
- [x] **[KPERS-01]**: Ordered custom-list ingestion and bridge/defer decisions.
- [x] **[KPERS-02]**: Morphology-aware, privacy-safe highlight workflows.
- [x] **[KEXP-01]**: Six-family APKG/CSV/TSV generation and media packaging.
- [x] **[KEXP-02]**: Korean template contracts and empty Image fields.
- [x] **[KQA-01]**: Current review state and fail-closed final export.
- [x] **[KQA-02]**: Scanner-readable requirement and evidence mapping.
- [x] **[GLEX-01]**: Frozen final-frequency asset loading without live replacements.
- [x] **[GLEX-02]**: Persisted lexical identity and grounding metadata.
- [x] **[GMOR-01]**: Language-specific conclusive morphology validation.
- [x] **[GTXT-01]**: Bounded candidate selection and distinct repair cache identities.
- [x] **[GPRO-01]**: Policy-controlled provider attempts and sanitized telemetry.
- [x] **[GJOB-01]**: Persisted item outcomes and isolated, resumable processing.
- [x] **[GAUD-01]**: Provider/fallback policy and exact-text audio integrity.
- [x] **[GREV-01]**: Auditable per-field approve/reject/edit/regenerate operations.
- [x] **[GEXP-01]**: Real frequency subdecks with stable GUID semantics.
- [x] **[GOPS-01]**: Atomic generation leases, bounded concurrency and explicit recovery.
- [x] **[GEVAL-01]**: Focused structural regression and safety evidence.

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
*Last updated: 2026-09-19 — implementation closeout; original delivery acceptance retained in the production backlog.*
