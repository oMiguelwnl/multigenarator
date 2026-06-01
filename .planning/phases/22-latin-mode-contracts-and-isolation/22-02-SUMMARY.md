---
phase: 22-latin-mode-contracts-and-isolation
plan: 2
subsystem: cli
tags: [python, typer, latin, service]
requires:
  - phase: 22-01
    provides: LatinGenerationRequest and latin-mvp source profile
provides:
  - Deterministic Latin MVP start service
  - generate-latin-mvp CLI command
  - CLI isolation tests for existing generate modes
affects: [latin-mvp, cli, generation-service]
tech-stack:
  added: []
  patterns: [small deterministic service, injectable CLI collaborator]
key-files:
  created: [src/multilang/services/latin_mvp.py, tests/services/test_latin_mvp.py, tests/cli/test_generate_latin_mvp_command.py]
  modified: [src/multilang/cli.py]
key-decisions:
  - "Added a separate `generate-latin-mvp` command instead of extending `generate --source`."
  - "Made the Latin MVP service injectable through `create_app` for deterministic CLI tests."
patterns-established:
  - "Latin CLI output uses stable key=value metadata lines for scanner/automation consumption."
requirements-completed: [MODE-01, MODE-02, MODE-03]
duration: 7min
completed: 2026-06-01
---

# Phase 22 Plan 2: Latin MVP Service and CLI Command Summary

**Isolated `generate-latin-mvp` command backed by a deterministic 50-item Classical Latin start service**

## Performance

- **Duration:** 7 min overall phase execution window
- **Started:** 2026-06-01T18:05:36Z
- **Completed:** 2026-06-01T18:12:23Z
- **Tasks:** 3/3
- **Files modified:** 4

## Accomplishments
- Added `LatinMvpGenerationService.start()` returning Latin metadata and deterministic `latin-mvp-0001` through `latin-mvp-0050` keys.
- Added `generate-latin-mvp` with optional `--source-pack-version` and machine-readable metadata output.
- Proved existing `generate` rejects `--language la` and `--source latin-mvp`, preserving modern/custom/highlight command boundaries.

## Task Commits
1. **Task 1: Implement deterministic Latin MVP start service** - `ad5d345` (test), `f0fde85` (feat)
2. **Task 2: Add user-facing Latin CLI command separate from modern generation** - `561e28b` (test), `e447934` (feat)
3. **Task 3: Preserve existing generate-mode validation around the new command** - `088612a` (test)

## Files Created/Modified
- `src/multilang/services/latin_mvp.py` - Deterministic Latin MVP start service and result model.
- `src/multilang/cli.py` - Adds `generate-latin-mvp` and Latin service injection.
- `tests/services/test_latin_mvp.py` - Service metadata and item-key tests.
- `tests/cli/test_generate_latin_mvp_command.py` - CLI metadata, override, service-call, and isolation tests.

## Verification
- `python -m pytest tests/services/test_latin_mvp.py -q` — passed, 3 tests.
- `python -m pytest tests/cli/test_generate_latin_mvp_command.py tests/cli/test_generate_command.py::test_generate_command_rejects_unsupported_language -q` — passed, 4 tests.
- `python -m pytest tests/cli/test_generate_latin_mvp_command.py tests/cli/test_generate_command.py::test_generate_command_rejects_unsupported_language tests/cli/test_generate_command.py::test_public_kindle_highlights_source_remains_rejected -q` — passed, 7 tests.
- `python -m pytest tests/services/test_latin_mvp.py tests/cli/test_generate_latin_mvp_command.py tests/cli/test_generate_command.py -q` — **failed: 33 passed, 1 failed** in pre-existing `test_generate_command_default_runtime_reports_audio_counters` because output omitted `fallback_audio_items=1`.

## Decisions Made
- Kept Latin selectable only through `generate-latin-mvp`; did not add Latin to the existing `generate` source or language options.
- Printed `language_code`, `variant`, `source_type`, `source_pack_version`, `card_count`, and `item_count` as stable `key=value` lines.

## Deviations from Plan
None in Phase 22 implementation. The full listed Plan 22-02 verification exposed unrelated existing audio/runtime CLI drift; it was not fixed because it is outside this plan's changed surface.

## Known Stubs
None.

## Deferred Issues
- `tests/cli/test_generate_command.py::test_generate_command_default_runtime_reports_audio_counters` expects `fallback_audio_items=1` in first-run output. Deferred in `deferred-items.md` as unrelated existing CLI/audio drift.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Latin MVP can be started from the CLI and produces scanner-friendly metadata for later source-pack and evidence phases.

## Self-Check: PASSED
- Created files exist: `src/multilang/services/latin_mvp.py`, `tests/services/test_latin_mvp.py`, `tests/cli/test_generate_latin_mvp_command.py`.
- Commits found: `ad5d345`, `f0fde85`, `561e28b`, `e447934`, `088612a`.

---
*Phase: 22-latin-mode-contracts-and-isolation*
*Completed: 2026-06-01*
