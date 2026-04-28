---
phase: 07-milestone-evidence-audit-hygiene
researched: 2026-04-28
status: complete
source: internal-artifact-audit
---

# Phase 7 Research: Milestone Evidence & Audit Hygiene

## Research Question

What needs to be planned so the v1.0 milestone audit uses current evidence instead of stale verification artifacts or mismatched planning metadata?

## Relevant Existing Evidence

### Phase 1 lifecycle behavior

The stale blocker is `.planning/phases/01-job-orchestration-recovery/01-VERIFICATION.md`, which still has `status: gaps_found` and blocks `JOB-01`, `JOB-02`, and `JOB-03`. Later Phase 1 gap-closure summaries provide superseding evidence:

- `01-05-SUMMARY.md` records lazy repository-backed runtime bootstrap on the shipped CLI path and `requirements-completed: [JOB-01, JOB-02, JOB-03]`.
- `01-06-SUMMARY.md` records shipped-app lifecycle summary output, safe resume diagnostics, duplicate-skip/overwrite coverage, and `requirements-completed: [JOB-01, JOB-02, JOB-03]`.
- `tests/integration/test_job_flow.py` now exercises `create_app()` with real runtime settings and asserts `resumed_from_job=`, `skipped_duplicates=2`, and `overwritten_items=2` on the shipped app.
- `tests/cli/test_generate_command.py` asserts progress lines, summary counters, duplicate counts, inconsistent resume aborts, and runtime audio counters.

Planning implication: refresh `01-VERIFICATION.md` from `gaps_found` to a current re-verification report only after rerunning the focused shipped-path test commands.

## Milestone Audit Gaps Still In Scope After Phase 6

Phase 6 closed the functional E2E text acceptance gap (`GAP-1`) with:

- `06-01-SUMMARY.md`: natural deterministic local text adapters and accepted text proof.
- `06-02-SUMMARY.md`: refreshed `tests/integration/test_text_job_flow.py`, now contract-based.
- `06-03-SUMMARY.md`: custom word-list generate → accepted text → fake Azure audio → `.apkg`/CSV/TSV export proof.
- `06-04-SUMMARY.md`: frequency all-three-level sample → accepted text → fake Azure audio → export proof, plus preservation of the 3×1000 production contract.

Planning implication: Phase 7 should not reimplement E2E functionality. It should update audit and roadmap metadata to reference Phase 6 evidence.

## Metadata Hygiene Items

The stale v1.0 audit names these metadata issues:

1. `01-VERIFICATION.md` remains stale and blocks `JOB-01`, `JOB-02`, `JOB-03`.
2. Phase 4 has no `04-VALIDATION.md`, so Nyquist validation metadata reports missing.
3. Phase 5 summary frontmatter has empty `requirements-completed` arrays in `05-01-SUMMARY.md` through `05-04-SUMMARY.md` even though `05-VERIFICATION.md` passed all Phase 5 requirements.
4. `audit-open --json` reported passed UAT files as open despite `03-HUMAN-UAT.md` and `04-HUMAN-UAT.md` having `status: passed`, `pending: 0`, and `issues: 0` in the body.
5. `audit-open --json` reported quick task `260421-001` as missing even though its quick summary and verification both show completion/passed evidence.

Planning implication: Create explicit metadata fields rather than relying only on prose body tables:

- Add Phase 4 validation strategy with `nyquist_compliant: true` and `wave_0_complete: true` because existing Phase 4 verification proves automated and human validation coverage.
- Add explicit UAT frontmatter counters (`total`, `passed`, `issues`, `pending`, `blocked`) to Phase 3 and Phase 4 human UAT files.
- Add explicit quick-task completion/verification evidence to quick task summary frontmatter if needed by open-audit scanning.
- Fill Phase 5 `requirements-completed` frontmatter by plan evidence:
  - `05-01`: `[CARD-01, CARD-02]`
  - `05-02`: `[CARD-01, CARD-02, CARD-04, EXPT-02, EXPT-03]`
  - `05-03`: `[EXPT-01, EXPT-03, CARD-03]`
  - `05-04`: `[EXPT-01, EXPT-02, EXPT-03]`
  - `05-05` already lists `[CARD-03, EXPT-01, EXPT-03]`.

## Validation Architecture

Phase 7 is evidence/metadata work. Verification should be fast, deterministic, and focused on the evidence that the audit consumes.

### Automated checks to use in plans

- `uv run pytest tests/integration/test_job_flow.py tests/cli/test_generate_command.py -q` — proves current shipped lifecycle behavior for `JOB-01`, `JOB-02`, and `JOB-03`.
- `uv run pytest tests/integration/test_text_job_flow.py tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_frequency_e2e_export_flow.py -q` — proves Phase 6 E2E evidence remains green while metadata is refreshed.
- `uv run pytest tests/services/test_audio_synthesis.py tests/integration/test_audio_job_flow.py tests/cli/test_generate_command.py -q -k 'audio or default_runtime_reports_audio_counters or reports_failed_audio_when_no_approved_voice_exists'` — validates the Phase 4 validation metadata references live code paths with automated coverage. If the `-k` expression deselects too broadly, use the exact commands from `04-VERIFICATION.md`.
- `python - <<'PY' ... PY` metadata assertions are acceptable for docs-only changes when checking frontmatter strings in `.planning` files.

### Audit refresh approach

Do not edit product code in Phase 7 unless an automated check unexpectedly fails because of code regression. The intended outputs are evidence artifacts and metadata alignment.

## Discovery Level

Level 0/1: no new libraries or external APIs are required. This phase follows existing docs, pytest, and shipped CLI test patterns already present in the codebase.

## Risks and Mitigations

- **Risk:** Marking requirements complete without current behavioral proof.
  - **Mitigation:** Plan 07-01 must rerun focused shipped-path tests before updating `01-VERIFICATION.md`.
- **Risk:** Audit metadata hides real functional gaps.
  - **Mitigation:** Plan 07-04 must reference Phase 6 E2E tests and not simply delete audit findings.
- **Risk:** YAML/frontmatter changes break GSD scanners.
  - **Mitigation:** Each metadata task must include grep/Python frontmatter assertions.

## Research Complete

No external technical research is required. Phase 7 is an internal evidence reconciliation phase grounded in existing verification reports, summaries, requirements, and tests.
