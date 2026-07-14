# Quick Task 012 Plan: eSpeak Windows Autodetect

## Objective

Make the `phonemizer-espeak` pronunciation resolver automatically find the standard Windows eSpeak NG DLL installed by `winget`, without changing the established resolver order or requiring manual per-process setup.

## Task 1: Add eSpeak DLL Autodetection
<files>
- `src/multilang/services/library_pronunciation_adapters.py`
- `tests/services/test_library_pronunciation_adapters.py`
</files>
<action>
Add a small lazy helper used by the phonemizer resolver that checks whether `EspeakBackend` is already available, and if not, tries common Windows eSpeak NG DLL paths such as `C:\Program Files\eSpeak NG\libespeak-ng.dll` before calling `phonemize`. Add focused tests for the helper using monkeypatched backend/wrapper objects.
</action>
<done>
The phonemizer resolver can use an installed Windows eSpeak NG DLL without explicit manual `EspeakWrapper.set_library(...)` setup, while missing DLLs still fail only inside the resolver and allow fallback to later adapters.
</done>
<verify>
Run `uv run pytest tests/services/test_library_pronunciation_adapters.py -q`.
</verify>

## Task 2: Re-verify Pronunciation Flow
<files>
- `.planning/quick/012-espeak-windows-autodetect/012-SUMMARY.md`
- `.planning/quick/012-espeak-windows-autodetect/012-VERIFICATION.md`
- `.planning/quick/LOG.md`
</files>
<action>
Run focused pronunciation/runtime/grounding tests and a local smoke for `phonemizer-espeak` availability. Record the result and residual language-quality decision in quick-task artifacts.
</action>
<done>
Focused tests pass, local smoke proves eSpeak availability when installed, and quick-task artifacts are persisted.
</done>
<verify>
Run `uv lock --check` and `uv run pytest tests/services/test_provider_pronunciation_adapters.py tests/services/test_library_pronunciation_adapters.py tests/test_runtime.py tests/services/test_lexical_grounding.py -q`.
</verify>

## No UI Proof Rationale

This quick task changes backend pronunciation resolver configuration only and has no rendered UI surface.
