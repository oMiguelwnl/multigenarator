---
phase: 33-grammar-and-personal-sources
plan: "07"
runtime: opencode
assurance: self_checked
---

# Phase 33: Grammar and Personal Sources - Plan 07 Summary

**Completed**: 2026-08-31
**Tasks**: 3
**Git Actions**: None; no staging or commits performed.
**Deviations**: Recoverable factual discoveries only. Lifecycle preflight allowed execution but the canonical worktree was already dirty; work was kept to declared Plan 33-07 files plus this required summary. SPEC, ROADMAP, and state fingerprint were not updated because the active handoff explicitly said not to touch them without a separate decision.
**Decisions Made**: No product, legal, provider, production migration, or publication decisions. Local schema names and SQL constraint names follow the approved persistence contract.
**Notes for Verification**: Verification used disposable SQLite databases through the frozen/offline phase environment. No production database, provider, Azure, asset, or release side effect was performed.
**Notes for Next Work**: Plans 33-08 and 33-09 can consume the new persistence substrate. They should keep private excerpt text isolated to `highlight_private_excerpt_revisions` and use versioned CAS rows for mutable pointers/capabilities.

## Migration Chain

- Settled predecessor before implementation: `20260821_18`.
- New revision: `20260828_19` in `alembic/versions/20260828_19_grammar_personal_sources.py`.
- `down_revision`: `20260821_18`.
- Current Alembic head after implementation: `20260828_19 (head)`.

## Schema Inventory

- Grammar authority: `korean_grammar_bundles`, `korean_grammar_members`.
- Personal sources: `personal_source_rows`, `personal_source_decisions`.
- Private context: `highlight_private_excerpt_revisions`, `private_context_capabilities`, `private_disclosure_attempts`, `private_processing_receipts`.
- Review evidence: `review_field_revisions`, `review_current_pointers`, `review_decisions`, `review_access_events`.
- Item/run accounting: `item_terminal_status_events`, `item_processing_facts`, `generation_run_denominators`.
- Audio publication: `audio_publication_reservations`, `audio_publication_transitions`, `audio_revision_evidence`.

## Constraint and Index Inventory

- Enforced exact 64-character lowercase hex hash checks across authority, receipt, review, item, denominator, and audio evidence hashes.
- Enforced closed states/actions for grammar bundle status, private capability/attempt state, review status, terminal status, audio reservation state, access action, and audio transition steps.
- Enforced uniqueness for grammar bundle IDs, grammar bundle sequence/construction, personal source position/source-row hash, personal decision revision, private capability ID/idempotency key, disclosure attempt version, processing receipt hashes, review field revision, review current pointer identity, review decision revision, stable review access identity, terminal item stage, processing fact attempt, denominator job/stage, one audio reservation per field revision, one final path hash, one transition version, and one evidence tuple per reservation/role.
- Added planned lookup indexes including `ix_personal_source_rows_job_id_item_key`, `ix_private_context_capabilities_item_state`, `ix_review_current_pointers_item_field`, `ix_item_terminal_status_events_status_job`, and `ix_audio_publication_reservations_item_field`.
- Added SQLite and PostgreSQL append-only guards for immutable Phase 33 history/evidence tables; mutable state remains limited to explicit current pointers, private capabilities, and audio reservations.

## Private Column Audit

- Exact private highlight text and private paths are confined to `highlight_private_excerpt_revisions` via `normalized_text`, `source_path`, and `raw_location`.
- Other Phase 33 tables store IDs, hashes, counts, versions, reason codes, states, provider/model/route identifiers, and timestamps only.
- ORM metadata intentionally does not add ordinary relationships from job/item/review models to the private excerpt table.

## TDD Log

- 33-07-01 RED was already observed before implementation: `tests/db/test_phase33_schema.py` failed on missing Phase 33 tables and revision. GREEN added revision `20260828_19`, complete tables, indexes, constraints, private token cap, audio reservation/evidence rules, and append-only guards.
- 33-07-02 RED covered missing ORM metadata parity for Phase 33 tables. GREEN added SQLAlchemy mappings with mirrored columns, indexes, unique/check constraints, explicit versions, and no private-value convenience relationships.
- 33-07-03 RED covered sole-head/parity/round-trip expectations. GREEN updated the parity harness to recognize `20260828_19` as the sole head while preserving prior Phase 32 migration regression coverage.
- Additional RED: non-hex lowercase `g...` command hashes were accepted by the first length/lowercase check. GREEN tightened migration and ORM helper checks to accept only 64 lowercase hex characters and updated test fixtures to use valid evidence hashes.

## Verification Results

- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/db/test_phase33_schema.py -q` passed: `8 passed, 11 warnings`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync alembic heads` passed: `20260828_19 (head)`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/db/test_phase33_schema.py tests/test_migration_schema_parity.py -q` passed after the hash-check tightening: `21 passed, 26 warnings`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync python -m py_compile alembic/versions/20260828_19_grammar_personal_sources.py src/multilang/db/models.py tests/db/test_phase33_schema.py tests/test_migration_schema_parity.py` passed with only the expected `VIRTUAL_ENV` warning.
- `test "$(UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync alembic heads | wc -l)" -eq 1` passed.
- `git diff --check -- alembic/versions/20260828_19_grammar_personal_sources.py src/multilang/db/models.py tests/db/test_phase33_schema.py tests/test_migration_schema_parity.py .planning/phases/33-grammar-and-personal-sources/33-07-SUMMARY.md` passed with no output.

## Bounded Claim

This proves an isolated additive/reversible Phase 33 persistence schema, ORM metadata parity, one-head Alembic history, append-only evidence guards, private-column separation, and representative constraint failures on disposable local databases. It does not prove production PostgreSQL migration execution, runtime repository transactions, CLI observability, live providers, Azure, content quality, learner-ready deck export, release, or phase closure.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Targeted schema tests, combined migration parity tests, py_compile, one-head check, hex-only hash regression, and diff hygiene check passed in the frozen offline phase environment. The plan checker status in the source plan was skipped/unreviewed, so execution assurance remains self_checked.
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
  summary: `node .planning/bin/gsdd.mjs lifecycle-preflight execute 33 --expects-mutation phase-status` allowed execution but reported a dirty canonical worktree and detached Phase 31 candidate worktrees. Work stayed inside Plan 33-07 declared code/test files plus the required summary.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The execute workflow normally updates SPEC, ROADMAP, and state fingerprint, but the active handoff explicitly said not to touch those files without a separate decision. Those lifecycle writes were skipped and recorded here.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Verification ran on disposable SQLite databases rather than a live PostgreSQL instance. The migration uses PostgreSQL-compatible lower-case identifiers, explicit constraints/indexes, and a PostgreSQL trigger function path, but live PostgreSQL execution remains outside this plan's local proof boundary.
</deltas>

<judgment>
<active_constraints>
- Do not migrate production databases, publish content, call live providers/Azure, or promote learner-ready artifacts from this schema work.
- Keep private highlight text and paths confined to `highlight_private_excerpt_revisions`; all general review, context, provider, item, and audio tables must remain hash/count/ID/status based.
- Preserve append-only history for grammar members, personal rows/decisions, private excerpt revisions, disclosure attempts/receipts, review revisions/decisions/access events, item facts/events, run denominators, audio transitions, and audio revision evidence.
- Only explicit versioned rows are mutable: review current pointers, private context capabilities, and audio publication reservations.
- Keep Alembic history linear with sole head `20260828_19` until a future approved migration extends it.
</active_constraints>
<unresolved_uncertainty>
- Live PostgreSQL execution was not run in this local verification pass.
- Repository methods, transaction/CAS behavior, CLI/API observability, and production compatibility over real data remain for later plans.
- Phase 33 is not phase-verified or closed by this plan summary.
</unresolved_uncertainty>
<decision_posture>
- Use DB-enforced invariants and immutable evidence rows as the substrate for Phase 33 grammar/personal-source flows.
- Prefer exact IDs, hashes, closed states, and versioned CAS anchors over mutable JSON shortcuts or inferred success/backfill semantics.
- Treat compatibility with prior Phase 32 data conservatively: new Phase 33 evidence is absent until explicitly created, never inferred as accepted/reviewed from coarse legacy status.
</decision_posture>
<anti_regression>
- Do not add private text/path/prompt/payload columns to general Phase 33 tables.
- Do not add uniqueness to `audio_revision_evidence.artifact_sha256`; identical bytes may back different approved final paths.
- Do not allow in-place update/delete on append-only Phase 33 evidence tables.
- Do not change `private_context_capabilities.tokenization_rule_id` away from `phase33-private-token-v1` or raise `max_context_tokens` above 24 without a new approved plan.
- Do not mark Phase 33 complete solely because the migration and ORM parity tests pass.
</anti_regression>
</judgment>
