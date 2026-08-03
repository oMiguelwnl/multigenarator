# Quick Task 029 Plan: Japanese Frequency Preview Template

## Objective

Make the Japanese frequency Anki template use the structure and visual language from `ja_freq_v3_preview.html` while preserving the current Japanese frequency field contract.

No UI proof rationale: this task changes an Anki HTML/CSS template and validates rendered template references through tests/APKG inspection; no browser UI route exists in the app.

## Task 1: Replace Japanese Frequency Template Structure

<files>
- `src/multilang/templates/japanese_card.md`
</files>

<action>
- Rework the front/back HTML to use the preview's `customCard`, `targetWordContainer`, `targetWord`, `jPlain`, `jReading`, `furiganaToggle`, `definitionsList`, `exampleSentenceLine`, `sentenceTranslation`, and `jpLinks` structure.
- Preserve the existing fields: `SortIndex`, `Target Word`, `Word Reading`, `Definition`, `Sentence`, `Sentence Furigana`, `Sentence Translation`, `word_audio`, `sentence_audio`, `Image`.
- Keep Anki `{{furigana:...}}` rendering for `Word Reading` and `Sentence Furigana`.
</action>

<verify>
- Template reference validation passes for `JAPANESE_EXPORT_CARD_FIELD_NAMES`.
</verify>

## Task 2: Update Template Expectations

<files>
- `tests/services/test_card_template_loader.py`
- `tests/services/test_export_anki_package.py`
- `tests/services/test_japanese_frequency_deck.py`
</files>

<action>
- Update tests so they assert the preview-based class names and links.
- Keep field-order and note-type assertions unchanged.
</action>

<verify>
- `uv run pytest tests/services/test_card_template_loader.py::test_project_japanese_template_uses_japanese_fields_and_furigana_filter tests/services/test_export_anki_package.py::test_build_japanese_frequency_model_uses_japanese_note_type_and_template tests/services/test_japanese_frequency_deck.py::test_build_japanese_model_uses_template_and_field_order -q`
</verify>
