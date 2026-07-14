# Quick Task 018 Verification: Add Hungarian

## Verdict

Passed.

## Goal Check

Hungarian (`hu`) is now registered as a supported modern-language deck target across contracts, runtime/provider maps, local deterministic generation, TTS routing, pronunciation/POS support, and frequency assets.

## Evidence

- `GenerationRequest(language="hu", source_type="frequency")` resolves to `SupportedLanguage.HU`.
- `Settings(_env_file=None).supported_languages` includes `hu`.
- Provider maps include `Hungarian`, DeepL target `HU`, Tatoeba code `hun`, language-id code `hu`, validation markers, and highlight stopwords.
- Library pronunciation resolver order includes `phonemizer-espeak` for `hu`.
- POS inference resolves Hungarian `és` as `conjunction`.
- Azure voice selection returns `hu-HU-NoemiNeural` with locale `hu-HU`; ElevenLabs and Google Translate fallback selectors return Hungarian locales/codes.
- Hungarian frequency assets contain 3000 curated rows with 1000 rows per level and `wordfreq:hu` provenance.

## Commands Run

- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.settings import Settings; assert GenerationRequest(language='hu', source_type='frequency').language is SupportedLanguage.HU; assert 'hu' in Settings(_env_file=None).supported_languages"`
- `uv run python -c "from multilang.domain.jobs import SupportedLanguage; from multilang.services.provider_text_adapters import _DEEPL_TARGET_LANGUAGES, _LANGUAGE_NAMES as text_names; from multilang.services.provider_pronunciation_adapters import _LANGUAGE_NAMES as pronunciation_names; from multilang.services.language_identifier import SUPPORTED_LANGUAGE_CODES; from multilang.services.tatoeba_sentence_source import _TATOEBA_API_CODES; from multilang.services.text_validation import _LANGUAGE_MARKERS; from multilang.services.highlight_candidate_extraction import _STOPWORDS; assert text_names['hu'] == 'Hungarian'; assert _DEEPL_TARGET_LANGUAGES['hu'] == 'HU'; assert pronunciation_names['hu'] == 'Hungarian'; assert 'hu' in SUPPORTED_LANGUAGE_CODES; assert _TATOEBA_API_CODES['hu'] == 'hun'; assert _LANGUAGE_MARKERS['hu']; assert _STOPWORDS[SupportedLanguage.HU]"`
- `uv run python -c "from multilang.services.library_pronunciation_adapters import LibraryPronunciationAdapter; from multilang.services.part_of_speech import infer_function_word_part_of_speech; assert 'phonemizer-espeak' in LibraryPronunciationAdapter().resolver_names_for_language('hu'); assert infer_function_word_part_of_speech(source_language='hu', display_form='és', lemma='és') == 'conjunction'"`
- `uv run pytest tests/domain/test_jobs.py::test_generation_request_accepts_hungarian tests/test_settings.py::test_default_supported_languages_include_hungarian tests/services/test_local_text_adapter.py::test_local_adapter_supports_hungarian tests/services/test_audio_voice_registry.py::test_voice_registry_selects_hungarian_voice tests/services/test_elevenlabs_speech_adapter.py::test_elevenlabs_adapter_uses_default_voice_for_hungarian tests/services/test_google_translate_speech_adapter.py::test_google_translate_adapter_selects_hungarian_language tests/services/test_frequency_decks.py::test_hungarian_frequency_assets_validate tests/cli/test_generate_command.py::test_generate_command_rejects_unsupported_language tests/services/test_text_field_remediation.py::test_remediate_definition_html_infers_function_word_labels_across_supported_languages -q`
- `uv run python scripts/build_frequency_assets.py --check`
- `git diff --check`

## Residual Risk

- Full suite was not run.
- Live provider behavior for Azure, DeepL, Tatoeba, ElevenLabs, and Google Translate was not exercised; this verification covers local routing contracts only.
