---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "29"
runtime: opencode
assurance: self_checked
---

# Phase 31: Hangul and Pronunciation i+1 - Plan 29 Summary

**Completed**: 2026-08-27
**Tasks**: 2
**Git Actions**: `d756ea1` added the launch safeguards, `e5725c9` fixed real shared-`/tmp` validation, and `21e433b` fixed linked-worktree protected-state verification.
**Deviations**: Three recoverable factual discoveries were fixed test-first: real `/tmp` mode includes the sticky bit; Git checkouts do not reproduce local non-executable permission bits; and linked worktrees initially fingerprinted their absent `.venv` instead of the canonical shared `.venv`.
**Decisions Made**: Protected rows bind path, kind, Git-reproducible executable mode, and bytes; every lane resolves the canonical integration root through the validated Git common directory for no-follow `.venv` fingerprinting.

## Completed Work

- Added no-follow repository `.venv` fingerprinting that records path/type/mode/link-target metadata and regular-file bytes without following or repairing links.
- Added fixed baseline, field-read, worktree-runtime, lane-recording, sealing, join, merge, and protected-state operations in `scripts/phase31_parallel_launch.py`.
- Bound baseline verification to an independently carried SHA-256 instead of trusting either diagnostic sidecar.
- Added canonical committed lane handoffs, strict handoff schema/identity validation, exact allowlisted patch hashes, and separately sealed lane heads.
- Required a real available Python 3.12 runtime and exact `PYTHONPATH=$PWD/src` for lane runtime checks.
- Prepared `/tmp/multilang-phase31-py312` with frozen offline dependencies under Python 3.12.3.
- Created immutable baseline `/tmp/multilang-phase31-parallel/baseline.json` and sidecar with private/read-only modes.
- Created clean exact worktrees `/tmp/multilang-phase31-ai` on `phase31-ai-lane` and `/tmp/multilang-phase31-media` on `phase31-media-lane`.

## Baseline Handoff

- The final baseline SHA-256 is intentionally carried only in executor state until both lane handoffs commit it; this tracked summary does not become a second digest authority.
- The final baseline commit/tree are the exact clean integration HEAD/tree after this summary and lifecycle state are committed.
- Runtime: `/tmp/multilang-phase31-py312/bin/python`, Python 3.12.3.
- State modes: baseline root `0700`; baseline and sidecar `0444`; runtime root `0700`.
- Both worktrees are clean at the exact baseline commit/tree and pass their lane-specific runtime checks.

## Verification

- Initial RED proved `scripts/phase31_parallel_launch.py` and `fingerprint_repository_venv` were absent before implementation.
- No-follow fingerprint RED/GREEN covered external link target mutation and deterministic absent state.
- Runtime/baseline RED/GREEN covered missing and non-3.12 runtimes, wrong `PYTHONPATH`, safe empty retry roots, symlinked handoff parents, and forged committed baseline trees.
- Live RED/GREEN covered sticky `1777` `/tmp`, Git-reproducible protected modes, and canonical `.venv` resolution from linked worktrees.
- Planned isolated verification: frozen/offline sync checked 198 packages and `/tmp/multilang-phase31-py312/bin/python -m pytest tests/services/test_phase31_runtime_isolation.py tests/services/test_phase31_parallel_launch.py -q` passed 30 tests.
- Python compilation and `git diff --check` passed.
- Final read-only second pass verified baseline, integration base, protected state, both lane runtimes, exact HEAD/tree equality, file modes, and Python 3.12.3.
- Repository `.venv` remained honestly `unsafe` with the same no-follow fingerprint; it was not repaired, followed, or mutated.

## Notes For Verification

- Claim only one clean common baseline, one fixed Python 3.12 environment, disjoint lane ownership, exact join provenance, and unchanged shared `.venv` fingerprinting.
- No provider, network, LLM, TTS, Azure, database, content review, rights decision, media generation, canonical receipt/snapshot/pointer, activation, or export operation occurred.
- The first failed baseline/worktree attempt was removed and recreated only after explicit user authorization; no lane changes existed in those worktrees.

## Notes For Next Work

- Carry the single `PHASE31_BASELINE_SHA256` value returned by the final `prepare-baseline` invocation independently into every 31-30 and 31-31 lane command; never reconstruct it from `/tmp` files or this summary.
- Run every lane command with `/tmp/multilang-phase31-py312/bin/python` and `PYTHONPATH="$PWD/src"` from its assigned worktree.
- Do not mutate integration HEAD, the external baseline, protected inputs, or the other lane's allowlist before 31-32 seals and joins both committed heads.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified TDD RED/GREEN cycles, frozen Python 3.12 runtime, exact baseline and worktree provenance, no-follow shared `.venv` behavior, protected-state invariance, disjoint allowlists, strict handoff validation, and final read-only second pass.
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
  summary: Real `/tmp` reports mode `1777`; the initial helper compared the full mode to `0777` while separately requiring sticky. A live preflight failure and regression test led to masked permission validation that still requires root ownership and sticky world-writable semantics.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Protected files created locally as `0600` and directories as `0700` check out as `0664` and `0775`, although Git content and executable semantics are identical. Protected rows now canonicalize only Git-reproducible executable mode while retaining fail-closed type/link/content checks.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: A helper launched from a linked lane initially fingerprinted that lane's absent `.venv`; it now validates `git-common-dir`, resolves the canonical integration worktree, and fingerprints the same unsafe shared `.venv` no-follow from every lane. The invalid first baseline/worktrees were recreated after explicit user authorization.
</deltas>

<judgment>
<active_constraints>
- The carried baseline digest is independent executor state and must not be reconstructed from either sidecar.
- AI and media lanes may write only their disjoint allowlists and must commit their canonical handoffs before sealing.
- Every command uses the fixed Python 3.12 runtime with the current worktree's `src` as `PYTHONPATH`.
- Repository `.venv`, candidates, protected evidence, media, pointer, exports, lockfile, and dependency metadata remain read-only.
</active_constraints>
<unresolved_uncertainty>
- AI linguistic consensus, rights/provider authority, exact media bytes, acoustic consensus, canonical activation, and local exports remain unresolved and belong to Plans 31-30 through 31-32.
- No live provider capability, credential, budget, legal right, linguistic verdict, or acoustic verdict was inferred by this launch plan.
</unresolved_uncertainty>
<decision_posture>
- Prefer exact committed provenance and independently carried digests over mutable adjacent files.
- Compare protected filesystem state using properties Git can reproduce while retaining descriptor/no-follow safety for links and bytes.
- Keep one serial launch baseline, then permit only the planned disjoint AI/media parallelism.
</decision_posture>
<anti_regression>
- Do not replace, chmod, regenerate, or repair the external baseline or repository `.venv` after lane launch.
- Do not accept a lane handoff with extra/missing/noncanonical fields, wrong baseline commit/tree/digest, invalid roots/totals, unallowlisted paths, or mismatched patch bytes.
- Do not seal dirty worktrees, replay different heads, trust lane-head sidecars as authority, or merge anything beyond the exact union of both sealed commits.
- Do not start provider/content/media work from a different commit, tree, runtime, or baseline digest.
</anti_regression>
</judgment>
