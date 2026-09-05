---
phase: 32-frequency-portuguese-text-and-audio
plan: "08"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 08 Summary

**Completed**: 2026-08-29
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: Recoverable fast-track simplification only. The plan asked for offline contracts and fake catalog/audio behavior; implementation added strict service seams and CLI surfaces without performing live Azure calls, schema migrations, or production DB authority work.
**Decisions Made**: Korean text review and audio work remain hash-only, authority-gated, no-fallback, and pending-review until later checkpoint authorities exist. Korean still has no static voice registry entry.
**Notes for Verification**: This summary proves bounded review import/application contracts, explicit command surfaces, fake catalog ordering, neutral Korean SSML/request hashing, synthesized-pending asset identity, and exact approved-reuse gates. It does not prove live Azure catalog/synthesis, heard approval, production review application, Phase 31 active output, or final export readiness.
**Notes for Next Work**: Continue offline `32-09` unless it reaches a live/provider/production authority gate. Keep the known adjacent out-of-plan Korean locale regression separate.

## Completed Work

- Added `src/multilang/services/korean_text_review.py` with bounded batch decisions, idempotent import ledger, aggregate model, mode-specific application authority, prestate hash checks, and reject/promote application service.
- Added `src/multilang/services/korean_audio.py` with Korean audio authority, Azure catalog voice/result/profile contracts, Phase-31-before-adapter catalog capture ordering, neutral `ko-KR` SSML request construction, synthesized-pending audio asset construction, and exact reuse checks.
- Added `synthesis_request_sha256` to `NormalizedTtsInput`.
- Tightened reusable audio lookup to exclude fallback assets and made Korean reuse require exact reviewed profile/catalog/request/artifact/review identity.
- Added CLI surfaces for text review import/application, offline catalog readiness, and Korean frequency audio synthesis delegation.

## Review Mutation Matrix

| Mode | Required Power | Mutates | Blocks |
|---|---|---|---|
| `reject_only` | `remediation` | exact rejected rows only; accepted decisions are not promoted | wrong power, aggregate drift, prestate drift, stale candidate hash |
| `promote` | `initial_content_promotion` or `final_content_promotion` | exact accepted rows only | any rejection, wrong power, aggregate drift, prestate drift, stale candidate hash |
| import | review receipt only | content-free receipt ledger only | extra/private fields, over-100 decisions, unknown or stale current row |

## Catalog And Audio Proof

| Surface | Contract |
|---|---|
| Static registry | `select_voice(SupportedLanguage.KO, ...)` still raises; Korean needs live/fake catalog evidence |
| Catalog capture | endpoint validation and Phase 31 verification run before adapter construction/fetch |
| SSML | NFC text, XML escaping, `xml:lang="ko-KR"`, no external-resource tags |
| Asset identity | Azure provider, `ko-KR`, profile hash, catalog receipt, request hash, artifact hash, SDK version |
| Review state | provider success becomes `synthesized_pending`, not approval |
| Reuse | requires non-fallback synthesized approved asset with exact profile/catalog/request/artifact/review identity |

## TDD Evidence

- RED observed: `tests/services/test_korean_text_review_application.py` failed with `ModuleNotFoundError: multilang.services.korean_text_review`.
- RED observed: `tests/services/test_korean_audio.py` failed with `ModuleNotFoundError: multilang.services.korean_audio`.
- GREEN: combined focused Plan 32-08 command -> `10 passed, 1 deselected`.

## Verification

- Task 32-08-01 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_text_review_application.py tests/cli/test_korean_provider_commands.py -k 'text_review and (batch or bounded or exact_retry or ledger or final_promote or authority or rollback or mutation)' -q` -> `3 passed, 5 deselected`.
- Task 32-08-02 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_audio.py -k 'catalog or profile or static_registry or job or authority or zero_attempt or wrong_receipt or locator' -q` -> `1 passed, 2 deselected`.
- Task 32-08-03 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_audio.py -k 'synthesize or neutral or phase31 or pending or integrity or reuse or both or fallback or resume or pre_constructor' -q` -> `2 passed, 1 deselected`.
- Combined focused command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_text_review_application.py tests/services/test_korean_audio.py tests/cli/test_korean_provider_commands.py -k 'text_review and (batch or bounded or exact_retry or ledger or final_promote or authority or rollback or mutation) or catalog or profile or static_registry or job or authority or zero_attempt or wrong_receipt or locator or synthesize or neutral or phase31 or pending or integrity or reuse or both or fallback or resume or pre_constructor' -q` -> `10 passed, 1 deselected`.
- Audio regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_text_review_application.py tests/services/test_korean_audio.py tests/cli/test_korean_provider_commands.py tests/services/test_audio_synthesis.py tests/services/test_generate_audio_items.py tests/repositories/test_audio_repository.py tests/domain/test_audio.py -q` -> `38 passed`.
- Whitespace check passed: `git diff --check -- tests/services/test_korean_text_review_application.py tests/services/test_korean_audio.py tests/cli/test_korean_provider_commands.py src/multilang/services/korean_text_review.py src/multilang/services/korean_audio.py src/multilang/domain/audio.py src/multilang/services/generate_audio_items.py src/multilang/repositories/audio_repository.py src/multilang/cli.py`.
- Planning state update: `node .planning/bin/gsdd.mjs phase-status 32 in_progress` -> unchanged/open; `node .planning/bin/gsdd.mjs session-fingerprint write` -> `465fc23d10bf2f041632adada8fa33c33182e03e232fc6c75720ea99a5142599`.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified Plan 32-08 offline with deterministic tests only. No live Azure catalog query, synthesis, production DB mutation, provider call, review approval, Git commit, release, or publication action was performed.
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
  summary: Existing audio models already had profile/catalog/review fields, so Plan 32-08 added `synthesis_request_sha256` and exact Korean service/reuse gates rather than creating a new storage schema.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Korean was already absent from the static voice registry; Plan 32-08 locked that behavior with regression coverage.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Fast-track preserved no-live-call boundaries by exposing CLI seams and offline readiness/delegation behavior instead of attempting real Azure catalog capture or synthesis.
</deltas>

<judgment>
<active_constraints>
Phase 32 remains in progress and phase verification is pending. Plan 32-08 authorizes only offline review/audio contract claims. Network, live provider, Azure, production database, review approval, export, release, Git, and publication effects still require exact later authorities.
</active_constraints>
<unresolved_uncertainty>
Exact Phase 31 active snapshot output, NIKL source rights and transformed 3000-entry inventory, source review, provider model/budget, live Azure voice/profile/catalog, generated audio bytes, AI/provider/heard review outputs, production DB target authority, Anki import/playback evidence, and publication approval remain unresolved checkpoint facts.
</unresolved_uncertainty>
<decision_posture>
Keep text review mutation and Korean audio side effects subordinate to exact hash authorities. Provider/Azure success is not approval; final reuse/export requires exact reviewed identity and non-fallback assets.
</decision_posture>
<anti_regression>
Do not weaken review batch bounds, extra-field rejection, content-free receipts, mode-specific remediation versus promotion powers, prestate/candidate CAS, Korean absence from static voice registry, Phase-31-before-Azure ordering, neutral escaped Korean SSML, `ko-KR` locale requirement, synthesized-pending state, no-fallback audio, exact approved-reuse identity, or separation between provider success and heard/review approval.
</anti_regression>
</judgment>
