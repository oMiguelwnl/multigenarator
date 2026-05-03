# Architecture Research: v1.2 Kindle Highlights and Template Refresh

**Project:** Multilang Anki Card Generator  
**Milestone:** v1.2 Kindle Highlights and Template Refresh  
**Researched:** 2026-05-03  
**Scope:** Integration of new v1.2 features into the existing Python CLI/batch architecture only.  
**Overall confidence:** HIGH for integration shape, MEDIUM for exact Kindle export file format until real WebDAV fixture is captured.

## Executive Recommendation

Add Kindle highlights as a **third source type** that feeds the existing pipeline after a new deterministic ingestion/normalization pre-stage:

```text
frequency deck      -> existing lexical ingestion -> existing text/audio/export
custom word list    -> existing lexical ingestion -> existing text/audio/export
Kindle highlights   -> NEW fetch/normalize/extract -> existing lexical ingestion -> modified text/export profile
```

Do **not** build a separate highlights pipeline. The existing job orchestration, lexical grounding, text generation, audio synthesis, export snapshotting, and genanki packaging are the right boundaries. v1.2 should add source-specific adapters and policies, not duplicate services.

The most important architectural change is to introduce explicit **source profiles** for behavior that currently branches implicitly on `source_type == "frequency"` or `source_type == "word-list"`. Highlights need different input ingestion, no learner-facing `Translation` field, a different Anki note type/template, and slightly different sentence-generation constraints. Frequency and custom word-list behavior must remain the default and must not inherit highlight rules.

## Target v1.2 Data Flow

```text
CLI generate --source-type kindle-highlights
  |
  |-- optional WebDAV fetch
  |     WebDavHighlightSource
  |       -> raw Kindle export artifact(s) under .multilang/highlights/raw/
  |
  |-- local formatter-style normalization
  |     KindleHighlightNormalizer
  |       -> normalized highlight fragments / comma-separated text
  |
  |-- vocabulary candidate extraction
  |     HighlightVocabularyExtractor
  |       -> ordered HighlightVocabularyItem list
  |
  |-- existing GenerateJobService.orchestrate
  |     source_type = "kindle-highlights"
  |     fingerprint = hash(normalized candidate keys + source document hash)
  |
  |-- existing LexicalGroundingService
  |     persisted in lexical_candidates with source_type = "kindle-highlights"
  |
  |-- existing GenerateTextItemsService with highlight source profile
  |     concise but grammatically richer example sentence rules
  |     translation can be generated internally only if policy keeps it, but export omits it
  |
  |-- existing GenerateAudioItemsService
  |     word_audio + sentence_audio unchanged
  |
  |-- modified AssembleExportCardsService / export domain
  |     same internal snapshot columns; source-specific field mapping
  |
  `-- modified export_anki_package
        source_type-specific genanki model/template
        Highlight template: Definition on back, no Translation field
```

## Component Map: New vs Modified vs Unchanged

| Component | Status | Recommendation | Why |
|-----------|--------|----------------|-----|
| `multilang.domain.jobs.GenerationRequest` | Modified | Extend `source_type` literal to include `"kindle-highlights"`; keep `input_file` for local highlight export fixtures; add no provider-specific WebDAV fields here unless needed by CLI. | Keeps orchestration source-aware without coupling domain contracts to WebDAV credentials. |
| `multilang.settings.Settings` | Modified | Add `kindle_webdav_url`, `kindle_webdav_username`, `kindle_webdav_password`, optional `kindle_webdav_remote_path`, timeout, and local highlight artifact dir. | WebDAV config belongs in settings/env, never in domain models or committed files. |
| `WebDavHighlightSource` | New | Thin adapter using HTTP/WebDAV operations to list and download configured Kindle export files. Return raw bytes + metadata; do not normalize. | Isolates remote I/O and makes it mockable. |
| `KindleHighlightNormalizer` | New | Pure local service that reimplements Kindle Formatter-style cleanup and highlight splitting. Input bytes/text, output normalized fragments. | Highest test value; can be built and verified before WebDAV. |
| `HighlightVocabularyExtractor` | New | Convert normalized fragments into ordered vocabulary candidates compatible with existing lexical ingestion. Dedupe deterministically. | Bridges highlights to existing `LexicalCardCandidate` flow without a parallel pipeline. |
| `IngestLexicalItemsService` | Modified | Add `_ingest_kindle_highlights()` branch that calls the new normalizer/extractor, then grounds each extracted candidate like word-list items. | Reuses job lifecycle, duplicate protection, grounding, and persistence. |
| `input_fingerprint.py` | Modified | Include source document hash + normalized item keys for highlights. Ignore WebDAV timestamps unless content changes. | Reruns must be idempotent and not duplicate cards. |
| `LexicalRepository` / `lexical_candidates` table | Mostly unchanged | Store highlight metadata in existing `provenance` JSON: document path, source hash, highlight index, original fragment/excerpt, normalized fragment. | Avoids a migration-heavy highlight schema for v1.2 while preserving auditability. |
| `GenerateTextItemsService` | Modified | Replace hard-coded translation rule with source-profile policy: `requires_export_translation`, sentence min/max tokens, fallback policy. | Highlights need richer-but-concise examples and no exported translation; frequency behavior stays unchanged. |
| `TextGenerationService` / adapters | Modified lightly | Pass a generation style/profile in request provenance or an added field: `template_kind="highlight"`, `source_type="kindle-highlights"`, target length roughly 6-16 tokens. | Keeps prompt behavior source-specific without creating a separate generator. |
| `TextValidationService` | Modified | Support source-specific sentence length profile. Frequency can keep current 4-12 token gate; highlights should allow slightly richer 6-16 token sentences. | Prevents highlight examples from being rejected by frequency-deck constraints. |
| `AssembleExportCardsService` | Modified | Continue building `ExportCardRow`; for highlight source, set `translation=""` and preserve definition/audio/image fields. | Existing DB snapshot columns are sufficient. |
| `domain.exporting` | Modified | Add `HIGHLIGHT_EXPORT_CARD_FIELD_NAMES` and make `export_field_names_for_source_type()` return highlight fields for highlights. | Enables template-specific field order and omits `Translation` from exported note model. |
| `export_anki_package.py` | Modified | Add `HIGHLIGHT_MODEL_ID`, `HIGHLIGHT_NOTE_TYPE_NAME`, template resolution by source type, and robust mixed-source guard. | genanki note types must be source-specific; mixed rows in one deck should fail fast. |
| `templates/highlight_card.md` | New | Dedicated highlight template based on the supplied option B, renamed to English fields, centered/responsive, Definition on back, no Translation field. | Safer than overloading `CARD_TEMPLATE.md`. |
| `templates/russian_phoneme_card.md` | Modified | Apply provided phonetics front, back with `Sentence Translation`, remove unused conditional fields, use Multilang colors. | Template-only refresh; should not affect normal/highlight decks. |
| `russian_phoneme_deck.py` | Modified | Rename field constants to match template: likely `Sound`, `Example Sentence`, `Sentence Translation`, `Image`; keep card data. | Existing fields include no `Notes`, `is_priming`, or `is_sentence`; refresh is mostly field/template alignment. |
| Audio services | Unchanged | Reuse word and sentence audio synthesis. | Highlight mode still needs playable word and sentence audio. |
| Frequency deck services | Unchanged except source-profile safety | Existing `frequency_decks.py` and frequency ingestion should remain untouched. | Protects shipped v1.0/v1.1 behavior. |

## Source Type Policy

Introduce a small source profile module rather than scattering conditionals:

```python
@dataclass(frozen=True)
class SourceProfile:
    source_type: str
    requires_translation_validation: bool
    exports_translation_field: bool
    min_sentence_tokens: int
    max_sentence_tokens: int
    note_type_name: str
    template_name: str

SOURCE_PROFILES = {
    "frequency": SourceProfile("frequency", True, True, 4, 12, "Multilang::Card", "normal"),
    "word-list": SourceProfile("word-list", False, True, 4, 12, "Multilang::Manual Card", "normal"),
    "kindle-highlights": SourceProfile("kindle-highlights", False, False, 6, 16, "Multilang::Highlight Card", "highlight"),
}
```

Use this profile in:

- `load_requested_item_keys()` for deterministic item keys.
- `build_input_fingerprint()` for source-specific fingerprints.
- `GenerateTextItemsService._validate_bundle()` for translation and sentence-length rules.
- `export_field_names_for_source_type()` and `build_multilang_model()` for field/template selection.

This is the cleanest way to preserve existing flows while adding highlight-specific behavior.

## Schema and Domain Contract Implications

### Minimal DB migration strategy

Prefer **no new DB tables for v1.2** unless implementation discovers that raw highlight history must be queryable. Existing tables already support the new mode:

- `generation_jobs.source_type` can store `kindle-highlights`.
- `generation_jobs.source_fingerprint` can store a normalized highlight input fingerprint.
- `lexical_candidates.source_type` can store `kindle-highlights`.
- `lexical_candidates.provenance` can store highlight source metadata.
- `text_quality_records` can store generated examples and optional/empty translation text.
- `audio_assets` are unchanged.
- `card_exports` columns are sufficient even when exported highlight note fields omit `translation`.
- `deck_exports` are unchanged.

The main migration may only be needed if application-level constraints or enum assumptions exist outside Pydantic. PostgreSQL columns are plain strings, so the DB model itself does not require a source-type enum migration.

### Domain additions

Add `multilang.domain.highlights` with pure Pydantic contracts:

```python
class HighlightSourceDocument(BaseModel):
    source_uri: str
    content_hash: str
    fetched_at: datetime | None = None
    raw_storage_path: str | None = None

class NormalizedHighlight(BaseModel):
    highlight_index: int
    original_text: str
    normalized_text: str
    source_document_hash: str

class HighlightVocabularyItem(BaseModel):
    item_key: str
    submitted_form: str
    normalized_source: str
    highlight_index: int
    source_excerpt: str
```

Keep these contracts separate from `LexicalCardCandidate`. They represent input provenance, not grounded lexical data.

### Export contracts

Add source-specific field names:

```python
HIGHLIGHT_EXPORT_CARD_FIELD_NAMES = (
    "SortIndex",
    "Word",
    "IPA",
    "word_audio",
    "Example Sentence",
    "sentence_audio",
    "Definition",
    "Image",
)
```

`ExportCardRow.ordered_field_mapping()` should synthesize aliases for highlight export:

- `Word` from internal `word`.
- `Definition` from internal `definitions`.
- omit `Translation` entirely.

Do not rename DB columns for this milestone. Rename only the exported Anki field names.

## WebDAV Integration Pattern

Recommended adapter boundary:

```python
class HighlightSource(Protocol):
    def fetch_latest(self) -> list[HighlightSourceDocument]: ...

class WebDavHighlightSource:
    def fetch_latest(self) -> list[HighlightSourceDocument]:
        # list configured remote path, choose matching files, download bytes,
        # write raw artifact, return content hash + source URI metadata
```

Implementation rules:

1. Credentials come only from `Settings` / environment.
2. Raw downloads are stored under `.multilang/highlights/raw/` with content-hash filenames.
3. The normalizer consumes local raw artifacts, not live WebDAV streams.
4. WebDAV failures should fail ingestion before job creation when possible, or mark the job failed at `INGEST`; do not continue with stale remote data silently.
5. Provide a local-file path first: `--input-file highlights.txt --source-type kindle-highlights`. This gives deterministic tests and lets WebDAV be added as an adapter, not as the foundation.

## Local Normalization Pattern

`KindleHighlightNormalizer` should be pure and fixture-driven:

```text
raw Kindle export text
  -> normalize line endings / Unicode / whitespace
  -> remove location/book metadata if present
  -> split highlight entries
  -> discard empty or boilerplate entries
  -> emit NormalizedHighlight list
```

`HighlightVocabularyExtractor` should then produce stable candidate keys:

```text
highlight-0001-word-0001
highlight-0001-word-0002
highlight-0002-word-0001
```

Use deterministic dedupe by normalized token/lemma candidate while preserving first-seen order. Do not use AI for the first extractor version unless local extraction proves insufficient. AI can later be added behind an adapter to rank or select vocabulary from normalized highlight fragments, but v1.2 should keep ingestion reproducible.

## Highlight Deck Generation and Template Export

### Export behavior

Highlights need a distinct Anki model:

| Aspect | Frequency / word-list | Kindle highlights |
|--------|------------------------|-------------------|
| Note type | `Multilang::Card` / `Multilang::Manual Card` | `Multilang::Highlight Card` |
| Template source | current normal template | new `templates/highlight_card.md` |
| Definition placement | front currently includes definition | back only |
| Translation field | present in field list | omitted |
| Audio | word + sentence audio | word + sentence audio |
| Image | blank image field | blank image field |

`export_anki_package()` should fail if rows include mixed source types. Current source detection treats non-word-list as frequency; v1.2 must replace this with exact source-type resolution:

```python
source_types = {row.identity.source_type for row in rows}
if len(source_types) != 1:
    raise ExportAnkiPackageError("cannot export mixed source types in one note model")
source_type = source_types.pop()
```

### Template storage

Do not keep adding template variants to `CARD_TEMPLATE.md`. Move toward source-specific template files:

```text
templates/
  normal_card.md              # existing normal deck template, or current CARD_TEMPLATE.md kept temporarily
  highlight_card.md           # new highlight template
  russian_phoneme_card.md     # existing phoneme template, refreshed
```

If moving the normal template is too much churn for v1.2, keep `CARD_TEMPLATE.md` for existing decks and add only `templates/highlight_card.md`. The loader can branch without changing old template paths.

## Phonetics Template Refresh Integration

The phonetics deck is currently isolated in `services/russian_phoneme_deck.py` and `templates/russian_phoneme_card.md`. Keep it isolated.

Required integration changes:

1. Update `PHONEME_FIELD_NAMES` to match the supplied front template and requested back behavior:
   - `Spellings`
   - `Sound` instead of current `IPA` if the template uses `{{Sound}}`
   - `letter_audio`
   - `Example Word`
   - `word_audio`
   - `Word Translation`
   - `Example Sentence` instead of current typo `Exemple Sentence`
   - `sentence_audio`
   - `Sentence Translation` instead of current `Translation`
   - `Image`
2. Update `_phoneme_card_fields()` mapping only; keep `RussianPhonemeCard` data unchanged.
3. Remove any `{{#Notes}}`, `{{is_priming}}`, or `{{is_sentence}}` references from the template. The current Python model does not include those fields, so they should not be introduced.
4. Use Multilang colors in CSS and preserve responsiveness.
5. Add tests that inspect model fields and rendered template strings; no normal/highlight export code should depend on phoneme internals.

No database migration is needed for phonetics because this deck is generated deterministically in-memory and not through job tables.

## Safe Build Order for Roadmap

### Phase 1: Source profiles and export isolation

**Build first:**

- Add `kindle-highlights` to `GenerationRequest.source_type`.
- Add source profile helper.
- Update `export_field_names_for_source_type()` and genanki source-type resolution.
- Add tests proving frequency and word-list field names/model IDs are unchanged.

**Rationale:** prevents highlight-specific export/template work from breaking shipped decks.

### Phase 2: Local highlight normalization and candidate extraction

**Build:**

- `domain.highlights` contracts.
- `KindleHighlightNormalizer` with raw Kindle fixtures.
- `HighlightVocabularyExtractor` with deterministic item keys/dedupe.
- Local CLI path from `--input-file`.

**Rationale:** local normalization is the core product behavior and can be validated without remote I/O.

### Phase 3: Ingest highlights into existing lexical pipeline

**Build:**

- `_ingest_kindle_highlights()` in `IngestLexicalItemsService`.
- `load_requested_item_keys()` support.
- `input_fingerprint.py` support.
- Provenance JSON for source document hash/highlight index/excerpt.

**Rationale:** this proves highlights can reuse grounding, jobs, resume, and duplicate prevention.

### Phase 4: Highlight text-generation profile

**Build:**

- Source-specific sentence length and prompt style.
- Validation profile for 6-16 token concise-but-richer sentences.
- Ensure highlight export omits translation even if translation exists internally.

**Rationale:** sentence behavior is quality-sensitive but should ride on existing generator/validator seams.

### Phase 5: Highlight template and export

**Build:**

- `templates/highlight_card.md`.
- `HIGHLIGHT_MODEL_ID`, `HIGHLIGHT_NOTE_TYPE_NAME`.
- `.apkg`, CSV, TSV tests for no `Translation` field and Definition on back.

**Rationale:** export should happen after source/profile behavior is stable.

### Phase 6: WebDAV fetch adapter

**Build:**

- Settings and CLI flags for WebDAV fetch.
- `WebDavHighlightSource` with fake adapter tests.
- Raw artifact storage by content hash.
- Integration test using a local/fake WebDAV response, not the real service.

**Rationale:** remote ingestion is valuable but should not block local highlight generation.

### Phase 7: Phonetics template refresh

**Build:**

- Update `russian_phoneme_deck.py` field names/mapping.
- Refresh `templates/russian_phoneme_card.md`.
- Add focused phoneme model/template tests.

**Rationale:** independent from highlights; can be scheduled before or after Phase 6 if desired, but should remain separate to reduce regression blast radius.

## Test Seams

| Seam | Tests to Add | Regression Guard |
|------|--------------|------------------|
| Source profiles | Unit tests for frequency, word-list, kindle-highlights settings | Frequency requires translation and exports existing fields; highlights omits translation. |
| WebDAV adapter | Mock/fake HTTP/WebDAV list/download responses; credential missing tests | No real network in unit tests; no secret leakage in errors. |
| Normalizer | Golden fixtures from real Kindle exports and Kindle Formatter-style expected output | Handles line endings, metadata, empty highlights, duplicated fragments. |
| Vocabulary extractor | Deterministic item keys, dedupe, order preservation | Same input hash produces same job run key. |
| Highlight ingestion | Repository-backed test for lexical candidates with `source_type="kindle-highlights"` and provenance | Does not alter frequency/word-list ingestion counts. |
| Input fingerprint | Hash changes when normalized content changes; does not change for timestamp-only WebDAV metadata | Prevents silent duplicates and unnecessary reruns. |
| Text generation profile | Adapter receives highlight style/profile; validation accepts richer concise sentence | Frequency max-length behavior remains unchanged. |
| Export field mapping | `ExportCardRow.ordered_field_mapping(source_type=kindle-highlights)` omits `Translation`, maps `Definition` | Existing `FREQUENCY_EXPORT_CARD_FIELD_NAMES` unchanged. |
| genanki model selection | Model ID/name/fields for each source type | Mixed-source export raises error. |
| Highlight template | HTML contains Definition on back, no Translation placeholder, centered responsive CSS | Field names exactly match genanki model fields. |
| Phoneme template | Field names include `Sentence Translation`; no `Notes`, `is_priming`, `is_sentence`; typo fixed | Normal and highlight templates unaffected. |
| E2E smoke | Local highlight fixture -> 3-5 cards -> audio mocked/local -> `.apkg` package | Existing frequency and word-list smoke tests still pass. |

## Integration Risks and Mitigations

### Risk 1: Highlight mode accidentally changes shipped deck behavior

**Why it happens:** existing code branches on `source_type != "word-list"`, which would treat highlights as frequency.  
**Mitigation:** add explicit source profiles and tests around translation validation, field names, and model selection before building highlight ingestion.

### Risk 2: WebDAV variability hides normalization bugs

**Why it happens:** remote file names, export formats, or network failures can vary.  
**Mitigation:** build local file ingestion first; store raw downloads by content hash; run normalizer against fixtures.

### Risk 3: Overengineering raw highlight persistence

**Why it happens:** it is tempting to model books/highlights/documents in normalized DB tables.  
**Mitigation:** for v1.2, use raw filesystem artifacts plus `lexical_candidates.provenance` JSON. Add tables later only if querying highlight history becomes a real requirement.

### Risk 4: Translation assumptions leak into highlight export

**Why it happens:** existing `ExportCardRow` and templates include `Translation` by default.  
**Mitigation:** source-specific export field mapping; highlight template must not reference `Translation`; tests inspect genanki model fields.

### Risk 5: Sentence-length validator rejects the desired richer examples

**Why it happens:** current validation max is 12 tokens globally.  
**Mitigation:** source-specific validation profile: highlights allow approximately 6-16 tokens while frequency remains 4-12.

### Risk 6: Phoneme field renames break template rendering

**Why it happens:** current field names include `IPA`, `Exemple Sentence`, and `Translation`; provided front uses `Sound` and requested back uses `Sentence Translation`.  
**Mitigation:** update field constants and mapping atomically with template tests.

### Risk 7: Mixed-source export creates invalid note models

**Why it happens:** current export chooses frequency unless all rows are word-list.  
**Mitigation:** fail fast on mixed source types and select exact source model.

## Architecture Decision Summary

- Add `kindle-highlights` as a **new source type**, not a replacement for frequency decks.
- Build highlights ingestion as **fetch → normalize → extract candidates → existing lexical pipeline**.
- Keep WebDAV behind a small adapter; build and test local file normalization first.
- Use source profiles to control translation, sentence-length, and export/template behavior.
- Reuse existing DB tables; put highlight-specific audit data in provenance JSON for v1.2.
- Add a dedicated highlight Anki note type/template; omit `Translation` at the exported field level.
- Keep the phonetics refresh isolated in `russian_phoneme_deck.py` and its template file.

## Sources and Evidence

- `.planning/PROJECT.md` — active v1.2 requirements and constraints. [HIGH]
- `alter_organizado.md` — user-provided WebDAV, template, sentence, and phonetics requirements. [HIGH]
- `.planning/ROADMAP.md` — current v1.1 completion context. [HIGH]
- `.planning/REQUIREMENTS.md` — v1.1 template/audio/pronunciation constraints to preserve. [HIGH]
- Code inspection: `domain.jobs`, `ingest_lexical_items`, `generate_text_items`, `text_generation`, `text_validation`, `domain.exporting`, `assemble_export_cards`, `export_anki_package`, `russian_phoneme_deck`, `settings`, repositories, and DB models. [HIGH]
