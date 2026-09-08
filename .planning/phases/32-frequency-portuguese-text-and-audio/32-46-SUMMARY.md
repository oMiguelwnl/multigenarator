# Plan 32-46 Summary: Live Korean Text/Catalog Pilot

## Status

Plan 32-46 completed as non-closing Phase 32 evidence. Phase 32 remains in progress.

## Decisions Made

- Executed only the bounded `pilot_base` live text/catalog pilot for 10 Korean final-bundle candidates in local ignored SQLite.
- Kept `fallback_policy=none`, `max_items=10`, `max_concurrency=1`, `max_attempts=2`, and `cost_ceiling_usd=1.00` from provider policy `6174ebd73b7e2963285bb2e44205dde10ef9d3917e50c90850b483b3c8a6fc79`.
- Preserved the Phase 31 fallback seam only for the known `active_provenance_invalid` drift and exact approved Phase 31 tuple.
- Treated the pilot as mechanics evidence only. It does not approve generated text quality, voice profile selection, audio, production execution, review promotion, export, release, publication, or delivery.

## Work Completed

- Added setup support for `setup-korean-frequency-live-pilot-candidates`, which loads the final Korean bundle, prepares exactly 10 local candidates, advances them through ingest, and writes sanitized setup evidence.
- Added provider-policy telemetry propagation for Korean text routes and retry failure rows, including route policy, budget snapshot, cache key, and response schema hashes.
- Added Azure `ko-KR` catalog pilot capture using Azure Speech voice inventory only, with sanitized voice metadata and no synthesis.
- Added combined provider/catalog pilot validation that derives catalog hashes from the catalog result file, checks DB provider rows, verifies protected input invariance, and grants no downstream authority.
- Fixed runtime authority validation to compare `frequency_bundle_locator_sha256` with the manifest file SHA and `source_build_result_sha256` with validated build-result model bytes, matching the approved phase evidence contract.
- Fixed Korean frequency persistence so same-surface Korean final candidates are de-duplicated by morphology-aware `lemma_key` rather than `display_form`.
- Fixed `.env` parsing for `MULTILANG_SUPPORTED_LANGUAGES` values such as `[pt,ko]`.
- Fixed Azure catalog pilot logging to use an explicit `job_id` instead of expecting `KoreanFrequencyJobAuthority` to carry one.

## Evidence

- Setup result: `.planning/phases/32-frequency-portuguese-text-and-audio/evidence-inbox/live-pilot-candidate-setup.json`, file SHA-256 `d9a607cacbfc5d395019a74d2b72d5cce2ec6b75c3328528545cf4a4d3cc5200`.
- Text result: `.planning/phases/32-frequency-portuguese-text-and-audio/evidence-inbox/live-text-pilot-result.json`, file SHA-256 `b2ab3b4e1ca588f9b38e702442b7212db6a27d98f98f2fb261146c961da22ddf`.
- Azure catalog result: `.planning/phases/32-frequency-portuguese-text-and-audio/evidence-inbox/live-azure-catalog-result.json`, file SHA-256 `8341efaf3a1fab5f062f63c4934a93f3f1b4c5472b1612a4736b0125164824ec`.
- Combined validator evidence: `.planning/phases/32-frequency-portuguese-text-and-audio/evidence-inbox/live-provider-catalog-pilot-evidence.json`, file SHA-256 `325c442aec96c7503dcb4e58e496163d5da21ad92cf8872967c6a51d14e6d03b`, internal evidence SHA-256 `cdda37ba5305ed3cececffcfbaae84aab3690752c11f26d2fa615e99f54770dc`.
- Local ignored pilot DB: `.multilang/phase32/pilot/pilot-live-text-catalog.sqlite3`, file SHA-256 `90180c943c5de75f898952a31e92db6882e8485592689edeb92b163793268dcf`.
- Setup evidence records 10 candidates, 10 ingested items, zero provider attempts before live text, local ignored SQLite, no production DB, and no audio synthesis.
- Text evidence records 10 processed items, 3 accepted items, 7 review-required items, no audio synthesis, zero fallback audio items, and zero failed audio items.
- Catalog evidence records 16 live `ko-KR` voices, one successful catalog query in the evidence result, and zero synthesis attempts.
- Combined evidence records 48 provider-call rows, 48 provider attempts, zero fallback attempts, zero forbidden attempts, zero synthesis attempts, 192 required telemetry hashes, zero missing required telemetry hashes, 10 protected inputs, and zero protected-input drift.

## Commands Run

- `node .planning/bin/gsdd.mjs lifecycle-preflight execute 32 --expects-mutation phase-status` passed with warnings only.
- `git check-ignore --quiet .multilang/phase32/pilot/pilot-live-text-catalog.sqlite3` passed.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_text_generation.py tests/cli/test_korean_provider_commands.py tests/services/test_korean_provider_pilot_evidence.py tests/test_runtime.py -q` passed: 64 tests.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_provider_retry.py tests/services/test_korean_audio.py tests/repositories/test_provider_call_log_repository.py tests/services/test_korean_frequency.py tests/repositories/test_lexical_repository.py tests/test_settings.py -q` passed: 59 tests.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_frequency.py -q` passed: 19 tests.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/repositories/test_lexical_repository.py -q` passed: 10 tests.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/test_settings.py -q` passed: 12 tests.
- Setup command completed and wrote `live-pilot-candidate-setup.json`.
- Live text command completed and wrote `live-text-pilot-result.json`.
- Azure catalog command completed on the approved retry and wrote `live-azure-catalog-result.json`.
- Read-only validator completed and wrote `live-provider-catalog-pilot-evidence.json`.
- Final JSON assertion over setup, text, catalog, and combined evidence passed.

## Deviations And Notes

- The first setup attempt failed before provider/Azure calls because the route budget assertion was invoked on the budget object instead of the route object.
- Setup then exposed two authority-contract mismatches: manifest file SHA versus canonical path locator, and reviewed build-result model bytes versus formatted bundle bytes. Both are now covered by tests.
- The live text command initially failed during settings import because `.env` used a non-JSON list format for supported languages. No provider call occurred before that failure.
- The first Azure catalog attempt likely completed the voice-list fetch and then failed locally while logging because `KoreanFrequencyJobAuthority` has no `job_id`. The user approved one additional Azure `ko-KR` voice-list query; the approved retry completed and wrote evidence.
- The live text command emitted third-party startup noise from dependency initialization. The persisted evidence files remain sanitized and contain no prompts, completions, secrets, or generated text bodies.

## Boundaries

- No audio synthesis was performed.
- No production database was used.
- No generated Korean text or Portuguese translation content is published by this summary.
- No provider route, voice profile, audio, review, release, publication, or delivery authority is granted.
- No Phase 32 closure is claimed.

## Next Steps

- Plan the next Phase 32 gap closure for production DB migration, voice-profile/audio authority, production-scale generation, review/remediation, or export/release evidence.
- Keep Phase 32 open until production DB, audio, review, export, release, and delivery evidence exists.
