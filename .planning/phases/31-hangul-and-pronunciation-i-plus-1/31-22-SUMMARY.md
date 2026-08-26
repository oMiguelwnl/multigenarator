---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "22"
runtime: opencode
assurance: self_checked
---

# Phase 31: Hangul and Pronunciation i+1 - Plan 22 Summary

**Completed**: 2026-08-25
**Tasks**: 2
**Git Actions**: None.
**Deviations**: The checkout already contained older v1 request files, so the v2 binding RED failed on stale bindings rather than missing files. The fixed regeneration replaced those files. During security review, `current-candidate.json` reader symlink handling was hardened before completion.
**Decisions Made**: Request regeneration now derives both review requests only from the fixed current-candidate pointer and the referenced immutable v2 bundle. Request files remain request-only and carry no evidence or approval authority.
**Notes for Verification**: Adjacent evidence tests still encode the older v1 request hashes and are intentionally not updated in this plan; evidence/receipt work remains later Phase 31 scope.
**Notes for Next Work**: Proceed to Plan 31-23 using the v2 request artifacts as pending reviewer inputs only; do not treat them as evidence.

## Request Artifacts

| Item | Hash |
|---|---|
| Request regeneration result | `24c60fe9e5eb12035dac514b5fcb58a6bc0cbe410cb17cc309dea7fdce1f3b00` |
| Curriculum request file | `df52d78f2bcd3a89e9589ea68d645df02841a2f9017394d14c833cb7580b36cc` |
| Audio/playback request file | `4e28149921c9602c78f1e15633923b55eaf572993fce506651d6d474acf73035` |
| Candidate pointer file | `0fa9e0756ab59969dc55ab428544c18aad1d1d14631b0d2569a33823feb24518` |
| Candidate bundle | `36c1442b161fb3d8529678099b4df1c93b43fb2456a24260ac2942787b7f44f0` |
| Bundle manifest file | `2390974b9f48534665d474b9fe18290e28edc361aa3cc119481db70e44acfd40` |

## Counts and Roles

| Check | Result |
|---|---|
| Curriculum items | 139 total: 92 Hangul and 47 pronunciation. |
| Curriculum decisions | 557 total decisions; 563 total role assignments including P11-P13 specialist atomization. |
| Portuguese policy | One canonical `pt` policy decision remains `needs_review`; no regional policy is selected. |
| Media slots | 509 total slots, 325 required slots, 233 audio slots. |
| Audio/media decisions | 4403 total decisions across rights, integrity, spoken text, specialist playback, independent native playback, and heard playback. |
| Pending state | Every request status and nested decision status remains `needs_review`; `request_only=true`, `evidence_supplied=false`, `human_checkpoint_count=0`. |

## Task Results

### 31-22-01: Implement fixed request regeneration test-first

- RED: `tests/services/test_korean_foundation_ai_curation.py::test_regenerate_requests_fixed_operation_is_implemented` failed with `AssertionError` because `regenerate_korean_foundation_review_requests()` and `verify_korean_foundation_review_requests()` were absent.
- GREEN: added fixed request generation/verification functions, v2 candidate projection builders, request result model, safe fixed-path request writing, drift detection, symlink pointer rejection, and CLI operations `regenerate-requests` and `verify-requests`.
- Additional coverage verifies command allowlist, complete pending request output, candidate pointer drift before write, symlink pointer refusal, and request drift rejection.

### 31-22-02: Regenerate and verify exact v2 requests

- Ran `UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py regenerate-requests`; it returned `24c60fe9e5eb12035dac514b5fcb58a6bc0cbe410cb17cc309dea7fdce1f3b00`.
- Ran `UV_OFFLINE=1 uv run python scripts/build_korean_foundation_candidates.py verify-requests`; it returned the same hash.
- The two request files now bind `current-candidate.json`, `bundle-manifest.json`, `hangul-v2.json`, `pronunciation-i-plus-1-v2.json`, `korean-foundations-v2-curation.json`, and `korean-foundations-v2-media.json`.

## Verification Results

| Check | Result |
|---|---|
| Lifecycle preflight | `node .planning/bin/gsdd.mjs lifecycle-preflight execute 31 --expects-mutation phase-status` allowed execution with clean planning state. |
| Control map | `node .planning/bin/gsdd.mjs control-map --json` reported a clean worktree on `reconcile/monarch-20260818` at `5ba9dfb`. |
| Named RED | Failed with `AssertionError` before implementation. |
| Symlink RED | Failed as `ARTIFACT_INVALID` before hardening; after fix, symlink pointer returns `CANDIDATE_POINTER_INVALID`. |
| Fixed operation GREEN | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_ai_curation.py::test_regenerate_requests_fixed_operation_is_implemented -q` -> `1 passed`. |
| Request generation/drift tests | Three focused service tests for request output, pointer drift, and request drift passed. |
| Combined 31-22 suite | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_ai_curation.py tests/services/test_korean_foundation_review_requests.py -q` -> `43 passed`. |
| Real request flow | `test_requests_bind_complete_candidate_sets`, `regenerate-requests`, `verify-requests`, and full request suite passed. |
| Structural assertion pass | Verified exact v2 bindings, counts, pending-only status, no populated evidence/activation/export keys, and unchanged v1 file hashes. |
| Diff hygiene | `git diff --check` passed. |

## Boundaries Preserved

- No provider, network, LLM, TTS, Azure, database, or external source call occurred.
- Candidate bundle files, candidate pointer, and v1 source packs were not modified.
- No evidence, reviewer receipt, rights disposition, media artifact, playback result, active snapshot, activation, export, production readiness, or Anki acceptance was created or claimed.
- P11-P13 pronunciation records remain specialist-sensitive and unresolved; request files only enumerate required review decisions.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified RED/GREEN request operation, fixed CLI surface, v2 candidate binding, request hashes, decision/role counts, pending-only state, pointer symlink refusal, request drift detection, v1/candidate invariance, and diff hygiene.
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
  summary: Existing request files were stale v1 artifacts rather than absent; fixed regeneration replaced them with v2 current-candidate-bound requests.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Candidate pointer reads followed symlinks before this plan; the reader now refuses symlink/reparse/non-regular pointer paths before reading.
- class: factual_discovery
  impact: non_blocking
  disposition: deferred_to_later_phase31_scope
  summary: Evidence tests still reference older v1 request hashes and candidate filenames; evidence/receipt migration remains later Phase 31 work and was not expanded into this request-regeneration plan.
</deltas>

<judgment>
<active_constraints>
Continue to preserve immutable v1 source packs, exact current-candidate pointer binding, fixed request filenames, fixed evidence-filename selectors only, no arbitrary roots or repair flags, no provider/network calls, no authority-bearing approvals, and no canonical evidence/export mutation.
</active_constraints>
<unresolved_uncertainty>
Qualified Korean phonetics review, Portuguese policy, rights dispositions, exact media bytes, playback evidence, canonical receipt, inactive snapshot, activation authorization, local exports, and observed Anki acceptance remain unresolved later gates.
</unresolved_uncertainty>
<decision_posture>
Proceed to Plan 31-23 with the regenerated request files as complete pending reviewer inputs. Treat request hashes as binding selectors, not evidence or approval.
</decision_posture>
<anti_regression>
Do not regenerate requests from v1 source files, prose hashes, caller-provided paths, or stale bundle members; do not populate reviewer/evidence/media/activation/export fields; do not weaken pointer symlink refusal; do not update later evidence tests by approving or fabricating evidence.
</anti_regression>
</judgment>

## Self-Check: PASSED

- Required service primitives, script operations, tests, request files, summary, and planning handoff updates exist.
- Required structured sections occur in the summary: `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`.
- RED and GREEN verification paths passed as recorded.
- `31-CURRICULUM-REVIEW.md` and `31-AUDIO-PLAYBACK-REVIEW.md` bind exact v2 candidate members and remain pending-only.
- `ROADMAP.md` remains in-progress for Phase 31; no phase was marked complete by execution.
- No Git staging, commit, push, reset, restore, clean, stash, tag, or PR action occurred.

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 22*
*Completed: 2026-08-25*
