# Domain Pitfalls

**Domain:** Multilingual AI-assisted language-learning Anki card generation
**Researched:** 2026-04-18
**Overall confidence:** HIGH for Anki/Azure constraints, MEDIUM for content-quality failure patterns

## Critical Pitfalls

These are the mistakes most likely to cause rework, unusable decks, or a loss of trust in the generated content.

### 1) Treating a “word” as a raw string instead of a lexical entry
**What goes wrong:** The system builds cards around surface forms without modeling lemma, part of speech, sense, inflection, or fixed expression status.

**Why it happens:** Frequency lists and user word lists look like simple strings, so teams postpone lexical modeling.

**Consequences:**
- Duplicate cards for inflected variants
- Wrong definitions for ambiguous forms
- Bad examples for verbs that need reflexive particles or required prepositions
- Inconsistent cards across languages with richer morphology

**Warning signs:**
- Same spelling appears twice with different meanings and no disambiguation
- Cards mix noun/verb/adjective senses under one definition block
- Portuguese/Spanish reflexive verbs, gendered forms, or article-dependent nouns look wrong
- Russian or German cards lose case/gender information needed for study

**Prevention strategy:**
- Define a canonical lexical record early: `lemma`, `surface_form`, `pos`, `sense_id`, `morphology`, `register`, `translation`, `example`, `audio_text`
- Separate lemma ranking from card rendering
- Require POS-aware generation and validation
- Add per-language morphology adapters instead of one universal formatter

**Phase to address:** Phase 1 - Content schema and lexical model

### 2) Using frequency lists as a ready-made curriculum
**What goes wrong:** Teams import top-N frequency data directly into the deck and assume “frequent” equals “good beginner card.”

**Why it happens:** Frequency data looks objective and scalable.

**Consequences:**
- Decks contain proper nouns, web noise, discourse fragments, abbreviations, or forms that are common in corpora but poor flashcards
- Levels feel random instead of pedagogically useful
- Cross-language decks become incomparable because the corpora differ

**Warning signs:**
- Top 500 includes names, broken tokens, numerals, or corpus artifacts
- Too many function words appear before more teachable content words
- Users ask why obvious learner vocabulary is missing while junk is included

**Prevention strategy:**
- Treat frequency as one ranking signal, not the curriculum itself
- Add a filtering layer for proper nouns, symbols, OCR/web noise, taboo content, and low-teachability items
- Define inclusion/exclusion rules per POS and per language
- Spot-audit each 100-word slice before scaling to 3000 cards/language

**Phase to address:** Phase 2 - Lexical sourcing and ranking pipeline

**Evidence:** `wordfreq` explicitly says its frequencies are a snapshot through about 2021 and unlikely to be updated again; it also mixes sources such as subtitles, web text, books, Twitter, and Reddit, which is useful for breadth but not a learner-ready curriculum by itself.

### 3) One-shot AI generation with no validation loop
**What goes wrong:** The system asks a model for definition + example + translation + IPA and trusts the response if it is syntactically valid JSON.

**Why it happens:** Structured output looks reliable, and early demos seem impressive.

**Consequences:**
- Example sentence does not actually match the target sense
- Translation is plausible but not faithful to the example
- Definitions are too advanced, too dictionary-like, or subtly wrong
- Quality drifts by language and by provider/model version

**Warning signs:**
- Example omits the target word or uses the wrong inflected form
- Back-translation of the example diverges from intended meaning
- Cards pass schema validation but fail human review
- Quality is good in English/Spanish and noticeably worse in Russian/Dutch

**Prevention strategy:**
- Split generation into stages: lexical analysis -> candidate content -> validation -> repair
- Use separate prompts/models for generation vs critique
- Add automatic checks: target word present, POS alignment, translation consistency, banned patterns, length bounds, register checks
- Maintain a human-reviewed benchmark set per language and compare every pipeline revision against it

**Phase to address:** Phase 3 - Content generation and QA pipeline

### 4) Letting low-quality example sources poison the deck
**What goes wrong:** Teams ingest example corpora because they are cheap and multilingual, but they contain unnatural, mistranslated, decontextualized, or learner-hostile sentences.

**Why it happens:** Example sourcing is the highest-volume content problem, so shortcuts are tempting.

**Consequences:**
- Cards feel robotic or bizarre
- Sentence translations are misleading
- TTS sounds unnatural because the source sentence was unnatural
- Users lose trust quickly because examples are the most visible quality signal

**Warning signs:**
- Sentences are grammatically valid but socially odd, rare, or humorously unnatural
- Literal translations preserve syntax from another language
- Many examples read like subtitles, fragments, or isolated dialogue turns

**Prevention strategy:**
- Maintain a source quality rubric before any bulk ingestion
- Score examples for naturalness, pedagogical usefulness, and translation faithfulness
- Reject sources that cannot provide provenance and consistent quality
- Prefer generation-plus-validation or curated sources over raw parallel corpora

**Phase to address:** Phase 3 - Example sourcing and sentence QA

### 5) Ignoring language-specific grammar and register rules
**What goes wrong:** A single “universal card template” erases differences that matter for learners: articles, gender, aspect, separable prefixes, reflexive markers, case government, politeness, or formality.

**Why it happens:** Teams optimize for shared schema and underestimate what must vary by language.

**Consequences:**
- Cards are technically filled but pedagogically weak
- Learners memorize incomplete forms
- Examples teach the wrong register or unnatural collocations

**Warning signs:**
- German nouns lack article/gender policy
- Russian verbs/nouns omit aspect or case cues
- Spanish/Portuguese verbs lose reflexive markers
- Definitions and examples mix formal and colloquial registers without labeling

**Prevention strategy:**
- Keep one canonical schema, but allow language-specific rendering rules
- Define mandatory metadata per language family before deck generation
- Add language-specific acceptance tests and review checklists

**Phase to address:** Phase 1 - Schema design, then Phase 6 - language-by-language expansion

### 6) Assuming Azure TTS compatibility without building a voice matrix
**What goes wrong:** The system assumes every in-scope language/locale has the desired voice, accent, and SSML behavior, then discovers late that some voices or locale variants differ from expectations.

**Why it happens:** Voice support looks broad, so teams skip capability inventory.

**Consequences:**
- Broken synthesis for some languages or accents
- Inconsistent audio quality across decks
- Last-minute schema changes because audio text must differ from display text

**Warning signs:**
- Voice IDs are hard-coded in prompts/config without smoke tests
- Some languages use locale fallback silently
- Audio sounds fine for the word but poor for full sentences
- Preferred accents are unavailable or inconsistent with target market

**Prevention strategy:**
- Build and version a voice capability matrix per target language and locale
- Smoke-test every chosen voice with both single words and full sentences
- Separate `display_text`, `tts_text`, and `tts_voice`
- Define fallback voices before launch, not after failures

**Phase to address:** Phase 4 - Audio integration and SSML compatibility

**Evidence:** Azure documents locale-specific voice availability and notes that multilingual voice language/accent behavior depends on supported locales and SSML; non-multilingual voices do not support `<lang xml:lang>`.

### 7) Treating pronunciation/IPA as a formatting problem
**What goes wrong:** IPA is generated or normalized as decorative text instead of as a language-specific pronunciation artifact.

**Why it happens:** IPA looks like “just another field.”

**Consequences:**
- Incorrect or inconsistent phonetics across cards
- Mixing phonemic and phonetic notation
- Romanized helper text drifts from IPA and from TTS pronunciation

**Warning signs:**
- Same word gets different IPA in different runs
- Broad transcription for one language and narrow transcription for another with no policy
- IPA is copied from the wrong regional standard

**Prevention strategy:**
- Define a pronunciation policy per language before generation
- Separate authoritative pronunciation sourcing from LLM paraphrasing
- Normalize output to one notation style per language and test for stability
- Allow missing IPA when confidence is low instead of fabricating it

**Phase to address:** Phase 2 - Lexical enrichment and pronunciation sourcing

### 8) Designing export late instead of as a product contract
**What goes wrong:** Teams get content generation “working” first and postpone Anki import/export rules until the end.

**Why it happens:** CSV export seems trivial.

**Consequences:**
- Broken UTF-8 import for multilingual text
- Wrong field counts due to unescaped delimiters/newlines
- Duplicate handling updates the wrong notes
- Audio fields do not play after import

**Warning signs:**
- CSV rows have variable column counts
- Example sentences include raw newlines or separators without escaping
- Import requires manual clicking/tweaking to succeed
- Re-importing the same deck creates duplicates unexpectedly

**Prevention strategy:**
- Freeze the Anki note schema early and treat it as an integration contract
- Add golden-file tests for importable UTF-8 text exports
- Test round-trip behavior: import -> reimport update -> media check
- Decide early whether stable IDs live in the first field, a dedicated ID field, or both

**Phase to address:** Phase 1 - Schema contract, then Phase 5 - export verification

**Evidence:** Anki requires plain UTF-8 text for text imports, determines field count from the first row, treats the first field as the default uniqueness key for duplicate handling, and requires media references like `[sound:file.mp3]` to live in fields rather than templates.

### 9) Inconsistent field formatting across languages
**What goes wrong:** Each language pipeline gradually invents its own formatting for definitions, examples, IPA, and audio references.

**Why it happens:** Teams add language support incrementally without a strict field contract.

**Consequences:**
- Deck templates become brittle
- Export/import behavior changes by language
- Users cannot trust what each field means
- Regression testing becomes expensive

**Warning signs:**
- Definitions are bullets in one language and prose blocks in another
- Some decks include HTML, others plain text, others mixed formatting
- Audio references use different naming conventions by language

**Prevention strategy:**
- Publish a canonical field-spec document with examples for every field
- Create formatters that emit one normalized representation only
- Add schema and snapshot tests at the record level

**Phase to address:** Phase 1 - Field contract and formatting rules

## Moderate Pitfalls

### 10) Coupling translation quality to definition quality
**What goes wrong:** The system uses one translation output to stand in for both sense gloss and sentence translation.

**Warning signs:**
- Word meaning is correct but sentence translation misses idiom or syntax
- Same translation text appears in both `Definitions` and `Translation`

**Prevention strategy:**
- Treat lemma definition and example translation as separate tasks
- Validate sentence translation against the actual example, not the isolated headword

**Phase to address:** Phase 3 - Translation validation

### 11) Not separating display text from TTS text
**What goes wrong:** The exact same string is used for rendered fields, export fields, and synthesis input.

**Warning signs:**
- TTS misreads abbreviations, punctuation, IPA, clitics, or parenthetical glosses
- Teams strip useful learner-facing formatting because audio breaks on it

**Prevention strategy:**
- Store dedicated `tts_text_word` and `tts_text_sentence`
- Keep UI formatting out of synthesis inputs
- Use SSML only after plain-text baselines pass

**Phase to address:** Phase 4 - Audio pipeline design

### 12) No stable note identity/versioning strategy
**What goes wrong:** Regenerated decks cannot reliably update existing Anki notes.

**Warning signs:**
- Re-import creates duplicates after minor formatting changes
- The same lemma changes deck position or identity between runs

**Prevention strategy:**
- Define deterministic note IDs from language + lemma + POS + sense
- Keep a stable import key in the first field or dedicated GUID workflow
- Version records and exports explicitly

**Phase to address:** Phase 5 - Export/update semantics

## Minor Pitfalls

### 13) Overfitting sentence length rules
**What goes wrong:** Teams optimize only for shortness, producing unnaturally clipped examples.

**Warning signs:**
- Sentences are simple but not something a native speaker would say
- High rejection rate from reviewers for “technically fine, pedagogically bad” examples

**Prevention strategy:**
- Optimize for comprehensibility and naturalness, not minimum token count alone
- Use length bands by language and level rather than one global hard cap

**Phase to address:** Phase 3 - Example quality policy

### 14) Hiding low confidence instead of surfacing it
**What goes wrong:** Weak cards are emitted without confidence metadata or review flags.

**Warning signs:**
- Same pipeline generates both excellent and dubious cards with no distinction
- Reviewers cannot target the worst items first

**Prevention strategy:**
- Attach confidence and provenance to every field group
- Route low-confidence cards to review or exclusion

**Phase to address:** Phase 3 - QA instrumentation

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 1 - Schema & note design | Freezing Anki fields before lexical modeling, or vice versa | Define lexical record and Anki field contract together; include stable IDs and language-specific required metadata |
| Phase 2 - Frequency & lexical sourcing | Shipping raw top-N frequency lists | Add teachability filters, POS/sense enrichment, and manual slice audits |
| Phase 2 - Pronunciation enrichment | Fabricated or inconsistent IPA | Set language-specific pronunciation policy and confidence thresholds |
| Phase 3 - Example/definition generation | One-pass LLM generation accepted as truth | Use generate -> validate -> repair pipeline with benchmark decks |
| Phase 3 - Translation layer | Sentence translation not faithful to example | Validate against example sentence, not headword gloss |
| Phase 4 - TTS integration | Discovering voice/locale issues after content is generated | Build a voice matrix and synthesis smoke tests before bulk generation |
| Phase 5 - Anki export | CSV/media issues discovered only in manual import | Add golden import tests, UTF-8 checks, escaped newline tests, and media verification |
| Phase 6 - New language rollout | Reusing the same heuristics across all languages | Add per-language acceptance criteria and staged rollout by language |

## Most Important Planning Implications

1. **Do not start with bulk generation.** Start with schema, lexical identity, and export contract.
2. **Treat example quality as the core product risk.** This deserves its own validation phase.
3. **Audio should not be “just another field.”** Voice/locale validation must happen before large-scale synthesis.
4. **Plan for language-specific rules from day one.** Shared schema is good; shared heuristics are not enough.

## Sources

- Project context: `/home/miguel/Programming/Multilang/.planning/PROJECT.md`
- Anki Manual - Text Files: https://docs.ankiweb.net/importing/text-files.html
- Anki Manual - Media: https://docs.ankiweb.net/media.html
- Anki Manual - Field Replacements / media field references: https://docs.ankiweb.net/templates/fields.html
- Azure Speech language and voice support: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts
- Azure Speech SSML voice/language behavior: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice
- wordfreq README and sunset note: https://github.com/rspeer/wordfreq/blob/master/README.md
