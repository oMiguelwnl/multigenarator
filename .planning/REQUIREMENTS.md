# Requirements: Multilang Anki Card Generator v1.2

**Defined:** 2026-05-03  
**Milestone:** v1.2 Kindle Highlights and Template Refresh  
**Core Value:** Generate reliable, high-quality Anki cards for real vocabulary the learner needs to study, with accurate definitions, examples, translations where appropriate, and audio.  
**Source:** `alter_organizado.md`, milestone questioning, and `.planning/research/SUMMARY.md`

## v1.2 Requirements

Requirements for the current milestone. Each requirement maps to exactly one roadmap phase.

### Kindle/WebDAV Ingestion

- [ ] **INGEST-01**: User can configure the Kindle WebDAV URL, username, and secret without editing source code or exposing credentials in logs or artifacts.
- [ ] **INGEST-02**: User can fetch Kindle highlight exports from WebDAV with remote listing, file selection, and distinct auth, path, network, and empty-source failures.
- [ ] **INGEST-03**: User can process a local Kindle export file through the same normalization path used by WebDAV imports.
- [ ] **INGEST-04**: User can rerun the same highlight import without creating duplicate cards, using content hashes, import manifests, and a visible import summary.

### Local Kindle Normalization

- [ ] **NORM-01**: User can normalize Kindle-exported HTML or text into deterministic highlight records without using the external Kindle Formatter website.
- [ ] **NORM-02**: User keeps target-language characters, punctuation, record order, and source provenance through normalization.
- [ ] **NORM-03**: User receives rejected-highlight reasons for unusable, malformed, empty, or unsafe highlight fragments, and failed imports do not proceed silently.

### Candidate Extraction

- [ ] **CAND-01**: User can extract target-language vocabulary candidates from normalized highlights for all existing supported languages.
- [ ] **CAND-02**: User gets deterministic candidate filtering, duplicate detection, and first-seen ordering without treating every token as a card.
- [ ] **CAND-03**: User can review imported highlight count, extracted candidate count, rejected count, duplicate count, and planned card count before expensive generation.

### Highlight Deck Mode and Generation

- [ ] **MODE-01**: User can generate a `highlights` deck mode alongside existing frequency-deck and custom word-list modes.
- [ ] **MODE-02**: Existing frequency-deck and custom word-list behavior remains unchanged when highlight mode is added.
- [ ] **GEN-01**: User receives highlight cards with word or headword, IPA and spoken-pronunciation behavior, definition, example sentence, word audio, sentence audio, and blank `Image`.
- [ ] **GEN-02**: User receives concise but grammatically richer highlight examples that include the target word and pass language and length validation.
- [ ] **GEN-03**: User's private highlight text is minimized or redacted in prompts, reports, and errors while preserving enough internal provenance for audit and sense or context use.

### Highlight Export and Template

- [ ] **EXPORT-01**: User can export highlight decks to APKG, CSV, and TSV with a dedicated highlight note type, exact English field names, and no `Translation` field.
- [ ] **EXPORT-02**: User sees highlight card fronts with prompt-side content only and backs with `{{FrontSide}}`, an answer divider, and `Definition`.
- [ ] **EXPORT-03**: User gets centered, responsive, Multilang-colored highlight templates with safe packaged media references and no dangling field references.

### Phonetics Template Refresh

- [ ] **PHON-01**: User sees phonetics card fronts using the provided layout for spellings, sound, letter audio, example word, word audio, word translation, example sentence, and sentence audio.
- [ ] **PHON-02**: User sees `Sentence Translation` revealed on the phonetics card back, using Multilang colors.
- [ ] **PHON-03**: User receives phonetics exports without `Notes`, `is_priming`, or `is_sentence` fields or references while existing Russian phonetics audio behavior remains working.

### Regression, Security, and Evidence

- [ ] **SEC-01**: User's WebDAV credentials, raw highlight files, book metadata, and private reading text are excluded from commits and redacted from logs and errors.
- [ ] **SEC-02**: User gets tests proving existing frequency and custom generation, audio, and export contracts still work after v1.2 changes.
- [ ] **EVID-01**: User gets end-to-end evidence that a local Kindle fixture can become generated highlight cards and importable Anki exports, plus phonetics template export evidence.

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
| INGEST-01 | TBD | Pending |
| INGEST-02 | TBD | Pending |
| INGEST-03 | TBD | Pending |
| INGEST-04 | TBD | Pending |
| NORM-01 | TBD | Pending |
| NORM-02 | TBD | Pending |
| NORM-03 | TBD | Pending |
| CAND-01 | TBD | Pending |
| CAND-02 | TBD | Pending |
| CAND-03 | TBD | Pending |
| MODE-01 | TBD | Pending |
| MODE-02 | TBD | Pending |
| GEN-01 | TBD | Pending |
| GEN-02 | TBD | Pending |
| GEN-03 | TBD | Pending |
| EXPORT-01 | TBD | Pending |
| EXPORT-02 | TBD | Pending |
| EXPORT-03 | TBD | Pending |
| PHON-01 | TBD | Pending |
| PHON-02 | TBD | Pending |
| PHON-03 | TBD | Pending |
| SEC-01 | TBD | Pending |
| SEC-02 | TBD | Pending |
| EVID-01 | TBD | Pending |

**Coverage:**

- v1.2 requirements: 24 total
- Mapped to phases: 0
- Unmapped: 24 pending roadmap

---
*Requirements defined: 2026-05-03*  
*Last updated: 2026-05-03 after initial v1.2 definition*
