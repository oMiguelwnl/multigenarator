# Generation Pipeline Hardening Update

This update advances the remaining generation-improvement plan without changing the exported card field schema.

Implemented flow changes:
- Frequency curation now normalizes Unicode/punctuation variants before candidate use and rejects additional web, handle, email, emoticon, symbol, and sensitive brand/name noise.
- Frequency lexical persistence rejects duplicate lemma/display forms across levels before rows are committed.
- APKG notes now include traceability tags for `multilang`, language, source type, level, rank, job, and item.
- `audit-deck` reads Anki note tags and reports missing traceability tags on frequency decks.
- Text validation includes deterministic language mismatch checks and targeted foreign-token rejection for Polish examples.
- Provider retry stops once the circuit breaker opens and records privacy-safe retry telemetry.
- Export gating blocks fallback audio by default, or reports it as partial/warning when `--allow-partial` is explicit.
- `synthesize-audio --fallback-only` regenerates only audio assets that previously used fallback voices/providers.
- Generation reports now include gate status, duplicate counts, invalid translation count, fallback audio count, provider latency averages, and APKG sha256.

Heavy language-specific morphology providers remain optional. The current validator keeps deterministic fallback behavior in tests while allowing future Stanza/Morfeusz/pymorphy adapters behind the same validation boundary.
