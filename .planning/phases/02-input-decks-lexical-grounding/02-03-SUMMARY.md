---
phase: 02-input-decks-lexical-grounding
plan: 03
subsystem: lexicon
tags: [word-list, kaikki, lexical-grounding, pytest]
requires:
  - phase: 01-job-orchestration-recovery
    provides: single-command generation flow with persisted job/item state
provides:
  - Plain-text word-list parsing with explicit blank-line and duplicate diagnostics
  - Cached Kaikki lookup indexes for fixture-backed authoritative lexical data
  - Trust-first lexical grounding with English definitions and pending/backfill outcomes
affects: [phase-02-runtime-integration, phase-03-sentence-quality]
tech-stack:
  added: []
  patterns: [fixture-backed lexical cache indexes, trust-first grounding provenance]
key-files:
  created:
    - src/multilang/services/word_list_parser.py
    - src/multilang/services/kaikki_lookup.py
    - src/multilang/services/lexical_grounding.py
    - tests/services/test_word_list_parser.py
    - tests/services/test_kaikki_lookup.py
    - tests/services/test_lexical_grounding.py
  modified:
    - src/multilang/settings.py
    - src/multilang/domain/lexicon.py
key-decisions:
  - "Keep word-list parsing deterministic by preserving submitted text while deduping on a whitespace-normalized casefolded key."
  - "Model missing custom lookups as pending and missing frequency lookups as backfill_required so requested items are never silently swapped."
patterns-established:
  - "Fixture-first lexical tests: cache and grounding services use tiny gzipped JSONL fixtures instead of live downloads."
  - "Trust-first grounding: authoritative IPA only, English definitions joined with <br>, and provenance records for missing data."
requirements-completed: [DECK-03, LEX-01, LEX-02, LEX-03]
duration: 4 min
completed: 2026-04-19
---

# Phase 2 Plan 3: Plain-text word-list parsing, cached Kaikki lookup, and trust-first lexical grounding Summary

**Custom word lists now parse deterministically, cached Kaikki extracts ground authoritative lexical data locally, and missing lookups stay pending or trigger frequency backfill instead of silent substitution.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-19T16:23:58Z
- **Completed:** 2026-04-19T16:28:07Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added a UTF-8-only plain-text parser that preserves submitted forms, trims display forms, normalizes dedupe keys, and emits explicit blank/duplicate warnings.
- Added a local Kaikki index builder/reader so tests and runtime lookup can use cached fixture data without live network downloads.
- Implemented trust-first lexical grounding with English-only definitions, authoritative-only IPA handling, and distinct pending vs. backfill-required failure behavior.

## Task Commits

Each task was committed atomically:

1. **Task 1: Parse plain-text word lists and bootstrap cached Kaikki lookup** - `a5bb434`, `ba67e62` (test, feat)
2. **Task 2: Implement trust-first lexical grounding and pending-item behavior** - `8c0f9fa`, `0b1ead2` (test, feat)

**Plan metadata:** _pending at summary creation time_

## Files Created/Modified
- `src/multilang/settings.py` - adds configurable `lexicon_data_dir` for cached lexical assets
- `src/multilang/domain/lexicon.py` - adds `BACKFILL_REQUIRED` grounding status to preserve failure semantics
- `src/multilang/services/word_list_parser.py` - parses UTF-8 word lists with structured diagnostics
- `src/multilang/services/kaikki_lookup.py` - builds and queries cached Kaikki indexes from gzipped JSONL extracts
- `src/multilang/services/lexical_grounding.py` - grounds custom and frequency inputs with provenance-aware trust-first rules
- `tests/services/test_word_list_parser.py` - locks parser preservation and warning behavior
- `tests/services/test_kaikki_lookup.py` - locks fixture-backed cache build, lookup, and refresh behavior
- `tests/services/test_lexical_grounding.py` - locks display-form selection, definition formatting, IPA provenance, and pending/backfill semantics

## Decisions Made
- Kept lookup normalization shared between cache indexing and grounding so parser item keys and lexical lemma keys stay deterministic.
- Preferred lexical display forms only when they differ from the bare lemma, which preserves study-critical markers like reflexive forms without overwriting ordinary submitted display text.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Extended the lexical status contract with `backfill_required`**
- **Found during:** Task 2 (Implement trust-first lexical grounding and pending-item behavior)
- **Issue:** The existing lexical status enum could not represent the required distinction between pending custom-list failures and frequency candidates that must be backfilled.
- **Fix:** Added `GroundingStatus.BACKFILL_REQUIRED` and used it in the grounding service for frequency lookup misses.
- **Files modified:** `src/multilang/domain/lexicon.py`, `src/multilang/services/lexical_grounding.py`
- **Verification:** `uv run pytest tests/services/test_lexical_grounding.py -q`
- **Committed in:** `0b1ead2`

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Required for correctness; it preserved the plan's trust-first failure semantics without expanding scope.

## Issues Encountered
- `gsd-sdk` and the dedicated search helpers were unavailable in this environment, so summary/state/roadmap updates and acceptance checks were completed with equivalent direct file edits and verification commands.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 2 now has the parser, lexical cache, and grounding primitives needed to wire lexical ingestion into the shipped CLI/runtime path in Plan 02-04.
- Integration still needs to connect these services to persisted lexical candidates and end-to-end generation flow.

## Self-Check: PASSED

- Found `.planning/phases/02-input-decks-lexical-grounding/02-03-SUMMARY.md` on disk.
- Verified commits `a5bb434`, `ba67e62`, `8c0f9fa`, and `0b1ead2` exist in `git log --oneline --all`.
