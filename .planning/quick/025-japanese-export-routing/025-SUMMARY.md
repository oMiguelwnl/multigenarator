# Quick Task 025 Summary: Japanese Export Routing

## Status

Completed.

## Implemented

- Added `JAPANESE_EXPORT_CARD_FIELD_NAMES` matching the existing Japanese card schema.
- Routed Japanese frequency templates through `japanese_card.md` and validated Anki filter references like `{{furigana:Word Reading}}`.
- Routed Japanese frequency APKG models to `Multilang::Japanese Card` using the existing Japanese model id.
- Routed Japanese tabular note type naming to `Multilang::Japanese Card`.
- Allowed Japanese frequency assembly without requiring a normal IPA export field.
- Mapped Japanese dynamic export rows to `Target Word`, `Word Reading`, `Definition`, `Sentence`, `Sentence Furigana`, `Sentence Translation`, audio fields, and blank image.
- Added focused tests for template loading, APKG model/note field order, and Japanese assembly without IPA.

## Verification

- Passed: `uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py -q` (`40 passed`)
- Passed: `uv run pytest tests/services/test_assemble_export_cards.py::test_assemble_export_cards_builds_japanese_row_without_ipa tests/services/test_assemble_export_cards.py::test_assemble_export_cards_fails_fast_on_missing_export_prerequisites -q` (`4 passed`)
- Passed: `uv run pytest tests/services/test_japanese_frequency_deck.py tests/services/test_frequency_decks.py::test_japanese_frequency_assets_validate tests/domain/test_jobs.py tests/test_settings.py -q` (`37 passed`)

## Deferred

- Contextual furigana generation remains deferred. Dynamic export currently uses raw word/sentence as `Word Reading` and `Sentence Furigana` fallbacks.
