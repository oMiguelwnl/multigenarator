---
phase: 11
slug: highlight-pipeline-integration
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-05
---

# Phase 11 — Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | pyproject.toml |
| **Quick run command** | `python -m pytest tests/services/test_highlight_candidate_extraction.py tests/services/test_generate_job.py -q` |
| **Full suite command** | `python -m pytest tests/services/test_highlight_candidate_extraction.py tests/repositories/test_highlight_import_repository.py tests/services/test_highlight_ingest_lexical_items.py tests/cli/test_generate_command.py tests/cli/test_kindle_highlight_preview_command.py tests/integration/test_v12_existing_mode_regression_boundary.py tests/integration/test_kindle_local_normalization_flow.py -q` |
| **Estimated runtime** | < 60 seconds focused |

## Sampling Rate

- **After every task commit:** Run that task's focused `<automated>` command.
- **After every plan wave:** Run the plan-level verification command.
- **Before `/gsd-verify-work`:** Full suite above must be green.
- **Max feedback latency:** < 60 seconds for focused phase checks.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | INGEST-04 | T-11-01 | stable keys omit file path/order | unit | `python -m pytest tests/services/test_highlight_candidate_extraction.py tests/services/test_generate_job.py -q` | ✅ | ⬜ pending |
| 11-02-01 | 02 | 1 | INGEST-04 | T-11-02 | private text separated from manifest | repository | `python -m pytest tests/repositories/test_highlight_import_repository.py -q` | ✅ | ⬜ pending |
| 11-03-01 | 03 | 2 | MODE-01, INGEST-04 | T-11-03 | blocked ungrounded highlights are counted not backfilled | service | `python -m pytest tests/services/test_highlight_ingest_lexical_items.py -q` | ✅ | ⬜ pending |
| 11-04-01 | 04 | 3 | MODE-01, INGEST-04 | T-11-04 | count-only CLI output and public alias | CLI/integration | `python -m pytest tests/cli/test_generate_command.py tests/integration/test_v12_existing_mode_regression_boundary.py -q` | ✅ | ⬜ pending |

## Wave 0 Requirements

Existing pytest infrastructure covers all phase requirements. Each task creates or updates its focused tests before implementation.

## Manual-Only Verifications

All Phase 11 behaviors have automated verification.

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covered by existing pytest setup
- [x] No watch-mode flags
- [x] Feedback latency target < 60s

**Approval:** pending execution
