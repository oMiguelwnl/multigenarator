---
phase: 27-latin-audio-policy-and-integrity
verified: 2026-06-08T17:12:55Z
status: gaps_found
score: 3/4 must-haves verified
overrides_applied: 0
gaps:
  - truth: "Every final exported Latin MVP card has approved playable word audio and sentence audio; missing, failed, or unapproved audio blocks learner-ready export."
    status: partial
    reason: "The committed manifest currently references 100 existing nonempty RIFF WAV files, but assert_latin_audio_manifest_export_ready() does not validate storage_path safety/existence/nonempty media. A manifest with an approved exact-text artifact and missing storage_path still passes readiness."
    artifacts:
      - path: "src/multilang/services/latin_audio.py"
        issue: "_readiness_issues() checks status/text/hash but not repository-relative storage_path, file existence, file size, or WAV/playability marker."
      - path: "tests/services/test_latin_audio.py"
        issue: "No unit coverage for absolute/path-traversal/missing/empty storage_path export blockers."
    missing:
      - "Add export-readiness validation for storage_path: repository-relative/path-safe, exists under repo, nonempty, and points to actual media."
      - "Add focused tests proving absolute, unsafe, missing, and empty media paths block readiness."
  - truth: "Focused Phase 27 tests execute reliably as evidence for AUD-01/AUD-03 sample generation and provider comparison."
    status: failed
    reason: "The focused Phase 27 pytest suite fails collection because tests/services/test_latin_audio_samples.py imports FakeRunner from tests.services.test_espeak_ng_speech_adapter, but tests is not importable as a package in this environment."
    artifacts:
      - path: "tests/services/test_latin_audio_samples.py"
        issue: "Line 13 imports from tests.services.test_espeak_ng_speech_adapter; focused suite collection aborts with ModuleNotFoundError: No module named 'tests'."
    missing:
      - "Make sample tests self-contained or move FakeRunner to an importable helper module."
      - "Confirm the full focused Phase 27 test command runs green from a clean checkout."
---

# Phase 27: Latin Audio Policy and Integrity Verification Report

**Phase Goal:** Users receive approved playable word and sentence audio for every final Latin MVP card, with provider metadata, fallback reasons, and export-blocking integrity checks.  
**Verified:** 2026-06-08T17:12:55Z  
**Status:** gaps_found  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can compare candidate Latin TTS samples for representative words and sentences before the final MVP audio policy is locked. | ✓ VERIFIED | `latin_audio_samples.py` defines the representative set (`virum`, `puella`, `caesar`, `cicero`, `veni`, `quae`, `cum`, `Romae`, `Arma virumque cano.`). `27-AUDIO-PLAYBACK-REVIEW.md` records approved human playback for `espeak-ng/la/classical_approx` and Azure blocked caveat. |
| 2 | Every final exported Latin MVP card has approved playable word audio and sentence audio; missing, failed, or unapproved audio blocks learner-ready export. | ✗ PARTIAL | Current assets are present: behavioral check found 100/100 existing nonempty RIFF WAV files. However, mutating an approved artifact to `storage_path='.../missing-word.wav'` still let `assert_latin_audio_manifest_export_ready()` pass, so missing media is not export-blocking. |
| 3 | Every Latin audio artifact records provider, provider version, voice, pronunciation policy, generated text, text hash, audio kind, playback review status, and fallback reason when applicable. | ✓ VERIFIED | `LatinAudioArtifact` defines all AUD-03 fields; `latin-mvp-50-v1-audio.json` contains 50 word + 50 sentence artifacts with `espeak-ng`, `1.52.0`, `la`, `classical_approx`, exact generated text/hash, approved status, and null fallback for non-fallback eSpeak artifacts. |
| 4 | Export is blocked when persisted audio text does not match the exported target word or Latin sentence. | ✓ VERIFIED | `latin_audio.py` compares word `generated_text` to source-pack `target_form` and sentence `generated_text` to `latin_sentence`; focused tests cover word/sentence text mismatch and stale hash blockers. |

**Score:** 3/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/multilang/services/latin_audio.py` | Audio contracts, manifest loader, summary, readiness validators | ⚠️ PARTIAL | Substantive and imported by service/tests, but readiness omits media storage path/file validation. |
| `src/multilang/services/espeak_ng_speech_adapter.py` | eSpeak NG adapter | ✓ VERIFIED | Substantive adapter with version/voice discovery and `-v la -s 135 -w` synthesis command. |
| `src/multilang/services/latin_audio_samples.py` | Representative sample generation | ✓ VERIFIED | Generates sample manifest and Azure blocked comparison metadata; uses `LatinAudioArtifact`. |
| `data/latin_mvp/latin-mvp-50-v1-audio.json` | 50-card word/sentence manifest | ✓ VERIFIED | 50 pairs / 100 artifacts aligned to source pack; all approved. |
| `data/latin_mvp/audio/latin-mvp-50-v1/` | Playable media files | ✓ VERIFIED | Glob found 100 `.wav` files; behavioral check found 100/100 existing nonempty RIFF files. |
| `data/latin_mvp/latin-mvp-50-v1-curation.json` | Audio gates approved | ✓ VERIFIED | `audio_gate` entries are approved with `playback_review_approved: espeak-ng/la/classical_approx`. |
| `src/multilang/services/latin_mvp.py` | Optional public audio summary | ✓ VERIFIED | `include_audio_summary=True` loads manifest and emits aggregate counts only. |
| `src/multilang/cli.py` | `generate-latin-mvp --audio-json` | ✓ VERIFIED | CLI flag calls service with `include_audio_summary=audio_json`; spot-check returned approved aggregate counts. |
| `tests/services/test_latin_audio_samples.py` | Sample metadata tests | ✗ FAILED | Focused suite collection fails due `from tests.services...` import. |
| `tests/integration/test_v20_latin_audio_asset.py` | Real asset evidence | ✓ VERIFIED | Covers media file existence/nonempty/RIFF and text/status mutations. |
| `tests/integration/test_v20_latin_audio_evidence.py` | Scanner-readable AUD evidence | ✓ VERIFIED | Maps AUD-01..AUD-04 and checks public summaries/boundaries. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `latin_audio_samples.py` | `latin_audio.py` | `LatinAudioArtifact` models | ✓ WIRED | Imports and constructs `LatinAudioArtifact`. |
| `espeak_ng_speech_adapter.py` | `espeak-ng --voices / -v la -w` | subprocess runner abstraction | ✓ WIRED | Adapter invokes `--voices`; synthesis command includes `-v`, `voice_id`, `-w`, output path, and Latin text. |
| `27-AUDIO-PLAYBACK-REVIEW.md` | full manifest policy | review artifact handoff | ✓ WIRED | Review records approved `selected_provider=espeak-ng`, `selected_voice=la`, `pronunciation_policy=classical_approx`; manifest uses same values. |
| `latin-mvp-50-v1-audio.json` | source pack | item/text/version alignment | ✓ WIRED | Loader/readiness compares `item_key` order, `source_pack_version`, target forms, and Latin sentences. |
| `latin-mvp-50-v1-curation.json` | review gates | `audio_gate` approved | ✓ WIRED | Curation asset contains approved `audio_gate`; `load_latin_curated_records()` loads it. |
| `cli.py` | `latin_mvp.py` | `--audio-json` calls service | ✓ WIRED | CLI passes `include_audio_summary=audio_json`; output includes aggregate audio summary. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `src/multilang/cli.py` | `audio_summary` | `LatinMvpGenerationService.start(... include_audio_summary=True)` | Yes — loaded from committed `data/latin_mvp/latin-mvp-50-v1-audio.json` | ✓ FLOWING |
| `src/multilang/services/latin_mvp.py` | `audio_summary` | `load_latin_audio_manifest()` + `summarize_latin_audio_manifest()` | Yes — aggregate counts from real manifest | ✓ FLOWING |
| `src/multilang/services/latin_audio.py` | readiness blockers | source pack + audio manifest | Partial — real text/status/hash flow, but media path/file state does not flow into readiness | ⚠️ HOLLOW EDGE |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Focused Phase 27 suite runs | `PATH="/c/Program Files/eSpeak NG:$PATH" uv run pytest tests/services/test_latin_audio.py tests/services/test_espeak_ng_speech_adapter.py tests/services/test_latin_audio_samples.py tests/services/test_latin_mvp.py tests/cli/test_generate_latin_mvp_command.py tests/integration/test_v20_latin_audio_asset.py tests/integration/test_v20_latin_audio_evidence.py -q` | Collection error: `ModuleNotFoundError: No module named 'tests'` from `tests/services/test_latin_audio_samples.py:13` | ✗ FAIL |
| Phase 27 suite excluding broken sample-test import | `PATH="/c/Program Files/eSpeak NG:$PATH" uv run pytest tests/services/test_latin_audio.py tests/services/test_espeak_ng_speech_adapter.py tests/services/test_latin_mvp.py tests/cli/test_generate_latin_mvp_command.py tests/integration/test_v20_latin_audio_asset.py tests/integration/test_v20_latin_audio_evidence.py -q` | `59 passed` | ✓ PASS |
| CLI exposes public audio readiness | `uv run python -m multilang.cli generate-latin-mvp --audio-json` | JSON shows `entry_count=50`, `word_count=50`, `sentence_count=50`, `approved_count=50`, `provider_counts={"espeak-ng":100}`, `readiness_status=approved` | ✓ PASS |
| Media files exist and are nonempty RIFF WAV | Python manifest walk | `artifacts 100`, `existing_nonempty_riff 100` | ✓ PASS |
| Missing media path blocks readiness | In-memory manifest mutation changing first word `storage_path` to nonexistent file, then `assert_latin_audio_manifest_export_ready()` | Printed `bad_storage_path_readiness PASSED_UNEXPECTEDLY` | ✗ FAIL |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| AUD-01 | 27-02, 27-03, 27-05 | Compare/evaluate candidate Latin TTS providers before policy lock | ⚠️ PARTIAL | Sample generator and approved review artifact exist; however sample test module breaks focused suite collection. |
| AUD-02 | 27-01, 27-04, 27-05 | Approved playable word/sentence audio; missing/failed/unapproved blocks export | ✗ PARTIAL | 100 approved WAV files exist, but missing storage path does not block readiness. |
| AUD-03 | 27-01, 27-02, 27-04, 27-05 | Metadata fields stored for every audio artifact | ✓ SATISFIED | Manifest and Pydantic contract include provider/version/voice/policy/text/hash/kind/status/fallback. |
| AUD-04 | 27-01, 27-04, 27-05 | Text mismatch blocks export | ✓ SATISFIED | Readiness compares generated text to source-pack target form and sentence; mutation tests cover mismatch. |

No orphaned Phase 27 requirements found in `REQUIREMENTS.md`; AUD-01 through AUD-04 are all mapped to Phase 27 and declared in plan frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| `tests/services/test_latin_audio_samples.py` | 13 | Test imports another test module via `tests.services...` | 🛑 Blocker | Breaks focused Phase 27 pytest collection in this environment. |
| `src/multilang/services/latin_audio.py` | 152-183 | Readiness ignores `storage_path` file existence/safety | 🛑 Blocker | Approved manifest can pass export readiness with missing or unsafe media path. |

### Human Verification Required

None for this verification pass. The required playback human review already exists in `27-AUDIO-PLAYBACK-REVIEW.md` with `playback_review_status=approved`.

### Gaps Summary

Phase 27 substantially delivered the Latin audio policy, approved manifest, committed media, CLI summary, and text-integrity checks. Two gaps remain before the phase goal is fully achieved: the focused Phase 27 test suite is not reliably executable, and the export-readiness gate does not fail closed for missing/unsafe media paths even though AUD-02 requires missing audio to block learner-ready export.

---

_Verified: 2026-06-08T17:12:55Z_  
_Verifier: the agent (gsd-verifier)_
