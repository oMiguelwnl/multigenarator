# Deferred Items

## Out-of-scope failures noticed during Plan 04-05

- `tests/integration/test_text_job_flow.py::test_generate_command_regenerates_one_flagged_item_without_full_rerun`
  - Current failure: expected `accepted_text_items=1` is missing from CLI output.
- `tests/integration/test_text_job_flow.py::test_generate_command_skips_pending_groundings_during_text_generation`
  - Current failure: expected `accepted_text_items=1` is missing from CLI output.
- `tests/integration/test_text_job_flow.py::test_generate_command_uses_requested_sentence_and_translation_languages`
  - Current failure: expected Spanish sentence text no longer matches runtime output.

These failures were observed while smoke-checking nearby runtime coverage after the Phase 4 audio gap closure. They touch pre-existing text-runtime expectations outside Plan 04-05 and were not modified as part of this plan.
