# Phase 2: Input Decks & Lexical Grounding - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Turn either built-in frequency decks or user-provided word lists into normalized lexical card records for the selected language. This phase covers ingestion, normalization, lexical grounding, ranking where applicable, IPA, and definitions. Example sentences, sentence translation, audio, and final Anki export remain outside this phase.

</domain>

<decisions>
## Implementation Decisions

### Lexical identity
- **D-01:** Each card should persist both a study-facing display form and an internal normalized `lemma` with lexical grounding metadata. Phase 2 should not model cards as raw input strings or as bare lemmas only.
- **D-02:** The card front should use the pedagogically appropriate study form for the language, not the bare lemma by default. Language-specific rules may keep needed context such as reflexive markers or other study-critical cues.

### Frequency deck curation
- **D-03:** Frequency decks should be built from deterministic frequency ranking with light curation, not from raw ranking alone and not from heavy manual review before Phase 2 can ship.
- **D-04:** The mandatory frequency filters should remove corpus noise, broken abbreviations or symbols, obvious proper names, and clearly bad study items, while keeping legitimate high-frequency function words when they are part of real learner vocabulary.

### Custom word-list ingestion
- **D-05:** Custom word-list items should preserve the original submitted form and also store a normalized lexical target for deduplication, grounding, and later regeneration.
- **D-06:** Phase 2 should prioritize plain-text word-list ingestion with one item per line and clear rejection or warning output. CSV or TSV input can wait.

### Missing lexical data
- **D-07:** Use a trust-first fallback policy. Do not invent IPA. Allow controlled fallback only where justified, especially for definitions, and keep provenance so weak data never looks first-party.
- **D-08:** If lexical grounding still fails after fallback attempts, frequency decks should backfill with the next valid candidate to preserve the 1000-card level targets, while custom word lists should keep the requested item and mark it as pending or insufficient instead of silently swapping it away.

### Output language policy
- **D-09:** `Definitions` should be written in English across all decks.
- **D-10:** `Translation` should target English for non-English decks. For the English deck, `Translation` should target Portuguese.

### the agent's Discretion
- Exact source-priority order across lexical providers, as long as the trust-first fallback policy is preserved.
- Exact metadata shape beyond display form, lemma, rank, and provenance, as long as it supports later sentence, audio, and export phases.
- Exact CLI wording for warnings, rejected rows, and pending-item diagnostics.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` - Phase 2 goal, dependencies, and success criteria for input decks and lexical grounding.
- `.planning/REQUIREMENTS.md` - `DECK-02`, `DECK-03`, `LEX-01`, `LEX-02`, and `LEX-03`, plus the phase traceability table.
- `.planning/PROJECT.md` - Product constraints, supported languages, requested card fields, and trust-first quality expectations.
- `.planning/STATE.md` - Carry-forward decisions from Phase 1, especially the single-command CLI surface and the decision to treat frequency decks and custom word lists as one lexical-ingestion capability.

### Research guidance
- `.planning/research/SUMMARY.md` - Recommended Phase 2 shape, deterministic enrichment direction, and open lexical-policy gaps.
- `.planning/research/STACK.md` - Frequency bootstrap guidance, lexical/IPA sourcing recommendations, and the canonical storage direction.
- `.planning/research/FEATURES.md` - Table-stakes for frequency decks, custom word-list import, and word-level enrichment.
- `.planning/research/PITFALLS.md` - Risks of raw-string lexical modeling, shipping raw frequency lists, and weak pronunciation handling.

### Existing product contract
- `CARD_TEMPLATE.md` - Current `Definitions`, `Example Sentence`, and hidden/revealed `Translation` field behavior that later phases must preserve.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/multilang/cli.py` - Already separates `frequency` and `word-list` sources and loads requested item keys through one `multilang generate` flow.
- `src/multilang/domain/jobs.py` - Already defines supported languages, source types, levels, and staged job flow that lexical ingestion must plug into.
- `src/multilang/services/input_fingerprint.py` - Already provides deterministic item normalization and run-key generation that can be extended once lexical normalization rules are defined.
- `src/multilang/services/generate_job.py` - Already treats frequency and word-list requests as one orchestration surface, which matches the locked Phase 2 direction.
- `src/multilang/repositories/job_repository.py` and `src/multilang/db/models.py` - Already persist job and item state, giving Phase 2 a stable place to connect ingestion and grounding progress.

### Established Patterns
- The shipped surface remains one CLI entry point: `multilang generate`.
- The codebase currently uses a thin CLI -> service -> repository split with deterministic rerun behavior.
- Resume and duplicate-safe rerun depend on stable normalized item identities, so lexical normalization must preserve determinism.

### Integration Points
- The placeholder frequency item generation in `src/multilang/cli.py` should be replaced by real frequency-deck ingestion.
- Lexical normalization and grounding should happen after requested items are loaded but before item processing moves deeper into later pipeline stages.
- New lexical tables and services should extend the Phase 1 job model rather than replace it, because the job lifecycle path is already verified.

</code_context>

<specifics>
## Specific Ideas

- Keep custom word-list UX close to the current CLI shape: `--input-file` with one item per line.
- A submitted custom-list item should remain inspectable in its original form even when the system resolves it to a different internal lemma or study form.
- Definitions should stay in English deck-wide.
- Sentence translations should also target English, except for the English deck where the translation target becomes Portuguese.

</specifics>

<deferred>
## Deferred Ideas

- CSV or TSV support for custom word-list import can wait until plain-text ingestion is stable.
- Stronger pedagogical curation beyond the mandatory light filters can be revisited after the first deterministic frequency pipeline exists.

</deferred>

---

*Phase: 02-input-decks-lexical-grounding*
*Context gathered: 2026-04-19*
