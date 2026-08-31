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
- Media evidence now verifies structurally as a blocked aggregate rooted at `76456c7049edc187d438cc8445af4600cf63c047051ab802198567e1f7ddab1c`.
- Fresh post-recovery lane baseline verifies at `c66b72e9a05266b69d24ee491597cc2151130d459277d433b7d1b1b5ee582074`.
- AI and media lane handoffs verify in their temporary worktrees.
- Lane join and temporary merged-lane state verify.

## Gaps

- Full media byte generation remains blocked because actual Azure Speech execution is not implemented in this builder: `generate-authorized` returns `provider_execution_not_available` after loading credentials from `.env`.
- Canonical `ai-lane.json` and `media-lane.json` are updated from verified temporary handoffs rather than by running `merge-lanes` in the canonical checkout, because unrelated dirty files prevent the canonical checkout from serving as the clean integration worktree.

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
- `PYTHONPATH="/tmp/multilang-phase31-integration/src" /tmp/multilang-phase31-py312/bin/python scripts/phase31_parallel_launch.py prepare-baseline --output /tmp/multilang-phase31-parallel/baseline.json --print-sha256`
- `PYTHONPATH="/tmp/multilang-phase31-ai/src" /tmp/multilang-phase31-py312/bin/python scripts/review_korean_foundations_ai.py record-lane --baseline /tmp/multilang-phase31-parallel/baseline.json --baseline-sha256 c66b72e9a05266b69d24ee491597cc2151130d459277d433b7d1b1b5ee582074`
- `PYTHONPATH="/tmp/multilang-phase31-media/src" /tmp/multilang-phase31-py312/bin/python scripts/build_korean_foundation_media.py record-lane --baseline /tmp/multilang-phase31-parallel/baseline.json --baseline-sha256 c66b72e9a05266b69d24ee491597cc2151130d459277d433b7d1b1b5ee582074`
- `PYTHONPATH="/tmp/multilang-phase31-integration/src" /tmp/multilang-phase31-py312/bin/python scripts/phase31_parallel_launch.py verify-join --baseline /tmp/multilang-phase31-parallel/baseline.json --baseline-sha256 c66b72e9a05266b69d24ee491597cc2151130d459277d433b7d1b1b5ee582074`
- `PYTHONPATH="/tmp/multilang-phase31-integration/src" /tmp/multilang-phase31-py312/bin/python scripts/phase31_parallel_launch.py verify-merged-lanes --baseline /tmp/multilang-phase31-parallel/baseline.json --baseline-sha256 c66b72e9a05266b69d24ee491597cc2151130d459277d433b7d1b1b5ee582074`
