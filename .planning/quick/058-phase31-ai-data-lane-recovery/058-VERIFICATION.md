# Quick Task 058 Verification

## Verdict

human_needed

## Verified

- Final focused verification was rerun on 2026-08-30 from the canonical repo with `PYTHONPATH="$PWD/src" python ...`.
- The final Korean foundation current candidate loads as bundle `e95c795f0e9653b67163345d8acf6d1e31228c544380e95db84342e7e1401357` with `92` Hangul entries and `47` pronunciation entries.
- Candidate draft and promoted-candidate validators pass for draft manifest `2cbab1150d862511a66c22a902737df1d65601a9f38351b0a97aecad852f7cf2`.
- AI review status is complete: `21` required invocations, `21` completed, `0` missing, `0` failed-attempt files.
- AI aggregate verifies with `139` passing subjects and `0` blocked subjects.
- Media rights now validate for the final candidate.
- Project-owner media authority now verifies for the final rights SHA.
- Media evidence now verifies structurally as a blocked aggregate rooted at `3efdef776e3374fcacbcdf8f4b8289ffcef427702c42efc391e417690426b798`.

## Gaps

- Full media byte generation remains blocked by missing Azure Speech credentials: `generate-authorized` returns `azure_speech_credentials_missing`.
- Lane handoff recording remains blocked by missing temporary worktrees/baseline and the dirty canonical worktree. The lane helper requires a clean integration checkout to prepare the baseline and the fixed `/tmp/multilang-phase31-ai` or `/tmp/multilang-phase31-media` worktree paths to record lanes. This requires an explicit commit or a clean baseline strategy before `record-lane` can honestly succeed.

## Commands Run

- `PYTHONPATH="$PWD/src" python -m pytest tests/services/test_ai_linguistic_review.py tests/services/test_phase31_parallel_launch.py -q`
- `PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_candidates.py validate-drafts`
- `PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_candidates.py verify-promoted --expected-draft-manifest-sha256 2cbab1150d862511a66c22a902737df1d65601a9f38351b0a97aecad852f7cf2`
- `PYTHONPATH="$PWD/src" python scripts/review_korean_foundations_ai.py status`
- `PYTHONPATH="$PWD/src" python scripts/review_korean_foundations_ai.py verify`
- `PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_media.py validate-rights`
- `PYTHONPATH="$PWD/src" python scripts/phase31_handoff.py verify-media-authority --require-project-owner --require-unconsumed --require-voice-profile --require-provider-attempt-ceiling`
- `PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_media.py generate-authorized`
- `PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_media.py acoustic-status`
- `PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_media.py verify-evidence`
