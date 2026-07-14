# Quick Task 011 Verification: IPA Library Resolvers

## Verdict

passed

## Goal Check

Task description: implement deterministic IPA library resolvers so `gruut` is primary for covered languages, `phonemizer`/eSpeak NG covers broad languages including `pt-BR`, `epitran` is a fallback, and AI is only the final fallback.

The runtime now builds a library-first pronunciation generator and only appends LiteLLM pronunciation when configured. The library adapter attempts `gruut`, `phonemizer-espeak`, and `epitran` in order for each supported language map, and lexical grounding falls back to the word form if every pronunciation adapter fails.

## Evidence

- Resolver-order tests prove `gruut` is first for covered languages, `phonemizer-espeak` is first when `gruut` has no language mapping, `epitran` is tried after `phonemizer-espeak`, and fallback composition stops on first success.
- Runtime tests prove local runtime uses `LibraryPronunciationAdapter`, while LiteLLM-enabled runtime wraps it in `FallbackPronunciationAdapter` before `LiteLLMPronunciationAdapter`.
- Grounding tests prove provider-generated IPA is used when authoritative IPA is missing, and word fallback is used when pronunciation generation raises.
- Dependency verification passed with `uv lock --check`.
- Focused regression command passed: `36 passed in 1.51s`.
- Current environment smoke generated `pt/casa` through `gruut` as `/kɐzɐ/` and `pl/dom` through `epitran` as `/dɔm/`.

## Residual Risk

- Native eSpeak NG is not available in this environment, so `phonemizer-espeak` fallback behavior is covered by tests but not by a live local eSpeak smoke.
- Portuguese uses `gruut` before `phonemizer-espeak` by requirement; the observed `gruut` IPA for `casa` may not satisfy strict Brazilian Portuguese expectations.
- Full project test suite was not run.
