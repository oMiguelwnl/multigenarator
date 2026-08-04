---
mode: quick
task: 044-romaji-frequencia-japones
plan: "044"
type: execute
wave: 1
runtime: opencode
assurance: independently_checked_user_risk_accepted
reduced_assurance: true
reduced_assurance_reason: ".planning/templates/roles/planner.md and .planning/templates/delegates/plan-checker.md are absent. An independent checker did run and still flagged scope_sanity at the inclusive 15-file boundary; the user explicitly accepted that known risk after confirming /gsdd-plan would incorrectly target Korean Phase 30. The pre-change-baseline warning is addressed."
depends_on: []
autonomous: true
task_count: 3
requirements: []
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
scope_sanity:
  status: checker_flagged_user_accepted
  changed_file_count: 15
  threshold: 15
  consolidation: "10 production/dependency files + 4 test files + UI-PROOF.md; generic template-loader, tabular, domain, and migration-parity suites are executed unchanged."
  risk_acceptance: "The checker still flags the inclusive 15-file boundary; the user explicitly accepted this known quick-task risk and chose not to route into unrelated Korean Phase 30 planning."
non_goals:
  - "Do not create a third Japanese deck, reverse-kana training, another note type, or another model/deck identity."
  - "Do not add romaji to Japanese word-list, highlights, kana, or any non-Japanese schema; the changed product surface is Japanese frequency only."
  - "Do not use pykakasi, an LLM, a provider, or a network call for romanization."
  - "Do not redesign the Japanese card, remove/change furigana behavior, change audio, populate Image, or alter frequency content/assets."
  - "Do not update ROADMAP.md, SPEC.md, STATE.md, or .planning/quick/LOG.md."
  - "Do not edit, revert, stage, clean, or include unrelated planning/preview artifacts already present in the worktree."
hard_boundaries:
  - "Use canonical spelling `romaji` in identifiers, exported field names, template classes, tests, and learner-facing text; never introduce `romanji`."
  - "JAPANESE_MODEL_ID remains 1762800701, JAPANESE_DECK_ID remains 1762800702, JAPANESE_NOTE_TYPE_NAME remains `Multilang::Japanese Card`, and both isolated and dynamic note GUID inputs remain unchanged."
  - "The Japanese frequency schema is exactly: SortIndex, Target Word, Word Reading, Word Romaji, Definition, Sentence, Sentence Furigana, Sentence Romaji, Sentence Translation, word_audio, sentence_audio, Image."
  - "Romanization is local Modified Hepburn through cutlet 0.5.x with foreign spellings disabled and ASCII enforcement enabled. Blank output, raw non-ASCII output, and question marks beyond punctuation present in the source fail closed."
  - "The sole migration adds word_reading, word_romaji, sentence_furigana, and sentence_romaji as nullable Text columns; it neither rewrites nor drops existing columns during upgrade."
  - "Tests must be added and observed failing for the intended missing behavior before any production file is changed."
  - "Tests remain offline and must not invoke Azure, an LLM, translation APIs, or any other provider."
anti_regression_targets:
  - "Existing Japanese Target Word, Word Reading/furigana toggle, Sentence/Sentence Furigana, Definition/Translation, both audio fields, and blank Image retain their behavior and order relative to the inserted romaji fields."
  - "All non-Japanese field tuples, templates, APKG models, CSV/TSV headers, and repository rows remain byte-for-byte equivalent at the contract level."
  - "Existing Japanese model/deck IDs, note type name, and GUID derivation stay stable when romaji content changes."
  - "Frozen Japanese snapshots reload all four reading fields after session expiration; exporters consume the snapshot rather than recalculating romaji."
escalation_triggers:
  - "Before creating the migration, stop if Alembic has any head other than 20260720_15; do not create a competing branch or guess a new down_revision."
  - "Stop if uv cannot resolve cutlet in the >=0.5,<0.6 range on Python 3.12; do not substitute another romanizer."
  - "Stop if a requested field insertion requires changing the Japanese model/deck IDs or adding a note type/deck; those outcomes conflict with locked scope."
closure_claim_limit: "Automation may claim deterministic romaji derivation, fail-closed validation, frozen persistence, exact template/model/format structure, and stable identity. It may not claim visual placement, typography, wrapping, or usability in Anki Desktop/mobile because no native Anki renderer is exercised."
ui_proof_slots:
  - slot_id: japanese-frequency-romaji-structural-contract
    claim: "The Japanese frequency front contains no romaji, while its back places Word Romaji beneath the existing word reading and Sentence Romaji beneath the existing sentence reading without changing Japanese/furigana/audio/Image fields."
    route_state: "Inspect japanese_card.md, build_japanese_model(), build_multilang_model(source_type='frequency', language=SupportedLanguage.JA), and a generated Japanese APKG's collection.anki2 model/note fields."
    required_evidence_kinds: [code, test, runtime]
    minimum_observations: 7
    expected_artifact_types:
      - "static front/back template assertions"
      - "generated isolated and dynamic genanki model field inspection"
      - "generated APKG ZIP and collection.anki2 SQLite inspection"
      - "Japanese CSV and TSV header/value assertions"
      - "UI-PROOF.md with command, observation, artifact, and privacy metadata"
    validation_command: "uv run pytest tests/services/test_japanese_frequency_deck.py tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py -q"
    environment: "Python 3.12, cutlet 0.5.x, genanki, zipfile, and SQLite; offline; no Anki renderer."
    viewport: "Not applicable to this structural claim: no rendered pixels or viewport-dependent behavior is asserted."
    manual_acceptance_required: false
    claim_limit: "Proves field references/order, front omission, back structural adjacency, unchanged existing references, and generated APKG/CSV/TSV contents only; actual Anki Desktop/mobile rendering is outside the claim."
must_haves:
  truths:
    - "A Japanese frequency learner sees deterministic target-word and sentence romaji only on the answer side as secondary reading aids."
    - "Isolated and dynamic Japanese frequency notes use the same exact 12-field order, and APKG/CSV/TSV carry the corresponding romaji values."
    - "Blank or unresolved romanization cannot be persisted or exported, while a legitimate source question mark remains valid punctuation."
    - "Japanese furigana and romaji survive snapshot commit, session expiration, and reload without exporter-side recalculation."
    - "Japanese model/deck/note identity, GUID behavior, furigana toggle, audio, blank Image, and every non-Japanese schema remain unchanged."
    - "The additive migration upgrades, downgrades, and upgrades a disposable database while touching only the four Japanese snapshot columns."
  artifacts:
    - path: src/multilang/services/japanese_romaji.py
      provides: "Local Modified-Hepburn conversion and fail-closed output validation."
    - path: src/multilang/domain/exporting.py
      provides: "Exact Japanese frequency row schema, aliases, validation, and ordered mapping."
    - path: src/multilang/templates/japanese_card.md
      provides: "Back-only Word Romaji and Sentence Romaji structural references."
    - path: alembic/versions/20260804_16_japanese_romaji_fields.py
      provides: "One reversible additive migration for old furigana and new romaji snapshot values."
    - path: src/multilang/repositories/export_repository.py
      provides: "Four-field snapshot write/read round trip."
    - path: tests/services/test_japanese_frequency_deck.py
      provides: "Deterministic offline converter/rejection evidence plus isolated Japanese deck coverage."
    - path: .planning/quick/044-romaji-frequencia-japones/UI-PROOF.md
      provides: "Narrow structural UI evidence with explicit native-Anki claim limits."
  key_links:
    - from: src/multilang/services/assemble_export_cards.py
      to: src/multilang/services/japanese_romaji.py
      via: "one word call and one sentence call on unescaped Japanese source text before HTML escaping"
    - from: src/multilang/services/assemble_export_cards.py
      to: src/multilang/domain/exporting.py
      via: "word_romaji and sentence_romaji on the frozen ExportCardRow"
    - from: src/multilang/repositories/export_repository.py
      to: src/multilang/db/models.py
      via: "explicit payload and domain reconstruction for all four Japanese reading columns"
    - from: src/multilang/domain/exporting.py
      to: src/multilang/services/export_anki_package.py
      via: "JAPANESE_EXPORT_CARD_FIELD_NAMES and ordered_field_mapping consumed by generic note creation"
    - from: src/multilang/domain/exporting.py
      to: src/multilang/services/export_tabular_bundle.py
      via: "language-aware field tuple consumed by generic CSV/TSV serialization"
    - from: src/multilang/templates/japanese_card.md
      to: src/multilang/domain/exporting.py
      via: "template references validated against the same exact Japanese field tuple"
---

# Quick Task 044: Romaji in Japanese Frequency Cards

<objective>
Add deterministic, local Modified-Hepburn romaji for the target word and example sentence to the existing Japanese frequency note, render both values on the back only, and freeze Japanese furigana plus romaji in export snapshots without changing deck/note identity or any non-Japanese contract.

Purpose: Make Japanese frequency answers easier to read while preserving recall, furigana pedagogy, export stability, and offline determinism.

Output: A cutlet-backed romaji service, the exact expanded Japanese schema/template, one reversible persistence migration, repository round-trip support, and focused structural/export evidence.
</objective>

## Reduced Assurance / Checker Result

- `.planning/templates/roles/planner.md` and `.planning/templates/delegates/plan-checker.md` do not exist, so template-backed role assurance remains unavailable.
- An independent checker did run. It blocked the prior 20-file write set and warned that historical broad-suite failures lacked a pre-change baseline; this plan consolidates the write set to 15 files and adds an exact green before/after broad regression baseline.
- The checker still flags `scope_sanity` at its inclusive 15-file boundary. The user explicitly accepted that known risk and chose to continue this quick task after confirming `/gsdd-plan` would incorrectly route to Korean Phase 30.
- The recreated plan was also self-checked against the quick-skill contract, the live implementation/tests, and the current single Alembic head `20260720_15`.
- Context7 had no relevant cutlet entry. Official PyPI/GitHub documentation was used instead and confirms cutlet 0.5.2 (MIT), default Modified Hepburn, `use_foreign_spelling=False`, `ensure_ascii=True`, and the existing fugashi/UniDic integration.

## Locked Decisions

- **D-01 — Product identity:** This is romanized reading inside Japanese frequency cards, not another deck and not reverse-kana training. Preserve model `1762800701`, deck `1762800702`, note type `Multilang::Japanese Card`, and existing GUID inputs.
- **D-02 — Exact fields:** Insert `Word Romaji` immediately after `Word Reading` and `Sentence Romaji` immediately after `Sentence Furigana`, using canonical code/UI spelling `romaji`.
- **D-03 — Local derivation:** Use cutlet `>=0.5,<0.6` with Modified Hepburn, foreign spellings disabled, and ASCII enforcement enabled. Do not use pykakasi, an LLM, or a provider.
- **D-04 — Fail closed:** Reject blank input/output, raw non-ASCII output, and unresolved `?` placeholders; retain `?` only when it corresponds to question punctuation already present in the source.
- **D-05 — Back-only aid:** Keep romaji entirely absent from the front and show both values as secondary aids on the back without changing the furigana toggle, audio, Image, or other Japanese fields.
- **D-06 — Frozen persistence:** In one additive migration, persist existing `word_reading` and `sentence_furigana` plus new `word_romaji` and `sentence_romaji`; prove reload after session expiration.
- **D-07 — Complete export path:** Derive dynamic word/sentence romaji once each before escaping, then carry exact values through isolated/dynamic models and APKG/CSV/TSV field-order checks.
- **D-08 — TDD and proof:** Write and observe focused failures before production changes, keep tests offline, and limit UI proof to static/generated-model/APKG structure unless a native renderer is actually exercised.

## Goal-Backward Outcomes

1. For back-only romaji to be visible, the Japanese schema, isolated card mapping, dynamic ExportCardRow mapping, and template must all share the exact two new field names and order.
2. For values to be reliable, a single local converter must produce validated Modified Hepburn and both assembly paths must fail before persistence/export on unresolved output.
3. For regenerated exports to be stable, all four Japanese reading values must be explicit database columns wired through ORM and repository conversion.
4. For Anki imports to remain compatible, the existing note/deck IDs and GUID inputs must not depend on romaji, while generated APKG/CSV/TSV artifacts must expose the expanded field tuple.
5. For the visual claim to be honest, automated evidence must inspect source/model/APKG structure and explicitly exclude native Anki pixels and usability.

## Existing Interfaces to Preserve

<interfaces>
From `src/multilang/services/japanese_frequency_deck.py`:

```python
JAPANESE_MODEL_ID = 1_762_800_701
JAPANESE_DECK_ID = 1_762_800_702
JAPANESE_NOTE_TYPE_NAME = "Multilang::Japanese Card"

class JapaneseCard:
    @property
    def guid(self) -> str: ...  # ja-frequency|sort_index|target_word|sentence
```

From `src/multilang/domain/exporting.py`:

```python
class ExportCardRow(BaseModel):
    word_reading: str | None = Field(default=None, alias="Word Reading")
    sentence_furigana: str | None = Field(default=None, alias="Sentence Furigana")

    def ordered_field_mapping(self, *, field_names: tuple[str, ...] | None = None) -> dict[str, object]: ...
```

From `src/multilang/repositories/export_repository.py`:

```python
def upsert_card_snapshots(self, records: list[ExportCardRow]) -> list[ExportCardRow]: ...
def list_card_snapshots(self, job_id: str) -> list[ExportCardRow]: ...
```

Verified cutlet 0.5.x API:

```python
converter = cutlet.Cutlet(
    "hepburn",
    use_foreign_spelling=False,
    ensure_ascii=True,
)
converter.romaji("学校に行く。")  # "Gakkou ni iku."
```
</interfaces>

## Dependency Order

| Task | Needs | Creates | Why sequential |
|---|---|---|---|
| 044-01 | Current green focused baseline and locked decisions | Collectable tests that fail for the intended missing romaji/persistence/template contracts | Establishes RED evidence before any production edit. |
| 044-02 | Recorded RED output from 044-01 | Dependency, converter, Japanese row/assembly/isolated/template implementation | Implements all learner/export behavior against pre-existing tests. |
| 044-03 | Green in-memory/export behavior and Alembic head `20260720_15` | Migration/ORM/repository round trip, rollback evidence, full focused regressions, structural UI proof | Persistence consumes the established fields and final proof inspects the completed path. |

Do not execute tasks in parallel. Task 044-01 owns all test expectations first; Tasks 044-02 and 044-03 may modify only production/proof files after the RED command has been observed and recorded.

<tasks>

<task id="044-01" type="auto" tdd="true">
  <name>Write the complete offline romaji contract and observe RED</name>
  <files>
    tests/services/test_japanese_frequency_deck.py,
    tests/services/test_assemble_export_cards.py,
    tests/services/test_export_anki_package.py,
    tests/repositories/test_export_repository.py
  </files>
  <entry_checkpoint>
    <automated>uv run pytest tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py tests/cli/test_export_command.py tests/integration/test_frequency_e2e_export_flow.py tests/integration/test_custom_word_list_e2e_export_flow.py -q</automated>
    <done>Before any edit, require exit code 0 and record the exact command plus passing count as the broad pre-change baseline. If it is not green, stop without edits rather than classifying failures as historical. Task 044-03 must run this identical node set.</done>
  </entry_checkpoint>
  <behavior>
    - `学校` becomes `Gakkou`, `学校に行く。` becomes `Gakkou ni iku.`, and `カツカレーは美味しい` becomes `Katsu karee wa oishii` rather than foreign-spelling output.
    - Blank input/output, `㐂 -> ?`, unknown text plus punctuation, and a fake converter returning raw Japanese raise `JapaneseRomajiError`; `何しているの？ -> Nan shite iru no?` remains valid because the source contains one question mark.
    - Japanese frequency rows require exact non-empty reading/romaji values, reject unresolved/raw romaji, preserve blank Image, and keep GUIDs stable when romaji changes.
    - Dynamic assembly calls romaji exactly once for the unescaped display word and once for the unescaped sentence, escapes both results, and saves nothing on derivation failure.
    - Isolated and dynamic model/note fields use the exact 12-field tuple; the front omits both romaji references and the back places them adjacent to their Japanese reading counterparts.
    - Generated Japanese APKG notes and parametrized CSV/TSV rows contain both values in exact order; existing furigana/audio/Image references remain present.
    - All four Japanese reading values survive `session.expire_all()` and reload.
    - A disposable migrated database can upgrade to the new head, downgrade to `20260720_15` with only the four added columns removed, and upgrade again.
  </behavior>
  <action>
    - Run and record the entry baseline before editing any file. It must be green; otherwise stop without production/test edits. Task 044-03 repeats the exact command and must also be green, so no unproven historical-failure classification is permitted.
    - Per D-08, add every new assertion to the four listed test files before touching production files. Keep the absent service import inside `test_japanese_frequency_deck.py` test bodies behind an `importlib.util.find_spec` assertion so pytest collects normally and reports a feature assertion failure rather than a collection/configuration error while `japanese_romaji.py` is absent.
    - In `test_japanese_frequency_deck.py`, add `test_japanese_romaji_uses_modified_hepburn_and_rejects_unresolved_output` covering foreign-spelling disablement, legitimate question punctuation, and parametrized blank/unresolved/raw-output cases. Extend isolated deck tests with exact IDs, exact fields, generated romaji, front omission, back adjacency, unchanged furigana/audio/Image references, and unchanged GUID inputs (D-01, D-03, D-04, D-05).
    - In `test_assemble_export_cards.py`, add `test_japanese_export_row_requires_valid_romaji_and_preserves_non_japanese_contracts` for the exact D-02 tuple, required Japanese values, unresolved/raw romaji rejection, stable GUID behavior, and unchanged non-Japanese tuples. Update the existing Japanese assembly test and add `test_assemble_japanese_romaji_fails_before_persisting`, using a counting fake/monkeypatch to prove calls are exactly `["学校", "学校に行く。"]`, escaping occurs only after conversion, and the fake repository remains empty when conversion fails (D-01, D-02, D-04, D-07).
    - In `test_export_anki_package.py`, add `test_japanese_frequency_template_and_apkg_are_back_only_with_romaji`: exercise `build_multilang_model`/the validated Japanese template directly, assert front omission/back adjacency/existing references, and extract generated `collection.anki2` to inspect `col.models` and `notes.flds`. In the same file add `test_japanese_tabular_exports_use_romaji_field_order`, importing `write_export_tabular_bundle` and parametrizing CSV/TSV for the exact tuple and values (D-02, D-05, D-07).
    - In `test_export_repository.py`, add `test_japanese_snapshot_round_trip_survives_expiration` and self-contained `test_japanese_export_columns_upgrade_downgrade_upgrade`. The latter upgrades a disposable SQLite database, checks the four columns, downgrades to `20260720_15`, proves only those additions disappeared while pre-existing `card_exports` columns remain, then upgrades again (D-06). Leave generic migration-parity tests unchanged.
    - Run the RED command below. Confirm every named test is collected and the exit code is exactly pytest's test-failure code `1`; syntax, fixture, import-collection, or command errors do not satisfy RED. Record the failing assertions in the execution summary before continuing.
  </action>
  <verify>
    <automated>bash -lc 'uv run pytest tests/services/test_japanese_frequency_deck.py::test_japanese_romaji_uses_modified_hepburn_and_rejects_unresolved_output tests/services/test_japanese_frequency_deck.py::test_build_japanese_model_uses_template_and_field_order tests/services/test_assemble_export_cards.py::test_japanese_export_row_requires_valid_romaji_and_preserves_non_japanese_contracts tests/services/test_assemble_export_cards.py::test_assemble_export_cards_builds_japanese_row_without_ipa tests/services/test_assemble_export_cards.py::test_assemble_japanese_romaji_fails_before_persisting tests/services/test_export_anki_package.py::test_build_multilang_note_maps_japanese_frequency_fields tests/services/test_export_anki_package.py::test_japanese_frequency_template_and_apkg_are_back_only_with_romaji tests/services/test_export_anki_package.py::test_japanese_tabular_exports_use_romaji_field_order tests/repositories/test_export_repository.py::test_japanese_snapshot_round_trip_survives_expiration tests/repositories/test_export_repository.py::test_japanese_export_columns_upgrade_downgrade_upgrade -q; code=$?; test "$code" -eq 1'</automated>
  </verify>
  <done>All requested contracts exist as collectable tests, the targeted command fails only because romaji fields/service/template/persistence are absent, and no production file has changed.</done>
</task>

<task id="044-02" type="auto" tdd="true">
  <name>Implement local romaji and wire both Japanese frequency export paths</name>
  <files>
    pyproject.toml,
    uv.lock,
    src/multilang/services/japanese_romaji.py,
    src/multilang/domain/exporting.py,
    src/multilang/services/assemble_export_cards.py,
    src/multilang/services/japanese_frequency_deck.py,
    src/multilang/templates/japanese_card.md
  </files>
  <action>
    - Add `cutlet>=0.5,<0.6` with uv and refresh `uv.lock`. Do not add pykakasi or any provider dependency. Keep existing fugashi/unidic-lite dependencies unchanged (D-03).
    - Create `japanese_romaji.py` exporting `JapaneseRomajiError` and `romanize_japanese`. Lazily cache one `cutlet.Cutlet("hepburn", use_foreign_spelling=False, ensure_ascii=True)` instance. Strip source/output and normalize output whitespace; raise on blank source/output or non-ASCII output. Count ASCII `?` plus full-width `？` in the source and reject output when its `?` count exceeds that source punctuation count, which blocks cutlet placeholders without rejecting a real question sentence (D-03, D-04).
    - In `domain/exporting.py`, define the exact D-02 Japanese tuple, add optional Pydantic fields `word_romaji`/alias `Word Romaji` and `sentence_romaji`/alias `Sentence Romaji`, and map all four Japanese reading values directly rather than falling back to raw word/sentence text. For `ja + frequency`, require the four reading values, require romaji to be ASCII, and apply the same source-question-count rule so manually constructed invalid rows cannot bypass the service. Leave every non-Japanese path untouched (D-02, D-04).
    - In dynamic assembly, replace the two-value Japanese helper with a four-value Japanese pronunciation result. On `ja + frequency` only, call `format_japanese_furigana` and `romanize_japanese` exactly once each for the raw display word and raw accepted sentence, then HTML-escape all four derived values when constructing `ExportCardRow`. Wrap either local derivation error as `AssembleExportCardsError` with item context before persistence; no fallback/recalculation is allowed (D-04, D-07).
    - In the isolated Japanese deck, add `word_romaji` and `sentence_romaji` to `JapaneseCard` as derived, non-GUID content and ensure each immutable card/note gets values from `romanize_japanese(target_word)` and `romanize_japanese(sentence)`, not hand-written strings. Insert both fields into `JAPANESE_FIELD_NAMES` and `_japanese_card_fields` at the exact D-02 positions. Do not change `JAPANESE_MODEL_ID`, `JAPANESE_DECK_ID`, note type/deck names, audio logic, Image, or the GUID payload (D-01, D-02).
    - Update `japanese_card.md`'s documented field list. Keep the front markup free of both romaji references. On the back, render `<div class="wordRomaji">{{Word Romaji}}</div>` immediately below the word reading and `<div class="sentenceRomaji">{{Sentence Romaji}}</div>` immediately below the sentence reading and before translation. Style both as smaller/muted secondary aids without modifying the existing `.jPlain`/`.jReading` toggle contract, audio nodes, conditional Image, or other layout structure (D-05).
    - Use only identifiers and labels containing `romaji`; scan the changed code/template/tests for the misspelling `romanji` and remove it (D-02).
  </action>
  <verify>
    <automated>uv lock --check && uv run python -c "from importlib.metadata import version; from multilang.services.japanese_romaji import romanize_japanese; assert version('cutlet').startswith('0.5.'); assert romanize_japanese('学校') == 'Gakkou'; assert romanize_japanese('学校に行く。') == 'Gakkou ni iku.'; assert romanize_japanese('何しているの？') == 'Nan shite iru no?'"</automated>
    <automated>uv run pytest tests/services/test_japanese_frequency_deck.py tests/services/test_assemble_export_cards.py::test_japanese_export_row_requires_valid_romaji_and_preserves_non_japanese_contracts tests/services/test_assemble_export_cards.py::test_assemble_export_cards_builds_japanese_row_without_ipa tests/services/test_assemble_export_cards.py::test_assemble_japanese_romaji_fails_before_persisting tests/services/test_export_anki_package.py::test_build_multilang_note_maps_japanese_frequency_fields tests/services/test_export_anki_package.py::test_japanese_frequency_template_and_apkg_are_back_only_with_romaji tests/services/test_export_anki_package.py::test_japanese_tabular_exports_use_romaji_field_order -q</automated>
    <automated>uv run python -c "from pathlib import Path; paths=['pyproject.toml','src/multilang/services/japanese_romaji.py','src/multilang/services/japanese_frequency_deck.py','src/multilang/services/assemble_export_cards.py','src/multilang/domain/exporting.py','src/multilang/templates/japanese_card.md']; text='\n'.join(Path(p).read_text(encoding='utf-8') for p in paths); assert 'romanji' not in text.casefold(); assert 'pykakasi' not in Path('pyproject.toml').read_text(encoding='utf-8').casefold()"</automated>
  </verify>
  <done>Both isolated and dynamic Japanese frequency rows derive validated local romaji, expose the exact 12 fields, render romaji on the back only, and keep all locked Japanese identity/pedagogy contracts intact.</done>
</task>

<task id="044-03" type="auto" tdd="true">
  <name>Persist all Japanese readings and close migration/export/UI evidence</name>
  <files>
    src/multilang/db/models.py,
    src/multilang/repositories/export_repository.py,
    alembic/versions/20260804_16_japanese_romaji_fields.py,
    .planning/quick/044-romaji-frequencia-japones/UI-PROOF.md
  </files>
  <entry_checkpoint>
    <automated>uv run python -c "from alembic.config import Config; from alembic.script import ScriptDirectory; heads=ScriptDirectory.from_config(Config('alembic.ini')).get_heads(); assert heads == ['20260720_15'], heads"</automated>
    <done>The live migration graph still has exactly the expected predecessor before the new revision is created.</done>
  </entry_checkpoint>
  <action>
    - Before writing the migration, run the head assertion below and require exactly `['20260720_15']`. Then create revision `20260804_16` with `down_revision = "20260720_15"`. Its upgrade adds `word_reading`, `word_romaji`, `sentence_furigana`, and `sentence_romaji` to `card_exports` as nullable `sa.Text()` in that order; its downgrade drops only those four columns in reverse order (D-06). Nullable columns preserve legacy-row upgrade compatibility; do not invent unavailable backfill data.
    - Mirror the same four nullable `Text` fields on `CardExportModel`. Add all four values explicitly to `ExportRepository._card_payload` and `_to_card_domain`; do not place them in JSON or recalculate through cutlet during reads/exports. Keep ORM query construction parameterized through SQLAlchemy (D-06, D-07).
    - Run the migration upgrade/downgrade/upgrade test and repository expiration test first. A reloaded Japanese row must exactly equal the pre-expiration `word_reading`, `word_romaji`, `sentence_furigana`, and `sentence_romaji`, while its model/note GUID and blank Image remain unchanged.
    - Run the complete focused command and treat it as the authoritative gate. Then repeat the exact green broad command captured by Task 044-01 and require exit code 0 again. Do not classify or waive any final failure as historical within this plan.
    - Create `UI-PROOF.md` only after the structural validation command passes. Use fenced JSON with top-level `proof_bundle_version`, `scope`, `route_state`, `environment`, `viewport`, `evidence_inputs`, `commands_or_manual_steps`, `observations`, `artifacts`, `privacy`, `result`, and `claim_limits`. Record at least seven observations matching the slot; every observation must include `slot_id`, `claim`, `route_state`, `observation`, `evidence_kind`, `artifact_path` or a precise manual step, privacy metadata, `result`, and `claim_limit`.
    - Give each evidence artifact explicit `visibility`, `retention`, `sensitivity`, and `safe_to_publish`. Repository source/tests may be marked repository-visible/non-sensitive; raw APKG extractions, SQLite files, logs, screenshots, traces, or reports are local-only and `safe_to_publish: false` by default. Do not create or claim screenshots. Set the slot result to pass only for structural evidence and state that Anki Desktop/mobile visual acceptance was not exercised and is outside the claim (D-08).
    - Validate `UI-PROOF.md` with the repository-local gsdd helper. Do not use this proof task to alter ROADMAP/SPEC/LOG or any unrelated preview/planning files.
  </action>
  <verify>
    <automated>uv run pytest tests/repositories/test_export_repository.py::test_japanese_export_columns_upgrade_downgrade_upgrade tests/repositories/test_export_repository.py::test_japanese_snapshot_round_trip_survives_expiration -q</automated>
    <automated>uv run python -c "from alembic.config import Config; from alembic.script import ScriptDirectory; heads=ScriptDirectory.from_config(Config('alembic.ini')).get_heads(); assert heads == ['20260804_16'], heads"</automated>
    <automated>uv run pytest tests/services/test_japanese_furigana.py tests/domain/test_exporting.py tests/services/test_japanese_frequency_deck.py tests/services/test_assemble_export_cards.py tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py tests/repositories/test_export_repository.py tests/test_migration_schema_parity.py -q</automated>
    <automated>uv run pytest tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py tests/cli/test_export_command.py tests/integration/test_frequency_e2e_export_flow.py tests/integration/test_custom_word_list_e2e_export_flow.py -q</automated>
    <automated>node .planning/bin/gsdd.mjs ui-proof validate .planning/quick/044-romaji-frequencia-japones/UI-PROOF.md</automated>
  </verify>
  <done>The single reversible migration is the Alembic head, all four Japanese reading values survive session expiration, focused tests pass, the identical broad regression passes before and after edits, and the validated proof bundle supports only the narrow structural claim.</done>
</task>

</tasks>

<threat_model>

## Trust Boundaries

| Boundary | Description |
|---|---|
| Japanese lexical/sentence text -> local cutlet | Learner-facing source text enters a morphology-backed converter and may contain unknown characters or punctuation. |
| Derived readings -> ExportCardRow snapshot | Furigana/romaji become escaped, validated, frozen export data. |
| Snapshot -> Anki HTML/APKG/CSV/TSV | Persisted text crosses into HTML-capable card fields and importable artifacts. |
| Alembic/ORM -> repository reload | Database schema and object mapping must agree across upgrade, rollback, expiration, and reload. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-Q044-01 | Tampering | `japanese_romaji.py` / assembly | mitigate | Require nonblank ASCII output, reject excess `?` placeholders/raw Japanese, and abort before repository persistence. |
| T-Q044-02 | Elevation of Privilege | text -> `japanese_card.md` HTML | mitigate | Romanize raw source first, then use `html.escape`; template contains only fixed project JavaScript and validated field references. |
| T-Q044-03 | Spoofing | Japanese note/deck identity | mitigate | Lock numeric IDs/name and prove GUID inputs ignore romaji through isolated and dynamic tests. |
| T-Q044-04 | Tampering | migration/ORM/repository | mitigate | One linear additive migration, ORM parity, upgrade/downgrade/upgrade test, and expiration/reload assertions for all four fields. |
| T-Q044-05 | Information Disclosure | converter/tests | mitigate | Use local cutlet only; no source text leaves the process and tests make no provider/network calls. |
| T-Q044-06 | Denial of Service | cutlet conversion | accept | Inputs are already bounded card word/sentence strings and one converter instance is cached; no unbounded network or recursive processing is introduced. |
| T-Q044-07 | Repudiation | structural UI claim | mitigate | UI-PROOF records exact commands, observations, artifact/privacy metadata, result, and explicit native-Anki claim exclusion. |

</threat_model>

## Multi-Source Coverage Audit

| Source | ID | Feature / constraint | Coverage | Status |
|---|---|---|---|---|
| GOAL | — | Romaji inside existing Japanese frequency cards | Tasks 044-01..03 | COVERED |
| REQ | — | Roadmap/SPEC requirement IDs | N/A — quick task explicitly has no phase requirements and does not edit ROADMAP/SPEC | EXCLUDED |
| RESEARCH | — | cutlet 0.5.x, MIT, Modified Hepburn, fugashi/UniDic, foreign spelling switch | Task 044-02 dependency/service and tests | COVERED |
| CONTEXT | D-01 | Existing frequency identity; no third/reverse deck | ID/GUID locks and isolated/dynamic tests | COVERED |
| CONTEXT | D-02 | Canonical `romaji` and exact adjacency | Domain/isolated tuples, mappings, spelling scan | COVERED |
| CONTEXT | D-03 | Local cutlet; no pykakasi/LLM/provider | Service/dependency/offline tests | COVERED |
| CONTEXT | D-04 | Fail closed on blank/unresolved/raw output | Service + domain + assembly rejection tests | COVERED |
| CONTEXT | D-05 | Back-only secondary aid; preserve furigana/audio/Image | Template/model/APKG structural assertions and UI slot | COVERED |
| CONTEXT | D-06 | Persist old furigana plus new romaji in one migration | Task 044-03 migration/ORM/repository/expiry evidence | COVERED |
| CONTEXT | D-07 | Isolated/dynamic and APKG/CSV/TSV consistency | Tasks 044-01..02 field and artifact tests | COVERED |
| CONTEXT | D-08 | TDD, offline tests, narrow UI proof | RED gate, no-network boundaries, UI-PROOF contract | COVERED |
| DEFERRED | — | Standalone third deck / reverse-kana training | Explicit non-goals; absent from tasks | EXCLUDED |

## Final Verification

Authoritative focused regression:

```bash
uv run pytest tests/services/test_japanese_furigana.py tests/domain/test_exporting.py tests/services/test_japanese_frequency_deck.py tests/services/test_assemble_export_cards.py tests/services/test_card_template_loader.py tests/services/test_export_anki_package.py tests/services/test_export_tabular_bundle.py tests/repositories/test_export_repository.py tests/test_migration_schema_parity.py -q
```

Broad relevant regression (run once before edits in Task 044-01 and repeat with the identical node set after implementation; both runs must pass, otherwise stop rather than attributing failures to historical drift):

```bash
uv run pytest tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py tests/cli/test_export_command.py tests/integration/test_frequency_e2e_export_flow.py tests/integration/test_custom_word_list_e2e_export_flow.py -q
```

## Success Criteria

- `cutlet` resolves in the 0.5.x range and local exact-output/rejection tests pass without network calls.
- Both Japanese field constants equal the exact 12-field tuple and every non-Japanese constant remains unchanged.
- Dynamic assembly derives two romaji values once each, escapes them, and persists no row on invalid output.
- Isolated and dynamic generated notes/APKGs contain romaji in the same positions; Japanese CSV and TSV match those positions.
- The front has zero romaji references; the back has both in the required structural locations with all existing furigana/audio/Image references intact.
- Alembic has one head `20260804_16`; upgrade/downgrade/upgrade and ORM schema parity pass.
- Repository expiration/reload returns exact furigana and romaji values without recalculation.
- Existing model/deck/note IDs and GUID behavior remain stable.
- Focused regression passes, the identical broad relevant command passes both before and after edits, and UI-PROOF validates with native Anki visual acceptance explicitly outside the claim.

## Output

After execution, create `.planning/quick/044-romaji-frequencia-japones/044-SUMMARY.md`; do not update ROADMAP.md or SPEC.md.
