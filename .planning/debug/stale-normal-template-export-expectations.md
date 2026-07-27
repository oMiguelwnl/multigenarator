---
status: resolved
trigger: "The focused template/export suite has one failure because test_build_multilang_model_uses_project_card_template_sections still asserts the superseded blue 400px normal-card theme after quick 032 approved the Gemini layout."
created: 2026-07-27T00:00:00Z
updated: 2026-07-27T00:03:00Z
---

## Current Focus

reasoning_checkpoint:
  hypothesis: "The production template is correct; only the export test expectations are stale relative to the authoritative normal-template contract and final template."
  confirming_evidence:
    - "The reported focused suite result is 1 failed and 64 passed, with the failure confined to obsolete style signatures in test_build_multilang_model_uses_project_card_template_sections."
  falsification_test: "Replace only the obsolete style assertions with a minimal set of Gemini layout signatures, preserve markup/reveal/order assertions, and rerun the exact 65-test suite."
  fix_rationale: "Updating the consumer test to the approved template contract corrects test drift without changing production behavior."
  blind_spots: "None remaining within the bounded test-only scope."
  next_action: resolved

## Symptoms

expected: The export model test should validate the final approved Gemini normal-card template while preserving markup, reveal, and section-order contracts.
actual: The test still expects the superseded 400px blue theme from quick 029.
errors: "tests/services/test_export_anki_package.py::test_build_multilang_model_uses_project_card_template_sections fails on obsolete CSS signatures."
reproduction: "uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_russian_phoneme_deck.py tests/integration/test_v13_normal_template_export_contract.py -q"
started: "Before the commit of template series 029/030/032."

## Eliminated

- "Production-template regression: the authoritative loader contract and approved normal_card.md define the Gemini layout."

## Evidence

- timestamp: 2026-07-27T00:00:00Z
  checked: "User-provided focused-suite result and identified authoritative contract paths."
  found: "One stale consumer-test expectation remains; production code is not implicated."
  implication: "Limit the fix to assertions inside the named test."
- timestamp: 2026-07-27T00:01:00Z
  checked: "Exact focused pytest suite before editing."
  found: "The suite reproduced at 1 failed and 64 passed; the named test failed first on the obsolete 400px expectation while exported CSS contained 460px."
  implication: "The stale test-contract hypothesis is confirmed."
- timestamp: 2026-07-27T00:02:00Z
  checked: "Named export test against the authoritative loader contract and normal_card.md."
  found: "Markup, reveal, and section-order assertions remain valid; only CSS signatures described the superseded theme."
  implication: "Replace only the CSS signature block with Gemini layout signatures."
- timestamp: 2026-07-27T00:03:00Z
  checked: "Exact focused pytest suite and git diff whitespace validation after the assertion-only patch."
  found: "All 65 tests passed; git diff --check reported no whitespace errors (only the existing LF-to-CRLF working-copy warning)."
  implication: "The minimal test-only correction resolves the bounded failure."

## Resolution

root_cause: "The export test retained obsolete quick-029 CSS expectations after quick 032 made the Gemini normal-card layout the authoritative contract; the production template was correct."
fix: "Replaced only the stale CSS assertions in test_build_multilang_model_uses_project_card_template_sections with exported Gemini signatures while preserving markup, reveal, and ordering assertions."
verification: "Exact requested suite passed with 65 tests; git diff --check passed with only the existing line-ending warning."
files_changed: [tests/services/test_export_anki_package.py]
