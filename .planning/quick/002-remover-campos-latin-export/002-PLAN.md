---
quick: 002-remover-campos-latin-export
type: quick-plan
task_count: 2
autonomous: true
files_modified:
  - src/multilang/services/latin_export.py
  - tests/services/test_latin_export.py
  - tests/integration/test_v20_latin_export_evidence.py
  - tests/integration/test_v20_existing_modes_regression_evidence.py
  - .planning/quick/002-remover-campos-latin-export/002-SUMMARY.md
no_ui_proof_rationale: "This quick task changes a generated Anki export/card schema and test evidence only; it does not add or modify UI, browser routes, visual layout outside the Anki template string, or interactive behavior."
locked_context:
  - "User confirmed removing Translation, Lemma, and Source from everything: generation/export/schema, not just hiding them."
  - "Do not remove Sentence Translation or Gramatica."
  - "Do not alter source pack, Portuguese translation asset, audio manifest, review gates, modern-language exports, ROADMAP.md, or SPEC.md."
scope_signal: "This changes a public Anki note field contract. Keep the quick task bounded to the Latin export contract and focused regression evidence."
---

<objective>
Remove the Latin MVP export fields `Translation`, `Lemma`, and `Source` entirely from generated Latin cards so they do not exist in the Latin Anki note model, CSV/TSV headers, or generated export row mappings.

Purpose: align the Latin card field contract with the user's requested learner-facing shape while preserving `Sentence Translation`, `Gramatica`, audio, image, export gates, and existing mode isolation.
</objective>

<context>
Implementation surface:
- `src/multilang/services/latin_export.py` owns `LATIN_EXPORT_FIELD_NAMES`, `LatinExportRow`, export row assembly, Anki model/template, APKG notes, and CSV/TSV headers.
- `tests/services/test_latin_export.py` programmatically checks field order, row mapping, APKG model fields, and CSV/TSV output.
- `tests/integration/test_v20_latin_export_evidence.py` checks committed Latin export evidence.
- `tests/integration/test_v20_existing_modes_regression_evidence.py` checks Latin note isolation against existing export modes.

Risk controls:
- Keep `Sentence Translation` in the export.
- Keep Portuguese translation asset validation/gates intact even if short `Translation` is no longer exported; the existing translation pack can still be used to provide `Sentence Translation` and approval status.
- Do not remove source/privacy validation from assets unless it is only checking the removed exported `Source` field; source provenance remains in source/curation assets.
- Do not touch modern export contracts.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Remove fields from Latin export contract</name>
  <files>src/multilang/services/latin_export.py</files>
  <action>
Update the Latin export contract so `Translation`, `Lemma`, and `Source` are absent from `LATIN_EXPORT_FIELD_NAMES`, `LatinExportRow`, `ordered_field_mapping()`, and the Anki back template. Remove row assembly assignments for those exported fields while keeping any loader/validator calls needed for fail-closed translation/source/audio readiness. Preserve `SortIndex`, `Latin Word`, `Latin Sentence`, `Sentence Translation`, `Gramatica`, `word_audio`, `sentence_audio`, and `Image`.
  </action>
  <verify>
    <automated>python -m pytest tests/services/test_latin_export.py -q</automated>
  </verify>
  <done>`Translation`, `Lemma`, and `Source` no longer appear in the Latin field tuple, row mapping, Anki model fields, or rendered template, and focused service tests pass.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Update focused export evidence tests</name>
  <files>tests/services/test_latin_export.py, tests/integration/test_v20_latin_export_evidence.py, tests/integration/test_v20_existing_modes_regression_evidence.py</files>
  <action>
Update focused tests to assert the new field contract exactly and to prove removed fields are absent from APKG model fields, CSV/TSV headers, row mappings, and Latin model templates. Keep existing checks for 50 rows, 100 media refs, sound tags, blank `Image`, no `Classe`, and model isolation against normal/manual/highlight/phoneme exports. Adjust column index assertions to the new field order.
  </action>
  <verify>
    <automated>python -m pytest tests/services/test_latin_export.py tests/integration/test_v20_latin_export_evidence.py tests/integration/test_v20_existing_modes_regression_evidence.py -q</automated>
  </verify>
  <done>Focused service and integration evidence tests pass and demonstrate the removed fields do not exist in generated Latin exports.</done>
</task>

</tasks>

<verification>
Run after implementation:
- `python -m pytest tests/services/test_latin_export.py -q`
- `python -m pytest tests/services/test_latin_export.py tests/integration/test_v20_latin_export_evidence.py tests/integration/test_v20_existing_modes_regression_evidence.py -q`
- `git diff -- src/multilang/services/latin_export.py tests/services/test_latin_export.py tests/integration/test_v20_latin_export_evidence.py tests/integration/test_v20_existing_modes_regression_evidence.py`

Confirm no runtime provider, source-pack, audio manifest, translation asset, ROADMAP, or SPEC changes were introduced.
</verification>

<success_criteria>
- `Translation`, `Lemma`, and `Source` do not exist as Latin export fields.
- `Sentence Translation`, `Gramatica`, `word_audio`, `sentence_audio`, and blank `Image` remain.
- Latin APKG, CSV, and TSV tests pass with the new field order.
- Existing mode isolation evidence remains passing.
</success_criteria>

<output>
After execution, create `.planning/quick/002-remover-campos-latin-export/002-SUMMARY.md` with changed files, verification results, and confirmation that the change is limited to the Latin export field contract.
</output>
