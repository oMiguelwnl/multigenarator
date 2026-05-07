---
phase: 14
slug: webdav-highlight-fetch-adapter
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-07
---

# Phase 14 — Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/test_settings.py tests/domain/test_webdav.py tests/services/test_webdav_highlight_fetch.py tests/cli/test_webdav_highlight_commands.py -q` |
| **Full suite command** | `uv run pytest tests/test_settings.py tests/domain/test_webdav.py tests/services/test_webdav_highlight_fetch.py tests/cli/test_webdav_highlight_commands.py tests/cli/test_generate_webdav_highlights_command.py tests/integration/test_webdav_highlight_fetch_flow.py tests/security/test_redaction.py -q` |
| **Estimated runtime** | < 60 seconds focused |

## Sampling Rate

- **After every task commit:** Run the task-specific `<automated>` command in the relevant PLAN.md.
- **After every plan wave:** Run the full suite command above.
- **Before `/gsd-verify-work`:** Focused phase suite and existing highlight suites must be green.
- **Max feedback latency:** < 60 seconds for focused WebDAV suites.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | INGEST-01 | T-14-01 | Env-only secret settings, no CLI secret flags | unit | `uv run pytest tests/test_settings.py tests/domain/test_webdav.py -q` | ✅ | ⬜ pending |
| 14-01-02 | 01 | 1 | INGEST-01 | T-14-02 | Redacted failure contract carries safe codes | unit | `uv run pytest tests/domain/test_webdav.py -q` | ✅ | ⬜ pending |
| 14-02-01 | 02 | 2 | INGEST-02 | T-14-03 | Listing filters/sanitizes candidates | unit | `uv run pytest tests/services/test_webdav_highlight_fetch.py -q` | ✅ | ⬜ pending |
| 14-02-02 | 02 | 2 | INGEST-02 | T-14-04 | Fetch writes content-hash cache only after validation | unit | `uv run pytest tests/services/test_webdav_highlight_fetch.py -q` | ✅ | ⬜ pending |
| 14-03-01 | 03 | 3 | INGEST-01/02 | T-14-05 | CLI list/fetch outputs redacted key=value summaries | cli | `uv run pytest tests/cli/test_webdav_highlight_commands.py -q` | ✅ | ⬜ pending |
| 14-03-02 | 03 | 3 | INGEST-02 | T-14-06 | CLI fetch reuses local preview parser counts | cli | `uv run pytest tests/cli/test_webdav_highlight_commands.py tests/services/test_highlight_import_preview.py -q` | ✅ | ⬜ pending |
| 14-04-01 | 04 | 4 | INGEST-02 | T-14-07 | Generate resolves WebDAV path to local cache without secrets | cli/integration | `uv run pytest tests/cli/test_generate_webdav_highlights_command.py tests/integration/test_webdav_highlight_fetch_flow.py -q` | ✅ | ⬜ pending |
| 14-04-02 | 04 | 4 | INGEST-01/02 | T-14-08 | Evidence contains hashes/counts only, no private data | integration | `uv run pytest tests/integration/test_webdav_highlight_fetch_flow.py tests/security/test_redaction.py -q` | ✅ | ⬜ pending |

## Wave 0 Requirements

Existing pytest infrastructure covers all phase requirements. New tests are created inside the phase plans before production implementation.

## Manual-Only Verifications

All Phase 14 behaviors have automated fake-transport verification. Live WebDAV account testing is optional and must not use real credentials in committed artifacts.

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 is not required beyond test files planned in task order.
- [x] No watch-mode flags.
- [x] Feedback latency < 60 seconds for focused suites.

**Approval:** pending execution
