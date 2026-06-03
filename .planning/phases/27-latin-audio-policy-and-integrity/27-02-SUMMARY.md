---
phase: 27-latin-audio-policy-and-integrity
plan: 02
subsystem: services
tags: [latin, audio, espeak-ng, samples, tdd]
requires:
  - phase: 27-latin-audio-policy-and-integrity
    provides: Latin audio artifact metadata contracts from Plan 27-01
provides:
  - Local eSpeak NG Latin adapter with injectable subprocess runner
  - Deterministic representative Latin audio sample manifest generation
  - Azure multilingual experimental candidate metadata with blocked Latin caveat
affects: [phase-27, playback-review, latin-audio-policy]
tech-stack:
  added: []
  patterns: [subprocess runner injection, sanitized native-tool errors, local-only sample generation]
key-files:
  created:
    - src/multilang/services/espeak_ng_speech_adapter.py
    - src/multilang/services/latin_audio_samples.py
    - tests/services/test_espeak_ng_speech_adapter.py
    - tests/services/test_latin_audio_samples.py
  modified: []
key-decisions:
  - "eSpeak NG `la` is the only locally synthesizeable Latin candidate for playback review; Azure multilingual remains blocked without a verified native Classical Latin/`la` locale."
  - "Sample generation is local-only and does not contact Azure or any network provider."
patterns-established:
  - "Native TTS tools are wrapped behind injectable runners so tests remain subprocess-free and deterministic."
  - "Sample manifest paths are repository-relative `.multilang` paths, not absolute workstation paths."
requirements-completed: [AUD-01, AUD-03]
duration: 7min
completed: 2026-06-03
---

# Phase 27 Plan 02: eSpeak NG Sample Generation Summary

**Local eSpeak NG Latin sample synthesis adapter with representative AUD-01 metadata and explicit Azure blocked caveat**

## Performance

- **Duration:** 7 min
- **Started:** 2026-06-03T18:14:50Z
- **Completed:** 2026-06-03T18:22:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `EspeakNgSpeechAdapter` with version discovery, Latin voice detection, `-v la -s 135 -w` WAV synthesis, and sanitized fail-closed native-tool errors.
- Added deterministic representative sample manifest generation for `virum`, `puella`, `caesar`, `cicero`, `veni`, `quae`, `cum`, `Romae`, and `Arma virumque cano.`.
- Recorded Azure multilingual as an experimental blocked candidate with the public reason that no verified native Classical Latin/`la` Azure TTS locale is available.

## Task Commits

Each task was committed atomically using a combined TDD sequence for the adapter and sample manifest behavior:

1. **Tasks 1-2 RED: eSpeak adapter and representative sample behavior** - `1232967` (test)
2. **Tasks 1-2 GREEN: eSpeak adapter and sample manifest implementation** - `c7c4788` (feat)

**Plan metadata:** pending final metadata commit

## Files Created/Modified

- `src/multilang/services/espeak_ng_speech_adapter.py` - Local eSpeak NG adapter with version/voice discovery and WAV synthesis.
- `src/multilang/services/latin_audio_samples.py` - Representative sample manifest generator using Plan 27-01 metadata contracts.
- `tests/services/test_espeak_ng_speech_adapter.py` - Subprocess-free adapter tests using fake runners.
- `tests/services/test_latin_audio_samples.py` - Provider comparison and sample metadata tests.

## Decisions Made

- Kept eSpeak NG sample synthesis separate from `AudioSynthesisService` so Classical Latin does not enter the modern-language Azure voice registry.
- Used `classical_approx` as the sample pronunciation policy, pending human playback review.
- Kept Azure multilingual blocked rather than reviewable by default because no concrete verified Latin Azure sample files were supplied.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The local runner does not currently have `espeak-ng` on `PATH`; focused tests pass with fake runners, but real sample WAV generation could not be performed in this environment.

## User Setup Required

- Install eSpeak NG 1.52+ and ensure `espeak-ng` is on `PATH` before a human playback review can approve `espeak-ng/la/classical_approx`.

## Known Stubs

None.

## Auth Gates

None.

## Threat Flags

None.

## Next Phase Readiness

- Plan 27-03 can use `generate_latin_audio_sample_manifest()` when eSpeak NG is installed.
- Because this environment lacks eSpeak NG, the playback checkpoint cannot produce real WAV files here and should be treated as a human-action/setup blocker before approval.

## Self-Check: PASSED

- Verified `src/multilang/services/espeak_ng_speech_adapter.py` exists.
- Verified `src/multilang/services/latin_audio_samples.py` exists.
- Verified `tests/services/test_espeak_ng_speech_adapter.py` exists.
- Verified `tests/services/test_latin_audio_samples.py` exists.
- Verified commits `1232967` and `c7c4788` exist in git history.
- Verified `python -m pytest tests/services/test_latin_audio_samples.py tests/services/test_espeak_ng_speech_adapter.py -q` passes: 8 passed.
- Checked optional real sample generation: `espeak-ng` is not on `PATH` in this environment.

---
*Phase: 27-latin-audio-policy-and-integrity*
*Completed: 2026-06-03*
