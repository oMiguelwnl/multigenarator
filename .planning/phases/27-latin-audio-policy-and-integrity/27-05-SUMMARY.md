---
phase: 27-latin-audio-policy-and-integrity
plan: 05
subsystem: cli-evidence
tags: [latin, audio, cli, evidence, tdd]
requires:
  - phase: 27-latin-audio-policy-and-integrity
    provides: Approved eSpeak NG Latin playback policy and full 50-card audio manifest from Plans 27-03 and 27-04.
provides:
  - Opt-in public Latin audio readiness summaries through the Latin MVP service and CLI.
  - Scanner-readable AUD-01 through AUD-04 evidence over committed assets and public summaries.
  - No-scope-creep evidence preserving modern-language routing and Phase 28 export boundaries.
affects: [28-latin-export-and-milestone-evidence, latin-audio-policy, latin-mvp-export]
tech-stack:
  added: []
  patterns: [aggregate-only CLI diagnostics, opt-in manifest loading, scanner-readable requirement maps]
key-files:
  created:
    - tests/integration/test_v20_latin_audio_evidence.py
  modified:
    - src/multilang/services/latin_mvp.py
    - src/multilang/cli.py
    - tests/services/test_latin_mvp.py
    - tests/cli/test_generate_latin_mvp_command.py
key-decisions:
  - "Latin audio readiness output is opt-in through --audio-json and contains aggregate counts only, not media paths or provider raw details."
  - "Phase 27 evidence uses committed source, curation, playback review, and audio manifest assets rather than mocks."
patterns-established:
  - "Latin MVP optional summaries are attached through include_*_summary flags so default startup remains provider-free and backward-compatible."
  - "Requirement evidence files expose a PHASE_27_REQUIREMENTS tuple and executable public-boundary assertions."
requirements-completed: [AUD-01, AUD-02, AUD-03, AUD-04]
duration: 6min
completed: 2026-06-08
---

# Phase 27 Plan 05: Audio Readiness CLI and Evidence Summary

**Opt-in Latin audio readiness JSON with scanner-readable AUD evidence over approved committed audio assets**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-08T17:00:26Z
- **Completed:** 2026-06-08T17:05:55Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `include_audio_summary` to `LatinMvpGenerationService.start()` and `audio_summary` to `LatinMvpStartResult` so audio readiness is loaded only when requested.
- Added `generate-latin-mvp --audio-json`, including coexistence with `--portuguese-json`, while default CLI output remains unchanged and does not load the audio manifest.
- Added scanner-readable Phase 27 evidence mapping AUD-01/AUD-02/AUD-03/AUD-04 to executable assertions over the real source pack, curation asset, playback review artifact, audio manifest, public CLI/service summaries, and Latin boundary checks.
- Verified public audio summary output exposes manifest/readiness counts but omits storage paths, raw provider responses, secrets, and absolute workstation paths.

## Task Commits

TDD was used for both tasks:

1. **Task 1: Add optional audio summary to service and CLI**
   - `2a00b44` test(27-05): add failing audio summary tests
   - `528fb83` feat(27-05): expose Latin audio readiness JSON
2. **Task 2: Add scanner-readable Phase 27 evidence and boundary checks**
   - `0863f70` test(27-05): add failing Phase 27 audio evidence gate
   - `625e512` test(27-05): add Phase 27 audio evidence

## Files Created/Modified

- `src/multilang/services/latin_mvp.py` - Optional audio manifest loader, public aggregate audio summary, and result attachment.
- `src/multilang/cli.py` - `generate-latin-mvp --audio-json` flag and combined optional summary output.
- `tests/services/test_latin_mvp.py` - Service tests for opt-in audio loading and public readiness counts.
- `tests/cli/test_generate_latin_mvp_command.py` - CLI tests for audio JSON, combined Portuguese/audio JSON, default stability, and approved audio gate summary counts.
- `tests/integration/test_v20_latin_audio_evidence.py` - Scanner-readable AUD evidence and no-scope-creep checks.

## Decisions Made

- Latin audio readiness is exposed as aggregate public metadata only: counts, provider/status tallies, and readiness status, with no media paths in CLI/service JSON.
- The audio summary derives readiness from the validated committed manifest via `summarize_latin_audio_manifest()` rather than caller-supplied flags.
- Phase 27 evidence keeps export implementation out of scope by asserting no Latin APKG/CSV/TSV artifacts or Latin export modules were introduced.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated stale review summary assertion after Plan 27-04 approved audio gates**
- **Found during:** Task 1 focused verification.
- **Issue:** `test_review_latin_mvp_summary_prints_gate_counts` still expected all audio gates to be `needs_review`, but Plan 27-04 legitimately approved all 50 audio gates.
- **Fix:** Updated the planned CLI test expectation to assert `"audio": {"approved": 50, "needs_review": 0, "rejected": 0}`.
- **Files modified:** `tests/cli/test_generate_latin_mvp_command.py`
- **Verification:** `python -m pytest tests/services/test_latin_mvp.py tests/cli/test_generate_latin_mvp_command.py -q` passed.
- **Committed in:** `528fb83`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The fix aligned existing focused verification with prior approved Phase 27 audio gate state and did not expand implementation scope.

## Issues Encountered

- Existing unrelated working-tree items remained untouched: deleted `newrole.md` and untracked `new2.md`.

## User Setup Required

None - no external service configuration required.

## Verification

- RED Task 1: `python -m pytest tests/services/test_latin_mvp.py tests/cli/test_generate_latin_mvp_command.py -q` → expected failures for missing `audio_manifest_loader`, missing `include_audio_summary`, missing `--audio-json`, plus the stale audio-gate assertion.
- GREEN Task 1: `python -m pytest tests/services/test_latin_mvp.py tests/cli/test_generate_latin_mvp_command.py -q` → `29 passed`.
- RED Task 2: `python -m pytest tests/integration/test_v20_latin_audio_evidence.py -q` → expected failing evidence gate.
- GREEN Task 2: `python -m pytest tests/integration/test_v20_latin_audio_evidence.py -q` → `6 passed`.
- Final: `python -m pytest tests/services/test_latin_mvp.py tests/cli/test_generate_latin_mvp_command.py tests/integration/test_v20_latin_audio_evidence.py -q` → `35 passed`.

## TDD Gate Compliance

- RED commits present: `2a00b44`, `0863f70`.
- GREEN commits present after RED: `528fb83`, `625e512`.
- No refactor commit was needed.

## Known Stubs

None. Stub scan found intentional optional `None` defaults for opt-in summaries, local aggregate count initializers, and test assertions for absent Phase 28 artifacts; none are learner-facing stub data.

## Auth Gates

None.

## Threat Flags

None.

## Next Phase Readiness

- Phase 28 can call `generate-latin-mvp --audio-json` or `LatinMvpGenerationService.start(..., include_audio_summary=True)` to inspect approved audio readiness before export.
- Phase 28 evidence can reuse `PHASE_27_REQUIREMENTS` and the committed audio evidence file as a dependency for v2.0 requirement coverage.

## Self-Check: PASSED

- Verified `src/multilang/services/latin_mvp.py` exists.
- Verified `src/multilang/cli.py` exists.
- Verified `tests/integration/test_v20_latin_audio_evidence.py` exists.
- Verified `.planning/phases/27-latin-audio-policy-and-integrity/27-05-SUMMARY.md` exists.
- Verified task commits exist in git history: `2a00b44`, `528fb83`, `0863f70`, `625e512`.
- Verified focused final test suite passed: `python -m pytest tests/services/test_latin_mvp.py tests/cli/test_generate_latin_mvp_command.py tests/integration/test_v20_latin_audio_evidence.py -q` → `35 passed`.

---
*Phase: 27-latin-audio-policy-and-integrity*
*Completed: 2026-06-08*
