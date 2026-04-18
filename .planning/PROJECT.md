# Multilang Anki Card Generator

## What This Is

Multilang is a multilingual Anki card generator focused on the most frequent words in a target language. It is meant to create high-quality study decks for learners of Portuguese, Spanish, English, French, German, Russian, and Dutch, with a separate mode for generating cards from a user-provided word list collected from reading.

The product generates structured Anki-ready cards with word data, phonetics, definitions, example sentences, translations, audio, and an empty image field that the user can fill manually later. AI-assisted generation is part of the intended approach, but the exact provider and supporting services still need research and validation.

## Core Value

Generate reliable, high-quality Anki cards for frequent vocabulary in the chosen language so the learner can study real words with accurate definitions, examples, translations, and audio.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Generate a 3-level frequency-based card set for each supported language, with 1000 cards per level.
- [ ] Produce complete Anki-ready cards with consistent fields, formatting, and export structure.
- [ ] Support a custom input mode where the user provides their own list of words and receives generated cards for those words.

### Out of Scope

- Automatic image generation or image sourcing — the image field should stay blank because the user wants to add images manually.
- Using Tatoeba as the default sentence source without quality validation — prior experience suggests example quality is not good enough.
- Languages outside Portuguese, Spanish, English, French, German, Russian, and Dutch for v1 — initial scope should stay focused.

## Context

The project idea started from the need to generate multilingual Anki cards based on the most frequent vocabulary instead of assembling decks manually. The user already knows about the `wordfreq` library as a possible source for ranking words, but is unsure whether it is the right fit for production use.

Each card should include these fields:
- `SortIndex` — rank position of the word by frequency
- `word` — the base word for the card
- `Front of Card` — the word itself
- `IPA` — phonetic transcription in a normalized format such as `/tolʲkɐ/ (tol-kah)`
- `Definitions` — meaning of the word using a consistent template across the deck
- `Example Sentence` — a sentence containing the word, with sentence-length rules still to be defined
- `Translation` — a high-accuracy translation of the example sentence
- `word_audio` — audio for the word
- `sentence_audio` — audio for the example sentence
- `Image` — blank field

Audio is intended to use Azure TTS, with user-provided preferred voices for German, English, Spanish, French, Italian, and Russian. Voice availability and exact model identifiers still need validation. Dutch is in language scope, but no voice preference was provided yet.

The implementation stack is still open between Python and JavaScript. The user wants the project to follow good architecture and engineering practices, including tests, fallbacks, and robust integrations with AI and supporting services.

The user also mentioned possible future integration patterns around OpenRouter, which matters for evaluating how AI generation should be routed, but that is not yet a locked product decision.

## Constraints

- **Languages**: v1 must support Portuguese, Spanish, English, French, German, Russian, and Dutch — these are the explicit target languages.
- **Deck Structure**: Cards must be separated into 3 levels with 1000 cards per level — this defines the core content structure.
- **Output Quality**: Example sentences and translations must be high quality — prior low-quality outputs from Tatoeba are a known concern.
- **Audio Provider**: Audio should use Azure TTS if the required voices are available — this is the user's preferred TTS direction.
- **Card Schema**: The generated deck must preserve the requested field set and formatting — Anki export usefulness depends on consistent structure.
- **Engineering Quality**: The codebase must follow architecture and good practices, with tests and fallbacks — reliability is a stated requirement, not a nice-to-have.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build around high-frequency vocabulary first | The initial product value is based on common words learners encounter most often | — Pending |
| Use a 3-level deck structure with 1000 cards per level | The user already defined this as the core learning progression | — Pending |
| Include a custom word-list mode in v1 scope | The user wants to generate cards from vocabulary gathered during reading | — Pending |
| Keep the image field blank | The user prefers to add images manually later | — Pending |
| Use Azure TTS as the planned audio provider | The user already selected Azure voices as the intended direction for audio generation | — Pending |
| Defer the stack decision between Python and JavaScript until research | The right ecosystem depends on frequency data, AI orchestration, translation quality, audio tooling, and export ergonomics | — Pending |
| Re-evaluate sentence and translation sourcing instead of defaulting to Tatoeba | Existing quality concerns make source quality a first-class decision | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-18 after initialization*
