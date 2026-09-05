---
phase: 32-frequency-portuguese-text-and-audio
plan: "10"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 10 Summary

**Completed**: 2026-08-30
**Tasks**: 3
**Git Actions**: None; commit not requested.
**Deviations**: None. The registry records the full current ID baseline, while only the plan-declared first-family consumers were migrated; Japanese/kana and Korean foundation declarations remain untouched because they were outside this plan's write-set.
**Decisions Made**: Use `AnkiIdKind` plus family/role lookup as the typed numeric authority. Keep legacy exported constants as compatibility aliases resolved from the registry in migrated modules.
**Notes for Verification**: This plan proves numeric registry integrity and no drift for core, Latin, Russian, Polish, Greek, and shared phoneme constructors. It does not package Korean frequency decks, replace note GUID formulas, run observed Anki import/playback, or migrate out-of-write-set Japanese/kana/Korean foundation consumers.
**Notes for Next Work**: Future family migrations should replace remaining local numeric declarations with registry aliases and keep the same source-level no-local-literal tests.

## ID Inventory

| Family | Role | Kind | Value |
|---|---|---|---|
| core | frequency_model | model | 1602300501 |
| core | export_deck | deck | 1602300502 |
| core | manual_model | model | 1602300503 |
| core | highlight_model | model | 1602300504 |
| phoneme | russian_model | model | 1602300601 |
| phoneme | russian_deck | deck | 1602300602 |
| phoneme | polish_model | model | 1602300603 |
| phoneme | polish_deck | deck | 1602300604 |
| phoneme | greek_model | model | 1602300605 |
| phoneme | greek_deck | deck | 1602300606 |
| latin | mvp_model | model | 1602300701 |
| latin | mvp_deck | deck | 1602300702 |
| japanese_frequency | model | model | 1762800701 |
| japanese_frequency | deck | deck | 1762800702 |
| japanese_kana | model | model | 1762800801 |
| japanese_kana | hiragana_deck | deck | 1762800802 |
| japanese_kana | katakana_deck | deck | 1762800803 |
| mandarin | card_model | model | 1762800901 |
| korean_foundation | hangul_model | model | 1762801001 |
| korean_foundation | hangul_deck | deck | 1762801002 |
| korean_foundation | pronunciation_model | model | 1762801003 |
| korean_foundation | pronunciation_deck | deck | 1762801004 |
| korean_frequency | model | model | 1762801101 |
| korean_frequency | parent_deck | deck | 1762801102 |
| korean_frequency | level_1_deck | deck | 1762801103 |
| korean_frequency | level_2_deck | deck | 1762801104 |
| korean_frequency | level_3_deck | deck | 1762801105 |

## Migration Matrix

| Surface | Before | After | Drift Evidence |
|---|---|---|---|
| `export_anki_package.py` | local literals for core/manual/highlight/Mandarin model IDs and deck ID | aliases resolved from `registry_id(...)` | focused export tests passed; no local first-family literals remain |
| `latin_export.py` | local literals for Latin model/deck IDs | aliases resolved from `registry_id(...)` | focused Latin tests passed; APKG model/deck contracts unchanged |
| `russian_phoneme_deck.py` | local literals for Russian/Polish/Greek model/deck IDs | aliases resolved from `registry_id(...)` | focused phoneme tests passed; inventory/template/GUID hashes unchanged |
| `phoneme_deck.py` | accepted any raw model ID | requires registered model ID before `genanki.Model` construction | unregistered ID test fails closed; registered Korean pronunciation ID remains accepted |

## TDD Evidence

- Task 32-10-01 RED: `tests/services/test_anki_id_registry.py` failed with `ModuleNotFoundError: No module named 'multilang.services.anki_id_registry'`.
- Task 32-10-01 GREEN: registry implementation passed `5 passed`.
- Task 32-10-02 RED: core export source-level test failed on local literal `1_602_300_501`; Latin source-level test failed on local literal `1_602_300_701`.
- Task 32-10-02 GREEN: core/Latin focused commands passed `7 passed, 23 deselected` and `2 passed, 10 deselected`.
- Task 32-10-03 RED: Russian source-level test failed on local literal `1_602_300_601`; neutral phoneme model test failed because unregistered raw ID did not raise.
- Task 32-10-03 GREEN: Russian/shared phoneme focused commands passed `1 passed, 13 deselected` and `5 passed, 6 deselected`.

## Verification

- Task 32-10-01 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_anki_id_registry.py -k 'baseline or declaration or duplicate or cross_kind or korean_frequency' -q` -> `5 passed`.
- Task 32-10-02 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_export_anki_package.py -k 'registry or id or guid' -q && UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_latin_export.py -k 'id or registry or guid' -q` -> `7 passed, 23 deselected`; `2 passed, 10 deselected`.
- Task 32-10-03 command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_russian_phoneme_deck.py -k 'id or registry or guid' -q && UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_phoneme_deck.py -k 'id or registry or guid' -q` -> `1 passed, 13 deselected`; `5 passed, 6 deselected`.
- Regression command passed: `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_anki_id_registry.py tests/services/test_export_anki_package.py tests/services/test_latin_export.py tests/services/test_russian_phoneme_deck.py tests/services/test_phoneme_deck.py -q` -> `72 passed`.
- Whitespace check passed: `git diff --check -- tests/services/test_anki_id_registry.py tests/services/test_export_anki_package.py tests/services/test_latin_export.py tests/services/test_russian_phoneme_deck.py tests/services/test_phoneme_deck.py src/multilang/services/anki_id_registry.py src/multilang/services/export_anki_package.py src/multilang/services/latin_export.py src/multilang/services/russian_phoneme_deck.py src/multilang/services/phoneme_deck.py`.
- Planning state update: `node .planning/bin/gsdd.mjs phase-status 32 in_progress` -> unchanged/open; `node .planning/bin/gsdd.mjs session-fingerprint write` -> `7be1e1733dd4a87470f76d95cfdb621f80d9af1830f4bf7260de2e0b4abbec8a`.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified the complete registry baseline, duplicate/cross-kind failure behavior, Korean frequency reservation, first-family source migration, and unchanged focused export/phoneme identities. No network, provider, production DB, Git, release, publication, Korean frequency packaging, or observed Anki action was performed.
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
  summary: The plan's write-set permitted first-family migration only, so Japanese frequency/kana and Korean foundation values are registered as baseline authority but their existing local declarations were not edited in this plan.
</deltas>

<judgment>
<active_constraints>
Phase 32 remains in progress and phase verification is pending. Plan 32-10 authorizes only numeric ID registry and first-family migrations. Network, provider, Azure, production DB, real review approval, full-suite closure, Korean frequency packaging, export release, Git, and publication effects still require exact later authorities.
</active_constraints>
<unresolved_uncertainty>
Exact Phase 31 active snapshot output, NIKL rights/source facts, real 3000-entry inventory, source review, provider model/budget, live Azure catalog/synthesis, heard review outputs, production DB authority, final full-suite evidence, Anki import/playback proof, and publication approval remain unresolved checkpoint facts.
</unresolved_uncertainty>
<decision_posture>
Keep numeric Anki IDs behind typed family/role/kind registry lookups. Preserve exported compatibility constants as aliases during incremental family migration; do not invent replacement IDs on collision.
</decision_posture>
<anti_regression>
Do not weaken registry duplicate/cross-kind validation, Korean frequency reserved IDs `1762801101` through `1762801105`, migrated source-level no-local-literal coverage, existing core/Latin/Russian/Polish/Greek model/deck values, existing field order, template hashes, media behavior, or GUID formulas.
</anti_regression>
</judgment>
