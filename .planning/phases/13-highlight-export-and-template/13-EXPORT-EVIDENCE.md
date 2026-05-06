# Phase 13 Export Evidence

## Scope

Scanner-readable evidence for strict highlight export artifacts across APKG, CSV, and TSV while preserving existing frequency and word-list export behavior.

## Requirements Covered

| Requirement | Evidence | Status |
|-------------|----------|--------|
| EXPORT-01 | Highlight APKG package uses `Multilang::Highlight Card`, exact highlight fields, and packaged word/sentence media. | PASS |
| EXPORT-02 | Highlight model/template references are bounded to exported highlight fields plus Anki `FrontSide`; no `Translation` reference appears. | PASS |
| EXPORT-03 | Highlight CSV/TSV files include strict Anki import metadata and exact `SortIndex, Word, IPA, word_audio, Example Sentence, sentence_audio, Definition, Image` columns. | PASS |

## Commands Run

| Command | Result |
|---------|--------|
| `python -m pytest tests/services/test_export_tabular_bundle.py tests/domain/test_exporting.py -q` | 20 passed |
| `python -m pytest tests/integration/test_highlight_export_artifacts.py -q` | 3 passed |
| `python -m pytest tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py tests/integration/test_highlight_export_artifacts.py tests/domain/test_exporting.py -q` | 39 passed |

## Regression Command

```bash
python -m pytest tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py tests/integration/test_highlight_export_artifacts.py tests/domain/test_exporting.py -q
```

Expected result: `39 passed`.

## Artifact Assertions

- APKG zip contains `collection.anki2`, a media manifest, and packaged synthetic word/sentence audio files.
- APKG collection model id `HIGHLIGHT_MODEL_ID` resolves to `Multilang::Highlight Card` with exact highlight fields.
- Highlight template markup contains no dangling field references after resolving Anki conditional helpers and contains no `Translation` reference.
- CSV header starts with `#separator:Comma`, `#html:true`, `#notetype:Multilang::Highlight Card`, `#deck:<deck>`, and exact comma-separated highlight columns.
- TSV header starts with `#separator:Tab`, `#html:true`, `#notetype:Multilang::Highlight Card`, `#deck:<deck>`, and exact tab-separated highlight columns.
- CSV/TSV rows serialize `Word`, `Definition`, safe `[sound:...]` audio tags, and blank `Image`; `Translation`, `word`, and `Definitions` are absent from highlight headers.
- Frequency and word-list tabular exports retain `Translation` as regression evidence for existing source-mode boundaries.

## Privacy Note

Evidence uses synthetic fixture text, synthetic job identifiers, and local temporary audio files only. No raw private highlight text, book metadata, source path, WebDAV location, credentials, or provider secrets are included.
