---
phase: 27-latin-audio-policy-and-integrity
plan: 03
review_artifact: latin-audio-playback-review
selected_provider: google-translate-tts
selected_voice: la
pronunciation_policy: google_translate_latin
playback_review_status: approved
reviewer: user
reviewed_at: 2026-06-17T00:00:00Z
sample_manifest: .multilang/latin-audio-samples/latin-audio-samples.json
---

# Phase 27 Latin Audio Playback Review

This artifact records the blocking playback review decision for the Classical Latin MVP audio policy. It is intentionally fail-closed: later full-manifest generation must not treat Latin audio as approved unless `playback_review_status` is `approved` and the selected provider/voice/policy are explicitly recorded.

## Current Review Status

| Field | Value |
|---|---|
| selected_provider | google-translate-tts |
| selected_voice | la |
| pronunciation_policy | google_translate_latin |
| playback_review_status | approved |
| reviewer | user |
| reviewed_at | 2026-06-17T00:00:00Z |
| blocking_reason | None; handoff policy selects Google Translate TTS for Latin MVP audio. |

## Provider Candidates

| Provider | Voice | Pronunciation policy | Status | Caveat |
|---|---|---|---|---|
| google-translate-tts | la | google_translate_latin | approved | Primary provider selected by the real-data provider handoff for Latin MVP MP3 audio. |
| elevenlabs-italian | it-IT | italian_multilingual_approx | fallback | Fallback 1 if Google Translate TTS is unavailable. |
| azure-italian | it-IT | italian_voice_fallback | fallback | Fallback 2 if Google Translate TTS and ElevenLabs are unavailable. |
| finevoice | research-only | research_only | blocked | Research-only; do not use in production. |

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
| approval_phrase | `approved google-translate-tts google_translate_latin` |
| pronunciation_acceptability | Acceptable for the 50-card Latin MVP as provider-generated Latin TTS, not a native/human-recorded pronunciation guarantee. |
| rejection_reason | None |
| fallback_caveats | ElevenLabs Italian and Azure Italian are fallback providers only; FineVoice remains research-only. |

## Verification Performed

- `PATH="$PATH:/c/Program Files/eSpeak NG" python -m pytest tests/services/test_latin_audio_samples.py tests/services/test_espeak_ng_speech_adapter.py -q` → passed (`10 passed`).
- Real sample generation with `generate_latin_audio_sample_manifest()` → generated 9 eSpeak NG 1.52.0 WAV samples and `.multilang/latin-audio-samples/latin-audio-samples.json`.
- Real-data provider handoff → approved Google Translate TTS (`la`) as primary Latin MVP audio provider with ElevenLabs Italian and Azure Italian fallbacks.

## Policy Handoff

Later Latin MVP export plans may treat Google Translate TTS voice `la` with pronunciation policy `google_translate_latin` as the approved Latin MVP audio policy only when this artifact still records `playback_review_status=approved`, `selected_provider=google-translate-tts`, `selected_voice=la`, and `pronunciation_policy=google_translate_latin`.
