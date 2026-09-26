<!-- GSD:project-start source:PROJECT.md -->
## Project

**Multilang Anki Card Generator**

Multilang is a multilingual Anki card generator focused on the most frequent words in a target language. It creates high-quality study decks for modern-language frequency, user-provided word lists, and reading highlights, with language-specific foundation paths where needed. v3.0 plans complete Korean support alongside the existing language and Classical Latin paths.

The product generates structured Anki-ready cards with word data, phonetics, definitions, example sentences, translations, audio, and an empty image field that the user can fill manually later. AI-assisted generation is part of the intended approach, but the exact provider and supporting services still need research and validation.

**Core Value:** Generate reliable, high-quality Anki cards for frequent vocabulary in the chosen language so the learner can study real words with accurate definitions, examples, translations, and audio.

### Constraints

- **Languages**: v1 supports Portuguese, Spanish, English, French, German, Italian, Polish, Turkish, Romanian, Russian, and Dutch; v3.0 adds modern standard Korean with canonical code `ko` and provider locale `ko-KR`.
- **Deck Size — all languages**: 3,000 is an initial frequency reference, not a maximum number of cards per language. A language may have more than 3,000 cards when useful vocabulary, distinct senses or pedagogically important forms justify them. Preserve quality, lexical identity, provenance and deduplication; do not discard valid content or generate redundant conjugations merely to meet a number. The existing three levels of 1,000 core entries are the initial organization, not a ceiling on total cards. Foundation, custom-list and highlight decks follow their own content needs.
- **Frequency organization**: Count lexical identities separately from cards. Keep useful cards for an existing identity with its parent frequency level, even when that level exceeds 1,000 cards. Put additional lexical identities beyond the initial core in frequency expansions, retaining their source/rank metadata. Prefer a small deck hierarchy and tags for detailed classification; frequency bands are not proficiency certificates.
- **Vocabulary coverage — all languages**: The user's target is at least 90% lexical occurrence coverage in representative general-use material, expanding the vocabulary when needed rather than stopping at 3,000 cards. Measure the finalized inventory against independent, versioned evaluation corpora with language-appropriate normalization/morphology; report spoken and written coverage separately, the counting unit and exclusions. Card count and literature estimates do not prove achieved coverage or comprehension. This is a target until the exact inventory has been evaluated.
- **Current preparation scope**: The user requested vocabulary files and reports for every language now, with deck generation deferred until a later explicit instruction. Notify the user before resuming card text, translation, audio or deck generation. Offline preparation and tests may proceed; do not interpret completed preparation as authorization to run generation.
- **Korean Decks**: Korean includes Hangul foundations, strict-i+1 pronunciation, three frequency levels, strict-i+1 Particles & Endings, custom lists, and privacy-safe highlights.
- **Korean Linguistics**: Korean content must use NFC normalization, morphology-aware lemma/POS/sense identity, and fail-closed target matching rather than whitespace or suffix heuristics.
- **Korean Licensing**: A redistributed 3000-entry Korean frequency asset requires an approved source, attribution, and redistribution decision before it is committed.
- **Output Quality**: Example sentences and translations must be high quality — prior low-quality outputs from Tatoeba are a known concern.
- **Audio Provider**: Audio should use Azure TTS if the required voices are available — this is the user's preferred TTS direction.
- **Card Schema**: The generated deck must preserve the requested field set and formatting — Anki export usefulness depends on consistent structure.
- **Engineering Quality**: The codebase must follow architecture and good practices, with tests and fallbacks — reliability is a stated requirement, not a nice-to-have.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Bottom-line Recommendation
## Recommended Stack
### Core runtime / app shape
| Technology | Version / family | Purpose | Why this choice | Confidence |
|---|---|---|---|---|
| Python | **3.12** baseline | Main runtime | Best ecosystem for NLP assets, lexical ETL, Azure Speech SDK, and Anki packaging. Safer than making JS do data-engineering work it is not best at. | HIGH |
| uv | current `uv` family | Package/env/project manager | Fast, modern, lockfile-based, and now standard for greenfield Python projects. | HIGH |
| FastAPI | current stable | API layer | Clean typed API, easy background integration, OpenAPI docs, strong fit for internal/admin APIs. | HIGH |
| Typer | current stable | CLI layer | Same type-hint-first ergonomics as FastAPI; ideal for `import`, `generate`, `synthesize`, `export` commands. | HIGH |
| Pydantic | **v2** family | Schema validation | Critical for validating card payloads, AI outputs, provider responses, and export contracts. | HIGH |
### Database / persistence
| Technology | Version / family | Purpose | Why this choice | Confidence |
|---|---|---|---|---|
| PostgreSQL | **17 family** target; 18-compatible schema | Source of truth | Best default relational store for card generation jobs, lexical assets metadata, deck versions, audio manifests, and auditability. Use PG17 for broad hosting support; keep schema compatible with PG18. | HIGH |
| SQLAlchemy | **2.0** family | ORM / SQL layer | Mature, current, async-capable, and better long-term than lightweight ORMs for a data-heavy product. | HIGH |
| Alembic | **1.18** family | DB migrations | Standard SQLAlchemy migration tool; use from day one. | HIGH |
| Object storage | **Azure Blob** initially | Store generated audio, exports, cached raw assets | Since Azure TTS is already chosen, Blob is the path of least friction for audio artifacts and signed downloads. | MEDIUM |
| Redis | current family, optional in MVP | Cache + job queue backing | Useful once you parallelize TTS/LLM work; not required for day-1 if a DB-backed job table is enough. | MEDIUM |
### AI orchestration
| Technology | Version / family | Purpose | Why this choice | Confidence |
|---|---|---|---|---|
| PydanticAI | current stable | Typed LLM workflow layer | Best fit when the output must be strict JSON-like card structures, not chatbot text. Stronger than prompt-string glue code. | HIGH |
| LiteLLM | current stable | Provider abstraction / fallback routing | Keeps OpenAI/Azure/OpenRouter optionality without infecting the whole codebase with provider-specific logic. | HIGH |
| Provider model | OpenAI or Azure OpenAI family for generation/judging | Generate definitions, examples, normalization, QA | Use one high-quality model family first; add fallbacks later through LiteLLM. | MEDIUM |
## Domain-specific stack decisions
### 1) Frequency lists
| Component | Version / family | Role | Recommendation |
|---|---|---|---|
| `wordfreq` | **3.1.1** | Bootstrap candidate frequency ranks | Use to seed the initial 1k/2k/3k candidate lists for supported languages. |
| Curated frozen assets | internal CSV/JSON/SQL tables | Production source of truth | After seeding, freeze and version your own frequency lists per language. |
- Generate candidate top-N lists with `wordfreq`
- Filter junk tokens, inflected duplicates, abbreviations, and punctuation artifacts
- Freeze the final production lists in Postgres + versioned asset files
### 2) Dictionary + IPA data
| Component | Version / family | Role | Recommendation |
|---|---|---|---|
| Manual/generic lexical cache | JSON cache | Structured lexical source | Runtime source for lemma, display form, usage labels, and IPA/audio links. Definitions are generated by the configured LLM provider. |
| Internal normalization layer | custom | Canonical lexical model | Normalize entries into one internal schema before any AI step. |
- filling gaps
- generating definitions through the LLM deck style
- normalizing inconsistent glosses
### 3) Example sentence sourcing
| Component | Role | Recommendation |
|---|---|---|
| Grounded LLM generation | Primary sentence source | Generate short learner-friendly example sentences from lexical context and deck rules. |
| Curated examples | Secondary/reference source | Reuse only when short, natural, and clearly mapped to the intended sense. |
| spaCy + Stanza | Validation layer | Check the target lemma/form actually appears and sentence segmentation/tokenization are sane. |
- use lexical grounding + prompt template + structured output
- verify sentence length, lemma inclusion, banned patterns, and language correctness
- keep human-review hooks for the top-frequency decks
### 4) Translation quality
| Technology | Version / family | Role | Why |
|---|---|---|---|
| DeepL API | current API | Primary sentence translation | Strong support for all target languages here and usually better literal sentence quality than generic LLM-only translation for European languages. | 
| LLM judge / rewrite pass | same provider as generation | Repair/normalize edge cases | Use only as fallback or QA, not as the main translator. |
### 5) TTS / audio generation
| Technology | Version / family | Role | Why |
|---|---|---|---|
| Azure Speech Service | current | TTS provider | Officially supports TTS voices for the target languages and is already the intended provider. |
| `azure-cognitiveservices-speech` | **1.49.x** | Python SDK | Official SDK with current releases and good Python support. |
| SSML | Azure SSML support | Pronunciation/styling control | Necessary for pronunciation tuning, voice selection, pacing, and multilingual handling. |
- Generate and cache **word audio** and **sentence audio** separately
- Track voice ID, locale, SDK version, and synthesis hash in DB
- Make audio generation idempotent
### 6) Anki export
| Technology | Version / family | Role | Why |
|---|---|---|---|
| `genanki` | **0.13.1** | `.apkg` generation | Still the pragmatic Python standard for generating Anki decks programmatically with media packaging. |
| Stable internal card schema | custom | Export contract | Prevents export logic from leaking into generation logic. |
### 7) Storage model
- `language`
- `frequency_list_version`
- `lemma`
- `lexical_entry`
- `example_sentence`
- `translation`
- `audio_asset`
- `card`
- `deck_export`
- `generation_job`
### 8) Testing stack
| Technology | Version / family | Purpose | Why |
|---|---|---|---|
| pytest | **9.x** family | Test runner | Standard Python choice; strong fixtures and parametrization. |
| HTTPX | current stable | API tests / external client mocking | Natural fit with FastAPI and async integrations. |
| PydanticAI test utilities / mock providers | current family | AI workflow tests | Lets you test deterministic structured outputs without hitting live models. |
| Golden-file fixtures | custom | Deck/export regression tests | Essential for ensuring card field order, HTML, media refs, and GUID stability. |
- lexical normalization tests
- prompt/output schema tests
- translation/TTS provider adapter tests
- `.apkg` export regression tests
- end-to-end “generate 10 cards” smoke test
## Recommended application shape
### MVP shape
### Why this shape
## What NOT to use
| Avoid | Why not |
|---|---|
| Full JS/TS backend as the primary stack | Worse fit for lexical ETL, Python-only language tooling, and Anki packaging. |
| LangChain as the default orchestration layer | Too much abstraction for a product that needs deterministic typed outputs, not agent experimentation. |
| Tatoeba as default sentence source | Known quality concern; should be optional reference data only. |
| SQLite as production source of truth | Fine for local dev; weak for concurrent generation jobs, auditability, and long-lived assets. |
| “LLM-only” dictionary/IPA generation | Too hallucination-prone for learner content. Ground first, generate second. |
| Live provider responses as permanent truth | Always persist normalized outputs and provider metadata; never make export depend on re-calling providers. |
## Installation baseline
# project/runtime

## Working Practices

- Implement the user's requested scope and follow existing codebase conventions.
- Verify changes before claiming completion.
- Research unfamiliar domains from real documentation and code.
- Existing `.planning/` documents remain available as project history and context.
- Put generated card previews, examples, decks and delivery reports under the single `output/` root: `previews/`, `examples/`, `decks/` and `reports/`. Use the output directory properties in `Settings`; respect an explicit user-supplied destination.
- Keep each example's HTML, images, audio and supporting files together. Do not create new deliverables in the repository root, `docs/`, `work/`, `exports/` or `.multilang/verification/`. See `output/README.md` for the directory convention.
- Templates belong in `src/multilang/templates/`, reusable generators in `scripts/`, and runtime databases/caches in `.multilang/`. Historical compatibility links are not new output destinations.

# ai/orchestration
# language + export
# testing
## Decision summary for roadmap use
### Prescriptive recommendation
- **Use Python.**
- **Use FastAPI + Typer + Pydantic + SQLAlchemy + PostgreSQL as the backbone.**
- **Use `wordfreq` only to bootstrap frequency candidates, then freeze your own lists.**
- **Use a generic/manual lexical cache for lexical grounding/IPA, and generate card definitions through the configured LLM provider.**
- **Use grounded LLM generation for example sentences, validated with spaCy/Stanza.**
- **Use DeepL for translation.**
- **Use Azure Speech for audio.**
- **Use genanki for `.apkg` export.**
## Confidence by area
| Area | Confidence | Notes |
|---|---|---|
| Python over JavaScript | HIGH | Strong ecosystem advantage for this exact problem shape. |
| Core app stack | HIGH | FastAPI/Pydantic/SQLAlchemy/Postgres is standard and current. |
| Frequency bootstrap | HIGH | `wordfreq` is solid for seeding. |
| Dictionary/IPA source | MEDIUM | Manual/generic cache quality depends on curation and normalization. |
| Sentence sourcing | MEDIUM | Quality depends on prompt + validation design. |
| Translation | HIGH | DeepL language support is strong for this scope. |
| TTS | HIGH | Azure Speech coverage and Python SDK are current. |
| Anki export | MEDIUM-HIGH | `genanki` is older but still the pragmatic choice. |
## Sources
- FastAPI docs — https://fastapi.tiangolo.com/ — HIGH
- Pydantic docs (v2.13.2 shown) — https://docs.pydantic.dev/latest/ — HIGH
- PydanticAI docs — https://ai.pydantic.dev/ — HIGH
- SQLAlchemy 2.0 docs (2.0.49 current release) — https://docs.sqlalchemy.org/en/20/ — HIGH
- Alembic docs (1.18.4 docs) — https://alembic.sqlalchemy.org/en/latest/ — HIGH
- Typer docs — https://typer.tiangolo.com/ — HIGH
- uv docs — https://docs.astral.sh/uv/ — HIGH
- PostgreSQL current docs (18.3 current, recommend PG17 target for hosting compatibility) — https://www.postgresql.org/docs/current/ — HIGH
- Azure Speech TTS overview — https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech — HIGH
- Azure Speech language/voice support — https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts — HIGH
- Azure Speech Python SDK PyPI (`azure-cognitiveservices-speech` 1.49.1) — https://pypi.org/project/azure-cognitiveservices-speech/ — HIGH
- DeepL supported languages — https://developers.deepl.com/docs/getting-started/supported-languages — HIGH
- `wordfreq` 3.1.1 PyPI — https://pypi.org/project/wordfreq/ — MEDIUM-HIGH
- spaCy language/models docs — https://spacy.io/usage/models — HIGH
- Stanza overview — https://stanfordnlp.github.io/stanza/ — MEDIUM-HIGH
- `genanki` 0.13.1 PyPI — https://pypi.org/project/genanki/ — MEDIUM
- pytest docs — https://docs.pytest.org/en/stable/ — HIGH
- HTTPX docs — https://www.python-httpx.org/ — HIGH
- LiteLLM docs — https://docs.litellm.ai/ — MEDIUM-HIGH
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

Project skills are stored in `.agents/skills/`. Use relevant skills when they help fulfill the user's request.
<!-- GSD:skills-end -->
