# Quick Task 022 Summary: Register Japanese Runtime Basics

## Status

Completed.

## Implemented

- Added `ja` to `SupportedLanguageCode` and `DEFAULT_SUPPORTED_LANGUAGES` in `src/multilang/settings.py`.
- Added `SupportedLanguage.JA` to runtime language display names in `src/multilang/runtime.py`.
- Added Japanese provider text naming and DeepL target routing (`JA`) in `src/multilang/services/provider_text_adapters.py`.
- Added focused Japanese coverage in `tests/domain/test_jobs.py`.
- Updated default supported-language settings coverage in `tests/test_settings.py`.

## Verification

- Passed: `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.settings import Settings; from multilang.services.provider_text_adapters import _LANGUAGE_NAMES, _DEEPL_TARGET_LANGUAGES; assert GenerationRequest(language='ja', source_type='frequency').language is SupportedLanguage.JA; assert 'ja' in Settings(_env_file=None).supported_languages; assert _LANGUAGE_NAMES['ja'] == 'Japanese'; assert _DEEPL_TARGET_LANGUAGES['ja'] == 'JA'"`
- Passed: `uv run pytest tests/domain/test_jobs.py tests/test_settings.py -q` (`29 passed`)

## Deferred

- Stage 2: Japanese local/Tatoeba/TTS fallback maps, frequency assets, and Japanese-aware text validation.
- Stage 3: Japanese export routing to `Multilang::Japanese Card`.
