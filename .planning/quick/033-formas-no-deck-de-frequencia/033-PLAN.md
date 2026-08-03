---
mode: quick
task: 033-formas-no-deck-de-frequencia
plan: 033
type: execute
wave: 1
runtime: opencode
assurance: self_checked
depends_on: []
autonomous: true
task_count: 2
requirements: []
files_modified:
  - docs/multilingual-lexical-adaptive-plan-v4.md
reduced_assurance: true
reduced_assurance_reason: ".planning/templates/roles/planner.md is absent from the worktree and HEAD; this plan applies the supplied quick-mode planner contract directly."
non_goals:
  - "Do not activate v4, start Phase 35, or change the active v3 Korean milestone."
  - "Do not implement runtime behavior, schemas, migrations, source data, templates, tests, exports, or UI."
  - "Do not revise the substantive scope of Core identities, Optional Expansion identities, form justification, optional card roles, or the isolated Classical Latin path beyond resolving the locked count and routing semantics."
hard_boundaries:
  - "The execution write set is exactly docs/multilingual-lexical-adaptive-plan-v4.md; workflow artifacts are handled separately."
  - "Treat .planning/SPEC.md, .planning/ROADMAP.md, .planning/STATE.md, source, templates, tests, Quick Tasks 029/030/032, and every unrelated dirty path as read-only."
  - "Use apply_patch for every master-document edit; do not stage, commit, restore, clean, reformat, or update .planning/quick/LOG.md."
  - "Do not run the broad test suite; this documentation task closes through exhaustive document inspection, protected-scope checks, and task-owned whitespace checks."
anti_regression_assertions:
  - "Core 3x1000 always denotes exactly 3000 lexical identities (1000 per level), never a 3000-card maximum."
  - "No justified Important Form of a Core identity may be dropped, capped, or rerouted merely to keep a frequency export at 3000 cards."
  - "Every Core Important Form card uses the exact real frequency level/subdeck of its parent identity and is sequenced after the lemma."
  - "Important Forms are neither Optional Expansion identities nor an opt-in card class, and no standalone top-level Important Forms subdeck exists."
  - "Optional Expansion remains opt-in and contains only additional lexical identities beyond Core; a form card inherits its parent source/inventory destination without becoming an expansion identity."
  - "Active planning and all concurrent unrelated work remain untouched."
browser_proof_required: false
no_ui_proof_rationale: "Documentation-only revision of a preserved, inactive Markdown master plan; no rendered UI or browser behavior is changed or claimed."
must_haves:
  truths:
    - "A reader understands that Core fixes identity count at 3000 while the corresponding frequency-card count is variable and exceeds 3000 whenever at least one Core Important Form card exists."
    - "The document states the normative total and per-level formulas, distinguishes identity counts from card/workload counts, and reports optional card roles only when explicitly enabled."
    - "Every justified Important Form attached to a Core identity is exported after its lemma in that identity's exact Level 1, 2, or 3 real frequency subdeck."
    - "Important Forms never consume Core or Expansion identity slots, never become Optional Expansion, and never route to a standalone top-level Important Forms subdeck."
    - "Optional Expansion remains a separate opt-in inventory of only additional lexical identities; forms from Core, Expansion, Custom, Highlight, or another source inherit their parent's destination."
    - "Contracts, be/is/was/were examples, end-to-end flow, Phases 35-51, export topology, workload reporting, gates, decisions, and traceability express one consistent rule set."
    - "The preserved v4 proposal remains inactive and no protected active-planning or unrelated dirty file changes."
  artifacts:
    - path: docs/multilingual-lexical-adaptive-plan-v4.md
      provides: "Internally consistent preserved v4 identity-count, Important Form, expansion, sequencing, workload, and export-topology contract"
      contains: "Explicit frequency-card formulas and same-parent destination rules propagated through G0/Phases 35-51 and traceability"
  key_links:
    - from: "Core lexical identity membership and rank"
      to: "default headword card plus every justified Important Form card"
      via: "one identity slot, variable card fan-out, and prerequisite sequencing"
    - from: "parent identity's source/inventory and Core level"
      to: "Important Form export destination"
      via: "the same real subdeck/deck ID rather than an Important Forms or Expansion reroute"
    - from: "N_important_form_cards"
      to: "frequency_card_count and workload gates"
      via: "3000 + N + explicitly enabled optional-role cards, with per-level reconciliation"
    - from: "Optional Expansion membership"
      to: "additional identities and their descendant form cards"
      via: "opt-in identity inventory; descendant forms inherit destination but do not consume expansion identity slots"
    - from: docs/multilingual-lexical-adaptive-plan-v4.md
      to: ".planning/SPEC.md, .planning/ROADMAP.md, and .planning/STATE.md"
      via: "preserved inactive boundary; no promotion or active-planning edit"
---

# Quick Task 033 Plan: Formas no deck de frequência

<objective>
Revise the preserved v4 master plan so `Core 3x1000` is unambiguously an identity inventory and every justified Core `Important Form` increases card workload inside its lemma's real frequency level, without being absorbed by Optional Expansion or a standalone forms deck.

Purpose: remove a contract ambiguity that could otherwise cause implementations to cap frequency exports at 3000 cards or route required forms away from their parent identities.

Output: one internally consistent revision of `docs/multilingual-lexical-adaptive-plan-v4.md`; v4 remains inactive.
</objective>

<context>
- Target: `docs/multilingual-lexical-adaptive-plan-v4.md` (currently the preserved, non-active v4 proposal created by Quick Task 031).
- Discovery level 0: documentation-only consistency work over one existing artifact; no external research, dependency lookup, runtime implementation, or active ROADMAP requirements apply.
- The repository is CLI-first, but architecture/runtime details are out of scope. Broad-suite drift is irrelevant.
- The worktree already contains unrelated concurrent template/test work and Quick Tasks 029/030/032. Capture `git status --short` before editing, preserve that baseline, and never restore or absorb those changes.
- Read every matching occurrence in the target rather than replacing terms mechanically: references to candidate pools `>3000`, 3000 identity slots, Optional Expansion identity limits, and subdecks for other source inventories remain valid when correctly qualified.
</context>

## Locked Decisions

- **D-01 — Identity count, not card ceiling:** `Core 3x1000` is exactly 3000 ranked lexical identities, 1000 in each real frequency level. It is never a cap on cards.
- **D-02 — Mandatory same-level Core forms:** Every justified/approved `Important Form` belonging to a Core identity is exported in the exact same real Level 1/2/3 frequency subdeck as its lemma, with eligibility/order after the lemma under prerequisite sequencing. No truncation to 3000 cards is allowed.
- **D-03 — Normative workload formula:** The document must define `frequency_card_count = 3000 + N_important_form_cards + O_enabled_optional_role_cards`, where the 3000 are default headword recognition cards, `N` counts all exported Core Important Form cards, and `O` counts only optional roles explicitly enabled for that frequency inventory. It must also state `N_important_form_cards > 0 => frequency_card_count > 3000` and reconcile the analogous 1000-based formula per level.
- **D-04 — Forms are not Expansion or a separate deck:** `Important Forms` are required form-role descendants, never `Optional Expansion`, never opt-in merely because they add cards, and never routed to a standalone top-level `Important Forms` subdeck.
- **D-05 — Expansion remains identity-only and opt-in:** `Optional Expansion 0-3000` contains only additional lexical identities beyond Core. A form follows its parent source/inventory destination; an Expansion form can be colocated with its Expansion parent without becoming or consuming an Expansion identity.
- **D-06 — Whole-document consistency:** Align all affected contracts, `be/is/was/were`, end-to-end routing, Phases 35-51, freeze/export/adaptive/migration behavior, workload reports, transverse gates, fixed decisions, capability ownership, gate matrix, and migration traceability. No contradictory wording may remain.
- **D-07 — Preservation boundary:** Keep v4 explicitly inactive and modify no active planning, implementation, test, template, prior quick-task, log, staged state, or unrelated dirty file.

## Anti-Regression Assertions

1. Exactly 3000 Core identities and exactly 3000 default Core headword cards coexist with **more than 3000 frequency cards whenever `N > 0`**.
2. Identity totals/hashes can remain unchanged while form-card and total-card counts intentionally increase; wording such as “form packs do not change the count” must always name **identity count**, never imply unchanged card count.
3. `Important Form` is a card role linked to a parent identity, not a source inventory. Card role cannot override the parent's Level 1/2/3, Expansion, Custom, Highlight, Grammar/foundation, or other approved destination.
4. For a Core parent, lemma and forms share the same frequency subdeck/deck ID; the lemma precedes every form through `DEPEND-01`, and sibling burying remains intact.
5. Expansion opt-in controls additional identities only. It cannot be used to hide, defer, count, or route Core forms.
6. The export topology has real frequency Level 1/2/3 subdecks and may retain real Grammar, Expansion, Custom, and Highlight destinations, but has no top-level `Important Forms` destination.
7. No formula, sample size, freeze count, quality gate, migration preview, or release check may reintroduce a 3000-card ceiling.

<tasks>

<task id="033-01" type="auto">
  <name>Task 1: Fix the normative identity, form, formula, and routing contracts</name>
  <files>docs/multilingual-lexical-adaptive-plan-v4.md</files>
  <action>
Before editing, run `git status --short`, inspect the target diff, and retain the unrelated-worktree baseline in the execution transcript. Then use `apply_patch` only to revise the target's scope/non-goals where needed and §§3.3-3.6 plus §4 per D-01 through D-05. Make the distinction explicit: Core owns exactly 3000 identities/ranks and 3000 default headword-recognition cards, while approved Core forms are mandatory additional cards. Add a machine-searchable normative block containing exactly `core_identity_count = 3000`, `frequency_card_count = 3000 + N_important_form_cards + O_enabled_optional_role_cards`, `N_important_form_cards > 0 => frequency_card_count > 3000`, and `frequency_level_card_count = 1000 + N_level_important_form_cards + O_level_enabled_optional_role_cards`; define every variable and require total/per-level reconciliation. State that `O` is zero unless a card role is explicitly enabled and that no cap, sampling, edition setting, or Expansion routing may discard a justified Core form to preserve 3000 cards.

Update `CARD-01`, `FORM-01` through `FORM-03`, `ROUTE-01`, `LOAD-01`, `DEPEND-01`, and all surrounding prose without weakening `SENSE-01`, `MWE-01`, `DEF-01`, `AUDIO-01`, or `GUID-01`. A form remains outside identity quotas but inside card/workload totals. Routing must resolve parent source/inventory and Core rank/level before role, preserve the exact parent deck ID, then sequence the form after the lemma. Use real topology examples `{language}::Frequency::Level 1`, `Level 2`, and `Level 3`; do not create an `Important Forms` destination. Define Optional Expansion as opt-in additional identities only and explain destination inheritance for Expansion/Custom/Highlight/other parent inventories without recategorizing a form as an identity.

Rewrite the normative `be/is/was/were` example so a Core `be` headword and every approved analysis-specific `is`, `was`, and `were` form card share `be`'s actual frequency level and appear after it. Preserve the distinct indicative/irrealis analyses and GUIDs; if both `were` analyses produce cards, count both in `N`. Update the end-to-end flow so inventory membership/level is inherited through form creation, routing, export, workload, and recovery. Do not edit any other file.
  </action>
  <verify>
    <automated>f="docs/multilingual-lexical-adaptive-plan-v4.md"; rg -n -i -C 1 'Important Forms|form packs?|subdecks?|3000|expans' "$f"</automated>
    <automated>python -c "from pathlib import Path; s=Path('docs/multilingual-lexical-adaptive-plan-v4.md').read_text(encoding='utf-8'); required=('core_identity_count = 3000','frequency_card_count = 3000 + N_important_form_cards + O_enabled_optional_role_cards','N_important_form_cards > 0 => frequency_card_count > 3000','frequency_level_card_count = 1000 + N_level_important_form_cards + O_level_enabled_optional_role_cards','{language}::Frequency::Level 1','{language}::Frequency::Level 2','{language}::Frequency::Level 3'); missing=[x for x in required if x not in s]; assert not missing, missing; forbidden=('Uma identidade pode produzir mais de um card pedagógico sem aumentar a contagem.','Todo deck extra de formas exige relatório','subdecks reais para Core, `Important Forms`','Form packs não alteram contagem;'); found=[x for x in forbidden if x in s]; assert not found, found; print('core/form normative assertions OK')"</automated>
    <automated>git diff --check -- "docs/multilingual-lexical-adaptive-plan-v4.md"</automated>
  </verify>
  <done>The core model, formulas, contracts, English example, and end-to-end flow make identity count fixed, card count variable, Core forms mandatory/same-level/after-lemma, and Expansion identity-only/opt-in.</done>
</task>

<task id="033-02" type="auto">
  <name>Task 2: Propagate the rule through phases, topology, gates, and traceability</name>
  <files>docs/multilingual-lexical-adaptive-plan-v4.md</files>
  <action>
Use `apply_patch` only and perform a phase-by-phase consistency pass over every Phase 35-51 section plus all four transverse gates and §8 traceability per D-06/D-07. Phase 35 must freeze the formulas and distinguish identity quota from exported cards; Phase 36 must persist parent inventory/level and form analysis without assigning form identity membership; Phases 37-44 must keep candidate/Core/Expansion counts identity-based while their pilots and rollout samples exercise inherited destinations, mandatory Core forms, sequencing, and variable workload; Phase 45 must freeze 66,000 identities while separately freezing/reconciling form packs whose cards intentionally raise export counts; Phase 46 must remove the standalone `Important Forms` subdeck and require same-deck-ID/after-lemma export tests; Phases 47-49 must preserve form-role/history mapping, same-level adaptive prerequisites, content/GUID/audio distinctions, and source-destination inheritance; Phases 50-51 must preview/preflight identity counts, card formulas, per-level totals, topology, sequencing, and absence of form-to-Expansion/standalone reroutes. Keep unchanged phase dependencies and unrelated outcomes.

Make `LOAD-01`, phase deliverables, cost/quality gates, migration previews, and release reports expose at least: Core identity count, 3000 default headword-card count, `N` Core Important Form cards, each explicitly enabled optional-role count, computed total, and per-Level 1/2/3 reconciliation; report Expansion identity/headword/form/optional-role counts separately. Clarify every “outside quota” or “does not alter count” reference as outside/not altering **identity** count while increasing **card/workload** count. Treat form packs as versioned datasets linked to parent inventories, not export subdecks. Preserve Grammar as a distinct destination only for grammar/foundation identities or roles already assigned there, not as a sink for Core forms.

Update fixed-decision rows (especially D-05, D-07, D-08, D-12), capability ownership/evidence, gate-by-phase rows, and migration invariants so the formulas, same-parent topology, Expansion separation, workload, and no-card-ceiling rules are traceable. Finally rerun the exhaustive occurrence scan and read every line matching `Important Forms`, `form pack`, `subdeck`, `3000`, or `expans`; repair each remaining ambiguity in context rather than deleting valid identity/source-pool references. Preserve the prominent inactive-v4 boundary, G0, all Phase 35-51 headings/dependencies, all 22 modern languages, isolated Latin, and every unrelated contract.
  </action>
  <verify>
    <automated>f="docs/multilingual-lexical-adaptive-plan-v4.md"; rg -n -i -C 1 'Important Forms|form packs?|subdecks?|3000|expans' "$f"</automated>
    <automated>python -c "import re; from pathlib import Path; s=Path('docs/multilingual-lexical-adaptive-plan-v4.md').read_text(encoding='utf-8'); assert all(f'### Fase {n}:' in s for n in range(35,52)); assert re.search(r'Important Forms.{0,160}nunca.{0,160}Optional Expansion', s, re.I|re.S); assert re.search(r'n[aã]o existe.{0,120}subdeck.{0,120}Important Forms', s, re.I|re.S); assert re.search(r'Important Form.{0,240}mesmo subdeck real.{0,240}lema', s, re.I|re.S); assert re.search(r'expans[aã]o opcional.{0,240}somente.{0,120}identidades lexicais adicionais', s, re.I|re.S); assert 'subdecks reais para Core, `Important Forms`' not in s; assert 'Core/form quota' not in s; assert '{language}::Important Forms' not in s; print('routing/expansion/phase assertions OK')"</automated>
    <automated>python -c "from pathlib import Path; s=Path('docs/multilingual-lexical-adaptive-plan-v4.md').read_text(encoding='utf-8'); required=('core_identity_count = 3000','frequency_card_count = 3000 + N_important_form_cards + O_enabled_optional_role_cards','N_important_form_cards > 0 => frequency_card_count > 3000','frequency_level_card_count = 1000 + N_level_important_form_cards + O_level_enabled_optional_role_cards','D-05','D-07','D-08','D-12','LOAD-01','DEPEND-01','be','is','was','were'); missing=[x for x in required if x not in s]; assert not missing, missing; assert s.endswith('\n'); assert all(line.rstrip()==line for line in s.splitlines()); print('formula/traceability/whitespace assertions OK')"</automated>
    <automated>test -z "$(git status --porcelain=v1 -- .planning/SPEC.md .planning/ROADMAP.md .planning/STATE.md)" &amp;&amp; git diff --exit-code -- .planning/SPEC.md .planning/ROADMAP.md .planning/STATE.md</automated>
    <automated>git diff --check -- "docs/multilingual-lexical-adaptive-plan-v4.md" &amp;&amp; git diff --cached --exit-code</automated>
    <automated>git status --short -- .planning/quick/029-restyle-anki-card-templates .planning/quick/030-unify-dark-card-layouts .planning/quick/032-adaptar-template-normal-gemini src/multilang/templates tests</automated>
  </verify>
  <done>Every affected phase, report, topology rule, gate, decision, and traceability row agrees with the identity/card formulas and inherited form destination; exhaustive references are reviewed; protected planning is clean; the unrelated-worktree status matches the recorded baseline; and the task-owned Markdown passes whitespace checks without staging or committing.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Preserved v4 proposal -> future active planning/implementation | Ambiguous normative wording could be promoted into incorrect inventory, routing, workload, or export behavior. |
| Quick-task edit -> concurrent dirty worktree | A broad cleanup or restore could overwrite unrelated template/test/quick-task work or active planning state. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-Q033-01 | Tampering | Core/form/Expansion contract | mitigate | Require explicit total/per-level formulas, exhaustive occurrence inspection, forbidden-phrase assertions, and traceability updates before completion. |
| T-Q033-02 | Tampering / Repudiation | Protected active planning and dirty worktree | mitigate | Limit edits to one document with `apply_patch`, capture before/after status, assert active planning has no status/diff, check only task-owned whitespace, and prohibit staging/commit/restore. |
</threat_model>

## Dependency Analysis

- `033-01` needs only the existing preserved master plan and locked clarification; it creates the corrected normative vocabulary, formulas, topology, and flow.
- `033-02` depends on `033-01` because phases/gates/traceability must refer to those exact contracts; both tasks intentionally share the single task-owned file and execute serially.
- No output is consumed by active v3 work because the artifact remains explicitly inactive.

## Source Coverage Audit

| Source | Item | Coverage |
|---|---|---|
| GOAL | Core is 3000 identities, not a 3000-card ceiling | D-01/D-03; Tasks 033-01 and 033-02 |
| GOAL | Every justified Core form exports same-level after its lemma and raises card total | D-02; Task 033-01 contracts/example/flow; Task 033-02 phases/export/gates |
| REQ | Quick mode has no active ROADMAP requirement IDs | `requirements: []`; protected active planning checks |
| RESEARCH | No research is authorized or needed | Discovery level 0; existing document only |
| CONTEXT | Important Forms are not Expansion and have no standalone top-level subdeck | D-04; both tasks and anti-regression assertions |
| CONTEXT | Expansion is separate, opt-in, additional identities only; forms inherit parent destination | D-05; contracts, flow, phases, workload, and traceability |
| CONTEXT | Align examples, phases 35-51, topology, reporting, gates, decisions, and traceability | D-06; Task 033-02 exhaustive pass |
| CONTEXT | Keep v4 inactive and preserve active/dirty work | D-07; hard boundaries and protected-scope verification |

No source item is deferred or unplanned. Existing valid `>3000` candidate-pool, 3000-identity, language, Latin, provider, privacy, licensing, and migration decisions remain in scope only for consistency and must not be silently changed.

<verification>
Run every task-level command. The two `rg` occurrence listings are review gates, not decorative output: inspect every match in context and leave no statement that can be read as a 3000-card cap, a form-to-Expansion route, an optional Core form, or an `Important Forms` top-level subdeck. Compare the final unrelated-path status output with the baseline captured before Task 033-01. Do not run broad tests, create UI proof, modify LOG, stage, or commit.
</verification>

<success_criteria>
- `Core 3x1000` remains exactly 3000 lexical identities/3000 default headword cards, while the normative formulas require a variable frequency-card total greater than 3000 whenever `N > 0`.
- Every justified Core Important Form is in its lemma's exact frequency level/subdeck and follows the lemma through prerequisite sequencing.
- Important Forms never become Optional Expansion identities, never consume identity slots, and never use a standalone top-level forms subdeck.
- Optional Expansion remains opt-in and identity-only; all form cards inherit their parent inventory destination while retaining a distinct form role/GUID/analysis.
- The be/is/was/were example, contracts, flow, all affected Phase 35-51 language, export topology, reports, gates, decisions, and traceability are mutually consistent.
- Exhaustive reference scans and anti-regression assertions pass; `git diff --check` passes for the sole task-owned document.
- `.planning/SPEC.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, implementation/tests/templates, Quick Tasks 029/030/032, LOG, staged state, and unrelated dirty work remain untouched.
- No UI proof is created or claimed.
</success_criteria>
