---
phase: 33-grammar-and-personal-sources
plan: "04"
runtime: opencode
assurance: self_checked
---

# Phase 33: Grammar and Personal Sources - Plan 04 Summary

**Completed**: 2026-08-30
**Tasks**: 2
**Git Actions**: none; no staging, commits, or git config changes.
**Deviations**: Normal GSD lifecycle mutations to `.planning/SPEC.md`, `.planning/ROADMAP.md`, and `.planning/.state-fingerprint.json` were intentionally skipped because the user explicitly prohibited touching those files and narrowed the write scope to the plan-owned files plus this summary.
**Decisions Made**: Exact authority is represented by frozen Pydantic contracts plus an injected offline broker seam. Provider idempotency support is a literal `supported|unsupported` capability binding; non-idempotent unknown results get no retry, while idempotent retry reuses the exact key only when the run budget permits it.
**Notes for Verification**: No live provider, shared `text_generation.py`, Phase 31/32 artifact, database, network, staging, commit, or production mutation path was touched. Tests use injected fake callbacks and an in-memory CAS store only.
**Notes for Next Work**: Plan 18 can later wire this broker into the shared provider boundary after its dependency summary exists; it should preserve these content-free receipt/error and zero-call refusal invariants.

## Implementation

- Added `src/multilang/domain/private_processing.py` with strict frozen contracts for `PrivateProcessingPolicy`, `PrivateProcessingCapability`, `PrivateProviderIdempotency`, `PrivateDisclosureAttempt`, `PrivateDisclosureStateTransition`, `PrivateProcessingReceipt`, and `PrivateProcessingRefusal`.
- Added the locked `phase33-private-token-v1` tokenizer: NFC normalization, one token per maximal Letter/Number/Mark run, one token per non-whitespace punctuation/symbol code point, and no token for whitespace/control separators.
- Added `src/multilang/services/private_context.py` with local target-centered context derivation, hard `<=24` token enforcement, independent code-point/UTF-8-byte caps, exact capability validation, default-denied missing authority, and an offline broker that commits `pending -> disclosing` before invoking the injected callback outside the transaction.
- Added refusal/replay/unknown handling: missing/stale/mismatched/expired/over-budget/CAS/replay states return content-free refusals and make zero adapter calls; non-idempotent unknown results finalize `failed_unknown`; idempotent retry uses the identical key; success finalizes `disclosed` with a content-free receipt.
- Added output hardening: callback output is treated as untrusted, extra authority/identity/approval fields are rejected, exact-copy output is unsafe, and receipts/refusals do not serialize context, excerpt, prompt, payload, paths, or private sentinels.

## TDD Evidence

- RED 1: `tests/domain/test_private_processing.py` and `tests/services/test_private_context.py` were created first; plan selectors failed on missing modules (`7 failed` domain; `14 failed, 2 deselected` service).
- GREEN 1: Implemented the minimal domain and service modules; domain selector passed, service selector exposed two focused failures.
- REFACTOR/FIX 1: Root-caused service failures to NFC target-span realignment and a test setup that excluded the intended injection text; added deterministic unique-target realignment and adjusted the injection fixture cap.
- RED 2: Added `test_missing_capability_defaults_to_denied_zero_call_without_context_derivation`; it failed because absent authority was rejected by the request schema.
- GREEN 2: Allowed `capability=None` on the request and made the broker fail closed before context derivation or adapter invocation.
- RED 3: Added an idempotency contract case proving a supported route can record an exact key even with one allowed attempt; it failed under an over-strict validator.
- GREEN 3: Relaxed only that validator while retaining one-attempt enforcement for unsupported idempotency.

## Verification

- `node .planning/bin/gsdd.mjs lifecycle-preflight execute 33 --expects-mutation phase-status`: passed/allowed; warnings only for the known dirty canonical worktree and unrelated Phase 31 sibling worktrees.
- `node .planning/bin/gsdd.mjs control-map --json`: completed; warnings matched known concurrent-lane dirtiness, with no blockers.
- `git status --short --branch`: confirmed dirty concurrent worktree on `reconcile/monarch-20260818`; no cleanup or staging performed.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_private_processing.py -k 'exact or wildcard or provider or purpose or budget or token_v1 or token_cap_24 or unicode_count or consumed or private or hidden or frozen' -q`: final result `7 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_private_context.py -k 'bounded or token_v1 or token_cap_24 or token_25_refused or unicode or target or stale or mismatch or expiry or replay or cas or receipt or zero_call or injection' -q`: final result `15 passed, 2 deselected`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_private_processing.py -q`: final result `7 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_private_context.py -q`: final result `17 passed`.
- `git diff --check -- src/multilang/domain/private_processing.py src/multilang/services/private_context.py tests/domain/test_private_processing.py tests/services/test_private_context.py .planning/phases/33-grammar-and-personal-sources/33-04-SUMMARY.md`: passed with no output.

## Authority Matrix

| Case | Adapter Call | Result |
|---|---:|---|
| Missing capability/default remote processing | 0 | `refused/missing_capability` |
| Stale excerpt revision/hash | 0 | `refused/stale_excerpt` |
| Provider/model/route/purpose/policy mismatch | 0 | `refused/binding_mismatch` |
| Expired capability | 0 | `refused/expired` |
| Invalid or absent target span | 0 | `refused/invalid_target_span` or `target_absent` |
| Target requires 25 tokens under cap 24 | 0 | `refused/context_over_budget` |
| CAS version conflict | 0 | `refused/cas_conflict` |
| `disclosing` replay | 0 | `inspect_required/replay_or_closed_state` |
| `disclosed` replay | 0 | prior content-free receipt returned |
| `failed_unknown` replay | 0 | `inspect_required/replay_or_closed_state` |
| Non-idempotent timeout/unknown | 1 | terminal `failed_unknown`, no retry |
| Idempotent unknown then success | 2 | identical idempotency key, then `disclosed` |
| Provider output tries authority/identity/approval fields | 1 | terminal `failed_unknown/unsafe_provider_output` |

## Disclosure Bounds

- Token rule: `phase33-private-token-v1` only.
- Hard token ceiling: `max_context_tokens <= 24`; tests cover 24 accepted and 25 refused.
- Additional independent bounds: capability-level code-point and UTF-8 byte maxima.
- Context derivation: NFC-normalized, deterministic, target-centered, local only, hash-bound before callback construction.
- Claim limit: proves exact offline broker behavior with fake callbacks; does not prove shared text-generation wiring, live provider behavior, provider privacy terms, or production publication safety.

## Sentinel Scan

- Receipt/refusal tests assert Korean private sentinels, `/home/private`, prompt-like text, `context_text`, `excerpt_text`, `prompt`, and `payload` do not appear in serialized receipts/refusals.
- Callback request may contain the bounded authorized context by design; receipt/error artifacts remain content-free.
- No provider payload persistence, telemetry table write, file export, or live adapter call was introduced.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Plan selectors, full new test files, default-denied zero-call behavior, idempotency retry branch, content-free receipt/error assertions, and whitespace check passed offline with fake callbacks only.
</executor_check>
</checks>

<handoff>
plan_runtime: opencode
plan_assurance: unreviewed
plan_check_status: skipped
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: false
</handoff>

<deltas>
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Target modules/tests did not exist, matching the plan's create-file task shape; implementation proceeded as create-only for scoped code/test files.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Control-map reported the known dirty canonical worktree and unrelated Phase 31 sibling worktree warnings; the user had already acknowledged concurrent lanes, so execution stayed limited to the explicit write set.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Normal GSD state files were dirty and explicitly out of scope by user instruction; SPEC/ROADMAP/fingerprint state updates were not performed.
</deltas>

<judgment>
<active_constraints>
Remote private processing remains denied by default. Exact per-run authority is required and bound to item, immutable excerpt revision/hash, target span/hash, provider/model/route, purpose, policy hash, token rule, budgets, expiry, and idempotency support/key. `max_context_tokens` remains capped at 24 under `phase33-private-token-v1`. Refusal, replay, closed, stale, mismatch, over-budget, and CAS-conflict states must make zero adapter calls. Provider callback invocation must happen only after committed `pending -> disclosing` reservation and outside the transaction. Receipts/refusals stay content-free.
</active_constraints>
<unresolved_uncertainty>
This plan did not wire the broker into shared text generation, live provider adapters, telemetry persistence, database transactions, or production authority minting. Provider-specific tokenization may be stricter than `phase33-private-token-v1`, but the local disclosure ceiling remains authoritative and fail-closed.
</unresolved_uncertainty>
<decision_posture>
The governing approach is least-privilege, single-use, at-most-once disclosure. Deterministic local code owns authority, identity, route, policy, target matching, state transitions, and approval boundaries; provider text is untrusted output and cannot assign authority, identity, or approval. Unknown non-idempotent results stop at `failed_unknown`; exact idempotency may retry only with the same key.
</decision_posture>
<anti_regression>
Do not add `allow_private` booleans, wildcard/broad grants, job/source/account inherited authority, alternate token rules, context caps above 24, prompt/payload persistence, live provider calls in tests, callback invocation on refusal/replay/closed states, transaction-held callbacks, closed-state reset, or content-bearing receipts/errors. Do not modify `src/multilang/services/text_generation.py` until the later gated integration plan owns that join.
</anti_regression>
</judgment>
