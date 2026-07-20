# Quick Task 022 Verification: Register Japanese Runtime Basics

## Verdict

Passed.

## Goal Check

The bounded stage-1 goal was to register Japanese as a default supported runtime language for core text-generation configuration, without completing assets, validation, or export routing.

## Evidence

- `GenerationRequest(language="ja", source_type="frequency")` resolves to `SupportedLanguage.JA`.
- `Settings(_env_file=None).supported_languages` includes `ja`.
- Provider text maps resolve `_LANGUAGE_NAMES["ja"] == "Japanese"` and `_DEEPL_TARGET_LANGUAGES["ja"] == "JA"`.
- Focused tests passed: `uv run pytest tests/domain/test_jobs.py tests/test_settings.py -q`.

## Remaining Gaps

- `generate --language ja --source frequency` is not complete yet because Japanese frequency assets, text validation, local/Tatoeba/TTS fallback maps, and export routing remain deferred.
