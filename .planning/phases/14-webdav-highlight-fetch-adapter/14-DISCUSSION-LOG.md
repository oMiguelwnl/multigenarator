# Phase 14: WebDAV Highlight Fetch Adapter - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-06
**Phase:** 14-WebDAV Highlight Fetch Adapter
**Areas discussed:** Config and secrets, Remote selection, Fetched file handling, Failure and summary output

---

## Config and Secrets

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| How should a user provide the WebDAV URL? | Settings env var | Add `MULTILANG_WEBDAV_URL`; matches existing `Settings` env/.env pattern and avoids source edits. | yes |
| How should a user provide the WebDAV URL? | CLI option only | Use a `--webdav-url` option per command. More explicit per run, but easier to leak through shell history/logs. | |
| How should a user provide the WebDAV URL? | Both env and CLI | Allow env default plus CLI override. Flexible, but more precedence rules to document and test. | |
| How should username and secret be provided? | Env secrets only | Add `MULTILANG_WEBDAV_USERNAME` and `MULTILANG_WEBDAV_SECRET`; minimizes accidental terminal/history exposure. | yes |
| How should username and secret be provided? | Prompt at runtime | Ask interactively for missing secret. Safer than CLI flags, but awkward for automation and tests. | |
| How should username and secret be provided? | CLI flags allowed | Permit `--webdav-username` and `--webdav-secret`. Convenient but has the highest leakage risk. | |
| Should CLI commands allow per-run WebDAV overrides? | No secret override | Only non-secret options may be CLI flags; secrets stay in Settings. | yes |
| Should CLI commands allow per-run WebDAV overrides? | URL override only | Allow `--webdav-url`, but keep username/secret env-only. | |
| Should CLI commands allow per-run WebDAV overrides? | All overrides | Allow URL, username, and secret flags. Maximum flexibility with extra redaction burden. | |
| Should CLI commands allow per-run WebDAV overrides? | You decide | Let downstream agents choose the smallest safe interface that satisfies INGEST-01. | |
| What should happen when required WebDAV config is missing? | Fail before network | Stop with a clear redacted config error before trying any request. | yes |
| What should happen when required WebDAV config is missing? | Prompt for missing | Ask interactively for missing values. Friendly locally, poor for CI/batch workflows. | |
| What should happen when required WebDAV config is missing? | Skip WebDAV | Fall back to local `--input-file` behavior. Less disruptive, but can mask misconfiguration. | |

**User's choices:** Settings env var; Env secrets only; No secret override; Fail before network.
**Notes:** Preserve the existing `Settings` env/.env pattern and privacy boundary.

---

## Remote Selection

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| How should the WebDAV command choose which export to fetch? | Explicit path required | User passes or configures a remote file path; listing can show candidates but fetch is deterministic and non-interactive. | yes |
| How should the WebDAV command choose which export to fetch? | Pick latest export | Automatically fetch the newest plausible Kindle export. Convenient, but depends on remote timestamps/naming. | |
| How should the WebDAV command choose which export to fetch? | Interactive choose | List remote files and prompt the user to choose. Friendly locally, harder for automation. | |
| What should remote listing include? | Safe names only | Show redacted/sanitized file names plus size/date when available; do not print full URLs or credentials. | yes |
| What should remote listing include? | Full remote paths | Useful for debugging nested directories, but paths can reveal private book/export structure. | |
| What should remote listing include? | Counts only | Most private, but not enough to let the user select a specific file. | |
| Which files should be considered Kindle highlight exports? | HTML and TXT | Match the existing local parser support for `.html`, `.htm`, and `.txt` only. | yes |
| Which files should be considered Kindle highlight exports? | Any remote file | Fetch anything and let the parser reject unsupported formats. Simpler, but noisier and less helpful. | |
| Which files should be considered Kindle highlight exports? | Name pattern plus type | Require both extension and Kindle-ish name. More precise, but may reject valid user exports. | |
| Should listing and fetching be separate commands or one command mode? | Separate commands | `list` gives safe candidates; `fetch` retrieves an explicit candidate. Easier to test and automate. | yes |
| Should listing and fetching be separate commands or one command mode? | One fetch command | A single command lists and fetches. Fewer commands, but selection behavior gets more complex. | |
| Should listing and fetching be separate commands or one command mode? | You decide | Let downstream agents choose the smallest CLI shape that satisfies list, select, and fetch. | |

**User's choices:** Explicit path required; Safe names only; HTML and TXT; Separate commands.
**Notes:** Listing is for safe discovery; fetching remains explicit and deterministic.

---

## Fetched File Handling

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| After fetching a remote export, should Multilang keep a local raw copy? | Private cache file | Save under an ignored `.multilang` private path for reproducible local parsing and reruns, never commit it. | yes |
| After fetching a remote export, should Multilang keep a local raw copy? | Temp file only | Parse via temporary file and delete after import. Best privacy, weaker debugging/retry evidence. | |
| After fetching a remote export, should Multilang keep a local raw copy? | Memory only | Avoid filesystem persistence, but existing parser is path-based so implementation becomes larger. | |
| What should be persisted in safe manifests after a WebDAV fetch? | Hashes and counts | Reuse existing safe manifest pattern: content hash, candidate keys, and import counts only. | yes |
| What should be persisted in safe manifests after a WebDAV fetch? | Add safe filename | Also persist sanitized remote basename for human traceability. Slight privacy risk if names include book metadata. | |
| What should be persisted in safe manifests after a WebDAV fetch? | Add remote metadata | Persist sanitized size/date/etag. Better auditability, more redaction and schema decisions. | |
| How should duplicate remote content be handled? | Hash-based reuse | If fetched content hash is unchanged, reuse existing import/candidate identity and print unchanged/reused counts. | yes |
| How should duplicate remote content be handled? | Always reimport | Simpler semantics, but undermines idempotent summaries and can create unnecessary work. | |
| How should duplicate remote content be handled? | Ask before reuse | Gives control, but adds interactivity where existing generation prefers deterministic summaries. | |
| Should fetched files feed the exact same local parser path as local imports? | Same parser path | WebDAV fetch should produce a local/private path and call the existing Kindle parser/preview/generation path. | yes |
| Should fetched files feed the exact same local parser path as local imports? | Separate parser | Create WebDAV-specific parsing logic. More room for drift and duplicate behavior. | |
| Should fetched files feed the exact same local parser path as local imports? | You decide | Let downstream agents choose as long as local and WebDAV normalization stay equivalent. | |

**User's choices:** Private cache file; Hashes and counts; Hash-based reuse; Same parser path.
**Notes:** Private local cache is acceptable as long as public manifests and artifacts remain hash/count-only.

---

## Failure and Summary Output

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| How detailed should WebDAV failure messages be? | Typed safe detail | Distinct codes/messages for auth, path, network, malformed response, empty source, with all sensitive values redacted. | yes |
| How detailed should WebDAV failure messages be? | Minimal codes only | Safest and easy to test, but less helpful when fixing WebDAV setup. | |
| How detailed should WebDAV failure messages be? | Verbose debug mode | Default safe messages plus optional verbose diagnostics. Useful, but must be carefully redacted. | |
| What should a successful fetch summary print? | Counts and hashes | Print safe file count/fetched bytes or content hash prefix, imported/rejected/extracted/duplicate/planned/reused/new counts. | yes |
| What should a successful fetch summary print? | Counts only | Maximum privacy and consistent with existing preview output, but less useful for proving unchanged content. | |
| What should a successful fetch summary print? | Include safe filename | More human-friendly, but remote basenames can contain private book metadata. | |
| How should malformed WebDAV responses be surfaced? | Fail closed | Do not guess; emit `malformed_response` and do not write cache/import records. | yes |
| How should malformed WebDAV responses be surfaced? | Retry then fail | Retry transient malformed responses before failing. More resilient, but more moving parts. | |
| How should malformed WebDAV responses be surfaced? | Best-effort parse | Try to extract files from partial responses. Risky and can mask provider issues. | |
| Should failures ever include remote URLs, paths, or raw response bodies? | Never raw sensitive | Redact URLs, credentials, book metadata, raw response bodies, and raw highlight text in all logs/errors/artifacts. | yes |
| Should failures ever include remote URLs, paths, or raw response bodies? | Debug flag may show | Allow raw details behind a debug flag. Useful locally, but conflicts with current privacy boundary. | |
| Should failures ever include remote URLs, paths, or raw response bodies? | You decide | Let downstream agents enforce privacy using existing redaction helpers. | |

**User's choices:** Typed safe detail; Counts and hashes; Fail closed; Never raw sensitive.
**Notes:** Diagnostics should be useful but always redacted and fail closed.

---

## the agent's Discretion

- Exact command names, option names, class names, and fixture shapes are left to downstream agents.

## Deferred Ideas

None.
