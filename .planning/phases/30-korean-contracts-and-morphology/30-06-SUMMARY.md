---
phase: 30-korean-contracts-and-morphology
plan: "06"
subsystem: korean-identity-bound-text-acceptance
runtime: opencode
assurance: self_checked
tags: [korean, kiwi, morphology, validation, retry, regeneration, unicode-nfc, privacy, tdd]
requires:
  - 30-05
provides:
  - Korean-first generated-sentence validation that accepts only a typed top-two matched result with an equal persisted/runtime fingerprint
  - Content-free morphology failures for every missing, malformed, mismatched, inconclusive, unavailable, untyped, or drifted Korean outcome
  - Exact persisted Korean identity restoration and reuse through initial generation, retry, and regeneration
  - Explicit Korean Tatoeba denial before fallback-source access
affects: [30-07, 30-08, 32-frequency-portuguese-text-and-audio]
tech-stack:
  added: []
  patterns:
    - Korean language and target checks return before Japanese, Mandarin, corpus-ID, generic-key, Stanza, suffix, or heuristic paths
    - Persisted Pydantic identity is restored once and passed unchanged across every text attempt
    - Review diagnostics contain controlled match status and reason codes without learner content, sense data, fingerprints, or exceptions
key-files:
  created:
    - .planning/phases/30-korean-contracts-and-morphology/30-06-SUMMARY.md
  modified:
    - src/multilang/services/text_validation.py
    - src/multilang/services/generate_text_items.py
    - src/multilang/services/regenerate_text_item.py
    - tests/services/test_text_validation.py
    - tests/services/test_generate_text_items.py
    - tests/services/test_regenerate_text_item.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Korean acceptance requires a valid persisted identity, an equal active analyzer fingerprint, and a valid KoreanMatchResult whose fingerprint is equal and whose status is matched."
  - "Every other Korean match outcome maps to MORPHOLOGY_MISMATCH with controlled content-free detail; no generic matcher can rescue it."
  - "Generation restores Korean identity from persisted JSON once, reuses that same object for initial generation and retry, and exits before Korean Tatoeba access."
  - "Regeneration consumes the shared restored candidate and passes the identical identity on both attempts without reanalysis or a separate matcher."
patterns-established:
  - "Frozen source identity, not display text or provider output, is the sole Korean sentence-acceptance authority."
  - "Korean inconclusive morphology remains review-required across every implemented text lifecycle."
requirements-advanced: [KMODE-02, KNLP-01, KNLP-02]
requirements-completed: []
duration: 14m
completed: 2026-08-04
---

# Phase 30 Plan 06: Strict Korean Text Acceptance Summary

**Korean generated text now passes only through an exact persisted-identity and equal-fingerprint Kiwi consensus result, while initial generation, retry, and regeneration preserve that identity, keep every inconclusive outcome review-required, and make Korean Tatoeba and generic matching unreachable.**

## Performance

- **Started:** 2026-08-04T19:40:02Z
- **Completed checks:** 2026-08-04T19:54:00Z
- **Duration:** approximately 14m
- **Tasks:** 3/3
- **Execution-owned files created/modified:** 9, including this summary, SPEC, and the session fingerprint
- **Assurance:** `self_checked` with strict RED/GREEN cycles, deterministic local fakes, exact focused commands, all-file regression evidence, a zero-fallback selection, and the required high-leverage second pass

## Accomplishments

- Added a separately injected lazy Korean matcher and optional typed identity to `TextValidationService`.
- Placed the `ko` target branch before Japanese/Mandarin substring checks and every generic key, Stanza, suffix, or heuristic target-matching route.
- Revalidated persisted identity and active fingerprint, rejected fingerprint drift before analysis, validated the typed match result and its fingerprint, and accepted only `KoreanMatchStatus.MATCHED`.
- Mapped mismatch, ambiguity, OOV, unavailable analysis, missing identity, malformed identity/result, untyped result, and fingerprint drift to `MORPHOLOGY_MISMATCH` with content-free controlled details.
- Added Korean-first NFC/script language detection before the generic corpus identifier, rejecting compatibility Hangul and non-Korean script without echoing input.
- Avoided generic match-key/suffix helpers in Korean translation, command, and capitalization checks while preserving those generic paths for all other languages.
- Restored `KoreanLexicalIdentity` from persisted JSON and passed the same restored object through initial generation, retry generation, and every validation call.
- Returned before Tatoeba source access for Korean after a failed retry; the final failed result persists as review-required.
- Applied the identical restored-identity handoff to both regeneration attempts while preserving existing text-row identity and repair counters.

## TDD Task Evidence

### Task 30-06-01: Add the Korean-first persisted-signature validator

- **Test-harness correction:** The first test-only run stopped at collection because a multi-section patch did not retain the new `pytest` import. The import/helper block was reapplied before a valid RED was accepted; no production code had been changed.
- **RED:** `UV_OFFLINE=1 uv run pytest tests/services/test_text_validation.py -q` produced **18 failed, 33 passed in 3.08s** for the absent Korean matcher/identity API and missing Korean-first language branch.
- **GREEN:** Added identity/fingerprint/result validation, safe non-passing details, Korean script checking, and early exits around generic matching helpers.
- **Final:** The exact task command produced **51 passed in 3.01s**.

### Task 30-06-02: Preserve Korean identity through generation and repair

- **RED:** `UV_OFFLINE=1 uv run pytest tests/services/test_generate_text_items.py tests/services/test_text_validation.py -q` produced **2 failed, 71 passed in 2.95s** because DB-loaded candidates discarded `korean_identity`; the hidden downstream assertions also required retry identity reuse and zero Tatoeba calls.
- **GREEN:** Restored typed identity from persisted JSON, passed it into validation, reused the same candidate for retry, and returned before Korean Tatoeba source access.
- **Final:** The exact task command produced **73 passed in 2.85s**.

### Task 30-06-03: Apply the identical Korean gate to regeneration

- **RED:** `UV_OFFLINE=1 uv run pytest tests/services/test_regenerate_text_item.py tests/services/test_text_validation.py -q` produced **3 failed, 55 passed in 3.01s** because regeneration omitted `korean_identity` from both validation calls.
- **GREEN:** Passed the shared restored identity to initial and repair validation without reanalysis or a regeneration-specific matcher.
- **Final:** The exact task command produced **58 passed in 2.80s**.

## Final Verification Results

| Check | Exact result |
|---|---|
| Task 1 validator command | `51 passed in 3.01s` |
| Task 2 generation + validator command | `73 passed in 2.85s` |
| Task 3 regeneration + validator command | `58 passed in 2.80s` |
| All three plan test files together | `80 passed in 2.83s` |
| Korean high-leverage selection | `23 passed, 57 deselected in 0.72s` |
| Same-file non-Korean regression selection | `57 passed, 23 deselected in 2.99s` |
| Direct + orchestration Korean Tatoeba denial | `2 passed in 0.73s` |
| Offline Korean script smoke check | `offline-korean-script-check: passed` |
| Python compilation of all six source/test files | Exit 0 with no output |
| Scoped patch whitespace check | Exit 0; Windows LF-to-CRLF notices only |

Every `uv` command used `UV_OFFLINE=1`. All sentence generation, translation, morphology, language-identification, persistence, and Tatoeba collaborators exercised by the new lifecycle tests were deterministic local fakes or in-process typed services. No live provider, HTTP, network, paid, quota, audio, export, production database, or corpus call ran.

## Zero-Fallback Evidence

- The positive validator test replaces Japanese target matching, Mandarin target matching, generic `_match_keys`, and suffix derivation with raising sentinels; it also injects a counting generic morphology analyzer and a forbidden generic language identifier. Korean `먹다/VV -> 먹었어요` passed with **zero** calls to every forbidden route.
- The Korean target branch returns before Japanese, Mandarin, generic key construction, Stanza, heuristic acceptance, and suffix derivation. Korean language checking returns before Mandarin validation, corpus language ID, and Japanese script handling.
- All seven typed non-matched statuses (`mismatch`, `ambiguous`, `oov`, `unavailable`, `missing`, `fingerprint-mismatch`, `invalid`) failed with exactly one morphology flag in the focused validator matrix.
- Missing and malformed identities failed before matcher access. Persisted fingerprint drift failed before matcher access. Untyped matched output and a typed matched output carrying a drifted result fingerprint both failed.
- Generation tests proved the same restored identity object reached both generation and validation attempts for unavailable and ambiguous morphology, while the injected Tatoeba source recorded `[]` calls.
- Regeneration tests proved the same identity object reached both attempts for unavailable and ambiguous morphology; fingerprint drift reached neither matcher call and still persisted review-required.
- Existing direct Tatoeba-source evidence separately proved Korean returns `None` while its candidate provider call count remains zero.

## High-Leverage Second Pass

| Lifecycle/status | Trace result |
|---|---|
| Typed `matched` + equal persisted/active/result fingerprint | Accepted; full identity passed to matcher over the complete sentence |
| Typed `mismatch` | Failed as content-free morphology mismatch |
| Typed `ambiguous` | Failed; generation retry and regeneration remained review-required |
| Typed `oov` | Failed as content-free morphology mismatch |
| Typed `unavailable` | Failed; generation retry and regeneration remained review-required |
| Typed `missing` / absent identity | Failed before any generic route; absent identity never becomes accepted |
| Malformed identity or typed-result payload | Failed before acceptance with no learner content in detail |
| Persisted or result fingerprint drift | Failed before analysis or acceptance; regeneration remained review-required |
| Untyped object claiming `matched` | Failed; status-like attributes alone carry no authority |
| Failed Korean retry | Persisted review-required with `review_reason=morphology_mismatch`; Tatoeba source not accessed |

The lifecycle branches only on the shared `ValidationStatus.FAILED`, so every non-passing status proven equivalent at the validator boundary follows the same retry/review path. Representative unavailable/ambiguous lifecycle tests and the drift regeneration test prove that no later attempt promotes an inconclusive result.

## Files Created/Modified

### Created

- `.planning/phases/30-korean-contracts-and-morphology/30-06-SUMMARY.md` - TDD, strict-acceptance, zero-fallback, lifecycle, and handoff evidence.

### Modified

- `src/multilang/services/text_validation.py` - Korean-first matcher, typed identity/result and fingerprint gates, content-free failures, and Korean script handling.
- `src/multilang/services/generate_text_items.py` - Persisted identity restoration, validation handoff, retry continuity, and pre-source Korean Tatoeba denial.
- `src/multilang/services/regenerate_text_item.py` - Exact candidate identity passed on both regeneration validations.
- `tests/services/test_text_validation.py` - Typed consensus, all non-passing statuses, malformed/missing/drift, generic-path sentinels, and NFC/script evidence.
- `tests/services/test_generate_text_items.py` - DB JSON restoration, same-object attempt continuity, review persistence, safe details, and zero Tatoeba calls.
- `tests/services/test_regenerate_text_item.py` - Unavailable/ambiguous/drift regeneration, exact identity continuity, row/counter preservation, and review persistence.
- `.planning/SPEC.md` - Current State advanced through Plan 30-06 while Phase 30 remains in progress.
- `.planning/.state-fingerprint.json` - Reviewed planning-state fingerprint updated after the SPEC handoff.

## Git Actions

None. Per explicit user instruction and the carried Phase 30 execution convention, no files were staged or committed, and no branch, push, PR, amend, reset, stash, clean, checkout, restore, or other delivery/destructive action was performed.

## Decisions Made

- Validator authority requires three equal evidence points: persisted identity fingerprint, active matcher fingerprint, and typed result fingerprint.
- A result is not accepted by truthy attributes or a `matched` string; it must validate as `KoreanMatchResult` and have enum status `MATCHED`.
- Safe failure details expose only controlled status/reason codes. They do not include sentence text, lemma, sense ID, fingerprint versions, analyzer output, paths, tokens, or exceptions.
- Korean script detection validates forbidden ranges through the shared canonicalizer, measures modern Hangul after NFC canonicalization, and returns before the generic corpus detector.
- Identity is reconstructed only from persisted typed JSON, never from display form, lemma, definitions, generated text, or a retry analysis.
- The existing non-Korean AI-retry/Tatoeba chain remains intact; only `SupportedLanguage.KO` returns before fallback-source access.

## Deviations from Plan

None - the plan was executed as written. No consensus, fingerprint policy, generic non-Korean validator, provider fallback behavior, schema, endpoint, runtime composition, sentence-quality policy, or later-plan scope changed.

## Issues Encountered

- A tool-level multi-section patch against the same test file retained the appended tests but not the earlier import/helper section twice. Each collection error was corrected in test code before accepting a valid RED result; production TDD order remained intact.
- `phase-status 30 in_progress` reported `changed: false` because Phase 30 was already open at `[-]`; no ROADMAP mutation was required.
- The canonical worktree remains intentionally dirty with completed Plans 30-01 through 30-05 and carried milestone work. This execution touched only the six Plan 30-06 code/test files plus required planning handoff artifacts.

## Security and Privacy Review

- Generated/model text remains untrusted and cannot provide Korean lemma, POS, sense, signature, fingerprint, or approval authority.
- Fingerprint drift is rejected before sentence analysis, preventing stale persisted evidence from being interpreted under a different analyzer policy.
- Matcher exceptions are converted to a controlled unavailable morphology failure; raw exception messages and source text are not retained in review detail.
- Missing, malformed, or untyped evidence fails closed and cannot enter generic permissive matching.
- Retry and regeneration receive the exact durable identity and cannot reconstruct or mutate it from learner-facing content.
- Korean Tatoeba exits before source/provider access, so no network fallback can bypass morphology or disclose a query.
- No new endpoint, schema, authentication path, file-access path, network route, secret, logging payload, production corpus, or threat surface outside the plan threat register was added.

## Known Stubs

None. Deterministic fakes, synthetic reviewed identities, and content-free unavailable/ambiguous outcomes are test evidence required by the plan, not runtime stubs. Runtime-wide shared matcher composition remains intentionally assigned to Plan 30-07.

## User Setup Required

None. No credentials, provider configuration, network access, production database, or live Korean service is required for this offline contract work.

## State and Handoff

- `.planning/SPEC.md` records Plans 30-01 through 30-06 complete while Phase 30 remains in progress.
- `.planning/ROADMAP.md` remains open at `[-]`; `phase-status 30 in_progress` was a no-op and the phase was not closed.
- No requirement checkbox was closed; `KMODE-01`, `KMODE-02`, `KNLP-01`, and `KNLP-02` still require Plans 30-07 through 30-08 and phase verification.
- `node .planning/bin/gsdd.mjs session-fingerprint write` completed with fingerprint `f7e2eb85aea24c5c4b09dd2bef10653579688bc83801402b3866a665158408bf`.
- Plan 30-07 can compose one shared matcher into runtime services; it must preserve this exact acceptance gate and must not add Tatoeba or reconstruct identity.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: All strict RED/GREEN cycles, exact task commands, the combined plan suite, Korean zero-fallback selection, same-file non-Korean regressions, direct Tatoeba denial, compilation, scoped whitespace check, and the required identity/status lifecycle trace passed offline.
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
  summary: Multi-section same-file test patches intermittently omitted their first section; imports/helpers were reapplied before valid RED runs, with no production-code-before-test violation.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Phase 30 was already marked open, so the required in-progress lifecycle helper made no ROADMAP change before the reviewed session fingerprint was rewritten.
</deltas>

<judgment>
<active_constraints>
Keep `ko` as the sole internal identity and branch it before every Japanese, Mandarin, generic-key, Stanza, suffix, or heuristic matching route. Require the exact persisted `KoreanLexicalIdentity`, equal persisted/active/result fingerprints, and a valid typed top-two `matched` result. Carry the same restored identity through initial generation, retry, and regeneration. Keep all other outcomes review-required with content-free details and never access Tatoeba for Korean.
</active_constraints>
<unresolved_uncertainty>
Runtime-wide composition of one shared matcher, complete three-mode integration, and broad existing-mode closure remain assigned to Plans 30-07 and 30-08. Korean sentence naturalness, register, translation quality, and calibrated length policy remain Phase 32 work. No approved production Korean lexical/frequency source or redistribution decision exists.
</unresolved_uncertainty>
<decision_posture>
Persisted source identity and its exact analyzer policy remain immutable authority. False negatives route to review; ambiguity, OOV, unavailable analysis, malformed evidence, and drift must never be promoted through display-text reconstruction, generic heuristics, provider output, retry, regeneration, or corpus fallback.
</decision_posture>
<anti_regression>
Non-Korean Stanza, suffix, key, heuristic, retry, Tatoeba, validation, record identity, and repair-counter behavior must remain unchanged. Later plans must not weaken top-two consensus, accept status-like untyped objects, skip fingerprint equality, reanalyze a persisted candidate opportunistically, expose content in failure detail, or make Korean Tatoeba reachable.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All nine execution-owned files exist, including this summary, the SPEC update, and the reviewed planning-state fingerprint.
- Every exact task command and final combined command passed; focused Korean, non-Korean, zero-Tatoeba, compilation, and whitespace claims match deterministic local output.
- Phase 30 remains open at `[-]`, no Plan 30-07-or-later summary was created, and no requirement checkbox was prematurely closed.
- Required structured sections (`<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`) plus zero-fallback and high-leverage evidence are present and substantive.
- The staging area remains unchanged and empty; no git delivery or destructive action occurred.

---
*Phase: 30-korean-contracts-and-morphology*
*Plan: 06*
*Completed: 2026-08-04*
