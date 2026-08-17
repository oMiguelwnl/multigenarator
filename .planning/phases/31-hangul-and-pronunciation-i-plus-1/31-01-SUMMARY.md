---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "01"
subsystem: korean-foundation-contracts
runtime: opencode
assurance: self_checked
tags: [korean, hangul, unicode, pydantic, graphlib, strict-i-plus-1, security, tdd]
requires:
  - phase: 30-korean-contracts-and-morphology
    provides: Canonical ko identity, unchanged NFC canonicalization, Compatibility/halfwidth rejection, and fail-closed Korean contracts
provides:
  - Frozen Korean concept, curriculum, pronunciation, and positional pedagogical-Jamo contracts
  - Exhaustive Unicode-formula composition and decomposition for all 11,172 modern Hangul syllables
  - Bounded fixed-path JSON manifest schemas and content-free loader failures
  - Shared graph validator that recomputes bootstrap and strict-i+1 evidence before target admission
affects: [31-02, 31-03, korean-foundation-review, korean-foundation-media, korean-foundation-export]
tech-stack:
  added: []
  patterns:
    - Compatibility Jamo remains display-only evidence mapped explicitly to positional conjoining Jamo
    - Frozen manifests use canonical-JSON SHA-256 and no-argument fixed-path public loaders
    - Strict-i+1 targets become known only after graph and observed-minus-known recomputation succeeds
key-files:
  created:
    - src/multilang/services/korean_curriculum.py
    - tests/services/test_korean_curriculum.py
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-01-SUMMARY.md
  modified:
    - src/multilang/domain/korean.py
    - tests/domain/test_korean.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Keep Phase 30 canonicalize_korean() byte-for-byte unchanged; pedagogical Compatibility Jamo is isolated in a reviewed positional mapping."
  - "Load foundation manifests only through public no-argument fixed-path loaders; no public path, root, URL, archive, or APKG input is accepted."
  - "Treat serialized prerequisite and unknown tuples as evidence to compare, never as proof; the validator independently computes known-before and one target unknown."
patterns-established:
  - "Foundation domain flow is orthography-only for Hangul and orthography-plus-phonology for pronunciation, with dependency direction checked in the registry."
  - "Manifest limits are checked both before and after reading so a changed file cannot bypass the byte cap."
requirements-advanced: [KHAN-01, KHAN-02, KPRO-02]
requirements-completed: []
duration: 31m
completed: 2026-08-05
---

# Phase 31 Plan 01: Korean Foundation Contracts and Strict Curriculum Engine Summary

**Immutable positional-Jamo contracts, exhaustive modern-Hangul Unicode round trips, bounded fixed-path manifests, and independently recomputed strict-i+1 graph admission now form the shared foundation for later Hangul and pronunciation packs.**

## Performance

- **Started:** approximately 2026-08-05T19:52:28Z
- **Completed final checks:** 2026-08-05T20:23:10Z
- **Duration:** approximately 31m
- **Tasks:** 3/3
- **Execution-owned files created/modified:** 7, including this summary, the SPEC handoff, and the reviewed session fingerprint
- **Assurance:** `self_checked` through strict RED/GREEN cycles, exhaustive Unicode evidence, graph mutations, security review, compilation, dependency-lock validation, and focused Korean regressions

## Accomplishments

- Added frozen, extra-forbidden, bounded `KoreanConcept`, `KoreanCurriculumEvidence`, `KoreanPronunciationEvidence`, `KoreanReviewStatus`, and `KoreanPedagogicalJamoMapping` contracts without changing any Phase 30 public export.
- Kept learner-facing Compatibility Jamo outside canonical identity while range-checking its explicit modern choseong, jungseong, or jongseong mapping and Unicode name.
- Implemented Unicode's modern Hangul arithmetic over 19 initials, 21 medials, and 28 final states; all 11,172 precomposed syllables are unique, NFC, and exactly reversible.
- Added frozen source-provenance, pending-review, media-slot, stage-coverage, registry, Hangul-pack, pronunciation-pack, and validation-result models with deterministic canonical-JSON SHA-256 checks.
- Added public no-argument fixed-path UTF-8 JSON loaders with one-megabyte limits, controlled content-free reason codes, and no network/archive/package intake.
- Added one shared validator for registry alignment, exact H0 bootstrap order, declared inherited orthography, known-before sequencing, active non-target rules, and serialized-versus-recomputed one-unknown evidence.
- Closed second-pass gaps by rechecking actual bytes after the file-size probe and rejecting non-foundation domains or phonology-to-orthography dependency inversion.

## TDD Task Evidence

### Task 31-01-01: Define frozen Korean foundation and positional-Jamo contracts

- **Baseline:** `UV_OFFLINE=1 uv run --extra dev pytest tests/domain/test_korean.py -q` produced **21 passed in 0.08s**.
- **RED:** The new domain contract suite produced **39 failed, 21 passed in 0.52s** because the models and exports did not exist.
- **GREEN:** The frozen contracts, validators, display boundary, and exports produced **60 passed in 0.12s** after one patch-application correction and warning cleanup.

### Task 31-01-02: Implement exhaustive modern-Hangul composition and decomposition

- **RED:** The algorithmic and invalid-boundary tests produced **27 failed, 32 passed, 28 deselected in 0.46s**.
- **First GREEN attempt:** **1 failed, 58 passed, 28 deselected in 0.29s** exposed that an empty final string must be rejected rather than treated as the no-final state.
- **GREEN:** Checking `final is not None` preserved `None` as the sole no-final marker and produced **59 passed, 28 deselected in 0.14s**.
- The exhaustive contract checks every generated code point, uniqueness, NFC, exact decomposition, and the `U+AC00` through `U+D7A3` boundaries.

### Task 31-01-03: Create bounded loaders and the shared strict curriculum engine

- **RED:** The service suite produced **36 failed, 87 passed in 0.90s** because `multilang.services.korean_curriculum` did not exist.
- **Initial GREEN:** The complete in-memory loader/graph/bootstrap/mutation matrix produced **123 passed in 0.39s**.
- **Security second-pass RED:** Three focused tests failed as expected: post-`stat()` growth returned `manifest_malformed`, and unsupported registry domains/dependency direction were accepted.
- **Security second-pass GREEN:** The focused fixes produced **3 passed, 36 deselected in 0.11s**, followed by **126 passed in 0.36s** for the complete Task 3/domain suite.

No task commits were created because the user explicitly prohibited all Git delivery actions. RED/GREEN command evidence is preserved here instead.

## Final Verification Results

| Check | Exact result |
|---|---|
| Final domain suite | `87 passed in 0.19s` |
| Final Hangul/Jamo/canonical selection | `59 passed, 28 deselected in 0.16s` |
| Final curriculum + domain + Phase 30 language-support regression | `134 passed in 1.57s` |
| Broad Korean/Hangul/pronunciation selection | `271 passed, 1002 deselected, 5 warnings in 47.87s` |
| Focused registry/bootstrap/strict/inheritance second pass | `24 passed, 12 deselected in 0.13s` |
| Focused exhaustive Hangul/Jamo/canonical second pass | `30 passed, 57 deselected in 0.10s` |
| Python compilation of all four implementation/test files | Exit 0 with no output |
| Dependency lock | `Resolved 200 packages in 2ms` |
| Phase 30 canonicalizer source hash | `d3ab62a1f26d494d024ccf3c5c9ed20fd4efdbc18d05d71d441209337e83fb6b` (unchanged) |
| Reviewed session fingerprint | `4cddc2a3ec93dcc731e38ae2ba5119e1b3c766988ea8cad3e0e2be89193aeaf6` |

The five warnings are the known Alembic `path_separator` deprecations from migration parity tests. They are unrelated to this plan. Ruff is not installed or configured in the offline project environment, so the supplemental Ruff command reported `program not found`; no dependency or network change was attempted, and compilation plus every required pytest gate passed.

## High-Leverage Trace

### Hangul bootstrap and later target

1. The first H0 entry starts with an empty `known_before`, observes only `orthography.jamo.unit`, recomputes that target as its sole unknown, and admits it only after validation.
2. The second H0 entry explicitly requires and observes the now-known Jamo unit plus `orthography.block.unit`; only the block target is unknown and then admitted.
3. The H1 vowel entry requires the known Jamo unit, observes that prerequisite plus `orthography.vowel.a`, and admits only the vowel target.
4. Reversing `bootstrap_concept_ids`, pre-knowing another H0 target, forging unknown evidence, repeating a target, or adding an undeclared active rule all fail with controlled reason codes.

### Pronunciation inheritance and active rule

1. The pronunciation pack declares exactly `orthography.jamo.unit` as inherited; the caller must supply the identical ordered tuple, and every inherited ID must exist in the registry as orthography.
2. `phonology.syllable.timing` is validated as the first phonological target while inherited orthography is already known.
3. The nasalization entry observes the inherited orthography, known timing rule, and new nasalization target; timing is an explicit active non-target prerequisite.
4. Missing/forged inheritance, a non-phonological target, an unknown prerequisite, or an active rule absent from known prerequisites fails before review or export.

## Files Created/Modified

### Created

- `src/multilang/services/korean_curriculum.py` - frozen manifest contracts, fixed loaders, canonical hashes, registry validation, and strict curriculum admission.
- `tests/services/test_korean_curriculum.py` - safe-loader, graph, bootstrap, inheritance, domain, and false-evidence mutation matrix.
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-01-SUMMARY.md` - TDD, security, verification, and bounded handoff evidence.

### Modified

- `src/multilang/domain/korean.py` - additive foundation models plus modern-Hangul composition/decomposition; Phase 30 canonicalization remains unchanged.
- `tests/domain/test_korean.py` - frozen-contract, display-boundary, invalid-code-point, and exhaustive 11,172-syllable evidence.
- `.planning/SPEC.md` - compact Current State handoff to Plan 31-02 while Phase 31 remains open.
- `.planning/.state-fingerprint.json` - reviewed SPEC/ROADMAP/config fingerprint after the handoff.

## Git Actions

None. Per explicit user instruction and the carried Phase 30 convention, no file was staged or committed, and no branch, push, PR, amend, reset, stash, clean, checkout, restore, tag, or other Git delivery/destructive action was performed.

## Decisions Made

- The existing four-domain `KoreanConcept` contract remains future-compatible, while this foundation registry accepts only orthography and phonology and prevents an orthographic concept from depending on phonology.
- A pedagogical glyph never passes through `canonicalize_korean()` or NFKC; its positional modern identity and Unicode name must be supplied and validated explicitly.
- `None` is the only valid no-final marker for Hangul composition; blank strings and every compatibility, halfwidth, archaic, multi-character, or out-of-range input fail closed.
- Registry and pack hashes are canonical UTF-8 JSON SHA-256 values over all fields except `content_hash`; manifest values cannot silently self-certify drifted content.
- H0 is explicit data, not an exemption. No bootstrap target is pre-known, and every target enters the known set only after the same strict one-unknown calculation used by later entries.
- Model-level `needs_review` records describe actionable future work only; this plan creates no linguistic, pedagogical, media, or playback approval.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Security] Rechecked bytes after the manifest size probe**
- **Found during:** Task 31-01-03 security second pass.
- **Issue:** A file that grew between `stat()` and `read_bytes()` could bypass the one-megabyte pre-read limit and be parsed as malformed input instead of being rejected as oversized.
- **Fix:** Recheck `len(raw)` immediately after reading and raise the same content-free `manifest_oversized` reason.
- **Files modified:** `src/multilang/services/korean_curriculum.py`, `tests/services/test_korean_curriculum.py`.
- **Verification:** Focused RED returned `manifest_malformed`; GREEN returned `manifest_oversized`, and the complete 126-test task suite passed.
- **Committed in:** Not committed by explicit user instruction.

**2. [Rule 2 - Missing Critical Correctness] Enforced foundation registry domain compatibility**
- **Found during:** Task 31-01-03 high-leverage graph review.
- **Issue:** A registry could accept grammar/lexicon concepts or an orthographic concept depending on a phonological predecessor despite this phase loading only orthography/phonology and requiring family/domain-compatible edges.
- **Fix:** Restrict the foundation registry to orthography/phonology; orthography may depend only on orthography, while phonology may depend on orthography or phonology.
- **Files modified:** `src/multilang/services/korean_curriculum.py`, `tests/services/test_korean_curriculum.py`.
- **Verification:** Both mutations failed RED by being accepted, then passed GREEN by raising hidden-input Pydantic validation errors; all graph and broad Korean regressions passed.
- **Committed in:** Not committed by explicit user instruction.

---

**Total deviations:** 2 auto-fixed (2 missing-critical safeguards).
**Impact on plan:** Both fixes directly satisfy the planned DoS and domain-link mitigations; no dependency, architecture, content, provider, media, export, or runtime scope was added.

## Issues Encountered

- One Task 1 implementation patch initially left the intended source additions unapplied; the unchanged RED result exposed it immediately, and the source was reapplied before GREEN.
- Task 2's first implementation treated an empty final string like `None`; the failing boundary test identified the exact cause, and the implementation was narrowed to `final is not None`.
- Ruff is absent from the repository's offline development environment. This is established project tooling state, not a plan blocker; no package was added.

## Security and Privacy Review

- Public production loaders accept no arguments and read only fixed project constants; the private parser is not exported.
- Inputs are UTF-8 JSON only, bounded before and after read, parsed without pickle/YAML/code evaluation, validated through frozen extra-forbidden models, and reported through content-free reason codes.
- Source text rejects unsafe markup/media markers, non-NFC data, Compatibility Jamo outside the dedicated display contract, and all halfwidth Hangul.
- The new modules contain no Azure, Tatoeba, HTTP client, remote fetch, archive, APKG, subprocess, database, credential, or LLM path.
- SHA-256 is used for deterministic data integrity, not password storage or authentication.
- The only new file-access surface is the fixed manifest boundary already covered by threat IDs T-31-01-03 through T-31-01-05; no unplanned endpoint, authentication path, schema boundary, or network surface was introduced.

## Known Stubs

None. Optional `None` values and empty tuple defaults are bounded source-schema states, not learner-facing placeholders. The four changed implementation/test files contain no TODO, FIXME, coming-soon, placeholder, or unavailable copy, and no missing data source prevents this plan's contract/engine objective.

## Authentication Gates

None.

## User Setup Required

None. This plan makes no provider call and requires no credential, production manifest, media byte, database, export application, or visual review.

## State and Handoff

- `.planning/SPEC.md` records Plan 31-01 complete and Plan 31-02 next while Phase 31 remains in progress.
- `.planning/ROADMAP.md` remains open at `[-]`; execution did not mark Phase 31 complete.
- `KHAN-01`, `KHAN-02`, and `KPRO-02` are advanced but remain unchecked because this plan proves contracts and mechanics, not the complete reviewed learner capabilities.
- The reviewed planning fingerprint is `4cddc2a3ec93dcc731e38ae2ba5119e1b3c766988ea8cad3e0e2be89193aeaf6`.
- Plan 31-02 can now populate the shared registry and H0-H10 pack through these contracts. It must not weaken canonicalization, invent approval, or reinterpret Compatibility Jamo as machine identity.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: All three TDD tasks, exhaustive 11,172-syllable round trips, loader/graph/bootstrap mutations, final 134-test focused regression, 271-test broad Korean selection, compilation, lock validation, security scans, and canonicalizer hash check passed offline.
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
  disposition: proceeded
  summary: The pre-read byte limit alone had a stat/read race; a focused failing test and post-read length check closed the planned manifest DoS boundary.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Initial graph validation covered IDs, closure, cycles, and order but not foundation domain compatibility; focused mutations now reject unsupported domains and dependency direction.
</deltas>

<judgment>
<active_constraints>
Keep canonical Korean identity at `ko`; keep `ko-KR` restricted to the pre-existing provider locale constant. Preserve `canonicalize_korean()` rejection of Compatibility and halfwidth Hangul. Machine Jamo identity is positional modern conjoining Jamo only. Public source loading remains fixed-path, bounded, local, and provider-free. No automated result may become linguistic, pedagogical, media, playback, or export approval.
</active_constraints>
<unresolved_uncertainty>
The exact reviewed H0-H10 and P0-P13 inventories, concept atomicity, source-backed learner copy, qualified reviewer identities, licensed media bytes, playback evidence, templates, and export artifacts remain later Phase 31 work. This plan does not validate their linguistic quality or learner readiness.
</unresolved_uncertainty>
<decision_posture>
Prefer explicit positional identity, complete predecessor closure, and a blocked false negative over Unicode inference or trusted serialized labels. Treat manifests as untrusted even when committed, recompute graph facts before review, and leave every unavailable human/media fact actionable and unapproved.
</decision_posture>
<anti_regression>
Do not change the Phase 30 canonicalizer hash, use NFKC for Jamo identity, pre-mark H0 as known, trust serialized unknown tuples, allow orthography to depend on phonology, add arbitrary path/URL loaders, expose source content in errors, or introduce provider/runtime/export/media behavior into this foundation contract layer.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All seven execution-owned source, test, planning, fingerprint, and summary files exist.
- Every finalized task and plan-level verification passed: domain `87`, Hangul/Jamo selection `59`, focused regression `134`, and broad Korean selection `271`.
- The exhaustive domain test still covers all 11,172 modern Hangul syllables, and the Phase 30 canonicalizer hash remains exactly `d3ab62a1f26d494d024ccf3c5c9ed20fd4efdbc18d05d71d441209337e83fb6b`.
- Rewriting the reviewed session fingerprint after the SPEC handoff reproduced `4cddc2a3ec93dcc731e38ae2ba5119e1b3c766988ea8cad3e0e2be89193aeaf6`.
- Phase 31 remains open at `[-]`; the three plan requirements remain advanced but unchecked, and no learner-ready content, media, approval, template, export, provider, database, or UI claim was made.
- Required structured sections (`<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`) are present and substantive.
- No commit check applies because all Git actions were explicitly prohibited and none were performed.

---
*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 01*
*Completed: 2026-08-05*
