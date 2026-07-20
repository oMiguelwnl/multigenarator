# Quick Task 024 Summary: Japanese Generation And Validation Support

## Status

Completed.

## Implemented

- Added Japanese prompt naming for pronunciation generation.
- Added Japanese stopwords, Tatoeba API routing (`jpn`), local sentence/translation templates, local definition labels, fallback TTS mappings, and closed-class POS inference.
- Added Japanese-aware text validation for no-space sentences using substring target matching, character-count length checks, and deterministic Japanese script detection.
- Avoided adding `ja` to corpus `wordfreq` language-id because that path requires optional `MeCab`; Japanese target validation now uses script heuristics instead.
- Added focused tests for local Japanese generation, fallback TTS selection, and Japanese validation.

## Verification

- Passed: `uv run pytest tests/services/test_local_text_adapter.py tests/services/test_elevenlabs_speech_adapter.py tests/services/test_google_translate_speech_adapter.py -q` (`44 passed`)
- Passed: `uv run pytest tests/services/test_text_validation.py::test_validation_accepts_no_space_japanese_sentence tests/services/test_text_validation.py::test_validation_rejects_non_japanese_sentence_for_japanese_target -q` (`2 passed`)
- Passed: smoke assertion for Tatoeba `jpn`, pronunciation name, highlight stopwords, and Japanese particle POS inference.

## Deferred

- Stage 4: Japanese export routing to `Multilang::Japanese Card`.
