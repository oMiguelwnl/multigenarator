# Phase 3: Sentence Quality & Review Loop - Context

**Gathered:** 2026-04-21
**Status:** Implemented and verified complete on 2026-04-21; retained as the canonical Phase 3 context record

<domain>
## Phase Boundary

Turn grounded lexical candidates into trustworthy example sentences and matching translations, then route weak outputs into a reviewable regeneration flow. This phase covers text generation, translation, automatic validation, bounded repair, confidence/review state, and targeted regeneration. Audio synthesis and Anki export remain outside this phase.

</domain>

<decisions>
## Implementation Decisions

### Runtime shape
- **D-01:** Phase 3 should extend the existing repository-backed pipeline and `multilang generate` path instead of adding a second generation workflow.
- **D-02:** Sentence generation, translation, validation, repair, and review should be modeled as a staged `generate -> validate -> repair` flow rather than one-shot text generation.

### Data separation
- **D-03:** Meaning-bearing text results should live in new persisted Phase 3 records rather than being stuffed into `lexical_candidates`, because lexical grounding and text quality are separate lifecycle stages.
- **D-04:** Translation must be generated and validated from the example sentence itself, not inferred from the headword or copied from `Definitions`.

### Quality and repair policy
- **D-05:** v1 sentence quality should target short learner-friendly examples: concise, natural, and readable, without forcing unnaturally clipped output.
- **D-06:** Automatic repair is bounded to one retry attempt. If validation still fails, the item must be flagged for review instead of looping.
- **D-07:** Validation should explicitly check lemma/form presence, sentence-length/readability rules, banned-pattern heuristics, confidence/risk flags, and translation faithfulness.

### Sentence sourcing policy
- **D-11:** If Tatoeba is used in v1, it should act only as a secondary candidate pool behind advanced filtering/reranking and validation, not as the raw primary/default sentence source.

### Review workflow
- **D-08:** The first review surface should be CLI-first and report-backed, not a new UI.
- **D-09:** Users must be able to regenerate a flagged item without rerunning the whole job, but field-level regeneration can wait until a later milestone.

### Dependency guardrail
- **D-10:** Phase 3 execution depended on Phase 2 re-verification first because Phase 3 depends directly on stable persisted lexical candidates. That dependency was satisfied before execution began on 2026-04-21.

### the agent's Discretion
- Exact provider/service boundaries for generation and translation, as long as sentence generation and sentence translation remain separate tasks.
- Exact confidence-score representation, as long as low-confidence outcomes can be persisted, inspected, and routed to review.
- Exact CLI wording for validation failures and review reports.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` - Phase 3 goal, dependency on Phase 2, and the required review/regeneration outcomes.
- `.planning/REQUIREMENTS.md` - `TEXT-01` through `TEXT-05`, plus the phase traceability table.
- `.planning/PROJECT.md` - Product constraints, supported languages, card fields, and trust-first quality expectations.
- `.planning/STATE.md` - Carry-forward decisions from Phases 1 through 3, including the single-command CLI surface, the completed review/regeneration flow, and the next-up Phase 4 focus.

### Research guidance
- `.planning/research/SUMMARY.md` - Recommends Phase 3 as a text quality engine with validation, repair, confidence scoring, and a minimal review queue.
- `.planning/research/PITFALLS.md` - Warns against coupling sentence translation to definitions and against weak quality gates.
- `.planning/research/STACK.md` - Recommends grounded generation, translation QA, and deterministic validation layers.

### Existing product contract
- `CARD_TEMPLATE.md` - Preserves `Definitions`, `Example Sentence`, and hidden/revealed `Translation` field expectations for later export phases.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/multilang/domain/jobs.py` - Already defines `JobStage.GENERATE_TEXT`, which gives Phase 3 a natural stage boundary.
- `src/multilang/db/models.py` - Already persists lexical candidates that can act as the source records for text generation.
- `src/multilang/runtime.py` and `src/multilang/cli.py` - Already provide one shipped runtime path that Phase 3 should extend instead of bypassing.
- `src/multilang/domain/lexicon.py` - Already separates lexical identity from downstream enrichment, which should stay stable while Phase 3 adds text artifacts.

### Established Patterns
- The shipped surface remains one CLI entry point: `multilang generate`.
- The codebase uses a CLI -> service -> repository split with repository-backed runtime behavior.
- Resume and rerun semantics are already important, so Phase 3 persistence should preserve deterministic item identities and stage progress.

### Integration Points
- Phase 3 should consume grounded lexical candidates after Phase 2 and persist text-generation outcomes before Phase 4 audio work begins.
- Review/regeneration should attach to stable item/card identity so a flagged item can be repaired without rerunning the full batch.
- New text-quality tables/services should extend the current job model rather than replace it.

</code_context>

<specifics>
## Specific Ideas

- Keep v1 review output CLI-first with a generated report or queue artifact that lists flagged items and why they were flagged.
- Treat sentence generation and sentence translation as separate tasks with separate validation.
- Keep the first repair loop intentionally small: one automatic retry, then review.
- Prefer a new Phase 3 persistence boundary for text results, validation flags, confidence, and review state.

</specifics>

<deferred>
## Deferred Ideas

- Full human editing UI can wait until after the CLI/report-backed review flow proves useful.
- Field-level regeneration can wait until a later milestone; v1 only needs item-level regeneration.
- Rich language-specific quality rubrics can start with shared learner-friendly defaults, then expand once benchmarks exist.

</deferred>

---

*Phase: 03-sentence-quality-review-loop*
*Context gathered: 2026-04-21*
