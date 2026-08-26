---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "23"
runtime: opencode
assurance: self_checked
---

# Phase 31: Hangul and Pronunciation i+1 - Plan 23 Summary

**Completed**: 2026-08-25
**Tasks**: 2
**Git Actions**: None.
**Deviations**: The worktree was already dirty with uncommitted Plan 31-22 and completed 31-23-01 changes when 31-23-02 resumed; execution stayed scoped to the planned review/media files and planning handoff artifacts.
**Decisions Made**: First-group Korean foundation production defaults now resolve the exact `current-candidate` bundle. Historical v1 curation/media loading is explicit only and does not influence defaults.
**Notes for Verification**: The migrated defaults remain candidate-only and cannot satisfy review or media readiness. Request files are still pending reviewer inputs from Plan 31-22, not evidence or approval.
**Notes for Next Work**: Plan 31-24 must migrate evidence/snapshot/export consumers without fabricating evidence, reviewer receipts, rights dispositions, playback observations, activation, exports, or Anki acceptance.

## Bundle And Hashes

| Item | Hash |
|---|---|
| Candidate pointer file | `0fa9e0756ab59969dc55ab428544c18aad1d1d14631b0d2569a33823feb24518` |
| Candidate bundle | `36c1442b161fb3d8529678099b4df1c93b43fb2456a24260ac2942787b7f44f0` |
| Bundle manifest file | `2390974b9f48534665d474b9fe18290e28edc361aa3cc119481db70e44acfd40` |
| Registry content | `89a520055cfd94eb086c9ed3e937499a71fbcb07c056e1916b645c3bd312d89d` |
| `hangul-v2.json` file | `63c36c50c0efa61f7ba76ebdf92ff174f79aadedb63b46d15da01599f2594f59` |
| `hangul-v2` content | `15143e23dea2236b0ada6f3603f79babb52bc4a89213906084d16c8bf864843a` |
| `pronunciation-i-plus-1-v2.json` file | `cdac65b7e3a9615e62f187dcf7c7f6c543a480710b618ce0c9eb580281cd955c` |
| `pronunciation-i-plus-1-v2` content | `4cb7f0b2a453a61858bf6a4b15a95568328a7348ba164d6ef9fd2bdf68119682` |
| `korean-foundations-v2-curation.json` file | `faa233cdc67f99c28c3f203e1b206f4ad4f631bc34b8e2fbb970db336f1157db` |
| `korean-foundations-v2-curation` content | `08874c6f4c64240d79cbdb982c1aa0d8a886749bc8100da41036b7c1b8ba9b22` |
| `korean-foundations-v2-media.json` file | `e21c7a11006cf70a0559ec7fff7279b466097cf3bbc1fa092cee84e7b963e938` |
| `korean-foundations-v2-media` content | `8d860b5e41738d2322dc63eb220eb23de66f4b68b4ff1f9e3dd8979e90b5b55a` |
| Curriculum request file | `df52d78f2bcd3a89e9589ea68d645df02841a2f9017394d14c833cb7580b36cc` |
| Audio/playback request file | `4e28149921c9602c78f1e15633923b55eaf572993fce506651d6d474acf73035` |

## Counts And Gates

| Check | Result |
|---|---|
| Curriculum records | 139 total: 92 Hangul and 47 pronunciation. |
| Review records | 139 total, all `candidate_only=true`. |
| Review gates | 973 total, all `needs_review`, no reviewer metadata or evidence hashes. |
| Media slots | 509 total: 368 Hangul and 141 pronunciation. |
| Required media slots | 325 required; no artifact hashes or review receipts in the pending manifest. |
| Audio slots | 233 total audio-family slots remain pending. |
| Readiness | Review and media readiness both fail closed with `candidate_manifest_not_active`; learner-ready review records remain `0`. |
| History | Explicit v1 curation/media loaders return `korean-foundations-v1-curation` and `korean-foundations-v1-media` without changing defaults. |

## Task Results

### 31-23-01: Migrate domain and curriculum resolution to exact v2 test-first

- RED: `tests/services/test_korean_curriculum.py::test_curriculum_defaults_to_atomic_v2_candidate_bundle` failed before implementation because defaults still resolved v1.
- GREEN: added `KOREAN_FOUNDATION_DEFAULT_SOURCE`, `KOREAN_FOUNDATION_HISTORY_SOURCE`, `KoreanFoundationSourceBundle`, exact current-candidate loading, and explicit v1 history loaders.
- Verification: `UV_OFFLINE=1 uv run --extra dev pytest tests/domain/test_korean.py tests/services/test_korean_curriculum.py -q` -> `225 passed`.

### 31-23-02: Migrate review and media projections without widening authority

- RED: `tests/services/test_korean_foundation_review.py::test_review_and_media_default_to_exact_v2_bundle_with_all_gates_pending` failed with an assertion because review/media default path constants still pointed at v1 files instead of `current-candidate`.
- GREEN: review and media defaults now resolve the same current-candidate bundle root, verify exact member file hashes, parse only exact v1/v2 manifest-version tuples, reject mixed source versions, and expose explicit v1 history loaders.
- Additional coverage updates keep drift tests meaningful under v2 defaults and assert v1 media history remains loadable without mutating the current-candidate pointer or active snapshot pointer.

## Verification Results

| Check | Result |
|---|---|
| Lifecycle preflight | `node .planning/bin/gsdd.mjs lifecycle-preflight execute 31 --expects-mutation phase-status` allowed execution with a canonical-dirty warning from known uncommitted prior work. |
| Control map | `node .planning/bin/gsdd.mjs control-map --json` reported branch `reconcile/monarch-20260818`, no blockers, and known dirty Plan 31-22/31-23 files. |
| Named RED | Passed the harness expectation: the new named test failed with an assertion before production-code changes. |
| Named GREEN | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_review.py::test_review_and_media_default_to_exact_v2_bundle_with_all_gates_pending -q` -> `1 passed`. |
| Review/media suites | `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_review.py tests/services/test_korean_foundation_media.py -q` -> `24 passed`. |
| First-group suites | `UV_OFFLINE=1 uv run --extra dev pytest tests/domain/test_korean.py tests/services/test_korean_curriculum.py tests/services/test_korean_foundation_review.py tests/services/test_korean_foundation_media.py -q` -> `249 passed`. |
| Diff hygiene | `git diff --check` passed. |
| Source asset mutation | `data/korean_foundations` remained unmodified by Plan 31-23; no active pointer, media artifact, snapshot, evidence, or export file was created. |

## Boundaries Preserved

- No provider, network, LLM, TTS, Azure, database, or external source call occurred.
- No qualified-human review, Portuguese policy, rights disposition, licensed media, playback evidence, receipt, activation, export, production readiness, or Anki acceptance was created or claimed.
- Current defaults use one exact v2 candidate bundle; v1 history is explicit and opt-in only.
- Curation/media manifests remain `candidate_only=true`, every gate/slot remains `needs_review`, and readiness remains false.
- Evidence/snapshot/export consumer migration remains deferred to Plan 31-24.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified RED/GREEN behavior, one v2 bundle root across curriculum/review/media defaults, exact member/request hashes, 92/47 source counts, 139 curation records, 973 pending review gates, 509 media slots, explicit v1-history loading, candidate-only readiness refusal, no data source mutation, and diff hygiene.
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
  summary: Execution resumed with a canonical-dirty worktree from known uncommitted Plan 31-22 and 31-23-01 changes; edits stayed scoped to the active plan files and required planning handoff artifacts.
</deltas>

<judgment>
<active_constraints>
Continue to preserve exact current-candidate bundle defaults, immutable explicit v1 history, pending-only curation/media state, false readiness, no provider/network calls, and no authority-bearing evidence or export mutation.
</active_constraints>
<unresolved_uncertainty>
Evidence/snapshot/export consumers still need v2 migration. Qualified Korean phonetics review, Portuguese policy, rights dispositions, exact media bytes, playback evidence, canonical receipt, inactive snapshot, activation authorization, local exports, and observed Anki acceptance remain unresolved later gates.
</unresolved_uncertainty>
<decision_posture>
Treat v2 current-candidate curation and media manifests as complete pending projections for review only. Do not infer approval from their exact hashes or from service-level loadability.
</decision_posture>
<anti_regression>
Do not restore v1 as a default, do not read curation/media from independent latest-version files, do not allow mixed v1/v2 source identities, do not populate review/media approval metadata, do not turn candidate manifests into active production snapshots, and do not update deferred evidence tests by fabricating evidence.
</anti_regression>
</judgment>

## Self-Check: PASSED

- Required service defaults, explicit v1-history loaders, tests, planning updates, and summary exist.
- Required structured sections occur in the summary: `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`.
- RED and GREEN verification paths passed as recorded.
- `.planning/SPEC.md` and `.planning/ROADMAP.md` were updated; `node .planning/bin/gsdd.mjs phase-status 31 in_progress` left Phase 31 open; `node .planning/bin/gsdd.mjs session-fingerprint write` wrote fingerprint `940452d6756c89db9d75c0a4a5dbc6d7009dfa31f67ffa48374650fbb45430ef`.
- No Git staging, commit, push, reset, restore, clean, stash, tag, or PR action occurred.

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 23*
*Completed: 2026-08-25*
