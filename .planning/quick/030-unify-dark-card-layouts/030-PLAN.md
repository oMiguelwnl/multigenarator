---
mode: quick
task: 030-unify-dark-card-layouts
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: []
files_modified:
  - tests/services/test_card_template_loader.py
  - src/multilang/templates/normal_card.md
  - src/multilang/templates/russian_phoneme_card.md
  - src/multilang/templates/mandarin_card.md
  - src/multilang/templates/japanese_card.md
  - src/multilang/templates/japanese_kana_card.md
  - modified_templates_preview.html
  - .planning/quick/030-unify-dark-card-layouts/UI-PROOF.md
non_goals:
  - Do not change note-model IDs, deck IDs, field names/order, generation data, provider behavior, or exporter routing.
  - Do not restyle Latin, highlight, Korean, or any template outside the five explicitly selected files.
  - Do not treat a browser rendering of the preview as proof of native Anki Desktop or mobile rendering.
hard_boundaries:
  - Preserve all current working-tree changes and build on the prior CSS restyle; do not revert, overwrite from HEAD, or clean unrelated tracked/untracked files.
  - Preserve filenames, Anki field references and conditionals, audio references, reveal scripts, Japanese furigana toggle and links, and Kana media blocks.
  - Do not flatten Japanese frequency or Kana pedagogy into the normal-card DOM structure; make only the markup changes needed to group answer-only content with its own panel.
  - The executor must not edit .planning/ROADMAP.md, .planning/SPEC.md, or .planning/quick/LOG.md and must not stage or commit; the quick-workflow orchestrator may perform its mandatory post-verification LOG append after execution and verification finish.
escalation_triggers:
  - Stop if an always-dark implementation requires changing an exported field, service/model contract, reveal behavior, or a production file outside the five templates.
  - Stop if a focused pre-existing assertion fails before production edits for a reason unrelated to the newly added regressions.
approval_gates:
  - Native Anki visual acceptance remains a later human verification gate; browser-preview evidence must not be promoted to that claim.
anti_regression_targets:
  - Normal and Mandarin translations remain hidden on the question side and reveal on the answer side inside their example panels.
  - Shared Russian, Polish, and Greek phoneme models keep identical templates/CSS and sentence-translation reveal behavior.
  - Japanese frequency keeps its furigana toggle, separate front/back pedagogy, audio, optional image, and Jisho/Images/Weblio links.
  - Kana keeps its separate recognition/reveal sides and optional Gif, Picture, Strokes, and Mnemonic media/content blocks.
known_unknowns:
  - No tool-supported screenshot is planned, so exact browser layout and native Anki font, replay-control, WebView, and reveal rendering fidelity remain unobserved.
closure_claim_limit: Completion proves source/generated-model contracts and the structure of the local static preview; exact browser and native Anki Desktop/mobile appearance remain human_needed unless a tool-supported rendering artifact is captured separately.
parallelism_budget:
  max_concurrent_plans: 1
  safe_parallelism: []
leverage:
  lost: The preview intentionally duplicates representative rendered markup instead of becoming a template compiler.
  kept: Existing loaders, model builders, field contracts, language-specific pedagogy, and the prior dark restyle.
  gained: One explicit always-dark visual contract and a repeatable five-template browser review surface.
must_haves:
  truths:
    - "Normal, shared phoneme, Mandarin, Japanese frequency, and Kana cards use the same always-dark blue palette whether or not Anki night mode is active."
    - "The normal and Mandarin answer translations are visually inside the same dark example panel as their example content, matching normal_card_inline_lightdark.html."
    - "Each selected template preserves its exported fields/order, Anki conditionals, audio references, reveal behavior, and language-specific teaching structure."
    - "modified_templates_preview.html accurately shows front and back states for all five selected template families."
  artifacts:
    - path: src/multilang/templates/normal_card.md
      provides: "Always-dark normal layout with hidden/revealed translation inside the example panel"
    - path: src/multilang/templates/russian_phoneme_card.md
      provides: "Always-dark shared phoneme layout without shared-deck contract drift"
    - path: src/multilang/templates/mandarin_card.md
      provides: "Mandarin markup and auxiliary typography composed over the always-dark normal CSS"
    - path: src/multilang/templates/japanese_card.md
      provides: "Always-dark Japanese frequency front/back while retaining furigana and links"
    - path: src/multilang/templates/japanese_kana_card.md
      provides: "Always-dark Kana recognition/reveal layout retaining all media blocks"
    - path: modified_templates_preview.html
      provides: "Static front/back browser preview for all five template families"
    - path: .planning/quick/030-unify-dark-card-layouts/UI-PROOF.md
      provides: "Honest browser-preview evidence and native-Anki claim boundary"
  key_links:
    - from: src/multilang/templates/normal_card.md
      to: src/multilang/templates/mandarin_card.md
      via: "card_template_loader concatenates normal CSS before Mandarin CSS"
    - from: src/multilang/templates/russian_phoneme_card.md
      to: Russian/Polish/Greek phoneme models
      via: "shared _load_phoneme_template path"
    - from: src/multilang/templates/japanese_card.md
      to: Japanese frequency model and integrated Japanese frequency export
      via: "dedicated Japanese template loaders"
    - from: src/multilang/templates/japanese_kana_card.md
      to: imported and generated Kana decks
      via: "shared build_kana_model template loader"
ui_proof_slots:
  - slot_id: five-template-browser-preview
    claim: "The local static preview source contains distinct front and back states for normal, shared phoneme, Mandarin, Japanese frequency, and Kana using one always-dark blue visual language, with answer-only content placed in each template's intended panel."
    route_state: "Inspect modified_templates_preview.html for the ten labeled cards (five families x front/back), including normal/Mandarin translation containment, Japanese front toggle/back meanings and links, and Kana front/back media structure."
    required_evidence_kinds: [code, test]
    minimum_observations: 10
    expected_artifact_types: ["focused pytest output", "static HTML source", "UI-PROOF.md observation records"]
    validation_command: "uv run pytest tests/services/test_card_template_loader.py -q"
    environment: "Repository source/model inspection; agent-browser is unavailable in the current shell and no screenshot artifact is required"
    viewport: "Responsive CSS is inspected at source level only; no browser viewport is claimed as observed"
    manual_acceptance_required: true
    claim_limit: "Proves the static preview's source structure only; exact browser layout, native Anki rendering, live field substitution, and native replay controls remain human_needed without tool-supported rendering evidence."
  - slot_id: native-anki-five-template-acceptance
    claim: "Representative generated cards for all five families render acceptably on their question and answer sides in native Anki."
    route_state: "Inspect representative normal, shared phoneme, Mandarin, Japanese frequency, and Kana cards front/back in Anki Desktop and a portrait mobile Anki client."
    required_evidence_kinds: [human]
    minimum_observations: 20
    expected_artifact_types: ["manual checklist for five families x front/back x desktop/mobile"]
    validation_command: "uv run pytest tests/services/test_card_template_loader.py tests/services/test_russian_phoneme_deck.py tests/services/test_japanese_frequency_deck.py tests/services/test_japanese_kana_deck.py -q"
    environment: "Native Anki Desktop and mobile Anki client; unavailable to the repository browser-preview run"
    viewport: "Desktop and representative portrait-mobile native Anki surfaces"
    manual_acceptance_required: true
    claim_limit: "Native appearance remains human_needed until all twenty observations are recorded; browser HTML cannot close this slot."
---

# Quick Task 030 Plan: Unify Always-Dark Card Layouts

## Objective

Finish the prior restyle by giving the five user-selected template families one always-dark blue visual language, correcting answer-panel containment, and expanding the browser preview without changing any Anki data or pedagogical contract.

## Context

- `normal_card_inline_lightdark.html` is the locked layout reference, especially its back-side translation nested inside the example panel.
- `unified_templates_preview.html` supplies the locked dark palette: page `#0a1220`, card `#0f1b2d`, panel `#12213a`, border `#24405f`, accent `#3b82f6`, accent text `#93c5fd`, word `#bfdbfe`, primary text `#e8f0fe`, and muted text `#7f9bc4`.
- Quick task 029 already changed normal, phoneme, and Mandarin CSS and tests in the dirty working tree. Preserve those edits and evolve them in place.
- `card_template_loader.py` composes Mandarin CSS as complete normal CSS followed by Mandarin-specific CSS. Japanese frequency and Kana load their own selected markdown templates; imported and generated Kana decks share `build_kana_model`.
- Research skipped: this is an internal HTML/CSS/template-contract change using established files and pytest patterns; no new dependency, browser tooling, or external API is needed.

## Locked Decisions

1. `normal_card.md`, `russian_phoneme_card.md`, `mandarin_card.md`, `japanese_card.md`, and `japanese_kana_card.md` are all in scope.
2. Styling is always dark and does not depend on `.nightMode` being present.
3. Normal/Mandarin answer translations belong visually inside their example panels.
4. Japanese frequency and Kana retain their own teaching structures; they are not normal-card variants.
5. Existing filenames, fields/order, conditionals, audio, furigana toggle, links, Kana media, and reveal behavior are immutable contracts.

## Evidence Contract

- Observe a real RED from newly added contract/layout assertions before modifying production templates.
- Reach GREEN in the single edited regression file, then run the existing phoneme/Japanese suites unchanged as broader verification.
- Inspect generated model front/back/CSS rather than only markdown source.
- Inspect the updated static preview source and record ten family/side observations in `UI-PROOF.md`; do not require or create screenshot artifacts.
- Report exact browser and native Anki appearance as `human_needed` because no tool-supported rendering artifact is planned.

## Tasks

<task id="030-01" type="auto" tdd="true">
  <name>Lock the five template contracts and always-dark layout in tests</name>
  <files>
    - tests/services/test_card_template_loader.py
  </files>
  <behavior>
    - Normal and Mandarin generated fronts keep exact field-reference order, hidden translation, `FrontSide`, and reveal scripts, while the translation is nested in an example-panel wrapper after the sentence/audio row.
    - Normal CSS defines the locked dark palette as the base state and produces the same effective page/card/text/panel colors with or without `.nightMode`; no light base palette controls the rendered card.
    - Mandarin keeps base-CSS-prefix composition and Pinyin/Traditional ordering and places Sentence Pinyin, Traditional Sentence, and hidden Translation inside its language-aware example panel.
    - Shared phoneme models retain exact field order/references, identical Russian/Polish/Greek template/CSS, native audio references, and answer reveal while using the same base dark palette and panel vocabulary.
    - Japanese frequency retains exact fields, conditionals, front furigana toggle/audio, back image/audio/meaning rows and all three links while gaining palette/panel signatures that are dark in both base and night-mode states.
    - Kana retains exact fields and the `Gif`, `Picture`, `Strokes`, and `Mnemonic` conditionals/order plus audio while gaining the same always-dark shell/panels in both base and night-mode states.
  </behavior>
  <action>
    Extend only `tests/services/test_card_template_loader.py` before touching production files. Import the existing phoneme, Japanese frequency, and Kana model builders into this test module and add focused source/generated-model semantic assertions for all five templates; do not duplicate their full dedicated suites or modify those suite files. Assert generated-model contracts and semantic markup/CSS signatures rather than whole-file snapshots. For translation containment, assert a dedicated panel wrapper encloses the sentence/audio and answer-only translation in normal and Mandarin; apply equivalent panel containment to the phoneme sentence/translation without altering its reveal fallback. For Japanese/Kana, assert their existing language-specific selectors and exact pedagogical/reference anchors remain present and ordered while base variables already equal the approved dark values. Run this one test file and record the expected failures from the new containment/Japanese/Kana/always-dark assertions. Do not weaken or delete prior quick-029 assertions to manufacture RED.
  </action>
  <verify>
    <automated>uv run pytest tests/services/test_card_template_loader.py -q</automated>
    Expected RED: newly added assertions fail because translations are not yet panel-contained and Japanese/Kana still use light base palettes; existing contract tests remain green.
  </verify>
  <done>The single focused test file encodes all five immutable contracts and desired layout, and an attributable RED result is recorded before production edits.</done>
</task>

<task id="030-02" type="auto" tdd="true">
  <name>Unify production templates without flattening pedagogy</name>
  <files>
    - src/multilang/templates/normal_card.md
    - src/multilang/templates/russian_phoneme_card.md
    - src/multilang/templates/mandarin_card.md
    - src/multilang/templates/japanese_card.md
    - src/multilang/templates/japanese_kana_card.md
  </files>
  <action>
    Build on the existing dirty-tree restyle rather than replacing files from HEAD. In normal and Mandarin markup, add a semantic example-panel wrapper so sentence/audio and the hidden Translation are siblings inside the same `#12213a` panel; keep the same translation ID, inline hidden state, field references, and back reveal script. In the phoneme template, group the example sentence, audio, and hidden sentence translation inside the corresponding dark panel while retaining `FrontSide`, the IIFE, and the noscript fallback. Make base selectors and variables in all five templates use the locked dark palette unconditionally; `.nightMode` selectors may remain only as equal-value compatibility rules and must not be required to activate dark styling.

    Restyle Japanese frequency within its existing `jpCard--front`/`jpCard--back` hierarchy: preserve the front recall flow, toggle function and selectors, two audio fields, optional back image, furigana filters, separate word/sentence meaning rows, and Jisho/Images/Weblio footer. Restyle Kana within its existing recognition front and media-rich reveal back: preserve every conditional and the Gif → divider → Romaji/Audio → Picture → Strokes → Mnemonic order. Use shared palette values, rounded blue-top shells, dark panels, circular native replay SVG treatment, overflow safety, and responsive spacing, but do not copy normal-card markup into either Japanese template. Run the focused suite to GREEN and inspect generated normal, Mandarin frequency/word-list, Russian/Polish/Greek phoneme, Japanese frequency, and imported/generated Kana model contracts.
  </action>
  <verify>
    <automated>uv run pytest tests/services/test_card_template_loader.py -q</automated>
    <automated>uv run python -c "from multilang.domain.jobs import SupportedLanguage as L; from multilang.services.card_template_loader import load_card_template; from multilang.services.russian_phoneme_deck import build_russian_phoneme_model,build_polish_phoneme_model,build_greek_phoneme_model; from multilang.services.japanese_frequency_deck import build_japanese_model; from multilang.services.japanese_kana_deck import build_kana_model; n=load_card_template('frequency'); z=load_card_template('frequency',language=L.ZH); p=[build_russian_phoneme_model(),build_polish_phoneme_model(),build_greek_phoneme_model()]; j=build_japanese_model(); k=build_kana_model(); assert z.css.startswith(n.css) and p[0].templates==p[1].templates==p[2].templates and p[0].css==p[1].css==p[2].css and 'toggleFurigana' in j.templates[0]['qfmt'] and '{{#Gif}}' in k.templates[0]['afmt']; print('all five generated template contracts OK')"</automated>
    <automated>uv run pytest tests/services/test_russian_phoneme_deck.py tests/services/test_japanese_frequency_deck.py tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py -q</automated>
  </verify>
  <done>All five production templates are always dark, answer content is panel-contained where appropriate, every immutable contract survives generated-model inspection, and the focused suite is green.</done>
</task>

<task id="030-03" type="auto">
  <name>Update the five-family preview and record proportional local evidence</name>
  <files>
    - modified_templates_preview.html
    - .planning/quick/030-unify-dark-card-layouts/UI-PROOF.md
  </files>
  <action>
    Rewrite the existing static preview so it has labeled front/back examples for exactly normal, shared phoneme, Mandarin, Japanese frequency, and Kana. Make representative markup mirror each production hierarchy and state: front translations hidden; normal/Mandarin back translations inside the example panel; phoneme answer translation in its sentence panel; Mandarin Pinyin/Traditional lines retained; Japanese front recall/toggle controls and back image/meanings/links represented; Kana front recognition and back Gif/Picture/Strokes/Mnemonic blocks represented. Keep the document always dark and responsive. Do not present the preview as executable Anki templates or duplicate/export production field contracts from it.

    Write `UI-PROOF.md` with fenced JSON containing `proof_bundle_version`, scope, route/state, environment, viewport, evidence inputs, exact commands, at least ten family/side source observations, artifact metadata (`visibility`, `retention`, `sensitivity`, `safe_to_publish`), privacy, result, and claim limits. Record that `agent-browser` is unavailable and no tool-supported screenshot artifact was captured. The local static preview may support code/test evidence that all ten states and expected structures exist, but exact browser layout and native Anki rendering must both remain `human_needed`.
  </action>
  <verify>
    <automated>uv run python -c "from pathlib import Path; p=Path('modified_templates_preview.html').read_text(encoding='utf-8'); names=('normal','phoneme','mandarin','japanese-frequency','kana'); assert all(f'data-template=\"{n}\"' in p for n in names); assert all(p.count(f'data-template=\"{n}\"') == 2 for n in names); assert p.count('data-side=\"front\"') == 5 and p.count('data-side=\"back\"') == 5; assert 'nightMode' not in p; print('five front/back preview pairs OK')"</automated>
    <automated>uv run python -c "import json,re; from pathlib import Path; p=Path('.planning/quick/030-unify-dark-card-layouts/UI-PROOF.md'); d=json.loads(re.search(r'```json\s*(.*?)\s*```',p.read_text(encoding='utf-8'),re.S).group(1)); required={'proof_bundle_version','scope','route_state','environment','viewport','evidence_inputs','commands_or_manual_steps','observations','artifacts','privacy','result','claim_limits'}; assert required.issubset(d) and len(d['observations']) >= 10; assert all(Path(x['path']).exists() for x in d['artifacts']); assert d['result'] == 'human_needed' and 'native Anki' in d['claim_limits'] and 'browser' in d['claim_limits']; print('UI proof bundle OK; exact browser/native Anki remain human_needed')"</automated>
  </verify>
  <done>The local preview source accurately covers ten front/back states, its proof metadata exists, and the evidence explicitly leaves exact browser and native Anki rendering human_needed.</done>
</task>

## Verification

- Run `uv run pytest tests/services/test_card_template_loader.py -q` after all tasks and require a clean pass.
- Run the unchanged existing suites with `uv run pytest tests/services/test_russian_phoneme_deck.py tests/services/test_japanese_frequency_deck.py tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py -q`.
- Run `git diff --check --` on the five templates, one edited test, and preview.
- Confirm `git diff --name-only` includes no service/domain/export implementation added by this task.
- Confirm the executor did not modify `.planning/ROADMAP.md`, `.planning/SPEC.md`, `.planning/quick/LOG.md`, or unrelated dirty-tree paths; the orchestrator may append the mandatory quick-task LOG row only after verification.
- Do not stage or commit.

## Success Criteria

- Five selected production templates share the locked always-dark blue palette in base and Anki night-mode states.
- Normal/Mandarin answer translations render inside their example panels; phoneme sentence translation uses its corresponding panel; reveal semantics are unchanged.
- Japanese frequency and Kana remain distinct pedagogical layouts with every named behavior and media contract preserved.
- The single edited focused test shows recorded RED then GREEN, unchanged existing suites pass, and generated models retain fields/order/wiring.
- `modified_templates_preview.html` contains all five front/back pairs and `UI-PROOF.md` records proportional source/model evidence without screenshot artifacts.
- Exact browser and native Anki rendering are both reported honestly as human gates.
- The executor makes no roadmap/spec/log update, unrelated cleanup, or commit; only the orchestrator's mandatory post-verification quick-task LOG append is allowed afterward.

## Notes

- The current worktree intentionally contains quick-029 CSS/test edits plus unrelated changes. Executors must edit the current files in place and never restore target files from `HEAD`.
- The write surface is exactly eight files: one focused existing test, five production templates, the static preview, and `UI-PROOF.md`. Existing dedicated phoneme/Japanese suites are verification-only and must remain unmodified.
