---
phase: 27-latin-audio-policy-and-integrity
plan: 03
review_artifact: latin-audio-playback-review
selected_provider: blocked
selected_voice: null
pronunciation_policy: classical_approx
playback_review_status: blocked
reviewer: pending-human-playback
reviewed_at: null
sample_manifest: .multilang/latin-audio-samples/latin-audio-samples.json
---

# Phase 27 Latin Audio Playback Review

This artifact records the blocking playback review decision for the Classical Latin MVP audio policy. It is intentionally fail-closed: later full-manifest generation must not treat Latin audio as approved unless `playback_review_status` is `approved` and the selected provider/voice/policy are explicitly recorded.

## Current Review Status

| Field | Value |
|---|---|
| selected_provider | blocked |
| selected_voice | null |
| pronunciation_policy | classical_approx |
| playback_review_status | blocked |
| reviewer | pending-human-playback |
| reviewed_at | null |
| blocking_reason | eSpeak NG binary is not available on PATH in the execution environment, so representative WAV files could not be generated for human playback. |

## Provider Candidates

| Provider | Voice | Pronunciation policy | Status | Caveat |
|---|---|---|---|---|
| espeak-ng | la | classical_approx | blocked | Candidate for review only after `espeak-ng` is installed and sample WAV files are generated. |
| azure-multilingual-experimental | multilingual-experimental | experimental_unverified | blocked | No verified native Classical Latin/`la` Azure TTS locale is available. |

## Representative Samples Required for Review

The intended sample manifest path is `.multilang/latin-audio-samples/latin-audio-samples.json`. It could not be generated in this run because the native `espeak-ng` binary is unavailable.

### Word Samples

| Text | Expected sample path | Status |
|---|---|---|
| virum | .multilang/latin-audio-samples/word-virum.wav | not_generated_missing_espeak_ng |
| puella | .multilang/latin-audio-samples/word-puella.wav | not_generated_missing_espeak_ng |
| caesar | .multilang/latin-audio-samples/word-caesar.wav | not_generated_missing_espeak_ng |
| cicero | .multilang/latin-audio-samples/word-cicero.wav | not_generated_missing_espeak_ng |
| veni | .multilang/latin-audio-samples/word-veni.wav | not_generated_missing_espeak_ng |
| quae | .multilang/latin-audio-samples/word-quae.wav | not_generated_missing_espeak_ng |
| cum | .multilang/latin-audio-samples/word-cum.wav | not_generated_missing_espeak_ng |
| Romae | .multilang/latin-audio-samples/word-Romae.wav | not_generated_missing_espeak_ng |

### Sentence Samples

| Text | Expected sample path | Status |
|---|---|---|
| Arma virumque cano. | .multilang/latin-audio-samples/sentence-1.wav | not_generated_missing_espeak_ng |

## Human Playback Decision Fields

These fields must be updated only after real sample playback:

| Field | Value |
|---|---|
| approval_phrase | pending: `approved espeak-ng classical_approx` or rejection details |
| pronunciation_acceptability | pending |
| rejection_reason | eSpeak NG sample generation blocked by missing binary |
| fallback_caveats | Azure remains blocked without a verified native Classical Latin/`la` locale; eSpeak NG quality remains unapproved until playback review. |

## Verification Performed

- `python -m pytest tests/services/test_latin_audio_samples.py -q` → passed (`3 passed`).
- Real sample generation attempted with `generate_latin_audio_sample_manifest()` → blocked: `eSpeak NG binary is not available`.

## Resume Instructions

Install eSpeak NG 1.52+ and ensure `espeak-ng` is on `PATH`, then rerun Plan 27-03 sample generation. After WAV files exist, play the listed samples and record either `approved espeak-ng classical_approx` or rejection details.
