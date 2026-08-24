# Phase 31: Hangul and Pronunciation i+1 - Research

**Researched:** 2026-08-04; execution-gate resolutions updated 2026-08-23
**Domain:** Korean orthography and phonology curricula, reviewed foundation media, and deterministic Anki export
**Confidence:** MEDIUM

## Summary

Phase 31 should be implemented as an isolated, frozen foundation-content path: versioned JSON manifests enter Pydantic contracts, Unicode and dependency-graph validators recompute curriculum evidence, independent review/media gates fail closed, and a dedicated exporter emits the two Korean foundation families. It should not enter the modern frequency/job runtime, create a database migration, choose a production Korean voice, or synthesize media while exporting. This matches the repository's Latin source/review/audio/export boundary while reusing only the visual mechanics of the kana and shared phoneme layouts. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:45-66,528-632`]

The core implementation challenge is not Hangul composition itself; Unicode defines deterministic modern Hangul composition, and Python provides normalization directly. The hard part is proving that every strict note has one atomic target concept, every other observed/active concept is already known and explicitly declared, normative and surface pronunciation are not conflated, and the exact reviewed media bytes survive APKG/CSV/TSV output. [CITED: https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/#G24646] [VERIFIED: `.planning/SPEC.md:45-53,77-112`; `KOREAN-STRUCTURE.md:41-75,115-175,410-452`]

`31-APPROACH.md` now records the user-confirmed assisted-curation amendment: AI may prepare bounded hash-bound drafts, while qualified Korean/Portuguese review, rights, exact-byte playback, receipt, activation, and observed Anki acceptance remain separate authorities. The controlling inputs are the active SPEC, ROADMAP, approved Korean structure, Phase 30 judgment, this approach amendment, and project instructions. Learner-ready completion remains blocked on genuine licensed media and exact qualified evidence; tests, drafts, or fake providers cannot manufacture those approvals. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-APPROACH.md:6-40`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:7-16`; `.planning/SPEC.md:20-25`; `KOREAN-STRUCTURE.md:168-175,423-452`]

**Primary recommendation:** Build one shared Korean concept registry and strict validator, two frozen family manifests, independent review/media manifests, a Korean-owned Hangul template, a language-neutral extraction of the existing phoneme model mechanics, and a dedicated all-format foundation exporter; stop at explicit human checkpoints until the exact content and media hashes are approved. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:45-66,878-891`]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|---|---|---|---|
| Modern-jamo identity, NFC, block composition | API / Backend domain | — | Pure deterministic domain logic belongs beside the existing Korean contracts, not in templates or Anki. [VERIFIED: `src/multilang/domain/korean.py:99-167`] |
| Concept graph and strict-i+1 validation | API / Backend service | Database / Storage manifests | The service recomputes evidence from versioned source data; source files do not self-certify. [VERIFIED: `.planning/SPEC.md:97-103`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:230-239`] |
| Hangul/pronunciation source inventory | Database / Storage | API / Backend validation | Frozen UTF-8 JSON is the auditable source of truth, loaded through typed contracts. [VERIFIED: `src/multilang/services/latin_source_pack.py`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:174-223`] |
| Content, translation, curriculum, media, and audio approval | API / Backend review service | Human review boundary | Code verifies status, provenance, and hashes; qualified humans supply linguistic and playback judgments. [VERIFIED: `src/multilang/services/latin_review.py:56-156`; `KOREAN-STRUCTURE.md:423-452`] |
| Media bytes and provenance | Database / Storage | API / Backend validation | Repository-relative assets and manifests are validated for containment, exact bytes, and approved identity before export. [VERIFIED: `src/multilang/services/latin_audio.py:59-95,164-254`; `KOREAN-STRUCTURE.md:382-408`] |
| Hangul/phoneme rendering | Anki client | API / Backend template construction | Backend freezes fields/templates; actual Anki rendering and playback are client behavior requiring later observed evidence. [CITED: https://docs.ankiweb.net/importing/packaged-decks.html] [VERIFIED: `.planning/ROADMAP.md:97-107`] |
| APKG, CSV, and TSV assembly | API / Backend exporter | Anki client / filesystem | `genanki` writes APKG; Python `csv` writes tables; Anki consumes basenames and sound tags. [CITED: https://github.com/kerrickstaley/genanki] [CITED: https://docs.ankiweb.net/importing/text-files.html#importing-media] |
| Azure voice discovery/synthesis | External Azure service | API / Backend adapter | Azure currently documents `ko-KR`, but production voice qualification belongs to Phase 32 and paid/live calls require approval. [CITED: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts] [VERIFIED: `.planning/SPEC.md:61,148,154`] |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|---|---|---|
| KHAN-01 | Curated Hangul foundations with modern jamo, block construction, stroke order, mnemonics, reviewed audio, Korean note identity, fonts, and complete media. [VERIFIED: `.planning/SPEC.md:47`] | Modern-inventory invariants, display/canonical-jamo boundary, Hangul schema, media/review gates, dedicated model IDs, and template leakage checks are specified below. [VERIFIED: this research] |
| KHAN-02 | Explicit bootstrap followed by exactly-one-unknown orthographic notes with stored prerequisite/observed/target evidence and NFC output. [VERIFIED: `.planning/SPEC.md:48`] | The bootstrap contract, concept registry, recomputation algorithm, H0-H10 coverage map, and negative-test matrix are specified below. [VERIFIED: this research] |
| KPRO-01 | Korean pronunciation deck using the exact shared nine-field phoneme contract, with all fields/media surviving APKG/CSV/TSV. [VERIFIED: `.planning/SPEC.md:52`] | Exact field order, richer non-rendered source model, shared model extraction, media bundles, and archive/tabular inspection are specified below. [VERIFIED: this research] |
| KPRO-02 | Strict dependency-ordered pronunciation curriculum covering onset contrasts through connected speech, with one new concept and all other active rules declared as prerequisites. [VERIFIED: `.planning/SPEC.md:53`] | P0-P13 concept families, active-rule accounting, ordering-relation targets, graph checks, and human phonetics gates are specified below. [VERIFIED: this research] |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Use Python as the primary runtime; the project baseline is Python 3.12 with `uv`, Pydantic v2, `genanki`, and pytest. Do not introduce a JS backend or an unrelated orchestration framework. [VERIFIED: `AGENTS.md`, Technology Stack]
- Keep Korean identity `ko`; use `ko-KR` only for provider/locale contracts. Normalize canonical Korean content to NFC and keep morphology-aware, fail-closed behavior. [VERIFIED: `AGENTS.md`, Project Constraints; `src/multilang/domain/korean.py:19-22,109-120`]
- Korean foundations must include Hangul, strict-i+1 pronunciation, reviewed media, tests, and fallbacks without weakening existing language paths. [VERIFIED: `AGENTS.md`, Project Constraints]
- Preserve requested field sets and formatting because Anki usefulness depends on stable schema. [VERIFIED: `AGENTS.md`, Project Constraints]
- Do not use Tatoeba as the default sentence source, do not treat ungrounded LLM output as lexical/pronunciation truth, and prefer Azure only after required voices are qualified. [VERIFIED: `AGENTS.md`, Technology Stack and Project Constraints]
- Do not commit redistributed assets until source, attribution, and redistribution rights are approved; the Korean 3000-entry licensing gate remains Phase 32 and must not leak into this phase. [VERIFIED: `AGENTS.md`, Project Constraints; `.planning/SPEC.md:23,57-59,136`]
- Before roadmap work, read SPEC, ROADMAP, config, and relevant phase artifacts; stay in approved scope; verify artifacts are substantive and wired; research unfamiliar APIs from real docs. [VERIFIED: `AGENTS.md`, GSDD Governance]
- Keep vendor-specific workflow syntax out of core application workflows and follow repository conventions before advisory Git settings. [VERIFIED: `AGENTS.md`, GSDD Governance]
- Start file-changing work through a GSD workflow; the Phase 31 phase operation was initialized before this artifact was written. [VERIFIED: `AGENTS.md`, GSD Workflow Enforcement; `gsd-tools init phase-op 31` output on 2026-08-04]
- Conventions and architecture are not globally established; follow the concrete analogs already present in the codebase. [VERIFIED: `AGENTS.md`, Conventions and Architecture]

## Standard Stack

### Core

| Library / facility | Version | Purpose | Why Standard Here |
|---|---|---|---|
| Python | 3.12 baseline (`>=3.12`) | Runtime and standard-library algorithms | Project contract; `unicodedata`, `graphlib`, `json`, `csv`, `hashlib`, `pathlib`, `zipfile`, and `sqlite3` cover the deterministic core. [VERIFIED: `pyproject.toml:10`; `AGENTS.md`, Technology Stack] |
| Pydantic | Keep locked 2.12.5; project range `>=2.11,<3`; registry current 2.13.4 published 2026-05-06 | Frozen manifest/domain validation and cross-field invariants | Existing Korean contracts use `ConfigDict(extra="forbid", frozen=True)` and model validators; no phase-scoped upgrade is needed. [VERIFIED: `src/multilang/domain/korean.py:99-106`; Context7 `/pydantic/pydantic`; PyPI JSON fetched 2026-08-04] |
| `unicodedata` | Python stdlib | NFC checks and canonical normalization | Python exposes `normalize()` and `is_normalized()`; use NFC, not blanket NFKC. [CITED: https://docs.python.org/3.12/library/unicodedata.html] |
| `graphlib.TopologicalSorter` | Python stdlib since 3.9 | Cycle detection and prerequisite ordering | It accepts a node-to-predecessors graph and raises `CycleError` when a complete order is impossible. [CITED: https://docs.python.org/3.12/library/graphlib.html] |
| genanki | 0.13.1 installed/current, published 2023-11-12 | Dedicated note models, decks, packages, and media | It is already used by all project exporters and documents fixed unique model/deck IDs, stable GUIDs, and package media. [VERIFIED: `pyproject.toml:28`; Context7 `/kerrickstaley/genanki`; PyPI JSON fetched 2026-08-04] |
| pytest | Keep project-compatible 8.4.2; project range `<9`; registry current 9.1.1 published 2026-06-19 | Unit, contract, archive, and integration checks | Existing infrastructure is configured in `pyproject.toml`; upgrading to 9.x is unrelated scope. [VERIFIED: `pyproject.toml:43-57`; environment probe and PyPI JSON on 2026-08-04] |

### Supporting

| Library / facility | Version | Purpose | When to Use |
|---|---|---|---|
| Typer | Existing project range `>=0.12,<1.0` | Thin local export/review commands | Use enum-constrained family/format options; do not accept arbitrary module/template paths. [VERIFIED: `pyproject.toml:12`; `src/multilang/cli.py`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:636-667`] |
| zstandard | 0.25.0 installed; project range `>=0.22,<1.0` | Existing Anki package inspection compatibility | Reuse existing readers/tests when an Anki package contains zstd-compressed members; do not write a new decompressor. [VERIFIED: `pyproject.toml:29`; `src/multilang/services/japanese_kana_deck.py:117-204`; environment probe] |
| Azure Speech SDK | 1.49.1 installed; range `>=1.49,<2`; registry current 1.51.1 published 2026-07-25 | Existing provider adapter only | Do not invoke it in Phase 31 export. Store provider metadata only for already-created, reviewed assets; live voice qualification is Phase 32. [VERIFIED: `pyproject.toml:27`; environment/PyPI probes; `.planning/SPEC.md:61,148,154`] |
| Python `wave` + SHA-256 | Stdlib | Offline duration/header/hash checks for PCM WAV foundation recordings | Prefer reviewed PCM WAV for new human foundation recordings so duration and byte integrity remain testable without missing `ffprobe`; existing Latin export proves WAV media is supported by the project path. [VERIFIED: `src/multilang/services/latin_export.py:259-278`; environment probe found `ffprobe` missing] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff / Decision |
|---|---|---|
| Stdlib Hangul/NFC logic | `jamo`, `hangul-jamo`, or custom G2P libraries | Do not add them. Unicode/Python already cover identity and composition, while pronunciation approval remains source-backed and human-reviewed. [CITED: https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/#G24646] [VERIFIED: `.planning/SPEC.md:149,155`] |
| Frozen manifests | Database-backed foundation jobs | Do not add a migration. Phase requirements need auditable curated inventories, not concurrent runtime generation. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:800-813`] |
| Korean-owned Hangul template | Parameterizing the Japanese template | Copy structural layout only; Korean labels/classes/fonts and IDs must remain isolated, and Japanese remains a regression oracle. [VERIFIED: `.planning/SPEC.md:47`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:459-524`] |
| Frozen reviewed media | Live export-time Azure synthesis | Prohibited for this phase: raw glyphs are not phonemes, provider success is not review, and failures may not become blank audio. [VERIFIED: `KOREAN-STRUCTURE.md:168-175`; `src/multilang/services/russian_phoneme_deck.py:327-418`] |
| Dedicated foundation exporter | Extending generic modern exporters | Keep the two richer foundation schemas out of existing job rows and modern runtime paths; Phase 34 can unify milestone evidence later. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:528-632`] |

**Installation:** no dependency change is recommended. [VERIFIED: all required core libraries are installed or in the standard library]

```bash
uv sync --extra dev
```

**Version verification:** [VERIFIED: environment and PyPI JSON probes on 2026-08-04]

```text
installed: uv 0.11.14; Python 3.13.7; pydantic 2.12.5; pytest 8.4.2;
           genanki 0.13.1; azure-cognitiveservices-speech 1.49.1
registry:  pydantic 2.13.4 (2026-05-06); pytest 9.1.1 (2026-06-19);
           genanki 0.13.1 (2023-11-12); Azure Speech SDK 1.51.1 (2026-07-25)
```

## Architecture Patterns

### System Architecture Diagram

```text
Operator CLI
    |
    v
Frozen concept registry + Hangul source pack + pronunciation source pack
    |
    v
UTF-8 JSON parse -> Pydantic schema validation -> Korean NFC/script validation
    |                                      |
    | invalid                              | valid
    v                                      v
fail closed                        prerequisite DAG / stage coverage
                                           |
                                           v
                           recompute known, observed, active, unknown
                              | false i+1            | valid i+1
                              v                      v
                         fail closed        curation/review manifests
                                                     |
                                                     v
                                      media path + exact-byte hash checks
                                         | blocked          | approved
                                         v                  v
                                    fail closed       learner export rows
                                                            |
                          +---------------------------------+------------------+
                          v                                 v                  v
                    genanki APKG                      UTF-8 CSV           UTF-8 TSV
                    + media bytes                  + media bundle      + media bundle
                          |                                 |                  |
                          +----------------+----------------+------------------+
                                           v
                              ZIP/SQLite/table/reference audit
                                           |
                              +------------+-------------+
                              v                          v
                    automated structure proof   human linguistic/playback proof
```

The primary branch must fail before creating an output path whenever source, graph, review, or media validation fails. [VERIFIED: `src/multilang/services/latin_export.py:130-192,259-278`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:758-783`]

### Recommended Project Structure

```text
src/multilang/
├── domain/korean.py                         # extend frozen concept/evidence contracts
├── services/korean_curriculum.py            # load and validate graph/family packs
├── services/korean_foundation_review.py     # independent review readiness
├── services/korean_foundation_media.py      # paths, hashes, exact reviewed bytes
├── services/phoneme_deck.py                 # language-neutral nine-field mechanics
├── services/russian_phoneme_deck.py         # wrappers; preserve existing behavior
├── services/korean_foundation_export.py     # APKG/CSV/TSV for both families
├── templates/korean_hangul_card.md           # Korean-owned kana-derived layout
└── cli.py                                    # thin, enum-constrained local commands
data/korean_foundations/
├── korean-concepts-v1.json
├── hangul-v1.json
├── pronunciation-i-plus-1-v1.json
├── korean-foundations-v1-curation.json
├── korean-foundations-v1-media.json
└── media/korean-foundations-v1/              # approved repository-relative bytes
tests/
├── domain/test_korean.py
├── services/test_korean_curriculum.py
├── services/test_korean_foundation_review.py
├── services/test_korean_foundation_media.py
├── services/test_phoneme_deck.py
├── services/test_korean_foundation_export.py
├── cli/test_korean_foundation_commands.py
└── integration/test_korean_foundations_flow.py
```

This structure follows the mapped repository analogs and intentionally leaves runtime, DB models, generic modern exporters, Japanese source/template files, frequency assets, and the Korean production voice registry untouched. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:68-105,800-813`]

### Pattern 1: Frozen Source Records, Not Python Tuples

**What:** Store concept, Hangul, and pronunciation records in versioned UTF-8 JSON; load them through frozen Pydantic models with `extra="forbid"`, bounded fields, and cross-field validators. [VERIFIED: `src/multilang/domain/korean.py:99-106`; Context7 `/pydantic/pydantic`]
**When to use:** For every curriculum, review, translation, and media input. [VERIFIED: the Latin source/review/audio path uses this boundary at `src/multilang/services/latin_source_pack.py`, `latin_review.py`, and `latin_audio.py`]

```python
# Source: Context7 /pydantic/pydantic and src/multilang/domain/korean.py:99-106
class KoreanConcept(_FrozenContract):
    id: str
    domain: Literal["orthography", "phonology"]
    prerequisite_ids: tuple[str, ...] = ()
    sequence: int = Field(ge=1)


class KoreanCurriculumEvidence(_FrozenContract):
    target_concept_id: str
    prerequisite_concept_ids: tuple[str, ...]
    observed_concept_ids: tuple[str, ...]
    unknown_concept_ids: tuple[str, ...]
    policy: Literal["strict", "adaptive", "contextual"]
```

Keep source records richer than learner fields. Source records also need stable item key, family/stage, sequence, source-pack version, source citations, active rule IDs, content hash, and review/media joins. [VERIFIED: `.planning/SPEC.md:77-112`; `KOREAN-STRUCTURE.md:117-131`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:174-239`]

### Pattern 2: One Registry and Recomputed Strict Evidence

**What:** Both families reference one concept registry. The loader validates IDs, predecessor existence, acyclicity, stage order, and prerequisite closure, then recomputes unknowns; serialized `unknown_concept_ids` are evidence to compare, not trusted input. [CITED: https://docs.python.org/3.12/library/graphlib.html] [VERIFIED: `.planning/SPEC.md:97-103`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:230-239`]
**When to use:** Before any review-readiness or export check. Approval status cannot rescue invalid source evidence. [VERIFIED: `src/multilang/services/latin_review.py:145-202`]

For entry `n`, compute `known_before` from explicitly completed bootstrap targets plus all prior validated targets, compute `unknown = observed - known_before`, and require all of the following for `policy="strict"`: [VERIFIED: `KOREAN-STRUCTURE.md:41-62`; `.planning/SPEC.md:47-53`]

```text
target in observed
serialized unknown == recomputed unknown
recomputed unknown == {target}
prerequisite_ids subset known_before
all active non-target rule IDs are explicitly listed in prerequisite_ids
every prerequisite has lower sequence or belongs to the completed bootstrap
```

Use an explicit ordered `bootstrap_concept_ids` plus `strict_start_sequence`; require H0 entry targets to equal the bootstrap list exactly. Keep the SPEC policy enum unchanged: H0 is a named curriculum section, and each H0 note can still satisfy strict one-unknown accounting in its own sequence. [VERIFIED: `.planning/SPEC.md:48,97-103`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:232-238`]

### Pattern 3: Canonical Machine Jamo, Reviewed Display Jamo

**What:** Machine identity uses modern conjoining Jamo by position; standalone learner display may use explicitly mapped Compatibility Jamo. Never pass the display glyph through lexical `canonicalize_korean()`, never silently NFKC-fold it, and never admit halfwidth Hangul. [CITED: https://www.unicode.org/reports/tr15/] [VERIFIED: `src/multilang/domain/korean.py:49-50,109-120`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:39-44`]
**When to use:** Every standalone jamo and coda-position source record. [VERIFIED: `KOREAN-STRUCTURE.md:97-113`]

Recommended pedagogical mapping fields are `display_glyph`, `canonical_jamo`, `jamo_position`, `unicode_name`, and `mapping_review_status`. The same display consonant can map to a choseong or jongseong identity depending on position, so the mapping must be positional rather than inferred with NFKC. [CITED: https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/#G24646]

### Pattern 4: Normative, Surface, and IPA Are Separate Evidence

**What:** Preserve canonical spelling, normative bracketed pronunciation, reviewed surface realization, optional IPA, active rule IDs, register/context, and review status as distinct source fields. [VERIFIED: `.planning/SPEC.md:105-112`; `KOREAN-STRUCTURE.md:133-175`]
**When to use:** Every pronunciation entry and every sound-bearing Hangul entry. [VERIFIED: `.planning/SPEC.md:52-53`]

The National Institute of Korean Language standard-language rule defines modern Seoul speech as the standard baseline, and its standard-pronunciation material covers the normative processes needed by this phase. Optional colloquial reductions and rate effects must remain explicitly marked surface/register variants rather than silently replacing the normative form. [CITED: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0002] [VERIFIED: `KOREAN-STRUCTURE.md:9,147-175`]

### Pattern 5: Review and Media Are Independent, Hash-Bound Gates

**What:** Validate source semantics first, then require relevant `content`, `translation`, `curriculum`, `pronunciation`, `media_license`, and `audio_playback` gates. A learner-ready record has every applicable gate approved and every copied source/version/hash field aligned. [VERIFIED: `src/multilang/services/latin_review.py:56-156,159-202`; `KOREAN-STRUCTURE.md:423-452`]
**When to use:** Before joining any learner export row. [VERIFIED: `src/multilang/services/latin_export.py:130-192`]

For sound assets persist at least the approved metadata contract already locked in `KOREAN-STRUCTURE.md`: kind, `language=ko`, `locale=ko-KR` only where provider-relevant, display/spoken/NFC text, text hash, provider/version, exact voice, catalog status/time, SSML hash, output format, artifact hash, duration, repository-relative path, review status, reviewed artifact hash, reviewer role, and generation/rejection reason. Export requires `artifact_hash == reviewed_artifact_hash == SHA256(actual_bytes)`. [VERIFIED: `KOREAN-STRUCTURE.md:370-408`]

### Pattern 6: Exact Learner Schemas; Rich Evidence Stays Outside Pronunciation Notes

**Hangul note fields, in order:** [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:485-505`]

```text
SortIndex, Category, JamoOrBlock, ReadingOrName, Sound, Mnemonic,
Picture, Strokes, Gif, Audio, TargetConceptId, PrerequisiteConceptIds,
ObservedConceptIds, UnknownConceptIds, IPlusOnePolicy
```

Only pedagogical fields render; curriculum evidence remains stored but hidden. The template must use Korean-owned labels/classes and an explicit Korean-capable font stack, while static tests reject Japanese/Kana/Romaji/Hiragana/Katakana and Japanese font tokens. [VERIFIED: `.planning/SPEC.md:47`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:459-524`]

**Pronunciation note fields, exactly and in order:** [VERIFIED: `src/multilang/services/russian_phoneme_deck.py:35-45`; `.planning/SPEC.md:52`]

```text
Spellings, Sound, letter_audio, Example Word, word_audio,
Word Translation, Example Sentence, sentence_audio, Sentence Translation
```

Do not add graph, surface-pronunciation, IPA-review, or provenance fields to that note type. Keep them in the validated source/review/checksum manifests and map only the nine approved learner values during export. [VERIFIED: `KOREAN-STRUCTURE.md:117-131`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:39-43`]

### Pattern 7: Stable IDs, GUIDs, and Fail-Before-Write Export

Use these currently unused fixed constants, subject to one final global collision test: [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:570-594`]

```text
KOREAN_HANGUL_MODEL_ID        = 1_762_801_001
KOREAN_HANGUL_DECK_ID         = 1_762_801_002
KOREAN_PRONUNCIATION_MODEL_ID = 1_762_801_003
KOREAN_PRONUNCIATION_DECK_ID  = 1_762_801_004
```

Use deck names `Multilang Korean::Foundations::Hangul` and `Multilang Korean::Foundations::Pronunciation i+1`. Generate a 32-hex SHA-256 GUID from immutable family, source-pack version, and item key; do not hash mutable translation, mnemonic, media filename, template, or Python's process-random `hash()`. [VERIFIED: `KOREAN-STRUCTURE.md:17-28`; `src/multilang/services/latin_export.py:195-231`; Context7 `/kerrickstaley/genanki`]

Resolve all source, review, and media joins before creating output directories. APKG uses `genanki.Package.media_files`; CSV/TSV use UTF-8, `csv.writer`, Anki headers, basename-only sound/image references, and a deterministic sibling media/checksum manifest. [CITED: https://github.com/kerrickstaley/genanki] [CITED: https://docs.ankiweb.net/importing/text-files.html] [VERIFIED: `src/multilang/services/latin_export.py:259-333`]

## Curriculum Content Contract

### Modern Hangul Inventory Invariants

- Cover exactly 19 modern initial consonant identities, 21 modern vowel identities, and 27 non-empty modern final identities plus the no-final state. [CITED: https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/#G24646]
- Exhaustively test all `19 × 21 × 28 = 11,172` algorithmic modern syllable combinations, but curate representative construction cards rather than generating 11,172 learner notes. [CITED: https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/#G24646]
- Use Unicode constants `SBase=0xAC00`, `LBase=0x1100`, `VBase=0x1161`, `TBase=0x11A7`, `LCount=19`, `VCount=21`, `TCount=28`, `NCount=588`, and `SCount=11172`. [CITED: https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/#G61399]
- Cover the NIKL modern letter inventory: 24 base letters, five doubled consonants, and eleven additional compound vowels, while retaining explicit positional mappings for final clusters. [CITED: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0001]
- Cover all 27 non-empty final spellings: `ㄱ ㄲ ㄳ ㄴ ㄵ ㄶ ㄷ ㄹ ㄺ ㄻ ㄼ ㄽ ㄾ ㄿ ㅀ ㅁ ㅂ ㅄ ㅅ ㅆ ㅇ ㅈ ㅊ ㅋ ㅌ ㅍ ㅎ`. [CITED: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0001]
- Keep every canonical syllable block, Korean word, sentence, and pronunciation equal to its NFC form; NFC preserves compatibility distinctions that blind NFKC could erase. [CITED: https://www.unicode.org/reports/tr15/] [VERIFIED: `.planning/SPEC.md:40-43,47-48`]

### Prescriptive H0-H10 Coverage

Each listed family expands into atomic concept records/cards; a stage label is not itself proof of i+1. [VERIFIED: `KOREAN-STRUCTURE.md:41-75`; `.planning/SPEC.md:146`]

| Stage | Required target concept families | Completion check |
|---|---|---|
| H0 | Jamo as units; block as unit; onset/nucleus/optional-coda slots; vertical-vowel layout; horizontal-vowel layout. [VERIFIED: `KOREAN-STRUCTURE.md:99-102`] | Explicit `bootstrap_concept_ids` equals H0 target IDs; each H0 entry still recomputes one unknown. [VERIFIED: `.planning/SPEC.md:48`] |
| H1 | Basic vowels `ㅏ ㅓ ㅗ ㅜ ㅡ ㅣ`, each with display-to-canonical mapping and approved sound/context. [VERIFIED: `KOREAN-STRUCTURE.md:102`] | Six unique vowel identities; required strokes/mnemonic/audio manifest entries resolve. [VERIFIED: `.planning/SPEC.md:47`] |
| H2 | Null onset `ㅇ`; block composition with known vertical and horizontal vowels. [VERIFIED: `KOREAN-STRUCTURE.md:103`] | Composition examples decompose back to declared L/V(/T), and every output is NFC. [CITED: https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/#G59688] |
| H3 | Basic onsets `ㄴ ㅁ ㄹ ㄱ ㄷ ㅂ ㅈ ㅅ ㅎ`. [VERIFIED: `KOREAN-STRUCTURE.md:104`] | Nine unique choseong mappings; cards do not pretend a raw isolated glyph is a context-free phoneme. [VERIFIED: `KOREAN-STRUCTURE.md:168-175`] |
| H4 | Iotized/orthographic vowels `ㅑ ㅕ ㅛ ㅠ ㅐ ㅔ ㅒ ㅖ`. [VERIFIED: `KOREAN-STRUCTURE.md:105`] | Eight unique identities; cumulative vowel coverage is 14. [VERIFIED: `KOREAN-STRUCTURE.md:102,105`] |
| H5 | Aspirated `ㅋ ㅌ ㅍ ㅊ` and tense `ㄲ ㄸ ㅃ ㅆ ㅉ` onset spellings. [VERIFIED: `KOREAN-STRUCTURE.md:106`] | Nine new onset identities; cumulative modern-onset coverage is 19. [CITED: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0001] |
| H6 | Compound vowels `ㅘ ㅝ ㅙ ㅞ ㅚ ㅟ ㅢ`. [VERIFIED: `KOREAN-STRUCTURE.md:107`] | Seven unique identities; cumulative modern-vowel coverage is 21. [CITED: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0001] |
| H7 | Batchim position and seven pedagogical coda output categories `[ㄱ ㄴ ㄷ ㄹ ㅁ ㅂ ㅇ]`. [VERIFIED: `KOREAN-STRUCTURE.md:108`] | Coda-position concepts are distinct from onset identity; P2 references the same shared concepts rather than duplicating IDs. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:880-882`] |
| H8 | All alternative singleton coda spellings and eleven complex final clusters. [VERIFIED: `KOREAN-STRUCTURE.md:109`] | Exact 27-final coverage, unique positional conjoining-jamo identity, and no forward phonological claims. [CITED: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0001] |
| H9 | Morpheme-preserving spelling; basic word spacing; attached-particle spacing; only the smallest reviewed orthographic rules needed by examples. [VERIFIED: `KOREAN-STRUCTURE.md:109-110`; NIKL orthography principles at the cited source] | Every example declares observed orthography/grammar concepts; grammar beyond foundation remains Phase 33. [VERIFIED: `.planning/ROADMAP.md:85-95`] |
| H10 | NFC/NFD equivalence; Korean keyboard orientation; punctuation; numerals; bounded mixed-script text. [VERIFIED: `KOREAN-STRUCTURE.md:111`] | NFC/NFD goldens deduplicate; compatibility and halfwidth forms fail; mixed text cannot bypass canonical checks. [VERIFIED: `src/multilang/domain/korean.py:109-120`; `.planning/SPEC.md:42`] |

Traditional jamo names should appear only after their written forms are decodable from prior orthographic concepts. Early audio should use an approved pedagogical spoken form or explicit syllable/coda context rather than sending a raw display glyph to TTS. [VERIFIED: `KOREAN-STRUCTURE.md:113,168-175`]

### Prescriptive P0-P13 Coverage

Each pronunciation record must cite the normative source rule/example where applicable, declare all active rule IDs, and receive Korean-phonetics review. The examples below are approved curriculum seeds from the project structure, not automatic proof that an implementation's exact IPA or surface transcription is correct. [VERIFIED: `KOREAN-STRUCTURE.md:133-175`; `.planning/SPEC.md:155`]

| Stage | Required atomic concept families | Seed evidence / gate |
|---|---|---|
| P0 | Syllable timing; reviewed vowel qualities; null onset; sonorants; intervocalic versus coda `ㄹ`. [VERIFIED: `KOREAN-STRUCTURE.md:151`] | Orthographic concepts are inherited from the approved Hangul pack; each phonological target remains one unknown. [VERIFIED: `.planning/SPEC.md:53`] |
| P1 | Separate onset contrast concepts for `ㅂ/ㅃ/ㅍ`, `ㄷ/ㄸ/ㅌ`, `ㄱ/ㄲ/ㅋ`, `ㅈ/ㅉ/ㅊ`, `ㅅ/ㅆ`, and `ㅎ`. [VERIFIED: `KOREAN-STRUCTURE.md:152`] | Do not teach these as a simple English-style voiceless/voiced opposition; exact phonetic descriptions require specialist approval. [VERIFIED: `KOREAN-STRUCTURE.md:166`] |
| P2 | Unreleased coda behavior and each of the seven coda-neutralization/output categories. [VERIFIED: `KOREAN-STRUCTURE.md:153`] | Normative spelling-to-pronunciation mappings cite NIKL; H7/H8 orthographic positional concepts are prerequisites. [CITED: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0002] |
| P3 | Liaison/resyllabification before a vowel-initial dependent morpheme. [VERIFIED: `KOREAN-STRUCTURE.md:154`] | Curated seeds include `옷이 [오시]` and `먹어 [머거]`; morphology/boundary is explicit. [VERIFIED: `KOREAN-STRUCTURE.md:154`] |
| P4 | Post-obstruent tensification, split into reviewed environments if they differ pedagogically. [VERIFIED: `KOREAN-STRUCTURE.md:155`] | Curated seeds include `먹다 [먹따]`, `학교 [학꾜]`. [VERIFIED: `KOREAN-STRUCTURE.md:155`] |
| P5 | Velar, coronal, and labial nasalization environments as atomic mappings. [VERIFIED: `KOREAN-STRUCTURE.md:156`] | Curated seeds include `국물 [궁물]`, `받는 [반는]`, `앞문 [암문]`. [VERIFIED: `KOREAN-STRUCTURE.md:156`] |
| P6 | Aspiration involving `ㅎ`, with direction/environment represented explicitly. [VERIFIED: `KOREAN-STRUCTURE.md:157`] | Curated seeds include `좋다 [조타]`, `입학 [이팍]`; exact active rules are prerequisites. [VERIFIED: `KOREAN-STRUCTURE.md:157`] |
| P7 | `ㄷ`- and `ㅌ`-palatalization in the licensed morphological environment. [VERIFIED: `KOREAN-STRUCTURE.md:158`] | Curated seeds include `굳이 [구지]`, `같이 [가치]`; NIKL orthography explicitly illustrates these alternations. [CITED: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0001] |
| P8 | Liquid assimilation/related `ㄹ` processes and `ㄴ` insertion as separate targets. [VERIFIED: `KOREAN-STRUCTURE.md:159`] | Do not collapse several environments into one catch-all concept; each source record requires a normative citation and review. [CITED: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0002] |
| P9 | Complex-coda selection and alternation by following environment/morpheme boundary. [VERIFIED: `KOREAN-STRUCTURE.md:160`] | Contrast seed `읽다 [익따]` versus `읽어 [일거]`; active neutralization/tensification/liaison rules are declared. [VERIFIED: `KOREAN-STRUCTURE.md:160`] |
| P10 | Regular contraction concepts `보아요→봐요`, `주어요→줘요`, `되어요→돼요`, `하여요→해요`. [VERIFIED: `KOREAN-STRUCTURE.md:161`] | Each contraction family is one target; constituent orthography and morphology remain prerequisites. [VERIFIED: `.planning/SPEC.md:53`] |
| P11 | Curated optional conversational reductions, each marked by register and context. [VERIFIED: `KOREAN-STRUCTURE.md:162`] | No unreviewed reduction list was approved in this session; source records remain blocked until specialist/native review. [VERIFIED: research source audit, 2026-08-04] |
| P12 | Phrase accent, focus, boundary intonation, and rate-conditioned effects as separate auditory concepts. [VERIFIED: `KOREAN-STRUCTURE.md:163`] | Text-only assertions are insufficient; contrastive reviewed recordings and playback review are mandatory. [VERIFIED: `KOREAN-STRUCTURE.md:168-175,446-452`] |
| P13 | Cumulative rule interaction and ordering relations, each relation itself the one new target. [VERIFIED: `KOREAN-STRUCTURE.md:164`] | Do not label an all-known review card i+1; target an explicit ordering concept while all participating rules are prerequisites. [VERIFIED: `.planning/SPEC.md:53`] |

### Portuguese and Learner-Field Policy

Use translation language code `pt`, matching the existing frozen Portuguese translation contract; do not introduce a second regional identity in Phase 31. Store separate short word translation and full sentence translation, align them to the exact source word/sentence, block English/provider-error leakage, and require human approval for naturalness and sense. [VERIFIED: `src/multilang/services/latin_translation_quality.py:74-108,147-241`; `KOREAN-STRUCTURE.md:9-15,360-369`]

`Sound` should render a reviewed pedagogical sound representation derived from the source evidence. IPA remains optional; if present, it must be consistent in transcription policy and specialist-approved. The Azure phonetic-set page documents Korean IPA support for SSML but does not make generated IPA or synthesized audio linguistically approved. [CITED: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-ssml-phonetic-sets#ko-kr] [VERIFIED: `.planning/SPEC.md:105-112,149,155`]

## Human Gates and Evidence Boundaries

| Gate | Automated proof | Required human proof | Blocking condition |
|---|---|---|---|
| Hangul inventory/orthography | Exact H0-H10, 19/21/27 coverage, NFC, mappings, graph, field/template scans. [VERIFIED: this research] | Korean orthography reviewer approves glyph mappings, names, examples, strokes, and mnemonic accuracy. [VERIFIED: `KOREAN-STRUCTURE.md:446-449`] | Missing reviewer identity/time, rejected item, or source/hash drift blocks export. [VERIFIED: `src/multilang/services/latin_review.py:145-202`] |
| Pronunciation content | Exact P0-P13 category/rule coverage, active-rule/prerequisite accounting, schema/hash checks. [VERIFIED: this research] | Korean phonetics specialist approves normative/surface/IPA/rule analysis for 100% of records. [VERIFIED: `KOREAN-STRUCTURE.md:448-450`] | G2P/LLM/provider output alone can never set `approved`. [VERIFIED: `.planning/SPEC.md:155`] |
| Portuguese | Source alignment and deterministic leakage/copy checks. [VERIFIED: `src/multilang/services/latin_translation_quality.py:147-241`] | Portuguese reviewer approves meaning, naturalness, and register. [VERIFIED: `KOREAN-STRUCTURE.md:360-369,446-452`] | Any unapproved translation blocks the joined row. [VERIFIED: `src/multilang/services/latin_export.py:155-161`] |
| Media license | Path, basename, required-kind, source fields, attribution, and SHA-256 checks. [VERIFIED: `.planning/SPEC.md:10,156`; `AGENTS.md`, Korean Licensing] | Human records reuse/redistribution decision for every non-original stroke, image, GIF, mnemonic, or recording. [VERIFIED: `AGENTS.md`, Korean Licensing and Engineering Quality] | Unknown license or absent attribution blocks committing and export. [VERIFIED: `.planning/SPEC.md:156`] |
| Audio playback | Exact spoken text/NFC/text hash/SSML hash/byte hash/duration/path and manifest agreement. [VERIFIED: `KOREAN-STRUCTURE.md:382-408`] | Pronunciation specialist plus independent native speaker approve the exact reviewed artifact hash for jamo/rule audio. [VERIFIED: `KOREAN-STRUCTURE.md:168-175`] | Raw-glyph TTS, changed bytes, changed provider/voice/SSML/prosody/text, or either missing role resets to `needs_review`. [VERIFIED: `KOREAN-STRUCTURE.md:168-175`] |
| Anki structure | ZIP/media map/SQLite model/note/deck/field/GUID/reference inspection. [VERIFIED: `tests/services/test_latin_export.py`; `tests/services/test_export_anki_package.py`] | Phase 31 may record audio playback review, but final Anki Desktop/mobile visual/import acceptance remains Phase 34. [VERIFIED: `.planning/ROADMAP.md:97-107`] | Do not claim final visual/import acceptance from static or archive tests. [VERIFIED: `.planning/SPEC.md:158`] |

Recommended tracked evidence artifacts are `31-CURRICULUM-REVIEW.md` and `31-AUDIO-PLAYBACK-REVIEW.md`, each naming exact source/media versions, reviewer roles, reviewed counts, artifact hashes, decision, and timestamp. A media manifest must separately retain license/attribution/redistribution fields for each asset. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:83-90,287-300`]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Unicode normalization | Ad-hoc combining-jamo substitutions or blanket NFKC | `unicodedata.normalize("NFC", value)` plus explicit compatibility-display mapping | NFC is canonical composition; NFKC performs compatibility transformations that can erase distinctions. [CITED: https://docs.python.org/3.12/library/unicodedata.html] [CITED: https://www.unicode.org/reports/tr15/] |
| Hangul composition | Lookup table of 11,172 syllables | Unicode composition constants/formula with exhaustive tests | Unicode specifies algorithmic decomposition/composition for modern Hangul. [CITED: https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/#G59688] |
| Cycle detection | Custom DFS with partial diagnostics | `graphlib.TopologicalSorter` plus explicit sequence checks | Stdlib detects cycles and models predecessor graphs directly. [CITED: https://docs.python.org/3.12/library/graphlib.html] |
| Manifest validation | Dict access and scattered `if` statements | Existing frozen Pydantic v2 pattern and `model_validator` | It rejects extra fields, freezes top-level models, and supports cross-field invariants. [VERIFIED: Context7 `/pydantic/pydantic`; `src/multilang/domain/korean.py:99-106`] |
| Korean pronunciation authority | Regex suffix rules, romanization, G2P/LLM auto-approval | NIKL-grounded records plus Korean-phonetics and native-speaker review | Project policy explicitly forbids sole LLM approval and persistent romanization truth. [VERIFIED: `.planning/SPEC.md:133,149,155`; NIKL sources in `KOREAN-STRUCTURE.md:487-496`] |
| APKG generation | Custom Anki SQLite writer | Existing `genanki` model/deck/package pattern | The package library and repository already handle Anki database/media assembly. [VERIFIED: Context7 `/kerrickstaley/genanki`; `src/multilang/services/latin_export.py:195-278`] |
| CSV/TSV escaping | String concatenation | Python `csv.writer` and existing Anki headers | Anki requires UTF-8 and supports explicit separator/html/notetype/deck/columns headers. [CITED: https://docs.ankiweb.net/importing/text-files.html] |
| Stable identity | Python `hash()` or mutable-field GUIDs | Literal model/deck IDs and SHA-256 over immutable source identity | Stable GUIDs allow updates on re-import; mutable content should not duplicate notes. [VERIFIED: Context7 `/kerrickstaley/genanki`; `src/multilang/services/latin_export.py:220-231`] |
| Media integrity | Existence-only checks | Existing root containment plus exact SHA-256 byte/review hash validation | A path can exist while pointing outside the root or containing changed bytes. [VERIFIED: `src/multilang/services/latin_audio.py:164-185`; `.agents/skills/code-security/rules/path-traversal.md`] |
| Korean foundation TTS | Legacy raw-letter synthesis with swallowed exceptions | Frozen approved recordings/assets and explicit blocked status | Current phoneme exporter synthesizes letters and catches exceptions; copying it would violate Korean audio policy. [VERIFIED: `src/multilang/services/russian_phoneme_deck.py:327-418`; `KOREAN-STRUCTURE.md:168-175`] |
| Korean media acquisition | User-supplied APKG parser or remote media URLs | Approved repository-relative manifest assets | Phase 31 has no need to ingest arbitrary packages/URLs, which adds traversal, archive, SSRF, and licensing risk. [VERIFIED: `.agents/skills/code-security/rules/path-traversal.md`; `.agents/skills/code-security/rules/ssrf.md`; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:867-876`] |

**Key insight:** deterministic libraries can prove encoding, graph, package, and byte-integrity facts; they cannot prove pedagogical atomicity, pronunciation correctness, mnemonic quality, licensing rights, or playback acceptability. Those judgments must remain explicit, versioned human gates. [VERIFIED: `.planning/SPEC.md:9-12,154-158`; `KOREAN-STRUCTURE.md:423-452`]

## Runtime State Inventory

> This inventory is included because the recommended implementation extracts language-neutral phoneme mechanics while preserving the existing Russian/Polish/Greek module as compatibility wrappers. It is not a product rename. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:383-455`]

| Category | Items Found | Action Required |
|---|---|---|
| Stored data | Existing user-imported Russian/Polish/Greek Anki notes can depend on their fixed model/deck IDs, note-type names, field order, and stable GUID behavior. No project DB migration or stored Korean foundation data exists. [VERIFIED: `src/multilang/services/russian_phoneme_deck.py:17-45,178-309`; Phase 31 data directory audit] | Preserve all existing IDs/names/fields/GUID inputs byte-for-byte through wrappers; add regression tests. No data migration. [VERIFIED: Anki update behavior at https://docs.ankiweb.net/importing/packaged-decks.html] |
| Live service config | No external live service configuration is renamed; Korean production voice registration remains out of scope, and existing language voice constants stay in `russian_phoneme_deck.py`. [VERIFIED: `src/multilang/services/russian_phoneme_deck.py:29-34`; no-touch boundary] | None. Do not patch Azure/live configuration or add a Korean voice. [VERIFIED: `.planning/SPEC.md:61`; pattern map] |
| OS-registered state | The installed `multilang` console entry point remains `multilang.cli:app`, and existing phoneme command/public module surfaces are to remain available. [VERIFIED: `pyproject.toml:39-40`; pattern map compatibility guidance] | Preserve command names/import wrappers; no task-scheduler, service, or OS registration migration is required. [VERIFIED: scope audit] |
| Secrets/env vars | Existing Azure/provider environment configuration is not renamed or consumed by the frozen exporter; Phase 31 adds no credential name. [VERIFIED: architecture/no-live-provider boundary; `.agents/skills/code-security/rules/secrets.md`] | None. Never copy credentials into manifests, tests, review artifacts, or logs. [VERIFIED: `.planning/SPEC.md:154`] |
| Build artifacts | No package/project/module identity is removed. A new `phoneme_deck.py` module is added while the old module remains as wrappers; editable/source installs discover modules under `src/multilang`. [VERIFIED: recommended structure; `pyproject.toml:48-52`] | Run `uv sync --extra dev` and import/regression tests. No package reinstall migration, global CLI re-registration, or artifact rename is required. [VERIFIED: project packaging config] |

## Common Pitfalls

### Pitfall 1: Compatibility Jamo Leaks Into Canonical Identity
**What goes wrong:** Display `ㄱ` is treated as canonical lexical text or silently folded into a choseong, losing position and bypassing Phase 30 rejection. [VERIFIED: `src/multilang/domain/korean.py:49-50,109-120`]
**Why it happens:** Learner-friendly standalone glyphs and machine conjoining-jamo identity look equivalent on screen but have different Unicode roles. [CITED: https://www.unicode.org/reports/tr15/]
**How to avoid:** Keep a reviewed positional mapping model and leave `canonicalize_korean()` unchanged. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:39-44`]
**Warning signs:** NFKC in learner-content code, compatibility ranges added to lexical allowlists, or one consonant mapping reused blindly for onset and coda. [VERIFIED: source/code audit criteria]

### Pitfall 2: Ordered List Masquerades as i+1
**What goes wrong:** A record appears later but still observes an undeclared rule, or a broad concept ID hides several new ideas. [VERIFIED: `.planning/SPEC.md:53,146`]
**Why it happens:** Sequence labels do not compute unknown sets, and concept granularity can be gamed. [VERIFIED: `KOREAN-STRUCTURE.md:41-62`]
**How to avoid:** Recompute unknowns, require explicit active-rule prerequisites, and have curriculum review approve concept atomicity. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:230-239`]
**Warning signs:** `unknown_concept_ids` trusted from JSON, empty observed sets, one target named “all batchim rules,” or review approval before graph validation. [VERIFIED: planned negative-test criteria]

### Pitfall 3: Bootstrap Is Inferred or Pre-Knows Untaught Concepts
**What goes wrong:** The validator exempts the first cards or initializes all H0 concepts as known, making false strict claims pass. [VERIFIED: `.planning/SPEC.md:48`]
**How to avoid:** Persist ordered `bootstrap_concept_ids`, validate H0 targets against it, and admit each target only after its own entry passes. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:232-238`]
**Warning signs:** `known = set(bootstrap_ids)` before validating H0, or “first N cards” hardcoded without manifest identity. [VERIFIED: validator design review]

### Pitfall 4: Normative, Surface, and IPA Forms Drift
**What goes wrong:** Export audio/text represents a different pronunciation or register than the approved record. [VERIFIED: `KOREAN-STRUCTURE.md:133-175,382-408`]
**How to avoid:** Keep distinct fields, exact text/SSML/byte hashes, and reset approval after any relevant change. [VERIFIED: `KOREAN-STRUCTURE.md:168-175,382-408`]
**Warning signs:** one `pronunciation` string, IPA generated at render time, or unchanged review status after text/voice/prosody edits. [VERIFIED: required source/media contract]

### Pitfall 5: Raw-Glyph TTS or Silent Audio Failure
**What goes wrong:** A provider reads a letter name, silence, or unintended word; exporter catches the failure and ships blank audio. [VERIFIED: `src/multilang/services/russian_phoneme_deck.py:327-418`]
**How to avoid:** Never call Azure from the foundation exporter; use explicit approved spoken text/context or reviewed human recordings and fail closed. [VERIFIED: `KOREAN-STRUCTURE.md:168-175`]
**Warning signs:** `AzureSpeechAdapter` import in foundation export, `spoken_text == display_glyph`, broad `except Exception`, or empty required sound fields. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:362-379`]

### Pitfall 6: Review Status Is Not Bound to Exact Bytes
**What goes wrong:** A reviewed filename is replaced while status stays approved. [VERIFIED: `KOREAN-STRUCTURE.md:382-408`]
**How to avoid:** Recompute byte SHA-256 and require equality with both artifact and reviewed hashes; bind source/media versions and reviewer roles. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:303-347`]
**Warning signs:** approval keyed only by basename, duration, provider, or path. [VERIFIED: media threat analysis]

### Pitfall 7: CSV/TSV “Survival” Means Tags Without Media
**What goes wrong:** Tables contain `[sound:x.wav]` but no deterministic bundle tells the user which exact bytes to copy. [CITED: https://docs.ankiweb.net/importing/text-files.html#importing-media]
**How to avoid:** Emit a sibling media directory/checksum manifest and resolve every reference in tests. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:620-631`]
**Warning signs:** `media_count=0`, absolute paths in cells, subdirectory names in sound/image tags, or no checksum manifest. [CITED: https://github.com/kerrickstaley/genanki]

### Pitfall 8: Export Writes Before Validation Finishes
**What goes wrong:** A failed build leaves a partial artifact that appears usable. [VERIFIED: existing exporters create directories near the final write at `src/multilang/services/latin_export.py:259-312`]
**How to avoid:** Complete all source/review/media/reference checks first, write to a secure temporary file where needed, then atomically replace the target. [VERIFIED: `.agents/skills/code-security/AGENTS.md`, race-condition guidance; `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:758-763`]
**Warning signs:** `mkdir()` before readiness validation or a target file present after expected failure. [VERIFIED: planned negative tests]

### Pitfall 9: Template Reuse Leaks Japanese Semantics
**What goes wrong:** Korean notes contain `Kana`, `Romaji`, Japanese class names, or Japanese fonts. [VERIFIED: `.planning/SPEC.md:47`]
**How to avoid:** Create a Korean-owned template, preserve only layout behavior, and scan fields/HTML/CSS case-insensitively. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:459-524`]
**Warning signs:** imports from `japanese_kana_deck` in Korean source or modifications to the Japanese template. [VERIFIED: no-touch boundary]

### Pitfall 10: Shared Phoneme Refactor Regresses Existing Decks
**What goes wrong:** Russian/Polish/Greek IDs, imports, fields, templates, CSS, inventories, voices, or commands change while extracting generic mechanics. [VERIFIED: `src/multilang/services/russian_phoneme_deck.py:17-45,178-309`]
**How to avoid:** Extract only model/note/field mapping mechanics; retain wrappers/aliases and assert byte-identical existing render contracts. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:383-455,710-723`]
**Warning signs:** renamed public symbols without aliases or regenerated existing APKG snapshots. [VERIFIED: regression plan]

### Pitfall 11: Static Tests Overclaim Human Acceptance
**What goes wrong:** Passing schema/archive tests are reported as Korean linguistic, playback, or Desktop/mobile acceptance. [VERIFIED: `.planning/SPEC.md:158`; `.planning/ROADMAP.md:97-107`]
**How to avoid:** Separate automated and human evidence in manifests/reports and keep final Anki rendering/import claims in Phase 34. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:725-745`]
**Warning signs:** “approved” produced by a test fixture or fake provider, screenshots absent, or no reviewer/artifact hash. [VERIFIED: `KOREAN-STRUCTURE.md:423-452`]

### Pitfall 12: Unsafe Manifest/HTML/Path Handling
**What goes wrong:** Malicious JSON values create traversal, remote fetches, event-handler HTML, template injection, or expensive regex matching. [VERIFIED: `.agents/skills/code-security/rules/path-traversal.md`; `.agents/skills/code-security/rules/xss.md`; `.agents/skills/code-security/rules/regex-dos.md`]
**How to avoid:** Treat committed manifests as untrusted, forbid extras, bound lengths/counts, reject URLs/absolute/traversal paths, allowlist media markup, HTML-escape plain learner text, and use fixed non-nested regexes. [VERIFIED: Context7 `/pydantic/pydantic`; `.agents/skills/llm-security/rules/output-handling.md`]
**Warning signs:** `pickle`, unsafe YAML, arbitrary URL fields, `on*=` attributes, `<script>`, absolute Windows paths, or nested quantifier regexes. [VERIFIED: `.agents/skills/code-security/rules/insecure-deserialization.md`; `.agents/skills/code-security/rules/regex-dos.md`]

### Pitfall 13: Scope Drift Into Phase 32/34
**What goes wrong:** Work adds a Korean frequency asset, production voice registry entry, live generation, DB migration, or claims final all-family visual/import acceptance. [VERIFIED: `.planning/ROADMAP.md:73-107`]
**How to avoid:** Keep frozen foundations isolated and stop/replan if a no-touch surface proves necessary. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:800-813`]
**Warning signs:** changes under `assets/frequency/ko`, `runtime.py`, Alembic, `audio_voice_registry.py`, or generic exporter schemas. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:800-813`]

### Pitfall 14: Phase Slug Drift
**Status:** The earlier slug mismatch has been reconciled; the canonical Phase 31 slug is now `i-plus-1`, and all Phase 31 artifacts belong under `.planning/phases/31-hangul-and-pronunciation-i-plus-1/`. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:11-13`]
**How to avoid:** Keep future research and plans under the canonical Phase 31 directory. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:878-881`]
**Warning signs:** Phase 31 references that do not use the canonical `i-plus-1` slug. [VERIFIED: current directory audit]

## Code Examples

Verified implementation patterns from official sources and repository analogs follow.

### Unicode Hangul Composition

```python
# Source: Unicode 17 Core Spec, Chapter 3, Hangul composition sample/constants
S_BASE = 0xAC00
L_BASE = 0x1100
V_BASE = 0x1161
T_BASE = 0x11A7
L_COUNT = 19
V_COUNT = 21
T_COUNT = 28
N_COUNT = V_COUNT * T_COUNT
S_COUNT = L_COUNT * N_COUNT


def compose_modern_hangul(initial: str, medial: str, final: str | None = None) -> str:
    l_index = ord(initial) - L_BASE
    v_index = ord(medial) - V_BASE
    t_index = 0 if final is None else ord(final) - T_BASE
    if not (0 <= l_index < L_COUNT and 0 <= v_index < V_COUNT and 0 <= t_index < T_COUNT):
        raise ValueError("modern Hangul jamo identity is out of range")
    return chr(S_BASE + (l_index * V_COUNT + v_index) * T_COUNT + t_index)
```

Normalize/compare the output with NFC and exhaustively round-trip all valid index combinations in tests. [CITED: https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/#G59688] [CITED: https://docs.python.org/3.12/library/unicodedata.html]

### Strict Curriculum Recalculation

```python
# Source: project SPEC/KOREAN-STRUCTURE contract + Python graphlib docs
from graphlib import CycleError, TopologicalSorter


def validate_graph(concepts: dict[str, KoreanConcept]) -> tuple[str, ...]:
    predecessors = {concept_id: set(c.prerequisite_ids) for concept_id, c in concepts.items()}
    missing = {p for values in predecessors.values() for p in values if p not in concepts}
    if missing:
        raise ValueError("curriculum references unknown concept IDs")
    try:
        return tuple(TopologicalSorter(predecessors).static_order())
    except CycleError as exc:
        raise ValueError("curriculum prerequisite cycle") from exc


def assert_strict(entry: SourceEntry, known_before: set[str]) -> None:
    observed = set(entry.curriculum.observed_concept_ids)
    prerequisites = set(entry.curriculum.prerequisite_concept_ids)
    recomputed_unknown = observed - known_before
    if recomputed_unknown != {entry.curriculum.target_concept_id}:
        raise ValueError("false strict i+1 evidence")
    if tuple(sorted(recomputed_unknown)) != entry.curriculum.unknown_concept_ids:
        raise ValueError("serialized unknown concepts do not match recomputation")
    if not prerequisites <= known_before:
        raise ValueError("curriculum prerequisite is not known before this card")
    active_non_target = set(entry.active_rule_ids) - {entry.curriculum.target_concept_id}
    if not active_non_target <= prerequisites:
        raise ValueError("active non-target rules must be explicit prerequisites")
```

Use source-order tuples rather than sorted IDs if order is part of the serialized contract; the snippet sorts only to illustrate deterministic comparison. [VERIFIED: `.planning/SPEC.md:97-103`; `KOREAN-STRUCTURE.md:41-62`]

### Safe Repository-Relative Media Resolution

```python
# Source: src/multilang/services/latin_audio.py:164-185, extended with byte hash
from hashlib import sha256
from pathlib import Path


def resolve_reviewed_media(root: Path, path_text: str, expected_sha256: str) -> Path:
    relative = Path(path_text)
    if relative.is_absolute() or ".." in relative.parts or ":" in path_text or "\\" in path_text:
        raise ValueError("media path is not repository-relative")
    candidate = (root.resolve() / relative).resolve(strict=True)
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("media path escapes repository root") from exc
    if not candidate.is_file() or candidate.stat().st_size <= 0:
        raise ValueError("media file is missing or empty")
    if sha256(candidate.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError("media artifact hash mismatch")
    return candidate
```

Public diagnostics should emit only family, item key, media kind, and failed field—not absolute paths, source text, reviewer notes, or provider payloads. [VERIFIED: `src/multilang/services/latin_audio.py:188-254`; Phase 30 privacy posture at `.planning/phases/30-korean-contracts-and-morphology/30-08-SUMMARY.md:233-245`]

### Stable genanki Model and Media Package

```python
# Source: Context7 /kerrickstaley/genanki and src/multilang/services/latin_export.py
model = genanki.Model(
    KOREAN_PRONUNCIATION_MODEL_ID,
    KOREAN_PRONUNCIATION_NOTE_TYPE_NAME,
    fields=[{"name": name} for name in PHONEME_FIELD_NAMES],
    templates=[{"name": "Pronunciation Card", "qfmt": front, "afmt": back}],
    css=shared_css + korean_font_override,
)
deck = genanki.Deck(KOREAN_PRONUNCIATION_DECK_ID, KOREAN_PRONUNCIATION_DECK_NAME)
for row in sorted(rows, key=lambda item: (item.sort_index, item.item_key)):
    note = KoreanPronunciationNote(model=model, fields=row.ordered_fields())
    note._multilang_guid = sha256(
        f"ko|foundation-pronunciation|{source_pack_version}|{row.item_key}".encode("utf-8")
    ).hexdigest()[:32]
    deck.add_note(note)
package = genanki.Package(deck)
package.media_files = [str(path) for path in resolved_approved_media]
package.write_to_file(str(temporary_output))
```

All validation and media resolution must happen before this write block, and the temporary artifact must be inspected before replacing the requested output. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:551-618`]

## State of the Art

| Old / unsafe approach | Current approach | When / evidence | Impact |
|---|---|---|---|
| Treat visually similar Hangul forms as interchangeable | NFC canonical identity plus explicit positional display mapping | Unicode 17 UAX #15 and Phase 30 contract. [CITED: https://www.unicode.org/reports/tr15/] [VERIFIED: `src/multilang/domain/korean.py:109-120`] | Prevents compatibility/halfwidth leakage and preserves machine identity. [VERIFIED: Phase 30 verification] |
| Ordered syllabus with informal “i+1” labels | Executable concept DAG and recomputed exactly-one-unknown evidence | Locked for v3.0 on 2026-07-20. [VERIFIED: `.planning/SPEC.md:146`; `KOREAN-STRUCTURE.md:41-62`] | False i+1 becomes a validation failure, not a review opinion. [VERIFIED: `.planning/SPEC.md:53`] |
| Raw-letter TTS during export with swallowed errors | Frozen exact-text, exact-byte reviewed media before export | Korean audio policy locked in v3.0. [VERIFIED: `KOREAN-STRUCTURE.md:168-175,382-408`] | Provider success cannot auto-approve pedagogical audio. [VERIFIED: `.planning/SPEC.md:149,155`] |
| Language-specific phoneme mechanics embedded in `russian_phoneme_deck.py` | Language-neutral model/note/field builder with compatibility wrappers | Recommended Phase 31 extraction. [VERIFIED: `src/multilang/services/russian_phoneme_deck.py:178-249`; pattern map] | Korean reuses exact layout without changing existing language identities. [VERIFIED: `.planning/SPEC.md:52`] |
| Text export containing unresolved media references | UTF-8 Anki headers plus sibling basename/checksum media bundle | Anki documents collection-media copying and basename tags. [CITED: https://docs.ankiweb.net/importing/text-files.html#importing-media] | KPRO-01 can prove references survive without claiming automatic Anki media installation. [VERIFIED: `.planning/SPEC.md:52`] |
| Static voice name selected from memory | Live catalog qualification and exact reviewed voice metadata | Microsoft voice page updated 2026-07-22 and lists current `ko-KR` voices. [CITED: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts] | Phase 31 must not lock a production voice; Phase 32 qualifies one with approval. [VERIFIED: `.planning/SPEC.md:61,148`] |

**Deprecated/outdated for this phase:**

- Legacy `russian_phoneme_deck.py` export-time letter synthesis and broad exception swallowing are regression-preserved existing behavior, not a Korean pattern. [VERIFIED: `src/multilang/services/russian_phoneme_deck.py:327-418`]
- User-APKG ingestion from the kana implementation is unnecessary for Korean foundations and should not be copied; only its model/layout/media-reference shape is relevant. [VERIFIED: `src/multilang/services/japanese_kana_deck.py:1-9,296-401`; pattern map]
- Romanization is not Korean pronunciation ground truth and must not become a persistent dependency. [VERIFIED: `.planning/SPEC.md:132`; `KOREAN-STRUCTURE.md:15`]
- A package upgrade to Pydantic 2.13, pytest 9, or Azure SDK 1.51 is not required to deliver this phase. [VERIFIED: current project ranges, installed versions, and required APIs]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| — | None. All factual claims are tied to repository evidence, official documentation, Context7, or current registry/environment probes. | — | — |

## Open Questions (RESOLVED)

The external values are not fabricated during planning. Each is resolved by an exact execution authority and a fail-closed consequence; missing values stop Phase 31 rather than becoming an implementation ambiguity.

1. **Redistributable stroke, mnemonic, image/GIF, and recording assets**
   - Resolution: The fixed Phase 31 evidence bundle accepts an asset only when its rights record names the exact source/version, attribution, license, exact artifact hash, and both `reuse_disposition=approved` and `redistribution_disposition=approved`. Unknown or merely convenient assets remain absent. [VERIFIED: `src/multilang/services/korean_foundation_evidence.py:605-614`; `31-APPROACH.md:184-201`]
   - Owner: The user coordinates the source/rightsholder evidence at Plan 31-26; the named rights authority supplies the disposition.
   - Authority: Exact rights records plus exact licensed bytes reviewed through the fixed request/inbox contracts, not the executor, AI draft, filename, or provider response.
   - Fail-closed consequence: Any missing/ambiguous source, attribution, license, reuse, redistribution, or byte hash blocks `inspect-inbox`; no receipt, snapshot, activation, or export is written.

2. **Qualified Korean/Portuguese reviewers and distinct playback roles**
   - Resolution: Plan 31-26 requires the four fixed reviewer records and all request-declared qualifications. Korean phonetics-specialist and independent-native-speaker playback authority must be distinct for jamo/rule audio; one identity cannot satisfy both. [VERIFIED: `evidence-inbox/README.md:8-20`; `31-APPROACH.md:190-201`]
   - Owner: The user coordinates direct placement; each named person owns only the qualifications and decisions recorded in their signed/hash-bound reviewer evidence.
   - Authority: Qualified Korean orthography, Korean phonetics, Portuguese, and independent native-speaker records bound to exact v2/request/artifact hashes and timestamps.
   - Fail-closed consequence: Missing identity, qualification, role separation, scope, timestamp, or exact-hash binding blocks inbox validation with zero canonical mutation. There is no automated fallback.

3. **P11 reductions and P12/P13 auditory contrasts**
   - Resolution: The structurally frozen item inventory is the exact selected/promoted v2 projection of the existing 47-record P0-P13 candidate. Plan 31-26 requires a qualified Korean phonetics specialist to approve all six specialist-atomization scopes plus every item-level normative/surface/active-rule claim against that exact version. [VERIFIED: `src/multilang/services/korean_foundation_evidence.py:581-592`; `31-APPROACH.md:108-117,233-236`]
   - Owner: The Korean phonetics specialist owns item/atomization acceptance; the user only coordinates the checkpoint and exact evidence placement.
   - Authority: Exact specialist review records, normative sources, and reviewed recordings bound to v2 content hashes.
   - Fail-closed consequence: Rejection or need for a structural item/graph change stops Phase 31 and requires a new candidate version/replan before evidence receipt; the executor cannot patch structure inside the inbox.

4. **Portuguese regional editorial policy**
   - Resolution: Canonical language identity remains exactly `pt`. A qualified Portuguese reviewer must choose and record one bounded `regional_editorial_policy` value in the fixed curriculum review and approve every learner-facing translation/alignment/register decision under that policy. The executor and AI drafts do not choose `pt-BR`, `pt-PT`, or neutral style implicitly. [VERIFIED: `src/multilang/services/korean_foundation_evidence.py:558-579`; `31-APPROACH.md:228-236`]
   - Owner: The qualified Portuguese reviewer owns the editorial decision; the user coordinates its evidence at Plan 31-26.
   - Authority: The exact reviewer record and policy review bound to the v2 proposed-curation/request hashes.
   - Fail-closed consequence: Missing policy, unqualified reviewer, mixed policy application, English leakage, or translation contradiction blocks inbox validation and production readiness.

5. **Phase 31 directory canonicalization**
   - Resolution: The canonical slug is `i-plus-1`; all Phase 31 planning/handoff/evidence artifacts remain under `.planning/phases/31-hangul-and-pronunciation-i-plus-1/`. [VERIFIED: current directory audit; pattern map]
   - Owner/authority: Repository planning contract.
   - Fail-closed consequence: The fixed-root helpers reject alternate roots or arbitrary path input.

6. **Foundation audio format**
   - Resolution: Phase 31 production audio is exact `pcm_s16le_wav` with `.wav` paths and stdlib header/duration validation. PNG/GIF remain the only supported non-audio media formats declared by the fixed slots. [VERIFIED: `src/multilang/services/korean_foundation_media.py:83,99-107,1123-1131`; `src/multilang/services/korean_foundation_evidence.py:1007,1599-1607`]
   - Owner: The fixed media/evidence contract owns the accepted format; reviewers/rightsholders supply exact compliant bytes.
   - Authority: Exact media manifest, rights, playback, and recomputed byte/header/hash evidence.
   - Fail-closed consequence: MP3 or any other undeclared format is rejected. Supporting it requires an explicit dependency/validator replan; no silent conversion or guessed duration is permitted.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---:|---|---|
| `uv` | Reproducible test/runtime commands | ✓ | 0.11.14 | — [VERIFIED: environment probe 2026-08-04] |
| Python | Domain, manifests, export, tests | ✓ | 3.13.7 active; project baseline >=3.12 | Run the required 3.12 compatibility smoke before closure. [VERIFIED: environment probe; `pyproject.toml:10`] |
| Pydantic | Typed source/review/media contracts | ✓ | 2.12.5 | — [VERIFIED: environment probe] |
| genanki | APKG generation | ✓ | 0.13.1 | — [VERIFIED: environment probe] |
| pytest | Validation suite | ✓ | 8.4.2 | — [VERIFIED: environment probe] |
| zstandard | Existing APKG inspection compatibility | ✓ | 0.25.0 | Existing legacy `collection.anki2` path when applicable. [VERIFIED: environment probe; `japanese_kana_deck.py:117-204`] |
| Azure Speech SDK | Existing adapter/metadata compatibility only | ✓ | 1.49.1 | No live call in Phase 31; approved human/frozen audio is primary. [VERIFIED: environment probe; `.planning/SPEC.md:154`] |
| Anki Desktop CLI/app | Observed import/render/playback | ✗ | — | Automated ZIP/SQLite checks now; explicit human Anki evidence in Phase 34. [VERIFIED: environment probe; `.planning/ROADMAP.md:97-107`] |
| `ffmpeg` | Optional transcoding/media inspection | ✗ | — | Prefer reviewed PCM WAV and stdlib validation; do not transcode silently. [VERIFIED: environment probe] |
| `ffprobe` | Optional MP3 duration inspection | ✗ | — | PCM WAV + stdlib `wave`, or add a planned dependency only if approved assets require MP3. [VERIFIED: environment probe] |
| Korean orthography/phonetics reviewers | Learner-ready content/audio approval | execution input | — | Fixed Plan 31-26 reviewer records and role-separation gate; absence blocks with no fallback. [VERIFIED: resolved Question 2] |

**Execution inputs with no fallback:** qualified human review and approved licensed media remain mandatory Plan 31-26 inputs under the resolved contracts above. Their absence is a defined zero-mutation stop condition, not an unresolved implementation decision. [VERIFIED: `.planning/SPEC.md:47,149,155-158`; resolved Questions 1-4 and 6]

**Missing dependencies with fallback:** Anki Desktop and ffmpeg/ffprobe are not needed for Phase 31's bounded automated structure claim if PCM WAV and archive inspection are used; final observed Anki acceptance remains Phase 34. [VERIFIED: `.planning/ROADMAP.md:97-107`; environment audit]

## Validation Architecture

The execution-current per-task Nyquist matrix, checkpoint handoffs, latencies, and new assisted-curation tests are maintained in `31-VALIDATION.md`. The original architecture below remains the requirement-level rationale.

### Test Framework

| Property | Value |
|---|---|
| Framework | pytest 8.4.2 installed; project range `>=8.3,<9.0`. [VERIFIED: environment probe; `pyproject.toml:43-57`] |
| Config file | `pyproject.toml` (`pythonpath=["src"]`, `testpaths=["tests"]`, asyncio auto). [VERIFIED: `pyproject.toml:54-57`] |
| Quick run command | `UV_OFFLINE=1 uv run --extra dev pytest tests/domain/test_korean.py tests/services/test_korean_curriculum.py tests/services/test_korean_foundation_review.py tests/services/test_korean_foundation_media.py -q` |
| Full suite command | `UV_OFFLINE=1 uv run --extra dev pytest -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| KHAN-01 | Exact modern inventory, Korean-only note/template IDs/fields/fonts, complete hash-aligned required media, APKG/table structure | unit + integration + human gate | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_curriculum.py tests/services/test_korean_foundation_media.py tests/services/test_korean_foundation_export.py tests/services/test_card_template_loader.py -q` | ✅ Existing after Plans 31-01 through 31-10; v2 additions mapped in `31-VALIDATION.md`. |
| KHAN-02 | Explicit bootstrap, DAG, NFC, recomputed exactly-one target unknown, no compatibility/halfwidth leakage | unit/property-style parametrization | `UV_OFFLINE=1 uv run --extra dev pytest tests/domain/test_korean.py tests/services/test_korean_curriculum.py -q` | ✅ Existing after Plans 31-01 through 31-10. |
| KPRO-01 | Exact nine fields and shared HTML/CSS, Korean IDs, Portuguese fields, APKG/CSV/TSV media references resolve | contract + archive/integration | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_phoneme_deck.py tests/services/test_korean_foundation_export.py tests/integration/test_korean_foundations_flow.py -q` | ✅ Existing after Plans 31-01 through 31-10; v2 migration remains planned. |
| KPRO-02 | P0-P13 coverage, active non-target rules are prerequisites, cycles/forward edges/false i+1 block approval/export | unit + mutation negatives + human gate | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_curriculum.py tests/services/test_korean_foundation_review.py -q` | ✅ Existing after Plans 31-01 through 31-10. |

### Required Automated Evidence

- Domain tests: frozen contracts, NFC/NFD equivalence, compatibility/halfwidth rejection, positional display mapping, all 11,172 composition round trips, and invalid index bounds. [CITED: Unicode/Python docs above] [VERIFIED: Phase 30 test style at `tests/domain/test_korean.py`]
- Curriculum tests: duplicate/missing IDs, exact H0-H10/P0-P13 coverage, explicit bootstrap, omitted target, caller-forged unknowns, cycles, forward prerequisites, undeclared active rules, broad false concepts, and deterministic ordering. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:671-684`]
- Review/media tests: every relevant gate, approved-overwrite guard, source/version/hash drift, Windows absolute paths, `..`, URLs, missing/empty/wrong bytes, basename collisions, raw-glyph spoken text, and missing reviewer role. [VERIFIED: `tests/services/test_latin_review.py`; `tests/services/test_latin_audio.py`; security skill rules]
- Template/shared-phoneme tests: exact field/reference order, Korean fonts, Japanese token absence, and byte-identical Russian/Polish/Greek HTML/CSS behavior after extraction. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:710-731`]
- Export tests: inspect APKG ZIP media map and collection SQLite; assert IDs, names, field order, note count, GUIDs, tags, hidden evidence, exact media bytes, and no artifact after failure; parse both CSV/TSV with `csv.reader` and resolve every media reference through checksums. [VERIFIED: `tests/services/test_latin_export.py`; `tests/services/test_export_anki_package.py`; pattern map]
- Integration test: build both approved families in all three formats offline, inspect outputs, then mutate one graph edge and one reviewed byte to prove every format fails closed. No provider object may be constructed. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:741-745`]

### Human-Only Evidence

- Korean orthography/stroke/mnemonic review, Korean phonetics review, Portuguese quality review, license/redistribution decision, and exact-hash playback approval are manual-only because code cannot establish those judgments. [VERIFIED: `.planning/SPEC.md:154-158`; `KOREAN-STRUCTURE.md:423-452`]
- A fake provider may test an adapter boundary but may not create an `approved` curation or audio record. [VERIFIED: `.planning/SPEC.md:155`; `.agents/skills/llm-security/rules/misinformation.md`]
- Static/APKG inspection may prove artifact structure, but not final Anki Desktop/mobile appearance or actual import/playback acceptance. [VERIFIED: `.planning/SPEC.md:158`; `.planning/ROADMAP.md:97-107`]

### Sampling Rate

- **Per task commit/checkpoint:** run the narrow test file(s) named by the task; use offline mode and no provider credentials. [VERIFIED: established Phase 30 offline pattern]
- **Per wave merge:** run Phase 31 focused tests plus kana, phoneme, Latin export/media, and Phase 30 Korean boundary regressions. [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md:815-863`]
- **Phase gate:** full offline suite green, Python 3.12 compatibility smoke green, human artifacts present and hash-aligned, and no unapproved record exported before `/gsd-verify-work`. [VERIFIED: `AGENTS.md`, Engineering Quality; Phase 30 verification precedent]

### Wave 0 Status

- [x] Original curriculum, review, media, shared phoneme, export, CLI, and integration test gaps were closed by Plans 31-01 through 31-10. [VERIFIED: live test-file audit; `31-10-SUMMARY.md`]
- [x] No framework install gap; pytest is configured and installed. [VERIFIED: environment and `pyproject.toml`]
- [ ] `tests/services/test_korean_foundation_ai_curation.py` is intentionally created test-first by Task 31-11-01.
- [ ] `tests/services/test_phase31_handoff.py` is intentionally created test-first by Task 31-20-02.
- [ ] `tests/services/test_phase31_runtime_isolation.py` is intentionally created test-first by Task 31-25-01.

## Security Domain

Security enforcement is enabled because `.planning/config.json` does not explicitly set `security_enforcement` to `false`. [VERIFIED: `.planning/config.json`]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication | no | Phase 31 adds local operator CLI/services and no authentication surface. [VERIFIED: recommended ownership boundary and existing CLI analog] |
| V3 Session Management | no | No browser/server session is introduced. [VERIFIED: phase architecture] |
| V4 Access Control | limited | Restrict filesystem access to fixed repository roots and enum-selected family/format operations; no arbitrary paths/modules/templates. [VERIFIED: `.agents/skills/code-security/rules/path-traversal.md`; pattern map CLI guidance] |
| V5 Input Validation | yes | Pydantic `extra="forbid"`, bounded fields/counts, controlled enums, NFC/script checks, graph recomputation, fixed regexes, and HTML/media allowlists. [VERIFIED: Context7 `/pydantic/pydantic`; `src/multilang/domain/korean.py`] |
| V6 Cryptography | yes, integrity only | Use stdlib SHA-256 for content/media/review/GUID integrity; do not invent encryption or password hashing. [VERIFIED: `.agents/skills/code-security/AGENTS.md`, insecure-crypto guidance; existing project hash patterns] |
| V8 Data Protection | yes | Errors/logs expose item keys and reason codes only, not source text, absolute paths, reviewer notes, provider payloads, or secrets. [VERIFIED: Phase 30 judgment; `.agents/skills/llm-security/rules/sensitive-disclosure.md` via skill index] |
| V12 Files and Resources | yes | Reject absolute/traversal/URL paths, contain resolved paths, require exact basenames, size/header/hash checks, and fail before writing. [VERIFIED: `.agents/skills/code-security/rules/path-traversal.md`; `src/multilang/services/latin_audio.py:164-185`] |
| V14 Configuration | yes | Fixed model/deck IDs, source-pack versions, provider metadata, and no secrets in manifests/source. [VERIFIED: `.agents/skills/code-security/rules/secrets.md`; Context7 genanki docs] |

### Known Threat Patterns for Python + Anki Manifests

| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Path traversal / absolute media path | Elevation / Information Disclosure | Resolve against a fixed root, require `relative_to(root)`, reject `..`, drives, backslashes, URLs, and private path output. [VERIFIED: `.agents/skills/code-security/rules/path-traversal.md`; Latin analog] |
| Script/event-handler HTML in card fields | Tampering / Elevation | Escape plain text and allowlist only required Anki media markup; reject `<script>`, `javascript:`, inline events, remote media, and unknown template references. [VERIFIED: `.agents/skills/code-security/rules/xss.md`; genanki README HTML guidance] |
| Unsafe object deserialization | Elevation | UTF-8 JSON + Pydantic only; no pickle, unsafe YAML, arbitrary protobuf parser, or dynamic imports for foundation manifests. [VERIFIED: `.agents/skills/code-security/rules/insecure-deserialization.md`] |
| SSRF through media/source URLs | Information Disclosure | Never fetch manifest URLs; source URLs are inert provenance strings and media must be repository-relative. [VERIFIED: `.agents/skills/code-security/rules/ssrf.md`] |
| Tampered reviewed audio/media | Tampering | SHA-256 actual bytes must equal artifact and reviewed hashes; changes reset approval. [VERIFIED: `KOREAN-STRUCTURE.md:382-408`] |
| Unicode compatibility confusion | Spoofing / Tampering | NFC canonical boundaries, explicit positional display mapping, compatibility/halfwidth rejection, and code-point goldens. [CITED: https://www.unicode.org/reports/tr15/] [VERIFIED: `src/multilang/domain/korean.py`] |
| ReDoS in template/media extraction | Denial of Service | Fixed compiled regex without nested quantifiers, bounded input size/count, and direct parser/allowlist logic where possible. [VERIFIED: `.agents/skills/code-security/rules/regex-dos.md`] |
| LLM/G2P misinformation promoted to curriculum truth | Tampering | Treat generated output as untrusted, ground in NIKL/source records, and require qualified human approval. [VERIFIED: `.agents/skills/llm-security/rules/misinformation.md`; `.planning/SPEC.md:155`] |
| Provider credentials leaked in manifests/logs | Information Disclosure | No provider calls in export, no secrets in source/review data, environment/secret-manager use only in owning provider phase. [VERIFIED: `.agents/skills/code-security/rules/secrets.md`; `.planning/SPEC.md:154`] |
| Partial artifact after validation failure | Tampering / Repudiation | Validate before output, write temporary artifact, inspect, atomically replace, and test target absence on failure. [VERIFIED: pattern map fail-before-write guidance; security race-condition guidance] |

## Sources

### Primary (HIGH confidence)

- [CITED: https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/] — Unicode 17 conjoining-jamo behavior, Hangul decomposition/composition, constants, and conformance; fetched 2026-08-04.
- [CITED: https://www.unicode.org/reports/tr15/] — UAX #15 revision 57 (2025-07-30), NFC/NFD versus compatibility normalization and Hangul equivalence; fetched 2026-08-04.
- [CITED: https://docs.python.org/3.12/library/unicodedata.html] — Python 3.12.13 normalization APIs and bundled UCD version; fetched 2026-08-04.
- [CITED: https://docs.python.org/3.12/library/graphlib.html] — predecessor graph, topological order, and cycle behavior; fetched 2026-08-04.
- [CITED: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0001] — NIKL Hangul orthography, modern letter names/order, final order, morphophonemic spelling, and spacing; fetched 2026-08-04.
- [CITED: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0002] — NIKL standard language/pronunciation and modern Seoul baseline; fetched 2026-08-04.
- [CITED: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts] — current `ko-KR` TTS support/voices, page dated 2026-07-22; fetched 2026-08-04.
- [CITED: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-ssml-phonetic-sets#ko-kr] — Korean IPA/SSML support, page dated 2026-02-25; fetched 2026-08-04.
- [CITED: https://docs.ankiweb.net/importing/packaged-decks.html] — APKG import/update behavior and stable note-type implications; fetched 2026-08-04.
- [CITED: https://docs.ankiweb.net/importing/text-files.html] — UTF-8 text import, headers, HTML, sound/image tags, basename media copying, and GUID behavior; fetched 2026-08-04.
- [VERIFIED: Context7 `/pydantic/pydantic`] — `extra="forbid"`, frozen models, `model_validate`, and after-model validators; queried 2026-08-04.
- [VERIFIED: Context7 `/kerrickstaley/genanki`] — fixed unique IDs, stable GUIDs, package/media, and write behavior; queried 2026-08-04.
- [VERIFIED: PyPI JSON endpoints] — current/publish metadata for Pydantic 2.13.4, pytest 9.1.1, genanki 0.13.1, and Azure Speech SDK 1.51.1; fetched 2026-08-04.
- [VERIFIED: `.planning/SPEC.md`; `.planning/ROADMAP.md`; `KOREAN-STRUCTURE.md`] — locked product, schema, curriculum, review, scope, and phase contracts.
- [VERIFIED: `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-PATTERNS.md`] — live codebase analog map, no-touch surfaces, test assignments, and reconciled canonical slug.
- [VERIFIED: Phase 30 summary/verification] — inherited canonical `ko`, NFC, fail-closed, privacy, and no-overclaim boundaries.
- [VERIFIED: repository source/tests cited inline] — kana, phoneme, Latin source/review/audio/export, APKG/tabular, and Korean domain patterns.

### Secondary (MEDIUM confidence)

- None required; critical implementation claims were verified against official documentation, Context7, registry data, or the live repository. [VERIFIED: source audit]

### Tertiary (LOW confidence)

- None. Unresolved content/media/reviewer questions are explicitly gated rather than asserted. [VERIFIED: Open Questions]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all recommended facilities are standard library or installed project dependencies, with current registry/docs checked. [VERIFIED: environment, PyPI, Context7, and `pyproject.toml`]
- Architecture: HIGH — frozen source/review/media/export patterns have direct in-repository Latin/kana/phoneme analogs. [VERIFIED: pattern map and cited source]
- Unicode/Hangul inventory: HIGH — official Unicode and NIKL sources define the machine and modern-letter invariants. [CITED: Unicode and NIKL sources above]
- P0-P13 item-level phonetics: MEDIUM — stage coverage is locked and normative sources are available, but exact atomization, IPA/surface forms, P11 reductions, P12 recordings, and P13 ordering items still need specialist review. [VERIFIED: `KOREAN-STRUCTURE.md:147-175`; Open Questions]
- Media/audio readiness: LOW until human gates — no approved Phase 31 media manifest, asset-license decision, reviewer identities, or exact playback hashes currently exist. [VERIFIED: Phase 31 directory and data audit]
- Pitfalls/security: HIGH — each is grounded in live anti-patterns, project policy, official docs, or loaded security rules. [VERIFIED: cited sources]

**What might have been missed review:** The audit explicitly checked runtime/provider scope, Unicode/display boundaries, graph semantics, active rules, content/media licensing, Portuguese policy, exact-byte audio review, APKG/text media behavior, missing local tools, human evidence, existing-mode regressions, and confirmed that the Phase 31 slug mismatch is reconciled with `i-plus-1` canonical. Remaining uncertainty is listed rather than hidden. [VERIFIED: research checklist completed 2026-08-04]

**Research date:** 2026-08-04
**Valid until:** 2026-08-11 for Azure voice/catalog details; Unicode, NIKL, repository architecture, and package-lock recommendations remain usable longer if no relevant source changes. [CITED: Azure page update cadence; official stable Unicode UAX status]
