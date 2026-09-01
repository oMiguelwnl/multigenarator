# Phase 31: Hangul and Pronunciation i+1 - Plan 31 Summary

## Status

passed

## Completed

- Refreshed Phase 31 media rights for the exact current v2 media manifest with `325` required slots: `233` audio and `92` visual.
- Raised the bounded Azure Speech provider-attempt ceiling from `72` to `233`, matching the exact required audio slot count.
- Captured project-owner authorization for media rights hash `c00cc1d5b297bf15499a49318fcc31ab373e595167b01f7f72b47d0a6290a8c6` and consumed that single-use authority before provider effects.
- Implemented authorized media generation in `scripts/build_korean_foundation_media.py` using the existing Azure Speech adapter, safe repository-relative media paths, atomic staging, provider-failure blocking, and idempotent reuse of already verified media.
- Generated and recorded `92` deterministic project-authored PNG stroke artifacts.
- Generated and recorded `233` Azure Speech WAV artifacts with locked locale `ko-KR` and voice profile `ko-KR-SunHiNeural`.
- Bound all required artifacts into `evidence-inbox/media/artifacts.json` with content hash `07a67a70de58d27ecd1694a9c70a3c72e5cfe96f56c2fb651adadb27ee46e08a`.
- Recorded passing acoustic evidence in `evidence-inbox/acoustic-review.json` with aggregate root `1618b67d251d13a29a1c9d27ce736c5f14a23be2fd8c679ae45739fae57a4c4d`.
- Updated media authority validation so consumed authorities remain valid for evidence replay while `--require-unconsumed` still fails closed after effects.

## Verification

- `env PYTHONPATH="/home/miguel/Programming/Multilang/src" UV_PROJECT_ENVIRONMENT=".planning/.local/phase32-py312" UV_OFFLINE=1 uv run --frozen --no-sync python scripts/build_korean_foundation_media.py validate-rights` returned `c00cc1d5b297bf15499a49318fcc31ab373e595167b01f7f72b47d0a6290a8c6`.
- `env PYTHONPATH="/home/miguel/Programming/Multilang/src" UV_PROJECT_ENVIRONMENT=".planning/.local/phase32-py312" UV_OFFLINE=1 uv run --frozen --no-sync python scripts/build_korean_foundation_media.py generate-authorized` returned `status=passing`, media artifacts SHA `07a67a70de58d27ecd1694a9c70a3c72e5cfe96f56c2fb651adadb27ee46e08a`, and aggregate root `1618b67d251d13a29a1c9d27ce736c5f14a23be2fd8c679ae45739fae57a4c4d`.
- `env PYTHONPATH="/home/miguel/Programming/Multilang/src" UV_PROJECT_ENVIRONMENT=".planning/.local/phase32-py312" UV_OFFLINE=1 uv run --frozen --no-sync python scripts/build_korean_foundation_media.py verify-evidence` returned `1618b67d251d13a29a1c9d27ce736c5f14a23be2fd8c679ae45739fae57a4c4d`.
- `env PYTHONPATH="/home/miguel/Programming/Multilang/src" UV_PROJECT_ENVIRONMENT=".planning/.local/phase32-py312" UV_OFFLINE=1 uv run --frozen --no-sync python scripts/build_korean_foundation_media.py acoustic-status` returned `status=passing`, `required_slots=325`, `audio_subjects=233`, `visual_subjects=92`, `passing=325`, and `blocked=0`.
- `env PYTHONPATH="/home/miguel/Programming/Multilang/src" UV_PROJECT_ENVIRONMENT=".planning/.local/phase32-py312" UV_OFFLINE=1 uv run --frozen --no-sync python scripts/build_korean_foundation_media.py aggregate-acoustic` returned `1618b67d251d13a29a1c9d27ce736c5f14a23be2fd8c679ae45739fae57a4c4d`; the first chained invocation reached the same preceding passing checks but timed out during the final `uv` startup, so this read-only command was rerun alone.
- `env PYTHONPATH="/home/miguel/Programming/Multilang/src" UV_PROJECT_ENVIRONMENT=".planning/.local/phase32-py312" UV_OFFLINE=1 uv run --frozen --no-sync python -m pytest tests/services/test_korean_foundation_media_build.py tests/services/test_ai_acoustic_review.py tests/services/test_azure_speech_adapter.py tests/services/test_phase31_handoff.py tests/services/test_korean_foundation_review.py -q` passed: `40 passed`.
- `env PYTHONPATH="/home/miguel/Programming/Multilang/src" UV_PROJECT_ENVIRONMENT=".planning/.local/phase32-py312" UV_OFFLINE=1 uv run --frozen --no-sync python -m py_compile scripts/build_korean_foundation_media.py scripts/phase31_handoff.py` passed.
- `git diff --check` passed for the intended Phase 31 media source, tests, and evidence files.

## Claim Limits

- This plan claims rights-bound generated media bytes, hash/integrity binding, and automated acoustic evidence only.
- It does not claim human listening, native-speaker review, linguistic text approval, activation, export, publication, or device playback behavior.
- The refreshed media lane handoff is produced from a clean post-summary Phase 31 baseline because the original `/tmp/multilang-phase31-*` worktrees and baseline file were no longer available.

## Next Work

- Plan 31-32 can now consume the verified AI aggregate `9abb3d6b950e34c010ea0ed380e995cf39d653e875f43c3a2bfdc78363993922` and media aggregate `1618b67d251d13a29a1c9d27ce736c5f14a23be2fd8c679ae45739fae57a4c4d` for join, activation, and export checks.
