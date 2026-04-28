---
phase: 05-anki-safe-export-contract
verified: 2026-04-28T12:53:37Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
---

# Phase 5: Anki-Safe Export Contract Verification Report

**Phase Goal:** Users receive complete cards in a fixed schema with the expected template behavior and can export them into Anki safely.
**Verified:** 2026-04-28T12:53:37Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User receives every generated card in the fixed schema with the requested fields in a consistent order and format. | ✓ VERIFIED | `EXPORT_CARD_FIELD_NAMES` in `src/multilang/domain/exporting.py` defines the exact ten CARD-01 fields in order; `ExportCardRow.ordered_field_mapping()` emits only that order; tests assert exact aliases and order. |
| 2 | User receives `Image` as an empty field on every exported card, and `Translation` stays hidden on the front and is revealed on the back according to the provided template. | ✓ VERIFIED | `ExportCardRow` defaults `image` to `""` and rejects non-empty image values; `CARD_TEMPLATE.md` hides `Translation` in the front template with `style="display:none;"` and reveals it on the back via `{{FrontSide}}` plus script; `05-05-SUMMARY.md` records user approval in Anki Desktop. |
| 3 | User receives `Definitions` as one template-compatible field value, with multiple senses rendered inside the same field using `<br>` separators instead of nested list markup. | ✓ VERIFIED | `AssembleExportCardsService._render_definitions()` strips `<ul>/<li>`, escapes text, and joins parts with `<br>`; tests cover `<br>` normalization and absence of list markup. |
| 4 | User can export an `.apkg` deck that imports into Anki without manual field remapping. | ✓ VERIFIED | `export_anki_package()` builds a real `genanki.Package` with fixed fields and stable model/deck IDs; `multilang export --format apkg` is wired through runtime/CLI; `05-05-SUMMARY.md` records explicit human approval that import required no field remapping. |
| 5 | User can export the same cards as a UTF-8-safe CSV or TSV fallback. | ✓ VERIFIED | `write_export_tabular_bundle()` uses Python `csv`, writes UTF-8, emits Anki import headers and `#columns:` in fixed field order; integration tests export `.csv` and `.tsv` from real SQLite job data. |
| 6 | User receives packaged audio media and Anki-compatible sound references that play correctly after import. | ✓ VERIFIED | Assembly emits basename-only `[sound:...]` fields; runtime validates media references for all formats before writing; `.apkg` exporter requires matching existing media files; `05-05-SUMMARY.md` records user approval that word and sentence audio played after import. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/multilang/domain/exporting.py` | Frozen export-card contract, fixed field order, stable note GUID, blank Image rule | ✓ VERIFIED | 117 lines; contains exact field tuple, Pydantic aliases, deterministic GUID helper, `Image` blank validator, and SortIndex identity consistency check. |
| `src/multilang/repositories/export_repository.py` | Job-scoped snapshot/artifact persistence | ✓ VERIFIED | 151 lines; maps `CardExportModel`/`DeckExportModel`, upserts by job/item and job/format, returns snapshots ordered by `sort_index`, then `item_key`. |
| `src/multilang/db/models.py` | Export snapshot and manifest ORM tables | ✓ VERIFIED | Contains `CardExportModel` and `DeckExportModel` with fixed field columns, unique constraints, relationships, and indexes. |
| `alembic/versions/20260426_05_export_contract_tables.py` | Schema migration for `card_exports` and `deck_exports` | ✓ VERIFIED | Disposable SQLite upgrade to head succeeded and created Phase 5 export tables. |
| `src/multilang/services/assemble_export_cards.py` | Assembly from lexical/text/audio persistence into fixed rows | ✓ VERIFIED | Reads accepted text, lexical candidates, and synthesized audio; fails fast on missing prerequisites; persists snapshots through `ExportRepository`. |
| `src/multilang/services/export_tabular_bundle.py` | CSV/TSV UTF-8 fallback serialization | ✓ VERIFIED | Uses stdlib `csv`, Anki text-import headers, fixed columns, deterministic row ordering, and UTF-8 writes. |
| `src/multilang/services/export_anki_package.py` | Genanki model/note/deck/package exporter | ✓ VERIFIED | Builds fixed-field `genanki.Model`, uses project `CARD_TEMPLATE.md`, deterministic note GUIDs, and media-file validation before package write. |
| `src/multilang/runtime.py` | Runtime export orchestration | ✓ VERIFIED | `RuntimeGenerateService.export_job()` resolves snapshots or assembles on demand, validates media index, dispatches `.apkg`/CSV/TSV writers, and records artifact manifests. |
| `src/multilang/cli.py` | Shipped `multilang export` command | ✓ VERIFIED | CLI exposes `--job-id`, `--format apkg|csv|tsv`, `--output-dir`, and `--deck-name`; prints artifact path and card count; failure exits non-zero. |
| `.planning/phases/05-anki-safe-export-contract/05-05-SUMMARY.md` | Human Anki Desktop approval | ✓ VERIFIED | Lines 101-107 record approved import without remapping, hidden/revealed Translation, playable word/sentence audio, and post-fix test results. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `ExportCardRow` | CSV/TSV exporter | `ordered_field_mapping()` and `EXPORT_CARD_FIELD_NAMES` | ✓ WIRED | Tabular writer imports `EXPORT_CARD_FIELD_NAMES`/`ExportCardRow` and writes fields in that order. |
| `ExportCardRow` | `.apkg` exporter | `_row_fields()` and deterministic `note_guid` | ✓ WIRED | Anki notes use exact field list and custom `MultilangNote.guid`. |
| `AssembleExportCardsService` | `ExportRepository` | `upsert_card_snapshot(row)` | ✓ WIRED | Assembly persists every row rather than returning ad-hoc dicts. |
| `RuntimeGenerateService.export_job()` | export services | format dispatch | ✓ WIRED | Runtime dispatches APKG to `export_anki_package()` and CSV/TSV to `write_export_tabular_bundle()`. |
| `src/multilang/cli.py` | `RuntimeGenerateService.export_job()` | `multilang export` command | ✓ WIRED | CLI resolves runtime service and calls `export_job()` with typed `ExportArtifactFormat`. |
| Generated `.apkg` artifact | Anki Desktop import flow | Manual import and review session | ✓ WIRED | `05-05-SUMMARY.md` records the human checkpoint as approved for import, template behavior, and audio playback. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `AssembleExportCardsService` | `cards` / `ExportCardRow` | `TextRepository.list_accepted_records`, `LexicalRepository.get_candidate_for_item`, `AudioRepository.get_asset` | Yes | ✓ FLOWING |
| `ExportRepository` | persisted snapshots/artifact manifests | SQLAlchemy `CardExportModel`/`DeckExportModel` rows | Yes | ✓ FLOWING |
| `RuntimeGenerateService.export_job()` | `rows`, `media_index`, `output_path` | persisted snapshots or on-demand assembly plus audio repository assets | Yes | ✓ FLOWING |
| `export_anki_package()` | `genanki.Deck` notes and media files | frozen rows and validated media index | Yes | ✓ FLOWING |
| `write_export_tabular_bundle()` | CSV/TSV rows | frozen rows sorted by stable export identity | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Phase 05 tests pass | `uv run pytest tests/domain/test_exporting.py tests/repositories/test_export_repository.py tests/services/test_assemble_export_cards.py tests/services/test_export_tabular_bundle.py tests/services/test_export_anki_package.py tests/cli/test_export_command.py tests/integration/test_export_job_flow.py -q` | `28 passed in 13.07s` | ✓ PASS |
| Phase 5 migration applies cleanly | `rm -f .tmp-phase05-verify.db && MULTILANG_DATABASE_URL=sqlite+pysqlite:///$(pwd)/.tmp-phase05-verify.db uv run alembic upgrade head && rm -f .tmp-phase05-verify.db` | Alembic upgraded through `20260426_05` without error | ✓ PASS |
| CLI exposes shipped export command | `uv run python -m multilang.cli export --help` | Help lists `--job-id`, `--format [apkg|csv|tsv]`, `--output-dir`, `--deck-name` | ✓ PASS |
| Export model uses exact fields | Python import check of `ExportCardRow.field_names()` and `build_multilang_model()` | Both returned the ten CARD-01 fields; front template has hidden translation marker | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| CARD-01 | 05-01, 05-02 | Fixed schema fields: `SortIndex`, `word`, `Front of Card`, `IPA`, `Definitions`, `Example Sentence`, `Translation`, `word_audio`, `sentence_audio`, `Image` | ✓ SATISFIED | Domain contract, tabular headers, Anki model fields, assembly tests, and integration tests all use exact ordered fields. |
| CARD-02 | 05-01, 05-02 | `Image` is empty in every generated/exported card | ✓ SATISFIED | `ExportCardRow.image` defaults to `""` and validator rejects non-empty image; assembly omits image, preserving blank default. |
| CARD-03 | 05-03, 05-05 | Translation hidden on front and revealed on back | ✓ SATISFIED | `CARD_TEMPLATE.md` and `build_multilang_model()` hide/reveal Translation; user-approved Anki Desktop checkpoint recorded in `05-05-SUMMARY.md`. |
| CARD-04 | 05-02 | Definitions as one template-compatible field with `<br>` separators, no nested list markup | ✓ SATISFIED | `_render_definitions()` normalizes list/line separators into one escaped `<br>`-joined string; tests assert no `<ul>`/`<li>`. |
| EXPT-01 | 05-01, 05-03, 05-04, 05-05 | `.apkg` export imports into Anki without manual field remapping | ✓ SATISFIED | Genanki package service, shipped CLI/runtime path, integration artifact test, and human Anki import approval. |
| EXPT-02 | 05-02, 05-04 | UTF-8-safe CSV/TSV fallback export | ✓ SATISFIED | Tabular writer emits UTF-8 CSV/TSV with Anki headers and exact field order; integration test writes both formats. |
| EXPT-03 | 05-02, 05-03, 05-04, 05-05 | Anki-compatible audio references and bundled playable media | ✓ SATISFIED | `[sound:basename.mp3]` fields, runtime media validation for all formats, package media file bundling, and human audio playback approval. |

No Phase 5 orphaned requirements were found in `.planning/REQUIREMENTS.md` beyond the seven declared IDs.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| `src/multilang/runtime.py` | 175 | `placeholder` text in local template generator | ℹ️ Info | This is an intentional review/validation trigger for flagged text behavior, not an export-path stub; it does not flow into accepted export rows unless review accepts it. |

### Human Verification Required

None. The required human checkpoint has already been completed and is recorded in `05-05-SUMMARY.md`: import without field remapping, front-side Translation hidden, back-side Translation revealed, and both word/sentence audio playable in Anki Desktop.

### Gaps Summary

No blocking gaps found. Phase 05 achieved the roadmap goal and all six success criteria. Automated checks and the recorded Anki Desktop checkpoint support closing the phase.

---

_Verified: 2026-04-28T12:53:37Z_
_Verifier: the agent (gsd-verifier)_
