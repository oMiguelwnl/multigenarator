---
status: resolved
trigger: "Diagnose and fix the 11 failing cross-phase regression tests found after Phase 13 execution. Keep the fix minimal and commit it atomically. Do not revert unrelated Phase 13 work."
created: 2026-05-06T00:00:00Z
updated: 2026-05-06T18:05:00Z
---

## Current Focus
<!-- OVERWRITE on each update - reflects NOW -->

reasoning_checkpoint:
  hypothesis: "word-list text generation is marked review_required because translation validation runs even when the candidate translation target equals the deck language, and local/runtime same-language translations intentionally equal the example sentence; this causes accepted_text_items=0, prevents audio generation, and makes export fail before media checks."
  confirming_evidence:
    - "Direct local CLI probe for word-list alpha produced text_processed_items=1, accepted_text_items=0, review_required_text_items=1, audio_processed_items=0."
    - "Persisted TextQualityRecord for alpha has example_sentence and translation_text both `Friends discuss alpha during lunch.`, validation_status=failed, review_reason=translation_mismatch."
    - "TextValidationService flags translation_mismatch when translation equals sentence only when require_translation=True; GenerateTextItemsService passed require_translation from source_profile.requires_translation_validation without considering candidate.translation_target_language."
    - "LexicalGroundingService sets word-list translation_target_language to the requested deck language, and failing tests expect manual word-list same-language text (including Spanish usar) to be accepted even when translation_text equals example_sentence."
  falsification_test: "After changing only GenerateTextItemsService to skip translation validation when candidate.translation_target_language == deck_language.value, representative text/audio/export failures should pass and source profile contract tests should still pass; if accepted_text_items remains 0 or APKG still fails for the same reason, this hypothesis is wrong or incomplete."
  fix_rationale: "Keeping the word-list profile contract but disabling translation validation only for same-language word-list generation preserves translation export fields and cross-language validation while allowing intentional same-language local/manual text to be accepted; accepted records then unblock existing audio and export flows without altering Phase 13 highlight template behavior."
  blind_spots: "Resolved after review follow-up WR-01 scoped the bypass to word-list candidates only and the full regression gate passed."
  next_action: resolved

## Symptoms
<!-- Written during gathering, then IMMUTABLE -->

expected: Cross-phase regression suite should pass, preserving pre-Phase-13 generate/export behavior and Phase 13 highlight export behavior.
actual: 11 failures after Phase 13; generate command counters are missing accepted/review/audio counts, audio assets are not produced, APKG export exits 1, and missing-audio export tests report no accepted text records instead of missing media.
errors: |
  tests/cli/test_generate_command.py::test_generate_command_regenerates_single_flagged_item expected review_required_text_items=1 in output, missing.
  tests/cli/test_generate_command.py::test_generate_command_default_runtime_reports_audio_counters expected audio_processed_items=2, missing.
  tests/cli/test_generate_command.py::test_generate_command_reports_failed_audio_when_no_approved_voice_exists expected audio_processed_items=2, missing.
  tests/integration/test_audio_job_flow.py::test_generate_command_default_runtime_uses_azure_audio_adapter expected 2 audio assets, got 0.
  tests/integration/test_export_job_flow.py::test_export_command_runtime_path_writes_apkg_csv_and_tsv_artifacts APKG export command exit_code 1.
  tests/integration/test_export_job_flow.py::test_export_command_runtime_path_fails_loudly_when_audio_is_missing[apkg/csv/tsv] output says no accepted text records instead of missing media.
  tests/integration/test_text_job_flow.py::test_generate_command_regenerates_one_flagged_item_without_full_rerun expected accepted_text_items=1, missing.
  tests/integration/test_text_job_flow.py::test_generate_command_skips_pending_groundings_during_text_generation expected accepted_text_items=1, missing.
  tests/integration/test_text_job_flow.py::test_generate_command_uses_requested_language_for_manual_word_list_text expected accepted_text_items=1, missing.
reproduction: Run the failing subset from tests/cli/test_generate_command.py, tests/integration/test_audio_job_flow.py, tests/integration/test_export_job_flow.py, and tests/integration/test_text_job_flow.py.
started: After Phase 13 execution; fix commit 1cbf682 changed template JS only and did not resolve these failures.

## Eliminated
<!-- APPEND only - prevents re-investigating -->


## Evidence
<!-- APPEND only - facts discovered -->

- timestamp: 2026-05-06T00:02:00Z
  checked: failing tests and recent Phase 13 template/export files
  found: Failures cluster around runtime text/audio summary counters and export assembly seeing no accepted text records; Phase 13 export_anki_package now selects note model/template by row.identity.source_type, while failing generate tests use --source word-list runtime data.
  implication: A source-type/data-contract regression is plausible; need trace from CLI source option through runtime generation records to export row assembly.
- timestamp: 2026-05-06T00:03:00Z
  checked: runtime, CLI, export assembly, and source profile/export schema code
  found: CLI prints accepted/review/audio counters only if runtime generate_text runs; RuntimeGenerateService always runs audio after text, but audio generation depends on accepted text records; AssembleExportCards also requires accepted text before checking audio/media.
  implication: A common upstream cause is text records being generated as review_required instead of accepted, which would suppress audio assets and make exports fail with no accepted text records.
- timestamp: 2026-05-06T00:04:00Z
  checked: representative pytest subset command through uv
  found: Shell reported `uv: command not found` before tests ran.
  implication: Need use available Python test runner directly in this environment; this does not bear on product root cause.
- timestamp: 2026-05-06T00:05:00Z
  checked: representative pytest subset via python -m pytest
  found: The text test output lacks accepted_text_items entirely, not merely accepted_text_items=0; audio assets count is 0; export missing-audio tests fail earlier with `no accepted text records`.
  implication: Text generation may be skipped entirely, not just producing review_required records. Need determine why CLI did not print the text/audio counter block.
- timestamp: 2026-05-06T00:06:00Z
  checked: direct local CLI probe and persisted TextQualityRecord
  found: RuntimeGenerateService is invoked; word-list alpha generates `Friends discuss alpha during lunch.` for both sentence and translation, then fails validation with `translation_mismatch` because translation equals the sentence. Output shows accepted_text_items=0, review_required_text_items=1, and audio_processed_items=0.
  implication: The upstream cause is word-list translation validation rejecting intentional same-language local/manual translations; this explains missing accepted counters, no audio assets, and export failing before media checks.
- timestamp: 2026-05-06T00:08:00Z
  checked: representative subset after minimal source profile fix
  found: 5 representative tests passed, covering accepted_text_items, Azure audio asset creation, and missing media export errors.
  implication: Fix addresses the common upstream cause for text/audio/export failures in the reported cluster.
- timestamp: 2026-05-06T00:09:00Z
  checked: all 11 originally reported failing tests after minimal source profile fix
  found: All 11 reported tests passed.
  implication: The regression cluster is resolved by the word-list translation validation profile fix.
- timestamp: 2026-05-06T00:10:00Z
  checked: full pytest suite after fix
  found: Suite exceeded 120s timeout around 21% progress, with one failure marker before timeout.
  implication: Need rerun with fail-fast/longer timeout to determine whether the failure is related or an independent pre-existing issue.
- timestamp: 2026-05-06T00:11:00Z
  checked: fail-fast full suite after source profile boolean change
  found: tests/domain/test_source_profiles.py expects word-list requires_translation_validation to remain True.
  implication: Better minimal fix is not changing the source profile contract; instead, GenerateTextItemsService should skip translation validation only when the generated translation target equals the deck language.
- timestamp: 2026-05-06T00:12:00Z
  checked: final service-level fix against source profile contract test plus all 11 reported failing tests
  found: 12 tests passed.
  implication: Final fix preserves the source profile contract and resolves the reported regression cluster.
- timestamp: 2026-05-06T00:13:00Z
  checked: full pytest suite with MULTILANG_TEXT_GENERATION_PROVIDER=local and MULTILANG_TRANSLATION_PROVIDER=local
  found: 339 tests passed and 1 failed: test_runtime_fails_loudly_when_litellm_is_configured_without_credentials did not raise because the full-suite environment override forced local providers.
  implication: The full-suite run was not a valid signal for that credential configuration test; targeted regression verification remains valid, and the failed test should pass without the local provider override.
- timestamp: 2026-05-06T00:14:00Z
  checked: credential-specific runtime test with LLM credential environment variables unset and no provider override
  found: test_runtime_fails_loudly_when_litellm_is_configured_without_credentials passed.
  implication: The prior full-suite failure was an environment override artifact, not caused by the fix.
- timestamp: 2026-05-06T00:15:00Z
  checked: Phase 13 highlight export target tests
  found: 42 tests passed across highlight export artifacts, card template loader, APKG export package, and tabular bundle tests.
  implication: The final service-level fix preserves the recent Phase 13 highlight export behavior.
- timestamp: 2026-05-06T00:16:00Z
  checked: atomic code commit
  found: Created commit 7b5418c with only src/multilang/services/generate_text_items.py staged; .planning/debug remains untracked session state.
  implication: The product fix is committed without reverting unrelated Phase 13 work.


## Resolution
<!-- OVERWRITE as understanding evolves -->

root_cause: GenerateTextItemsService required translation validation even when a word-list candidate's translation_target_language equals the deck language; same-language local/manual translations intentionally equal the example sentence, so valid word-list records were marked review_required, leaving no accepted records for audio/export.
fix: Keep the word-list source profile unchanged, but pass require_translation=False to TextValidationService only when source_profile.source_type is word-list and candidate.translation_target_language equals deck_language.value. The follow-up review fix preserved same-language frequency validation.
verification: The original 11 failing regression tests passed after commit 7b5418c; WR-01 was fixed in commit 3a5537a; final regression gate passed with 226 tests. Phase 13 highlight export target tests and focused generate-text tests passed.
files_changed: [src/multilang/services/generate_text_items.py, tests/services/test_generate_text_items.py]
