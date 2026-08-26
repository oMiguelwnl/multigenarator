---
phase: 31-hangul-and-pronunciation-i-plus-1
plan: "25"
runtime: opencode
assurance: self_checked
---

# Phase 31: Hangul and Pronunciation i+1 - Plan 25 Summary

**Completed**: 2026-08-26
**Tasks**: 3
**Git Actions**: None
**Deviations**: Two recoverable factual deltas occurred: the existing repository `.venv` is rejected by the new helper as `venv_unsafe`, and the user explicitly asked to fix a high-level export regression by allowing blank optional Hangul `Sound` fields without changing candidate assets.
**Decisions Made**: Keep public Korean foundation CLI commands unchanged, bind high-level fixtures to exact v2 current-candidate provenance, and preserve blocked production behavior until genuine evidence and activation exist.

## Completed Work

- Added `scripts/verify_phase31_runtime_isolation.py` with two fixed operations: `prepare` for `/tmp/multilang-phase31-py312` and `hash-venv` for repository `.venv`.
- Added `tests/services/test_phase31_runtime_isolation.py` covering fixed operation names, safe direct-child creation, root-owned/sticky `/tmp` checks, unsafe child/link/mode rejection, absent `.venv`, deterministic recursive mode/content hashing, and content-free CLI errors.
- Migrated high-level Korean foundation CLI/integration tests to exact v2 candidate pointer, bundle member, request, snapshot member, and pre-first-activation GUID expectations.
- Added assertions that production defaults refuse with exact scanner-safe output and create no requested export output before evidence/activation.
- Fixed the discovered high-level v2 export regression by allowing `HangulExportRow.sound` to be blank when the source `sound` is `None`, while keeping `reading_or_name` and `mnemonic` mandatory.

## Verification

- RED runtime helper: `set +e; OUTPUT="$(UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_phase31_runtime_isolation.py::test_runtime_isolation_contract_is_not_implemented -q 2>&1)"; STATUS=$?; set -e; test "$STATUS" -eq 1 && case "$OUTPUT" in *AssertionError*|*assert*) ;; *) exit 1 ;; esac` passed before helper implementation.
- Runtime helper: `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_phase31_runtime_isolation.py -q` -> 12 passed.
- Runtime prepare: `UV_OFFLINE=1 uv run python scripts/verify_phase31_runtime_isolation.py prepare` -> `operation=prepare`, `path=/tmp/multilang-phase31-py312`, `status=ready`, `mode=0700`.
- Real shared `.venv` probe before and after the matrix: `UV_OFFLINE=1 uv run python scripts/verify_phase31_runtime_isolation.py hash-venv` -> `runtime_isolation_error=venv_unsafe` both times; no repair was attempted.
- RED Hangul blank sound regression: `set +e; OUTPUT="$(UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_export.py::test_hangul_row_allows_blank_optional_sound_but_requires_core_copy -q 2>&1)"; STATUS=$?; set -e; test "$STATUS" -eq 1 && case "$OUTPUT" in *learner_copy_missing*|*Failed*|*ValueError*) ;; *) exit 1 ;; esac` passed before export fix.
- Targeted fixed flow: `UV_OFFLINE=1 uv run --extra dev pytest tests/integration/test_korean_foundations_flow.py::test_complete_cli_flow_through_active_provenance_and_all_six_exports -q` -> 1 passed.
- Export suite: `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_korean_foundation_export.py -q` -> 46 passed.
- CLI suite: `UV_OFFLINE=1 uv run --extra dev pytest tests/cli/test_korean_foundation_commands.py -q` -> 58 passed.
- Integration suite: `UV_OFFLINE=1 uv run --extra dev pytest tests/integration/test_korean_foundations_flow.py -q` -> 20 passed.
- High-level combined: `UV_OFFLINE=1 uv run --extra dev pytest tests/cli/test_korean_foundation_commands.py tests/integration/test_korean_foundations_flow.py -q` -> 78 passed.
- Exact refusal command: `assert_refusal "korean_foundations_error=inbox_incomplete" ... inspect-inbox && ... check --family hangul && ... check --family pronunciation && ... export --family hangul --format apkg --output /tmp/multilang-phase31-refusal-hangul.apkg && test ! -e /tmp/multilang-phase31-refusal-hangul.apkg` passed.
- Phase 30 focused matrix: `UV_OFFLINE=1 uv run --extra dev pytest tests/domain/test_jobs.py tests/test_settings.py tests/services/test_frequency_decks.py tests/services/test_audio_voice_registry.py tests/services/test_tatoeba_sentence_source.py tests/domain/test_korean.py tests/services/test_korean_morphology.py tests/services/test_korean_language_support.py tests/domain/test_lexicon.py tests/services/test_lexical_lookup.py tests/services/test_word_list_parser.py tests/services/test_input_fingerprint.py tests/repositories/test_lexical_repository.py tests/test_migration_schema_parity.py tests/services/test_lexical_grounding.py tests/services/test_highlight_candidate_extraction.py tests/services/test_highlight_import_preview.py tests/services/test_highlight_ingest_lexical_items.py tests/services/test_text_generation.py tests/services/test_provider_text_adapters.py tests/services/test_text_validation.py tests/services/test_generate_text_items.py tests/services/test_regenerate_text_item.py tests/test_runtime.py tests/cli/test_kindle_highlight_preview_command.py tests/cli/test_webdav_highlight_commands.py tests/integration/test_korean_modern_flow.py -q` -> 467 passed, 10 existing Alembic deprecation warnings.
- Existing-mode integration matrix: `UV_OFFLINE=1 uv run --extra dev pytest tests/integration/test_frequency_e2e_export_flow.py tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_highlight_generation_audio_flow.py tests/integration/test_v13_existing_modes_regression_evidence.py tests/services/test_japanese_furigana.py tests/services/test_assemble_export_cards.py::test_assemble_export_cards_builds_japanese_row_without_ipa tests/integration/test_mandarin_modern_flow.py tests/integration/test_v21_latin_google_tts_final_audio.py tests/services/test_russian_phoneme_deck.py -q` -> 38 passed.
- Phase 31 foundation service matrix: `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_phase31_runtime_isolation.py tests/services/test_korean_curriculum.py tests/services/test_korean_foundation_review.py tests/services/test_korean_foundation_media.py tests/services/test_korean_foundation_evidence.py tests/services/test_korean_foundation_snapshot.py tests/services/test_korean_foundation_export.py -q` -> 328 passed.
- Kana/phoneme/template group: `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_japanese_kana_deck.py tests/services/test_japanese_kana_generated_deck.py tests/services/test_phoneme_deck.py tests/services/test_russian_phoneme_deck.py tests/services/test_card_template_loader.py tests/integration/test_russian_phoneme_template_refresh_flow.py -q` -> 67 passed.
- Latin group: `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_latin_source_pack.py tests/services/test_latin_export.py tests/services/test_latin_audio.py tests/integration/test_v20_latin_mode_isolation_evidence.py tests/integration/test_v20_latin_export_evidence.py tests/integration/test_v21_latin_google_tts_final_audio.py -q` -> 78 passed.
- Mandarin group: `UV_OFFLINE=1 uv run --extra dev pytest tests/services/test_mandarin_language_support.py tests/services/test_mandarin_orthography.py tests/integration/test_mandarin_modern_flow.py -q` -> 28 passed.
- Protected-output absence: no `/tmp/multilang-phase31-refusal-hangul.apkg`, no `data/korean_foundations/validation-receipt.json`, no `data/korean_foundations/active-foundations.json`, and no `.multilang/exports/korean-foundations` after verification.
- `git diff --check` passed.

## Notes For Verification

- Claim limit: v2 migration regression safety, fixed runtime helper behavior, and blocked production only.
- No canonical validation receipt, canonical snapshot, active pointer, export artifact, review approval, rights disposition, playback evidence, provider call, database call, or production readiness was created or claimed.
- The helper rejects the existing repository `.venv` as `venv_unsafe`; this plan intentionally did not repair or mutate `.venv`.

## Notes For Next Work

- Plan 31-26 remains the genuine evidence checkpoint and must not infer approvals from v2 candidates or temporary fixtures.
- Plan 31-27/31-28 still own the canonical receipt, inactive snapshot, authorization, activation, and local exports.
- If later plans require a real repository `.venv` hash instead of the isolated `/tmp/multilang-phase31-py312` path, they must address the current `venv_unsafe` state explicitly without silent repair.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified runtime helper RED/GREEN, user-directed Hangul blank-sound fix RED/GREEN, high-level Korean CLI/integration, exact refusal output, focused existing-mode matrices, protected-output absence, and diff whitespace checks.
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
  summary: The existing repository `.venv` is rejected by the helper as `venv_unsafe`; the plan did not require or permit repairing shared `.venv`, and all regression commands ran offline without mutating canonical outputs.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: Exact v2 Hangul contains 27 `sound: null` rows, so current high-level exports failed while row copy otherwise remained present. The user explicitly requested the error be fixed, and export now permits blank Hangul `Sound` while keeping `reading_or_name` and `mnemonic` mandatory.
</deltas>

<judgment>
<active_constraints>
- Public `korean-foundations` command names and options remain unchanged.
- Production defaults remain blocked before genuine evidence, canonical receipt, active pointer, and exports.
- No provider, network, LLM, TTS, Azure, database, approval, activation, canonical evidence, snapshot, export, or candidate/request mutation work occurred in this plan.
- The fixed runtime-isolation helper creates or verifies only `/tmp/multilang-phase31-py312` and hashes only repository `.venv`.
</active_constraints>
<unresolved_uncertainty>
- Genuine qualified reviews, Portuguese policy, rights dispositions, exact media, playback evidence, canonical receipt, inactive snapshot, activation, local exports, and observed Anki acceptance remain unresolved.
- Existing repository `.venv` cannot currently produce a helper tree hash because it is reported as `venv_unsafe`.
</unresolved_uncertainty>
<decision_posture>
- Keep exact v2 current-candidate provenance as the high-level default while preserving explicit v1 history only.
- Treat Hangul `Sound` as optional learner copy in export rows; keep core display/mnemonic copy and required media strict.
- Treat isolated `/tmp/multilang-phase31-py312` as the safe later closure path rather than repairing shared `.venv` in this plan.
</decision_posture>
<anti_regression>
- CLI/integration fixtures must keep exact v2 pointer/member/request/snapshot/GUID bindings and no provider construction.
- Missing inbox, receipt, active pointer, and export readiness must continue to fail with exact scanner-safe `korean_foundations_error=...` output and zero output creation.
- `reading_or_name` and `mnemonic` remain mandatory for Hangul export rows; optional missing `sound` must export as an empty `Sound` field only.
- Runtime isolation must reject unsafe `/tmp` or environment child state without cleanup/repair and must not accept arbitrary paths.
- Future work must not treat temporary integration activation/export fixtures as production approval or learner-ready evidence.
</anti_regression>
</judgment>
