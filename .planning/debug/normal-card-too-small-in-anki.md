---
status: resolved
trigger: 'User report: "O template que você gerou está muito pequeno; antes preenchia quase toda a tela." Confirmed in Anki rather than the historical HTML preview.'
created: 2026-07-28T00:00:00Z
updated: 2026-07-28T00:18:00Z
---

## Current Focus

reasoning_checkpoint:
  hypothesis: "The canonical body.card flex centering makes Anki's injected #qa wrapper an auto-sized flex item, so the fluid .customCard fills only that narrow wrapper rather than the reviewer viewport."
  confirming_evidence:
    - "The german-test-2 APKG contains canonical flex centering on .card and fluid width on .customCard, but no #qa width contract."
    - "Anki inserts template HTML inside #qa, making #qa the direct flex item of body.card and allowing it to shrink to its auto content width."
    - "pt2.png is consistent with a centered narrow #qa whose child correctly occupies 100% of that wrapper."
  falsification_test: "Change only tests to require block layout on canonical .card, no canonical justify/align centering, explicit #qa width/min-width, and zero shell margin, then verify RED against current exported CSS."
  fix_rationale: "Return body.card to normal block flow and make #qa span the available width; .customCard can then resolve width: 100% against the viewport-wide wrapper while retaining content-driven height."
  blind_spots: "Native Anki rendering cannot be exercised by pytest in this environment; exported CSS propagation and static contracts are the automated proxy."
  next_action: resolved

## Symptoms

expected: "The normal Anki card should keep its improved fluid width, but its background and border should end after the content while the page background covers the rest of the viewport."
actual: "After the height correction, the shell follows content but remains narrow and centered because its 100% width is relative to Anki's shrink-to-fit #qa flex item."
errors: "No runtime exception; this is a rendered layout regression/expectation mismatch."
reproduction: "Open a generated normal card in a large Anki reviewer window."
started: "Observed with the current canonical normal-card template."

## Eliminated

- "Historical preview mismatch: the user confirmed the issue in Anki, and normal_card_gemini_preview.html is out of scope."
- "Mandarin-specific CSS as the source: Mandarin inherits the normal CSS by architecture, so the canonical normal template is the source to correct."
- "Cycle-1 width correction as the new defect: the user confirmed width improved, so width, max-width, and outer padding must remain unchanged."
- "Cycle-2 content-height correction as the current defect: min-height: 0 is correct and must remain on .customCard."

## Evidence

- timestamp: 2026-07-28T00:00:00Z
  checked: "User-provided report and bounded root-cause evidence."
  found: "The expected behavior is explicitly near-fullscreen in Anki, regardless of the immediately previous Git version also having a fixed max-width."
  implication: "Treat the fixed-width canonical CSS as the product bug rather than preserving literal preview fidelity."
- timestamp: 2026-07-28T00:01:00Z
  checked: "Final canonical CSS declarations in src/multilang/templates/normal_card.md and their loader/export tests."
  found: "The winning rules set 40px 16px outer padding, max-width: 460px, and min-height: 0; tests currently codify those values."
  implication: "First update only the size expectations in both test layers and prove RED on the three obsolete dimensions."
- timestamp: 2026-07-28T00:02:00Z
  checked: "Focused RED selection after changing tests only."
  found: "Both tests failed as intended: the loader contract first reported 40px 16px instead of 12px, and the exported model still reported --max-width-card: 460px instead of none. Production was unchanged at this point."
  implication: "The new tests detect the obsolete constrained shell and provide a valid TDD RED gate."
- timestamp: 2026-07-28T00:05:00Z
  checked: "Requested focused GREEN suite after the minimal canonical CSS change."
  found: "After making the CSS test helper distinguish top-level declarations from final media-query overrides, all 54 tests passed."
  implication: "The loader, exported model, and v1.3 normal-template integration contract accept the fluid desktop and compact mobile sizing."
- timestamp: 2026-07-28T00:06:00Z
  checked: "Requested expanded regression suite including Russian phoneme and all listed Japanese deck paths."
  found: "All 83 tests passed. The loader coverage also confirmed Mandarin continues to inherit the canonical normal CSS without editing mandarin_card.md."
  implication: "The bounded normal-card sizing change did not regress the listed sibling deck paths or routing contract."
- timestamp: 2026-07-28T00:07:00Z
  checked: "git diff --check on the two test files and canonical normal template, followed by scoped diff/status inspection."
  found: "No whitespace errors were reported; only existing Windows LF-to-CRLF warnings appeared. Unrelated worktree changes remained untouched."
  implication: "The intended three-file implementation diff is clean and isolated; no Git state-changing operation was performed."
- timestamp: 2026-07-28T00:09:00Z
  checked: "New user-supplied visual evidence pt1.png and pt2.png against the cycle-1 canonical sizing declarations."
  found: "pt1.png ends the card border after content, while pt2.png keeps the border to the viewport bottom; the user confirmed the new width is correct."
  implication: "Preserve all width and spacing improvements, but remove only viewport-derived minimum heights from .customCard."
- timestamp: 2026-07-28T00:10:00Z
  checked: "Cycle-2 focused RED after changing only loader/export expectations and this debug artifact."
  found: "Both tests failed as intended: the canonical loader returned calc(100vh - 24px) instead of 0, and the exported CSS lacked min-height: 0 while still containing the viewport-derived shell heights."
  implication: "The revised tests directly reproduce the visually confirmed excessive shell-height regression before production changes."
- timestamp: 2026-07-28T00:11:00Z
  checked: "Exact focused GREEN suite after changing only the canonical shell height declarations."
  found: "All 54 tests passed, including preservation of body/.card min-height: 100vh, fluid width, mobile spacing, references, reveal behavior, and export propagation."
  implication: "The shell follows content while the page remains viewport-height and the cycle-1 width correction stays intact."
- timestamp: 2026-07-28T00:12:00Z
  checked: "Exact expanded regression suite from cycle 1."
  found: "All 83 tests passed across normal export, Russian phoneme, Japanese frequency/kana paths, integration contract, and Mandarin inheritance coverage."
  implication: "The height-only correction does not regress the requested adjacent paths."
- timestamp: 2026-07-28T00:13:00Z
  checked: "Scoped git diff --check and diff/status inspection for the canonical template and two test files."
  found: "No whitespace errors occurred; only existing LF-to-CRLF warnings were emitted. The diff changes CSS sizing/tests only, and pt1.png, pt2.png, Mandarin, previews, planning tasks, LOG, docs, and other concurrent files remain untouched."
  implication: "The second-cycle patch is bounded and no Git state-changing operation was performed."
- timestamp: 2026-07-28T00:14:00Z
  checked: "User-provided german-test-2 APKG CSS evidence and Anki's #qa wrapper structure."
  found: "The exported CSS makes body.card a centered flex container and .customCard fluid, but gives #qa no width; therefore #qa shrink-wraps as the flex item and constrains its 100%-wide child."
  implication: "Fix the canonical containing block by using block flow and a full-width #qa, without reverting fluid width or content-driven shell height."
- timestamp: 2026-07-28T00:15:00Z
  checked: "Cycle-3 focused RED after changing only loader/export expectations and this debug artifact."
  found: "Both tests failed as intended: the canonical .card returned display: flex instead of block, and exported CSS lacked the required block-layout/#qa contract."
  implication: "The tests reproduce the Anki wrapper constraint before any cycle-3 production change."
- timestamp: 2026-07-28T00:16:00Z
  checked: "Exact focused GREEN suite after the minimal canonical containing-block correction."
  found: "All 54 tests passed, including .card block flow without canonical justify/align centering, #qa width/min-width, zero shell margin, fluid width, content height, exact field references, one fixed reveal script, and no innerHTML."
  implication: "The loaded and exported normal template now gives .customCard a viewport-wide containing block without changing markup or reveal behavior."
- timestamp: 2026-07-28T00:17:00Z
  checked: "Exact expanded regression suite from the prior cycles."
  found: "All 83 tests passed across the requested normal, export, Russian phoneme, Japanese, integration, and Mandarin-inheritance paths."
  implication: "The wrapper correction remains isolated from adjacent deck architectures."
- timestamp: 2026-07-28T00:18:00Z
  checked: "Scoped git diff --check plus diff/status inspection for the canonical template and two tests."
  found: "No whitespace errors occurred; only existing LF-to-CRLF warnings appeared. No markup, field, script, asset, APKG, image, preview, quick037/038, or concurrent file was changed, and no Git state-changing command ran."
  implication: "The cycle-3 patch is minimal, secure within the static template contract, and bounded to the approved write scope."

## Resolution

root_cause: "Anki injects the card template inside #qa; canonical display:flex centering on body.card made that unstyled wrapper a shrink-to-fit flex item, so .customCard width:100% filled only the narrow #qa instead of the reviewer viewport."
fix: "Changed only the canonical .card layout to display:block without justify/align centering, added #qa width:100% and min-width:0, and set .customCard margin:0 while preserving fluid width, max-width:none, min-height:0, desktop/mobile padding, markup, and visual styling."
verification: "Cycle-3 TDD RED produced 2 expected failures before production; focused GREEN passed 54 tests, expanded GREEN passed 83 tests, and scoped git diff --check passed with line-ending warnings only. Native Anki visual rendering was not available, so final width behavior still requires confirmation in Anki with a regenerated/exported template."
files_changed: [.planning/debug/normal-card-too-small-in-anki.md, tests/services/test_card_template_loader.py, tests/services/test_export_anki_package.py, src/multilang/templates/normal_card.md]
