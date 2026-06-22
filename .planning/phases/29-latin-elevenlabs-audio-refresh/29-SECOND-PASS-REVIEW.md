---
phase: 29-latin-elevenlabs-audio-refresh
review_artifact: second-pass-review
selected_provider: google-translate-tts
selected_voice: la
pronunciation_policy: google_translate_latin
provider_version: google-translate-tts-la
elevenlabs_status: deferred_billing_blocked
finevoice_status: research_only
system_espeak_uninstall: not_requested
review_status: passed
reviewed_at: 2026-06-22T00:00:00Z
---

# Phase 29 Second-Pass Review

## Verdict

PASS. Phase 29 finalizes Google Translate TTS (`la`) for the current 50-card Latin MVP audio pack and keeps the export path offline, approved-only, and fail-closed.

## High-Leverage Surfaces Reviewed

| Surface | Result |
|---|---|
| `data/latin_mvp/latin-mvp-50-v1-audio.json` | 50 word and 50 sentence artifacts use `google-translate-tts`, voice `la`, provider version `google-translate-tts-la`, and approved playback status. |
| `data/latin_mvp/audio/latin-mvp-50-v1/` | 100 committed MP3 media files exist and are packaged by APKG export. |
| `src/multilang/services/latin_audio.py` | Export readiness remains fail-closed for missing, stale, unsafe, unapproved, mismatched, or legacy-provider audio. |
| `src/multilang/services/latin_export.py` | Latin export still validates curation, translation, grammar, audio readiness, field order, and media packaging before writing output. |
| `LATIN-STRUCTURE.md` | Current audio section names Google TTS as approved for MVP 50 and ElevenLabs as not required for current export. |
| `.planning/STATE.md` | Current state records Phase 29 Google TTS finalization; eSpeak references are historical/superseded context only. |

## Provider Decision

| Provider | Current status | Notes |
|---|---|---|
| google-translate-tts | final_audio_provider | Final for `latin-mvp-50-v1` word and sentence audio. |
| elevenlabs-italian | deferred_billing_blocked | Deferred after configured keys returned `HTTP 402 Payment Required`; not required for current export. |
| azure-italian | fallback | Retained as fallback candidate, not final provider. |
| finevoice | research_only | Not wired as an active provider. |
| eSpeak NG | historical/superseded | No system uninstall requested; legacy manifest input fails closed unless explicitly treated as historical test data. |

## Verification Run

| Check | Result |
|---|---|
| `uv run pytest tests/services/test_latin_audio.py tests/services/test_latin_audio_generation.py tests/services/test_latin_audio_refresh.py tests/services/test_latin_audio_samples.py -q` | 23 passed |
| `uv run pytest tests/integration/test_v21_latin_google_tts_final_audio.py tests/integration/test_v20_latin_audio_asset.py tests/integration/test_v20_latin_audio_evidence.py -q` | 21 passed |
| `uv run pytest tests/services/test_latin_mvp.py tests/cli/test_generate_latin_mvp_command.py tests/services/test_latin_export.py tests/integration/test_v20_latin_export_evidence.py tests/integration/test_v20_final_milestone_evidence.py -q` | 50 passed |
| `uv run pytest tests/integration/test_v20_existing_modes_regression_evidence.py tests/integration/test_v13_existing_modes_regression_evidence.py -q` | 8 passed |
| `uv run multilang export-latin-mvp --format apkg --output-dir exports/latin_mvp` | completed; 50 cards, 100 media |
| `uv run multilang export-latin-mvp --format csv --output-dir exports/latin_mvp` | completed; 50 cards |
| `uv run multilang export-latin-mvp --format tsv --output-dir exports/latin_mvp` | completed; 50 cards |
| `rg "espeak|eSpeak|espeak-ng|ElevenLabs" src tests LATIN-STRUCTURE.md .planning/STATE.md` | shell `rg` unavailable; equivalent workspace grep completed and remaining hits are adapters, fallback/deferred tests, or historical/superseded context. |

## Privacy And Safety

- No provider credentials are recorded in review artifacts, tests, public CLI output, or generated exports.
- No raw provider responses are recorded.
- No local absolute media paths are exposed in public summaries.
- No live provider calls are required for current Latin export.
- No system-level eSpeak NG uninstall is requested.

## Closure Notes

The current committed Latin MVP export path is Google TTS final for `latin-mvp-50-v1`. ElevenLabs can only be reconsidered in a future plan that proves billing availability, sample generation, playback review, and export-readiness evidence.
