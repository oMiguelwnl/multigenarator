---
phase: 30-korean-contracts-and-morphology
plan: "05"
subsystem: korean-identity-aware-provider-contracts
runtime: opencode
assurance: self_checked
tags: [korean, pydantic, provider-cache, prompt-security, unicode-nfc, privacy, tdd]
requires:
  - 30-04
provides:
  - Complete persisted Korean identity in typed definition/sentence requests, dumps, and cache-key material
  - Canonical identity-grounded Korean prompts with homograph isolation and Portuguese output policy
  - NFC/script-gated Korean provider results before cache and durable handoff
  - Redacted, bounded, explicitly untrusted private highlight context
  - Provider-output authority separation from morphology, POS, source sense, signature, fingerprint, and approval
affects: [30-06, 30-07, 30-08, 32-frequency-portuguese-text-and-audio]
tech-stack:
  added: []
  patterns:
    - Optional Korean-only Pydantic fields excluded from generic serialized payloads
    - Complete identity in cache material plus canonical prompt projection and content-free identity digest
    - Unicode/script validation at adapter, cache-restore, cache-write, fallback, and grounding handoff boundaries
    - Private context sanitation before request validation, serialization, hashing, or prompting
key-files:
  created:
    - .planning/phases/30-korean-contracts-and-morphology/30-05-SUMMARY.md
  modified:
    - src/multilang/services/text_generation.py
    - src/multilang/services/provider_text_adapters.py
    - src/multilang/services/lexical_grounding.py
    - tests/services/test_text_generation.py
    - tests/services/test_provider_text_adapters.py
    - tests/services/test_lexical_grounding.py
    - .planning/SPEC.md
    - .planning/.state-fingerprint.json
key-decisions:
  - "Korean requests fail closed without an exact persisted identity and retain Portuguese as the definition/translation target; generic requests serialize exactly as before without a Korean field."
  - "Prompts render canonical trusted identity evidence and a digest of the complete persisted identity, while exact submitted evidence remains in the typed request/cache contract rather than being exposed as prompt prose."
  - "Provider intended_sense is never authoritative for Korean: cache and handoff overwrite it with the persisted source sense_id."
  - "Korean highlight context is sanitized and bounded before request validation so dumps, cache material, structured errors, and prompts cannot retain raw paths, secrets, vendor dumps, or identity-override instructions."
patterns-established:
  - "Source authority survives generation: provider fields can produce learner text only, never Korean lexical identity or approval state."
  - "Defense in depth: Korean provider text is canonicalized both in the concrete adapter and generic text-generation boundary."
requirements-advanced: [KMODE-01, KMODE-02, KNLP-01, KNLP-02]
requirements-completed: []
duration: 26m
completed: 2026-08-04
---

# Phase 30 Plan 05: Identity-Aware Korean Provider Contracts Summary

**Exact persisted Korean lemma/POS/sense/signature/fingerprint identity now isolates offline provider requests, prompts, and cache keys while private context and untrusted output are sanitized, NFC/script-gated, and denied authority over source morphology or approval.**

## Performance

- **Started:** 2026-08-04T19:12:17Z
- **Completed checks:** 2026-08-04T19:38:35Z
- **Duration:** approximately 26m
- **Tasks:** 3/3
- **Execution-owned files created/modified:** 9, including this summary, SPEC, and session fingerprint
- **Assurance:** `self_checked` with strict RED/GREEN cycles, deterministic fakes, focused regressions, privacy scans, and the required high-leverage second pass

## Accomplishments

- Added optional `KoreanLexicalIdentity` fields to sentence and definition requests, copied exact persisted identity from grounded candidates, rejected missing/mismatched Korean identity, and excluded absent fields from every generic dump.
- Reused Pydantic JSON dumps as cache-key material, proving POS, sense, ordered signature, analyzer fingerprint, and exact persisted-identity differences isolate generated content.
- Added `Korean (ko)` prompt naming, full controlled source evidence, complete-identity digest, immutable-authority rules, and Portuguese definition/translation policy without adding `ko-KR` routing.
- Sanitized Korean highlight context before validation/serialization, bounded it to 24 tokens, and delimited it as untrusted sense guidance after removing paths, secrets, vendor-object dumps, and identity-override instructions.
- Canonicalized Korean sentence/definition output at adapter and service boundaries before cache or handoff, normalized stale cached/fallback NFD, and rejected compatibility/halfwidth Hangul with content-free errors.
- Overrode provider-authored Korean `intended_sense` with the persisted source `sense_id`; forged morphology/POS/sense/signature/fingerprint/approval fields cannot enter candidates.
- Resolved Korean source identity before requesting a Portuguese definition and built the final candidate exclusively from the frozen identity regardless of provider content.

## TDD Task Evidence

### Task 30-05-01: Add identity-bearing request and cache contracts

- **RED:** After correcting the deterministic cache test harness, `UV_OFFLINE=1 uv run pytest tests/services/test_text_generation.py -q` produced **7 failed, 12 passed in 0.48s** for absent identity fields, colliding dumps/cache keys, NFD cache/handoff text, and accepted compatibility output.
- **GREEN:** Added identity-bearing request models, generic-field exclusion, complete dump-derived cache isolation, Korean NFC/script handling before cache writes and after cache restores, and fallback/bundle re-normalization.
- **Supplemental RED/GREEN:** A provider-controlled `intended_sense` produced **3 failed** focused tests, then **3 passed** after source `sense_id` became the only Korean handoff/cache sense.
- **Final:** The exact task command produced **19 passed in 0.35s**.

### Task 30-05-02: Ground Korean prompts without exposing private or vendor data

- **RED:** The first prompt/output command produced **5 failed, 12 passed in 1.01s** for missing Korean naming/evidence, colliding homograph prompts, absent untrusted delimiters, noncanonical output, and identityless requests.
- **Contract RED:** Four focused request invariants produced **4 failed, 16 deselected in 0.95s** before fail-closed identity/language/Portuguese-target validation.
- **GREEN:** Added canonical identity JSON, complete-identity digest, immutable-authority rules, Korean output normalization, and deterministic request/prompt privacy sanitation.
- **Supplemental RED/GREEN:** Exact submitted-form identity initially did not affect prompt content (**1 failed**), then passed through a content-free SHA-256 identity digest; structured Pydantic errors initially retained raw context (**1 failed**), then passed after pre-validation sanitation.
- **Final:** The exact task command produced **21 passed in 1.07s**.

### Task 30-05-03: Pass resolved identity into Portuguese definition generation

- **RED:** `UV_OFFLINE=1 uv run pytest tests/services/test_lexical_grounding.py tests/services/test_provider_text_adapters.py -q` produced **2 failed, 59 passed in 7.08s** because Korean grounding skipped definition generation and no identity handoff occurred.
- **GREEN:** Converted the resolved Korean candidate builder into an identity-aware instance path, passed exact source identity with `ko -> pt`, NFC/script-gated the definition, and ignored forged provider identity/approval fields.
- **Final:** The exact task command produced **62 passed in 7.06s**.

## Final Verification Results

| Check | Exact result |
|---|---|
| Task 1 text-generation contract | `19 passed in 0.35s` |
| Task 2 provider prompt/output contract | `21 passed in 1.07s` |
| Task 3 grounding + provider contract | `62 passed in 7.06s` |
| All three plan files together | `81 passed in 6.69s` |
| Required high-leverage identity/privacy review | `6 passed, 75 deselected in 0.88s` |
| Adjacent non-Korean adapter/runtime/cache/retry regressions | `53 passed in 3.82s` |
| Generate/regenerate text-item regressions | `24 passed in 2.69s` |
| Python compilation | Exit 0 with no output |
| Scoped patch whitespace check | Exit 0; Windows LF-to-CRLF notices only |
| Ruff check/format | Not available in the offline project environment (`ruff`: program not found); no installation or network access attempted |

All commands used `UV_OFFLINE=1` where `uv` was involved. Every provider completion, translation, cache, morphology, and definition collaborator exercised by this plan was deterministic and local; no live provider, network, quota, production-source, audio, export, or asset call ran.

## High-Leverage Second Pass

- Request dumps and generic `_cache_key_for_request` values differ when otherwise identical Korean identities change only POS, sense, ordered signature, analyzer fingerprint, or exact submitted evidence.
- Noun and predicate `배우` identities produce distinct prompt evidence and identity digests; ordered signatures and source senses remain visible as controlled JSON data rather than provider-authored prose.
- Concrete adapter output and generic cache/handoff boundaries both normalize NFD to NFC; compatibility Hangul is rejected before cache or durable handoff, including stale-cache and fallback paths.
- Korean grounding records source and surface morphology calls before the definition collaborator runs, and the definition request receives the exact frozen identity.
- Forged response/provenance fields for lemma, POS, sense, signature, fingerprint, and approval are discarded; Korean `intended_sense` is replaced with source `sense_id`.
- Raw Windows paths, API-key material, vendor `Token(...)` dumps, and identity-override instructions are absent from request values/dumps, structured validation errors, and delimited prompt context.

## Files Created/Modified

### Created

- `.planning/phases/30-korean-contracts-and-morphology/30-05-SUMMARY.md` - TDD, verification, privacy, authority, and handoff evidence.

### Modified

- `src/multilang/services/text_generation.py` - Identity-bearing request validation/serialization, safe context ingress, homograph-safe keys, NFC cache/fallback/handoff handling, and trusted-sense enforcement.
- `src/multilang/services/provider_text_adapters.py` - Korean naming, canonical identity prompts/digest, untrusted context delimiters, forged-field isolation, and adapter result normalization.
- `src/multilang/services/lexical_grounding.py` - Exact Korean identity handoff into Portuguese definition generation and identity-owned final candidates.
- `tests/services/test_text_generation.py` - Request dump/cache separation, NFC cache/restore/fallback, forbidden output, and trusted-sense evidence.
- `tests/services/test_provider_text_adapters.py` - Prompt homographs, complete-identity digest, context privacy/injection, output normalization, authority, and request-gate evidence.
- `tests/services/test_lexical_grounding.py` - Source-before-definition ordering, exact request identity, Portuguese target, and forged-provider non-authority evidence.
- `.planning/SPEC.md` - Current State advanced through Plan 30-05 while Phase 30 remains in progress.
- `.planning/.state-fingerprint.json` - Reviewed planning-state fingerprint updated after the SPEC handoff.

## Git Actions

None. Per explicit user instruction and the carried Phase 30 execution convention, no files were staged or committed, and no branch, push, PR, amend, reset, stash, clean, checkout, restore, or other delivery/destructive action was performed.

## Decisions Made

- Korean sentence/definition requests are invalid without exact persisted identity; non-Korean requests cannot carry it, and absent identity remains omitted from generic serialized shapes.
- Korean definitions and sentence translations remain Portuguese (`pt`); this plan adds no Korean DeepL target or `ko-KR` internal route.
- Prompt prose exposes canonical trusted evidence and a digest covering the complete persisted identity, not exact submitted private/noncanonical evidence.
- Highlight context is sanitized before request validation and bounded to the established 24-token window, then sanitized again at the prompt boundary and explicitly treated as untrusted data.
- Provider `intended_sense` cannot select Korean sense identity; source `sense_id` is restored before cache, translation handoff, or bundle creation.
- Provider definition text can populate `definitions_html` only. Candidate lemma/key/POS/sense/signature/fingerprint/status remain source-owned and no approval field is accepted.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Prevented deterministic Unicode rejection from entering provider retry classification**
- **Found during:** Task 30-05-01 GREEN.
- **Issue:** Running Korean script validation inside the retry callback caused a compatibility-Hangul error containing the word `forbidden` to be classified as temporary and wrapped after three retries.
- **Fix:** Kept the provider call/retry behavior unchanged and applied deterministic Korean output validation immediately after the call but before cache/handoff.
- **Files modified:** `src/multilang/services/text_generation.py`.
- **Verification:** Task 1 compatibility tests pass for adapter and cache sources without cache writes or raw-content diagnostics.
- **Commit:** None by user instruction.

**2. [Rule 2 - Missing critical privacy boundary] Sanitized Korean highlight context before typed request/error/cache surfaces**
- **Found during:** Required privacy and high-leverage second pass.
- **Issue:** Prompt-only sanitation left a direct Korean request dump and Pydantic structured error capable of retaining raw paths, secrets, vendor dumps, and hostile identity instructions.
- **Fix:** Added pre-validation redaction/injection filtering and the existing 24-token centered bound, with prompt-boundary defense in depth and explicit untrusted delimiters.
- **Files modified:** `src/multilang/services/text_generation.py`, `src/multilang/services/provider_text_adapters.py`, `tests/services/test_provider_text_adapters.py`.
- **Verification:** Focused privacy test passes and inspects request values, JSON dumps, structured errors, and prompt content.
- **Commit:** None by user instruction.

**3. [Rule 2 - Missing critical authority enforcement] Replaced provider-authored Korean intended sense**
- **Found during:** Provider-output authority review.
- **Issue:** The legacy generic result schema allowed a provider to supply `intended_sense`, contradicting the requirement that generated output cannot author Korean sense identity.
- **Fix:** Korean adapter, cache restore, cache write, fallback, translation handoff, and bundle boundaries now use persisted `sense_id` regardless of provider content.
- **Files modified:** `src/multilang/services/text_generation.py`, `src/multilang/services/provider_text_adapters.py`, `tests/services/test_text_generation.py`, `tests/services/test_provider_text_adapters.py`.
- **Verification:** Supplemental RED produced 3 failures; GREEN produced 3 passes, and final combined evidence remains green.
- **Commit:** None by user instruction.

**Total deviations:** Three correctness/security hardenings directly required by the plan threat model. No cache architecture, provider capability, schema, endpoint, live call, production source, or later-plan scope changed.

## Issues Encountered

- The offline environment does not contain `ruff`; check and format commands reported `program not found`. Python compilation, whitespace checks, all exact plan tests, and adjacent regressions passed, and no dependency installation/network operation was attempted.
- The canonical worktree remains intentionally dirty with completed Plans 30-01 through 30-04 and unrelated carried milestone work. Lifecycle preflight was allowed with a warning; this execution touched only the listed Plan 30-05 and required planning-state files.

## Security and Privacy Review

- Complete typed identity—not surface text alone—participates in dumps and cache hashes, preventing noun/predicate and distinct-sense reuse.
- Identity prompt data is compact JSON with escaped values, ordered project-owned signatures, complete analyzer fingerprint, resolved status, and a SHA-256 digest of the complete persisted identity; no raw analyzer alternatives or vendor objects are serialized.
- Private highlight context is redacted before request validation, bounded to 24 tokens, stripped of common indirect-injection identity directives, and isolated between explicit untrusted-data delimiters.
- Korean provider output is treated as untrusted: direct adapter and generic service boundaries enforce NFC/script rules, extra identity/approval keys are ignored, and content-free `KoreanTextError` diagnostics omit rejected output.
- Definition output cannot replace candidate identity; only normalized learner-facing `definitions_html` and a safe provenance source are retained.
- No new endpoint, schema, file-access path, authentication path, network route, secret, logging payload, production corpus, or threat surface outside the plan threat register was added.

## Known Stubs

None. Synthetic reviewed identities and deterministic fakes are test evidence required by the plan, not runtime stubs. The lack of an approved production Korean lexical/frequency source remains the explicit licensing blocker for later work.

## User Setup Required

None. No provider credentials, service configuration, live capability, or network access is required for this offline contract work.

## State and Handoff

- `.planning/SPEC.md` records Plans 30-01 through 30-05 complete while Phase 30 remains in progress.
- `.planning/ROADMAP.md` remains open at `[-]` and was not modified by this execution.
- No requirement checkbox was closed; `KMODE-01`, `KMODE-02`, `KNLP-01`, and `KNLP-02` still require Plans 30-06 through 30-08 and phase verification.
- `node .planning/bin/gsdd.mjs session-fingerprint write` completed with fingerprint `5a515a4a3317d28cad3267be7ade1b72c56cdbe3a0a33c04eea7bbbfe817f46f`.
- Plan 30-06 can consume exact identity-aware generated sentences and enforce Korean morpheme-signature acceptance without reconstructing identity or trusting provider sense claims.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: All strict RED/GREEN cycles, exact task commands, combined tests, deterministic high-leverage identity/privacy selection, adjacent non-Korean regressions, text-item regressions, compilation, and scoped whitespace checks passed. Ruff was unavailable offline and was not a plan verification requirement.
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
  summary: Deterministic compatibility-Hangul validation had to run after provider retry but before cache/handoff to avoid retry misclassification.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Prompt-only context sanitation did not protect request dumps or structured validation errors, so Korean private context is now sanitized before model validation.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Legacy provider-authored intended_sense conflicted with source-sense authority and is now overwritten by persisted Korean sense_id at every handoff.
</deltas>

<judgment>
<active_constraints>
Keep `ko` as the sole internal language identity and `ko-KR` provider-only. Carry exact persisted identity through every Korean definition/sentence request and cache key. Render only canonical source evidence plus a content-free complete-identity digest in prompts. Keep Portuguese as the Korean definition/translation output. Sanitize and bound private highlight context before any dump, hash, error, prompt, or telemetry boundary. NFC/script-gate all Korean generated text before cache or durable handoff.
</active_constraints>
<unresolved_uncertainty>
No live provider quality, Korean sentence naturalness, generated-target acceptance, or repair behavior is proven here. No approved production Korean lexical/frequency source or redistribution decision exists. These remain assigned to Plan 30-06, later Phase 30 composition, Phase 32 quality work, and the licensing gate.
</unresolved_uncertainty>
<decision_posture>
Persisted source identity is immutable authority. LLM/provider output may supply normalized learner text only; it cannot choose or replace lemma, POS, source sense, register, signature, analyzer fingerprint, resolution status, or approval. Fail closed rather than accepting identityless Korean requests or unsafe provider text.
</decision_posture>
<anti_regression>
Non-Korean request models, dumps, cache keys, prompts, adapters, retries, grounding, and output-language behavior must remain unchanged. Korean private context must never reappear raw after ingress sanitation. Later plans must not reconstruct identity from surface text, trust provider intended_sense, add a Korean translation-target map, or cache provider output before NFC/script validation.
</anti_regression>
</judgment>

## Self-Check: PASSED

- All nine execution-owned files exist, including this summary, SPEC update, and planning-state fingerprint.
- Every exact task command and final combined command passed; all claims above correspond to deterministic local evidence.
- Phase 30 remains open, no Plan 30-06-or-later summary was created, and no requirement was prematurely closed.
- Required structured sections (`<checks>`, `<handoff>`, `<deltas>`, and `<judgment>`) are present and substantive.
- No git delivery/destructive action occurred; the staging area remains unchanged.

---
*Phase: 30-korean-contracts-and-morphology*
*Plan: 05*
*Completed: 2026-08-04*
