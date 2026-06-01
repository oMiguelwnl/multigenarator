# Feature Landscape: v2.0 Classical Latin MVP

**Domain:** Classical Latin Anki vocabulary deck generation for Portuguese-speaking learners  
**Project:** Multilang  
**Researched:** 2026-06-01  
**Overall confidence:** MEDIUM-HIGH

## Executive Take

The Latin MVP should feel like a new **Latin reading-card mode**, not a minor addition to the existing modern-language frequency pipeline. From the user's perspective, the command should generate a small reviewed deck of **50 Classical Latin cards** ordered by **lemma frequency**, with every card built around a real or clearly marked reliable Latin sentence, Portuguese meaning/explanation, a short `Gramatica` field, traceable source, review status, and word/sentence audio.

The MVP should optimize for **trust and didactic usefulness** over scale. A 50-card deck is valuable only if the learner can see why each lemma was selected, where the sentence came from, what the target form is doing grammatically, and whether the card has been reviewed. Do not promise a full 3000-card Latin deck yet; use the MVP to validate the card contract, source traceability, grammar-note format, review workflow, audio quality, and APKG export.

The Rafael Falcon reference should become product behavior: cards must keep Latin in context, progress from simpler sentence structures to more complex ones, explain the target form briefly in Portuguese-facing grammar terms, and avoid isolated word-list study. Frequency remains the primary ordering principle, but the first 50 should be **frequency filtered through didactic suitability**: a high-frequency lemma with an opaque poetic construction can be deferred in favor of a still-common lemma with a clearer first reading context.

## Scope Recommendation

### Build in v2.0 Latin MVP

1. A separate `latin` / `classical-latin` generation path that does not regress existing modern-language frequency, custom word-list, highlight, review, audio, or export flows.
2. A curated **50-card** MVP, not 300/1000/3000 cards.
3. Lemma-based ranking with stored `frequency_rank` and `frequency_source` metadata.
4. Sentence selection from traceable Classical Latin or clearly marked didactic/reliable sources.
5. Portuguese learner-facing fields: short word translation, sentence translation, and short `Gramatica`.
6. Latin-specific card schema and Anki template/export contract.
7. Review workflow with `needs_review`, `approved`, and `rejected` status.
8. Word audio and sentence audio with provider/quality metadata; audio can be marked experimental if TTS quality is not yet sufficient.
9. APKG plus CSV/TSV evidence export for the 50-card deck.

### Explicitly defer

- Greek.
- Ecclesiastical/medieval/neolatin variants as first-class targets.
- Full 3-level × 1000-card Latin deck.
- Automatic card generation at scale without human review.
- Complex poetry-heavy reading progression.
- AI tutor, grammar lesson course, or SRS replacement.
- Automatic image generation or image sourcing.

## Table Stakes

Features users should expect in the Latin MVP. Missing items make the deck feel unreliable or out of scope.

| Feature | Why Expected | Complexity | Depends on Existing Behavior | Acceptance Signals / REQ Seed |
|---------|--------------|------------|-------------------------------|-------------------------------|
| Separate Classical Latin mode | Latin needs different frequency, morphology, source, grammar, and TTS rules than v1 modern languages | Medium | CLI/job routing, deck type isolation, regression evidence | **LATIN-MODE-01:** User can generate Latin MVP without changing existing language modes; existing frequency/custom/highlight smoke tests still pass |
| 50-card MVP size cap | User explicitly wants a small Classical Latin MVP before scaling | Low | Batch generation limits, export naming | **LATIN-SCOPE-01:** Default Latin MVP produces exactly 50 accepted cards unless user passes a smaller test limit |
| Classical Latin variant marker | Prevents drifting into ecclesiastical, medieval, or modern Latin pronunciation/source conventions | Low-Medium | Language registry/config | **LATIN-VARIANT-01:** Deck metadata and reports identify `la` / Classical Latin; unsupported Latin variants fail with clear message |
| Frequency by lemma | Latin inflection makes surface-form frequency misleading | High | New Latin frequency asset/import path | **LATIN-FREQ-01:** Every card has `lemma`, `frequency_rank`, and `frequency_source`; ranking is by lemma, not surface form |
| Curated first-50 selection | Fully automated Latin analysis is too risky for learner content | Medium | Review report workflow, fixtures | **LATIN-CURATE-01:** First MVP list is stored/versioned and reproducible; rejected/replaced lemmas are recorded with reason |
| Target form in sentence context | Rafael Falcon-style reading requires the learner to study Latin inside a phrase/sentence | Medium | Existing target-containing sentence validators | **LATIN-SENT-01:** Front shows `target_form` and `latin_sentence`; validator confirms the exact form or accepted enclitic/orthographic variant appears |
| Traceable sentence source | Classical texts and didactic sentences must be auditable | Medium | Provenance fields/export | **LATIN-SOURCE-01:** Every accepted card has source type, citation, URL/work/line when available, and `source_license_note` or local provenance note |
| Portuguese word translation | User wants Portuguese translations/explanations | Medium | Existing translation field validation adapted to PT | **LATIN-PT-01:** Every card has `short_translation_pt`; empty/English-only translations fail validation |
| Portuguese sentence translation | Learner needs the contextual sentence meaning, not just a dictionary gloss | Medium-High | Translation QA/remediation pipeline | **LATIN-PT-02:** Every card has `sentence_translation_pt`; it must correspond to the displayed Latin sentence and target sense |
| Short `Gramatica` field | Mandatory differentiator for Latin; explains target form in context | High | New morphology/grammar formatter | **LATIN-GRAM-01:** Every card has a concise `Gramatica` string matching the approved pattern and using `Genitivus` spelling |
| No separate learner-facing `Classe` field | Seed decision says class can exist internally but not on study card | Low | Export schema/template isolation | **LATIN-SCHEMA-01:** APKG/CSV/TSV Latin exports contain no final `Classe` study field |
| Review status | Latin grammar/source/translation quality needs explicit human approval | Medium | Existing review reports and validation gates | **LATIN-REVIEW-01:** Cards move through `needs_review`, `approved`, `rejected`; export can be configured to include only approved cards |
| Word and sentence audio | User requested both, and existing Multilang value includes audio | Medium-High | Existing audio generation, media packaging, audio integrity gates | **LATIN-AUDIO-01:** Each exported approved card has playable word and sentence audio or a documented experimental/blocked status according to milestone policy |
| Audio provider/quality metadata | Latin TTS may be weak; user needs transparency | Medium | Audio manifest/provider metadata | **LATIN-AUDIO-02:** Audio records store provider, voice, pronunciation policy, generated text, quality status, and fallback reason |
| Blank `Image` field | Existing product decision remains | Low | Existing export schema behavior | **LATIN-IMAGE-01:** Latin exports include `Image` but leave it blank |
| APKG/CSV/TSV export evidence | Existing product is Anki-first and validates exports | Medium | genanki/export tests, media validation | **LATIN-EXPORT-01:** MVP exports APKG, CSV, and TSV with stable field order, packaged audio, and import/template evidence |

## Differentiators

These should be part of the MVP if possible because they make the Latin deck distinctly better than generic generated vocabulary cards.

| Feature | Value Proposition | Complexity | Notes / Acceptance Signals |
|---------|-------------------|------------|----------------------------|
| Rafael Falcon-style progression rules | Makes the 50-card deck feel like guided reading, not a random frequency list | High | Start with clearer sentences and common syntactic roles; delay hard poetic inversions, dense subordinate clauses, and ambiguous forms unless reviewed |
| Didactic suitability score | Balances frequency with readability for first exposure | Medium | Store reason codes such as `simple_clause`, `clear_case`, `common_verb`, `poetic_complexity_deferred` |
| Source-type labeling | Lets user know if a sentence is original classical text, adapted didactic Latin, or reliable reference sentence | Medium | Use values like `classical_text`, `adapted_didactic`, `reference_example`; adapted sentences must not masquerade as original citations |
| Grammar uncertainty marking | Avoids false confidence on ambiguous forms | Medium | Allow `revisar contexto` / `analysis_uncertain=true`; export should block uncertain cards unless milestone allows reviewed uncertainty |
| Enclitic-aware target matching | Latin common forms like `virumque` should map to `virum`/`vir` without losing traceability | Medium-High | Validator should recognize `-que`, `-ve`, `-ne` handling and record normalized target span |
| Portuguese didactic wording style | Aligns with target learner and Rafael Falcon reference | Medium | Prefer concise Portuguese explanations and Latin case labels; avoid long English-like grammar prose |
| Latin-specific tags/subdeck naming | Helps Anki organization | Low | Tags: `multilang`, `latin`, `classical-latin`, source/work slug, review status |
| Audio A/B evaluation report | TTS quality is uncertain; comparison evidence builds trust | Medium | For candidate providers, store sample text, provider, reviewer rating, and chosen default/fallback |

## Anti-Features

Features to explicitly not build in this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Full 3000-card Latin deck | Scale will amplify source, frequency, morphology, translation, and audio errors | Validate 50 reviewed cards first; later milestones can scale to 300, 1000, then 3000 |
| Greek support | User explicitly scoped this milestone to Latin only | Keep Greek as a separate future milestone |
| Isolated lemma-only cards | Conflicts with Rafael Falcon-style contextual reading | Always show target form in a Latin sentence |
| Surface-form frequency ranking | Inflection would overrepresent forms and split one lemma into many ranks | Rank by lemma and store target form separately |
| Untraceable generated Latin sentences | User wants real or reliable sources; generated-only sentences reduce trust | Use classical citations or clearly labeled didactic/adapted sources with provenance |
| Pretending adapted sentences are classical quotations | Misleads learners and corrupts source traceability | Mark adapted/didactic sentences explicitly |
| Long poetry-first examples | First 50 cards should prove the study workflow, not overwhelm the learner with difficult syntax | Select short, readable contexts; defer dense poetic lines unless exceptionally useful |
| Long grammar lectures in `Gramatica` | The field is meant to be short and direct | Keep one-line morphology/function notes; defer full grammar explanations to future lessons/references |
| Separate `Classe` field on the study card | Seed decision says it is unnecessary and clutters the card | Keep part of speech inside `Gramatica` and optional internal metadata only |
| Exporting unreviewed cards as if approved | Latin learner content needs human QA | Default export to approved cards or visibly tag/report unreviewed status |
| Treating audio as solved because Azure multilingual voices exist | Azure docs list multilingual voices but no dedicated Latin locale; Latin quality must be tested | Run TTS comparison; use eSpeak NG or other fallback if better; mark quality honestly |
| Blocking all progress until perfect Latin TTS exists | Audio quality is important, but the MVP can validate the rest of the pipeline with experimental audio if transparent | Include audio metadata and review status; decide milestone gate after sample evaluation |
| Automatic images | Existing project says image field stays blank | Preserve blank `Image` field |
| AI-only morphology/grammar | Hallucinated case/function notes can teach wrong grammar | Ground with Latin morphology tools/data and require review |

## Future / Deferred Features

| Future Feature | Why Defer | Prerequisites |
|----------------|-----------|---------------|
| 300-card Latin pilot | Useful next scale after MVP, but too large before grammar/source/audio contract is validated | Approved first-50 deck, stable source/frequency workflow, reviewer process |
| Full 3×1000 Latin deck | Final target shape, but requires large curated assets and stronger automation | 300-card pilot evidence, frequency corpus decision, source licensing confidence |
| Multiple Latin tracks | Ecclesiastical, medieval, legal, or Vulgate tracks need different source/pronunciation assumptions | Classical MVP complete; variant registry design |
| Rich grammar lessons | Valuable but outside Anki vocabulary-card MVP | Stable `Gramatica` taxonomy and maybe separate note/template type |
| Interactive reviewer UI | Review workflow can start from reports/files | Persistent review states, edit/regenerate operations, reviewer needs clarified |
| Field-level regeneration for Latin | Useful for fixing only grammar/translation/audio | Latin schema and validators stabilized |
| Human-recorded audio pack | May be best quality but costly | Final pronunciation policy, script list, recording process |
| Source corpus browser | Nice for selecting sentences | Corpus ingestion/indexing, licensing review |
| Sense-aware multiple cards per lemma | Some frequent lemmas need multiple senses/forms | First one-card-per-lemma MVP validated; sense taxonomy |
| Cloze or parsing drills | Could deepen study but changes card type | Basic reading-card note type proven |

## Feature Dependencies

```text
Latin mode isolation
  → Latin config/variant metadata
  → Latin card schema/template/export
  → Regression tests for existing deck modes

Frequency source selection
  → Lemma-ranked first-50 candidate list
  → Didactic suitability filtering
  → Curated MVP deck manifest

Sentence source ingestion/selection
  → Source provenance fields
  → Target form matching/enclitic handling
  → Portuguese translation
  → Gramatica generation/review

Morphology/grammar analysis
  → Gramatica formatter
  → Review status decisions
  → Validation gates before export

TTS provider evaluation
  → Word audio generation
  → Sentence audio generation
  → Audio manifest quality metadata
  → APKG media packaging

Review workflow
  → Approved-only export policy
  → Evidence artifacts for 50-card MVP
```

## MVP User Workflow

From the user's perspective, the MVP should work like this:

1. User runs a Latin MVP command, e.g. `multilang generate latin --mvp 50` or equivalent.
2. Multilang loads a curated lemma-frequency manifest for Classical Latin.
3. For each selected lemma, Multilang uses a reviewed target form and a traceable Latin sentence.
4. It prepares Portuguese `short_translation_pt` and `sentence_translation_pt`.
5. It prepares a short `Gramatica` line describing the target form in that sentence.
6. It generates word and sentence audio using the selected Latin TTS provider/fallback.
7. It writes a review report where cards are `needs_review`, `approved`, or `rejected`.
8. User/reviewer approves or rejects cards.
9. Multilang exports approved cards to APKG/CSV/TSV with the Latin note type and packaged audio.
10. The resulting Anki card shows Latin context on the front and Portuguese explanation/source/grammar on the back.

## Recommended Latin Card Contract

### Front

| Field | User-visible behavior | Notes |
|-------|-----------------------|-------|
| `target_form` | Main prompt word/form | Form as it appears in sentence, e.g. `virum` or accepted span inside `virumque` |
| `latin_sentence` | Main reading context | Short enough for MVP review; target should be visually identifiable via template if feasible |
| `word_audio` | Plays target form | Provider metadata stored separately/internal or export evidence |
| `sentence_audio` | Plays full Latin sentence | Must match displayed sentence text |
| `Image` | Blank | User fills manually later |

### Back

| Field | User-visible behavior | Notes |
|-------|-----------------------|-------|
| `lemma` | Dictionary/canonical form | Should appear on back, not front, to preserve target-form recall |
| `short_translation_pt` | Short Portuguese meaning | Contextual enough for the displayed sentence |
| `sentence_translation_pt` | Portuguese sentence translation | Natural Portuguese, not a word-by-word gloss unless chosen for didactic clarity |
| `Gramatica` | Short morphology/syntax note | Example: `virum: subst masc, 2a declinacao, Accusativus singularis, OD.` |
| `source` | Citation/provenance | Example: `Vergil, Aeneid 1.1` plus URL/work metadata where available |
| `review_status` | Optional visible or tag/report | At minimum must exist internally/export report; visible field is acceptable if user wants auditability |

### Internal / metadata fields

- `language_code`: `la`
- `variant`: `classical`
- `frequency_rank`
- `frequency_source`
- `source_type`
- `source_url` / `work_id` / `line_ref` where available
- `grammar_analysis_status`
- `audio_provider`, `audio_voice`, `audio_quality_status`
- `review_status`

## Validation Gates

| Gate | Blocks Export? | Why |
|------|----------------|-----|
| Missing lemma/frequency rank/source | Yes | MVP is specifically lemma-frequency based |
| Missing sentence provenance | Yes | Traceability is table stakes |
| Target form not found in sentence | Yes unless accepted normalized/enclitic span exists | Prevents disconnected word/sentence cards |
| Missing Portuguese translations | Yes | User requested Portuguese learner-facing deck |
| Missing or malformed `Gramatica` | Yes | Core Latin-specific value |
| Wrong genitive spelling (`Genetivus`) in final field | Yes or auto-remediate to `Genitivus` | Seed decision says final label is `Genitivus` |
| `Classe` exported as separate study field | Yes | Explicit exclusion |
| Audio missing | Policy decision: block if audio mandatory; otherwise export only with explicit experimental/missing-audio report | TTS quality research is still a risk |
| Review status not approved | Default should block from final APKG | Prevents unreviewed learner content |

## Suggested Requirement IDs

- **LATIN-MODE-01:** Multilang provides a separate Classical Latin MVP generation path isolated from existing deck modes.
- **LATIN-SCOPE-01:** The default Latin MVP produces a reproducible 50-card deck manifest and does not attempt a full 3000-card deck.
- **LATIN-FREQ-01:** Latin card ordering is based on lemma frequency with stored rank and source metadata.
- **LATIN-SENT-01:** Each Latin card contains a target form in a traceable Latin sentence and validates target-form presence.
- **LATIN-SOURCE-01:** Each Latin card records sentence source provenance, including source type and citation/URL/work metadata when available.
- **LATIN-PT-01:** Each Latin card contains a Portuguese short translation for the target lemma/form.
- **LATIN-PT-02:** Each Latin card contains a Portuguese translation of the displayed Latin sentence.
- **LATIN-GRAM-01:** Each Latin card contains a short standardized `Gramatica` field describing morphology and syntactic function in context.
- **LATIN-GRAM-02:** Final Latin grammar labels use `Genitivus` and the required case vocabulary: `Nominativus`, `Vocativus`, `Accusativus`, `Genitivus`, `Dativus`, `Ablativus`.
- **LATIN-SCHEMA-01:** The Latin exported study schema excludes a separate learner-facing `Classe` field while preserving blank `Image`.
- **LATIN-REVIEW-01:** Latin cards support `needs_review`, `approved`, and `rejected` states, with approved-only final export by default.
- **LATIN-AUDIO-01:** Latin cards generate/package word and sentence audio or fail/mark experimental according to the milestone audio policy.
- **LATIN-AUDIO-02:** Latin audio artifacts store provider, voice, pronunciation/variant assumptions, and quality/fallback metadata.
- **LATIN-EXPORT-01:** Multilang exports the Latin MVP to APKG/CSV/TSV with stable field order, packaged media, and template/import evidence.
- **LATIN-REGRESSION-01:** Existing modern-language frequency, custom word-list, highlight, review, audio, and export behavior remains operational after Latin changes.

## Sources and Confidence

- Project context: `.planning/PROJECT.md` — **HIGH confidence** for current product state, shipped behavior, and v2.0 goals.
- Latin seed decisions: `LATIN-STRUCTURE.md` — **HIGH confidence** for user intent: Classical Latin only, Portuguese, Rafael Falcon reference, lemma frequency, traceable sentences, `Gramatica`, no `Classe`, 50-card MVP, Greek excluded.
- Dickinson College Commentaries Latin Core Vocabulary — confirms a pedagogical Latin core list with frequency ranks and Portuguese localization available: https://dcc.dickinson.edu/latin-vocabulary-list — **HIGH confidence** for feature implications; exact licensing/asset reuse still needs stack/implementation validation.
- Perseus/Scaife Viewer — confirms a large pre-modern text collection with Latin works and a current 2026 release: https://scaife.perseus.org/ — **MEDIUM-HIGH confidence** for source-discovery direction; exact texts/license/provenance format need implementation research.
- Azure Speech language and voice support docs, updated 2026-05-07 — confirms multilingual TTS exists but no dedicated Latin locale was found in the exposed TTS language table: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts — **HIGH confidence** that Azure Latin requires testing through multilingual voices rather than assuming first-class Latin support.
- eSpeak NG language list — confirms `la` Latin support in eSpeak NG development language list: https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md — **MEDIUM-HIGH confidence** for local Latin TTS fallback; audio quality must be reviewed by ear.

## Confidence Notes

- **HIGH:** MVP scope, explicit exclusions, card fields requested by the user, need for review states, APKG/export continuity, no separate `Classe`, `Genitivus` spelling.
- **MEDIUM-HIGH:** DCC/Perseus/eSpeak as feature-shaping resources; official/public pages support their existence, but licensing and implementation details need phase research.
- **MEDIUM:** Exact first-50 ordering and Rafael Falcon progression rules; these require user/reviewer calibration and concrete examples.
- **LOW:** Final best Latin TTS provider quality; Azure multilingual and eSpeak NG must be compared with real Latin samples before locking the user-facing promise.
