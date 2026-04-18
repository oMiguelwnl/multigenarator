---
phase: 1
slug: job-orchestration-recovery
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-18
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/domain tests/repositories tests/services tests/cli -q` |
| **Full suite command** | `uv run pytest tests -q` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/domain tests/repositories tests/services tests/cli -q`
- **After every plan wave:** Run `uv run pytest tests -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | DECK-01 | T-01-job-01 / T-01-job-02 | Unsupported language values rejected before job creation | unit | `uv run pytest tests/test_settings.py tests/domain/test_jobs.py -q` | ✅ | ⬜ pending |
| 1-01-02 | 01 | 1 | JOB-01 | T-01-job-02 | Resume diagnostics modeled explicitly and validated | unit | `uv run pytest tests/domain/test_jobs.py -q` | ✅ | ⬜ pending |
| 1-02-01 | 02 | 2 | JOB-01 | T-01-job-03 | Persisted state is schema-validated and repository-backed | integration | `uv run pytest tests/repositories/test_job_repository.py -q` | ✅ | ⬜ pending |
| 1-02-02 | 02 | 2 | JOB-03 | T-01-job-04 | Duplicate item keys are prevented by repository and schema rules | integration | `uv run pytest tests/repositories/test_job_repository.py -q` | ✅ | ⬜ pending |
| 1-03-01 | 03 | 3 | DECK-01 | T-01-job-01 | CLI accepts only supported languages and one primary command surface | cli | `uv run pytest tests/cli/test_generate_command.py -q` | ✅ | ⬜ pending |
| 1-03-02 | 03 | 3 | JOB-01, JOB-03 | T-01-job-02 / T-01-job-04 | Resume continues from persisted state; rerun skips duplicates unless confirmed overwrite | service | `uv run pytest tests/services/test_generate_job.py -q` | ✅ | ⬜ pending |
| 1-04-01 | 04 | 4 | JOB-02 | T-01-job-05 | Progress shows stage counters and failure counts without verbose default logs | unit | `uv run pytest tests/test_progress.py tests/test_job_summary.py -q` | ✅ | ⬜ pending |
| 1-04-02 | 04 | 4 | JOB-01, JOB-02, JOB-03 | T-01-job-02 / T-01-job-04 / T-01-job-05 | End-to-end job flow preserves resume, duplicate skipping, bounded retry, and summary visibility | smoke | `uv run pytest tests/integration/test_job_flow.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure does not exist yet, so Phase 1 Plan 01 must create:
  - `tests/conftest.py` — shared fixtures
  - `tests/domain/test_jobs.py` — contract tests for enums and diagnostics
  - `tests/test_settings.py` — environment/config bootstrap tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stage counter readability in a real terminal | JOB-02 | Terminal rendering fidelity is easier to judge visually than via assertions alone | Run `uv run python -m multilang.cli generate --language pt --source frequency --level 1` against a stubbed dataset and confirm the default output shows one stage line with completed/total, retries, failures, and skipped counts. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-18
