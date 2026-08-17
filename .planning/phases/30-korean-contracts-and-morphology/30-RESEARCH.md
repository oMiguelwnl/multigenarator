# Phase 30: Korean Contracts and Morphology - Research

**Researched:** 2026-08-03
**Domain:** Canonical Korean language contracts, Unicode NFC, Kiwi morphology, lexical identity, and fail-closed target matching
**Confidence:** HIGH overall; MEDIUM for the initial multi-analysis ambiguity policy

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| KMODE-01 | Accept canonical `ko` for frequency, word-list, and highlight generation; reserve `ko-KR` for provider/locale values. | Add `SupportedLanguage.KO`, one Korean profile, boundary-only locale constants, capability-separated frequency routing, and canonical-code persistence/export tests. [VERIFIED: `.planning/SPEC.md:38`; `.planning/ROADMAP.md:49-59`; codebase `domain/jobs.py`, `settings.py`, `domain/source_profiles.py`] |
| KMODE-02 | Preserve all existing language, source-mode, template, audio, persistence, and export behavior. | Isolate Korean branches before generic heuristics, keep existing source profiles/export schemas, make Kiwi lazy and Korean-only, and run the existing modern/Japanese/Mandarin/Latin/phoneme regression matrix. [VERIFIED: `.planning/SPEC.md:39`; `.planning/phases/30-korean-contracts-and-morphology/30-PATTERNS.md`] |
| KNLP-01 | Normalize Korean to NFC and analyze lemma, POS, and morphology with a pinned analyzer. | Pin `kiwipiepy==0.23.2` plus `kiwipiepy-model==0.23.0`, centralize NFC/script validation, persist typed identity and analyzer fingerprint, and exercise real-analyzer goldens. [VERIFIED: `.planning/SPEC.md:40,85-93`; PyPI registry; kiwipiepy v0.23.2 docs; Unicode UAX #15] |
| KNLP-02 | Match examples and highlights by Korean morpheme signatures and fail closed when analysis is unavailable or inconclusive. | Compare normalized `(form, base-POS)` signatures within Kiwi `word_position` boundaries, preserve `XSV`/`XSA`, reject heuristic fallback, and model mismatch/ambiguous/OOV/unavailable as explicit outcomes. [VERIFIED: `.planning/SPEC.md:41`; `KOREAN-STRUCTURE.md:334-351`; kiwipiepy v0.23.2 docs/runtime] |
</phase_requirements>

## Summary

Phase 30 should add Korean as a modern-pipeline capability, not as a second isolated pipeline. The canonical identity must be `ko` in requests, settings, run keys, database rows, lexical lookup, cache keys, export identities, and Anki tags; `ko-KR` belongs only at provider/locale boundaries. The three existing source profiles remain the route for frequency, word-list, and Kindle highlights, while a Korean domain contract and morphology adapter provide language-specific normalization and identity evidence. [VERIFIED: `.planning/SPEC.md:38-41,137-148`; `KOREAN-STRUCTURE.md:294-351,475-481`; codebase `domain/source_profiles.py`, `domain/jobs.py`]

Use Python's `unicodedata.normalize("NFC", ...)` at every Korean canonicalization boundary and reject Compatibility Jamo and halfwidth Hangul rather than compatibility-folding them. Feed only canonical NFC text to a single, lazily constructed Kiwi service. Resolve an identity by intersecting analyzer output with source-backed lemma/POS/sense records; Kiwi morphology is evidence, not a dictionary-sense authority. Persist the resulting typed identity before text generation so resumed jobs and validation use the same analyzer evidence. [CITED: https://www.unicode.org/reports/tr15/]; [CITED: https://docs.python.org/3.12/library/unicodedata.html]; [VERIFIED: `.planning/SPEC.md:85-93`; `KOREAN-STRUCTURE.md:296-312,343-358`]

For Korean target presence, bypass the existing whitespace/subsequence/suffix fallback completely. Build lexical signatures from Kiwi tokens, normalize `VV-I`/`VV-R`-style tags to their base POS for comparison, remove particles and inflectional endings, retain derivational `XSV`/`XSA`, and require compound-signature tokens to share one `word_position`. Any missing identity, analyzer/model exception, OOV target, unresolved lexical sense, or analysis disagreement becomes review-required rather than accepted. [VERIFIED: `KOREAN-STRUCTURE.md:334-351`; codebase `services/text_validation.py:268-319`; kiwipiepy v0.23.2 docs/runtime]

**Primary recommendation:** Implement one typed `KoreanLexicalIdentity`, one shared lazy `KiwiKoreanMorphologyService`, and one strict Korean matcher; persist their evidence and never let `ko` reach the generic heuristic target-matching path. [VERIFIED: `.planning/SPEC.md:75-123`; `.planning/phases/30-korean-contracts-and-morphology/30-PATTERNS.md`]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Canonical language identity and source-mode routing | API / Backend | Database / Storage | Requests and orchestration own `ko`; persistence stores that same enum value. [VERIFIED: codebase `domain/jobs.py`, `job_repository.py`, `export_repository.py`] |
| Korean profile and Portuguese output policy | API / Backend | External provider boundary | The backend selects Korean rules and Portuguese definition/translation targets; adapters translate canonical codes into provider values. [VERIFIED: `KOREAN-STRUCTURE.md:360-368`; codebase `domain/lexicon.py`, `provider_text_adapters.py`] |
| NFC and Korean script acceptance | API / Backend | Database / Storage | Canonicalization must happen before analysis, hashing, lookup, persistence, and export, with canonical values stored at rest. [VERIFIED: `.planning/SPEC.md:40`; `KOREAN-STRUCTURE.md:353-358`] |
| Lemma/POS/morpheme analysis | API / Backend | Kiwi package/model boundary | A local adapter owns analyzer configuration and converts vendor tokens into project domain evidence. [CITED: https://bab2min.github.io/kiwipiepy/v0.23.2/kr/]; [VERIFIED: codebase `services/morphology.py`] |
| Lexical sense resolution | API / Backend | Database / Storage | A curated lexical source supplies `sense_id`; Kiwi output constrains morphology/POS but does not replace source-backed senses. [VERIFIED: `.planning/SPEC.md:85-93`; `KOREAN-STRUCTURE.md:296-312`] |
| Target-in-sentence and highlight matching | API / Backend | — | Matching is a deterministic domain validation decision over stored identity and analyzer-derived sentence signatures. [VERIFIED: `.planning/SPEC.md:41`; `KOREAN-STRUCTURE.md:334-351`] |
| Analyzer evidence durability | Database / Storage | API / Backend | The repository persists identity plus analyzer fingerprint so resume/reload does not silently reanalyze under different behavior. [VERIFIED: codebase `db/models.py:207-248`, `repositories/lexical_repository.py:185-235`; `.planning/SPEC.md:112-123`] |
| Generic card rendering/export | API / Backend | Database / Storage | Phase 30 should verify existing generic schemas and `ko` tags, not add final Korean note types or learner-visible morphology fields. [VERIFIED: `KOREAN-STRUCTURE.md:410-421,475-481`; codebase `domain/exporting.py`, `export_anki_package.py`] |

## Project Constraints (from AGENTS.md)

- Use modern standard Korean with canonical code `ko`, reserving `ko-KR` for provider locale contracts. [VERIFIED: `AGENTS.md:12-18`]
- Korean canonical content must use NFC and morphology-aware lemma/POS/sense identity; target matching must fail closed rather than use whitespace or suffix heuristics. [VERIFIED: `AGENTS.md:16-18`]
- Do not commit a redistributed 3000-entry Korean frequency asset before source, attribution, and redistribution approval. [VERIFIED: `AGENTS.md:18`; `.planning/SPEC.md:20-22`]
- Preserve three 1000-card frequency levels, requested card fields/formatting, privacy-safe highlights, and existing modes. Phase 30 establishes contracts but does not create those later-phase assets or final decks. [VERIFIED: `AGENTS.md:15-22`; `.planning/ROADMAP.md:43-107`]
- Keep Tatoeba non-default because prior output quality is a known concern; ground generated content and retain review hooks. [VERIFIED: `AGENTS.md:19,69-77,123-131`]
- Keep Azure Speech as the preferred modern-language TTS direction, but Phase 32 owns Korean live voice qualification. [VERIFIED: `AGENTS.md:20,83-91`; `.planning/ROADMAP.md:73-83`]
- Use the existing Python/Pydantic/SQLAlchemy/Alembic/pytest architecture and `uv` lockfile workflow; do not replace the backend with JavaScript or add LangChain. [VERIFIED: `AGENTS.md:25-51,108-131,161-170`; `pyproject.toml`]
- Use `wordfreq` only for candidate bootstrapping and freeze approved production lists; do not treat live provider responses as permanent truth. [VERIFIED: `AGENTS.md:52-68,123-131,161-170`]
- Follow existing code patterns because project conventions and architecture are not separately mapped; test substantive behavior and fallbacks. [VERIFIED: `AGENTS.md:204-214`; codebase]
- Stay in approved scope, research real APIs, verify artifacts before claiming completion, and keep vendor-specific implementation behind adapters. [VERIFIED: `AGENTS.md:135-155`]

## Scope Boundaries

Phase 30 owns contracts, registries, Kiwi, Unicode, persisted morphology evidence, and target matching. Hangul/pronunciation curricula belong to Phase 31; Korean frequency data/text/audio to Phase 32; full grammar/personal-source pedagogy to Phase 33; and final Korean export/review evidence to Phase 34. [VERIFIED: `KOREAN-STRUCTURE.md:475-481`; `.planning/ROADMAP.md:49-107`]

Do not create a Korean 3000-row asset, guess an Azure voice, synthesize Korean audio, add Korean-specific note/model/deck IDs, add Romanization/Hanja/dialect behavior, or claim final APKG readiness in this phase. [VERIFIED: `.planning/SPEC.md:126-156`; `KOREAN-STRUCTURE.md:475-506`]

Korean frequency must become a selectable capability while the actual asset boundary remains explicitly license-blocked. Separate “selectable languages” from “languages with approved committed frequency assets”; test the Korean frequency route with temporary/fake candidates and make an explicit real `ko` asset build fail with an actionable gate. [VERIFIED: `.planning/SPEC.md:38,55-57`; codebase `scripts/build_frequency_assets.py`; `.planning/phases/30-korean-contracts-and-morphology/30-PATTERNS.md:272-306`]

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | Project baseline `>=3.12` | Runtime, Unicode normalization, typed services | Existing project runtime; `unicodedata` provides NFC normalization and normalized-form checks. [VERIFIED: `pyproject.toml:10`; CITED: https://docs.python.org/3.12/library/unicodedata.html] |
| `kiwipiepy` | **exactly `0.23.2`** | Korean tokenization, morphology, lemma/POS, word boundaries, OOV evidence | Current PyPI release on 2026-08-03; it exposes `analyze`, token POS/form/lemma/`word_position`, standard-dialect configuration, and fixes Windows model paths containing Unicode. [VERIFIED: PyPI JSON queried 2026-08-03; CITED: https://bab2min.github.io/kiwipiepy/v0.23.2/kr/; CITED: https://github.com/bab2min/kiwipiepy/releases/tag/v0.23.2] |
| `kiwipiepy-model` | **exactly `0.23.0`** | Analyzer model files | `kiwipiepy 0.23.2` declares `kiwipiepy_model>=0.23,<0.24`; pinning the current model removes transitive model drift. [VERIFIED: https://pypi.org/pypi/kiwipiepy/json; https://pypi.org/pypi/kiwipiepy-model/json] |
| Pydantic | Existing `>=2.11,<3.0`; installed `2.12.5` | Domain contracts and cross-field invariants | Existing candidate/request contracts already use Pydantic models and validators. [VERIFIED: `pyproject.toml`; local environment; codebase `domain/lexicon.py`] |
| SQLAlchemy + Alembic | Existing SQLAlchemy `>=2,<3` / Alembic `>=1.16,<2`; installed `2.0.49` / `1.18.4` | Nullable typed-evidence persistence and migration | Existing lexical candidates are ORM-backed and migration parity is already tested. [VERIFIED: `pyproject.toml`; local environment; codebase `db/models.py`, `repositories/lexical_repository.py`, `tests/test_migration_schema_parity.py`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `unicodedata` | Python 3.12 standard library; UCD 15.0 in Python 3.12 docs | NFC, code-point inspection, normalized-form checks | Use at every canonical Korean boundary; never write a custom Hangul composer. [CITED: https://docs.python.org/3.12/library/unicodedata.html] |
| pytest | Existing `>=8.3,<9.0`; installed `8.4.2` | Real-analyzer goldens, service fakes, migration and integration regressions | Use real Kiwi for linguistic positives and fakes only for unavailable/error branches and orchestration. [VERIFIED: `pyproject.toml`; local environment; existing `tests/`] |
| `hashlib.sha256` | Python standard library | Stable privacy-safe candidate and evidence fingerprints | Hash only after NFC and include lemma/POS/sense in lexical identity payloads. [VERIFIED: codebase `highlight_candidate_extraction.py:200-226`; `KOREAN-STRUCTURE.md:316-324`] |

### Version Decision

PyPI reported `kiwipiepy 0.23.2`, uploaded `2026-06-11T15:36:55Z`, with a `cp39-abi3-win_amd64` wheel and dependency `kiwipiepy_model>=0.23,<0.24`; the isolated package ran successfully on the current Windows Python 3.13.7 environment. PyPI reported `kiwipiepy-model 0.23.0`, uploaded `2026-03-17T16:28:32Z`. [VERIFIED: PyPI JSON queries and isolated runtime on 2026-08-03]

The exact two-package pin is deliberate: analyzer code and model both affect signatures, so a broad compatible range is not deterministic enough for persisted lexical evidence. Record both versions plus an application-owned configuration version on every resolved Korean identity. [VERIFIED: `.planning/SPEC.md:40,112-123`; PyPI dependency metadata; recommendation derived from persistence requirements]

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Kiwi `cong` | Kiwi `cong-global` | Official docs say `cong-global` considers longer-range context and is about twice as slow; use explicit `cong` for this phase's short lexical/example validation and lock fixtures to it. [CITED: https://bab2min.github.io/kiwipiepy/v0.23.2/kr/] |
| Kiwi | Existing optional Stanza adapter | Retain Stanza for existing languages only; its current project API yields only lemma-presence reliability and falls back to generic heuristics, so it cannot satisfy Korean compound signatures or fail-closed extraction. [VERIFIED: codebase `services/morphology.py`, `services/text_validation.py`; `KOREAN-STRUCTURE.md:328-351`] |
| Kiwi | KoNLPy/JVM stack | Do not introduce it; the approved Korean design selects Kiwi and explicitly declines KoNLPy as the new base. [VERIFIED: `KOREAN-STRUCTURE.md:328-333`] |
| NFC | NFKC | Do not substitute it: NFC preserves compatibility distinctions while NFKC applies compatibility decomposition; Korean canonical content must reject compatibility/halfwidth forms instead of hiding them. [CITED: https://www.unicode.org/reports/tr15/]; [VERIFIED: `KOREAN-STRUCTURE.md:353-358`] |

**Installation:**

```bash
uv add "kiwipiepy==0.23.2" "kiwipiepy-model==0.23.0"
uv lock --check
uv run python -c "import kiwipiepy, kiwipiepy_model; print(kiwipiepy.__version__, kiwipiepy_model.__version__)"
```

These package names and versions were verified against PyPI; import names use underscores. [VERIFIED: PyPI registry and isolated runtime]

## Architecture Patterns

### System Architecture Diagram

```text
Frequency request ─────┐
Word-list UTF-8 file ──┼──> GenerationRequest(language=ko, source profile)
Private highlights ────┘                    │
                                             v
                          Korean acceptance boundary
                    reject compatibility/halfwidth Hangul
                              then canonicalize NFC
                                             │
                                             v
                      shared lazy Kiwi adapter + pinned model
                       analyze top candidates and boundaries
                                             │
                   ┌─────────────────────────┴────────────────────────┐
                   │ resolved against source lemma/POS/sense?         │
                   └──────────────┬───────────────────────┬───────────┘
                                  │ yes                   │ no
                                  v                       v
                    KoreanLexicalIdentity       typed blocked outcome
                  signature + analyzer evidence   ambiguous/OOV/unavailable
                                  │                       │
                                  v                       └──> needs_review / stop
                    SQLAlchemy repository
                    nullable JSON evidence
                                  │
                                  v
                grounded text request (Korean identity included)
                                  │
                                  v
                     provider-generated Korean output
                     normalize NFC; treat as untrusted
                                  │
                                  v
                   Kiwi sentence analyses + signature match
                         ┌────────┴────────┐
                         │ consensus match?│
                         └──────┬─────┬────┘
                                │ yes │ no/disagreement/unavailable
                                v     v
                           accepted  needs_review
                                │
                                v
               existing generic snapshot/export contracts
                         canonical `ko` tag/identity

External/service boundaries: PyPI-installed Kiwi model (local inference),
provider adapters (generation only), and SQL database persistence.
```

This flow keeps morphology local and authoritative for matching while keeping LLM/provider output untrusted and downstream of source-backed identity. [VERIFIED: `.planning/SPEC.md:9-13,38-41,150-156`; codebase generation/validation flow]

### Recommended Project Structure

```text
src/multilang/
├── domain/
│   ├── korean.py                    # canonical constants and typed identity/results
│   ├── jobs.py                      # SupportedLanguage.KO
│   ├── lexicon.py                   # optional Korean identity on shared candidate
│   └── highlights.py                # optional safe Korean identity evidence
├── services/
│   ├── korean_morphology.py         # lazy Kiwi adapter and signature matcher
│   ├── lexical_grounding.py         # all three ko routes resolve identity
│   ├── highlight_candidate_extraction.py
│   ├── text_generation.py           # identity participates in request/cache key
│   ├── text_validation.py           # strict ko branch before heuristics
│   └── provider_text_adapters.py    # Korean name, canonical-code boundary
├── db/models.py                     # nullable korean_identity JSON
├── repositories/lexical_repository.py
└── runtime.py                       # one shared adapter instance
alembic/versions/
└── 20260803_16_korean_lexical_identity.py
tests/
├── domain/test_korean.py
├── services/test_korean_morphology.py
├── services/test_korean_language_support.py
└── integration/test_korean_modern_flow.py
```

The file mapping follows existing Latin contract, Mandarin adapter/integration, shared lexical repository, and current unique Alembic head `20260720_15`. [VERIFIED: codebase; `.planning/phases/30-korean-contracts-and-morphology/30-PATTERNS.md`]

### Component Responsibilities

| Component | Responsibility | Planning instruction |
|-----------|----------------|----------------------|
| `domain/korean.py` | Constants, normalization error, signature item, analyzer fingerprint, resolution/match status, lexical identity. | Make resolved identity impossible when canonical text is non-NFC, lemma/POS/sense/signature is blank, or analysis is not resolved. [VERIFIED: `.planning/SPEC.md:75-123`; Latin invariant precedent in codebase] |
| `korean_morphology.py` | Hide all vendor APIs; produce project-domain analyses and matches. | Lazy-load once, capture safe exceptions by class, and return typed unavailable rather than raising through unrelated language startup. [VERIFIED: codebase `services/morphology.py:33-96`; KMODE-02] |
| `lexical_grounding.py` | Intersect analyzer candidates with source records and bind `sense_id`. | A Korean candidate becomes grounded only when exactly one source-backed lemma/POS/sense is compatible; never let the LLM invent identity. [VERIFIED: `.planning/SPEC.md:85-93,150-155`; codebase `services/lexical_grounding.py`] |
| highlight extraction | Analyze local bounded text, retain one-syllable lexemes, attached morphology, ordering, and hash-only provenance. | Branch before current NFKC/length/regex path; do not persist excerpts, local paths, or token dumps. [VERIFIED: `KOREAN-STRUCTURE.md:314-326`; codebase `highlight_candidate_extraction.py:49-226`] |
| text request/cache | Carry Korean identity into generation input. | Since request dumps form cache keys, include POS/sense/signature so homographs cannot share generated output. [VERIFIED: codebase `services/text_generation.py`; `.planning/phases/30-korean-contracts-and-morphology/30-PATTERNS.md:631-653`] |
| text validation | Match the entire sentence against stored identity. | Handle `ko` before Japanese/Mandarin/generic branches; only `matched` passes, all other statuses emit morphology mismatch/review. [VERIFIED: codebase `services/text_validation.py:268-319`; KNLP-02] |
| repository + migration | Round-trip typed identity. | Add one nullable JSON column, serialize with `model_dump(mode="json")`, restore with `model_validate`, and keep existing rows `NULL`; migration descends from `20260720_15`. [VERIFIED: codebase `db/models.py`, `repositories/lexical_repository.py`, `alembic/versions/`] |
| runtime | Compose one adapter and inject it into grounding, highlights, and validation. | Do not instantiate Kiwi per card or create divergent configuration in each service. [VERIFIED: codebase `runtime.py`; kiwipiepy constructor docs] |
| asset/audio boundaries | Represent unsupported Korean asset/voice states with domain errors. | Do not satisfy enum exhaustiveness by creating a frequency CSV or guessing an Azure voice. [VERIFIED: `.planning/SPEC.md:20-22,55-59`; codebase `audio_voice_registry.py`, `scripts/build_frequency_assets.py`] |

### Pattern 1: Canonical Product Code, Locale at Edges

Add exactly `KO = "ko"` to `SupportedLanguage` and exactly `"ko"` to settings. Keep `KOREAN_PROVIDER_LOCALE = "ko-KR"` in the Korean domain module and permit it only in locale-aware adapters. [VERIFIED: `.planning/SPEC.md:38,137-143`; codebase `domain/jobs.py`, `settings.py`]

The canonical scan after implementation should reject `ko-KR` in job languages, run keys, source directories, cache identities, lexical keys, persistence, or Anki tags. [VERIFIED: codebase `job_repository.py`, `export_repository.py`, `export_anki_package.py`; KMODE-01]

### Pattern 2: Validate Script, Then NFC, Then Derive Keys

Reject Compatibility Jamo block `U+3130–U+318F` and halfwidth Hangul `U+FFA0–U+FFDC`, then apply NFC. Unicode lists Hangul Compatibility Jamo at `3130..318F`; Python runtime inspection confirms NFC leaves representative Compatibility/Halfwidth characters unchanged while NFKC maps them to conjoining jamo. [CITED: https://www.unicode.org/Public/17.0.0/ucd/Blocks.txt]; [VERIFIED: Python `unicodedata` runtime on 2026-08-03]

Preserve the submitted string separately; derive display form, item key, analyzer input, canonical lemma, dedupe key, hashes, persistence values, and export text from the NFC value. Normalize again after concatenating or assembling text because Unicode normalization forms are not closed under concatenation. [CITED: https://www.unicode.org/reports/tr15/#Concatenation]; [VERIFIED: `KOREAN-STRUCTURE.md:294-305,353-358`]

### Pattern 3: Source-Constrained Morphology Resolution

Do not blindly accept Kiwi top-1 as lexical identity. In the pinned runtime, bare `배우다` ranks `배우/NNG + 이/VCP + 다/EF` above the intended `배우/VV + 다/EF`; source POS is therefore required to distinguish noun/copyula and verb analyses. [VERIFIED: isolated `kiwipiepy==0.23.2`, `kiwipiepy-model==0.23.0` runtime on 2026-08-03]

Resolution sequence: NFC-normalize input; obtain fixed-option analyses; retrieve source lexical candidates; retain analyses compatible with each source lemma/POS; require exactly one source-backed `sense_id`; and persist that chosen identity. Zero compatible records is OOV/insufficient, while multiple compatible lexical identities is ambiguous/review-required. [VERIFIED: `.planning/SPEC.md:85-93`; `KOREAN-STRUCTURE.md:296-312,343-351`; recommendation derived from observed ambiguity]

Kiwi's token `sense` is analyzer-internal meaning-number evidence and must not be copied into the project's `sense_id` without a documented lexical-source mapping. [CITED: https://bab2min.github.io/kiwipiepy/v0.23.2/kr/]; [VERIFIED: `.planning/SPEC.md:85-93`]

### Pattern 4: Signature Matching Within Eojeol Boundaries

Normalize POS suffixes `-R`/`-I` to base tags for identity comparison while retaining raw tag/regularity as diagnostic evidence. Exclude `J*` particles and `E*` endings; preserve `XSV`/`XSA`; compare ordered lexical `(NFC form, base POS)` tuples grouped by the same Kiwi `word_position`. [CITED: https://bab2min.github.io/kiwipiepy/v0.23.2/kr/]; [VERIFIED: `KOREAN-STRUCTURE.md:334-351`]

Use an explicit lexical tag allowlist rather than “everything not punctuation.” This prevents endings, web tokens, unknown `UN`, and appended-coda `Z_CODA` artifacts from becoming lexical identities. [CITED: https://bab2min.github.io/kiwipiepy/v0.23.2/kr/#id20]; [VERIFIED: recommendation based on KNLP-02]

### Pattern 5: Fail Closed Locally, Preserve Existing Languages

The adapter converts import/model/runtime errors into `unavailable` with analyzer/version and exception class only. Korean operations reject unavailable, ambiguous, OOV, or missing-identity results; non-Korean services retain their existing Stanza/heuristic behavior. [VERIFIED: KMODE-02/KNLP-02; codebase `services/morphology.py:47-96`, `services/text_validation.py:296-319`]

Do not import and initialize Kiwi at module import time. Lazy construction allows existing modes to boot if the Korean model is unavailable while ensuring the first Korean operation returns a controlled failure. [VERIFIED: codebase optional Stanza pattern; KMODE-02]

### Pattern 6: Persist Before Generation and Resume

Store one optional typed `korean_identity` object on `LexicalCardCandidate` and one nullable JSON column on `lexical_candidates`. Include canonical form, source lemma/POS/sense, signature, analyzer package/model versions, model type, dialect/config version, and resolution status; keep non-Korean constructors and rows unchanged. [VERIFIED: `.planning/SPEC.md:75-123`; codebase `domain/lexicon.py`, `db/models.py`]

On reload, validate the JSON back into the domain model. If runtime analyzer fingerprint differs from persisted evidence, require explicit reanalysis/review rather than silently mixing signatures from two versions. [VERIFIED: reproducibility principle in `.planning/SPEC.md:9-13`; repository round-trip precedent]

### Analyzer Configuration

Use one explicit configuration rather than relying on changing defaults. [CITED: https://bab2min.github.io/kiwipiepy/v0.23.2/kr/]

| Option | Phase 30 value | Reason |
|--------|----------------|--------|
| `num_workers` | `1` | One shared bounded worker avoids per-card pools; Kiwi preserves iterable input order, but this makes resource use explicit. [CITED: kiwipiepy v0.23.2 docs] |
| `model_type` | `"cong"` | Current default model family and suitable for short contextual examples; persist the value. [CITED: kiwipiepy v0.23.2 docs] |
| `enabled_dialects` | `"standard"` | Project scope is modern standard/Seoul Korean, not regional or archaic dialects. [VERIFIED: `.planning/SPEC.md:126-130`; CITED: kiwipiepy dialect docs] |
| `integrate_allomorph` | `True` | Constructor-documented allomorph integration; make it explicit in the fingerprint. [CITED: Context7 `/bab2min/kiwipiepy`, Kiwi constructor] |
| `split_complex` | `False` | Official default; it preserves stable surface derivations while still yielding `공부/NNG + 하/XSV`. [CITED: kiwipiepy split-complex docs]; [VERIFIED: isolated runtime] |
| `compatible_jamo` | `False` | Canonical content rejects Compatibility Jamo before analysis. [VERIFIED: `KOREAN-STRUCTURE.md:353-358`; isolated runtime accepts this option] |
| `normalize_coda` | `False` | Do not repair chat-style appended codas in canonical learner content. [CITED: kiwipiepy normalize-coda docs]; [VERIFIED: fail-closed project policy] |
| `z_coda` | `False` | Do not split malformed appended codas into `Z_CODA` evidence in strict canonical analysis. [CITED: kiwipiepy z-coda docs]; [VERIFIED: fail-closed project policy] |
| `typos` | `None` | Typo correction can alter forms and moved to analysis-time configuration in 0.23.0; Phase 30 identity must not silently correct input. [CITED: kiwipiepy v0.23.2 typo docs] |
| `oov_handling` | `"chr"` | This is the documented 0.23 default and exposes OOV tokens; explicit configuration prevents default drift. [CITED: kiwipiepy v0.23.2 OOV docs] |
| analysis alternatives | `top_n=2` | Initial conservative policy: accept target presence only when both returned analyses agree; disagreement is ambiguous. This must be locked by reviewed goldens before broad use. [ASSUMED] |

## Empirical Kiwi Findings

The following outputs were reproduced with `kiwipiepy==0.23.2`, `kiwipiepy-model==0.23.0`, `model_type="cong"`, standard dialect, and strict options on Windows/Python 3.13.7. [VERIFIED: isolated local runtime on 2026-08-03]

| Input | Relevant output | Planning consequence |
|-------|-----------------|----------------------|
| `학교에서` | `학교/NNG + 에서/JKB`, same `word_position=0` | Match `학교/NNG`; exclude the particle. [VERIFIED: isolated runtime] |
| `밥을 먹었어요` | `밥/NNG + 을/JKO`, then `먹/VV` (`lemma=먹다`) + `었/EP + 어요/EF` | `먹다` matches by `먹/VV`, not suffix stripping. [VERIFIED: isolated runtime] |
| `음악을 들어요` | Both top two analyses contain `듣/VV-I` (`lemma=듣다`); only final `EF`/`EC` differs | Normalize `VV-I` to `VV` for identity and keep irregularity as evidence. [VERIFIED: isolated runtime] |
| `꽃이 예뻐요` / `예뻐요` | `예쁘/VA` (`lemma=예쁘다`) + ending | Predicate matching can use the stem/POS signature. [VERIFIED: isolated runtime] |
| `공부해요` | `공부/NNG + 하/XSV + 어요/EF`, all in one eojeol | Compound identity is `공부/NNG + 하/XSV`; do not reduce it to noun `공부`. [VERIFIED: isolated runtime] |
| `배우가` | `배우/NNG + 가/JKS` | Noun identity remains distinct. [VERIFIED: isolated runtime] |
| `배워요` | `배우/VV` (`lemma=배우다`) + ending | Verb identity remains distinct despite shared visible stem. [VERIFIED: isolated runtime] |
| bare `배우다` | Top analysis is noun `배우/NNG + 이/VCP`; second is `배우/VV` | Identity creation must be source-POS constrained, not blind top-1. [VERIFIED: isolated runtime] |
| bare `걸어요` | Top analyses disagree between regular `걸다/VV` and irregular `걷다/VV-I` | Context-free disagreement is a useful ambiguity golden; `길을 걸어요` resolves both top analyses to `걷다`. [VERIFIED: isolated runtime] |
| Compatibility `ㄱ` / halfwidth `ﾡ` | NFC leaves each unchanged; Kiwi classifies tested compatibility forms as non-lexical `SW` | Reject these ranges before analysis instead of relying on Kiwi or NFKC. [VERIFIED: Python/kiwipiepy isolated runtime] |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hangul composition/canonical equivalence | Manual jamo composition tables | `unicodedata.normalize("NFC", ...)` | Unicode specifies canonical decomposition/composition, including Hangul. [CITED: https://www.unicode.org/reports/tr15/] |
| Korean tokenization and lemma recovery | Whitespace splitting, regex tokenization, suffix tables | Pinned Kiwi adapter | Korean particles/endings attach to eojeol and irregular/compound predicates require morphological analysis. [VERIFIED: `KOREAN-STRUCTURE.md:328-351`; isolated runtime] |
| Irregular conjugation | Custom rules for ㄷ/ㅂ/르/etc. | Kiwi token `lemma`, POS suffix, and reviewed contextual goldens | The pinned analyzer already returns dictionary lemmas and irregular tags; hand-written stripping would duplicate complex behavior. [CITED: kiwipiepy tag/Token docs] |
| Target matching | Substring, whitespace, or generic recursive suffix matching | Project signatures built from Kiwi tokens | Current generic heuristics can overmatch and are explicitly forbidden for Korean. [VERIFIED: `.planning/SPEC.md:41`; codebase `services/text_validation.py:57-128,726-759`] |
| Lexical senses | Kiwi `Token.sense`, LLM gloss hashes, or first-hit selection | Source-backed `sense_id` plus explicit ambiguity state | Project identity requires a stable external sense identifier and unresolved homographs must be reviewed. [VERIFIED: `.planning/SPEC.md:85-93`; `KOREAN-STRUCTURE.md:296-312`] |
| Analyzer lifecycle | A Kiwi instance per card/service | One runtime-composed lazy service with cache/fingerprint | Kiwi owns model files and optional worker pools; one configuration avoids startup and evidence drift. [CITED: kiwipiepy constructor/multithreading docs]; [VERIFIED: codebase composition-root pattern] |
| Persistence evolution | Prose in `provenance.notes` or ad-hoc schema checks | Typed Pydantic JSON plus Alembic migration/parity test | The identity must round-trip and be query/review usable after session expiration. [VERIFIED: codebase repository and migration patterns] |
| Korean frequency inventory or voice selection | Guessed CSV/voice constants | Explicit later-phase license/catalog gates | Source redistribution and exact Azure voice are deliberately unresolved until Phase 32. [VERIFIED: `.planning/SPEC.md:20-22,55-59`; `.planning/ROADMAP.md:73-83`] |

**Key insight:** The custom code should translate stable analyzer output into project contracts and policy decisions; it should not recreate Korean morphology. [VERIFIED: approved Kiwi decision in `.planning/SPEC.md:137-148`]

## Common Pitfalls

### Pitfall 1: Letting `ko-KR` Become a Second Language Identity
**What goes wrong:** Jobs, cache keys, rows, asset paths, and tags split between `ko` and `ko-KR`. [VERIFIED: KMODE-01 rationale in `.planning/SPEC.md:137-143`]
**How to avoid:** Accept only `SupportedLanguage.KO`; translate to `ko-KR` inside a locale-aware adapter and add a repository-wide canonical identity test. [VERIFIED: existing enum/provider-boundary pattern]
**Warning signs:** `SupportedLanguage("ko-KR")`, a `ko-KR` database value, or an Anki tag other than exactly `ko`. [VERIFIED: codebase persistence/export behavior]

### Pitfall 2: Conflating Selectable Languages with Approved Frequency Assets
**What goes wrong:** Adding `ko` to the default language tuple causes build-all/check paths to require or generate an unlicensed Korean CSV. [VERIFIED: codebase `settings.py`, `scripts/build_frequency_assets.py`; licensing gate]
**How to avoid:** Introduce an explicit approved-frequency-asset capability list that excludes Korean; direct Korean builds return the license gate. [VERIFIED: `.planning/SPEC.md:20-22,55-57`]
**Warning signs:** A new `assets/frequency/ko` file or silent skip in an explicit `--language ko` build. [VERIFIED: scope constraints]

### Pitfall 3: Applying NFKC Because Existing Highlight Code Does
**What goes wrong:** Compatibility characters are folded into ordinary jamo and invalid canonical input becomes indistinguishable from accepted input. [CITED: https://www.unicode.org/reports/tr15/#Norm_Forms]
**How to avoid:** Branch Korean before `_lemma_key()` in highlight extraction, reject forbidden ranges, and apply NFC. [VERIFIED: codebase `highlight_candidate_extraction.py:140-165`; `KOREAN-STRUCTURE.md:353-358`]
**Warning signs:** `normalize("NFKC", ...)` in a Korean canonical path or compatibility characters passing a golden. [VERIFIED: Korean contract]

### Pitfall 4: Normalizing Only at Initial Input
**What goes wrong:** Provider results, assembled strings, keys, hashes, or export snapshots can reintroduce canonically distinct forms; concatenating normalized strings is not guaranteed to remain normalized. [CITED: https://www.unicode.org/reports/tr15/#Concatenation]
**How to avoid:** Normalize at typed ingress/output boundaries and after assembly, before every stable key/hash/persistence/export boundary. [VERIFIED: KNLP-01]
**Warning signs:** NFD/NFC equivalents produce different item keys, cache keys, hashes, or rows. [VERIFIED: `.planning/SPEC.md:40`]

### Pitfall 5: Trusting Bare-Form Top-1 Analysis
**What goes wrong:** Homographs such as bare `배우다` can rank an unintended noun/copula analysis above the verb. [VERIFIED: isolated Kiwi runtime]
**How to avoid:** Intersect multiple analyzer candidates with source-backed lemma/POS/sense and block unresolved multiplicity. [VERIFIED: KNLP-01/KNLP-02; empirical finding]
**Warning signs:** `results[0]` directly becomes a grounded identity without lexical-source compatibility checks. [VERIFIED: implementation risk derived from runtime]

### Pitfall 6: Treating Any Alternative Match as Success
**What goes wrong:** Accepting if any low-ranked analysis contains the target can turn analyzer ambiguity into false-positive target presence. [VERIFIED: top-N API and observed `걸어요` ambiguity]
**How to avoid:** Use the explicit reviewed consensus policy; disagreement blocks rather than score-threshold guessing. [ASSUMED]
**Warning signs:** `any(matches)` produces `matched` while other configured analyses disagree. [ASSUMED]

### Pitfall 7: Losing Compound Predicate Boundaries
**What goes wrong:** `공부하다` becomes the noun `공부`, or `하/XSV` is matched from another eojeol. [VERIFIED: `KOREAN-STRUCTURE.md:334-351`; isolated runtime]
**How to avoid:** Retain ordered `NNG + XSV`/`XSA` signatures and require one `word_position`. [CITED: kiwipiepy token metadata docs]
**Warning signs:** Signature sets instead of ordered tuples, or no boundary field in analysis evidence. [VERIFIED: requirement-derived]

### Pitfall 8: Dropping Valid One-Syllable Highlights
**What goes wrong:** Current generic extraction rejects normalized keys of length one, including valid Korean words such as `물`, `집`, and `말`. [VERIFIED: codebase `highlight_candidate_extraction.py:149-165`; `KOREAN-STRUCTURE.md:314-324`]
**How to avoid:** Analyzer-backed Korean extraction must branch before the generic length filter and deduplicate by lemma/POS/sense. [VERIFIED: KPERS groundwork and KNLP-02]
**Warning signs:** A Korean stopword table is added but tokenization still uses `_TOKEN_RE` and `len <= 1`. [VERIFIED: codebase]

### Pitfall 9: Failing Open When Kiwi Is Missing
**What goes wrong:** The existing generic validator permits a heuristic match when Stanza is unreliable; copying this shape would violate KNLP-02. [VERIFIED: codebase `services/text_validation.py:296-319`; `.planning/SPEC.md:41`]
**How to avoid:** Use a separate Korean matcher whose non-matched statuses always fail, while preserving generic behavior for other languages. [VERIFIED: KMODE-02/KNLP-02]
**Warning signs:** A Korean call reaches `_match_keys()` or `_derive_matchable_forms()`. [VERIFIED: codebase insertion point]

### Pitfall 10: Persisting Vendor Dumps or Private Highlight Text
**What goes wrong:** Raw excerpts, paths, prompts, tracebacks, or token dumps can leak private reading content and bind storage to a vendor class layout. [VERIFIED: `KOREAN-STRUCTURE.md:314-324`; LLM02 guidance]
**How to avoid:** Persist only typed canonical identity, safe analyzer fingerprint, existing content hashes/indexes, and controlled reason codes; errors include exception class but no source text/path. [VERIFIED: codebase privacy patterns; `.agents/skills/llm-security/rules/sensitive-disclosure.md`]
**Warning signs:** `repr(token)`, full highlight text, or local file paths appear in persisted evidence/log messages. [VERIFIED: privacy requirement]

### Pitfall 11: Letting Analyzer Configuration Drift
**What goes wrong:** Defaults, model packages, dialects, typo correction, or user dictionaries can change signatures across reruns. [CITED: kiwipiepy constructor, dialect, typo, and user-dictionary docs]
**How to avoid:** Exact-lock code/model, set options explicitly, avoid mutable global user dictionaries in Phase 30, persist a configuration version, and require reanalysis on mismatch. [VERIFIED: reproducibility requirements]
**Warning signs:** `Kiwi()` appears in several services or persisted evidence records only `provider="kiwi"`. [VERIFIED: architecture recommendation]

### Pitfall 12: Schema Change Without Round-Trip Proof
**What goes wrong:** In-memory identity passes tests but disappears after commit/expire/reload or migration-created schema differs from ORM metadata. [VERIFIED: existing repository architecture and migration parity test]
**How to avoid:** Add ORM column, Alembic upgrade/downgrade, repository payload/restore, `session.expire_all()` assertion, and migration parity in one wave. [VERIFIED: Mandarin integration and lexical repository precedents]
**Warning signs:** Tests assert only the pre-commit Pydantic object. [VERIFIED: codebase test patterns]

## Code Examples

Verified APIs and recommended project patterns follow.

### NFC and Forbidden-Range Boundary

```python
# Sources:
# https://docs.python.org/3.12/library/unicodedata.html
# https://www.unicode.org/reports/tr15/
import unicodedata

_HANGUL_COMPATIBILITY_JAMO = range(0x3130, 0x3190)
_HALFWIDTH_HANGUL = range(0xFFA0, 0xFFDD)


class KoreanTextError(ValueError):
    pass


def canonicalize_korean(value: str) -> str:
    if any(
        ord(character) in _HANGUL_COMPATIBILITY_JAMO
        or ord(character) in _HALFWIDTH_HANGUL
        for character in value
    ):
        raise KoreanTextError("compatibility or halfwidth Hangul is not canonical")
    return unicodedata.normalize("NFC", value)
```

The error message is intentionally content-free so private source text is not echoed. [VERIFIED: privacy requirements and Unicode APIs]

### Pinned, Explicit Kiwi Construction

```python
# Source: https://bab2min.github.io/kiwipiepy/v0.23.2/kr/
from kiwipiepy import Kiwi

kiwi = Kiwi(
    num_workers=1,
    model_type="cong",
    enabled_dialects="standard",
    integrate_allomorph=True,
)

analyses = kiwi.analyze(
    canonicalize_korean("밥을 먹었어요"),
    top_n=2,
    split_complex=False,
    compatible_jamo=False,
    normalize_coda=False,
    z_coda=False,
    typos=None,
    oov_handling="chr",
)
```

This exact call shape executed successfully with the pinned packages in the isolated runtime. [VERIFIED: isolated runtime on 2026-08-03]

### Stable Signature Projection

```python
# Token fields/tag semantics source:
# https://bab2min.github.io/kiwipiepy/v0.23.2/kr/
from collections import defaultdict

_LEXICAL_POS = {
    "NNG", "NNP", "NNB", "NR", "NP",
    "VV", "VA", "VX", "VCP", "VCN",
    "MM", "MAG", "MAJ", "IC", "XR",
}
_COMPOUND_DERIVATION_POS = {"XSV", "XSA"}


def base_pos(raw_tag: str) -> str:
    return raw_tag.partition("-")[0]


def lexical_signatures(tokens: list[object]) -> tuple[tuple[tuple[str, str], ...], ...]:
    by_word: dict[int, list[tuple[str, str]]] = defaultdict(list)
    for token in tokens:
        pos = base_pos(token.tag)
        if pos not in _LEXICAL_POS | _COMPOUND_DERIVATION_POS:
            continue
        by_word[token.word_position].append(
            (canonicalize_korean(token.form), pos)
        )
    return tuple(tuple(items) for _, items in sorted(by_word.items()) if items)
```

The production implementation should return typed immutable Pydantic/domain items, not vendor tokens. [VERIFIED: project typed-contract conventions]

### Conservative Match Outcome

```python
# Project policy sketch; the fixed top_n value remains assumption A1.
def match_target(target_signature, analyses):
    decisions = [
        target_signature in lexical_signatures(tokens)
        for tokens, _score in analyses
    ]
    if decisions and all(decisions):
        return "matched"
    if any(decisions):
        return "ambiguous"
    return "mismatch"
```

Analyzer exceptions, missing analyses, target OOV, and absent persisted identity must be handled before this function and returned as distinct non-passing outcomes. [VERIFIED: KNLP-02; kiwipiepy OOV API]

### Typed Persistence Round Trip

```python
# Source: existing repository serialization pattern.
payload["korean_identity"] = (
    candidate.korean_identity.model_dump(mode="json")
    if candidate.korean_identity is not None
    else None
)

identity = (
    KoreanLexicalIdentity.model_validate(row.korean_identity)
    if row.korean_identity is not None
    else None
)
```

This mirrors the existing `LexicalProvenance` serialization and keeps non-Korean rows nullable. [VERIFIED: codebase `repositories/lexical_repository.py:185-235`]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Legacy Kiwi `knlm`/`sbg` models | `cong` is the provided default; `cong-global` is available for longer context | `cong` introduced in 0.21; default from 0.22 | Pin `cong`; do not plan against removed legacy model defaults. [CITED: kiwipiepy v0.23.2 language-model docs] |
| Rule/length-only OOV handling | Character-model `oov_handling="chr"` default with token OOV evidence | 0.23.0 | Persist/inspect OOV and fail closed instead of accepting a guessed lexical identity. [CITED: kiwipiepy v0.23.2 OOV docs] |
| Typo transformer fixed at construction | `typos` supplied at analysis time | 0.23.0 | Explicitly use `None`; silent correction must not alter canonical identity. [CITED: kiwipiepy v0.23.2 typo docs] |
| Windows model path failure with Unicode characters | Fixed in `kiwipiepy 0.23.2` | 2026-06-11/12 release | Exact 0.23.2 pin is especially appropriate for this Windows workspace. [CITED: https://github.com/bab2min/kiwipiepy/releases/tag/v0.23.2] |
| Generic project NFD/NFKC/heuristic normalization | Korean-specific forbidden-range validation + NFC + signatures | Phase 30 | Keep old behavior isolated; Korean never enters generic suffix or NFKC paths. [VERIFIED: codebase `services/morphology.py`, `highlight_candidate_extraction.py`, `text_validation.py`; KNLP requirements] |

**Deprecated/outdated:**
- Do not configure `knlm` or `sbg`; current v0.23.2 documentation says they are no longer provided from the 0.22 model family. [CITED: https://bab2min.github.io/kiwipiepy/v0.23.2/kr/]
- Do not pass typo configuration only at Kiwi construction as pre-0.23 examples did; current API applies it at analysis time. [CITED: kiwipiepy v0.23.2 history/typo docs]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Runtime/tests | ✓ | Local `3.13.7`; project contract `>=3.12` | Validate CI/project baseline on 3.12 as well. [VERIFIED: local command; `pyproject.toml`] |
| `uv` | Dependency lock and test execution | ✓ | `0.11.14` | None needed. [VERIFIED: local command] |
| `kiwipiepy` in project environment | KNLP-01/02 | ✗ currently; isolated install ✓ | Selected `0.23.2` | Wave 0 adds exact dependency and regenerates `uv.lock`. [VERIFIED: `pyproject.toml`, `uv.lock` grep, isolated runtime] |
| `kiwipiepy-model` in project environment | Kiwi local model | ✗ currently; isolated install ✓ | Selected `0.23.0` | Wave 0 adds direct exact pin. [VERIFIED: `uv.lock` grep, PyPI, isolated runtime] |
| PostgreSQL service | Production persistence | Not required for focused phase tests | Schema uses existing SQLAlchemy/Alembic contract | Use existing disposable SQLite integration pattern; migration parity still runs. [VERIFIED: codebase tests] |
| External Korean provider/network | Not required by morphology implementation | Not required | — | Use local Kiwi and offline provider fakes; no paid calls. [VERIFIED: `.planning/SPEC.md:150-156`; Mandarin integration precedent] |

**Missing dependencies with no fallback:** None after the planned exact Kiwi/model installation; a failed model import must block Korean operations by design. [VERIFIED: KNLP-02]

**Missing dependencies with fallback:** Production PostgreSQL is not needed for the phase's fast integration proof because existing tests use SQLite, but migration parity remains mandatory. [VERIFIED: codebase test architecture]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `8.4.2` installed; project constraint `>=8.3,<9.0` [VERIFIED: local environment; `pyproject.toml`] |
| Config file | `pyproject.toml` (`pythonpath=["src"]`, `testpaths=["tests"]`, asyncio auto) [VERIFIED: `pyproject.toml:51-54`] |
| Quick run command | `uv run pytest tests/domain/test_korean.py tests/services/test_korean_morphology.py tests/services/test_korean_language_support.py -q` [VERIFIED: existing pytest/uv workflow; planned files] |
| Full suite command | `uv run pytest -q` [VERIFIED: existing project test setup] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| KMODE-01 | `ko` accepted for three modes; `ko-KR` rejected internally; locale remains boundary-only | unit + integration | `uv run pytest tests/services/test_korean_language_support.py tests/integration/test_korean_modern_flow.py -q` | ❌ Wave 0 |
| KMODE-02 | Existing modern/Japanese/Mandarin/Latin/phoneme contracts unchanged | integration/regression | `uv run pytest tests/integration/test_frequency_e2e_export_flow.py tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_highlight_generation_audio_flow.py tests/integration/test_mandarin_modern_flow.py tests/integration/test_v21_latin_google_tts_final_audio.py -q` | ✅ existing files [VERIFIED: codebase test inventory] |
| KNLP-01 | NFC, forbidden-range rejection, noun/particle, regular/irregular/adjective/compound analysis, persistence fingerprint | real-library unit + repository integration | `uv run pytest tests/domain/test_korean.py tests/services/test_korean_morphology.py tests/repositories/test_lexical_repository.py tests/test_migration_schema_parity.py -q` | ❌ new Korean files; ✅ repository/parity files |
| KNLP-02 | Inflected target match, POS homograph separation, one-eojeol compounds, OOV/ambiguity/unavailable fail closed, highlight extraction | unit + integration | `uv run pytest tests/services/test_korean_morphology.py tests/services/test_text_validation.py tests/services/test_highlight_candidate_extraction.py tests/integration/test_korean_modern_flow.py -q` | ❌ Korean files; ✅ shared files |

### Required Linguistic Golden Matrix

| Case | Positive/negative assertion |
|------|-----------------------------|
| Noun + particle | `학교/NNG` matches `학교에서 ...`; `에서/JKB` is excluded. [VERIFIED: approved signature table and runtime] |
| Regular predicate | `먹다` matches `밥을 먹었어요` by `먹/VV`. [VERIFIED: approved signature table and runtime] |
| Contextual irregular | `듣다` matches `음악을 들어요` by normalized `듣/VV-I`; raw irregular evidence remains. [VERIFIED: runtime] |
| Adjectival predicate | `예쁘다` matches `꽃이 예뻐요` by `예쁘/VA`. [VERIFIED: approved signature table and runtime] |
| Compound predicate | `공부하다` matches only `공부/NNG + 하/XSV` in one `word_position`. [VERIFIED: approved signature table and runtime] |
| POS homograph | `배우/NNG` matches `배우가`; `배우다/VV` matches `배워요`; neither cross-matches. [VERIFIED: runtime; KNLP-02] |
| Canonical equivalence | NFC and NFD spellings produce one canonical value/key/signature while submitted input is retained. [CITED: Unicode UAX #15]; [VERIFIED: KNLP-01] |
| Invalid compatibility text | Compatibility Jamo and halfwidth Hangul are rejected before matching/storage. [VERIFIED: Korean contract and runtime] |
| Ambiguous context | Bare `걸어요` returns ambiguous under the initial top-two consensus policy; contextual `길을 걸어요` resolves `걷다`. [VERIFIED: runtime; ASSUMED policy A1] |
| Unavailable/OOV | Import/model exception and target `Token.oov=True` never pass; details omit source text/path. [CITED: kiwipiepy OOV docs]; [VERIFIED: KNLP-02/privacy constraints] |
| Negative boundaries | Substring-only, same stem/different POS, and matching morphemes across different eojeol do not pass. [VERIFIED: KNLP-02 and approved signature rules] |

### Sampling Rate

- **Per task commit:** run the directly affected Korean unit file plus `tests/services/test_text_validation.py -q`. [VERIFIED: recommended test decomposition]
- **Per wave merge:** run all Phase 30 focused files, repository round-trip, and migration parity. [VERIFIED: planned architecture]
- **Phase gate:** run `uv lock --check`, version import assertion, all focused tests, the existing-mode regression matrix, then `uv run pytest -q`. [VERIFIED: project quality constraints]

### Wave 0 Gaps

- [ ] `tests/domain/test_korean.py` — canonical constants, NFC/script invariants, identity validation, deterministic key. [VERIFIED: no file currently exists]
- [ ] `tests/services/test_korean_morphology.py` — pinned real-Kiwi goldens and fake unavailable/error paths. [VERIFIED: no file currently exists]
- [ ] `tests/services/test_korean_language_support.py` — registries, modes, provider boundaries, asset/voice/Tatoeba gates. [VERIFIED: no file currently exists]
- [ ] `tests/integration/test_korean_modern_flow.py` — offline three-mode persistence/reload and generic export identity proof. [VERIFIED: no file currently exists]
- [ ] Framework dependency install: `uv add "kiwipiepy==0.23.2" "kiwipiepy-model==0.23.0"`. [VERIFIED: packages absent from project manifest/lock]
- [ ] Alembic migration `20260803_16_korean_lexical_identity.py` plus repository round-trip fixture. [VERIFIED: current migration head is `20260720_15`]

## Security Domain

ASVS 5.0.0 is the current stable ASVS release and is intended as a basis for testing application security controls. [CITED: https://owasp.org/www-project-application-security-verification-standard/]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no new Phase 30 surface | Preserve existing authentication behavior; do not add credentials to analyzer/provider evidence. [VERIFIED: phase scope; ASVS source] |
| V3 Session Management | no new Phase 30 surface | No session contract changes. [VERIFIED: phase scope] |
| V4 Access Control | yes for private highlights | Keep raw excerpts/path in private persistence only; safe lexical candidates and provider requests receive bounded/redacted context. [VERIFIED: `KOREAN-STRUCTURE.md:314-324`; LLM02 skill guidance] |
| V5 Input Validation | yes | Pydantic contracts, UTF-8 file handling, length/resource bounds, forbidden-range checks, NFC, and typed analyzer outcomes. [VERIFIED: codebase input contracts; Unicode docs; code-security skill] |
| V6 Cryptography | limited | Use standard-library SHA-256 for privacy-safe fingerprints; do not invent encryption or expose raw source text as a substitute for a hash. [VERIFIED: codebase `highlight_candidate_extraction.py`; code-security crypto guidance] |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Oversized/malformed highlight causes analyzer resource exhaustion | Denial of Service | Enforce existing/bounded input limits, one shared bounded worker, time/job limits, and no unbounded analyzer logging. [VERIFIED: LLM10/code-security resource guidance; Kiwi worker docs] |
| Compatibility/control characters create identity confusion | Spoofing / Tampering | Reject forbidden Hangul ranges and unexpected control tokens, normalize NFC, and hash canonical structured identity. [CITED: Unicode UAX #15]; [VERIFIED: Korean contract] |
| Raw private highlight leaks through evidence, logs, errors, or prompts | Information Disclosure | Persist hashes/indexes and typed morphology only; redact/bound provider context; log reason codes and exception classes without text/path. [VERIFIED: `KOREAN-STRUCTURE.md:314-324`; `.agents/skills/llm-security/rules/sensitive-disclosure.md`] |
| Highlight text contains indirect prompt instructions | Tampering | Treat highlight context as untrusted data, keep it delimited/redacted/bounded, and never let LLM output author morphology/sense/approval. [VERIFIED: `.planning/SPEC.md:150-155`; llm-security prompt/output guidance] |
| Generated HTML/text reaches cards without validation | Tampering / XSS | Preserve current structured output validation and HTML allowlisting/escaping; treat all LLM output as untrusted. [VERIFIED: `.agents/skills/llm-security/rules/output-handling.md`; project text validation architecture] |
| Compromised or drifting analyzer/model dependency | Tampering / Supply chain | Exact-pin both packages in `uv.lock`, record versions/config, install from PyPI, and re-review on fingerprint change. [VERIFIED: PyPI metadata; `.agents/skills/llm-security/rules/supply-chain.md`] |
| User text interpolated into SQL | Tampering | Continue SQLAlchemy expression/ORM parameterization; store validated JSON values and never compose SQL from forms/signatures. [VERIFIED: codebase repository; `.agents/skills/code-security/rules/sql-injection.md`] |
| User-controlled source path escapes expected import policy | Information Disclosure | Preserve existing file-boundary validation and never include a resolved local path in public evidence/provider payloads. [VERIFIED: `.agents/skills/code-security/rules/path-traversal.md`; highlight privacy requirement] |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A fixed `top_n=2` target-presence consensus is the initial ambiguity policy; all returned analyses must agree for acceptance. [ASSUMED] | Analyzer Configuration; matching code; pitfalls/tests | Too strict causes false negatives; too shallow misses lower-ranked ambiguity. Validate against reviewed fixtures/corpus before treating it as a locked production threshold. |

## Open Questions

1. **Which approved lexical source supplies production Korean `sense_id` values?**
   - What we know: The contract requires source-backed sense identity, and Kiwi's meaning number is not automatically that identifier. [VERIFIED: `.planning/SPEC.md:85-93`; kiwipiepy docs]
   - What's unclear: Phase 30 has no approved Korean production lexical/frequency asset, and the 3000-entry licensing decision belongs to Phase 32. [VERIFIED: `.planning/SPEC.md:20-22`; roadmap]
   - Recommendation: Implement the source-neutral field and resolver now; use small synthetic/reviewed test records, and leave production records pending when no source sense is bound. [VERIFIED: scope-derived recommendation]

2. **Is top-two consensus the right long-term ambiguity policy?**
   - What we know: Kiwi exposes ranked analyses, and tested context-free forms can disagree while contextual forms converge. No project-approved calibrated score threshold exists. [VERIFIED: official `analyze(top_n=...)` docs; isolated runtime; project docs]
   - What's unclear: The best false-positive/false-negative tradeoff across the eventual 3000-entry inventory and authentic highlights. [ASSUMED]
   - Recommendation: Make `top_n` and policy version explicit, lock Phase 30 to reviewed goldens, record ambiguity counts, and require a later corpus calibration before changing the fingerprint. [ASSUMED]

3. **How much Korean sentence-length policy belongs in Phase 30?**
   - What we know: Existing source profiles use generic token limits, while Phase 30 is scoped to contracts/morphology/target matching and Phase 32 owns Korean text quality. [VERIFIED: codebase `domain/source_profiles.py`; `KOREAN-STRUCTURE.md:475-481`]
   - What's unclear: Whether current whitespace/regex counts reject any minimal Phase 30 integration fixture. [VERIFIED: codebase `services/text_validation.py:321-383`]
   - Recommendation: Change only what is required to keep focused Korean contract tests meaningful; defer a broader Korean naturalness/length policy to Phase 32. [VERIFIED: phase-scope recommendation]

## Sources

### Primary (HIGH confidence)

- Context7 library `/bab2min/kiwipiepy` — constructor, `analyze(top_n)`, token fields, `word_position`, tag regularity, split-complex and normalization options. [VERIFIED: Context7 CLI lookup on 2026-08-03]
- https://bab2min.github.io/kiwipiepy/v0.23.2/kr/ — pinned API, model families, POS tags, dialects, OOV, typo, release history. [CITED: official versioned docs]
- https://pypi.org/pypi/kiwipiepy/json — current version, dependency range, wheel filenames, upload timestamp. [VERIFIED: PyPI JSON query on 2026-08-03]
- https://pypi.org/pypi/kiwipiepy-model/json — current model version and upload timestamp. [VERIFIED: PyPI JSON query on 2026-08-03]
- https://github.com/bab2min/kiwipiepy/releases/tag/v0.23.2 — Windows Unicode model-path fix and release provenance. [CITED: official release]
- https://www.unicode.org/reports/tr15/ — NFC/NFKC semantics, Hangul canonical equivalence, compatibility behavior, concatenation caveat. [CITED: Unicode Standard Annex #15 revision 57]
- https://www.unicode.org/Public/17.0.0/ucd/Blocks.txt — Hangul block ranges. [CITED: Unicode Character Database 17.0]
- https://docs.python.org/3.12/library/unicodedata.html — Python normalization API and UCD version. [CITED: Python 3.12 docs]
- https://owasp.org/www-project-application-security-verification-standard/ — ASVS 5.0.0 stable baseline. [CITED: OWASP]
- `.planning/SPEC.md`, `.planning/ROADMAP.md`, `KOREAN-STRUCTURE.md`, `AGENTS.md` — locked requirements, scope, architecture, licensing, and project constraints. [VERIFIED: codebase]
- `.planning/phases/30-korean-contracts-and-morphology/30-PATTERNS.md` — current file classification, analogs, no-touch surfaces, and regression map. [VERIFIED: codebase]
- Live code and tests under `src/multilang`, `alembic/versions`, and `tests` — current architecture and insertion points. [VERIFIED: codebase inspection]
- Isolated pinned Kiwi runtime probes on Korean nouns, particles, regular/irregular/adjectival/compound predicates, homographs, top-N ambiguity, OOV/config APIs, and Unicode forms. [VERIFIED: local execution on 2026-08-03]

### Secondary (MEDIUM confidence)

- `.agents/skills/code-security/` and `.agents/skills/llm-security/` — project-provided OWASP/CWE-aligned implementation guardrails for input, persistence, private context, output handling, and dependency pinning. [VERIFIED: local project skills]

### Tertiary (LOW confidence)

- None. Unverified ecosystem claims were not used. [VERIFIED: research log]

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — exact versions, dependency metadata, official versioned docs, wheels, and local runtime were verified. [VERIFIED: PyPI/official docs/runtime]
- Architecture: **HIGH** — requirements are explicit and every proposed component has an existing in-repo structural analog. [VERIFIED: SPEC/KOREAN-STRUCTURE/codebase/PATTERNS]
- Signature mechanics: **HIGH** — approved signature rules and pinned real-analyzer outputs agree on required fixtures. [VERIFIED: KOREAN-STRUCTURE and isolated runtime]
- Ambiguity policy: **MEDIUM** — fail-closed behavior is locked, but fixed top-two consensus needs broader fixture/corpus calibration. [ASSUMED]
- Pitfalls: **HIGH** — most are directly visible in current generic code or reproduced with the pinned analyzer. [VERIFIED: codebase/runtime]
- Security: **HIGH** — privacy gates are explicit and controls were checked against current OWASP/project skill guidance. [VERIFIED: SPEC/KOREAN-STRUCTURE/OWASP/skills]

**Research date:** 2026-08-03
**Valid until:** 2026-09-02; recheck PyPI releases and the exact lock before implementation because analyzer packages are active. [VERIFIED: current release cadence in official history]
