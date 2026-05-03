# Stack Research: v1.2 Kindle Highlights and Template Refresh

**Project:** Multilang Anki Card Generator  
**Milestone:** v1.2 Kindle Highlights and Template Refresh  
**Researched:** 2026-05-03  
**Scope:** Stack additions/changes only for WebDAV Kindle highlight ingestion, local Kindle Formatter-style normalization, highlight deck templates, concise richer examples, and phonetics template refresh. Existing Python 3.12/uv/Typer/Pydantic/SQLAlchemy/Alembic/Azure/genanki choices remain valid and should not be reworked.

## Recommendation Summary

Do **not** add a new application framework or browser automation layer for v1.2. Implement Kindle highlight ingestion as a small typed Python adapter in the existing CLI/domain/persistence pipeline: `httpx` for WebDAV `PROPFIND`/`GET`, `defusedxml` for safe WebDAV XML parsing, stdlib `html.parser`/`html`/`re`/`unicodedata` for local Kindle export normalization, existing Pydantic models for normalized highlight contracts, existing SQLAlchemy/Alembic tables for idempotent import tracking, and existing `genanki` model/template support for highlight and phonetics decks.

The only runtime dependency I recommend adding is **`defusedxml==0.7.1`** if it is not already present. Use existing `httpx` if already in the project; if not pinned yet, pin the current stable **`httpx==0.28.1`** rather than adding a WebDAV-specific library. Add **`respx==0.23.1`** as a dev dependency only if the current test suite lacks HTTPX request mocking.

This milestone is mostly about **adapters, contracts, templates, and regression tests**, not new external services. The roadmap should schedule work around: WebDAV source adapter, Kindle HTML/text normalizer, highlight candidate mapper, highlight deck export model, phonetics template refresh, and golden-file/export validation.

## Stack Additions

| Area | Recommendation | Version / Status | Runtime or Dev | Why | Confidence |
|---|---|---:|---|---|---|
| WebDAV HTTP client | `httpx` | `0.28.1` current stable; `1.0.dev*` exists but do not use pre-release | Runtime if not already present | Supports custom HTTP methods through generic requests, strict timeouts, Basic/Digest auth, sync/async APIs, and matches existing FastAPI/HTTPX testing stack. | HIGH |
| WebDAV XML parsing | `defusedxml.ElementTree` | `0.7.1` latest stable; old but production/stable | Runtime | WebDAV `PROPFIND` returns XML `207 Multi-Status`; safe XML parsing avoids entity-expansion/XXE issues from remote server responses. | HIGH |
| Kindle export parsing | stdlib `html.parser.HTMLParser`, `html.unescape` / `html.escape` | Python 3.12 baseline | Runtime | Kindle Formatter is a client-side HTML normalizer. For v1.2, parse exported Kindle HTML locally into highlights/notes without a heavyweight HTML dependency. | MEDIUM-HIGH |
| Text normalization | stdlib `re`, `unicodedata`, `pathlib`, `hashlib`, `datetime` | Python 3.12 baseline | Runtime | Handles whitespace collapse, comma/newline formatting, Unicode quote/dash cleanup, deterministic source hashes, file naming, and import timestamps without dependency bloat. | HIGH |
| Import/export text artifacts | stdlib `csv` | Python 3.12 baseline | Runtime | Existing CSV/TSV artifacts can support normalized highlight audit output and candidate review; no pandas needed. | HIGH |
| Highlight contracts | Existing Pydantic v2 | Already validated stack | Runtime | Define `WebDavResource`, `KindleHighlightRaw`, `KindleHighlightNormalized`, `HighlightDeckCandidate`, and `HighlightCard` contracts. Avoid untyped dicts between ingestion and generation. | HIGH |
| Persistence | Existing SQLAlchemy/Alembic | Already validated stack | Runtime | Add import-source/job tables and uniqueness constraints for idempotent highlight ingestion; no new database. | HIGH |
| Anki templates | Existing `genanki` | Existing stack (`0.13.1` previously recommended) | Runtime | `genanki.Model` supports fields, templates, CSS, media files, stable model IDs/GUIDs, and multiple note models for highlight vs phonetics cards. | HIGH |
| HTTP mocking | `respx` | `0.23.1` current, released 2026-04-08 | Dev only | Mock WebDAV `PROPFIND`, `GET`, redirects, auth failures, timeouts, and malformed XML at HTTPX layer. Add only if existing HTTPX mocks are insufficient. | HIGH |

### Minimal uv changes

```bash
# runtime addition
uv add defusedxml

# only if httpx is not already installed/pinned
uv add httpx

# only if current tests cannot mock HTTPX requests cleanly
uv add --dev respx
```

Do not pin to HTTPX `1.0.dev*`; PyPI shows pre-releases, but v1.2 should use stable `0.28.1` unless the project has a deliberate pre-release policy.

## Integration Points

### 1. WebDAV ingestion adapter

Add a source adapter, not a new service:

- `KindleWebDavSource` or `WebDavHighlightSource` using `httpx.Client` / existing project HTTP client conventions.
- Operations needed for v1.2:
  - `PROPFIND` configured directory (`Depth: 1`) to list candidate files.
  - Parse `207 Multi-Status` XML with `defusedxml.ElementTree`.
  - Select newest or matching Kindle export files by extension/name/mtime/ETag.
  - `GET` selected file content.
  - Persist source URL, ETag / Last-Modified where available, content hash, fetched timestamp, and import job ID.
- Keep credentials in existing config/env handling. Do not store WebDAV passwords in DB or exported artifacts.

Use direct WebDAV protocol support rather than a WebDAV package because v1.2 only needs read/list/download. RFC 4918 confirms these are standard HTTP extensions (`PROPFIND`, `Depth`, `207 Multi-Status`) over normal HTTP.

### 2. Local Kindle Formatter-style normalization

Implement as a deterministic local module, e.g. `kindle_normalizer.py`:

- Input: raw Kindle exported HTML/text bytes from WebDAV or local fixture.
- Decode with explicit UTF-8 fallback strategy and preserve raw content hash.
- Use `html.parser.HTMLParser` to extract book title/author if present and highlight/note text blocks.
- Use `html.unescape`, `unicodedata.normalize("NFC", ...)`, `re` whitespace cleanup, and quote/dash normalization rules.
- Output Pydantic records with raw text, normalized text, source book metadata, source position if available, and deterministic highlight hash.
- Produce comma-separated or line-separated normalized candidate text only as an **artifact**, not as the internal canonical model.

The pch Kindle Formatter page confirms the existing external tool accepts Kindle-exported HTML and produces Markdown/plain text in-browser. Reimplement the necessary deterministic subset locally; do not automate the site.

### 3. Highlight deck candidate flow

Integrate highlights as a third input mode beside frequency and custom word-list flows:

- Add CLI commands/options such as `import-kindle-highlights`, `normalize-highlights`, and `generate --mode highlights` or equivalent consistent with existing Typer command style.
- Convert normalized highlights to candidate vocabulary through existing word-list/generation pipeline where possible, but tag source as `highlight`.
- Preserve existing frequency deck mode; despite `alter_organizado.md` saying highlights may replace `wordfreq` for this workflow, project constraints say highlights are a **new mode**, not a replacement.
- Store source provenance so generated highlight cards can be traced back to book/export/highlight.

### 4. Highlight-specific Anki model/template

Use existing `genanki` export layer but add a separate note model for highlight cards:

- Field names should be English and stable, e.g. `SortIndex`, `Word`, `IPA`, `Example Sentence`, `Definition`, `word_audio`, `sentence_audio`, `Image`, plus optional hidden provenance fields only if they do not leak into the template.
- No `Translation` field for highlight cards.
- Front: word, IPA, audio, example sentence.
- Back: `{{FrontSide}}`, divider, `Definition`, blank/manual image field.
- CSS: centered responsive layout using Multilang colors; adapt the supplied template but avoid fragile inline JS autoplay assumptions as a core requirement.

Genanki supports separate `Model` definitions with fields/templates/CSS and media packaging, so this does not require a new export library.

### 5. Phonetics template refresh

Keep this inside the existing genanki template registry:

- Add/update the phonetics model fields to remove unused `Notes`, `is_priming`, and `is_sentence` from the export contract where safe.
- Use the supplied front template structure.
- Back should reveal `Sentence Translation` like the normal card behavior.
- Restyle CSS to Multilang colors.
- Preserve media field references: `letter_audio`, `word_audio`, `sentence_audio`.

This is template/model contract work, not new TTS/audio stack work.

### 6. Example sentence rule refresh

No new sentence-generation library is needed. Adjust existing LLM prompt/contracts/validators:

- Add highlight-mode sentence policy: grammatically richer than v1.0/v1.1 but still concise.
- Validate max token/character length, target word inclusion, no excessive clauses, and no translation field for highlight decks.
- Keep existing text validation/regeneration path.

## Testing Notes

### Unit tests

- WebDAV XML parser:
  - Valid `207 Multi-Status` with multiple resources.
  - Namespaces and URL-encoded filenames.
  - Missing ETag/Last-Modified.
  - Malformed XML and entity/DTD payloads blocked by `defusedxml`.
- Kindle normalizer:
  - Golden fixtures for representative Kindle-exported HTML.
  - Unicode normalization, smart quotes, em/en dashes, non-breaking spaces, duplicated whitespace.
  - Empty highlights, notes without highlights, duplicate highlights, multiline highlights.
- Pydantic contracts:
  - Raw-to-normalized-to-candidate schema validation.
  - Deterministic hashes and dedupe keys.

### Adapter/integration tests

- Use `respx` or existing HTTPX mock utilities to test:
  - `PROPFIND` then `GET` happy path.
  - 401/403 auth errors.
  - 404 configured folder/file not found.
  - Timeout/retry behavior according to existing retry policy.
  - Server redirects and trailing-slash collection behavior.
- Use SQLAlchemy tests for idempotent imports:
  - Same ETag/hash does not duplicate records.
  - Changed content creates a new import version.
  - Candidate/card generation can resume after partial failure.

### Export regression tests

- Golden-file or model snapshot tests for:
  - Highlight model field order and absence of `Translation`.
  - `Definition` only on the back.
  - English field names in templates.
  - Responsive CSS retained in generated model.
  - Phonetics model no longer references removed fields.
  - Back template reveals `Sentence Translation`.
  - Stable GUIDs for highlight cards, preferably derived from `(language, normalized_word_or_lemma, highlight_source_hash)` or an explicit candidate identity.

### Manual smoke tests

- Fetch one real WebDAV export from `https://otaru.infini-cloud.net/dav/` using configured credentials.
- Generate a tiny highlight deck and import into Anki Desktop.
- Confirm media references play, layout is centered on desktop/mobile widths, highlight cards have no translation, and phonetics back reveals sentence translation.

## What Not To Add

| Avoid | Why |
|---|---|
| Browser automation / Playwright / Selenium for Kindle Formatter | The external formatter is a static client-side tool; automation would be brittle, untestable, and unnecessary. Reimplement normalization locally. |
| A WebDAV-specific dependency as the default (`webdavclient3`, etc.) | v1.2 only needs list/download. Direct `httpx` keeps behavior transparent, typed, and easy to mock. Reconsider only if the real server exposes non-standard quirks that make direct HTTP too costly. |
| BeautifulSoup/lxml as default HTML parser | Kindle export normalization is narrow. Start with stdlib `html.parser`; add `beautifulsoup4` only if real Kindle fixtures prove malformed markup cannot be handled deterministically. Avoid `lxml` unless needed because it expands the dependency/security surface. |
| pandas | Highlight normalization is record parsing, not dataframe analytics. Pydantic + stdlib CSV is enough. |
| New database or queue | Existing SQLAlchemy/Alembic persistence and job tracking are sufficient for v1.2. Add queue work only if parallel ingestion/generation becomes a measured bottleneck. |
| New LLM/translation provider | Highlight mode changes prompt rules and templates, not provider strategy. Keep existing generation/validation stack. |
| New Anki export library | `genanki` already supports separate models, CSS, templates, media files, and stable note GUIDs. |
| Storing WebDAV secrets in imported source rows | Credentials should stay in env/config/secrets handling; persist only non-secret source metadata. |

## Sources/Confidence

| Source | Finding Used | Confidence |
|---|---|---|
| Project context: `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `alter_organizado.md` | v1.2 scope, current stack constraints, highlight/template requirements. | HIGH |
| HTTPX docs — https://www.python-httpx.org/ | HTTPX provides sync/async APIs, strict timeouts, auth support, custom HTTP transport behavior; appropriate for WebDAV requests. | HIGH |
| HTTPX PyPI — https://pypi.org/project/httpx/ | Current stable `0.28.1`; `1.0.dev*` pre-releases exist. | HIGH |
| RFC 4918 — https://www.rfc-editor.org/rfc/rfc4918 | WebDAV uses HTTP methods/headers and XML `207 Multi-Status`; `PROPFIND` and `Depth` are standard. | HIGH |
| defusedxml PyPI — https://pypi.org/project/defusedxml/ | Latest stable `0.7.1`; package protects stdlib XML parsing from entity expansion/external reference risks. | HIGH |
| Python `html.parser` docs — https://docs.python.org/3/library/html.parser.html | Stdlib parser handles invalid HTML and exposes events for tags/data/comments; suitable for deterministic Kindle export extraction. | HIGH |
| Python `csv` docs — https://docs.python.org/3/library/csv.html | Stdlib CSV supports dialects and dict reader/writer for audit artifacts. | HIGH |
| Python `re` docs — https://docs.python.org/3/library/re.html | Stdlib regex supports Unicode string matching and compiled patterns for normalization rules. | HIGH |
| Kindle Formatter page — https://pch.github.io/kindle-formatter/ | External formatter is browser/local-file oriented and transforms Kindle-exported HTML to Markdown/plain text. | MEDIUM |
| Anki Manual templates — https://docs.ankiweb.net/templates/intro.html | Anki templates are HTML/CSS and control front/back field display. | HIGH |
| genanki GitHub README — https://github.com/kerrickstaley/genanki | `genanki.Model` supports fields/templates/CSS/media and stable GUID customization. | HIGH |
| RESPX PyPI — https://pypi.org/project/respx/ | Current `0.23.1`; mocks HTTPX/HTTP Core for pytest. | HIGH |

**Overall confidence:** HIGH for WebDAV/httpx/defusedxml/genanki recommendations; MEDIUM-HIGH for stdlib-only Kindle normalization until real exported Kindle fixtures from the user's WebDAV folder are validated.
