---
task: 030-unify-dark-card-layouts
mode: quick
subsystem: ui
tags: [anki, html, css, templates, tdd]
runtime: opencode
assurance: self_checked
requires:
  - task: 029-restyle-anki-card-templates
    provides: dirty-tree dark restyle for normal, phoneme, and Mandarin templates
provides:
  - Always-dark blue styling for normal, shared phoneme, and Mandarin templates
  - Panel-contained answer translations for normal, Mandarin, and phoneme cards
  - Five-family static front/back preview showing the three revised dark designs plus original Japanese frequency and Kana designs
affects: [normal-cards, phoneme-decks, mandarin, japanese-frequency, kana]
tech-stack:
  added: []
  patterns: [semantic example-panel containment, scoped three-family dark palette, unchanged Japanese and Kana templates]
key-files:
  created:
    - .planning/quick/030-unify-dark-card-layouts/UI-PROOF.md
  modified:
    - tests/services/test_card_template_loader.py
    - tests/services/test_export_anki_package.py
    - src/multilang/templates/normal_card.md
    - src/multilang/templates/russian_phoneme_card.md
    - src/multilang/templates/mandarin_card.md
    - modified_templates_preview.html
key-decisions:
  - "Apply the locked dark design only to normal, shared phoneme, and Mandarin; keep Japanese frequency and Kana byte-for-byte at their pre-task production state."
  - "Treat browser and native Anki appearance as human-needed because no rendering tool or screenshot evidence was available."
requirements-completed: []
duration: 7min
completed: 2026-07-23
---

# Quick Task 030: Unify Selected Dark Card Layouts Summary

**Normal, shared phoneme, and Mandarin cards now share the locked dark-blue design, while Japanese frequency and Kana retain their original light/night purple designs and pedagogy.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-07-23T20:11:43Z
- **Completed:** 2026-07-23T20:18:45Z
- **Tasks:** 3
- **Final changed implementation/evidence files:** 7 (excluding this summary)
- **Git actions:** None, as explicitly required

## Accomplishments

- Added focused generated-model and source-level regressions covering all five template families, including exact field order, references, conditionals, reveal behavior, shared phoneme identity, dark palette values for the three revised families, and original palette contracts for Japanese/Kana.
- Nested normal, Mandarin, and phoneme answer translations inside semantic example panels without changing scripts or field references.
- Restored Japanese frequency and Kana byte-for-byte to their pre-task production state after the user corrected scope.
- Expanded `modified_templates_preview.html` to exactly five front/back pairs: the new dark design for normal/phoneme/Mandarin and the original designs for Japanese/Kana.
- Reconciled one stale exporter regression assertion with the planned panel-contained translation markup after post-verification exposed the mismatch.

## TDD Evidence

### RED

Only `tests/services/test_card_template_loader.py` was changed before the first run.

- Command: `uv run pytest tests/services/test_card_template_loader.py -q`
- Result: **5 failed, 19 passed**
- Attributable failures under the original, later-superseded five-family scope: missing `examplePanel` containment in normal, Mandarin, and phoneme templates; Japanese and Kana still had light base palettes. The final user correction intentionally preserves those original Japanese/Kana palettes instead.
- Existing focused assertions remained green.

### GREEN

The initial GREEN was reached after modifying five production templates; the later user correction restored both Japanese production templates and revised their focused assertions:

- Focused suite: **24 passed**
- Generated-model inspection: `all five generated template contracts OK`
- Unchanged broader suites: **29 passed**
- Post-verification quick-029 focused suite after assertion reconciliation: **60 passed**
- Final combined focused suites after the user-directed correction: **78 passed**

## Files Changed/Verified

- `tests/services/test_card_template_loader.py` - Contracts the three revised dark layouts while preserving Japanese/Kana original light/night purple palettes and pedagogy.
- `tests/services/test_export_anki_package.py` - Updated one stale exact-markup expectation from `sentenceTranslation indent` to the planned panel-contained `sentenceTranslation` markup.
- `src/multilang/templates/normal_card.md` - Always-dark normal card with translation inside its example panel.
- `src/multilang/templates/russian_phoneme_card.md` - Shared phoneme palette and sentence-answer panel containment.
- `src/multilang/templates/mandarin_card.md` - Language-aware example panel retaining Pinyin and Traditional lines.
- `src/multilang/templates/japanese_card.md` - **Unchanged in final diff**; restored byte-for-byte to HEAD/pre-task state.
- `src/multilang/templates/japanese_kana_card.md` - **Unchanged in final diff**; restored byte-for-byte to HEAD/pre-task state.
- `modified_templates_preview.html` - Exactly five labeled front/back pairs with the corrected mixed-design scope.
- `.planning/quick/030-unify-dark-card-layouts/UI-PROOF.md` - Structured proof bundle with ten observations and honest claim limits.

## Verification

- `uv run pytest tests/services/test_card_template_loader.py -q` → **24 passed**
- Quick-029 focused suite after the verification-driven assertion fix → **60 passed**
- Final combined focused suites after Japanese/Kana restoration and assertion updates → **78 passed**
- Dedicated phoneme/Japanese/Kana suites from the plan → **29 passed**
- Generated-model contract inspection → **passed**
- Five-pair preview source validation → **passed**
- UI proof JSON validation → **passed**
- Final diff inspection → **no changes** for `japanese_card.md` or `japanese_kana_card.md`
- `git diff --check --` on the test, five templates, and preview → **passed**
- No service/domain/export production implementation was added by this task.
- `.planning/ROADMAP.md`, `.planning/SPEC.md`, and `.planning/quick/LOG.md` were not edited by this executor; their pre-existing worktree state was preserved.

## Decisions Made

- Used equal always-dark base/night compatibility values for normal, phoneme, and Mandarin rather than requiring Anki's mode class to activate their theme.
- Honored the corrected scope by keeping Japanese frequency and Kana exactly at their original production designs, including their light/night purple palettes.
- Kept proof proportional: source/tests establish structure, while exact browser and native Anki appearance remain human-needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test contract drift] Updated stale exact-markup exporter assertion**
- **Found during:** Post-verification regression run
- **Issue:** `tests/services/test_export_anki_package.py` still expected `class="sentenceTranslation indent"`, although the planned semantic `examplePanel` wrapper now owns panel indentation and the translation correctly uses `class="sentenceTranslation"` inside it.
- **Root cause:** The exporter test encoded the pre-containment class string as an exact markup contract rather than the preserved translation/reveal semantics. The production layout changed as planned, but this adjacent assertion was not included in the original test write surface.
- **Fix:** Updated only the stale expected markup in `tests/services/test_export_anki_package.py`; no production template, behavior, field, script, or exporter implementation changed.
- **Verification:** Quick-029 focused suite passes **60 tests**; broader phoneme/Japanese/Kana suites pass **29 tests**.

**2. [User-directed scope correction] Restored Japanese frequency and Kana production templates**
- **Found during:** Post-completion user review
- **Issue:** The approved final scope excludes Japanese frequency and Kana from quick-030 production restyling, contrary to the original plan's five-family always-dark requirement.
- **Correction:** Restored `src/multilang/templates/japanese_card.md` and `src/multilang/templates/japanese_kana_card.md` byte-for-byte to HEAD/pre-task state; revised focused assertions to preserve their original light/night purple palettes and pedagogical contracts; revised the static preview to show their original designs.
- **Final production scope:** Only normal, shared phoneme, and Mandarin receive the new always-dark design and panel containment.
- **Verification:** Combined focused suites pass **78 tests**, and final diff inspection shows no changes for either Japanese production template.

**Total deviations:** 2 (1 auto-fixed test-contract drift, 1 explicit user-directed scope correction).
**Impact on plan:** The final result intentionally narrows the production restyle from five families to three while retaining five-family contract and preview coverage.

## Issues Encountered

- The proof-validation one-liner initially needed shell-safe quoting because Markdown backticks were interpreted by Bash. Re-running the unchanged validation with safe quoting passed.

## Known Stubs

None found in the three modified production templates.

## Claim Limits

No browser renderer, agent-browser session, screenshot, Anki Desktop, or mobile Anki client was available. Exact layout, fonts, replay controls, WebView behavior, and reveal rendering therefore remain **human_needed**. The static preview is not presented as native Anki proof.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Final combined focused suites passed 78 tests; generated contracts and the corrected preview were checked; final diff inspection confirmed Japanese frequency and Kana production templates are unchanged.
</executor_check>
</checks>

<handoff>
plan_runtime: unknown
plan_assurance: unknown
plan_check_status: unknown
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: false
</handoff>

<deltas>
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Post-verification found one adjacent exporter test with a stale pre-panel exact class-string expectation; the assertion was aligned with the planned markup and all focused/broader suites passed.
- class: intent_scope_change
  impact: recoverable
  disposition: proceeded
  summary: User explicitly corrected the final scope so Japanese frequency and Kana remain byte-for-byte unchanged; tests and preview were aligned with that direction and 78 focused tests passed.
</deltas>

<judgment>
<active_constraints>
Preserve all current dirty-tree work and immutable Anki field/reveal/audio contracts. Keep Japanese frequency and Kana production templates exactly at their pre-quick-030 state. Do not claim native visual acceptance from static source.
</active_constraints>
<unresolved_uncertainty>
Exact browser and native Anki Desktop/mobile appearance has not been observed.
</unresolved_uncertainty>
<decision_posture>
Use one always-dark palette only for normal, shared phoneme, and Mandarin; preserve Japanese frequency and Kana original light/night purple designs.
</decision_posture>
<anti_regression>
Do not move normal/Mandarin/phoneme translations back outside their panels, make those three designs mode-dependent, or introduce any quick-030 production diff in Japanese frequency or Kana.
</anti_regression>
</judgment>

## Self-Check: PASSED

The corrected summary and proof reflect the reported 78 passing focused tests and unchanged Japanese/Kana production templates. Exact browser/native Anki appearance remains human-needed. No git operation was performed during this documentation correction.
