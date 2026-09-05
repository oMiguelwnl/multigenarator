---
phase: 33-grammar-and-personal-sources
plan: "18"
runtime: opencode
assurance: self_checked
---

# Phase 33: Grammar and Personal Sources - Plan 18 Summary

**Completed**: 2026-08-30
**Tasks**: 1
**Git Actions**: none; no staging, commits, pushes, or git config changes.
**Deviations**: Recoverable factual discoveries only. Normal GSD lifecycle updates to `.planning/SPEC.md`, `.planning/ROADMAP.md`, and `.planning/.state-fingerprint.json` were intentionally skipped to preserve the active dirty planning state and prior user constraint against touching those files without an explicit decision.
**Decisions Made**: Korean highlight provider context now uses an optional Plan 04 broker factory plus exact disclosure request. The shared service captures generated text inside the broker-approved callback, caches only the bounded request/result, and never lets provider output set private authority, approval, identity, source-mode, or export metadata.
**Notes for Verification**: This plan wires only `TextGenerationService` and focused tests. It does not grant private-processing authority, create disclosure records, read credentials, call live providers, mutate a database, publish source content, create audio, export decks, or claim linguistic quality.
**Notes for Next Work**: Production callers still need an authority-minting/persistence path before Korean highlight context can be used outside these fake-adapter tests. Context-free Korean highlights and existing non-Korean highlight behavior remain compatible.

## Upstream Gate Proof

- `.planning/phases/32-frequency-portuguese-text-and-audio/32-07-SUMMARY.md` exists and records the settled Phase 32 text-generation selector/cache/retry/telemetry interface.
- `.planning/phases/33-grammar-and-personal-sources/33-04-SUMMARY.md` exists and records the Plan 04 private-context broker contract, exact `phase33-private-token-v1` rule, `max_context_tokens <= 24`, content-free refusals/receipts, CAS reservation, and idempotency behavior.
- `node .planning/bin/gsdd.mjs lifecycle-preflight execute 33 --expects-mutation phase-status` returned `allowed: true` with only known dirty-worktree/sibling-worktree warnings.
- `node .planning/bin/gsdd.mjs control-map --json` reported no blockers; execution stayed limited to the Plan 18 write set.

## Implementation

- Added `PrivateContextAuthorizationError` as a content-free Korean private-context refusal surface.
- Added an optional `private_context_broker_factory` constructor dependency and optional `private_context_request` argument on `TextGenerationService.generate_bundle(...)`; existing callers remain compatible.
- Routed only Korean `kindle-highlights` requests with non-empty context through the broker path. Missing broker/request/capability refuses before any adapter call.
- Validated exact request binding against the active sentence adapter provider/model, fixed route `korean-highlight-microexample`, fixed purpose `highlight_microexample_context`, exact route hash, job id when present, source excerpt hash, and candidate target hash.
- Performed provider invocation only inside the Plan 04 disclosure callback after the broker's `pending -> disclosing` reservation has committed.
- Avoided the generic provider retry loop for private context. Non-idempotent unknown results stop after one adapter attempt; idempotent routes retry only through the broker and pass the exact idempotency key only to adapters that expose `generate_sentence_with_idempotency(...)`.
- Preserved cache behavior by caching/reading only the bounded, sanitized `SentenceGenerationRequest` produced from the broker's provider context, never the raw excerpt.
- Added private microexample metadata with content-free hashes, receipt hash, token rule/count, contextual evidence policy, and `needs_review` state. Long source-copy patterns add `review_reason=source_copy_policy_violation`.
- Sanitized private-path sentence provenance so untrusted provider output cannot set authority, approval, source type, identity, policy, review state, or export fields.

## TDD Evidence

- RED: After adding focused tests, the Plan 18 selector failed during collection with `ImportError: cannot import name 'PrivateContextAuthorizationError'`, proving the new service API/behavior was absent.
- GREEN: Implemented the optional broker-approved Korean highlight branch and content-free refusal surface; the Plan 18 selector passed with `12 passed, 18 deselected`.
- REFACTOR: Corrected the over-budget fixture to use an undersized code-point budget instead of a one-token context, removed an unused test import, and reran full/adjacent regressions.

## Call-Count Matrix

| Case | Adapter Calls | Result |
|---|---:|---|
| Missing broker/request/capability | 0 | `PrivateContextAuthorizationError(reason_code="missing_capability")` |
| Stale excerpt hash | 0 | `PrivateContextAuthorizationError(reason_code="stale_excerpt")` |
| Over-budget bounded context | 0 | `PrivateContextAuthorizationError(reason_code="context_over_budget")` |
| `disclosing` replay state | 0 | `PrivateContextAuthorizationError(reason_code="replay_or_closed_state")` |
| `disclosed` replay state without captured text | 0 | `PrivateContextAuthorizationError(reason_code="replay_or_closed_state")` |
| `failed_unknown` replay state | 0 | `PrivateContextAuthorizationError(reason_code="replay_or_closed_state")` |
| Authorized pending disclosure | 1 | Generated bundle with content-free receipt/microexample metadata |
| Non-idempotent unknown/timeout | 1 | `failed_unknown`, no retry, content-free error |
| Idempotent unknown then success | 2 | Same exact idempotency key on both attempts |
| Korean highlight without context | 1 | Existing context-free generation; no excerpt sent |
| Existing non-Korean highlight context | 1 | Existing behavior preserved |
| Long source-copy microexample | 1 | Generated bundle marked `needs_review/source_copy_policy_violation` |

## Sentinel Scan

- Refusal tests assert private Korean text and `/home/private` do not appear in `PrivateContextAuthorizationError` strings.
- Authorized callback tests assert the adapter observes `store.transaction_open == False`, proving the provider call happens after reservation commit.
- Adapter request tests assert private paths and prompt-injection text are removed by the existing Korean highlight sanitizer before the provider-facing sentence request.
- Provenance tests assert malicious provider keys such as `authority`, `approval_status`, and `source_type` are stripped from private microexample metadata.
- No test or implementation persists raw excerpt text, provider prompts, payloads, credentials, paths, or private context in receipts/refusals/telemetry metadata; only hashes and controlled reason codes are emitted.

## Verification

- `test -f .planning/phases/32-frequency-portuguese-text-and-audio/32-07-SUMMARY.md && UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_text_generation.py -k 'korean and (private or authority or zero_call or local_only or microexample or copy or prompt or existing_source)' -q`: `12 passed, 18 deselected`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_text_generation.py -q`: `30 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_private_context.py tests/services/test_korean_text_generation.py -q`: `21 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_provider_text_adapters.py -k 'korean and highlight' -q`: `1 passed, 22 deselected`.
- `git diff --check -- src/multilang/services/text_generation.py tests/services/test_text_generation.py .planning/phases/33-grammar-and-personal-sources/33-18-SUMMARY.md`: passed with no output.

## Bounded Claim

- Plan 18 proves the shared text-generation boundary refuses Korean private highlight context by default, invokes fake adapters only after exact Plan 04 authorization, keeps replay/refusal paths zero-call, preserves existing non-private source behavior, and stores only content-free private microexample evidence.
- It does not prove live provider privacy terms, production authority creation, persisted disclosure storage, real text quality, review approval, APKG/CSV/TSV export, audio, publication readiness, or Phase 33 completion.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified the upstream summary gate, optional constructor/caller compatibility, fake-adapter zero-call refusal/replay matrix, idempotent retry key reuse, private sentinel stripping, focused provider-prompt compatibility, adjacent Plan 04 broker tests, Korean selector tests, and whitespace check.
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
  summary: The Phase 32 Plan 07 selector-attempt changes were already present in the dirty shared `text_generation.py`, matching `32-07-SUMMARY.md`; Plan 18 layered only the private-context join on top.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The Plan 04 `PrivateContextBroker` returns receipts/refusals rather than generated sentence content, so the shared service uses an injected broker factory and captures the generated sentence inside the broker-approved callback.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: A one-token private-context cap can still disclose a one-token target, so the over-budget test uses an undersized code-point budget to exercise the same fail-closed broker refusal.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Normal GSD state-file updates were skipped because `.planning/SPEC.md`, `.planning/ROADMAP.md`, and `.planning/.state-fingerprint.json` are dirty shared planning files and prior user constraints prohibited touching them without an explicit decision.
</deltas>

<judgment>
<active_constraints>
Korean private highlight context remains denied by default. Exact Plan 04 authority is required for each run and must bind job, run, item, excerpt revision/hash, target span/hash, provider, model, route, purpose, policy, token rule, budgets, expiry, idempotency, and CAS version. Provider calls must occur only after committed reservation and outside the transaction. Non-idempotent unknown results do not retry; idempotent retries reuse exactly the same key. Context-free Korean highlights and non-Korean source modes must retain existing behavior.
</active_constraints>
<unresolved_uncertainty>
Production authority creation, persisted disclosure attempts, exact caller wiring from highlight import records, live provider privacy terms, live model behavior, provider budgets, real Korean text review, and export eligibility remain unresolved downstream facts. Phase 33 is still not verified or closed.
</unresolved_uncertainty>
<decision_posture>
Keep the shared text-generation boundary least-privilege and hash-bound. Raw excerpts stay local; provider-visible context is bounded, sanitized, and explicitly untrusted. Generated microexamples are output artifacts with content-free evidence and default `needs_review`; provider output cannot author identity, policy, approval, authority, source mode, or export state.
</decision_posture>
<anti_regression>
Do not add broad `allow_private` flags, job-wide/source-wide/account-wide authority, route/model/provider wildcards, generic retry around private disclosures, unkeyed retry on idempotent routes, raw excerpt prompt/cache/telemetry persistence, private values in receipts/refusals/errors, callback execution while a disclosure transaction is open, replay calls on `disclosing`/`disclosed`/`failed_unknown`, source-copy approval, or non-Korean behavior drift.
</anti_regression>
</judgment>
