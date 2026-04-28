---
phase: 7
slug: milestone-evidence-audit-hygiene
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-28
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/integration/test_job_flow.py tests/cli/test_generate_command.py -q` |
| **Full suite command** | `uv run pytest tests/integration/test_text_job_flow.py tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_frequency_e2e_export_flow.py tests/integration/test_job_flow.py tests/cli/test_generate_command.py -q` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run that task's focused `<automated>` command.
- **After every plan wave:** Run `uv run pytest tests/integration/test_text_job_flow.py tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_frequency_e2e_export_flow.py tests/integration/test_job_flow.py tests/cli/test_generate_command.py -q`.
- **Before `/gsd-verify-work`:** Full suite above must be green and metadata grep/Python assertions must pass.
- **Max feedback latency:** 60 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 7-01-01 | 01 | 1 | JOB-01, JOB-02, JOB-03 | T-07-01-01 | Current shipped CLI evidence supersedes stale blocker without deleting historical context | integration | `uv run pytest tests/integration/test_job_flow.py tests/cli/test_generate_command.py -q` | ✅ | ⬜ pending |
| 7-01-02 | 01 | 1 | JOB-01, JOB-02, JOB-03 | T-07-01-02 | Requirement evidence references current verification status | metadata | `python - <<'PY'\nfrom pathlib import Path\ntext=Path('.planning/phases/01-job-orchestration-recovery/01-VERIFICATION.md').read_text()\nassert 'status: verified' in text\nassert 'JOB-01' in text and 'JOB-02' in text and 'JOB-03' in text\nPY` | ✅ | ⬜ pending |
| 7-02-01 | 02 | 1 | JOB-01, JOB-02, JOB-03 | T-07-02-01 | Phase 4 validation metadata cannot be mistaken for missing validation | metadata | `python - <<'PY'\nfrom pathlib import Path\ntext=Path('.planning/phases/04-audio-synthesis/04-VALIDATION.md').read_text()\nassert 'nyquist_compliant: true' in text\nassert 'AUDI-01' in text and 'AUDI-02' in text\nPY` | ✅ | ⬜ pending |
| 7-03-01 | 03 | 1 | JOB-01, JOB-02, JOB-03 | T-07-03-01 | Passed UAT and verified quick-task metadata are explicit in frontmatter | metadata | `python - <<'PY'\nfrom pathlib import Path\nfor path in ['.planning/phases/03-sentence-quality-review-loop/03-HUMAN-UAT.md','.planning/phases/04-audio-synthesis/04-HUMAN-UAT.md']:\n    text=Path(path).read_text(); assert 'status: passed' in text and 'pending: 0' in text and 'issues: 0' in text\nq=Path('.planning/quick/260421-001-tatoeba-filtered-secondary-source/260421-001-SUMMARY.md').read_text(); assert 'status: complete' in q and 'verification_status: passed' in q\nPY` | ✅ | ⬜ pending |
| 7-03-02 | 03 | 1 | JOB-01, JOB-02, JOB-03 | T-07-03-02 | Phase 5 summary metadata reflects verified requirement ownership | metadata | `python - <<'PY'\nfrom pathlib import Path\nexpect={"05-01-SUMMARY.md":['CARD-01','CARD-02'],"05-02-SUMMARY.md":['CARD-01','CARD-02','CARD-04','EXPT-02','EXPT-03'],"05-03-SUMMARY.md":['CARD-03','EXPT-01','EXPT-03'],"05-04-SUMMARY.md":['EXPT-01','EXPT-02','EXPT-03']}\nbase=Path('.planning/phases/05-anki-safe-export-contract')\nfor name, ids in expect.items():\n    text=(base/name).read_text()\n    for req in ids: assert req in text, (name, req)\nPY` | ✅ | ⬜ pending |
| 7-04-01 | 04 | 2 | JOB-01, JOB-02, JOB-03 | T-07-04-01 | Requirements and roadmap report current phase closure truthfully | metadata | `python - <<'PY'\nfrom pathlib import Path\nreq=Path('.planning/REQUIREMENTS.md').read_text(); road=Path('.planning/ROADMAP.md').read_text(); audit=Path('.planning/v1.0-MILESTONE-AUDIT.md').read_text()\nfor rid in ['JOB-01','JOB-02','JOB-03']:\n    assert f'- [x] **{rid}**' in req\nassert '**Plans:** 4 plans' in road\nassert 'status: passed' in audit\nPY` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all Phase 7 requirements. No Wave 0 test scaffolding is required.

---

## Manual-Only Verifications

All Phase 7 behaviors have automated or metadata verification. No manual-only verification is required.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-28
