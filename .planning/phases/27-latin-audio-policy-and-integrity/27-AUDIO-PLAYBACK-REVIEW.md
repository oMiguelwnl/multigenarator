---
phase: 27-latin-audio-policy-and-integrity
plan: 03
review_artifact: latin-audio-playback-review
selected_provider: pending-human-playback
selected_voice: la
pronunciation_policy: classical_approx
playback_review_status: needs_playback_review
reviewer: pending-human-playback
reviewed_at: null
sample_manifest: .multilang/latin-audio-samples/latin-audio-samples.json
---

# Phase 27 Latin Audio Playback Review

This artifact records the blocking playback review decision for the Classical Latin MVP audio policy. It is intentionally fail-closed: later full-manifest generation must not treat Latin audio as approved unless `playback_review_status` is `approved` and the selected provider/voice/policy are explicitly recorded.

## Current Review Status

| Field | Value |
|---|---|
| selected_provider | pending-human-playback |
| selected_voice | la |
| pronunciation_policy | classical_approx |
| playback_review_status | needs_playback_review |
| reviewer | pending-human-playback |
| reviewed_at | null |
| blocking_reason | Human playback approval is still pending. Real eSpeak NG 1.52.0 WAV samples have been generated and must be listened to before approval can be recorded. |

## Provider Candidates

| Provider | Voice | Pronunciation policy | Status | Caveat |
|---|---|---|---|---|
| espeak-ng | la | classical_approx | needs_playback_review | Candidate generated local WAV files for review with eSpeak NG 1.52.0. Approval requires human playback evaluation. |
| azure-multilingual-experimental | multilingual-experimental | experimental_unverified | blocked | No verified native Classical Latin/`la` Azure TTS locale is available. |

## Representative Samples Required for Review

Sample manifest: `.multilang/latin-audio-samples/latin-audio-samples.json`

### Word Samples

| Text | Sample path | Status |
|---|---|---|
| virum | .multilang/latin-audio-samples/word-virum.wav | generated_needs_playback_review |
| puella | .multilang/latin-audio-samples/word-puella.wav | generated_needs_playback_review |
| caesar | .multilang/latin-audio-samples/word-caesar.wav | generated_needs_playback_review |
| cicero | .multilang/latin-audio-samples/word-cicero.wav | generated_needs_playback_review |
| veni | .multilang/latin-audio-samples/word-veni.wav | generated_needs_playback_review |
| quae | .multilang/latin-audio-samples/word-quae.wav | generated_needs_playback_review |
| cum | .multilang/latin-audio-samples/word-cum.wav | generated_needs_playback_review |
| Romae | .multilang/latin-audio-samples/word-Romae.wav | generated_needs_playback_review |

### Sentence Samples

| Text | Sample path | Status |
|---|---|---|
| Arma virumque cano. | .multilang/latin-audio-samples/sentence-1.wav | generated_needs_playback_review |

## Human Playback Decision Fields

These fields must be updated only after real sample playback:

| Field | Value |
|---|---|
| approval_phrase | pending: `approved espeak-ng classical_approx` or rejection details |
| pronunciation_acceptability | pending |
| rejection_reason | pending human playback review |
| fallback_caveats | Azure remains blocked without a verified native Classical Latin/`la` locale; eSpeak NG quality remains unapproved until playback review. |

## Verification Performed

- `PATH="$PATH:/c/Program Files/eSpeak NG" python -m pytest tests/services/test_latin_audio_samples.py tests/services/test_espeak_ng_speech_adapter.py -q` → passed (`10 passed`).
- Real sample generation with `generate_latin_audio_sample_manifest()` → generated 9 eSpeak NG 1.52.0 WAV samples and `.multilang/latin-audio-samples/latin-audio-samples.json`.

## Resume Instructions

Play the listed sample WAV files. After playback, resume with either `approved espeak-ng classical_approx` or rejection details. Do not mark Latin MVP audio approved until this artifact records explicit human approval.
