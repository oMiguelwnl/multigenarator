---
phase: 30-korean-contracts-and-morphology
verified: 2026-08-04T21:01:40Z
status: passed
assurance: self_checked
score: 30/30 merged must-haves verified
overrides_applied: 0
---

# Phase 30: Korean Contracts and Morphology Verification Report

**Phase Goal:** Users can select Korean throughout the modern pipeline and receive deterministic NFC-normalized, morphology-aware processing without regressing existing modes.
**Verified:** 2026-08-04T21:01:40Z
**Status:** passed
**Re-verification:** No — initial verification

## Phase Summary

Phase 30 achieved its bounded goal. Canonical `ko` routing, pinned lazy Kiwi analysis, NFC/source-backed lexical identity, all three modern ingestion modes, strict morpheme-signature validation, persistence, provider/cache boundaries, privacy, and generic tag/field compatibility are implemented and wired. No Korean frequency asset, production voice, Tatoeba mapping, Korean-specific template, or final export-readiness claim was introduced; those remain explicitly assigned to later phases.

## Goal Achievement

### Observable Truths

The five Roadmap success criteria were merged with the eight plans' frontmatter truths. Clear restatements were deduplicated, leaving 30 independently checkable must-haves.

| # | Truth | Status | Evidence |
|---:|---|---|---|
| 1 | `ko` is the sole public/internal Korean identity and `ko-KR` occurs only at the explicit locale boundary. | ✓ VERIFIED | `domain/korean.py:19-22`; production scanner found only `KOREAN_PROVIDER_LOCALE`; focused suite passed. |
| 2 | Requests accept `ko` for frequency, word-list, and Kindle-highlight modes and reject `ko-KR`. | ✓ VERIFIED | `domain/jobs.py:12-35`; `tests/domain/test_jobs.py`; three-mode integration passed. |
| 3 | Settings expose `ko` once while keeping it separate from approved frequency-asset languages. | ✓ VERIFIED | `settings.py:11-70`; `tests/test_settings.py`; `tests/services/test_korean_language_support.py`. |
| 4 | Kiwi analyzer/model dependencies are pinned and installed exactly at `0.23.2`/`0.23.0`. | ✓ VERIFIED | `pyproject.toml:35-36`, lock check, and isolated Python 3.12 import/version command passed. |
| 5 | Build/check-all excludes Korean and explicit Korean asset operations fail before filesystem/provider work. | ✓ VERIFIED | `build_frequency_assets.py:54-73`; no `assets/frequency/ko`; no-side-effect tests passed. |
| 6 | Korean has no guessed production voice and no Tatoeba fallback/network access. | ✓ VERIFIED | `audio_voice_registry.py:150-177`; `tatoeba_sentence_source.py:190-200`; counting-provider tests passed. |
| 7 | Korean canonicalization preserves submitted evidence, rejects compatibility/halfwidth Hangul, and produces NFC-stable keys. | ✓ VERIFIED | `domain/korean.py:109-167`; domain/parser/fingerprint tests passed. |
| 8 | A resolved identity requires canonical lemma, lexical POS, source sense, register, ordered signature, and complete analyzer fingerprint. | ✓ VERIFIED | `domain/korean.py:170-400`; invalid-construction tests passed. |
| 9 | Real pinned Kiwi resolves nouns with particles, regular/irregular/adjectival predicates, compound predicates, and NFC/NFD equivalents. | ✓ VERIFIED | `korean_morphology.py`; real-library goldens in `test_korean_morphology.py`; Python 3.12 smoke passed. |
| 10 | Inflections match complete ordered same-eojeol signatures while POS homographs and split compounds do not cross-match. | ✓ VERIFIED | `korean_morphology.py:181-252`; `먹다`, `듣다`, `예쁘다`, `공부하다`, and `배우` goldens passed. |
| 11 | Top-two disagreement, OOV, unavailable analysis, malformed identity, and fingerprint drift are typed non-passing outcomes. | ✓ VERIFIED | `korean_morphology.py:119-252`; real `Token.oov=True` and negative tests passed. |
| 12 | Shared lexical candidates carry optional typed Korean identity without breaking non-Korean constructors. | ✓ VERIFIED | `domain/lexicon.py:56-83`; domain and full regression suites passed. |
| 13 | Korean lexical lookup exposes deterministic multi-record POS/sense inventories while preserving legacy lookup behavior. | ✓ VERIFIED | `lexical_lookup.py:67-157`; lookup tests passed. |
| 14 | NFC/NFD word-list forms share display/item/run identity while preserving submitted form and first-seen order. | ✓ VERIFIED | `word_list_parser.py:154-205`; `input_fingerprint.py:12-49`; focused tests passed. |
| 15 | Typed Korean identity survives commit, `expire_all()`, reload, and Pydantic restoration exactly. | ✓ VERIFIED | `lexical_repository.py:187-246`; repository test and three-mode integration passed. |
| 16 | The nullable JSON migration is linear, legacy-NULL compatible, downgrade/re-upgrade safe, and ORM-parity clean. | ✓ VERIFIED | revision `20260804_17`; sole-head check returned `['20260804_17']`; migration tests passed. |
| 17 | Grounding binds only when source-lemma analysis and both surface alternatives select the same exact source lemma/POS/sense by full signature. | ✓ VERIFIED | `lexical_grounding.py:211-647`; real compound, disagreement, missing-source, POS/sense, OOV, and drift tests passed. |
| 18 | Frequency fixtures, custom word lists, and highlights persist the same identity shape and Portuguese output policy. | ✓ VERIFIED | `lexical_grounding.py:658-938`; `ingest_lexical_items.py`; offline three-mode integration passed. |
| 19 | Korean highlights retain one-syllable lexemes, remove attached particles/endings from identity, preserve compounds, and separate homographs. | ✓ VERIFIED | Korean-first extraction in `highlight_candidate_extraction.py:56-253`; grounding and integration tests passed. |
| 20 | Preview and ingestion share one resolver and expose only safe counts/hashes/indexes/canonical identity on public boundaries. | ✓ VERIFIED | `highlight_import_preview.py`; `ingest_lexical_items.py:83-205`; privacy tests and public-persistence inspection passed. |
| 21 | Korean definition/sentence requests receive the exact persisted identity; non-Korean requests carry no Korean field. | ✓ VERIFIED | `text_generation.py:42-149`; request and grounding handoff tests passed. |
| 22 | POS/sense/signature differences isolate serialized requests, prompts, and cache keys. | ✓ VERIFIED | request dump/cache-key tests; `_cache_key_for_request` hashes the complete Pydantic dump. |
| 23 | Korean prompts identify `Korean (ko)`, carry controlled source evidence, and delimit bounded/redacted highlight context as untrusted. | ✓ VERIFIED | `provider_text_adapters.py:416-572`; prompt-injection/privacy tests passed. |
| 24 | Korean provider output is NFC/script-checked before cache write and after cache restore; forbidden compatibility output is rejected. | ✓ VERIFIED | `text_generation.py:391-420,528-545`; adapter/cache tests passed. |
| 25 | Korean validation branches before generic matching and accepts only a typed `matched` result with equal fingerprint. | ✓ VERIFIED | `text_validation.py:287-420`; counting fakes prove zero generic calls; all non-matched states fail. |
| 26 | Initial generation, retry, and regeneration restore the same identity, remain review-required on failure, and never use Korean Tatoeba. | ✓ VERIFIED | `generate_text_items.py:301-500`; `regenerate_text_item.py:30-109`; focused tests passed. |
| 27 | Runtime grounding, normal validation, and regeneration share one lazy Korean morphology service; unavailable Korean analysis does not block non-Korean startup. | ✓ VERIFIED | `runtime.py:523-626`; object-identity/laziness tests passed. |
| 28 | Local and WebDAV Korean previews reuse the source-aware resolver, remain count-only, and fail with content-free output. | ✓ VERIFIED | `cli.py:439-579,627-717`; both CLI suites passed. |
| 29 | Real offline orchestration for all three modes survives database reload and uses persisted identity for strict match/review and privacy outcomes. | ✓ VERIFIED | `tests/integration/test_korean_modern_flow.py`; all four integration tests passed. |
| 30 | Existing fields, blank `Image`, exact `ko` tags, language/source/template/audio/persistence/export behavior, lock, migrations, and full regressions remain green. | ✓ VERIFIED | No exporter/template source changed; named matrix 36/36 and full suite 1168/1168 passed. |

**Score:** 30/30 merged truths verified

## Required Artifacts

`gsd-tools verify artifacts` reported **31/31 present and substantive**. Manual inspection and runtime/integration evidence established wiring rather than relying on existence alone.

| Plan | Artifact Set | Exists/Substantive | Wired | Details |
|---|---|---:|---:|---|
| 30-01 | `pyproject.toml`, `jobs.py`, `settings.py`, asset builder | 4/4 | ✓ | Exact pins, enum/settings, approved-assets tuple, and pre-write license gate are exercised. |
| 30-02 | voice/Tatoeba boundaries, `domain/korean.py`, morphology service, domain/morphology tests | 6/6 | ✓ | Project-owned models receive real lazy Kiwi projections and strict matching. |
| 30-03 | lexicon, lookup, migration, repository, repository tests | 5/5 | ✓ | Typed JSON crosses ORM commit/expire/reload and migration lifecycle. |
| 30-04 | grounding, highlight domain/extraction/preview, ingestion | 5/5 | ✓ | All three modes use source-backed identity and shared privacy-safe resolution. |
| 30-05 | text generation, provider adapters, grounding handoff | 3/3 | ✓ | Identity reaches typed requests/prompts/cache and output normalization. |
| 30-06 | validator, generation, regeneration | 3/3 | ✓ | Persisted identity gates every attempt before generic fallbacks. |
| 30-07 | runtime, CLI, runtime tests | 3/3 | ✓ | One lazy service is shared; local/WebDAV previews are wired. |
| 30-08 | modern-flow integration and canonical contract scanner | 2/2 | ✓ | Offline closure exercises production orchestration, persistence, matcher, privacy, and generic tags. |

## Key Link Verification

The literal-path `gsd-tools` heuristic reported 0/25 because several frontmatter links name symbols/behaviors rather than literal target paths. Each link was therefore traced manually through imports, constructor injection, calls, persistence, and passing tests.

| Plan | From → To | Status | Manual Evidence |
|---|---|---|---|
| 30-01 | settings/jobs → asset builder/request tests (2 links) | ✓ 2/2 | Builder imports `APPROVED_FREQUENCY_ASSET_LANGUAGES`; request tests exercise all three modes and locale rejection. |
| 30-02 | language/provider boundaries and morphology → domain/Kiwi/signature matcher (4 links) | ✓ 4/4 | Controlled voice/Tatoeba branches, domain-model imports, exact factory/options, and full-signature comparison are present. |
| 30-03 | candidate → Korean domain; repository → ORM; parser → fingerprint; migration → parity tests (4 links) | ✓ 4/4 | Typed imports/serialization, shared NFC rule, and migration tests are direct. |
| 30-04 | grounding → lookup; extraction/preview → resolver; ingestion → repository (4 links) | ✓ 4/4 | Source inventory is analyzed and selected; injected resolver output is persisted by the shared repository. |
| 30-05 | candidate → typed requests/prompts/cache (3 links) | ✓ 3/3 | `from_candidate`, definition handoff, complete request dump, and pre-cache normalization are wired. |
| 30-06 | DB restoration → validation; validator → matcher; regeneration → validator (3 links) | ✓ 3/3 | `_to_candidate` restores identity and both generation services call the shared strict validator. |
| 30-07 | runtime → grounding/validation; CLI → preview (2 links) | ✓ 2/2 | The same object is injected; closure-scoped/injected resolver is passed to preview. |
| 30-08 | three modes → DB identity → strict validation → generic fields/tags (3 links) | ✓ 3/3 | Disposable SQLite integration expires/reloads rows before match/review and generic note assertions. |

## Data-Flow Trace (Level 4)

| Artifact/Behavior | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| Three-mode ingestion | `LexicalCardCandidate.korean_identity` | Validated local lexical index + real Kiwi + existing ingestion services | Yes; fixture records are source-backed and cross real SQLite lifecycle | ✓ FLOWING |
| Strict sentence validation | persisted `morpheme_signature`/fingerprint | Reloaded `lexical_candidates.korean_identity` → shared matcher | Yes; real Kiwi analyzes sentences and controls accepted/review-required state | ✓ FLOWING |
| Korean highlights | resolved lexemes and safe provenance | Private parsed highlights → local resolver → public candidate hashes/identity | Yes; raw text remains private while source-backed identities persist | ✓ FLOWING |
| Provider/cache boundary | typed identity and generated sentence | Grounded candidate → typed request/prompt/cache → canonical result | Yes; offline provider fake replaces only external network, not internal wiring | ✓ FLOWING |
| Generic field/tag compatibility | persisted job/candidate identity | Reloaded representative rows → existing field resolver/note builder | Yes for compatibility evidence; final Korean templates/APKG are intentionally later scope | ✓ FLOWING |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Complete Phase 30 focused evidence | `uv run pytest <27 Phase 30 files> -q` | 401 passed, 10 third-party warnings | ✓ PASS |
| Existing-mode regression matrix | `uv run --extra dev pytest <named matrix> -q` | 36 passed, 3 third-party warnings | ✓ PASS |
| Real pinned Kiwi under Python 3.12 | isolated `UV_PROJECT_ENVIRONMENT=... uv run --extra dev --python 3.12 pytest ... -k test_real_kiwi_python312_smoke...` | 1 passed, 23 deselected | ✓ PASS |
| Exact lock/package versions and Alembic head | `uv lock --check`; Python version/import assertions; `ScriptDirectory.get_heads()` | Python 3.12.13, Kiwi 0.23.2/model 0.23.0, head `20260804_17` | ✓ PASS |
| Full project regression | `uv run --extra dev pytest -q` | 1168 passed, 17 third-party warnings | ✓ PASS |
| Diff whitespace integrity | `git diff --check` | Exit 0; only Git LF→CRLF notices | ✓ PASS |
| GSD phase artifact/UI gate | `node .planning/bin/gsdd.mjs verify 30` | All planned artifacts present; UI proof correctly `not_applicable`; no blockers | ✓ PASS |

One initial parallel verifier attempt was discarded as invalid because multiple `uv` commands contended for the editor-held shared `.venv`. Commands were rerun serially; Python 3.12 used the existing isolated Phase 30 environment. This was verifier/environment contention, not a product failure.

## Requirements Coverage

Active v3.0 requirements are canonical in `.planning/SPEC.md`; `.planning/REQUIREMENTS.md` is explicitly a legacy v2.0/v2.1 archive and maps no Phase 30 requirements. All four active Phase 30 IDs are claimed across the plan set, so no orphaned Phase 30 requirement exists.

| Requirement | Source Plans | Status | Evidence |
|---|---|---|---|
| KMODE-01 | 30-01 through 30-05, 30-07, 30-08 | ✓ SATISFIED | Canonical request/settings/runtime/provider/cache/DB/tag identity and all three modes are verified. |
| KMODE-02 | 30-01 through 30-08 | ✓ SATISFIED | Additive nullable contracts, lazy isolation, no-touch exporter/templates, named regressions, and full suite pass. |
| KNLP-01 | 30-01 through 30-08 | ✓ SATISFIED | Exact pins/options, NFC/script contracts, real linguistic goldens, source identity, and reload persistence pass. |
| KNLP-02 | 30-02 through 30-08 | ✓ SATISFIED | Ordered same-eojeol signatures, top-two consensus, inflection/homograph evidence, and fail-closed validation pass. |

## Anti-Patterns Found

| File/Scan | Pattern | Severity | Impact |
|---|---|---|---|
| Phase 30 production surfaces | TODO/FIXME/placeholder/NotImplemented/empty user-visible implementation | None | No stubs found. Empty returns reviewed were legitimate parser or fail-closed branches. |
| Production source/scripts | `ko-KR` outside locale allowlist | None | Exactly one explicit locale constant occurrence. |
| Production source/tests | Multiple eager/per-item `Kiwi(...)` constructions | None | One production lazy factory; the other constructor is the real-test helper. |
| Assets/providers/exporters | Korean asset, guessed voice, Tatoeba `kor`, exporter/template mutation | None | None found; later-phase boundaries remain intact. |
| Test output | Deprecation/Syntax warnings in third-party packages/Alembic config | ℹ️ Info | No Phase 30 failure; 1168 tests passed. |

## Human Verification Required

None. Phase 30 makes backend contract, persistence, privacy, and offline integration claims only; it explicitly excludes rendered UI, Anki visual acceptance, live provider quality, production Korean audio, and final APKG readiness.

## Delivery Metadata

- Canonical branch: `Monarch`
- Verification baseline: `240b21abb8efce5e028fd0b80d1767cbcac0f145`
- Worktree: expected dirty repo-only Phase 30 implementation/planning set; no staged changes
- Verification report: `.planning/phases/30-korean-contracts-and-morphology/30-VERIFICATION.md`
- Commit/push: intentionally not performed
- Lifecycle update: `node .planning/bin/gsdd.mjs phase-status 30 done` returned `changed: true`; both Phase 30 Roadmap markers are `[x]`, and control-map now reports `next_phase: 31`

## Gaps Summary

No actionable Phase 30 gaps remain. Production Korean frequency licensing/content, approved audio, curriculum decks, final templates/APKGs, and visual/import evidence are explicit Phase 31-34 work, not deferred defects in this phase's bounded goal.

---

_Verified: 2026-08-04T21:01:40Z_
_Verifier: the agent (gsd-verifier)_
