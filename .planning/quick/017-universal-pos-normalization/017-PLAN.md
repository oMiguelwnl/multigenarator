# Quick Task 017: Universal POS Normalization

## Objective

Centralize part-of-speech normalization and deterministic function-word inference so learner-facing definitions use a consistent `[part of speech]: [meaning]` label across all supported modern languages instead of German-only special cases or weak `term:` fallbacks.

## Scope

- Keep the change in the modern-language text/lexical grounding path.
- Do not change Anki field order, templates, provider prompts, database schema, or frequency assets.
- Preserve trusted asset/provider POS when it is already canonical.
- Use deterministic function-word maps only for high-confidence closed-class words.

## No UI Proof Rationale

This is a backend/service normalization task. There is no rendered UI surface to validate.

## Tasks

### Task 1: Add Shared POS Contract

<files>
- `src/multilang/services/part_of_speech.py`
- `src/multilang/services/text_field_remediation.py`
- `src/multilang/services/lexical_grounding.py`
</files>

<action>
- Create a shared service module for canonical POS labels, alias normalization, and supported-label checks.
- Replace duplicated POS label sets in remediation and lexical grounding with the shared contract.
- Keep public helpers small and explicit so tests can assert the contract directly.
</action>

<done>
- Remediation and lexical grounding import the same POS contract instead of maintaining separate label lists.
- Existing focused tests for remediation and grounding still pass after the shared contract is introduced.
</done>

<verify>
- `uv run pytest tests/services/test_text_field_remediation.py tests/services/test_lexical_grounding.py -q`
</verify>

### Task 2: Add Multilingual Function-Word Inference

<files>
- `src/multilang/services/part_of_speech.py`
- `src/multilang/services/text_field_remediation.py`
- `tests/services/test_text_field_remediation.py`
</files>

<action>
- Move German deterministic function-word inference into the shared POS module.
- Add high-confidence closed-class words for Portuguese, Spanish, English, French, German, Italian, Polish, Turkish, Romanian, Russian, and Dutch.
- Ensure inference is used before accepting weak provider/fallback labels when source POS is missing or unknown.
</action>

<done>
- Supported-language function words that are present in the deterministic map produce canonical POS labels when source POS is missing or unknown.
- Unknown/content words continue to fall back to provider labels or `term:` rather than being guessed.
</done>

<verify>
- `uv run pytest tests/services/test_text_field_remediation.py -q`
</verify>

### Task 3: Regression Tests And Workflow Evidence

<files>
- `tests/services/test_text_field_remediation.py`
- `tests/services/test_lexical_grounding.py`
- `.planning/quick/017-universal-pos-normalization/017-SUMMARY.md`
- `.planning/quick/017-universal-pos-normalization/017-VERIFICATION.md`
- `.planning/quick/LOG.md`
</files>

<action>
- Add focused tests proving POS labels normalize consistently and function-word inference works across the supported languages.
- Run focused service tests; run broader tests if the focused suite passes quickly enough.
- Persist summary, verification, and log artifacts for the quick task.
</action>

<done>
- Focused POS/remediation/grounding tests pass.
- Quick task summary, verification, and log row exist on disk.
</done>

<verify>
- `uv run pytest tests/services/test_text_field_remediation.py tests/services/test_lexical_grounding.py -q`
- `uv run pytest -q`
</verify>
