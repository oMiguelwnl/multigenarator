# Quick Task 012 Verification: eSpeak Windows Autodetect

## Verdict

passed

## Goal Check

Task description: make `phonemizer-espeak` automatically find the standard Windows eSpeak NG DLL installed by `winget`, without changing resolver order.

The phonemizer resolver now calls a lazy helper that checks backend availability and, when needed, points `phonemizer` to common Windows eSpeak NG DLL install locations before phonemization. The established resolver order remains unchanged.

## Evidence

- Unit coverage passed for the library pronunciation adapter, including eSpeak DLL autodetection.
- Focused pronunciation/runtime/grounding regression suite passed: `37 passed in 1.88s`.
- Local smoke proved `phonemizer-espeak` now works through the adapter without manual per-process setup: `pl/dom` and `tr/ev` both returned `provider='phonemizer-espeak'`.
- Dependency lock check passed with `uv lock --check`.

## Residual Risk

- Full suite is not currently green: `uv run pytest` reported `800 passed, 24 failed, 3 warnings`.
- Observed full-suite failures appear unrelated to this change and involve missing Latin planning/data assets, Latin boundary assertions, and pre-existing export/audio integration expectations.
- Portuguese remains `gruut`-first because the `phonemizer` `pt-br` sample was not clearly better.
