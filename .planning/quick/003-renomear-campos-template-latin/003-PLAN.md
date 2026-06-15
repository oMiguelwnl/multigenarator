---
quick: 003-renomear-campos-template-latin
type: quick-plan
task_count: 2
autonomous: true
files_modified:
  - src/multilang/domain/exporting.py
  - src/multilang/services/latin_export.py
  - src/multilang/templates/latin_mvp_card.md
  - tests/services/test_card_template_loader.py
  - tests/services/test_latin_export.py
  - tests/integration/test_v20_existing_modes_regression_evidence.py
  - .planning/quick/003-renomear-campos-template-latin/003-SUMMARY.md
no_ui_proof_rationale: "This quick task changes generated Anki card fields/templates and validates them through APKG/template tests; it does not modify a browser/UI route."
locked_context:
  - "Rename Latin export fields: Latin Word -> Word, Latin Sentence -> Sentence, Gramatica -> Grammar."
  - "Keep Sentence Translation, word_audio, sentence_audio, Image, and SortIndex."
  - "Use the frequency-card visual structure for the Latin template, with Grammar as the extra field."
  - "Do not remove eSpeak NG yet and do not alter audio provider/manifest/runtime behavior."
scope_signal: "This changes the public Latin Anki note field contract but is bounded to Latin export/template files and focused tests."
---

<objective>
Rename the Latin MVP card fields to `Word`, `Sentence`, and `Grammar`, and keep the Latin template aligned with the frequency card visual structure while adding `Grammar` as the Latin-specific extra field.
</objective>

<context>
- `src/multilang/domain/exporting.py` owns `LATIN_EXPORT_CARD_FIELD_NAMES`.
- `src/multilang/services/latin_export.py` maps `LatinExportRow` values into exported field names and loads the `latin_mvp_card` template.
- `src/multilang/templates/latin_mvp_card.md` already mirrors `normal_card.md` styling and must switch references/labels to the renamed fields.
- Tests in `tests/services/test_latin_export.py`, `tests/services/test_card_template_loader.py`, and `tests/integration/test_v20_existing_modes_regression_evidence.py` assert field names, model fields, template references, and existing-mode isolation.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Rename Latin field contract and row mapping</name>
  <files>src/multilang/domain/exporting.py, src/multilang/services/latin_export.py</files>
  <action>
Update the Latin field tuple and row mapping so generated Latin exports use exact field names `Word`, `Sentence`, and `Grammar` instead of `Latin Word`, `Latin Sentence`, and `Gramatica`. Keep internal dataclass attribute names if that is the smallest safe change, but ensure APKG/CSV/TSV exported field names use the new names. Do not alter audio, translation gates, source-pack assets, or provider behavior.
  </action>
  <verify>
    <automated>python -m pytest tests/services/test_latin_export.py -q</automated>
  </verify>
  <done>Latin APKG/CSV/TSV export field names are renamed and focused Latin export tests pass.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Update Latin template and focused evidence tests</name>
  <files>src/multilang/templates/latin_mvp_card.md, tests/services/test_card_template_loader.py, tests/services/test_latin_export.py, tests/integration/test_v20_existing_modes_regression_evidence.py</files>
  <action>
Update `latin_mvp_card.md` to reference `{{Word}}`, `{{Sentence}}`, and `{{Grammar}}`, preserving the frequency-card layout/classes and keeping `Grammar` as the extra Latin-specific field. Update tests to assert the new field names, absence of old names, valid template references, and existing-mode isolation.
  </action>
  <verify>
    <automated>python -m pytest tests/services/test_card_template_loader.py tests/services/test_latin_export.py tests/integration/test_v20_existing_modes_regression_evidence.py -q</automated>
  </verify>
  <done>Template references validate against the renamed Latin field contract and focused tests pass.</done>
</task>

</tasks>

<verification>
Run after implementation:
- `python -m pytest tests/services/test_latin_export.py -q`
- `python -m pytest tests/services/test_card_template_loader.py tests/services/test_latin_export.py tests/integration/test_v20_existing_modes_regression_evidence.py -q`
- `python -m pytest tests/integration/test_v20_latin_export_evidence.py tests/integration/test_v20_final_milestone_evidence.py -q`

Confirm no eSpeak/audio provider files or audio manifests changed.
</verification>

<success_criteria>
- Latin generated fields use `Word`, `Sentence`, and `Grammar`.
- Old field names `Latin Word`, `Latin Sentence`, and `Gramatica` are absent from Latin export field names and template references.
- Latin template preserves the frequency-card visual structure and adds `Grammar` as the extra field.
- Focused export/template/evidence tests pass.
- No audio/eSpeak behavior changes.
</success_criteria>

<output>
After execution, create `.planning/quick/003-renomear-campos-template-latin/003-SUMMARY.md` and `.planning/quick/003-renomear-campos-template-latin/003-VERIFICATION.md`, then update `.planning/quick/LOG.md`.
</output>
