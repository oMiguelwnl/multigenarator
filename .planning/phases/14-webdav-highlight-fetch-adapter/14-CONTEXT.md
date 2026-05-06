# Phase 14: WebDAV Highlight Fetch Adapter - Context

**Gathered:** 2026-05-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 14 adds secure WebDAV fetching for Kindle highlight exports. The phase covers configuration, remote listing, explicit remote file fetch, safe local handoff into the existing local Kindle normalization path, clear redacted failure handling, and idempotent sync summaries. It does not change highlight generation, highlight export templates, phonetics templates, or existing frequency/custom deck behavior.

</domain>

<decisions>
## Implementation Decisions

### Config and Secrets
- **D-01:** WebDAV URL is provided through typed `Settings` using a `MULTILANG_*` environment variable, matching the existing env/.env configuration pattern.
- **D-02:** WebDAV username and secret are env-only settings. Do not add CLI flags for secrets.
- **D-03:** Per-run CLI secret overrides are not allowed. Non-secret command arguments may exist only where needed for remote selection.
- **D-04:** Missing required WebDAV configuration fails before any network request with a clear redacted configuration error.

### Remote Selection
- **D-05:** Fetching requires an explicit remote file path or selected candidate; do not auto-pick the latest export.
- **D-06:** Remote listing shows safe/sanitized candidate names plus safe metadata when available. Do not print full WebDAV URLs or credentials.
- **D-07:** Candidate filtering is limited to the local parser's supported Kindle export formats: `.html`, `.htm`, and `.txt`.
- **D-08:** Listing and fetching should be separate CLI commands or subcommands so listing can safely expose candidates and fetching remains deterministic/testable.

### Fetched File Handling
- **D-09:** Fetched WebDAV exports are saved to an ignored private cache under `.multilang` rather than committed or written to planning artifacts.
- **D-10:** Safe manifests persist only hashes, candidate keys, and counts. Do not persist raw remote paths, raw highlight text, credentials, book metadata, or raw response bodies in safe/public records.
- **D-11:** Idempotency is content-hash based. Unchanged remote content should reuse existing import/candidate identity and report unchanged/reused counts.
- **D-12:** WebDAV-fetched content must feed the same local Kindle parser/preview/generation path used by local `--input-file` imports.

### Failure and Summary Output
- **D-13:** Failure output uses distinct safe failure types for missing config, auth, path/not-found, network, malformed response, unsupported format, and empty source.
- **D-14:** Malformed WebDAV responses fail closed and must not write cache files, import records, or manifests from guessed/partial content.
- **D-15:** Successful fetch summaries print safe counts and hash identity, including imported/rejected/extracted/duplicate/planned/reused/new counts where available.
- **D-16:** Failures, logs, reports, summaries, tests, and artifacts must never include raw credentials, full remote URLs, raw remote paths with private metadata, raw response bodies, or raw highlight text.

### the agent's Discretion
- Exact command names, option names, internal class names, and test fixture shapes are left to downstream research/planning as long as they satisfy the decisions above and preserve existing CLI/test patterns.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Planning Constraints
- `.planning/ROADMAP.md` - Phase 14 goal, dependency on Phase 13, and success criteria for secure WebDAV fetch, listing, explicit selection, distinct failures, and idempotent redacted summaries.
- `.planning/REQUIREMENTS.md` - `INGEST-01`, `INGEST-02`, `SEC-01`, and v1.2 out-of-scope boundaries for credentials, raw exports, and private highlights.
- `.planning/PROJECT.md` - Current milestone context and carry-forward decisions for highlights, Azure/audio stability, blank image field, and privacy-safe WebDAV/highlight behavior.
- `.planning/STATE.md` - Current carry-forward implementation decisions from Phases 09-13, especially source profiles, redaction, highlight manifests, and template isolation.

### Existing Implementation Contracts
- `src/multilang/settings.py` - Existing typed `Settings` env/.env pattern using `MULTILANG_` prefix.
- `src/multilang/cli.py` - Current Typer command structure, `preview-kindle-highlights`, public `--source highlights` mapping, and key=value summary output style.
- `src/multilang/services/kindle_highlight_parser.py` - Existing path-based local parser for `.html`, `.htm`, and `.txt` with safe rejected-highlight reasons.
- `src/multilang/services/highlight_import_preview.py` - Count-only local preview flow that combines parser and candidate extraction.
- `src/multilang/services/ingest_lexical_items.py` - Current highlight ingestion path, import content hashing, candidate extraction, safe manifest writes, and CLI summary counts.
- `src/multilang/repositories/highlight_import_repository.py` - Private highlight record storage and safe manifest repository boundary.
- `src/multilang/security/redaction.py` - Redaction helpers for credentials, URLs, WebDAV paths, book metadata, and private text.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Settings` in `src/multilang/settings.py`: use this for WebDAV URL, username, secret, timeout, and private cache location rather than ad hoc config loading.
- `redact_sensitive_text`, `redact_mapping`, and `redact_exception` in `src/multilang/security/redaction.py`: apply these to every WebDAV diagnostic, exception, and summary path before display or persistence.
- `parse_kindle_highlight_export` in `src/multilang/services/kindle_highlight_parser.py`: WebDAV fetch should produce a local/private path that this parser can consume instead of creating a separate parser.
- `build_highlight_import_preview` in `src/multilang/services/highlight_import_preview.py`: remote preview/list/fetch flows should reuse count-only preview semantics where possible.
- `HighlightImportRepository` in `src/multilang/repositories/highlight_import_repository.py`: continue the private-record versus safe-manifest split for WebDAV imports.

### Established Patterns
- CLI commands are Typer-based and testable via `create_app`; outputs are stable `key=value` lines rather than rich interactive UI.
- Public CLI source naming uses `highlights` while the internal source profile remains `kindle-highlights`.
- Highlight imports already use content hashes and safe manifest counts for idempotency; WebDAV should extend this instead of inventing sequence-only identity.
- Privacy-safe behavior is an explicit boundary from earlier phases: source paths, raw highlight text, book metadata, credentials, and unsupported raw input should not leak.

### Integration Points
- Add WebDAV settings in `Settings` and test env alias behavior near existing settings tests.
- Add CLI listing/fetch commands near `preview-kindle-highlights` and `generate` so fetched files can be previewed/generated through the same local path.
- Add a WebDAV fetch adapter/service that returns a private cached path plus safe metadata/counts for CLI reporting.
- Extend highlight ingestion/preview tests with synthetic WebDAV fixtures and fake client responses; do not require real WebDAV credentials or network access.

</code_context>

<specifics>
## Specific Ideas

- The user chose env-only secrets and no CLI secret overrides because the project treats WebDAV credentials and reading data as sensitive.
- Listing should help the user identify the intended export without exposing full remote paths or private book metadata.
- A private local cache is acceptable and preferred, provided it stays under ignored `.multilang` storage and public manifests remain hash/count-only.
- Success summaries should prove idempotency with safe counts and hash identity rather than private names or raw content.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within Phase 14 scope.

</deferred>

---

*Phase: 14-webdav-highlight-fetch-adapter*
*Context gathered: 2026-05-06*
