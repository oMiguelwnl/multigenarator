---
phase: 05-anki-safe-export-contract
plan: 02
subsystem: export
tags: [anki, csv, tsv, utf-8, export]
requires:
  - phase: 05-01
    provides: frozen export contracts and export snapshot persistence
provides:
  - deterministic export-row assembly from accepted lexical text and audio records
  - utf-8 csv and tsv fallback bundles with Anki import headers
  - basename-only sound references and html-safe field serialization
affects: [phase-05-plan-03, phase-05-plan-04, export, anki]
tech-stack:
  added: []
  patterns: [assembly service persists frozen export rows, tabular bundles normalize multiline fields to br html, explicit export prerequisite failures]
key-files:
  created:
    - src/multilang/services/assemble_export_cards.py
    - src/multilang/services/export_tabular_bundle.py
    - tests/services/test_assemble_export_cards.py
    - tests/services/test_export_tabular_bundle.py
  modified: []
key-decisions:
  - "Assemble export rows only from accepted text records with synthesized audio, and fail fast when any prerequisite is missing."
  - "Normalize multiline tabular fields to `<br>` before serialization so UTF-8 text imports stay structurally safe for Anki."
patterns-established:
  - "Export workflow services return typed results instead of ad-hoc dictionaries."
  - "Tabular export files always include Anki import headers plus the canonical CARD-01 column order."
requirements-completed: []
duration: 3min
completed: 2026-04-26
---

# Phase 5 Plan 02: Turn persisted rows into deterministic export cards and tabular fallbacks Summary

**Accepted lexical, text, and audio rows now assemble into frozen export cards, and CSV/TSV fallbacks ship with UTF-8-safe Anki import headers**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-26T20:05:06Z
- **Completed:** 2026-04-26T20:08:07Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added deterministic export-card assembly from accepted text, grounded lexical data, and synthesized audio assets.
- Added CSV and TSV fallback writers with canonical field order and Anki import headers.
- Enforced explicit failures for missing lexical rows, missing accepted text, and missing required audio.

## Task Commits

1. **Task 1: Assemble accepted-card export rows with deterministic identity** - `04206ab` (test), `145390c` (feat)
2. **Task 2: Write UTF-8-safe CSV and TSV fallback bundles** - `6745f92` (feat)

**Plan metadata:** pending

## Files Created/Modified
- `src/multilang/services/assemble_export_cards.py` - assembles accepted records into persisted export-card snapshots with basename-only sound tags
- `src/multilang/services/export_tabular_bundle.py` - writes deterministic CSV/TSV fallback bundles with UTF-8 and import headers
- `tests/services/test_assemble_export_cards.py` - covers field order, `<br>` definitions, stable GUIDs, and failure diagnostics
- `tests/services/test_export_tabular_bundle.py` - covers CSV/TSV headers, UTF-8 content, and multiline/non-Latin serialization

## Decisions Made
- Used export-row assembly as the trust boundary so later `.apkg` and CLI work can consume already-frozen snapshots.
- Converted embedded newlines to `<br>` during tabular serialization to preserve Anki-safe structure for multiline content.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected multiline tabular test expectations to reflect one field per column**
- **Found during:** Task 2 (Write UTF-8-safe CSV and TSV fallback bundles)
- **Issue:** The initial RED assertions split newline-bearing example sentences as if they were separate CSV columns, which did not match the intended fixed-schema export contract.
- **Fix:** Normalized multiline values to `<br>` in the serializer and updated the task test to assert one preserved field per column.
- **Files modified:** `src/multilang/services/export_tabular_bundle.py`, `tests/services/test_export_tabular_bundle.py`
- **Verification:** `uv run pytest tests/services/test_assemble_export_cards.py tests/services/test_export_tabular_bundle.py -q`
- **Committed in:** `6745f92`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The deviation tightened the serializer to match Anki-safe multiline field semantics without expanding scope.

## Issues Encountered
- None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Plan 03 can package `.apkg` notes from the frozen export rows without reconstructing field payloads.
- Plan 04 can reuse the same assembly and tabular services on the shipped CLI path.

## Self-Check: PASSED
- Found `.planning/phases/05-anki-safe-export-contract/05-02-SUMMARY.md`
- Verified task commits `04206ab`, `145390c`, and `6745f92`

---
*Phase: 05-anki-safe-export-contract*
*Completed: 2026-04-26*
