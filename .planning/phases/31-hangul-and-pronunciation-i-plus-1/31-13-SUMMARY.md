---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "13"
subsystem: korean-foundation-h4-h7-assisted-curation
runtime: opencode
assurance: self_checked
tags: [korean, hangul, assisted-curation, draft-only, fixed-root, no-provider]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "12"
    provides: Validated H0-H3 draft and fixed-path curation handoff.
provides:
  - Bounded exact H4-H7 compact projection.
  - Validated nonauthoritative H4-H7 learner-copy draft dispositions.
affects: [31-14, 31-15, 31-19, 31-20]
key-files:
  created:
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/curation-drafts/inputs/hangul-h4-h7.json
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/curation-drafts/hangul-h4-h7.json
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-13-SUMMARY.md
  modified:
    - .planning/SPEC.md
    - .planning/ROADMAP.md
    - .planning/.state-fingerprint.json
requirements-advanced: [KHAN-01, KHAN-02]
requirements-completed: []
completed: 2026-08-24
---

# Phase 31 Plan 13: H4-H7 Assisted-Curation Summary

Plan 31-13 is complete. It produced one compact H4-H7 input projection and one validated H4-H7 draft patch set. The output remains nonauthoritative: `draft_only=true`, `review_status=needs_review`, and `promotion_authority=false`.

## Artifacts

| Artifact | Size | Content hash | Records |
|---|---:|---|---:|
| `curation-drafts/inputs/hangul-h4-h7.json` | 40,894 bytes | `b80e5ead702fb38df5ce46f30b8a674b0402c4a9f00b570f6fa454e5d19b5d6e` | 32 |
| `curation-drafts/hangul-h4-h7.json` | 41,268 bytes | `f641410fe46c5b218a7adfd419bd77a1f6704525b2a9ac56ed494382dfc3de33` | 32 |

## Draft Dispositions

| Count | Value |
|---|---:|
| Records | 32 |
| Stages | H4, H5, H6, H7 |
| AI-proposed learner fields | 95 |
| Explicit uncertainties | 1 |
| Challenge disagreements | 0 |

- The one uncertainty is the `sound` disposition for `ko-hangul-0050`, the H7 batchim-position structural concept.
- All other H4-H7 records have proposals for `reading_or_name`, `sound`, and `mnemonic`.
- All proposal values are NFC, contain no compatibility jamo, and remain bounded plain text.
- The draft contains no approval, reviewer, rights, redistribution, media hash, playback, production voice, prerequisite, active-rule, target-concept, or structure-hash mutation field.

## Challenge Pass

- H4 complex vowel names and sounds were kept to bounded learner approximations and flagged by wording where modern Seoul mergers or variation are relevant.
- H5 aspirated and tense consonant records use contrastive terms such as `aspirado` and `tenso` without claiming specialist phonetics approval.
- H6 compound vowels avoid structural graph changes while giving learner mnemonics for glide-like movement.
- H7 batchim-position sound remains an explicit uncertainty because the position itself is structural.
- H7 final consonant proposals are bounded to final-output learner guidance and do not claim audio, playback, or production review.

## Verification Results

| Check | Result |
|---|---|
| Lifecycle/control preflight | Allowed; planning drift remained clean after Plan 31-12 fingerprinting. Dirty-worktree warning reflects current intended Phase 31 files. |
| Projection build | `UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py project-batch hangul-h4-h7` returned `b80e5ead702fb38df5ce46f30b8a674b0402c4a9f00b570f6fa454e5d19b5d6e`. |
| Projection model validation | Passed: `32` records, stages `H4,H5,H6,H7`, first `ko-hangul-0026`, last `ko-hangul-0057`, size `40,894` bytes. |
| Draft validation | `UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py validate-batch hangul-h4-h7` returned `f641410fe46c5b218a7adfd419bd77a1f6704525b2a9ac56ed494382dfc3de33`. |
| Draft identity/challenge scan | Passed: identity matches projection, 95 proposals, 1 uncertainty, 0 disagreements, no forbidden record keys, 0 compatibility-jamo values, 0 non-NFC values. |
| Focused curation regression | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_ai_curation.py -q` -> `25 passed in 37.10s`. |
| Whitespace/diff check | `git diff --check` passed. |
| Protected canonical/evidence/export targeted status | Clean under `data/korean_foundations`, Phase 31 `evidence-inbox`, and `.multilang/exports/korean-foundations`. |
| Protected canonical/evidence/export tracked tree hash | `2bfcd9b17e6826aa9a9afb4755e70360a31f4d2c399492f0523b854e37f7f931`. |

## Boundaries Preserved

- No provider, network, LLM, TTS, Azure, database, or external source call occurred.
- No files under `data/korean_foundations`, Phase 31 `evidence-inbox`, snapshots, active pointer state, candidate bundle state, or `.multilang/exports/korean-foundations` were modified.
- No approval, selection, promotion, evidence, rights, playback, or production-readiness claim was made.
- The H4-H7 draft is not a family draft and cannot satisfy later Hangul family completeness, human review, media, or export gates.

## Deviations and Recoverable Discoveries

### Stale Projection Verify Command

`31-13-PLAN.md` names `validate-projection --batch hangul-h4-h7`, but Plan 31-11 intentionally shipped a smaller fixed command surface with no `validate-projection` operation and positional batch IDs. I used `project-batch hangul-h4-h7`, model validation of `KoreanFoundationBatchProjection`, and the focused regression suite instead of widening the CLI.

### Stale Draft Filename

`31-13-PLAN.md` names `curation-drafts/hangul-h4-h7-draft.json`, but the Plan 31-11 fixed validator reads `curation-drafts/hangul-h4-h7.json`. I wrote the validator-owned path and did not create an unvalidated duplicate.

### Initial Parallel Validation Race

One projection existence check was launched in parallel with the writer and observed the file before it existed. The writer completed successfully, and all writer-dependent checks were then rerun sequentially. Future projection validation should stay sequential after writes.

## Remaining Work

- Plan 31-14 should continue with bounded H8-H10 Hangul curation using the same fixed projection/draft-validator contract.
- Plan 31-15 remains responsible for Hangul family assembly after all three Hangul batches exist.
- Plan 31-20 remains responsible for exact selection/handoff; this draft grants no selection authority.
- Qualified Korean orthography review, Portuguese review where applicable, rights, media bytes, playback, receipt, snapshot, activation, export, and observed Anki acceptance remain later gates.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified fixed H4-H7 projection generation, projection model constraints, exact draft validation, identity/challenge scan, focused curation regression, diff hygiene, and protected canonical/evidence/export invariance. No provider/network/canonical mutation occurred.
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
  summary: The plan's `hangul-h4-h7-draft.json` filename is stale against the Plan 31-11 fixed validator path `hangul-h4-h7.json`; only the validator-owned file was written.
- class: factual_discovery
  impact: recoverable
  disposition: reran_sequentially
  summary: A projection existence check raced the writer when launched in parallel; sequential validation passed afterward and writer-dependent checks will remain sequential.
</deltas>

<judgment>
<active_constraints>
Continue to preserve immutable v1 source packs, exact source-entry hash binding, compact projection boundaries, `draft_only=true`, `review_status=needs_review`, `promotion_authority=false`, fixed roots, no provider/network calls, no authority-bearing fields, no structural mutation fields in drafts, and no canonical evidence/export mutation.
</active_constraints>
<unresolved_uncertainty>
H4-H7 learner copy remains AI-authored draft content, not qualified Korean orthography review, Portuguese approval, pronunciation approval, rights evidence, media approval, playback evidence, or Anki acceptance. The H7 batchim-position sound disposition intentionally remains an explicit uncertainty.
</unresolved_uncertainty>
<decision_posture>
Proceed to Plan 31-14 for bounded H8-H10 Hangul curation. Reuse the Plan 31-11 fixed command surface and validator-owned batch filenames even where older plan text still names `validate-projection`, `--batch`, or `*-draft.json` paths.
</decision_posture>
<anti_regression>
Do not convert H7 batchim-position structural sound uncertainty into an asserted sound without qualified review; do not add compatibility jamo to learner-copy proposals; do not add approval, reviewer, rights, playback, media, production voice, prerequisite, active-rule, target, structure, path, URL, provider, force, repair, or promote fields/options.
</anti_regression>
</judgment>

## Self-Check: PASSED

- Required projection, draft, state, and summary artifacts exist.
- Required structured sections occur in the summary: `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`.
- Fixed H4-H7 validation and focused curation tests pass.
- Protected canonical/evidence/export paths remain clean.
- `.planning/SPEC.md`, `.planning/ROADMAP.md`, and `.planning/.state-fingerprint.json` were updated for Plan 31-13 handoff.
- No Git staging, commit, push, reset, restore, clean, stash, tag, or PR action occurred.

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 13*
*Completed: 2026-08-24*
