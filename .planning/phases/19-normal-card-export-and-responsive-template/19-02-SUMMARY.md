---
phase: 19-normal-card-export-and-responsive-template
plan: 02
subsystem: templates
tags: [anki, responsive-css, sentence-audio, normal-card]
requires:
  - phase: 19-normal-card-export-and-responsive-template
    provides: plan 19-01 revised normal field contract without `Front of Card`
provides:
  - Normal example sentence/audio sibling row markup
  - Responsive flex CSS for `sentence_audio` beside `Example Sentence`
  - Regression assertions preserving hidden/revealed Translation behavior
affects: [normal-card-template, apkg-model-css, phase-19]
tech-stack:
  added: []
  patterns: [bounded flex row with min-width zero text child]
key-files:
  created: []
  modified:
    - src/multilang/templates/normal_card.md
    - tests/services/test_card_template_loader.py
    - tests/services/test_export_anki_package.py
key-decisions:
  - "Use a dedicated `.exampleSentenceLine` flex row with separate text/audio child classes so the audio control stays beside the sentence without horizontal overflow."
patterns-established:
  - "Normal sentence/audio layout uses `.exampleSentenceText { flex: 1 1 auto; min-width: 0; }` plus fixed-size `.sentenceAudioButton`."
requirements-completed: [TMPL-02]
duration: 16min
completed: 2026-05-13
---

# Phase 19 Plan 02: Responsive Normal Sentence Audio Layout Summary

**Normal card example sentences and sentence audio now render as one responsive flex row while preserving hidden-front/back-revealed translations.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-05-13T17:36:00Z
- **Completed:** 2026-05-13T17:52:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Grouped `{{Example Sentence}}` and `{{sentence_audio}}` as sibling elements in `.exampleSentenceLine`.
- Added bounded flex CSS that lets sentence text wrap while keeping the audio button beside it.
- Added loader and APKG model CSS tests proving the responsive selectors are exported.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add normal example sentence/audio flex markup per TMPL-02** - `7c6ef90` (test RED), `4154b1b` (feat GREEN)
2. **Task 2: Add responsive CSS for beside-sentence audio per TMPL-02** - `c2394a6` (test RED), `7625731` (feat GREEN)

_Note: TDD tasks used separate failing-test and implementation commits._

## Files Created/Modified

- `src/multilang/templates/normal_card.md` - Added sentence/audio row markup and responsive flex CSS.
- `tests/services/test_card_template_loader.py` - Asserted row structure, translation reveal preservation, and responsive CSS.
- `tests/services/test_export_anki_package.py` - Asserted exported normal model CSS includes the responsive selectors.

## Decisions Made

- Used a dedicated flex row instead of reusing the existing word-audio class, keeping normal sentence-audio behavior explicit and testable.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Verification

- `python -m pytest tests/services/test_card_template_loader.py -q` → 16 passed
- `python -m pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py -q` → 34 passed

## Next Phase Readiness

Plan 19-03 can add integrated artifact evidence for the revised normal export field contract and responsive sentence/audio CSS while checking highlight and phonetics isolation.

## Self-Check: PASSED

- Modified files exist.
- Task commits found: `7c6ef90`, `4154b1b`, `c2394a6`, `7625731`.

---
*Phase: 19-normal-card-export-and-responsive-template*
*Completed: 2026-05-13*
