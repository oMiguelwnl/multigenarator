---
phase: 13-highlight-export-and-template
plan: 02
subsystem: export-template
tags: [anki, apkg, highlights, templates, media, pytest]
requires:
  - phase: 13-highlight-export-and-template
    provides: Source-profile-aware card template loader and dedicated highlight template
provides:
  - Source-profile-aware APKG note model creation
  - Dedicated highlight APKG model with validated fields/template/CSS
  - Regression coverage for highlight media packaging and fail-closed media validation
affects: [phase-13-highlight-export, apkg-export, highlight-template, anki-media]
tech-stack:
  added: []
  patterns: [source-profile template routing at APKG boundary, fail-closed template validation errors, pre-write media validation regression tests]
key-files:
  created: []
  modified: [src/multilang/services/export_anki_package.py, tests/services/test_export_anki_package.py]
key-decisions:
  - "APKG model creation now delegates template selection to load_card_template(source_type=...) so SourceProfile remains the single routing contract."
  - "Template loader validation errors are surfaced as ExportAnkiPackageError at the APKG boundary for clear pre-write failure behavior."
patterns-established:
  - "Highlight APKG model assertions inspect the generated package collection and media manifest, not only in-memory model state."
  - "Broken highlight audio references must assert the output APKG path is absent after failure."
requirements-completed: [EXPORT-01, EXPORT-03]
duration: 2min
completed: 2026-05-06
---

# Phase 13 Plan 02: Highlight APKG Export and Template Wiring Summary

**Source-profile-aware APKG export uses the dedicated highlight note model and fails closed on broken highlight media**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-06T17:30:19Z
- **Completed:** 2026-05-06T17:32:33Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Replaced the local APKG template parser with `load_card_template(source_type=...)`, preserving frequency and word-list templates while routing `kindle-highlights` to the dedicated highlight template.
- Confirmed highlight models use `HIGHLIGHT_MODEL_ID`, `Multilang::Highlight Card`, the exact highlight export fields, highlight qfmt/afmt/CSS, and no `Translation` reference.
- Added APKG package-level regression tests proving highlight exports include both word and sentence audio, reject malformed media before writing, and reject mixed highlight/existing source rows.

## Task Commits

Each task was committed atomically:

1. **Task 1: Use validated source-profile templates for model creation**
   - `7a28a61` test: add failing APKG model template contracts
   - `cc30f86` feat: route APKG models through source templates
2. **Task 2: Prove highlight APKG media and mixed-source failures**
   - `3291acc` test: cover highlight APKG media safety

**Plan metadata:** pending final docs commit

## Files Created/Modified

- `src/multilang/services/export_anki_package.py` - APKG model construction now loads validated templates through the source-profile-aware loader and converts template validation errors into `ExportAnkiPackageError`.
- `tests/services/test_export_anki_package.py` - Expanded model/template assertions and highlight APKG media/mixed-source fail-closed regression coverage.

## Decisions Made

- APKG template routing now depends on `SourceProfile.template_name` via `load_card_template`, avoiding a second local markdown parser and preventing highlight behavior from leaking into word-list decks.
- `ValueError` from template parsing/reference validation is wrapped as `ExportAnkiPackageError` so callers see one export-layer failure type.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Task 2 RED tests passed immediately because the existing `_resolve_media_files()` and mixed-source gates already enforced the planned fail-closed behavior after Task 1 wired the highlight model. The tests were kept as regression coverage; no production code change was necessary for Task 2.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Threat Flags

None.

## TDD Gate Compliance

- Task 1 RED gate commit present: `7a28a61`; GREEN gate commit present after RED: `cc30f86`.
- Task 2 test commit present: `3291acc`. RED did not fail because the required media/mixed-source behavior was already implemented by existing export gates; this is documented for verifier visibility.

## Verification

- `python -m pytest tests/services/test_export_anki_package.py tests/services/test_card_template_loader.py -q` — 28 passed

## Next Phase Readiness

- Plan 13-03 can refresh the phonetics template independently; normal frequency/word-list APKG behavior remains isolated from the highlight note model.
- Highlight APKG export now has package-level regression evidence for dedicated note model selection and safe audio packaging.

## Self-Check: PASSED

- Found modified files: `src/multilang/services/export_anki_package.py`, `tests/services/test_export_anki_package.py`, and this summary.
- Found task commits: `7a28a61`, `cc30f86`, `3291acc`.

---
*Phase: 13-highlight-export-and-template*
*Completed: 2026-05-06*
