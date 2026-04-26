# Phase 05 Research — Anki-Safe Export Contract

**Date:** 2026-04-26
**Phase:** 05-anki-safe-export-contract
**Discovery level:** Level 2 — new external dependency (`genanki`) plus export/import contract decisions

## Research Question

What needs to be true for Multilang to export fixed-schema cards as `.apkg`, CSV, and TSV artifacts that import into Anki without repair, preserve media playback, and remain deterministic across reruns?

## Bottom-Line Recommendation

- Use **`genanki` 0.13.x** for `.apkg` generation.
- Freeze one **stable note type** with the exact field order required by `CARD-01`.
- Build **deterministic note GUIDs** from stable card identity fields, not mutable content.
- Emit **audio references inside fields** as `[sound:filename.mp3]` using **basename-only** filenames.
- Keep `Definitions` as a single HTML field joined with `<br>` separators.
- Export **both TSV and CSV** as UTF-8 plain-text fallbacks using Python's `csv` module; prefer TSV as the safest default for multiline and comma-heavy content.
- Treat `.apkg` as the **reimport-safe primary artifact** and CSV/TSV as the **plain-text fallback**.

## Findings

### 1) `genanki` fits the export shape

`genanki` supports:
- fixed field-order note models
- explicit front/back templates
- CSS on the model
- deck packaging through `genanki.Package(...).write_to_file(...)`
- bundled media via `package.media_files`
- custom stable note GUIDs by subclassing `genanki.Note`

**Implication:** Multilang should create one export-specific model and note subclass instead of building ad-hoc `.apkg` internals.

### 2) Model IDs and deck IDs must be stable

`genanki` requires hardcoded numeric `model_id` and `deck_id` values. Changing them later risks note-type churn or duplicate deck behavior on import.

**Implication:** Phase 05 should introduce export constants with permanently stable IDs for the Multilang note type and exported deck family.

### 3) Reimport reliability depends on stable note GUIDs

`genanki` defaults note GUIDs to a hash of all field values. That is wrong for Multilang because changing definitions, sentences, translations, or audio would change identity and create duplicates instead of updates.

**Implication:** Multilang must compute GUIDs from **stable identity only** — e.g. language + source type + item key + lemma/sort identity — and never from mutable enrichment fields.

### 4) Field content is HTML, not plain text

Both `genanki` fields and Anki text imports treat field values as HTML-capable content. Literal `<`, `>`, and `&` must be escaped when they are not intentional markup.

**Implication:** Export assembly must sanitize text while still allowing intentional `<br>` separators in `Definitions`.

### 5) Audio references belong in fields, not templates

Anki and `genanki` both expect media references such as `[sound:file.mp3]` to live in field values. Template-level dynamic media references like `[sound:{{Word}}]` are unsupported.

**Implication:** Multilang should populate `word_audio` and `sentence_audio` field values with full `[sound:...]` strings during export assembly.

### 6) Media filenames must be basename-only in note fields

Anki media references must use the filename only. Subdirectories in field references break import expectations. The package can include absolute/relative paths in `media_files`, but the field value must reference the basename.

**Implication:** Export assembly must strip directories from persisted `storage_path` values before placing them into note fields.

### 7) `.apkg` imports update by note identity and modification time

Packaged deck imports can update previously imported notes when identity is preserved. Changing the note type structure makes updates less reliable.

**Implication:** Phase 05 must freeze the field list and template behavior now, and later changes should be additive only with strong compatibility review.

### 8) CSV/TSV import safety depends on UTF-8 and explicit structure

Anki text import expects plain-text UTF-8 files. It guesses separators unless headers are provided. Multiline fields and separators must be quoted or represented with HTML `<br>`.

**Implication:** Multilang should:
- write UTF-8 files explicitly
- use Python's `csv` module instead of hand-rolled escaping
- include import headers such as `#separator`, `#html:true`, `#notetype`, `#deck`, and `#columns`
- emit deterministic column order matching the fixed card schema

### 9) TSV is the safest plain-text default

Anki itself exports text with tab-separated fields. Tabs reduce collisions with natural-language commas and semicolons.

**Implication:** Multilang should support both CSV and TSV because the requirement asks for both, but docs/tests should treat TSV as the more robust fallback artifact.

### 10) Phase 05 should export only accepted text rows with valid audio references

Existing Phase 3 and 4 contracts already distinguish accepted text from flagged rows and successful audio from failed assets.

**Implication:** Export assembly should only include rows where:
- lexical grounding exists
- text review status is accepted
- required audio references either exist as synthesized/reused assets or are handled by a documented omission policy enforced in tests

For this phase's trust-first goal, the recommended policy is to **block `.apkg` export when required audio references are missing** instead of silently emitting broken sound tags.

## Recommended Export Contract

### Fixed field order (must not drift)

1. `SortIndex`
2. `word`
3. `Front of Card`
4. `IPA`
5. `Definitions`
6. `Example Sentence`
7. `Translation`
8. `word_audio`
9. `sentence_audio`
10. `Image`

### Template behavior

- **Front:** show `Front of Card`, optionally pronunciation/context, but **do not show `Translation`**
- **Back:** show `{{FrontSide}}`, separator, then `Definitions`, `Example Sentence`, `Translation`, and audio fields
- `Image` stays blank in exported data

### Definitions formatting

- one field only
- multiple senses joined with `<br>`
- never emit nested `<ul>`/`<li>` markup

### Audio formatting

- `word_audio` = `[sound:<basename>.mp3]` or empty string when policy allows omission
- `sentence_audio` = `[sound:<basename>.mp3]` or empty string when policy allows omission
- packaged media list contains the corresponding on-disk files

## Architecture Recommendation

### Domain layer

Add an export domain contract that represents:
- stable card identity
- exact field order
- note GUID
- tabular row values
- Anki note payload
- export artifact metadata (`apkg`, `csv`, `tsv`)

### Persistence layer

Add dedicated persistence for:
- frozen per-card export snapshots (`card_exports`)
- produced artifact manifests (`deck_exports`)

This matches the project stack recommendation that includes `card` and `deck_export` storage objects.

### Service layer

Split implementation into:
1. **card assembly** — converts lexical/text/audio rows into fixed export cards
2. **tabular export** — writes UTF-8 CSV/TSV fallbacks
3. **Anki package export** — builds `genanki` model/deck/package and bundles media
4. **runtime/CLI export orchestration** — exposes export on the shipped CLI path

## Common Pitfalls To Avoid

- Do **not** generate random GUIDs per run.
- Do **not** derive GUIDs from mutable fields like sentence or translation text.
- Do **not** place media paths like `audio/word/file.mp3` in Anki field values; use `file.mp3` only.
- Do **not** put `[sound:{{field}}]` or `<img src="{{field}}">` in templates.
- Do **not** hand-roll CSV escaping.
- Do **not** emit literal `<ul>`/`<li>` lists for `Definitions`.
- Do **not** silently package cards with missing audio files.
- Do **not** change field order across formats.

## Validation Architecture

Phase 05 should verify export safety at three levels:

1. **Contract tests**
   - fixed field order
   - definitions rendered as one field with `<br>` joins
   - translation excluded from front template
   - image field empty
   - deterministic GUID stability across reruns

2. **Artifact tests**
   - CSV/TSV are UTF-8
   - headers match the contract
   - multiline/HTML content round-trips correctly
   - `.apkg` contains packaged media and note data

3. **Workflow tests**
   - shipped CLI can export by job id
   - rerunning export for the same job preserves note identity
   - missing media or unaccepted text fails with explicit diagnostics

4. **Manual verification**
   - import sample `.apkg` into Anki without field remapping
   - confirm `Translation` is hidden on the front and shown on the back
   - confirm packaged audio plays after import

## Architectural Responsibility Map

| Concern | Tier | Responsibility |
|--------|------|----------------|
| fixed field order, GUID rules, audio-tag formatting | domain/service | pure deterministic export contract logic |
| card/export snapshot persistence | repository/db | store frozen export rows and artifact manifests |
| CSV/TSV writing | service | UTF-8-safe serialization with explicit headers |
| `.apkg` model/template/media packaging | service | `genanki` integration and media bundling |
| command surface | CLI/runtime | expose export flow and diagnostics |
| import/playback confirmation | human verification | final Anki desktop validation |

## Sources

- PyPI — `genanki` 0.13.1: https://pypi.org/project/genanki/
- Anki Manual — Text Files: https://docs.ankiweb.net/importing/text-files.html
- Anki Manual — Field Replacements / Media & LaTeX: https://docs.ankiweb.net/templates/fields.html
- Anki Manual — Media: https://docs.ankiweb.net/media.html
- Anki Manual — Packaged Decks: https://docs.ankiweb.net/importing/packaged-decks.html
- Anki Manual — Exporting: https://docs.ankiweb.net/exporting.html#packaged-decks
