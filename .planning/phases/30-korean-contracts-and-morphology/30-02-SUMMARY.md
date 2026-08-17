---
phase: 30-korean-contracts-and-morphology
plan: "02"
subsystem: korean-domain-and-morphology
runtime: opencode
assurance: self_checked
tags: [korean, kiwi, unicode-nfc, morphology, pydantic, privacy, tdd]
requires:
  - 30-01
provides:
  - Controlled unsupported Korean voice and Tatoeba boundaries
  - Immutable canonical Korean text, analyzer, signature, result, and lexical identity contracts
  - Lazy exact-config Kiwi analysis projection with top-two same-eojeol target consensus
  - Real pinned Kiwi linguistic, compound, homograph, and OOV regression goldens
affects: [30-03, 30-04, 30-05, 30-06, 30-07, 30-08]
tech-stack:
  added: []
  patterns:
    - Reject compatibility and halfwidth Hangul before NFC normalization
    - Keep Kiwi import and construction behind one cached lazy factory
    - Project vendor tokens into immutable project-owned evidence
    - Require both top analyses to match one complete ordered eojeol signature
key-files:
  created:
    - src/multilang/domain/korean.py
    - src/multilang/services/korean_morphology.py
    - tests/domain/test_korean.py
    - tests/services/test_korean_morphology.py
  modified:
    - src/multilang/services/audio_voice_registry.py
    - src/multilang/services/tatoeba_sentence_source.py
    - tests/services/test_korean_language_support.py
    - tests/services/test_audio_voice_registry.py
    - tests/services/test_tatoeba_sentence_source.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Korean remains absent from the approved voice registry and exits Tatoeba selection before candidate-provider access."
  - "Resolved Korean identity requires canonical NFC, lexical POS, a source-backed sense ID, a non-empty ordered signature, and the complete locked analyzer fingerprint."
  - "Any actual Kiwi OOV evidence blocks the whole analysis and match, even when the requested target appears in both alternatives."
  - "Target presence requires both top analyses to contain the exact complete signature within one word_position."
patterns-established:
  - "Privacy-safe failure: reason code and exception class only; never source text, paths, tracebacks, or vendor reprs."
  - "Lifecycle isolation: importing the adapter does not import Kiwi; one analyzer is constructed only on first Korean use."
requirements-advanced: [KMODE-01, KMODE-02, KNLP-01, KNLP-02]
requirements-completed: []
duration: 21m07s
completed: 2026-08-04
---

# Phase 30: Korean Contracts and Morphology - Plan 02 Summary

**Canonical NFC/source identity and a lazy pinned Kiwi adapter now provide privacy-safe top-two same-eojeol matching, with real OOV evidence forcing typed rejection.**

## Performance

- **Duration:** 21m07s
- **Started:** 2026-08-04T17:28:12Z
- **Completed checks:** 2026-08-04T17:49:19Z
- **Tasks:** 4/4
- **Repository files created/modified by this execution:** 12, including this summary
- **Assurance:** `self_checked` (same-runtime OpenCode execution plus real Python 3.12 Kiwi checks)

## Accomplishments

- Converted missing Korean voice selection from raw `KeyError` to the existing controlled `VoiceSelectionError` without registering or guessing a voice.
- Disabled Korean Tatoeba fallback before candidate-provider or network access without adding a `kor` mapping.
- Added immutable Pydantic contracts for NFC text, source-backed lexical identity, analyzer fingerprints, ordered morpheme signatures, projected alternatives, and typed analysis/match outcomes.
- Added one lazy, thread-safe cached Kiwi adapter with exact constructor and analysis options, actual installed code/model versions, and no module-import construction.
- Projected real Kiwi tokens into safe project models while retaining lemma, base/raw POS, OOV, ordering, scores, and `word_position` boundaries.
- Implemented exact top-two consensus matching for regular, irregular, adjectival, compound, and POS-homograph cases without generic suffix, substring, whitespace, or regex fallback.
- Proved the locked `알리오올리오가 진짜 맛있는 집` fixture carries actual `Token.oov is True` in both alternatives and blocks both analysis and an otherwise-valid `집/NNG` target match.

## TDD Task Evidence

### Task 30-02-01: Fail closed at Korean voice and Tatoeba boundaries

- **RED:** `uv run pytest tests/services/test_korean_language_support.py tests/services/test_audio_voice_registry.py tests/services/test_tatoeba_sentence_source.py -q` produced **3 failed, 23 passed in 1.82s**. Both voice tests exposed raw `KeyError`; the counting Tatoeba provider recorded one forbidden Korean call.
- **GREEN:** Missing voice lookup now raises `VoiceSelectionError`, and `select_sentence` returns before Korean provider access: **26 passed in 0.70s**.
- **REFACTOR:** No structural refactor was needed.
- **Final:** The exact command produced **26 passed in 0.74s**.

### Task 30-02-02: Define canonical Korean Unicode and identity contracts

- **RED:** The complete domain test file produced **21 failed in 0.29s**, each on the intentional missing-module assertion before any production domain module existed.
- **GREEN:** The first complete contract implementation produced **21 passed in 0.07s**, with one Pydantic field-shadow warning.
- **REFACTOR:** The public `register` contract was retained through an aliased internal field/property, removing the warning; **21 passed in 0.07s** with clean output.
- **Final:** The final combined domain/morphology suite remained green at **45 passed in 25.98s**.

### Task 30-02-03: Implement the lazy pinned Kiwi adapter and projection

- **RED:** With the real Kiwi/OOV and unavailable tests already present, the focused command produced **12 failed, 21 passed in 0.38s** because the adapter module did not exist.
- **GREEN:** Lazy construction, complete fingerprinting, real projection, typed unavailable paths, and actual OOV handling produced **33 passed in 8.57s**.
- **REFACTOR:** A second pass removed an unused import and avoided truth-testing arbitrary malformed vendor output; all focused tests stayed green.
- **Python 3.12 real OOV:** The named pinned-Kiwi check initially produced **1 passed, 11 deselected in 2.01s** and, after the matcher tests were added, finalized at **1 passed, 23 deselected in 2.00s**.

### Task 30-02-04: Implement top-two consensus matching and real goldens

- **RED:** All matcher/golden tests were written first; the command produced **12 failed, 33 passed in 12.42s**, exclusively because `match_target` did not yet exist.
- **GREEN:** Exact per-alternative, same-eojeol signature consensus produced **45 passed in 25.72s**.
- **REFACTOR:** The high-leverage second pass rechecked option/fingerprint parity, lexical POS filtering, raw-tag normalization, word boundaries, OOV precedence, missing/malformed identity, and privacy-safe outcomes.
- **Final:** The exact focused suite produced **45 passed in 25.98s**.
- **Python 3.12 compound/OOV:** The required named checks finalized at **2 passed, 22 deselected in 3.86s** using real pinned Kiwi and no fake factory.

## Final Verification Results

| Check | Exact result |
|---|---|
| Unsupported voice/Tatoeba and existing-provider regression command | `26 passed in 0.74s` |
| Final Korean domain + morphology command | `45 passed in 25.98s` |
| Python 3.12 real OOV analysis check | `1 passed, 23 deselected in 2.00s` |
| Python 3.12 real compound + OOV-match checks | `2 passed, 22 deselected in 3.86s` |
| Python compilation check for new domain/service/tests | Exit 0 with no output |
| Real raw OOV contract | Both top alternatives contained `form == "알리오올리오"` with `Token.oov is True` |
| Existing provider preservation | All approved voice selections and existing Tatoeba tests remained green |
| Korean Tatoeba network boundary | Counting providers remained at zero Korean calls; no `kor` mapping exists |
| Lazy lifecycle | Subprocess import left `kiwipiepy` absent from `sys.modules`; repeated Korean calls constructed one analyzer |
| Patch hygiene | `git diff --check` exited 0; only pre-existing Windows line-ending conversion warnings were emitted |
| Stub scan | No TODO/FIXME/HACK/XXX or rendering placeholder exists in plan-created production files |

The Python 3.12 checks reused the OS-temporary project environment established by Plan 30-01 so the active Python 3.13 repository environment and editor-held executables were not replaced. The `VIRTUAL_ENV` mismatch warning was expected; each selected real-Kiwi test passed. No TTS, Tatoeba, translation, LLM, or other application provider/network call ran.

## Files Created/Modified

- `src/multilang/domain/korean.py` - Canonical constants, NFC/script gate, immutable evidence/results, source-backed identity, and stable lexical keys.
- `src/multilang/services/korean_morphology.py` - Lazy exact-config Kiwi construction, safe projection, OOV handling, and top-two matcher.
- `src/multilang/services/audio_voice_registry.py` - Controlled missing-plan error for Korean without a voice entry.
- `src/multilang/services/tatoeba_sentence_source.py` - Early Korean no-fallback return before provider access.
- `tests/domain/test_korean.py` - Unicode, key, identity, immutability, and fail-closed domain invariants.
- `tests/services/test_korean_morphology.py` - Real linguistic/OOV goldens, lazy lifecycle, safe unavailable paths, consensus, homograph, and Python 3.12 smoke coverage.
- `tests/services/test_korean_language_support.py` - Combined no-guessed-provider Korean boundary proof.
- `tests/services/test_audio_voice_registry.py` - Approved-language registry regression plus Korean controlled failure.
- `tests/services/test_tatoeba_sentence_source.py` - Counting-provider Korean early-return proof.
- `.planning/SPEC.md` - Updated only the Current State handoff from Plan 30-01 to Plan 30-02.
- `.planning/.state-fingerprint.json` - Rebaselined reviewed planning state after the SPEC update.
- `.planning/phases/30-korean-contracts-and-morphology/30-02-SUMMARY.md` - This execution evidence and handoff.

## Git Actions

None. Per the explicit user instruction, this execution did not stage, commit, push, create a branch/PR, amend, reset, stash, or clean. Pre-existing Plan 30-01 and unrelated worktree changes were preserved.

## Decisions Made

- A missing voice plan is a supported domain outcome, not registry exhaustiveness; Korean remains intentionally absent until later live qualification.
- Tatoeba support is capability-gated at the service entry point, so Korean cannot accidentally reach a provider through a missing-map exception or generic matcher.
- Fingerprints store every locked constructor/analysis input and actual analyzer/model package versions; version drift blocks persisted target reuse.
- Morphology results may retain safe projected morpheme evidence, but only source-backed `KoreanLexicalIdentity` can carry a resolved project sense.
- Exact ordered signature equality is evaluated independently in each `word_position`; only `(True, True)` is `matched`.
- OOV precedence is global to each analysis result: unrelated actual OOV evidence blocks an otherwise matching target.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Warning/contract collision] Removed Pydantic `register` field shadowing**
- **Found during:** Task 30-02-02 GREEN.
- **Issue:** Pydantic reported that `KoreanLexicalIdentity.register` shadowed a parent attribute, leaving otherwise-passing output non-pristine.
- **Fix:** Stored the field under an internal name with `register` validation/serialization aliases and a public read-only `register` property.
- **Files modified:** `src/multilang/domain/korean.py`.
- **Verification:** Focused domain suite returned `21 passed` without warnings.
- **Commit:** None by user instruction.

**2. [Rule 3 - Blocking environment] Reused the reviewed OS-temporary Python 3.12 environment**
- **Found during:** Required Python 3.12 verification.
- **Issue:** The repository environment remains Python 3.13 and was intentionally not replaced because Plan 30-01 documented editor-held executables.
- **Fix:** Selected the existing OS-temporary uv project environment while still running each listed `uv run --python 3.12` test command.
- **Files modified:** No repository implementation files.
- **Verification:** Required real OOV check passed once; required compound/OOV-match selection passed twice.
- **Commit:** None by user instruction.

**Total deviations:** 2 recoverable auto-fixes. Neither changed architecture, locked analyzer policy, goldens, or plan scope.

## Issues Encountered

- The first exploratory Korean-token print used the Windows legacy console encoding and failed before displaying token evidence. Re-running the same local-only probe with UTF-8 output produced stable alternatives and scores; no fixture or policy was changed.
- A supplemental `uv run ruff check` could not run because Ruff is not installed or configured in this repository. It was not a listed plan check; Python compilation and every required pytest command passed.
- No locked real-analyzer golden was unstable. Therefore no stop-and-challenge, fixture weakening, score threshold, heuristic fallback, or policy change was needed.

## Security and Boundary Review

- Compatibility Jamo and halfwidth Hangul are rejected before NFC and never repaired with NFKC.
- Analyzer/vendor exceptions become only controlled reason codes and exception class names.
- Tests inject source text plus path/token-like exception messages and prove none enter serialized results.
- Vendor token objects and reprs are never retained; only immutable project fields are projected.
- No Korean voice ID, `kor` Tatoeba code, provider request, endpoint, schema change, file-access path, or external trust boundary was added.
- Analyzer construction is lazy, cached, and lock-protected; module import and fingerprint access do not construct Kiwi.

## Known Stubs

None. No intentional empty/mock data flow prevents this plan's isolated domain and morphology goal.

## State and Handoff

- `.planning/SPEC.md` Current State records Plans 30-01 and 30-02 complete while Phase 30 remains in progress.
- `.planning/ROADMAP.md` remains open (`[-]`) and was not modified by this execution.
- `node .planning/bin/gsdd.mjs session-fingerprint write` completed with fingerprint `d0304cc429b84de20f66f6a3766eeb7ce3aca802b55da499dc7842007d6e5eb7`.
- No SPEC requirement checkbox was closed; later Phase 30 plans and phase verification remain required.

## Next Plan Readiness

- Plan 30-03 can persist `KoreanLexicalIdentity` and compare complete fingerprints without importing Kiwi vendor classes.
- Plan 30-04 can bind source records using canonical lemma/POS/signature evidence while preserving the rule that Kiwi cannot author `sense_id`.
- Later validation/highlight paths must consume `match_target`; Korean may never fall through to existing generic matching.
- Production lexical senses, database durability, full three-mode routing, Korean audio, final assets, templates, and export readiness remain unclaimed.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: All four TDD cycles, every listed focused command, both real pinned Kiwi OOV checks, the Python 3.12 compound smoke, provider regressions, compilation, privacy assertions, stub scan, and high-leverage second pass passed without weakening a golden.
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
  summary: Pydantic exposes a parent `register` attribute, so the required public field uses an internal aliased storage name plus a read-only property to keep validation, serialization, and warning-free behavior.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Required Python 3.12 checks reused the reviewed OS-temporary uv environment from Plan 30-01 rather than replacing the active Python 3.13 repository environment.
</deltas>

<judgment>
<active_constraints>
Keep `ko` as the only product identity and `ko-KR` as a provider-locale constant only. Do not add a Korean voice or Tatoeba mapping/call. Canonical learner content rejects compatibility/halfwidth Hangul before NFC. Keep Kiwi lazy, exact-pinned, standard-dialect `cong`, one-worker, no-correction, `top_n=2`, and fully fingerprinted. Never expose source text, paths, token dumps, or tracebacks through analysis/match failures.
</active_constraints>
<unresolved_uncertainty>
No approved production Korean lexical source or sense mapping exists, so this plan's identities use reviewed synthetic sense IDs only in tests. The conservative top-two policy has deterministic required goldens but no corpus-wide calibration; any future policy change requires a new approved fingerprint rather than weakening current fixtures. Persistence, source intersection, three-mode routing, and accepted generated cards remain for later plans.
</unresolved_uncertainty>
<decision_posture>
Prefer review-required false negatives over false-positive Korean target acceptance. Treat Kiwi as pinned morphology evidence, never lexical-sense authority; preserve complete ordered same-eojeol signatures and reject disagreement, OOV, missing identity, malformed evidence, unavailable analysis, or fingerprint drift.
</decision_posture>
<anti_regression>
Korean must remain absent from the approved voice registry and must return before Tatoeba provider access. Importing non-Korean modules must not import or construct Kiwi. Both configured analyses must independently match the exact target signature; one-of-two remains ambiguous, cross-eojeol assembly remains mismatch, noun/predicate homographs remain separate, and any actual OOV evidence remains non-passing. Existing approved voice and Tatoeba behavior must stay unchanged.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All 12 execution-owned files exist.
- Every listed pytest and Python 3.12 real-Kiwi check passed with the exact final results recorded above.
- Required summary sections (`<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`) are present and substantive.
- Lifecycle preflight reports planning state `clean`; the reviewed session fingerprint matches current ROADMAP/SPEC/config content.
- Phase 30 remains open with the `[-]` marker, and no later plan or requirement checkbox was executed or closed.
- No commit check applies because the user explicitly prohibited all git delivery actions.

---
*Phase: 30-korean-contracts-and-morphology*
*Plan: 02*
*Completed: 2026-08-04*
