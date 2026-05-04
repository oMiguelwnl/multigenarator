---
phase: 09
slug: source-profiles-privacy-regression-boundary
status: verified
threats_open: 0
asvs_level: 1
created: 2026-05-04T12:38:37Z
updated: 2026-05-04T12:59:09Z
---

# Phase 09 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| user input -> GenerationRequest | User-provided CLI/source strings enter typed domain validation. | Source strings, local input paths |
| source profile -> downstream generation/export | Source-specific privacy/export decisions control later prompt and artifact behavior. | Source profile metadata |
| persisted rows -> export renderer | Persisted source_type decides note model and visible fields. | Card rows, source_type, media references |
| mixed source rows -> Anki package | Invalid mixed source data could create field/template collisions. | Export rows from multiple source modes |
| private local files -> logs/errors | Raw highlights and local paths may enter diagnostics. | Raw highlight text, file paths, book metadata |
| WebDAV config -> process output | Credentials and remote URLs may enter exceptions, reports, or debug output. | WebDAV URL, username, secret/token |
| working tree -> commit candidates | Local secrets/raw exports may be present during development. | .env files, raw Kindle exports, WebDAV secret files |
| test fixtures -> regression proof | Synthetic fixtures stand in for private inputs and must not include secrets. | Synthetic lexical/test data |
| future highlight work -> existing modes | New source behavior must not mutate shipped frequency/custom flows. | Source-specific fields, note models, CLI modes |

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-09-01 | Tampering | `GenerationRequest.source_type` | mitigate | `GenerationRequest` uses shared `SourceType`; supported keys live in `SOURCE_PROFILES`. Evidence: `src/multilang/domain/jobs.py`, `src/multilang/domain/source_profiles.py`. | closed |
| T-09-02 | Information Disclosure | `get_source_profile` errors | mitigate | Unsupported source errors include only safe source-type keys and never file contents, raw highlights, paths, or credentials. Evidence: `src/multilang/domain/source_profiles.py`, `tests/domain/test_source_profiles.py`. | closed |
| T-09-03 | Elevation of Privilege | highlight profile defaults | mitigate | `kindle-highlights` is internal-only in Phase 09; CLI remains gated to `frequency` and `word-list`. Evidence: `src/multilang/cli.py`, `tests/integration/test_v12_existing_mode_regression_boundary.py`. | closed |
| T-09-04 | Tampering | `export_anki_package()` | mitigate | Mixed source rows are rejected before package/model creation. Evidence: `src/multilang/services/export_anki_package.py`, `tests/services/test_export_anki_package.py`. | closed |
| T-09-05 | Information Disclosure | highlight field mapping | mitigate | Highlight field names omit `Translation` and use explicit aliases instead of fallback. Evidence: `src/multilang/domain/exporting.py`, `tests/domain/test_exporting.py`. | closed |
| T-09-06 | Repudiation | note type selection | mitigate | Note model and tabular note type selection resolve through exact source profiles. Evidence: `src/multilang/services/export_anki_package.py`, `src/multilang/runtime.py`. | closed |
| T-09-07 | Information Disclosure | `redact_sensitive_text` | mitigate | Redaction helpers cover credentials, URLs, private terms, metadata, nested mappings, and exceptions. Evidence: `src/multilang/security/redaction.py`, `tests/security/test_redaction.py`. | closed |
| T-09-08 | Information Disclosure | `.gitignore` | mitigate | `.gitignore` excludes local secrets, raw highlight caches, Kindle exports, and WebDAV secret files. Evidence: `.gitignore`, `tests/security/test_redaction.py`. | closed |
| T-09-09 | Repudiation | redacted diagnostics | accept | Accepted by plan: redaction intentionally reduces raw forensic detail while preserving labels/structure. | accepted |
| T-09-10 | Tampering | regression suite | mitigate | Regression suite asserts exact field constants/note types and CLI source gating for shipped modes. Evidence: `tests/integration/test_v12_existing_mode_regression_boundary.py`. | closed |
| T-09-11 | Information Disclosure | test fixtures/evidence | mitigate | Evidence and fixtures use synthetic data; no real WebDAV/highlight data is stored. Evidence: `09-REGRESSION-EVIDENCE.md`, integration fixtures. | closed |
| T-09-12 | Denial of Service | regression command size | accept | Accepted by plan: focused commands are bounded/fake-provider based; broad drift detection is collect-only. | accepted |

Status: open or closed. Disposition: mitigate, accept, or transfer.

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-09-01 | T-09-09 | Privacy-preserving redaction intentionally reduces raw forensic detail; labels and structure are preserved enough for diagnosis without private content. | Phase 09 threat model | 2026-05-04 |
| AR-09-02 | T-09-12 | Focused evidence commands are bounded and fake-provider based; broad suite drift is checked with collect-only to avoid unnecessary runtime. | Phase 09 threat model | 2026-05-04 |

## Unregistered Flags

| Flag | File | Mapping | Disposition |
|------|------|---------|-------------|
| `threat_flag: test-fixture-boundary` | `tests/integration/test_v12_existing_mode_regression_boundary.py` | T-09-11 | Informational; synthetic fixture boundary supports the listed mitigation. |

## Open Threats

No open threats remain after T-09-02 remediation.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-05-04 | 12 | 11 | 1 | gsd-security-auditor |
| 2026-05-04 | 12 | 11 | 1 | gsd-security-auditor recheck |
| 2026-05-04 | 12 | 12 | 0 | gsd-gap-closure |

Notes:
- `gsd-sdk` was unavailable on PATH; security enforcement used the workflow default `true`.
- Auditor result: `OPEN_THREATS`, `threats_open: 1`.
- User chose to block the gate rather than accept T-09-02.
- Recheck result at 2026-05-04T12:53:41Z: `OPEN_THREATS`; `src/multilang/domain/source_profiles.py` still reflects raw unknown `source_type`, and `tests/domain/test_source_profiles.py` still asserts a private/path-bearing value appears in the error.
- Gap-closure result at 2026-05-04T12:59:09Z: `VERIFIED`; `get_source_profile()` omits the unsafe unknown source value, and `tests/domain/test_source_profiles.py` asserts private/path-bearing values are absent from unsupported source errors.

## Recommendations

- Keep future highlight/WebDAV diagnostics on the same safe-output boundary: omit or redact private source values before they reach errors, logs, prompts, reports, or artifacts.

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified after T-09-02 remediation
