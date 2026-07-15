# Quick Task 020 Plan: Add Croatian

## Objective

Add Croatian (`hr`) as a supported modern-language deck target with the same core registration, provider routing, audio voice selection, frequency assets, and focused regression coverage as the existing modern languages.

Approach context: No clarification required; Croatian maps to ISO 639-1 code `hr` and should follow the existing modern-language support pattern used for Hungarian and Czech.

Planner note: `.planning/templates/roles/planner.md` and `.planning/templates/delegates/plan-checker.md` are absent, so this plan follows the quick-task contract directly with reduced planner/checker-template assurance.

No UI proof rationale: This task changes CLI/domain/provider configuration and data assets only; it has no rendered UI surface.

## Task 1: Register `hr` Across Language Contracts

<files>
- `src/multilang/domain/jobs.py`
- `src/multilang/settings.py`
- `src/multilang/runtime.py`
- `src/multilang/services/provider_text_adapters.py`
- `src/multilang/services/provider_pronunciation_adapters.py`
- `src/multilang/services/library_pronunciation_adapters.py`
- `src/multilang/services/language_identifier.py`
- `src/multilang/services/highlight_candidate_extraction.py`
- `src/multilang/services/tatoeba_sentence_source.py`
- `src/multilang/services/text_validation.py`
- `src/multilang/services/local_text_adapter.py`
- `src/multilang/services/part_of_speech.py`
- `tests/services/test_local_text_adapter.py`
- `tests/services/test_text_field_remediation.py`
</files>

<action>
- Add `SupportedLanguage.HR = "hr"` to the language enum.
- Add `hr` to typed settings defaults and runtime language-name maps as "Croatian".
- Add `hr` to provider prompt language names, DeepL target mapping, pronunciation prompt names, Tatoeba API routing, and corpus language-id supported codes.
- Add `hr` to deterministic library pronunciation resolver maps and function-word POS inference maps.
- Add Croatian highlight stopwords and text-validation language markers so Kindle/highlight and validation flows do not fail on language-key lookups.
- Add `hr` to local/offline text-generation support so local smoke paths can produce deterministic Croatian sentences/translations.
</action>

<done>
- `GenerationRequest(language="hr", ...)` parses to `SupportedLanguage.HR`.
- Default settings expose `hr` in the supported-language list.
- Croatian exists in all runtime/provider/local maps touched by this task without falling through to raw language codes or key errors.
</done>

<verify>
- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.settings import Settings; assert GenerationRequest(language='hr', source_type='frequency').language is SupportedLanguage.HR; assert 'hr' in Settings(_env_file=None).supported_languages"`
- `uv run python -c "from multilang.domain.jobs import SupportedLanguage; from multilang.services.provider_text_adapters import _DEEPL_TARGET_LANGUAGES, _LANGUAGE_NAMES as text_names; from multilang.services.provider_pronunciation_adapters import _LANGUAGE_NAMES as pronunciation_names; from multilang.services.language_identifier import SUPPORTED_LANGUAGE_CODES; from multilang.services.tatoeba_sentence_source import _TATOEBA_API_CODES; from multilang.services.text_validation import _LANGUAGE_MARKERS; from multilang.services.highlight_candidate_extraction import _STOPWORDS; assert text_names['hr'] == 'Croatian'; assert _DEEPL_TARGET_LANGUAGES['hr'] == 'HR'; assert pronunciation_names['hr'] == 'Croatian'; assert 'hr' in SUPPORTED_LANGUAGE_CODES; assert _TATOEBA_API_CODES['hr'] == 'hrv'; assert _LANGUAGE_MARKERS['hr']; assert _STOPWORDS[SupportedLanguage.HR]"`
- `uv run python -c "from multilang.services.library_pronunciation_adapters import LibraryPronunciationAdapter; from multilang.services.part_of_speech import infer_function_word_part_of_speech; assert 'phonemizer-espeak' in LibraryPronunciationAdapter().resolver_names_for_language('hr'); assert infer_function_word_part_of_speech(source_language='hr', display_form='i', lemma='i') == 'conjunction'"`
- `uv run pytest tests/services/test_local_text_adapter.py::test_local_adapter_supports_croatian -q`
</verify>

## Task 2: Add Audio Provider Routing For `hr`

<files>
- `src/multilang/services/audio_voice_registry.py`
- `src/multilang/services/elevenlabs_speech_adapter.py`
- `src/multilang/services/google_translate_speech_adapter.py`
- `tests/services/test_audio_voice_registry.py`
- `tests/services/test_elevenlabs_speech_adapter.py`
- `tests/services/test_google_translate_speech_adapter.py`
</files>

<action>
- Add an Azure voice plan for Croatian using `hr-HR` voices.
- Add ElevenLabs and Google Translate TTS locale/code routing for `hr`.
- Add focused tests proving Croatian voice/locale selection without changing broader unrelated audio behavior.
</action>

<done>
- Azure voice selection returns a deterministic Croatian `hr-HR` voice.
- ElevenLabs and Google Translate fallback adapters can select Croatian without key errors.
- Existing voice registry coverage still proves every `SupportedLanguage` has an approved Azure voice plan.
</done>

<verify>
- `uv run pytest tests/services/test_audio_voice_registry.py::test_voice_registry_selects_croatian_voice tests/services/test_elevenlabs_speech_adapter.py::test_elevenlabs_adapter_uses_default_voice_for_croatian tests/services/test_google_translate_speech_adapter.py::test_google_translate_adapter_selects_croatian_language -q`
</verify>

## Task 3: Add Frequency Assets And Contract Coverage For `hr`

<files>
- `assets/frequency/hr/curated-v1.csv`
- `assets/frequency/hr/rejections-v1.csv`
- `tests/domain/test_jobs.py`
- `tests/test_settings.py`
- `tests/cli/test_generate_command.py`
- `tests/services/test_frequency_decks.py`
</files>

<action>
- Create committed Croatian frequency assets with 3 levels of 1000 rows from `wordfreq` using the existing curated frequency schema and structural curation flags.
- Add/update focused tests proving `hr` is accepted as a supported language, appears in default settings, its curated assets validate, and unsupported-language tests continue to use a truly unsupported code.
- Avoid ROADMAP/SPEC updates because quick tasks do not modify phase-level artifacts.
</action>

<done>
- `assets/frequency/hr/curated-v1.csv` and `assets/frequency/hr/rejections-v1.csv` exist and pass the existing asset validators.
- Croatian has exactly 1000 curated rows in each frequency level.
</done>

<verify>
- `uv run pytest tests/domain/test_jobs.py::test_generation_request_accepts_croatian tests/test_settings.py::test_default_supported_languages_include_croatian tests/services/test_frequency_decks.py::test_croatian_frequency_assets_validate tests/cli/test_generate_command.py::test_generate_command_rejects_unsupported_language -q`
- `uv run python scripts/build_frequency_assets.py --check --language hr`
- `uv run python scripts/build_frequency_assets.py --check`
</verify>
