---
phase: 14-webdav-highlight-fetch-adapter
requirements: [INGEST-01, INGEST-02]
artifact_type: evidence
privacy: redacted
---

# Phase 14 WebDAV Evidence

## Commands

- `uv run pytest tests/integration/test_webdav_highlight_fetch_flow.py -q`
- `uv run pytest tests/cli/test_generate_webdav_highlights_command.py tests/integration/test_webdav_highlight_fetch_flow.py tests/services/test_highlight_ingest_lexical_items.py -q`

## Expected Pass Signals

- Synthetic WebDAV bytes are cached under `.multilang/highlights/cache/` by content hash.
- Cached content is parsed through the existing Kindle highlight parser path.
- The first ingestion reports imported, extracted, and planned counts.
- The second ingestion of unchanged content reports reused candidates and `newly_planned_candidates == 0`.
- Evidence uses `[synthetic highlight text redacted]` instead of raw highlight prose.

## Privacy Checklist

- [x] No real credentials are included.
- [x] No full private WebDAV URL is included.
- [x] No raw remote path with private metadata is included.
- [x] No raw response body is included.
- [x] No raw Kindle highlight prose is included: `[synthetic highlight text redacted]`.
