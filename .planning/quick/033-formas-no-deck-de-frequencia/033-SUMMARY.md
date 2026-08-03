---
quick_task: 033-formas-no-deck-de-frequencia
plan: "033"
runtime: opencode
assurance: self_checked
status: complete_with_concurrent_worktree_caveat
completed: 2026-07-27
task_count: 2
git_actions: none
files_changed:
  - docs/multilingual-lexical-adaptive-plan-v4.md
  - .planning/quick/033-formas-no-deck-de-frequencia/033-SUMMARY.md
---

# Quick Task 033 Summary: Formas no deck de frequência

The preserved inactive v4 plan now fixes Core at 3000 lexical identities and 3000 default headword cards while requiring every approved Core Important Form to add a card in its lemma's real frequency level, producing an intentionally variable larger card count.

## Completion Status

**Complete with a concurrent-worktree caveat.** Both planned tasks and all normative target checks passed. Task 033 did not stage, commit, restore, clean, or intentionally edit any unrelated path. During execution, a separate Quick 032 verification workflow appended to `.planning/quick/LOG.md` and created `032-VERIFICATION.md`; a Quick 034 planner then created its own plan. The fingerprint evidence records those concurrent changes rather than hiding or reversing them.

## Files Changed by Quick Task 033

| File | Action | Purpose |
|---|---|---|
| `docs/multilingual-lexical-adaptive-plan-v4.md` | Modified with `apply_patch` only | Normative formulas, required form routing, phase propagation, export topology, reporting, gates, and traceability |
| `.planning/quick/033-formas-no-deck-de-frequencia/033-SUMMARY.md` | Created | Execution evidence and handoff |

The pre-existing untracked `033-PLAN.md` was read as input and not modified. No source, template, test, active-planning, prior quick-task, or LOG file was edited by Task 033.

## Work Completed

### Task 1 — Normative identity, form, formula, and routing contracts

- Defined Core as exactly 3000 lexical identities, 1000 per real level, with exactly 3000 default headword-recognition cards rather than a 3000-card ceiling.
- Made every justified/approved Important Form of a Core identity a mandatory additional card, outside identity quotas but inside card/workload totals.
- Required Core forms to retain the lemma's exact real Level 1/2/3 subdeck and deck ID, become eligible after the lemma, and retain sibling burying.
- Defined Important Form as a descendant card role rather than a source inventory; it cannot route a Core form to Expansion, Grammar, or a standalone forms deck.
- Kept Optional Expansion opt-in and identity-only. Forms of Expansion, Custom, Highlight, Grammar/foundation, or another approved inventory inherit the parent destination without consuming an identity slot.
- Updated `CARD-01`, `FORM-01`–`FORM-03`, `ROUTE-01`, `LOAD-01`, and `DEPEND-01` while preserving `SENSE-01`, `MWE-01`, `DEF-01`, `AUDIO-01`, and `GUID-01` verbatim.
- Reworked `be/is/was/were`: each approved analysis-specific form shares `be`'s resolved frequency deck ID, follows `be`, and counts separately in `N`; indicative and irrealis `were` retain distinct analyses and GUIDs.
- Propagated parent inventory, level, destination, sequencing, formulas, and recovery behavior through the end-to-end flow.

### Task 2 — Phases, export topology, reports, gates, and traceability

- Propagated the locked semantics through G0 and every Phase 35–51 section without changing headings or dependencies.
- Phase 35 freezes the identity/card distinction and formulas; Phase 36 persists parent inventory/level/destination without form membership; Phases 37–44 keep candidate/Core/Expansion counts identity-based while testing mandatory inherited form routes and variable workload.
- Phase 45 freezes 66,000 Core identities and 66,000 default Core headwords while freezing form packs as parent-linked datasets whose cards increase exports.
- Phase 46 exports real frequency Level 1/2/3 subdecks, tests identical lemma/form deck IDs and lemma-first order, and expressly excludes a top-level Important Forms destination.
- Phases 47–49 preserve form-role/history mapping, source destination, adaptive prerequisites, distinct analysis/GUID/content/audio, and real workload.
- Phases 50–51 preview, preflight, apply, and postflight identity/headword/form/optional-role counts, formulas, per-level reconciliation, topology, and sequencing.
- Expanded privacy, license, cost, and quality gates plus D-05, D-07, D-08, D-12, capability ownership, gate-by-phase evidence, and migration invariants.

## Locked Formulas

```text
core_identity_count = 3000
frequency_card_count = 3000 + N_important_form_cards + O_enabled_optional_role_cards
N_important_form_cards > 0 => frequency_card_count > 3000
frequency_level_card_count = 1000 + N_level_important_form_cards + O_level_enabled_optional_role_cards
```

- The fixed 3000 term is the 3000 default Core headword cards.
- `N` includes every exported approved Core Important Form card, including separate cards for distinct analyses of the same spelling.
- `O` includes only optional roles explicitly enabled for that frequency inventory and is zero by default.
- Level 1/2/3 components must sum to the total formula.
- Expansion identities, headwords, forms, optional roles, and total are reported separately.

## Export Topology Semantics

- Real Core destinations are `{language}::Frequency::Level 1`, `{language}::Frequency::Level 2`, and `{language}::Frequency::Level 3`.
- Parent rank resolves the real frequency destination before card role is applied.
- A Core Important Form preserves the lemma's exact deck ID and follows the lemma.
- No top-level `Important Forms` subdeck or `{language}::Important Forms` route exists.
- Expansion remains an opt-in inventory of additional identities only; a descendant form stays with its Expansion parent without becoming an Expansion identity.
- Custom, Highlight, Grammar/foundation, and other descendants likewise inherit their parent destination. Grammar is not a sink for Core forms.

## Validation Results

| Validation | Result |
|---|---|
| Required formula and topology literals | PASS |
| Forbidden legacy phrases/routes (`Core/form quota`, standalone forms path, ambiguous no-count wording) | PASS |
| Routing/Expansion regex assertions from the plan | PASS |
| All Phase 35–51 headings present | PASS |
| Phase-by-phase semantic assertions for Phases 35–51 | PASS |
| Inactive banner preserved exactly | PASS |
| Phase headings and dependency lines preserved exactly against `HEAD` | PASS |
| All 23 language matrix rows preserved exactly against `HEAD` | PASS |
| All 15 fixed decision IDs retained | PASS |
| `SENSE-01`, `MWE-01`, `DEF-01`, `AUDIO-01`, `GUID-01` rows unchanged | PASS |
| Final exhaustive occurrence review | PASS — 109 matching lines inspected |
| Target newline/trailing-whitespace assertions | PASS |
| `git diff --check -- docs/multilingual-lexical-adaptive-plan-v4.md` | PASS (Git emitted only the existing LF/CRLF configuration warning) |
| `.planning/SPEC.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` status/diff | PASS — untouched |
| Git staged diff | PASS — empty |
| Broad tests | Not run by design; documentation-only plan forbids them |

`rg` was unavailable (`command not found`), so the exhaustive scan used a deterministic Python regex over every UTF-8 line. The first fallback attempt exposed the Windows `cp1252` console limitation on Romanian `ș`; rerunning with `PYTHONIOENCODING=utf-8` completed all 109 matches. The plan's Python assertions were also rerun with shell-safe quoting because Markdown backticks in the verbatim Bash command trigger command substitution.

## Dirty-Worktree Fingerprint Evidence

Baseline artifacts were written outside the repository at:

`C:\Users\MIGUEL~1.RAF\AppData\Local\Temp\opencode\quick-033-baseline-20260727T192800Z\`

- Baseline manifest: `manifest.json`
- Baseline time: `2026-07-27T19:28:00Z`
- Pre-existing non-task dirty paths fingerprinted: 31
- Baseline index listing SHA-256: `4e0cc548cb304afbb62d049d3d3b141e941cd8f3931e0127859c20f96de2d961`
- Baseline cached diff SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty staged diff)
- Final comparison: `comparison-final.json`, captured at `2026-07-27T19:47:09Z`.
- Final result for baseline paths: 30/31 content fingerprints unchanged; the sole mismatch is the documented concurrent Quick 032 LOG append.
- Final index result: unchanged (`ls-files --stage` and empty cached-diff hashes both match baseline).
- New non-task dirty paths after baseline: Quick 032 `032-VERIFICATION.md` and Quick 034 `034-PLAN.md`; neither was written or modified by Task 033.

### Concurrent worktree caveat

The final comparison found 30 of 31 pre-existing dirty path contents unchanged and the Git index unchanged. `.planning/quick/LOG.md` changed from SHA-256 `6a740489d079f847510128fff8dfd289b84ddac4464434620ae512699cf7d118` to `9bb91bf423ad5c7668cd9b356ac86c27388020d8f04148d9aa89931a6df8f4ca`, while a new `.planning/quick/032-adaptar-template-normal-gemini/032-VERIFICATION.md` appeared with SHA-256 `d3d8c282b2bf9c80ce6bf219da106ca6fb38083ba23916ac0fc566f71d8c791f`. Their modification times and the newly appended Quick 032 LOG row place those writes after the Task 033 baseline and identify them as concurrent Quick 032 workflow output. After the Task 033 summary was persisted, `.planning/quick/034-preview-card-normal-gemini/034-PLAN.md` also appeared with SHA-256 `25424c279ca7de28c5463cb7dd1f248bb7a06ec56134ead8a5a617397f3ce484`, confirming that unrelated quick workflows remained active. Task 033 did not restore, absorb, stage, or alter that work.

## Deviations from Plan

- **Tooling fallback:** `rg` was unavailable; deterministic UTF-8 Python scans provided equivalent coverage without weakening the occurrence review.
- **Concurrent external mutation:** Quick 032 updated its own verification/LOG surfaces and Quick 034 created its plan after the baseline. These were recorded, not modified or reverted.
- No semantic scope deviations were made.

## Git Actions

None. Per task constraints, no files were staged or committed.

## Self-Check: PASSED WITH DOCUMENTED CONCURRENT CAVEAT

- Normative target exists and has SHA-256 `619d545ea14d03471890da8a40c55563901d7872de4383416d6a32a05e0beaae` (893 lines before this summary-only update).
- This summary exists at the required path.
- Task-owned Markdown passes newline and trailing-whitespace checks.
- Active planning remains untouched and the Git index remains unchanged/unstaged.
- All 30 non-concurrently-mutated baseline paths match their content fingerprints. The only baseline mismatch and both new unrelated paths are identified above; none was reverted or claimed as Task 033 output.
