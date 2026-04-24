---
phase: 04-audio-synthesis
plan: 05
subsystem: runtime
tags: [audio, azure-speech, runtime, cli, integration-testing]
requires:
  - phase: 04-audio-synthesis
    provides: shipped audio orchestration, deterministic voice selection, and persisted audio reuse from Plans 04-01 through 04-04
provides:
  - Azure Speech SDK adapter with cached live voice inventory lookup
  - shipped runtime wiring that uses Azure synthesis by default instead of fake mp3 payload bytes
  - CLI and integration coverage for fallback, failure visibility, and reusable playable media
affects: [phase-04-verification, phase-05-export, runtime]
tech-stack:
  added: [azure-cognitiveservices-speech]
  patterns: [provider-backed runtime adapter, cached Azure voice inventory, visible failed-audio records]
key-files:
  created:
    - .planning/phases/04-audio-synthesis/04-05-SUMMARY.md
    - .planning/phases/04-audio-synthesis/deferred-items.md
    - src/multilang/services/azure_speech_adapter.py
    - tests/services/test_azure_speech_adapter.py
  modified:
    - pyproject.toml
    - uv.lock
    - src/multilang/runtime.py
    - src/multilang/services/audio_synthesis.py
    - tests/services/test_audio_synthesis.py
    - tests/cli/test_generate_command.py
    - tests/integration/test_audio_job_flow.py
key-decisions:
  - "Keep Azure Speech provider logic in a dedicated adapter so runtime orchestration stays testable and fallback policy remains enforced by the existing voice registry."
  - "Return failed audio assets instead of crashing when the provider boundary errors so operators still see explicit failure counts on the shipped path."
patterns-established:
  - "The default runtime now instantiates AzureSpeechAdapter unless a test-specific adapter is injected."
  - "Azure voice inventory is fetched once per adapter instance and fed back into deterministic registry selection rather than relying on provider defaults."
requirements-completed: [AUDI-01, AUDI-02]
duration: 28 min
completed: 2026-04-24
---

# Phase 4 Plan 5: Azure runtime audio gap closure Summary

**The shipped `multilang generate` path now uses an Azure Speech adapter for real word and sentence audio, while fallback and failure remain visible and reusable media stays deterministic.**

## Performance

- **Duration:** 28 min
- **Started:** 2026-04-24T16:05:00Z
- **Completed:** 2026-04-24T16:33:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Added a real Azure Speech SDK adapter with cached voice inventory lookup and file-backed SSML synthesis.
- Replaced the shipped runtime stub so the default path now builds the Azure adapter instead of writing fake bytes to `.mp3` files.
- Added CLI and integration coverage proving fallback counting, explicit failed-audio outcomes, and resume-safe reuse of playable media.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add the real Azure Speech adapter and deterministic voice inventory lookup** - `0207e97` (test), `4019b69` (feat)
2. **Task 2: Replace the shipped runtime stub and prove default-path playable media behavior** - `3c744f3` (test), `39c5e65` (feat)

**Plan metadata:** pending local summary/docs commit

## Files Created/Modified
- `src/multilang/services/azure_speech_adapter.py` - wraps Azure Speech SDK synthesis and voice inventory lookup behind the existing adapter protocol.
- `src/multilang/runtime.py` - makes the shipped runtime use `AzureSpeechAdapter` by default.
- `src/multilang/services/audio_synthesis.py` - turns adapter exceptions into explicit failed audio records instead of crashing the job.
- `pyproject.toml` and `uv.lock` - add the Azure Speech SDK dependency to the shipped environment.
- `tests/services/test_azure_speech_adapter.py` - locks voice-list caching, file synthesis, and missing-credential behavior.
- `tests/services/test_audio_synthesis.py` - verifies provider errors become failed assets.
- `tests/cli/test_generate_command.py` - proves default runtime fallback and failed-audio counters without injected stub adapters.
- `tests/integration/test_audio_job_flow.py` - proves the default runtime path writes non-zero audio files and reuses them on resume.

## Decisions Made
- Used Azure's voices-list endpoint to provide runtime availability data while keeping actual selection logic in the in-repo voice registry.
- Kept missing-voice and synthesis-error outcomes as persisted failed assets so operators can distinguish real failures from reuse or fallback.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Converted provider exceptions into failed audio assets**
- **Found during:** Task 1 (Add the real Azure Speech adapter and deterministic voice inventory lookup)
- **Issue:** A canceled or failing provider call would have bubbled out of `AudioSynthesisService` and aborted the shipped job instead of recording a visible failed asset.
- **Fix:** Wrapped adapter synthesis calls in `AudioSynthesisService` and converted exceptions into failed `AudioAssetRecord` results with preserved identity and fallback metadata.
- **Files modified:** `src/multilang/services/audio_synthesis.py`, `tests/services/test_audio_synthesis.py`
- **Verification:** `uv run pytest tests/services/test_azure_speech_adapter.py tests/services/test_audio_synthesis.py tests/cli/test_generate_command.py tests/integration/test_audio_job_flow.py -q`
- **Committed in:** `4019b69`

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** The fix was required to make provider failures visible and non-destructive on the shipped runtime path. No scope creep beyond the planned Azure gap closure.

## Issues Encountered
- `gsd-sdk` is unavailable in this environment, so automated state-handler updates could not be run.
- A nearby regression sweep found pre-existing text-runtime test failures outside Plan 04-05; they were logged to `deferred-items.md` and left untouched.

## User Setup Required

Azure Speech still requires manual credentials for live synthesis:
- `MULTILANG_AZURE_SPEECH_KEY`
- `MULTILANG_AZURE_SPEECH_REGION`

## Next Phase Readiness
- Phase 4's shipped runtime gap is closed: default audio generation now reaches Azure-backed provider logic, keeps fallback explicit, and preserves reuse.
- Phase 5 can consume persisted audio storage paths and provider-backed media instead of placeholder `.mp3` bytes.

## Self-Check: PASSED

- Found `.planning/phases/04-audio-synthesis/04-05-SUMMARY.md`
- Found task commit `0207e97`
- Found task commit `4019b69`
- Found task commit `3c744f3`
- Found task commit `39c5e65`
