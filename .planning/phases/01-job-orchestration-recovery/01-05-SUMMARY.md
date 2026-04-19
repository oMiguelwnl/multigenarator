---
phase: 01-job-orchestration-recovery
plan: 05
subsystem: cli-runtime
tags: [runtime-bootstrap, persistence, cli, summary-contract, testing]
requires:
  - phase: 01-job-orchestration-recovery/04
    provides: progress rendering, lifecycle summaries, and repository-backed orchestration internals
provides:
  - Lazy runtime bootstrap for the shipped CLI path using settings-backed SQLAlchemy construction
  - Shared execution-report contract without CLI-to-summary circular imports
  - Default-app coverage proving repository-backed execution on the shipped path
affects: [cli, runtime, services, persistence, testing]
tech-stack:
  added: []
  patterns: [lazy runtime dependency resolution, shared execution-report contract, shipped-path bootstrap testing]
key-files:
  created: [src/multilang/runtime.py, src/multilang/services/execution_report.py, tests/cli/test_runtime_bootstrap.py, .planning/phases/01-job-orchestration-recovery/01-05-SUMMARY.md]
  modified: [src/multilang/cli.py, src/multilang/services/job_summary.py, tests/test_job_summary.py, .planning/STATE.md, .planning/ROADMAP.md, .planning/REQUIREMENTS.md]
key-decisions:
  - "Build the default CLI service lazily at command execution so environment overrides are honored by the shipped app and tests."
  - "Move JobExecutionReport into a shared services module so CLI runtime code and lifecycle summaries can share one contract without import cycles."
patterns-established:
  - "Runtime bootstrap pattern: construct engine, session, repository, and service from Settings only when the command actually runs."
  - "Contract-sharing pattern: shared execution metadata lives under services, not inside the CLI entrypoint."
requirements-completed: [JOB-01, JOB-02, JOB-03]
duration: 12 min
completed: 2026-04-19
---

# Phase 1 Plan 5: Runtime Bootstrap Gap Closure Summary

**Lazy repository-backed CLI bootstrap with a shared execution-report contract and shipped-path runtime coverage.**

## Performance

- **Duration:** 12 min
- **Completed:** 2026-04-19T14:56:57Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Moved `JobExecutionReport` into a shared services module so runtime summary code no longer imports from `cli.py`.
- Added `build_runtime_service()` to build engine, session, repository, and `GenerateJobService` from `Settings.database_url`.
- Rewired the default `create_app()` path to resolve the real persistence-backed service lazily at command execution time.
- Added shipped-path tests proving both `create_app()` and the module-level `app` honor runtime database overrides.

## Task Commits

1. **Task 1: Extract a shared execution-report contract and runtime bootstrap — RED** - `0ee8447` (test)
2. **Task 1: Extract a shared execution-report contract and runtime bootstrap — GREEN** - `ba75942` (feat)
3. **Task 2: Add default-app bootstrap coverage for repository-backed execution** - `f98bb84` (test)

## Files Created/Modified
- `src/multilang/runtime.py` - Adds shipped-path runtime construction from settings-backed database configuration.
- `src/multilang/services/execution_report.py` - Hosts the shared `JobExecutionReport` dataclass.
- `src/multilang/cli.py` - Lazily resolves the default runtime service instead of using a no-op executor.
- `src/multilang/services/job_summary.py` - Imports the shared execution-report contract from services.
- `tests/test_job_summary.py` - Verifies the shared report contract and runtime bootstrap database binding.
- `tests/cli/test_runtime_bootstrap.py` - Verifies the shipped bootstrap path persists jobs through a real runtime service.

## Decisions Made
- The shipped CLI should resolve runtime dependencies only when a command executes, not during import.
- Shared execution metadata belongs in `multilang.services`, not in the CLI module.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Replaced missing `gsd-sdk` state tooling with manual metadata edits**
- **Found during:** Summary/state finalization
- **Issue:** `gsd-sdk` commands required by the workflow are unavailable in this environment.
- **Fix:** Updated `.planning/STATE.md`, `.planning/ROADMAP.md`, and `.planning/REQUIREMENTS.md` manually after verification.
- **Files modified:** `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`
- **Commit:** pending final docs commit

## Verification Results
- `uv run pytest tests/test_job_summary.py tests/cli/test_generate_command.py -q` → `9 passed`
- `uv run pytest tests/cli/test_runtime_bootstrap.py tests/cli/test_generate_command.py tests/test_job_summary.py -q` → `11 passed`

## Self-Check: PASSED
- Found `.planning/phases/01-job-orchestration-recovery/01-05-SUMMARY.md`, `src/multilang/runtime.py`, `src/multilang/services/execution_report.py`, and `tests/cli/test_runtime_bootstrap.py` on disk.
- Found task commits `0ee8447`, `ba75942`, and `f98bb84` in git history.

---
*Phase: 01-job-orchestration-recovery*
*Completed: 2026-04-19*
