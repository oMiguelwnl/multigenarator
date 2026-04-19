---
phase: 02-input-decks-lexical-grounding
plan: 02
subsystem: lexical-ingestion
tags: [wordfreq, frequency-decks, lexical-grounding, pytest]
requires:
  - phase: 02-input-decks-lexical-grounding
    provides: typed lexical candidate contracts and persistence for Phase 2 ingestion
provides:
  - Deterministic `wordfreq`-backed candidate curation for supported deck languages
  - Explicit 1-1000, 1001-2000, and 2001-3000 level selection rules
  - Bounded backfill behavior that preserves 1000 items per level after rejections
affects: [word-list-grounding, cli-runtime, phase-2]
tech-stack:
  added: [wordfreq]
  patterns: [deterministic frequency curation, bounded rank-window backfill, TDD service coverage]
key-files:
  created: [src/multilang/services/frequency_decks.py, tests/services/test_frequency_decks.py, .planning/phases/02-input-decks-lexical-grounding/02-02-SUMMARY.md]
  modified: [pyproject.toml, uv.lock, .planning/STATE.md, .planning/ROADMAP.md, .planning/REQUIREMENTS.md]
key-decisions:
  - "Use wordfreq as the deterministic ranked source, then apply mandatory token curation before any item becomes a study candidate."
  - "Keep level windows explicit at 1-1000, 1001-2000, and 2001-3000 while allowing bounded post-window backfill for rejected items."
patterns-established:
  - "Frequency ingestion services return LexicalCardCandidate seed records with frequency metadata preserved from the ranking source."
  - "Noise filtering and rank-window selection live in one service instead of CLI-specific logic."
requirements-completed: [DECK-02, LEX-01]
duration: 4 min
completed: 2026-04-19
---

# Phase 2 Plan 2: Deterministic frequency deck curation Summary

**Deterministic `wordfreq` deck curation with explicit three-level rank windows, teachability filters, and bounded backfill metadata.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-19T16:15:02Z
- **Completed:** 2026-04-19T16:19:32Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added a `wordfreq`-backed iterator that rejects digits, web noise, malformed abbreviations, symbol-heavy tokens, and title-cased proper-name candidates.
- Built deterministic level selectors for ranks 1-1000, 1001-2000, and 2001-3000.
- Preserved `frequency_rank` and `frequency_level` on lexical seed records while backfilling rejected candidates under a bounded scan limit.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add the curated frequency candidate iterator** - `0eed32a` (test), `a5f0db7` (feat)
2. **Task 2: Build the 3-level selector with backfill support** - `0647fe0` (test), `125b4a4` (feat)

**Plan metadata:** `docs(02-02)` metadata commit recorded in git history

## Files Created/Modified
- `pyproject.toml` - Adds `wordfreq` as the ranked frequency source dependency.
- `uv.lock` - Locks the resolved runtime dependency set including `wordfreq`.
- `src/multilang/services/frequency_decks.py` - Implements ranked token curation plus level/deck builders.
- `tests/services/test_frequency_decks.py` - Locks deterministic filtering, rank windows, and backfill behavior with TDD coverage.

## Decisions Made
- Use `wordfreq.iter_wordlist()` as the single deterministic source for ranked bootstrap candidates so curation stays stable across runs.
- Represent curated deck items as `LexicalCardCandidate` seed records immediately so later grounding and persistence stages inherit the same metadata shape.
- Keep backfill bounded by `scan_limit` so rejection handling cannot turn into unbounded iteration.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The environment did not expose the repo `grep`/`glob` wrappers or `gsd-sdk`, so acceptance checks and planning-file updates were performed with the available local tools while preserving the plan outputs.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 2 now has a deterministic built-in frequency deck path that can feed the remaining lexical grounding and CLI integration work.
- Ready for `02-03-PLAN.md` custom word-list parsing and trust-first lexical grounding.

## Verification Results
- `uv run pytest tests/services/test_frequency_decks.py -q` ✅

## Self-Check: PASSED
- Found summary file: `.planning/phases/02-input-decks-lexical-grounding/02-02-SUMMARY.md`
- Found task commits: `0eed32a`, `a5f0db7`, `0647fe0`, `125b4a4`

---
*Phase: 02-input-decks-lexical-grounding*
*Completed: 2026-04-19*
