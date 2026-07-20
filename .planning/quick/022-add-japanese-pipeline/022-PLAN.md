# Quick Task 022 Plan: Register Japanese Runtime Basics

## Objective

Register Japanese (`ja`) as a default supported runtime language for the core text-generation configuration, without yet adding frequency assets, Japanese validation, or export routing.

Approach context: User chose to split the broader Japanese pipeline integration into smaller stages after the initial plan checker flagged the full integration as too large for a quick task. This is stage 1 only: make `ja` visible in default settings/runtime language names and provider text routing so later tasks can build assets/validation/export on a stable contract.

Planner note: `.planning/templates/roles/planner.md` and `.planning/templates/delegates/plan-checker.md` are absent in this repo state, so this quick plan follows the quick-task contract directly with reduced planner/checker-template assurance.

No UI proof rationale: This task changes CLI/domain/provider configuration and tests only; it has no rendered UI surface.

## Task 1: Register Japanese Defaults And Text Provider Routing

<files>
- `src/multilang/settings.py`
- `src/multilang/runtime.py`
- `src/multilang/services/provider_text_adapters.py`
- `tests/test_settings.py`
- `tests/domain/test_jobs.py`
</files>

<action>
- Add `ja` to `SupportedLanguageCode` and `DEFAULT_SUPPORTED_LANGUAGES` so default settings expose Japanese.
- Add `SupportedLanguage.JA` to runtime display names as `Japanese` so default deck naming and runtime summaries can resolve the enum.
- Add Japanese to provider text language names and DeepL target mapping (`JA`) so provider-backed generation/translation prompts do not fall back to raw `ja` or miss DeepL routing.
- Tighten focused tests for settings/domain contracts around Japanese.
</action>

<done>
- `GenerationRequest(language="ja", ...)` parses to `SupportedLanguage.JA`.
- `Settings(_env_file=None).supported_languages` includes `ja`.
- Provider text maps resolve Japanese and DeepL `JA`.
</done>

<verify>
- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.settings import Settings; from multilang.services.provider_text_adapters import _LANGUAGE_NAMES, _DEEPL_TARGET_LANGUAGES; assert GenerationRequest(language='ja', source_type='frequency').language is SupportedLanguage.JA; assert 'ja' in Settings(_env_file=None).supported_languages; assert _LANGUAGE_NAMES['ja'] == 'Japanese'; assert _DEEPL_TARGET_LANGUAGES['ja'] == 'JA'"`
- `uv run pytest tests/domain/test_jobs.py tests/test_settings.py -q`
</verify>

## Deferred Follow-Up Tasks

- Stage 2: Add Japanese local/Tatoeba/TTS fallback maps, frequency assets, and Japanese-aware text validation.
- Stage 3: Route `language=ja` export rows to `Multilang::Japanese Card` with the Japanese field set/template.
