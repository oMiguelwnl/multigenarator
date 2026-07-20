# Quick Task 025 Plan: Japanese Export Routing

## Objective

Route dynamic Japanese generation/export rows to the existing Japanese Anki note type, field order, and template.

Approach context: This is stage 4 of the split Japanese pipeline work. Stages 1-3 registered Japanese defaults/provider routing, added frequency assets, and added generation/validation support. This task completes the pipeline-side export routing while leaving full contextual furigana generation for a future morphology milestone.

No UI proof rationale: This task changes backend export contracts and Anki template routing only; it has no rendered web UI surface.

## Task 1: Add Japanese Export Field Resolution

<files>
- `src/multilang/domain/exporting.py`
- `src/multilang/services/card_template_loader.py`
- `src/multilang/services/export_anki_package.py`
- `src/multilang/runtime.py`
- `tests/services/test_card_template_loader.py`
- `tests/services/test_export_anki_package.py`
</files>

<action>
- Add `JAPANESE_EXPORT_CARD_FIELD_NAMES` matching the existing `JAPANESE_FIELD_NAMES` contract.
- Resolve export fields by row language so `language=ja` uses Japanese fields while other frequency rows keep the normal field order.
- Load `japanese_card.md` for Japanese rows and use the existing Japanese model id/note type name in APKG export.
- Return `Multilang::Japanese Card` for Japanese tabular exports.
</action>

<done>
- `build_multilang_model(source_type="frequency", language=SupportedLanguage.JA)` uses the Japanese note type, fields, and template.
- `export_field_names_for_rows()` returns Japanese fields for Japanese rows and normal fields for non-Japanese rows.
</done>

<verify>
- `uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py -q`
</verify>

## Task 2: Assemble Japanese Export Rows Without IPA Field Dependency

<files>
- `src/multilang/services/assemble_export_cards.py`
- `tests/services/test_assemble_export_cards.py`
</files>

<action>
- Allow Japanese export assembly to omit the normal IPA field because the Japanese template does not export IPA.
- Map Japanese export rows to `Target Word`, `Word Reading`, `Definition`, `Sentence`, `Sentence Furigana`, `Sentence Translation`, audio, and blank image through `ExportCardRow.ordered_field_mapping()`.
- Use raw word/sentence as reading/furigana fallbacks until contextual furigana generation is implemented.
- Add focused assembly coverage for a Japanese row.
</action>

<done>
- Japanese assembled rows can be exported through the Japanese field tuple without missing-IPA failure.
- Existing non-Japanese assembly still requires IPA and keeps current behavior.
</done>

<verify>
- `uv run pytest tests/services/test_assemble_export_cards.py::test_assemble_export_cards_builds_japanese_row_without_ipa tests/services/test_assemble_export_cards.py::test_assemble_export_cards_fails_fast_on_missing_export_prerequisites -q`
</verify>

## Final Verification

<verify>
- `uv run pytest tests/services/test_japanese_frequency_deck.py tests/services/test_frequency_decks.py::test_japanese_frequency_assets_validate tests/domain/test_jobs.py tests/test_settings.py -q`
</verify>
