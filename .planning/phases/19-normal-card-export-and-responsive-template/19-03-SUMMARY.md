---
phase: 19-normal-card-export-and-responsive-template
plan: 03
subsystem: testing
tags: [integration-tests, apkg, csv, tsv, templates, source-profiles]
requires:
  - phase: 19-normal-card-export-and-responsive-template
    provides: plans 19-01 and 19-02 normal export/template changes
provides:
  - Integrated normal APKG/CSV/TSV evidence for the revised field contract
  - Integrated evidence that normal responsive sentence/audio CSS reaches APKG model output
  - Source-profile isolation checks for highlight, manual, and phonetics templates
affects: [phase-19-verification, v1.3-regression-evidence]
tech-stack:
  added: []
  patterns: [synthetic tmp_path artifact evidence, APKG model inspection via collection.anki2]
key-files:
  created:
    - tests/integration/test_v13_normal_template_export_contract.py
  modified: []
key-decisions:
  - "Use synthetic rows and tmp_path media only for v1.3 normal-template export evidence."
patterns-established:
  - "Phase-level template/export regressions inspect generated artifacts, not only in-memory constants."
requirements-completed: [TMPL-01, TMPL-02, TMPL-03]
duration: 18min
completed: 2026-05-13
---

# Phase 19 Plan 03: Integrated Normal Template Export Contract Evidence Summary

**Synthetic integration tests now prove normal APKG/CSV/TSV exports omit `Front of Card`, carry responsive sentence-audio layout CSS, and leave highlight/manual/phonetics templates isolated.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-05-13T17:52:00Z
- **Completed:** 2026-05-13T18:10:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Added APKG inspection coverage for the normal note model's field list, template references, and responsive CSS selectors.
- Added CSV/TSV import metadata assertions for the revised normal header order and exported row values.
- Added source-profile isolation coverage for highlight/manual note models and Russian phoneme note fields/references.

## Task Commits

Each task was committed atomically:

1. **Task 1: Prove normal APKG/CSV/TSV revised contract and layout evidence per TMPL-01/TMPL-02** - `f7b9ad9` (test evidence)
2. **Task 2: Prove highlight and phonetics isolation per TMPL-03** - `4d11c39` (test evidence)

## Files Created/Modified

- `tests/integration/test_v13_normal_template_export_contract.py` - New synthetic integration evidence for normal artifacts, responsive CSS, highlight/manual isolation, and phonetics isolation.

## Decisions Made

- Kept integration evidence synthetic and local to `tmp_path`, avoiding private APKG audit reports or deck excerpts.

## Deviations from Plan

None - plan scope was executed as written.

## TDD Gate Compliance

- Task 1 integration tests passed immediately because plans 19-01 and 19-02 had already implemented the normal export/template behavior. The evidence was still committed as a test-only task commit.
- Task 2 test assertions were corrected before commit to match existing highlight and phonetics contracts (`highlight_card` uses generic `.card` markup, and phonetics intentionally has its own `Example Sentence`/`word_audio` fields). The final committed tests passed.

## Known Stubs

None.

## Threat Flags

None - new tests use only synthetic rows and temporary media under `tmp_path`.

## Issues Encountered

- The first combined isolation verification timed out at 120 seconds after partial failures; re-running with corrected assertions and a 300-second timeout passed in 28 seconds.

## User Setup Required

None - no external service configuration required.

## Verification

- `python -m pytest tests/integration/test_v13_normal_template_export_contract.py -q` → 3 passed after Task 1 evidence
- `python -m pytest tests/integration/test_v13_normal_template_export_contract.py tests/integration/test_highlight_export_artifacts.py tests/integration/test_russian_phoneme_template_refresh_flow.py -q` → 10 passed

## Next Phase Readiness

Phase 19 has integrated evidence for TMPL-01, TMPL-02, and TMPL-03 and can proceed to phase verification.

## Self-Check: PASSED

- Created file exists: `tests/integration/test_v13_normal_template_export_contract.py`.
- Task commits found: `f7b9ad9`, `4d11c39`.

---
*Phase: 19-normal-card-export-and-responsive-template*
*Completed: 2026-05-13*
