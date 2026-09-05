---
phase: 32-frequency-portuguese-text-and-audio
plan: "11"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 11 Summary

**Completed**: 2026-08-30
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: None. Work stayed inside the declared source/test/CLI/runtime write-set and did not perform package publication, live provider work, production DB writes, release, or Git actions.
**Decisions Made**: Registry scanning is deterministic and local: Python AST scanning for source, key-pattern scanning for JSON/YAML/TOML/CSV, and runtime/CLI export preflight before output mutation.
**Notes for Verification**: This proves remaining Japanese/Korean foundation ID migrations plus scanner/prewrite guard behavior. It does not prove Korean frequency packaging, observed Anki import/playback, production generation, live Azure/provider authority, or final full-suite closure.
**Notes for Next Work**: Later package/export plans can rely on `multilang check-anki-id-registry --production-roots` and `assert_anki_id_registry_clean(...)` to fail before creating destination outputs.

## Remaining Family Migrations

| Surface | Registry Keys | Identity Evidence |
|---|---|---|
| Japanese frequency | `japanese_frequency/model`, `japanese_frequency/deck` | model `1762800701`, deck `1762800702`, note type/fields/GUIDs unchanged |
| Japanese kana importer | `japanese_kana/model`, `japanese_kana/hiragana_deck`, `japanese_kana/katakana_deck` | model `1762800801`, decks `1762800802`/`1762800803`, split hierarchy/GUIDs unchanged |
| Japanese generated kana | consumes kana registry aliases through shared kana module | generated two-deck output path remains unchanged |
| Korean Hangul foundation | `korean_foundation/hangul_model`, `korean_foundation/hangul_deck` | model `1762801001`, deck `1762801002`, fields/tags/GUIDs/media unchanged |
| Korean pronunciation foundation | `korean_foundation/pronunciation_model`, `korean_foundation/pronunciation_deck` | model `1762801003`, deck `1762801004`, shared phoneme mechanics and Korean font CSS unchanged |
| Korean frequency reservation | `korean_frequency/model`, `parent_deck`, `level_1_deck`, `level_2_deck`, `level_3_deck` | remains distinct from foundation IDs; still reserved only, no packaging |

## Scanner Inventory

| Scanner Area | Behavior |
|---|---|
| Production roots | default command scans existing `src/multilang`, `scripts`, `data`, and `assets` roots |
| Exclusions | excludes tests, planning, build/private/cache/venv roots |
| Python source | inspects assignments, annotations, `registry_id(...)` keys, `genanki.Model(...)` dynamics, and registered literals outside the registry file |
| Data files | inspects JSON/YAML/TOML/CSV-like `model_id`/`deck_id` key patterns |
| Registry integrity | validates duplicate same-kind IDs, cross-kind collisions, unknown keys, unknown declarations, unused unreserved registrations, and reserved Korean frequency keys |
| Prewrite guard | `assert_anki_id_registry_clean(production_roots=True)` runs before runtime export and direct export CLI commands |
| Real command result | `multilang check-anki-id-registry --production-roots` scanned `195` files with `0` issues |

## Injected Violations

| Injection | Expected Result |
|---|---|
| registered model/deck literal in source | `direct_literal` issue |
| unknown `_MODEL_ID`/`_DECK_ID` literal assignment | `unknown_declaration` issue |
| `genanki.Model(model_id, ...)` without registry validation | `unchecked_dynamic` issue |
| data file `deck_id`/`model_id` literal | `data_literal` or `unknown_declaration` issue |
| unreserved registration with no source usage | `unused_registration` issue |
| prewrite failure with destination sentinel | raises before mutation and preserves sentinel bytes |
| export CLI with registry failure | exits non-zero before calling `export_job` and preserves output sentinel |

## TDD Evidence

- Task 32-11-01 RED: Japanese frequency/kana tests failed on local literals `1_762_800_701` and `1_762_800_801`.
- Task 32-11-01 GREEN: Japanese family migration passed `4 passed, 22 deselected`.
- Task 32-11-02 RED: Korean foundation registry-backed test failed on local literal `1_762_801_001`; the first broad filtered run timed out after showing the expected failure.
- Task 32-11-02 GREEN: Korean foundation migration passed `16 passed, 31 deselected`.
- Task 32-11-03 RED: scanner/CLI tests failed because `assert_anki_id_registry_clean`, `scan_anki_id_registry_paths`, and `AnkiIdRegistryScanResult` were missing.
- Task 32-11-03 GREEN: scanner/prewrite and CLI guard tests passed `6 passed, 3 deselected` and `2 passed, 4 deselected`.

## Verification

- Task 32-11-01 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py tests/services/test_japanese_frequency_deck.py -k 'id or registry or guid' -q` -> `4 passed, 22 deselected`.
- Task 32-11-02 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_foundation_export.py -k 'id or registry or guid or collision' -q` -> `16 passed, 31 deselected`.
- Task 32-11-03 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_anki_id_registry.py -k 'scanner or literal or config or dynamic or collision or reserved or prewrite' -q && UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_export_command.py -k 'registry or collision or output' -q` -> `6 passed, 3 deselected`; `2 passed, 4 deselected`.
- Required command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync multilang check-anki-id-registry --production-roots` -> `anki_id_registry_status=clean`, `scanned_files=195`, `issue_count=0`.
- Additional regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/cli/test_export_command.py -q` -> `6 passed`.
- Additional regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/test_runtime.py -q` -> `15 passed`.
- Additional regression passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_anki_id_registry.py tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py tests/services/test_japanese_frequency_deck.py -q` -> `35 passed`.
- Whitespace check passed: `git diff --check -- tests/services/test_anki_id_registry.py tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py tests/services/test_japanese_frequency_deck.py tests/services/test_korean_foundation_export.py tests/cli/test_export_command.py src/multilang/services/japanese_kana_deck.py src/multilang/services/japanese_kana_generated_deck.py src/multilang/services/japanese_frequency_deck.py src/multilang/services/korean_foundation_export.py src/multilang/services/anki_id_registry.py src/multilang/runtime.py src/multilang/cli.py`.
- Planning state update: `node .planning/bin/gsdd.mjs phase-status 32 in_progress` -> unchanged/open; `node .planning/bin/gsdd.mjs session-fingerprint write` -> `9a274f60643885df2493a42c809717786fe2fb862bab8bb3a3a24dd55bc56046`.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified remaining family registry migration, source-level literal removal, Korean foundation/frequency collision separation, injected scanner violations, real production-root scanner cleanliness, and prewrite export refusal. No network, provider, Azure, production DB, Korean frequency packaging, full-suite closure, Git, release, or publication action was performed.
</executor_check>
</checks>

<handoff>
plan_runtime: opencode
plan_assurance: self_checked
plan_check_status: passed
execution_runtime: opencode
execution_assurance: self_checked
executor_check_status: passed
hard_mismatches_open: false
</handoff>

<deltas>
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: An existing Korean foundation uniqueness test assumed AST literal declarations; after registry migration it was updated to validate the canonical registry and Korean foundation/frequency separation instead.
</deltas>

<judgment>
<active_constraints>
Phase 32 remains in progress and phase verification is pending. Plan 32-11 authorizes only ID-family migration plus local scanner/prewrite claims. Network, provider, Azure, production DB, real review approval, Korean frequency packaging, full-suite closure, export release, Git, and publication effects still require exact later authorities.
</active_constraints>
<unresolved_uncertainty>
Exact Phase 31 active snapshot output, NIKL rights/source facts, real 3000-entry inventory, source review, provider model/budget, live Azure catalog/synthesis, heard review outputs, production DB authority, final full-suite evidence, Anki import/playback proof, and publication approval remain unresolved checkpoint facts.
</unresolved_uncertainty>
<decision_posture>
All production Anki numeric IDs now live in the typed registry. Export-facing compatibility constants may remain, but they must be aliases from `registry_id(...)`; direct production literals and unchecked dynamic model IDs are scanner failures.
</decision_posture>
<anti_regression>
Do not weaken scanner coverage of `src/multilang`, `scripts`, `data`, and `assets`; tests/planning/build/private exclusions; duplicate/cross-kind registry validation; unknown key/declaration detection; registered literal detection; unchecked `genanki.Model(model_id, ...)` detection; unused unreserved registration detection; Korean foundation/frequency ID separation; or prewrite guard ordering before runtime/CLI export output mutation.
</anti_regression>
</judgment>
