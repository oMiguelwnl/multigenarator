---
phase: 32-frequency-portuguese-text-and-audio
plan: "05"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 05 Summary

**Completed**: 2026-08-29
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: Recoverable factual discoveries only. Existing runtime tests already proved one shared lazy Kiwi across grounding/generation/regeneration, so Plan 32-05 extended runtime with explicit Korean final entries plus source-review receipt inputs instead of constructing another analyzer path. `src/multilang/services/lexical_grounding.py` did not require a new edit because Plan 32-04 already made grounded Korean final candidates pass through without seed grounding or reanalysis. Sparse legacy adaptive evidence remains readable while new expanded evidence enforces sorted known concepts and observed incidental concepts.
**Decisions Made**: No source-rights, provider, Azure, production database, review approval, release, publication, or live authority decisions. Added only offline deterministic composition, prefix evidence, and hard-gate contracts.
**Notes for Verification**: This summary proves synthetic explicit-entry runtime ingestion, lazy one-Kiwi preservation, path-free frozen-prefix hashing, evidence reload, hard-gate-before-score ordering, and non-NFC Korean rejection. It does not prove real Phase 31 activation, genuine 3000-entry source approval, provider calls, Azure catalog/synthesis, human/provider review acceptance, production DB migration, APKG import/playback, or publication readiness.
**Notes for Next Work**: Continue offline Phase 32 lanes only. Runtime Korean final ingestion must receive explicit frozen entries and source-review receipt hashes, or use the existing `load_korean_final_frequency_entries` authority loader before runtime composition; it must not discover authority from mutable settings or live `wordfreq`.

## Completed Work

- Added `tests/services/test_korean_text_quality.py` and `src/multilang/services/korean_text_quality.py` for frozen-prefix known-state evidence and hard-gate-first Korean candidate selection.
- Extended `KoreanAdaptiveIPlusOneEvidence` with sorted `known_concept_ids`, `known_concept_count`, Phase 31 pointer/receipt/snapshot hashes, frequency bundle hashes, candidate hash, selected ordinal, hard-gate codes, score components, and policy version.
- Added `korean_lexical_concept_id`, `KOREAN_LEXICON_CONCEPT_PREFIX`, and `KOREAN_TEXT_QUALITY_POLICY_VERSION` to Korean domain contracts.
- Extended `build_runtime_service` and `RuntimeGenerateService` with explicit Korean final frequency entries and source-review receipts, preserving non-Korean paths and the existing one lazy `KiwiKoreanMorphologyService` shared by grounding, generation validation, and regeneration validation.
- Added Korean runtime ingestion regression proving explicit final entries do not use mutable settings frequency assets or live wordfreq authority.
- Added repository persistence coverage for expanded adaptive evidence reloads.
- Updated Korean language detection to reject non-NFC Hangul without echoing learner text.

## One-Kiwi Proof

- Existing and rerun runtime tests prove injected Korean morphology is the same object in `grounding_service`, `generate_text_items_service.text_validation_service`, and `regenerate_text_item_service.text_validation_service`.
- Default runtime construction creates exactly one lazy `KiwiKoreanMorphologyService`; vendor analyzer construction is deferred until Korean analysis is requested.
- Unavailable Korean analyzer construction does not block non-Korean startup.

## Frozen Prefix Proof

- Rank 1 known state is active Phase 31 foundation concept IDs only.
- Rank `n` known state uses exactly frozen Korean lexical concept IDs for ranks `1..n-1`, sorted into canonical `known_concept_ids` with a count and hash.
- The prefix hash binds Phase 31 pointer locator/content, validation receipt, snapshot manifest/root, frequency bundle locator/content, target rank, foundation IDs, and prior lexical IDs.
- Reordered input entries produce the same prefix hash; missing lower ranks, duplicate known concepts, and Phase 31 receipt drift fail closed.

## Gate Matrix

- `selected_morphology_mismatch`: non-selectable; no adaptive evidence or score components are produced.
- `selected_morphology_inconclusive`: non-selectable through typed/equal-fingerprint selected-Kiwi checks.
- `nfc_or_script` and `language`: non-selectable before scoring.
- `source_sense_mismatch`: non-selectable when intended sense evidence conflicts with the frozen target sense.
- `register_policy`: non-selectable for default-policy formal/plain markers without explicit exception evidence.
- `template_naturalness`: non-selectable for meta/template text patterns.
- `translation_consistency`: non-selectable for empty, copied, or provider-error-like translations.
- Passing machine evidence returns `review_status="review_required"`; it does not approve learner-ready text.

## TDD Evidence

- Task 32-05-01 RED: runtime test failed with `TypeError: build_runtime_service() got an unexpected keyword argument 'korean_final_frequency_entries'`. GREEN: added explicit Korean final-entry/source-review runtime composition and Korean-specific grounded-frequency override.
- Task 32-05-02 RED: new Korean text-quality tests failed with `ModuleNotFoundError: multilang.services.korean_text_quality`, and repository test failed on extra adaptive evidence fields. GREEN: added the service and expanded evidence model with reload coverage.
- Task 32-05-03 RED: Korean language check accepted decomposed Hangul. GREEN: `detect_language_mismatch(... expected_language="ko")` now rejects non-canonical Korean text without echoing content; hard-gate service blocks failures before scoring.

## Verification

- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/test_runtime.py -k 'korean and (locator or one or lazy or frequency or unavailable)' -q` -> `4 passed, 9 deselected`.
- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_frequency_decks.py -k 'supported_frequency_assets' -q` -> `1 passed, 27 deselected`.
- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_text_quality.py -k 'known_state or frozen_prefix or rank_boundary or text_status_independent or incidental' -q` -> `4 passed, 3 deselected`.
- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_text_repository.py -k 'adaptive or prefix' -q` -> `1 passed, 3 deselected`.
- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_text_quality.py -k 'hard_gate or register or naturalness or sense or review' -q` -> `3 passed, 4 deselected`.
- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_text_validation.py -k 'korean' -q` -> `24 passed, 33 deselected`.
- Full modified-file checks passed individually: `tests/test_runtime.py` -> `13 passed`; `tests/services/test_frequency_decks.py` -> `28 passed`; `tests/services/test_korean_text_quality.py` -> `7 passed`; `tests/repositories/test_text_repository.py` -> `4 passed`; `tests/services/test_text_validation.py` -> `57 passed`.
- Adjacent evidence/domain/schema checks passed: `tests/repositories/test_phase32_text_audio_evidence.py` -> `4 passed`; `tests/domain/test_text_quality.py` -> `3 passed`; `tests/test_migration_schema_parity.py` -> `12 passed, 14 warnings`.
- Final combined relevant regression passed: `tests/test_runtime.py tests/services/test_frequency_decks.py tests/services/test_korean_text_quality.py tests/repositories/test_text_repository.py tests/services/test_text_validation.py tests/repositories/test_phase32_text_audio_evidence.py tests/domain/test_text_quality.py tests/test_migration_schema_parity.py -q` -> `128 passed, 14 warnings`.
- Planning preflight allowed execution with known dirty-worktree warnings; Phase 32 remained open/in progress and session fingerprint was written after SPEC update: `ca9a69728ab14322b4fbe3cc5404bfc29db3c20f6290268fcbc686354a3039e9`.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified Plan 32-05 task surfaces offline with synthetic fixtures. No live network, provider, Azure, production DB, source retrieval, asset activation, export release, Git commit, or publication action was performed.
</executor_check>
</checks>

<handoff>
plan_runtime: opencode
plan_assurance: self_checked
plan_check_status: passed
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: false
</handoff>

<deltas>
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Preflight/control-map allowed execution but reported canonical dirty worktree state and dirty/detached sibling Phase 31 worktrees. Work stayed within Plan 32-05 source/test surfaces plus required GSDD state artifacts.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Existing runtime already used one shared lazy Korean morphology object across grounding, generation validation, and regeneration validation. Plan 32-05 added explicit Korean final-entry runtime inputs without replacing that path.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: `src/multilang/services/lexical_grounding.py` was listed as a planned modification, but Plan 32-04 already made grounded Korean final candidates pass through without seed grounding or reanalysis, so no additional edit was needed.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Expanded adaptive evidence initially over-constrained sparse legacy evidence. The validator now enforces observed incidental concepts only when expanded Phase 32 evidence fields are present, preserving older sparse rows while new service output remains fully bound.
</deltas>

<judgment>
<active_constraints>
Phase 32 remains in progress and is not phase-verified. No live source retrieval, real source transformation, final bundle activation, provider call, Azure catalog or synthesis call, production database mutation, review approval, asset commit, release, Git action, or publication is authorized by this summary. Korean final runtime must use explicit frozen entries plus source-review receipts or the existing hash-bound loader output; it must not discover Korean final authority from settings, live wordfreq, seed fallback, or provider-authored identity.
</active_constraints>
<unresolved_uncertainty>
Exact Phase 31 active snapshot, NIKL source bytes/terms/attribution, local-use and redistribution decisions, genuine transformed 3,000-entry inventory, source review, provider model/budget, Azure voice/profile/catalog, generated text/audio bytes, AI/provider/heard review outputs, production DB target authority, Anki import/playback evidence, and publication approval remain unresolved checkpoint facts.
</unresolved_uncertainty>
<decision_posture>
Continue with offline fail-closed infrastructure and bounded claims. Treat missing Korean frozen entries, source-review receipts, Phase 31 pointer/receipt/snapshot drift, frequency bundle drift, selected-Kiwi mismatch, analyzer inconclusive states, and Korean hard-gate failures as blockers rather than repair or fallback opportunities. Machine evidence can reject or require review but cannot approve learner-ready Korean text.
</decision_posture>
<anti_regression>
Do not add Korean final runtime edges to live `wordfreq`, mutable settings authority discovery, seed grounding, first-sense lookup, provider-authored identity, generic suffix rescue, Stanza fallback, raw path persistence, raw prompt/provider payload persistence, private context leakage, or GUID changes. Do not weaken one lazy shared Kiwi, canonical `ko` identity, NFC Korean checks, selected-Kiwi fail-closed target matching, frozen-prefix text-status independence, blank `Image`, stable export field order, or source-review hash requirements.
</anti_regression>
</judgment>
