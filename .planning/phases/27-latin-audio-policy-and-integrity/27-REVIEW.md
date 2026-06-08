---
phase: 27-latin-audio-policy-and-integrity
reviewed: 2026-06-08T17:09:32Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - src/multilang/services/latin_audio.py
  - src/multilang/services/espeak_ng_speech_adapter.py
  - src/multilang/services/latin_audio_samples.py
  - src/multilang/services/latin_mvp.py
  - src/multilang/cli.py
  - data/latin_mvp/latin-mvp-50-v1-audio.json
  - data/latin_mvp/latin-mvp-50-v1-curation.json
  - tests/services/test_latin_audio.py
  - tests/services/test_espeak_ng_speech_adapter.py
  - tests/services/test_latin_audio_samples.py
  - tests/services/test_latin_mvp.py
  - tests/cli/test_generate_latin_mvp_command.py
  - tests/integration/test_v20_latin_audio_asset.py
  - tests/integration/test_v20_latin_audio_evidence.py
findings:
  critical: 0
  warning: 2
  info: 0
  total: 2
status: issues_found
---

# Phase 27: Code Review Report

**Reviewed:** 2026-06-08T17:09:32Z
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Reviewed the Phase 27 Latin audio policy/integrity implementation, committed audio/curation assets, CLI exposure, and focused/integration tests. The core exact-text/status checks are well-covered, but the phase currently has one test-suite reliability regression and one export-readiness integrity gap around media paths/files.

Verification attempted:

`uv run pytest tests/services/test_latin_audio.py tests/services/test_espeak_ng_speech_adapter.py tests/services/test_latin_audio_samples.py tests/services/test_latin_mvp.py tests/cli/test_generate_latin_mvp_command.py tests/integration/test_v20_latin_audio_asset.py tests/integration/test_v20_latin_audio_evidence.py`

Result: collection failed because `tests/services/test_latin_audio_samples.py` imports `tests.services...` but `tests` is not importable as a package in this environment.

## Warnings

### WR-01: Phase 27 test suite fails collection due to importing another test module as a package

**File:** `tests/services/test_latin_audio_samples.py:13`
**Issue:** The test imports `FakeRunner` from `tests.services.test_espeak_ng_speech_adapter`. In this repo layout, `tests` is not importable as a package during the reviewed pytest invocation, so collection fails before any Phase 27 tests run. This makes the Phase 27 verification commands unreliable.
**Fix:** Keep tests independent by moving the fake runner to a source/test helper module that is importable, or duplicate the tiny fake in this file. For example:

```python
@dataclass(frozen=True)
class FakeCompletedProcess:
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""

class FakeRunner:
    ...
```

Alternatively, add a proper `tests` package setup and verify the same command works from a clean checkout.

### WR-02: Export-readiness gate can approve manifests with missing or unsafe media paths

**File:** `src/multilang/services/latin_audio.py:175-183`
**Issue:** `assert_latin_audio_manifest_export_ready()` verifies source alignment, exact generated text, hash, and approval status, but it does not validate that `storage_path` is repository-relative, path-safe, or points to an existing nonempty audio file. A malformed manifest with `playback_review_status="approved"`, exact text/hash, and `storage_path="C:/private/missing.wav"` (or a nonexistent relative file) can pass the export-readiness gate, leading to broken exports or path disclosure risks later.
**Fix:** Add storage-path checks to readiness validation and cover absolute/path-traversal/missing/empty file cases in unit tests. For example:

```python
def _validate_audio_storage_path(path_text: str) -> bool:
    path = Path(path_text)
    return (
        not path.is_absolute()
        and "\\" not in path_text
        and ":" not in path_text
        and not path_text.startswith(("/", "~"))
        and path.exists()
        and path.stat().st_size > 0
    )
```

Then append `field=storage_path` blockers from `_readiness_issues()` when this check fails.

---

_Reviewed: 2026-06-08T17:09:32Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
