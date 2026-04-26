---
phase: 04-audio-synthesis
verified: 2026-04-26T14:08:02Z
status: verified
score: 8/8 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 6/8
  gaps_closed:
    - "User receives `word_audio` for generated cards using Azure TTS or a documented fallback when a preferred voice is unavailable."
    - "User receives `sentence_audio` for generated cards using Azure TTS or a documented fallback when a preferred voice is unavailable."
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Run `multilang generate` with valid Azure Speech credentials on a small word list."
    expected: "The default runtime should create non-zero `word_audio` and `sentence_audio` files, and CLI output should report audio counters without crashing."
    why_human: "Live Azure Speech integration depends on external credentials/network and was only verified with monkeypatched provider seams in automated tests. Closed in 04-HUMAN-UAT.md with user-confirmed live runtime verification."
  - test: "Play the generated word and sentence audio for a sample card in at least one supported language."
    expected: "Both files should be playable and should pronounce the headword/example sentence naturally enough for learner use."
    why_human: "Programmatic checks can prove file creation and byte presence, but not subjective pronunciation quality or real playback behavior. Closed in 04-HUMAN-UAT.md with user-confirmed playback/pronunciation approval."
---

# Phase 4: Audio Synthesis Verification Report

**Phase Goal:** Users receive playable pronunciation audio for both the headword and the example sentence.
**Verified:** 2026-04-26T14:08:02Z
**Status:** verified
**Re-verification:** Yes — after gap closure and subsequent human UAT closure

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Phase 4 has one typed contract for separate word and sentence audio assets. | ✓ VERIFIED | Quick regression check passed: `src/multilang/domain/audio.py:15-80` still defines `AudioAssetKind`, `NormalizedTtsInput`, `AudioProvenance`, and `AudioAssetRecord` with distinct word/sentence identity. |
| 2 | Azure voice selection is deterministic for all seven supported languages. | ✓ VERIFIED | Quick regression check passed: `src/multilang/services/audio_voice_registry.py:42-103` still hard-codes ordered preferred/same-locale/alternate-locale voice plans and raises when no approved voice exists. |
| 3 | Every job item can persist separate reusable word and sentence audio rows. | ✓ VERIFIED | Quick regression check passed: `src/multilang/db/models.py:165-206` still defines `audio_assets` with unique `(job_id,item_key,asset_kind)` identity, and `src/multilang/repositories/audio_repository.py:28-122` still reuses synthesized assets by hashes/voice/format. |
| 4 | The synthesis service normalizes TTS input safely and rejects invalid media before accepting assets. | ✓ VERIFIED | `src/multilang/services/audio_synthesis.py:119-177,321-328` catches adapter failures, rejects missing/empty media, and only returns synthesized assets after integrity checks; `uv run pytest tests/services/test_audio_synthesis.py -q` passed (`6 passed`). |
| 5 | The shipped `multilang generate` path runs audio generation after accepted text and reports audio counters. | ✓ VERIFIED | `src/multilang/runtime.py:176-190,245-276` runs `GenerateAudioItemsService` after text generation, and `tests/cli/test_generate_command.py:544-639` proves fallback/failed counters are emitted on the default runtime path. |
| 6 | Interrupted or repeated runs reuse existing audio assets instead of silently duplicating them. | ✓ VERIFIED | `src/multilang/services/generate_audio_items.py:80-94` reuses prior synthesized assets before re-synthesizing; `uv run pytest tests/integration/test_audio_job_flow.py -q` passed and `tests/integration/test_audio_job_flow.py:97-167` verifies resume keeps exactly two reused assets. |
| 7 | User receives `word_audio` for generated cards using Azure TTS or a documented fallback when a preferred voice is unavailable. | ✓ VERIFIED | `src/multilang/runtime.py:245-247` now defaults to `AzureSpeechAdapter(runtime_settings)`; `src/multilang/services/azure_speech_adapter.py:41-108` fetches Azure voice inventory and synthesizes to the requested file; `tests/services/test_azure_speech_adapter.py:120-156` and `tests/cli/test_generate_command.py:544-639` verify synthesized file output, approved fallback counting, and visible failure when no approved voice exists. |
| 8 | User receives `sentence_audio` for generated cards using Azure TTS or a documented fallback when a preferred voice is unavailable. | ✓ VERIFIED | Same shipped-path closure as #7, plus `src/multilang/services/audio_synthesis.py:73-75` synthesizes both `word_asset` and `sentence_asset`; `tests/integration/test_audio_job_flow.py:134-162` verifies the default runtime creates two non-zero audio files and reuses them on resume. |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `src/multilang/domain/audio.py` | Typed audio contracts and provenance models | ✓ VERIFIED | Exists, substantive, still used by synthesis and repository layers. |
| `src/multilang/services/audio_voice_registry.py` | Versioned Azure voice registry and deterministic fallback | ✓ VERIFIED | Exists, substantive, and still drives `select_voice(...)`. |
| `src/multilang/settings.py` | Azure speech settings and registry version exposure | ✓ VERIFIED | Exists and exposes Azure credentials/output/storage settings. |
| `src/multilang/db/models.py` | ORM storage for persisted audio assets | ✓ VERIFIED | `AudioAssetModel` remains present with unique identity and job relationship. |
| `src/multilang/repositories/audio_repository.py` | Persistence boundary and reusable lookup | ✓ VERIFIED | Upsert/get/list/reuse paths remain substantive and wired. |
| `src/multilang/services/audio_synthesis.py` | Azure-first synthesis boundary with validation and visible failures | ✓ VERIFIED | Provider calls, fallback selection, integrity validation, and failed-asset conversion are implemented. |
| `src/multilang/services/generate_audio_items.py` | Runtime orchestration for accepted-text audio generation/reuse | ✓ VERIFIED | Reuse-first orchestration remains wired into the runtime path. |
| `src/multilang/services/azure_speech_adapter.py` | Real Azure Speech adapter with voice inventory lookup and file synthesis | ✓ VERIFIED | New substantive artifact; imports Azure SDK, calls voices-list endpoint, writes provider output to file. |
| `src/multilang/runtime.py` | Shipped runtime composition for real audio generation | ✓ VERIFIED | The previous hollow `_RuntimeAudioAdapter` path is gone; runtime now constructs `AzureSpeechAdapter` by default. |
| `tests/services/test_azure_speech_adapter.py` | Provider-boundary coverage | ✓ VERIFIED | Covers voice inventory caching, file synthesis, and credential failure. |
| `tests/integration/test_audio_job_flow.py` | Shipped-path proof of non-zero reusable media | ✓ VERIFIED | Confirms two audio assets are created and reused on resume. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `src/multilang/services/audio_voice_registry.py` | `src/multilang/domain/jobs.py` | `SupportedLanguage`-keyed voice resolution | ✓ WIRED | `select_voice(...)` in `src/multilang/services/audio_voice_registry.py:84-103` is keyed by `SupportedLanguage`. |
| `src/multilang/repositories/audio_repository.py` | `src/multilang/db/models.py` | unique upsert on `(job_id, item_key, asset_kind)` | ✓ WIRED | Repository queries and writes `AudioAssetModel` fields matching `uq_audio_assets_job_id_item_key_asset_kind`. |
| `src/multilang/services/audio_synthesis.py` | `src/multilang/services/audio_voice_registry.py` | deterministic voice selection/fallback | ✓ WIRED | `src/multilang/services/audio_synthesis.py:189-194` calls `select_voice(... available_voice_ids=self.adapter.available_voice_ids())`. |
| `src/multilang/runtime.py` | `src/multilang/services/azure_speech_adapter.py` | default adapter construction when no explicit test adapter is injected | ✓ WIRED | `src/multilang/runtime.py:245-247` builds `AudioSynthesisService(adapter=audio_adapter or AzureSpeechAdapter(runtime_settings), ...)`. |
| `src/multilang/services/azure_speech_adapter.py` | Azure Speech provider | voices-list HTTP call + SDK synthesis | ✓ WIRED | `src/multilang/services/azure_speech_adapter.py:47-63` calls the voices-list endpoint, and `:78-108` uses the Azure Speech SDK to synthesize audio to disk. |
| `src/multilang/cli.py` | runtime audio counters | printed CLI diagnostics | ✓ WIRED | Existing CLI audio-counter behavior still passes via `uv run pytest tests/cli/test_generate_command.py -q -k 'default_runtime_reports_audio_counters or reports_failed_audio_when_no_approved_voice_exists'` (`2 passed`). |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `src/multilang/services/generate_audio_items.py` | `text_record` / `prepared_bundle` | `TextRepository.list_accepted_records()` + `AudioRepository.get_reusable_asset()` | Yes | ✓ FLOWING |
| `src/multilang/services/audio_synthesis.py` | `voice` / `response` | `select_voice(...available_voice_ids=adapter.available_voice_ids())` + `adapter.synthesize(...)` | Yes | ✓ FLOWING |
| `src/multilang/services/azure_speech_adapter.py` | `_cached_voice_ids` / `result.audio_data` | Azure voices-list JSON payload + Azure SDK synthesis result | Yes | ✓ FLOWING |
| `src/multilang/runtime.py` | `audio_result.*` counters | `GenerateAudioItemsService.execute(...)` | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Azure adapter voice inventory and synthesis seams work | `uv run pytest tests/services/test_azure_speech_adapter.py -q` | `3 passed in 0.70s` | ✓ PASS |
| Audio synthesis handles fallback, invalid media, and provider errors | `uv run pytest tests/services/test_audio_synthesis.py -q` | `6 passed in 0.49s` | ✓ PASS |
| Default runtime reports fallback and failed-audio counters | `uv run pytest tests/cli/test_generate_command.py -q -k 'default_runtime_reports_audio_counters or reports_failed_audio_when_no_approved_voice_exists'` | `2 passed, 13 deselected in 6.07s` | ✓ PASS |
| Shipped-path runtime creates reusable non-zero audio media | `uv run pytest tests/integration/test_audio_job_flow.py -q` | `1 passed in 7.48s` | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `AUDI-01` | 04-01, 04-02, 04-03, 04-04, 04-05 | User receives `word_audio` using Azure TTS or documented fallback. | ✓ SATISFIED | Runtime now defaults to `AzureSpeechAdapter`; fallback/failure are explicit in `audio_synthesis.py`, and shipped-path tests verify non-zero word audio plus visible fallback/failure counters. |
| `AUDI-02` | 04-01, 04-02, 04-03, 04-04, 04-05 | User receives `sentence_audio` using Azure TTS or documented fallback. | ✓ SATISFIED | The same runtime/provider path synthesizes `sentence_asset`, and integration coverage verifies two audio assets exist and are reused. |

No orphaned Phase 4 requirements were found in `REQUIREMENTS.md`.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `src/multilang/runtime.py` | 102-104 | Placeholder sentence branch for flagged text rows | ℹ️ Info | User-visible text placeholder logic still exists on the text-generation side, but it is pre-existing and unrelated to the Phase 4 audio gap closure verified here. |
| `tests/cli/test_generate_command.py` | 34-50 | `FileWritingAudioAdapter` test helper | ℹ️ Info | Still present as a helper, but no longer used as evidence for the default shipped runtime path in the Phase 4 closure checks. |
| `tests/integration/test_audio_job_flow.py` | 23-39 | `FileWritingAudioAdapter` test helper | ℹ️ Info | Helper remains in the file, but the verified shipped-path test now monkeypatches `AzureSpeechAdapter` instead. |

### Human Verification Completed

### 1. Live Azure shipped-path synthesis

**Result:** Passed
**Evidence:** `.planning/phases/04-audio-synthesis/04-HUMAN-UAT.md` records the live default-runtime smoke command, successful CLI counters, and the generated non-zero word/sentence audio files under `.multilang/live-smoke-azure/audio/`.

### 2. Real playback and pronunciation quality

**Result:** Passed
**Evidence:** `.planning/phases/04-audio-synthesis/04-HUMAN-UAT.md` records the reviewed `.mp3` paths and the user's approval after the live smoke run.

### Gaps Summary

The two blocking Phase 4 gaps from the previous verification are closed. The shipped runtime no longer routes audio through the fake byte-writing stub; it now constructs `AzureSpeechAdapter` by default, the Azure dependency is declared in `pyproject.toml:11-24`, provider failures are converted into visible failed audio assets in `src/multilang/services/audio_synthesis.py:132-162`, and shipped-path tests now verify fallback/failure visibility plus reuse of non-zero audio files.

Human verification has now also been recorded in `04-HUMAN-UAT.md`, closing the remaining live-Azure and playback-quality sign-off items. Phase 4 is therefore verified complete.

Disconfirmation pass:
- **Former partial requirement:** live Azure credentials and network behavior were not exercised end-to-end during automated verification, so closure required separate human UAT now recorded in `04-HUMAN-UAT.md`.
- **Misleading passing test avoided:** helper adapters that write bytes still exist in tests, but the closure evidence now comes from tests that monkeypatch the default runtime's `AzureSpeechAdapter` path rather than treating those helpers as shipped-path proof.
- **Uncovered error path:** no automated shipped-path test exercises a real Azure voices-list timeout/credential-expiry scenario.

---

_Verified: 2026-04-26T14:08:02Z_
_Verifier: the agent (gsd-verifier)_
