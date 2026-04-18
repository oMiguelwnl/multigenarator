# Project Research Summary

**Project:** Multilang Anki Card Generator
**Domain:** Multilingual AI-assisted Anki deck generation
**Researched:** 2026-04-18
**Confidence:** MEDIUM-HIGH

## Executive Summary

Multilang should be built as a **Python-based batch content pipeline** that produces reliable Anki decks, not as a generic AI app or a hosted learning platform. The research is consistent: the hard part is not generating text, but producing **lexically grounded, reviewable, Anki-safe cards** with good examples, faithful translations, stable audio, and deterministic export behavior. The recommended v1 shape is **library-first**, with a thin **CLI** for deck generation and an optional internal/admin API later.

The strongest recommendation is to optimize for **quality control and reproducibility** over feature breadth. Use **FastAPI + Typer + Pydantic + SQLAlchemy + PostgreSQL** for the backbone, **Kaikki/Wiktextract + curated frequency assets** for lexical grounding, **PydanticAI + LiteLLM** for structured generation, **DeepL** for sentence translation, **Azure Speech** for audio, and **genanki** for `.apkg` export. v1 should focus on the 7 target languages, 3-level frequency decks, custom word-list import, a fixed card schema, and a minimal review/regeneration loop.

The biggest risks are also clear: treating words as raw strings instead of lexical entries, shipping raw frequency lists as curriculum, trusting one-shot AI output, and discovering Anki/TTS issues too late. Planning should therefore start with the **card schema, lexical identity model, export contract, and validation gates**, then move into enrichment and generation. Do not attempt a rich frontend, extra languages, image generation, or an Anki competitor in v1.

## Key Findings

### Recommended Stack

The stack research is unusually decisive: this project fits Python much better than JavaScript because it is fundamentally ETL + NLP + media generation + Anki packaging. The recommended app shape is a typed Python core with batch orchestration, persisted artifacts, and provider adapters so generation, translation, TTS, and export can evolve independently.

**Core technologies:**
- **Python 3.12 + uv**: main runtime and project management — best fit for language tooling, lexical ETL, and export workflows.
- **FastAPI + Typer**: admin/API and CLI surfaces — gives a clean internal API while keeping batch commands first-class.
- **Pydantic v2 + SQLAlchemy 2 + PostgreSQL 17 + Alembic**: schema, persistence, and migrations — needed for strict contracts, resumability, provenance, and stable exports.
- **PydanticAI + LiteLLM**: typed LLM orchestration — use LLMs for structured generation and adjudication, not as the source of truth.
- **Kaikki/Wiktextract + curated frequency assets + `wordfreq` bootstrap**: lexical grounding — seed with `wordfreq`, then freeze reviewed lists and normalize into an internal schema.
- **DeepL + Azure Speech + genanki**: translation, audio, and Anki export — strongest fit for learner-facing translations, broad voice support, and `.apkg` generation.

**Critical version requirements:**
- Python **3.12** baseline
- Pydantic **v2** family
- SQLAlchemy **2.0** family
- PostgreSQL **17** target, keep schema **18-compatible**
- Azure Speech SDK **1.49.x**
- `genanki` **0.13.1**

### Expected Features

v1 is not “AI cards for everything.” It is a constrained deck generator with a very high trust bar. Users will forgive limited scope, but they will not forgive bad examples, weak translations, broken audio, or exports that need manual repair.

**Must have (table stakes):**
- Language selection limited to the 7 v1 languages
- Frequency-list deck generation with 3 levels × 1000 cards
- Custom word-list import
- Fixed Anki-ready schema with the requested fields
- Clean CSV/TSV export and primary `.apkg` export behavior
- Word enrichment: normalized word, lemma/POS where available, IPA, definitions
- Example sentence generation/sourcing with quality checks
- High-quality sentence translation
- Word and sentence audio
- Minimal review/edit/regenerate flow
- Duplicate detection, resumable jobs, progress/failure visibility

**Should have (competitive):**
- Quality-gated sentence pipeline
- Quality-gated translation pipeline
- Per-language generation/rendering rules
- Sense disambiguation for polysemous words
- Source/provenance metadata in review surfaces
- Deck linting and field-level regeneration

**Defer (v2+):**
- Full spaced-repetition app
- Browser-extension/web capture workflows
- AI tutor/chat features
- Automatic image generation/sourcing
- Broad language expansion beyond the 7 targets
- Rich theme/styling builders or deck marketplace features

### Architecture Approach

The architecture research strongly favors **library-first, stage-based pipeline design**. The canonical unit is a `CardSpec`/card record that each stage enriches and validates. The system should persist artifacts after ingestion, enrichment, generation, validation, audio, and export so failures are inspectable and reruns are cheap.

**Major components:**
1. **CLI / orchestrator** — runs batch jobs, checkpoints stages, reports progress, and coordinates retries.
2. **Ingestion + lexical enrichment** — normalizes inputs, deduplicates, attaches lemma/POS/IPA/definitions, and stores provenance.
3. **Generation + validation + repair** — produces example/translation, runs quality gates, retries/falls back, and routes failures to review.
4. **Audio adapter** — synthesizes word and sentence audio only after text passes validation.
5. **Deck assembler + exporters** — maps canonical fields to Anki, emits `.apkg`, and writes CSV/JSONL manifests for debug/recovery.

### Critical Pitfalls

1. **Modeling a word as just a string** — define lexical identity early (`lemma`, `pos`, sense/morphology metadata) so decks do not collapse meanings or duplicate inflections.
2. **Shipping raw frequency lists as curriculum** — use `wordfreq` only as bootstrap data, then filter and freeze curated lists per language.
3. **Trusting one-shot AI output** — separate generation, validation, and repair; validate word presence, sense alignment, translation faithfulness, and formatting.
4. **Ignoring language-specific rules** — keep one schema but support per-language rendering, morphology, and acceptance tests from the start.
5. **Leaving export/audio validation until late** — freeze the Anki contract early, build stable note identity, and create a voice matrix plus synthesis smoke tests before bulk runs.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Schema, Lexical Identity, and Pipeline Shell
**Rationale:** Everything else depends on stable card contracts and stage boundaries; starting with generation first would create rework.
**Delivers:** Canonical `CardSpec`, lexical record, field contract, stable note/GUID strategy, config model, artifact layout, CLI skeleton, no-op/sample pipeline.
**Addresses:** Fixed Anki-ready schema, duplicate handling foundation, export compatibility, language selection scaffold.
**Avoids:** Raw-string lexical modeling, inconsistent field formatting, late export design.

### Phase 2: Input Ingestion and Deterministic Enrichment
**Rationale:** Quality generation depends on clean inputs and grounded lexical context.
**Delivers:** Frequency ingestion, custom list import, filtering/teachability rules, per-language config registry, lemma/POS/IPA/definition enrichment, provenance capture.
**Uses:** `wordfreq`, Kaikki/Wiktextract, Pydantic, SQLAlchemy/Postgres.
**Implements:** Ingestion/normalizer, card store, enrichment adapters, Gate A/B validation.

### Phase 3: Text Quality Engine
**Rationale:** Example sentence and translation quality are the core product risk and should be proven before audio/export polish.
**Delivers:** Sentence generation, translation pipeline, validation rules, repair/fallback loop, confidence scoring, benchmark deck checks, minimal manual review queue.
**Addresses:** Example generation, translation quality, edit/regenerate workflow, failure visibility.
**Avoids:** One-shot AI generation, poisoned example sources, coupling translation to definitions.

### Phase 4: Audio Integration
**Rationale:** Audio is expected in v1, but only after text quality is trustworthy.
**Delivers:** Azure voice matrix, word/sentence TTS adapters, SSML policy, `display_text` vs `tts_text` separation, audio caching, media validation.
**Addresses:** Word and sentence audio, resumable generation, provider metadata.
**Avoids:** Late voice/locale surprises, broken synthesis from display formatting, non-idempotent media generation.

### Phase 5: Export, Reimport, and Deck Reliability
**Rationale:** The product succeeds or fails at the Anki boundary; export should be hardened after upstream fields stabilize.
**Delivers:** `.apkg` export via `genanki`, CSV/TSV + JSONL fallback manifests, golden import/reimport tests, media reference checks, deck-level linting.
**Addresses:** Clean Anki import, duplicate/update behavior, deterministic deck outputs.
**Avoids:** Broken UTF-8/escaping, unstable note identity, silent partial failures.

### Phase 6: Workflow Hardening and Language-Specific Differentiation
**Rationale:** Once the baseline pipeline works, invest in the features that most improve trust and multilingual quality.
**Delivers:** Better review UX, field-level regeneration, per-language rules, sense disambiguation, provenance surfaces, resumability/concurrency improvements.
**Addresses:** Main differentiators worth keeping in scope after baseline reliability.
**Avoids:** Premature frontend/platform expansion while still improving real output quality.

### Phase Ordering Rationale

- Put **contracts before content generation**: schema, lexical identity, and export semantics are prerequisites, not cleanup work.
- Group **input + enrichment** together because the generation phase depends on grounded lexical context and curated frequency data.
- Isolate **text quality** as its own phase because it is the main trust risk and the most likely area to need iteration.
- Delay **audio** until validated text exists, and delay **export hardening** until field semantics are stable.
- Keep **differentiators** after baseline reliability, except for the minimal review queue, which belongs in v1 because users need a way to fix bad cards without rerunning everything.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** lexical normalization, per-language teachability filters, and pronunciation policy need more implementation-level design.
- **Phase 3:** sentence quality scoring, translation validation, and benchmark strategy are the most complex product-quality problems.
- **Phase 4:** Azure voice selection and locale/SSML behavior need explicit capability validation for all 7 languages.

Phases with standard patterns (skip research-phase):
- **Phase 1:** schema, typed pipeline shell, CLI structure, persistence, and migrations are all well-understood patterns.
- **Phase 5:** Anki export testing, UTF-8 handling, and deterministic packaging are straightforward once field contracts are frozen.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Backed mostly by official docs and strong ecosystem fit; Python choice is well-supported by the problem shape. |
| Features | MEDIUM | Table stakes are plausible and useful, but some market expectations were inferred from adjacent tools rather than direct user validation. |
| Architecture | MEDIUM-HIGH | The library-first pipeline recommendation is an informed design judgment strongly aligned with the product shape, even where not directly sourced from vendor docs. |
| Pitfalls | HIGH | Anki and Azure constraints are well documented, and the major content-quality risks are consistently supported across research. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Per-language lexical policy:** decide required metadata and rendering rules for each of the 7 languages before large-scale deck generation.
- **Frequency curation policy:** define inclusion/exclusion rules and spot-audit process before freezing the 3×1000-card lists.
- **Sentence quality rubric:** formalize what counts as acceptable length, naturalness, and register by language/level.
- **Translation QA policy:** define how fidelity will be checked against the example sentence, not just the headword meaning.
- **Voice inventory:** confirm preferred Azure voices and fallback voices for every target language, especially Dutch and locale variants.

## Sources

### Primary (HIGH confidence)
- FastAPI docs — API design patterns and typed service support
- Pydantic docs — schema validation approach
- SQLAlchemy + Alembic docs — persistence and migration patterns
- PostgreSQL docs — database baseline and compatibility direction
- Azure Speech docs — TTS language/voice support and SSML constraints
- DeepL docs — supported language coverage
- Anki Manual — import/export, duplicate handling, media syntax

### Secondary (MEDIUM confidence)
- `wordfreq` docs/README — ranked vocabulary bootstrap guidance and limitations
- Kaikki/Wiktextract docs — structured lexical source practicality
- `genanki` docs/PyPI — pragmatic `.apkg` export path
- LiteLLM docs — provider abstraction strategy
- spaCy and Stanza docs — validation-layer support for language checks

### Tertiary (LOW confidence)
- Adjacent product pages (Readlang, Migaku) — used only to infer user expectations and differentiator opportunities, not as implementation truth.

---
*Research completed: 2026-04-18*
*Ready for roadmap: yes*
