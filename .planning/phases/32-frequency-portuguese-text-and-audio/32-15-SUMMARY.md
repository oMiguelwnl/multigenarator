---
phase: 32-frequency-portuguese-text-and-audio
plan: "15"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 15 Summary

**Completed**: 2026-09-01
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: Fast-track implementation kept the plan's offline/no-release boundary and implemented compact deterministic coverage for the core safety, aggregate, and promotion contracts instead of running exhaustive failure injection at every fsync/rename boundary.
**Decisions Made**: Release safety distinguishes `safe_for_local_release` from `safe_to_publish`; local-only/private-approved members can pass local release while publication remains false. Review aggregation and release promotion grant no review, promotion, release, remote, or publication authority beyond the exact local operation.
**Notes for Verification**: This summary proves offline read-only review aggregation, fixed-member release safety/build evidence, and local complete-tree promotion with current-pointer idempotence. It does not prove real review receipts, production content/audio quality, live provider/Azure execution, production DB mutation, external release, Git remote action, publication, or Phase 34 Anki acceptance.
**Notes for Next Work**: Continue to Plan 32-16 only as offline/constrained delivery tooling. Plan 32-17 still contains a blocking user checkpoint before source access.

## Completed Work

- Added read-only `validate_korean_production_review_batches(...)` and `korean_production_review_identity_hash(...)` to `src/multilang/services/korean_production_evidence.py`.
- Added CLI command `validate-korean-production-review-batches` with explicit authority file, DB/job, receipt directories, counts, and aggregate output.
- Added `src/multilang/services/korean_release_safety.py` with fixed release member inventory, safety/build report generation, local/publication distinction, private marker rejection, atomic JSON writes, complete-tree manifest creation, local promotion, pointer replacement, and exact retry no-op validation.
- Added CLI commands `build-korean-release-safety` and `promote-korean-release-bundle`.
- Added focused tests in `tests/services/test_korean_release_safety.py`, `tests/cli/test_korean_release_safety_commands.py`, and extended production evidence service/CLI tests.

## Verification

- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_production_evidence.py -k 'review_aggregate or bounded or risk_coverage or read_only' -q` -> `4 passed, 2 deselected in 172.14s`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_korean_production_evidence_commands.py -k 'validate_review_batches or no_import or read_only' -q` -> `2 passed, 3 deselected in 37.52s`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_release_safety.py -k 'builder or schema or private or scan or attribution or safe_to_publish or build_result or acyclic or release_promoter or staging or fsync or reopen or atomic_rename or pointer or interruption or collision or exact_retry' -q` -> `2 passed in 1.46s`.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_korean_release_safety_commands.py -k 'build_safety or fixed_roots or privacy or release_graph or release_promoter or staging or fsync or reopen or atomic_rename or pointer or interruption or collision or exact_retry' -q` -> `2 passed in 27.34s`.
- Regression: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_release_safety.py tests/cli/test_korean_release_safety_commands.py -q` -> `4 passed in 37.10s`.
- Regression: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_korean_production_evidence_commands.py -q` -> `5 passed in 48.14s`.
- Registry: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync multilang check-anki-id-registry --production-roots` -> `anki_id_registry_status=clean`, `scanned_files=210`, `issue_count=0`.
- Whitespace check passed for modified 32-15 files.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified offline aggregate/safety/promoter code paths and restored Anki ID registry cleanliness. No live release, provider, Azure, production DB, Git remote, publication, or Phase 34 observed Anki action was performed.
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
  summary: Plan 32-14's local Korean frequency Anki ID constants violated the production Anki ID registry scanner; they were replaced with `registry_id(...)` lookups before Plan 32-15 verification continued.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The user requested faster execution, so this pass implemented compact deterministic tests for the core aggregate/safety/promoter contracts while preserving the plan's no-external-action boundary.
</deltas>

<judgment>
<active_constraints>
Plan 32-15 authorizes only offline/read-only review aggregation, release safety/build evidence, and local durable promotion tooling. It does not authorize review import/application, production DB mutation, live release, Git remote action, arbitrary destination, provider/Azure calls, publication, or Phase 34 closure.
</active_constraints>
<unresolved_uncertainty>
Exact Phase 31 active output, real NIKL source/rights facts, transformed 3000-entry inventory, real review receipts, provider model/budget approval, live Azure profile/synthesis, production DB target, final full-suite evidence, observed Anki import/playback, and publication approval remain unresolved.
</unresolved_uncertainty>
<decision_posture>
Use hash/count-only review aggregates and fixed-member safety reports as local evidence. Treat `safe_for_local_release` and `safe_to_publish` as separate gates; local-only approval never implies publication permission.
</decision_posture>
<anti_regression>
Do not add import/application side effects to review aggregation; do not let local release imply publication; do not accept private markers, traversal, links, or undeclared members in safety/promotion paths; keep release promotion fixed to exact declared members, manifest-last creation, pointer-after-target replacement, and exact retry no-op behavior.
</anti_regression>
</judgment>
