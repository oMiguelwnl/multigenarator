# Phase 13 Multi-Source Coverage Audit

## Coverage table

| Source | Item | Coverage |
|---|---|---|
| GOAL | Generated highlight cards export to Anki-compatible artifacts with the requested dedicated study template. | Plans 13-01, 13-02, 13-03 |
| REQ EXPORT-01 | APKG, CSV, and TSV export with dedicated highlight note type, exact English fields, and no `Translation`. | Plans 13-02 and 13-03 |
| REQ EXPORT-02 | Front has prompt-side content only; back uses `{{FrontSide}}`, divider, and `Definition`. | Plan 13-01 |
| REQ EXPORT-03 | Centered responsive Multilang template, safe packaged media references, and no dangling field references. | Plans 13-01, 13-02, and 13-03 |
| RESEARCH | `genanki.Model` fields/templates/css and `Package.media_files` are the correct APKG integration points. | Plan 13-02 |
| RESEARCH | Anki text import headers support `#notetype`, `#deck`, `#columns`, `#separator`, and `#html`. | Plan 13-03 |
| CONTEXT D-01 | Front shows `Word`, `IPA`, `word_audio`, `Example Sentence`, and `sentence_audio`. | Plan 13-01 |
| CONTEXT D-02 | Example sentence appears on front with `sentence_audio`. | Plan 13-01 |
| CONTEXT D-03 | `Image` exported but conditionally rendered only when populated. | Plan 13-01 |
| CONTEXT D-04 | Minimal front labels. | Plan 13-01 |
| CONTEXT D-05 | Back keeps `{{FrontSide}}`, answer divider, and `Definition`. | Plan 13-01 |
| CONTEXT D-06 | Answer label is `Definition`. | Plan 13-01 |
| CONTEXT D-07 | Multiple definitions render as clean bullet list when possible. | Plan 13-01 |
| CONTEXT D-08 | No repeated audio/autoplay on back beyond `{{FrontSide}}`. | Plan 13-01 |
| CONTEXT D-09 | Multilang-branded blue visual direction. | Plan 13-01 |
| CONTEXT D-10 | Centered shell. | Plan 13-01 |
| CONTEXT D-11 | Comfortable density. | Plan 13-01 |
| CONTEXT D-12 | Vertical mobile scrolling, no horizontal scroll. | Plan 13-01 |
| CONTEXT D-13 | Highlight exports contain only highlight rows; mixed-source exports fail closed. | Plans 13-02 and 13-03 |
| CONTEXT D-14 | Templates reference only final fields, not private/raw/`Translation`. | Plans 13-01 and 13-02 |
| CONTEXT D-15 | APKG fails before writing if word/sentence audio media is missing or mismatched. | Plan 13-02 |
| CONTEXT D-16 | CSV/TSV strict Anki headers include `#notetype`, `#deck`, and exact `#columns`. | Plan 13-03 |
| CONTEXT D-17 | Keep `frequency`, `word-list`, and `highlights` distinct. | Plans 13-02 and 13-03 |
| CONTEXT D-18 | Apply dedicated template to highlights only; existing modes unchanged. | Plans 13-01, 13-02, and 13-03 |

## Exclusions

- Deferred: applying highlight-style template to manual `word-list` decks.
- Out of scope: ingestion, WebDAV fetching, phonetics template refresh, automatic images, or adding translations to highlight cards.

## Result

No unplanned items found.
