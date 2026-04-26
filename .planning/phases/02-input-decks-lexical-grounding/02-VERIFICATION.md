---
phase: 02-input-decks-lexical-grounding
verified: 2026-04-21T17:32:43Z
status: verified
score: 5/5 must-haves verified
overrides_applied: 0
gaps: []
---

# Phase 2: Input Decks & Lexical Grounding Verification Report

**Phase Goal:** Users can generate grounded card candidates from either built-in frequency decks or their own word lists.
**Verified:** 2026-04-21T17:32:43Z
**Status:** verified
**Re-verification:** Yes — gap-closure verification after Plan 02-05

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Lexical candidates persist submitted text, display form, normalized lemma identity, rank, provenance, and language-policy fields. | ✓ VERIFIED | `src/multilang/domain/lexicon.py` still defines the typed lexical contract and `src/multilang/repositories/lexical_repository.py` still persists and reloads it through `lexical_candidates`; the phase-2 validation subset passed (`33 passed in 170.51s`). |
| 2 | The frequency-deck builder can deterministically produce three 1000-item levels with filtering and backfill support. | ✓ VERIFIED | `src/multilang/services/frequency_decks.py` remains the deterministic builder, and the shipped-path integration test `tests/integration/test_lexical_job_flow.py::test_generate_frequency_deck_persists_three_grounded_levels` proves 1000 grounded candidates are persisted for each level with `backfilled_candidates=4`. |
| 3 | Custom word-list ingestion preserves original submitted forms, normalized targets, and pending status instead of silently swapping misses away. | ✓ VERIFIED | `src/multilang/services/word_list_parser.py`, `src/multilang/services/lexical_grounding.py`, and `src/multilang/services/ingest_lexical_items.py` still preserve submitted forms and pending misses; shipped-path integration coverage in `tests/integration/test_lexical_job_flow.py::test_custom_word_list_preserves_pending_items` proves grounded and pending rows survive rerun and resume. |
| 4 | Grounded candidates use one deck-wide lexical format: normalized lemma, English definitions joined with `<br>`, and authoritative-only IPA/provenance. | ✓ VERIFIED | `src/multilang/services/lexical_grounding.py` still joins definitions with `<br>`, preserves authoritative-only IPA, and returns normalized lemma identity; lexical-grounding unit tests remain green in the phase-2 validation subset. |
| 5 | Shipped `multilang generate` can produce grounded candidates from either a built-in frequency deck or a custom word list using only the runtime path. | ✓ VERIFIED | `src/multilang/cli.py` now runs `_prepare_lexical_data()` before default runtime ingestion, bootstrapping the cache from `--lexicon-source-file` or exiting early with a prerequisite diagnostic. CLI and integration coverage now prove three shipped behaviors: bootstrap succeeds, missing data fails fast before ingestion, and cached runtime generation works (`tests/cli/test_generate_command.py`, `tests/integration/test_lexical_job_flow.py`). |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/multilang/domain/lexicon.py` | Typed lexical candidate contract | ✓ VERIFIED | Substantive Pydantic models and language-policy helper. |
| `src/multilang/repositories/lexical_repository.py` | Persistence boundary for lexical candidates | ✓ VERIFIED | Upsert/list/count methods backed by ORM rows. |
| `alembic/versions/20260419_02_lexical_grounding_tables.py` | Live schema for lexical candidate storage | ✓ VERIFIED | Creates `lexical_candidates` with unique `(job_id, item_key)` key and indexes. |
| `src/multilang/services/frequency_decks.py` | Curated deterministic frequency builder | ✓ VERIFIED | Filtering, level windows, and bounded backfill implemented. |
| `src/multilang/services/word_list_parser.py` | Plain-text parser with diagnostics | ✓ VERIFIED | Preserves submitted text and emits blank/duplicate warnings. |
| `src/multilang/services/kaikki_lookup.py` | Cached lexical lookup plus bootstrap | ✓ VERIFIED | `ensure_index()`/`build_index()` now serve the shipped CLI prerequisite path in addition to tests. |
| `src/multilang/services/lexical_grounding.py` | Trust-first lexical grounding | ✓ VERIFIED | Grounded/pending/backfill-required behavior implemented and tested. |
| `src/multilang/services/ingest_lexical_items.py` | Runtime coordinator for both source types | ✓ VERIFIED | Wires job orchestration, grounding, persistence, and lexical counts. |
| `src/multilang/cli.py` | Shipped CLI surface for Phase 2 | ✓ VERIFIED | `generate` now validates lexical prerequisites, bootstraps cache data from `--lexicon-source-file`, prints lexical counters, and aborts early on missing cache state. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `src/multilang/repositories/lexical_repository.py` | `src/multilang/db/models.py` | ORM-backed candidate persistence | ✓ WIRED | Repository selects/updates `LexicalCandidate` rows and reconstructs domain models. |
| `src/multilang/runtime.py` | `src/multilang/services/ingest_lexical_items.py` | Shipped runtime service construction | ✓ WIRED | `build_runtime_service()` returns `IngestLexicalItemsService(...)`. |
| `src/multilang/services/ingest_lexical_items.py` | `src/multilang/services/lexical_grounding.py` | Grounding frequency and word-list inputs | ✓ WIRED | Calls `ground_word_list_item()` and `ground_frequency_candidate()` during ingestion. |
| `src/multilang/services/lexical_grounding.py` | `src/multilang/services/kaikki_lookup.py` | Cached lexical lookup | ✓ WIRED | Runtime builder constructs `KaikkiLookup`; `_lookup_record()` calls `lookup()`. |
| `src/multilang/services/kaikki_lookup.py` | shipped runtime/CLI path | Cache/index bootstrap | ✓ WIRED | `src/multilang/cli.py::_prepare_lexical_data()` calls `KaikkiLookup.ensure_index(...)` on the default runtime path. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `src/multilang/services/ingest_lexical_items.py` | `candidates`, `grounded_candidates`, `pending_groundings` | `LexicalRepository.list_candidates()` / `count_pending_candidates()` over `lexical_candidates` DB rows | Yes | ✓ FLOWING |
| `src/multilang/services/lexical_grounding.py` | `record` | `KaikkiLookup.lookup(language_code, term)` reading `lexicon/<lang>/kaikki-index.json` | Yes — cached index is either pre-existing or bootstrapped from `--lexicon-source-file` before ingestion starts | ✓ FLOWING |
| `src/multilang/cli.py` | lexical counter output | `IngestLexicalItemsResult` from runtime coordinator | Yes — default runtime path now reaches real grounded, pending, and backfill counts | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Custom word-list runtime works when cached lexical data exists | `uv run pytest tests/integration/test_lexical_job_flow.py::test_custom_word_list_preserves_pending_items -q` | `1 passed`; shipped path preserved `grounded_candidates=3`, `pending_groundings=1`, and stable rows across rerun/resume | ✓ PASS |
| Frequency runtime works when cached lexical data exists | `uv run pytest tests/integration/test_lexical_job_flow.py::test_generate_frequency_deck_persists_three_grounded_levels -q` | `1 passed`; shipped path persisted `grounded_candidates=3000`, `level_1/2/3=1000`, `backfilled_candidates=4` | ✓ PASS |
| Clean runtime can bootstrap lexical data on demand | `uv run pytest tests/integration/test_lexical_job_flow.py::test_generate_frequency_deck_bootstraps_lexicon_from_local_archive -q` | `1 passed`; shipped path created `lexicon/en/kaikki-index.json` and completed generation successfully | ✓ PASS |
| Clean runtime fails fast without lexical data | `uv run pytest tests/cli/test_generate_command.py::test_generate_command_fails_fast_when_lexical_data_is_missing tests/integration/test_lexical_job_flow.py::test_generate_frequency_deck_fails_fast_without_lexicon_data -q` | `2 passed`; exit `1` with explicit `--lexicon-source-file` guidance and no persisted job/candidate rows | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| DECK-02 | 02-02, 02-04, 02-05 | User can generate a frequency deck with 3 levels of 1000 cards each. | ✓ SATISFIED | Deterministic builder, shipped-path integration persistence, and clean-runtime bootstrap/fail-fast coverage are all green. |
| DECK-03 | 02-01, 02-03, 02-04, 02-05 | User can generate cards from a custom word list instead of the built-in deck. | ✓ SATISFIED | Parser, grounding, pending persistence, rerun/resume behavior, and clean-runtime lexical prerequisite handling are all verified on the shipped path. |
| LEX-01 | 02-01, 02-03, 02-04 | User receives a normalized base word and frequency rank where applicable. | ✓ SATISFIED | Contracts, repository rows, frequency builder, and grounding service preserve lemma/lemma_key/rank metadata. |
| LEX-02 | 02-01, 02-03, 02-04, 02-05 | User receives IPA in one consistent display format. | ✓ SATISFIED | Grounding preserves authoritative-only IPA, and the shipped runtime now guarantees either a usable cache or an explicit prerequisite failure before generation starts. |
| LEX-03 | 02-01, 02-03, 02-04, 02-05 | User receives consistent deck-wide definitions. | ✓ SATISFIED | Definitions remain English `<br>`-joined output, and the shipped runtime now exposes a complete path to grounded lexical data. |

### Anti-Patterns Found

No blocking anti-patterns were found in the Phase 2 scope during this re-verification.

### Gaps Summary

Phase 2 now verifies cleanly. The earlier shipped-path gap is closed: the default `multilang generate` command checks for language cache availability, bootstraps it from a local Kaikki archive when `--lexicon-source-file` is provided, and otherwise fails fast with a clear prerequisite diagnostic before any ingestion work starts. The lexical contract, persistence layer, deterministic frequency builder, custom word-list parser, trust-first grounding rules, and shipped-path CLI/integration flows are all backed by green targeted validation and a green full test suite.

---

_Verified: 2026-04-21T17:32:43Z_
_Verifier: the agent (gsd-verifier)_
