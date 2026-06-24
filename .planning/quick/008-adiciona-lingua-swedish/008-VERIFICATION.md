---
quick_task: 008-adiciona-lingua-swedish
verified: 2026-06-24T01:19:08Z
status: passed
score: 5/5 must-haves verified
human_verification: []
gaps: []
---

# Quick Task 008 Verification: Add Swedish

**Task description:** adiciona a lingua Swedish  
**Scope:** quick-mode verification against the task only; no ROADMAP/cross-phase checks.  
**Status:** passed

## Goal Achievement

| Must-have surface | Status | Evidence |
| --- | --- | --- |
| Domain/settings support `sv` | ✓ Verified | `SupportedLanguage.SV = "sv"` exists in `src/multilang/domain/jobs.py`; `DEFAULT_SUPPORTED_LANGUAGES` and `SupportedLanguageCode` include `sv` in `src/multilang/settings.py`; `GenerationRequest(language="sv")` check passed. |
| Runtime/provider routing supports Swedish | ✓ Verified | `runtime._LANGUAGE_NAMES` maps `SupportedLanguage.SV` to `Swedish`; text/pronunciation provider maps include `sv`; DeepL maps `sv -> SV`; language-id, Tatoeba (`swe`), text-validation markers, highlight stopwords, and local text templates include Swedish. |
| Audio routing supports Swedish | ✓ Verified | Azure registry selects `sv-SE-SofieNeural` with `sv-SE-MattiasNeural` fallback; ElevenLabs maps `sv` to `sv-SE`; Google Translate TTS maps `sv` to `sv`. Focused audio tests passed. |
| Frequency assets exist and validate | ✓ Verified | `assets/frequency/sv/curated-v1.csv` and `rejections-v1.csv` exist; curated asset has 3000 rows with exactly 1000 per level and `wordfreq:sv` provenance; `scripts/build_frequency_assets.py --check` passed. |
| Regression tests cover promised surfaces | ✓ Verified | Focused Swedish/domain/settings/audio/frequency/CLI tests passed: `8 passed in 0.90s`. |

## Commands Run

- `uv run python -c "... GenerationRequest(language='sv') ... Settings(_env_file=None).supported_languages ..."`
- `uv run python -c "... provider/runtime map assertions for sv ..."`
- `uv run pytest tests/services/test_local_text_adapter.py::test_local_adapter_supports_swedish tests/services/test_audio_voice_registry.py::test_voice_registry_selects_swedish_voice tests/services/test_elevenlabs_speech_adapter.py::test_elevenlabs_adapter_uses_default_voice_for_swedish tests/services/test_google_translate_speech_adapter.py::test_google_translate_adapter_selects_swedish_language tests/domain/test_jobs.py::test_generation_request_accepts_swedish tests/test_settings.py::test_default_supported_languages_include_swedish tests/services/test_frequency_decks.py::test_swedish_frequency_assets_validate tests/cli/test_generate_command.py::test_generate_command_rejects_unsupported_language -q` → `8 passed in 0.90s`
- `uv run python scripts/build_frequency_assets.py --check`
- `uv run python -c "... csv count validation ..."` → `curated=3000 levels={'1': 1000, '2': 1000, '3': 1000} rejections=30`

## Anti-patterns / Notes

- No Swedish-specific stubs or missing wiring found.
- Existing `placeholder` handling in `local_text_adapter.py` is an intentional review-case branch for flagged items, not part of Swedish routing.

## Human Verification

None required.

## Gaps Summary

No gaps found. Swedish (`sv`) is supported across the promised domain/settings, runtime/provider, audio, frequency-asset, and test surfaces.

---

_Verified: 2026-06-24T01:19:08Z_
_Verifier: the agent (quick verifier)_
