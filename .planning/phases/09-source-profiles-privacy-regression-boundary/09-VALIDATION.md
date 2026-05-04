---
phase: 09
slug: source-profiles-privacy-regression-boundary
status: verified
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-04T13:12:52Z
updated: 2026-05-04T13:12:52Z
---

# Phase 09 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tests/domain/test_source_profiles.py tests/domain/test_jobs.py tests/domain/test_exporting.py tests/services/test_export_anki_package.py tests/security/test_redaction.py -q` |
| **Full suite command** | `uv run pytest tests/domain/test_source_profiles.py tests/domain/test_jobs.py tests/domain/test_exporting.py tests/services/test_export_anki_package.py tests/security/test_redaction.py tests/integration/test_v12_existing_mode_regression_boundary.py tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_frequency_e2e_export_flow.py -q` |
| **Collection drift command** | `uv run pytest --collect-only -q` |
| **Estimated runtime** | ~13 seconds for Phase 09 suite; ~6 seconds for collection |

## Sampling Rate

- **After every task commit:** Run the task-specific `<automated>` command from the PLAN.
- **After every plan wave:** Run the Phase 09 full suite command.
- **Before `/gsd-verify-work`:** Phase 09 full suite and collection drift command must be green.
- **Max feedback latency:** ~20 seconds for the required Phase 09 validation commands.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | MODE-02, SEC-02 | T-09-01, T-09-02, T-09-03 | Source profiles are explicit; unsupported lookup diagnostics are privacy-safe after 09-05. | unit | `uv run pytest tests/domain/test_source_profiles.py -q` | yes | green |
| 09-01-02 | 01 | 1 | MODE-02, SEC-02 | T-09-01, T-09-03 | `GenerationRequest` accepts existing modes and internal `kindle-highlights` while rejecting unsupported values. | unit | `uv run pytest tests/domain/test_jobs.py tests/domain/test_source_profiles.py -q` | yes | green |
| 09-02-01 | 02 | 2 | MODE-02, SEC-02 | T-09-05, T-09-06 | Export field resolution preserves frequency/manual translation fields and omits Translation for highlight rows. | unit | `uv run pytest tests/domain/test_exporting.py -q` | yes | green |
| 09-02-02 | 02 | 2 | MODE-02, SEC-02 | T-09-04, T-09-06 | APKG/tabular note selection uses exact source type and rejects mixed-source exports. | unit | `uv run pytest tests/services/test_export_anki_package.py tests/domain/test_exporting.py -q` | yes | green |
| 09-03-01 | 03 | 1 | SEC-01 | T-09-07, T-09-09 | Redaction helpers remove credentials, WebDAV URLs, raw paths, metadata, private terms, mappings, and exception text. | security unit | `uv run pytest tests/security/test_redaction.py -q` | yes | green |
| 09-03-02 | 03 | 1 | SEC-01 | T-09-08 | `.gitignore` excludes local secrets and raw highlight/WebDAV artifacts before ingestion exists. | security unit | `uv run pytest tests/security/test_redaction.py -q` | yes | green |
| 09-04-01 | 04 | 3 | MODE-02, SEC-01, SEC-02 | T-09-10, T-09-11, T-09-12 | Existing frequency/custom flows still generate accepted text, fake Azure audio, APKG/CSV/TSV exports, and CLI highlight gating remains closed. | integration | `uv run pytest tests/integration/test_v12_existing_mode_regression_boundary.py -q` | yes | green |
| 09-04-02 | 04 | 3 | MODE-02, SEC-01, SEC-02 | T-09-10, T-09-11, T-09-12 | Regression evidence commands are documented and runnable before highlight work proceeds. | integration/docs | `uv run pytest tests/domain/test_source_profiles.py tests/domain/test_jobs.py tests/domain/test_exporting.py tests/services/test_export_anki_package.py tests/security/test_redaction.py tests/integration/test_v12_existing_mode_regression_boundary.py tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_frequency_e2e_export_flow.py -q` | yes | green |
| 09-05-01 | 05 | 5 | SEC-01 | T-09-02 | Unsupported source-profile errors omit rejected private/path-bearing input and list only safe supported source keys. | unit | `uv run pytest tests/domain/test_source_profiles.py -q` | yes | green |
| 09-05-02 | 05 | 5 | SEC-01 | T-09-02 | Security record verifies `threats_open: 0` after source-profile diagnostic remediation. | security/docs | `uv run pytest tests/domain/test_source_profiles.py tests/domain/test_jobs.py tests/security/test_redaction.py -q` | yes | green |

Status: pending, green, red, or flaky.

## Requirement Coverage

| Requirement | Coverage Status | Automated Evidence |
|-------------|-----------------|--------------------|
| MODE-02 | covered | `tests/domain/test_source_profiles.py`, `tests/domain/test_jobs.py`, `tests/domain/test_exporting.py`, `tests/services/test_export_anki_package.py`, `tests/integration/test_v12_existing_mode_regression_boundary.py`, existing frequency/custom E2E tests |
| SEC-01 | covered | `tests/security/test_redaction.py`, `tests/domain/test_source_profiles.py`, `09-SECURITY.md`, Phase 09 full validation suite |
| SEC-02 | covered | Source/export unit tests plus existing-mode E2E regression tests and collection drift command |

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

## Manual-Only Verifications

All phase behaviors have automated verification.

## Validation Audit 2026-05-04

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Phase tests passed | 46 |
| Tests collected | 247 |

Commands run:

- `uv run pytest tests/domain/test_source_profiles.py tests/domain/test_jobs.py tests/domain/test_exporting.py tests/services/test_export_anki_package.py tests/security/test_redaction.py tests/integration/test_v12_existing_mode_regression_boundary.py tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_frequency_e2e_export_flow.py -q` - 46 passed.
- `uv run pytest --collect-only -q` - 247 tests collected.

Notes:

- `gsd-sdk` was unavailable on PATH; workflow init/model/config queries could not run. Nyquist validation was treated as enabled because the GSD template config has `workflow.nyquist_validation: true`.
- No implementation or test files were generated during this validation pass because all mapped requirements already had runnable green automated coverage.
- Pre-existing unrelated working-tree modifications were left untouched.

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20 seconds
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-04
