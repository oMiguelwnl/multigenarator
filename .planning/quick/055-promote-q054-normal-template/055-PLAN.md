# Quick Task 055 Plan: Promote Q054 Normal Template

## Objective

Promote the user-approved Q054 black-background, top-positioned, left-padded, fixed-audio layout into the production normal Anki card template used by frequency exports.

## Scope

Modify only the production normal template and its focused contract tests. Do not alter generated card data, field order, note model IDs, audio generation, Latin/Japanese/highlight/manual templates, or ROADMAP/SPEC phase artifacts.

## Must-Haves

- Production normal template keeps the existing front/back field contract and translation reveal behavior.
- Desktop layout uses the approved Q054 geometry: black page background, card near the top with 16px outer top padding, `680px` maximum width, `32px 40px` card padding, left-aligned/LTR natural wrapping, no horizontal scroll, and fixed `32px` audio columns.
- Narrow layout at `<=720px` uses `12px` outer horizontal padding, `width: calc(100vw - 24px)`, and `24px 20px` card padding.
- Regression tests prove the effective production CSS contract and export model CSS contract.

## Tasks

### 1. Lock approved template contract in tests

<action>
Update focused tests in `tests/services/test_card_template_loader.py` and `tests/services/test_export_anki_package.py` to assert the Q054 production contract: 680px card width, 16px top placement, 32px/40px desktop padding, 12px/20px narrow gutters, natural left/LTR wrapping, no overflow-x auto, and 32px audio columns.
</action>

<files>
- `tests/services/test_card_template_loader.py`
- `tests/services/test_export_anki_package.py`
</files>

<verify>
Run `uv run pytest tests/services/test_card_template_loader.py::test_normal_frequency_template_uses_production_dark_layout_contract tests/services/test_export_anki_package.py::test_build_multilang_model_uses_project_card_template_sections -q` and confirm the new/updated assertions fail before the template edit.
</verify>

### 2. Promote Q054 layout into the normal template

<action>
Update `src/multilang/templates/normal_card.md` canonical terminal CSS so normal frequency exports use the approved Q054 layout while preserving existing front/back HTML and field references.
</action>

<files>
- `src/multilang/templates/normal_card.md`
</files>

<verify>
Run `uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py::test_build_multilang_model_uses_project_card_template_sections tests/integration/test_v13_normal_template_export_contract.py::test_normal_apkg_omits_front_of_card_and_exports_responsive_sentence_layout -q`.
</verify>

## UI Proof Rationale

No new live UI proof slot is required for this quick task because the visual design was already accepted through the Q054 dummy APKG. This task promotes that approved contract into the production template and verifies the generated model CSS structurally; native Anki rendering remains outside automated project tooling.
