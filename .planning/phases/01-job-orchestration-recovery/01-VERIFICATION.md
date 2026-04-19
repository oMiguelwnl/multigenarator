---
phase: 01-job-orchestration-recovery
verified: 2026-04-19T14:28:38Z
status: gaps_found
score: 3/7 must-haves verified
overrides_applied: 0
gaps:
  - truth: "User can see batch-level progress and failures while generation is running."
    status: failed
    reason: "The shipped CLI entrypoint is not wired to the orchestration service, so running `multilang generate` exits successfully with no progress output."
    artifacts:
      - path: "src/multilang/cli.py"
        issue: "`app = create_app()` uses the default no-op executor because no `GenerateJobService` is provided."
      - path: "src/multilang/progress.py"
        issue: "`ProgressRenderer` is only reachable through `build_generate_executor(service=...)`, which is used in tests but not by the shipped app."
    missing:
      - "Create runtime wiring that instantiates a repository/service and passes it to `create_app(service=...)`."
      - "Route the default `multilang generate` path through `build_generate_executor(...)` so progress lines are emitted during execution."
  - truth: "User can resume an interrupted generation run without losing cards that already completed."
    status: failed
    reason: "Resume logic exists in repository/service code, but the shipped CLI never constructs a runtime session or repository, so users cannot persist a job and later resume it from the real app."
    artifacts:
      - path: "src/multilang/cli.py"
        issue: "The default app falls back to `default_generate_executor`, which returns the request and does not create or resume jobs."
      - path: "src/multilang/services/generate_job.py"
        issue: "Resume behavior is implemented but only exercised through test-injected services."
    missing:
      - "Add runtime database/session bootstrap and repository construction in application code."
      - "Wire `--resume` on the shipped CLI to the real `GenerateJobService.resume` path backed by persistence."
  - truth: "User can rerun the same input without silent duplicate card creation."
    status: failed
    reason: "Duplicate-safe rerun logic exists in `JobRepository` and `GenerateJobService`, but the shipped CLI does not use that stack, so the real operator path never reaches duplicate detection or overwrite confirmation execution."
    artifacts:
      - path: "src/multilang/repositories/job_repository.py"
        issue: "Duplicate-safe logic is implemented and tested, but unreachable from the default CLI entrypoint."
      - path: "tests/integration/test_job_flow.py"
        issue: "Lifecycle coverage uses injected test wiring (`create_app(service=service)`) rather than the shipped `app = create_app()` path."
    missing:
      - "Make the default CLI use the repository-backed orchestration service."
      - "Add an integration test against the shipped app/bootstrap path, not only injected test doubles."
---

# Phase 1: Job Orchestration & Recovery Verification Report

**Phase Goal:** Users can start a generation run for a supported language and trust the job lifecycle even when runs fail or are repeated.
**Verified:** 2026-04-19T14:28:38Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | User can choose one of the 7 supported target languages before a job starts. | ✓ VERIFIED | `SupportedLanguage` restricts values to `pt/es/en/fr/de/ru/nl` in `src/multilang/domain/jobs.py:10-17`; CLI flag uses that enum in `src/multilang/cli.py:299-344`; tests cover invalid language in `tests/cli/test_generate_command.py:12-21`. |
| 2 | User can see batch-level progress and failures while generation is running. | ✗ FAILED | `ProgressRenderer` exists in `src/multilang/progress.py:11-56`, but the shipped app is `app = create_app()` in `src/multilang/cli.py:352`, and `create_app()` only uses the real executor when `service is not None` (`src/multilang/cli.py:290-291`). Behavioral spot-check: `uv run python -c ... CliRunner().invoke(app,[...])` returned `exit 0` and empty output. |
| 3 | User can resume an interrupted generation run without losing cards that already completed. | ✗ FAILED | Resume logic is implemented in `src/multilang/services/generate_job.py:87-128` and `src/multilang/repositories/job_repository.py:155-199`, but no runtime repository/session bootstrap exists in `src/`; search only found `create_engine`/`Session` setup in tests. The shipped CLI path never creates persisted jobs. |
| 4 | User can rerun the same input without silent duplicate card creation. | ✗ FAILED | Duplicate-safe logic exists in `src/multilang/repositories/job_repository.py:71-118` and `src/multilang/services/generate_job.py:149-165`, but it is unreachable from the default `app = create_app()` path. Integration coverage uses `create_app(service=service)` in `tests/integration/test_job_flow.py:90`, not the shipped bootstrap. |
| 5 | The codebase has explicit job lifecycle contracts for status, stage progress, and resume diagnostics. | ✓ VERIFIED | `JobStage`, `JobStatus`, `JobProgressSnapshot`, and `ResumeDiagnostic` are defined in `src/multilang/domain/jobs.py:20-69`, with contract tests in `tests/domain/test_jobs.py:15-69`. |
| 6 | Job and item persistence plus corrupted-resume diagnostics exist in code. | ✓ VERIFIED | SQLAlchemy models and migration define `generation_jobs`/`generation_items` with uniqueness in `src/multilang/db/models.py:14-70` and `alembic/versions/20260418_01_job_tables.py:16-59`; `validate_resume_state` returns `ResumeDiagnostic` in `src/multilang/repositories/job_repository.py:155-199`; repository tests cover this in `tests/repositories/test_job_repository.py:45-68`. |
| 7 | Failed items retry automatically, then remain visible in the final summary if they still fail. | ✗ FAILED | Retry execution and summary code exist in `src/multilang/cli.py:130-229` and `src/multilang/services/job_summary.py:36-76`, but both are only exercised through injected services in tests. The shipped CLI does not execute this path. |

**Score:** 3/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `pyproject.toml` | Python package + pytest config | ✓ VERIFIED | Substantive project metadata and pytest config present (`pyproject.toml:1-33`). |
| `src/multilang/settings.py` | Typed runtime settings | ✓ VERIFIED | Defines constrained settings and seven-language default (`settings.py:8-30`). |
| `src/multilang/domain/jobs.py` | Shared lifecycle contracts | ✓ VERIFIED | Enums/models are substantive and tested (`jobs.py:10-80`). |
| `src/multilang/db/models.py` | Persisted job/item schema | ✓ VERIFIED | SQLAlchemy tables + unique constraint present and aligned with migration. |
| `alembic/versions/20260418_01_job_tables.py` | Migration for persistence schema | ✓ VERIFIED | Creates both Phase 1 tables and duplicate constraint. |
| `src/multilang/repositories/job_repository.py` | Persistence API for resume/rerun safety | ✓ VERIFIED | Substantive repository with create/load/reuse/failure/diagnostic paths. |
| `src/multilang/services/input_fingerprint.py` | Deterministic run-key logic | ✓ VERIFIED | Normalizes item keys and computes reproducible fingerprints/run keys. |
| `src/multilang/services/generate_job.py` | Start/resume/rerun orchestration | ✓ VERIFIED | Service is substantive and wired to repository methods. |
| `src/multilang/cli.py` | User-facing command path | ⚠️ HOLLOW — wired but disconnected | File is substantive, but shipped `app` uses the default no-op executor instead of a real service. |
| `src/multilang/progress.py` | Visible progress rendering | ⚠️ ORPHANED | Reachable only when tests inject a service via `build_generate_executor(...)`; shipped app never instantiates it. |
| `src/multilang/services/job_summary.py` | Final lifecycle summary | ⚠️ ORPHANED | Implemented and tested, but no runtime consumer in the shipped CLI path. |
| `tests/integration/test_job_flow.py` | End-to-end lifecycle coverage | ⚠️ PARTIAL | Good repository-backed lifecycle coverage, but it validates injected wiring rather than the shipped app bootstrap. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `src/multilang/db/models.py` | `alembic/versions/20260418_01_job_tables.py` | matching schema/table names | ✓ WIRED | Both define `generation_jobs`, `generation_items`, and `(run_key, item_key)` uniqueness. |
| `src/multilang/repositories/job_repository.py` | `src/multilang/domain/jobs.py` | `ResumeDiagnostic` + `JobProgressSnapshot` returns | ✓ WIRED | Repository imports and returns domain contracts (`job_repository.py:12-18`, `251-258`). |
| `src/multilang/services/generate_job.py` | `src/multilang/repositories/job_repository.py` | `list_completed_item_keys` + `validate_resume_state` | ✓ WIRED | Service calls both methods on resume/rerun paths (`generate_job.py:51-52`, `98-99`, `156-157`). |
| `src/multilang/cli.py` | `src/multilang/services/generate_job.py` | CLI invokes orchestration service | ✗ NOT_WIRED (shipped path) | `create_app()` only builds the real executor when `service is not None`; shipped `app = create_app()` provides none (`cli.py:286-291`, `352`). |
| `src/multilang/cli.py` | `src/multilang/progress.py` | default execution uses `ProgressRenderer` | ✗ NOT_WIRED (shipped path) | `ProgressRenderer` is instantiated only inside `build_generate_executor`, which the shipped app never uses. |
| `src/multilang/services/job_summary.py` | runtime CLI flow | summary emitted after execution | ✗ NOT_WIRED | Summary builder is imported only in tests, not in application runtime wiring. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `src/multilang/cli.py` | `executor` used by `generate(...)` | `create_app()` chooses `default_generate_executor` when no service is supplied | No — default executor just returns the request (`cli.py:46-49`, `290-291`) | ✗ DISCONNECTED |
| `src/multilang/services/generate_job.py` | `pending_item_keys` / `skipped_item_keys` | normalized requested items + repository completed-item lookup | Yes | ✓ FLOWING |
| `src/multilang/services/job_summary.py` | summary counts + failed item list | persisted job row + failed `GenerationItem` rows | Yes, but only in tests | ⚠️ FLOWING INTERNAL ONLY |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Repository/service/tests run successfully | `"/home/miguel/.local/bin/uv" run --extra dev pytest -q` | `26 passed in 9.80s` | ✓ PASS |
| Shipped `multilang generate` path emits runtime lifecycle behavior | `"/home/miguel/.local/bin/uv" run python -c "from typer.testing import CliRunner; from multilang.cli import app; r=CliRunner().invoke(app,['generate','--language','en','--source','frequency','--level','1']); print('exit', r.exit_code); print('output', repr(r.output))"` | `exit 0`, `output ''` | ✗ FAIL |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `DECK-01` | 01-01, 01-03 | User can choose one of 7 supported target languages before generation starts | ✓ SATISFIED | Enum-backed CLI option rejects unsupported values. |
| `JOB-01` | 01-01, 01-02, 01-03, 01-04 | User can resume an interrupted generation job without losing already completed cards | ✗ BLOCKED | Resume/persistence code exists, but the shipped app never bootstraps the repository/service stack. |
| `JOB-02` | 01-04 | User can see per-batch progress and failures while generation is running | ✗ BLOCKED | Progress renderer is unreachable from the shipped CLI entrypoint. |
| `JOB-03` | 01-02, 01-03, 01-04 | User can rerun the same input without silent duplicate card creation | ✗ BLOCKED | Duplicate-safe logic is implemented but unreachable from the shipped CLI entrypoint. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `src/multilang/cli.py` | 46-49 | default executor is a no-op (`return request`) | 🛑 Blocker | The shipped app exits successfully without creating/resuming jobs or showing lifecycle output. |
| `src/multilang/cli.py` | 52-55 | default item processor is a stub (`return None`) | ⚠️ Warning | Even if service wiring were added, default processing still does no real downstream work until later phases. |
| `tests/integration/test_job_flow.py` | 90 | integration test uses injected `create_app(service=service)` instead of shipped `app = create_app()` | ⚠️ Warning | Tests pass without covering the actual runtime bootstrap path that users would run. |

### Gaps Summary

Phase 1 produced substantial internal scaffolding: typed lifecycle contracts, persistence models, repository rules, deterministic rerun keys, progress rendering, retry logic, and lifecycle summaries. The phase goal still failed because the shipped CLI entrypoint is not connected to that stack.

The core root cause is runtime wiring: `src/multilang/cli.py` defines the real execution path behind `build_generate_executor(service=...)`, but the published app object is `app = create_app()` with no service. That makes `multilang generate` a silent no-op in the real app, while tests pass by injecting a repository-backed service manually. Because of that disconnect, the roadmap truths for visible progress, real resume, and duplicate-safe reruns are not achieved for users yet.

---

_Verified: 2026-04-19T14:28:38Z_
_Verifier: the agent (gsd-verifier)_
