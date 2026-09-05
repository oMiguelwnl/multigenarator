---
phase: 33-grammar-and-personal-sources
plan: "10"
runtime: opencode
assurance: self_checked
---

# Phase 33: Grammar and Personal Sources - Plan 10 Summary

**Completed**: 2026-09-01
**Tasks**: 3
**Git Actions**: None; no staging, commits, pushes, config changes, cleanup, or destructive git actions performed.
**Deviations**: Recoverable factual discoveries only. The new field-level regeneration surface was added as an optional `GenerateTextItemsService.regenerate_field(...)` method so the legacy batch `execute(...)` path remains unchanged. An attempt-only pending selection gap was found during TDD and fixed by adding safe processing-fact listing and resumed attempt-number offsets.
**Decisions Made**: Keep Phase 33 job coordination thin: source adapters provide inventory, per-source handlers perform source-specific work, `JobRepository` persists attempt/status/denominator facts, and closed field dispatch uses injected text, translation, review, and role-specific audio ports.
**Notes for Verification**: Verification used disposable SQLite databases, deterministic fakes, poisoned fallback ports, and offline frozen dependencies. No live provider, production private import, production database, audio artifact write, deck export, external authority creation, or publication path was invoked.
**Notes for Next Work**: Plan 11 can add CLI/status UX on top of `Phase33JobCoordinator` and `GenerateTextItemsService.regenerate_field(...)`; it must still treat review/audio/private authority as gates, not as implicit success.

## Implementation

- Added `JobRepository.list_phase33_processing_facts(...)` as a content-free safe query over persisted attempt/processed facts.
- Added `src/multilang/services/phase33_jobs.py` with `Phase33JobItem`, `Phase33JobCoordinator`, and `Phase33JobResult`.
- The coordinator preserves deterministic source order across grammar, custom, and highlight sources, skips duplicates/deferred rows as explicit denominator items, skips private `disclosing|disclosed|failed_unknown` states, and delegates all source-specific processing to injected handlers.
- `start` selects only items with no prior terminal status and no prior attempt fact. `resume` processes pending attempt-only items and retryable selections, skips current accepted/review-required/private-closed items, and offsets attempt numbers so persisted facts do not conflict with prior attempts.
- Item-local controlled failures persist sanitized failed terminal status and do not stop siblings; systemic schema/config/authority failures propagate and stop fail-closed without misleading later item processing.
- Added `GenerateTextItemsService.regenerate_field(...)` for closed Phase 33 field dispatch: `definition`, `sentence`, and `microexample` use the text generator; `translation` uses the exact translation adapter; `word_audio` and `sentence_audio` use separate injected audio ports.
- Text/translation field regeneration appends pending review candidate revisions through the review repository using value SHA-256 only. Audio dispatch reserves publication first with exact revision/request/authority/root hashes, then calls the role-specific audio port.

## Coordinator Graph

| Input | Owner | Output |
|---|---|---|
| Grammar/custom/highlight inventory | Injected source adapters | Ordered `Phase33JobItem` list |
| Prior terminal status and attempt facts | `JobRepository` | Start/resume selection, skipped/current facts, attempt offsets |
| Source-specific generation/review/media behavior | Injected handlers | `ItemHandlerResult` or controlled item/systemic error |
| Per-item isolation and bounded retry | `run_item_outcomes(...)` | Sanitized item outcomes |
| Attempt/status/denominator persistence | `JobRepository` | Exact `ItemRunReport` and completion predicate |

## Mixed-Run Outcome Table

| Case | Handler Call | Persisted Result | Aggregate Meaning |
|---|---:|---|---|
| Grammar accepted/current obligations | yes | accepted + processed fact | Counts accepted/processed |
| Custom duplicate row | no | no attempt/status mutation | Counts duplicate + not_attempted |
| Custom item-local failure | yes | failed + attempt fact, no raw error text | Counts failed, siblings continue |
| Highlight stale media/review | yes | review_required + processed fact | Blocks completion |
| Current accepted replay | no | existing accepted/skipped-current fact | Counts skipped_current and accepted |
| Review-required replay | no | existing review_required status | Blocks completion, not reprocessed |
| Private disclosing/disclosed/failed_unknown | no | no callback or privileged load | Remains not_attempted/deferred by explicit source state |
| Systemic schema/config/authority failure | first failing item only | no misleading later status | Raises fail-closed |

## Resume and Idempotency Trace

- Exact retries of attempt/status facts return the existing content-free records; changed payloads conflict.
- `start` now ignores items with an attempt-only fact, preventing duplicate side effects for in-flight/pending attempts.
- `resume` retries attempt-only pending items with the next persisted attempt number, avoiding conflicts with immutable prior attempt facts.
- Current accepted rows can be represented as skipped-current facts and do not invoke handlers.
- Review-required rows are left unchanged and visible in recomputed denominators.
- Closed private states are never sent to handlers or fallback ports.

## Field Dispatch Matrix

| Field | Port | Persistence |
|---|---|---|
| `definition` | `text_generation_service.generate_definition(...)` | `create_candidate_revision(...)` with value hash |
| `sentence` | `text_generation_service.generate_sentence(...)` | `create_candidate_revision(...)` with value hash |
| `microexample` | `text_generation_service.generate_sentence(...)` | `create_candidate_revision(...)` with value hash under `microexample` |
| `translation` | injected `translation_adapter.translate_sentence(...)` | `create_candidate_revision(...)` with value hash |
| `word_audio` | injected `word_audio_port.synthesize(...)` | `reserve_audio_publication(...)` before call |
| `sentence_audio` | injected `sentence_audio_port.synthesize(...)` | `reserve_audio_publication(...)` before call |

## TDD Evidence

- RED 33-10-01: Repository tests failed because `JobRepository.record_phase33_item_outcome(...)` was missing. GREEN: Added granular attempt/status/denominator/inventory methods; selector passed `7 passed, 5 deselected`.
- RED 33-10-02: Coordinator tests failed during collection with `ModuleNotFoundError: No module named 'multilang.services.phase33_jobs'`. GREEN: Added the thin source-aware coordinator; focused coordinator suite passed.
- RED 33-10-02b: Attempt-only start/resume test first exposed fixture issues, then the intended immutable fact conflict from reprocessing a pending item. GREEN: Added safe processing-fact listing plus start skip/resume attempt offsets; selector passed `2 passed, 2 deselected`.
- RED 33-10-03: Field-dispatch tests failed because `GenerateTextItemsService.__init__()` did not accept review/translation/audio ports. GREEN: Added optional injected ports and `regenerate_field(...)`; selector passed `3 passed, 23 deselected`.

## Verification Results

- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_job_repository.py -k 'granular or seven_denominators or personal_inventory_ids_order_root or no_inventory_drop or outcome or retry or concurrent or aggregate or duplicate or deferred or private' -q`: `7 passed, 5 deselected`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_phase33_jobs.py -q`: `3 passed` before the attempt-only hardening, then covered by the full touched suite after the added test.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_phase33_jobs.py -k 'start_new_only or retry_pending' -q`: final result `2 passed, 2 deselected`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_generate_text_items.py -k 'definition_text_dispatch or translation_adapter_dispatch or word_audio_port_dispatch or sentence_audio_port_dispatch or audio_reservation_before_call' -q`: `3 passed, 23 deselected`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_job_repository.py tests/services/test_phase33_jobs.py tests/services/test_generate_text_items.py -k 'granular or seven_denominators or personal_inventory_ids_order_root or no_inventory_drop or outcome or retry or concurrent or aggregate or duplicate or deferred or private or grammar or custom or highlight or start_new_only or resume_persisted_facts or skip_current_accepted or retry_pending or explicitly_retryable_failure or leave_review_required or no_repeat_disclosing_disclosed_failed_unknown or deterministic_order or isolation or systemic or bounded or definition_text_dispatch or translation_adapter_dispatch or word_audio_port_dispatch or sentence_audio_port_dispatch or audio_reservation_before_call or unique_revision_path or audio_resume_reconcile or external_call_outside_transaction or pending_candidate or approved_pointer_unchanged or sentence_candidate_no_stale or private_closed_no_call or no_fallback or eligible_custom_nonzero or eligible_highlight_nonzero or ready_counts_separate' -q`: `21 passed, 21 deselected`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_job_repository.py tests/services/test_phase33_jobs.py tests/services/test_generate_text_items.py -q`: `42 passed`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync python -m py_compile src/multilang/repositories/job_repository.py src/multilang/services/phase33_jobs.py src/multilang/services/generate_text_items.py tests/repositories/test_job_repository.py tests/services/test_phase33_jobs.py tests/services/test_generate_text_items.py`: passed with only the expected `VIRTUAL_ENV` warning.
- `git diff --check -- src/multilang/repositories/job_repository.py src/multilang/services/phase33_jobs.py src/multilang/services/generate_text_items.py tests/repositories/test_job_repository.py tests/services/test_phase33_jobs.py tests/services/test_generate_text_items.py`: passed before summary creation.

## Sentinel Scan

- Coordinator tests persist only item IDs, controlled reason codes, hashes, timestamps, and denominator counts; raw handler exception text is not stored.
- Field-dispatch tests use poisoned fallback ports to prove unknown fields fail before calls and translation/audio do not fall through to text-generation defaults.
- Highlight/private replay states are source metadata only; `disclosing`, `disclosed`, and `failed_unknown` items are never passed to handlers by the coordinator.
- No test or implementation invokes a live provider, reads credentials, releases private excerpt text, writes staging bytes, or finalizes publication.

## Bounded Claim

This proves repository-backed Phase 33 item attempt/status/denominator facts, deterministic mixed-source coordination, item-local isolation, systemic fail-closed behavior, attempt-only start/resume safety, content-free custom/highlight inventory projections, and closed field dispatch with reservation-before-audio-call through deterministic local tests. It does not prove live PostgreSQL isolation, production authority creation, live provider execution, real AI/audio evidence quality, private provider policy compliance, actual audio artifact publication, CLI/API UX, deck export, or Phase 33 completion.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: RED failures were observed before implementation for repository granular outcomes, missing coordinator module, attempt-only start/resume selection, and field-dispatch constructor/method support. Focused selectors, full touched-file pytest, py_compile, and diff whitespace checks passed in the frozen offline environment with deterministic fakes only.
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
  summary: `src/multilang/services/phase33_jobs.py` and `tests/services/test_phase33_jobs.py` did not exist; they were created under the plan write set.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Prior attempt-only facts were invisible to coordinator selection through terminal-status listing alone. A content-free `list_phase33_processing_facts(...)` query was added so `start` does not duplicate in-flight work and `resume` can continue with the next attempt number.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Existing batch text generation had no field-specific regeneration API. A separate optional `regenerate_field(...)` method was added instead of changing the legacy `execute(...)` behavior.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Verification used local SQLite and fakes. Production PostgreSQL locking/isolation, live provider behavior, and actual publication remain outside this proof boundary.
</deltas>

<judgment>
<active_constraints>
- Completion must remain derived from persisted terminal statuses, attempt/processed facts, explicit denominators, and current review/audio obligations.
- Do not infer accepted/completed from loop completion, handler success, attempted facts, processed facts, or source inventory size.
- Keep private highlight excerpt/context/prompt/payload values out of ordinary job, review, event, receipt, denominator, telemetry, and export rows.
- Do not call handlers or providers for private `disclosing`, `disclosed`, or `failed_unknown` replay states.
- Audio dispatch must reserve exact publication state before any external audio port call; finalization remains a separate authority/evidence step.
- Unknown regenerable fields and missing exact injected ports must fail before fallback calls.
</active_constraints>
<unresolved_uncertainty>
- Live PostgreSQL transaction/isolation behavior for concurrent Phase 33 job coordination is not verified by this local SQLite run.
- Production source adapters still need to bind real grammar/custom/highlight eligibility, graph, AI-review, private-authority, and audio evidence.
- Real provider output validation, review consensus, acoustic evidence, artifact publication, CLI wiring, and export delivery remain downstream work.
- Terminal-status rows remain exact replay/conflict projections; this plan proves pending attempt resume, not mutable rewriting of an already persisted terminal failure into success.
</unresolved_uncertainty>
<decision_posture>
- Keep the coordinator thin and dependency-injected; source-specific truth stays in source/review/audio/private repositories and handlers.
- Keep field regeneration closed and explicit by field name; prefer missing-port failures over hidden fallbacks.
- Preserve the legacy batch text-generation path while adding field-level Phase 33 orchestration alongside it.
</decision_posture>
<anti_regression>
- Do not reintroduce coarse generate-all completion or caller-supplied success totals.
- Do not process duplicate/deferred/private-closed rows as ordinary eligible side effects.
- Do not reattempt current accepted or review-required rows during resume.
- Do not route translation through the text generator or audio through a generic/fallback port when exact role-specific ports are required.
- Do not reserve audio after the external port call, share final paths across revisions, or finalize publication without exact evidence.
</anti_regression>
</judgment>
