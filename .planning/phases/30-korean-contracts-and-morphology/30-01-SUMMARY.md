---
phase: 30-korean-contracts-and-morphology
plan: "01"
subsystem: language-contracts
runtime: opencode
assurance: self_checked
tags: [korean, kiwi, pydantic, uv, frequency-assets, licensing]
requires: []
provides:
  - Exact direct and locked Kiwi analyzer/model dependencies
  - Canonical Korean `ko` request and settings selectability
  - Separate approved committed frequency-asset capability
  - Pre-write Korean frequency licensing gate
affects: [30-02, 30-03, 30-04, 30-05, 30-06, 30-07, 30-08]
tech-stack:
  added: [kiwipiepy==0.23.2, kiwipiepy-model==0.23.0]
  patterns:
    - Selectable languages are distinct from approved committed frequency assets
    - Explicit Korean asset operations fail before filesystem or word-list access
key-files:
  created:
    - tests/services/test_korean_language_support.py
  modified:
    - pyproject.toml
    - uv.lock
    - src/multilang/domain/jobs.py
    - src/multilang/settings.py
    - scripts/build_frequency_assets.py
    - tests/domain/test_jobs.py
    - tests/test_settings.py
    - tests/services/test_frequency_decks.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Use `ko` as the sole request/settings Korean identity; reject `ko-KR`."
  - "Keep Korean selectable while excluding it from approved committed frequency-asset iteration."
  - "Block explicit Korean build/check operations before any filesystem or wordfreq side effect."
patterns-established:
  - "Capability split: DEFAULT_SUPPORTED_LANGUAGES is selectable; APPROVED_FREQUENCY_ASSET_LANGUAGES controls committed assets."
  - "License gate: `_language_codes` rejects explicit `ko` before build/check dispatch."
requirements-completed: [KMODE-01, KMODE-02, KNLP-01]
duration: 13m23s
completed: 2026-08-04
---

# Phase 30: Korean Contracts and Morphology - Plan 01 Summary

**Exact Kiwi code/model pins, canonical `ko` selectability, and a no-write Korean frequency licensing gate now form the foundation for later morphology work.**

## Performance

- **Duration:** 13m23s
- **Started:** 2026-08-04T17:11:18Z
- **Completed:** 2026-08-04T17:24:41Z
- **Tasks:** 3/3
- **Repository files created/modified by this execution:** 12
- **Assurance:** `self_checked` (same-runtime OpenCode execution and checks)

## Accomplishments

- Added direct exact requirements and lock entries for `kiwipiepy==0.23.2` and `kiwipiepy-model==0.23.0`, with real Python 3.12 module/distribution version proof.
- Registered `SupportedLanguage.KO = "ko"` and one selectable settings entry while preserving every existing language and source type.
- Introduced `APPROVED_FREQUENCY_ASSET_LANGUAGES`, retaining all previously shipped asset languages and excluding Korean.
- Made build/check-all use only approved committed assets and made explicit Korean build/check requests fail with a deterministic, content-free error before directory creation, wordfreq iteration, loading, or CSV writes.
- Preserved the licensing boundary: no `assets/frequency/ko` directory or Korean frequency file was created.

## TDD Task Evidence

### Task 30-01-01: Lock the exact Kiwi analyzer and model distributions

- **RED:** `uv run --python 3.12 pytest tests/services/test_korean_language_support.py -q` reached the intended dependency assertion: **1 failed in 0.28s** because `kiwipiepy==0.23.2` was absent.
- **GREEN:** After `uv add "kiwipiepy==0.23.2" "kiwipiepy-model==0.23.0"`, the initial focused result was **1 passed in 0.08s**.
- **REFACTOR:** No implementation refactor was needed; later additions kept the same dependency contract green.
- **Final:** The expanded file passed under asserted Python 3.12: **5 passed in 0.68s**. `uv lock --check` resolved **200 packages in 1ms**, and the exact interpreter/module/distribution assertion exited 0.

### Task 30-01-02: Register canonical `ko` in requests and selectable settings

- **RED:** **8 failed, 32 passed in 0.41s** for missing `KO`, missing settings acceptance/default, and missing approved-asset capability.
- **GREEN:** Adding only `KO = "ko"`, one settings literal/default, and the approved-asset tuple produced **40 passed in 0.27s**.
- **REFACTOR:** No structural refactor was needed; defaults derive from the approved tuple plus one `ko` entry.
- **Final:** `uv run pytest tests/domain/test_jobs.py tests/test_settings.py tests/services/test_korean_language_support.py -q` produced **43 passed in 0.48s**.

### Task 30-01-03: Enforce the Korean frequency redistribution gate

- **RED:** After correcting the test harness import, build-all included Korean and direct operations reached side effects: **3 failed, 28 passed in 1.42s**.
- **GREEN:** Routing build/check-all through the approved tuple and guarding explicit `ko` before dispatch produced **31 passed in 1.39s**.
- **REFACTOR:** Test helper typing/formatting was cleaned up; **31 passed in 1.38s** remained green.
- **Final:** `uv run pytest tests/services/test_korean_language_support.py tests/services/test_frequency_decks.py -q` produced **31 passed in 1.35s**.

## Final Verification Results

| Check | Exact result |
|---|---|
| Mandarin execution-head preflight | All seven commands exited 0 at `HEAD` `240b21abb8efce5e028fd0b80d1767cbcac0f145` |
| Python 3.12 Korean support test | `5 passed in 0.68s` |
| Lock consistency | `Resolved 200 packages in 1ms` |
| Python/module/distribution version assertion | Exit 0 under Python 3.12 |
| Task 02 focused suite | `43 passed in 0.48s` |
| Task 03 focused suite | `31 passed in 1.35s` |
| Approved committed asset CLI check | `uv run python scripts/build_frequency_assets.py --check` exited 0 with no output |
| Korean asset absence | `assets/frequency/ko` does not exist; glob returned no files |
| Eager Kiwi source scan | No `kiwipiepy`, `kiwipiepy_model`, or `Kiwi(` occurrence under `src/` |
| Locale identity scan | `ko-KR` occurs only in the three rejection/non-membership tests changed by this plan |
| Patch hygiene | `git diff --check` exited 0; only line-ending conversion warnings were emitted |
| Staging check | No plan implementation file is staged |

The Python 3.12 commands used an OS-temporary uv project environment because the pre-existing Python 3.13 `.venv` executables were held open by editor language servers. This changed no repository path or contract. The final non-3.12 task commands ran exactly as listed after restoring the dev extra in the ordinary project environment.

## Files Created/Modified

- `pyproject.toml` - Declares both exact Kiwi runtime dependencies.
- `uv.lock` - Locks Kiwi analyzer/model distributions and hashes.
- `src/multilang/domain/jobs.py` - Adds canonical `SupportedLanguage.KO`.
- `src/multilang/settings.py` - Adds selectable `ko` and the separate approved-frequency capability tuple.
- `scripts/build_frequency_assets.py` - Uses approved-only all-language iteration and rejects explicit Korean operations before side effects.
- `tests/domain/test_jobs.py` - Covers all three Korean modern source types and locale rejection.
- `tests/test_settings.py` - Covers exact defaults, settings validation, and capability separation.
- `tests/services/test_korean_language_support.py` - Adds dependency, identity, approved-iteration, and no-write licensing contracts.
- `tests/services/test_frequency_decks.py` - Validates only the explicitly approved committed asset set.
- `.planning/SPEC.md` - Updates only Current State for the completed plan handoff.
- `.planning/.state-fingerprint.json` - Rebaselines reviewed planning state via the required helper.
- `.planning/phases/30-korean-contracts-and-morphology/30-01-SUMMARY.md` - Records execution evidence and handoff.

## Git Actions

None. Per the explicit user instruction, this execution did not stage, commit, push, create a branch/PR, amend, reset, stash, or clean. Pre-existing unrelated `ROADMAP.md`, planning-directory, and worktree content was preserved.

## Decisions Made

- Kept `DEFAULT_SUPPORTED_LANGUAGES` as the selectable capability and introduced `APPROVED_FREQUENCY_ASSET_LANGUAGES` as the committed-asset capability, avoiding any implication that Korean data redistribution is approved.
- Kept `ko-KR` out of enums, settings literals, defaults, and asset paths; this plan adds no provider locale constant.
- Used one shared content-free license error for explicit Korean build and check operations so private or caller-provided text cannot enter diagnostics.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking environment] Used an OS-temporary Python 3.12 uv environment**
- **Found during:** Task 30-01-01 RED.
- **Issue:** The pre-existing `.venv` was Python 3.13 and four editor language-server processes held its executables open, so uv could not replace its `Scripts` directory for the required Python 3.12 run. The fresh temporary environment also needed the existing `dev` extra before `pytest` was available.
- **Fix:** Left the editor processes and repository `.venv` intact, created a project environment under the OS temp area, synced the existing `dev` extra, and ran the required Python 3.12 RED/GREEN/version checks there. The ordinary environment later received the same existing `dev` extra for exact task commands.
- **Files modified:** No repository files beyond the planned dependency files.
- **Verification:** Python 3.12 focused test `5 passed`; exact import/version assertion exited 0.
- **Commit:** None by user instruction.

**2. [Rule 1 - Test harness bug] Corrected deterministic loading of the asset-builder script**
- **Found during:** Task 30-01-03 RED.
- **Issue:** Pytest resolved a conflicting `scripts` namespace, causing collection errors before the intended license-gate assertions ran.
- **Fix:** Loaded the confirmed repository script path with the existing `importlib.util.spec_from_file_location` test pattern.
- **Files modified:** `tests/services/test_korean_language_support.py`.
- **Verification:** Correct RED reached three behavioral failures; GREEN/final suite reached `31 passed`.
- **Commit:** None by user instruction.

**Total deviations:** 2 auto-fixed (1 blocking environment, 1 test harness bug).
**Impact on plan:** Both were local, recoverable, and necessary to obtain valid TDD evidence. No product scope or architecture changed.

## Issues Encountered

- Two preliminary RED attempts were invalid environmental/harness failures (locked `.venv`/missing `pytest`, then script namespace resolution). Neither was counted as the behavioral RED gate; execution continued only after the tests failed for the intended missing contracts.
- `uv` accessed its package registry/cache only to resolve and install the two plan-mandated dependencies and the existing dev extra. No application provider, TTS, translation, LLM, Tatoeba, or other product network call ran.

## Security and Boundary Review

- No Korean frequency asset or directory exists.
- Explicit Korean build/check rejects before `Path.mkdir`, `iter_wordlist`, loader access, or `_write_csv`.
- The license error is deterministic and does not interpolate user input, private text, paths, provider responses, or raw tokens.
- No new endpoint, auth path, schema change, provider integration, audio route, template, or export route was introduced.
- No production module imports or constructs Kiwi eagerly.

## Known Stubs

None. Stub-pattern scans found no TODO/FIXME/HACK/placeholder marker in the files changed by this plan.

## State and Handoff

- `.planning/SPEC.md` Current State records Plan 30-01 complete and Phase 30 still in progress.
- `.planning/ROADMAP.md` remains open (`[-]`) and was not modified by this execution.
- `node .planning/bin/gsdd.mjs session-fingerprint write` completed with fingerprint `5cb5fbd495cc0ebfde08c7acfba10c2fd9d8c617bf4ec6871223cd26c25be5ab`.
- No requirement checkbox was closed; Phase 30 verification and later plans remain outstanding.

## Next Plan Readiness

- Plan 30-02 may rely on exact local Kiwi imports and `SupportedLanguage.KO` without constructing Kiwi during non-Korean startup.
- The 3000-entry Korean frequency source, attribution, and redistribution decision remains blocked for Phase 32.
- This plan does not claim morphology, persistence, provider/audio behavior, templates, export readiness, or a working Korean generation flow.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: All seven preflight commands, every task verification, Python 3.12 package proof, approved-asset check, no-write/absence checks, stub scan, and high-leverage second pass passed. Assurance remains self_checked.
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
  summary: The canonical Python 3.13 venv was locked by editor language servers, so required Python 3.12 evidence ran in an OS-temporary uv project environment without disturbing the worktree.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Pytest's scripts namespace conflicted with the repository script import; the test now uses the established deterministic file-loader pattern.
</deltas>

<judgment>
<active_constraints>
Keep `ko` as the only request/settings identity; keep `ko-KR` at future provider boundaries only. Do not create Korean frequency data or an `assets/frequency/ko` directory. Keep Kiwi lazy in later production work. Do not make provider calls or expose private text in errors. Preserve all existing language/source/default contracts and the approved committed asset set.
</active_constraints>
<unresolved_uncertainty>
The Korean frequency source, attribution text, and redistribution terms remain unapproved. This plan proves installation and contract boundaries only; analyzer behavior, downstream enum exhaustiveness, persistence, and morphology matching remain for later Phase 30 plans and verification.
</unresolved_uncertainty>
<decision_posture>
Build Korean support additively on the shared modern pipeline: one canonical `ko` identity, exact reproducible Kiwi code/model packages, and explicit capability gates rather than provisional data, silent skips, broad aliases, or Korean-only source modes.
</decision_posture>
<anti_regression>
Do not remove or reorder prior selectable languages. Do not use selectable-language exhaustiveness as proof of asset approval. Build/check-all must remain approved-only, and explicit Korean asset work must continue to fail before filesystem or word-list side effects until licensing approval is documented. Non-Korean startup must not import or construct Kiwi eagerly.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All 12 execution-owned files exist.
- All required summary sections (`<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`) are present and substantive.
- Planning-state fingerprint validation is clean, Phase 30 remains open, and no Korean frequency asset path exists.
- No commit check applies because the user explicitly prohibited all git delivery actions.

---
*Phase: 30-korean-contracts-and-morphology*
*Plan: 01*
*Completed: 2026-08-04*
