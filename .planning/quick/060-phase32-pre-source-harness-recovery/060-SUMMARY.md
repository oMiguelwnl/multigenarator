---
task: 060-phase32-pre-source-harness-recovery
runtime: opencode
assurance: self_checked
status: done
---

# Quick Task 060 Summary: Phase 32 Pre-Source Harness Recovery

**Completed**: 2026-09-03
**Git Actions**: None; commit not requested.
**Deviations**: This quick-task record was written after the bounded recovery edit because the issue surfaced during continuation of Phase 32 Plan 18. The deviation is documented to avoid an untracked out-of-plan code change.

## Completed Work

- Added RED tests proving `run_full(...)` was missing and that non-ready preflight must block full-mode execution.
- Implemented guarded `full` mode in `scripts/run_phase32_isolated_suite.py`.
- The full-mode harness now uses shell-free `uv run --project <repo> --frozen --no-sync pytest <repo>/tests`, strips credential-name environment variables, sets disposable HOME/XDG/TMP/DB roots, injects a `sitecustomize.py` socket poison, records content-free output hashes, and fails closed on network/provider attempts.
- Updated the Plan 32-18 preflight evidence to reflect the new harness hash while preserving `status=blocked` for unresolved shared `.venv` identity.

## Verification

- RED: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/scripts/test_run_phase32_isolated_suite.py -q` failed on missing `run_full`.
- GREEN: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/scripts/test_run_phase32_isolated_suite.py -q` passed: `5 passed`.
- Regression: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/scripts/test_run_phase32_isolated_suite.py tests/services/test_phase31_runtime_isolation.py -q` passed: `19 passed`.
- CLI help: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync python scripts/run_phase32_isolated_suite.py --help` showed `--mode {dependency-only,full}`, `--preflight-file`, `--dependency-output`, and `--readiness-output`.
- Blocked gate proof: invoking `--mode full` against blocked Plan 32-18 preflight raised `ValueError: pre-source preflight is not ready` before creating suite/dependency evidence.
- Whitespace check passed for touched files.

## Remaining Blocker

Plan 32-18 remains blocked by shared `.venv` identity/invariance:

- Current no-follow `.venv` fingerprint: `c59fa62c6fc469aa896cbc68f2df79c46d0120b072f5bbf41b1e726ef3092526`
- Expected Phase 32 receipt hash: `d6a8151e363a1c511d3a614082c2be646b6f24ef1a2211c4dffece73c57ffbf6`
- Current `.venv` status: `unsafe` because it contains symlinks; no repair or rebaseline was performed.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified harness full-mode behavior with focused tests and confirmed blocked preflight still prevents full-suite execution. No `.venv` mutation, dependency sync, source retrieval, provider/network call, database mutation, release, Git action, or publication occurred.
</executor_check>
</checks>

<handoff>
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: true
</handoff>

<deltas>
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Phase 32 Plan 18 expected a full-mode harness, but the implemented script explicitly rejected `--mode full`; added the missing guarded implementation with tests.
- class: factual_discovery
  impact: blocking
  disposition: escalated
  summary: Shared `.venv` fingerprint no longer matches the Plan 01 receipt, so Plan 32-18 remains blocked before full-suite evidence and source retrieval.
</deltas>

<judgment>
<active_constraints>
Do not retrieve NIKL source or run source transformation until Plan 32-18 pre-source readiness is genuinely `ready` and the full suite passes in the guarded harness. Do not silently repair, delete, sync, or rebaseline `.venv`.
</active_constraints>
<unresolved_uncertainty>
Whether the current `.venv` fingerprint should be accepted as a new baseline, repaired to the old baseline, or excluded by a revised authority remains a human/authority decision.
</unresolved_uncertainty>
<decision_posture>
The harness blocker is fixed; the remaining decision is operational authority over shared `.venv` identity, not code behavior.
</decision_posture>
<anti_regression>
Keep full-mode guarded by preflight readiness; preserve credential stripping, socket poison, shell-free subprocess execution, frozen/no-sync semantics, complete tests scope, and fail-closed evidence.
</anti_regression>
</judgment>
