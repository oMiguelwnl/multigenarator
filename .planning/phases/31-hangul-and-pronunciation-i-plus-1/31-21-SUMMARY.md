# Phase 31: Hangul and Pronunciation i+1 - Plan 21 Summary

**Completed**: 2026-08-24
**Tasks**: 2
**Git Actions**: None.
**Deviations**: The first self-created candidate bundle included `size_bytes` in member declarations. The contract was tightened to member `name` and `sha256` only, the self-created obsolete candidate files were removed, and the bundle was republished. Full `pytest -q` was attempted twice but exceeded the 120s and 300s tool timeouts while still progressing; targeted regressions passed.
**Decisions Made**: Candidate publication is atomic-create/idempotent rather than arbitrary replace; conflicting pointers or bundles are refused. The published bundle is candidate-only and does not approve content, evidence, media, activation, export, production use, or Anki acceptance.
**Notes for Verification**: `current-candidate.json` is the only reader-visible pointer and contains only `schema_version`, `bundle_sha256`, `bundle_relpath`, and `bundle_manifest_sha256`.
**Notes for Next Work**: Proceed to Plan 31-22 request regeneration using the candidate pointer as read-only selected candidate input; do not bypass later review/evidence gates.

## Published Candidate

| Item | Hash |
|---|---|
| Selected draft manifest | `8f053a815b4b18c9e8004d295849f562989410f05f4a1cc8725bc37f8c7f26b5` |
| Selection check plan | `710a319c6b62183cb66d829ebb10cc2770af453bae5823fee77a612ebad2549b` |
| Publication content | `13fdd603cfdaf60f0c236121ee214e2ffcd40b28b311d48c8e487d5cfd5cf88f` |
| Bundle SHA-256 | `36c1442b161fb3d8529678099b4df1c93b43fb2456a24260ac2942787b7f44f0` |
| Bundle manifest file SHA-256 | `2390974b9f48534665d474b9fe18290e28edc361aa3cc119481db70e44acfd40` |
| Pointer file SHA-256 | `0fa9e0756ab59969dc55ab428544c18aad1d1d14631b0d2569a33823feb24518` |

Bundle relpath: `data/korean_foundations/candidate-bundles/36c1442b161fb3d8529678099b4df1c93b43fb2456a24260ac2942787b7f44f0/`

Pointer path: `data/korean_foundations/current-candidate.json`

## Member Hashes

| Member | File SHA-256 | Internal `content_hash` |
|---|---|---|
| `hangul-v2.json` | `63c36c50c0efa61f7ba76ebdf92ff174f79aadedb63b46d15da01599f2594f59` | `15143e23dea2236b0ada6f3603f79babb52bc4a89213906084d16c8bf864843a` |
| `pronunciation-i-plus-1-v2.json` | `cdac65b7e3a9615e62f187dcf7c7f6c543a480710b618ce0c9eb580281cd955c` | `4cb7f0b2a453a61858bf6a4b15a95568328a7348ba164d6ef9fd2bdf68119682` |
| `korean-foundations-v2-curation.json` | `faa233cdc67f99c28c3f203e1b206f4ad4f631bc34b8e2fbb970db336f1157db` | `08874c6f4c64240d79cbdb982c1aa0d8a886749bc8100da41036b7c1b8ba9b22` |
| `korean-foundations-v2-media.json` | `e21c7a11006cf70a0559ec7fff7279b466097cf3bbc1fa092cee84e7b963e938` | `8d860b5e41738d2322dc63eb220eb23de66f4b68b4ff1f9e3dd8979e90b5b55a` |

## Counts and Pending Gates

| Check | Result |
|---|---|
| Bundle members | Exact four members plus `bundle-manifest.json`; no extra member declarations beyond `name` and `sha256`. |
| Hangul entries | 92 entries, `source_pack_version=hangul-v2`, `review_status=needs_review`. |
| Pronunciation entries | 47 entries, `source_pack_version=pronunciation-i-plus-1-v2`, `review_status=needs_review`. |
| Curation records | 139 total: 92 Hangul and 47 pronunciation; `candidate_only=true`. |
| Curation gates | All gates remain `needs_review`; reviewer/evidence approval fields remain null. |
| Media slots | 509 total; `candidate_only=true`; all slots remain `needs_review` with no artifact/source approval metadata. |
| v1 invariance | Embedded source-pack hashes remain `2bdbfb60aaca1419c2bb20abc8fb9954941bc8f92cb2361c3bc778b01c9b599c` and `641b06f4d1c05c70803b859aa2936fc517a1038ad190ac7c58574da8a93ea49e`; v1 files were not edited. |

## Task Results

### 31-21-01: Implement candidate bundle publication test-first

- RED: `tests/services/test_korean_foundation_ai_curation.py::test_candidate_bundle_publication_is_atomic_for_readers` failed with `AssertionError` because promotion/read/verify functions were absent.
- GREEN: added `promote_korean_foundation_curation_selection()`, `verify_promoted_korean_foundation_candidate()`, `read_current_korean_foundation_candidate()`, immutable bundle assembly, bundle manifest validation, atomic-create pointer publication, conflict refusal, and CLI wiring.
- The writer stages the complete four-member bundle under `candidate-bundles/<bundle_sha256>` before publishing the four-field pointer.
- Existing identical state is idempotent; conflicting pointer/bundle state is refused with explicit reason codes.

### 31-21-02: Publish and verify the exact selected v2 bundle

- Ran the fixed command sequence: `get-selection`, `check-selection`, `promote --expected-draft-manifest-sha256`, and `verify-promoted --expected-draft-manifest-sha256`.
- The final command sequence returned selection check `710a319c6b62183cb66d829ebb10cc2770af453bae5823fee77a612ebad2549b` and publication `13fdd603cfdaf60f0c236121ee214e2ffcd40b28b311d48c8e487d5cfd5cf88f`.
- Re-running `promote` against the existing pointer returned the same publication hash, proving exact retry idempotency.

## Verification Results

| Check | Result |
|---|---|
| Named RED | Failed with `AssertionError` before implementation. |
| Focused publication tests | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_ai_curation.py::test_candidate_bundle_publication_is_atomic_for_readers tests/services/test_korean_foundation_ai_curation.py::test_candidate_bundle_publication_refuses_conflicting_pointer -q` -> `2 passed`. |
| Curation service tests | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_ai_curation.py -q` -> `29 passed`. |
| Combined relevant regressions | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_ai_curation.py tests/services/test_phase31_handoff.py -q` -> `34 passed`. |
| Promotion command sequence | `check-selection`, `promote`, and `verify-promoted` passed with hashes above. |
| Structural assertion pass | Verified exact pointer keys, manifest/member hashes, counts, candidate-only flags, needs-review gates, and no approval artifacts. |
| Idempotent retry | Re-running `promote` returned `13fdd603cfdaf60f0c236121ee214e2ffcd40b28b311d48c8e487d5cfd5cf88f`. |
| Full suite attempt | `UV_OFFLINE=1 uv run --extra dev pytest -q` timed out after 120s, then after 300s while still progressing; no failure was reported before timeout. |

## Boundaries Preserved

- No provider, network, LLM, TTS, Azure, database, or external source call occurred.
- No canonical evidence, receipt, active snapshot pointer, production export, or `.multilang/exports/korean-foundations` artifact was created.
- No content, Korean phonetics, Portuguese, rights, playback, media, production-readiness, export-readiness, or Anki acceptance claim was made.
- P11-P13 pronunciation uncertainties remain candidate-only and specialist-sensitive; no learner-ready approval was inferred.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified RED/GREEN tests, fixed CLI promotion/verification, exact selected hash binding, final pointer/member hashes, structural counts, pending-only gates, idempotent retry, and preserved no-provider/no-evidence/no-export boundaries. Full pytest exceeded tool timeout while progressing; targeted regressions passed.
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
- class: implementation_correction
  impact: recoverable
  disposition: corrected_before_completion
  summary: Removed `size_bytes` from candidate bundle member declarations and republished the self-created candidate bundle so the manifest declares only member names and hashes.
- class: verification_limit
  impact: non_blocking
  disposition: targeted_regressions_passed
  summary: Full pytest exceeded 120s and 300s timeouts while still progressing; targeted Phase 31 regressions and structural artifact assertions passed.
</deltas>

<judgment>
<active_constraints>
Continue to preserve immutable v1 source packs, exact selected-manifest binding, fixed hash-only handoff roots, fixed candidate pointer semantics, no arbitrary output roots, no provider/network calls, no authority-bearing approvals, no canonical evidence/export mutation, and no production activation before later authorization gates.
</active_constraints>
<unresolved_uncertainty>
The published v2 bundle is a selected candidate bundle only. Qualified Korean phonetics review, Portuguese review, rights dispositions, licensed exact media, playback evidence, canonical receipt, inactive snapshot, activation authorization, local exports, and observed Anki acceptance remain unresolved later gates.
</unresolved_uncertainty>
<decision_posture>
Proceed to Plan 31-22 with this immutable candidate pointer as input for pending request regeneration. Do not treat `current-candidate.json` as a production active snapshot pointer.
</decision_posture>
<anti_regression>
Do not expose four sibling files independently; do not overwrite conflicting pointers/bundles; do not parse selection hashes from prose; do not mutate v1 or approved evidence paths; do not convert candidate-only review fields into approved fields during request regeneration.
</anti_regression>
</judgment>

## Self-Check: PASSED

- Required service primitives, CLI commands, tests, candidate bundle tree, four-field pointer, summary, and planning handoff updates exist.
- Required structured sections occur in the summary: `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`.
- RED/GREEN verification paths passed as recorded.
- The bundle manifest declares exactly four fixed member names and hashes.
- The pointer contains only the four fixed fields.
- No Git staging, commit, push, reset, restore, clean, stash, tag, or PR action occurred.

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 21*
*Completed: 2026-08-24*
