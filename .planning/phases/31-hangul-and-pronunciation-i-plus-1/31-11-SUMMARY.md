---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "11"
subsystem: korean-foundation-assisted-curation-contracts
runtime: opencode
assurance: self_checked
tags: [korean, assisted-curation, pydantic-v2, fixed-root, draft-only, no-provider]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "10"
    provides: Pathless Korean foundations CLI integration and canonical-state invariance gate.
provides:
  - Frozen hash-bound nonauthoritative draft contracts for Korean foundation assisted curation.
  - Fixed local script surface for compact projections, batch validation, family assembly, manifest assembly, and read-only full validation.
  - Focused TDD regression coverage for source hashes, authority rejection, field allowlists, NFC safety, exact 92/47/139 coverage, fixed roots, and read-only validation.
affects: [31-12, 31-13, 31-14, 31-15, 31-16, 31-17, 31-18, 31-19, 31-20]
tech-stack:
  added: []
  patterns:
    - Pydantic v2 frozen `extra="forbid"` models with deterministic canonical JSON SHA-256 content hashes.
    - Fixed-root atomic JSON writers and read-only validators with content-free controlled errors.
    - Thin argparse wrapper with enum-only operation and target choices.
key-files:
  created:
    - src/multilang/services/korean_foundation_ai_curation.py
    - scripts/build_korean_foundation_candidates.py
    - tests/services/test_korean_foundation_ai_curation.py
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-11-SUMMARY.md
  modified:
    - .planning/SPEC.md
    - .planning/ROADMAP.md
key-decisions:
  - "Draft contracts can propose only allowlisted learner-copy fields and explicit uncertainty/disagreement records."
  - "All proposal, batch, family, and manifest contracts retain `draft_only=true`, `review_status=needs_review`, and `promotion_authority=false`."
  - "Compact projections may expose read-only source structure for later curation context, but structural graph changes are not representable in draft proposals."
requirements-advanced: [KHAN-01, KHAN-02, KPRO-01, KPRO-02]
requirements-completed: []
completed: 2026-08-24
---

# Phase 31 Plan 11: Assisted-Curation Contracts and Tooling Summary

Plan 31-11 is complete. It adds safe local machinery for later assisted curation, but does not author or select Korean learner content, modify `v1` assets, create `v2` candidate assets, write evidence, call providers, approve reviews, activate snapshots, or export production decks.

## Accomplishments

- Added `src/multilang/services/korean_foundation_ai_curation.py` with frozen Pydantic v2 models for source references, field proposals, uncertainties, disagreements, records, batch drafts, family drafts, manifest bindings, compact projections, validation reports, and controlled errors.
- Bound every draft record to exact immutable source file name, source file SHA-256, source pack version, source pack content hash, registry version/hash, item key, sequence, stage, and entry content hash.
- Enforced family-specific learner-copy allowlists:
  - Hangul: `reading_or_name`, `sound`, `mnemonic`.
  - Pronunciation: `spellings`, `sound`, `example_word`, `word_translation`, `example_sentence`, `sentence_translation`, `normative_pronunciation`, `surface_pronunciation`, `ipa`.
- Added fixed compact projection generation for six stage groups, each capped at 120 KiB and excluding unrelated records, media slots, pending review authority, and inherited full source-pack bulk.
- Added deterministic assembly for exact three-batch family drafts and one exact two-family manifest with 92 Hangul records, 47 pronunciation records, and 139 total records.
- Added read-only validation that loads all six batches, both family drafts, and the manifest, reconstructs expected family/manifest bindings from loaded children, aggregates content-free failures, and never writes.
- Added `scripts/build_korean_foundation_candidates.py` with exactly five fixed operations: `project-batch`, `validate-batch`, `assemble-family`, `assemble`, and `validate-drafts`.
- Updated `.planning/SPEC.md` and `.planning/ROADMAP.md` so Plan 31-11 is complete and Plan 31-12 is next.

## Command Surface

```text
python scripts/build_korean_foundation_candidates.py project-batch {six batch IDs}
python scripts/build_korean_foundation_candidates.py validate-batch {six batch IDs}
python scripts/build_korean_foundation_candidates.py assemble-family hangul|pronunciation
python scripts/build_korean_foundation_candidates.py assemble
python scripts/build_korean_foundation_candidates.py validate-drafts
```

- Batch IDs are fixed to `hangul-h0-h3`, `hangul-h4-h7`, `hangul-h8-h10`, `pronunciation-p0-p4`, `pronunciation-p5-p9`, and `pronunciation-p10-p13`.
- The script exposes no root, output, URL, provider, force, approve, repair, promote, check-selection, or regenerate option.
- Writers are restricted to the fixed Phase 31 curation draft roots; validation functions remain read-only.

## RED/GREEN Evidence

Representative RED failures were witnessed before corresponding implementation:

| Task | RED evidence | GREEN evidence |
|---|---|---|
| `31-11-01` module existence | `test_ai_curation_contract_module_exists` failed with an assertion because the module was absent. | Focused module test passed after creating the minimal module. |
| `31-11-01` contract symbols | `test_ai_curation_contract_types_exist` failed with an `AssertionError` listing missing model names. | Contract type test passed after adding frozen model shells. |
| `31-11-01` source reference | `test_source_reference_is_exact_frozen_and_forbids_authority` failed with `extra_forbidden` validation errors before fields existed. | Source reference accepted exact v1 hashes and rejected mutation, extras, and uppercase hashes. |
| `31-11-01` proposal/uncertainty text | `test_field_dispositions_are_bounded_plain_nfc_text_without_placeholders` failed before field models existed and later caught compatibility-jamo acceptance. | Field models now reject null proposals, placeholders, markup, non-NFC values, compatibility jamo, and authority extras. |
| `31-11-01` batch/family/manifest | Batch and family tests failed before models existed. | Batch/family/manifest contracts validate exact 92/47/139 coverage and reject stale source or entry hashes. |
| `31-11-02` script surface | `test_fixed_curation_script_surface_exists` failed because the script was absent. | Script exists and help shows only the five fixed operations. |
| `31-11-02` projections | `test_compact_projections_have_exact_bounded_stage_coverage` failed because the projection builder was absent. | Six projections cover exactly 139 records, stay under 120 KiB each, and omit unrelated records/media/review authority. |
| `31-11-02` assembly/validation | `test_fixed_validation_and_assembly_are_deterministic_and_read_only` failed because assembly functions were absent. | Family and manifest assembly are deterministic; validation is write-poisoned and read-only. |
| `31-11-02` cross-binding defect | A stale family child-batch hash was initially accepted by self-hashed family/manifest payloads. | Read-only validation now reconstructs expected families from the six loaded batches before accepting a manifest. |
| `31-11-02` aggregate failures | Batch validation initially stopped at the first failing batch. | Read-only validation now checks all six batches and reports content-free aggregate failure codes. |

## Verification Results

| Check | Result |
|---|---|
| Plan RED command for module absence | Passed: status `1` with assertion failure. |
| Plan RED command for script absence | Passed: status `1` with assertion failure. |
| Focused curation suite | `25 passed in 40.96s` |
| Adjacent curriculum + curation regression | `161 passed in 83.53s` |
| Script help | `UV_OFFLINE=1 uv run --extra dev python scripts/build_korean_foundation_candidates.py --help` returned only the five fixed operations. |
| Whitespace/diff check | `git diff --check` passed. |
| Protected canonical/evidence/export tree hash | `2bfcd9b17e6826aa9a9afb4755e70360a31f4d2c399492f0523b854e37f7f931` |
| Protected canonical/evidence/export targeted status | clean; no tracked or untracked changes under `data/korean_foundations`, Phase 31 `evidence-inbox`, or `.multilang/exports/korean-foundations`. |

The protected tree hash is the scoped post-run invariant for the tracked canonical/evidence/export paths. No Plan 31-11 operation wrote those paths, and targeted Git status remained clean for them before summary creation.

## Forbidden Field Coverage

Tests explicitly reject authority, rights, playback, media/artifact, production voice, and structural-spoof fields including:

```text
approval
reviewer
qualification
rights_disposition
redistribution_disposition
media_hash
artifact_hash
playback_verified
production_voice_id
prerequisite_concept_ids
active_rule_ids
```

The contracts also reject extra fields generally through `extra="forbid"`; these names are representative high-risk regressions.

## Canonical Boundaries

- `data/korean_foundations/{hangul-v1,pronunciation-i-plus-1-v1}.json` remained unchanged.
- No files were written under Phase 31 evidence inbox, canonical snapshots, active pointer state, candidate bundle state, or production export roots.
- No provider, network, database, TTS, Azure, LLM, or external source hook was introduced.
- No draft field can represent reviewer identity, qualification, approval, rights disposition, playback evidence, production voice approval, media bytes, or canonical promotion authority.
- No user-selected source/output root was added. The only write helper is fixed-path and rejects unregistered paths.

## Deviations and Recoverable Discoveries

### Factual Discovery: Prior Summary Wording

`31-10-SUMMARY.md` still describes Plan 31-11 as a human checkpoint. The approved replanned `31-11-PLAN.md`, `.planning/SPEC.md`, and `.planning/ROADMAP.md` now govern: Plan 31-11 is engineering contracts/tooling, while genuine evidence remains later at Plan 31-26.

### Factual Discovery: Projection Structure Context

Compact projections include read-only target/prerequisite/active-rule context plus a structural hash so later curation can challenge prerequisite leakage and rule alignment without loading full source packs. Draft proposal schemas do not allow structural graph fields, so this does not create structural mutation authority.

### Factual Discovery: Shared State File

`.planning/STATE.md` remains stale and still says Plan 31-11 is next. It was intentionally left untouched because the user had already identified parallel work there. Current handoff is through `SPEC.md`, `ROADMAP.md`, and this summary.

## Remaining Work

- Plans 31-12 through 31-18 can now produce bounded batch drafts using the six compact projections.
- Plan 31-19 remains responsible for exact two-family draft assembly and reporting.
- Plan 31-20 remains responsible for human selection/handoff; this plan grants no selection authority.
- Genuine reviewer, Portuguese policy, rights, exact media bytes, playback, receipt, snapshot, activation, export, release, and observed Anki acceptance gates remain unresolved.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified TDD RED/GREEN path, fixed script help, focused curation suite, adjacent curriculum regression, write-boundary test, content-free aggregate failure handling, protected canonical/evidence/export status, and git diff check. No provider/network/canonical mutation was introduced.
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
  disposition: recorded_and_proceeded
  summary: `31-10-SUMMARY.md` described the former Plan 31-11 checkpoint role; the approved replanned Plan 31-11 is engineering-only contracts/tooling.
- class: factual_discovery
  impact: recoverable
  disposition: recorded_and_proceeded
  summary: Compact projections need read-only structural context for later linguistic challenge passes, but draft schemas still reject structural mutation fields.
- class: factual_discovery
  impact: recoverable
  disposition: preserved_parallel_work
  summary: `.planning/STATE.md` still points at old Plan 31-11 wording and was intentionally not modified because it is shared parallel state.
</deltas>

<judgment>
<active_constraints>
Continue to preserve immutable v1 source packs, `draft_only=true`, `review_status=needs_review`, `promotion_authority=false`, exact hash bindings, fixed curation roots, enum-only script operations, no provider/network calls, no approval-bearing fields, and no canonical evidence/export mutation.
</active_constraints>
<unresolved_uncertainty>
Actual learner-copy quality, uncertainty dispositions, selected drafts, human review, Portuguese policy, rights, exact media bytes, playback, candidate publication, request regeneration, canonical receipt/snapshot/activation, production exports, and observed Anki acceptance remain later-plan work.
</unresolved_uncertainty>
<decision_posture>
Proceed to Plan 31-12 for bounded Hangul H0-H3 curation using the fixed projection and draft contracts. Do not infer approval, selection, promotion, or production readiness from Plan 31-11 machinery.
</decision_posture>
<anti_regression>
Do not add arbitrary roots, URLs, providers, force/approve/repair options, raw chain-of-thought storage, reviewer authority fields, rights/playback/media-byte fields, structural mutation fields in drafts, or writes outside fixed curation draft outputs.
</anti_regression>
</judgment>

## Self-Check: PASSED

- Required service, script, test, summary, SPEC, and ROADMAP files exist.
- Required structured sections occur in the summary: `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`.
- Focused and adjacent offline suites pass.
- Protected canonical/evidence/export paths remain clean.
- No Git staging, commit, push, reset, restore, clean, stash, tag, or PR action occurred.

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 11*
*Completed: 2026-08-24*
