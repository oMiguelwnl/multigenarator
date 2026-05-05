# Phase 11 Research: Highlight Pipeline Integration

**Phase:** 11-highlight-pipeline-integration  
**Requirements:** MODE-01, INGEST-04  
**Status:** Complete

## Planning-Relevant Findings

- Existing public CLI currently allows only `frequency` and `word-list`; Phase 11 must expose `generate --source highlights` while mapping that alias to internal `kindle-highlights` per D-01 and D-04.
- Phase 10 already provides parser/extractor/preview contracts, but `HighlightCandidate.item_key` is sequence-derived (`highlight-{lang}-{position}-{lemma}`), so it must be hardened for same-content reorder safety per D-06.
- Existing job duplicate prevention works through deterministic `requested_item_keys`, `source_fingerprint`, `run_key`, and `GenerationItem` rows. Highlight mode should reuse that layer by producing stable candidate item keys and a content-derived fingerprint rather than adding a parallel job runner.
- Private normalized highlight text needs persistence for Phase 12 context/audit, but safe manifests and CLI output must remain count/hash-only per D-08, D-10, D-15, and D-16.
- Frequency grounding backfills missing lexical entries; highlight grounding must not backfill. Missing/insufficient highlight candidates should be counted as blocked and omitted from planned cards per D-13.

## Recommended Implementation Shape

1. Add stable highlight identity contracts in `domain/highlights.py` and extraction helpers:
   - `import_content_hash`: SHA-256 over sorted normalized highlight content hashes.
   - candidate `source_content_hash`: first contributing normalized highlight content hash.
   - candidate `item_key`: `highlight-{language}-{source_content_hash[:16]}-{lemma_hash[:16]}`.
   - safe manifest shape containing hashes, candidate keys, and counts only.
2. Persist private highlight imports in a dedicated repository/table pair:
   - private table: stores `job_id`, `import_content_hash`, `highlight_id`, `source_content_hash`, `source_index`, and `normalized_text`.
   - manifest table: stores `job_id`, `import_content_hash`, `candidate_keys`, and count JSON; no raw text/path/book metadata.
3. Extend `IngestLexicalItemsService.execute()` with a `kindle-highlights` branch that:
   - requires `request.input_file`;
   - parses local highlights, extracts stable candidates, orchestrates the job with stable item keys;
   - persists private normalized text separately from lexical candidates;
   - grounds pending item keys through Kaikki using highlight candidate lemmas;
   - records only grounded candidates as `JobStage.INGEST` successes;
   - counts ungrounded/insufficient candidates as blocked without frequency backfill.
4. Update CLI validation and output:
   - accept only public `--source highlights`, not `kindle-highlights`;
   - map `highlights` to internal `kindle-highlights` in `GenerationRequest`;
   - allow `--input-file` for `highlights`;
   - print stable counts for every D-12 lifecycle category.

## Validation Architecture

- Unit tests: stable candidate identity, reorder-safe extraction, safe manifest serialization, and no-private-data assertions.
- Repository tests: private table stores normalized text; manifest table omits normalized text, source paths, snippets, book metadata, and credentials.
- Service tests: highlight ingestion creates/resumes jobs, persists grounded lexical candidates, skips duplicate reruns, blocks ungrounded candidates, and advances only to the next existing job stage.
- CLI tests: public `highlights` alias accepted with `--input-file`, internal `kindle-highlights` rejected, preview remains side-effect-free, and output includes the D-12 counters.
- Regression tests: existing Phase 09/10 focused commands stay green.

## Common Pitfalls

- Do not use source file paths/names in import identity; this violates D-05 and leaks private local context.
- Do not place raw highlight text in lexical candidate provenance or safe manifests; use the private import table only.
- Do not enable WebDAV, export/template behavior, generated highlight examples, audio, or QA in this phase.
- Do not use frequency backfill for highlight candidates; blocked counts are the correct behavior.

## Source Audit

| Source | Item | Coverage |
|--------|------|----------|
| GOAL | Highlight candidates run through existing job pipeline as duplicate-safe `highlights` mode | Plans 01-04 |
| REQ | MODE-01 public `highlights` deck mode | Plan 04 |
| REQ | INGEST-04 duplicate-safe rerun with content hashes, manifests, visible summary | Plans 01-04 |
| CONTEXT | D-01..D-04 CLI alias/profile/preview decisions | Plans 01 and 04 |
| CONTEXT | D-05..D-08 identity and manifest privacy | Plans 01 and 02 |
| CONTEXT | D-09..D-12 count-only import summary | Plans 03 and 04 |
| CONTEXT | D-13..D-16 grounding boundary and private provenance | Plans 02 and 03 |
| RESEARCH | Existing job/resume pipeline should be reused | Plans 01 and 03 |
| RESEARCH | Private text separated from safe manifest | Plan 02 |

Deferred/out-of-scope items intentionally excluded: WebDAV fetching, generated examples, audio, export/template behavior, phonetics refresh, interactive candidate review, bilingual highlight decks.
