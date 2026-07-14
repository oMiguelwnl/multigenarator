# Quick Task 019 Plan: Add Czech

## Objective

Add Czech (`cs`) as a supported modern-language deck target with the same core registration, provider routing, audio voice selection, frequency assets, and focused regression coverage as the existing modern languages.

Approach context: No clarification required; Czech maps to ISO 639-1 code `cs` and should follow the existing modern-language support pattern used for Danish, Norwegian Bokmal, Swedish, Finnish, and Hungarian.

Planner note: `.planning/templates/roles/planner.md` and `.planning/templates/delegates/plan-checker.md` are absent, so this plan follows the quick-task contract directly with reduced planner/checker-template assurance.

No UI proof rationale: This task changes CLI/domain/provider configuration and data assets only; it has no rendered UI surface.

## Task 1: Register `cs` Across Language Contracts

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
- Add `SupportedLanguage.CS = "cs"` to the language enum.
- Add `cs` to typed settings defaults and runtime language-name maps as "Czech".
- Add `cs` to provider prompt language names, DeepL target mapping, pronunciation prompt names, Tatoeba API routing, and corpus language-id supported codes.
- Add `cs` to deterministic library pronunciation resolver maps and function-word POS inference maps.
- Add Czech highlight stopwords and text-validation language markers so Kindle/highlight and validation flows do not fail on language-key lookups.
- Add `cs` to local/offline text-generation support so local smoke paths can produce deterministic Czech sentences/translations.
</action>

<done>
- `GenerationRequest(language="cs", ...)` parses to `SupportedLanguage.CS`.
- Default settings expose `cs` in the supported-language list.
- Czech exists in all runtime/provider/local maps touched by this task without falling through to raw language codes or key errors.
</done>

<verify>
- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.settings import Settings; assert GenerationRequest(language='cs', source_type='frequency').language is SupportedLanguage.CS; assert 'cs' in Settings(_env_file=None).supported_languages"`
- `uv run python -c "from multilang.domain.jobs import SupportedLanguage; from multilang.services.provider_text_adapters import _DEEPL_TARGET_LANGUAGES, _LANGUAGE_NAMES as text_names; from multilang.services.provider_pronunciation_adapters import _LANGUAGE_NAMES as pronunciation_names; from multilang.services.language_identifier import SUPPORTED_LANGUAGE_CODES; from multilang.services.tatoeba_sentence_source import _TATOEBA_API_CODES; from multilang.services.text_validation import _LANGUAGE_MARKERS; from multilang.services.highlight_candidate_extraction import _STOPWORDS; assert text_names['cs'] == 'Czech'; assert _DEEPL_TARGET_LANGUAGES['cs'] == 'CS'; assert pronunciation_names['cs'] == 'Czech'; assert 'cs' in SUPPORTED_LANGUAGE_CODES; assert _TATOEBA_API_CODES['cs'] == 'ces'; assert _LANGUAGE_MARKERS['cs']; assert _STOPWORDS[SupportedLanguage.CS]"`
- `uv run python -c "from multilang.services.library_pronunciation_adapters import LibraryPronunciationAdapter; from multilang.services.part_of_speech import infer_function_word_part_of_speech; assert 'phonemizer-espeak' in LibraryPronunciationAdapter().resolver_names_for_language('cs'); assert infer_function_word_part_of_speech(source_language='cs', display_form='a', lemma='a') == 'conjunction'"`
- `uv run pytest tests/services/test_local_text_adapter.py::test_local_adapter_supports_czech -q`
</verify>

## Task 2: Add Audio Provider Routing For `cs`

<files>
- `src/multilang/services/audio_voice_registry.py`
- `src/multilang/services/elevenlabs_speech_adapter.py`
- `src/multilang/services/google_translate_speech_adapter.py`
- `tests/services/test_audio_voice_registry.py`
- `tests/services/test_elevenlabs_speech_adapter.py`
- `tests/services/test_google_translate_speech_adapter.py`
</files>

<action>
- Add an Azure voice plan for Czech using `cs-CZ` voices.
- Add ElevenLabs and Google Translate TTS locale/code routing for `cs`.
- Add focused tests proving Czech voice/locale selection without changing broader unrelated audio behavior.
</action>

<done>
- Azure voice selection returns a deterministic Czech `cs-CZ` voice.
- ElevenLabs and Google Translate fallback adapters can select Czech without key errors.
- Existing voice registry coverage still proves every `SupportedLanguage` has an approved Azure voice plan.
</done>

<verify>
- `uv run pytest tests/services/test_audio_voice_registry.py::test_voice_registry_selects_czech_voice tests/services/test_elevenlabs_speech_adapter.py::test_elevenlabs_adapter_uses_default_voice_for_czech tests/services/test_google_translate_speech_adapter.py::test_google_translate_adapter_selects_czech_language -q`
</verify>

## Task 3: Add Frequency Assets And Contract Coverage For `cs`

<files>
- `assets/frequency/cs/curated-v1.csv`
- `assets/frequency/cs/rejections-v1.csv`
- `tests/domain/test_jobs.py`
- `tests/test_settings.py`
- `tests/cli/test_generate_command.py`
- `tests/services/test_frequency_decks.py`
</files>

<action>
- Create committed Czech frequency assets with 3 levels of 1000 rows from `wordfreq` using the existing curated frequency schema and structural curation flags.
- Add/update focused tests proving `cs` is accepted as a supported language, appears in default settings, its curated assets validate, and unsupported-language tests continue to use a truly unsupported code.
- Avoid ROADMAP/SPEC updates because quick tasks do not modify phase-level artifacts.
</action>

<done>
- `assets/frequency/cs/curated-v1.csv` and `assets/frequency/cs/rejections-v1.csv` exist and pass the existing asset validators.
- Czech has exactly 1000 curated rows in each frequency level.
- Tests no longer treat `cs` as unsupported.
</done>

<verify>
- `uv run pytest tests/domain/test_jobs.py::test_generation_request_accepts_czech tests/test_settings.py::test_default_supported_languages_include_czech tests/services/test_frequency_decks.py::test_czech_frequency_assets_validate tests/cli/test_generate_command.py::test_generate_command_rejects_unsupported_language -q`
- `uv run python scripts/build_frequency_assets.py --check --language cs`
- `uv run python scripts/build_frequency_assets.py --check`
</verify>
