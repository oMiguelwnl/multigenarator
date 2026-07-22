---
task: 027
name: adicionar-mandarim-integrado
status: human_needed
completed: 2026-07-20
subsystem: generation-export
tags: [mandarin, zh, pinyin, opencc, azure-tts, anki, apkg, csv, tsv]
requires: [modern-generation-flow, export-snapshots, genanki]
provides: [mandarin-frequency, mandarin-word-list, persisted-orthography, mandarin-anki-template]
affects: [language-registry, providers, frequency-assets, audio, persistence, exporters]
tech-stack:
  added: [pypinyin, opencc-python-reimplemented, wordfreq-jieba]
  patterns: [language-aware-field-routing, frozen-derived-fields, offline-apkg-inspection]
key-files:
  created:
    - src/multilang/services/mandarin_orthography.py
    - src/multilang/templates/mandarin_card.md
    - alembic/versions/20260720_15_mandarin_export_fields.py
    - assets/frequency/zh/curated-v1.csv
    - tests/integration/test_mandarin_modern_flow.py
    - .planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md
  modified:
    - src/multilang/domain/exporting.py
    - src/multilang/services/assemble_export_cards.py
    - src/multilang/services/generate_audio_items.py
    - src/multilang/services/export_anki_package.py
    - src/multilang/runtime.py
decisions:
  - "Use zh as the sole product identity; map provider-specific locales only at adapter boundaries."
  - "Persist all four Mandarin orthography values in the export snapshot and never recompute during export."
  - "Use one language-and-source field resolver for assembly, audio, runtime, APKG, CSV, and TSV decisions."
  - "Keep visual rendering human_needed while automated evidence proves only the static template/export contract."
---

# Quick Task 027: Integrated Mandarin Summary

Mandarin now traverses the modern frequency and word-list flows as canonical `zh`, producing validated Simplified Chinese, tonal pinyin, Traditional complements, two Azure-compatible audio assets, persisted snapshots, and a dedicated 12-field Anki model across APKG/CSV/TSV.

## Outcome

- Added `zh` to generation requests, settings, runtime labels, provider registries, text validation, grounding, and both supported source types. `zh-CN` remains a provider locale rather than a product identity.
- Added deterministic Simplified validation and pinyin/Traditional derivation with `pypinyin` and OpenCC. Kana, Latin-letter contamination, Traditional primary text, missing Han, and empty derivations fail closed.
- Generated and validated `assets/frequency/zh/curated-v1.csv` with exactly 3,000 Simplified/Han entries split into three levels of 1,000, plus an auditable rejection asset.
- Added Azure voices `zh-CN-XiaoxiaoNeural` and `zh-CN-YunxiNeural`; Google TTS uses `tl=zh-CN`; ElevenLabs keeps locale `zh-CN` but emits payload `language_code=zh` only for supported model families. DeepL uses `ZH-HANS` and Tatoeba uses `cmn`.
- Added exact Mandarin fields: `SortIndex`, `word`, `Pinyin`, `Traditional`, `Definitions`, `Example Sentence`, `Sentence Pinyin`, `Traditional Sentence`, `Translation`, `word_audio`, `sentence_audio`, `Image`.
- Added migration head `20260720_15` and nullable ORM/repository columns for all four derived orthography values. Commit/expire/reload tests prove exports reuse frozen values without recomputation.
- Made field, IPA, translation, audio, media, quality-gate, note-type, and template routing language-aware. Mandarin frequency and word-list both require word and sentence audio; other word lists retain sentence-only behavior.
- Added `Multilang::Mandarin Card` model id `1762800901`, derived from the normal Multilang card language. Translation stays hidden on the front and uses the existing fixed reveal script on the back.
- Added offline CLI/repository E2E slices for three-card frequency and two-card word-list flows, including fake Azure synthesis, persisted snapshots, APKG SQLite/media inspection, and UTF-8 CSV/TSV inspection.

## Persisted UI Proof

- Artifact: `.planning/quick/027-adicionar-mandarim-integrado/artifacts/mandarin-proof.apkg`
- Size: `66024` bytes
- SHA-256: `63712333c79acd2e42002d8c7465d45257cac99dd06df83a4764932f89a4433c`
- Privacy: local-only, low sensitivity, no user/reference-deck content, `safe_to_publish: false`.
- Automated inspection proves one `zh` note, model id/name and exact field order, blank Image, stored pinyin/Traditional values, two sound tags, and two archived audio payloads.
- `.planning/quick/027-adicionar-mandarim-integrado/UI-PROOF.md` records six static observations while its human observation slot remains `observations: []` and `result: human_needed`.

## Verification Evidence

| Check | Result |
|---|---|
| `uv lock --check` | Passed |
| Frequency asset generation with `--scan-limit 25000`, then `--check` | Passed; 3x1000 rows |
| Alembic unique head | Passed: `20260720_15` |
| Fresh disposable SQLite upgrade through head | Passed |
| Mandarin providers/orthography/E2E focused suite | `56 passed` |
| Wave 2 domain/assembly/audio suite | `65 passed` |
| Wave 2 repository/schema parity suite | `13 passed` |
| Template/APKG/tabular/Mandarin E2E suite | `62 passed` |
| Existing frequency and custom-word-list E2E regressions | `3 passed` |
| Aggregated suite excluding the named Japanese baseline file | `976 passed`, one additional occurrence of the same pre-existing Windows Fugashi path failure |
| Reference-deck identifier scan under `src/` and `scripts/` | Passed |
| Persistent APKG hash/size check | Passed |
| UI proof local JSON/contract fallback validation | Passed |
| `git diff --check` | Passed with existing Windows LF/CRLF conversion warnings only |

The exact targeted export suite also reached `186 passed` before the same pre-existing Japanese assembly test failed while initializing Fugashi. All Mandarin tests and the requested non-Mandarin E2E regressions pass.

## Gap Closure Update — 2026-07-22

- Closed the verifier blocker where `pypinyin` could return an unmapped Han fallback and the export row contract accepted it as non-empty “Pinyin”.
- `src/multilang/services/mandarin_orthography.py` now rejects unsupported input letters, Han/kana/non-Latin letters in rendered pinyin, and empty/non-pinyin derivations.
- `src/multilang/domain/exporting.py` now rejects Mandarin `ExportCardRow` instances whose `Pinyin` or `Sentence Pinyin` fields contain non-pinyin letters, protecting direct row construction and persisted/exported snapshots.
- Added regressions for U+3402 fallback, Han+cyrillic contamination, invalid snapshot persistence, and direct malformed Mandarin row construction.
- Verification evidence after the fix: `uv run pytest tests/domain/test_exporting.py tests/services/test_mandarin_orthography.py tests/services/test_mandarin_language_support.py tests/services/test_frequency_decks.py tests/services/test_assemble_export_cards.py tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py tests/integration/test_mandarin_modern_flow.py -k "not japanese" -q` passed with `132 passed, 10 deselected`.
- Additional focused evidence: `uv run pytest tests/services/test_mandarin_orthography.py tests/domain/test_exporting.py tests/services/test_assemble_export_cards.py -k "not japanese" -q` passed with `53 passed, 7 deselected`; `uv lock --check` passed; `git diff --check` passed with only existing LF/CRLF warnings.
- Status remains `human_needed` only for the manual Anki Desktop/mobile render review documented below.

## Manual Acceptance Still Required

1. Import the exact hashed APKG above into Anki Desktop at `1280x800`; inspect front and back.
2. Confirm Simplified at top, pinyin immediately below, discreet Traditional text, sentence/audio grouping, sentence pinyin/Traditional below, and Translation only after flipping.
3. Import the same APKG hash into AnkiDroid on Google Pixel 7 at `412x915` portrait and repeat front/back checks for overflow, collision, and legibility.
4. Until this review is reported, no pixel-level or real-render fidelity is claimed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking dependency] Added the Chinese tokenizer extra required by wordfreq**
- `wordfreq` imports `jieba` for `zh`; without it, real asset generation cannot run.
- Changed the dependency to `wordfreq[jieba]>=3.1,<4.0` and refreshed `uv.lock`.

**2. [Rule 1 - API mismatch] Used the installed pypinyin 0.55 signature**
- `lazy_pinyin()` in the pinned family does not accept `heteronym`; the deterministic single-reading API was used without that keyword.

**3. [Rule 2 - Mixed-batch safety] Rejected mixed-language batches explicitly**
- Domain, APKG, and runtime routing now fail closed instead of selecting a model from an arbitrary first language.

### Reduced Assurance

- `.planning/templates/roles/planner.md` and `.planning/templates/roles/executor.md` were unavailable, so their role-specific review could not run.
- The installed `gsdd-cli` no longer exposes the planned `ui-proof validate` subcommand; it printed command help instead. A deterministic local fallback parsed the fenced JSON, checked every required top-level field, required six automated observations, verified `human_needed` plus empty human observations, and rejected screenshot artifacts.
- The pre-existing Windows Fugashi dictionary-path defect also appears through `test_assemble_export_cards_builds_japanese_row_without_ipa`, although the plan named only `tests/services/test_japanese_furigana.py` for exclusion. It was not changed because Japanese Windows correction is explicitly out of scope.

## Authentication Gates

None. All provider behavior was tested with offline fakes; no live secrets or `.env` file were read.

## Known Stubs

None in the Mandarin implementation. Integration providers are intentional offline test doubles, not runtime stubs.

## Threat Review

- No unplanned endpoint, authentication path, or external file-ingest boundary was introduced.
- Planned trust-boundary mitigations are present: Simplified/script validation, escaped derived fields, explicit snapshot columns, mixed-language/source rejection, media basename/existence checks, and fixed template JavaScript only.
- The proof artifact contains generated fixture content and generated audio bytes only; the reference APKG was never opened or copied.

## Git and Planning State

- No commit, amend, push, branch, PR, reset, clean, or staging operation was performed.
- No roadmap, project specification, phase state, or verification file was created or updated.
- Pre-existing deleted Danish reports and unrelated untracked Japanese images/documents were left untouched.

## Self-Check: PASSED

Verified all eight key implementation/proof artifacts exist. The retained APKG is exactly `66024` bytes and its SHA-256 matches both this summary and `UI-PROOF.md`.
