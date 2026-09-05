---
phase: 33-grammar-and-personal-sources
plan: "02"
runtime: opencode
assurance: self_checked
---

# Phase 33: Grammar and Personal Sources - Plan 02 Summary

**Completed**: 2026-08-30
**Tasks**: 3
**Git Actions**: none
**Deviations**:
- Did not mutate `.planning/SPEC.md`, `.planning/ROADMAP.md`, or `.planning/.state-fingerprint.json` because the user explicitly scoped execution to the listed implementation/test files plus this summary and those lifecycle files were already dirty from concurrent lanes.
**Decisions Made**:
- Korean ordered input uses an opt-in `parse_korean_ordered_word_list()` API; `parse_word_list()` keeps the existing duplicate-omission behavior for non-Korean/default use.
- Korean custom source fingerprints use `korean-ordered-source-v1`, length-framed display/duplicate-key entries, input positions, and duplicate references while leaving generic `items:<sha256>` fingerprints and run keys unchanged.
- The adaptive prerequisite policy is `korean-personal-adaptive-prereq-v1` with a deterministic threshold parameter and policy hash; decisions are explicit `bridge`, `defer`, or derived `needs_review` only.
**Notes for Verification**:
- `PersonalSourceRow` preserves every nonblank row with `input_position`, exact `submitted_form`, NFC `display_form`, duplicate key, and visible `duplicate_of_position` for repeats.
- `KoreanPersonalSourceService` resolves only through an injected resolver/source selector and returns content-free `needs_review` outcomes for ambiguity, OOV, unavailable analysis, malformed identity, non-consensus, fingerprint drift, invalid text, or resolver error.
- Bridge references are projected only after an explicit compare-and-set decision and do not mutate source rows or create generated bridge content.
**Notes for Next Work**:
- Plan 08 can persist the new row/proposal/decision identity without changing behavior.
- Later integration must keep prepared row ordering separate from export GUID semantics and must not treat bridge references as generated/approved cards without their own reviewed prerequisite IDs and authority.

## Row/Duplicate Matrix

| Input case | Parser outcome | Card-bearing behavior |
|---|---|---|
| First exact normalized Korean row | `PersonalSourceRow(disposition="card_bearing", duplicate_of_position=None)` | Eligible for lexical resolution |
| Later exact NFC/case/whitespace-normalized repeat | `PersonalSourceRow(disposition="duplicate", duplicate_of_position=<first input position>)` | Visible, not card-bearing |
| Multiple entries on one line | Monotonic `input_position` per parsed entry | Order preserved before dedupe/resolution |
| Distinct submitted Korean surfaces resolving to same lemma/POS/sense | Separate rows and stable item keys | Both remain card-bearing unless exact duplicate keys match |
| Compatibility/halfwidth Hangul | Rejected by Korean opt-in parser/service validation | No NFKC concealment or fallback |

## Fingerprint Compatibility

| Path | Behavior |
|---|---|
| Default `normalize_requested_item_keys()` / `build_input_fingerprint()` / `build_run_key()` | Unchanged set/sort duplicate-insensitive behavior for existing source modes and languages |
| Korean ordered source fingerprint | Order-sensitive and duplicate-sensitive `korean-ordered-source-v1:<sha256>` over length-framed row entries |
| Stable item identity | Uses the row duplicate key and remains separate from ordered source/run fingerprinting |

## Identity Refusal Cases

| Case | Outcome |
|---|---|
| Inflected `먹었어요` with source-backed `먹다` selection | `resolved` with submitted surface retained and analyzer/source hashes persisted |
| Compound predicate `공부하다` | `resolved` only with complete ordered morpheme signature preserved |
| Ambiguity, OOV, unavailable analysis | `needs_review` with controlled reason code |
| Missing/conflicting sense/POS, malformed signature, fingerprint drift, non-consensus | `needs_review`; no top-1, suffix, substring, whitespace, provider, or generic fallback |

## Decision Transition Table

| Input state | Command/evidence | Result |
|---|---|---|
| Resolved row within threshold | Adaptive evidence `within_threshold` | `ready`, no decision required |
| Resolved row with excessive prerequisites | Explicit bridge command with exact reviewed missing prerequisite IDs | `bridge`, projected references can appear before dependent row |
| Resolved row with excessive prerequisites | Explicit defer command | `defer`, row/position preserved and current preparation blocked |
| Unresolved identity | Any assessment | `needs_review`; bridge/defer not valid |
| Bridge/defer retry with same proposal/policy/dependencies | Same compare-and-set command | Idempotent same decision identity |
| Policy hash or prerequisite set drift | Stale compare-and-set command | Derived `needs_review` with `policy_drift` or `dependency_drift` |

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Followed RED-GREEN-REFACTOR for ordered rows/fingerprint, Korean resolution, and adaptive decisions. Verified all plan commands plus unfiltered scoped regressions passed offline with no provider/network calls.
</executor_check>
</checks>

<handoff>
plan_runtime: opencode
plan_assurance: unreviewed
plan_check_status: skipped
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: false
</handoff>

<deltas>
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Lifecycle planning files were already dirty and explicitly outside the user-approved write scope, so execution wrote only the requested plan summary instead of applying standard GSDD SPEC/ROADMAP/fingerprint updates.
</deltas>

<verification>
- RED 33-02-01: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_personal_sources.py tests/services/test_word_list_parser.py tests/services/test_input_fingerprint.py -k 'input_position or duplicate_of or ordered or reorder or nfc or compatibility or existing_language or fingerprint' -q` failed on missing `personal_sources` module and Korean ordered parser/fingerprint APIs.
- GREEN 33-02-01: same command passed with 10 passed, 9 deselected.
- RED 33-02-02: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_personal_sources.py -k 'inflected or compound or distinct_surface or ambiguity or oov or unavailable or sense or pos or signature or fingerprint or no_fallback' -q` failed on missing Korean personal-source selection/service contracts.
- GREEN 33-02-02: same command passed with 6 passed, then final plan rerun passed with 8 passed, 4 deselected after adaptive-decision tests were added.
- RED 33-02-03: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_personal_sources.py tests/services/test_korean_personal_sources.py -k 'adaptive or proposal or bridge or defer or needs_review or no_auto or idempotent or policy_drift or order' -q` failed on missing adaptive evidence and decision command contracts.
- GREEN 33-02-03: same command passed with 12 passed, 7 deselected.
- Plan verification: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_personal_sources.py tests/services/test_word_list_parser.py tests/services/test_input_fingerprint.py -k 'input_position or duplicate_of or ordered or reorder or nfc or compatibility or existing_language or fingerprint' -q` passed with 10 passed, 13 deselected.
- Plan verification: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_personal_sources.py -k 'inflected or compound or distinct_surface or ambiguity or oov or unavailable or sense or pos or signature or fingerprint or no_fallback' -q` passed with 8 passed, 4 deselected.
- Plan verification: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_personal_sources.py tests/services/test_korean_personal_sources.py -k 'adaptive or proposal or bridge or defer or needs_review or no_auto or idempotent or policy_drift or order' -q` passed with 12 passed, 7 deselected.
- Additional regression: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_word_list_parser.py tests/services/test_input_fingerprint.py -q` passed with 16 passed.
- Additional regression: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/domain/test_personal_sources.py tests/services/test_word_list_parser.py tests/services/test_input_fingerprint.py tests/services/test_korean_personal_sources.py -q` passed with 35 passed.
</verification>

<judgment>
<active_constraints>
- Korean custom lists preserve input order and every nonblank position before duplicate or lexical resolution.
- Exact duplicate outcomes remain visible via `duplicate_of_position`; only first exact normalized rows are card-bearing.
- Distinct submitted forms remain distinct rows even when source-backed lexical identity is the same.
- Korean identity remains source-backed, NFC-normalized, top-two/source-consensus gated, and fail-closed.
- Existing default parser, fingerprint, run-key, source-mode, and GUID behavior must remain unchanged.
- No provider calls, no heuristic Korean fallback, no auto bridge insertion, no adaptive queue, and no GUID migration are authorized.
</active_constraints>
<unresolved_uncertainty>
- Persistence is domain/service-only in this plan; SQL/repository adapters and lifecycle state updates remain for later coordinated work.
- Exact production resolver/source-selector integration must preserve the injected contract and controlled refusal reasons.
</unresolved_uncertainty>
<decision_posture>
- The implementation chooses additive Korean opt-in strictness over changing generic word-list behavior. Source/run fingerprinting now separates Korean ordered evidence from stable item identity so reorders and repeats are replayable without changing note GUID semantics.
</decision_posture>
<anti_regression>
- Do not sort, set-dedupe, or lemma-collapse Korean custom rows before recording input positions.
- Do not use NFKC to normalize away Compatibility/halfwidth Hangul.
- Do not resolve Korean personal-source identity from top-1 analyzer output, whitespace/suffix/substring heuristics, generic-language fallback, or provider output.
- Do not project bridge references unless an explicit local decision matches the current proposal ID, policy hash, and prerequisite IDs.
- Do not count `needs_review`, `duplicate`, or `defer` rows as card-bearing ready items.
</anti_regression>
</judgment>

## Bounded Claim

Plan 33-02 proves ordered Korean custom-source identity and explicit prerequisite-decision behavior with offline synthetic fixtures. It does not authorize provider generation, bridge content creation, audio, export publication, production database mutation, lifecycle-state mutation, or GUID migration.
