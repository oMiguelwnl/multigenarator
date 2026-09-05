---
phase: 33-grammar-and-personal-sources
plan: "09"
runtime: opencode
assurance: self_checked
---

# Phase 33: Grammar and Personal Sources - Plan 09 Summary

**Completed**: 2026-08-31
**Tasks**: 3
**Git Actions**: None; no staging, commits, config, cleanup, or destructive git actions performed.
**Deviations**: Recoverable factual discoveries only. The persistent broker was added as a separate no-excerpt `disclose_persistent()` path to preserve existing in-memory `disclose()` request semantics. The Phase 33 schema stores receipt context hash/token count and idempotency key hash only, so persisted replay receipts remain content-free and exact provider idempotency keys are available only from the issued/requested capability object.
**Decisions Made**: Keep Korean private excerpts in `highlight_private_excerpt_revisions`, keep existing non-Korean `highlight_import_records` behavior unchanged, and use a dedicated persistent capability repository that mutates only capability state/version while appending attempt/receipt evidence.
**Notes for Verification**: Verification used disposable SQLite databases and injected fake callbacks only. No live provider, production private import, production database migration, network call, purge policy, export, staging, or publication path was invoked.
**Notes for Next Work**: Downstream broker/provider integration must use `disclose_persistent()` or an equivalent no-excerpt request shape; do not route private Korean excerpt values through ordinary provider, telemetry, review, or export rows.

## Implementation

- `HighlightImportRepository.upsert_import_records()` now branches only `ko` jobs into immutable `highlight_private_excerpt_revisions`; exact retries return the existing revision and changed text/source hash appends a new revision under the same stable highlight ID.
- Added `list_korean_safe_inventory(job_id)` with an explicit hash-only column projection and deterministic `inventory_root_sha256` over safe candidate IDs, source hashes, counts, and private-boundary revision IDs.
- Added `load_private_excerpt_revision(job_id, excerpt_revision_id)` as the narrow local-only privileged load method; ordinary inventory does not select `normalized_text`, `source_path`, or `raw_location`.
- Added `PrivateProcessingRepository` with `issue_capability()`, `get_attempt()`, `reserve_disclosure()`, `finalize_disclosed()`, `finalize_failed_unknown()`, and transaction release before callback.
- Added `PrivateContextPersistentDisclosureRequest`, `PrivateContextExcerptPayload`, and `PrivateContextBroker.disclose_persistent()` so safe capability validation and committed reservation happen before privileged load and callback.

## Revision History Evidence

- First Korean import writes revision `1` to `highlight_private_excerpt_revisions` and writes no row to the legacy mutable `highlight_import_records` table.
- Exact retry of the same highlight text/hash returns the same safe `excerpt_revision_id` and leaves the revision count at `1`.
- Changed exact text/hash under the same `highlight_id` appends revision `2`; revision `1.normalized_text` remains unchanged and privileged reload by exact revision ID returns the original text.
- Distinct excerpt hashes that can map to the same learner candidate stay distinct through separate safe inventory rows and separate private revision IDs.

## Safe and Privileged Query Inventory

- Safe inventory selects only `highlight_id`, `import_content_hash`, `source_content_hash`, `source_index`, `excerpt_revision_id`, and `revision_number` from `highlight_private_excerpt_revisions`.
- Safe inventory serialization excludes exact text, source path, raw location, book/location metadata, context text, prompt, payload, and private sentinels.
- Privileged exact text is available only through `load_private_excerpt_revision(job_id, excerpt_revision_id)` and remains outside receipts, attempts, capabilities, manifests, safe inventory rows, and review/access/event tables.

## Race and Callback Trace

- Capability issuance persists exact job/run/item/excerpt/target/provider/model/route/purpose/policy bindings with `phase33-private-token-v1`, `max_context_tokens <= 24`, actual bounded token count, state `pending`, and version `0`.
- Exact supported-idempotency retry with the same key returns the same capability ID; changed authority under the same idempotency key conflicts.
- Reservation uses capability state/version CAS. One `pending -> disclosing` winner commits version `1`; a second reservation attempt with version `0` raises `PrivateProcessingRepositoryConflict` and does not invoke a callback.
- Persistent broker order is safe validation, replay check, committed reservation, privileged load, context derivation, transaction release, callback, then finalization.
- Known-success callback count is `1` with `session.in_transaction() == False`; non-idempotent unknown callback count is `1`, finalizes `failed_unknown`, and replay returns `inspect_required` without a second privileged load or callback.

## TDD Evidence

- RED 33-09-01: Highlight repository selector failed with missing `get_private_excerpt_revision`/`list_korean_safe_inventory` behavior (`4 failed, 5 deselected`). GREEN: Added immutable Korean revision branch, safe inventory, exact privileged loader, and tests passed (`4 passed, 5 deselected`).
- RED 33-09-02: Private-processing repository selector failed during collection because `multilang.repositories.private_processing_repository` did not exist (`1 error`). GREEN: Added the persistent repository and tests passed (`3 passed`).
- RED 33-09-03: Broker persistent selector failed on missing `PrivateContextPersistentDisclosureRequest` (`3 failed, 11 passed, 9 deselected`). GREEN: Added persistent request/payload/broker path and tests passed (`14 passed, 9 deselected`).

## Verification Results

- `node .planning/bin/gsdd.mjs lifecycle-preflight execute 33 --expects-mutation phase-status`: allowed; warnings only for the known dirty canonical worktree and invalid/detached Phase 31 sibling worktrees.
- `node .planning/bin/gsdd.mjs control-map --json`: completed; canonical branch `reconcile/monarch-20260818`, head `38bcd1c05dafe2852dd889731de87d6ef795f864`, known dirty canonical worktree, invalid/detached Phase 31 sibling warnings, no blockers.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_highlight_import_repository.py -k 'korean and (revision or unchanged or retry or changed or distinct_excerpt or safe_inventory_root or no_inventory_drop or private_boundary_hash_only or order or existing)' -q`: `4 passed, 5 deselected`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_private_processing_repository.py -k 'issue or token_v1 or token_cap_24 or token_count or consume or exact or one_winner or replay or second_call or changed or expired or stale or no_private' -q`: `3 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_private_context.py tests/repositories/test_private_processing_repository.py -k 'persistent or privileged_load or replay or zero_call or callback_failure or resumable or no_leak or logs' -q`: `14 passed, 9 deselected`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_highlight_import_repository.py tests/repositories/test_private_processing_repository.py tests/services/test_private_context.py -q`: `32 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/db/test_phase33_schema.py tests/test_migration_schema_parity.py -q`: first 120s run timed out while progressing; rerun with 240s passed `21 passed, 26 warnings`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync python -m compileall -q src/multilang/repositories/highlight_import_repository.py src/multilang/repositories/private_processing_repository.py src/multilang/services/private_context.py tests/repositories/test_highlight_import_repository.py tests/repositories/test_private_processing_repository.py tests/services/test_private_context.py`: passed with only the expected `VIRTUAL_ENV` warning.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync alembic heads`: `20260828_19 (head)`.
- Narrow source scans over touched repository/service files found no provider/network/destructive-operation calls; private sentinel scans found no source sentinel strings, only generic local variable names and intentional local-only service request fields.
- `git diff --check -- src/multilang/repositories/highlight_import_repository.py src/multilang/repositories/private_processing_repository.py src/multilang/services/private_context.py tests/repositories/test_highlight_import_repository.py tests/repositories/test_private_processing_repository.py tests/services/test_private_context.py`: passed with no output before summary.
- `git diff --check -- src/multilang/repositories/highlight_import_repository.py src/multilang/repositories/private_processing_repository.py src/multilang/services/private_context.py tests/repositories/test_highlight_import_repository.py tests/repositories/test_private_processing_repository.py tests/services/test_private_context.py .planning/phases/33-grammar-and-personal-sources/33-09-SUMMARY.md`: passed with no output after summary.

## Bounded Claim

This proves isolated immutable Korean private excerpt revisions, hash-only safe inventory, exact privileged revision loading, persistent capability issuance, CAS reservation/finalization, fake-callback transaction separation, and non-idempotent unknown-result closure in local tests. It does not prove live PostgreSQL isolation, production private imports, remote provider privacy compliance, production provider idempotency, provider telemetry integration, purge/retention policy, generated content quality, learner-ready exports, publication, or Phase 33 closure.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: RED failures were observed before implementation for highlight revisions, persistent repository creation, and persistent broker API. Plan selectors, full touched-file suite, schema/parity regression, compileall, Alembic head, source scans, and diff hygiene passed in the frozen offline environment with fake callbacks only.
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
  summary: The existing `PrivateContextBroker.disclose()` request carries exact excerpt text and has established Plan 04 behavior. A separate persistent `disclose_persistent()` path was added to enforce safe validation/reservation before privileged load without regressing the legacy in-memory tests.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The Phase 33 schema stores provider idempotency key hash and receipt context hash/token count, not exact idempotency keys or full receipt code-point/byte counts. The repository keeps persisted replay evidence content-free and returns exact idempotency keys only from the issued/requested capability object.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Local verification used disposable SQLite databases. The CAS/update patterns and constraints are SQLAlchemy/PostgreSQL-compatible, but live PostgreSQL isolation and lock behavior remain unproven.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Standard execute lifecycle writes to `.planning/SPEC.md`, `.planning/ROADMAP.md`, and `.planning/.state-fingerprint.json` were skipped to honor the active no-touch constraint for those files.
</deltas>

<judgment>
<active_constraints>
- Remote/private provider processing remains default-denied unless exact per-run capability authority exists.
- Korean private highlight text and private source path/location metadata remain confined to `highlight_private_excerpt_revisions` and privileged local loaders.
- `phase33-private-token-v1` and `max_context_tokens <= 24` remain locked for private context disclosure.
- Capability issuance, reservation, finalization, and replay must remain exact, hash-bound, and content-free outside the dedicated private excerpt table.
- `pending -> disclosing` reservation must commit before any privileged excerpt load/provider callback, and callbacks must run outside DB transactions.
- `disclosing`, `disclosed`, and `failed_unknown` replays must not invoke privileged load or callback.
</active_constraints>
<unresolved_uncertainty>
- Live PostgreSQL transaction/isolation behavior and production multi-process race behavior are not verified by this local SQLite run.
- Production authority minting, provider route integration, telemetry persistence, and any remote disclosure policy remain outside this plan.
- Retention/purge policy remains explicitly unapproved; no cleanup or expiration deletion was added.
- Persisted receipt reconstruction is intentionally hash/count-only under the current schema; richer receipt replay would require a future schema decision.
</unresolved_uncertainty>
<decision_posture>
- Continue with least-privilege, single-use, at-most-once disclosure: safe validation first, reservation before privileged load, no transaction around callbacks, and content-free final evidence.
- Preserve existing non-Korean highlight import semantics while making Korean private imports append-only.
- Treat exact private values as local-only inputs to a bounded callback, never as candidate/event/receipt/manifest/review/export data.
</decision_posture>
<anti_regression>
- Do not route Korean private imports through mutable `highlight_import_records` or update old private revision rows in place.
- Do not add ordinary ORM relationships/eager loaders from public job/candidate/review rows to private excerpt text/path/location fields.
- Do not select `normalized_text`, `source_path`, or `raw_location` in safe inventory/list/report methods.
- Do not add broad `allow_private` flags, wildcard provider/model/route/purpose grants, token caps above 24, alternate private token rules, or closed-state reset for redisclosure.
- Do not persist private excerpt/context/prompt/payload values in capabilities, attempts, receipts, events, manifests, candidates, logs, or exports.
- Do not perform live provider calls in private-processing tests; fake callbacks remain the only authorized path here.
</anti_regression>
</judgment>
