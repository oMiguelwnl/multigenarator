---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "12"
subsystem: korean-foundation-h0-h3-assisted-curation
runtime: opencode
assurance: self_checked
tags: [korean, hangul, assisted-curation, draft-only, fixed-root, no-provider]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "11"
    provides: Fixed projection and draft validation contracts/tooling.
provides:
  - Bounded exact H0-H3 compact projection.
  - Validated nonauthoritative H0-H3 learner-copy draft dispositions.
affects: [31-13, 31-14, 31-15, 31-19, 31-20]
key-files:
  created:
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/curation-drafts/inputs/hangul-h0-h3.json
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/curation-drafts/hangul-h0-h3.json
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-12-SUMMARY.md
  modified:
    - .planning/SPEC.md
    - .planning/ROADMAP.md
    - .planning/.state-fingerprint.json
requirements-advanced: [KHAN-01, KHAN-02]
requirements-completed: []
completed: 2026-08-24
---

# Phase 31 Plan 12: H0-H3 Assisted-Curation Summary

Plan 31-12 is complete. It produced one compact H0-H3 input projection and one validated H0-H3 draft patch set. The output remains nonauthoritative: `draft_only=true`, `review_status=needs_review`, and `promotion_authority=false`.

## Artifacts

| Artifact | Size | Content hash | Records |
|---|---:|---|---:|
| `curation-drafts/inputs/hangul-h0-h3.json` | 30,361 bytes | `804d718cf9a198b56a6aaacab4da88d46566aad54f5c167e5fa48af3445cd62a` | 25 |
| `curation-drafts/hangul-h0-h3.json` | 32,105 bytes | `a14590a950ad9cde3bef63d58e47c0dee102ebd41e309b074d2d2f8f113a87a3` | 25 |

## Draft Dispositions

| Count | Value |
|---|---:|
| Records | 25 |
| Stages | H0, H1, H2, H3 |
| AI-proposed learner fields | 68 |
| Explicit uncertainties | 7 |
| Challenge disagreements | 0 |

- The seven uncertainties are all `sound` dispositions for H0 structural concepts where a direct sound value would overclaim the concept.
- H1-H3 records have proposals for all three Hangul learner-copy fields: `reading_or_name`, `sound`, and `mnemonic`.
- All proposal values are NFC, contain no compatibility jamo, and remain bounded plain text.
- The draft contains no approval, reviewer, rights, redistribution, media hash, playback, production voice, prerequisite, active-rule, target-concept, or structure-hash mutation field.

## Challenge Pass

- H0 structural records were challenged for misleading sound claims; all seven structural `sound` fields were left as explicit uncertainties.
- H1 vowel records were kept as bounded learner approximations rather than IPA or specialist pronunciation claims.
- H2 `ieung` and block-composition records were limited to visible onset/block guidance and did not claim media or production audio readiness.
- H3 onset records used bounded context language for Korean stops and `rieul`, avoiding single absolute Portuguese-equivalent claims.
- No prerequisite, target, active-rule, source identity, media slot, or graph data was copied into the draft patch surface.

## Verification Results

| Check | Result |
|---|---|
| Lifecycle preflight | Allowed after intentional Plan 31-11 planning-state rebaseline. |
| Projection build | `UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py project-batch hangul-h0-h3` returned `804d718cf9a198b56a6aaacab4da88d46566aad54f5c167e5fa48af3445cd62a`. |
| Projection model validation | Passed: `25` records, stages `H0,H1,H2,H3`, first `ko-hangul-0001`, last `ko-hangul-0025`, size `30,361` bytes. |
| Draft validation | `UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py validate-batch hangul-h0-h3` returned `a14590a950ad9cde3bef63d58e47c0dee102ebd41e309b074d2d2f8f113a87a3`. |
| Draft identity/challenge scan | Passed: identity matches projection, 68 proposals, 7 uncertainties, 0 disagreements, no forbidden record keys, 0 compatibility-jamo values, 0 non-NFC values. |
| Focused curation regression | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_ai_curation.py -q` -> `25 passed in 38.28s`. |
| Whitespace/diff check | `git diff --check` passed. |
| Protected canonical/evidence/export targeted status | Clean under `data/korean_foundations`, Phase 31 `evidence-inbox`, and `.multilang/exports/korean-foundations`. |
| Protected canonical/evidence/export tracked tree hash | `2bfcd9b17e6826aa9a9afb4755e70360a31f4d2c399492f0523b854e37f7f931`. |

## Boundaries Preserved

- No provider, network, LLM, TTS, Azure, database, or external source call occurred.
- No files under `data/korean_foundations`, Phase 31 `evidence-inbox`, snapshots, active pointer state, candidate bundle state, or `.multilang/exports/korean-foundations` were modified.
- No approval, selection, promotion, evidence, rights, playback, or production-readiness claim was made.
- The H0-H3 draft is not a family draft and cannot satisfy later Hangul family completeness, human review, media, or export gates.

## Deviations and Recoverable Discoveries

### Stale Projection Verify Command

`31-12-PLAN.md` names `validate-projection --batch hangul-h0-h3`, but Plan 31-11 intentionally shipped a smaller fixed command surface with no `validate-projection` operation and positional batch IDs. I used `project-batch hangul-h0-h3`, model validation of `KoreanFoundationBatchProjection`, and the focused regression suite instead of widening the CLI.

### Stale Draft Filename

`31-12-PLAN.md` names `curation-drafts/hangul-h0-h3-draft.json`, but the Plan 31-11 fixed validator reads `curation-drafts/hangul-h0-h3.json`. I wrote the validator-owned path and did not create an unvalidated duplicate.

### Initial Parallel Validation Race

One projection existence check was launched in parallel with the writer and observed the file before it existed. The writer completed successfully, and the projection was then validated sequentially. No artifact changed because of the race.

## Remaining Work

- Plan 31-13 should continue with bounded H4-H7 Hangul curation using the same fixed projection/draft-validator contract.
- Plan 31-15 remains responsible for Hangul family assembly after all three Hangul batches exist.
- Plan 31-20 remains responsible for exact selection/handoff; this draft grants no selection authority.
- Qualified Korean orthography review, Portuguese review where applicable, rights, media bytes, playback, receipt, snapshot, activation, export, and observed Anki acceptance remain later gates.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified fixed H0-H3 projection generation, projection model constraints, exact draft validation, identity/challenge scan, focused curation regression, diff hygiene, and protected canonical/evidence/export invariance. No provider/network/canonical mutation occurred.
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
  summary: The plan's `hangul-h0-h3-draft.json` filename is stale against the Plan 31-11 fixed validator path `hangul-h0-h3.json`; only the validator-owned file was written.
- class: factual_discovery
  impact: recoverable
  disposition: reran_sequentially
  summary: A projection existence check raced the writer when launched in parallel; sequential validation passed afterward.
</deltas>

<judgment>
<active_constraints>
Continue to preserve immutable v1 source packs, exact source-entry hash binding, compact projection boundaries, `draft_only=true`, `review_status=needs_review`, `promotion_authority=false`, fixed roots, no provider/network calls, no authority-bearing fields, no structural mutation fields in drafts, and no canonical evidence/export mutation.
</active_constraints>
<unresolved_uncertainty>
H0-H3 learner copy remains AI-authored draft content, not qualified Korean orthography review, Portuguese approval, pronunciation approval, rights evidence, media approval, playback evidence, or Anki acceptance. Seven H0 structural sound dispositions intentionally remain explicit uncertainties.
</unresolved_uncertainty>
<decision_posture>
Proceed to Plan 31-13 for bounded H4-H7 Hangul curation. Reuse the Plan 31-11 fixed command surface and validator-owned batch filenames even where older plan text still names `validate-projection`, `--batch`, or `*-draft.json` paths.
</decision_posture>
<anti_regression>
Do not convert H0 structural sound uncertainties into asserted sounds without qualified review; do not add compatibility jamo to learner-copy proposals; do not add approval, reviewer, rights, playback, media, production voice, prerequisite, active-rule, target, structure, path, URL, provider, force, repair, or promote fields/options.
</anti_regression>
</judgment>

## Self-Check: PASSED

- Required projection, draft, state, and summary artifacts exist.
- Required structured sections occur in the summary: `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`.
- Fixed H0-H3 validation and focused curation tests pass.
- Protected canonical/evidence/export paths remain clean.
- `.planning/SPEC.md`, `.planning/ROADMAP.md`, and `.planning/.state-fingerprint.json` were updated for Plan 31-12 handoff.
- No Git staging, commit, push, reset, restore, clean, stash, tag, or PR action occurred.

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 12*
*Completed: 2026-08-24*
