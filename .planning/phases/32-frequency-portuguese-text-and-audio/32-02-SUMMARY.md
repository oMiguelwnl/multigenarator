---
phase: 32-frequency-portuguese-text-and-audio
plan: "02"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 02 Summary

**Completed**: 2026-08-28
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: Recoverable factual discoveries only. The worktree and a Phase 31 sibling worktree were dirty before this continuation; preflight allowed execution, the user had already authorized continuing in the dirty canonical worktree, and Task 32-02-03 did not overlap the sibling media-lane write set. Source-review aggregate tests required a larger local timeout because the test helper rebuilds 5,965-row subjects for every batch; service import was optimized with a digest-bound subject cache.
**Decisions Made**: No product, legal, provider, Azure, release, or publication decisions. Column and model names are local technical choices within the approved additive persistence shape.
**Notes for Verification**: This plan proves synthetic/offline atomic bundle building, content-free review receipt accounting, CLI privacy output, and disposable migration parity. It does not prove real NIKL bytes, production transformation authority, production database mutation, provider/Azure approval, final asset eligibility, export readiness, or publication.
**Notes for Next Work**: Continue only offline Phase 32 lanes until exact source/license/provider/Azure/Phase 31 authorities exist. Production DB migration remains a later checkpoint-bound action even though the revision file and disposable migration tests now pass.

## Completed Work

- Implemented durable inactive Korean frequency bundle construction in `scripts/build_frequency_assets.py`, including sibling staging, fsync/reopen validation, absent-target install, collision protection, interruption cleanup, and exact-existing idempotency.
- Added strict build-result validation in `src/multilang/services/korean_frequency.py` and exposed `validate-korean-source-build-result` through `src/multilang/cli.py` with content-free output.
- Added `src/multilang/services/korean_source_review.py` for at-most-100-row source-review batch import, immutable canonical content-free receipts, replay no-write behavior, stale/hash/role/overlap/privacy rejection, and exact 5,965-disposition aggregation.
- Added CLI commands `import-korean-bundle-review-batch` and `validate-korean-bundle-review-batches` with safe hash/count/status output only.
- Added sole additive Alembic revision `alembic/versions/20260821_18_frequency_text_audio_evidence.py` over `20260804_17` and matching nullable ORM columns for Phase 31 tuple hashes, Korean frequency authority, lexical/source review evidence, candidate/adaptive/review evidence, audio catalog/profile/request/artifact/heard evidence, export evidence, provider telemetry hashes, and staged execution hashes.
- Added `KoreanFrequencyTextAudioEvidence` to `src/multilang/domain/korean.py` to validate hash-only Phase 32 authority tuples and reject extra private fields.

## Verification

- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/scripts/test_build_frequency_assets.py -k 'staging or fsync or atomic_rename or interruption or rollback or collision or idempotent' -q` passed earlier in this plan: `4 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_frequency.py -k 'build_validator or manifest or root or inactive or exact_existing' -q` passed earlier in this plan: `2 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_korean_frequency_build_commands.py -k 'build_result or cli or privacy or safe_output' -q` passed earlier in this plan: `2 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/scripts/test_build_frequency_assets.py tests/services/test_korean_frequency.py tests/cli/test_korean_frequency_build_commands.py -k 'build_validator or manifest or root or inactive or exact_existing or build_result or cli or privacy or safe_output' -q` passed: `7 passed, 12 deselected`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_source_review.py -k 'batch or aggregate or bounded or disjoint or complete or role or privacy' -q` passed: `3 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_korean_source_review_commands.py -q` passed: `3 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/test_migration_schema_parity.py -k 'frequency_text_audio or locator or sole_linear_head or migrations_include_every_orm_column' -q` passed: `5 passed, 7 deselected`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync alembic heads` passed: `20260821_18 (head)`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/test_migration_schema_parity.py -q` passed: `12 passed`.

## TDD Evidence

- Task 32-02-01 RED: build/validator/CLI tests were written before production code and initially failed on missing build-result behavior. GREEN: added staged builder, strict validator, and CLI command; focused verification passed.
- Task 32-02-02 RED: service tests failed with `ModuleNotFoundError: No module named 'multilang.services.korean_source_review'`. GREEN: added source-review import/aggregate service and CLI commands; focused service and CLI verification passed.
- Task 32-02-03 RED: migration tests failed on sole head `20260804_17`, missing ORM columns, missing revision file, and missing `KoreanFrequencyTextAudioEvidence`. GREEN: added the sole child revision, nullable ORM mappings, and strict domain evidence model; targeted and full migration parity passed.

## Interruption Matrix

- Staging, write, flush/fsync, manifest, reopen, rename, parent-fsync, collision, rollback, and idempotent exact-existing boundaries are covered by the builder tests.
- Source-review receipt creation is canonical, atomic, immutable by batch ID, and exact replay is no-write.
- Migration upgrade, downgrade, and re-upgrade are covered on disposable SQLite only; production database mutation was not run.

## Review Accounting

- Batch size is bounded to 100 decisions.
- Aggregate coverage requires exactly 5,965 disjoint dispositions.
- Aggregate acceptance requires exactly 3,000 accepted rows and 2,965 rejected rows.
- Receipts store hashes, ranks, roles, counts, and controlled risk codes only; raw source text, private paths, notes, prompts, payloads, and credentials are not stored or emitted.

## Migration Parity

- Sole Alembic head is `20260821_18`.
- Revision `20260821_18` is a reversible child of `20260804_17`.
- Added columns are nullable for historical rows and are mirrored in SQLAlchemy metadata.
- New hash columns use `String(64)` and the domain evidence model enforces lowercase 64-hex SHA-256 values for locator/content authority tuples.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified all Plan 32-02 task surfaces offline with synthetic fixtures and disposable databases. No live network, provider, Azure, production DB, asset commit, release, or publication action was performed.
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
  summary: `node .planning/bin/gsdd.mjs lifecycle-preflight execute 32 --expects-mutation phase-status` allowed execution but reported canonical dirty worktree state. The user had already authorized continuing in the dirty worktree; no unrelated dirty files were reverted or modified intentionally.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: `node .planning/bin/gsdd.mjs control-map --json` reported a dirty unannotated Phase 31 media-lane sibling worktree. Task 32-02-03 touched only Plan 32-02 migration/ORM/domain/test files and did not overlap that sibling write set.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The source-review aggregate test fixture rebuilds a 5,965-row subject map for every 100-row batch, so the first 120-second verification timed out after two passing tests. The service import was optimized with a bundle-digest-bound subject cache and the focused tests were rerun with a larger local timeout.
</deltas>

<judgment>
<active_constraints>
Phase 32 remains in progress and is not phase-verified. No live source retrieval, real source transformation, final bundle activation, provider call, Azure catalog or synthesis call, production database migration, review approval, asset commit, release, or publication is authorized by this summary. Korean final frequency authority remains separated into retrieval, build, review, promotion, database, provider, audio, export, and release powers.
</active_constraints>
<unresolved_uncertainty>
Exact NIKL attachment bytes, terms evidence, approved attribution, local-use and redistribution disposition, genuine transformed 3,000-entry inventory, complete source review, Phase 31 active snapshot, provider models/budgets, Azure voice/profile, generated text/audio bytes, heard review outputs, production DB target authority, and publication approval are still unresolved checkpoint facts.
</unresolved_uncertainty>
<decision_posture>
Continue with offline fail-closed infrastructure and exact hash-bound authorities. Treat every production or external side effect as a separate least-power checkpoint, not as implied by the existence of a passing builder, receipt validator, or migration file.
</decision_posture>
<anti_regression>
Do not weaken Phase 30 Korean NFC/source-backed identity/Kiwi contracts. Do not introduce live `wordfreq`, spreadsheet/HWP parser authority, generic suffix rescue, provider-authored identity, source/build power conflation, private path leakage, prompt/payload persistence, production migration without exact checkpoint authority, or Korean production promotion from synthetic fixtures.
</anti_regression>
</judgment>
