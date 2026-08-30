# Quick Task 058 Summary: Phase 31 AI Data Lane Recovery

## Status

human_needed

## Completed

- Recovered and regenerated Phase 31 Korean foundation candidate corrections in the canonical worktree.
- Final current candidate bundle: `e95c795f0e9653b67163345d8acf6d1e31228c544380e95db84342e7e1401357`.
- Final current candidate publication hash: `4f8edd966e45bf435ad38a9e79dd21759d15dc026fcd9070b1bc5fa8d6164a26`.
- Final draft manifest hash: `2cbab1150d862511a66c22a902737df1d65601a9f38351b0a97aecad852f7cf2`.
- Fixed AI-review-blocking candidate content issues: ambiguous aspirated Hangul names, `ko-hangul-0025`, `ko-hangul-0071`, `ko-hangul-0083`, `ko-pron-0020`, and `ko-pron-0043`.
- Narrowed AI phonetics review scope so internal curriculum taxonomy IDs remain deterministic-validator territory instead of phonetics claim scope.
- Regenerated AI projections and validator runs for all 139 subjects.
- Ingested 21 fresh tool-less AI review passes with no failed-attempt ledger entries.
- Verified AI aggregate: `139` passing, `0` blocked, aggregate root `9abb3d6b950e34c010ea0ed380e995cf39d653e875f43c3a2bfdc78363993922`.
- Refreshed media rights request for the final candidate; current media rights file SHA is `ab28ba11512a44e21837212da9a421c8e58832c0ba8a3b498ebe69dc197de637`.
- Added a stale-only media authority replacement command and test so a superseded single-use authority can be replaced only after the rights document hash changes.
- Recorded fresh project-owner media authority for `ab28ba11512a44e21837212da9a421c8e58832c0ba8a3b498ebe69dc197de637` after explicit user authorization.
- Ran authorized media generation; it failed closed with `azure_speech_credentials_missing` because Azure Speech credentials are not present in the environment.
- Committed Phase 31 recovery as `e6d2eae284a53376ea06b77ffd963aa64ea94f40`.
- Prepared fresh sealed post-recovery baseline `2f7438fa624cd1a3cf763eff4bf9cc19c5140771a2fcbbdda1472a8247d9d937` in `/tmp/multilang-phase31-parallel/`.
- Recorded and verified AI lane head `f0670e05711fafd1913cb58f598924c84b354ef3` and media lane head `c7abbf4c54e0865ef629e5cbcc711d52d4afc218` in temporary worktrees.
- Verified temporary lane join and merged-lane state.

## Verification

- `PYTHONPATH="$PWD/src" python -m pytest tests/services/test_ai_linguistic_review.py tests/services/test_phase31_parallel_launch.py -q` passed: `31 passed`.
- `PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_candidates.py validate-drafts` passed: `a300a5376119d3e2fb4a734390d61e2cf0c5f8db794f758c95ad4de64aa2fb78`.
- `PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_candidates.py verify-promoted --expected-draft-manifest-sha256 2cbab1150d862511a66c22a902737df1d65601a9f38351b0a97aecad852f7cf2` passed: `4f8edd966e45bf435ad38a9e79dd21759d15dc026fcd9070b1bc5fa8d6164a26`.
- `PYTHONPATH="$PWD/src" python scripts/review_korean_foundations_ai.py status` returned `complete` with `21` completed invocations.
- `PYTHONPATH="$PWD/src" python scripts/review_korean_foundations_ai.py verify` passed with aggregate root `9abb3d6b950e34c010ea0ed380e995cf39d653e875f43c3a2bfdc78363993922`.
- `PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_media.py validate-rights` passed: `ab28ba11512a44e21837212da9a421c8e58832c0ba8a3b498ebe69dc197de637`.
- `PYTHONPATH="$PWD/src" python scripts/phase31_handoff.py verify-media-authority --require-project-owner --require-unconsumed --require-voice-profile --require-provider-attempt-ceiling` passed: `media_authority_status=verified`.
- `PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_media.py generate-authorized` returned blocked aggregate root `3efdef776e3374fcacbcdf8f4b8289ffcef427702c42efc391e417690426b798` with reason `azure_speech_credentials_missing`.
- `PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_media.py verify-evidence` passed structurally with blocked aggregate root `3efdef776e3374fcacbcdf8f4b8289ffcef427702c42efc391e417690426b798`.
- `/tmp/multilang-phase31-py312/bin/python scripts/phase31_parallel_launch.py verify-join --baseline /tmp/multilang-phase31-parallel/baseline.json --baseline-sha256 2f7438fa624cd1a3cf763eff4bf9cc19c5140771a2fcbbdda1472a8247d9d937` passed: `parallel_join_status=verified`.
- `/tmp/multilang-phase31-py312/bin/python scripts/phase31_parallel_launch.py verify-merged-lanes --baseline /tmp/multilang-phase31-parallel/baseline.json --baseline-sha256 2f7438fa624cd1a3cf763eff4bf9cc19c5140771a2fcbbdda1472a8247d9d937` passed: `parallel_merged_status=verified`.

## Remaining Blockers

- Full media bytes cannot regenerate until Azure Speech credentials are present in `MULTILANG_AZURE_SPEECH_KEY` and `MULTILANG_AZURE_SPEECH_REGION`; current evidence is a verified blocked aggregate.
- Canonical lane handoff files are being updated from the verified temporary lane merge in a follow-up commit because the canonical checkout has unrelated dirty files and cannot run `merge-lanes` directly.
- The worktree contains unrelated dirty Phase 32/33 and service changes; they were not modified as part of this recovery.

## Notes

- Prompt-template hash used for the final AI review ingests: `9c85b9019d66bfbb5962e6f7ba3ef60c21a6cf039b3802c86b6bc02a73a21deb`.
- Legacy failed-attempt evidence files from the previous blocked run were removed from the AI evidence ledger because the final run has no failed attempts.
- The recreated lane handoffs have empty `changed_paths` by design: this was a recovery-after-commit baseline, not a replay of the original lost worktrees.
