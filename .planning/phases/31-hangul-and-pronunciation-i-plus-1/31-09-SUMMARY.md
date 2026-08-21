---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "09"
subsystem: korean-foundation-snapshot-activation
runtime: opencode
assurance: self_checked
tags: [korean, immutable-snapshot, atomic-activation, sha256, filesystem-security, concurrency, tdd]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "08"
    provides: Fixed evidence schemas, complete semantic/media validation, exact receipt continuity, and the shared cross-process state lock
provides:
  - Validation-first immutable 527-member snapshot preparation with separate root and manifest-file hashes
  - A pathless prepared verifier proven read-only with lock, recovery, and every reachable write primitive poisoned
  - Five-hash activation authorization, atomic active-pointer v2 replacement, and exact active provenance
  - Backward-compatible one-resolution readers proven to observe complete old or new snapshots only
affects: [31-10, 31-11, 31-12, korean-foundation-cli, korean-foundation-export]
tech-stack:
  added: []
  patterns:
    - Shared lock then complete read-only validation then recovery/write
    - Non-self-referential member-root hash plus separate serialized-manifest hash
    - Read-only descriptor validation with final authority and prestate rereads
    - Secure same-filesystem staging and one atomic pointer document
key-files:
  created:
    - tests/helpers/korean_foundation_activation_worker.py
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-09-SUMMARY.md
  modified:
    - src/multilang/services/korean_foundation_snapshot.py
    - tests/services/test_korean_foundation_snapshot.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Keep preparation and activation pathless and serialize both with the exact Plan 31-08 state lock before any authority validation, recovery, or write."
  - "Use snapshot v2 for receipt/evidence/prestate provenance while retaining schema-v1 reading so concurrent transitions can safely expose either complete generation."
  - "Derive authorization from receipt, bundle, manifest-file, member-root, and active-prestate hashes; exact already-active retries verify provenance and perform no write or recovery."
patterns-established:
  - "Prepared verification independently reconstructs expected immutable state, reads it twice, and performs a final authority fingerprint after all snapshot reads without acquiring the state lock."
  - "Recovery accepts only prevalidated direct-child non-link .staging-* directories under the exact fixed snapshot root."
requirements-advanced: [KHAN-01, KHAN-02, KPRO-01, KPRO-02]
requirements-completed: []
duration: 71min
completed: 2026-08-06
---

# Phase 31 Plan 09: Immutable Korean Foundation Snapshot and Activation Summary

**A receipt-bound 527-member immutable snapshot can now be prepared, verified with every write path disabled, hash-authorized, atomically activated, and read concurrently as complete old-or-new state—all on private temporary roots.**

## Performance

- **Started:** 2026-08-06T00:26:11Z
- **Final summary self-check completed:** 2026-08-06T01:37:20Z
- **Duration:** 1h 11m
- **Tasks:** 2/2
- **Core implementation/test files:** 3
- **Planning artifacts updated/created:** 3, including this summary
- **Git actions:** None, as explicitly required by the user

## Accomplishments

- Added lock-first preparation that validates the receipt, complete inbox/index, canonical sources and requests, reviewers, rights, playback/media bytes, immutable target, active pointer, prestate, and stale-stage safety before recovery or filesystem creation.
- Built an exact 527-member snapshot: 5 typed source members, 13 receipt/index/candidate/request/review evidence members, and 509 media members, plus one canonical `snapshot-manifest.json`.
- Added separate `snapshot_root_sha256` and serialized `snapshot_manifest_sha256` identities; the manifest hash is not self-referential.
- Added a separate pathless prepared verifier that never locks, recovers, stages, fsyncs, replaces, or writes and succeeds while all reachable write and state-changing helpers are poisoned.
- Added a five-hash authorization digest and active-pointer v2 provenance binding receipt, bundle, manifest, root, prior active state, and authorization.
- Added atomic, idempotent activation and active-provenance verification with an exact no-write already-active branch.
- Preserved schema-v1 snapshot/pointer resolution and proved concurrent readers retain one complete old or new immutable generation per operation.
- Kept every canonical candidate, request, inbox, receipt, snapshot, pointer, and export path unchanged (`canonical_mutation_count=0`).

## Strict TDD Evidence

### Task 31-09-01: Immutable preparation and separately read-only prepared verification

- **RED:** The first focused run returned `25 failed, 20 deselected in 61.26s`; failures were the absent private path bundle, preparation API, immutable builder, authorization tuple, and prepared verifier.
- **GREEN:** The same focused command returned `25 passed, 20 deselected in 123.05s` after lock-first authority validation, exact snapshot construction, safe recovery, collision refusal, failure cleanup, and write-poisoned verification were implemented.
- **Security RED/GREEN:** An uncontained directory whose parent was merely named `snapshots` produced the expected failing containment test (`1 failed, 66 deselected in 0.35s`); exact-root recovery then passed with the success/order tests (`3 passed, 64 deselected in 11.74s`).
- **Verifier race RED/GREEN:** A pointer created after the verifier's second snapshot read initially escaped detection (`1 failed, 68 deselected in 7.21s`); a final full authority fingerprint made the focused verification pass (`2 passed, 67 deselected in 14.65s`).

### Task 31-09-02: Hash-authorized atomic activation and concurrent readers

- **RED:** The activation matrix returned `20 failed, 8 passed, 38 deselected in 117.00s`; all 20 new activation/provenance/crash/concurrency behaviors failed before implementation.
- **GREEN:** After implementing activation-state validation, pointer v2, atomic replacement, idempotence, provenance, and the private crash worker, the complete task filter returned `28 passed, 38 deselected in 150.75s`.
- **Provenance race RED/GREEN:** Mutation immediately after the final snapshot reread initially escaped the active report (`1 failed, 67 deselected in 9.25s`); a final pointer reread then passed with activation/idempotence coverage (`3 passed, 65 deselected in 27.85s`).
- **Concurrency harness:** The first green attempt had one private test-barrier timeout under continuous pre-validation reader load. Systematic tracing showed activation reached the barrier just after the 10-second harness deadline and then timed out waiting for release; starting the reader loop after the private pre-replace barrier retained the same old/new proof without production hooks and passed in `8.43s`.

No TDD commits were created because commits and staging were explicitly prohibited. RED/GREEN command evidence is recorded here instead.

## Fixed Contract Versions

| Contract | Version |
|---|---|
| Shared state lock | `phase31-korean-foundation-state-lock-v1` |
| Validation receipt | `phase31-korean-foundation-validation-receipt-v1` |
| Immutable snapshot | `phase31-korean-foundation-snapshot-v2` |
| Prepared verification | `phase31-korean-foundation-prepared-verification-v1` |
| Activation authorization | `phase31-korean-foundation-activation-authorization-v1` |
| Active pointer | `phase31-korean-foundation-active-pointer-v2` |

Snapshot schema v2 binds the receipt file/payload, confirmed index, evidence bundle, source/reviewer/rights/media evidence groups, active marker/prestate, exact member descriptors, and member-root hash. The separate manifest-file hash is SHA-256 over canonical serialized manifest bytes. Authorization is SHA-256 over the versioned tuple of receipt, bundle, manifest-file, member-root, and active-prestate hashes.

## Validation and Write-Order Matrix

| Operation | Before validation | Complete read-only validation | First allowed mutation |
|---|---|---|---|
| Prepare | Acquire Plan 31-08 lock only | Receipt/inbox/index/sources/requests/reviewers/rights/playback/media/target/pointer/prestate/stages | Recover exact contained stale stages, then create same-filesystem stage |
| Activate | Acquire Plan 31-08 lock only | All receipt authority plus immutable snapshot, authorization, current pointer, recorded/current prestate, and idempotence provenance | Recover exact contained stale stages, then create pointer temp |
| Verify prepared | Nothing state-changing; no lock | Full receipt authority, exact immutable tree, both hashes, complete tuple, prestate, then final tree and authority rereads | Never permitted |
| Verify active | Nothing state-changing; no lock | Receipt authority, immutable snapshot, exact pointer v2 provenance, final snapshot and pointer rereads | Never permitted |

Call-order evidence passed for both state-changing operations. Seven preparation drift classes and nine activation drift classes retained stale stages and every pre-call path byte/mtime unchanged.

## Immutable Snapshot and Hash Evidence

| Dimension | Exact fixture result |
|---|---:|
| Typed source members | 5 |
| Receipt/index/candidate/request/review evidence members | 13 |
| Exact media members | 509 |
| Manifest-declared members | 527 |
| Total immutable files including manifest | 528 |
| Snapshot targets overwritten on collision | 0 |

- Existing exact targets return without cleanup, directory touch, mtime update, or rewrite.
- Missing, changed, or extra same-name immutable state fails as `immutable_snapshot_collision`; it is never replaced.
- Preparation injected failures cover member copy, manifest write, staged hash validation, file/directory fsync, and final directory rename. Each leaves no partial immutable target or active-pointer change and removes only its own failed stage.
- Recovery leaves unrelated snapshot-root children untouched and rejects same-named but uncontained directories.

## Strictly Read-Only Prepared Verification

- Valid verification passed with high-level staging/activation/recovery helpers and low-level write/create opens, `mkdir`, `touch`, text/byte writes, temp creation, copy/move, `os.write`, chmod/fchmod, fsync, rename/replace, unlink/remove/rmdir/rmtree, and lock acquisition all poisoned to raise.
- Nine missing/altered receipt, source member, media member, manifest file, extra root member, tuple, root-hash, and active-prestate cases failed while their post-mutation trees stayed byte-identical.
- A dedicated race test proves active prestate is checked after the final immutable-tree reread.
- Source inspection confirms the prepared verifier calls neither prepare, activation, recovery, staging, atomic-pointer writing, nor lock acquisition.

## Authorization, Crash, Idempotence, and Reader Evidence

- Changing any one of the five authorization inputs changes the authorization SHA-256.
- Nine receipt/index/reviewer/rights/media/snapshot/manifest/authorization/prestate activation drifts fail before recovery or pointer-temp creation.
- Four injected pointer write/fsync/replace/parent-fsync failures leave a complete old or new pointer and no handled-failure temp file.
- The private subprocess helper exits with code `91` immediately before pointer replacement; the old pointer bytes remain exact and resolve successfully.
- Exact retries verify receipt to snapshot to pointer provenance, report `already_active`, retain stale stages, and perform no cleanup or pointer rewrite.
- The reader-loop proof observed exactly two internally consistent identities: the complete legacy old snapshot and the complete v2 new snapshot. No missing, malformed, or mixed member/root state was observed.
- The production resolver still reads the active pointer exactly once and retains one immutable snapshot for the operation.

## Final Verification Results

| Check | Exact result |
|---|---|
| Complete Plan 31-09 snapshot suite | `69 passed in 270.38s` |
| Required independent second pass | `47 passed, 22 deselected in 261.35s` |
| Plan 31-08 evidence regression | `37 passed in 73.34s` |
| Review/media/export regressions | `68 passed in 93.28s` |
| Complete Korean-named regression matrix | `441 passed in 481.65s` |
| Python compilation | Passed for service, test suite, and private worker |
| Format/trailing-whitespace scan | `format_scan=passed` |
| Public/path/provider/hook static scan | `second_pass_static_scan=passed` |
| Canonical candidate/request hash pins | All seven exact and unchanged |
| Canonical side-effect scan | `canonical_mutation_count=0` |
| Human checkpoint proof | `human_checkpoint_count=0` |
| Phase lifecycle | `phase-status 31 in_progress` returned `changed: false` |
| Reviewed planning fingerprint | `81c43d1629a9d8c31c4fa65142dfe5a170eb2fe69f2470e0297bcb0146cdfb34` |

`ruff` remains unavailable in the offline environment (`Failed to spawn: program not found`). Compilation, the 69-test service suite, 47-test second pass, 441-test Korean matrix, bounded format scan, and static security/canonical scan all passed.

## Canonical Integrity Evidence

The final scanner reconfirmed these exact existing SHA-256 pins:

| Canonical input | SHA-256 |
|---|---|
| `korean-concepts-v1.json` | `79e50d509d3dd732f7bcadc4568697747646af1f191fc0b59a8e94e0b6b18625` |
| `hangul-v1.json` | `80716d1f19672777ab2516f1c592066e5f443dc86a1d9e64785be1867ba079b1` |
| `pronunciation-i-plus-1-v1.json` | `6a2eb0b6a0a467de6074ffafc2fb674a674ea96c3c2187f339d1c278aa8f55ec` |
| `korean-foundations-v1-curation.json` | `6c422c5c5edf581af39f91773b40f72ac5570b84b76cd38d6f18bea4ef190c00` |
| `korean-foundations-v1-media.json` | `9f53766ea174c963e4904dd6172e490079ad693aded8dcb025a952327c90f0e1` |
| `31-CURRICULUM-REVIEW.md` | `788aea87abb9d710617b86d8e05878151184d9ec92e4d3f0e013747c3655ae57` |
| `31-AUDIO-PLAYBACK-REVIEW.md` | `867aeb8e2fc79257aa1f55661f2e59f644062cedacbe55f42a65cc2f7cc424c9` |

> **2026-08-18 Quick 056 correction:** This table supersedes stale pre-final-serialization byte pins. It changes deterministic byte bindings only; canonical content hashes, request-only/pending state, and the absence of evidence, activation, export, or approval remain unchanged.

The canonical evidence inbox still contains only `README.md`. The canonical receipt, snapshot tree, active pointer, and Korean foundation export root remain absent.

## Files Created/Modified

### Created

- `tests/helpers/korean_foundation_activation_worker.py` - private argv-only temporary-root worker that terminates immediately before replacement by monkeypatching a private implementation primitive; it adds no production hook, environment control, or import surface.
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-09-SUMMARY.md` - exact execution, security, regression, and Plan 31-10 handoff evidence.

### Modified

- `src/multilang/services/korean_foundation_snapshot.py` - versioned immutable manifest/provenance models, validation-first preparation, safe recovery, write-free prepared verification, authorization digest, atomic activation, active provenance, and v1/v2 one-resolution reading.
- `tests/services/test_korean_foundation_snapshot.py` - 69 temporary-root contract, drift, poison, failure, crash, idempotence, provenance, and concurrency tests.
- `.planning/SPEC.md` - records Plan 31-09 complete and Plan 31-10 next while Phase 31 remains open.
- `.planning/.state-fingerprint.json` - reviewed planning-state baseline after the SPEC update.

No canonical candidate, request, inbox evidence, receipt, snapshot, pointer, export, CLI, provider, lock, or dependency file was modified.

## Decisions Made

- Kept all production state APIs fixed and pathless; tests replace one private frozen path bundle only.
- Retained schema-v1 manifest/pointer compatibility specifically so the one-resolution reader can cross an atomic v1-old to v2-new activation without mixed state.
- Copied the approved proposed curation/media bytes into typed content members while retaining the original pending candidate bytes under review evidence, preserving both reviewed output and its source authority.
- Made exact-target preparation and exact-active activation early no-write returns that occur before stale-stage recovery.
- Kept abrupt termination entirely in a private test helper; production has no environment flag, callback, barrier, CLI option, or public test hook.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Regression] Preserved schema-v1 bundle hashes after adding optional v2 fields**
- **Found during:** Task 31-09-02 RED activation/concurrent-reader run.
- **Issue:** Serializing newly added optional v2 fields as `null` changed legacy schema-v1 bundle hash recomputation and rejected a valid old snapshot.
- **Fix:** Excluded absent optional fields from bundle-hash material while retaining every required v2 field.
- **Files modified:** `src/multilang/services/korean_foundation_snapshot.py`.
- **Verification:** Legacy one-read resolver tests and the old/new concurrency test pass.
- **Committed in:** Not committed; Git delivery was explicitly disabled.

**2. [Rule 2 - Security] Bound recovery to the exact fixed snapshot root**
- **Found during:** Independent high-leverage recovery review.
- **Issue:** The first implementation checked only that a stale stage's parent basename was `snapshots`; a private forged stage under another same-named parent could be removed.
- **Fix:** Recovery now requires exact parent equality with the validated fixed snapshot root in addition to direct-child name, type, link/reparse, and inode/device checks.
- **Files modified:** `src/multilang/services/korean_foundation_snapshot.py`, `tests/services/test_korean_foundation_snapshot.py`.
- **Verification:** The dedicated RED/GREEN uncontained-stage test and complete 69-test suite pass.
- **Committed in:** Not committed; Git delivery was explicitly disabled.

**3. [Rule 1 - Race] Rejected active-pointer drift after the final provenance snapshot read**
- **Found during:** Independent high-leverage active-provenance review.
- **Issue:** A pointer changed immediately after the second immutable-tree read could produce a stale successful provenance report.
- **Fix:** Re-read and compare the exact pointer/prestate after final snapshot validation.
- **Files modified:** `src/multilang/services/korean_foundation_snapshot.py`, `tests/services/test_korean_foundation_snapshot.py`.
- **Verification:** The dedicated RED/GREEN race test and activation/idempotence regressions pass.
- **Committed in:** Not committed; Git delivery was explicitly disabled.

**4. [Rule 1 - Race] Rechecked complete authority after the prepared verifier's final tree read**
- **Found during:** Independent high-leverage write-free verifier review.
- **Issue:** Active prestate could change after its first final reread but during the second immutable-tree read.
- **Fix:** Run the complete read-only authority fingerprint once more after the final snapshot validation.
- **Files modified:** `src/multilang/services/korean_foundation_snapshot.py`, `tests/services/test_korean_foundation_snapshot.py`.
- **Verification:** The dedicated RED/GREEN prestate-race test and all-write-primitives-poisoned verifier pass.
- **Committed in:** Not committed; Git delivery was explicitly disabled.

---

**Total deviations:** 4 auto-fixed (3 Rule 1 correctness/race regressions, 1 Rule 2 security hardening).
**Impact on plan:** Every fix directly enforces backward compatibility, exact containment, or final-reread race safety required by the approved threat model. No scope, public surface, provider, canonical state, or dependency was added.

## Issues Encountered

- The first concurrent-reader green run timed out in the private harness because continuous reader work delayed activation validation past a 10-second pre-replace deadline. Cause tracing showed no mixed state or production deadlock; sequencing the reader loop after the private pre-replace barrier made the boundary deterministic without adding a production hook.
- The first static public-surface scan treated required field name `snapshot_root_sha256` as a forbidden path/root argument. Narrowing the scanner to actual path-bearing parameter names produced `second_pass_static_scan=passed`; implementation was unchanged.
- `ruff` is not installed in the offline environment. Authoritative pytest, compilation, line-length, and trailing-whitespace checks passed.

## Security and Privacy Review

- Production APIs accept only lowercase SHA-256 values and expose no source, inbox, receipt, snapshot, pointer, URL, archive, APKG, hook, barrier, environment, or caller-owned object input.
- SHA-256 protects integrity and authorization binding; no MD5/SHA-1, password use, encryption claim, secret, dynamic code execution, pickle, shell command, remote fetch, or provider construction was introduced.
- All fixed and manifest-derived paths are bounded safe POSIX-relative allowlisted members. Reads lstat every component, reject symlinks/Windows reparse points and special files, open descriptors read-only with no-follow where supported, compare descriptor identity, and enforce byte limits.
- Stages and pointer temps use secure same-filesystem creation, restrictive permissions, exclusive member creation, file fsync, directory fsync where supported, and atomic rename/replace.
- State-changing operations use the shared artifact-free Plan 31-08 Windows mutex/POSIX directory lock. The lock is entered before hash/receipt validation and retained through recovery and atomic publication.
- Errors expose controlled reason codes only, never Korean text, reviewer notes, attribution, absolute temporary paths, source bytes, or credentials.
- All success, crash, failure, idempotence, and concurrency state lived under pytest `tmp_path`; the only process termination path is the private test helper.
- Threats T-31-09-01 through T-31-09-07 are covered. No endpoint, authentication path, schema boundary, network access, or other unregistered threat surface was introduced.

## Known Stubs

None. Fixture-only reviewers/media and temporary old/new snapshots are deliberate private test evidence, not production data or a public fallback. Genuine evidence and canonical state remain named later-plan gates rather than implementation stubs.

## Task Commits and Git Actions

None. No staging, commit, branch, push, PR, reset, restore, checkout, clean, stash, tag, or other destructive/delivery Git action was performed.

## Authentication Gates

None.

## User Setup Required

None. This plan performs no provider call, credential access, network request, media acquisition, or human checkpoint.

## State and Handoff to Plan 31-10

- `.planning/SPEC.md` records Plan 31-09 complete and Plan 31-10 next.
- `node .planning/bin/gsdd.mjs phase-status 31 in_progress` returned `changed: false`; Phase 31 remains open at `[-]`.
- The reviewed planning fingerprint is `81c43d1629a9d8c31c4fa65142dfe5a170eb2fe69f2470e0297bcb0146cdfb34`.
- KHAN-01, KHAN-02, KPRO-01, and KPRO-02 remain unchecked. This plan proves temporary-root state machinery, not genuine approvals or learner-ready production.
- The repository's authoritative GSDD handoff remains SPEC/ROADMAP/fingerprint based; the stale legacy `.planning/STATE.md` was not advanced or reconstructed.
- Plan 31-10 can route its exact fixed CLI directly to the five new public service functions and print the six receipt/bundle/manifest/root/prestate/authorization hashes already present in result models.
- Plan 31-10 should retain private constant injection, repeat write-poisoned `verify-prepared`, exercise all six temporary exports, run `uv lock --check`, and perform its required isolated Python 3.12 full-suite closure. This plan used the existing environment and does not claim that later Python 3.12/full-suite gate.
- Canonical receipt/snapshot/pointer/export state remains absent; no engineering blocker remains for Plan 31-10.

## Next Phase Readiness

- **Ready:** Exact pathless preparation, verification, activation, and provenance interfaces; scanner-stable result hashes; one shared lock; private temporary-root composition; private crash worker; and old/new-only readers.
- **Still blocked by design:** Real qualified reviewers, Portuguese policy, approved rights/media/playback evidence, canonical receipt/preparation/authorization/activation, production exports, and observed Anki acceptance.
- **Next:** Execute only `31-10-PLAN.md`; keep Phase 31 open and do not begin Plan 31-11's first human checkpoint until Plan 31-10's isolated Python 3.12 and full offline suite pass.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Strict TDD established 25 Task-1 RED failures and 20 Task-2 RED failures before implementation. The final 69-test service suite, 47-test independent second pass, 441-test Korean matrix, compilation, format scan, public-surface/security scan, exact seven-file hash pins, write-poisoned verifier, abrupt process termination, old/new reader proof, and zero canonical mutation all passed.
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
  summary: Optional v2 provenance fields had to be excluded when absent so schema-v1 bundle identities remain byte-compatible for old/new activation reads.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Stale-stage recovery required exact fixed-root parent equality rather than a basename-only containment check.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Active provenance required one final pointer reread after immutable-tree validation to reject a narrow concurrent drift window.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Prepared verification required one final complete authority fingerprint after its second snapshot read to close the last prestate drift window.
</deltas>

<judgment>
<active_constraints>
Preserve canonical `ko`, every candidate/request byte, the fixed direct-placement evidence boundary, the Plan 31-08 shared lock, pathless public state APIs, validation-before-recovery/write ordering, immutable snapshot identities, separate no-write prepared verification, and one-resolution active readers. Fixture authority remains temporary and cannot become production authority.
</active_constraints>
<unresolved_uncertainty>
Genuine qualified reviewer identities, Portuguese regional policy, source/attribution/license/reuse decisions, exact licensed media, heard playback, canonical receipt and snapshot creation, real authorization, canonical activation, all-format production exports, isolated Python 3.12 full-suite closure, and observed Anki acceptance remain unavailable or later-plan work.
</unresolved_uncertainty>
<decision_posture>
Prefer fixed pathless interfaces, exhaustive hash-bound authority, validation-first locked transitions, separately write-poisoned inspection, immutable complete generations, and atomic one-pointer publication over flexible paths, repair-on-read, caller-supplied objects, or test hooks in production.
</decision_posture>
<anti_regression>
Do not validate outside the shared lock before prepare/activation, recover stale state before complete authority validation, overwrite same-hash collisions, let prepared verification lock/write/recover, weaken the five-hash authorization tuple, rewrite exact active pointers, read the pointer more than once per learner operation, expose private fixture paths/hooks/env controls, copy fixtures into canonical state, or alter any candidate/request/inbox/export byte.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All six implementation, test-helper, summary, SPEC, and fingerprint artifacts exist at the required paths.
- The final service suite returned `69 passed`; the independent second pass returned `47 passed, 22 deselected`; the Korean regression matrix returned `441 passed`.
- Every recorded ROADMAP/SPEC/config source hash matches current bytes, and the aggregate planning fingerprint remains `81c43d1629a9d8c31c4fa65142dfe5a170eb2fe69f2470e0297bcb0146cdfb34`.
- Required structured execution sections each occur exactly once; summary and changed-file format/trailing-whitespace scans passed.
- Git's staged-file list is empty. No commit, staging, or destructive Git action occurred.
- Canonical candidates, requests, inbox, receipt, snapshots, pointer, and exports remain exact with `canonical_mutation_count=0`.
- Phase 31 remains open for Plan 31-10, and all four requirements remain unchecked.

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 09*
*Completed: 2026-08-06*
