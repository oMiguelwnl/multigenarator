# Phase 3 Research: Sentence Quality & Review Loop

**Phase:** 3 - Sentence Quality & Review Loop  
**Researched:** 2026-04-21  
**Status:** Ready for planning  
**Confidence:** MEDIUM-HIGH

## Research Answer

Phase 3 should extend the existing repository-backed pipeline with one persisted text-quality stage that turns grounded lexical candidates into short learner-friendly example sentences, sentence-faithful translations, and explicit review/regeneration state. The phase should use separate generation and validation responsibilities: structured sentence generation from lexical context, separate sentence translation, deterministic rule checks, one bounded repair attempt, then persistence of confidence and review flags so weak cards can be inspected and regenerated without rerunning the full batch.

## Decisions to Carry Into Planning

### Stack and provider choices
- Use **PydanticAI** for typed sentence-generation and critique workflows so outputs stay schema-shaped rather than free-form chat text.
- Use **LiteLLM** as the provider boundary for sentence generation and judging so provider routing stays isolated from the rest of the codebase.
- Use **DeepL** as the primary sentence-translation adapter for v1, with any LLM rewrite/judge pass treated as QA or repair rather than the main translation engine.
- Keep provider integrations behind explicit service interfaces so tests can use fixture adapters and never require live model calls.

### Phase-3-specific architecture
- Keep `JobStage.GENERATE_TEXT` as the top-level runtime stage and model `generate -> validate -> repair -> review` as substatus inside persisted text records instead of adding multiple new job stages.
- Add a new persisted text-quality table keyed by `(job_id, item_key)` rather than overloading `lexical_candidates`.
- Persist, at minimum: `example_sentence`, `translation_text`, sentence/translation provenance, validation flags, confidence status/score, repair attempt count, review status, and review reason.
- Keep `multilang generate` as the primary shipped operator surface; Phase 3 should extend that command instead of introducing a second generation workflow.

### Quality and validation policy
- Generate example sentences from grounded lexical context, not raw submitted strings.
- Generate sentence translations from the final example sentence, not from the headword gloss.
- Apply deterministic validation before accepting output:
  - target lemma or required study form is present
  - sentence fits a short learner-friendly length/readability band
  - banned-pattern heuristics reject robotic, placeholder, or malformed text
  - translation is non-empty and tied to the sentence, not copied from `Definitions`
  - low-confidence outcomes are explicitly flagged instead of silently shipped
- Use one bounded repair attempt; if the repaired result still fails, persist the item as review-required.

### Review and regeneration policy
- The first review surface should be CLI-first and report-backed, not UI-driven.
- Review should list the flagged item, reason, and current text payload so users can target the worst cards first.
- Regeneration should be item-level in v1: rerun the sentence/translation pipeline for one flagged item without rerunning the full batch.
- Field-level regeneration can wait until a later milestone.

## Recommended File Layout

```text
src/multilang/
  domain/text_quality.py
  repositories/text_repository.py
  services/text_generation.py
  services/text_validation.py
  services/text_review.py
  services/regenerate_text_item.py

alembic/versions/
  20260421_03_text_quality_tables.py

tests/
  domain/test_text_quality.py
  repositories/test_text_repository.py
  services/test_text_generation.py
  services/test_text_validation.py
  services/test_text_review.py
  integration/test_text_job_flow.py
```

## Concrete Design Guidance

### Persisted text-quality record
- Extend the database with a text-quality table keyed by `(job_id, item_key)`.
- Persist these fields explicitly:
  - request identity: `job_id`, `run_key`, `item_key`
  - source link: lexical candidate identity / foreign key
  - output text: `example_sentence`, `translation_text`
  - lifecycle: `generation_status`, `validation_status`, `review_status`, `repair_attempt_count`
  - diagnostics: `confidence_score`, `confidence_label`, `validation_flags`, `review_reason`
  - provenance JSON: generator, translator, judge/validator metadata, prompt/version notes

### Sentence generation boundary
- Build sentence generation from the persisted lexical candidate, including `display_form`, `lemma`, definitions, target language, and translation-target language.
- Use typed output models so the generator returns structured fields such as sentence text, intended sense note, and any self-reported uncertainty.
- Keep generation adapters isolated from CLI/runtime code.

### Translation boundary
- Treat translation as a separate adapter fed by the generated sentence.
- Do not reuse the definition text or lexical gloss as the translation value.
- Persist provider metadata so later regressions can be traced to a translation backend change.

### Validation engine
- Start with deterministic checks that are cheap and reliable in tests:
  - sentence contains the required target form or accepted study-form variant
  - sentence length sits inside a short learner-friendly band
  - banned-pattern and malformed-text rejects
  - translation is present and differs from raw definitions
- Layer critique/judge behavior on top of those checks rather than replacing them.
- Represent validation results as structured flags, not one free-form error string.

### Review and regeneration workflow
- When validation passes, persist the text row as accepted.
- When validation fails once, run one repair/regeneration attempt and validate again.
- When the second result still fails, mark the row as review-required and include machine-readable reasons.
- Expose a CLI-visible review report for flagged rows and support item-level regeneration against stable `item_key` identity.

## Common Pitfalls To Prevent In Phase 3

- Do not accept one-pass LLM generation as truth; keep the validate-and-repair loop.
- Do not translate the headword and call that the sentence translation; validate against the actual example sentence.
- Do not hide low-confidence outputs; attach explicit review state and reasons.
- Do not optimize only for shortness; keep sentences learner-friendly but still natural.
- Do not break the one-command shipped surface unless there is a concrete operator need.

## Architectural Responsibility Map

| Layer | Phase 3 Responsibility |
|------|-------------------------|
| CLI | Trigger text generation on the shipped path, print review/report diagnostics, and allow item-level regeneration |
| Domain models | Encode text outputs, confidence/review statuses, validation flags, and repair outcomes |
| Repository | Persist generated text rows and query flagged/reviewable items |
| Generation service | Produce sentence candidates from grounded lexical context |
| Translation service | Produce sentence-faithful translations from generated sentences |
| Validation service | Apply deterministic checks and capture machine-readable flags |
| Review service | Build CLI/report-backed review listings and regeneration targeting |
| Tests | Lock persistence, validator behavior, repair loop outcomes, and shipped-path CLI integration |

## Validation Architecture

Phase 3 should stay executable only with automated verification attached to every new contract.

- Use **pytest** with fixture adapters and mocked provider responses.
- Keep a quick command focused on Phase 3 boundaries:
  - `uv run pytest tests/domain/test_text_quality.py tests/repositories/test_text_repository.py tests/services/test_text_generation.py tests/services/test_text_validation.py tests/services/test_text_review.py tests/cli/test_generate_command.py -q`
- Full phase regression command:
  - `uv run pytest tests/integration/test_text_job_flow.py tests/cli/test_generate_command.py -q`

Required automated coverage:
- persisted text result contract and review-state fields
- generator output normalization from lexical candidates
- translation generation kept separate from lexical definitions
- validator positive/negative cases for lemma presence, length, and banned patterns
- one-repair-attempt behavior
- review-required routing when validation still fails
- item-level regeneration without full-job rerun
- shipped-path CLI/report behavior for flagged items

## Source Coverage Notes For Planning

This research directly supports:
- **TEXT-01** via sentence generation from grounded lexical context plus lemma-form validation
- **TEXT-02** via short learner-friendly validation rules and review-required fallback
- **TEXT-03** via separate sentence translation and sentence-faithfulness checks
- **TEXT-04** via persisted confidence/review state and CLI/report-backed review listing
- **TEXT-05** via stable item-level regeneration tied to persisted item identity

## Recommendation

Proceed to planning with five focused plans: text contracts/persistence, generation and translation adapters, validation plus repair, review/report flow, and shipped-path regeneration/integration verification.

## Sources

- `.planning/phases/03-sentence-quality-review-loop/03-CONTEXT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/research/SUMMARY.md`
- `.planning/research/STACK.md`
- `.planning/research/FEATURES.md`
- `.planning/research/PITFALLS.md`
- `CARD_TEMPLATE.md`

---

*Phase: 03-sentence-quality-review-loop*  
*Research completed: 2026-04-21*
