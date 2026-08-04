---
mode: quick
task: 044-romaji-frequencia-japones
plan: "044"
runtime: opencode
assurance: independently_checked_user_risk_accepted
status: complete
completed: 2026-08-04
duration: 20m
tasks_completed: 3
files_modified:
  - pyproject.toml
  - uv.lock
  - src/multilang/services/japanese_romaji.py
  - src/multilang/services/japanese_frequency_deck.py
  - src/multilang/services/assemble_export_cards.py
  - src/multilang/domain/exporting.py
  - src/multilang/db/models.py
  - src/multilang/repositories/export_repository.py
  - src/multilang/templates/japanese_card.md
  - alembic/versions/20260804_16_japanese_romaji_fields.py
  - tests/services/test_japanese_frequency_deck.py
  - tests/services/test_assemble_export_cards.py
  - tests/services/test_export_anki_package.py
  - tests/repositories/test_export_repository.py
  - .planning/quick/044-romaji-frequencia-japones/UI-PROOF.md
workflow_owned_artifacts:
  - .planning/quick/044-romaji-frequencia-japones/044-SUMMARY.md
---

# Quick 044: Romaji in Japanese Frequency Cards — Summary

**Local cutlet 0.5.2 Modified-Hepburn romaji now flows through the existing Japanese frequency note's exact 12-field schema, back-only template, frozen snapshots, APKG, CSV, and TSV without changing note/deck identity or GUID inputs; dynamic frozen APKG export performs no romanization.**

## Result

Tasks 044-01 through 044-03 were completed sequentially under strict RED-before-production TDD:

- Japanese target words and sentences are romanized locally with `cutlet.Cutlet("hepburn", use_foreign_spelling=False, ensure_ascii=True)`.
- Blank source/output, non-ASCII output, and excess `?` placeholders fail closed; a source question mark permits its matching output punctuation.
- Japanese frequency rows require all four frozen readings: `Word Reading`, `Word Romaji`, `Sentence Furigana`, and `Sentence Romaji`.
- Isolated and dynamic Japanese frequency models share the exact 12-field order.
- Both romaji values are absent from the front and structurally adjacent to their Japanese reading counterparts on the back.
- Snapshot persistence stores and reloads all four reading fields without converter-side recalculation.
- A fresh-process APKG regression forces the converter unavailable and still exports a fully populated frozen Japanese row, proving zero converter dependency in the dynamic export path.
- APKG model/note fields and CSV/TSV headers/values carry the expanded schema.
- Model ID `1762800701`, deck ID `1762800702`, note type `Multilang::Japanese Card`, isolated GUID payload, and dynamic identity/GUID inputs remain unchanged.

## TDD Evidence

### Pre-change baseline

The user supplied the exact broad baseline captured before any code or test edit, as explicitly allowed by the execution prompt:

```bash
uv run pytest tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py tests/cli/test_export_command.py tests/integration/test_frequency_e2e_export_flow.py tests/integration/test_custom_word_list_e2e_export_flow.py -q
```

Result: **18 passed, 3 warnings**.

Alembic was also confirmed at the sole pre-change head `20260720_15`. The executor repeated that exact head assertion immediately before creating the migration.

### RED — observed before all production/dependency edits

Only these four test files had changed when RED was run:

- `tests/services/test_japanese_frequency_deck.py`
- `tests/services/test_assemble_export_cards.py`
- `tests/services/test_export_anki_package.py`
- `tests/repositories/test_export_repository.py`

The exact planned RED node set was executed through the plan's exit-code guard. Pytest returned its expected test-failure exit code **1**; the shell guard then returned success because it confirmed that exact code.

Result: **16 failed, 1 warning in 14.45s**. All named tests collected; there were no collection, syntax, fixture, import-collection, or configuration errors.

Observed missing-behavior failures were:

1. Six parameter cases asserted that `multilang.services.japanese_romaji` did not yet exist.
2. The isolated model still exposed the old 10-field tuple rather than the required 12 fields.
3. `JAPANESE_EXPORT_CARD_FIELD_NAMES` still exposed the old 10-field tuple.
4. Dynamic assembly made zero romaji calls instead of calls for `学校` and `学校に行く。`.
5. The assembly failure-path test asserted the missing romaji service.
6. Dynamic Japanese note fields lacked both romaji positions.
7. The Japanese back template lacked `Word Romaji` and `Sentence Romaji` references.
8. Parametrized CSV and TSV rows lacked both romaji positions.
9. Reloaded snapshots returned `word_reading=None` because Japanese reading columns were not persisted.
10. The Alembic graph lacked revision `20260804_16`.

This RED evidence established every intended gap before `uv add` or any production, dependency, ORM, repository, template, or migration edit.

### GREEN

After implementation:

- Task 044-02 focused behavior: **20 passed in 8.29s**.
- Task 044-03 migration/reload gate: **2 passed, 5 warnings in 7.72s**.
- Authoritative focused regression after verifier-gap closure: **156 passed, 10 warnings in 57.47s**.
- Exact post-change broad baseline after verifier-gap closure: **18 passed in 87.41s**.
- Structural UI-proof suite after verifier-gap closure: **83 passed in 35.30s**.

No behavior-only refactor beyond the tested implementation was needed.

## Implementation Details

### Dependency and local converter

- Added `cutlet>=0.5,<0.6`; `uv.lock` resolved `cutlet==0.5.2` plus its local conversion dependencies.
- Added a lazily cached converter in `japanese_romaji.py`.
- Conversion strips source/output, normalizes output whitespace, enforces ASCII, and rejects excess output question marks relative to ASCII/full-width question punctuation in the source.
- Conversion errors are wrapped as `JapaneseRomajiError`; no provider, LLM, TTS, or network path is involved at runtime or in tests.

### Export domain and assembly

- Expanded only Japanese frequency rows to:

```text
SortIndex, Target Word, Word Reading, Word Romaji, Definition, Sentence,
Sentence Furigana, Sentence Romaji, Sentence Translation,
word_audio, sentence_audio, Image
```

- Added aliased Pydantic fields and fail-closed Japanese-frequency validation.
- Removed fallback derivation from ordered Japanese reading mappings; all four values must already be frozen.
- Dynamic assembly derives furigana and romaji once each from the unescaped display word and accepted sentence, then HTML-escapes all four values.
- Any local derivation failure is wrapped with item context before snapshot persistence.
- Literal tuple assertions preserve every non-Japanese export contract.

### Isolated deck and template

- `JapaneseCard` derives `word_romaji` and `sentence_romaji` through cached properties when an isolated note first consumes them; module import constructs no romaji and neither value participates in the GUID payload.
- Isolated notes use the same exact 12 fields as dynamic notes.
- The front remains romaji-free.
- The back adds `<div class="wordRomaji">` below word reading and `<div class="sentenceRomaji">` below sentence reading and before translation.
- Existing furigana toggle markup, word/sentence audio, conditional blank Image, and Japanese fields remain present.
- New romaji styles are deliberately smaller and muted; no native-rendering claim is made.

### Persistence and migration

- Added nullable ORM `Text` columns for `word_reading`, `word_romaji`, `sentence_furigana`, and `sentence_romaji`.
- Repository payload and reconstruction map all four columns explicitly and never recalculate them.
- Added linear Alembic revision `20260804_16` with `down_revision = "20260720_15"`.
- Upgrade adds only the four nullable columns in the locked order; downgrade drops only those columns in reverse order.
- A disposable SQLite database passed upgrade → downgrade → upgrade while retaining every pre-existing `card_exports` column.

## Verification Commands and Results

| Command / gate | Result |
|---|---|
| User-supplied exact pre-change broad baseline | `18 passed, 3 warnings` |
| Exact RED node set with `test "$code" -eq 1` | pytest exit `1`; `16 failed, 1 warning` |
| `uv lock --check` plus exact cutlet version/output assertions | PASS; `cutlet==0.5.2`, `Gakkou`, `Gakkou ni iku.`, `Nan shite iru no?` |
| Task 044-02 focused romaji/model/export tests | `20 passed` |
| Exact `romanji` / `pykakasi` scan command | PASS |
| Migration upgrade/downgrade/upgrade plus expiration reload | `2 passed, 5 warnings` |
| Alembic sole-head assertion | PASS: `['20260804_16']` |
| Fresh-process frozen APKG export with converter forced unavailable | PASS; exporter import and APKG generation made zero converter calls |
| Authoritative focused domain/template/tabular/repository/migration suite | `156 passed, 10 warnings` |
| Exact post-change broad baseline | `18 passed` |
| Structural Japanese model/template/APKG/tabular suite | `83 passed` |
| `node .planning/bin/gsdd.mjs ui-proof validate .../UI-PROOF.md` | `valid: true`, no errors or warnings |
| `git diff --check` | PASS |

The 10 focused-suite warnings and 5 migration-gate warnings are the existing Alembic `path_separator` deprecation warning from `alembic.ini`; changing that unrelated configuration was outside the accepted 15-file scope. `uv add` also reported the pre-existing `huggingface-hub==1.11.0` missing `inference` extra warning without affecting resolution.

## Structural UI Proof and Claim Limit

`.planning/quick/044-romaji-frequencia-japones/UI-PROOF.md` contains nine passed code/test/runtime observations covering:

1. front omission;
2. back adjacency and unchanged references;
3. isolated model fields and identity;
4. dynamic model parity;
5. generated isolated/dynamic note fields;
6. generated APKG ZIP and `collection.anki2` model/note inspection;
7. generated CSV header/value order;
8. generated TSV header/value order.
9. fresh-process dynamic APKG export from frozen values with the romaji converter forced unavailable.

The proof validates structure only. **Anki Desktop/mobile pixels, typography, wrapping, visual placement, responsiveness, accessibility judgment, and usability were not exercised or accepted.** No screenshot, trace, video, provider call, or retained raw APKG/SQLite/tabular report was created.

## Changed Files

### Accepted 15-file implementation/test/proof scope

1. `pyproject.toml`
2. `uv.lock`
3. `src/multilang/services/japanese_romaji.py`
4. `src/multilang/services/japanese_frequency_deck.py`
5. `src/multilang/services/assemble_export_cards.py`
6. `src/multilang/domain/exporting.py`
7. `src/multilang/db/models.py`
8. `src/multilang/repositories/export_repository.py`
9. `src/multilang/templates/japanese_card.md`
10. `alembic/versions/20260804_16_japanese_romaji_fields.py`
11. `tests/services/test_japanese_frequency_deck.py`
12. `tests/services/test_assemble_export_cards.py`
13. `tests/services/test_export_anki_package.py`
14. `tests/repositories/test_export_repository.py`
15. `.planning/quick/044-romaji-frequencia-japones/UI-PROOF.md`

This `044-SUMMARY.md` is the separately required workflow completion artifact.

## Scope Risk Acceptance and Worktree Integrity

- The independent checker flagged the inclusive 15-file quick-task threshold.
- The user explicitly accepted that known risk and instructed execution without revisiting or widening scope.
- No third Japanese deck, reverse-kana training, new note type, model/deck identity, non-frequency Japanese schema, pykakasi path, provider path, image population, audio redesign, or frequency-content change was introduced.
- Unrelated dirty/untracked planning and preview artifacts, including `.planning/quick/LOG.md`, were not edited, reverted, staged, cleaned, or incorporated.
- `ROADMAP.md`, `SPEC.md`, `STATE.md`, and `.planning/quick/LOG.md` were not updated by this execution.

## Security and Threat Model

- **T-Q044-01:** mitigated by blank/ASCII/question-placeholder validation in both the converter and manually constructible export rows, with failure before persistence.
- **T-Q044-02:** mitigated by romanizing raw source first and HTML-escaping all derived readings during assembly.
- **T-Q044-03:** mitigated by locked IDs/names and stable isolated/dynamic GUID assertions.
- **T-Q044-04:** mitigated by one linear additive migration, explicit ORM/repository mapping, schema parity, rollback, and expiration/reload tests.
- **T-Q044-05:** mitigated by local cutlet-only execution and offline fixed-data tests.
- **T-Q044-06:** accepted as planned; conversion is bounded to one word and one sentence per card through one cached converter.
- **T-Q044-07:** mitigated by validated structural proof metadata and explicit native-Anki claim exclusion.

No unplanned network endpoint, authentication path, file-access trust boundary, or schema surface was introduced beyond the migration registered in the plan threat model.

## Known Stubs

None. Blank `Image` remains an intentional locked export contract, and occurrences of “placeholder” in the new code are fail-closed validation messages rather than stub behavior.

## Deviations from Plan

### Implementation deviations

Initial verification found that importing the dynamic APKG exporter constructed the 12 isolated sample cards and eagerly ran 24 Cutlet conversions through `JapaneseCard.__post_init__`. A new RED regression reproduced that coupling with the converter forced unavailable. The root cause was fixed in the existing `japanese_frequency_deck.py` scope by replacing eager derived dataclass fields with cached properties, so isolated notes still derive romaji while dynamic exporter import and frozen APKG generation make zero converter calls. No new file or product scope was added.

### Execution-environment notes

1. `gsd-sdk` was unavailable (`command not found`) during initial context queries. This quick task explicitly prohibited global state/roadmap updates, so no required implementation or verification was blocked; the repository-local `gsdd.mjs` helper validated UI proof successfully.
2. Context7 resolved an unrelated TypeScript “Cullet” package rather than Python cutlet. Per the documented fallback, the official cutlet v0.5.2 GitHub README/source was checked and confirmed the constructor flags and local Modified-Hepburn behavior.
3. No commit or staging operation was performed because the user explicitly prohibited commit, stage, amend, reset, clean, and git-configuration changes.

## Git and Workflow

- Commits: none.
- Staging: none.
- Destructive Git commands: none.
- Git configuration changes: none.
- Live LLM/provider/TTS calls: none.
- Manual edits: all performed with `apply_patch`; only `uv add` refreshed dependency metadata/lock state.

## Self-Check: PASSED

- All 15 accepted scope files and both quick-task workflow artifacts exist.
- RED occurred after only the four planned test files changed and before every production/dependency edit.
- The exact RED process returned pytest test-failure code 1 for missing behavior only.
- The verifier-discovered frozen-export coupling was reproduced RED, fixed at its eager-initialization source, and verified with zero converter calls.
- The final focused, broad, structural, migration, lock, spelling, Alembic-head, and UI-proof gates passed.
- IDs, GUID inputs, blank Image, non-Japanese tuples, and back-only romaji boundaries are asserted.
- No unrelated dirty/untracked artifact or prohibited planning state file was modified by this execution.
