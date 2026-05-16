# Multilang Anki Card Generator

## What This Is

Multilang is a Python CLI/batch pipeline for generating high-quality multilingual Anki vocabulary cards from supported-language frequency decks, user-provided word lists, and reading-derived vocabulary sources. v1.0 ships the first usable product slice for Portuguese, Spanish, English, French, German, Italian, Polish, Turkish, Romanian, Russian, and Dutch.

The product generates structured Anki-ready cards with word data, IPA, definitions, example sentences, translations where the deck type requires them, word audio, sentence audio, and an empty `Image` field that the user can fill manually later. v1.0 uses grounded lexical inputs, deterministic validation, Azure-first audio synthesis, and fixed-schema Anki export rather than relying on unverified generated text alone.

## Core Value

Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.

## Current State

**Shipped version:** v1.3 Card Quality Remediation and Deck Validation on 2026-05-16  
**Milestone archive:** `.planning/milestones/v1.3-ROADMAP.md`  
**Requirements archive:** `.planning/milestones/v1.3-REQUIREMENTS.md`  
**Audit result:** Phase 21 final evidence passed with 15/15 v1.3 requirements covered and 9/9 Phase 21 must-haves verified.

v1.0 provides the shipped CLI path for generation, review support, audio generation, and export. Representative custom word-list and frequency-deck inputs are verified end to end through accepted text, audio assets, and `.apkg`/CSV/TSV artifacts.

v1.1 Card Quality Refresh was executed through Phase 08 on 2026-05-02. The planning state records the phase as complete with targeted validation passing, but the milestone has not been archived in `.planning/MILESTONES.md` yet.

v1.2 Phase 10 Local Kindle Normalization and Candidate Extraction was completed on 2026-05-05. Synthetic local Kindle HTML/text fixtures now parse locally, normalize into privacy-safe highlight records, extract deterministic vocabulary candidates, and expose a count-only preview command while keeping full highlight generation deferred to Phase 11.

v1.2 Phase 12 Highlight Generation, Audio, and QA was completed on 2026-05-05. Highlight examples now use source-profile validation and bounded redacted reading context, accepted highlight rows generate word and sentence audio, assembled highlight cards keep `Translation` learner-facing blank with blank `Image`, and source-aware QA reports prove privacy-safe behavior alongside existing frequency/custom regression evidence.

v1.2 Phase 13 Highlight Export and Template was completed on 2026-05-06. Highlight APKG, CSV, and TSV exports now use a dedicated `Multilang::Highlight Card` note type with exact English fields, no `Translation`, a responsive Definition-on-back template, fail-closed media/template validation, and regression evidence preserving existing frequency and word-list export behavior.

v1.2 was completed through Phase 16 on 2026-05-08. Local Kindle highlights, highlight export, phonetics export, and existing frequency/custom regressions were audited with 24/24 requirements mapped and complete.

v1.3 Phase 18 Text Field Remediation was completed on 2026-05-13. Normal generated cards now keep IPA fields to phonetic transcription or a safe word fallback, remediate learner-facing Definitions away from morphology-only metadata including the known `дости́чь` sense, and reject isolated-word Translations before accepted text can be exported.

v1.3 Phase 19 Normal Card Export and Responsive Template was completed on 2026-05-13. Normal generated-card APKG/CSV/TSV exports now omit the redundant `Front of Card` field, normal templates render the target word through `word`, sentence audio sits beside the example sentence with responsive flex CSS, and integrated tests prove highlight/manual/phonetics templates remain isolated.

v1.3 Phase 20 Word Audio Integrity Gate was completed on 2026-05-13. Word-audio metadata now has exact-match validation against exported `Word`, mismatched reusable WORD audio is regenerated during audio generation, and APKG/CSV/TSV exports fail before artifact creation when persisted word audio drifts from card snapshots.

v1.3 was completed on 2026-05-16 after Phases 17-21. Generated-card quality defects can now be audited, IPA/Definition/Translation defects are remediated before export, normal generated-card exports use the revised field/template contract, word-audio mismatches are regenerated or blocked, and shared v1.3 validators plus scanner-readable evidence prove the known defects do not recur across normal, custom word-list, highlight, and phonetics deck paths.

## Current Milestone: Ready for v1.4 Definition

**Goal:** Define the next milestone from the remaining product directions and known technical debt.

**Target features:** To be defined by `/gsd-new-milestone`.

## Next Milestone Goals

After v1.2, candidate directions from the archived v1 requirement seeds remain:

- Add language-specific generation and rendering rules for each supported language.
- Add sense-aware disambiguation before export for polysemous words.
- Add field-level regeneration for translation, text, or audio without regenerating the whole card.
- Add deck linting for missing audio, malformed IPA, repeated sentence patterns, and translation mismatch.
- Add field provenance and reusable glossary or translation-memory support.

## Requirements

### Validated

- [x] User can choose one of the 11 supported target languages before generation starts. _(v1.0)_
- [x] User can generate a 3-level frequency deck with 1000 cards per level for the selected language. _(v1.0)_
- [x] User can generate cards from a custom user-provided word list. _(v1.0)_
- [x] User receives complete Anki-ready cards with the fixed ten-field schema, blank `Image`, template-compatible definitions, hidden/revealed `Translation`, and stable export behavior. _(v1.0)_
- [x] User receives normalized lexical grounding, IPA, and deck-wide definition formatting. _(v1.0)_
- [x] User receives target-containing example sentences, matching translations, text quality validation, review reports, and targeted regeneration. _(v1.0)_
- [x] User receives word and sentence audio through Azure-first synthesis or documented fallback behavior. _(v1.0)_
- [x] User can export `.apkg`, CSV, and TSV artifacts with packaged playable audio references. _(v1.0)_
- [x] User can resume, monitor, and rerun jobs without silent duplicate card creation. _(v1.0)_
- [x] Normalize Kindle highlight exports locally into usable vocabulary candidates. _(v1.2 Phase 10)_
- [x] Generate privacy-safe highlight text/audio/card rows without replacing the existing frequency-deck or custom word-list flows. _(v1.2 Phase 12)_
- [x] Add a responsive highlight deck template with `Definition` on the back and no `Translation` field. _(v1.2 Phase 13)_
- [x] Update the normal card schema/template by removing redundant `Front of Card` and preserving responsive audio layout. _(v1.3 Phase 19)_
- [x] Audit generated decks for normalized card-quality defects and produce actionable issue reports. _(v1.3 Phase 17)_
- [x] Correct IPA, Definition, Translation, and audio-field alignment defects before export. _(v1.3 Phases 18 and 20)_
- [x] Add validation and regression evidence that prevents recurrence of the normalized issue catalog. _(v1.3 Phase 21)_

### Active

- [ ] Define v1.4 requirements and roadmap.

### Out of Scope

- Automatic image generation or image sourcing - the image field should stay blank because the user wants to add images manually.
- Using Tatoeba as the default sentence source without quality validation - v1.0 locked Tatoeba to a secondary-only filtered fallback path.
- Languages outside Portuguese, Spanish, English, French, German, Italian, Polish, Turkish, Romanian, Russian, and Dutch until a future milestone explicitly expands scope.
- Full spaced-repetition app or AI tutor - Anki remains the destination study tool.

## Context

The v1.0 codebase is a Python 3.12 project managed by uv. The runtime exposes CLI-first generation and export workflows, with typed Pydantic/domain contracts, SQLAlchemy/Alembic persistence, deterministic local/fallback adapters for tests, Azure Speech integration for audio, and genanki packaging for `.apkg` exports.

Before v1.3, normal exported cards preserve these fields:

- `SortIndex`
- `word`
- `Front of Card`
- `IPA`
- `Definitions`
- `Example Sentence`
- `Translation`
- `word_audio`
- `sentence_audio`
- `Image`

The preferred audio direction remains Azure TTS. The current code includes an Azure voice registry and fallback matrix for the supported languages.

v1.3 intentionally revises the normal generated-card export contract by removing redundant `Front of Card` from newly generated cards while keeping existing learner-facing fields, audio references, blank `Image`, and Anki-safe media behavior.

Known follow-up debt: one incomplete quick task remains for `260430-001-russian-card-quality-regression`, and full-suite collection/assertion drift still has failures outside the focused v1.3 evidence gate. Focused milestone evidence suites passed; the broad suite should be repaired before it is treated as authoritative again.

## Constraints

- **Languages**: v1 supports Portuguese, Spanish, English, French, German, Italian, Polish, Turkish, Romanian, Russian, and Dutch.
- **Deck Structure**: Cards are separated into 3 levels with 1000 cards per level.
- **Highlights Mode**: Kindle highlights are a new deck input mode and must not remove the existing frequency-deck mode.
- **Output Quality**: Example sentences and translations must be high quality; Tatoeba is secondary-only behind validation.
- **Audio Provider**: Audio should use Azure TTS if required voices are available, with documented fallback behavior.
- **Card Schema**: Generated decks must preserve the active requested field set and formatting; v1.3 intentionally removes redundant `Front of Card` from normal generated cards.
- **Engineering Quality**: The codebase must keep tests, fallback paths, deterministic contracts, and auditable persistence.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build around high-frequency vocabulary first | The initial product value is based on common words learners encounter most often | Validated in v1.0 through frequency-deck E2E evidence. |
| Use a 3-level deck structure with 1000 cards per level | The user defined this as the core learning progression | Validated in v1.0 with explicit level-window contracts and E2E samples across all levels. |
| Include a custom word-list mode in v1 scope | The user wants cards from vocabulary gathered during reading | Validated in v1.0 through custom word-list E2E export evidence. |
| Keep the image field blank | The user prefers to add images manually later | Validated in v1.0 export contract. |
| Use Azure TTS as the planned audio provider | The user selected Azure voices as the intended direction for audio generation | Validated in v1.0 with Azure adapter, fallback matrix, and human playback checks. |
| Use Python as the implementation backbone | Python best fits lexical ETL, Anki packaging, Azure Speech SDK, and testing needs | Locked in v1.0. |
| Re-evaluate sentence and translation sourcing instead of defaulting to Tatoeba | Existing quality concerns make source quality a first-class decision | Locked: Tatoeba is secondary-only behind filtering/reranking and validation. |
| Freeze the Anki export contract around the requested ten fields and project card template | Stable field order, blank `Image`, hidden/revealed `Translation`, and playable packaged audio define whether exports are useful in Anki | Validated in v1.0 with automated tests and approved Anki Desktop import/audio verification. |
| Treat milestone close as evidence-driven, not task-count driven | Stale artifacts can hide real gaps or false positives | Validated in Phase 7 with refreshed verification, requirements, and audit metadata. |
| Add Kindle highlights as a new mode instead of replacing frequency decks | The learner wants reading-derived vocabulary while preserving the shipped frequency-deck path | Pending in v1.2. |
| Normalize Kindle highlights locally instead of automating the external formatter website | A local formatter keeps generation reproducible, testable, and independent of a browser-only tool | Validated in v1.2 Phase 10 with local parser, candidate extraction, preview CLI, and regression evidence. |
| Keep highlight QA source-aware and privacy-safe | Raw reading text, paths, and book metadata may appear in private imports but must not leak to prompts/reports/artifacts | Validated in v1.2 Phase 12 with redacted context generation, source-aware review reports, and regression evidence. |
| Use a dedicated highlight note type and template | Highlight cards need English fields, no Translation, Definition on the back, responsive styling, and no leakage into frequency or word-list decks | Validated in v1.2 Phase 13 with APKG/CSV/TSV export evidence and regression coverage. |
| Treat card quality defects as validation failures before export | IPA repetition, morphology-only definitions, translation mismatches, and audio/word mismatches make learner decks unreliable | Pending in v1.3. |
| Validate word audio at generation and export boundaries | Stale or corrupted reusable audio can otherwise produce cards whose audio pronounces a different word than the displayed `Word` | Validated in v1.3 Phase 20 with exact metadata checks, regeneration, and export blocks. |
| Validate normalized issue coverage through executable fixtures | Narrative issue catalogs can drift unless every known defect maps to a runnable validator case | Validated in v1.3 Phase 21 with shared validators, JSON fixtures, and scanner-readable milestone evidence. |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):

1. Requirements invalidated? Move to Out of Scope with reason.
2. Requirements validated? Move to Validated with phase reference.
3. New requirements emerged? Add to Active.
4. Decisions to log? Add to Key Decisions.
5. "What This Is" still accurate? Update if drifted.

**After each milestone** (via `/gsd-complete-milestone`):

1. Full review of all sections.
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state.

---
*Last updated: 2026-05-16 after v1.3 milestone completion*
