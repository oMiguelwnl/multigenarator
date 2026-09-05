---
phase: 32-frequency-portuguese-text-and-audio
plan: "06"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 06 Summary

**Completed**: 2026-08-29
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: Recoverable factual discoveries only. DeepL already mapped canonical `pt` to provider `PT-BR`; Plan 32-06 preserved that mapping and added explicit canonical/cache `pt` provenance plus a versioned Brazilian-Portuguese editorial policy ID. Provider call repository code already had route/budget/cache/schema hash aggregation and redacted error summaries, so Plan 32-06 added telemetry regression coverage without editing the undeclared repository implementation file.
**Decisions Made**: No live provider/model, budget approval, source-rights, Azure, production database, review approval, export, release, Git, or publication authority was created. Environment settings can propose Korean provider policy metadata only; they cannot approve live provider use.
**Notes for Verification**: This summary proves offline schemas and deterministic behavior only: immutable qualified human text-review contracts, strict Korean provider output handling, canonical `pt` with DeepL `PT-BR` metadata, hard-gate-only candidate scoring, and no-fallback route/budget/cache/result-summary contracts. It does not prove real provider calls, model quality, human review acceptance, live Azure catalog/synthesis, production DB persistence of new provider policy objects, or publication readiness.
**Notes for Next Work**: Continue offline Phase 32 lanes only. Later review/import work must consume the new review decision schemas explicitly; these contracts intentionally grant no DB mutation, promotion, export, release, or approval power by themselves.

## Completed Work

- Added strict frozen `KoreanTextReviewQualification`, `KoreanTextReviewCoverage`, `KoreanTextReviewDecision`, and `KoreanTextReviewRejection` schemas in `src/multilang/domain/text_quality.py`.
- Added `KoreanTextCandidate` and deterministic `KoreanTextQualityService.select_best_candidate(...)` so only hard-gate passers score, incidental novelty is minimized, and ties use candidate hash then ordinal.
- Expanded Korean translation hard gates for `unsafe_markup`, `english_leakage`, and `isolated_word_translation` while preserving existing morphology, sense, register, language, and template gates.
- Tightened Korean LiteLLM response handling to reject unexpected sentence/definition keys and unsafe Korean definition markup without echoing raw provider content.
- Added `KOREAN_PT_BR_EDITORIAL_POLICY_ID` and DeepL provenance fields that keep canonical/cache language as `pt` while provider boundary uses `PT-BR`.
- Created `src/multilang/domain/korean_provider.py` with offline frozen route, budget, retry, cache-key, policy, result-summary, and settings-proposal contracts.
- Added proposal-only Korean provider settings: `korean_provider_policy_version` and `korean_provider_max_attempts`.
- Added tests for provider telemetry denominators and hash aggregation without raw prompt/output/private context fields.

## Review Schema

| Contract | Authority | Required Binding | Fail-Closed Checks |
|---|---|---|---|
| `KoreanTextReviewQualification` | qualified human identity only | reviewer kind/role plus reviewer, qualification policy, and qualification receipt hashes | machine/model reviewer kind, extra fields, bad hashes |
| `KoreanTextReviewCoverage` | controlled checklist only | target identity, source sense, morphology, natural Korean, pt-BR translation, adaptive i+1, private context, unsafe markup | incomplete acceptance coverage, non-boolean coercion, extra notes |
| `KoreanTextReviewDecision` | review record only | production/job/run/item/candidate/identity/policy/evidence-root hashes | stale identity, accepted+rejection contradiction, rejected without codes, mutation attempt |
| `KoreanTextReviewRejection` | review rejection record only | same decision hashes plus controlled rejection codes | missing/duplicate/unsafe codes, extra/private fields |

## pt/PT-BR Matrix

| Surface | Stored/Domain Code | Provider/Editorial Boundary | Evidence |
|---|---|---|---|
| Korean request target | `pt` | `pt` requirement validation | existing Korean request tests |
| DeepL call | `pt` in request/cache provenance | `PT-BR` target language | `test_deepl_korean_PT_BR_policy_keeps_canonical_pt_cache_identity` |
| Translation provenance | `canonical_target_language=pt`, `cache_target_language=pt` | `editorial_policy_id=korean-pt-br-editorial-policy-v1` | provider adapter tests |
| Text quality gates | canonical Korean identity unchanged | rejects English leakage, isolated-word translation, unsafe markup | Korean text-quality tests |

## Route And Budget Table

| Task Vocabulary | Route Contract | Budget Contract | Fallback |
|---|---|---|---|
| `definition` | provider/model or disabled | attempts, token, cost, latency, timeout, batch, concurrency | `none` only |
| `sentence_generation` | provider/model or disabled | same bounded budget fields | `none` only |
| `repair` | provider/model or disabled | same bounded budget fields | `none` only |
| `translation` | provider/model or disabled | same bounded budget fields | `none` only |
| `judge` | provider/model or disabled | same bounded budget fields | `none` only |
| `catalog` | provider/model or disabled | same bounded budget fields | `none` only |
| `word_audio` | provider/model or disabled | same bounded budget fields | `none` only |
| `sentence_audio` | provider/model or disabled | same bounded budget fields | `none` only |

## Privacy And Telemetry

- `KoreanProviderResultSummary` allows only controlled task/provider/status/denominator, hash, token, cost, and latency fields; raw prompts, outputs, private roots, credentials, and exceptions are rejected as extras.
- `KoreanProviderRoute` rejects credential-looking provider/model identifiers and computes route, budget, and cache hashes from controlled metadata only.
- `ProviderCallLogRepository` regression coverage proves summaries aggregate route/budget/cache/schema hashes, token/cost denominator counts, and redacted failure summaries without prompt/output attributes.

## TDD Evidence

- Task 32-06-01 RED: review tests failed with missing `KoreanTextReviewDecision`, `KoreanTextReviewCoverage`, and related classes. GREEN: added immutable human review qualification, coverage, decision, and rejection schemas.
- Task 32-06-02 RED: Korean text-quality tests showed English leakage was selectable and `KoreanTextCandidate` was missing; provider tests showed extra Korean output was accepted and `KOREAN_PT_BR_EDITORIAL_POLICY_ID` was missing. GREEN: added translation hard gates, deterministic selector, strict Korean output checks, and pt/PT-BR provenance metadata.
- Task 32-06-03 RED: provider policy tests failed with missing `multilang.domain.korean_provider`. GREEN: added offline route/budget/policy/result/proposal contracts and proposal-only settings.

## Verification

- RED observed: `tests/services/test_korean_text_quality.py -k 'review_decision or rejection or role or coverage or immutable or authority_separation'` -> `2 failed, 9 deselected` before implementation.
- RED observed: `tests/services/test_korean_text_quality.py -k 'pt_br or translation or score or tie or hard_gate'` -> `2 failed, 3 passed, 6 deselected` before implementation.
- RED observed: `tests/services/test_provider_text_adapters.py -k 'korean or PT_BR or canonical_pt'` -> `2 failed, 9 passed, 12 deselected` before implementation.
- RED observed: `tests/domain/test_korean_provider_policy.py -k 'route or budget or denominator or privacy or fallback'` -> `2 failed, 1 deselected` before implementation.
- RED observed: `tests/repositories/test_provider_call_log_repository.py -k 'route or cache or token or cost or latency or redaction'` -> `1 passed, 2 deselected`; repository behavior already existed and was locked by regression coverage.
- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_text_quality.py -k 'review_decision or rejection or role or coverage or immutable or authority_separation' -q` -> `2 passed, 9 deselected`.
- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_text_quality.py -k 'pt_br or translation or score or tie or hard_gate' -q` -> `5 passed, 6 deselected`.
- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_provider_text_adapters.py -k 'korean or PT_BR or canonical_pt' -q` -> `11 passed, 12 deselected`.
- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_korean_provider_policy.py -k 'route or budget or denominator or privacy or fallback' -q` -> `2 passed, 1 deselected`.
- Plan command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_provider_call_log_repository.py -k 'route or cache or token or cost or latency or redaction' -q` -> `1 passed, 2 deselected`.
- Modified-file checks passed: `tests/services/test_korean_text_quality.py` -> `11 passed`; `tests/services/test_provider_text_adapters.py` -> `23 passed`; `tests/domain/test_korean_provider_policy.py` -> `3 passed`; `tests/repositories/test_provider_call_log_repository.py` -> `3 passed`; `tests/domain/test_text_quality.py tests/repositories/test_phase32_text_audio_evidence.py` -> `7 passed`.
- Final combined relevant regression passed: `tests/services/test_korean_text_quality.py tests/services/test_provider_text_adapters.py tests/domain/test_korean_provider_policy.py tests/repositories/test_provider_call_log_repository.py tests/domain/test_text_quality.py tests/repositories/test_phase32_text_audio_evidence.py tests/test_runtime.py tests/test_migration_schema_parity.py -q` -> `72 passed, 14 warnings`.
- Planning preflight allowed execution with known dirty-worktree warnings; Phase 32 remained open/in progress and session fingerprint was written after SPEC update: `3530ec196267541f19b2f3ac07613146d09dadc19e0b431f007c1960602f0aef`.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified Plan 32-06 offline with synthetic deterministic fixtures. No live network, provider, Azure, production DB, source retrieval, asset activation, export release, Git commit, or publication action was performed.
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
  summary: Preflight/control-map allowed execution but reported canonical dirty worktree state and detached or candidate Phase 31 sibling worktrees. Work stayed within Plan 32-06 source/test surfaces plus required GSDD state artifacts.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: DeepL already mapped canonical `pt` to `PT-BR`; Plan 32-06 preserved that behavior and added explicit canonical/cache `pt` provenance plus the versioned Brazilian-Portuguese editorial policy ID.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: `src/multilang/repositories/provider_call_log_repository.py` already implemented route/budget/cache/schema hash aggregation and redacted summaries, while the plan did not declare it writable. Plan 32-06 added regression tests only for that repository behavior.
</deltas>

<judgment>
<active_constraints>
Phase 32 remains in progress and is not phase-verified. No live provider/model choice, provider call, budget approval, source-rights decision, Azure catalog/synthesis call, production DB mutation, review approval, export, release, Git action, or publication is authorized by this summary. Plan 32-06 contracts are offline schema and deterministic-selection infrastructure only.
</active_constraints>
<unresolved_uncertainty>
Exact Phase 31 active snapshot, NIKL source bytes/terms/attribution, local-use and redistribution decisions, genuine transformed 3,000-entry inventory, source review, provider model/budget, Azure voice/profile/catalog, generated text/audio bytes, AI/provider/heard review outputs, production DB target authority, Anki import/playback evidence, and publication approval remain unresolved checkpoint facts.
</unresolved_uncertainty>
<decision_posture>
Continue with offline fail-closed infrastructure and bounded claims. Treat provider output as untrusted data; providers can generate text and telemetry hashes but cannot author identity, approval, fallback, budget authority, mutation, promotion, export, or release decisions. Keep canonical product language `pt`; use `PT-BR` only at provider/editorial boundaries with explicit provenance.
</decision_posture>
<anti_regression>
Do not weaken immutable review schemas, qualified-human-only acceptance, extra-field rejection, stale identity checks, no-mutation authority scope, canonical `pt` cache/domain identity, DeepL `PT-BR` provider boundary, strict Korean provider output validation, hard-gate-before-score ordering, deterministic candidate hash/ordinal tie-breaking, no-fallback provider routes, budget ceilings, cache-hit separation, content-free telemetry, or provider-secret/private-context exclusion. Do not add live provider calls, fallback providers, budget approval, production DB writes, source-rights inference, raw prompt/output persistence, or review application side effects without the exact later checkpoint authority.
</anti_regression>
</judgment>
