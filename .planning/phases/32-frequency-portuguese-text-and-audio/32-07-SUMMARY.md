---
phase: 32-frequency-portuguese-text-and-audio
plan: "07"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 07 Summary

**Completed**: 2026-08-29
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: Recoverable factual discoveries only. Existing job-repository authority binding, exact retry, zero-attempt drift rejection, and stage guards already existed, so Plan 32-07 added CLI/runtime wrappers and focused tests instead of creating a second persistence path. The generate command uses Typer's native boolean pair `--synthesize-audio/--no-synthesize-audio` rather than accepting a string boolean value.
**Decisions Made**: Korean final frequency text execution remains hash-authority-bound, offline, and explicit. No live provider/model choice, provider fallback, budget approval, Azure catalog/synthesis authority, production database target, review approval, export, release, Git action, or publication authority was created.
**Notes for Verification**: This summary proves exact fake-provider 2+1 text selection/history, generation/regeneration resumability, explicit Korean frequency text command contracts, and fresh Phase 31 verification before final runtime construction. It does not prove real Phase 31 active artifacts, Korean source rights, production 3000-entry inventory, live model quality, Azure audio, human/provider/heard review approval, Anki import/playback, or publication readiness.
**Notes for Next Work**: Continue Phase 32 offline lanes only until exact Phase 31/source/license/provider/Azure/DB authorities exist. The known adjacent out-of-plan Korean locale regression remains outside Plan 32-07 scope.

## Completed Work

- Added `KoreanTextGenerationSelector` and `KoreanTextGenerationHistory` in `src/multilang/services/korean_text_generation.py`.
- Added `KoreanSelectorAttemptContext` and threaded attempt metadata through `SentenceGenerationRequest` and `TextGenerationService.generate_bundle(...)`.
- Updated provider prompts to include only trusted orchestration metadata: rejected candidate hashes and controlled rejection codes, never raw rejected text.
- Shared selector history across batch generation and targeted regeneration with persisted `korean_selector_history` provenance.
- Preserved non-Korean text generation and regeneration behavior.
- Added `KoreanFrequencyTextRuntimeAuthority` and `build_korean_frequency_text_runtime_service(...)` to revalidate Phase 31 before loading final frequency entries and constructing runtime adapters.
- Added root CLI commands: `prepare-korean-frequency-job`, `bind-korean-frequency-audio-authority`, `check-korean-frequency-job-binding`, and `generate-korean-frequency-text`.

## 2+1 Matrix

| Stage | Count | Cache/History Contract | Failure Behavior |
|---|---:|---|---|
| Initial candidates | exactly 2 | distinct ordinal/cache attempt metadata persisted by hash | if neither validates, history records rejected candidate hashes and controlled rejection codes |
| Repair candidate | at most 1 | cache-distinct repair attempt uses prior hashes/codes only | no fourth path, no history reset, no local/Tatoeba/cross-provider fallback |
| Regeneration resume | remaining budget only | loads persisted history before selecting | failed initial history can consume only the unused repair budget |
| Non-Korean paths | unchanged | no Korean selector metadata allowed | existing generation/repair behavior preserved |

## Command Contracts

| Command | Stage | Side Effect | Authority Inputs |
|---|---|---|---|
| `prepare-korean-frequency-job` | `pilot_base` | creates/binds the explicit Korean frequency job authority if Phase 31 verifies | database/job id, Phase 31 pointer/content/receipt/snapshot hashes, bundle locator/content, source/build/review/policy/pilot hashes, binding receipt |
| `bind-korean-frequency-audio-authority` | `full` | upgrades/binds full audio/text authority through existing repository guards | all base inputs plus catalog locator/content, profile-sample, provider-review, and heard-review authority hashes |
| `check-korean-frequency-job-binding` | `full` | read-only check of persisted authority equality | same full authority tuple |
| `generate-korean-frequency-text` | `full` | builds verified runtime and calls `generate_text` | same full authority tuple plus bounded text-generation flags |

## CAS Ordering

| Step | Evidence |
|---|---|
| CLI receives explicit hashes | no `--provider`, `--model`, `--fallback-provider`, or `--phase31-path` command option exists on the new command surface |
| Runtime authority is assembled | `KoreanFrequencyTextRuntimeAuthority` carries job id, explicit bundle root, binding receipt, and frozen `KoreanFrequencyJobAuthority` |
| Phase 31 is revalidated first | `build_korean_frequency_text_runtime_service(...)` calls `verify_active_korean_foundation_snapshot_provenance(...)` before final entry loading |
| Bundle authority is reloaded | runtime helper calls `load_korean_final_frequency_entries(...)` with the explicit authority and binding receipt |
| Adapters are constructed last | runtime helper calls `build_runtime_service(...)` only after Phase 31 and bundle authority checks pass |

## TDD Evidence

- Task 32-07-01 RED: selector tests failed before `multilang.services.korean_text_generation` and `KoreanSelectorAttemptContext` existed. GREEN: `tests/services/test_korean_text_generation.py -k 'two_plus_one or repair or selector or fallback or cache or structured or PT_BR'` -> `4 passed`.
- Task 32-07-02 RED: generation/regeneration tests failed before persisted selector history and shared repair budget existed. GREEN: targeted old/new Korean tests -> `7 passed`; focused generation/regeneration selector tests -> `2 passed, 29 deselected`.
- Task 32-07-03 RED: `tests/test_runtime.py` collection failed with `ImportError: cannot import name 'KoreanFrequencyTextRuntimeAuthority'`. GREEN: focused CLI/runtime check -> `3 passed, 15 deselected`; full new CLI/runtime files -> `18 passed`.

## Verification

- Plan Task 32-07-03 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_korean_provider_commands.py tests/test_runtime.py -k 'korean and (phase31 or verify_active or binding or locator or receipt or snapshot or exact_retry or drift or pre_constructor or attempt_guard)' -q` -> `3 passed, 15 deselected`.
- Full CLI/runtime regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_korean_provider_commands.py tests/test_runtime.py -q` -> `18 passed`.
- Combined Plan 32-07 touched regression passed after clean timeout rerun: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_text_generation.py tests/services/test_generate_text_items.py tests/services/test_regenerate_text_item.py tests/cli/test_korean_provider_commands.py tests/test_runtime.py -q` -> `53 passed`.
- Planning state update: `node .planning/bin/gsdd.mjs phase-status 32 in_progress` -> unchanged/open; `node .planning/bin/gsdd.mjs session-fingerprint write` -> `40d7edbcfd03a915d50f807e57a312bdfcbbb076ce9705665bcf3c4aef7b3821`.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified Plan 32-07 offline with deterministic tests only. No live network, provider, Azure, production DB, source publication, Git commit, or release action was performed.
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
  summary: Existing `JobRepository` already provided staged Korean authority bind/load, exact retry no-op, zero-attempt drift rejection, and operation stage guards. Plan 32-07 reused it from the CLI instead of adding duplicate persistence logic.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Typer exposes boolean flags as `--synthesize-audio/--no-synthesize-audio`; the test invocation was aligned to the native CLI surface while still preserving the explicit option contract.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The first combined regression emitted `53 passed` but the shell wrapper attached inconsistent timeout metadata, so the same command was rerun with a larger timeout and passed cleanly.
</deltas>

<judgment>
<active_constraints>
Phase 32 remains in progress and phase verification is still pending. Plan 32-07 authorizes only offline exact-selection, persisted-history, and explicit command/runtime contract claims. Network, live provider, Azure, production database, source publication, Git, and release side effects still require their exact later authorities.
</active_constraints>
<unresolved_uncertainty>
Exact Phase 31 active snapshot output, NIKL source bytes/terms/attribution, local-use and redistribution decisions, real transformed 3000-entry inventory, source review, provider model/budget, Azure voice/profile/catalog, generated text/audio bytes, AI/provider/heard review outputs, production DB target authority, Anki import/playback evidence, and publication approval remain unresolved checkpoint facts.
</unresolved_uncertainty>
<decision_posture>
Keep Korean final frequency generation deterministic, bounded, hash-authority-bound, and no-fallback. Provider output is untrusted data: it may provide candidate content only through strict schemas and bounded telemetry, and it cannot assign identity, policy, approval, paths, commands, SQL, review status, or release authority.
</decision_posture>
<anti_regression>
Do not weaken exact two-initial-plus-one-repair limits, cache-distinct repair identity, hash-only rejected-candidate metadata, persisted selector history, regeneration repair-budget reuse, non-Korean behavior preservation, explicit authority CLI options, Phase 31 verification-before-loader-before-adapter ordering, repository exact-retry/drift guards, final Korean frequency entry loading, no-fallback provider route posture, canonical `pt` with provider/editorial `PT-BR`, or private/raw provider text exclusion from repair prompts and telemetry.
</anti_regression>
</judgment>
