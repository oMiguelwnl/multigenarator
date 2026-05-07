# Phase 14 — WebDAV Highlight Fetch Adapter Research

**Phase:** 14 — WebDAV Highlight Fetch Adapter  
**Requirements:** INGEST-01, INGEST-02  
**Status:** Complete  
**Scope:** Secure WebDAV configuration, remote listing, explicit remote fetch, local Kindle parser handoff, distinct redacted failures, idempotent summaries.

## Executive Recommendation

Use a small in-repo WebDAV adapter built on Python standard-library HTTP primitives with an injectable transport for tests. Do **not** add a WebDAV dependency for this phase: the required behavior is limited to `PROPFIND` depth-1 listing and `GET` fetch, and the security requirements are easier to enforce at a narrow adapter boundary.

## Existing Contracts to Reuse

- `src/multilang/settings.py` already uses `pydantic-settings` with `MULTILANG_` env prefix. Add WebDAV URL, username, secret, timeout, and cache directory there.
- `src/multilang/cli.py` uses Typer commands and stable `key=value` output lines. Add WebDAV list/fetch commands near `preview-kindle-highlights` and `generate`.
- `src/multilang/services/kindle_highlight_parser.py` accepts local `.html`, `.htm`, and `.txt` paths. WebDAV fetch should write a private cached local file and pass that path into this parser.
- `src/multilang/services/highlight_import_preview.py` already combines parser and candidate extraction for count-only previews.
- `src/multilang/services/ingest_lexical_items.py` already computes content hashes, candidate keys, duplicate/reuse counts, and safe highlight import manifests.
- `src/multilang/security/redaction.py` already redacts credentials, WebDAV URLs, `.multilang` raw/cache paths, book metadata, and caller-supplied private text.

## WebDAV Implementation Notes

### Listing

- Use `PROPFIND` against the configured base URL with `Depth: 1`.
- Parse XML with `xml.etree.ElementTree` and extract `href`, `getcontentlength`, and `getlastmodified` where present.
- Filter candidates to `.html`, `.htm`, and `.txt` because the local parser supports only those formats.
- Return safe display names derived from the basename and redacted/sanitized metadata; never print the configured full URL, credentials, raw href, or private book metadata.

### Fetching

- Require an explicit remote path argument; do not auto-select the newest item.
- Resolve the explicit remote path against the configured base URL without allowing credentials to enter output.
- Save successful bytes into an ignored private cache under `.multilang/highlights/cache/` using a content-hash-based filename plus the original supported suffix.
- Only write the cache file after the response status and body are validated. Malformed responses or empty sources fail closed with no cache file.
- After caching, run the same local parser/preview/generation path used by `--input-file` local imports.

### Failure Taxonomy

Use distinct exception/error codes and redacted CLI messages for:

| Failure | Trigger | Safe output |
|---------|---------|-------------|
| `missing_config` | URL, username, or secret missing | `webdav_error=missing_config` |
| `auth` | 401/403 | `webdav_error=auth` |
| `path_not_found` | 404 or missing selected href | `webdav_error=path_not_found` |
| `network` | timeout, connection, TLS, DNS, or non-mapped 5xx | `webdav_error=network` |
| `malformed_response` | unparsable PROPFIND XML or invalid response shape | `webdav_error=malformed_response` |
| `unsupported_format` | explicit path suffix is not `.html`, `.htm`, or `.txt` | `webdav_error=unsupported_format` |
| `empty_source` | fetched body is empty/whitespace | `webdav_error=empty_source` |

## Validation Architecture

- Unit-test settings aliases with `Settings(_env_file=None)` and monkeypatched `MULTILANG_WEBDAV_*` variables.
- Unit-test the WebDAV adapter using an injected fake transport; no live network, no real credentials.
- CLI-test list/fetch/generate WebDAV flows with fake service injection or monkeypatches through `create_app`-friendly seams.
- Integration-test the fetched-cache-to-local-parser path with synthetic Kindle exports and assert count lines match existing highlight preview/generation semantics.
- Privacy-test every failure path for absence of raw username, secret, configured full URL, raw remote path, raw response body, and private highlight text.

## Source Audit

SOURCE | ID | Feature/Requirement | Plan | Status | Notes
------ | -- | ------------------- | ---- | ------ | -----
GOAL | — | Fetch Kindle highlight exports from configured WebDAV without leaking secrets or masking failures | 01-04 | COVERED | Settings, adapter, CLI, generate handoff, failures, idempotency
REQ | INGEST-01 | Configure WebDAV URL, username, and secret without source edits or credential exposure | 01,03 | COVERED | Settings plus CLI redaction
REQ | INGEST-02 | Fetch from WebDAV with listing, selection, and distinct auth/path/network/empty failures | 02-04 | COVERED | Adapter, CLI, generate handoff, evidence
RESEARCH | — | Use stdlib/injectable WebDAV adapter with no new dependency | 02 | COVERED | Narrow PROPFIND/GET scope
RESEARCH | — | Cache fetched bytes only under ignored `.multilang/highlights/cache/` | 02 | COVERED | Content-hash cache filenames
RESEARCH | — | Validate malformed responses fail closed without cache/manifest writes | 02,04 | COVERED | Adapter tests and evidence
CONTEXT | D-01 | WebDAV URL via typed Settings and `MULTILANG_*` env | 01 | COVERED | `webdav_url`
CONTEXT | D-02 | Username and secret env-only | 01,03 | COVERED | No CLI secret flags
CONTEXT | D-03 | No per-run CLI secret overrides | 03,04 | COVERED | CLI accepts only non-secret selection args
CONTEXT | D-04 | Missing config fails before network request | 01,02 | COVERED | Service validation
CONTEXT | D-05 | Explicit remote path/selected candidate required | 03,04 | COVERED | No auto latest behavior
CONTEXT | D-06 | Listing prints sanitized names/metadata only | 02,03 | COVERED | Safe candidate DTOs and CLI output
CONTEXT | D-07 | Candidate filtering limited to `.html`, `.htm`, `.txt` | 02 | COVERED | Adapter filter
CONTEXT | D-08 | Listing and fetching are separate CLI commands/subcommands | 03 | COVERED | Separate commands
CONTEXT | D-09 | Fetched exports saved under ignored `.multilang` cache | 02 | COVERED | `webdav_cache_dir`
CONTEXT | D-10 | Safe manifests persist only hashes/keys/counts | 04 | COVERED | Existing ingestion path retained
CONTEXT | D-11 | Idempotency is content-hash based | 02,04 | COVERED | Cache and existing import identity
CONTEXT | D-12 | WebDAV content feeds same local parser/preview/generation path | 03,04 | COVERED | Cached path passed into existing services
CONTEXT | D-13 | Distinct safe failure types | 02,03 | COVERED | Failure taxonomy
CONTEXT | D-14 | Malformed WebDAV responses fail closed | 02 | COVERED | No cache writes on malformed
CONTEXT | D-15 | Successful summaries print safe counts/hash identity | 03,04 | COVERED | CLI key=value summaries
CONTEXT | D-16 | No raw credentials/URLs/paths/body/highlight text in outputs/artifacts | 02-04 | COVERED | Redaction tests
