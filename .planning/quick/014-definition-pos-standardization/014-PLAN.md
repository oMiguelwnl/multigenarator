# Quick Task 014 Plan: Definition POS Standardization

## Objective

Standardize generated card definitions so the label before `:` reflects a trusted or inferred part of speech, never an invented provider label, and fix German function-word cases such as `die` where the current output labels an article as `noun`.

## Task 1: Add Deterministic Definition Normalization
<files>
- `src/multilang/services/text_field_remediation.py`
- `tests/services/test_text_field_remediation.py`
</files>
<action>
Normalize learner definitions after provider generation: map known POS aliases to canonical labels, treat `unknown`/generic labels as absent, infer labels for known German function words such as `die`, and rewrite mismatched provider labels while preserving the semantic meaning. Add tests for `die`, unknown POS, and mismatched provider labels.
</action>
<done>
Definitions no longer preserve incorrect provider labels like `noun:` for known German articles, and unknown POS does not produce `unknown:`/`term:` labels.
</done>
<verify>
Run `uv run pytest tests/services/test_text_field_remediation.py -q`.
</verify>

## Task 2: Wire Grounding And Regenerate German Smoke
<files>
- `src/multilang/services/lexical_grounding.py`
- `tests/services/test_lexical_grounding.py`
</files>
<action>
Ensure lexical grounding passes source language context into remediation, and add an integration-level grounding test proving German `die` becomes an `article:` definition. Regenerate the small German provider-backed test deck after the fix.
</action>
<done>
German test deck no longer labels `die` as `noun`, and focused tests prove the standardization path.
</done>
<verify>
Run `uv run pytest tests/services/test_lexical_grounding.py tests/services/test_text_field_remediation.py -q`.
Regenerate the German provider-backed smoke with `PYTHONIOENCODING=utf-8 MULTILANG_TEXT_GENERATION_PROVIDER=litellm MULTILANG_TRANSLATION_PROVIDER=deepl MULTILANG_AUDIO_PROVIDER=azure MULTILANG_DATABASE_URL="sqlite+pysqlite:///C:/dev/multilang/.multilang/test-decks/de-full/de-test-standardized.db" MULTILANG_AUDIO_STORAGE_DIR=".multilang/test-decks/de-full-standardized/audio" MULTILANG_EXPORT_OUTPUT_DIR=".multilang/test-decks/de-full-standardized/exports" uv run multilang generate --language de --source frequency --cards-per-level 1 --rate-limit-per-minute 30`.
Export with `uv run multilang export --job-id <job_id> --format csv --output-dir ".multilang/test-decks/de-full-standardized/exports" --deck-name "Multilang German Test Standardized" --allow-partial` using the same environment variables, then assert the CSV contains `die,/diː/,article:` and does not contain `die,/diː/,noun:`.
</verify>

## No UI Proof Rationale

This task changes backend lexical definition normalization and deck content only; it has no rendered UI surface.
