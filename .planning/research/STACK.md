# Technology Stack

**Project:** Multilang Anki Card Generator  
**Dimension:** Stack  
**Researched:** 2026-04-18  
**Overall recommendation:** Build this in **Python**, not JavaScript.

## Bottom-line Recommendation

For a 2025-standard build of a multilingual AI-assisted Anki deck generator, use a **Python application stack with FastAPI + Pydantic + SQLAlchemy + PostgreSQL**, plus **Azure Speech** for TTS, **DeepL** for sentence translation, **PydanticAI + LiteLLM** for LLM orchestration, **Kaikki/Wiktextract + curated frequency assets** for lexical grounding, and **genanki** for `.apkg` export.

This is the standard stack because the hardest parts of the product are **language data assembly, validation, audio generation, and Anki packaging**. Python is materially better than JS/TS for those jobs.

---

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

**Recommendation:** use LLMs for **generation and adjudication**, not as the primary lexical database.

---

## Domain-specific stack decisions

### 1) Frequency lists

**Recommended stack**

| Component | Version / family | Role | Recommendation |
|---|---|---|---|
| `wordfreq` | **3.1.1** | Bootstrap candidate frequency ranks | Use to seed the initial 1k/2k/3k candidate lists for supported languages. |
| Curated frozen assets | internal CSV/JSON/SQL tables | Production source of truth | After seeding, freeze and version your own frequency lists per language. |

**Why:** `wordfreq` is excellent for bootstrapping and supports all 7 target languages, but it is not enough as the permanent product truth layer. It is from 2023 and aggregates mixed corpora; your deck product needs **deterministic, reviewable ranks**.

**Do this:**
- Generate candidate top-N lists with `wordfreq`
- Filter junk tokens, inflected duplicates, abbreviations, and punctuation artifacts
- Freeze the final production lists in Postgres + versioned asset files

**Do not:** query `wordfreq` live at runtime and treat it as the final deck definition.

**Confidence:** HIGH for bootstrap, MEDIUM for final ranking quality without manual curation.

### 2) Dictionary + IPA data

**Recommended stack**

| Component | Version / family | Role | Recommendation |
|---|---|---|---|
| Kaikki / Wiktextract | current dump family | Structured lexical source | Primary open lexical source for lemma, senses, forms, usage labels, and often IPA/audio links. |
| Internal normalization layer | custom | Canonical lexical model | Normalize per-language entries into one internal schema before any AI step. |

**Why:** there is no single clean, official, multilingual API that reliably gives high-quality lemma + IPA + sense data across Portuguese, Spanish, English, French, German, Russian, and Dutch. Kaikki/Wiktextract is the most practical open structured base.

**Use AI only for:**
- filling gaps
- rewriting definitions to your deck style
- normalizing inconsistent glosses

**Do not:** use unofficial free dictionary APIs as the core data source. Coverage and schema stability are too weak.

**Confidence:** MEDIUM-HIGH.

### 3) Example sentence sourcing

**Recommended stack**

| Component | Role | Recommendation |
|---|---|---|
| Grounded LLM generation | Primary sentence source | Generate short learner-friendly example sentences from lexical context and deck rules. |
| Kaikki/Wiktionary examples | Secondary/reference source | Reuse only when short, natural, and clearly mapped to the intended sense. |
| spaCy + Stanza | Validation layer | Check the target lemma/form actually appears and sentence segmentation/tokenization are sane. |

**Why:** Tatoeba is not a good default quality bar for this product. A better 2025 stack is **generate with constraints, then validate**.

**Practical rule:**
- use lexical grounding + prompt template + structured output
- verify sentence length, lemma inclusion, banned patterns, and language correctness
- keep human-review hooks for the top-frequency decks

**Confidence:** MEDIUM.

### 4) Translation quality

**Recommended stack**

| Technology | Version / family | Role | Why |
|---|---|---|---|
| DeepL API | current API | Primary sentence translation | Strong support for all target languages here and usually better literal sentence quality than generic LLM-only translation for European languages. | 
| LLM judge / rewrite pass | same provider as generation | Repair/normalize edge cases | Use only as fallback or QA, not as the main translator. |

**Why:** your output is learner-facing and sentence translation accuracy matters more than generic AI flexibility. DeepL is the better default translation backbone here.

**Do not:** rely on the same LLM prompt that generated the sentence to also “translate itself” as the only quality mechanism.

**Confidence:** HIGH for language coverage, MEDIUM for final quality until evaluated on your sentence style.

### 5) TTS / audio generation

**Recommended stack**

| Technology | Version / family | Role | Why |
|---|---|---|---|
| Azure Speech Service | current | TTS provider | Officially supports TTS voices for the target languages and is already the intended provider. |
| `azure-cognitiveservices-speech` | **1.49.x** | Python SDK | Official SDK with current releases and good Python support. |
| SSML | Azure SSML support | Pronunciation/styling control | Necessary for pronunciation tuning, voice selection, pacing, and multilingual handling. |

**Why:** Azure Speech is the most natural fit here because voice coverage is broad, SSML is mature, and Python integration is straightforward.

**Implementation advice:**
- Generate and cache **word audio** and **sentence audio** separately
- Track voice ID, locale, SDK version, and synthesis hash in DB
- Make audio generation idempotent

**Confidence:** HIGH.

### 6) Anki export

**Recommended stack**

| Technology | Version / family | Role | Why |
|---|---|---|---|
| `genanki` | **0.13.1** | `.apkg` generation | Still the pragmatic Python standard for generating Anki decks programmatically with media packaging. |
| Stable internal card schema | custom | Export contract | Prevents export logic from leaking into generation logic. |

**Why:** this is exactly the kind of task Python is better at. `genanki` is not flashy, but it directly matches the product need.

**Important:** use stable note GUID generation from `(language, lemma, rank/list_id)` so regenerated decks update cleanly in Anki instead of duplicating notes.

**Confidence:** MEDIUM-HIGH (library is older, but still the practical default).

### 7) Storage model

**Canonical entities**

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

**Recommendation:** keep **normalized generation data** in Postgres, and only materialize final Anki fields at export time.

Why: you will re-run prompts, switch voices, fix IPA normalization, and regenerate exports. A flat CSV-first architecture will become painful quickly.

### 8) Testing stack

| Technology | Version / family | Purpose | Why |
|---|---|---|---|
| pytest | **9.x** family | Test runner | Standard Python choice; strong fixtures and parametrization. |
| HTTPX | current stable | API tests / external client mocking | Natural fit with FastAPI and async integrations. |
| PydanticAI test utilities / mock providers | current family | AI workflow tests | Lets you test deterministic structured outputs without hitting live models. |
| Golden-file fixtures | custom | Deck/export regression tests | Essential for ensuring card field order, HTML, media refs, and GUID stability. |

**Minimum test layers:**
- lexical normalization tests
- prompt/output schema tests
- translation/TTS provider adapter tests
- `.apkg` export regression tests
- end-to-end “generate 10 cards” smoke test

**Confidence:** HIGH.

---

## Recommended application shape

### MVP shape

1. **Typer CLI** for batch generation workflows
   - `import-frequency`
   - `import-lexicon`
   - `generate-cards`
   - `synthesize-audio`
   - `export-anki`

2. **FastAPI admin/internal API**
   - trigger generation jobs
   - inspect failed jobs
   - preview cards
   - download exports

3. **Worker process**
   - LLM generation
   - translation
   - TTS synthesis
   - export packaging

### Why this shape

This product is fundamentally a **data pipeline with export**, not a realtime consumer SaaS app first. A CLI-first + API-assisted architecture is the cleanest v1. Build the web UI later on top of the same services.

---

## What NOT to use

| Avoid | Why not |
|---|---|
| Full JS/TS backend as the primary stack | Worse fit for lexical ETL, Python-only language tooling, and Anki packaging. |
| LangChain as the default orchestration layer | Too much abstraction for a product that needs deterministic typed outputs, not agent experimentation. |
| Tatoeba as default sentence source | Known quality concern; should be optional reference data only. |
| SQLite as production source of truth | Fine for local dev; weak for concurrent generation jobs, auditability, and long-lived assets. |
| “LLM-only” dictionary/IPA generation | Too hallucination-prone for learner content. Ground first, generate second. |
| Live provider responses as permanent truth | Always persist normalized outputs and provider metadata; never make export depend on re-calling providers. |

---

## Installation baseline

```bash
# project/runtime
uv init
uv add fastapi typer pydantic sqlalchemy alembic psycopg[binary] httpx

# ai/orchestration
uv add pydantic-ai litellm

# language + export
uv add wordfreq stanza spacy genanki azure-cognitiveservices-speech

# testing
uv add --dev pytest pytest-asyncio
```

**Optional later:** `redis`, worker library (`arq`/`dramatiq` family), `orjson`, `logfire`.

---

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

If you want one sentence: **this should be a Python data-product stack with strong lexical grounding and typed AI orchestration, not a generic JS AI app.**

---

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

---

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
