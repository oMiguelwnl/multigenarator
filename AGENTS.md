<!-- GSD:project-start source:PROJECT.md -->
## Project

**Multilang Anki Card Generator**

Multilang is a multilingual Anki card generator focused on the most frequent words in a target language. It is meant to create high-quality study decks for learners of Portuguese, Spanish, English, French, German, Russian, and Dutch, with a separate mode for generating cards from a user-provided word list collected from reading.

The product generates structured Anki-ready cards with word data, phonetics, definitions, example sentences, translations, audio, and an empty image field that the user can fill manually later. AI-assisted generation is part of the intended approach, but the exact provider and supporting services still need research and validation.

**Core Value:** Generate reliable, high-quality Anki cards for frequent vocabulary in the chosen language so the learner can study real words with accurate definitions, examples, translations, and audio.

### Constraints

- **Languages**: v1 must support Portuguese, Spanish, English, French, German, Russian, and Dutch — these are the explicit target languages.
- **Deck Structure**: Cards must be separated into 3 levels with 1000 cards per level — this defines the core content structure.
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
| Kaikki / Wiktextract | current dump family | Structured lexical source | Primary open lexical source for lemma, senses, forms, usage labels, and often IPA/audio links. |
| Internal normalization layer | custom | Canonical lexical model | Normalize per-language entries into one internal schema before any AI step. |
- filling gaps
- rewriting definitions to your deck style
- normalizing inconsistent glosses
### 3) Example sentence sourcing
| Component | Role | Recommendation |
|---|---|---|
| Grounded LLM generation | Primary sentence source | Generate short learner-friendly example sentences from lexical context and deck rules. |
| Kaikki/Wiktionary examples | Secondary/reference source | Reuse only when short, natural, and clearly mapped to the intended sense. |
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
# ai/orchestration
# language + export
# testing
## Decision summary for roadmap use
### Prescriptive recommendation
- **Use Python.**
- **Use FastAPI + Typer + Pydantic + SQLAlchemy + PostgreSQL as the backbone.**
- **Use `wordfreq` only to bootstrap frequency candidates, then freeze your own lists.**
- **Use Kaikki/Wiktextract as the lexical base for definitions/IPA, not LLMs alone.**
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
| Dictionary/IPA source | MEDIUM-HIGH | Kaikki/Wiktextract is practical, but normalization work is non-trivial. |
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
- Kaikki/Wiktextract raw data docs — https://kaikki.org/dictionary/rawdata.html — MEDIUM-HIGH
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

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
