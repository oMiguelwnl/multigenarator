---
task: 060-phase32-pre-source-harness-recovery
runtime: opencode
assurance: self_checked
type: quick
---

# Quick Task 060: Phase 32 Pre-Source Harness Recovery

## Objective

Recover the code-side blocker preventing Phase 32 Plan 18 from invoking the pre-source full-suite harness, without modifying `.venv`, retrieving source bytes, syncing dependencies, contacting providers, or widening authority.

## Scope

- Modify only `scripts/run_phase32_isolated_suite.py` and its focused test file.
- Preserve fail-closed behavior when Plan 32-18 preflight is not ready.
- Do not repair, delete, sync, or rebaseline `.venv`.

## Tasks

<tasks>
<task id="060-01" type="auto" tdd="true">
  <name>Add tested full-mode harness behavior</name>
  <files>
    - MODIFY: scripts/run_phase32_isolated_suite.py
    - MODIFY: tests/scripts/test_run_phase32_isolated_suite.py
  </files>
  <action>Add failing tests for full-mode behavior, then implement the minimal full-mode path that rejects non-ready preflight, uses fixed `uv run --frozen --no-sync pytest tests`, strips credential-name environment variables, poisons socket construction through `sitecustomize`, uses shell-free subprocess execution, records content-free evidence, and refuses success on network/provider attempts.</action>
  <verify><automated>UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/scripts/test_run_phase32_isolated_suite.py tests/services/test_phase31_runtime_isolation.py -q</automated></verify>
</task>
</tasks>

## Claim Limit

This quick task proves only that the harness now supports a guarded full-mode path and still fails closed on blocked preflight. It does not prove `.venv` identity, run the repository full suite, authorize source retrieval, or approve transformation/redistribution/provider/Azure/database/release/publication actions.
