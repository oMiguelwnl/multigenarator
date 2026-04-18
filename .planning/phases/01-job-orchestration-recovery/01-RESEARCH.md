# Phase 1 Research: Job Orchestration & Recovery

**Phase:** 1 - Job Orchestration & Recovery  
**Researched:** 2026-04-18  
**Status:** Ready for planning  
**Confidence:** HIGH

## Research Answer

Phase 1 should establish a **Python 3.12 library-first job runner with a Typer CLI entrypoint, SQLAlchemy/Alembic persistence, and a resumable job state machine**. This phase does not need deep domain research beyond the existing project research because the required patterns are standard: typed CLI input, persisted job state, idempotent item tracking, progress rendering, bounded retries, and safe overwrite confirmation.

## Decisions to Carry Into Planning

### Stack and shape
- Use **Python 3.12 + uv** per project stack research.
- Use **Typer** for the CLI because D-01 and D-02 require a CLI-first, single-command-plus-flags surface.
- Use **Pydantic v2** models for job requests, progress snapshots, and resume diagnostics.
- Use **SQLAlchemy 2 + Alembic + PostgreSQL-oriented schema design** for persisted job state. Local tests can use SQLite, but schema and repository patterns should stay PostgreSQL-compatible.
- Use **Rich** for stage-level terminal progress rendering so the default UX shows counters instead of verbose logs per D-03.

### Phase-1-specific architecture
- Create a single primary CLI command: `multilang generate`.
- Model a `run_key` derived from `(language, source_type, normalized_input_fingerprint)` so reruns can reuse completed work and skip duplicates by default.
- Persist both **job-level state** and **item-level state**:
  - job-level: status, current stage, last completed stage, counters, timestamps, resume metadata
  - item-level: item key, stage status, retry count, last error, completion markers
- Resume behavior should load persisted state, reuse completed items, and continue from the next incomplete work unit per D-05.
- If persisted state is internally inconsistent, stop with a typed diagnostic instead of trying to auto-heal per D-06.
- Default reruns must skip already completed items for the same `run_key` per D-07.
- Any overwrite path must require explicit confirmation before reprocessing existing outputs per D-08.

## Recommended File Layout

```text
src/multilang/
  __init__.py
  cli.py
  settings.py
  progress.py
  domain/jobs.py
  db/base.py
  db/models.py
  repositories/job_repository.py
  services/generate_job.py
  services/job_summary.py

alembic/
  env.py
  versions/

tests/
  cli/
  domain/
  repositories/
  services/
  integration/
```

## Concrete Design Guidance

### Supported language input
- Encode the 7 supported languages as a strict enum: `pt`, `es`, `en`, `fr`, `de`, `ru`, `nl`.
- Reject any other value at CLI parsing time so DECK-01 is enforced before a job starts.

### CLI surface
- Primary command: `multilang generate`
- Required/expected flags:
  - `--language <pt|es|en|fr|de|ru|nl>`
  - `--source <frequency|word-list>`
  - `--level <1|2|3>` when `--source frequency`
  - `--input-file <path>` when `--source word-list`
  - `--resume <job-id>` to continue an interrupted run
  - `--overwrite` to allow reprocessing existing outputs
  - `--yes-overwrite` to explicitly confirm overwrite in non-interactive runs

### Persistence model
- `generation_jobs`
  - `id`
  - `run_key`
  - `language`
  - `source_type`
  - `source_fingerprint`
  - `status`
  - `current_stage`
  - `last_completed_stage`
  - `total_items`
  - `completed_items`
  - `failed_items`
  - `retrying_items`
  - `resume_state` (JSON/JSONB)
  - timestamps
- `generation_items`
  - `id`
  - `job_id`
  - `run_key`
  - `item_key`
  - `status`
  - `last_completed_stage`
  - `retry_count`
  - `last_error`
  - timestamps
- Unique constraint: `(run_key, item_key)` to block silent duplicates across reruns.

### Retry and continue policy
- Use a bounded retry count for item failures; recommended default for Phase 1: **2 total attempts per item**.
- After final retry failure, mark the item failed, include it in the final summary, and continue processing remaining work per D-04.

### Progress UX
- Default output should be stage-level counters, not verbose per-item logs.
- Render at minimum:
  - current stage name
  - completed / total items
  - retrying count
  - failed count
  - skipped duplicates count
- Keep verbose failure detail for the final summary or explicit debug mode later.

### Resume safety
- Validate that persisted `current_stage`, `last_completed_stage`, and item rows agree.
- If the stage pointer says `generate_text` but there are no completed upstream item markers, raise a resume diagnostic and abort.
- Never guess how to repair corrupted state during this phase.

## Common Pitfalls To Prevent In Phase 1

- Do not treat reruns as a new job with no link to previous outputs; use `run_key` and item uniqueness.
- Do not rely on in-memory progress only; resumability requires persisted counters and item state.
- Do not use free-form string languages; use a strict enum so unsupported languages fail fast.
- Do not default overwrite silently; require interactive or flag-based confirmation.
- Do not print only verbose logs; the default user experience must show concise stage-level progress.

## Architectural Responsibility Map

| Layer | Phase 1 Responsibility |
|------|-------------------------|
| CLI | Parse validated flags, invoke coordinator, display progress/summary |
| Domain models | Encode supported languages, job stages, status, diagnostics |
| Repository | Persist and read job/item state; enforce uniqueness and resume-safe reads |
| Service layer | Start jobs, resume jobs, schedule only missing items, apply retry policy |
| Presentation | Stage-level counters and final failure summary |
| Tests | Contract tests, repository tests, service behavior tests, job-flow smoke test |

## Validation Architecture

Phase 1 should be executable only with automated verification in place from the start.

- Use **pytest** as the test runner.
- Add Wave 0 tests immediately for settings, domain contracts, repository behavior, and job orchestration rules.
- Keep a quick command under 30 seconds: `uv run pytest tests/domain tests/repositories tests/services tests/cli -q`
- Add a smoke command for the whole phase: `uv run pytest tests -q`

Required automated coverage:
- supported-language validation
- `run_key` / duplicate-skip behavior
- corrupted resume-state diagnostic
- overwrite confirmation requirement
- bounded retry then continue behavior
- progress snapshot rendering

## Source Coverage Notes For Planning

This research directly supports:
- **DECK-01** via strict language enum and CLI validation
- **JOB-01** via persisted job/item state and resume diagnostics
- **JOB-02** via Rich stage-level counters and final summary behavior
- **JOB-03** via `run_key`, uniqueness, duplicate skipping, and overwrite confirmation

## Recommendation

Proceed to planning without additional research. Phase 1 uses well-understood implementation patterns and should be planned as a greenfield foundation phase with 4 focused plans.

---

*Phase: 01-job-orchestration-recovery*  
*Research completed: 2026-04-18*
