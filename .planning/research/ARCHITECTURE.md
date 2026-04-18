# Architecture Patterns

**Domain:** Multilingual AI-assisted Anki card generation
**Researched:** 2026-04-18

## Recommended Architecture

**Recommendation:** build **library-first with a CLI entrypoint** for v1.

This product is primarily a **batch content pipeline**, not a request/response app. The hard problems are data quality, retries, provenance, validation, and reproducible exports. A service-first design adds auth, queueing, tenancy, and deployment complexity before the core generation pipeline is trusted. A CLI-first UX is useful, but the architecture should be **library-first underneath** so the pipeline is testable and later reusable from a CLI, worker, or web service.

**Suggested v1 shape:**

```text
CLI command
  -> run coordinator
    -> ingestion
    -> lexical enrichment
    -> sentence/translation generation
    -> validation + repair loop
    -> audio synthesis
    -> deck assembly
    -> export (.apkg + manifest/CSV fallback)
```

**Opinionated stack direction:** prefer **Python** for v1.

- `wordfreq` is a Python-native fit for ranked vocabulary input and supported-language inspection. [HIGH]
- `genanki` gives a direct `.apkg` packaging path with media file support. [HIGH]
- Azure Speech SDK supports Python and JavaScript, so TTS does not force the stack either way. [HIGH]
- The pipeline is offline/batch/ETL-like; Python usually gives the shortest path for NLP, validation, and fixture-heavy tests. [MEDIUM]

## System Shape

```text
                +----------------------+
Input sources ->| Ingestion/Normalizer |----+
                +----------------------+    |
                                              v
                                     +-------------------+
                                     | Canonical Lexeme  |
                                     | + Card Spec Store |
                                     +-------------------+
                                              |
                    +-------------------------+--------------------------+
                    |                         |                          |
                    v                         v                          v
          +------------------+     +--------------------+     +------------------+
          | Linguistic       |     | AI Generation      |     | Audio Synthesis  |
          | Enrichment       |     | (sentence/transl.) |     | (word/sentence)  |
          +------------------+     +--------------------+     +------------------+
                    |                         |                          |
                    +------------+------------+-------------+------------+
                                 |                          |
                                 v                          |
                         +-------------------+              |
                         | Validation Gates  |<-------------+
                         | + Repair / Retry  |
                         +-------------------+
                                  |
                                  v
                         +-------------------+
                         | Deck Assembler    |
                         | + Export Adapters |
                         +-------------------+
                                  |
                                  v
                         .apkg / CSV+media / JSONL audit
```

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| CLI / Runner | Accepts language, level, input mode, provider config, output path; starts jobs and renders progress | Orchestrator only |
| Orchestrator | Runs pipeline stages in order, persists stage results, handles retries/checkpoints | All components |
| Ingestion / Normalizer | Reads frequency lists or custom words, normalizes forms, deduplicates, assigns `SortIndex`, creates canonical work items | Orchestrator, Card Spec Store |
| Card Spec Store | Canonical schema for one target card and all stage outputs/provenance/status | All stage components |
| Linguistic Enrichment | Fetches or derives lemma, POS, IPA/phonetics, definitions scaffolding, language metadata | Card Spec Store, validators |
| Generation Adapter | Produces example sentence and translation via AI/provider abstraction | Orchestrator, validators |
| Validation Engine | Enforces schema, target-language rules, banned-output checks, sentence contains word, translation completeness, formatting rules | All content-producing stages |
| Repair / Fallback Engine | Re-prompts, switches provider/model, downgrades to safer template path, or marks card for review | Generation, audio, validators |
| Audio Adapter | Synthesizes `word_audio` and `sentence_audio`; stores media filenames and provider metadata | Card Spec Store, export |
| Deck Assembler | Converts validated card specs into Anki note models and media references | Export adapters |
| Export Adapters | Emit `.apkg`, plus machine-readable JSONL/CSV manifest fallback for debugging/regeneration | Filesystem |
| Observability / Audit | Logs prompts, provider IDs, retries, validation failures, output hashes | Orchestrator and all adapters |

## Canonical Data Model

Architecturally, the most important early decision is a **canonical card spec** that every stage reads/writes.

```python
class CardSpec:
    id: str
    language: str
    level: int
    sort_index: int
    source_type: Literal["frequency", "custom"]
    source_word: str
    normalized_word: str
    lemma: str | None
    pos: str | None
    ipa: str | None
    definitions: list[str]
    example_sentence: str | None
    translation: str | None
    word_audio_path: str | None
    sentence_audio_path: str | None
    image: str | None = ""
    validation_status: Literal["pending", "passed", "failed", "manual_review"]
    provenance: dict
    errors: list[str]
```

**Why this matters:** if the schema is stable, providers can change without rewriting the system.

## Data Flow

**Direction is one-way by default:** raw input -> normalized lexeme -> enriched draft -> generated card -> validated card -> exported deck.

Use **controlled backward edges only for repair loops**:

1. **Input ingestion**
   - Frequency list mode: load ranked words.
   - Custom mode: load user words in given order.
   - Normalize casing, Unicode, punctuation, duplicates.

2. **Lexical enrichment**
   - Add deterministic metadata first: lemma, POS, IPA, definitions scaffold, language config.
   - This stage should be as non-AI as possible.

3. **Sentence + translation generation**
   - Generate example sentence for the target word.
   - Generate translation, ideally in a separate step so each output can be validated independently.

4. **Validation gate #1: text quality**
   - Word present in sentence.
   - Sentence length within bounds.
   - Output language matches expectation.
   - No placeholders, disclaimers, or malformed markup.
   - Translation non-empty and aligned.

5. **Repair / fallback path**
   - Retry with stricter prompt.
   - Switch model/provider.
   - Fall back to template-driven sentence for simple nouns/verbs if repeated failure.
   - Escalate to `manual_review` instead of silently shipping bad cards.

6. **Audio synthesis**
   - Generate word audio and sentence audio only for cards that passed text validation.
   - Record provider voice and synthesis settings in provenance.

7. **Validation gate #2: media integrity**
   - Files exist.
   - Filenames stable and unique.
   - Duration/non-zero bytes sanity checks.

8. **Deck assembly + export**
   - Map canonical fields to Anki model fields.
   - Emit `.apkg` when all required assets exist.
   - Also emit JSONL/CSV manifest as a regeneration/debug fallback.

## Quality Gates

Quality gates belong **between every expensive or lossy stage**, not just at the end.

### Gate A: Input Quality
Before enrichment.

- Reject empty tokens, duplicates, obvious phrases if v1 is word-only
- Enforce supported language codes
- Record skipped items explicitly

### Gate B: Enrichment Completeness
Before AI generation.

- Required fields present: normalized word, language, rank/source
- IPA/definition missing -> allowed only if fallback policy says so
- If enrichment is weak, mark lower confidence before generation

### Gate C: Generated Text Quality
Before audio.

- Sentence uses target word or approved inflection
- Sentence is natural-length and single-example-oriented
- Translation matches the example, not just the word
- No hallucinated grammar notes or multiple alternatives in one field

### Gate D: Audio Quality
Before export.

- Synthesis succeeded
- Output file readable and non-empty
- Voice/language combination valid

### Gate E: Export Integrity
Final gate.

- Required Anki fields populated
- Media references resolve
- Deck counts per level correct
- Deterministic output manifest written

## Fallback Paths

Fallbacks should be **designed into adapters**, not scattered through business logic.

### AI generation fallback
- Primary: preferred model/provider
- Secondary: cheaper or more reliable backup model
- Tertiary: constrained template generation for simple cards
- Final: `manual_review`

### Linguistic data fallback
- Primary: structured lexical source / deterministic library
- Secondary: AI fill-in with low-confidence marker
- Final: ship only if field is optional for that phase

### Audio fallback
- Primary: Azure preferred voice
- Secondary: alternate voice in same locale
- Final: export card without audio only if roadmap explicitly allows it; otherwise fail card

### Export fallback
- Primary: `.apkg`
- Secondary: CSV/TSV + media directory + JSONL manifest for re-import/debug

## Patterns to Follow

### Pattern 1: Ports and Adapters
**What:** keep provider code behind interfaces.
**When:** AI, TTS, lexical sources, exporters.
**Why:** this project has known provider uncertainty.

```python
class SentenceGenerator(Protocol):
    def generate(self, card: CardSpec) -> GeneratedText: ...

class TTSProvider(Protocol):
    def synthesize_word(self, card: CardSpec) -> AudioAsset: ...
    def synthesize_sentence(self, card: CardSpec) -> AudioAsset: ...
```

### Pattern 2: Stage Persistence
**What:** persist each stage result to disk/db as artifacts.
**When:** after ingestion, enrichment, generation, validation, audio, export.
**Why:** makes reruns cheap and failures debuggable.

Recommended artifact layout:

```text
artifacts/
  pt/
    level-1/
      cards.jsonl
      generated.jsonl
      validated.jsonl
      media/
      export/
```

### Pattern 3: Deterministic Core, Probabilistic Edge
**What:** keep ranking, normalization, field mapping, validation, filenames, and export deterministic; isolate AI only where needed.
**When:** always.
**Why:** minimizes regressions and makes deck regeneration reproducible.

### Pattern 4: Idempotent Jobs
**What:** same input + same config should not duplicate work or generate duplicate media names.
**When:** batch reruns and resume-after-failure.
**Why:** this is essential once runs span thousands of cards.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Monolithic “generate_card()” function
**What:** one function that calls AI, TTS, validation, and export together.
**Why bad:** impossible to retry safely or inspect failure boundaries.
**Instead:** split by stage with persisted artifacts.

### Anti-Pattern 2: Provider-specific logic in the domain model
**What:** storing Azure/OpenRouter prompt quirks directly in card entities.
**Why bad:** provider swap becomes a rewrite.
**Instead:** keep provider config in adapters and provenance metadata.

### Anti-Pattern 3: Only final-pass validation
**What:** validating after deck export.
**Why bad:** expensive failures arrive too late, especially after audio generation.
**Instead:** gate before AI, before audio, and before export.

### Anti-Pattern 4: Shipping silent partial failures
**What:** missing audio or malformed translation quietly ends up in export.
**Why bad:** deck quality degrades invisibly.
**Instead:** explicit per-card status: passed / failed / manual review.

### Anti-Pattern 5: Service-first v1
**What:** building API, workers, database, auth, and frontend before the pipeline is reliable.
**Why bad:** solves delivery before correctness.
**Instead:** library-first core, thin CLI, optional service later.

## Suggested Build Order

This is the build order that best supports roadmap creation.

### Phase 1: Canonical schema + deterministic pipeline shell
Build first:
- `CardSpec` schema
- config model
- artifact layout
- orchestrator skeleton
- CLI command that runs no-op/sample pipeline

**Reason:** every later component depends on stable contracts.

### Phase 2: Input ingestion + normalization
Build:
- frequency list ingestion
- custom word list ingestion
- dedupe/normalization rules
- per-language config registry

**Reason:** stable inputs are needed before any expensive enrichment.

### Phase 3: Enrichment layer
Build:
- word metadata enrichment
- definitions/IPA/POS adapters
- provenance capture
- Gate A and Gate B

**Reason:** generation quality improves a lot when prompts receive structured context.

### Phase 4: Text generation + validation/repair loop
Build:
- sentence generator adapter
- translation generator adapter
- validation engine
- retry/fallback policies

**Reason:** this is the core product risk; it should be solved before audio/export polish.

### Phase 5: Audio pipeline
Build:
- Azure TTS adapter
- voice registry per language
- audio naming/storage
- Gate D

**Reason:** audio is expensive and should only run after text passes.

### Phase 6: Deck assembly + export
Build:
- Anki model mapping
- `.apkg` exporter
- CSV/JSONL fallback exporter
- Gate E

**Reason:** export is easiest once upstream fields are stable.

### Phase 7: Scale, observability, resumability
Build:
- batch resume/checkpointing
- concurrency controls
- richer audit logs
- failure dashboards or summaries

**Reason:** optimize throughput only after correctness is proven.

## v1 Runtime Model

**Best v1:** local/batch CLI over filesystem artifacts.

Why:
- Fits 3 x 1000-card deck generation jobs
- Easier snapshot testing
- Easier cost control for AI/TTS
- Easier to pause, inspect, and regenerate a subset

**Not recommended for v1:** long-running web service.

Add a service later only if you need:
- multi-user job submission
- hosted deck generation
- remote monitoring
- asynchronous queue workers

## Testing Strategy by Boundary

| Boundary | What to test | Type |
|----------|--------------|------|
| Canonical schema | field constraints, serialization, backward compatibility | Unit |
| Ingestion | normalization, dedupe, rank assignment | Unit |
| Enrichment adapters | parsing/mapping of provider responses | Unit + contract |
| Generation | prompt inputs, structured outputs, validator behavior | Contract + golden tests |
| Validation engine | positive/negative cases per language rule | Unit |
| Audio adapter | file creation, naming, error mapping | Contract |
| Exporter | Anki field mapping, media references, deck counts | Integration |
| End-to-end run | sample 10-word deck per language | Smoke |

## Scalability Considerations

| Concern | At 100 users / small local runs | At 10K cards / repeated runs | At hosted scale |
|---------|-------------------------------|-----------------------------|-----------------|
| Orchestration | Single-process CLI | Parallel workers per stage | Queue + worker fleet |
| State | Filesystem artifacts | SQLite/Postgres job metadata | Durable DB + object storage |
| AI cost | Manual control | Batch/rate limiting | Provider budgeting + quotas |
| Audio | Synchronous calls | Batched synthesis with retries | Async job processing |
| Observability | Local logs | Structured logs + summaries | Centralized tracing/metrics |

## Architecture Recommendation for Roadmap

Use this as the roadmap assumption:

1. **Python, library-first core**
2. **Thin CLI runner for v1**
3. **Stage-based batch pipeline with persisted artifacts**
4. **Provider adapters for AI/TTS/lexical sources**
5. **Validation and fallback paths between stages, not just at the end**
6. **Export `.apkg` as primary, JSONL/CSV as recovery/debug path**

If the roadmap follows that order, the project can validate output quality early and defer service complexity until the pipeline is trustworthy.

## Sources

- `wordfreq` docs: supported languages and `top_n_list` for ranked vocabulary input — https://github.com/rspeer/wordfreq/blob/master/README.md [HIGH via Context7]
- Azure AI Speech docs: Speech SDK text-to-speech and SSML for Python/JavaScript — https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-speech-synthesis [HIGH via Context7]
- `genanki` docs: deck/note modeling, media files, and `.apkg` export — https://github.com/kerrickstaley/genanki/blob/main/README.md [HIGH via Context7]
- Library-first / stage-oriented pipeline recommendation is based on architecture analysis of the product shape rather than a single official source. [MEDIUM]
