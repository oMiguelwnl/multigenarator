---
phase: 28-latin-export-and-milestone-evidence
plan: 01
subsystem: export
tags: [latin, anki, export, curation, review-gates]
requires:
  - phase: 25-latin-review-gates-and-curated-records
    provides: Latin curation review gates and fail-closed export readiness checks
  - phase: 26-portuguese-translation-quality
    provides: Frozen Portuguese translation pack for the 50 Latin MVP records
  - phase: 27-latin-audio-policy-and-integrity
    provides: Approved Latin audio manifest and committed WAV media paths
provides:
  - Stable Classical Latin export row contract
  - Approved 50-row Latin export bundle builder
  - Auditable user-approved Portuguese translation gate update
affects: [phase-28-export, latin-mvp, anki-packaging]
tech-stack:
  added: []
  patterns: [fail-closed committed-asset joins, injectable loaders for focused tests]
key-files:
  created: [src/multilang/services/latin_export.py]
  modified:
    - tests/services/test_latin_export.py
    - data/latin_mvp/latin-mvp-50-v1-curation.json
    - data/latin_mvp/latin-mvp-50-v1-pt.json
key-decisions:
  - "Latin export rows are built only after source, translation, grammar, and audio gates are approved."
  - "The user's `Approve translations` response is recorded as the human review event for all 50 Portuguese translation gates."
  - "Latin audio fields expose Anki sound basenames while media_index retains repository-relative WAV paths."
patterns-established:
  - "Latin export stays isolated from modern-language SupportedLanguage and existing ExportCardRow contracts."
  - "Learner-facing source text is assembled from public provenance fields only."
requirements-completed: [EXP-01, EXP-02]
duration: 3min
completed: 2026-06-08
---

# Phase 28 Plan 01: Latin Export Row Contract Summary

**Approved 50-card Classical Latin export rows joined from committed source, curation, Portuguese, and audio assets**

## Performance

- **Duration:** 3 min resumed execution time
- **Started:** 2026-06-08T22:29:40Z
- **Completed:** 2026-06-08T22:32:34Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added the stable Latin Anki field order with blank `Image` and no learner-facing `Classe`/`part_of_speech` field.
- Recorded the user's translation approval on all 50 curation `translation_gate` records and the Portuguese translation pack review statuses.
- Implemented `build_latin_export_rows()` to fail closed on review/audio readiness, exact item-key ordering, unapproved translations, unsafe source text, and missing media pairs.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define Latin export row contract** - `24e9ec7` (test), `e403079` (feat)
2. **Task 2: Build approved Latin export rows from committed assets** - `738a367` (feat)

_Note: Task 1 followed the TDD red/green split before this continuation agent resumed from the checkpoint._

## Files Created/Modified

- `src/multilang/services/latin_export.py` - Latin note/deck constants, row dataclass, export bundle, and committed-asset row builder.
- `tests/services/test_latin_export.py` - Field-order, blank-image, committed-asset, fail-closed validator, approval, media, and ordering tests.
- `data/latin_mvp/latin-mvp-50-v1-curation.json` - Translation gate approval recorded for all 50 records with user review metadata.
- `data/latin_mvp/latin-mvp-50-v1-pt.json` - Portuguese translation entries marked `approved` after user review.

## Decisions Made

- Accepted the user's `Approve translations` checkpoint response as the audit event unblocking the Phase 26 Portuguese translations for export.
- Kept media paths out of learner-facing sound fields by rendering `[sound:{basename}]` while preserving repository-relative paths in `media_index`.
- Required the Portuguese translation pack `review_status` to be `approved` in addition to the curation `translation_gate`, so committed assets cannot drift back to pending translations unnoticed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Recorded translation approval in both curation and translation assets**
- **Found during:** Task 2 (Build approved Latin export rows from committed assets)
- **Issue:** The plan required approved export rows, but the checkpoint showed all curation translation gates and translation pack entries were still pending review.
- **Fix:** Used the existing review-gate contract to approve all curation translation gates with user review metadata and updated the translation pack review statuses to approved.
- **Files modified:** `data/latin_mvp/latin-mvp-50-v1-curation.json`, `data/latin_mvp/latin-mvp-50-v1-pt.json`
- **Verification:** `uv run pytest tests/services/test_latin_export.py tests/services/test_latin_review.py tests/services/test_latin_audio.py -q`
- **Committed in:** `738a367`

**Total deviations:** 1 auto-fixed (Rule 2)
**Impact on plan:** Required for correctness and export readiness; no scope creep beyond recording the human checkpoint approval.

## Issues Encountered

- Plan 28 initially stopped at the Task 2 human-action checkpoint because translations were not approved. The user approved them, and this summary records that checkpoint outcome.

## Validations

- PASS: `uv run pytest tests/services/test_latin_export.py tests/services/test_latin_review.py tests/services/test_latin_audio.py -q` (`25 passed`)

## Known Stubs

None.

## Next Phase Readiness

- Plan 28-02 can build APKG/CSV/TSV artifacts from the approved 50-row Latin export bundle.
- No remaining Plan 28-01 blockers.

## Self-Check: PASSED

- Found `src/multilang/services/latin_export.py`.
- Found `tests/services/test_latin_export.py`.
- Found `data/latin_mvp/latin-mvp-50-v1-curation.json`.
- Found `data/latin_mvp/latin-mvp-50-v1-pt.json`.
- Found task commits `24e9ec7`, `e403079`, and `738a367` in recent git history.

---
*Phase: 28-latin-export-and-milestone-evidence*
*Completed: 2026-06-08*
