---
quick: "059"
description: "Implement real Azure Speech generation for Phase 31 Korean foundation media"
type: quick
date: 2026-09-01
assurance: plan_preview_required
no_ui_proof_rationale: Backend media generation, evidence, and governance only; no rendered UI claims.
---

# Quick Task 059: Implement Phase 31 Azure Media Generation

## Objective

Replace the Phase 31 `provider_execution_not_available` placeholder with bounded Azure Speech synthesis for approved Korean foundation audio slots, while preserving fail-closed rights, authority, evidence, and lane governance.

## Context

- Previous recovery commits through `e49fbc3` verified candidate data, AI review, media rights, authority, and lane handoffs.
- `scripts/build_korean_foundation_media.py generate-authorized` already loads `.env` through `Settings`, validates project-owner authority, and fails closed when credentials are missing.
- `src/multilang/services/azure_speech_adapter.py` already wraps Azure Speech SDK synthesis without logging credentials.
- `src/multilang/services/korean_foundation_media.py` defines exact slot metadata, storage paths, WAV validation, and active-media readiness gates.
- The existing media rights request authorizes `72` provider attempts, but the current candidate has `233` required audio slots, so a complete live run requires a refreshed rights hash and project-owner authority before synthesis.

## Scope Boundaries

- Do not touch unrelated Phase 32/33 dirty files.
- Do not print, commit, or copy credential values.
- Do not claim human listening, native-speaker, or acoustic QA approval from machine generation alone.
- Do not activate/export/publish the Korean foundation snapshot unless media validation gates already support it.
- Fail closed with explicit reason codes for missing credentials, provider failure, unsafe paths, invalid bytes, or budget/attempt exhaustion.

## Tasks

<task id="059-01" type="auto">
  <name>Add provider-execution tests</name>
  <files>
    - MODIFY: tests/services/test_korean_foundation_media_build.py
    - MODIFY: tests/services/test_ai_acoustic_review.py
    - POSSIBLY MODIFY: tests/services/test_korean_foundation_media.py
  </files>
  <action>
    Add tests that inject a fake Azure synthesizer and a small fake required-slot manifest, then verify `generate_authorized()` writes deterministic media files and a passing acoustic evidence document instead of returning `provider_execution_not_available`.
  </action>
  <verify>
    <automated>PYTHONPATH="$PWD/src" python -m pytest tests/services/test_korean_foundation_media_build.py -q</automated>
  </verify>
  <done>Tests fail first on the existing placeholder and then cover success and fail-closed provider failure behavior.</done>
</task>

<task id="059-02" type="auto">
  <name>Implement bounded Azure synthesis and evidence</name>
  <files>
    - MODIFY: scripts/build_korean_foundation_media.py
    - MODIFY: src/multilang/services/ai_acoustic_review.py
    - POSSIBLY MODIFY: src/multilang/services/azure_speech_adapter.py
    - POSSIBLY MODIFY: src/multilang/services/korean_foundation_media.py
    - MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox/media-rights.json
    - MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/execution-handoffs/media-authority.json
    - MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox/acoustic-review.json
    - CREATE/MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/evidence-inbox/media/
  </files>
  <action>
    Raise the authorized attempt ceiling to cover the exact `233` audio slots, refresh project-owner authority for the new rights hash, use the existing Azure Speech adapter to synthesize required audio slots to their manifest storage paths, generate deterministic placeholder PNG stroke assets only for required non-audio slots if already contract-safe, hash every artifact, and write an acoustic evidence aggregate that is passing only when all required slots have bytes and artifact hashes are bound. If provider execution fails, preserve a blocked aggregate with a content-free reason code.
  </action>
  <verify>
    <automated>PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_media.py generate-authorized</automated>
    <automated>PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_media.py verify-evidence</automated>
    <automated>PYTHONPATH="$PWD/src" python scripts/build_korean_foundation_media.py acoustic-status</automated>
  </verify>
  <done>`generate-authorized` no longer returns `provider_execution_not_available` when credentials are valid; evidence honestly records passing media or a provider-specific blocker.</done>
</task>

<task id="059-03" type="auto">
  <name>Refresh governance evidence and commit</name>
  <files>
    - MODIFY: .planning/quick/059-implement-phase31-azure-media-generation/059-SUMMARY.md
    - MODIFY: .planning/quick/059-implement-phase31-azure-media-generation/059-VERIFICATION.md
    - MODIFY: .planning/quick/LOG.md
    - MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/execution-handoffs/media-lane.json
    - MODIFY: .planning/phases/31-hangul-and-pronunciation-i-plus-1/execution-handoffs/ai-lane.json
  </files>
  <action>
    Record commands, outputs, evidence roots, provider blocker or success state, refresh lane handoffs if Phase 31 evidence changed, and commit only the specific source/test/evidence/Quick 059 files touched by this plan.
  </action>
  <verify>
    <automated>PYTHONPATH="$PWD/src" python -m pytest tests/services/test_korean_foundation_media_build.py tests/services/test_phase31_handoff.py tests/services/test_phase31_parallel_launch.py -q</automated>
    <automated>git diff --cached --check</automated>
  </verify>
  <done>Summary and verification exist, LOG is updated, and intended changes are committed without unrelated dirty Phase 32/33 files.</done>
</task>

## Scope Signal

This touches live provider execution and media artifacts, so it is XHigh risk despite being a bounded quick task.
