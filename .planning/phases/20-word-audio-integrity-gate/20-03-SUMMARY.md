---
phase: 20-word-audio-integrity-gate
plan: 03
subsystem: export-validation
tags: [audio, export, validation, cli, pytest]
requires:
  - phase: 20-01
    provides: Strict word-audio integrity helper
  - phase: 20-02
    provides: Generation-time cache mismatch repair
provides:
  - Assembly-time block for unrepaired word-audio mismatches
  - Runtime APKG/CSV/TSV export block for persisted word-audio drift
affects: [export-assembly, runtime-export, cli-export]
tech-stack:
  added: []
  patterns: [assembly service error boundary, runtime persisted metadata revalidation]
key-files:
  created: []
  modified: [src/multilang/services/assemble_export_cards.py, src/multilang/runtime.py, tests/services/test_assemble_export_cards.py, tests/integration/test_export_job_flow.py]
key-decisions:
  - "Assembly validates word audio against lexical_candidate.lemma, matching the exported normal card Word."
  - "Runtime export refreshes persisted audio rows before validating snapshots so APKG/CSV/TSV gates catch external metadata drift."
patterns-established:
  - "Export gates validate text metadata before media basename/file existence checks."
requirements-completed: [AUD-01, AUD-02]
duration: 7min
completed: 2026-05-13
---

# Phase 20 Plan 03: Export Word Audio Gate Summary

**Assembly and runtime export gates that block APKG, CSV, and TSV artifacts when word_audio metadata no longer matches Word**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-13T17:48:01Z
- **Completed:** 2026-05-13T17:55:23Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added assembly-time `assert_word_audio_matches_word` validation before export card snapshots are persisted.
- Added runtime persisted-snapshot validation before media indexing so existing card snapshots cannot export stale word audio.
- Added APKG/CSV/TSV CLI integration evidence that corrupts persisted WORD audio after snapshot creation and verifies export fails with `word_audio`/`Word` diagnostics.

## Task Commits

1. **Task 1: Block mismatched word audio during export-card assembly per AUD-01/AUD-02** - `66f5290` (test), `d940f81` (feat)
2. **Task 2: Block mismatched persisted snapshots during APKG/CSV/TSV export per AUD-02** - `eef580d` (test), `7c251d0` (feat)

## Files Created/Modified

- `src/multilang/services/assemble_export_cards.py` - Wraps word-audio integrity failures as `AssembleExportCardsError` before snapshot persistence.
- `src/multilang/runtime.py` - Revalidates persisted WORD audio against `row.word` before APKG/CSV/TSV export media indexing.
- `tests/services/test_assemble_export_cards.py` - Covers assembly block and highlight isolation.
- `tests/integration/test_export_job_flow.py` - Covers runtime export failure for APKG, CSV, and TSV after persisted audio metadata drift.

## Decisions Made

- Compare assembly word audio against `lexical_candidate.lemma`, not display form, because normal export `Word` is built from lemma.
- Refresh the runtime audio repository session before media index construction so validation reads current persisted metadata.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Refreshed runtime audio rows before export validation**
- **Found during:** Task 2 (runtime persisted snapshot export gate)
- **Issue:** The runtime service can keep a long-lived SQLAlchemy session, which may otherwise reuse stale audio rows and miss persisted metadata drift.
- **Fix:** Expire the audio repository session before preloading audio rows for export media indexing.
- **Files modified:** `src/multilang/runtime.py`
- **Verification:** `python -m pytest tests/integration/test_export_job_flow.py tests/services/test_assemble_export_cards.py tests/services/test_generate_audio_items.py tests/services/test_audio_integrity.py -q`
- **Committed in:** `7c251d0`

**Total deviations:** 1 auto-fixed (Rule 2 missing critical)
**Impact on plan:** Required for the runtime gate to enforce AUD-02 against persisted metadata, with no scope creep.

## Issues Encountered

- TDD red phase confirmed persisted APKG/CSV/TSV exports previously succeeded even after WORD audio metadata was corrupted.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Next Phase Readiness

- Phase 21 can include validation fixtures and milestone evidence over the completed word-audio integrity gates.

## Self-Check: PASSED

- Modified files exist: `src/multilang/services/assemble_export_cards.py`, `src/multilang/runtime.py`, `tests/services/test_assemble_export_cards.py`, `tests/integration/test_export_job_flow.py`.
- Commits exist: `66f5290`, `d940f81`, `eef580d`, `7c251d0`.
- Verification passed: `python -m pytest tests/integration/test_export_job_flow.py tests/services/test_assemble_export_cards.py tests/services/test_generate_audio_items.py tests/services/test_audio_integrity.py -q` (38 passed).

---
*Phase: 20-word-audio-integrity-gate*
*Completed: 2026-05-13*
