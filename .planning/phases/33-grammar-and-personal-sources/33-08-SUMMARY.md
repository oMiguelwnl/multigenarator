---
phase: 33-grammar-and-personal-sources
plan: "08"
runtime: opencode
assurance: self_checked
---

# Phase 33: Grammar and Personal Sources - Plan 08 Summary

**Completed**: 2026-08-31
**Tasks**: 3
**Git Actions**: None; no staging or commits performed.
**Deviations**: Recoverable factual discoveries only. `review_access_events.action` from Plan 33-07 did not allow `list`/`inspect`, but Plan 33-08 review access requires those audited reads; the Phase 33 migration, ORM check constraint, and schema test were aligned. Verification used isolated SQLite databases, including a file-backed two-session stale-writer test, not a live PostgreSQL instance.
**Decisions Made**: No product, provider, production database, release, or publication decisions. Repository APIs use typed local DTOs and SQLAlchemy ORM statements rather than dynamic SQL or permissive dict blobs.
**Notes for Verification**: The implementation proves isolated repository ordering, hash revalidation, exact retry/conflict handling, pointer/reservation CAS, access-event audit-before-return, and audio reservation/finalization constraints. It does not prove production PostgreSQL isolation levels, CLI/API integration, live providers, content quality, export readiness, or Phase 33 closure.
**Notes for Next Work**: Plan 33-09 can use the `list`/`inspect`/`private_display` access-event action set and should keep exact private values confined to dedicated private excerpt revision storage.

## Repository API Inventory

- `KoreanGrammarRepository.store_bundle()`, `load_bundle()`, and `list_active_ready_bundles()` persist immutable grammar bundle/member rows, detect exact retry, reject changed identity reuse, and rehash loaded members/bundles before returning typed `GrammarBundleRecord` values.
- `KoreanPersonalSourceRepository.store_rows()`, `list_inventory()`, and `append_decision()` persist every ordered custom row, compute duplicate visibility from source-order item keys, recompute a safe inventory root, and append explicit decision revisions under expected-latest CAS.
- `ReviewRepository.create_candidate_revision()`, `approve_revision()`, and `list_fields_with_audit()` append review revisions/decisions, mutate only explicit current pointers, and commit content-free access events before returning safe rows.
- `ReviewRepository.reserve_audio_publication()`, `append_audio_publication_transition()`, `list_reconcilable_audio_publications()`, and `finalize_audio_publication()` reserve exact final paths before provider work, enforce reservation state/version transitions, allow duplicate artifact hashes at distinct paths, and finalize only published reservations.

## Ordered Round-Trip Evidence

- Personal-source row storage preserves positions `[1, 2, 3]`, including a visible exact duplicate at position `2` with `duplicate_of_position == 1`.
- Same-lemma/distinct-surface rows remain separate inventory members because ordering uses persisted `input_position` and `item_key`, not lemma collapse.
- Exact row replay returns the same inventory root and does not insert duplicate rows.
- Reordered or changed input under the same job/source identity raises `PersonalSourceConflict` and leaves the row count unchanged.

## Rehash Results

- Grammar member hashes and bundle hashes are recomputed from typed payloads on insert and load.
- Tampering a stored member hash to a different valid lowercase SHA-256 raises `KoreanGrammarRepositoryIntegrityError` on load.
- Active grammar listing admits only `status='active'` plus `source_kind='active-approved-snapshot'`; candidate/synthetic source kinds are filtered out.

## Transaction and CAS Evidence

- Candidate revision exact retry returns the existing revision and does not duplicate `review_field_revisions`.
- Changed candidate content under the stale request/version raises `ReviewRepositoryConflict` without appending a second revision.
- Approval requires the current pointer version; stale approval raises `ReviewRepositoryCASConflict` and leaves `review_decisions` unchanged.
- File-backed two-session stale candidate writing leaves exactly one revision row and zero access events after the loser conflicts.
- Access event identity is stable on `(actor_id, request_id, action)`; same command hash replays, changed command hash conflicts, and no new event/result is returned.
- Audio finalization before `published` raises `ReviewRepositoryCASConflict`; `reserved -> staged -> published -> finalized` succeeds with version increments.
- Shared final path reservation conflicts, while the same artifact SHA-256 can finalize distinct request/revision-qualified paths.

## TDD Log

- 33-08 RED: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_korean_grammar_repository.py tests/repositories/test_korean_personal_source_repository.py tests/repositories/test_review_repository.py -q` failed during collection with missing `korean_grammar_repository`, `korean_personal_source_repository`, and `review_repository` modules.
- GREEN: Added the three repository modules, typed DTOs, SQLAlchemy statements, and focused tests; scoped repository tests passed.
- REFACTOR: Wrapped grammar rehash validation as a repository integrity error, removed the Pydantic `register` shadow warning, added the two-session stale-writer proof, and aligned access-event actions with repository reads.

## Verification Results

- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_korean_grammar_repository.py -k 'insert or retry or conflict or rollback or load or rehash or candidate or synthetic' -q` passed: `1 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_korean_personal_source_repository.py -k 'every_position or duplicate_of or same_lemma or ordered_inventory_root or no_inventory_drop or retry or reorder or decision or cas or no_auto_bridge' -q` passed: `1 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_review_repository.py -k 'reserve_before_call or reservation_commit or unique_revision_path or same_hash_distinct_paths or shared_path_conflict or list_reconcilable or finalize_requires_published or finalize_atomic_pointer_event or failed_unknown_no_retry or crash_before_call or crash_after_staging or crash_after_publish or crash_after_finalize or stable_access_key or changed_hash_conflict or no_release_on_conflict' -q` passed: `2 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_review_repository.py -q` passed after adding two-session proof: `3 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_korean_grammar_repository.py tests/repositories/test_korean_personal_source_repository.py tests/repositories/test_review_repository.py -q` passed: `5 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/db/test_phase33_schema.py tests/test_migration_schema_parity.py -q` passed after the access-action alignment: `21 passed, 26 warnings`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync python -m compileall -q src/multilang/repositories/korean_grammar_repository.py src/multilang/repositories/korean_personal_source_repository.py src/multilang/repositories/review_repository.py` passed with only the expected `VIRTUAL_ENV` warning.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync alembic heads` passed: `20260828_19 (head)`.
- Narrow source scan for provider/network/destructive calls in the three new repositories found no files.
- `git diff --check -- src/multilang/repositories/korean_grammar_repository.py src/multilang/repositories/korean_personal_source_repository.py src/multilang/repositories/review_repository.py tests/repositories/test_korean_grammar_repository.py tests/repositories/test_korean_personal_source_repository.py tests/repositories/test_review_repository.py alembic/versions/20260828_19_grammar_personal_sources.py src/multilang/db/models.py tests/db/test_phase33_schema.py tests/test_migration_schema_parity.py` passed with no output.

## Bounded Claim

This proves the Phase 33 repository adapters preserve immutable grammar roots, ordered personal-source rows, explicit decision revisions, review pointer CAS, access-event audit-before-return, and recoverable audio publication state in isolated local databases. It does not prove production PostgreSQL migration/execution, multi-process locking under production isolation, full Plan 05 in-memory service feature parity, private excerpt value release, provider calls, exports, publication, or phase closure.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: RED collection failures were observed before implementation. Exact plan commands, full scoped repository tests, schema/parity regression, compileall, Alembic head, source scan, and diff hygiene passed in the frozen offline environment.
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
  summary: `review_access_events.action` allowed `private_display` and transition-like actions but not `list`/`inspect`; Plan 33-08 audited read behavior requires `list`. The Phase 33 migration, ORM constraint, and migrated schema test were aligned to allow `list` and `inspect` without adding private-value columns.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Plan verification describes isolated PostgreSQL/two-session behavior, but the available offline test harness uses SQLite. A file-backed two-session stale-writer regression was added; live PostgreSQL isolation remains outside this local proof boundary.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The execute workflow normally updates SPEC, ROADMAP, and state fingerprint, but the active handoff said not to touch those files without a separate decision. Those lifecycle writes were skipped and recorded here.
</deltas>

<judgment>
<active_constraints>
- Keep grammar bundle/member persistence insert-only and hash-revalidated on load.
- Preserve every Korean personal-source input position and compute duplicate visibility from ordered row identity; do not set-dedupe, lemma-collapse, or auto-generate bridge content.
- Mutate only explicit current pointers/reservations under expected-version checks; keep revisions, decisions, access events, and audio transitions append-only.
- Access events remain content-free and must commit before returning safe rows or any later privileged value release.
- Audio final paths remain unique by request/revision-qualified path identity; artifact SHA-256 remains non-unique.
</active_constraints>
<unresolved_uncertainty>
- Live PostgreSQL transaction/isolation behavior is not verified in this run.
- Repository methods are not wired into coordinators, CLI/API routes, production workers, or private excerpt release paths.
- Full parity with every in-memory `ReviewRevisionService` feature, especially dependent staleness and richer AI/audio evidence payloads, remains for later integration if needed.
</unresolved_uncertainty>
<decision_posture>
- Continue with typed, minimal repository adapters over the Phase 33 schema. Favor exact retry-or-conflict semantics, deterministic safe roots, and versioned CAS over generic upserts or mutable content shortcuts.
- Treat any future need for additional persisted review transition metadata as a new schema decision, not an implicit dict/blob expansion.
</decision_posture>
<anti_regression>
- Do not remove `list`/`inspect` from the allowed content-free access-event action set.
- Do not update immutable grammar rows, personal rows/decisions, review revisions/decisions/access events, or audio transitions in place.
- Do not return private values from ordinary list/safe inventory repository methods.
- Do not add a uniqueness constraint on audio artifact hashes.
- Do not treat SQLite repository proof as production PostgreSQL authorization.
</anti_regression>
</judgment>
