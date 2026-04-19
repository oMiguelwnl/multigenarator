---
phase: 01-job-orchestration-recovery
reviewed: 2026-04-19T14:24:48Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - src/multilang/cli.py
  - src/multilang/services/generate_job.py
  - src/multilang/services/job_summary.py
  - src/multilang/progress.py
  - tests/cli/test_generate_command.py
  - tests/services/test_generate_job.py
  - tests/integration/test_job_flow.py
  - tests/test_job_summary.py
  - tests/test_progress.py
findings:
  critical: 0
  warning: 3
  info: 0
  total: 3
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-04-19T14:24:48Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Reviewed the Phase 1 job orchestration and recovery changes across the CLI, orchestration service, progress rendering, lifecycle summary builder, and related tests. The main regressions are around unsafe resume handling and CLI validation: resumes can accept a different input set than the original job, inconsistent persisted resume state is surfaced only as metadata and not as an operator-visible failure, and word-list paths are not validated before read-time.

## Warnings

### WR-01: Resume accepts mismatched input and can pollute an existing job

**File:** `src/multilang/services/generate_job.py:87-128`
**Issue:** `resume()` trusts the caller-provided `requested_item_keys` and partitions them against the stored `job.run_key`, but never verifies that the resumed request matches the original job fingerprint. A caller can resume job `A` with a different word list (or different frequency scope) and the service will enqueue those new items under the old job/run, corrupting the original run state.
**Fix:** Recompute the expected request identity on resume and reject mismatches before partitioning. For example, pass the full `GenerationRequest` into `resume()`, rebuild the expected `run_key`/`source_fingerprint`, and raise if they differ from the persisted job.

```python
def resume(
    self,
    request: GenerationRequest,
    *,
    job_id: str,
    requested_item_keys: Iterable[str],
    overwrite_confirmed: bool = False,
) -> GenerateJobResult:
    job = self.repository.get_job(job_id)
    if job is None:
        raise ValueError(f"unknown job_id: {job_id}")

    normalized_items = normalize_requested_item_keys(requested_item_keys)
    expected_run_key = build_run_key(request, requested_item_keys=normalized_items)
    expected_fingerprint = build_input_fingerprint(request, requested_item_keys=normalized_items)
    if job.run_key != expected_run_key or job.source_fingerprint != expected_fingerprint:
        raise ValueError("resume request does not match persisted job input")
```

Add a regression test that starts a word-list job, changes the input file, and verifies resume is rejected.

### WR-02: Invalid persisted resume state is returned as a successful no-op

**File:** `src/multilang/cli.py:77-95,130-159`
**Issue:** `build_generate_executor()` calls `service.orchestrate()` and then always proceeds into `_execute_with_progress()`. When `GenerateJobService.resume()` returns a `diagnostic` for inconsistent persisted state, the executor still emits a normal progress line and returns successfully with no work done. That hides a broken resume state from operators and from the CLI exit code.
**Fix:** Fail fast when `orchestration.diagnostic` is present. Surface the diagnostic message to the operator and exit non-zero instead of treating it as a clean execution.

```python
orchestration = service.orchestrate(...)
if orchestration.diagnostic is not None:
    raise typer.Exit(
        code=1,
        message=f"Cannot resume job {orchestration.job_id}: {orchestration.diagnostic.reason}",
    )
```

Add a CLI/executor test that injects an inconsistent persisted state and asserts the command fails visibly.

### WR-03: `--input-file` does not validate path existence and can crash with traceback

**File:** `src/multilang/cli.py:313-316,240-247`
**Issue:** The Typer option declares `exists=False`, so a missing `--input-file` path passes CLI parsing and fails later inside `load_requested_item_keys()` with an unhandled `FileNotFoundError`. This is a user-facing regression and bypasses the otherwise clean parameter validation flow.
**Fix:** Let Typer validate the path up front (and optionally readability), or catch the read failure and convert it to `typer.BadParameter`.

```python
input_file: Annotated[
    Path | None,
    typer.Option("--input-file", exists=True, dir_okay=False, readable=True),
] = None
```

Add a CLI test that passes a nonexistent file path and asserts a friendly validation error instead of a traceback.

---

_Reviewed: 2026-04-19T14:24:48Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
