# Phase 1: Job Orchestration & Recovery - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can start a generation run for a supported language and trust the job lifecycle even when runs fail or are repeated. This phase covers job entry, progress visibility, resumability, and duplicate-safe reruns. Frequency ingestion, lexical enrichment, content generation, audio, and export are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Job Surface
- **D-01:** v1 should be CLI-first for starting and operating generation jobs.
- **D-02:** The CLI should favor a single primary command with flags rather than a broader subcommand surface.

### Progress and Failure Handling
- **D-03:** During execution, the default user experience should show stage-level progress with counters rather than verbose logs by default.
- **D-04:** When an item fails during a run, the system should retry that item automatically and, if it still fails, continue the job while marking that item as failed in the final summary.

### Resume Behavior
- **D-05:** Resume should continue from the last successful point and reuse completed work instead of restarting the entire job.
- **D-06:** If persisted resume state is inconsistent or corrupted, the system should stop with a clear diagnostic rather than attempting an unsafe automatic restart.

### Rerun and Duplicate Policy
- **D-07:** The default rerun behavior should skip duplicates and process only what is still missing.
- **D-08:** If a manual rerun conflicts with already generated items, the system should require explicit confirmation before overwriting or reprocessing existing outputs.

### the agent's Discretion
- Exact flag names and CLI ergonomics, as long as they preserve the single-command-plus-flags shape.
- Internal retry count and how the summary is formatted, as long as failed items remain visible and the job continues safely.
- How progress counters are rendered in the terminal.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and success criteria
- `.planning/ROADMAP.md` — Phase 1 goal, requirements mapping, and success criteria for job orchestration, visibility, resume, and duplicate-safe reruns.

### Product constraints
- `.planning/PROJECT.md` — Core product value, supported languages, Azure-first direction, and reliability expectations that constrain Phase 1 decisions.
- `.planning/REQUIREMENTS.md` — Locked Phase 1 requirements: `DECK-01`, `JOB-01`, `JOB-02`, and `JOB-03`.

### Current project state
- `.planning/STATE.md` — Current milestone status and known blockers that may affect planning order.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No application source files exist yet. The repo is still greenfield for implementation.

### Established Patterns
- Planning is documentation-first: the repo already uses `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, and `.planning/STATE.md` as the current source of truth.
- There is no existing CLI, job runner, persistence layer, or progress-reporting pattern to preserve.

### Integration Points
- Phase 1 will establish the first runnable surface of the product and should create the baseline pattern that later phases plug into for lexical processing, text generation, audio, and export.

</code_context>

<specifics>
## Specific Ideas

- The user wants the early product to feel operationally trustworthy before content-generation sophistication: start jobs easily, see where they are, retry safely, resume safely, and avoid silent duplicates.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-job-orchestration-recovery*
*Context gathered: 2026-04-18*
