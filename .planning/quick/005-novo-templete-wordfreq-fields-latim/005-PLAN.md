# Quick Task 005 Plan: Novo Template Wordfreq + Campos Latim

## Objective

Create a Latin MVP Anki template that copies the existing wordfreq/normal-card visual structure and styling, adapts it to the current Latin export fields, and wires Latin MVP APKG generation to use that template without defining or changing the future Latin word-source strategy.

## Approach Context

User confirmed: create only the template and add it to Latin generation. Do not decide whether future Latin generation uses wordfreq or another source.

## Codebase Context

The modern frequency template lives in `src/multilang/templates/normal_card.md` and is loaded through `src/multilang/services/card_template_loader.py`. Latin MVP export is intentionally isolated in `src/multilang/services/latin_export.py` with stable `LATIN_EXPORT_FIELD_NAMES`; current Latin generation/export commands use committed assets and do not route through the modern frequency pipeline. Template/field changes are fragile contract surfaces and must be verified with focused tests rather than the known-red full suite. Avoid touching runtime generation source selection, Latin assets, audio policy, review gates, or broad export behavior.

## Tasks

### Task 1: Add Latin MVP template based on wordfreq card

<files>
src/multilang/templates/latin_mvp_card.md
src/multilang/services/card_template_loader.py
src/multilang/domain/exporting.py
</files>

<action>
Create `latin_mvp_card.md` using the existing `normal_card.md` structure and CSS as the base, with Latin field references from the current Latin card contract: `SortIndex`, `Latin Word`, `Latin Sentence`, `Sentence Translation`, `Gramatica`, `word_audio`, `sentence_audio`, and `Image`. Register `latin_mvp_card` in the template loader and make `export_field_names_for_source_type("latin-mvp")` return the Latin field tuple so loader validation can prove the template matches the Latin schema.
</action>

<verify>
uv run pytest tests/services/test_card_template_loader.py tests/domain/test_exporting.py -q
</verify>

<done>
`latin_mvp_card.md` exists, is parseable by the card template loader, preserves the wordfreq-style structure/CSS, and validates against the Latin MVP export field tuple.
</done>

### Task 2: Wire Latin APKG generation to use the new template

<files>
src/multilang/services/latin_export.py
tests/services/test_latin_export.py
tests/services/test_card_template_loader.py
</files>

<action>
Update `build_latin_anki_model()` to load the new `latin_mvp_card` template instead of the inline minimal Latin HTML/CSS, preserving the existing Latin model ID, note type name, field order, media handling, and CSV/TSV output behavior. Add focused assertions that the loaded Latin template uses the wordfreq-style structure while referencing only Latin export fields.
</action>

<verify>
uv run pytest tests/services/test_latin_export.py tests/services/test_card_template_loader.py -q
</verify>

<done>
`build_latin_anki_model()` uses the new Latin template while preserving the existing Latin note type, model ID, field order, media behavior, and tabular export contract.
</done>

## UI Proof

no_ui_proof_rationale: This is an Anki template/export contract change, not a rendered web UI change. Verification is via parser/model/export tests that inspect generated template/model fields and APKG contents.

## Final Verification

Run:

```bash
uv run pytest tests/services/test_card_template_loader.py tests/domain/test_exporting.py tests/services/test_latin_export.py -q
```
