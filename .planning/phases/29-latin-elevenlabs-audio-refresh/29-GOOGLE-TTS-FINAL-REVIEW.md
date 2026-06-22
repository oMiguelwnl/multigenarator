---
phase: 29-latin-elevenlabs-audio-refresh
review_artifact: google-tts-final-review
selected_provider: google-translate-tts
selected_voice: la
pronunciation_policy: google_translate_latin
provider_version: google-translate-tts-la
playback_review_status: approved
reviewer: user
reviewed_at: 2026-06-22T00:00:00Z
elevenlabs_status: deferred_billing_blocked
finevoice_status: research_only
system_espeak_uninstall: not_requested
---

# Phase 29 Google TTS Final Review

This artifact records the current Latin MVP audio provider decision for v2.1.

## Final Provider

| Field | Value |
|---|---|
| selected_provider | google-translate-tts |
| selected_voice | la |
| provider_version | google-translate-tts-la |
| pronunciation_policy | google_translate_latin |
| playback_review_status | approved |
| scope | latin-mvp-50-v1 only |

## Deferred Providers

| Provider | Status | Reason |
|---|---|---|
| elevenlabs-italian | deferred_billing_blocked | All three configured keys returned HTTP 402 Payment Required during sample generation. |
| azure-italian | fallback | Retained as a fallback candidate if Google TTS becomes unavailable. |
| finevoice | research_only | Research-only; no active runtime provider wiring in this phase. |

## Safety Notes

- No provider credentials are recorded in this artifact.
- No live provider call is required for Latin export.
- eSpeak NG is not uninstalled from the user/system environment.
- Historical planning artifacts may still mention earlier eSpeak or ElevenLabs exploration.

## Current Decision

Google Translate TTS (`la`) is the final provider for the current committed 50-card Latin MVP audio pack. ElevenLabs is deferred until a future plan proves billing, sample quality, and approval.
