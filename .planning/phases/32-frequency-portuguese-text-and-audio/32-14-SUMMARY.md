---
phase: 32-frequency-portuguese-text-and-audio
plan: "14"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 14 Summary

**Completed**: 2026-09-01
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: None blocking. The first combined final-evidence service filter exceeded the 120s command timeout after one completed test because the disposable 3000-row/6000-media APKG fixture is slow; the same filter passed with a 300s timeout. GSDD preflight/control-map reported existing canonical dirty work and detached/unannotated `/tmp/multilang-phase31-*` candidate worktrees; the preflight allowed this scoped execution and no broad cleanup or sibling worktree action was taken.
**Decisions Made**: Korean production evidence remains an offline/read-only validation surface. It derives closure evidence from exact DB rows, exact APKG bytes, exact JSON/Markdown reports, and explicit authority hashes; it grants no review application, content-promotion, release, publication, provider route, voice-profile, or synthesis authority.
**Notes for Verification**: This plan proves fake-data production run/final reconciliation, one-fact mutation refusal, protected-input invariance, content-free errors, and hash/count-only audit output. It does not prove real Korean content quality, NIKL rights, live provider calls, live Azure catalog/profile/synthesis, heard review execution, production DB execution, observed Anki import/playback, or publication readiness.
**Notes for Next Work**: Continue only with explicit upstream checkpoint authority. External production closure still needs exact Phase 31 active output, source/license/provider/Azure/DB/review evidence, fresh external recheck, and phase verification.

## Deliverables

| Surface | Result |
|---|---|
| Production evidence service | Added `src/multilang/services/korean_production_evidence.py` with read-only row loading plus `validate_korean_production_run_result` and `validate_korean_production_final_evidence`. |
| CLI contracts | Added `validate-korean-production-run-result` and `validate-korean-production-evidence` to `src/multilang/cli.py` with explicit DB, Phase 31, source/build/final-bundle/provider/review/catalog/profile/heard/binding, APKG/report/count, evidence, and audit arguments. |
| Service tests | Added `tests/services/test_korean_production_evidence.py` with disposable 3000 lexical/text rows, 6000 audio assets, provider telemetry, export rows, synthetic APKG, report sidecars, protected-input checks, and one-fact mutation failures. |
| CLI tests | Added `tests/cli/test_korean_production_evidence_commands.py` covering required flags, run/final result command wiring, no hidden provider/model/Phase31-path defaults, read-only behavior, output distinctness, and content-free failure output. |

## Row And APKG Matrix

| Evidence Family | Run Result | Final Result |
|---|---|---|
| Job authority | Requires Korean frequency job, exact Phase 31 tuple, frequency bundle hashes, and provider policy hash. | Same. |
| Lexical rows | Requires exactly 3000 grounded frequency candidates, unique item/lemma identities, ranks 1-3000, explicit persisted levels 1000/1000/1000, source/build/final-bundle authority fields. | Same. |
| Text rows | Requires 3000 passed records still `review_required`, two initial candidates, at most one repair, hard-gate pass, adaptive i+1 authority prefix evidence. | Requires 3000 passed and `accepted` records, provider-review acceptance, text application receipt, same history/hard-gate/adaptive evidence. |
| Audio rows | Requires 3000 word and 3000 sentence synthesized Azure `ko-KR` assets pending audio review, request/artifact hashes, byte counts, catalog/profile receipts, and zero fallback. | Requires the same 6000 assets approved with audio review application and heard-review receipts. |
| Provider telemetry | Requires explicit route/budget hashes, prompt/response/cache/schema hashes, attempts/retries/cache/latency/token/cost denominators, synthesis attempts, and zero fallback. | Same. |
| Export rows | Not required. | Requires 3000 card export rows, one completed APKG deck export row, exact content-promotion gate receipt, stable note GUIDs, explicit level counts, blank image field, and sound media references. |
| APKG bytes | Not required. | Reopens the exact APKG, checks media manifest count/payloads, model ID/name/fields, parent and three child deck IDs, 1000 cards per level deck, note/card counts, GUIDs, and field count. |
| Reports | Not required. | Reconciles JSON and Markdown report counts/hashes against exact authority and APKG SHA-256 while excluding raw report content from evidence output. |
| Outputs | Hash/count-only evidence JSON. | Hash/count-only evidence JSON plus JSON/Markdown audit derived from the recomputed evidence object. |

## Mutation And Invariance Proof

| Check | Coverage |
|---|---|
| Protected inputs | Every declared input file is hashed before and after validation; reused input/output paths fail before output write. |
| Read-only DB behavior | Tests snapshot table counts before validation and after success/failure; validators never import reviews, synthesize audio, export packages, or mutate rows. |
| One-fact false closures | Run mode rejects text history drift, protected input drift, Phase 31 drift, provider fallback, and premature approved audio. Final mode rejects reviewed text state drift, APKG child deck count/routing drift, and report count drift. |
| Privacy | Evidence, audit JSON, audit Markdown, and controlled CLI failure output exclude learner text, Korean text, prompts, provider payloads, credentials, file paths, `LEAK-` sentinels, and `private/audio` storage paths. |
| Authority limits | Evidence explicitly reports `grants_review_application_authority=false`, `grants_content_promotion_authority=false`, and `grants_release_authority=false`. |

## TDD Evidence

- Task 32-14-01 RED: service tests failed because `multilang.services.korean_production_evidence` did not exist.
- Task 32-14-01 GREEN: read-only row loader and run-result validator added; run-result slice passed.
- Task 32-14-02 RED: CLI tests failed because production evidence commands did not exist.
- Task 32-14-02 GREEN: run/final CLI commands and atomic output helpers added; CLI required-flag/run/final/read-only slice passed.
- Task 32-14-03 RED: final evidence tests failed because final reconciliation was unimplemented.
- Task 32-14-03 GREEN: reviewed text/audio checks, export row validation, APKG inspection, report reconciliation, and hash-only audit rendering added; final mutation slice passed.

## Verification

- Task 32-14-01 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_production_evidence.py -k 'run_result or histories or prefixes or attempts or denominators or pending_audio' -q` -> `3 passed, 2 deselected in 133.00s`.
- Task 32-14-02 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_korean_production_evidence_commands.py -k 'required_flags or run_result or final_result or no_defaults or read_only' -q` -> `4 passed in 37.47s`.
- Task 32-14-03 service command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_production_evidence.py -k 'final_evidence or mutation or apkg or review or read_only' -q` -> `4 passed, 1 deselected in 199.43s`.
- Task 32-14-03 CLI command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_korean_production_evidence_commands.py -k 'mutation or content_free' -q` -> `1 passed, 3 deselected in 21.64s`.
- Final service file passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_production_evidence.py -q` -> `5 passed in 215.60s`.
- Final CLI file passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_korean_production_evidence_commands.py -q` -> `4 passed in 27.85s`.
- Whitespace check passed: `git diff --check -- src/multilang/services/korean_production_evidence.py src/multilang/cli.py tests/services/test_korean_production_evidence.py tests/cli/test_korean_production_evidence_commands.py`.
- Planning state update: `node .planning/bin/gsdd.mjs phase-status 32 in_progress` -> unchanged/open; `node .planning/bin/gsdd.mjs session-fingerprint write` -> `8f8a7b8966a7a04dfffeab771d86dd71e3272321e0161ae07024b4e8ff1cc594`.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified exact run/final service validators, CLI contracts, protected input invariance, DB read-only behavior, content-free failure output, hash/count-only audit output, APKG/report reconciliation, and one-fact mutation refusal. No network, provider, live Azure, production DB mutation, review import/application, APKG build, release, Git, or publication action was performed.
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
  summary: The disposable final-evidence service fixture takes longer than the default 120s command timeout when several exact-scale fake APKG/database tests run together; rerunning with a 300s timeout produced stable passes.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The workspace remained broadly dirty with detached/unannotated `/tmp/multilang-phase31-*` candidate worktrees; GSDD preflight allowed the scoped Plan 32-14 write set and no unrelated cleanup or mutation was attempted.
</deltas>

<judgment>
<active_constraints>
Phase 32 remains in progress and phase verification is pending. Plan 32-14 authorizes only offline/read-only fake-data production evidence reconciliation. Network/provider calls, live Azure catalog/profile/synthesis, review import/application, production DB mutation, real APKG production, release, Git, and publication effects still require exact checkpoint authority.
</active_constraints>
<unresolved_uncertainty>
Exact Phase 31 active snapshot output, NIKL rights/source facts, transformed 3000-entry inventory, provider model/budget approval, live Azure catalog/profile/synthesis, text/audio review outputs, production DB target, real full-suite evidence, observed Anki import/playback proof, fresh external recheck, and publication approval remain unresolved.
</unresolved_uncertainty>
<decision_posture>
Production closure is evidence-driven rather than label-driven: validators reload rows/files, recompute authority and counts, inspect APKG structure, reconcile report facts, and emit only hashes/counts. The tooling deliberately refuses to grant review, promotion, release, or publication authority.
</decision_posture>
<anti_regression>
Do not treat report labels as production proof; do not infer Korean levels from rank or item key; do not allow fallback provider/audio rows in closure evidence; do not emit content, prompts, payloads, credentials, paths, or private audio locations in evidence/errors/audits; do not add review import/application, synthesis, export, release, or publication side effects to these validators; keep Phase 31 and all authority hashes explicit and fail closed on any drift.
</anti_regression>
</judgment>
