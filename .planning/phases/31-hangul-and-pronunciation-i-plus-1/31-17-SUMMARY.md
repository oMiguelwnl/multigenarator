---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "17"
runtime: opencode
assurance: self_checked
---

# Phase 31: Hangul and Pronunciation i+1 - Plan 17 Summary

**Completed**: 2026-08-24
**Tasks**: 2
**Git Actions**: None.
**Deviations**: Used the fixed positional CLI and validator-owned `pronunciation-p5-p9.json` path instead of the stale flagged commands and `-draft` filename in the plan text.
**Decisions Made**: None; the output remains `draft_only`, `needs_review`, and nonauthoritative.
**Notes for Verification**: P5-P9 assisted curation is bounded draft learner copy only, not qualified Korean phonetics review, Portuguese approval, rights evidence, media approval, playback evidence, production readiness, or Anki acceptance.
**Notes for Next Work**: Proceed to Plan 31-18 for bounded P10-P13 pronunciation curation using the same fixed positional CLI and validator-owned draft path.

## Artifacts

| Artifact | Hash | Size | Counts |
|---|---|---:|---|
| `curation-drafts/inputs/pronunciation-p5-p9.json` | `a1f9a1fa327127c25aebc11cd4b82c1e57d9a114efe6ac94396b18d698d58537` | 33,460 bytes | 13 records; stages P5=3, P6=2, P7=2, P8=3, P9=3 |
| `curation-drafts/pronunciation-p5-p9.json` | `b7b42cd50630abdbb0ffbeb2c26eff897ff2f40e8f1ef8ca15d209edba4332e2` | 31,810 bytes | 13 records; 104 proposals; 13 uncertainties; 0 disagreements |

## Task Results

### 31-17-01: Build and verify compact P5-P9 input

- Created `.planning/phases/31-hangul-and-pronunciation-i-plus-1/curation-drafts/inputs/pronunciation-p5-p9.json` from the immutable pronunciation source pack.
- Exact stages are P5-P9 only, with 13 records and no unrelated stages.
- Projection size is below the 120 KiB bound.
- The fixed projection build command returned `a1f9a1fa327127c25aebc11cd4b82c1e57d9a114efe6ac94396b18d698d58537`.

### 31-17-02: Curate and independently challenge P5-P9

- Created `.planning/phases/31-hangul-and-pronunciation-i-plus-1/curation-drafts/pronunciation-p5-p9.json` as the validator-owned draft artifact.
- Preserved source-provided spellings, bracketed sounds, example words, normative pronunciations, and surface pronunciations as AI-proposed learner-copy fields.
- Proposed bounded Portuguese word and sentence translations for simple target-containing Korean examples.
- Kept IPA as an explicit `ipa_absent_pending_phonetics_review` uncertainty for every record.
- Added no approval, reviewer, rights, redistribution, media, playback, production voice, prerequisite, active-rule, target-concept, structure-hash, provider, path, URL, promotion, or authority fields.

## Challenge Pass

- Independent challenge result: PASS.
- Counts verified by challenge: 13 source records, 13 draft records, no missing/extra/duplicate item keys, 104 proposals, 13 IPA uncertainties, 0 IPA proposals.
- Stage counts verified by challenge: P5=3, P6=2, P7=2, P8=3, P9=3.
- All draft records contain exactly the allowed pronunciation learner fields by proposal or uncertainty.
- Every Korean example sentence contains the intended surface text and has no obvious English leakage or placeholders.
- Portuguese translations were treated as plausible learner-copy candidates only; no Portuguese regional policy was selected.
- No authority, approval, provider, path, media, or playback fields appear.

## Verification Results

| Check | Result |
|---|---|
| Lifecycle preflight | `node .planning/bin/gsdd.mjs lifecycle-preflight execute 31 --expects-mutation phase-status` allowed execution; planning drift was clean. |
| Control map | `node .planning/bin/gsdd.mjs control-map --json` reported clean canonical worktree, no risks, and no required intervention. |
| Projection build | `UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py project-batch pronunciation-p5-p9` returned `a1f9a1fa327127c25aebc11cd4b82c1e57d9a114efe6ac94396b18d698d58537`. |
| Draft validation | `UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py validate-batch pronunciation-p5-p9` returned `b7b42cd50630abdbb0ffbeb2c26eff897ff2f40e8f1ef8ca15d209edba4332e2`. |
| Focused curation regression | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_ai_curation.py -q` -> `25 passed in 38.69s`. |
| Independent challenge | PASS with no item-key concerns. |
| Protected canonical/evidence/export targeted status | Clean under `data/korean_foundations`, Phase 31 `evidence-inbox`, and `.multilang/exports/korean-foundations`. |

## Boundaries Preserved

- No provider, network, LLM, TTS, Azure, database, or external source call occurred.
- No Portuguese regional policy was selected.
- No files under `data/korean_foundations`, Phase 31 `evidence-inbox`, snapshots, active pointer state, candidate bundle state, or `.multilang/exports/korean-foundations` were modified.
- No approval, selection, promotion, evidence, rights, playback, media, production-readiness, or Anki acceptance claim was made.
- The P5-P9 draft is not a pronunciation family draft and cannot satisfy later family completeness, phonetics/Portuguese review, media, or export gates.

## Deviations and Recoverable Discoveries

### Stale Projection Verify Command

- The plan text still references `validate-projection --batch pronunciation-p5-p9`, but the fixed Plan 31-11 CLI has only `project-batch {batch_id}` and `validate-batch {batch_id}`.
- Recovery: generated the projection through `project-batch pronunciation-p5-p9`; projection constraints were exercised by the model during write and by focused regression tests.

### Stale Batch Validation Flag

- The plan text still references `validate-batch --batch pronunciation-p5-p9`, but the fixed CLI accepts the batch id positionally.
- Recovery: validated with `validate-batch pronunciation-p5-p9`.

### Stale Draft Filename

- The plan frontmatter still lists `pronunciation-p5-p9-draft.json`, but Plan 31-11 fixed validator-owned batch draft paths as `curation-drafts/{batch_id}.json`.
- Recovery: wrote only `curation-drafts/pronunciation-p5-p9.json`; no stale `-draft` artifact was created.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified fixed P5-P9 projection generation, exact draft validation, independent challenge scan, focused curation regression, protected canonical/evidence/export status, and planning handoff updates. No provider/network/canonical mutation occurred.
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
  summary: The plan's `validate-projection --batch` command is stale against the fixed positional CLI; projection validation was performed through the model and focused tests without widening the CLI.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded_with_fixed_contract
  summary: The plan's `validate-batch --batch` command is stale against the fixed positional CLI; draft validation used `validate-batch pronunciation-p5-p9`.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded_with_validator_owned_path
  summary: The plan's `pronunciation-p5-p9-draft.json` filename is stale against the fixed validator path `pronunciation-p5-p9.json`; only the validator-owned file was written.
</deltas>

<judgment>
<active_constraints>
Continue to preserve immutable v1 source packs, exact source-entry hash binding, compact projection boundaries, `draft_only=true`, `review_status=needs_review`, `promotion_authority=false`, fixed roots, no provider/network calls, no authority-bearing fields, no structural mutation fields in drafts, no Portuguese regional-policy selection, and no canonical evidence/export mutation.
</active_constraints>
<unresolved_uncertainty>
P5-P9 learner copy remains AI-authored draft content, not qualified Korean phonetics review, Portuguese approval, rights evidence, media approval, playback evidence, production readiness, or Anki acceptance. IPA remains an explicit uncertainty for every record because no IPA evidence exists in the projection.
</unresolved_uncertainty>
<decision_posture>
Proceed to Plan 31-18 for bounded P10-P13 pronunciation curation. Keep using validator-owned filenames and fixed positional CLI operations.
</decision_posture>
<anti_regression>
Do not force IPA without evidence; do not choose a Portuguese regional policy inside curation drafts; do not add compatibility jamo or placeholder values to learner-copy proposals; do not add approval, reviewer, rights, playback, media, production voice, prerequisite, active-rule, target, structure, path, URL, provider, force, repair, or promote fields/options.
</anti_regression>
</judgment>

## Self-Check: PASSED

- Required projection, draft, state, and summary artifacts exist.
- Required structured sections occur in the summary: `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`.
- Fixed P5-P9 validation, independent challenge, and focused curation tests pass.
- Protected canonical/evidence/export paths remain clean.
- `.planning/SPEC.md` and `.planning/ROADMAP.md` were updated for Plan 31-17 handoff; `.planning/.state-fingerprint.json` is regenerated after state update.
- No Git staging, commit, push, reset, restore, clean, stash, tag, or PR action occurred.

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 17*
*Completed: 2026-08-24*
