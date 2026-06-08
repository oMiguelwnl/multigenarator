---
phase: 27-latin-audio-policy-and-integrity
plan: 03
review_artifact: latin-audio-playback-review
selected_provider: espeak-ng
selected_voice: la
pronunciation_policy: classical_approx
playback_review_status: approved
reviewer: user
reviewed_at: 2026-06-08T16:50:59Z
sample_manifest: .multilang/latin-audio-samples/latin-audio-samples.json
---

# Phase 27 Latin Audio Playback Review

This artifact records the blocking playback review decision for the Classical Latin MVP audio policy. It is intentionally fail-closed: later full-manifest generation must not treat Latin audio as approved unless `playback_review_status` is `approved` and the selected provider/voice/policy are explicitly recorded.

## Current Review Status

| Field | Value |
|---|---|
| selected_provider | espeak-ng |
| selected_voice | la |
| pronunciation_policy | classical_approx |
| playback_review_status | approved |
| reviewer | user |
| reviewed_at | 2026-06-08T16:50:59Z |
| blocking_reason | None; user approved playback with `approved espeak-ng classical_approx`. |

## Provider Candidates

| Provider | Voice | Pronunciation policy | Status | Caveat |
|---|---|---|---|---|
| espeak-ng | la | classical_approx | approved | User approved generated local WAV files for the 50-card Classical Latin MVP with the explicit `classical_approx` caveat. |
| azure-multilingual-experimental | multilingual-experimental | experimental_unverified | blocked | No verified native Classical Latin/`la` Azure TTS locale is available. |

## Representative Samples Required for Review

Sample manifest: `.multilang/latin-audio-samples/latin-audio-samples.json`

### Word Samples

| Text | Sample path | Status |
|---|---|---|
| virum | .multilang/latin-audio-samples/word-virum.wav | playback_approved |
| puella | .multilang/latin-audio-samples/word-puella.wav | playback_approved |
| caesar | .multilang/latin-audio-samples/word-caesar.wav | playback_approved |
| cicero | .multilang/latin-audio-samples/word-cicero.wav | playback_approved |
| veni | .multilang/latin-audio-samples/word-veni.wav | playback_approved |
| quae | .multilang/latin-audio-samples/word-quae.wav | playback_approved |
| cum | .multilang/latin-audio-samples/word-cum.wav | playback_approved |
| Romae | .multilang/latin-audio-samples/word-Romae.wav | playback_approved |

### Sentence Samples

| Text | Sample path | Status |
|---|---|---|
| Arma virumque cano. | .multilang/latin-audio-samples/sentence-1.wav | playback_approved |

## Human Playback Decision Fields

These fields must be updated only after real sample playback:

| Field | Value |
|---|---|
| approval_phrase | `approved espeak-ng classical_approx` |
| pronunciation_acceptability | Acceptable for the 50-card Classical Latin MVP as an approximate classical pronunciation policy, not a native/human-recorded pronunciation guarantee. |
| rejection_reason | None |
| fallback_caveats | Azure remains blocked without a verified native Classical Latin/`la` locale; eSpeak NG is approved only under `classical_approx` and should be replaced by human-recorded or better verified Latin audio if future quality requirements increase. |

## Verification Performed

- `PATH="$PATH:/c/Program Files/eSpeak NG" python -m pytest tests/services/test_latin_audio_samples.py tests/services/test_espeak_ng_speech_adapter.py -q` → passed (`10 passed`).
- Real sample generation with `generate_latin_audio_sample_manifest()` → generated 9 eSpeak NG 1.52.0 WAV samples and `.multilang/latin-audio-samples/latin-audio-samples.json`.
- Human playback review → approved via user response `approved espeak-ng classical_approx`.

## Policy Handoff

Later Phase 27 plans may treat eSpeak NG voice `la` with pronunciation policy `classical_approx` as the approved Latin MVP audio policy only when this artifact still records `playback_review_status=approved`, `selected_provider=espeak-ng`, `selected_voice=la`, and `pronunciation_policy=classical_approx`. Azure remains blocked unless a future review artifact verifies a native Classical Latin/`la` Azure voice.
