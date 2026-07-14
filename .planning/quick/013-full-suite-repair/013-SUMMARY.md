# Quick Task 013 Summary: Full Suite Repair

## Status

Completed.

## What Changed

- Added missing Latin source-candidate fixture at `data/latin_mvp/source_candidates.json`.
- Added missing scanner-readable evidence files for v12 and v13 milestone tests:
  - `.planning/phases/16-end-to-end-v12-audit/16-V12-AUDIT-EVIDENCE.md`
  - `.planning/phases/21-validation-fixtures-and-milestone-evidence/21-V13-MILESTONE-EVIDENCE.md`
- Updated stale Latin tests that still described earlier in-progress phase states:
  - Latin is now registered as `SupportedLanguage.LA` while frequency generation remains blocked for `la`.
  - Latin translation and audio gates are now approved in the committed curation asset.
  - Current source-pack attribution and exact target-match modes are accepted.
- Isolated affected audio/export integration tests from local `.env` values by setting `_env_file=None` and `audio_provider="azure"` where those tests rely on the fake Azure adapter.

## Verification

Passed:

- `uv run pytest tests/domain/test_latin_source_candidates.py tests/integration/test_v12_final_audit_evidence.py tests/integration/test_v13_final_milestone_evidence.py -q` -> `7 passed`.
- `uv run pytest tests/cli/test_generate_latin_mvp_command.py tests/integration/test_v20_latin_audio_evidence.py tests/integration/test_v20_latin_portuguese_translation_evidence.py tests/integration/test_v20_latin_review_curation_asset.py tests/integration/test_v20_latin_review_gate_evidence.py tests/integration/test_v20_latin_source_pack_asset.py tests/integration/test_v20_latin_source_pack_evidence.py -q` -> `54 passed`.
- `uv run pytest tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_export_job_flow.py tests/integration/test_v12_existing_mode_regression_boundary.py tests/integration/test_v12_phonetics_and_existing_modes_audit.py -q` -> `14 passed`.
- `uv lock --check`.
- `uv run pytest tests/services/test_provider_pronunciation_adapters.py tests/services/test_library_pronunciation_adapters.py tests/test_runtime.py tests/services/test_lexical_grounding.py -q` -> `37 passed`.
- `uv run pytest` -> `824 passed, 3 warnings`.

## Notes

- The remaining warnings are upstream/dependency deprecation warnings from `dateparser` and Alembic config behavior.
- No runtime product behavior was changed for the full-suite repair; changes were limited to test fixtures, evidence artifacts, and test assertions/isolation.
