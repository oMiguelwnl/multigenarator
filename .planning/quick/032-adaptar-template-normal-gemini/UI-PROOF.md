# UI Proof: Gemini-Derived Normal Anki Card

```json
{
  "proof_bundle_version": "1.0",
  "scope": "Normal frequency-card source and generated-template structure, effective Gemini-derived CSS declarations, unchanged export contract, and Mandarin base-CSS composition.",
  "route_state": "load_card_template(source_type='frequency') plus Mandarin frequency and word-list routes for SupportedLanguage.ZH; native Anki Desktop/mobile rendering is intentionally left to human fallback.",
  "environment": {
    "kind": "Python 3.12 source, generated-template, pytest, and git-diff inspection",
    "native_anki_available": false,
    "browser_proof_used": false,
    "browser_constraint": "agent-browser, even if available, renders a regular browser surface rather than Anki Desktop or mobile native WebViews and therefore cannot close native Anki acceptance.",
    "screenshots_captured": false
  },
  "viewport": "Source-level max-width 460px, 40px 16px page padding, bounded media, and overflow containment were inspected; no rendered viewport is claimed. Desktop and representative portrait-mobile native Anki surfaces remain unobserved.",
  "evidence_inputs": {
    "tools_used": [
      "git diff",
      "Python generated-template inspection",
      "pytest",
      "gsdd-cli ui-proof capability/validation probe"
    ],
    "files_observed": [
      "gemini-code-1785178063558.html",
      "src/multilang/templates/normal_card.md",
      "src/multilang/templates/mandarin_card.md",
      "src/multilang/services/card_template_loader.py",
      "tests/services/test_card_template_loader.py",
      "tests/integration/test_v13_normal_template_export_contract.py"
    ]
  },
  "commands_or_manual_steps": [
    "Initial evidence: git diff --unified=0 -- src/multilang/templates/normal_card.md tests/services/test_card_template_loader.py, followed by executable anchor inspection for conditionals, audio, example-panel containment, reveal, helpers, exact references, and Mandarin composition.",
    "RED: uv run pytest tests/services/test_card_template_loader.py -q returned 1 expected Gemini assertion failure and 23 passes before the template edit (#0a1220 observed instead of #121212).",
    "GREEN: uv run pytest tests/services/test_card_template_loader.py -q returned 24 passed after the template edit.",
    "Combined GREEN: uv run pytest tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py -q returned 29 passed.",
    "Final evidence: git diff --unified=0 -- src/multilang/templates/normal_card.md tests/services/test_card_template_loader.py, followed by the same executable anchor inspection; all ten preserved anchors returned true.",
    "Generated-template inspection loaded normal and both Mandarin routes and returned true for all thirteen structural, visual, composition, containment, and security observations.",
    "Validator incompatibility: npx -y gsdd-cli ui-proof validate .planning/quick/032-adaptar-template-normal-gemini/UI-PROOF.md printed the CLI help because this installed gsdd-cli has no ui-proof command; no structural-validator pass is claimed, while the fenced JSON was parsed separately during final verification.",
    "Human fallback 1 — Anki Desktop front: confirm the Gemini dark shell and typography, IPA and both relevant audio controls, optional image containment, and hidden Translation.",
    "Human fallback 2 — Anki Desktop back: confirm the identical FrontSide layout remains in place, Translation is revealed in the example section, and image/audio rendering remains acceptable.",
    "Human fallback 3 — portrait mobile Anki front: confirm wrapping/containment, IPA and audio controls, optional image sizing, and hidden Translation.",
    "Human fallback 4 — portrait mobile Anki back: confirm the same layout, revealed Translation, readable text, and acceptable image/audio rendering."
  ],
  "observations": [
    {
      "slot_id": "normal-gemini-source-contract",
      "claim": "Initial dirty-tree contracts were observed before test mutation.",
      "evidence_kind": "code",
      "artifact_path": "src/multilang/templates/normal_card.md",
      "result": "pass",
      "observation": "The initial diff showed the pre-existing examplePanel hunk, while executable inspection returned true for IPA/Image conditionals, word/sentence audio, hidden Translation, fixed FrontSide reveal, _balanced_div, _last_css_value, exact-reference regression, and Mandarin-composition regression."
    },
    {
      "slot_id": "normal-gemini-source-contract",
      "claim": "Final dirty-tree contracts still include the pre-existing quick-029/030 work.",
      "evidence_kind": "code",
      "artifact_path": "tests/services/test_card_template_loader.py",
      "result": "pass",
      "observation": "The final diff retained the examplePanel and test-helper/exact-reference/Mandarin-composition hunks, and the repeated executable inspection again returned true for all ten anchors including conditionals, both audio placeholders, and reveal behavior."
    },
    {
      "slot_id": "normal-gemini-source-contract",
      "claim": "Normal markup preserves the exact Anki reference sequence.",
      "evidence_kind": "test",
      "artifact_path": "tests/services/test_card_template_loader.py",
      "result": "pass",
      "observation": "The generated front/back sequence is word; IPA open/value/close; word_audio; Definitions; Image open/value/close; Example Sentence; sentence_audio; Translation; FrontSide."
    },
    {
      "slot_id": "normal-gemini-source-contract",
      "claim": "The generated normal CSS uses the reference palette and shell metrics.",
      "evidence_kind": "code",
      "artifact_path": "src/multilang/templates/normal_card.md",
      "result": "pass",
      "observation": "Effective declarations resolve to #121212 page, #1E1E1E card, #EAEAEA primary, #A0A0A0 muted, #333333 divider, 40px 16px page padding, 460px max width, 28px 24px card padding, 1px border, 8px radius, and the 0 4px 20px reference shadow."
    },
    {
      "slot_id": "normal-gemini-source-contract",
      "claim": "The target row and word hierarchy match the reference.",
      "evidence_kind": "test",
      "artifact_path": "tests/services/test_card_template_loader.py",
      "result": "pass",
      "observation": "Selector-aware last-declaration checks prove baseline alignment, wrapping, 10px gap, 20px bottom margin, and target word 38px/600/1.1/-0.5px plus IPA 16px/400 sans-serif treatment."
    },
    {
      "slot_id": "normal-gemini-source-contract",
      "claim": "Definition, divider, and heading proportions match the reference.",
      "evidence_kind": "test",
      "artifact_path": "tests/services/test_card_template_loader.py",
      "result": "pass",
      "observation": "Effective CSS checks prove 20px 0 divider margins, uppercase sans-serif headings at 12px/600/0.5px with 8px bottom margin, and definitions at 16px/1.6."
    },
    {
      "slot_id": "normal-gemini-source-contract",
      "claim": "The example is unboxed and Translation remains muted and answer-only.",
      "evidence_kind": "test",
      "artifact_path": "tests/services/test_card_template_loader.py",
      "result": "pass",
      "observation": "The example panel resolves to transparent background, zero border/padding, and 6px top margin; example text is 16px/1.5 and Translation is hidden inline on the front, then revealed at 16px/1.5 with 8px top margin and muted color on the back."
    },
    {
      "slot_id": "normal-gemini-source-contract",
      "claim": "Responsive containment and native Anki media wiring remain present without new active-content surfaces.",
      "evidence_kind": "code",
      "artifact_path": "src/multilang/templates/normal_card.md",
      "result": "pass",
      "observation": "Generated inspection found anywhere/break-word wrapping, contained object-fit media, replay SVG styling, no innerHTML, no external assets, no new field references, and only the pre-existing fixed reveal script."
    },
    {
      "slot_id": "normal-gemini-source-contract",
      "claim": "Mandarin routes compose the complete updated normal CSS before their untouched CSS suffix.",
      "evidence_kind": "test",
      "artifact_path": "tests/services/test_card_template_loader.py",
      "result": "pass",
      "observation": "Mandarin frequency and word-list templates are equal; composed CSS starts with base.css and equals base.css plus the exact CSS parsed from untouched mandarin_card.md, while the full Mandarin field/conditional/reveal order remains locked."
    },
    {
      "slot_id": "normal-gemini-source-contract",
      "claim": "Focused loader and unchanged export-contract suites are green.",
      "evidence_kind": "test",
      "artifact_path": "tests/integration/test_v13_normal_template_export_contract.py",
      "result": "pass",
      "observation": "The combined command completed with 29 passed, including generated APKG qfmt/afmt/CSS, field order, tabular headers, and isolation checks."
    },
    {
      "slot_id": "normal-gemini-native-anki-acceptance",
      "claim": "The approved appearance and interactions hold in native Anki Desktop and portrait-mobile WebViews on both sides.",
      "evidence_kind": "human",
      "artifact_path": ".planning/quick/032-adaptar-template-normal-gemini/UI-PROOF.md",
      "result": "human_needed",
      "observation": "Four native observations remain: Desktop front/back and mobile front/back, each covering translation state plus representative image/audio behavior."
    }
  ],
  "artifacts": [
    {
      "path": "src/multilang/templates/normal_card.md",
      "type": "template source inspection",
      "visibility": "repository",
      "retention": "project_source",
      "sensitivity": "none",
      "safe_to_publish": true
    },
    {
      "path": "tests/services/test_card_template_loader.py",
      "type": "generated template and CSS contract tests",
      "visibility": "repository",
      "retention": "project_source",
      "sensitivity": "none",
      "safe_to_publish": true
    },
    {
      "path": "tests/integration/test_v13_normal_template_export_contract.py",
      "type": "unchanged verification-only export regression",
      "visibility": "repository",
      "retention": "project_source",
      "sensitivity": "none",
      "safe_to_publish": true
    },
    {
      "path": ".planning/quick/032-adaptar-template-normal-gemini/UI-PROOF.md",
      "type": "proof metadata and native-Anki fallback checklist",
      "visibility": "local_only",
      "retention": "quick_task_record",
      "sensitivity": "none",
      "safe_to_publish": false
    }
  ],
  "privacy": {
    "contains_user_data": false,
    "contains_private_highlights": false,
    "contains_credentials": false,
    "screenshots_included": false,
    "publication_approved": false
  },
  "result": "human_needed",
  "claim_limits": "Automated evidence proves source/generated-template structure, selector-level effective CSS declarations, loader composition, and export contracts only. It does not prove pixels, installed fonts, native replay-control appearance, optional-image rendering quality, translation reveal appearance, or Anki Desktop/mobile WebView behavior. Native acceptance remains human_needed until all four Desktop/mobile front/back observations are recorded."
}
```
