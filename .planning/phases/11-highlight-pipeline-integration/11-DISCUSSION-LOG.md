# Phase 11: Highlight Pipeline Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `11-CONTEXT.md` - this log preserves the alternatives considered.

**Date:** 2026-05-05
**Phase:** 11-highlight-pipeline-integration
**Areas discussed:** CLI mode shape, Duplicate identity, Import summary, Grounding/provenance

---

## CLI Mode Shape

| Option | Description | Selected |
|--------|-------------|----------|
| `highlights` | Generic public deck mode; KOReader/Kindle remains importer/parser detail. | yes |
| `kindle-highlights` | Exposes existing internal source key directly. | |
| `koreader-highlights` | Most specific to the user's setup, but narrower than the roadmap mode. | |
| both aliases | Accept multiple public source values. | |

**User's choice:** Use public `generate --source highlights`.
**Notes:** User clarified: "lembre-se que estou usando o koreader no kindle". Follow-up confirmed `highlights` as the public mode. Reuse `--input-file`, keep `preview-kindle-highlights`, and persist internal audit/source-profile records as `kindle-highlights`.

---

## Duplicate Identity

| Option | Description | Selected |
|--------|-------------|----------|
| same normalized content | Same highlight text after normalization means same import, independent of file path/name. | yes |
| same file plus content | File identity and content must both match. | |
| same candidate list only | Candidate vocabulary alone defines identity. | |

| Option | Description | Selected |
|--------|-------------|----------|
| recognize as old card | Same word plus same source content remains the same card even if KOReader changes export order. | yes |
| create another card | Changed export order can create a new card. | |
| same word only | Same lemma is globally the same card regardless of source context. | |

| Option | Description | Selected |
|--------|-------------|----------|
| skip same source content | Skip duplicate source content/candidate while allowing same word from genuinely different context. | yes |
| skip same lemma globally | Never create a second highlight card for the same language+lemma. | |
| per import only | Only repeated runs of the same import skip duplicates. | |

| Option | Description | Selected |
|--------|-------------|----------|
| hashes and counts only | Manifest contains import hash, content hashes, candidate keys, and counts with no raw text. | yes |
| include safe snippets | Add redacted snippets for debugging. | |
| DB only, no file | Persist manifest-like data only in DB. | |

**User's choice:** Same normalized content/import should be recognized across reruns and reorder changes; safe manifests contain hashes/counts only.
**Notes:** User needed an example for reorder behavior and chose to recognize the card as old when the same source content appears in a different position.

---

## Import Summary

| Option | Description | Selected |
|--------|-------------|----------|
| key=value counts | Stable parseable CLI counters consistent with existing output. | yes |
| human paragraphs | More readable prose. | |
| both counts and text | Counts plus explanatory prose. | |

| Option | Description | Selected |
|--------|-------------|----------|
| counts only | Privacy safest default. | yes |
| safe word list | Show candidate words/headwords without snippets/paths. | |
| manifest path only | Print counts plus safe manifest path for details. | |

| Option | Description | Selected |
|--------|-------------|----------|
| continue with usable | Process usable candidates and report blocked counts/reasons. | yes |
| stop whole import | Fail if any candidate is blocked. | |
| ask user | Prompt interactively before continuing. | |

| Option | Description | Selected |
|--------|-------------|----------|
| full lifecycle counts | Include imported, rejected, extracted, duplicate, reused, new, blocked, and planned counts. | yes |
| Phase 10 counts only | Keep only parser/extraction/preview counts. | |
| minimal new counts | Only show reused/skipped/new/blocked counts. | |

**User's choice:** Count-only `key=value` summary with full lifecycle counters, continuing with usable candidates when some are blocked.
**Notes:** No candidate words, snippets, paths, or book metadata should print by default.

---

## Grounding/Provenance

| Option | Description | Selected |
|--------|-------------|----------|
| block that candidate | Keep blocked candidate visible in counts/reasons; no replacement/backfill. | yes |
| skip silently | Drop ungrounded candidates without visible item-level reason. | |
| fail whole import | Stop the entire run on any ungrounded candidate. | |

| Option | Description | Selected |
|--------|-------------|----------|
| through grounding only | Phase 11 creates/resumes job and persists grounded/planned candidates; Phase 12 handles text/audio/QA. | yes |
| through existing text/audio | Run current downstream generation/audio immediately. | |
| preview/plan only | No persisted job work yet. | |

| Option | Description | Selected |
|--------|-------------|----------|
| store privately in DB | Keep normalized text internally for Phase 12 context/audit but never print/commit/log it. | yes |
| store hashes only | Maximum privacy but no source context for Phase 12. | |
| store redacted snippets | Store partial context only. | |

| Option | Description | Selected |
|--------|-------------|----------|
| hash/index/count only | Candidate rows keep source content hash, first index/highlight id, occurrence count, and manifest identity. | yes |
| include location labels | Also preserve KOReader location/chapter labels. | |
| minimal candidate key only | Preserve only the candidate identity. | |

**User's choice:** Block ungrounded candidates, run Phase 11 through grounding only, store normalized highlight text privately in DB for Phase 12, and keep candidate-level provenance to hash/index/count/import identity only.
**Notes:** Raw highlight text may exist in private internal storage, but not in summaries, manifests, candidate rows, logs, reports, or committed artifacts.

---

## the agent's Discretion

- Exact schema/table names.
- Exact service/repository names.
- Exact counter names.
- Exact stable candidate-key algorithm, as long as it satisfies same-content and reorder-safe duplicate behavior.

## Deferred Ideas

- WebDAV fetching and sync summaries - Phase 14.
- Highlight generation/audio/QA - Phase 12.
- Highlight export/template - Phase 13.
- Interactive candidate review UI - future requirement.
