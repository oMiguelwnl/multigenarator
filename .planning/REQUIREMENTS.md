# Requirements: Multilang Anki Card Generator v1.2

**Defined:** 2026-05-03  
**Milestone:** v1.2 Kindle Highlights and Template Refresh  
**Core Value:** Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.  
**Source:** `alter_organizado.md`, milestone questioning, and `.planning/research/SUMMARY.md`

## v1.2 Requirements

Requirements for the current milestone. Each requirement maps to exactly one roadmap phase.

### Kindle/WebDAV Ingestion

- [x] **INGEST-01**: User can configure the Kindle WebDAV URL, username, and secret without editing source code or exposing credentials in logs or artifacts.
- [x] **INGEST-02**: User can fetch Kindle highlight exports from WebDAV with remote listing, file selection, and distinct auth, path, network, and empty-source failures.
- [x] **INGEST-03**: User can process a local Kindle export file through the same normalization path used by WebDAV imports.
- [x] **INGEST-04**: User can rerun the same highlight import without creating duplicate cards, using content hashes, import manifests, and a visible import summary.

### Local Kindle Normalization

- [x] **NORM-01**: User can normalize Kindle-exported HTML or text into deterministic highlight records without using the external Kindle Formatter website.
- [x] **NORM-02**: User keeps target-language characters, punctuation, record order, and source provenance through normalization.
- [x] **NORM-03**: User receives rejected-highlight reasons for unusable, malformed, empty, or unsafe highlight fragments, and failed imports do not proceed silently.

### Candidate Extraction

- [x] **CAND-01**: User can extract target-language vocabulary candidates from normalized highlights for all existing supported languages.
- [x] **CAND-02**: User gets deterministic candidate filtering, duplicate detection, and first-seen ordering without treating every token as a card.
- [x] **CAND-03**: User can review imported highlight count, extracted candidate count, rejected count, duplicate count, and planned card count before expensive generation.

### Highlight Deck Mode and Generation

- [x] **MODE-01**: User can generate a `highlights` deck mode alongside existing frequency-deck and custom word-list modes.
- [x] **MODE-02**: Existing frequency-deck and custom word-list behavior remains unchanged when highlight mode is added.
- [x] **GEN-01**: User receives highlight cards with word or headword, IPA and spoken-pronunciation behavior, definition, example sentence, word audio, sentence audio, and blank `Image`.
- [x] **GEN-02**: User receives concise but grammatically richer highlight examples that include the target word and pass language and length validation.
- [x] **GEN-03**: User's private highlight text is minimized or redacted in prompts, reports, and errors while preserving enough internal provenance for audit and sense or context use.

### Highlight Export and Template

- [x] **EXPORT-01**: User can export highlight decks to APKG, CSV, and TSV with a dedicated highlight note type, exact English field names, and no `Translation` field.
- [x] **EXPORT-02**: User sees highlight card fronts with prompt-side content only and backs with `{{FrontSide}}`, an answer divider, and `Definition`.
- [x] **EXPORT-03**: User gets centered, responsive, Multilang-colored highlight templates with safe packaged media references and no dangling field references.

### Phonetics Template Refresh

- [x] **PHON-01**: User sees phonetics card fronts using the provided layout for spellings, sound, letter audio, example word, word audio, word translation, example sentence, and sentence audio.
- [x] **PHON-02**: User sees `Sentence Translation` revealed on the phonetics card back, using Multilang colors.
- [x] **PHON-03**: User receives phonetics exports without `Notes`, `is_priming`, or `is_sentence` fields or references while existing Russian phonetics audio behavior remains working.

### Regression, Security, and Evidence

- [x] **SEC-01**: User's WebDAV credentials, raw highlight files, book metadata, and private reading text are excluded from commits and redacted from logs and errors.
- [x] **SEC-02**: User gets tests proving existing frequency and custom generation, audio, and export contracts still work after v1.2 changes.
- [x] **EVID-01**: User gets end-to-end evidence that a local Kindle fixture can become generated highlight cards and importable Anki exports, plus phonetics template export evidence.

## Future Requirements

Deferred to future milestones. Tracked but not in the current roadmap.

### Reading-Derived Vocabulary

- **FUTURE-01**: User can use full highlight context for robust sense-aware disambiguation before generation.
- **FUTURE-02**: User can organize highlight decks by book, chapter, or source metadata when the export format provides reliable metadata.
- **FUTURE-03**: User can approve or reject extracted candidates in an interactive review UI before generation.
- **FUTURE-04**: User can create optional bilingual highlight decks with translations through a separate note type or template option.
- **FUTURE-05**: User can ingest generic ebook, PDF, website, or browser-captured reading sources after Kindle highlights stabilize.

## Out of Scope

Explicitly excluded from v1.2 to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Replacing the shipped frequency-deck mode | v1.2 adds highlights as a new mode; existing frequency and custom word-list flows must keep working. |
| Automating the external Kindle Formatter website | Multilang should locally normalize Kindle exports for reproducible, testable behavior. |
| Automatic Kindle account or device sync | The requested source is WebDAV-exported highlights, not direct Kindle account/device integration. |
| Adding translations to highlight cards | The requested highlight deck has no `Translation` field. |
| Automatic image generation or sourcing | The project decision remains that `Image` is blank by default for manual user population. |
| Full reading app, SRS app, or AI tutor | Anki remains the destination study tool. |
| Committing real WebDAV credentials, raw exports, or private highlights | This violates the security/privacy requirements for reading data. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 14 | Complete |
| INGEST-02 | Phase 14 | Complete |
| INGEST-03 | Phase 10 | Complete |
| INGEST-04 | Phase 11 | Complete |
| NORM-01 | Phase 10 | Complete |
| NORM-02 | Phase 10 | Complete |
| NORM-03 | Phase 10 | Complete |
| CAND-01 | Phase 10 | Complete |
| CAND-02 | Phase 10 | Complete |
| CAND-03 | Phase 10 | Complete |
| MODE-01 | Phase 11 | Complete |
| MODE-02 | Phase 09 | Complete |
| GEN-01 | Phase 12 | Complete |
| GEN-02 | Phase 12 | Complete |
| GEN-03 | Phase 12 | Complete |
| EXPORT-01 | Phase 13 | Complete |
| EXPORT-02 | Phase 13 | Complete |
| EXPORT-03 | Phase 13 | Complete |
| PHON-01 | Phase 15 | Complete |
| PHON-02 | Phase 15 | Complete |
| PHON-03 | Phase 15 | Complete |
| SEC-01 | Phase 09 | Complete |
| SEC-02 | Phase 09 | Complete |
| EVID-01 | Phase 16 | Complete |

**Coverage:**

- v1.2 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0
- Coverage validated: 24/24 mapped exactly once across Phases 09-16

---
*Requirements defined: 2026-05-03*  
*Last updated: 2026-05-08 after Phase 16 completion*
