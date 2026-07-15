# Quick Task 021 Verification: Add Greek With Phonetic Deck

## Verdict

Passed.

## Goal Check

- Greek is now a supported modern language using code `el`.
- Greek frequency deck assets exist and validate with 3 levels of 1000 cards.
- Greek has a separate introductory phoneme deck export command: `export-greek-phonemes`.

## Evidence

- `GenerationRequest(language='el', source_type='frequency')` resolves to `SupportedLanguage.EL`.
- `Settings(_env_file=None).supported_languages` includes `el`.
- Provider maps include Greek language names, DeepL `EL`, Tatoeba `ell`, local text templates, validation markers, stopwords, and TTS routing.
- `assets/frequency/el/curated-v1.csv` contains 3000 `wordfreq:el` rows; `rejections-v1.csv` exists and validates.
- `tests/services/test_frequency_decks.py` passed with all supported-language asset validation.
- `tests/services/test_russian_phoneme_deck.py` passed and covers Greek phoneme cards/model/APKG export.
- CLI smoke wrote `.multilang/exports/greek-phonemes-smoke.apkg` with `card_count=2`.

## Commands Run

- `uv run python scripts/build_frequency_assets.py --language el`
- `uv run python scripts/build_frequency_assets.py --check --language el`
- `uv run python scripts/build_frequency_assets.py --check`
- `uv run pytest tests/services/test_frequency_decks.py -q`
- `uv run pytest tests/domain/test_jobs.py tests/test_settings.py tests/services/test_audio_voice_registry.py tests/services/test_elevenlabs_speech_adapter.py tests/services/test_google_translate_speech_adapter.py tests/services/test_local_text_adapter.py tests/services/test_text_field_remediation.py tests/services/test_russian_phoneme_deck.py tests/cli/test_generate_command.py::test_export_greek_phonemes_command_writes_limited_deck -q`
- `uv run python -m multilang.cli export-greek-phonemes --output-path .multilang/exports/greek-phonemes-smoke.apkg --limit 2`

## Residual Risk

- The Greek phoneme deck is deterministic introductory content, not a native-speaker-audited pronunciation curriculum.
- Live Azure audio quality still depends on configured Azure credentials and the available regional voice inventory.
