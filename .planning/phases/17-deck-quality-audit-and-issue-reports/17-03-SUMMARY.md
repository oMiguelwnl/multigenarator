---
phase: 17-deck-quality-audit-and-issue-reports
plan: 03
subsystem: deck-audit
tags: [typer, cli, apkg, audit, reproducibility]
requires:
  - phase: 17-01
    provides: Read-only APKG reader and Definition issue detector
  - phase: 17-02
    provides: Deterministic JSON and Markdown audit reports
provides:
  - audit-deck CLI command
  - End-to-end APKG audit reproducibility tests
  - Known APKG audit evidence for dbda4eb2-f0ec-402b-864f-48cdcf982b09.apkg
affects: [phase-17, phase-18, deck-quality, remediation]
tech-stack:
  added: []
  patterns: [Typer command wiring, non-mutating APKG audit command]
key-files:
  created:
    - tests/cli/test_audit_deck_command.py
  modified:
    - src/multilang/cli.py
key-decisions:
  - "The audit-deck command prints stable key/value metadata and writes only deck-audit.json and deck-audit.md report files."
  - "Known APKG deck-specific evidence is generated under ignored .multilang/audits because it may contain private deck excerpts."
patterns-established:
  - "CLI audit commands compose reader, detector, and reporter services without invoking generation/export mutation services."
requirements-completed: [AUDIT-01, AUDIT-02, AUDIT-03]
duration: 20min
completed: 2026-05-12
---

# Phase 17 Plan 03: audit-deck CLI + reproducibility/non-mutation evidence Summary

**Operator CLI audit flow for APKG decks with reproducible reports and known-deck evidence**

## Performance

- **Duration:** ~20 min plus checkpoint wait for user-supplied APKG location
- **Started:** 2026-05-12T19:28:29Z
- **Completed:** 2026-05-12
- **Tasks:** 3
- **Files modified:** 2 tracked files plus ignored local audit evidence

## Accomplishments

- Added `audit-deck --input-apkg ... --output-dir ...` to the Typer CLI.
- Added CLI tests proving metadata output, missing-path diagnostics, reproducible JSON bytes, Markdown grouping, and unchanged APKG hashes.
- Audited the supplied known APKG `dbda4eb2-f0ec-402b-864f-48cdcf982b09.apkg` from `.multilang/exports`.

## Known APKG Evidence

Command run:

```bash
python -m multilang.cli audit-deck --input-apkg "C:\dev\multilang\.multilang\exports\dbda4eb2-f0ec-402b-864f-48cdcf982b09.apkg" --output-dir ".multilang/audits/dbda4eb2-f0ec-402b-864f-48cdcf982b09"
```

Result:

- `json_report=.multilang\audits\dbda4eb2-f0ec-402b-864f-48cdcf982b09\deck-audit.json`
- `markdown_report=.multilang\audits\dbda4eb2-f0ec-402b-864f-48cdcf982b09\deck-audit.md`
- `card_count=2607`
- `issue_count=755`
- `input_sha256=5ccc4f11ebbbb8ba256a02174a02dcc727f95ad7b88fbf7e2da4d0ae09ac7b24`

Report files exist locally but are not committed because `.multilang/` is ignored runtime/private evidence storage.

## Verification

`uv` is unavailable in this shell, so equivalent Python verification was used:

```bash
python -m pytest tests/cli/test_audit_deck_command.py tests/services/test_deck_audit_reader.py tests/services/test_deck_audit_reports.py tests/domain/test_deck_audit.py -q
```

Result: `16 passed in 0.79s`.

## Task Commits

1. **Task 1/2 RED:** `8c53336` test(17-03): add failing audit-deck CLI tests
2. **Task 1/2 GREEN:** `3c27120` feat(17-03): add audit-deck CLI command

## Files Created/Modified

- `src/multilang/cli.py` - Added `audit-deck` command wiring reader, detector, and report writer.
- `tests/cli/test_audit_deck_command.py` - Added CLI integration tests for output, diagnostics, reproducibility, and non-mutation.

## Decisions Made

- Use ignored `.multilang/audits/...` for deck-specific evidence because reports contain deck field excerpts.
- Do not substitute a different APKG when the exact known APKG is unavailable; the exact file was found in the user-provided directory.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Used local Python pytest because `uv` is unavailable in the shell**
- **Found during:** Task verification
- **Issue:** `uv run pytest ...` is unavailable in this environment.
- **Fix:** Ran equivalent `python -m pytest ...` commands.
- **Files modified:** None
- **Verification:** Focused Phase 17 test command passed.
- **Committed in:** N/A

**Total deviations:** 1 auto-fixed (1 blocking)

## Auth Gates

None.

## Issues Encountered

- Initial checkpoint occurred because the known APKG was absent from the workspace search. The user supplied `.multilang/exports`, and the exact APKG was found there.

## Known Stubs

None.

## Threat Flags

None beyond the plan threat model. The CLI accepts local APKG and report output paths as planned.

## User Setup Required

None remaining.

## Next Phase Readiness

- Phase 18 can use the generated audit findings to prioritize text field remediation.
- Phase 17 audit tooling is complete; local known-deck reports remain under `.multilang/audits/...`.

## Self-Check: PASSED

- Confirmed created/modified tracked files exist.
- Confirmed task commits exist: `8c53336`, `3c27120`.
- Confirmed known APKG audit reports exist locally under `.multilang/audits/dbda4eb2-f0ec-402b-864f-48cdcf982b09/`.

---
*Phase: 17-deck-quality-audit-and-issue-reports*
*Completed: 2026-05-12*
