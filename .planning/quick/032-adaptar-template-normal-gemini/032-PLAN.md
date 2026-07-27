---
mode: quick
task: 032-adaptar-template-normal-gemini
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: []
files_modified:
  - tests/services/test_card_template_loader.py
  - src/multilang/templates/normal_card.md
  - .planning/quick/032-adaptar-template-normal-gemini/UI-PROOF.md
files_verified:
  - path: tests/integration/test_v13_normal_template_export_contract.py
    mode: verification-only
    note: "Pre-existing regression suite; execute unchanged and never treat as a produced or modified artifact."
reduced_assurance: true
reduced_assurance_reason: ".planning/templates/roles/ exists but contains no planner role contract; this plan applies the supplied quick-mode contract directly."
non_goals:
  - "Do not edit manual/highlight, phoneme, Japanese, Latin, Korean, or Mandarin markup/CSS."
  - "Do not change schemas, field order, model IDs, exporter routing, generation, providers, or the template loader."
  - "Do not edit ROADMAP.md, SPEC.md, LOG.md, unrelated dirty-tree files, or create browser scaffolding."
hard_boundaries:
  - "Evolve the current dirty versions of normal_card.md and test_card_template_loader.py; never restore them from HEAD or discard quick-029/030 work wholesale."
  - "Do not stage or commit."
closure_claim_limit: "Automated evidence proves source/generated-template structure, CSS signatures, and export contracts only; visual acceptance in native Anki Desktop/mobile remains human_needed."
must_haves:
  truths:
    - "Normal cards use the ergonomic dark layout from gemini-code-1785178063558.html on both sides."
    - "Translation stays hidden on the front and is revealed on the back without replacing the front layout."
    - "All current normal-note fields, reference order, IPA/Image conditionals, audio references, labels, and optional image behavior remain intact."
    - "Mandarin continues to prepend the complete normal CSS to its own CSS without any Mandarin markup or stylesheet edit."
  artifacts:
    - path: src/multilang/templates/normal_card.md
      provides: "Gemini-derived normal-card front/back shell and styling with the existing Anki contract"
    - path: tests/services/test_card_template_loader.py
      provides: "Normal visual/markup regressions and Mandarin CSS-composition coverage"
    - path: .planning/quick/032-adaptar-template-normal-gemini/UI-PROOF.md
      provides: "Source/test evidence plus an explicit native-Anki human-needed boundary"
  key_links:
    - from: src/multilang/templates/normal_card.md
      to: src/multilang/services/card_template_loader.py
      via: "markdown Front/Back/CSS parsing and normal template selection"
    - from: src/multilang/templates/normal_card.md
      to: src/multilang/templates/mandarin_card.md
      via: "loader concatenates the complete normal CSS before Mandarin CSS"
    - from: "normal front #translation"
      to: "normal back {{FrontSide}} reveal script"
      via: "fixed translation id hidden inline then shown on the answer side"
ui_proof_slots:
  - slot_id: normal-gemini-source-contract
    claim: "The generated normal template preserves its Anki contract and contains the reference's dark palette, typography, dimensions, defining padding/gaps/margins, weights, line heights, letter spacing, headings, border, radius, shadow, and 38px word hierarchy; Mandarin still composes that complete base CSS."
    route_state: "Inspect the normal frequency template returned by load_card_template and the Mandarin frequency template returned for SupportedLanguage.ZH, then run focused loader and export-contract tests."
    required_evidence_kinds: [code, test]
    minimum_observations: 8
    expected_artifact_types: ["template source inspection", "generated template inspection", "focused pytest output"]
    validation_command: "uv run pytest tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py -q"
    environment: "Python 3.12 template/model inspection; no browser or native Anki renderer"
    viewport: "Source-level max-width 460px and responsive containment only; no rendered viewport is claimed"
    manual_acceptance_required: false
    claim_limit: "Proves structure, effective CSS declarations, loader composition, and export contract; it does not prove pixels, installed fonts, native replay controls, or Anki WebView behavior."
  - slot_id: normal-gemini-native-anki-acceptance
    claim: "A representative normal card has the approved appearance on front and back in Anki Desktop and a portrait mobile Anki client, with translation hidden/revealed correctly and optional image/audio rendering acceptably."
    route_state: "Generate a representative normal deck with IPA, both audio fields, definitions, example, translation, and image; inspect front and back in Anki Desktop and mobile."
    required_evidence_kinds: [human]
    minimum_observations: 4
    expected_artifact_types: ["manual checklist for front/back on Desktop/mobile"]
    validation_command: "npx -y gsdd-cli ui-proof validate .planning/quick/032-adaptar-template-normal-gemini/UI-PROOF.md"
    environment: "Native Anki Desktop and mobile client, unavailable to repository pytest; agent-browser targets a regular browser and does not reproduce either native Anki WebView"
    viewport: "Desktop and representative portrait-mobile native Anki surfaces"
    manual_acceptance_required: true
    claim_limit: "Native appearance remains human_needed until all four side/platform observations are recorded; source inspection, pytest, and any agent-browser rendering cannot close this claim, so Desktop/mobile inspection is the required human fallback."
---

# Quick Task 032 Plan: Adaptar template normal ao visual Gemini

## Objective

Adapt only the production normal-card template to the visual model in `gemini-code-1785178063558.html`, using the same layout on both sides while preserving every existing Anki/export contract and building on the current uncommitted quick-029/030 changes.

## Context

- `gemini-code-1785178063558.html` is the locked visual reference; it is not an Anki template and must not replace field markup.
- `src/multilang/services/card_template_loader.py` parses `normal_card.md`; for Mandarin it concatenates all normal CSS before untouched Mandarin CSS.
- `tests/integration/test_v13_normal_template_export_contract.py` is a pre-existing `files_verified` input only: run it unchanged to protect model fields/order plus exported qfmt/afmt/CSS; it is not produced or modified by either task.
- Discovery level 0: this is an internal HTML/CSS and pytest regression change with no new dependency or external API.

## Locked Decisions

- **D-01:** Use the reference palette and defining visual metrics: page `#121212` with `40px 16px` padding; card `#1E1E1E`, primary `#EAEAEA`, muted `#A0A0A0`, divider/border `#333333`, serif content, sans-serif IPA/headings, `460px` max width, `28px 24px` card padding, `1px` border, `8px` radius, and `0 4px 20px rgba(0, 0, 0, 0.5)` shadow. Keep the target row baseline-aligned and wrapping with `10px` gap and `20px` bottom margin; target word is `38px`/`600`/`1.1` with `-0.5px` letter spacing; IPA is `16px`/`400`; dividers use `20px 0` margins; headings are uppercase sans-serif `12px`/`600` with `0.5px` letter spacing and `8px` bottom margin; definitions use `16px`/`1.6`, example text uses `16px`/`1.5`, and Translation uses `8px` top margin, `16px`/`1.5` muted text.
- **D-02:** Front and back use the same layout through `{{FrontSide}}`; Translation remains hidden on the front and the existing answer-side script reveals it.
- **D-03:** Preserve the current references and order for `word`, conditional `IPA`, `word_audio`, `Definitions`, conditional `Image`, `Example Sentence`, `sentence_audio`, `Translation`, and `FrontSide`; keep the exported model field order, including non-rendered `SortIndex`.
- **D-04:** Scope is normal card only. Mandarin may inherit the new normal CSS through existing loader composition, but its markup and CSS must not be edited.
- **D-05:** Edit the dirty working-tree files in place; do not restore from HEAD or erase unrelated quick-029/030 changes.
- **D-06:** No schema/model ID/routing/generation/provider changes, no ROADMAP/SPEC/LOG edits, no unrelated cleanup, no browser scaffolding, and no commit.

## Tasks

<task id="032-01" type="auto" tdd="true">
  <name>Lock the Gemini visual and immutable normal-card contracts</name>
  <files>
    - tests/services/test_card_template_loader.py
  </files>
  <files_verified>
    - tests/integration/test_v13_normal_template_export_contract.py (verification-only; pre-existing, run unchanged in Task 032-02)
  </files_verified>
  <behavior>
    - The normal template keeps the exact field-reference sequence, IPA/Image conditionals, both audio fields, hidden front Translation, `{{FrontSide}}`, and fixed reveal script per D-02/D-03.
    - Effective final CSS values match the palette plus the model-defining page/card padding, row gap/margins/alignment, weights, line heights, letter spacing, heading treatment, width, border, radius, shadow, and target-word signatures in D-01, replacing stale quick-029/030 blue-hero assertions rather than deleting contract coverage.
    - The example sentence, sentence audio, and hidden Translation remain in the same example container; the optional image stays between definition and example sections.
    - Mandarin frequency/word-list templates retain their own markup order and CSS suffix while their composed CSS starts with the complete, updated normal CSS per D-04.
  </behavior>
  <action>
    Before any edit, run `git diff --unified=0 -- src/multilang/templates/normal_card.md tests/services/test_card_template_loader.py` and an executable source inspection for the current IPA/Image conditionals, both audio placeholders, example-panel containment, hidden Translation, `FrontSide` reveal, `_balanced_div`, `_last_css_value`, exact-reference regression, and Mandarin-composition regression. Preserve the command and observed contract anchors for the initial-diff observation that Task 032-02 will record in `UI-PROOF.md`.

    Then evolve the existing focused normal and Mandarin tests in place per D-05. Keep the exact reference-order assertions and `_balanced_div`/`_last_css_value` helpers, but replace obsolete blue palette, top-border, 16px-radius, centered-column, 42px-word, and blue example-callout expectations with selector-appropriate semantic assertions for D-01. Cover the defining spacing/typography values listed in D-01 without snapshotting the entire stylesheet or demanding pixel-perfect rendering. Assert effective last declarations, not mere duplicate strings, so stale earlier rules cannot make the test pass. Retain the current checks for `Definition:`/`example:` because English-frequency localization depends on those literals. Strengthen Mandarin composition to prove `frequency.css` begins with `base.css`, both Mandarin routes agree, and its existing field/conditional/reveal order remains untouched. Run the test file and record RED attributable only to the new Gemini assertions; do not weaken unrelated tests or edit the verification-only integration suite.
  </action>
  <verify>
    <automated>uv run pytest tests/services/test_card_template_loader.py -q</automated>
    Expected RED before the template edit: new Gemini CSS assertions fail while preserved normal/Mandarin contract assertions remain green.
  </verify>
  <done>The focused test precisely locks D-01 through D-04 and demonstrates an attributable pre-implementation RED without changing any production file.</done>
</task>

<task id="032-02" type="auto" tdd="true">
  <name>Adapt the normal template and record bounded UI proof</name>
  <files>
    - src/multilang/templates/normal_card.md
    - .planning/quick/032-adaptar-template-normal-gemini/UI-PROOF.md
  </files>
  <files_verified>
    - tests/integration/test_v13_normal_template_export_contract.py (verification-only; pre-existing, execute unchanged)
  </files_verified>
  <action>
    Modify the current `normal_card.md` in place per D-05. Preserve the complete Front/Back reference sequence, exact label literals, IPA and Image conditionals, both native Anki audio placeholders, `id="translation"`, inline hidden state, `{{FrontSide}}`, and fixed reveal script per D-02/D-03. Keep the front as the sole content DOM so the answer side reuses exactly the same layout; do not add separate back-side markup.

    Rework/consolidate the Styling fence so its effective declarations implement all proportional D-01 signatures rather than leaving the quick-029/030 blue hero in control: ergonomic dark page/card colors; `40px 16px` page padding; centered 460px shell with `28px 24px` card padding, `1px solid #333333`, `8px` radius, and reference shadow; serif body/content and sans-serif IPA/headings; baseline/wrapping word/IPA/audio row with its `10px` gap and `20px` margin; the specified word/IPA weights, line heights, and letter spacing; `20px 0` divider spacing; compact uppercase heading metrics; definition/example/Translation text metrics; unboxed plain example content; and muted Translation. Retain overflow wrapping, responsive containment, native replay SVG support, and the existing optional image containment. Remove or override the blue top accent, blue callout panel, circular blue audio chrome, centered-column hero, and stale larger-radius/word declarations. Do not introduce external assets, dynamic field-driven JavaScript, `innerHTML`, or edits outside the three declared files (D-04/D-06).

    Reach GREEN with the modified loader suite and the unchanged verification-only integration suite. Re-run `git diff --unified=0 -- src/multilang/templates/normal_card.md tests/services/test_card_template_loader.py` plus the same executable contract-anchor inspection used initially. Then create `UI-PROOF.md` containing fenced JSON with `proof_bundle_version`, `scope`, `route_state`, `environment`, `viewport`, `evidence_inputs`, `commands_or_manual_steps`, `observations`, `artifacts`, `privacy`, `result`, and `claim_limits`. Record at least eight exact source/generated-template/test observations for the first proof slot, including separate initial/final diff observations that identify the preserved pre-existing conditionals, audio, reveal, example-panel, helper, exact-reference, and Mandarin-composition hunks. Include artifact metadata fields `visibility`, `retention`, `sensitivity`, and `safe_to_publish`.

    Do not create browser tooling or screenshots. Record explicitly that agent-browser, if available, renders a regular browser surface rather than Anki's native Desktop/mobile WebViews and therefore cannot satisfy native acceptance. Set the overall native-rendering result to `human_needed` and list the four Desktop/mobile front/back human-fallback observations still required, including image/audio/translation checks.
  </action>
  <verify>
    <automated>uv run pytest tests/services/test_card_template_loader.py tests/integration/test_v13_normal_template_export_contract.py -q</automated>
    <automated>git diff --unified=0 -- "src/multilang/templates/normal_card.md" "tests/services/test_card_template_loader.py"</automated>
    <automated>npx -y gsdd-cli ui-proof validate .planning/quick/032-adaptar-template-normal-gemini/UI-PROOF.md</automated>
    <automated>git diff --check -- "src/multilang/templates/normal_card.md" "tests/services/test_card_template_loader.py" ".planning/quick/032-adaptar-template-normal-gemini/UI-PROOF.md"</automated>
  </verify>
  <done>The normal generated template uses the Gemini visual while all contracts and Mandarin composition pass; UI-PROOF records automated evidence honestly and leaves native Anki appearance human_needed. No commit or out-of-scope edit is made.</done>
</task>

## Threat Model

### Trust Boundaries

| Boundary | Description |
|---|---|
| Generated field data → Anki HTML renderer | Existing Anki placeholders render lexical text, intentional definition HTML, audio, and optional image content inside the template. |

### STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-Q032-01 | Tampering / Elevation | `normal_card.md` field interpolation | accept | Raw Anki field rendering is an existing product contract and this visual-only task cannot alter generation/sanitization per D-03/D-06; add no new field references, `innerHTML`, external scripts, or field-driven JavaScript. |
| T-Q032-02 | Denial of service | Long text or oversized optional image in card layout | mitigate | Retain `overflow-wrap`, bounded `max-width`, `box-sizing`, responsive padding, and contained image sizing; loader/export tests keep the optional image wiring intact. |

## Source Coverage Audit

| Source | Item | Coverage |
|---|---|---|
| GOAL | Adapt the normal production card to the Gemini visual on both sides | Tasks 032-01 and 032-02 |
| REQ | No phase requirement IDs apply in quick mode | N/A |
| RESEARCH | Visual constraints extracted from `gemini-code-1785178063558.html` | D-01; Tasks 032-01 and 032-02 |
| CONTEXT | D-01 through D-06 | All covered explicitly in task behavior/actions |

Excluded without gap: every template family outside normal, architecture changes, browser scaffolding, full-suite drift, and native Anki observations that are explicitly `human_needed`.

## Success Criteria

- Only the current loader regression test, `normal_card.md`, and `UI-PROOF.md` are changed by this quick task.
- Focused pytest proves the exact normal field/reference/reveal/export contract and Mandarin CSS prefix composition.
- Effective normal CSS matches the proportional palette, dimensions, spacing, typography, and heading signatures in D-01, and no stale blue-hero declaration wins the cascade.
- Translation is hidden on the front and shown on the back in the identical `FrontSide` layout; image/audio/conditionals remain present.
- UI proof passes structural validation while native Anki Desktop/mobile appearance remains explicitly `human_needed`.
- UI proof records executable initial/final diff and source-contract inspections proving the important pre-existing quick-029/030 hunks remain present.
- ROADMAP, SPEC, LOG, loader/services, other templates, schemas, IDs, routing, generation, and providers are untouched; nothing is staged or committed.
