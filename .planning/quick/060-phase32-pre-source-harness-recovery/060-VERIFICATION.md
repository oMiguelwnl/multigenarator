---
task: 060-phase32-pre-source-harness-recovery
runtime: opencode
assurance: self_checked
status: passed_with_blocked_phase_gate
---

# Quick Task 060 Verification

## Result

The quick recovery goal is met: Phase 32's isolated-suite harness now has tested full-mode behavior and still fails closed when Plan 32-18 preflight is blocked.

## Evidence Checked

- `tests/scripts/test_run_phase32_isolated_suite.py` includes coverage for guarded full-mode execution and blocked preflight.
- `scripts/run_phase32_isolated_suite.py` exposes `--mode full`, `--preflight-file`, `--dependency-output`, and `--readiness-output`.
- Focused regression passed: `19 passed` for `tests/scripts/test_run_phase32_isolated_suite.py` and `tests/services/test_phase31_runtime_isolation.py`.
- Blocked full-mode invocation fails before suite output creation with `ValueError: pre-source preflight is not ready`.

## Residual Risk

Plan 32-18 itself is not complete. The current `.venv` fingerprint does not match the Phase 32 environment receipt, so source retrieval remains blocked until an explicit recovery/rebaseline decision is made and the guarded full suite passes.
