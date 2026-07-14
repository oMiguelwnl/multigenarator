# Quick Task 015 Plan: German POS And Display Normalization

## Objective

Fix the remaining German smoke deck quality issues: preserve useful provider POS labels for unknown asset rows (`blieb` should be `verb:`), keep deterministic overrides for known function words (`die` stays `article:`), and normalize known German noun display forms (`pause` should export as `Pause` with a noun definition).

## Task 1: Improve Definition Label Selection
<files>
- `src/multilang/services/text_field_remediation.py`
- `tests/services/test_text_field_remediation.py`
</files>
<action>
When the asset POS is unknown and no deterministic language override applies, preserve a canonical valid provider label instead of forcing `term:`. Deterministic language overrides must still win, so `die` cannot become `noun:`.
</action>
<done>
`verb: remained` remains `verb: remained`, while `noun: the definite article...` for German `die` is rewritten to `article: ...`.
</done>
<verify>
Run `uv run pytest tests/services/test_text_field_remediation.py -q`.
</verify>

## Task 2: Add German Display/POS Override For Observed Noun
<files>
- `src/multilang/services/lexical_grounding.py`
- `tests/services/test_lexical_grounding.py`
</files>
<action>
Add a small deterministic German lexical override for the observed lowercase noun `pause`, normalizing display/lemma to `Pause` and POS to `noun` before definition, sentence, IPA, and export data are built.
</action>
<done>
Frequency grounding for German `pause` exports `Pause` and uses a `noun:` definition label.
</done>
<verify>
Run `uv run pytest tests/services/test_lexical_grounding.py tests/services/test_text_field_remediation.py -q`.
</verify>

## Task 3: Regenerate German Provider Smoke
<files>
- `.planning/quick/015-german-pos-display-normalization/015-SUMMARY.md`
- `.planning/quick/015-german-pos-display-normalization/015-VERIFICATION.md`
- `.planning/quick/LOG.md`
</files>
<action>
Regenerate the 3-card German provider-backed smoke deck using `litellm`, `deepl`, and `azure`, then verify the CSV rows for `die`, `blieb`, and `Pause`.
</action>
<done>
New generated German CSV contains `die,/diː/,article:`, `blieb,/bliːp/,verb:`, and `Pause,` with a `noun:` definition.
</done>
<verify>
Run `uv run pytest`.
Regenerate with `PYTHONIOENCODING=utf-8 MULTILANG_TEXT_GENERATION_PROVIDER=litellm MULTILANG_TRANSLATION_PROVIDER=deepl MULTILANG_AUDIO_PROVIDER=azure MULTILANG_DATABASE_URL="sqlite+pysqlite:///C:/dev/multilang/.multilang/test-decks/de-full-normalized-v3/de-test.db" MULTILANG_AUDIO_STORAGE_DIR=".multilang/test-decks/de-full-normalized-v3/audio" MULTILANG_EXPORT_OUTPUT_DIR=".multilang/test-decks/de-full-normalized-v3/exports" uv run multilang generate --language de --source frequency --cards-per-level 1 --rate-limit-per-minute 30`.
Read `<job_id>` from the generated SQLite database, export CSV/APKG/TSV with `uv run multilang export --job-id <job_id> --format <apkg|csv|tsv> --output-dir ".multilang/test-decks/de-full-normalized-v3/exports" --deck-name "Multilang German Test Normalized" --allow-partial` using the same environment variables, then assert the CSV contains `die,/diː/,article:`, `blieb,/bliːp/,verb:`, and `Pause,` with `noun:`.
</verify>

## No UI Proof Rationale

This task changes backend lexical normalization and generated deck content only; it has no rendered UI surface.
