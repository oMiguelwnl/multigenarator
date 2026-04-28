---
phase: 05-anki-safe-export-contract
reviewed: 2026-04-28T12:50:44Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - src/multilang/runtime.py
  - src/multilang/domain/exporting.py
  - tests/integration/test_export_job_flow.py
  - tests/domain/test_exporting.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 05: Code Review Report

**Reviewed:** 2026-04-28T12:50:44Z  
**Depth:** standard  
**Files Reviewed:** 4  
**Status:** clean

## Summary

Re-reviewed the Phase 05 warning fixes for the two prior findings only:

1. CSV/TSV exports could succeed with stale or missing media references.
2. `ExportCardRow` could accept a visible `SortIndex` that differed from `identity.sort_index`.

Both findings are now addressed. `RuntimeService.export_job()` builds and validates the media index before dispatching to either `.apkg` or CSV/TSV export paths, so stale or missing media fails before tabular artifacts are written. `ExportCardRow.populate_stable_fields()` now rejects explicit `SortIndex` values that do not match `identity.sort_index`, preserving consistency between the exported field and deterministic note identity.

Targeted tests verify both fixes:

- `tests/integration/test_export_job_flow.py::test_export_command_runtime_path_fails_loudly_when_audio_is_missing` is parametrized across `apkg`, `csv`, and `tsv`.
- `tests/domain/test_exporting.py::test_visible_sort_index_must_match_stable_identity` confirms mismatched visible sort indexes are rejected.

Validation run: `pytest tests/domain/test_exporting.py tests/integration/test_export_job_flow.py` — **9 passed in 12.03s**.

All reviewed files meet quality standards for the prior warning scope. No issues found.

---

_Reviewed: 2026-04-28T12:50:44Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
