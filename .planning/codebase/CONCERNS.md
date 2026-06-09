# Codebase Concerns

**Analysis Date:** 2026-06-09

## Tech Debt

**Broad test suite drift:**
- Issue: The full test suite is not currently authoritative; `python -m pytest -q --maxfail=10` stops with 10 failures after 164 passing tests, while focused Latin evidence passes (`89 passed`). The planning state also records full-suite drift as an active deferred item.
- Files: `tests/cli/test_generate_command.py`, `tests/integration/test_custom_word_list_e2e_export_flow.py`, `tests/integration/test_export_job_flow.py`, `tests/integration/test_v12_final_audit_evidence.py`, `tests/integration/test_v13_final_milestone_evidence.py`, `.planning/STATE.md`
- Impact: Future changes can hide regressions behind a known-red full suite. Existing-mode audio/export failures are especially risky because Latin v2.0 uses focused evidence and may not detect modern-language regressions.
- Fix approach: Restore the full-suite gate before treating milestone-wide evidence as complete. Start with `tests/cli/test_generate_command.py::test_generate_command_default_runtime_reports_audio_counters`, then repair audio artifact persistence/export failures in `tests/integration/test_custom_word_list_e2e_export_flow.py` and missing archived evidence paths in `tests/integration/test_v12_final_audit_evidence.py` and `tests/integration/test_v13_final_milestone_evidence.py`.

**Audio provider selection mismatch in existing modes:**
- Issue: Modern-language tests expecting Azure/fallback accounting now persist paths under an ElevenLabs provider directory, and generated files are missing at those persisted paths in full-suite failures.
- Files: `src/multilang/runtime.py`, `src/multilang/services/audio_synthesis.py`, `src/multilang/services/generate_audio_items.py`, `src/multilang/services/fallback_audio_adapter.py`, `tests/integration/test_custom_word_list_e2e_export_flow.py`
- Impact: Custom word-list and frequency exports can fail after text generation because audio rows reference missing media files. Export commands then fail before `.apkg`, CSV, or TSV artifacts are produced.
- Fix approach: Trace `_build_audio_adapter()` and `AudioSynthesisService.synthesize_prepared_asset()` under test settings to ensure the injected `AzureSpeechAdapter` is used and provider/format metadata matches the written file. Add a regression that asserts `AudioAssetModel.storage_path` exists immediately after generation for both word and sentence audio.

**Workflow delegate template missing:**
- Issue: The requested mapper contract file is absent, so mapper delegates cannot follow the documented `.planning/templates/delegates/mapper-concerns.md` entrypoint from disk.
- Files: `.planning/templates/delegates/mapper-concerns.md`, `.agents/skills/gsdd-map-codebase/SKILL.md`, `.planning/codebase/CONCERNS.md`
- Impact: Codebase mapping behavior depends on tool/global instructions rather than a committed repository template. Future runtimes may fail or produce inconsistent maps.
- Fix approach: Commit mapper delegate templates under `.planning/templates/delegates/` or update `.agents/skills/gsdd-map-codebase/SKILL.md` to point at the canonical template location that exists in the repository.

**Classical Latin contracts are split across domain and service modules:**
- Issue: Base Latin contracts in `src/multilang/domain/latin.py` contain only request/metadata models, while source-pack morphology, grammar labels, review statuses, audio statuses, and export row contracts live in service modules.
- Files: `src/multilang/domain/latin.py`, `src/multilang/services/latin_source_pack.py`, `src/multilang/services/latin_review.py`, `src/multilang/services/latin_audio.py`, `src/multilang/services/latin_export.py`
- Impact: Cross-module drift is likely as Latin scales beyond 50 cards. A new feature can update one service-level literal without updating the others, producing mismatched loader, review, audio, and export validation.
- Fix approach: Move stable Latin enums and DTOs into `src/multilang/domain/latin.py` and have service modules import them. Keep I/O loaders in `src/multilang/services/`, but centralize canonical statuses, case labels, source types, and field names.

## Known Bugs

**Fallback audio counter regression:**
- Symptoms: `tests/cli/test_generate_command.py::test_generate_command_default_runtime_reports_audio_counters` fails because CLI output omits the expected fallback audio counter line even when the test expects fallback accounting.
- Files: `tests/cli/test_generate_command.py`, `src/multilang/runtime.py`, `src/multilang/services/generate_audio_items.py`, `.planning/STATE.md`
- Trigger: Run `python -m pytest -q -x` from the repository root.
- Workaround: Use focused v2.0 Latin evidence for Latin-only work, but do not claim the complete suite is green until this test is repaired.

**Custom word-list audio artifact paths can point to missing files:**
- Symptoms: `tests/integration/test_custom_word_list_e2e_export_flow.py::test_custom_word_list_generates_audio_and_exports_all_formats` raises `FileNotFoundError` reading `AudioAssetModel.storage_path`.
- Files: `tests/integration/test_custom_word_list_e2e_export_flow.py`, `src/multilang/services/audio_synthesis.py`, `src/multilang/runtime.py`, `src/multilang/repositories/audio_repository.py`
- Trigger: Run `python -m pytest -q --maxfail=10`; the custom word-list E2E test fails after generation reports accepted text and processed audio.
- Workaround: No safe product workaround for user-facing export; repair persistence/provider selection before relying on custom word-list exports.

**Archived evidence tests reference missing planning artifacts:**
- Symptoms: v1.2/v1.3 final evidence tests fail with missing files under `.planning/phases/16-end-to-end-v12-audit/` and `.planning/phases/21-validation-fixtures-and-milestone-evidence/`.
- Files: `tests/integration/test_v12_final_audit_evidence.py`, `tests/integration/test_v13_final_milestone_evidence.py`, `.planning/phases/`, `.planning/milestones/`
- Trigger: Run the full suite or `python -m pytest -q --maxfail=10`.
- Workaround: Point these tests at archived milestone evidence under `.planning/milestones/` or restore the expected phase evidence artifacts.

## Security Considerations

**Local environment file present:**
- Risk: A `.env` file exists and is gitignored; it likely contains local environment configuration and may contain secrets. Its contents were not read.
- Files: `.env`, `.gitignore`, `src/multilang/settings.py`
- Current mitigation: `.gitignore` ignores `.env` and `.env.*`; settings are loaded through `SettingsConfigDict(env_file=".env")` in `src/multilang/settings.py`.
- Recommendations: Keep `.env` untracked, add or maintain a scrubbed `.env.example`, and include generated-document scans for common key/token patterns before committing `.planning/codebase/*.md`.

**Default runtime settings include local development connection defaults:**
- Risk: `src/multilang/settings.py` contains default connection/provider configuration for local development. Defaults are useful, but they can be mistaken for production-safe settings if deployed without environment overrides.
- Files: `src/multilang/settings.py`, `src/multilang/runtime.py`
- Current mitigation: Provider API keys are optional environment-backed fields and runtime adapters fail loudly when required credentials are absent.
- Recommendations: Add a production settings validator that rejects localhost/default database configuration and missing provider secrets when running non-local jobs.

**Latin source/privacy scanner is narrow:**
- Risk: Latin privacy checks scan a fixed token list and selected JSON/CSV/TSV surfaces; they may miss other local path formats, provider traces, long copied source pages, or generated artifacts outside the listed files.
- Files: `tests/integration/test_v20_final_milestone_evidence.py`, `src/multilang/services/latin_export.py`, `data/latin_mvp/latin-mvp-50-v1.json`, `data/latin_mvp/latin-mvp-50-v1-curation.json`, `data/latin_mvp/latin-mvp-50-v1-pt.json`, `data/latin_mvp/latin-mvp-50-v1-audio.json`
- Current mitigation: `test_final_milestone_privacy_and_source_safeguards` blocks common local paths and provider markers; `_public_source_text()` rejects selected provenance fragments.
- Recommendations: Centralize redaction/scanning in `src/multilang/security/redaction.py` or a dedicated artifact scanner, and run it over all committed source-pack, prompt, evidence, export, and planning artifacts.

## Performance Bottlenecks

**Full suite runtime and timeout risk:**
- Problem: `python -m pytest -q` exceeded 120 seconds before completion, and `python -m pytest -q --maxfail=10` took 141.75 seconds while stopping early.
- Files: `tests/`, `.planning/STATE.md`, `pyproject.toml`
- Cause: Integration-heavy tests exercise CLI/runtime/export flows repeatedly, and the known-red suite prevents normal fast feedback.
- Improvement path: Add focused markers for fast unit, focused milestone evidence, and slow integration suites in `pyproject.toml`; keep full suite green but allow developers to run a stable fast subset locally.

**Latin audio readiness checks read media bytes repeatedly:**
- Problem: Audio readiness validates each Latin storage path by resolving and reading the file header for every manifest check.
- Files: `src/multilang/services/latin_audio.py`, `data/latin_mvp/latin-mvp-50-v1-audio.json`
- Cause: `_storage_path_is_export_ready()` performs filesystem existence, size, and header reads per artifact.
- Improvement path: Keep this for 50-card MVP safety, but add cached media stat/header validation if scaling to 300/1000/3000 Latin cards.

## Fragile Areas

**Latin MVP assets are committed source-of-truth data:**
- Files: `data/latin_mvp/latin-mvp-50-v1.json`, `data/latin_mvp/latin-mvp-50-v1-curation.json`, `data/latin_mvp/latin-mvp-50-v1-pt.json`, `data/latin_mvp/latin-mvp-50-v1-audio.json`
- Why fragile: Loader invariants require exact item order, item keys, source-pack version, gate approval, and source/provenance alignment across four separate JSON files.
- Safe modification: Update source pack, curation, Portuguese translations, and audio manifest together; run `python -m pytest -q tests/services/test_latin_source_pack.py tests/services/test_latin_review.py tests/services/test_latin_translation_quality.py tests/services/test_latin_audio.py tests/services/test_latin_export.py`.
- Test coverage: Strong focused coverage exists, but full-suite drift means integration confidence outside Latin remains limited.

**Latin export note/template contract is inline Python:**
- Files: `src/multilang/services/latin_export.py`, `tests/services/test_latin_export.py`, `tests/integration/test_v20_latin_export_evidence.py`
- Why fragile: Field names, model IDs, CSS, front/back templates, and source rendering live in one service file; a small edit can change Anki behavior without a separate template fixture diff.
- Safe modification: Treat `LATIN_EXPORT_FIELD_NAMES`, `LATIN_NOTE_TYPE_NAME`, `LATIN_MODEL_ID`, and `build_latin_anki_model()` as a versioned contract. Add snapshot assertions for rendered front/back templates before modifying layout.
- Test coverage: Focused Latin export tests pass, but there is no real Anki Desktop import automation in the repository.

**Review gates depend on force semantics:**
- Files: `src/multilang/services/latin_review.py`, `src/multilang/cli.py`, `data/latin_mvp/latin-mvp-50-v1-curation.json`
- Why fragile: Approved gates can be overwritten only with `force`; mistaken use of force can silently alter curated approval state across all downstream exports.
- Safe modification: Preserve `update_latin_review_gate()` overwrite checks and add CLI audit output for any forced update. Require review artifact updates when force changes approved gates.
- Test coverage: Focused service tests cover gate protection; operational audit trails are limited to JSON contents and planning summaries.

## Scaling Limits

**Latin MVP is hard-coded to 50 cards:**
- Current capacity: 50 Latin MVP cards.
- Limit: `LATIN_MVP_CARD_COUNT`, source-pack literals, filenames, export paths, and tests are fixed around `latin-mvp-50-v1`.
- Files: `src/multilang/domain/latin.py`, `src/multilang/services/latin_source_pack.py`, `src/multilang/services/latin_audio.py`, `src/multilang/services/latin_export.py`, `data/latin_mvp/`
- Scaling path: Introduce versioned pack metadata with variable card count, generalized asset paths, and scale-specific validators before attempting 300-card or 3000-card Latin decks.

**Classical Latin TTS quality is approved only as an approximation:**
- Current capacity: 50-card MVP uses approved eSpeak NG `la` audio under a `classical_approx` pronunciation policy.
- Limit: Audio quality may not be acceptable for larger learner decks or stronger release claims.
- Files: `src/multilang/services/espeak_ng_speech_adapter.py`, `src/multilang/services/latin_audio.py`, `.planning/phases/27-latin-audio-policy-and-integrity/27-AUDIO-PLAYBACK-REVIEW.md`, `.planning/STATE.md`
- Scaling path: Add a new audio review artifact and provider policy before using Latin audio at larger scale or claiming native/high-quality Classical Latin pronunciation.

## Dependencies at Risk

**eSpeak NG native binary:**
- Risk: Latin sample synthesis depends on an external `espeak-ng` binary being installed and discoverable on PATH.
- Impact: Sample/audio generation can fail outside developer machines or CI images that include eSpeak NG.
- Files: `src/multilang/services/espeak_ng_speech_adapter.py`, `tests/services/test_espeak_ng_speech_adapter.py`, `data/latin_mvp/latin-mvp-50-v1-audio.json`
- Migration plan: Keep fake runner tests, document install requirements, and add a CI preflight that reports missing eSpeak NG separately from product test failures.

**Python/runtime version mismatch risk:**
- Risk: `pyproject.toml` allows Python `>=3.12`, while research warns CLTK 1.5 is compatible below Python 3.13 and CLTK 2.x requires Python 3.13. Test output shows execution on Python 3.13, so optional Latin NLP choices may drift from the documented baseline.
- Impact: Adding CLTK or morphology dependencies without pinning can force an unintended runtime migration or break Windows installs.
- Files: `pyproject.toml`, `.planning/research/STACK.md`, `.planning/research/ARCHITECTURE.md`
- Migration plan: Pin supported Python versions explicitly for each dependency set and keep Latin morphology tooling optional until a platform upgrade is planned.

## Missing Critical Features

**No production database migrations for Latin records:**
- Problem: Latin MVP uses committed JSON assets and service loaders rather than first-class persisted Latin card/source tables.
- Blocks: Multi-user review workflows, field-level regeneration, audit histories, and scaling beyond a frozen 50-card asset are difficult.
- Files: `data/latin_mvp/`, `src/multilang/services/latin_review.py`, `src/multilang/services/latin_source_pack.py`, `src/multilang/db/models.py`, `.planning/research/ARCHITECTURE.md`

**No automated real Anki import/playback evidence:**
- Problem: APKG generation is tested with genanki and static inspections, but learner-facing import/render/playback behavior still depends on manual evidence.
- Blocks: Strong release claims that exported decks display and play correctly in Anki Desktop across platforms.
- Files: `src/multilang/services/latin_export.py`, `tests/services/test_latin_export.py`, `tests/integration/test_v20_latin_export_evidence.py`

## Test Coverage Gaps

**Existing-mode runtime regressions are failing:**
- What's not tested: The intended invariant is tested, but currently red: modern frequency/custom exports with accepted text and media should produce successful APKG/CSV/TSV artifacts.
- Files: `tests/integration/test_export_job_flow.py`, `tests/integration/test_custom_word_list_e2e_export_flow.py`, `tests/integration/test_v20_existing_modes_regression_evidence.py`
- Risk: Latin changes can be merged while existing deck modes remain broken.
- Priority: High

**Secret/artifact scanning is not applied uniformly:**
- What's not tested: Generated planning maps and all generated evidence artifacts are not uniformly scanned by a single reusable scanner before commit.
- Files: `.planning/codebase/CONCERNS.md`, `.agents/skills/gsdd-map-codebase/SKILL.md`, `tests/integration/test_v20_final_milestone_evidence.py`, `src/multilang/security/redaction.py`
- Risk: Future generated documents may include local paths, provider traces, or secret-looking values.
- Priority: Medium

---

*Concerns audit: 2026-06-09*
