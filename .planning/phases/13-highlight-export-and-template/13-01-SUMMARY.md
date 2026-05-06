---
phase: 13-highlight-export-and-template
plan: 01
subsystem: export-template
tags: [anki, templates, validation, highlights, pytest]
requires:
  - phase: 12-highlight-generation-audio-and-qa
    provides: Highlight card rows with word, IPA, definition, example sentence, audio, and blank Image
provides:
  - Dedicated highlight card front/back/CSS template
  - Source-profile-aware card template loader
  - Fail-closed exported-field reference validation for Anki templates
affects: [phase-13-apkg-export, highlight-export, anki-template-validation]
tech-stack:
  added: []
  patterns: [source-profile-driven template selection, regex-based Anki field reference validation, TDD contract tests]
key-files:
  created: [HIGHLIGHT_CARD_TEMPLATE.md, src/multilang/services/card_template_loader.py, tests/services/test_card_template_loader.py]
  modified: []
key-decisions:
  - "Keep normal frequency and word-list templates on CARD_TEMPLATE.md while routing kindle-highlights to HIGHLIGHT_CARD_TEMPLATE.md through SourceProfile.template_name."
  - "Validate template references against the resolved export field tuple and allow only FrontSide as a non-field Anki helper."
patterns-established:
  - "Template loading is source-profile-driven instead of hard-coded at export call sites."
  - "Highlight template validation fails closed for Translation, private highlight provenance, and dangling field references."
requirements-completed: [EXPORT-02, EXPORT-03]
duration: 3min
completed: 2026-05-06
---

# Phase 13 Plan 01: Highlight Template and Loader Summary

**Dedicated highlight Anki template with source-profile-aware loading and fail-closed field-reference validation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-06T17:24:54Z
- **Completed:** 2026-05-06T17:27:35Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `CardTemplate`, `load_card_template`, and `validate_template_references` so template selection follows `get_source_profile(source_type).template_name`.
- Created `HIGHLIGHT_CARD_TEMPLATE.md` with prompt-side word/IPA/audio/sentence/image front content and a Definition-only answer area after `{{FrontSide}}`.
- Added focused contract tests proving normal templates still allow `Translation` while highlight templates reject `Translation`, private provenance, source paths, and unknown fields.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define source-aware template loader contracts**
   - `2e3ea9d` test: failing loader/validation contracts
   - `4d95c8c` feat: source-aware loader implementation
2. **Task 2: Author dedicated highlight front/back/CSS template**
   - `e64c848` test: failing highlight template contracts
   - `b28d14f` feat: dedicated highlight template

**Plan metadata:** pending final docs commit

## Files Created/Modified

- `HIGHLIGHT_CARD_TEMPLATE.md` - Dedicated highlight front/back/CSS template with Multilang-blue responsive styling.
- `src/multilang/services/card_template_loader.py` - Source-profile-aware markdown template parser and exported-field reference validator.
- `tests/services/test_card_template_loader.py` - TDD contract tests for normal/highlight loading, validation failures, and highlight template content/CSS.

## Decisions Made

- Normal `frequency` and `word-list` cards continue to load `CARD_TEMPLATE.md`; only `kindle-highlights` routes to `HIGHLIGHT_CARD_TEMPLATE.md`.
- Template validation uses the resolved export field tuple from `export_field_names_for_source_type`, with `FrontSide` as the only allowed non-field helper.
- Multiple definitions are handled in the highlight back template by splitting exported `<br>` separators into a bullet list without introducing private fields.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## TDD Gate Compliance

- RED gate commits present: `2e3ea9d`, `e64c848`
- GREEN gate commits present after RED: `4d95c8c`, `b28d14f`

## Verification

- `python -m pytest tests/services/test_card_template_loader.py -q` — 12 passed

## Next Phase Readiness

- Plan 13-02 can wire `load_card_template(source_type="kindle-highlights")` into APKG model construction.
- The validator is ready for downstream export gates to reject dangling or private highlight template references before packaging.

## Self-Check: PASSED

- Found created files: `HIGHLIGHT_CARD_TEMPLATE.md`, `src/multilang/services/card_template_loader.py`, `tests/services/test_card_template_loader.py`, and this summary.
- Found task commits: `2e3ea9d`, `4d95c8c`, `e64c848`, `b28d14f`.

---
*Phase: 13-highlight-export-and-template*
*Completed: 2026-05-06*
