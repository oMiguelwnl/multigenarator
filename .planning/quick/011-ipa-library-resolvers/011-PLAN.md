# Quick Task 011 Plan: IPA Library Resolvers

## Objective
Implement deterministic IPA generation through pronunciation libraries, using `gruut` first for languages it covers, `phonemizer`/eSpeak NG for broad language coverage including `pt-BR`, `epitran` as a library fallback, and LiteLLM AI only after all library resolvers fail.

## Task 1: Add Library Pronunciation Adapter And Tests
<files>
- `src/multilang/services/library_pronunciation_adapters.py`
- `src/multilang/services/provider_pronunciation_adapters.py`
- `tests/services/test_library_pronunciation_adapters.py`
- `tests/services/test_provider_pronunciation_adapters.py`
</files>
<action>
Create a library-backed pronunciation adapter with ordered resolver maps: `gruut` first for covered languages, `phonemizer`/eSpeak NG next, `epitran` next, and a small fallback adapter that can compose library and AI adapters. Keep imports lazy so missing native binaries or optional packages fail per resolver instead of at application import time.
</action>
<done>
Library resolver tests prove `gruut` runs first for covered languages, `phonemizer` runs first for uncovered languages, `epitran` is tried after `phonemizer`, and fallback composition stops on the first successful adapter.
</done>
<verify>
Run `uv run pytest tests/services/test_library_pronunciation_adapters.py tests/services/test_provider_pronunciation_adapters.py -q`.
</verify>

## Task 2: Wire Runtime And Grounding Fallbacks
<files>
- `src/multilang/runtime.py`
- `src/multilang/services/lexical_grounding.py`
- `tests/test_runtime.py`
- `tests/services/test_lexical_grounding.py`
</files>
<action>
Update runtime pronunciation construction so library resolvers are always attempted first and LiteLLM is appended only when configured. Update lexical grounding so a pronunciation generator failure falls through to the existing word fallback instead of aborting grounding.
</action>
<done>
Runtime builds a library-first pronunciation adapter, appends LiteLLM only when configured, and grounding falls back to the word form if every pronunciation generator fails.
</done>
<verify>
Run `uv run pytest tests/test_runtime.py tests/services/test_lexical_grounding.py -q`.
</verify>

## Task 3: Add Dependencies And Lockfile
<files>
- `pyproject.toml`
- `uv.lock`
</files>
<action>
Declare `gruut`, `phonemizer`, and `epitran` dependencies and refresh the lockfile.
</action>
<done>
Project dependencies and `uv.lock` include the pronunciation libraries needed by the runtime adapter.
</done>
<verify>
Run `uv lock --check` and `uv run pytest tests/services/test_library_pronunciation_adapters.py tests/test_runtime.py tests/services/test_lexical_grounding.py -q`.
</verify>

## No UI Proof Rationale
This quick task changes backend pronunciation generation only and has no rendered UI surface.
