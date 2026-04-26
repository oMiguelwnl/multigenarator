# Phase 2 Research: Input Decks & Lexical Grounding

**Phase:** 2 - Input Decks & Lexical Grounding  
**Researched:** 2026-04-19  
**Status:** Ready for planning  
**Confidence:** MEDIUM-HIGH

## Research Answer

Phase 2 should turn the existing Phase 1 job runner into a real lexical-ingestion pipeline by combining three implementation tracks: a deterministic `wordfreq`-based frequency-deck builder, a plain-text custom word-list parser, and a trust-first lexical grounding service backed by cached Kaikki/Wiktextract extracts. The phase should persist lexical candidates as normalized records that keep both the user-facing study form and the internal lemma/provenance metadata, while leaving sentence generation, translation text, audio synthesis, and Anki export to later phases.

## Decisions to Carry Into Planning

### Stack and data-source choices
- Use **`wordfreq`** for deterministic ranked candidate bootstrap. `top_n_list(language, n)` and `iter_wordlist(language)` are the relevant APIs for collecting frequency candidates and backfill candidates.
- Use **Kaikki/Wiktextract** as the lexical grounding base for lemma, English glosses, and IPA where available.
- Do **not** download giant lexical dumps on every CLI run. Build a cached local extract/index per supported language, then query that local cache during generation.
- Keep the current **Typer -> service -> repository** split from Phase 1; extend it instead of replacing it.

### Phase-2-specific architecture
- Introduce a canonical lexical candidate contract that stores, at minimum, `submitted_form`, `display_form`, `lemma`, `lemma_key`, `frequency_rank`, `frequency_level`, `definitions_html`, `definition_language`, `ipa`, `translation_target_language`, `grounding_status`, and provenance metadata.
- Encode the output-language policy in the candidate contract:
  - `definition_language = "en"` for every deck per D-09.
  - `translation_target_language = "en"` for non-English decks and `"pt"` for English decks per D-10.
- Preserve both the original submitted text and the normalized lexical target for custom word lists per D-05.
- Keep frequency decks and custom word lists on the same orchestration surface (`multilang generate`) per STATE.md, but use different failure handling:
  - frequency runs backfill with the next valid candidate until the level reaches 1000 grounded items per D-08
  - custom word lists keep the requested item and mark it pending/insufficient instead of swapping it away per D-08

### Deterministic frequency curation policy
- Start from `wordfreq` ranked candidates, but apply a mandatory filter layer before a token can become a study candidate.
- Required rejects per D-03 and D-04:
  - tokens containing digits
  - punctuation-only or symbol-heavy tokens
  - obvious web/corpus noise (`http`, `https`, `www`, `nbsp`)
  - broken abbreviations and malformed mixed-symbol strings
  - obvious proper names via capitalization heuristics when the lower-cased form is not the study token
- Required keeps:
  - legitimate high-frequency function words
  - alphabetic tokens with internal apostrophes or hyphens when the surrounding characters are letters
- Build level boundaries by rank windows: level 1 = ranks 1-1000, level 2 = 1001-2000, level 3 = 2001-3000.
- Keep scanning ranked candidates past rank 3000 so failed lexical groundings can be backfilled without changing the ordering rule.

### Trust-first lexical grounding policy
- Model lexical grounding as lookup + normalization, not LLM invention.
- IPA is authoritative-only: if the lexical source has no IPA, keep the field empty and record provenance; do not synthesize or guess pronunciation per D-07.
- Definitions may use a controlled fallback only when the primary lexical source lacks a clean English gloss. Any fallback must be flagged in provenance so downstream phases know it is weaker than first-party lexical data per D-07.
- Normalize definitions into one deck-wide field format now so Phase 5 can reuse it directly: one HTML-safe string with senses joined by `<br>` separators, never nested list markup.

### Cache/bootstrap shape
- Add a configurable lexical data directory in settings (for example `MULTILANG_LEXICON_DATA_DIR`).
- Provide a bootstrap/indexing step that downloads or refreshes per-language Kaikki `.jsonl.gz` files, extracts only the needed fields, and stores a smaller lookup index for runtime use.
- Tests should use tiny fixture extracts rather than full live downloads.

## Recommended File Layout

```text
src/multilang/
  domain/lexicon.py
  repositories/lexical_repository.py
  services/frequency_decks.py
  services/word_list_parser.py
  services/kaikki_lookup.py
  services/lexical_grounding.py
  services/ingest_lexical_items.py

alembic/versions/
  20260419_02_lexical_grounding_tables.py

tests/
  domain/test_lexicon.py
  repositories/test_lexical_repository.py
  services/test_frequency_decks.py
  services/test_word_list_parser.py
  services/test_kaikki_lookup.py
  services/test_lexical_grounding.py
  integration/test_lexical_job_flow.py
```

## Concrete Design Guidance

### Lexical candidate persistence
- Extend the database with a lexical-candidate table keyed by `(job_id, item_key)`.
- Persist these fields explicitly:
  - request identity: `job_id`, `run_key`, `item_key`, `source_type`
  - source text: `submitted_form`, `normalized_source`
  - learner-facing text: `display_form`
  - grounding identity: `lemma`, `lemma_key`
  - ranking: `frequency_rank`, `frequency_level`
  - enrichment: `definitions_html`, `definition_language`, `ipa`, `translation_target_language`
  - lifecycle: `grounding_status`, `warning_code`, `warning_detail`
  - provenance JSON: lexical source, definition source, IPA source, fallback flags

### Word-list parsing
- Support only UTF-8 plain text with one item per line for this phase per D-06.
- For each non-empty line, persist:
  - original submitted text
  - trimmed display candidate
  - normalized dedupe key (casefolded, whitespace-normalized)
  - line number for diagnostics
- Return structured warnings for duplicates, blank lines, and normalization collisions.

### Kaikki lookup strategy
- Use language-specific download URLs and cache paths.
- Build an index keyed by normalized term so runtime lookup does not have to scan the full gzip file.
- Normalize Kaikki records into a small internal record containing the display form, lemma, English gloss candidates, IPA candidates, and source metadata.

### CLI/runtime integration
- Keep `multilang generate` as the only operator surface.
- Replace the placeholder frequency item loader in `cli.py` with the real frequency-deck builder.
- Replace raw word-list line reading with the parser so the CLI can print rejected-row and pending-grounding diagnostics.
- Persist lexical candidates during the ingest/enrich stages while preserving Phase 1 progress/resume semantics.

## Common Pitfalls To Prevent In Phase 2

- Do not collapse a candidate to a bare lemma; keep both submitted/display form and lemma per D-01 and D-02.
- Do not ship raw `wordfreq` output without filters; Phase 2 must include deterministic teachability filtering per D-03 and D-04.
- Do not silently substitute failed custom-list items with unrelated words; keep them pending/insufficient per D-08.
- Do not fabricate IPA when the lexical source is missing it per D-07.
- Do not let per-language output drift; definitions stay in English and translation target policy must be encoded now per D-09 and D-10.

## Architectural Responsibility Map

| Layer | Phase 2 Responsibility |
|------|-------------------------|
| CLI | Validate source-specific flags, invoke lexical-ingestion coordinator, print rejection/backfill/pending diagnostics |
| Domain models | Encode lexical candidate contracts, grounding statuses, language policy, and provenance shapes |
| Repository | Persist normalized lexical candidates and query pending/grounded rows |
| Frequency service | Build curated ranked candidates and level windows from `wordfreq` |
| Lexical data adapter | Bootstrap/cache Kaikki extracts and return normalized lexical records |
| Grounding service | Apply trust-first fallback policy, choose study form, normalize English definitions and IPA |
| Tests | Lock rank windows, parsing rules, provenance behavior, pending/backfill semantics, and CLI integration |

## Validation Architecture

Phase 2 should stay executable only with automated verification attached to every new contract.

- Use **pytest** with fixture-based lexical-source tests.
- Keep a quick command under 60 seconds:
  - `uv run pytest tests/domain/test_lexicon.py tests/repositories/test_lexical_repository.py tests/services/test_frequency_decks.py tests/services/test_word_list_parser.py tests/services/test_kaikki_lookup.py tests/services/test_lexical_grounding.py tests/cli/test_generate_command.py -q`
- Full phase regression command:
  - `uv run pytest tests -q`

Required automated coverage:
- 3 x 1000 frequency-level slicing per supported language
- deterministic filter rejects for noisy tokens while keeping valid function words
- plain-text word-list parsing with original-form preservation and dedupe diagnostics
- Kaikki cache/index lookup from fixture extracts
- no-IPA fabrication behavior
- English-only definition formatting and translation-target policy encoding
- frequency backfill on grounding failures
- custom-list pending/insufficient persistence instead of substitution

## Source Coverage Notes For Planning

This research directly supports:
- **DECK-02** via deterministic 3-level frequency-deck generation
- **DECK-03** via plain-text custom word-list ingestion
- **LEX-01** via persisted `lemma`, `display_form`, and frequency rank metadata
- **LEX-02** via authoritative IPA lookup with missing-data handling
- **LEX-03** via English-only, deck-wide definition formatting with provenance

## Recommendation

Proceed to planning with four focused plans: contracts/schema, frequency curation, word-list + lexical grounding, and CLI/runtime integration.

## Sources

- `.planning/phases/02-input-decks-lexical-grounding/02-CONTEXT.md`
- `.planning/research/SUMMARY.md`
- `.planning/research/STACK.md`
- `.planning/research/FEATURES.md`
- `.planning/research/PITFALLS.md`
- Context7 `/rspeer/wordfreq` docs for `top_n_list`, `iter_wordlist`, `zipf_frequency`, and supported language codes
- Kaikki raw-data docs: https://kaikki.org/dictionary/rawdata.html

---

*Phase: 02-input-decks-lexical-grounding*  
*Research completed: 2026-04-19*
