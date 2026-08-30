---
quick: "058"
description: "Recover Phase 31 AI candidate-data lane evidence after lost temporary worktrees"
type: quick
date: 2026-08-29
assurance: plan_preview_required
no_ui_proof_rationale: Backend data/evidence/governance recovery only; no rendered UI claims.
---

# Quick Task 058: Phase 31 AI Data Lane Recovery

## Objective

Recreate the verified Phase 31 Korean foundation candidate-data fixes in the canonical repo, update the parallel lane contract so those fixes can be recorded honestly, and determine media regeneration requirements for the new candidate hash.

## Tasks

<task id="058-01" type="auto">
  <name>Reapply candidate-data and AI-review regression fixes</name>
  <files>
    - MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/curation-drafts/*.json
    - MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/execution-handoffs/curation-selection.json
    - MODIFY: data/korean_foundations/current-candidate.json
    - CREATE: data/korean_foundations/candidate-bundles/<new-hash>/
    - MODIFY: scripts/review_korean_foundations_ai.py
    - MODIFY: tests/services/test_ai_linguistic_review.py
  </files>
  <action>
    Reapply the minimal Korean candidate-content corrections previously validated in the lost AI worktree: remove learner-facing `needs_review` placeholders from pronunciation projections, correct problematic P2/P12/P13 review content, preserve Korean learner-facing jamo names while documenting review scope, and regenerate self-hashed draft/family/manifest/current-candidate artifacts through project hash functions rather than manual JSON edits.
  </action>
  <verify>
    <automated>PYTHONPATH="$PWD/src" python -m pytest tests/services/test_ai_linguistic_review.py -q</automated>
    <automated>PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_candidates.py validate-drafts</automated>
    <automated>PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_candidates.py verify-promoted --expected-draft-manifest-sha256 "$NEW_DRAFT_MANIFEST_SHA256"</automated>
  </verify>
  <done>Current candidate points to regenerated fixed bytes and AI projection regression tests pass.</done>
</task>

<task id="058-02" type="auto">
  <name>Update lane governance and record AI evidence</name>
  <files>
    - MODIFY: scripts/phase31_parallel_launch.py
    - MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/31-30-PLAN.md
    - CREATE/MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox/ai-review/
    - CREATE/MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/execution-handoffs/ai-lane.json
  </files>
  <action>
    Amend the Phase 31 AI lane allowlist/protected-state contract only enough to admit the candidate-data corrections required by the AI review blockers. Regenerate AI projections and, if possible within this session, ingest fresh AI review passes or preserve the blocker state honestly. Record the AI lane only after aggregate verification passes.
  </action>
  <verify>
    <automated>PYTHONPATH="$PWD/src" python scripts/review_korean_foundations_ai.py project</automated>
    <automated>PYTHONPATH="$PWD/src" python scripts/review_korean_foundations_ai.py status</automated>
    <automated>PYTHONPATH="$PWD/src" python scripts/review_korean_foundations_ai.py aggregate</automated>
    <automated>PYTHONPATH="$PWD/src" python scripts/review_korean_foundations_ai.py verify</automated>
    <automated>PYTHONPATH="/tmp/multilang-phase31-ai/src" /tmp/multilang-phase31-py312/bin/python scripts/review_korean_foundations_ai.py record-lane --baseline /tmp/multilang-phase31-parallel/baseline.json --baseline-sha256 2f7438fa624cd1a3cf763eff4bf9cc19c5140771a2fcbbdda1472a8247d9d937</automated>
  </verify>
  <done>AI lane handoff records verified aggregate evidence without write-scope violation.</done>
</task>

<task id="058-03" type="auto">
  <name>Determine media regeneration path for the new candidate</name>
  <files>
    - READ: .planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox/acoustic-review.json
    - READ: .planning/phases/31-hangul-and-pronunciation-i-plus-1/execution-handoffs/media-lane.json
    - MODIFY: scripts/phase31_handoff.py
    - MODIFY: tests/services/test_phase31_handoff.py
    - MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/execution-handoffs/media-authority.json
    - POSSIBLY MODIFY: scripts/build_korean_foundation_media.py
    - POSSIBLY MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox/media-rights.json
    - POSSIBLY MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox/media/
    - POSSIBLY MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox/acoustic-review.json
  </files>
  <action>
    Compare existing media evidence bindings to the new candidate hash. If stale, report that join remains blocked until media rights/authority/acoustic evidence are regenerated against the new bundle; regenerate only if the existing scripts and local credentials make that safe and bounded.
  </action>
  <verify>
    <automated>PYTHONPATH="$PWD/src" python scripts/phase31_handoff.py verify-media-authority --require-project-owner --require-unconsumed --require-voice-profile --require-provider-attempt-ceiling</automated>
    <automated>PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_media.py generate-authorized</automated>
    <automated>PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_media.py verify-evidence</automated>
    <manual_blocker>Full media generation remains blocked if `MULTILANG_AZURE_SPEECH_KEY` and `MULTILANG_AZURE_SPEECH_REGION` are unavailable.</manual_blocker>
  </verify>
  <done>Media lane is either regenerated and verified for the new candidate or explicitly identified as the remaining join blocker.</done>
</task>

## Recovery Baseline Note

The original lane baseline and worktrees were unavailable. After explicit user approval, recovery changes were committed first and a fresh post-recovery sealed baseline was prepared from clean temporary worktrees. The resulting AI/media lane handoffs bind the verified evidence roots with empty lane patches because the recovery content is already present in baseline commit `e6d2eae284a53376ea06b77ffd963aa64ea94f40`.

## Scope Note

This is larger than a normal quick task because it recovers lost temporary worktree results and touches governance plus generated data. It is still bounded to Phase 31 Korean foundation recovery and does not activate/export/publish.
