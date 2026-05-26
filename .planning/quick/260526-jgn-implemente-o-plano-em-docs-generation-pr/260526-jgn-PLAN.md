---
quick_id: 260526-jgn
type: execute
wave: 1
depends_on: []
autonomous: true
files_modified:
  - src/multilang/domain/exporting.py
  - src/multilang/domain/jobs.py
  - src/multilang/repositories/job_repository.py
  - src/multilang/runtime.py
  - src/multilang/cli.py
  - src/multilang/services/assemble_export_cards.py
  - src/multilang/services/generation_report.py
  - src/multilang/services/text_validation.py
  - src/multilang/services/provider_text_adapters.py
  - src/multilang/domain/deck_audit.py
  - src/multilang/services/deck_audit_reader.py
  - src/multilang/services/deck_audit_reports.py
  - tests/services/test_assemble_export_cards.py
  - tests/services/test_text_validation.py
  - tests/services/test_provider_text_adapters.py
  - tests/cli/test_export_command.py
  - tests/cli/test_audit_deck_command.py
  - tests/domain/test_deck_audit.py
  - tests/integration/test_frequency_e2e_export_flow.py
requirements:
  - QUICK-260526-jgn
must_haves:
  truths:
    - "A frequency APKG export is blocked by default unless it has exactly 3000 cards split into 1000 cards per level, with zero review_required items, invalid translations, missing media, or non-synthesized audio."
    - "Partial export is possible only when the operator explicitly passes --allow-partial, and the job/export/report clearly record the warning state."
    - "Jobs no longer report completed when accepted/exportable items are fewer than total planned items; review_required items count as blocking, not completed product output."
    - "Translations that contain Error 500, HTML, quota/captcha/server-error/request-blocked text are rejected before acceptance/export."
    - "DeepL quota exhaustion does not silently fall back to Google Translate for final decks."
    - "audit-deck returns non-zero for blocking deck problems: incomplete frequency deck, invalid translations, duplicates, and missing media references."
    - "Each successful export writes generation-report.json and generation-report.md derived from current persisted job/export/card/audio/text state."
  artifacts:
    - path: "src/multilang/domain/exporting.py"
      provides: "export quality gate contracts and blocking issue result types"
    - path: "src/multilang/runtime.py"
      provides: "pre-export gate enforcement, --allow-partial handling, status updates, report generation hook"
    - path: "src/multilang/services/generation_report.py"
      provides: "per-job JSON/Markdown final generation report writer"
    - path: "src/multilang/services/text_validation.py"
      provides: "invalid translation rejection patterns"
    - path: "src/multilang/services/provider_text_adapters.py"
      provides: "no silent Google fallback after DeepL quota/provider failure"
    - path: "src/multilang/domain/deck_audit.py"
      provides: "expanded deck audit issue taxonomy and detectors"
    - path: "src/multilang/services/deck_audit_reader.py"
      provides: "APKG media manifest/reference metadata for audits"
    - path: "tests/integration/test_frequency_e2e_export_flow.py"
      provides: "regression coverage for blocked partial exports and complete export reporting"
  key_links:
    - from: "src/multilang/cli.py"
      to: "src/multilang/runtime.py"
      via: "export command passes allow_partial to export_job"
      pattern: "allow_partial"
    - from: "src/multilang/runtime.py"
      to: "src/multilang/services/generation_report.py"
      via: "successful export writes final report"
      pattern: "write_generation_report"
    - from: "src/multilang/services/text_validation.py"
      to: "src/multilang/services/generate_text_items.py"
      via: "existing TextValidationService validation result drives review_required/accepted records"
      pattern: "TRANSLATION_MISMATCH"
    - from: "src/multilang/cli.py"
      to: "src/multilang/domain/deck_audit.py"
      via: "audit-deck exits non-zero when blocking issues are found"
      pattern: "issue_count"
---

<objective>
Implement the focused quality gates from `docs/generation-process-improvement-plan.md` using `docs/polish-deck-generation-analysis-2a7473ce.md` as failure evidence.

Purpose: prevent another technically successful but incomplete/invalid APKG from being marked as a final deck.
Output: export gating, accurate job/export status, invalid-translation blocking, no silent DeepL→Google degradation, expanded audit-deck checks, final generation reports, and regression tests.
</objective>

<execution_context>
@$HOME/.config/opencode/get-shit-done/workflows/execute-plan.md
@$HOME/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@AGENTS.md
@docs/generation-process-improvement-plan.md
@docs/polish-deck-generation-analysis-2a7473ce.md
@src/multilang/domain/exporting.py
@src/multilang/domain/jobs.py
@src/multilang/repositories/job_repository.py
@src/multilang/runtime.py
@src/multilang/cli.py
@src/multilang/services/assemble_export_cards.py
@src/multilang/services/text_validation.py
@src/multilang/services/provider_text_adapters.py
@src/multilang/domain/deck_audit.py
@src/multilang/services/deck_audit_reader.py
@src/multilang/services/deck_audit_reports.py

<interfaces>
Existing export/runtime contracts to preserve and extend:

```python
class ExportArtifactStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class ExportCardRow(BaseModel):
    identity: ExportCardIdentity
    sort_index: int | None = Field(default=None, alias="SortIndex")
    word: str = Field(min_length=1, alias="word")
    definitions: str = Field(min_length=1, alias="Definitions")
    example_sentence: str = Field(min_length=1, alias="Example Sentence")
    translation: str = Field(default="", alias="Translation")
    word_audio: str = Field(default="", alias="word_audio")
    sentence_audio: str = Field(default="", alias="sentence_audio")

class RuntimeGenerateService(...):
    def export_job(self, *, job_id: str, export_format: ExportArtifactFormat, output_dir: Path,
                   deck_name: str | None = None, refresh_snapshots: bool = False) -> RuntimeExportResult: ...

class TextValidationService:
    def validate(..., require_translation: bool = True, ...) -> TextValidationResult: ...

def read_apkg_cards(path: Path) -> DeckAuditReadResult: ...
def detect_card_issues(card: AuditCard) -> list[AuditIssue]: ...
def write_deck_audit_reports(read_result: DeckAuditReadResult, issues: list[AuditIssue], output_dir: Path) -> DeckAuditReportResult: ...
```

Existing CLI points:
```python
multilang export --job-id JOB_ID --format apkg [--refresh-snapshots]
multilang audit-deck --input-apkg PATH --output-dir DIR
```

Add `--allow-partial` to export. If adding `multilang report --job-id JOB_ID` is low-touch after `generation_report.py` exists, add it; otherwise the mandatory behavior is automatic report generation after successful export.
</interfaces>
</context>

<source_audit>
## Multi-Source Coverage Audit

| Source | Item | Coverage |
|---|---|---|
| GOAL | Fix generation process so incomplete/invalid Polish APKG cannot be accepted as production final | Tasks 1-3 |
| REQ | Block partial export by default; allow only explicit `--allow-partial` | Task 1 |
| REQ | Correct job status and counters; review_required is blocking | Task 1 |
| REQ | Reject translations like `Error 500`, HTML, quota/captcha/server error/request blocked | Task 2 |
| REQ | Remove silent Google fallback when DeepL exceeds quota | Task 2 |
| REQ | Expand audit-deck for incomplete deck, invalid translations, duplicates, missing media | Task 3 |
| REQ | Add final generation report per job | Task 1 |
| REQ | Add regression tests for all listed failures | Tasks 1-3 |
| CONTEXT | Do not implement complete all-language curation | Excluded by user constraint; do not add curation pipeline |
| CONTEXT | Do not migrate to PostgreSQL/queue in this step | Excluded by user constraint; keep current DB/runtime architecture |
| RESEARCH | Preserve Python/uv/Pydantic/pytest architecture and export contract | Tasks use existing Python modules/tests |
</source_audit>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Fail closed on incomplete export and write final job report</name>
  <files>src/multilang/domain/exporting.py, src/multilang/domain/jobs.py, src/multilang/repositories/job_repository.py, src/multilang/runtime.py, src/multilang/cli.py, src/multilang/services/assemble_export_cards.py, src/multilang/services/generation_report.py, tests/services/test_assemble_export_cards.py, tests/cli/test_export_command.py, tests/integration/test_frequency_e2e_export_flow.py</files>
  <behavior>
    - Exporting a full frequency job without `--allow-partial` fails before writing APKG/CSV/TSV if card snapshots do not contain exactly 3000 cards, levels 1/2/3 do not each contain 1000 cards, review_required text records exist, invalid translations exist, required audio is absent, or audio status is not `synthesized`.
    - Error text lists per-level deficits, e.g. `level_3 missing 260 cards`, and includes blocking counts.
    - `multilang export --allow-partial` bypasses only the count/review gate, still never exports invalid translations or missing/non-synthesized audio, and records an explicit partial/warning export status/message.
    - Job status is `completed` only when final quality gates pass; blocked/partial/warning states are not shown as clean completion.
    - Successful export writes `generation-report.json` and `generation-report.md` next to the export artifact or under a deterministic job report directory, with job id, language, source type, total/accepted/review_required/failed counts, per-level card counts, export path, card count, APKG hash when applicable, provider counts available from text/audio provenance, and blocking/warning summaries.
  </behavior>
  <action>Define small domain objects/functions for export quality gate results in `domain/exporting.py` instead of burying ad-hoc checks in CLI. Extend `RuntimeGenerateService.export_job(..., allow_partial: bool = False)` and CLI `export --allow-partial`; update existing fake test services to match the new signature. Use persisted job/source_type plus card row identities/lexical candidate frequency_level or item_key pattern to compute expected frequency counts. Add repository methods only as needed to count text records by review/validation status and to update final job status; do not add migrations unless the existing SQLite models already tolerate the enum string values. Add `services/generation_report.py` to derive reports from current repositories after export. Do not implement PostgreSQL, queues, full provider telemetry, or all-language curation in this task.</action>
  <verify>
    <automated>uv run pytest tests/cli/test_export_command.py tests/services/test_assemble_export_cards.py tests/integration/test_frequency_e2e_export_flow.py -q</automated>
  </verify>
  <done>Default export blocks the documented `2740/3000` style failure; explicit partial export is visible as partial/warning; clean complete export writes report files and has consistent job/export status.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Reject invalid translations and remove silent DeepL-to-Google degradation</name>
  <files>src/multilang/services/text_validation.py, src/multilang/services/provider_text_adapters.py, src/multilang/runtime.py, tests/services/test_text_validation.py, tests/services/test_provider_text_adapters.py</files>
  <behavior>
    - Translation text containing `Error 500`, `Server Error`, `That's an error`, raw HTML, quota-exceeded text, captcha text, request-blocked text, or obvious provider/system error pages returns `ValidationStatus.FAILED` with `ValidationFlagCode.TRANSLATION_MISMATCH`.
    - `DeepLTranslationAdapter` failures due to quota/auth/rate/server/provider errors are raised to the job layer instead of silently using Google Translate.
    - `GoogleTranslateAdapter` is still usable only when the operator explicitly configures `MULTILANG_TRANSLATION_PROVIDER=google`; it is not an implicit fallback for DeepL final deck generation.
    - If a controlled fallback remains for non-final/local smoke paths, provenance must make fallback visible and the resulting translation still passes the invalid-translation detector before acceptance.
  </behavior>
  <action>Add deterministic invalid-translation helpers in `text_validation.py` and reuse them anywhere export/audit needs the same pattern. Remove `FallbackTranslationAdapter(primary=DeepLTranslationAdapter, fallback=GoogleTranslateAdapter())` from `_build_translation_adapter`; for `translation_provider == "deepl"`, return DeepL directly and let quota/provider exceptions block/resume rather than corrupt content. Keep explicit `translation_provider == "google"` behavior if existing settings/tests depend on it, but do not use it automatically after DeepL quota. Add unit tests using the exact Polish failure string from `docs/polish-deck-generation-analysis-2a7473ce.md`.</action>
  <verify>
    <automated>uv run pytest tests/services/test_text_validation.py tests/services/test_provider_text_adapters.py -q</automated>
  </verify>
  <done>`Error 500 (Server Error)!!1500.That's an error...` and HTML/quota/captcha/server-error strings cannot be accepted, and DeepL quota errors do not create Google fallback translations invisibly.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Expand audit-deck into a blocking package-quality audit</name>
  <files>src/multilang/domain/deck_audit.py, src/multilang/services/deck_audit_reader.py, src/multilang/services/deck_audit_reports.py, src/multilang/cli.py, tests/domain/test_deck_audit.py, tests/cli/test_audit_deck_command.py</files>
  <behavior>
    - `audit-deck` detects incomplete frequency decks: total not 3000 or level counts inferred from SortIndex/item tags are not 1000/1000/1000.
    - `audit-deck` detects invalid translations using the same patterns from Task 2.
    - `audit-deck` detects duplicate words/lemmas/examples/translations, at minimum exact normalized duplicates across exported notes.
    - `audit-deck` detects missing media: every `[sound:...]` reference in `word_audio` and `sentence_audio` fields must map to a media member in the APKG.
    - `audit-deck` exits non-zero when blocking issues exist, while still writing JSON/Markdown reports with issue_count and normalized issue types.
  </behavior>
  <action>Extend `DeckAuditReadResult` to include APKG media manifest information and sound references without mutating packages. Expand `AuditIssueType` with bounded values such as `INCOMPLETE_DECK`, `INCOMPLETE_LEVEL`, `INVALID_TRANSLATION`, `DUPLICATE_FIELD`, and `MISSING_MEDIA`; keep existing definition detectors intact. Add a package-level audit function that can inspect all cards plus read metadata, while `detect_card_issues(card)` may remain as a per-card helper. Update `cli.audit_deck` to run the package audit and return exit code 1 when any issue has severity `error`; reports must still be written before exiting. Do not add full language curation or PostgreSQL/queue work.</action>
  <verify>
    <automated>uv run pytest tests/domain/test_deck_audit.py tests/cli/test_audit_deck_command.py -q</automated>
  </verify>
  <done>audit-deck catches the documented Polish APKG failure classes: `2740/3000`, invalid `Error 500` translations, duplicates, and missing media references, and fails closed via non-zero exit.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Provider output → text validation/export | Untrusted translation/provider responses may contain HTML/error pages and must not become study content. |
| Persisted DB rows → APKG export | Stale or inconsistent accepted/review/audio rows must be revalidated before package creation. |
| APKG input → audit-deck reader | User-supplied ZIP/SQLite package may contain malformed paths, missing media, or unexpected fields. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|---|---|---|---|---|
| T-260526-jgn-01 | Tampering | `runtime.export_job` | mitigate | Recompute quality gates from persisted rows immediately before writing export artifacts. |
| T-260526-jgn-02 | Information Disclosure | `deck_audit_reports.py` | mitigate | Keep evidence bounded with existing `_bounded` behavior; do not dump full private deck contents into reports. |
| T-260526-jgn-03 | Denial of Service | `deck_audit_reader.py` | accept | Existing audit reads local APKG via temp extraction; keep path traversal checks and no network calls. |
| T-260526-jgn-04 | Spoofing/Tampering | Translation providers | mitigate | Treat provider error pages/system messages as invalid content and block export. |
</threat_model>

<verification>
Run focused regression suite after all tasks:

```bash
uv run pytest tests/cli/test_export_command.py tests/services/test_assemble_export_cards.py tests/services/test_text_validation.py tests/services/test_provider_text_adapters.py tests/domain/test_deck_audit.py tests/cli/test_audit_deck_command.py tests/integration/test_frequency_e2e_export_flow.py -q
```

If broad-suite drift appears, do not hide focused failures behind known unrelated collection drift from `.planning/STATE.md`; fix failures in the focused files above.
</verification>

<success_criteria>
- Default export cannot create a clean completed APKG for the Polish failure shape: 2740 cards, level 3 with 740 cards, 260 review_required items, or invalid translations.
- `--allow-partial` is the only way to export fewer than expected frequency cards, and its output/status/report are visibly partial/warning.
- DeepL quota/provider failure blocks or surfaces clearly; it does not silently use Google Translate for final decks.
- `audit-deck` detects incomplete deck, invalid translations, duplicates, and missing media with non-zero exit for blocking issues.
- Final generation report files are created for successful exports and contain card counts, level counts, job/export status, artifact path, and APKG hash.
- Regression tests cover each priority listed in the quick-task prompt.
</success_criteria>

<output>
After completion, create `.planning/quick/260526-jgn-implemente-o-plano-em-docs-generation-pr/260526-jgn-SUMMARY.md` with files changed, tests run, and any intentionally deferred items.
</output>
