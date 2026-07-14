# Quick Task 013 Plan: Full Suite Repair

## Objective

Repair the unrelated failures exposed by the full `uv run pytest` run after the IPA resolver work, keeping product behavior current and avoiding regressions in the pronunciation changes.

## Task 1: Restore Missing Evidence And Candidate Assets
<files>
- `data/latin_mvp/source_candidates.json`
- `.planning/phases/16-end-to-end-v12-audit/16-V12-AUDIT-EVIDENCE.md`
- `.planning/phases/21-validation-fixtures-and-milestone-evidence/21-V13-MILESTONE-EVIDENCE.md`
</files>
<action>
Create the missing scanner-readable assets required by existing tests, with candidate-only source metadata and privacy-safe evidence summaries.
</action>
<done>
The missing file failures are eliminated without changing runtime behavior.
</done>
<verify>
Run `uv run pytest tests/domain/test_latin_source_candidates.py tests/integration/test_v12_final_audit_evidence.py tests/integration/test_v13_final_milestone_evidence.py -q`.
</verify>

## Task 2: Align Obsolete Latin Evidence Tests With Current Product State
<files>
- `tests/cli/test_generate_latin_mvp_command.py`
- `tests/integration/test_v20_latin_audio_evidence.py`
- `tests/integration/test_v20_latin_portuguese_translation_evidence.py`
- `tests/integration/test_v20_latin_review_curation_asset.py`
- `tests/integration/test_v20_latin_review_gate_evidence.py`
- `tests/integration/test_v20_latin_source_pack_asset.py`
- `tests/integration/test_v20_latin_source_pack_evidence.py`
</files>
<action>
Update assertions that still describe earlier phase boundaries so they validate the current completed Latin state: Latin is registered, translation/audio gates are approved, current attribution text is accepted, and target-match assertions match the committed source pack.
</action>
<done>
Latin evidence tests validate current artifacts instead of requiring older in-progress phase states.
</done>
<verify>
Run `uv run pytest tests/cli/test_generate_latin_mvp_command.py tests/integration/test_v20_latin_audio_evidence.py tests/integration/test_v20_latin_portuguese_translation_evidence.py tests/integration/test_v20_latin_review_curation_asset.py tests/integration/test_v20_latin_review_gate_evidence.py tests/integration/test_v20_latin_source_pack_asset.py tests/integration/test_v20_latin_source_pack_evidence.py -q`.
</verify>

## Task 3: Isolate Audio/Export Integration Tests From Local Environment
<files>
- `tests/integration/test_custom_word_list_e2e_export_flow.py`
- `tests/integration/test_export_job_flow.py`
</files>
<action>
Make the affected E2E tests explicit about local provider settings so `.env` values such as ElevenLabs do not override their fake Azure adapter assumptions.
</action>
<done>
Export/audio E2E tests generate files through the fake Azure adapter and pass consistently regardless of local `.env` audio provider values.
</done>
<verify>
Run `uv run pytest tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_export_job_flow.py tests/integration/test_v12_existing_mode_regression_boundary.py tests/integration/test_v12_phonetics_and_existing_modes_audit.py -q` and then `uv run pytest`.
</verify>

## No UI Proof Rationale

This task repairs backend tests, fixtures, and scanner-readable evidence files only; it has no rendered UI surface.
