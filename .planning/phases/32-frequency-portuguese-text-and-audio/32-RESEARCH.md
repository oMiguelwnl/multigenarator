# Phase 32: Frequency, Portuguese Text, and Audio - Research

**Researched:** 2026-08-21
**Domain:** Korean frequency authority, morphology-aware text generation, pt-BR translation, Azure Speech evidence, and deterministic Anki subdeck export
**Confidence:** HIGH for the offline implementation path; MEDIUM for learner-ready completion because exact source bytes/terms, reviewers, provider routes, and live-Azure facts are not yet supplied

<user_constraints>
## User Constraints (from 32-APPROACH.md)

The following decisions are user-confirmed. Wording is copied from the confirmed-decision, discretion, and deferred sections except for the appended provenance tags. [VERIFIED: `.planning/phases/32-frequency-portuguese-text-and-audio/32-APPROACH.md`]

### Locked Decisions

- Use one reusable shared final-mode contract, activated first for Korean through one atomic manifest-bound 3000-entry bundle; do not recurate all existing language assets in Phase 32. [VERIFIED: `32-APPROACH.md`]
- Use the NIKL `한국어 학습용 어휘 목록` as the selected rank and initial lexical-authority path, while keeping exact attachment bytes, KOGL terms evidence, attribution, transformation review, modernity curation, and asset commit behind explicit checkpoints. [VERIFIED: user decision on 2026-08-21; `32-APPROACH.md`; `32-FREQUENCY-SOURCE-DECISION.md`]
- Create real Korean `Level 1`, `Level 2`, and `Level 3` child decks in Phase 32. Phase 34 generalizes the topology and owns final all-family export, import, rendering, playback, and evidence closure. [VERIFIED: `32-APPROACH.md`]
- Let one dominant source-backed sense consume each frequency rank unless the approved frequency source itself supplies independently sense-specific ranks; unresolved homographs block or require review. [VERIFIED: `32-APPROACH.md`]
- Define v3 adaptive i+1 from cumulative approved deck order, inherit only approved Phase 31 concept evidence, and make naturalness a hard gate before novelty scoring. [VERIFIED: `32-APPROACH.md`]
- Use everyday Standard-Seoul `해요체` by default; another register requires explicit context evidence and review. [VERIFIED: `32-APPROACH.md`]
- Produce pt-BR editorial copy while retaining canonical project language identity `pt`; provider-specific regional language codes exist only at provider boundaries, while editorial metadata uses a policy identifier rather than a second language identity. [VERIFIED: `32-APPROACH.md`]
- Generate exactly two initial sentence candidates and permit at most one cache-distinct repair; pin one approved provider/model route per task and prohibit cross-provider fallback for final Korean output. [VERIFIED: `32-APPROACH.md`]
- Require explicit approval for exact provider models, credentials, token/cost/latency ceilings, and every live or paid run. [VERIFIED: `32-APPROACH.md`]
- Use one live-discovered and approved Azure `ko-KR` voice/profile for ordinary frequency word and sentence audio, with neutral SSML unless heard approval authorizes a different versioned profile and with no alternate provider or voice fallback. [VERIFIED: `32-APPROACH.md`]
- Require human playback of at least 10% stratified samples of each ordinary frequency-audio type — at least 300 words and at least 300 sentences — plus 100% of flagged, homograph, and other risk cases; require exact automated integrity checks for 100% of assets. [VERIFIED: `32-APPROACH.md`]
- Implement all safe offline contracts, tests, and refusal behavior before pausing at license/source, exact-asset, Phase 31 dependency, provider budget/model, live catalog, paid generation, human review, asset commit, and publication checkpoints. [VERIFIED: `32-APPROACH.md`]
- Preserve verified Phase 30 `ko`, NFC, source-backed identity, Kiwi top-two consensus, matcher, persistence, and privacy contracts plus Phase 31 hash-bound gates; final mode never reaches live `wordfreq` or generic suffix rescue. [VERIFIED: `32-APPROACH.md`]
- Persist only sanitized hashes and bounded provider metrics in telemetry, never prompts, private excerpts or paths, provider payloads, secrets, or raw analyzer dumps. [VERIFIED: `32-APPROACH.md`]
- Keep Phase 33 field-level review and job hardening, Phase 34 worker/generalized closure beyond the explicitly assigned Korean child decks, and all v4/GUID/history/adaptive-queue work outside Phase 32. [VERIFIED: `32-APPROACH.md`]

### the agent's Discretion

- Exact internal class, function, module, enum, reason-code, and helper names, provided all locked typed states and boundaries remain explicit. [VERIFIED: `32-APPROACH.md`]
- Internal implementation decomposition and plan/test file split, provided the source, identity, provider, audio, and child-deck authorities remain single and deterministic rather than duplicated. [VERIFIED: `32-APPROACH.md`]
- Exact migration revision identifier derived from the unique live Alembic head, provided the migration is additive, legacy-compatible, and fully round-tripped. [VERIFIED: `32-APPROACH.md`]
- Exact canonical serialization helper implementation, provided its externally stored hashes follow the locked canonical UTF-8 JSON/raw-byte SHA-256 rules. [VERIFIED: `32-APPROACH.md`]
- Exact synthetic lexical rows, provider candidates, catalog payloads, media bytes, and mutation fixtures used only in tests, provided they are unmistakably non-production, offline, and cannot satisfy approval. [VERIFIED: `32-APPROACH.md`]
- Exact deterministic tie-break helper and test parametrization after all locked hard gates and score priorities are honored. [VERIFIED: `32-APPROACH.md`]
- No agent discretion extends to product topology, rank/sense policy, Korean register, pt-BR policy, provider/model/budget selection, source/license terms, production lexical content, review coverage, reviewer authority, voice/profile choice, SSML approval, fallback, live/paid calls, asset commit, publication, Phase 31 evidence, or any excluded Phase 33/34/v4 work. [VERIFIED: `32-APPROACH.md`]

### Deferred Ideas (OUT OF SCOPE)

- **Phase 33:** Reviewed Particles & Endings curriculum, strict grammar i+1, personal-list/highlight bridge/defer behavior, resumable item-state hardening assigned there, and field-level approve/reject/edit/regenerate commands. [VERIFIED: `32-APPROACH.md`]
- **Phase 34:** Generalize real frequency child decks across applicable existing languages; bounded PostgreSQL workers/claims; all Korean-family APKG/CSV/TSV closure; final milestone evidence; and observed Anki Desktop/mobile import, rendering, font, responsive, and playback acceptance. [VERIFIED: `32-APPROACH.md`]
- **Later explicit rollout:** Recurate existing frequency inventories and qualify each selected language-specific morphology adapter before activating the shared strict final mode for those languages. [VERIFIED: `32-APPROACH.md`]
- **Out of v3.0:** Semantic/form-card identities, GUID migration, APKG history import/adaptation, learner-history synchronization, adaptive queues, scheduling integration, Hanja curricula, regional Korean dialect decks, and interactive tutoring. [VERIFIED: `32-APPROACH.md`]

The missing Phase 31 approvals, exact NIKL attachment/terms evidence, exact 3000-entry asset, qualified Korean/pt-BR review, provider budgets/models, live Azure evidence, production media, asset-commit authorization, and publication authorization are **not** deferred product ideas. They are named Phase 32 completion checkpoints. If unavailable, the correct result is a verified blocked production path, not fabricated learner-ready output. [VERIFIED: `32-APPROACH.md`; `32-FREQUENCY-SOURCE-DECISION.md`]
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| KFREQ-01 | User receives a Korean frequency inventory whose lemma, sense, rank, POS, source, license, analyzer version, and curation decision are auditable. | Use the strict root-manifest, child-hash, typed identity, rejection-ledger, and source/license checkpoint architecture below. [VERIFIED: `.planning/SPEC.md`; `32-APPROACH.md`] |
| KFREQ-02 | User receives three real Korean frequency subdecks with exactly 1000 unique lemma/sense cards per level. | Persist manifest-assigned level independently of GUID inputs and package one parent plus three explicit `::Level N` decks with stable IDs. [VERIFIED: `.planning/SPEC.md`; `32-APPROACH.md`; genanki experiment] |
| KFREQ-03 | User receives frequency examples ordered with adaptive i+1 scoring. | Build cumulative known state from the active Phase 31 snapshot plus earlier final ranks; hard-gate naturalness before deterministic novelty scoring. [VERIFIED: `.planning/SPEC.md`; `32-APPROACH.md`] |
| KTXT-01 | User receives natural standard-Seoul Korean examples, context-matched Portuguese glosses, and Portuguese sentence translations. | Apply Korean-owned NFC, morphology, sense, register, leakage, naturalness, and pt-BR quality gates with exact review evidence. [VERIFIED: `.planning/SPEC.md`; `32-APPROACH.md`] |
| KAUD-01 | User receives approved Azure `ko-KR` word and sentence audio plus specialist-reviewed audio for jamo and phonological rules. | Reuse the active Phase 31 foundation-media authority and add a live-catalog-bound frequency voice/profile, exact byte hashes, separate word/sentence records, and heard review. [VERIFIED: `.planning/SPEC.md`; `32-APPROACH.md`] |
| GLEX-01 | User receives frequency candidates from frozen, versioned, provenance-aware assets rather than live `wordfreq` fallback during final generation. | Add a Korean strict-final branch with no import/call edge to `iter_wordlist`, seed candidates, or provider-authored identity. [VERIFIED: `.planning/SPEC.md`; `src/multilang/services/frequency_decks.py`; `src/multilang/runtime.py`] |
| GLEX-02 | User receives lexical candidates with enough metadata to validate the intended word before text generation. | Persist the complete Phase 30 identity plus source/version, confidence, ambiguity, rank, level, bundle hash, and curation evidence before any text call. [VERIFIED: `.planning/SPEC.md`; `src/multilang/domain/korean.py`; `32-APPROACH.md`] |
| GMOR-01 | User receives target matching based on a language-specific morphology adapter. | Keep the pinned Kiwi top-two consensus and map all non-match states to fail-closed `inconclusive` or `mismatch`; never enter generic suffix rescue. [VERIFIED: `.planning/SPEC.md`; `src/multilang/services/korean_morphology.py`] |
| GTXT-01 | User receives the best validated example available for each item instead of the first provider response. | Generate exactly two strict candidates, validate complete bundles, select deterministically, and issue no more than one task-distinct repair. [VERIFIED: `.planning/SPEC.md`; `32-APPROACH.md`] |
| GPRO-01 | User receives observable and policy-controlled provider execution. | Snapshot routes and budgets per task; thread job/item context through definition, generation, repair, translation, judge, catalog, and audio calls; log hashes and bounded metrics only. [VERIFIED: `.planning/SPEC.md`; `src/multilang/repositories/provider_call_log_repository.py`; `32-APPROACH.md`] |
| GAUD-01 | User receives audio governed by an explicit provider and fallback policy. | Separate synthesis from approval, strengthen reuse identity, block every fallback for Korean final mode, and mark item success only after both exact approved assets exist. [VERIFIED: `.planning/SPEC.md`; `src/multilang/services/generate_audio_items.py`; `32-APPROACH.md`] |
</phase_requirements>

## Summary

Phase 32 is primarily an **authority and promotion-gate phase**, not a package-selection phase. The repository already contains the needed Python, Pydantic, Kiwi, SQLAlchemy/Alembic, LiteLLM, DeepL, Azure Speech, genanki, caching, retry, telemetry, and test seams. The missing work is to connect them through one Korean-only strict final path whose source, lexical identity, candidate choice, translation, audio, review, and deck membership are all hash-bound and fail closed. [VERIFIED: `pyproject.toml`; `uv.lock`; `32-PATTERNS.md`; inspected `src/multilang/**`]

The most consequential direct gaps are that runtime composition still enables frequency seed grounding, `frequency_decks.py` still has a live `iter_wordlist()` path, repair can repeat the same cached sentence request, generation returns one candidate, generic repair can promote Tatoeba outside Korean, definition calls bypass the common provider boundary, Korean has no approved voice entry, audio records lack exact artifact/review evidence, failed assets still permit item-stage success, and export currently writes one deck and can infer levels arithmetically. [VERIFIED: `src/multilang/runtime.py:599-604`; `frequency_decks.py:174-185,362-440`; `text_generation.py:391-438`; `generate_text_items.py:187-193,373-454`; `audio_voice_registry.py`; `domain/audio.py`; `generate_audio_items.py:93-108`; `export_anki_package.py:114-145`; `domain/exporting.py:450-466`]

All safe schemas, loaders, migrations, deterministic fakes, refusal paths, selector logic, exact-audio gates, and three-child-deck structural tests can be implemented offline. Learner-ready production must remain blocked until the exact Phase 31 snapshot, source/license, inventory, provider/model/budget, reviewer, live Azure catalog/profile, generated bytes, heard review, asset-commit, and publication checkpoints are supplied. [VERIFIED: `32-APPROACH.md`]

**Primary recommendation:** Build one immutable Korean frequency bundle and one strict promotion pipeline—`source authority → typed identity → selected morphology → two-candidate text selection → pt-BR validation → exact reviewed Azure assets → manifest-routed child decks`—while leaving every unresolved external fact explicit and non-exportable. [VERIFIED: `32-APPROACH.md`; `32-PATTERNS.md`]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Source/license and frozen frequency authority | API / Backend | Database / Storage | Local operator commands validate one immutable bundle and active pointer; storage retains exact bytes/hashes, while no browser owns authority. [VERIFIED: `32-APPROACH.md`; Phase 31 snapshot precedent] |
| Rank, lemma/POS/sense identity, and curation | API / Backend | Database / Storage | Typed domain validation and repository round trips own identity before provider text exists. [VERIFIED: `domain/korean.py`; `db/models.py`] |
| Korean target matching | API / Backend | — | The pinned shared Kiwi adapter performs morphology and returns controlled match states. [VERIFIED: `services/korean_morphology.py`] |
| Adaptive i+1 evidence | API / Backend | Database / Storage | A deterministic scorer consumes frozen curriculum/deck order and persists the exact known/observed/incidental evidence. [VERIFIED: `32-APPROACH.md`] |
| Candidate generation, repair, and selection | API / Backend | External LLM provider | Backend policy constrains calls and validates untrusted outputs; the provider supplies candidates but owns no identity or approval. [VERIFIED: `32-APPROACH.md`; OWASP LLM01/05] |
| Korean → pt-BR translation | API / Backend | External DeepL service | The adapter maps canonical project codes at the boundary and backend quality gates retain authority. [VERIFIED: `provider_text_adapters.py`; DeepL docs] |
| Provider budgets/cache/retry/telemetry | API / Backend | Database / Storage | One composition root snapshots routes; repositories retain cache records and sanitized per-attempt metrics. [VERIFIED: `runtime.py`; `provider_response_cache.py`; `provider_call_log_repository.py`] |
| Voice discovery and speech synthesis | API / Backend | External Azure Speech | Backend validates a live regional catalog receipt and exact request; Azure returns candidate audio bytes, not approval. [VERIFIED: Azure Speech docs; `azure_speech_adapter.py`; `32-APPROACH.md`] |
| Audio and review evidence | Database / Storage | API / Backend | Storage retains exact byte/profile/review hashes; backend gates reuse, item completion, and export. [VERIFIED: `32-APPROACH.md`; Phase 31 media precedent] |
| APKG child-deck packaging | API / Backend | Static artifact | genanki creates an offline package after all rows/media pass; APKG is a generated static deliverable. [VERIFIED: genanki docs; `export_anki_package.py`] |
| Human source/content/audio decisions | Operator / CLI | Database / Storage | Fixed commands expose controlled summaries and persist exact receipts; no application UI is in scope. [VERIFIED: `32-APPROACH.md`] |

## Project Constraints (from AGENTS.md)

- Preserve canonical Korean code `ko`; use `ko-KR` only as provider locale metadata. [VERIFIED: `AGENTS.md`]
- Preserve three levels with exactly 1000 cards per level. [VERIFIED: `AGENTS.md`]
- Korean content must use NFC, morphology-aware lemma/POS/sense identity, and fail-closed target matching instead of whitespace or suffix heuristics. [VERIFIED: `AGENTS.md`]
- Do not commit a redistributed 3000-entry Korean frequency asset before an approved source, attribution, and redistribution decision. [VERIFIED: `AGENTS.md`]
- Treat Tatoeba quality as a known risk; it is not the default final sentence source. [VERIFIED: `AGENTS.md`]
- Use Azure TTS only if the required approved voices are available. [VERIFIED: `AGENTS.md`; `32-APPROACH.md`]
- Preserve the normal-card field set/format and blank `Image`; consistent Anki schema is product-critical. [VERIFIED: `AGENTS.md`; `domain/exporting.py`]
- Follow architecture, tests, and fail-safe behavior; do not trade reliability for a shorter implementation. [VERIFIED: `AGENTS.md`]
- Read `.planning/SPEC.md`, `.planning/ROADMAP.md`, `.planning/config.json`, and relevant phase artifacts before roadmap work; stay in scope and verify substantive wiring before claiming completion. [VERIFIED: `AGENTS.md`]
- Research unfamiliar APIs from actual documentation and code; keep portable workflow entry under `.agents/skills/`, helpers under `.planning/bin/`, and tool-native adapters in their native directories. [VERIFIED: `AGENTS.md`]
- The active GSD phase workflow authorizes this research artifact; implementation edits must occur through the approved execution workflow rather than ad hoc changes. [VERIFIED: `AGENTS.md`]

## Standard Stack

### Version Policy

Keep the existing lock for Phase 32. Registry checks found newer releases for several libraries, but the installed versions already expose the required APIs and are exercised by repository code/tests; coupling dependency upgrades to this phase would expand regression scope without closing a Phase 32 requirement. [VERIFIED: installed package metadata; PyPI registry; inspected code/tests]

### Core

| Library | Project Version | Current Registry Version / Publish Date | Purpose | Why Standard Here |
|---------|-----------------|-----------------------------------------|---------|-------------------|
| Python | 3.12.3 | Project baseline is `>=3.12` | Runtime, Unicode, hashing, filesystem safety | Existing application and tests are Python; use `unicodedata`, `hashlib`, `pathlib`, `tempfile`, and `os.replace` instead of new dependencies. [VERIFIED: environment; `pyproject.toml`; Python docs] |
| Pydantic | 2.12.5 | 2.13.4 / 2026-05-06 | Strict manifests, typed evidence, provider output parsing | Existing Korean contracts use frozen Pydantic models; current docs support strict mode, `extra="forbid"`, frozen models, hidden inputs, and `model_validate`. [VERIFIED: installed metadata; PyPI registry; Context7 `/pydantic/pydantic`] |
| kiwipiepy | 0.23.2 | 0.23.2 / 2026-06-11 | Korean morphology and target matching | Project pins this exact analyzer and top-two options in a lazy shared adapter. [VERIFIED: `pyproject.toml`; `korean_morphology.py`; Context7 `/bab2min/kiwipiepy`] |
| kiwipiepy-model | 0.23.0 | 0.23.0 / 2026-03-17 | Exact Kiwi model data | The analyzer fingerprint requires this exact model-package version. [VERIFIED: `pyproject.toml`; `korean_morphology.py`; PyPI registry] |
| SQLAlchemy | 2.0.49 | 2.0.52 / 2026-08-11 | ORM and repository round trips | Existing persistence uses typed `Mapped` models and explicit repositories. [VERIFIED: installed metadata; PyPI registry; Context7 `/websites/sqlalchemy_en_20`; `db/models.py`] |
| Alembic | 1.18.4 | 1.19.1 / 2026-08-08 | One additive reversible migration | Repository migration tests enforce sole-head, upgrade/downgrade/re-upgrade, and ORM parity. [VERIFIED: installed metadata; PyPI registry; Context7 `/websites/alembic_sqlalchemy`; `tests/test_migration_schema_parity.py`] |

### Supporting

| Library | Project Version | Current Registry Version / Publish Date | Purpose | When to Use |
|---------|-----------------|-----------------------------------------|---------|-------------|
| LiteLLM | 1.83.10 | 1.97.0 / 2026-08-16 | Explicit LLM route, structured output, usage/cost metadata | Use only after route/model/budget approval; locally validate every response and prohibit Korean final-mode cross-provider fallback. [VERIFIED: installed metadata; PyPI registry; Context7 `/berriai/litellm`; `32-APPROACH.md`] |
| deepl | 1.30.0 | 1.32.0 / 2026-08-13 | Korean sentence → pt-BR translation | Use `source_lang="KO"`, `target_lang="PT-BR"` at the adapter boundary while persisting canonical project language `pt`. [VERIFIED: installed metadata; PyPI registry; DeepL supported-languages docs; Context7 `/deepl/deepl-python`; `32-APPROACH.md`] |
| azure-cognitiveservices-speech | 1.49.1 | 1.51.2 / 2026-08-20 | Exact `ko-KR` word/sentence TTS | Use only after live catalog/profile approval; capture result, cancellation, duration, request, and final artifact evidence. [VERIFIED: installed metadata; PyPI registry; Azure Speech docs; `32-APPROACH.md`] |
| genanki | 0.13.1 | 0.13.1 / 2023-11-12 | Multi-deck `.apkg` packaging | Pass an explicit parent plus three child `Deck` objects to one `Package`; preserve the current model, fields, and note GUID. [VERIFIED: installed metadata; PyPI registry; Context7 `/kerrickstaley/genanki`; local package experiment] |
| wordfreq | 3.1.1 | 3.1.1 / 2023-11-21 | Optional pre-approval bootstrap tooling only | Never import or call it from Korean final loading; use only if the source decision explicitly permits that bootstrap. [VERIFIED: installed metadata; PyPI registry; `32-APPROACH.md`] |
| pytest | 8.4.2 | 9.1.1 / 2026-06-19 | Offline unit/integration/golden tests | Keep 8.x because `pyproject.toml` constrains `<9.0`; all provider/catalog/audio tests use deterministic fakes. [VERIFIED: installed metadata; PyPI registry; `pyproject.toml`] |

### Alternatives Considered (Rejected by Locked Decisions)

| Use | Rejected Alternative | Why Rejected |
|-----|----------------------|--------------|
| Atomic Korean-first root bundle | Extend weak CSVs while retaining runtime seed fallback | It cannot bind licensing, source identity, rejections, analyzer evidence, and exact membership into one authority. [VERIFIED: `32-APPROACH.md`] |
| Korean-first activation | Immediate strict cutover for every language | Existing assets/adapters have not been qualified against the new evidence contract. [VERIFIED: `32-APPROACH.md`] |
| Exactly two candidates + one repair | Accept first response or run an unbounded ensemble | First-response quality is insufficient; unbounded calls violate cost/resource policy. [VERIFIED: `32-APPROACH.md`] |
| One pinned provider route per task | Invisible cross-provider fallback | Output provenance, approval, cost, and quality would become nondeterministic. [VERIFIED: `32-APPROACH.md`] |
| One live-approved Azure profile | Documentation-picked or fallback voice | Static availability is not regional catalog evidence or heard approval. [VERIFIED: `32-APPROACH.md`; Azure Speech docs] |
| Real child decks now | Tags-only level grouping | `KFREQ-02` explicitly requires real subdecks. [VERIFIED: `.planning/SPEC.md`; `32-APPROACH.md`] |

**Installation:** no new package is required. Reproduce the checked environment with:

```bash
uv sync --frozen --extra dev
```

[VERIFIED: `pyproject.toml`; `uv.lock`; environment uses uv 0.11.7]

## Architecture Patterns

### System Architecture Diagram

```text
Operator checkpoint
  ├─ source/license denied or incomplete ───────────────> BLOCKED (no asset path/write)
  └─ approved exact source/use/redistribution decision
       ↓
Rank snapshot + lexical authority + attribution + rejection ledger + report
       ↓ bounded reads / path allowlist / byte SHA-256
Strict root manifest validator ── drift/malformed/short/ambiguous ──> BLOCKED
       ↓ one immutable 3000-entry identity set + bundle SHA-256
Final-frequency loader (Korean branch; no wordfreq/seed/provider identity)
       ↓
Lexical persistence (lemma + POS + sense + rank + level + source + Kiwi fingerprint)
       ↓
Shared pinned Kiwi matcher
  ├─ mismatch / ambiguous / OOV / unavailable / drift ──> REVIEW/BLOCK
  └─ conclusive match
       ↓
Approved Phase 31 concepts + prior final ranks → cumulative known-state builder
       ↓
Pinned LLM sentence route → exactly 2 structured candidates
       ↓
NFC + language + morphology + sense + register + naturalness hard gates
  ├─ none pass ──> one task-distinct constrained repair ──> REVIEW/BLOCK if failed
  └─ viable candidates
       ↓
DeepL boundary (KO → PT-BR) + pt-BR/context/contradiction gates
       ↓ deterministic adaptive score and immutable tie-break
Selected text bundle + machine evidence + exact human-review receipt
       ↓
Authorized Azure region → live voice catalog receipt → exact approved ko-KR profile
       ↓
Separate word + sentence SSML requests → final bytes → SHA-256/integrity
       ↓ stratified + risk-case heard review
Approved audio evidence (both assets required; no fallback)
       ↓
Final export gate
  ├─ missing/stale/unapproved/mismatched evidence ──────> BLOCKED
  └─ all exact
       ↓
One genanki package: parent + ::Level 1 + ::Level 2 + ::Level 3
       ↓
Staged APKG structural inspection → atomic destination replacement
```

This flow preserves external-service boundaries and makes every authority-changing decision occur before downstream generation or promotion. [VERIFIED: `32-APPROACH.md`; inspected repository architecture]

### Recommended Project Structure

```text
src/multilang/
├── domain/
│   ├── korean.py                    # canonical frequency/adaptive/review contracts
│   ├── lexicon.py                   # source/version/confidence provenance summary
│   ├── text_quality.py              # machine state plus distinct review evidence
│   ├── audio.py                     # catalog/request/artifact/review evidence
│   └── exporting.py                 # explicit level and final promotion gates
├── services/
│   ├── korean_frequency.py          # new root-manifest loader/validator
│   ├── frequency_decks.py           # Korean strict-final routing; legacy isolation
│   ├── korean_morphology.py         # existing pinned shared Kiwi authority
│   ├── korean_text_quality.py       # new hard gates + adaptive evidence/scoring
│   ├── text_generation.py           # bounded task-aware provider boundary
│   ├── generate_text_items.py       # shared candidate selector + one repair
│   ├── provider_text_adapters.py    # strict schema and KO→PT-BR boundary
│   ├── azure_speech_adapter.py      # complete catalog rows/receipt + synthesis
│   ├── audio_synthesis.py           # request, bytes, hashes, approval state
│   ├── generate_audio_items.py      # all-required-assets completion semantics
│   └── export_anki_package.py       # parent + three stable child decks
├── repositories/                    # explicit write/reload mappings
└── runtime.py                       # one Kiwi instance and explicit route policy
alembic/versions/
└── <new-revision>_frequency_text_audio_evidence.py
tests/
├── services/test_korean_frequency.py
├── services/test_korean_text_quality.py
├── cli/test_korean_frequency_commands.py
└── integration/test_korean_frequency_text_audio_flow.py
```

The exact split and names remain agent discretion; the architectural requirement is one authority per source, identity, selection, audio profile, and child-deck membership. [VERIFIED: `32-APPROACH.md`; `32-PATTERNS.md`]

### Component Responsibilities

| Component | Owns | Must Not Own |
|-----------|------|--------------|
| `domain/korean.py` | Frozen frequency entry, source decision summary, adaptive evidence, controlled Korean states | File I/O, provider calls, or reviewer decisions. [VERIFIED: existing domain pattern; `32-APPROACH.md`] |
| `korean_frequency.py` | Bounded path-safe reads, manifest/child hashes, 3000/1000 invariants, rejection reconciliation, active bundle resolution | `wordfreq`, provider calls, first-sense selection, or mutable DB authority. [VERIFIED: `32-PATTERNS.md`; Phase 31 snapshot precedent] |
| `frequency_decks.py` | Route Korean final requests to frozen entries and keep legacy languages unchanged | Silent seed fallback for Korean final mode. [VERIFIED: `frequency_decks.py`; `32-APPROACH.md`] |
| lexical grounding/repository | Persist already-resolved source identity and learner definitions after identity freeze | Reanalyze or rewrite source lemma/POS/sense from provider output. [VERIFIED: `32-APPROACH.md`; `domain/korean.py`] |
| `korean_text_quality.py` | Korean hard gates, conservative concept extraction, adaptive scoring, deterministic tie-break evidence | Provider transport, human approval, or generic-language heuristics. [VERIFIED: `32-APPROACH.md`; `32-PATTERNS.md`] |
| text generation/selector | Task routes, exactly two candidates, complete-bundle validation, one distinct repair | First-response acceptance, Tatoeba final promotion, hidden fallback, or unbounded retries. [VERIFIED: `32-APPROACH.md`] |
| Azure/audio services | Catalog receipt, trusted SSML, synthesis result, artifact hash, review state, exact reuse identity | Voice approval by documentation, provider fallback, or item success after partial failure. [VERIFIED: `32-APPROACH.md`; Azure docs] |
| exporter | Route persisted manifest level to stable decks after final gate; preserve fields/tags/GUID | Infer Korean level from rank/item-key, modify GUID inputs, or claim observed Anki behavior. [VERIFIED: `32-APPROACH.md`; current exporter gap] |

### Pattern 1: Immutable Root Bundle and Atomic Activation

**What:** The root manifest is the sole release authority and binds the exact source decision, attribution, ranked source snapshot, lexical authority snapshot, curated inventory, rejection ledger, report, analyzer fingerprint, child byte sizes/hashes, row counts, ordered identity set, level hashes, and root hash. [VERIFIED: `32-APPROACH.md`]

**When to use:** Every production-size Korean frequency load; synthetic tests inject an unmistakably non-production bundle and cannot activate production. [VERIFIED: `32-APPROACH.md`]

**Required validation order:** source/use/redistribution disposition → safe bounded members → byte hashes → strict typed payloads → analyzer fingerprint → 3000 contiguous final ranks → 1000 per manifest-assigned level → full identity uniqueness → rejection/report reconciliation → canonical root hash. No candidate persistence or output occurs before the chain passes. [VERIFIED: `32-APPROACH.md`; `32-PATTERNS.md`]

Reuse the Phase 31 snapshot pattern: fixed relative paths, no symlink/reparse components, bounded exact reads, `lstat`/`fstat` continuity, immutable directories, one pointer read, same-directory temporary write, file and directory `fsync`, and `os.replace`. Do not couple frequency code directly to foundation-specific private enums; extract a narrowly tested shared primitive only if needed. [VERIFIED: `services/korean_foundation_snapshot.py:303-505,730-968,1944-2003`; Python `os.replace` docs]

### Pattern 2: Source Identity Before Generated Text

**What:** One accepted rank stores a complete `KoreanLexicalIdentity`, source rank, final rank, explicit level, source/version, license disposition, grounding confidence, curation decision, rejection context code, and exact analyzer fingerprint. The identity key is lemma + normalized lexical POS + source sense, not visible token alone. [VERIFIED: `32-APPROACH.md`; `domain/korean.py`]

**When to use:** Before definition, sentence, translation, judge, TTS, or export work. Unresolved homographs and unsupported function-morpheme targets block or enter review. [VERIFIED: `32-APPROACH.md`]

One dominant source-backed sense consumes the rank unless the approved frequency authority itself provides independent sense ranks. Provider text may explain the frozen sense but may not create, split, merge, or rewrite it. [VERIFIED: `32-APPROACH.md`]

### Pattern 3: Selected-Adapter Tri-State Gate

**What:** Project the detailed Kiwi statuses into a stable final decision: `match`, `mismatch`, or `inconclusive`. Only top-two consensus `MATCHED` becomes `match`; ambiguity, OOV, unavailable analysis, invalid text, missing identity, malformed analysis, and fingerprint mismatch are `inconclusive`. [VERIFIED: `services/korean_morphology.py:119-252`; `32-APPROACH.md`]

**When to use:** Lexical curation, generated sentence validation, regeneration, and export revalidation. The Korean branch executes before Japanese, Mandarin, Stanza, token, substring, whitespace, or suffix logic. [VERIFIED: `services/text_validation.py`; `32-PATTERNS.md`]

Keep one lazy `KiwiKoreanMorphologyService` instance from the composition root. The exact fingerprint is currently analyzer 0.23.2, model 0.23.0, `model_type="cong"`, standard dialect, one worker, allomorph integration, and `top_n=2` with the persisted options. [VERIFIED: `services/korean_morphology.py:30-113`; Context7 `/bab2min/kiwipiepy`]

### Pattern 4: Hard-Gate, Then Score, Then Repair Once

**What:** Generate exactly two strict candidate objects. Validate each independently for schema/bounds, NFC/script, identity non-overwrite, language, selected morphology, source sense, Standard-Seoul register, non-leakage, duplication/template patterns, naturalness, and translation consistency. Only complete passing bundles enter adaptive scoring. [VERIFIED: `32-APPROACH.md`]

**When to use:** Initial generation and regeneration; both must delegate to the same selector. If neither initial candidate passes, issue exactly one repair with a distinct operation, prompt version, request hash, cache key, attempt identity, and controlled failure codes. If repair fails, persist review-required/isolated failure without another chain. [VERIFIED: `32-APPROACH.md`; current same-key gap in `text_generation.py`/`generate_text_items.py`]

Do not use the current final-mode regex JSON salvage that extracts an object from surrounding prose. A Korean final response must validate against the exact bounded schema; malformed or extra output fails safely. Keep any compatibility behavior isolated to legacy modes. [VERIFIED: `provider_text_adapters.py:630-642`; Pydantic strict docs; `32-APPROACH.md`]

### Pattern 5: Cumulative Adaptive Evidence

**What:** Resolve the active approved Phase 31 snapshot once. For final rank `n`, known concepts are its approved concept IDs plus accepted lexical identities from final ranks `< n`; the target is the current complete lexical identity. Persist target, known, observed, incidental/unknown IDs, candidate hash/ordinal, hard-gate outcomes, deterministic score components, scorer/policy versions, and `policy="adaptive"`. [VERIFIED: `32-APPROACH.md`; existing `KoreanCurriculumEvidence` pattern]

**When to use:** After hard quality gates and before final text selection. Build the prefix incrementally in final-rank order rather than deriving level membership or known state at export time. Inconclusive concept extraction stays review-required and is never relabeled strict i+1. [VERIFIED: dependency derivation from `32-APPROACH.md`; `32-PATTERNS.md`]

Naturalness is a hard gate, not a weighted score. A lower incidental-novelty count cannot rescue wrong sense, mixed register, unnatural Korean, or contradictory Portuguese. [VERIFIED: `32-APPROACH.md`]

### Pattern 6: Explicit Provider Policy Snapshot

**What:** Snapshot one approved route per operation: `definition`, `sentence_generation`, `sentence_repair`, `translation`, optional `sentence_judge`, `azure_catalog`, `word_audio`, and `sentence_audio`. Each route binds provider, model/voice when applicable, prompt/policy version, attempt limit, token ceiling, cost ceiling, latency timeout, batch/concurrency bound, and fallback policy. [VERIFIED: `32-APPROACH.md`]

**When to use:** Before every live provider call. Transport retry stays on the same route and is distinct from candidate count and repair count. Cache hits are reported separately, not as provider attempts. [VERIFIED: `32-APPROACH.md`; `provider_retry.py`; `provider_response_cache.py`]

Thread `job_id`, `item_key`, operation, provider, model/voice, attempt, latency, status, request/response hashes, tokens, estimated cost, and controlled retry/error/fallback codes into existing telemetry. Store generated learner text only in necessary typed domain/cache records; never store raw prompts, provider payloads, or private context in telemetry or reports. [VERIFIED: `provider_call_log_repository.py`; `32-APPROACH.md`; OWASP LLM02]

### Pattern 7: Synthesis Is Not Approval

**What:** Keep separate states for catalog qualification, profile approval, request preparation, provider synthesis, byte integrity, human playback review, and export approval. A successful SDK result creates only an integrity-checkable pending asset. [VERIFIED: `32-APPROACH.md`]

**When to use:** Both word and sentence audio. Bind region, exact catalog payload hash/checked time, selected `Locale`, `ShortName`, `VoiceType`, `Status`, SDK/provider version, registry/profile version, output format, NFC text, SSML, request hash, result metadata, final byte size, artifact SHA-256, duration, storage identity, review status, reviewed artifact/metadata hashes, reviewer identity/role, and controlled reason. [VERIFIED: Azure voice-list docs; `32-APPROACH.md`; Phase 31 media pattern]

The current Microsoft REST page illustrates a resource-endpoint voice-list path (`/tts/cognitiveservices/voices/list`), while the code constructs a regional endpoint ending `/cognitiveservices/voices/list`. Do not assert those forms are interchangeable or deprecated without the authorized live regional check; persist the exact endpoint form/region used in the receipt. [VERIFIED: Microsoft REST docs; `azure_speech_adapter.py:20,124-125`]

### Pattern 8: Explicit Manifest Level, Stable Note Identity

**What:** Carry `frequency_level` as internal evidence from the approved manifest through lexical persistence and export snapshot. Do not add it to learner fields or `ExportCardIdentity.stable_guid_input()`. Route notes by that explicit value into child names `<canonical parent>::Level 1`, `::Level 2`, and `::Level 3`. [VERIFIED: `32-APPROACH.md`; current GUID formula in `domain/exporting.py:95-117`]

**When to use:** Korean frequency APKG only in this phase. The current `_frequency_level()` and `_level_for_row()` arithmetic/item-key inference may remain for legacy behavior but cannot be Korean final authority. The current runtime deck-name sanitizer should sanitize only the parent input; internal trusted `::Level N` suffixes must be composed afterward. [VERIFIED: `export_anki_package.py:169-175`; `domain/exporting.py:450-466`; `runtime.py:306,645-646`; `32-APPROACH.md`]

A local genanki experiment verified that `Package([parent, level1, level2, level3])` writes all four deck rows, while packaging only child decks writes only the three `Parent::Level N` rows. Use an explicit parent plus children and inspect the APKG collection deck table and each card's deck ID. [VERIFIED: local genanki 0.13.1 experiment 2026-08-21; Context7 `/kerrickstaley/genanki`; Anki manual]

### Pattern 9: One Additive Persistence Migration

**What:** Extend domain, ORM, migration, repository write, and repository reload together. Preserve historical non-Korean rows with nullable columns or safe defaults; use current sole head `20260804_17` as `down_revision`. [VERIFIED: `uv run alembic heads`; `tests/test_migration_schema_parity.py`; Alembic docs]

**Minimum persistence shape:**

| Record | Minimum New Evidence |
|--------|----------------------|
| Generation job | Active frequency bundle/version/hash and provider-policy snapshot/hash. [VERIFIED: `32-APPROACH.md`] |
| Lexical candidate | Existing rank/level and `korean_identity`, plus typed source/version/confidence/license/curation/bundle evidence in provenance. [VERIFIED: `db/models.py:207-239`; `32-APPROACH.md`] |
| Text quality | Candidate-selection evidence, adaptive evidence, judge evidence if used, and a human-review binding distinct from machine validation. [VERIFIED: `32-APPROACH.md`; current automatic acceptance in `generate_text_items.py:335-371`] |
| Audio asset | Provider/SDK, registry/profile, catalog hash/time, request hash, artifact SHA-256, review status/evidence, fallback origin, and controlled rejection reason. [VERIFIED: `32-APPROACH.md`; current missing fields in `domain/audio.py`] |
| Export snapshot | Explicit internal frequency level and bundle hash without changing learner fields or note-GUID inputs. [VERIFIED: `32-APPROACH.md`; `domain/exporting.py`] |

Whether grouped evidence is stored in strict typed JSON or selected frequently gated fields are explicit columns remains agent discretion; it cannot live only in logs or filenames. [VERIFIED: `32-APPROACH.md`; `32-PATTERNS.md`]

### Anti-Patterns to Avoid

- **Global strict cutover:** do not force unqualified existing-language assets through the Korean contract. [VERIFIED: `32-APPROACH.md`]
- **Duplicate authorities:** do not let CSV notes, DB edits, prompt text, provider output, or export arithmetic override the root manifest and typed identity. [VERIFIED: `32-APPROACH.md`]
- **First valid response wins:** evaluate the complete bounded set deterministically. [VERIFIED: `GTXT-01`; `32-APPROACH.md`]
- **Machine pass equals human approval:** preserve separate states and exact review receipts. [VERIFIED: `32-APPROACH.md`]
- **One generic fallback chain:** final Korean text and audio have no cross-provider fallback. [VERIFIED: `32-APPROACH.md`]
- **Deck level in GUID:** child routing must never alter the current GUID formula or its inputs. [VERIFIED: `32-APPROACH.md`]
- **Write-then-validate:** validate all rows, media, deck IDs, and references in a staged artifact before atomically replacing the destination. [VERIFIED: Phase 31 export precedent; `32-APPROACH.md`]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Unicode equivalence | Ad hoc Hangul/Jamo replacements | `unicodedata.normalize("NFC", ...)` plus existing compatibility/halfwidth rejection | Unicode defines Hangul canonical equivalence and NFC composition; current Korean contract already enforces it. [CITED: unicode.org/reports/tr15/] [VERIFIED: `domain/korean.py`] |
| Korean morphology | Whitespace, suffix, substring, or regex lemma matching | Pinned shared `KiwiKoreanMorphologyService` top-two consensus | Korean inflection and analyzer ambiguity require morphology evidence; project policy already fails closed. [VERIFIED: `korean_morphology.py`; Context7 `/bab2min/kiwipiepy`] |
| Manifest/provider schemas | Loose dict access and coercion | Pydantic v2 strict frozen models with bounded tuples and `extra="forbid"` | Rejects unknown/coerced fields and creates canonical typed boundaries. [CITED: docs.pydantic.dev/latest/concepts/strict_mode/] |
| Cryptographic integrity | `repr()`, Python `hash()`, MD5, or path-derived identity | `hashlib.sha256` over canonical UTF-8 JSON or exact bytes | SHA-256 gives stable cross-process evidence and ASVS requires collision-resistant integrity hashes. [CITED: docs.python.org/3/library/hashlib.html] [VERIFIED: ASVS V11.4.3] |
| Safe asset path handling | String prefix checks or user-selected arbitrary paths | Fixed roots, `pathlib`, safe relative parts, `lstat`/`fstat`, no-follow reads, and Phase 31 snapshot pattern | Prevents traversal, symlink/reparse escape, and TOCTOU substitution. [CITED: docs.python.org/3/library/pathlib.html#pathlib.Path.resolve] [VERIFIED: ASVS V5.3.2/V15.4.2; Phase 31 code] |
| Atomic pointer/output replacement | Direct overwrite of active/final file | Same-directory temp file, flush/fsync, `os.replace`, directory fsync | Readers should observe the old or new complete state, never a partial pointer/artifact. [CITED: docs.python.org/3/library/os.html#os.replace] [VERIFIED: Phase 31 snapshot/export code] |
| Retry/backoff/circuit breaking | New broad `try/except` loops | Existing `retry_provider_call` and `ProviderCircuitBreaker` | Existing code distinguishes attempts and controlled failures; hidden loops break budgets and telemetry. [VERIFIED: `provider_retry.py`; ASVS V13.1.3] |
| LLM routing | Provider-specific calls spread through services | Existing LiteLLM adapter plus explicit operation policy | Central routing enables structured responses, usage/cost capture, cache separation, and approved provider/model snapshots. [CITED: docs.litellm.ai/docs/completion/json_mode] |
| Translation | Prompt-only Portuguese translation | Existing DeepL adapter with explicit `KO` → `PT-BR`, followed by project quality gates | DeepL officially supports both codes; the adapter keeps regional codes at the provider boundary. [CITED: developers.deepl.com/docs/getting-started/supported-languages] |
| SSML/XML escaping | String interpolation of untrusted learner text | `xml.sax.saxutils.escape`/ElementTree with an allowlisted neutral template | Provider text must not alter XML structure or inject audio/resource elements. [VERIFIED: `azure_speech_adapter.py`; ASVS V1.2.1/V1.5.1] |
| Speech synthesis | HTTP/codec implementation or consumer TTS fallback | Azure Speech SDK and approved live voice receipt | SDK exposes configured voice/output and result/cancellation data; Korean fallback is explicitly forbidden. [CITED: learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech] [VERIFIED: `32-APPROACH.md`] |
| APKG format | Direct SQLite/zip authoring | genanki `Deck`, `Note`, and `Package` | genanki already writes Anki collections/media and supports a list of decks. [VERIFIED: Context7 `/kerrickstaley/genanki`] |
| Schema migration | Startup DDL or manual DB edits | One Alembic revision plus SQLAlchemy mappings/repositories | Existing parity tests and reversible migrations are the project authority. [CITED: alembic.sqlalchemy.org/en/latest/tutorial.html] [VERIFIED: repository tests] |
| Linguistic/legal/voice approval | Automatic confidence threshold or LLM judge | Qualified human/legal checkpoints bound to exact hashes | These are external authority decisions and cannot be inferred from tool success. [VERIFIED: `32-APPROACH.md`] |

**Key insight:** Libraries solve parsing, morphology, transport, translation, synthesis, packaging, and migrations; they do not solve source rights, intended sense, naturalness, reviewer authority, voice suitability, or release approval. The implementation must preserve that distinction in its state machine. [VERIFIED: `32-APPROACH.md`; OWASP LLM09]

## Implementation Sequence

The planner should preserve this dependency order; parallelize only tasks that do not create competing authorities. [VERIFIED: dependency ordering in `32-APPROACH.md`]

### Wave 0 — Test Scaffolding and Synthetic Authorities

1. Add unmistakably synthetic strict bundle/catalog/provider/audio/review fixture builders under tests only.
2. Add missing service, CLI, integration, and migration-parity test surfaces before production wiring.
3. Keep all network/provider methods poisoned in automated tests and prove no production asset path is created.

[VERIFIED: `32-APPROACH.md`; `.planning/config.json` has `nyquist_validation=true`]

### Wave 1 — Frequency Authority and Persistence

1. Add frozen frequency/source/adaptive/review contracts and canonical hashing.
2. Implement path-safe root-manifest loading, exact member validation, counts, ranks, identity uniqueness, rejection reconciliation, and inactive/active resolution.
3. Add the one additive migration and complete domain/ORM/repository round trips.
4. Route Korean production-size final mode exclusively through the bundle; leave legacy modes unchanged.

[VERIFIED: `32-APPROACH.md`; direct gaps in `frequency_decks.py`/`runtime.py`]

### Wave 2 — Lexical and Morphology Promotion

1. Persist complete source-backed identity/provenance before definitions.
2. Reuse one shared pinned Kiwi instance for curation and sentence matching.
3. Add explicit `match/mismatch/inconclusive` promotion and mutation tests for ambiguity, OOV, unavailable analysis, malformed evidence, and fingerprint drift.
4. Resolve only genuine active Phase 31 evidence for production known state; retain fixture-only technical mode when unavailable.

[VERIFIED: `32-APPROACH.md`; `korean_morphology.py`]

### Wave 3 — Text Routes, Candidate Selection, and pt-BR Quality

1. Snapshot task routes/budgets and extend definition plus all text operations through one retry/cache/telemetry boundary.
2. Replace single-response Korean final generation with exactly two strict candidates and one distinct repair.
3. Implement Korean hard gates, conservative observed-concept evidence, adaptive scoring, deterministic selection, and shared regeneration semantics.
4. Map `KO` → `PT-BR`, persist canonical `pt` plus editorial-policy ID, and add deterministic/judge/human-review evidence without granting model approval authority.

[VERIFIED: `32-APPROACH.md`; DeepL docs; current text gaps]

### Wave 4 — Exact Azure Audio and Completion Semantics

1. Add complete catalog-row/receipt and approved-profile contracts while keeping Korean unregistered until evidence exists.
2. Bind neutral trusted SSML, exact requests, SDK results, bytes, artifact hashes, and review receipts.
3. Strengthen audio reuse identity and require both word and sentence assets to be exact, non-fallback, integrity-valid, and approved before item success.
4. Strengthen the final export gate against stale/unapproved/mismatched audio.

[VERIFIED: `32-APPROACH.md`; Azure docs; current audio gaps]

### Wave 5 — Real Child Decks and Offline Integration

1. Persist explicit internal level membership without changing learner fields or note GUID inputs.
2. Package the canonical parent and three stable child decks in one staged APKG.
3. Inspect deck rows, card-to-deck IDs, 1000/1000/1000 counts, model/fields/tags/GUIDs/media, then atomically replace output.
4. Run the complete offline Korean flow and affected existing-mode regressions; limit claims to technical structure until external checkpoints pass.

[VERIFIED: `32-APPROACH.md`; genanki/Anki docs; existing export code]

### External Checkpoint Sequence (Non-Autonomous)

1. Genuine Phase 31 receipt/snapshot activation.
2. Frequency rank/lexical source, version, attribution, intended-use, storage, and redistribution decision.
3. Exact 3000-entry inventory/rejection/report review and optional asset-commit authorization.
4. Korean and pt-BR editorial policy, reviewer qualifications, exact review scope, and hash-bound decisions.
5. Exact provider/model credentials and token/cost/latency/batch ceilings; bounded pilot approval, then separate full-run approval.
6. Azure region/credentials, live catalog capture, exact voice/profile/sample approval.
7. Paid 3000-card text and 6000-asset audio run approval.
8. At least 300 word and 300 sentence stratified playback samples plus all risk cases, and 100% automated integrity.
9. Local exact-output review, then separate publication/distribution authorization; Phase 34 still owns observed Anki and generalized closure.

[VERIFIED: `32-APPROACH.md`]

## Failure and Promotion Matrix

| Condition | Required State/Action | Forbidden Behavior |
|-----------|-----------------------|--------------------|
| Source/license missing or redistribution denied | Block before source stream, directory creation, or repo write; private configured root is allowed only if terms explicitly permit it. [VERIFIED: `32-APPROACH.md`] | Assuming use permission implies redistribution permission. |
| Manifest/member missing, oversized, malformed, hash-drifted, short, duplicated, or unreconciled | Controlled content-free failure before persistence/output. [VERIFIED: `32-APPROACH.md`; Phase 31 pattern] | Seed fallback, partial deck, or path/content leakage. |
| Unresolved POS/sense/homograph | Reject or review with source rank accounted for. [VERIFIED: `32-APPROACH.md`] | First dictionary match or provider-authored identity. |
| Kiwi mismatch | Reject candidate/sentence. [VERIFIED: `korean_morphology.py`] | Generic suffix rescue. |
| Kiwi ambiguous/OOV/unavailable/invalid/fingerprint drift | Persist inconclusive/review-required or block. [VERIFIED: `korean_morphology.py`; `32-APPROACH.md`] | Treating unavailable analysis as a match. |
| No complete initial text candidate | Make one cache-distinct repair. [VERIFIED: `32-APPROACH.md`] | Replaying the same cache key, Tatoeba promotion, or unbounded retries. |
| Repair fails | Persist review-required/isolated failure and continue safely where existing job policy permits. [VERIFIED: `32-APPROACH.md`] | Hidden second repair or provider switch. |
| Naturalness/sense/register/translation gate fails | Candidate cannot be scored or selected. [VERIFIED: `32-APPROACH.md`] | Trading quality failure for better i+1 score. |
| Provider route/budget/credentials absent or exhausted | Block the task with controlled telemetry. [VERIFIED: `32-APPROACH.md`] | Local/mock result promoted to production or cross-provider fallback. |
| Catalog/profile absent, stale, wrong locale/status/type, or drifted | Korean remains unregistered; no approved synthesis. [VERIFIED: `32-APPROACH.md`; Azure docs] | Choosing a static documentation voice. |
| SDK success but bytes/hash/review missing | `synthesized_needs_review` or equivalent non-exportable state. [VERIFIED: `32-APPROACH.md`] | Treating provider success as approval. |
| Either word or sentence asset fails, falls back, or is stale/unapproved | Do not call item success; persist resumable failure/review state. [VERIFIED: `generate_audio_items.py` gap; `32-APPROACH.md`] | Advancing audio stage or final export. |
| Deck/model ID collision or required GUID-input change | Stop and replan. [VERIFIED: `32-APPROACH.md`] | Generating replacement IDs at runtime or changing GUID semantics. |
| Phase 31 active evidence absent | Run fixtures for technical proof only; production known-state/export stays blocked. [VERIFIED: `31-28-PLAN.md`; `32-APPROACH.md`] | Copying temporary Phase 31 fixtures into production. |

## Common Pitfalls

### Pitfall 1: “Approved for use” Is Treated as “Approved to Redistribute”
**What goes wrong:** A derived 3000-row asset is written under `assets/frequency/ko/` before exact terms authorize repository redistribution. [VERIFIED: `AGENTS.md`; `32-APPROACH.md`]

**How to avoid:** Gate before directory creation or source access; encode intended use, attribution, storage mode, and redistribution as separate reviewed fields. [VERIFIED: `32-APPROACH.md`]

**Warning signs:** A plan creates Korean production assets before a source-decision task, or has a boolean named only `approved`. [VERIFIED: `32-PATTERNS.md`]

### Pitfall 2: Final Mode Still Has a Hidden `wordfreq`/Seed Edge
**What goes wrong:** The current composition root sets `allow_frequency_seed_fallback=True`, and the generic builder can call `iter_wordlist()`. [VERIFIED: `runtime.py:599-604`; `frequency_decks.py:174-185,362-440`]

**How to avoid:** Add an explicit final-mode route whose imports and call graph terminate at the configured manifest; poison `iter_wordlist`, seed builders, and provider identity in Korean integration tests. [VERIFIED: `GLEX-01`; `32-APPROACH.md`]

### Pitfall 3: Rank Is Mistaken for Sense Frequency
**What goes wrong:** Multiple dictionary senses consume duplicate slots despite the frequency source ranking only a surface token. [VERIFIED: risk resolved in `32-APPROACH.md`]

**How to avoid:** One dominant reviewed source-backed sense per source rank unless the frequency authority supplies independent sense ranks; unresolved joins block. [VERIFIED: `32-APPROACH.md`]

### Pitfall 4: Hashing Before Canonicalization
**What goes wrong:** Canonically equivalent Hangul gets different cache/evidence identities, or text, SSML, and review receipts bind different bytes. [CITED: unicode.org/reports/tr15/] [VERIFIED: `domain/korean.py`]

**How to avoid:** Reject forbidden compatibility/halfwidth Hangul, NFC-normalize before every identity/cache/text/SSML hash, and hash exact final artifact bytes separately. [VERIFIED: `32-APPROACH.md`; `domain/korean.py`]

### Pitfall 5: `frozen=True` Is Assumed to Deep-Freeze Nested Dicts
**What goes wrong:** A frozen Pydantic model can still contain a mutable dictionary whose contents change after validation. [CITED: docs.pydantic.dev/latest/concepts/models/]

**How to avoid:** Use tuples and frozen nested models for authority-bearing structures; canonicalize ordinary mappings into immutable typed entries before hashing. [VERIFIED: Pydantic docs; existing Korean tuple pattern]

### Pitfall 6: Repair Replays the Initial Cache Entry
**What goes wrong:** Current repair calls ordinary generation again under the same `sentence` task/prompt identity. [VERIFIED: `generate_text_items.py:373-400`; `text_generation.py:391-420`]

**How to avoid:** Distinct operation, prompt version, failure-code payload, attempt ID, and cache key; one repair maximum. [VERIFIED: `32-APPROACH.md`]

### Pitfall 7: Loose JSON Salvage Accepts Extra Provider Prose
**What goes wrong:** `_json_payload_from_response` can regex-extract a JSON object from a larger response, bypassing the exact final schema. [VERIFIED: `provider_text_adapters.py:630-642`]

**How to avoid:** Use bounded response schema where supported and always apply strict local Pydantic validation; reject extra/missing candidates and authority-bearing fields. [CITED: docs.litellm.ai/docs/completion/json_mode] [CITED: docs.pydantic.dev/latest/concepts/strict_mode/]

### Pitfall 8: Machine Validation Is Stored as Human Acceptance
**What goes wrong:** Current orchestration maps a passed validator directly to `ReviewStatus.ACCEPTED`, which is insufficient for the locked Korean/pt-BR review authority. [VERIFIED: `generate_text_items.py:335-371`; `domain/text_quality.py:19-29`]

**How to avoid:** Keep machine validation and qualified hash-bound human approval distinct; final Korean promotion requires both under the current policy. [VERIFIED: `32-APPROACH.md`]

### Pitfall 9: i+1 Scoring Rewards Unnatural Output
**What goes wrong:** A candidate with fewer incidental concepts can outrank a natural candidate despite register, sense, or fluency defects. [VERIFIED: risk resolved in `32-APPROACH.md`]

**How to avoid:** Naturalness and all semantic/register gates execute before scoring; score only passing complete bundles. [VERIFIED: `32-APPROACH.md`]

### Pitfall 10: Canonical `pt` and Provider `PT-BR` Become Two Product Languages
**What goes wrong:** Tags, cache identity, DB language, or deck identity drift to `pt-BR`. [VERIFIED: risk resolved in `32-APPROACH.md`]

**How to avoid:** Persist `pt`; translate via `PT-BR` only inside the DeepL adapter and store a versioned editorial-policy ID separately. [VERIFIED: `32-APPROACH.md`; DeepL docs]

### Pitfall 11: Token/Cost Telemetry Is Incomplete or Leaks Content
**What goes wrong:** Caller omits `job_id`, definition calls bypass orchestration, cache hits appear as calls, or raw exceptions/prompts/responses enter logs. [VERIFIED: `generate_text_items.py:187-193`; `lexical_grounding.py` gap mapped in `32-PATTERNS.md`; `provider_call_log_repository.py`]

**How to avoid:** Route every operation through one attempt logger, capture LiteLLM usage/cost when supplied, report missing-value denominators, and store only controlled summaries/hashes. [VERIFIED: Context7 `/berriai/litellm`; `32-APPROACH.md`; OWASP LLM02]

### Pitfall 12: A Static Azure Voice Name Is Mistaken for Regional Approval
**What goes wrong:** A voice listed in documentation is inserted into the registry without proving it exists in the configured region or sounds acceptable. [VERIFIED: Azure docs describe region-specific lists; `32-APPROACH.md`]

**How to avoid:** Keep Korean absent until an authorized live catalog payload and exact heard sample/profile approval are hash-bound. [VERIFIED: `audio_voice_registry.py`; `32-APPROACH.md`]

### Pitfall 13: XML/HTML Output Is Trusted Because It Came from a Provider
**What goes wrong:** Provider text alters SSML/Anki HTML structure or injects unexpected resources. [VERIFIED: OWASP LLM05; current provider returns `definitions_html`]

**How to avoid:** Treat LLM output as untrusted, permit only the intended definition structure, escape learner text, and construct SSML from trusted templates/voice IDs. [VERIFIED: OWASP LLM05; ASVS V1.2.1/V1.5.1; `azure_speech_adapter.py`]

### Pitfall 14: Audio Reuse Identity Is Too Weak
**What goes wrong:** Current lookup keys omit provider/SDK, locale, registry/profile, catalog, artifact, and review identity; sentence assets bypass the word alignment helper. [VERIFIED: `generate_audio_items.py:120-155`; `audio_repository.py`]

**How to avoid:** Reuse only on the complete request/profile/provider/format/artifact/review identity and revalidate exact current text before export. [VERIFIED: `32-APPROACH.md`]

### Pitfall 15: Failed Audio Still Marks the Item Successful
**What goes wrong:** The current loop increments failures but unconditionally calls `record_item_success`. [VERIFIED: `generate_audio_items.py:93-108`]

**How to avoid:** Aggregate all required kinds first; success only if both are exact, approved, current, and non-fallback. [VERIFIED: `32-APPROACH.md`; `GAUD-01`]

### Pitfall 16: Export Reconstructs Level from Rank or Item Key
**What goes wrong:** Current helpers use arithmetic/regex and can silently disagree with approved frozen membership. [VERIFIED: `export_anki_package.py:169-175`; `domain/exporting.py:450-466`]

**How to avoid:** Carry explicit manifest level to export; test mutations where rank and level disagree and require failure. [VERIFIED: `32-APPROACH.md`]

### Pitfall 17: Child Decks Change Note Identity or Disappear Through Sanitization
**What goes wrong:** Level/deck name enters the GUID, or `_sanitize_deck_name()` replaces trusted `::` hierarchy separators. [VERIFIED: current GUID and sanitizer code]

**How to avoid:** Preserve `stable_guid_input()` exactly; sanitize the parent only, append internal child suffixes afterward, and compare pre/post GUIDs. [VERIFIED: `domain/exporting.py:103-117`; `runtime.py:645-646`; `32-APPROACH.md`]

### Pitfall 18: Structural Tests Overclaim Human or Anki Acceptance
**What goes wrong:** APKG SQLite inspection or source-file playback is described as Desktop/mobile import, rendering, or in-Anki playback evidence. [VERIFIED: `32-APPROACH.md`]

**How to avoid:** Phase 32 claims exact package structure and reviewed source bytes only; Phase 34 owns observed Anki closure. [VERIFIED: `32-APPROACH.md`]

## Code Examples

Verified patterns from official sources and repository precedents follow. Names are illustrative; exact naming remains agent discretion. [VERIFIED: `32-APPROACH.md`]

### Strict Immutable Manifest Model

```python
# Sources:
# - https://docs.pydantic.dev/latest/concepts/strict_mode/
# - https://docs.pydantic.dev/latest/concepts/models/
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class FrozenEvidence(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )


class BundleMember(FrozenEvidence):
    role: Literal["curated", "rejections", "report", "attribution"]
    relpath: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class KoreanFrequencyManifest(FrozenEvidence):
    schema_version: Literal[1]
    bundle_version: str = Field(min_length=1, max_length=64)
    entry_count: Literal[3000]
    level_counts: tuple[Literal[1000], Literal[1000], Literal[1000]]
    members: tuple[BundleMember, ...] = Field(min_length=4, max_length=32)
    bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
```

Use tuples/frozen nested models because Pydantic's `frozen=True` does not deep-freeze a nested mutable dictionary. [CITED: docs.pydantic.dev/latest/concepts/models/]

### Canonical Structured Hash and Raw Artifact Hash

```python
# Source pattern: src/multilang/services/provider_response_cache.py
import json
from hashlib import sha256
from pydantic import BaseModel


def canonical_sha256(value: BaseModel) -> str:
    raw = json.dumps(
        value.model_dump(mode="json"),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(raw).hexdigest()


def artifact_sha256(raw: bytes) -> str:
    return sha256(raw).hexdigest()
```

Canonical structured hashes bind meaning; raw-byte hashes bind the exact file/audio artifact. Do not substitute one for the other. [VERIFIED: `32-APPROACH.md`]

### Path-Safe Read and Atomic Pointer Replacement

```python
# Sources:
# - src/multilang/services/korean_foundation_snapshot.py
# - https://docs.python.org/3/library/os.html#os.replace
import os
import tempfile
from pathlib import Path, PurePosixPath


def contained_member(root: Path, relpath: str) -> Path:
    if (
        not relpath
        or relpath != relpath.strip()
        or relpath.startswith(("/", "~"))
        or "\\" in relpath
        or ":" in relpath
        or "\x00" in relpath
        or "//" in relpath
    ):
        raise ValueError("unsafe bundle member")
    raw_parts = relpath.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError("unsafe bundle member")
    path = PurePosixPath(relpath)
    if path.is_absolute() or tuple(path.parts) != tuple(raw_parts):
        raise ValueError("unsafe bundle member")
    candidate = root.joinpath(*path.parts)
    candidate.relative_to(root)  # raises when outside the fixed root
    return candidate


def replace_pointer_atomically(directory: Path, destination: Path, raw: bytes) -> None:
    fd, name = tempfile.mkstemp(prefix=".active-frequency.", suffix=".tmp", dir=directory)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        dir_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        temporary.unlink(missing_ok=True)
```

Production code must also retain the Phase 31 `lstat`/no-follow/`fstat` continuity checks; the abbreviated example is not a replacement for those tested defenses. [VERIFIED: `korean_foundation_snapshot.py:730-831`]

### Deterministic Two-Candidate Selection

```python
# Source: user-confirmed Phase 32 approach
initial = adapter.generate_candidates(request, expected_count=2)
if len(initial) != 2:
    raise FinalTextBlocked("candidate_count_invalid")

passing = []
for ordinal, candidate in enumerate(initial):
    evidence = validate_complete_bundle(candidate, lexical_identity, known_state)
    if evidence.hard_gates_passed:
        passing.append((adaptive_score(evidence), evidence.candidate_sha256, ordinal, candidate, evidence))

if not passing:
    repaired = adapter.repair_candidate(
        request,
        operation="sentence_repair",
        controlled_reason_codes=collect_reason_codes(initial),
    )
    evidence = validate_complete_bundle(repaired, lexical_identity, known_state)
    if not evidence.hard_gates_passed:
        raise FinalTextBlocked("repair_exhausted")
    passing.append((adaptive_score(evidence), evidence.candidate_sha256, 0, repaired, evidence))

selected = min(passing, key=lambda item: (item[0], item[1], item[2]))
```

The score tuple is consulted only after every hard gate passes; candidate hash precedes ordinal so provider return ordering cannot change a tie between the same candidate set. [VERIFIED: `32-APPROACH.md`; `32-PATTERNS.md`]

### DeepL Boundary Mapping

```python
# Sources:
# - https://github.com/DeepLcom/deepl-python
# - https://developers.deepl.com/docs/getting-started/supported-languages
result = deepl_client.translate_text(
    korean_sentence,
    source_lang="KO",
    target_lang="PT-BR",
)
translation = result.text
```

Persist project target language `pt` and a pt-BR editorial-policy version, not `PT-BR` as a second product language. [VERIFIED: `32-APPROACH.md`]

### Neutral Escaped Azure SSML

```python
# Sources:
# - https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice
# - src/multilang/services/azure_speech_adapter.py
from xml.sax.saxutils import escape


def build_neutral_ko_ssml(text_nfc: str, approved_voice: str) -> str:
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR">'
        f'<voice name="{escape(approved_voice)}">{escape(text_nfc)}</voice>'
        '</speak>'
    )
```

Do not add prosody/style until exact heard approval creates a new versioned profile and invalidates dependent approval. [VERIFIED: `32-APPROACH.md`; Azure SSML docs]

### One Parent and Three Child Decks

```python
# Sources:
# - Context7 /kerrickstaley/genanki
# - https://docs.ankiweb.net/getting-started.html#decks
import genanki

parent = genanki.Deck(KO_PARENT_DECK_ID, parent_name)
levels = {
    1: genanki.Deck(KO_LEVEL_1_DECK_ID, f"{parent_name}::Level 1"),
    2: genanki.Deck(KO_LEVEL_2_DECK_ID, f"{parent_name}::Level 2"),
    3: genanki.Deck(KO_LEVEL_3_DECK_ID, f"{parent_name}::Level 3"),
}

for row in rows:
    levels[row.frequency_level].add_note(build_multilang_note(row, model=model))

package = genanki.Package([parent, levels[1], levels[2], levels[3]])
package.media_files = [str(path) for path in verified_media]
package.write_to_file(str(staged_output))
```

`frequency_level` is internal persisted manifest evidence and must not enter note fields or `stable_guid_input()`. Inspect `col.decks`, `cards.did`, note GUIDs, models, fields, and media before replacing the final APKG. [VERIFIED: local genanki experiment; `domain/exporting.py`; `32-APPROACH.md`]

### Reversible Additive Alembic Column

```python
# Source: https://alembic.sqlalchemy.org/en/latest/tutorial.html
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.add_column(
        "text_quality_records",
        sa.Column("candidate_selection_evidence", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("text_quality_records", "candidate_selection_evidence")
```

Mirror every actual migration field in the ORM and repositories and prove upgrade/downgrade/re-upgrade plus legacy-null behavior. [VERIFIED: `tests/test_migration_schema_parity.py`; SQLAlchemy/Alembic docs]

## Official API Quick Reference

| API | Verified Behavior | Phase 32 Use |
|-----|-------------------|--------------|
| Pydantic `ConfigDict` | Supports strict mode, forbidden extras, frozen models, and hidden input values; `model_validate` validates Python payloads. [VERIFIED: Context7 `/pydantic/pydantic`] | Strict manifest/evidence/provider schemas; remember nested mutable values are not deep-frozen. |
| Kiwi `analyze(text, top_n=...)` | Returns the top N token analyses with scores and supports standard-dialect/options configuration. [VERIFIED: Context7 `/bab2min/kiwipiepy`] | Preserve the exact pinned top-two consensus and fingerprint. |
| LiteLLM `response_format` and usage | Supports JSON/JSON-schema-style structured output for compatible models, returns token usage, and provides `completion_cost`. [VERIFIED: Context7 `/berriai/litellm`; official LiteLLM docs] | Route capability must be checked for the approved model; strict local validation remains mandatory. |
| DeepL `translate_text` | Requires target language, accepts optional source language/context/model controls, and returns text plus detected/model/billing metadata. [VERIFIED: Context7 `/deepl/deepl-python`] | Explicit `KO` → `PT-BR`; retain provider metadata without changing canonical `pt`. |
| DeepL languages | `KO` supports translation; `PT-BR` is a target variant. [CITED: developers.deepl.com/docs/getting-started/supported-languages] | Provider boundary codes only. |
| Azure voice list | Regional/resource voice inventory returns `ShortName`, `Locale`, `VoiceType`, `Status`, sample rate, styles, and related fields; authentication is required. [CITED: learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech#get-a-list-of-voices] | Hash the complete authorized response and selected row; do not retain IDs only. |
| Azure SSML | `<speak>` contains at least one `<voice name=...>`; voice/language/style/prosody are controllable. [CITED: learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice] | Start with escaped neutral `ko-KR` text and exact approved voice. |
| SQLAlchemy typed declarative | `Mapped[T | None]`/`Optional[T]` can represent nullable fields. [VERIFIED: Context7 `/websites/sqlalchemy_en_20`] | Add legacy-compatible evidence columns. |
| Alembic operations | `op.add_column` and `op.drop_column` implement reversible column migrations. [VERIFIED: Context7 `/websites/alembic_sqlalchemy`] | One sole-head additive migration. |
| genanki `Package` | Constructor accepts one deck or a list of decks; `Deck` accepts an explicit ID/name and package includes declared media. [VERIFIED: Context7 `/kerrickstaley/genanki`] | Explicit parent and three child decks in one package. |
| Anki deck hierarchy | Double colons (`::`) define parent/child deck levels. [CITED: docs.ankiweb.net/getting-started.html#decks] | Trusted internal names `Parent::Level N`. |
| Unicode NFC | NFC performs canonical decomposition followed by canonical composition; canonically equivalent Hangul has a unique normalized representation. [CITED: unicode.org/reports/tr15/] | Normalize before identity/cache/SSML/evidence hashes. |

## State of the Art

| Old/Current Approach | Phase 32 Approach | When Changed | Impact |
|----------------------|-------------------|--------------|--------|
| Live `wordfreq` candidate path and optional seed grounding | One immutable manifest-bound Korean final bundle; `wordfreq` isolated to approved bootstrap tooling | User-confirmed 2026-08-21 | Missing or insufficient production assets block instead of silently changing vocabulary. [VERIFIED: `32-APPROACH.md`] |
| Token/lemma CSV identity and first-match risk | Complete source-backed lemma + POS + sense + Kiwi fingerprint | Phase 30 contract, required by Phase 32 | Homographs and inflections cannot silently collapse or multiply ranks. [VERIFIED: Phase 30 code; `32-APPROACH.md`] |
| One provider response | Exactly two strict candidates, deterministic complete-bundle selection, one distinct repair | User-confirmed 2026-08-21 | Selection optimizes among validated options without unbounded spend. [VERIFIED: `32-APPROACH.md`] |
| Same `sentence` cache identity for retry | Separate generation/repair operations, versions, hashes, and controlled failure payloads | Phase 32 | Repair cannot replay the first cached answer. [VERIFIED: current code gap; `32-APPROACH.md`] |
| Automatic Tatoeba repair outside Korean | No Tatoeba automatic final-mode promotion for any language | Phase 32 shared hardening | Final examples remain provider/curation-evidence controlled. [VERIFIED: `GTXT-01`; `32-APPROACH.md`] |
| Generic target heuristics after adapter failure | Selected morphology adapter returns match/mismatch/inconclusive and fails closed | Phase 30/32 | Analyzer absence or ambiguity cannot become acceptance. [VERIFIED: `korean_morphology.py`; `GMOR-01`] |
| Canonical `pt` mapped implicitly to `PT-BR` | Explicit pt-BR editorial policy with provider-only `PT-BR` | User-confirmed 2026-08-21 | Regional output is reproducible without creating a new product-language identity. [VERIFIED: `32-APPROACH.md`] |
| Static voice registry IDs and synthesized/failed state | Live catalog/profile receipt plus synthesized-needs-review/approved exact-byte evidence | Phase 32 | Provider success and fallback cannot bypass heard approval. [VERIFIED: `32-APPROACH.md`] |
| Audio reuse by kind/text/SSML/voice/format | Full provider/profile/catalog/artifact/review identity | Phase 32 | Stale or differently approved bytes are not reused. [VERIFIED: current gap; `32-APPROACH.md`] |
| One APKG deck and arithmetic level tags | Explicit parent + three real child decks from persisted manifest level | User-confirmed 2026-08-21 | `KFREQ-02` is delivered without changing fields or note GUIDs. [VERIFIED: `32-APPROACH.md`] |

**Deprecated/outdated for Korean final mode:**

- `allow_frequency_seed_fallback=True`, `iter_wordlist()` final loading, `_build_seed_candidate`, and provider-authored lexical identity. [VERIFIED: `32-APPROACH.md`]
- First-response acceptance, regex JSON salvage, same-key repair, and automatic Tatoeba promotion. [VERIFIED: `32-APPROACH.md`; current code]
- Generic suffix/whitespace/substring rescue after selected Korean morphology is inconclusive. [VERIFIED: `GMOR-01`; `32-APPROACH.md`]
- Documentation-picked voice IDs, alternate voice/provider fallback, or synthesized status as approval. [VERIFIED: `32-APPROACH.md`]
- Export-time Korean level inference and any child-deck-driven GUID change. [VERIFIED: `32-APPROACH.md`]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| — | None. Recommendations are derived from user-confirmed Phase 32 decisions, inspected repository behavior, live registry probes, or cited official documentation. | — | — |

All production-specific unknowns are listed as open checkpoints rather than assumptions. [VERIFIED: `32-APPROACH.md`]

## Open Questions

1. **What are the exact NIKL attachment bytes, terms evidence, attribution, and final storage/redistribution disposition?**
   - What we know: the user selected NIKL `한국어 학습용 어휘 목록`; its official page describes 5,965 rows with 2002 rank, POS, homonym, gloss, and grade data and marks the work for KOGL Type 1 use with specific source attribution. No `assets/frequency/ko/` production asset exists. [VERIFIED: official NIKL page; `32-FREQUENCY-SOURCE-DECISION.md`]
   - What's unclear: exact attachment hash/schema after retrieval, captured KOGL terms evidence, approved attribution/change notice, modernity-review result, and whether the transformed bundle will be committed or kept private.
   - Recommendation: implement the decision schema and blocked loader now; stop before production source ingestion or asset creation until the exact artifact and every redistribution field pass review. [VERIFIED: `32-APPROACH.md`; `32-FREQUENCY-SOURCE-DECISION.md`]

2. **When will a genuine Phase 31 snapshot be active?**
   - What we know: The replanned sequence culminates in Plan 31-28's non-autonomous exact activation/export checkpoint, and no `31-28-SUMMARY.md` exists. [VERIFIED: phase files/glob]
   - What's unclear: reviewer evidence, rights/media bytes, receipt, activation authorization, and active snapshot hash.
   - Recommendation: depend on the fixed active resolver; use synthetic fixtures only for technical tests and leave production blocked. [VERIFIED: `31-28-PLAN.md`; `32-APPROACH.md`]

3. **What exact concept-extraction policy maps arbitrary Korean sentence analyses to frozen concept IDs?**
   - What we know: the repository has strict Phase 31 concepts and Kiwi analyses but no exact frequency-sentence concept extractor. [VERIFIED: `32-PATTERNS.md`; code search]
   - What's unclear: versioned mapping coverage and the policy for lexemes/morphemes not present in the frozen identity index.
   - Recommendation: map only conclusive selected-adapter results to known frozen IDs; classify every unresolved observation as incidental/unknown and require review rather than inferring mastery. [VERIFIED: `32-APPROACH.md`]

4. **Which text routes, models, budgets, and review policy are approved?**
   - What we know: project `Settings()` resolves OpenAI, OpenRouter, and DeepL credentials, but no credential, route, default model, token/cost/latency/batch policy, or live run is approved for Phase 32 merely by being configured. [VERIFIED: scanner-safe Settings probe; `settings.py`; `32-APPROACH.md`]
   - What's unclear: exact model IDs, prompt/judge policy, budgets, pilot size, reviewer qualifications, and text-review coverage.
   - Recommendation: implement typed policy snapshots and deterministic fakes; do not choose a model, budget, judge, reviewer, or review percentage in code/plans. [VERIFIED: `32-APPROACH.md`]

5. **Which Azure endpoint form, region, voice, output format, and neutral profile are approved?**
   - What we know: Azure supports `ko-KR`, the SDK is installed, `Settings()` resolves a Speech key and region, and current official docs plus code expose different voice-list endpoint forms. Configuration is not approval. [VERIFIED: Azure docs; installed metadata; scanner-safe Settings probe; `azure_speech_adapter.py`; `32-APPROACH.md`]
   - What's unclear: authorized credential/region use, resource endpoint form, exact live catalog, voice, output format, samples, and heard decision.
   - Recommendation: preserve these as an authorized live-catalog/profile checkpoint; do not pre-register any Korean voice. [VERIFIED: `32-APPROACH.md`]

6. **What stable parent/child deck IDs will be assigned?**
   - What we know: IDs must be explicit, stable, collision-checked, and cannot alter note GUID inputs. [VERIFIED: genanki docs; `32-APPROACH.md`]
   - What's unclear: the exact four numeric constants.
   - Recommendation: choose constants in implementation under agent discretion, scan all existing model/deck IDs, and add collision/golden tests; stop if preserving GUID semantics would require a broader identity migration. [VERIFIED: `32-APPROACH.md`]

7. **Will the approved frequency bundle be committed, stored privately, or remain inactive?**
   - What we know: use permission, repository redistribution, asset commit, local activation, and publication are separate checkpoints. [VERIFIED: `32-APPROACH.md`]
   - What's unclear: the final disposition.
   - Recommendation: support the same strict contract at a configured private root, but never interpret that capability as commit/publication authorization. [VERIFIED: `32-APPROACH.md`]

## Environment Availability

| Dependency | Required By | Available | Version / State | Fallback |
|------------|-------------|-----------|-----------------|----------|
| Python | All offline work | ✓ | 3.12.3 | — [VERIFIED: environment probe] |
| uv | Environment/test commands | ✓ | 0.11.7 | — [VERIFIED: environment probe] |
| Pydantic / SQLAlchemy / Alembic | Contracts and persistence | ✓ | 2.12.5 / 2.0.49 / 1.18.4 | — [VERIFIED: installed metadata] |
| Kiwi + model | Korean morphology | ✓ | 0.23.2 / 0.23.0 | No final-mode heuristic fallback. [VERIFIED: installed metadata; `32-APPROACH.md`] |
| genanki | APKG structure | ✓ | 0.13.1 | — [VERIFIED: installed metadata] |
| PostgreSQL | Target-database verification | ✓ | Server 17.11 reachable through project SQLAlchemy settings; standalone `psql`/`pg_isready` CLIs are absent | — [VERIFIED: read-only `SELECT 1`/`SHOW server_version` probe; environment command probe] |
| LiteLLM provider credentials | Live text generation | ✓ technical / ✗ approved | `Settings()` resolves OpenAI and OpenRouter keys; LiteLLM-specific key is absent | Deterministic fake for offline proof; configured keys/models must not be called until explicit Phase 32 approval. [VERIFIED: scanner-safe Settings probe; `_litellm_api_key`; `32-APPROACH.md`] |
| DeepL credentials | Live translation | ✓ technical / ✗ approved | `Settings()` resolves a key | Deterministic fake for offline proof; no live call until explicit approval. [VERIFIED: scanner-safe Settings probe; `32-APPROACH.md`] |
| Azure Speech credentials/region | Live voice list and synthesis | ✓ technical / ✗ approved | `Settings()` resolves a key and region | Injected catalog/SDK fake for offline proof; no live discovery/synthesis or provider fallback until explicit approval. [VERIFIED: scanner-safe Settings probe; `32-APPROACH.md`] |
| Selected frequency source / approved asset | Production inventory | partial / ✗ | NIKL path selected; exact attachment/terms and transformed bundle not supplied; no repo `ko` asset | None; production remains blocked until exact source and bundle evidence pass. [VERIFIED: official NIKL page; repository glob; `32-FREQUENCY-SOURCE-DECISION.md`] |
| Qualified Korean/pt-BR/audio evidence | Learner-ready promotion | ✗ | not supplied in Phase 32 | None; exact review remains blocked. [VERIFIED: `32-APPROACH.md`] |

**Missing dependencies with no production fallback:** approved Phase 31 state, exact NIKL attachment/terms and final inventory, authorization to use exact routes/models/budgets/configured credentials, qualified content review, live Azure profile, production media/review, and release authorization. [VERIFIED: `32-APPROACH.md`; `32-FREQUENCY-SOURCE-DECISION.md`; environment probes]

**Offline-only substitutes:** provider/catalog/audio boundaries can use deterministic fakes, and SQLite remains useful for fast migration/repository tests even though PostgreSQL 17.11 is reachable; neither fake-provider nor SQLite-only evidence proves production readiness. [VERIFIED: repository tests; read-only PostgreSQL probe; `32-APPROACH.md`]

## Validation Architecture

`.planning/config.json` explicitly enables Nyquist validation. [VERIFIED: `.planning/config.json`]

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 with pytest-asyncio 0.26.0 [VERIFIED: installed metadata] |
| Config file | `pyproject.toml` (`testpaths=["tests"]`, `pythonpath=["src"]`, `asyncio_mode="auto"`) [VERIFIED: `pyproject.toml`] |
| Measured quick baseline | `uv run pytest tests/services/test_text_generation.py::test_korean_requests_copy_the_complete_persisted_identity tests/services/test_audio_voice_registry.py::test_voice_registry_rejects_korean_without_an_approved_voice tests/services/test_export_anki_package.py::test_export_anki_package_bundles_referenced_media_and_sound_basenames tests/test_migration_schema_parity.py::test_korean_identity_revision_is_the_sole_linear_head -q` → 4 passed in 2.62s [VERIFIED: test run 2026-08-21] |
| Full suite command | `uv run pytest -q` (duration not measured in this research) [VERIFIED: pytest config] |

A broad four-module focused command exceeded the 120-second research timeout after producing test progress, so task verification should use exact nodes and wave verification should reserve a larger timeout. Do not describe the broad suite as a sub-30-second quick check. [VERIFIED: test run 2026-08-21]

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| KFREQ-01 | Exact auditable bundle fields, hashes, sequence, decisions, and controlled failures | unit | `uv run pytest tests/services/test_korean_frequency.py::test_manifest_requires_exact_auditable_inventory -q` | ❌ Wave 0 |
| KFREQ-02 | Explicit manifest levels route 1000/1000/1000 notes to real child decks without GUID changes | integration | `uv run pytest tests/integration/test_korean_frequency_text_audio_flow.py::test_manifest_levels_route_to_three_child_decks_without_guid_drift -q` | ❌ Wave 0 |
| KFREQ-03 | Natural passing candidates use cumulative known/incidental evidence and deterministic adaptive score | unit | `uv run pytest tests/services/test_korean_text_quality.py::test_adaptive_score_uses_prior_approved_order_after_hard_gates -q` | ❌ Wave 0 |
| KTXT-01 | Standard-Seoul/sense/register/leakage/naturalness/pt-BR contradictions block | unit | `uv run pytest tests/services/test_korean_text_quality.py::test_korean_and_pt_br_hard_gate_matrix -q` | ❌ Wave 0 |
| KAUD-01 | Live-receipt/profile/request/artifact/review hashes gate both exact assets | integration | `uv run pytest tests/integration/test_korean_frequency_text_audio_flow.py::test_only_exact_reviewed_azure_word_and_sentence_assets_promote -q` | ❌ Wave 0 |
| GLEX-01 | Korean final load never reaches wordfreq/seed fallback | unit | `uv run pytest tests/services/test_korean_frequency.py::test_final_loader_has_no_wordfreq_or_seed_edge -q` | ❌ Wave 0 |
| GLEX-02 | Complete source/POS/sense/version/confidence survives commit/expire/reload | repository | `uv run pytest tests/repositories/test_lexical_repository.py -k korean_frequency_provenance_round_trip -q` | Existing file; ❌ new case |
| GMOR-01 | Match/mismatch/inconclusive matrix never invokes generic rescue | unit | `uv run pytest tests/services/test_text_validation.py -k korean -q` | ✅; extend matrix |
| GTXT-01 | Exactly two candidates, deterministic selection, distinct one-repair cache, no Tatoeba | unit | `uv run pytest tests/services/test_generate_text_items.py -k 'candidate or repair or tatoeba' -q` | ✅; extend cases |
| GPRO-01 | Every task route logs sanitized attempt/hash/token/cost data and cache hits separately | unit | `uv run pytest tests/services/test_text_generation.py -k 'telemetry or cache or retry' -q` | ✅; extend routes |
| GAUD-01 | Failed/fallback/stale/unapproved asset prevents item success and export | unit | `uv run pytest tests/services/test_generate_audio_items.py -k 'failure or fallback or approval' -q` | ✅; extend cases |

### Sampling Rate

- **Per task commit:** run exact new/changed test nodes; keep deterministic unit nodes under 30 seconds. [VERIFIED: Nyquist requirement; measured quick baseline]
- **Per wave merge:** run all directly affected domain/service/repository/CLI/integration files with a timeout appropriate to their measured duration. [VERIFIED: broad focused run exceeded 120 seconds]
- **Phase gate:** run `uv run pytest -q`, the Korean Phase 30/31 boundary suites, migration parity, APKG structure inspection, and a no-network/no-production-side-effect scan before `/gsd-verify-work`. [VERIFIED: `32-APPROACH.md`; repository workflow]

### Wave 0 Gaps

- [ ] `tests/services/test_korean_frequency.py` — strict source/manifest/identity/rejection/final-loader authority for KFREQ-01, KFREQ-02, GLEX-01, and GLEX-02. [VERIFIED: file absent; `32-PATTERNS.md`]
- [ ] `tests/services/test_korean_text_quality.py` — Korean hard gates, adaptive evidence, deterministic candidate selection, pt-BR quality, and review binding for KFREQ-03/KTXT-01/GTXT-01. [VERIFIED: file absent; `32-PATTERNS.md`]
- [ ] `tests/cli/test_korean_frequency_commands.py` — fixed pathless check/validate/catalog/review/generate commands and scanner-safe output. [VERIFIED: file absent; `32-PATTERNS.md`]
- [ ] `tests/integration/test_korean_frequency_text_audio_flow.py` — frozen bundle through three child decks using SQLite, fakes, exact bytes, and no network. [VERIFIED: file absent; `32-PATTERNS.md`]
- [ ] Extend `tests/test_migration_schema_parity.py` with the new sole head, legacy-null behavior, upgrade/downgrade/re-upgrade, ORM parity, and repository reloads. [VERIFIED: existing parity pattern]
- [ ] Extend existing text/cache/retry/telemetry, Azure/registry/audio, export, runtime, and existing-mode regression files listed in `32-PATTERNS.md`. [VERIFIED: `32-PATTERNS.md`]
- [ ] Add a target-PostgreSQL 17 migration/repository run using an isolated test database/schema and explicit authorization before writes; the server is reachable, while the research probe was read-only. [VERIFIED: read-only PostgreSQL 17.11 probe; `AGENTS.md` PostgreSQL target]

No framework installation gap exists. [VERIFIED: pytest 8.4.2 installed]

## Security Domain

### Applicable ASVS 5.0.0 Categories

ASVS 5.0.0 uses the current chapter names below; authentication/session web categories do not drive this local-CLI phase, but service credentials, outbound APIs, files, untrusted model output, and sensitive telemetry do. [VERIFIED: OWASP ASVS 5.0.0 CSV; `32-APPROACH.md`]

| ASVS Category / Controls | Applies | Standard Control |
|--------------------------|---------|------------------|
| V1 Encoding and Sanitization — V1.2.1, V1.5.1, V1.5.3 | yes | Contextual HTML/XML escaping, restrictive SSML structure, and one canonical JSON parser/encoding policy. [VERIFIED: OWASP ASVS 5.0.0] |
| V2 Validation and Business Logic — V2.2.1, V2.3.3, V2.4.1 | yes | Positive allowlists/typed bounds, atomic all-or-nothing promotion, and exact candidate/retry/budget limits. [VERIFIED: OWASP ASVS 5.0.0] |
| V3 Web Frontend Security | no new surface | Phase 32 adds no browser/UI; preserve existing Anki template escaping/contracts without claiming browser evidence. [VERIFIED: `32-APPROACH.md`] |
| V4 API and Web Service | provider boundary only | Validate content types/statuses and never follow insecure redirects/fallback transport. [VERIFIED: Azure/DeepL SDK boundaries; ASVS V4] |
| V5 File Handling — V5.3.2 | yes | Fixed allowlisted roots, internally generated relative member names, no traversal/symlink/reparse escape. [VERIFIED: OWASP ASVS 5.0.0; Phase 31 precedent] |
| V6–V10 Authentication/Session/Authorization/Tokens/OAuth | no new user-auth surface | Do not add a web auth layer; existing local operator/checkpoint and provider-credential boundaries remain. [VERIFIED: `32-APPROACH.md`] |
| V11 Cryptography — V11.4.3 | yes | SHA-256 for collision-resistant integrity bindings; never hand-roll cryptography. [VERIFIED: OWASP ASVS 5.0.0; `32-APPROACH.md`] |
| V12 Secure Communication — V12.2.1, V12.3.1, V12.3.2 | yes for live calls | HTTPS/TLS only and normal certificate validation for LiteLLM provider, DeepL, and Azure. [VERIFIED: OWASP ASVS 5.0.0; official provider URLs] |
| V13 Configuration — V13.1.3, V13.2.4, V13.3.1 | yes | Document timeouts/retries, allowlist providers/endpoints, and keep API keys out of source/build artifacts. [VERIFIED: OWASP ASVS 5.0.0] |
| V14 Data Protection — V14.1.1, V14.2.4, V14.2.7 | yes | Classify private excerpts/prompts/secrets/reviewer data, define an approved retention/deletion policy before live operation, and keep sensitive content out of telemetry. No retention period is selected by this research. [VERIFIED: OWASP ASVS 5.0.0; `32-APPROACH.md`] |
| V15 Secure Coding and Architecture — V15.1.2, V15.2.2, V15.4.2 | yes | Locked dependency inventory, bounded costly work, and atomic/TOCTOU-safe activation. [VERIFIED: OWASP ASVS 5.0.0] |
| V16 Security Logging and Error Handling — V16.2.5, V16.3.3, V16.4.1, V16.5.2, V16.5.3 | yes | Hash/mask sensitive values, controlled codes, encode log fields, record bypass attempts, and fail securely on provider/resource errors. [VERIFIED: OWASP ASVS 5.0.0] |

### Known Threat Patterns for the Stack

| Pattern | STRIDE / OWASP | Standard Mitigation |
|---------|----------------|---------------------|
| Prompt injection through lexical/highlight context | Tampering / LLM01 | Bound and redact context, delimit it as untrusted data, reject identity/policy assignments, validate output locally, and give the model no approval authority. [VERIFIED: `text_generation.py`; OWASP LLM01] |
| Sensitive information disclosure | Information Disclosure / LLM02 | No secrets/private paths/excerpts/prompts/responses/raw analyzer dumps in telemetry; use hashes and controlled summaries only. [VERIFIED: `32-APPROACH.md`; OWASP LLM02] |
| Unsafe downstream handling of generated HTML/SSML | Tampering / LLM05 | Strict schemas, contextual escaping, allowlisted definition markup, trusted SSML templates, and no generated paths/SQL/commands. [VERIFIED: OWASP LLM05; ASVS V1] |
| Hallucinated sense, register, source, or approval | Spoofing/Tampering / LLM09 | Source-backed immutable identity, deterministic morphology/quality gates, and qualified exact-hash review. [VERIFIED: `32-APPROACH.md`; OWASP LLM09] |
| Cost/resource exhaustion | Denial of Service / LLM10 | Exactly two candidates, one repair, bounded transport retries, task token/cost/latency/batch ceilings, rate limits, and stop-on-budget drift. [VERIFIED: `32-APPROACH.md`; OWASP LLM10; ASVS V2.4.1] |
| Path traversal or symlink/TOCTOU substitution | Tampering/Elevation | Fixed roots and relative roles, reject `..`/absolute paths, no-follow exact reads, before/opened/after identity checks, and atomic replacement. [VERIFIED: Phase 31 code; ASVS V5.3.2/V15.4.2] |
| SSRF/unapproved outbound endpoint | Spoofing/Information Disclosure | Fixed provider adapters and endpoint allowlists; CLI accepts no arbitrary provider URL or source URL. [VERIFIED: `32-PATTERNS.md`; ASVS V13.2.4/V13.2.5] |
| Artifact/catalog/review tampering or replay | Tampering | Bind raw bytes and canonical metadata/policy hashes; reject stale profile, bundle, analyzer, request, or review versions. [VERIFIED: `32-APPROACH.md`; ASVS V11.4.3] |
| Secret leakage | Information Disclosure | Environment/secret-manager configuration, least privilege, no source/build/log inclusion, and content-free credential failures. [VERIFIED: ASVS V13.3.1/V13.3.2; repository settings pattern] |
| Hidden provider/voice fallback | Spoofing/Repudiation | One pinned route, explicit fallback=`none` for final Korean, per-attempt route telemetry, and final fallback gate. [VERIFIED: `32-APPROACH.md`] |
| Log injection or raw exception leakage | Tampering/Information Disclosure | Controlled enums, bounded redacted summaries, encoded output, no `str(exc)` or provider cancellation payload without sanitization. [VERIFIED: ASVS V16.4.1/V16.5.1; `32-APPROACH.md`] |

### Required Security Verification

- Mutation-test path traversal, absolute paths, Windows drives/reparse points, symlinks, changed inode/size, oversized members, undeclared files, and pointer drift. [VERIFIED: Phase 31 security precedent]
- Mutation-test prompt injection and provider fields attempting to overwrite lemma/POS/sense/fingerprint/approval. [VERIFIED: existing Korean request sanitizer; OWASP LLM01]
- Scan telemetry/report/cache-key rows for source text, prompts, responses, private excerpts, local paths, credentials, raw analyzer output, and tracebacks. [VERIFIED: `32-APPROACH.md`; OWASP LLM02]
- Assert outbound boundaries are fixed and every automated test fails if network or real credentials are touched. [VERIFIED: `32-APPROACH.md`; ASVS V13.2.4]
- Assert provider text cannot emit active HTML/SSML beyond the allowlisted contract. [VERIFIED: OWASP LLM05; ASVS V1.2.1]
- Assert budget, candidate, repair, retry, batch, and concurrency limits on every live-capable route. [VERIFIED: OWASP LLM10; `32-APPROACH.md`]

## Sources

### Primary (HIGH confidence)

- [Context7 `/pydantic/pydantic`](https://context7.com/pydantic/pydantic) — strict mode, `ConfigDict`, frozen models, extra fields, validation.
- [Pydantic documentation](https://docs.pydantic.dev/latest/concepts/strict_mode/) — strict validation behavior.
- [Context7 `/bab2min/kiwipiepy`](https://context7.com/bab2min/kiwipiepy) — `Kiwi.analyze`, `top_n`, morphology options.
- [Context7 `/berriai/litellm`](https://context7.com/berriai/litellm) and [LiteLLM structured output](https://docs.litellm.ai/docs/completion/json_mode) — response format, usage, and completion cost.
- [Context7 `/deepl/deepl-python`](https://context7.com/deepl/deepl-python) and [DeepL supported languages](https://developers.deepl.com/docs/getting-started/supported-languages) — `translate_text`, `KO`, and target variant `PT-BR`.
- [Azure Speech REST reference](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech#get-a-list-of-voices) — voice-list auth, regional/resource inventory fields, output formats, errors.
- [Azure language/voice support](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts) — `ko-KR` TTS support and region-specific discovery guidance.
- [Azure SSML voice documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice) — voice, locale, style, and prosody structure.
- [Context7 `/kerrickstaley/genanki`](https://context7.com/kerrickstaley/genanki) — explicit deck IDs, package list, media.
- [Anki manual: decks](https://docs.ankiweb.net/getting-started.html#decks) — `::` hierarchy semantics.
- [Context7 `/websites/sqlalchemy_en_20`](https://context7.com/websites/sqlalchemy_en_20) — typed declarative and nullability.
- [Context7 `/websites/alembic_sqlalchemy`](https://context7.com/websites/alembic_sqlalchemy) — reversible add/drop-column migrations.
- [Unicode UAX #15](https://unicode.org/reports/tr15/) — NFC and Hangul canonical equivalence.
- [Python `os.replace`](https://docs.python.org/3/library/os.html#os.replace), [pathlib](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve), and [hashlib](https://docs.python.org/3/library/hashlib.html) — atomic replacement, path resolution, SHA-256.
- [OWASP ASVS 5.0.0](https://github.com/OWASP/ASVS/tree/v5.0.0/5.0) — current security categories and controls.
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/) — LLM01, LLM02, LLM05, LLM09, and LLM10.
- PyPI JSON registry queries on 2026-08-21 — current package versions and release upload dates.

### Project-Primary (HIGH confidence)

- `.planning/phases/32-frequency-portuguese-text-and-audio/32-APPROACH.md` — user-confirmed scope, decisions, checkpoints, and claim limits.
- `.planning/phases/32-frequency-portuguese-text-and-audio/32-FREQUENCY-SOURCE-DECISION.md` and the [official NIKL text-source page](https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=70) — selected rank/identity path and remaining exact-artifact/redistribution gates; the official text variant avoids a new legacy-Excel parser dependency.
- `.planning/phases/32-frequency-portuguese-text-and-audio/32-PATTERNS.md` — repository analogs and direct implementation gaps, except its superseded Phase-34-only subdeck assumption.
- `.planning/SPEC.md`, `.planning/ROADMAP.md`, `AGENTS.md` — requirements and project constraints.
- Phase 30 Korean domain/morphology implementation and Phase 31 immutable snapshot/media/review implementation — exact in-repo precedents.
- Inspected frequency, lexical, text, provider, audio, persistence, export, runtime, migration, and test modules listed throughout this research.

### Secondary (MEDIUM confidence)

- None used for locked technical claims; no community-only recommendation was necessary.

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**

- Standard stack: **HIGH** — installed versions, current PyPI versions, official APIs, and repository usage were verified directly.
- Architecture: **HIGH** — derived from user-confirmed decisions and concrete repository seams/gaps.
- Persistence/export patterns: **HIGH** — existing Alembic parity, Phase 31 atomic snapshot code, genanki documentation, and local multi-deck experiments agree.
- Pitfalls/security: **HIGH** — most are direct code gaps or user-locked failure boundaries, cross-checked with OWASP ASVS/LLM controls.
- Learner-ready content/source/voice facts: **MEDIUM/blocked** — the implementation path is clear, but the exact legal, linguistic, provider, reviewer, and live-Azure evidence is intentionally absent.

**Research date:** 2026-08-21

**Valid until:** 2026-08-28 for provider catalogs/package currency; 2026-09-20 for stable architecture and repository patterns. Recheck PyPI, LiteLLM/DeepL/Azure docs, and the live Azure catalog before any authorized live run.
