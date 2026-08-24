---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "15"
subsystem: korean-foundation-hangul-family-draft-assembly
runtime: opencode
assurance: self_checked
tags: [korean, hangul, assisted-curation, family-assembly, draft-only, no-provider]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "12"
    provides: Validated H0-H3 draft.
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "13"
    provides: Validated H4-H7 draft.
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "14"
    provides: Validated H8-H10 draft.
provides:
  - Complete deterministic nonauthoritative Hangul family draft.
affects: [31-19, 31-20, 31-21]
key-files:
  created:
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/curation-drafts/hangul-v2-draft.json
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-15-SUMMARY.md
  modified:
    - .planning/SPEC.md
    - .planning/ROADMAP.md
    - .planning/.state-fingerprint.json
requirements-advanced: [KHAN-01, KHAN-02]
requirements-completed: []
completed: 2026-08-24
---

# Phase 31 Plan 15: Hangul Family Draft Assembly Summary

Plan 31-15 is complete. It assembled the three validated Hangul stage drafts into one deterministic family proposal. The output remains nonauthoritative: `draft_only=true`, `review_status=needs_review`, and `promotion_authority=false`.

## Artifacts

| Artifact | Size | Content hash | Records |
|---|---:|---|---:|
| `curation-drafts/hangul-v2-draft.json` | 78,933 bytes | `71e1d3c402acf964247c9551cc63f27dff6c18ad3d5bddc1322cf48cd80e254f` | 92 |

## Batch Bindings

| Batch | Content hash | Records | Proposals | Uncertainties |
|---|---|---:|---:|---:|
| `hangul-h0-h3` | `a14590a950ad9cde3bef63d58e47c0dee102ebd41e309b074d2d2f8f113a87a3` | 25 | 68 | 7 |
| `hangul-h4-h7` | `f641410fe46c5b218a7adfd419bd77a1f6704525b2a9ac56ed494382dfc3de33` | 32 | 95 | 1 |
| `hangul-h8-h10` | `ac2039edbe79ced986f1ec2bbe6abab8eae2393a83ccdbb1e0da407228e59376` | 35 | 86 | 19 |

## Family Coverage

| Count | Value |
|---|---:|
| Records | 92 |
| Stages | H0 through H10 |
| AI-proposed learner fields | 249 |
| Explicit uncertainties | 27 |
| Challenge disagreements | 0 |

- Source order is preserved from `ko-hangul-0001` through `ko-hangul-0092`.
- All three batch hashes are bound in the family draft with exact record/proposal/uncertainty counts.
- All proposal values remain NFC, contain no compatibility jamo, and remain bounded plain text.
- The family draft contains no approval, reviewer, rights, redistribution, media hash, playback, production voice, prerequisite, active-rule, target-concept, or structure-hash mutation field.

## Verification Results

| Check | Result |
|---|---|
| Lifecycle/control preflight | Allowed; planning drift remained clean after Plan 31-14 fingerprinting. Dirty-worktree warning reflects current intended Phase 31 files. |
| Batch validation | `validate-batch hangul-h0-h3`, `validate-batch hangul-h4-h7`, and `validate-batch hangul-h8-h10` returned the three exact batch hashes listed above. |
| Family assembly | `UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py assemble-family hangul` returned `71e1d3c402acf964247c9551cc63f27dff6c18ad3d5bddc1322cf48cd80e254f`. |
| Read-only family audit | `KoreanFoundationFamilyDraft.model_validate_json(...)` passed with 92 records, 249 proposals, 27 uncertainties, 0 disagreements, H0-H10 stages, first `ko-hangul-0001`, last `ko-hangul-0092`, 0 compatibility-jamo values, and 0 non-NFC values. |
| Focused curation regression | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_ai_curation.py -q` -> `25 passed in 41.04s`. |
| Whitespace/diff check | `git diff --check` passed. |
| Protected canonical/evidence/export targeted status | Clean under `data/korean_foundations`, Phase 31 `evidence-inbox`, and `.multilang/exports/korean-foundations`. |
| Protected canonical/evidence/export tracked tree hash | `2bfcd9b17e6826aa9a9afb4755e70360a31f4d2c399492f0523b854e37f7f931`. |

## Boundaries Preserved

- No stage recuration occurred during assembly.
- No provider, network, LLM, TTS, Azure, database, or external source call occurred.
- No files under `data/korean_foundations`, Phase 31 `evidence-inbox`, snapshots, active pointer state, candidate bundle state, or `.multilang/exports/korean-foundations` were modified.
- No approval, selection, promotion, evidence, rights, playback, or production-readiness claim was made.
- The Hangul family draft is one deterministic selection unit for later plans, not an approved learner-ready source pack.

## Deviations and Recoverable Discoveries

### Stale CLI Flags

`31-15-PLAN.md` names `validate-batch --batch ...` and `assemble-family --family hangul`, but Plan 31-11 shipped positional batch/family arguments. I used the fixed positional commands and did not widen the CLI.

### Family-Scoped Validate-Drafts Is Not Available

`31-15-PLAN.md` names `validate-drafts --family hangul`, but Plan 31-11 shipped only full `validate-drafts`, which requires all six batches and both family drafts. I performed the Plan 31-15 audit through read-only `KoreanFoundationFamilyDraft` model validation instead of adding a family-scoped command.

## Remaining Work

- Plan 31-16 should begin bounded pronunciation P0-P4 curation using the fixed projection/draft-validator contract.
- Plan 31-19 remains responsible for pronunciation family assembly and final two-family manifest assembly.
- Plan 31-20 remains responsible for exact selection/handoff; this family draft grants no selection authority.
- Qualified Korean orthography review, Portuguese review where applicable, rights, media bytes, playback, receipt, snapshot, activation, export, and observed Anki acceptance remain later gates.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified three batch validations, fixed Hangul family assembly, read-only family model audit, focused curation regression, diff hygiene, and protected canonical/evidence/export invariance. No provider/network/canonical mutation occurred.
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
  summary: The plan's `--batch` and `--family` command syntax is stale against the Plan 31-11 fixed positional CLI; assembly and validation used positional arguments without widening the CLI.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded_with_read_only_model_validation
  summary: The plan's `validate-drafts --family hangul` command is unavailable because the fixed CLI only has full-manifest `validate-drafts`; read-only family model validation supplied the Hangul-only audit.
</deltas>

<judgment>
<active_constraints>
Continue to preserve immutable v1 source packs, exact source-entry hash binding, compact projection boundaries, `draft_only=true`, `review_status=needs_review`, `promotion_authority=false`, fixed roots, no provider/network calls, no authority-bearing fields, no structural mutation fields in drafts, and no canonical evidence/export mutation.
</active_constraints>
<unresolved_uncertainty>
The assembled Hangul draft remains AI-authored draft content, not qualified Korean orthography review, Portuguese approval, pronunciation approval, rights evidence, media approval, playback evidence, production readiness, or Anki acceptance. All 27 uncertainties intentionally remain unresolved for later review/selection.
</unresolved_uncertainty>
<decision_posture>
Proceed to Plan 31-16 for bounded pronunciation P0-P4 curation. Do not promote, approve, or publish Hangul content from `hangul-v2-draft.json`; it is a nonauthoritative exact-hash selection candidate only.
</decision_posture>
<anti_regression>
Do not recurate assembled Hangul records during family or manifest assembly; do not drop, duplicate, reorder, or rewrite batch records; do not convert uncertainties into asserted proposals without qualified review; do not add approval, reviewer, rights, playback, media, production voice, prerequisite, active-rule, target, structure, path, URL, provider, force, repair, or promote fields/options.
</anti_regression>
</judgment>

## Self-Check: PASSED

- Required family draft, state, and summary artifacts exist.
- Required structured sections occur in the summary: `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`.
- Fixed Hangul batch validation, family read-only validation, and focused curation tests pass.
- Protected canonical/evidence/export paths remain clean.
- `.planning/SPEC.md`, `.planning/ROADMAP.md`, and `.planning/.state-fingerprint.json` were updated for Plan 31-15 handoff.
- No Git staging, commit, push, reset, restore, clean, stash, tag, or PR action occurred.

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 15*
*Completed: 2026-08-24*
