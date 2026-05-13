---
phase: 20-word-audio-integrity-gate
plan: 03
subsystem: export-audio-integrity
tags: [audio, export-gate, validation, pytest]
requires:
  - phase: 20-01
    provides: Strict word-audio integrity helper
  - phase: 20-02
    provides: Generation-time cache repair for mismatched word audio
provides:
  - Assembly-time block for unrepaired word-audio mismatches before card snapshots persist
  - Runtime APKG/CSV/TSV export block for corrupted persisted word-audio metadata
affects: [export-assembly, runtime-export, apkg-export, tabular-export]
tech-stack:
  added: []
  patterns: [service-boundary validation, runtime persisted-snapshot revalidation]
key-files:
  created: []
  modified:
    - src/multilang/services/assemble_export_cards.py
    - src/multilang/runtime.py
    - tests/services/test_assemble_export_cards.py
    - tests/integration/test_export_job_flow.py
key-decisions:
  - "Unrepaired word-audio mismatches are hard export blockers at both snapshot assembly and persisted runtime export boundaries."
requirements-completed: [AUD-01, AUD-02]
duration: 8min
completed: 2026-05-13
---

# Phase 20 Plan 03: Export Word-Audio Integrity Gate Summary

**Assembly and runtime export gates that block APKG/CSV/TSV artifacts when persisted `word_audio` no longer exactly matches `Word`**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-13T17:48:01Z
- **Completed:** 2026-05-13T17:56:30Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added assembly-time validation so normal/frequency card snapshots cannot be persisted when WORD audio metadata mismatches the lexical lemma used for exported `Word`.
- Added runtime persisted-snapshot validation before media index construction, including HTML-unescaped `row.word` matching for existing APKG/CSV/TSV exports.
- Added focused service and integration coverage proving clear `word_audio`/`Word` diagnostics and preserving missing-media behavior for otherwise valid assets.

## Task Commits

1. **Task 1: Block mismatched word audio during export-card assembly per AUD-01/AUD-02** - `66f5290` (test), `d940f81` (feat)
2. **Task 2: Block mismatched persisted snapshots during APKG/CSV/TSV export per AUD-02** - `eef580d` (test), `7c251d0` (feat)

## Files Created/Modified

- `src/multilang/services/assemble_export_cards.py` - Wraps `AudioIntegrityError` as `AssembleExportCardsError` before snapshot persistence.
- `src/multilang/runtime.py` - Revalidates persisted WORD audio against exported `row.word` before APKG/CSV/TSV media handling.
- `tests/services/test_assemble_export_cards.py` - Covers pre-persist snapshot blocking and diagnostics.
- `tests/integration/test_export_job_flow.py` - Covers persisted WORD audio corruption across APKG, CSV, and TSV export commands.

## Decisions Made

- Remaining word-audio mismatches after generation-time repair are not recoverable at export time and fail closed before writing learner-facing artifacts.

## Deviations from Plan

None - plan executed as written.

## Issues Encountered

- TDD red phases failed as expected before assembly/runtime gates were implemented.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Threat Flags

None - export validation touched the trust boundaries already listed in the plan threat model.

## Next Phase Readiness

- Phase 20 now provides both repair-on-generation and fail-closed export gates for AUD-01/AUD-02.
- Phase 21 can use the focused test evidence as milestone validation input.

## Self-Check: PASSED

- Modified files exist: `src/multilang/services/assemble_export_cards.py`, `src/multilang/runtime.py`, `tests/services/test_assemble_export_cards.py`, `tests/integration/test_export_job_flow.py`.
- Commits exist: `66f5290`, `d940f81`, `eef580d`, `7c251d0`.
- Verification passed: `python -m pytest tests/integration/test_export_job_flow.py tests/services/test_assemble_export_cards.py tests/services/test_generate_audio_items.py tests/services/test_audio_integrity.py -q` (38 passed).

---
*Phase: 20-word-audio-integrity-gate*
*Completed: 2026-05-13*
