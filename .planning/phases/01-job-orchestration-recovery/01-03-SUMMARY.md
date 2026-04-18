---
phase: 01-job-orchestration-recovery
plan: 03
subsystem: cli
tags: [typer, cli, orchestration, rerun, resume, fingerprints]
requires:
  - phase: 01-job-orchestration-recovery/02
    provides: persisted job/item state, duplicate-safe repository reads, and resume diagnostics
provides:
  - Single-command `multilang generate` CLI validation for start, resume, and overwrite flows
  - Deterministic input fingerprints and run keys for repository-backed reruns
  - Service-layer orchestration that resumes safely and skips completed items by default
affects: [services, repositories, testing, operator-workflows]
tech-stack:
  added: []
  patterns: [Typer single-command CLI, deterministic run-key fingerprinting, repository-backed orchestration with TDD]
key-files:
  created: [src/multilang/cli.py, src/multilang/services/__init__.py, src/multilang/services/input_fingerprint.py, src/multilang/services/generate_job.py, tests/cli/test_generate_command.py, tests/services/test_generate_job.py]
  modified: [.planning/phases/01-job-orchestration-recovery/01-03-SUMMARY.md, .planning/STATE.md, .planning/ROADMAP.md]
key-decisions:
  - "Use one Typer `generate` command with source-specific validation and explicit overwrite confirmation instead of multiple subcommands."
  - "Derive run keys from language, source type, and normalized requested items so duplicate-skip behavior stays deterministic across reruns."
  - "Abort resumes on repository diagnostics and let the service return the diagnostic instead of guessing how to repair persisted state."
patterns-established:
  - "CLI pattern: validate operator flags before any overwrite or orchestration path runs."
  - "Service pattern: compute pending work by subtracting repository completed-item keys from normalized requested items."
requirements-completed: [DECK-01, JOB-01, JOB-03]
duration: 7 min
completed: 2026-04-18
---

# Phase 1 Plan 3: Job Orchestration & Recovery Summary

**Single-command Typer job orchestration with deterministic run keys, safe resume diagnostics, and duplicate-skip reruns.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-18T21:43:20Z
- **Completed:** 2026-04-18T21:50:09Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Added the first operator-facing `multilang generate` command with strict language/source validation.
- Implemented deterministic input fingerprinting and run-key generation for fresh starts and reruns.
- Added repository-backed orchestration that reuses completed work on resume and blocks corrupted persisted state.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build the single-command CLI surface** - `871456d` (feat)
2. **Task 2: Orchestrate start, resume, and duplicate-safe rerun behavior — RED** - `0b7568a` (test)
3. **Task 2: Orchestrate start, resume, and duplicate-safe rerun behavior — GREEN** - `0cf6a8c` (feat)
4. **Task 2 support: Load deterministic CLI item keys** - `650f4a9` (fix)

**Plan metadata:** pending

## Files Created/Modified
- `src/multilang/cli.py` - Defines the `generate` command, overwrite confirmation, and service-facing item key loading.
- `src/multilang/services/input_fingerprint.py` - Normalizes requested items and builds deterministic fingerprints plus run keys.
- `src/multilang/services/generate_job.py` - Prepares safe start/resume/rerun decisions from repository state.
- `tests/cli/test_generate_command.py` - Verifies unsupported-language rejection, source-specific validation, and overwrite confirmation.
- `tests/services/test_generate_job.py` - Verifies deterministic run keys, safe resume diagnostics, and duplicate-skip reruns.
- `.planning/STATE.md` - Advances plan tracking to the next Phase 1 plan.
- `.planning/ROADMAP.md` - Marks Plan 01-03 complete and Phase 1 as 3/4 done.

## Decisions Made
- Used a single `generate` command with flag validation to preserve the CLI-first, one-command operator shape from the phase context.
- Kept duplicate-skip and unsafe-resume rules in the service layer so the CLI does not rely on operator discipline.
- Used normalized item keys for run-key derivation so rerun behavior is stable even when word-list ordering or casing changes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Loaded deterministic CLI item keys before invoking orchestration**
- **Found during:** Task 2 (Orchestrate start, resume, and duplicate-safe rerun behavior)
- **Issue:** The initial CLI-to-service wiring passed no requested items into the orchestration service, which would have prevented the CLI from building a real work queue.
- **Fix:** Added deterministic frequency slot keys for level-based runs and file-backed word-list loading so the CLI passes normalized work items into `GenerateJobService`.
- **Files modified:** `src/multilang/cli.py`
- **Verification:** `uv run pytest tests/cli/test_generate_command.py tests/services/test_generate_job.py -q`
- **Committed in:** `650f4a9`

**2. [Rule 3 - Blocking] Updated planning-state files manually because `gsd-sdk` is unavailable**
- **Found during:** Summary/state finalization
- **Issue:** The required `gsd-sdk query ...` workflow commands cannot run in this environment because `gsd-sdk` is not installed on `PATH`.
- **Fix:** Updated `.planning/STATE.md` and `.planning/ROADMAP.md` manually to preserve execution tracking consistency.
- **Files modified:** `.planning/STATE.md`, `.planning/ROADMAP.md`
- **Verification:** Read the updated files after editing to confirm plan counts, stop position, and next resume file are correct.
- **Committed in:** pending (metadata commit)

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 blocking)
**Impact on plan:** Both auto-fixes were required for a usable CLI orchestration flow and consistent planning metadata. No scope creep beyond plan intent.

## Issues Encountered
- Typer's single-command optimization initially treated `generate` as the root command, so the CLI needed an explicit callback to preserve the `multilang generate` command shape.
- The environment does not include `gsd-sdk`, so plan-tracking updates had to be applied manually.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 1 now has the CLI and service-layer entrypoint that the progress and retry plan can build on.
- The next plan can attach stage-level progress rendering and retry/failure behavior to `GenerateJobService` results without redefining resume or rerun semantics.

## Self-Check: PASSED
- Found `.planning/phases/01-job-orchestration-recovery/01-03-SUMMARY.md`, `src/multilang/cli.py`, `src/multilang/services/input_fingerprint.py`, `src/multilang/services/generate_job.py`, `tests/cli/test_generate_command.py`, and `tests/services/test_generate_job.py` on disk.
- Found task commits `871456d`, `0b7568a`, `0cf6a8c`, and `650f4a9` in git history.

---
*Phase: 01-job-orchestration-recovery*
*Completed: 2026-04-18*
