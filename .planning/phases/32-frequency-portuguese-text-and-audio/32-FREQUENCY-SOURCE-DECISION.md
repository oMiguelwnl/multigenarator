# Phase 32 Korean Frequency Source Decision

## Status

`selected_pending_exact_artifact_review`

The user selected the National Institute of Korean Language (NIKL) learner-vocabulary list as the Phase 32 rank and initial lexical-authority path on 2026-08-21. This record authorizes planning against that source. It does not authorize production download, transformation, asset creation, repository commit, generation, publication, or a legal conclusion beyond the cited official statements.

## Selected Source

| Field | Value |
|---|---|
| Publisher | National Institute of Korean Language (NIKL) |
| Official page | `https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=70` |
| Source title | `한국어 학습용 어휘 목록` |
| Primary named attachment | `한국어 학습용 어휘 목록.txt` |
| Published | 2003-06-04 |
| Page last revised | 2019-05-30 |
| Source population | 5,965 entries |
| Source levels | A: 982; B: 2,111; C: 2,872 |
| Frequency authority | Rank from NIKL's 2002 `현대 국어 사용 빈도 조사` |
| Lexical fields described by NIKL | word, dictionary-based homonym identity, POS abbreviation, short gloss/original/example, final grade |
| License statement on source page | May be used after specifically indicating the source under KOGL Type 1 conditions |
| Project disposition | Selected candidate; exact bytes and redistribution evidence not yet approved |

NIKL states that the same list is offered in text, Excel, and HWP formats. The text attachment is primary because it can be parsed with bounded standard-library decoding and explicit schema validation; Phase 32 must not add a legacy `.xls` parser for equivalent content. The Excel page (`etc_seq=71`) may be recorded only as an official cross-check and never as a second authority.

The approved execution policy distinguishes local use from redistribution. A qualified rights decision may authorize transformation and local-deck use from private/ignored storage while denying commit/publication of source-derived data. Missing or uncertain local-use rights block provider and production work; any committed or published derived asset still requires a separate exact-byte redistribution approval.

## Why This Source

- It is an official Korean government publication with learner-vocabulary curation rather than an opaque provider-generated list.
- It supplies rank, POS, homonym identity, gloss, and level evidence useful for the project's lemma/POS/sense contract.
- Its source page explicitly identifies KOGL Type 1 and a source-attribution condition.
- Its 5,965 rows provide a bounded replacement pool for an exact 3,000-entry final inventory.
- It avoids treating `wordfreq`, provider output, a subtitle list with noncommercial/no-derivatives terms, or an unconfirmed corpus derivative as repository authority.

The tradeoff is age: frequency ranks derive from a 2002 survey. Modernity must therefore be reviewed explicitly; the source cannot be described as a current 2026 usage measurement.

## Locked Transformation Policy

1. Preserve the original NIKL source rank, POS, homonym marker, gloss, and grade as immutable source evidence.
2. Use one dominant source-backed sense per ranked source item unless the source supplies independent sense-specific ranks.
3. Resolve each accepted row to the verified Phase 30 NFC lemma/POS/sense identity and exact Kiwi fingerprint before text generation.
4. Reject standalone particles/endings, inflection duplicates, script noise, unsupported proper names, obsolete/sensitive rows, malformed identities, and unresolved homographs with controlled reasons.
5. Backfill only from the same exact frozen 5,965-entry NIKL pool in source-rank order. Do not use live `wordfreq`, a provider, or an unapproved secondary corpus to fill gaps.
6. Assign contiguous project final ranks only after curation while retaining original NIKL ranks separately.
7. Freeze exactly 3,000 unique lemma/POS/sense identities into manifest-assigned Level 1, Level 2, and Level 3 sets of 1,000 each.
8. Record every accepted and rejected source row in numerator/denominator reports; no source row disappears silently.

## Required Evidence Before Ingestion

- Exact attachment URL after redirects, filename, byte size, raw SHA-256, retrieval timestamp, and publisher identity.
- Captured KOGL Type 1 terms/version or equivalent official terms evidence tied to the retrieval date.
- Approved attribution text naming NIKL, source title, publication date, official page, and project modifications.
- Explicit decisions for intended use, transformed-data distribution, public Git history, commercial downstream use, and change notices.
- Confirmation that the specifically KOGL-marked attachment, not a differently licensed NIKL/Sejong/Modu resource, is the only source opened by this path.
- A content and schema inspection showing the attachment actually contains the fields/counts represented on the official page.

Failure of any item above blocks before a source stream is processed or `assets/frequency/ko/` is created.

## Required Evidence Before Asset Commit

- A strict root manifest binding the source decision, exact source bytes, attribution, terms evidence, transformed inventory, rejection ledger, curation report, analyzer fingerprint, per-level hashes, and complete bundle hash.
- Exactly 3,000 accepted rows and 1,000 rows per level, with contiguous final ranks and no cross-level lexical-identity duplicates.
- Complete rejection/backfill accounting and a qualified modernity/content review.
- Explicit user authorization to commit the exact bundle after reviewing its hashes and license/attribution disposition.

Permission to use the source locally does not imply permission to commit it. If exact terms permit local transformation but not repository redistribution, the same strict bundle contract must use a configured private root and the repository asset path must remain absent.

## Alternatives Not Selected

| Alternative | Disposition |
|---|---|
| Leipzig rank + NIKL identity | Not selected; newer rank but requires package-specific written confirmation for the exact derivative/public/commercial use. |
| Korean Wikipedia rank + NIKL identity | Not selected; reproducible but requires a separately managed CC BY-SA data-asset and has encyclopedic/proper-name bias. |
| `wordfreq` Korean list | Rejected as final authority; its own documentation says not to convert the data to CSV, and its Korean output lacks project sense identity. |
| SUBTLEX-KR | Rejected without a separate grant; availability and CC BY-NC-ND constraints do not support the intended transformed public asset. |

## Claim Limit

This decision identifies the source path and curation policy only. It does not prove that the attachment's exact bytes have been reviewed, that the transformed 3,000-entry bundle is redistributable, that the vocabulary is current, or that any Korean card is learner-ready.
