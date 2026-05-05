# Multilang Anki Card Generator

## What This Is

Multilang is a Python CLI/batch pipeline for generating high-quality multilingual Anki vocabulary cards from supported-language frequency decks, user-provided word lists, and reading-derived vocabulary sources. v1.0 ships the first usable product slice for Portuguese, Spanish, English, French, German, Italian, Polish, Turkish, Romanian, Russian, and Dutch.

The product generates structured Anki-ready cards with word data, IPA, definitions, example sentences, translations where the deck type requires them, word audio, sentence audio, and an empty `Image` field that the user can fill manually later. v1.0 uses grounded lexical inputs, deterministic validation, Azure-first audio synthesis, and fixed-schema Anki export rather than relying on unverified generated text alone.

## Core Value

Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.

## Current State

**Shipped version:** v1.0 MVP on 2026-04-29  
**Milestone archive:** `.planning/milestones/v1.0-ROADMAP.md`  
**Requirements archive:** `.planning/milestones/v1.0-REQUIREMENTS.md`  
**Audit result:** passed with 23/23 requirements satisfied, 7/7 phases complete or verified, and 8/8 integration flows satisfied.

v1.0 provides the shipped CLI path for generation, review support, audio generation, and export. Representative custom word-list and frequency-deck inputs are verified end to end through accepted text, audio assets, and `.apkg`/CSV/TSV artifacts.

v1.1 Card Quality Refresh was executed through Phase 08 on 2026-05-02. The planning state records the phase as complete with targeted validation passing, but the milestone has not been archived in `.planning/MILESTONES.md` yet.

v1.2 Phase 10 Local Kindle Normalization and Candidate Extraction was completed on 2026-05-05. Synthetic local Kindle HTML/text fixtures now parse locally, normalize into privacy-safe highlight records, extract deterministic vocabulary candidates, and expose a count-only preview command while keeping full highlight generation deferred to Phase 11.

v1.2 Phase 12 Highlight Generation, Audio, and QA was completed on 2026-05-05. Highlight examples now use source-profile validation and bounded redacted reading context, accepted highlight rows generate word and sentence audio, assembled highlight cards keep `Translation` learner-facing blank with blank `Image`, and source-aware QA reports prove privacy-safe behavior alongside existing frequency/custom regression evidence.

## Current Milestone: v1.2 Kindle Highlights and Template Refresh

**Goal:** Add a highlights-based deck mode that automatically imports Kindle highlights from WebDAV, normalizes them locally, generates Anki cards from reading-derived vocabulary, and updates highlight and phonetics card templates for the new study flow.

**Target features:**

- Automatically fetch Kindle highlights from the configured WebDAV export location.
- Reimplement Kindle Formatter-style normalization inside Multilang instead of depending on the external formatter website.
- Add a new highlights deck mode alongside the existing frequency-deck and custom word-list flows.
- Generate highlight-specific cards with concise but grammatically richer example sentences.
- Support a highlight deck template where `Definition` is on the back, there is no `Translation` field, fields use English names, and the layout is centered and responsive.
- Refresh the phonetics card template with the provided front layout, `Sentence Translation` on the back, removed unused fields, and Multilang colors.

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

### Active

- [ ] Add automatic Kindle highlights ingestion from WebDAV as a new deck input source.
- [ ] Add a responsive highlight deck template with `Definition` on the back and no `Translation` field.
- [ ] Refresh the phonetics deck template while preserving required sentence translation behavior.

### Out of Scope

- Automatic image generation or image sourcing - the image field should stay blank because the user wants to add images manually.
- Using Tatoeba as the default sentence source without quality validation - v1.0 locked Tatoeba to a secondary-only filtered fallback path.
- Languages outside Portuguese, Spanish, English, French, German, Italian, Polish, Turkish, Romanian, Russian, and Dutch until a future milestone explicitly expands scope.
- Full spaced-repetition app or AI tutor - Anki remains the destination study tool.

## Context

The v1.0 codebase is a Python 3.12 project managed by uv. The runtime exposes CLI-first generation and export workflows, with typed Pydantic/domain contracts, SQLAlchemy/Alembic persistence, deterministic local/fallback adapters for tests, Azure Speech integration for audio, and genanki packaging for `.apkg` exports.

Each exported card preserves these fields:

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

Known follow-up debt: full-suite collection drift remains in tests that import removed private runtime template adapters. Focused milestone evidence suites passed; this should be handled before broad full-suite gating is treated as authoritative again.

## Constraints

- **Languages**: v1 supports Portuguese, Spanish, English, French, German, Italian, Polish, Turkish, Romanian, Russian, and Dutch.
- **Deck Structure**: Cards are separated into 3 levels with 1000 cards per level.
- **Highlights Mode**: Kindle highlights are a new deck input mode and must not remove the existing frequency-deck mode.
- **Output Quality**: Example sentences and translations must be high quality; Tatoeba is secondary-only behind validation.
- **Audio Provider**: Audio should use Azure TTS if required voices are available, with documented fallback behavior.
- **Card Schema**: The generated deck must preserve the requested field set and formatting.
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
*Last updated: 2026-05-05 after completing v1.2 Phase 12*
