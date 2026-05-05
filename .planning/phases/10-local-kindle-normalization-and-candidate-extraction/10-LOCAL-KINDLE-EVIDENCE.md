---
phase: 10-local-kindle-normalization-and-candidate-extraction
status: passed
updated: 2026-05-05T00:00:00Z
source: [10-01-SUMMARY.md, 10-02-SUMMARY.md, 10-03-SUMMARY.md, 10-04-SUMMARY.md]
---

# Phase 10 Local Kindle Evidence

## Evidence Commands

### Focused Phase 10 suite

```bash
python -m pytest tests/services/test_kindle_highlight_parser.py tests/services/test_highlight_candidate_extraction.py tests/services/test_highlight_import_preview.py tests/cli/test_kindle_highlight_preview_command.py tests/integration/test_kindle_local_normalization_flow.py -q
```

Expected: all parser, extraction, preview service, CLI, and integration checks pass.

### Phase 10 plus existing-mode/privacy regression boundary

```bash
python -m pytest tests/services/test_kindle_highlight_parser.py tests/services/test_highlight_candidate_extraction.py tests/services/test_highlight_import_preview.py tests/cli/test_kindle_highlight_preview_command.py tests/integration/test_kindle_local_normalization_flow.py tests/integration/test_v12_existing_mode_regression_boundary.py -q
```

Observed during execution: `33 passed`.

## Multi-Source Coverage Audit

| Source | Coverage | Plans |
|--------|----------|-------|
| GOAL Phase 10 | Local Kindle fixture normalizes, extracts candidates, and previews count-only results without external Kindle Formatter dependency. | 10-01, 10-02, 10-03, 10-04 |
| REQ INGEST-03 | Local HTML/text Kindle exports parse from synthetic fixtures and surface unsupported/malformed rejection paths. | 10-01, 10-03, 10-04 |
| REQ NORM-01 | Normalized records preserve target-language characters, punctuation, source order, and deterministic content hashes. | 10-01, 10-04 |
| REQ NORM-02 | Candidate extraction consumes normalized records and filters noise/duplicates deterministically. | 10-02, 10-04 |
| REQ NORM-03 | Rejected highlights and preview failures use safe reason codes without raw private text or absolute source paths. | 10-01, 10-03, 10-04 |
| REQ CAND-01 | All supported languages have deterministic candidate extraction coverage. | 10-02 |
| REQ CAND-02 | Candidate ordering follows first occurrence and duplicate counts retain first provenance. | 10-02, 10-04 |
| REQ CAND-03 | CLI preview exposes imported, candidate, rejected, duplicate, and planned-card counts before generation. | 10-03, 10-04 |
| RESEARCH existing stack/no-new-dependency constraints | Implementation uses existing Python/Pydantic/Typer stack plus stdlib parser/tokenization; no new runtime dependency was added. | 10-01, 10-02, 10-03 |
| CONTEXT carry-forward decisions from STATE.md | Kindle normalization stays local; raw exports/book metadata/private reading text are not committed or surfaced; `kindle-highlights` remains blocked from generation until Phase 11. | 10-01, 10-03, 10-04 |

## Source Audit

- Fixtures under `tests/fixtures/kindle_highlights/` are synthetic learner-safe examples only.
- Evidence references fixture paths and count summaries, not real raw Kindle exports.
- Parser provenance stores fixture/file names rather than absolute local paths.
- Preview CLI output is stable count-only `key=value` lines.

## Deferred / Out of Scope

- No WebDAV fetch.
- No generation job integration.
- No interactive review UI.
- No full reading disambiguation.
- No translations.
- No audio or Anki export side effects.
- No real private Kindle exports committed.

## Phase 09 Regression Guardrails

The regression command includes `tests/integration/test_v12_existing_mode_regression_boundary.py` to protect existing frequency/custom mode privacy and source-profile boundaries after adding highlight preview.
