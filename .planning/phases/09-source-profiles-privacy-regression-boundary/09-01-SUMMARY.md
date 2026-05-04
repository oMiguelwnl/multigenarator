---
phase: 09-source-profiles-privacy-regression-boundary
plan: 01
subsystem: domain
tags: [source-profiles, generation-request, privacy-boundary]
requires:
  - phase: 08-card-quality-refresh
    provides: existing frequency/custom generation behavior to preserve
provides:
  - explicit SourceProfile contracts for frequency, word-list, and kindle-highlights
  - shared SourceType contract for GenerationRequest
affects: [phase-10-kindle-ingestion, phase-11-highlight-cli, phase-13-highlight-template]
tech-stack:
  added: []
  patterns: [frozen dataclass source profiles, fail-closed source lookup]
key-files:
  created: [src/multilang/domain/source_profiles.py, tests/domain/test_source_profiles.py]
  modified: [src/multilang/domain/jobs.py, tests/domain/test_jobs.py]
key-decisions:
  - "Represent kindle-highlights as an internal domain source type before making it CLI-selectable."
  - "Keep profile lookup errors limited to the unknown source value to avoid leaking sensitive context."
patterns-established:
  - "Source-specific behavior is resolved from SourceProfile instead of ad hoc string branches."
requirements-completed: [MODE-02, SEC-02]
duration: 15min
completed: 2026-05-04
---

# Phase 09 Plan 01: Source Profiles Summary

**Typed source-profile boundary for existing deck modes plus internal kindle-highlights representation**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-04T11:54:52Z
- **Completed:** 2026-05-04T12:09:23Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added frozen `SourceProfile` definitions for `frequency`, `word-list`, and `kindle-highlights`.
- Updated `GenerationRequest.source_type` to use the shared `SourceType` alias.
- Covered existing mode preservation and fail-closed unknown source lookup with domain tests.

## Task Commits

1. **TDD RED: source profile tests** - `32280a3` (test)
2. **Tasks 1-2 GREEN: source profile boundary and GenerationRequest contract** - `666416f` (feat)

## Files Created/Modified

- `src/multilang/domain/source_profiles.py` - Source profile dataclass, constants, and lookup helper.
- `src/multilang/domain/jobs.py` - GenerationRequest now uses shared source type contract.
- `tests/domain/test_source_profiles.py` - Profile and privacy-safe error tests.
- `tests/domain/test_jobs.py` - Source-type validation regression tests.

## Deviations from Plan

None - plan executed as specified.

## Verification

- `uv run pytest tests/domain/test_source_profiles.py tests/domain/test_jobs.py -q` — 14 passed.

## Known Stubs

None.

## Self-Check: PASSED

Files and commits verified during execution.
