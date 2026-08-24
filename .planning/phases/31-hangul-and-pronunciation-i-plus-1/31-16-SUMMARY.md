---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "16"
subsystem: korean-foundation-p0-p4-assisted-curation
runtime: opencode
assurance: self_checked
tags: [korean, pronunciation, assisted-curation, draft-only, fixed-root, no-provider]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "15"
    provides: Complete nonauthoritative Hangul family draft.
provides:
  - Bounded exact P0-P4 compact projection.
  - Validated nonauthoritative P0-P4 pronunciation learner-copy draft dispositions.
affects: [31-17, 31-18, 31-19, 31-20]
key-files:
  created:
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/curation-drafts/inputs/pronunciation-p0-p4.json
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/curation-drafts/pronunciation-p0-p4.json
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-16-SUMMARY.md
  modified:
    - .planning/SPEC.md
    - .planning/ROADMAP.md
    - .planning/.state-fingerprint.json
requirements-advanced: [KPRO-01, KPRO-02]
requirements-completed: []
completed: 2026-08-24
---

# Phase 31 Plan 16: P0-P4 Assisted-Curation Summary

Plan 31-16 is complete. It produced one compact P0-P4 input projection and one validated P0-P4 draft patch set. The output remains nonauthoritative: `draft_only=true`, `review_status=needs_review`, and `promotion_authority=false`.

## Artifacts

| Artifact | Size | Content hash | Records |
|---|---:|---|---:|
| `curation-drafts/inputs/pronunciation-p0-p4.json` | 45,480 bytes | `8167c12d3dcb652977ca4fc2575b7c94ef626c3d12560a1bc18baf7f1b3b45ad` | 24 |
| `curation-drafts/pronunciation-p0-p4.json` | 57,971 bytes | `29781e441080af0b8c2504adae8f65982ab014864ad52490992a2a2f92af9c0c` | 24 |

## Draft Dispositions

| Count | Value |
|---|---:|
| Records | 24 |
| Stages | P0, P1, P2, P3, P4 |
| AI-proposed learner fields | 176 |
| Explicit uncertainties | 40 |
| Challenge disagreements | 0 |

- All 24 `ipa` fields remain explicit `ipa_absent_pending_phonetics_review` uncertainties.
- Eight P2 records keep `example_sentence` and `sentence_translation` as explicit `sentence_would_introduce_connected_speech` uncertainties because a simple sentence would trigger later connected-speech rules.
- P0/P1/P3/P4 received bounded Korean examples and Portuguese learner text without choosing a Portuguese regional policy.
- All proposal values are NFC, contain no compatibility jamo, contain no placeholder values, and remain bounded plain text.
- The draft contains no approval, reviewer, rights, redistribution, media hash, playback, production voice, prerequisite, active-rule, target-concept, or structure-hash mutation field.

## Challenge Pass

- Source-provided Korean spellings, bracketed sounds, example words, normative pronunciation, and surface pronunciation were preserved as proposals where already present in the compact projection.
- Portuguese word translations were proposed as learner-copy candidates only, not reviewed translation evidence.
- P2 sentence fields remain uncertain to avoid introducing liaison, nasalization, tensification, or other later rules while trying to force complete examples.
- IPA remains uncertain for every record because no IPA evidence exists in the projection and specialist phonetics review is still a later gate.
- No rule, prerequisite, target, active-rule, source identity, media slot, or graph data was copied into the draft patch surface.

## Verification Results

| Check | Result |
|---|---|
| Lifecycle/control preflight | Allowed; planning drift remained clean after Plan 31-15 fingerprinting. Dirty-worktree warning reflects current intended Phase 31 files. |
| Projection build | `UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py project-batch pronunciation-p0-p4` returned `8167c12d3dcb652977ca4fc2575b7c94ef626c3d12560a1bc18baf7f1b3b45ad`. |
| Projection model validation | Passed: `24` records, stages `P0,P1,P2,P3,P4`, first `ko-pron-0001`, last `ko-pron-0024`, size `45,480` bytes. |
| Draft validation | `UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py validate-batch pronunciation-p0-p4` returned `29781e441080af0b8c2504adae8f65982ab014864ad52490992a2a2f92af9c0c`. |
| Draft identity/challenge scan | Passed: identity matches projection, 176 proposals, 40 uncertainties, 0 disagreements, no forbidden record keys, 0 compatibility-jamo values, 0 non-NFC values, and 0 placeholder values. |
| Focused curation regression | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_ai_curation.py -q` -> `25 passed in 41.71s`. |
| Whitespace/diff check | `git diff --check` passed. |
| Protected canonical/evidence/export targeted status | Clean under `data/korean_foundations`, Phase 31 `evidence-inbox`, and `.multilang/exports/korean-foundations`. |
| Protected canonical/evidence/export tracked tree hash | `2bfcd9b17e6826aa9a9afb4755e70360a31f4d2c399492f0523b854e37f7f931`. |

## Boundaries Preserved

- No provider, network, LLM, TTS, Azure, database, or external source call occurred.
- No Portuguese regional policy was selected.
- No files under `data/korean_foundations`, Phase 31 `evidence-inbox`, snapshots, active pointer state, candidate bundle state, or `.multilang/exports/korean-foundations` were modified.
- No approval, selection, promotion, evidence, rights, playback, or production-readiness claim was made.
- The P0-P4 draft is not a pronunciation family draft and cannot satisfy later family completeness, phonetics/Portuguese review, media, or export gates.

## Deviations and Recoverable Discoveries

### Stale Projection Verify Command

`31-16-PLAN.md` names `validate-projection --batch pronunciation-p0-p4`, but Plan 31-11 intentionally shipped a smaller fixed command surface with no `validate-projection` operation and positional batch IDs. I used `project-batch pronunciation-p0-p4`, model validation of `KoreanFoundationBatchProjection`, and the focused regression suite instead of widening the CLI.

### Stale Draft Filename

`31-16-PLAN.md` names `curation-drafts/pronunciation-p0-p4-draft.json`, but the Plan 31-11 fixed validator reads `curation-drafts/pronunciation-p0-p4.json`. I wrote the validator-owned path and did not create an unvalidated duplicate.

## Remaining Work

- Plan 31-17 should continue with bounded P5-P9 pronunciation curation using the same fixed projection/draft-validator contract.
- Plan 31-19 remains responsible for pronunciation family assembly and final two-family manifest assembly.
- Plan 31-20 remains responsible for exact selection/handoff; this draft grants no selection authority.
- Qualified Korean phonetics review, Portuguese review, rights, media bytes, playback, receipt, snapshot, activation, export, and observed Anki acceptance remain later gates.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified fixed P0-P4 projection generation, projection model constraints, exact draft validation, pronunciation challenge scan, focused curation regression, diff hygiene, and protected canonical/evidence/export invariance. No provider/network/canonical mutation occurred.
</executor_check>
</checks>

<handoff>
plan_runtime: opencode
plan_assurance: self_checked
plan_check_status: passed
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: false
</handoff>

<deltas>
- class: factual_discovery
  impact: recoverable
  disposition: proceeded_with_fixed_contract
  summary: The plan's `validate-projection --batch` command is stale against the Plan 31-11 fixed positional CLI; projection validation was performed through the model and focused tests without widening the CLI.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded_with_validator_owned_path
  summary: The plan's `pronunciation-p0-p4-draft.json` filename is stale against the Plan 31-11 fixed validator path `pronunciation-p0-p4.json`; only the validator-owned file was written.
</deltas>

<judgment>
<active_constraints>
Continue to preserve immutable v1 source packs, exact source-entry hash binding, compact projection boundaries, `draft_only=true`, `review_status=needs_review`, `promotion_authority=false`, fixed roots, no provider/network calls, no authority-bearing fields, no structural mutation fields in drafts, no Portuguese regional-policy selection, and no canonical evidence/export mutation.
</active_constraints>
<unresolved_uncertainty>
P0-P4 learner copy remains AI-authored draft content, not qualified Korean phonetics review, Portuguese approval, rights evidence, media approval, playback evidence, production readiness, or Anki acceptance. IPA and P2 sentence fields intentionally remain explicit uncertainties.
</unresolved_uncertainty>
<decision_posture>
Proceed to Plan 31-17 for bounded P5-P9 pronunciation curation. Keep using validator-owned filenames and fixed positional CLI operations.
</decision_posture>
<anti_regression>
Do not force IPA or P2 sentence examples without evidence; do not choose a Portuguese regional policy inside curation drafts; do not add compatibility jamo or placeholder values to learner-copy proposals; do not add approval, reviewer, rights, playback, media, production voice, prerequisite, active-rule, target, structure, path, URL, provider, force, repair, or promote fields/options.
</anti_regression>
</judgment>

## Self-Check: PASSED

- Required projection, draft, state, and summary artifacts exist.
- Required structured sections occur in the summary: `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`.
- Fixed P0-P4 validation and focused curation tests pass.
- Protected canonical/evidence/export paths remain clean.
- `.planning/SPEC.md`, `.planning/ROADMAP.md`, and `.planning/.state-fingerprint.json` were updated for Plan 31-16 handoff.
- No Git staging, commit, push, reset, restore, clean, stash, tag, or PR action occurred.

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 16*
*Completed: 2026-08-24*
