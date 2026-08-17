---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "10"
subsystem: korean-foundation-cli-integration-precheckpoint
runtime: opencode
assurance: self_checked
tags: [korean, cli, typer, immutable-snapshot, anki-export, python312, offline-suite, no-provider]
requires:
  - phase: 31-hangul-and-pronunciation-i-plus-1
    plan: "09"
    provides: Pathless receipt-bound immutable snapshot preparation, write-free prepared verification, five-hash authorization, and atomic active provenance.
provides:
  - Locked pathless `korean-foundations` CLI command group with hash/enums-only authority and fixed six-artifact export inspection.
  - Complete private temporary evidence-to-receipt-to-snapshot-to-activation-to-export CLI integration proof.
  - Scanner-readable precheckpoint evidence for `uv lock --check`, approved-temp Python 3.12, full offline pytest, unchanged `.venv`, and zero canonical mutation.
affects: [31-11, 31-12, korean-foundation-evidence, korean-foundation-export, cli]
tech-stack:
  added: []
  patterns:
    - Fixed Typer command group wrapping fixed-root service functions without public source/root/path overrides.
    - Private test-only constant injection for temporary roots while production defaults fail closed.
    - Export readiness and inspection bound to active snapshot receipt/bundle/root hashes.
key-files:
  created:
    - tests/cli/test_korean_foundation_commands.py
    - tests/integration/test_korean_foundations_flow.py
    - .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-10-SUMMARY.md
  modified:
    - src/multilang/cli.py
    - src/multilang/services/korean_foundation_evidence.py
    - src/multilang/services/korean_foundation_export.py
    - src/multilang/services/korean_foundation_media.py
    - src/multilang/services/korean_foundation_snapshot.py
    - tests/services/test_korean_foundation_evidence.py
    - tests/services/test_korean_foundation_snapshot.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Keep the public Korean foundation workflow fixed and pathless except for the explicit export output destination."
  - "Treat Python 3.12 full-suite closure, unchanged shared `.venv`, and `canonical_mutation_count=0` as mandatory eligibility evidence before Plan 31-11."
  - "Make the write-poison helper platform-aware only for absent Windows `os.fchmod`, preserving all other poisoned write primitives."
patterns-established:
  - "CLI commands print scanner-stable aggregate keys only; no source text, local roots, reviewer notes, or private paths are exposed."
  - "Temporary integration can validate, prepare, verify with writes poisoned, activate, export all formats, inspect APKG/table artifacts, and still leave canonical state unchanged."
requirements-advanced: [KHAN-01, KHAN-02, KPRO-01, KPRO-02]
requirements-completed: []
duration: 28min continuation after checkpoint; earlier Task 31-10-01/02 work recorded in execution handoff
completed: 2026-08-17
---

# Phase 31 Plan 10: Korean Foundation CLI and Precheckpoint Regression Summary

**A locked pathless `korean-foundations` CLI now proves the full temporary foundation workflow and passes the complete offline isolated Python 3.12 suite without mutating canonical evidence/export state or the shared `.venv`.**

## Performance

- **Continuation started:** 2026-08-17T18:49:36Z after the user-authorized deviation checkpoint.
- **Completed:** 2026-08-17T19:17:06Z.
- **Continuation duration:** 28min, including one 16m22s isolated full-suite run and post-run invariance checks.
- **Tasks:** 3/3 complete; Task 31-10-03 completed in this continuation.
- **Human checkpoints consumed by the plan:** `human_checkpoint_count=0`; the only stop was an executor-requested deviation authorization before repair.
- **Git actions:** None. No staging, commit, push, reset, restore, clean, stash, tag, or PR action occurred.

## Locked Command Surface

The public command group is exactly:

```text
multilang korean-foundations inspect-inbox
multilang korean-foundations validate-and-write-receipt --confirmed-index-sha256 HASH
multilang korean-foundations check-receipt --expected-receipt-sha256 HASH
multilang korean-foundations prepare-snapshot --expected-receipt-sha256 HASH
multilang korean-foundations verify-prepared --expected-receipt-sha256 HASH
multilang korean-foundations activate --expected-receipt-sha256 HASH --authorization-sha256 HASH
multilang korean-foundations verify-active --expected-receipt-sha256 HASH
multilang korean-foundations check --family hangul|pronunciation
multilang korean-foundations export --family hangul|pronunciation --format apkg|csv|tsv --output PATH
multilang korean-foundations inspect-exports
```

- No command exposes source/inbox/receipt/snapshot/pointer roots, URLs, archives, import hooks, provider toggles, approval bypasses, or test hooks.
- `validate-and-write-receipt` is the sole public receipt writer and accepts only the confirmed evidence-index SHA-256.
- `verify-prepared` routes to the read-only verifier and has no repair/recover/create/force option.
- `inspect-exports` is fixed to `.multilang/exports/korean-foundations/` with exactly these six names: `hangul.apkg`, `hangul-csv/`, `hangul-tsv/`, `pronunciation-i-plus-1.apkg`, `pronunciation-i-plus-1-csv/`, and `pronunciation-i-plus-1-tsv/`.

## Accomplishments

- Added the fixed `korean-foundations` Typer subapp and scanner-stable aggregate output for inbox inspection, receipt continuity, snapshot preparation/verification, activation/provenance, readiness, export, and fixed export-set inspection.
- Proved production defaults fail closed with absent canonical evidence/pointer/export state and do not fall back to temporary candidates.
- Proved a complete private temporary CLI flow from evidence inspection through combined receipt write, receipt continuity, snapshot preparation, strictly read-only prepared verification, hash-authorized activation, active provenance, readiness, six exports, and fixed export-set inspection.
- Deep-inspected temporary APKG ZIP/media/SQLite plus CSV/TSV rows, media references, checksum bundles, IDs, GUIDs, and receipt/snapshot/root bindings.
- Kept all canonical Korean foundation candidates, review artifacts, inbox, receipt, snapshot tree, active pointer, and production export root byte-identical or absent as before.
- Closed the mandatory precheckpoint gate with `uv lock --check`, approved-temp Python 3.12, frozen offline sync, exact Python 3.12.13 probe, and the complete offline pytest suite in the isolated environment.

## Temporary Integration and Export Hash Evidence

The deterministic private temporary integration emitted these hashes during the final hash-capture rerun:

| Key | SHA-256 |
|---|---|
| integration_receipt_sha256 | `5a450deb06aa272f482593069974d1a593e8bd8aabfc676b233e508599ee5acf` |
| integration_bundle_sha256 | `cc3e2ef53b65c91e70126389d1e029c1c5106f3b1b3f85a365f7b9f2e1c2c260` |
| integration_snapshot_manifest_sha256 | `0cb098f023cf901e35bdb092ef0992bf4f4416af15c25b272e6c06170e462436` |
| integration_snapshot_root_sha256 | `8b1f0ab3a3cdd256c1278b86e95b10a54ab3689ccfaf6c70ea5bec1e945f7c9b` |
| integration_authorization_sha256 | `4778181c57ccee15026d73f46a2d76ba929b83403b94ff77a771a35ed3f7dfae` |
| hangul_apkg_sha256 | `105b8519482caaad521336061991e9e4385640ffa5a8fd2567bd573540e6ce45` |
| hangul_csv_sha256 | `6b5ca94f22e52b460a0b4991eb84e428c48b06cd03f23a7e2f3234b7f2d0f252` |
| hangul_tsv_sha256 | `43816488c1e006fb0447813db8445ca5b77b8574e4b3bf308d7d78b67bfa04bc` |
| pronunciation_apkg_sha256 | `c45965b6645c4b53626d3eb44e76fdf32c5506668d02dfd32682201d67498fdd` |
| pronunciation_csv_sha256 | `9f11d6932dde204eeb64b01c717446c8133e2c9f89c3216b691e01d6548d1fbc` |
| pronunciation_tsv_sha256 | `0fcf801f55b21b0b4c53b5c2946f799e9163f44b74cda2a74fdfb4f4ac6903ca` |

These are private `tmp_path` artifacts only. They are not canonical evidence, canonical receipts, canonical snapshots, active production pointers, or production exports.

## Write-Poisoned Prepared Verification

- `verify-prepared` succeeded in the full temporary CLI flow with write/recovery/lock primitives poisoned and returned the exact prepared tuple plus `prepared_status=verified`.
- The final focused snapshot suite returned `69 passed in 323.26s` after the approved Windows Python 3.12 poison-helper fix.
- The helper now skips poisoning `os.fchmod` only when the runtime lacks that attribute; all other reachable write/recovery primitives remain poisoned.
- Missing/altered prepared members, media, manifest/root hash, tuple, and active-prestate cases remain zero-write failures.

## Final Verification Results

| Check | Exact result |
|---|---|
| CLI command/refusal suite | `58 passed` |
| Temporary integration + CLI suite | `78 passed` |
| Existing-mode focused regression matrix | `110 passed` |
| Snapshot suite after authorized deviation | `69 passed in 323.26s` |
| Hash-capture temporary flow rerun | `1 passed in 56.41s` |
| Lock consistency | `uv lock --check` -> `Resolved 200 packages in 21ms` |
| Approved-temp sync/probe | `Checked 200 packages in 114ms`; Python `3.12.13 (main, May 10 2026, 19:35:37) [MSC v.1944 64 bit (AMD64)]` |
| Complete isolated offline suite | `1646 passed, 16 warnings in 982.57s (0:16:22)` |
| Shared `.venv` hash before/after | `dafc2dad80a8701545bdfff3ca792c21d9578664b6d4d75f9a1d9210363596ff` -> unchanged |
| Canonical-state hash before/after | `aa6ee79bd159d6a4c7c6b9eeef65893b1e0c9822c2fae1b1a8d13ae4ebff7d62` -> unchanged |
| Canonical mutation count | `canonical_mutation_count=0` |
| Human checkpoint count | `human_checkpoint_count=0` |
| Planning phase status helper | `phase-status 31 in_progress` returned `changed: false`; Phase 31 remains open |
| Reviewed planning fingerprint | `91b1e06756ff897c9a942f5f234c0e643c607b0eefada2109b9bda315bc697da` |

The isolated environment path was `C:/Users/MIGUEL~1.RAF/AppData/Local/Temp/opencode/multilang-phase31-precheckpoint-py312`. Containment checks confirmed the approved parent/child had no symlink or Windows reparse component.

## Files Created/Modified

### Created

- `tests/cli/test_korean_foundation_commands.py` - fixed CLI signature, option allowlist, refusal, redaction, no-construction, and existing-command regression coverage.
- `tests/integration/test_korean_foundations_flow.py` - private full-flow CLI integration, drift/refusal, write-poisoned prepared verification, activation, six-export, APKG/table inspection, and canonical hash proof.
- `.planning/phases/31-hangul-and-pronunciation-i-plus-1/31-10-SUMMARY.md` - this execution and precheckpoint closure record.

### Modified

- `src/multilang/cli.py` - fixed `korean-foundations` command group and aggregate output surface.
- `src/multilang/services/korean_foundation_evidence.py` - transient non-serialized receipt write status for `written|already_current` output.
- `src/multilang/services/korean_foundation_export.py` - schema-v2 review binding/export readiness fixes for active snapshot exports.
- `src/multilang/services/korean_foundation_media.py` - approved-media readiness validation now covers all approved media.
- `src/multilang/services/korean_foundation_snapshot.py` - prepared media relpath copy semantics for manifest storage paths.
- `tests/services/test_korean_foundation_evidence.py` - private export-ready fixture seam.
- `tests/services/test_korean_foundation_snapshot.py` - recursive media-drift mutators and the authorized platform-aware `os.fchmod` poison guard.
- `.planning/SPEC.md` - Plan 31-10 complete and Plan 31-11 next while Phase 31 remains open.
- `.planning/.state-fingerprint.json` - reviewed planning-state fingerprint after SPEC/ROADMAP/config review.

`node .planning/bin/gsdd.mjs phase-status 31 in_progress` reported `changed: false`; no additional ROADMAP mutation was made by this continuation.

## Decisions Made

- Keep all canonical state commands pathless and hash-bound; only `export --output` accepts a filesystem destination.
- Preserve private temporary-root composition as a test seam only; no public CLI path/source override was added.
- Treat the complete isolated Python 3.12 offline suite as the Plan 31-11 eligibility gate.
- Treat Windows Python 3.12's missing `os.fchmod` as a test-harness platform fact, not a production behavior change.

## Deviations from Plan

### User-Authorized Issues

**1. [Rule 3 - Blocking Test Harness] Made the write-poison helper platform-aware for Windows Python 3.12**
- **Found during:** Task 31-10-03 complete isolated Python 3.12 full-suite gate.
- **Issue:** The suite failed with `20 failed, 1626 passed` because `tests/services/test_korean_foundation_snapshot.py::_poison_snapshot_write_primitives` unconditionally monkeypatched `os.fchmod`, which does not exist in the Windows Python 3.12 runtime.
- **Fix:** Poison `os.fchmod` only when `api.os` exposes that attribute; leave every other write/recovery/lock primitive poisoned.
- **Files modified:** `tests/services/test_korean_foundation_snapshot.py`.
- **Verification:** `69 passed in 323.26s`; complete isolated Python 3.12 suite `1646 passed, 16 warnings in 982.57s`; `.venv` and canonical hashes remained unchanged.
- **Committed in:** Not committed; Git delivery was explicitly disabled by the user.

---

**Total deviations:** 1 user-authorized blocking test-harness fix.
**Impact on plan:** The fix is limited to platform compatibility for the read-only verification poison harness. It does not alter production behavior, command surface, canonical state, dependencies, lockfiles, providers, or export output.

## Issues Encountered

- The first isolated Python 3.12 full-suite attempt failed before planned assertions in every affected poison-helper use because `os.fchmod` was absent. After authorization, the exact platform guard resolved the blocker.
- The full isolated suite completed with 16 warnings from third-party/runtime deprecations: one `dateparser` UTC deprecation and 15 Alembic path-separator deprecations. They are unrelated to Plan 31-10 changes and did not fail the gate.

## Security and Privacy Review

- The plan's registered CLI, fixture-isolation, activation/export, prepared-verifier, and isolated-runtime threat surfaces were covered by tests and closure checks.
- No new endpoint, authentication path, database boundary, provider call, network request, frequency service, Kiwi construction, source URL/path override, import hook, or public test hook was introduced.
- Exact-path stub scan for Plan 31-10 files returned `stub_scan=passed`.
- Threat-surface scan found only expected forbidden-string/socket-poison coverage in tests and pre-existing unrelated CLI text; no unregistered production threat flag was introduced.

## Known Stubs

None. Temporary fixtures are deliberate private test authority and are not production fallbacks. Real evidence, canonical receipt/snapshot activation, production exports, and observed Anki acceptance remain later-plan gates.

## Authentication Gates

None. No provider credential, network login, secret, or external service was required.

## Task Commits and Git Actions

None. The user explicitly prohibited commit, staging, push, reset, clean, and related Git delivery actions for this continuation. The outer orchestrator will handle review and any separate commit request.

## State and Handoff to Plan 31-11

- `.planning/SPEC.md` now records Plan 31-10 complete, Phase 31 still open, and Plan 31-11 next.
- `.planning/.state-fingerprint.json` was rebaselined to `91b1e06756ff897c9a942f5f234c0e643c607b0eefada2109b9bda315bc697da` after SPEC/ROADMAP/config review.
- The legacy `.planning/STATE.md` remains stale by project convention; current GSDD handoff remains SPEC/ROADMAP/fingerprint based.
- KHAN-01, KHAN-02, KPRO-01, and KPRO-02 remain unchecked because this plan proves machinery and regressions, not genuine approved production evidence.

## Plan 31-11 Checkpoint Eligibility

Established: **yes**.

Plan 31-11 may begin because the fixed CLI, private temporary workflow, write-poisoned prepared verification, six-export inspection, lock check, approved-temp Python 3.12 probe, complete offline full suite, unchanged `.venv`, `canonical_mutation_count=0`, and `human_checkpoint_count=0` all passed. Plan 31-11 remains a human checkpoint for genuine evidence preparation only; it must not activate or export production state.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified the authorized Python 3.12 test-harness deviation with the focused snapshot suite, the exact isolated full offline pytest suite, lock check, approved-temp containment, `.venv`/canonical hash invariance, hash-capture integration rerun, stub/threat scans, and planning fingerprint update. No Git delivery action occurred.
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
  disposition: proceeded_after_user_authorization
  summary: Windows Python 3.12 lacks `os.fchmod`, so the write-poison test helper must skip only that poison when the runtime does not provide it.
</deltas>

<judgment>
<active_constraints>
Preserve canonical `ko`, fixed pathless Korean foundation commands, hash/enums-only authority, no public source/root/path overrides except export `--output`, no provider/network/DB/frequency/Kiwi construction in foundation commands, validation-before-write ordering, write-free prepared verification, unchanged shared `.venv`, and zero canonical evidence/export mutation until the explicit Plan 31-11/31-12 gates.
</active_constraints>
<unresolved_uncertainty>
Genuine qualified reviewer identities, Portuguese regional policy, source/attribution/license/reuse decisions, exact licensed media, heard playback, canonical receipt and inactive snapshot creation, human authorization, active production pointer replacement, production exports, and observed Anki acceptance remain unavailable or later-plan work.
</unresolved_uncertainty>
<decision_posture>
Proceed to Plan 31-11 only as the first human checkpoint for canonical inbox validation and inactive snapshot preparation. Do not reinterpret temporary fixture success as production approval, activation, export readiness, or Anki acceptance.
</decision_posture>
<anti_regression>
Do not add arbitrary evidence/snapshot/export roots, source URLs, APKG import paths, provider toggles, approval bypasses, test hooks, aliases, repair-on-verify behavior, broad exception fallbacks, dependency updates, shared `.venv` mutation, canonical fixture copying, or any CLI output that reveals local paths, source text, reviewer notes, or secrets.
</anti_regression>
</judgment>

## Self-Check: PASSED

- Required summary, source, service, test, SPEC, and fingerprint files exist.
- Required structured sections occur in the summary: `<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`.
- Summary records the exact isolated full-suite result, reviewed planning fingerprint, `canonical_mutation_count=0`, `human_checkpoint_count=0`, `.venv` invariance, and Plan 31-11 checkpoint eligibility.
- `git diff --check` passed for the summary, SPEC, fingerprint, and authorized test-helper change; only expected CRLF conversion warnings were reported for existing planning files.
- No Git staging, commit, push, reset, restore, clean, stash, tag, or PR action occurred.

---

*Phase: 31-hangul-and-pronunciation-i-plus-1*
*Plan: 10*
*Completed: 2026-08-17*
