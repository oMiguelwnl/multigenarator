---
phase: 09-source-profiles-privacy-regression-boundary
plan: 04
subsystem: testing
tags: [regression, e2e, privacy-evidence]
requires:
  - phase: 09-source-profiles-privacy-regression-boundary
    provides: source profiles, export isolation, redaction helpers
provides:
  - v1.2 existing-mode regression boundary suite
  - phase evidence command artifact
affects: [phase-10-kindle-ingestion, phase-11-highlight-cli, phase-13-highlight-template]
tech-stack:
  added: []
  patterns: [focused milestone evidence suite, collect-only drift check]
key-files:
  created: [tests/integration/test_v12_existing_mode_regression_boundary.py, .planning/phases/09-source-profiles-privacy-regression-boundary/09-REGRESSION-EVIDENCE.md]
  modified: [src/multilang/services/lexical_grounding.py, tests/integration/test_frequency_e2e_export_flow.py, tests/integration/test_custom_word_list_e2e_export_flow.py]
key-decisions:
  - "Phase 09 evidence includes existing frequency/custom E2E flows plus focused source/export/privacy tests."
  - "CLI remains intentionally gated to frequency and word-list until Phase 11 wires highlights."
patterns-established:
  - "Future highlight phases should run 09-REGRESSION-EVIDENCE.md commands before modifying existing modes."
requirements-completed: [MODE-02, SEC-01, SEC-02]
duration: 15min
completed: 2026-05-04
---

# Phase 09 Plan 04: Regression Evidence Summary

**Runnable v1.2 regression boundary proving existing modes, export/audio paths, privacy utilities, and CLI highlight gating**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-04T11:54:52Z
- **Completed:** 2026-05-04T12:09:23Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `test_v12_existing_mode_regression_boundary.py` to tie Phase 09 source/export/privacy boundaries to existing-mode behavior.
- Recorded exact evidence commands in `09-REGRESSION-EVIDENCE.md`.
- Verified focused Phase 09 evidence suite and broad pytest collection.

## Task Commits

1. **TDD RED: v1.2 regression tests** - `cf0e367` (test)
2. **Task 1 GREEN: existing-mode regression fixes** - `6c168fa` (fix)
3. **Task 2: evidence artifact** - `2d0c4c5` (docs)

## Files Created/Modified

- `tests/integration/test_v12_existing_mode_regression_boundary.py` - Focused Phase 09 regression boundary.
- `.planning/phases/09-source-profiles-privacy-regression-boundary/09-REGRESSION-EVIDENCE.md` - Evidence command list.
- `src/multilang/services/lexical_grounding.py` - Preserves spoken-form fallback for existing exports without a pronunciation provider.
- `tests/integration/test_frequency_e2e_export_flow.py` - Existing E2E fixture aligned with definition template requirements.
- `tests/integration/test_custom_word_list_e2e_export_flow.py` - Existing E2E fixture aligned with definition template requirements.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Existing E2E exports lacked spoken-form/definition-template prerequisites**
- **Found during:** Task 1 regression suite execution
- **Issue:** Existing frequency/custom E2E exports failed before Phase 09 could prove the boundary because fixtures lacked current definition template metadata and lexical grounding did not preserve a spoken-form fallback when no pronunciation provider was configured.
- **Fix:** Preserved learner display form as `spoken_form` when authoritative IPA exists and no provider overrides it; added synthetic part-of-speech metadata to existing E2E fixtures.
- **Files modified:** `src/multilang/services/lexical_grounding.py`, `tests/integration/test_frequency_e2e_export_flow.py`, `tests/integration/test_custom_word_list_e2e_export_flow.py`
- **Verification:** `uv run pytest tests/integration/test_v12_existing_mode_regression_boundary.py -q` and full Phase 09 evidence suite passed.
- **Committed in:** `6c168fa`

**Total deviations:** 1 auto-fixed (Rule 1 bug).  
**Impact on plan:** Required to make SEC-02 regression evidence meaningful; no highlight ingestion or CLI usability was added.

## Verification

- `uv run pytest tests/domain/test_source_profiles.py tests/domain/test_jobs.py tests/domain/test_exporting.py tests/services/test_export_anki_package.py tests/security/test_redaction.py tests/integration/test_v12_existing_mode_regression_boundary.py tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_frequency_e2e_export_flow.py -q` — 46 passed.
- `uv run pytest --collect-only -q` — 247 tests collected.

## Known Stubs

None.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: test-fixture-boundary | tests/integration/test_v12_existing_mode_regression_boundary.py | New integration fixture boundary intentionally uses only synthetic words and no real highlights/WebDAV data. |

## Self-Check: PASSED

Files and commits verified during execution.
