# Phase 1 Pattern Map

**Phase:** 1 - Job Orchestration & Recovery  
**Generated:** 2026-04-18

## Codebase Reality

The repository is greenfield for application code. There are **no existing source-file analogs** for CLI commands, repositories, services, or tests.

## Patterns To Establish In This Phase

### 1. Library-first package layout
- Put business logic under `src/multilang/`
- Keep CLI wiring in `src/multilang/cli.py`
- Keep persistence under `src/multilang/db/` and `src/multilang/repositories/`
- Keep orchestration under `src/multilang/services/`

### 2. Typed contracts first
- Define enums and Pydantic models before repository/service wiring
- Use those contracts as the only inputs/outputs between CLI, services, and repositories

### 3. Repository boundary
- Services should call repository methods such as `create_job`, `get_job`, `list_completed_item_keys`, `record_item_success`, `record_item_failure`
- Keep SQLAlchemy details out of the CLI layer

### 4. Test-first verification surface
- `tests/domain/` for enums and model contracts
- `tests/repositories/` for persistence and uniqueness behavior
- `tests/services/` for resume/rerun orchestration rules
- `tests/cli/` for command parsing and overwrite confirmation
- `tests/integration/` for job-flow smoke coverage

### 5. Terminal UX pattern
- Default output: concise stage-level counters
- Detailed failures: final summary or explicit debug path

## Planned File Roles

| File | Role |
|------|------|
| `src/multilang/settings.py` | Environment/runtime config |
| `src/multilang/domain/jobs.py` | Supported languages, statuses, stages, diagnostics |
| `src/multilang/db/models.py` | Job and item persistence schema |
| `src/multilang/repositories/job_repository.py` | State persistence and duplicate-safe reads/writes |
| `src/multilang/services/generate_job.py` | Start/resume/rerun orchestration |
| `src/multilang/progress.py` | Stage counter rendering |
| `src/multilang/services/job_summary.py` | Final run summary formatting |
| `src/multilang/cli.py` | Single-command CLI surface |

## Constraints From Context And Research

- Keep the public operator surface to **one main command with flags**.
- Resume must be **safe-first**, not best-effort.
- Duplicate handling must default to **skip existing**, not overwrite.
- Progress must be **counter-based**, not verbose-log-first.
