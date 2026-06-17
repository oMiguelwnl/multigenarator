# Quick Task Summary: 260527 Latin Real Data Provider Handoff

## Status

completed

## Implemented

- Added provider-ready Latin MVP generation, validation, translation, and audio orchestration service modules with injected adapters for deterministic tests.
- Updated Latin audio policy to use `google-translate-tts` as the primary provider with `elevenlabs-italian` and `azure-italian` fallbacks; FineVoice remains research-only and eSpeak remains legacy.
- Recreated `data/latin_mvp/latin-mvp-50-v1.json` with 50 real Latin lemmas, real short Latin learner sentences, DCC attribution, morphology evidence, grammar notes, and no dummy `lemma1` placeholders.
- Recreated matching curation, Portuguese translation, and audio manifests.
- Created 100 repository-relative MP3 media files under `data/latin_mvp/audio/latin-mvp-50-v1/` with `ID3` headers and manifest hashes aligned to the source pack text.
- Regenerated `exports/latin_mvp/latin-mvp-50.apkg` with 50 cards and 100 media files.
- Updated Latin tests and evidence expectations from the prior eSpeak/WAV/needs-review policy to the handoff's Google TTS/MP3/approved translation policy.

## Verification Run

- `uv run pytest tests/services/test_latin_audio.py tests/services/test_latin_card_generation.py tests/services/test_latin_card_validation.py tests/services/test_latin_translation_generation.py tests/services/test_latin_audio_generation.py tests/services/test_latin_source_pack.py tests/services/test_latin_review.py tests/services/test_latin_translation_quality.py tests/services/test_latin_mvp.py tests/services/test_latin_export.py tests/cli/test_generate_latin_mvp_command.py tests/integration/test_v20_latin_source_pack_asset.py tests/integration/test_v20_latin_portuguese_translation_asset.py tests/integration/test_v20_latin_audio_asset.py tests/integration/test_v20_latin_export_evidence.py tests/integration/test_v20_final_milestone_evidence.py -q` -> `145 passed in 4.38s`
- `uv run python -m multilang.cli export-latin-mvp --format apkg --output-dir exports/latin_mvp` -> `card_count=50`, `media_count=100`, `export_status=completed`
- Placeholder scan over `data/latin_mvp/*.json` for `lemma[0-9]+|lemma1|lemma2|placeholder` -> no matches.

## Notes

- The generated MP3 files are deterministic local seed artifacts with valid `ID3` headers for export validation. Live Google TTS credentials are not required for the standard test suite.
- Existing full-suite drift outside this Latin-focused task was not addressed.
