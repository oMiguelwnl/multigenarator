---
phase: 4
slug: audio-synthesis
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-28
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/services/test_azure_speech_adapter.py tests/services/test_audio_synthesis.py tests/integration/test_audio_job_flow.py -q` |
| **Full suite command** | `uv run pytest tests -q` |
| **Estimated runtime** | ~20 seconds for focused audio checks |

---

## Sampling Rate

- **After every task commit:** Run the task-specific automated command listed below.
- **After every plan wave:** Run `uv run pytest tests/services/test_azure_speech_adapter.py tests/services/test_audio_synthesis.py tests/integration/test_audio_job_flow.py -q`.
- **Before `/gsd-verify-work`:** Phase 4 verification commands and manual UAT references must remain green/current.
- **Max feedback latency:** 30 seconds for focused checks; live Azure checks are manual-only and recorded separately.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | AUDI-01, AUDI-02 | T-04-audio-contract | Separate word and sentence audio contracts stay typed and persisted independently | unit/contract | `uv run pytest tests/services/test_audio_synthesis.py -q` | ✅ | ✅ green |
| 4-02-01 | 02 | 1 | AUDI-01, AUDI-02 | T-04-voice-registry | Approved Azure voice selection and fallback remain deterministic | unit/provider | `uv run pytest tests/services/test_azure_speech_adapter.py -q` | ✅ | ✅ green |
| 4-03-01 | 03 | 2 | AUDI-01, AUDI-02 | T-04-reuse | Audio repository reuse prevents duplicate word/sentence media on resume | integration | `uv run pytest tests/integration/test_audio_job_flow.py -q` | ✅ | ✅ green |
| 4-04-01 | 04 | 2 | AUDI-01, AUDI-02 | T-04-runtime-counters | Shipped runtime reports audio counters and visible failures when no approved voice exists | cli | `uv run pytest tests/cli/test_generate_command.py -q -k 'default_runtime_reports_audio_counters or reports_failed_audio_when_no_approved_voice_exists'` | ✅ | ✅ green |
| 4-05-01 | 05 | 3 | AUDI-01 | T-04-azure-boundary | Azure adapter lists voices, synthesizes provider media, and fails visibly on credential/provider errors | provider-boundary | `uv run pytest tests/services/test_azure_speech_adapter.py -q` | ✅ | ✅ green |
| 4-05-02 | 05 | 3 | AUDI-01, AUDI-02 | T-04-live-uat | Live default-runtime Azure synthesis creates non-zero word and sentence files | manual | See `.planning/phases/04-audio-synthesis/04-HUMAN-UAT.md` | ✅ | ✅ passed |
| 4-05-03 | 05 | 3 | AUDI-01, AUDI-02 | T-04-playback-uat | Human playback confirms pronunciation quality is acceptable for learner use | manual | See `.planning/phases/04-audio-synthesis/04-HUMAN-UAT.md` | ✅ | ✅ passed |

*Status: ⬜ pending · ✅ green/passed · ❌ red · ⚠️ flaky*

---

## Evidence Source Map

| Evidence | Requirement | Source Artifact | Notes |
|----------|-------------|-----------------|-------|
| Audio contracts and synthesis validation | AUDI-01, AUDI-02 | `.planning/phases/04-audio-synthesis/04-VERIFICATION.md` | Verification rows 1 and 4 cover `AudioAssetKind`, `NormalizedTtsInput`, validation, and failed-asset conversion. |
| Voice registry and Azure adapter boundary | AUDI-01, AUDI-02 | `.planning/phases/04-audio-synthesis/04-VERIFICATION.md` | Verification rows 2, 7, and 8 reference deterministic voice plans and `tests/services/test_azure_speech_adapter.py`. |
| Audio repository reuse | AUDI-01, AUDI-02 | `.planning/phases/04-audio-synthesis/04-VERIFICATION.md` | Verification rows 3 and 6 cite reusable `(job_id,item_key,asset_kind)` identity and resume reuse. |
| Runtime audio counters | AUDI-01, AUDI-02 | `.planning/phases/04-audio-synthesis/04-VERIFICATION.md` | Behavioral spot-check uses `uv run pytest tests/cli/test_generate_command.py -q -k 'default_runtime_reports_audio_counters or reports_failed_audio_when_no_approved_voice_exists'`. |
| Live Azure synthesis and playback | AUDI-01, AUDI-02 | `.planning/phases/04-audio-synthesis/04-HUMAN-UAT.md` | Manual-only evidence records generated word/sentence `.mp3` files, CLI counters, and user playback approval. |

---

## Automated Verification Commands

The Phase 4 verification report records these current automated checks:

- `uv run pytest tests/services/test_azure_speech_adapter.py -q`
- `uv run pytest tests/services/test_audio_synthesis.py -q`
- `uv run pytest tests/cli/test_generate_command.py -q -k 'default_runtime_reports_audio_counters or reports_failed_audio_when_no_approved_voice_exists'`
- `uv run pytest tests/integration/test_audio_job_flow.py -q`

The combined non-live command used for Phase 7 evidence hygiene is:

- `uv run pytest tests/services/test_azure_speech_adapter.py tests/services/test_audio_synthesis.py tests/integration/test_audio_job_flow.py -q`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions | Status |
|----------|-------------|------------|-------------------|--------|
| Live Azure shipped-path synthesis | AUDI-01, AUDI-02 | Requires valid Azure Speech credentials and network access | Follow `.planning/phases/04-audio-synthesis/04-HUMAN-UAT.md` live smoke command and confirm non-zero word/sentence audio plus CLI counters. | ✅ passed |
| Real playback and pronunciation quality | AUDI-01, AUDI-02 | Programmatic checks cannot judge pronunciation naturalness | Play the generated `.mp3` files listed in `04-HUMAN-UAT.md` and confirm learner-use quality. | ✅ passed |

---

## Validation Sign-Off

- [x] All tasks have automated verification or documented manual-only UAT evidence.
- [x] `AUDI-01` and `AUDI-02` are mapped to audio contracts, voice registry, repository reuse, runtime counters, Azure adapter boundary, and live playback evidence.
- [x] No watch-mode flags.
- [x] Focused feedback latency remains suitable for phase-level checks.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** metadata reconstructed from verified Phase 4 evidence on 2026-04-28.
