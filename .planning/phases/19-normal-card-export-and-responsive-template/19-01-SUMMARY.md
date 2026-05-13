---
phase: 19-normal-card-export-and-responsive-template
plan: 01
subsystem: exporting
tags: [anki, templates, csv, tsv, source-profiles]
requires:
  - phase: 18-text-field-remediation
    provides: normal generated-card text-field remediation baseline
provides:
  - Normal frequency export field tuple without `Front of Card`
  - Normal APKG/CSV/TSV assertions for the revised field contract
  - Normal template reference updated to `{{word}}`
affects: [normal-card-export, template-loader, phase-19]
tech-stack:
  added: []
  patterns: [source-profile-isolated export fields, template validation against exported fields]
key-files:
  created: []
  modified:
    - src/multilang/domain/exporting.py
    - src/multilang/templates/normal_card.md
    - tests/domain/test_exporting.py
    - tests/services/test_export_anki_package.py
    - tests/services/test_export_tabular_bundle.py
    - tests/services/test_card_template_loader.py
key-decisions:
  - "Keep `ExportCardRow.front_of_card` as a backward-compatible construction attribute while excluding it from normal ordered exports."
patterns-established:
  - "Normal-card templates must validate against `FREQUENCY_EXPORT_CARD_FIELD_NAMES` and reference `{{word}}` for the target word."
requirements-completed: [TMPL-01, TMPL-03]
duration: 22min
completed: 2026-05-13
---

# Phase 19 Plan 01: Remove Normal Front-of-Card Export Field Summary

**Normal APKG, CSV, TSV, and template exports now omit the duplicated `Front of Card` field while preserving source-profile-isolated highlight/manual contracts.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-05-13T17:14:00Z
- **Completed:** 2026-05-13T17:36:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Removed `Front of Card` from the normal frequency export field tuple and normal ordered mappings.
- Updated the normal card template to render the target word through `{{word}}`.
- Added focused regression coverage for APKG model fields, CSV/TSV headers, template validation, and unchanged highlight/manual field contracts.

## Task Commits

Each task was committed atomically:

1. **Task 1: Revise the normal export field contract per TMPL-01** - `dd8cbc8` (test RED), `ac86427` (feat GREEN)
2. **Task 2: Remove normal template and artifact references to `Front of Card` per TMPL-01** - `e93f655` (test RED), `811b792` (feat GREEN)

_Note: TDD tasks used separate failing-test and implementation commits._

## Files Created/Modified

- `src/multilang/domain/exporting.py` - Removed `Front of Card` from the normal frequency export field tuple.
- `src/multilang/templates/normal_card.md` - Replaced `{{Front of Card}}` with `{{word}}` in the normal front template.
- `tests/domain/test_exporting.py` - Asserted revised normal field ordering and source-profile-aware contracts.
- `tests/services/test_export_anki_package.py` - Asserted normal APKG model fields and template references omit `Front of Card`.
- `tests/services/test_export_tabular_bundle.py` - Asserted revised CSV/TSV headers and row positions.
- `tests/services/test_card_template_loader.py` - Added validation coverage for rejecting removed normal template references.

## Decisions Made

- Kept `front_of_card` on `ExportCardRow` for backward-compatible row construction and existing assembly code, but excluded it from normal export field selection.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Verification

- `python -m pytest tests/domain/test_exporting.py -q` → 10 passed
- `python -m pytest tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py tests/services/test_card_template_loader.py tests/domain/test_exporting.py -q` → 52 passed

## Next Phase Readiness

Plan 19-02 can build on the revised normal-card template to place sentence audio beside the example sentence without carrying the removed `Front of Card` reference.

## Self-Check: PASSED

- Created/modified files exist.
- Task commits found: `dd8cbc8`, `ac86427`, `e93f655`, `811b792`.

---
*Phase: 19-normal-card-export-and-responsive-template*
*Completed: 2026-05-13*
