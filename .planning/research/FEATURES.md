# Feature Landscape

**Domain:** multilingual AI-assisted Anki vocabulary card generator
**Project:** Multilang
**Researched:** 2026-04-18
**Overall confidence:** MEDIUM

## Executive Take

In this category, users do **not** expect a full language-learning platform first. They expect a tool that turns vocabulary inputs into **clean, accurate, Anki-ready notes** with very little manual cleanup. The bar is especially high for **example sentence quality, translation quality, audio coverage, and export reliability**.

Products adjacent to this space consistently emphasize: fast vocabulary capture, context-aware meaning, flashcard generation, spaced-repetition compatibility, and export/use inside Anki. For Multilang specifically, the winning v1 is not “more AI”; it is **better controlled output quality** for multilingual vocabulary decks.

## Table Stakes

Features users expect. Missing these makes the product feel incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| Language selection for supported deck languages | Core entry point; users must choose target language before generation | Low | None | Must be explicit and constrained to the 7 v1 languages |
| Frequency-list deck generation | Your core promise is high-frequency vocabulary decks; without this there is no product | Medium | Language selection, frequency data source | Needs stable ranking source and level boundaries |
| Custom word-list import | User-provided vocabulary is a common expectation in vocab tooling and is explicitly in project scope | Medium | Language selection, parsing/validation | Accept plain text/CSV; show rejected rows clearly |
| Fixed Anki-ready card schema | Users expect consistent fields and import without manual remapping pain | Medium | Card model design, export pipeline | Must preserve requested fields: rank, word, IPA, definitions, sentence, translation, audio, blank image |
| CSV/TSV export that imports cleanly into Anki | Export reliability is table stakes because Anki is the destination product | Medium | Fixed schema, escaping/encoding rules | Must honor UTF-8, quoting, HTML/audio syntax, predictable column order |
| Word-level linguistic enrichment | A bare word list is not enough; users expect meaning and pronunciation data | Medium | Lexical data sources, normalization | Includes lemma/headword handling, part of speech if available, IPA, definitions |
| Example sentence generation or sourcing | Context is expected for vocab learning; bare definitions feel weak | High | Word enrichment, generation/sourcing pipeline | Must enforce sentence-length and readability rules |
| High-quality sentence translation | Especially critical here; poor translations destroy trust fast | High | Example sentence quality, translation pipeline | Translation must match the sentence actually shown, not generic word meaning |
| Audio for word and sentence | Common expectation for language flashcards, especially pronunciation training | Medium | TTS provider, field schema | Must generate both `word_audio` and `sentence_audio` consistently |
| Inline quality review/edit before export | Users expect to fix bad cards instead of regenerating entire batches | Medium | Generation pipeline, UI/CLI review surface | Even a minimal review queue is better than opaque batch output |
| Duplicate detection / idempotent regeneration | Users frequently re-run batches; duplicates and drift are painful in Anki workflows | Medium | Stable identifiers, export rules | Should support update vs skip behavior |
| Batch progress, failure visibility, retry | Long-running AI/TTS jobs fail sometimes; users expect recoverability | Medium | Queue/job orchestration | Need per-card status and resumability |

## Differentiators

Features that would create meaningful competitive advantage for this specific product.

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| Quality-gated sentence pipeline | Best differentiator because user cares strongly about sentence quality; reject awkward, too-long, low-frequency, or non-idiomatic examples before export | High | Example generation, validation rules, review UI | Make quality policy explicit rather than “AI wrote something” |
| Quality-gated translation pipeline | Strongest trust differentiator; translation should preserve nuance, register, and sentence meaning | High | Sentence pipeline, translation validation | Prefer translation checks against source sentence and target word sense |
| Source-aware card provenance | Lets users see whether a field came from lexicon, AI, or TTS and decide what to trust | Medium | Metadata model, export/review surface | Important for debugging and user trust |
| Per-language generation rules | Better than one generic pipeline; each language has different morphology, clitics, articles, stress, and tokenization issues | High | Language config layer | Especially valuable for Russian and Portuguese; likely needed for quality |
| Sense disambiguation for polysemous words | Prevents “wrong definition, right spelling” cards, a common low-quality failure mode | High | Lexical data + sentence context | High leverage for frequent words with multiple meanings |
| Register/frequency-aware example selection | Produces study material that feels natural and useful rather than literary or weirdly formal | High | Frequency metadata, quality scoring | Good place to outperform generic AI outputs |
| Human-in-the-loop approval workflow | Lets users approve only flagged cards, reducing total review effort while preserving trust | Medium | Quality scoring, review UI | Start with review-required flags, not full editor complexity |
| Regenerate-by-field controls | Much better UX than regenerating the whole card when only translation/audio is bad | Medium | Field-level job model | Practical and highly valuable |
| Consistency scoring / deck linting | Catch malformed IPA, missing audio, repeated example patterns, translation mismatch, and formatting drift before export | High | Validation layer | Strong differentiator for “export-ready” promise |
| Reusable user glossary / protected translations | Keeps recurring words translated consistently across decks and custom lists | Medium | User settings, term memory | Particularly useful for multilingual users and domain-specific vocab |

## Anti-Features

Features to deliberately not build in early phases.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Full spaced-repetition app competing with Anki | Duplicates Anki’s job and expands scope massively | Export cleanly to Anki and optimize note quality |
| Automatic image generation/sourcing | Already out of scope; adds cost, copyright risk, and QA burden | Keep image field blank as planned |
| Broad “learn from any website/video” browser-extension workflow in v1 | Valuable, but it changes product shape from generator to platform | Focus on frequency decks + custom word lists first |
| AI conversation/chat tutor | Common adjacent feature, but not necessary for card generation | Invest that effort in sentence/translation quality |
| Support for many more languages in v1 | Multiplies QA surface and language-specific edge cases | Make the 7 target languages excellent first |
| Rich deck styling/theme builder | Nice-to-have but not core to learning value | Ship one well-documented note template |
| Fully automatic publishing/sharing marketplace | Moderation and quality control become a product of their own | Export files locally first |

## Recommended MVP Feature Set

Prioritize these first:

1. **Frequency-list generation by language and level**
2. **Custom word-list import**
3. **Stable Anki-ready schema + reliable CSV/TSV export**
4. **Word enrichment: normalized word, IPA, definitions**
5. **High-quality example sentence generation/sourcing**
6. **High-quality sentence translation**
7. **Word audio + sentence audio generation**
8. **Minimal review queue with per-card accept/edit/regenerate**
9. **Duplicate handling and resumable batch jobs**

## Feature Dependencies

```text
Language selection
  → Frequency-list generation
  → Custom word-list import

Frequency-list generation / Custom word-list import
  → Word normalization + lexical enrichment
  → Stable card schema

Word normalization + lexical enrichment
  → Example sentence generation/sourcing

Example sentence generation/sourcing
  → Sentence translation
  → Sentence audio

Stable card schema
  → Anki export
  → Duplicate detection

Quality scoring / validation
  → Review queue
  → Field-level regeneration
  → Deck linting
```

## Scoping Guidance

### Phase 1: Must-have foundation
- Language selection
- Frequency-list ingestion
- Custom word-list ingestion
- Stable schema
- Export pipeline

### Phase 2: Core content quality
- IPA/definitions
- Example sentence generation/sourcing
- Translation generation
- Audio generation

### Phase 3: Trust and workflow quality
- Review/edit/regenerate flow
- Duplicate/update behavior
- Retry/resume behavior
- Validation/linting

### Phase 4: Competitive differentiation
- Per-language rules
- Sense disambiguation
- Provenance metadata
- Reusable glossary / translation memory

## What to Treat as the Real Product Constraint

The hard part is **not** generating cards; it is generating cards that users do not need to repair manually. For this product, sentence quality and translation quality are not secondary enrichment features. They are the product.

## Sources

- Anki Manual — Text file import requirements, media syntax, duplicate/update behavior: https://docs.ankiweb.net/importing/text-files.html **(HIGH confidence)**
- Readlang homepage — click-to-translate, flashcards, AI context explanations, export flashcards: https://readlang.com/ **(MEDIUM confidence; official marketing page)**
- Readlang features page — vocab manager, export to Anki, flashcards, AI context explanations: https://readlang.com/features **(MEDIUM confidence; official marketing page)**
- Migaku FAQ / Tools + Features — media-rich flashcards, dictionary/context explanations, text analysis, one-click card creation: https://migaku.com/faq/features **(MEDIUM confidence; official product page)**

## Confidence Notes

- **HIGH:** Anki import/export expectations and media formatting requirements.
- **MEDIUM:** Feature expectations inferred from adjacent official product pages (Readlang, Migaku).
- **LOW:** None stated as authoritative; where market-wide expectations are inferred from overlap across adjacent products, they are framed as recommendations rather than hard facts.
