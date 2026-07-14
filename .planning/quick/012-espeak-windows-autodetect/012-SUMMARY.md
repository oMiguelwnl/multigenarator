# Quick Task 012 Summary: eSpeak Windows Autodetect

## Status

Completed.

## What Changed

- Confirmed eSpeak NG is installed locally through `winget` at `C:\Program Files\eSpeak NG`.
- Added lazy autodetection for common Windows eSpeak NG DLL paths before `phonemizer` calls the eSpeak backend.
- Kept the resolver order unchanged: `gruut` remains first for covered languages, then `phonemizer-espeak`, then `epitran`, then configured AI fallback.
- Added a focused unit test proving the helper calls `EspeakWrapper.set_library(...)` when the backend is unavailable and a candidate DLL exists.

## Verification

Passed:

- `winget install --id eSpeak-NG.eSpeak-NG -e --accept-package-agreements --accept-source-agreements` -> package already installed, no upgrade available.
- Manual DLL validation with `EspeakWrapper.set_library(...)` -> `EspeakBackend.is_available()` became `True`, version `(1, 52, 0)`.
- `uv run pytest tests/services/test_library_pronunciation_adapters.py -q` -> `7 passed`.
- Adapter smoke without manual `set_library`: `pl/dom` and `tr/ev` resolved through `phonemizer-espeak`.
- `uv lock --check`.
- `uv run pytest tests/services/test_provider_pronunciation_adapters.py tests/services/test_library_pronunciation_adapters.py tests/test_runtime.py tests/services/test_lexical_grounding.py -q` -> `37 passed`.

Suite-wide check:

- `uv run pytest` -> `800 passed, 24 failed, 3 warnings`.
- The failures are outside this pronunciation resolver change, concentrated in Latin evidence/assets, Latin enum boundary expectations, and existing integration export/audio paths.

## Decision

- Did not change Portuguese resolver order. `phonemizer` with `pt-br` generated `casa` as `kˈazæ`, so it was not clearly better than the existing `gruut` output for the current quality target.
