---
phase: 05-anki-safe-export-contract
plan: 04
subsystem: cli
tags: [cli, runtime, anki, export, sqlite]
requires:
  - phase: 05-03
    provides: genanki package export service and stable note model
provides:
  - shipped `multilang export` command for apkg csv and tsv artifacts
  - runtime export orchestration from frozen snapshots or on-demand assembly
  - integration coverage for artifact creation and loud prerequisite failures
affects: [phase-05-plan-05, export, anki, runtime]
tech-stack:
  added: []
  patterns: [runtime export orchestration on existing service object, cli prints artifact path and card count, export artifacts persisted per job and format]
key-files:
  created:
    - tests/cli/test_export_command.py
    - tests/integration/test_export_job_flow.py
  modified:
    - src/multilang/settings.py
    - src/multilang/runtime.py
    - src/multilang/cli.py
key-decisions:
  - "Expose export as a dedicated shipped CLI command instead of overloading `multilang generate`."
  - "Reuse frozen snapshots when available and assemble on demand only when export snapshots are still missing."
patterns-established:
  - "Runtime export flows persist produced artifact manifests after every successful write."
  - "CLI export failures surface as explicit non-zero messages instead of empty or partial artifacts."
requirements-completed: []
duration: 4min
completed: 2026-04-26
---

# Phase 5 Plan 04: Expose the export workflow on the shipped CLI/runtime path Summary

**`multilang export` now writes `.apkg`, CSV, and TSV artifacts from persisted job data, with deterministic snapshot reuse and loud failure diagnostics**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-26T20:13:24Z
- **Completed:** 2026-04-26T20:16:31Z
- **Tasks:** 1
- **Files modified:** 5

## Accomplishments
- Added a shipped `multilang export` command with `--job-id`, `--format`, `--output-dir`, and optional `--deck-name`.
- Added runtime export orchestration that reuses frozen snapshots or assembles them on demand, then writes `.apkg`, CSV, or TSV artifacts.
- Added CLI and integration coverage that proves success paths and explicit failure when required export media is missing.

## Task Commits

1. **Task 1: Wire `multilang export` onto the shipped runtime path** - `f7b2c7e` (test), `892949c` (feat)

**Plan metadata:** pending

## Files Created/Modified
- `src/multilang/settings.py` - adds the default export output directory setting
- `src/multilang/runtime.py` - adds runtime export orchestration and artifact manifest persistence
- `src/multilang/cli.py` - adds the shipped `export` command and explicit diagnostic handling
- `tests/cli/test_export_command.py` - covers CLI success and failure behavior
- `tests/integration/test_export_job_flow.py` - covers end-to-end export artifacts from real SQLite job data

## Decisions Made
- Kept export on the same runtime service object as generate/review so the shipped CLI can reuse existing repository and settings wiring.
- Used `<job-id>.<format>` artifact names in the requested output directory so repeated exports remain auditable and predictable.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Real Azure Speech credentials are not configured in this shell (`MULTILANG_AZURE_SPEECH_KEY` / `MULTILANG_AZURE_SPEECH_REGION` absent), so I could not auto-generate a fresh human-review `.apkg` with production-style playable audio for the final Anki desktop checkpoint.

## User Setup Required

None for this plan's code path. Final human verification still needs a review artifact generated after Azure credentials are available.

## Next Phase Readiness
- Final automated pre-check is green: `uv run pytest tests/services/test_export_anki_package.py tests/cli/test_export_command.py tests/integration/test_export_job_flow.py -q`
- Export command template for the final Anki verification step:
  - `MULTILANG_DATABASE_URL=<db-url> MULTILANG_LEXICON_DATA_DIR=<lexicon-dir> MULTILANG_AUDIO_STORAGE_DIR=<audio-dir> uv run python -m multilang.cli export --job-id <job-id> --format apkg --output-dir .multilang/exports`
- The remaining blocker is generating a human-reviewable `.apkg` with real playable audio in an environment that has Azure Speech credentials.

## Self-Check: PASSED
- Found `.planning/phases/05-anki-safe-export-contract/05-04-SUMMARY.md`
- Verified task commits `f7b2c7e` and `892949c`

---
*Phase: 05-anki-safe-export-contract*
*Completed: 2026-04-26*
