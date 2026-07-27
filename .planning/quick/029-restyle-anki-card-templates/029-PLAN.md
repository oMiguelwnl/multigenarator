---
mode: quick
task: 029-restyle-anki-card-templates
type: execute
wave: 1
depends_on: []
autonomous: false
requirements: []
files_modified:
  - tests/services/test_card_template_loader.py
  - tests/services/test_export_anki_package.py
  - tests/services/test_russian_phoneme_deck.py
  - src/multilang/templates/normal_card.md
  - src/multilang/templates/russian_phoneme_card.md
  - src/multilang/templates/mandarin_card.md
  - .planning/quick/029-restyle-anki-card-templates/UI-PROOF.md
reduced_assurance: true
reduced_assurance_reason: ".planning/templates/roles/planner.md is absent from the worktree and HEAD; this plan follows the supplied quick-mode contract and existing quick-plan conventions."
must_haves:
  truths:
    - "Normal cards visually follow the centered dark hero design in freq_card_hero_dark.html."
    - "Shared phoneme cards visually follow the dark blue design in phoneme_card_restyle.html."
    - "Mandarin cards use the dark Mandarin treatment shown in unified_templates_preview.html while retaining concatenated normal plus Mandarin CSS."
    - "Template filenames, field references/order, front/back behavior, and translation reveal behavior are unchanged."
  artifacts:
    - path: src/multilang/templates/normal_card.md
      provides: "Dark centered normal-card stylesheet"
    - path: src/multilang/templates/russian_phoneme_card.md
      provides: "Dark blue phoneme-card stylesheet"
    - path: src/multilang/templates/mandarin_card.md
      provides: "Mandarin-specific dark typography layered over normal CSS"
  key_links:
    - from: src/multilang/services/card_template_loader.py
      to: src/multilang/templates/mandarin_card.md
      via: "normal CSS concatenated before Mandarin CSS"
    - from: src/multilang/templates/normal_card.md
      to: src/multilang/templates/mandarin_card.md
      via: "shared CSS variables and selectors"
ui_proof_slots:
  - slot_id: anki-template-source-model-fidelity
    claim: "Generated normal, phoneme, and Mandarin model templates retain their contracts and contain the distinctive palette, spacing, hierarchy, and responsive CSS of the three approved references."
    route_state: "Inspect load_card_template frequency/zh models and build_russian_phoneme_model front, back, and CSS; compare stylesheet signatures with freq_card_hero_dark.html, phoneme_card_restyle.html, and the Mandarin section of unified_templates_preview.html."
    required_evidence_kinds: [code, test, runtime]
    minimum_observations: 6
    expected_artifact_types: ["template source inspection", "generated model template inspection", "focused pytest output"]
    validation_command: "uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_russian_phoneme_deck.py -q"
    environment: "Python 3.12 template/model inspection; no Anki runtime or browser renderer assumed"
    viewport: "Source/model contract only; responsive max-width and overflow rules inspected without pixel rendering"
    manual_acceptance_required: false
    claim_limit: "Proves source/model contract and stylesheet fidelity only; it does not prove exact pixels, font availability, or Anki Desktop/mobile rendering."
  - slot_id: anki-template-exact-visual-acceptance
    claim: "Normal, phoneme, and Mandarin cards match the approved references in actual Anki front/back rendering, including translation reveal."
    route_state: "Generate representative normal, phoneme, and Mandarin models/decks; inspect front and back in Anki Desktop and one mobile Anki client."
    required_evidence_kinds: [human]
    minimum_observations: 12
    expected_artifact_types: ["manual checklist for three templates x front/back x desktop/mobile"]
    validation_command: "npx -y gsdd-cli ui-proof validate .planning/quick/029-restyle-anki-card-templates/UI-PROOF.md"
    environment: "Anki Desktop and mobile Anki client; unavailable in the repository test environment"
    viewport: "Desktop and representative portrait mobile viewport"
    manual_acceptance_required: true
    claim_limit: "Exact appearance remains human_needed until all twelve front/back Desktop/mobile observations are recorded; automated checks cannot close this claim."
---

# Quick Task 029 Plan: Restyle Anki Card Templates

## Objective

Restyle only the three existing Anki templates against their supplied visual references, preserving every filename and note-template contract. Do not modify or revert unrelated tracked deletions or untracked files.

## Locked Scope

- `normal_card.md` keeps its existing Front/Back sections and adopts `freq_card_hero_dark.html` styling.
- `russian_phoneme_card.md` keeps its existing Front/Back sections and adopts `phoneme_card_restyle.html` styling; Polish/Greek reuse remains intact.
- `mandarin_card.md` keeps its fields and pedagogy order and adopts the dark Mandarin styling shown in `unified_templates_preview.html`; the loader continues concatenating normal CSS followed by Mandarin CSS.
- No template rename, field rename/reorder, behavior change, preview-file edit, service change, or unrelated worktree cleanup is allowed.

## Tasks

<task id="029-01" type="auto" tdd="true">
  <name>Write contract and stylesheet-fidelity regressions first</name>
  <files>
    - tests/services/test_card_template_loader.py
    - tests/services/test_export_anki_package.py
    - tests/services/test_russian_phoneme_deck.py
  </files>
  <behavior>
    - Normal model preserves its exact field list/order, field references, hidden-front Translation, FrontSide back, and reveal script while exposing dark hero palette/layout signatures.
    - Phoneme model preserves PHONEME_FIELD_NAMES, field references/order, shared Russian/Polish/Greek template behavior, and sentence-translation reveal while exposing the reference dark blue card/box/audio styling.
    - Mandarin frequency and word-list models preserve their exact field order and front/back sequence, retain base.css as a prefix of composed CSS, and expose the reference dark-mode Mandarin colors plus readable Pinyin/Traditional selectors.
  </behavior>
  <action>
    Add focused assertions before editing production templates. Assert semantic CSS signatures rather than copying whole preview files: page/card/accent colors, 16px rounded card with blue top border and shadow, centered normal-card hero, example callout treatment, phoneme target box/sound-row hierarchy, and Mandarin auxiliary-line dark colors. Also assert the existing filename routing, field-reference sets/order, FrontSide use, hidden-front translation, and reveal scripts so a visual edit cannot mutate the contract. Run the focused suite immediately and record failures caused by the new style assertions; do not edit production files until RED is observed, and stop on unrelated failures.
  </action>
  <verify>
    <automated>uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_russian_phoneme_deck.py -q</automated>
    Expected RED: newly added stylesheet-fidelity assertions fail against at least the normal and phoneme current CSS, while pre-existing contract assertions remain green.
  </verify>
  <done>Tests precisely lock all three visual targets and unchanged contracts, and the pre-production RED result is recorded.</done>
</task>

<task id="029-02" type="auto" tdd="true">
  <name>Restyle CSS only and prove generated model contracts</name>
  <files>
    - src/multilang/templates/normal_card.md
    - src/multilang/templates/russian_phoneme_card.md
    - src/multilang/templates/mandarin_card.md
    - .planning/quick/029-restyle-anki-card-templates/UI-PROOF.md
  </files>
  <action>
    Change only each markdown file's Styling (CSS) fenced section; leave Front Template, Back Template, field references, labels, ordering, IDs, conditional blocks, and reveal JavaScript untouched. For normal cards, reproduce the `#0a1220` page, `#0f1b2d` card, `#3b82f6` accent, centered word/IPA/audio hero, 16px radius/top border/shadow, compact uppercase headings, dividers, and blue-left-border example callout from freq_card_hero_dark.html using existing classes. For phoneme cards, reproduce the same dark blue shell plus `#12213a` target box, `#24405f` borders, hierarchy, spacing, and circular native replay-button treatment from phoneme_card_restyle.html without changing field placement or shared Russian/Polish/Greek behavior. For Mandarin, add only specific overrides needed for Pinyin, Traditional, Sentence Pinyin, and Traditional Sentence to match the dark Mandarin preview; preserve loader composition by relying on normal-card variables rather than duplicating the base stylesheet. Keep responsive width/overflow behavior and native Anki replay SVG support.

    Run the focused tests to GREEN, then inspect generated normal, Mandarin frequency/word-list, and phoneme model front/back/CSS. Create `UI-PROOF.md` with fenced JSON and the workflow-required proof-bundle fields, recording commands, observations, local-only artifact metadata (`visibility`, `retention`, `sensitivity`, `safe_to_publish`), results, and the two claim limits above. If no Anki runtime/browser renderer is available, record that constraint and leave exact appearance `human_needed`; manual Anki Desktop/mobile acceptance is mandatory before claiming a pixel-level match.
  </action>
  <verify>
    <automated>uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_russian_phoneme_deck.py -q</automated>
    <automated>npx -y gsdd-cli ui-proof validate .planning/quick/029-restyle-anki-card-templates/UI-PROOF.md</automated>
  </verify>
  <done>All focused tests pass; generated models preserve every contract and carry the intended styles; source/model fidelity is evidenced, while exact Anki appearance remains explicitly pending manual Desktop/mobile acceptance.</done>
</task>

## Success Criteria

- The three existing template paths are the only production files changed.
- Tests demonstrate RED before CSS edits and GREEN afterward.
- Field names/references/order, front/back markup, translation reveal behavior, and Mandarin CSS concatenation remain unchanged.
- Automated evidence claims only source/model contract and stylesheet fidelity; exact visual equivalence requires manual Anki approval.
