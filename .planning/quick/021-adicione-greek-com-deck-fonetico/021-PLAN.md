# Quick Task 021 Plan: Add Greek With Phonetic Deck

## Objective

Add Modern Greek (`el`) as a supported language for normal frequency deck generation and add a dedicated introductory Greek phoneme deck export path.

Approach context: The request says Greek atual, so this plan uses Modern Greek with ISO code `el`, Azure locale `el-GR`, DeepL target `EL`, and Tatoeba code `ell`. Azure documentation confirms current Greek TTS voices `el-GR-AthinaNeural` and `el-GR-NestorasNeural`; DeepL documentation confirms Greek target code `EL`.

Planner note: `.planning/templates/roles/planner.md` and `.planning/templates/delegates/plan-checker.md` are absent, so this plan follows the quick-task contract directly with reduced planner/checker-template assurance.

No UI proof rationale: This task changes CLI/domain/provider configuration, data assets, and Anki export services only; it has no rendered web UI surface.

## Task 1: Register `el` Across Modern-Language Contracts

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
- `src/multilang/services/audio_voice_registry.py`
- `src/multilang/services/elevenlabs_speech_adapter.py`
- `src/multilang/services/google_translate_speech_adapter.py`
- `tests/domain/test_jobs.py`
- `tests/test_settings.py`
- `tests/services/test_audio_voice_registry.py`
- `tests/services/test_elevenlabs_speech_adapter.py`
- `tests/services/test_google_translate_speech_adapter.py`
- `tests/services/test_local_text_adapter.py`
- `tests/services/test_text_field_remediation.py`
</files>

<action>
- Add `SupportedLanguage.EL = "el"` and include `el` in typed settings defaults.
- Add Greek language names, DeepL target mapping, Tatoeba API routing, corpus language-id support, deterministic local templates, text validation markers, highlight stopwords, function-word POS inference, and pronunciation resolver maps.
- Add Azure, ElevenLabs, and Google Translate TTS voice/locale routing for Greek using `el-GR` where supported.
- Add focused tests proving Greek is parsed, appears in defaults, and resolves through local text and TTS paths.
</action>

<done>
- `GenerationRequest(language="el", ...)` parses to `SupportedLanguage.EL`.
- Default settings expose `el` in `supported_languages`.
- Greek has deterministic provider/local/audio mappings without key errors.
</done>

<verify>
- `uv run python -c "from multilang.domain.jobs import GenerationRequest, SupportedLanguage; from multilang.settings import Settings; assert GenerationRequest(language='el', source_type='frequency').language is SupportedLanguage.EL; assert 'el' in Settings(_env_file=None).supported_languages"`
- `uv run python -c "from multilang.domain.jobs import SupportedLanguage; from multilang.services.provider_text_adapters import _DEEPL_TARGET_LANGUAGES, _LANGUAGE_NAMES as text_names; from multilang.services.provider_pronunciation_adapters import _LANGUAGE_NAMES as pronunciation_names; from multilang.services.language_identifier import SUPPORTED_LANGUAGE_CODES; from multilang.services.tatoeba_sentence_source import _TATOEBA_API_CODES; from multilang.services.text_validation import _LANGUAGE_MARKERS; from multilang.services.highlight_candidate_extraction import _STOPWORDS; assert text_names['el'] == 'Greek'; assert _DEEPL_TARGET_LANGUAGES['el'] == 'EL'; assert pronunciation_names['el'] == 'Greek'; assert 'el' in SUPPORTED_LANGUAGE_CODES; assert _TATOEBA_API_CODES['el'] == 'ell'; assert _LANGUAGE_MARKERS['el']; assert _STOPWORDS[SupportedLanguage.EL]"`
- `uv run pytest tests/domain/test_jobs.py::test_generation_request_accepts_greek tests/test_settings.py::test_default_supported_languages_include_greek tests/services/test_audio_voice_registry.py::test_voice_registry_selects_greek_voice tests/services/test_elevenlabs_speech_adapter.py::test_elevenlabs_adapter_uses_default_voice_for_greek tests/services/test_google_translate_speech_adapter.py::test_google_translate_adapter_selects_greek_language tests/services/test_local_text_adapter.py::test_local_adapter_supports_greek tests/services/test_text_field_remediation.py -q`
</verify>

## Task 2: Add Greek Frequency Assets

<files>
- `assets/frequency/el/curated-v1.csv`
- `assets/frequency/el/rejections-v1.csv`
- `tests/services/test_frequency_decks.py`
</files>

<action>
- Generate committed Greek frequency assets with 3 levels of 1000 rows from `wordfreq` using the existing curated frequency schema and structural curation flags.
- Add focused frequency-asset validation for `SupportedLanguage.EL`.
</action>

<done>
- Greek curated and rejection CSV assets exist under `assets/frequency/el/`.
- Greek validates with exactly 1000 curated rows in each frequency level.
</done>

<verify>
- `uv run python scripts/build_frequency_assets.py --language el`
- `uv run python scripts/build_frequency_assets.py --check --language el`
- `uv run pytest tests/services/test_frequency_decks.py::test_greek_frequency_assets_validate -q`
</verify>

## Task 3: Add Greek Phoneme Deck Export

<files>
- `src/multilang/services/russian_phoneme_deck.py`
- `src/multilang/cli.py`
- `tests/services/test_russian_phoneme_deck.py`
- `tests/cli/test_generate_command.py`
</files>

<action>
- Add a small deterministic Modern Greek phoneme card set using the existing nine-field phoneme contract and template.
- Add Greek phoneme model/deck constants, model/note builders, and `export_greek_phoneme_deck`.
- Add `export-greek-phonemes` CLI command with the same `--output-path`, `--deck-name`, and `--limit` behavior as Russian/Polish phoneme exports.
- Add focused tests for Greek card data, model/template reuse, APKG writing, and limited CLI export.
</action>

<done>
- `uv run python -m multilang.cli export-greek-phonemes --output-path ... --limit 2` writes a Greek phoneme APKG.
- Greek phoneme cards reuse `PHONEME_FIELD_NAMES` and the existing template without changing Russian/Polish contracts.
</done>

<verify>
- `uv run pytest tests/services/test_russian_phoneme_deck.py tests/cli/test_generate_command.py::test_export_greek_phonemes_command_writes_limited_deck -q`
- `uv run python -m multilang.cli export-greek-phonemes --output-path .multilang/exports/greek-phonemes-smoke.apkg --limit 2`
</verify>
