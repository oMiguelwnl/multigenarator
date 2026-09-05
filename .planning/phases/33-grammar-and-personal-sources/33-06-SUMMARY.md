---
phase: 33-grammar-and-personal-sources
plan: "06"
runtime: opencode
assurance: self_checked
---

# Phase 33: Grammar and Personal Sources - Plan 06 Summary

**Completed**: 2026-08-30
**Tasks**: 3
**Git Actions**: None; no staging or commits performed.
**Deviations**: User-scoped execution explicitly forbade SPEC, ROADMAP, state-fingerprint, repository, Phase 31/32, staging, and commit mutations, so only the allowed code/test files plus this summary were changed.
**Decisions Made**: Added a separate Phase 33 item outcome algebra instead of renaming legacy `JobStatus`; `processed_at` remains an attempt fact, never a status.
**Notes for Verification**: The implementation is pure domain/service code; repository persistence and CLI observability remain deferred to later plans.
**Notes for Next Work**: Persistence layers should map legacy/coarse rows conservatively into `review_required` unless exact current obligation evidence exists.

## Outcome Truth Table

| Current status | Attempt facts | Completion meaning |
|---|---|---|
| `pending` | No attempts allowed. | Eligible but not attempted/currently untouched. |
| `processing` | Requires an open current attempt with no `processed_at`. | In-progress, never complete. |
| `accepted` | If attempted, latest attempt must have `processed_at`; explicit current AI/integrity/media obligations are required. | Counts as accepted only when all required obligations are current. |
| `review_required` | May be early or late; can carry stale/missing media or review debt. | Preserves progress but blocks completion. |
| `failed` | May be early without `processed_at` or late with `processed_at`. | Preserves attempted failure and blocks completion. |

## Mixed-Run Evidence

- Item-local controlled exceptions become sanitized item outcomes and do not abort eligible siblings.
- Unexpected item exceptions become `failed_unknown` with an opaque correlation ID and no persisted provider/private exception text.
- Systemic validation or handler-result schema mismatches stop fail-closed before misleading sibling continuation.
- Replayed current accepted items are counted as `skipped_current`, not reattempted side effects.

## Completion Matrix

- `attempted`, `skipped_current`, and `not_attempted` partition eligible IDs.
- `processed` is validated as a subset of `attempted`.
- `accepted`, `review_required`, and `failed` are independent current-state counts, not substitutes for attempted/processed facts.
- Completion requires every eligible item to be accepted with explicit current obligations and zero `review_required`, `failed`, `not_attempted`, duplicate, or deferred rows.
- Duplicate and deferred rows remain explicit non-card denominators and cannot force completion.

## Sentinel Scan

- Tests inject `PRIVATE_PROVIDER_PAYLOAD_123` and `PRIVATE_TOKEN` strings.
- Serialized item outcomes retain only controlled reason codes and correlation IDs; raw exception/provider/private strings are not present.

## TDD Log

- 33-06-01 RED: domain imports failed for missing outcome contracts, then focused evidence requirement failed for accepted-without-obligations. GREEN/REFACTOR: added item statuses, attempt records, diagnostics, obligation summaries, report algebra, and legacy status serialization checks.
- 33-06-02 RED: service imports failed for missing runner/contracts, then systemic handler-schema mismatch escaped as `AttributeError`. GREEN/REFACTOR: added ordered runner, item-local/systemic exception split, content-free diagnostics, idempotent skip, bounded retry, and persisted-outcome aggregation.
- 33-06-03 RED: mixed/debt tests were added before implementation. GREEN/REFACTOR: completion now respects review/media debt, skipped-current, duplicate, deferred, and later acceptance transitions.

## Verification Results

- `node .planning/bin/gsdd.mjs lifecycle-preflight execute 33 --expects-mutation phase-status` - passed/allowed; warnings only for known dirty canonical worktree and detached candidate worktrees.
- `node .planning/bin/gsdd.mjs control-map --json` - completed; warnings matched concurrent dirty-worktree context, no blockers.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_jobs.py -k 'pending or processing or accepted or review_required or failed or attempted_at or processed_at or skipped_current or not_attempted or denominator or complete or existing' -q` - passed: 8 passed, 27 deselected.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_item_outcomes.py -k 'continue or order or item_local or systemic or exception or private or idempotent or retry or aggregate' -q` - passed: 5 passed, 2 deselected.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_jobs.py tests/services/test_item_outcomes.py -k 'mixed or resumable or media or stale or later_accept or duplicate or deferred or force_complete' -q` - passed: 6 passed, 36 deselected.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_jobs.py tests/services/test_item_outcomes.py -q` - passed: 42 passed.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync python -m py_compile src/multilang/domain/jobs.py src/multilang/services/item_outcomes.py tests/domain/test_jobs.py tests/services/test_item_outcomes.py` - passed with no output.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync ruff check src/multilang/domain/jobs.py src/multilang/services/item_outcomes.py tests/domain/test_jobs.py tests/services/test_item_outcomes.py` - not run to completion because `ruff` is absent from the frozen environment.

## Bounded Claim

This proves granular outcome algebra, item-local isolation, systemic fail-closed behavior, bounded retry, idempotent skip, sanitized diagnostics, and review/media-aware completion through deterministic fakes. It does not prove repository transactions, CLI behavior, live providers, production migrations, or phase closure.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Planned pytest commands, full scoped pytest, and py_compile passed; RED failures were observed before production changes; ruff was unavailable in the frozen environment and is recorded as non-blocking because no plan command required it.
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
  summary: The GSD execute skill normally updates SPEC, ROADMAP, and state fingerprint, but the user explicitly forbade those writes; execution stayed inside the requested five-file scope.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: `ruff` is not installed in the frozen phase environment; targeted pytest and py_compile checks passed instead.
</deltas>

<judgment>
<active_constraints>
- Preserve existing job `JobStatus`, `JobStage`, `GenerationRequest`, `JobProgressSnapshot`, and serialization compatibility.
- Treat `attempted_at` and `processed_at` as orthogonal facts, never terminal outcome enum values.
- Continue only item-local controlled failures; stop systemic schema/config/authority failures fail-closed.
- Do not persist raw exception, provider, analyzer, or private content in item diagnostics.
- Do not force-complete stages with outstanding review, media, failure, duplicate, deferred, or not-attempted work.
</active_constraints>
<unresolved_uncertainty>
- Repository mapping/backfill for legacy item rows is not implemented here and should conservatively avoid inferring `accepted` without exact current obligation evidence.
- CLI progress and persisted transaction semantics remain outside this plan's proof boundary.
</unresolved_uncertainty>
<decision_posture>
- Add granular Phase 33 item contracts beside legacy job statuses rather than changing existing job lifecycle meanings in place.
- Base stage completion on exact denominator algebra and caller-supplied obligation evidence, not loop completion or optimistic handler results.
- Keep retry bounded and idempotency port-driven so storage layers can enforce atomic replay semantics later.
</decision_posture>
<anti_regression>
- `processed` must not become a valid item status.
- `attempted/skipped_current/not_attempted` must continue to partition eligible IDs, and `processed` must remain a subset of attempted IDs.
- Accepted items must carry explicit current AI/integrity/media obligation evidence.
- Item-local exceptions must not abort siblings, while systemic failures must not be converted into recoverable item outcomes.
- Serialized diagnostics must stay content-free and safe for private/personal-source runs.
</anti_regression>
</judgment>
