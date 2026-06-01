---
phase: 22-latin-mode-contracts-and-isolation
plan: 1
subsystem: domain
tags: [python, pydantic, latin, source-profiles]
requires: []
provides:
  - Classical Latin MVP domain contracts
  - Isolated latin-mvp source profile
  - Modern-language boundary tests proving la is not in SupportedLanguage
affects: [latin-mvp, generation-contracts, source-profiles]
tech-stack:
  added: []
  patterns: [isolated Pydantic domain request, source-profile registry extension]
key-files:
  created: [src/multilang/domain/latin.py, tests/domain/test_latin_contracts.py]
  modified: [src/multilang/domain/source_profiles.py, tests/domain/test_source_profiles.py, tests/domain/test_jobs.py]
key-decisions:
  - "Kept Classical Latin out of SupportedLanguage and represented it through LatinGenerationRequest."
  - "Registered latin-mvp as a first-class source profile without changing existing profile values."
patterns-established:
  - "Latin MVP mode uses its own Pydantic request and metadata contracts."
requirements-completed: [MODE-01, MODE-02, MODE-03]
duration: 7min
completed: 2026-06-01
---

# Phase 22 Plan 1: Latin Domain Contracts and Source Profile Isolation Summary

**Classical Latin `la` MVP contracts with fixed 50-card scope and an isolated `latin-mvp` source profile**

## Performance

- **Duration:** 7 min overall phase execution window
- **Started:** 2026-06-01T18:05:36Z
- **Completed:** 2026-06-01T18:12:23Z
- **Tasks:** 3/3
- **Files modified:** 5

## Accomplishments
- Added `LatinDeckMetadata` and `LatinGenerationRequest` with `language_code=la`, Classical variant, source pack version, and exactly 50 cards.
- Registered `latin-mvp` in source profiles while preserving frequency, word-list, and kindle-highlight profile contracts.
- Added tests proving `SupportedLanguage` still excludes `la` and that Latin contracts stay separate from modern generation requests.

## Task Commits
1. **Task 1: Add Classical Latin domain metadata contracts** - `8fb2f61` (test), `6d7b46b` (feat)
2. **Task 2: Register isolated Latin source profile without changing shipped profiles** - `3ec42af` (test), `3f2bda2` (feat)
3. **Task 3: Preserve modern-language request contracts while exporting Latin contracts** - `8a60929` (test)

## Files Created/Modified
- `src/multilang/domain/latin.py` - Classical Latin constants, enum, metadata, and request models.
- `src/multilang/domain/source_profiles.py` - Adds the isolated `latin-mvp` source profile.
- `tests/domain/test_latin_contracts.py` - Contract tests for Latin metadata/request validation.
- `tests/domain/test_source_profiles.py` - Source-profile isolation and redacted error evidence.
- `tests/domain/test_jobs.py` - Modern-language boundary tests.

## Verification
- `python -m pytest tests/domain/test_latin_contracts.py -q` — passed, 8 tests.
- `python -m pytest tests/domain/test_source_profiles.py -q` — passed, 6 tests.
- `python -m pytest tests/domain/test_latin_contracts.py tests/domain/test_source_profiles.py tests/domain/test_jobs.py -q` — passed, 26 tests.

## Decisions Made
- Kept Latin separate from `SupportedLanguage` to avoid mutating modern frequency-language behavior.
- Used a dedicated `latin-mvp` profile key rather than reusing `frequency`.

## Deviations from Plan
None - plan executed exactly as written.

## Known Stubs
None.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Plan 22-02 can consume `LatinGenerationRequest` and `latin-mvp` to expose an isolated CLI start path.

## Self-Check: PASSED
- Created files exist: `src/multilang/domain/latin.py`, `tests/domain/test_latin_contracts.py`.
- Commits found: `8fb2f61`, `6d7b46b`, `3ec42af`, `3f2bda2`, `8a60929`.

---
*Phase: 22-latin-mode-contracts-and-isolation*
*Completed: 2026-06-01*
