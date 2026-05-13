---
phase: 20-word-audio-integrity-gate
plan: 01
subsystem: audio-integrity
tags: [audio, validation, export-gate, pytest]
requires:
  - phase: 04
    provides: AudioAssetRecord and NormalizedTtsInput metadata contracts
provides:
  - Strict word-audio integrity helper for reusable audio validation
  - Deterministic AudioIntegrityError diagnostics for mismatched Word metadata
affects: [audio-generation, export-assembly, anki-export]
tech-stack:
  added: []
  patterns: [pure-service integrity checks, deterministic pytest fixtures]
key-files:
  created: [src/multilang/services/audio_integrity.py, tests/services/test_audio_integrity.py]
  modified: []
key-decisions:
  - "Word audio integrity is exact-match only; surrounding whitespace is stripped from caller input but stored audio metadata is not normalized."
patterns-established:
  - "Audio integrity helpers perform no repository, synthesis, or file-system IO."
requirements-completed: [AUD-01, AUD-02]
duration: 14min
completed: 2026-05-13
---

# Phase 20 Plan 01: Word Audio Integrity Contract Summary

**Strict word-audio integrity helper comparing exported Word against stored display text, TTS text, and provenance hash**

## Performance

- **Duration:** 14 min
- **Started:** 2026-05-13T17:30:00Z
- **Completed:** 2026-05-13T17:44:20Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `AudioIntegrityError`, `assert_word_audio_matches_word`, and `word_audio_matches_word` as a pure reusable service.
- Enforced exact matching for `asset.display_text`, `normalized_input.display_text`, `normalized_input.tts_text`, and `provenance.text_hash`.
- Added focused pytest coverage for happy path, wrong word metadata, stale hashes, accent-stripped synthesis text, empty Word, and sentence-audio substitution.

## Task Commits

1. **Task 1: Define exact word-audio match behavior per AUD-01** - `b489c76` (test), `f7e1dc9` (feat)
2. **Task 2: Preserve legitimate word normalization boundaries per AUD-01** - `b60bf11` (test)

## Files Created/Modified

- `src/multilang/services/audio_integrity.py` - Pure exact-match integrity gate for word audio assets.
- `tests/services/test_audio_integrity.py` - Deterministic coverage for strict matching and item-specific diagnostics.

## Decisions Made

- Stored audio metadata must match the exported `Word` exactly; no accent folding or synthesis-friendly rewriting is accepted by this integrity layer.

## Deviations from Plan

None - plan executed as written.

## Issues Encountered

- TDD red phase failed as expected because `multilang.services.audio_integrity` did not exist yet.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Next Phase Readiness

- Plan 20-02 can call the pure helper before reusing stored word audio.
- Plan 20-03 can raise `AudioIntegrityError` before export artifacts are written.

## Self-Check: PASSED

- Created files exist: `src/multilang/services/audio_integrity.py`, `tests/services/test_audio_integrity.py`.
- Commits exist: `b489c76`, `f7e1dc9`, `b60bf11`.
- Verification passed: `python -m pytest tests/services/test_audio_integrity.py -q` (8 passed).

---
*Phase: 20-word-audio-integrity-gate*
*Completed: 2026-05-13*
