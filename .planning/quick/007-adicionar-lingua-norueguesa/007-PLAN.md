# Quick Task 007 Plan: Add Norwegian Bokmal

## Objective

Add Norwegian Bokmal (`nb`) as a supported modern-language deck target with the same core registration, provider routing, audio voice selection, frequency assets, and focused regression coverage as the existing modern languages.

Approach context: User confirmed Norwegian should mean Bokmal (`nb`), not Nynorsk (`nn`) or both.

Planner note: `.planning/templates/roles/planner.md` is absent, so this plan follows the quick-task contract directly with reduced planner-template assurance.

No UI proof rationale: This task changes CLI/domain/provider configuration and data assets only; it has no rendered UI surface.

## Task 1: Register `nb` Across Language Contracts

<files>
- `src/multilang/domain/jobs.py`
- `src/multilang/settings.py`
- `src/multilang/runtime.py`
- `src/multilang/services/provider_text_adapters.py`
- `src/multilang/services/provider_pronunciation_adapters.py`
- `src/multilang/services/language_identifier.py`
- `src/multilang/services/highlight_candidate_extraction.py`
- `src/multilang/services/tatoeba_sentence_source.py`
- `src/multilang/services/text_validation.py`
- `src/multilang/services/local_text_adapter.py`
- `tests/services/test_local_text_adapter.py`
</files>

<action>
- Add `SupportedLanguage.NB = "nb"` to the modern language enum.
- Add `nb` to typed settings defaults and runtime language-name maps as "Norwegian Bokmal".
- Add `nb` to provider prompt language names, DeepL target mapping, pronunciation prompt names, and corpus language-id supported codes.
- Add `nb` highlight stopwords so Kindle highlight candidate extraction can handle Norwegian input without a language-key failure.
- Add `nb` to local/offline text-generation support, Tatoeba language routing, and language-marker validation maps.
</action>

<verify>
- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.settings import Settings; assert GenerationRequest(language='nb', source_type='frequency').language is SupportedLanguage.NB; assert 'nb' in Settings(_env_file=None).supported_languages"`
</verify>

## Task 2: Add Audio Provider Routing For `nb`

<files>
- `src/multilang/services/audio_voice_registry.py`
- `src/multilang/services/elevenlabs_speech_adapter.py`
- `src/multilang/services/google_translate_speech_adapter.py`
- `tests/services/test_audio_voice_registry.py`
- `tests/services/test_elevenlabs_speech_adapter.py`
- `tests/services/test_google_translate_speech_adapter.py`
</files>

<action>
- Add an Azure voice plan for Norwegian Bokmal using `nb-NO` voices.
- Add ElevenLabs and Google Translate TTS locale/code routing for `nb`.
- Add focused tests proving Norwegian voice/locale selection without changing broader unrelated audio behavior.
</action>

<verify>
- `uv run pytest tests/services/test_audio_voice_registry.py::test_voice_registry_selects_norwegian_bokmal_voice tests/services/test_elevenlabs_speech_adapter.py::test_elevenlabs_adapter_uses_default_voice_for_norwegian_bokmal tests/services/test_google_translate_speech_adapter.py::test_google_translate_adapter_selects_norwegian_bokmal_language -q`
</verify>

## Task 3: Add Frequency Assets And Contract Coverage For `nb`

<files>
- `assets/frequency/nb/curated-v1.csv`
- `assets/frequency/nb/rejections-v1.csv`
- `src/multilang/services/frequency_decks.py`
- `tests/domain/test_jobs.py`
- `tests/test_settings.py`
- `tests/services/test_frequency_decks.py`
</files>

<action>
- Create committed Norwegian Bokmal frequency assets with 3 levels of 1000 rows from `wordfreq` using the existing curated frequency schema and structural curation flags.
- Keep the shared structural token filter from accepting Unicode replacement-character artifacts surfaced by the `nb` wordfreq list.
- Add/update focused tests proving `nb` is accepted as a supported language, appears in default settings, and its curated assets validate.
- Avoid ROADMAP/SPEC updates because quick tasks do not modify phase-level artifacts.
</action>

<verify>
- `uv run pytest tests/domain/test_jobs.py::test_generation_request_accepts_norwegian_bokmal tests/test_settings.py::test_default_supported_languages_include_norwegian_bokmal tests/services/test_frequency_decks.py::test_norwegian_bokmal_frequency_assets_validate -q`
</verify>
