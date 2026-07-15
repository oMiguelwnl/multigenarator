# Quick Task 020 Verification: Add Croatian

## Verdict

passed

## Goal Check

The task requested adding Croatian to the project. Croatian (`hr`) is now available through the modern-language flow:

- `GenerationRequest(language="hr", ...)` parses to `SupportedLanguage.HR`.
- `Settings(_env_file=None).supported_languages` includes `hr`.
- Runtime, provider, validation, highlight, local text, pronunciation, POS, Tatoeba, DeepL, Azure, ElevenLabs, and Google Translate maps include Croatian entries.
- `assets/frequency/hr/curated-v1.csv` contains exactly 3000 curated rows across 3 levels of 1000 rows.
- `assets/frequency/hr/rejections-v1.csv` exists and validates.

## Evidence

- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.settings import Settings; assert GenerationRequest(language='hr', source_type='frequency').language is SupportedLanguage.HR; assert 'hr' in Settings(_env_file=None).supported_languages"`
- `uv run python -c "from multilang.domain.jobs import SupportedLanguage; from multilang.services.provider_text_adapters import _DEEPL_TARGET_LANGUAGES, _LANGUAGE_NAMES as text_names; from multilang.services.provider_pronunciation_adapters import _LANGUAGE_NAMES as pronunciation_names; from multilang.services.language_identifier import SUPPORTED_LANGUAGE_CODES; from multilang.services.tatoeba_sentence_source import _TATOEBA_API_CODES; from multilang.services.text_validation import _LANGUAGE_MARKERS; from multilang.services.highlight_candidate_extraction import _STOPWORDS; assert text_names['hr'] == 'Croatian'; assert _DEEPL_TARGET_LANGUAGES['hr'] == 'HR'; assert pronunciation_names['hr'] == 'Croatian'; assert 'hr' in SUPPORTED_LANGUAGE_CODES; assert _TATOEBA_API_CODES['hr'] == 'hrv'; assert _LANGUAGE_MARKERS['hr']; assert _STOPWORDS[SupportedLanguage.HR]"`
- `uv run python -c "from multilang.services.library_pronunciation_adapters import LibraryPronunciationAdapter; from multilang.services.part_of_speech import infer_function_word_part_of_speech; assert 'phonemizer-espeak' in LibraryPronunciationAdapter().resolver_names_for_language('hr'); assert infer_function_word_part_of_speech(source_language='hr', display_form='i', lemma='i') == 'conjunction'"`
- `uv run pytest tests/domain/test_jobs.py tests/test_settings.py tests/services/test_frequency_decks.py tests/services/test_audio_voice_registry.py tests/services/test_elevenlabs_speech_adapter.py tests/services/test_google_translate_speech_adapter.py tests/services/test_local_text_adapter.py tests/services/test_text_field_remediation.py tests/services/test_highlight_candidate_extraction.py tests/services/test_text_validation.py -q` passed with `178 passed in 3.39s`.
- `uv run python scripts/build_frequency_assets.py --check --language hr` passed.
- `uv run python scripts/build_frequency_assets.py --check` passed.
- `git diff --check` passed with Windows LF/CRLF normalization warnings only.

## Residual Risk

- Live provider calls were not made. Azure, DeepL, ElevenLabs, Google Translate, Tatoeba, and LLM paths are covered here by routing/configuration tests, not by network integration tests.
- Croatian frequency data is seeded from `wordfreq`'s nearest supported corpus code `sh`; this is recorded in `source_provenance` and should be reviewed if higher-quality Croatian-specific assets become available.
