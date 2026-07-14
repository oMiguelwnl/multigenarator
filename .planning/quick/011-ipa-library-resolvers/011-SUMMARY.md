# Quick Task 011 Summary: IPA Library Resolvers

## Status

Completed.

## What Changed

- Added `LibraryPronunciationAdapter` with ordered deterministic resolvers: `gruut`, then `phonemizer`/eSpeak NG, then `epitran`.
- Added `FallbackPronunciationAdapter` so runtime pronunciation generation can try libraries first and LiteLLM only as the final configured fallback.
- Kept pronunciation library imports lazy so missing optional/native runtime support fails per resolver instead of breaking application imports.
- Added a Windows UTF-8 patch for `panphon` resource loading before `epitran` initialization.
- Wired runtime grounding to always use the library pronunciation adapter, appending `LiteLLMPronunciationAdapter` only when LiteLLM credentials/configuration are available.
- Updated lexical grounding so pronunciation generation failures fall back to the word form instead of aborting grounding.
- Declared `gruut`, `phonemizer`, and `epitran` dependencies and refreshed `uv.lock`.
- Added focused tests for resolver order, fallback composition, runtime wiring, and grounding fallback behavior.

## Verification

Passed:

- `uv lock --check`
- `uv run pytest tests/services/test_provider_pronunciation_adapters.py tests/services/test_library_pronunciation_adapters.py tests/test_runtime.py tests/services/test_lexical_grounding.py -q` -> `36 passed`
- `PYTHONIOENCODING=utf-8 uv run python -c "from multilang.services.library_pronunciation_adapters import LibraryPronunciationAdapter; from multilang.services.provider_pronunciation_adapters import PronunciationGenerationRequest; adapter=LibraryPronunciationAdapter(); req=lambda lang, word: PronunciationGenerationRequest(target_language=lang, display_form=word, lemma=word, definitions_html=''); pt=adapter.generate_pronunciation(req('pt','casa')); pl=adapter.generate_pronunciation(req('pl','dom')); print({'pt': (pt.ipa, pt.provenance['provider']), 'pl': (pl.ipa, pl.provenance['provider'])})"` -> `{'pt': ('/kɐzɐ/', 'gruut'), 'pl': ('/dɔm/', 'epitran')}`
- `PYTHONIOENCODING=utf-8 uv run python -c "from phonemizer.backend import EspeakBackend; print(EspeakBackend.is_available())"` -> `False`

## Notes

- Plan check passed with no issues.
- `phonemizer` is configured, but `phonemizer-espeak` requires native eSpeak NG support in the runtime environment. This local environment currently reports eSpeak unavailable.
- `gruut` resolves Portuguese first per the requested order; current smoke output for `pt/casa` is `/kɐzɐ/`, which may be Portuguese-variant sensitive if strict `pt-BR` output becomes mandatory.
- Full test suite was not run; verification used the focused pronunciation/runtime/grounding suite.
