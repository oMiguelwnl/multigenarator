---
mode: quick
task: 029-restyle-anki-card-templates
runtime: opencode
assurance: self_checked
status: implementation_complete_visual_acceptance_pending
---

# Quick Task 029 Summary: Restyle Anki Card Templates

Dark centered normal cards, dark-blue shared phoneme cards, and Mandarin auxiliary typography now follow the supplied stylesheet references without changing note fields or front/back markup.

## Work Completed

- Added regression coverage for exact field/reference order, hidden-front translations, `FrontSide`, reveal scripts, template routing, shared phoneme behavior, Mandarin CSS composition, and distinctive stylesheet signatures.
- Restyled only the `Styling (CSS)` fenced sections in:
  - `src/multilang/templates/normal_card.md`
  - `src/multilang/templates/russian_phoneme_card.md`
  - `src/multilang/templates/mandarin_card.md`
- Preserved normal and Mandarin front/back markup exactly, including translation behavior and field order.
- Preserved shared Russian/Polish/Greek phoneme markup, fields, native replay SVG support, and sentence-translation reveal behavior.
- Created `UI-PROOF.md` with source, test, generated-model evidence and the mandatory human Anki acceptance boundary.

## TDD Record

### RED

Command:

`uv run pytest tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_russian_phoneme_deck.py -q`

Result before production edits: **4 failed, 53 passed**. All four failures were the expected new stylesheet-fidelity assertions for normal, Mandarin, generated normal-model, and phoneme CSS. Newly added contract assertions passed; no unrelated failure occurred.

### GREEN

Same focused command after CSS-only production edits: **57 passed in 0.99s**.

### Generated Model Inspection

Runtime inspection confirmed:

- Normal model retains its exact nine fields and `FrontSide` back.
- Mandarin frequency and word-list models are identical, retain the exact twelve fields, and composed CSS starts with normal CSS.
- Russian, Polish, and Greek phoneme models retain the exact nine fields and share identical templates/CSS.
- Production template diff is confined to the three CSS fenced sections.

## UI Proof Status

- **Source/model stylesheet fidelity:** automated evidence passed.
- **Exact native Anki appearance:** `human_needed`.

The plan-checker warning is binding: agent-browser cannot represent native Anki rendering. No real Anki Desktop or mobile screenshots were available, so exact pixels, fonts, overflow, replay controls, and front/back reveal appearance are not claimed as accepted. Twelve observations remain required: three templates × front/back × Desktop/mobile.

## Scope and Git

- Preview reference files were read but not modified.
- Unrelated tracked deletions, `.planning/quick/LOG.md`, images, and other untracked files were not modified or reverted.
- No files were staged, committed, amended, pushed, or reverted.

## Deviations

None. The plan was executed within its locked file and behavior scope.

## Verification

- Focused pytest: **PASS (57 tests)**
- Generated model contract inspection: **PASS**
- UI proof validator: **UNAVAILABLE/INCOMPATIBLE**. Running `npx -y gsdd-cli ui-proof validate .planning/quick/029-restyle-anki-card-templates/UI-PROOF.md` returned the CLI help; the installed command list has no `ui-proof` subcommand, so no validator pass is claimed.
- Native Anki Desktop/mobile visual acceptance: **HUMAN NEEDED**

## Self-Check: PASSED

- Both required planning artifacts exist and the fenced UI-proof JSON parses with all required top-level fields.
- A direct comparison against `HEAD` confirms the Front Template and Back Template sections of all three production templates are byte-for-byte unchanged.
- Focused tests remain green after documentation was written.
