# Generation Quality and Modular Architecture Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or
> superpowers:executing-plans for the bounded tasks below. The user requested
> both planning and implementation; continue without another execution question.

**Goal:** Make definitions evidence-backed and recoverable, scale native context,
and organize the existing monolith without breaking Anki or CLI contracts.

**Architecture:** Reuse the domain/service/repository boundaries. Add focused
content services, bounded provider projections and cohesive command/service
packages with compatibility exports. Preserve persisted contracts by omitting
new empty metadata from historical payloads where hashes depend on serialization.

**Tech Stack:** Python 3.12, Pydantic v2, LiteLLM, SQLAlchemy, Typer, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-09-13-generation-architecture-improvements.md`

## Global Constraints

- No GSD/GSDD, paid provider requests, real database migration, deploy or push.
- Preserve exact Anki fields/order, GUIDs, Korean authority and Latin isolation.
- Preserve concurrent qualification changes and the existing staged index.
- Fail closed on missing semantic authority; never replace it with word overlap,
  self-reported model confidence or a fabricated human approval.
- Keep all full known-concept sets in local validation; prompt limits are separate.
- No new third-party runtime dependency. Keep public commands/imports compatible.
- Tests use offline providers and disposable databases; no production credentials.
- Root owns integration and final formatting/CI; task ownership cannot overlap.

## Task 1: Evidence-backed definitions and recoveries

**Files:** `domain/lexicon.py`, `services/lexical_lookup.py`,
`services/lexical_grounding.py`, `services/text_generation.py`,
`services/provider_text_adapters.py`, `services/text_field_remediation.py`,
`services/local_text_adapter.py`, `services/assemble_export_cards.py`, `runtime.py`;
new focused modules in `services/content/`; related service tests.

**Interfaces:** Extend DefinitionGenerationRequest with bounded source evidence,
source sense and source language metadata. Preserve generate_definition(request)
and result.definitions_html as compatibility boundaries. Persist actual origin,
language, fallback reason and quality decision in DefinitionRecord.

- [x] Reproduce wrong meaning accepted, wrong-language fallback mislabeled,
  missing index marked grounded and multiple senses silently selected.
- [x] Implement explicit source selection and review-required handling; source
  lookup cannot silently choose among distinct senses. Remove production seed
  trust escalation. Feed resolved evidence into generation and sentence context.
- [x] Add a typed definition orchestration service using existing cache/retry/log
  controls, request timeout and output bound. Verify source/cache/schema changes
  invalidate results and transient errors retry without retrying exhausted quota.
- [x] Verify recovery bookkeeping and language; reject/invalidate unsupported
  semantic conclusions instead of certifying arbitrary output. Preserve local
  offline fixtures as explicitly synthetic evidence, not production approvals.
- [x] Add semantic/language adversarial cases and repair relevant legacy tests.

Regression shape:
```python
result = grounded_definition(source_meaning="a dwelling", generated_meaning="a dog")
assert result.review_required or result.meaning == "a dwelling"
assert fallback.definition_language == fallback.actual_source_language
assert fallback.provenance.fallback_used
```
Use actual service APIs in committed tests; these assertions describe the contract.

## Task 2: Bounded native provider context

**Files:** `domain/content.py`, `services/native_content.py`,
`tests/services/test_native_content_audio.py`; native integration tests as needed.

**Interfaces:** Keep NativeContentService.prepare/generate/complete. Introduce a
bounded prompt projection independent of the full ContentRequest. Preserve
content hashes for existing requests and all local target/i+1 checks.

- [x] Test 3000 valid 64-character known IDs reach generation within prompt limits.
- [x] Test a sentence with an unauthorized concept remains rejected with that set.
- [x] Bound local request bytes/cardinality separately and limit rendered provider
  messages; omit opaque administrative identifiers from provider-facing content.
- [x] Preserve private-context policy and output caps; run native content tests.

```python
known = tuple(sha256(str(i).encode()).hexdigest() for i in range(3000))
request = base_request(canonical_known_concept_ids=known)
assert len(provider_projection(request).encode()) <= 16000
assert request.canonical_known_concept_ids == known
```

## Task 3: Decompose CLI by responsibility

**Files:** `cli.py`, new `cli_commands/` package and focused CLI tests.

**Interfaces:** Existing create_app(...) injection signature and module app remain.
Group Korean foundation, frequency/evidence/release, personal-source, Latin and
export commands behind explicit registration functions. Keep options/help stable.

- [x] Capture command/help and injected-service behavior before moving code.
- [x] Extract cohesive registrars with explicit dependencies; do not execute source
  strings or copy every global into registrars. Preserve legacy patch seams.
- [x] Reduce cli.py substantially; remove obsolete imports and run CLI tests.

```python
assert command_names(create_app()) == expected_legacy_commands
assert runner.invoke(create_app(service=fake), command_args).exit_code == 0
```

## Task 4: Service packages and explicit transactions

**Files:** selected services grouped in `services/vocabulary/`, `services/content/`,
`services/audio/`, `services/review/`, `services/exporting/`; compatibility modules;
legacy repositories and new `repositories/transactions.py`; architecture tests.

**Interfaces:** Preserve existing import identities and monkeypatch behavior.
Add an explicit managed transaction scope for repository composition while
retaining standalone commit behavior for current callers.

- [x] Test old/new import and patch equivalence and resource lookup paths.
- [x] Relocate cohesive modules after Tasks 1–3 finish; maintain thin adapters.
- [x] Test a multi-repository operation rolls back together on an exception.
- [x] Implement transaction ownership with explicit scope; avoid implicit partial
  commit when called inside a declared application unit of work.
- [x] Run repository and export regressions; document the module ownership map.

```python
with pytest.raises(ValueError):
    with repository_transaction(session):
        first_repository.write(first)
        second_repository.write(second)
        raise ValueError("abort")
assert persisted_count(session) == 0
```

## Task 5: Evaluation and project-wide quality checks

**Files:** new evaluation fixtures/tests near content services, `pyproject.toml`
only if necessary, `.github/workflows/ci.yml`, `docs/architecture.md`, new
`docs/generation-quality.md` and implementation record.

- [x] Add repeatable offline evaluation cases for ambiguity, source-language
  differences, unsupported meaning, failure recovery and valid grounded output.
- [x] Preserve legitimate human-review requirements and link the existing
  qualification workflow instead of producing synthetic approval receipts.
- [x] Run Ruff across src/tests and correct current selected rule violations,
  preserving concurrent functionality. Change CI from allowlisted files to full
  source/test coverage. Capture any concurrent edits before touching shared files.
- [x] Run affected tests, offline regressions, build and documentation validation.
- [x] Review diffs independently; fix material findings; record evidence and
  outstanding real-world review requirements without claiming production quality.

Final integrated regression and quality commands:
```bash
env -u MULTILANG_DATABASE_URL MULTILANG_FORBID_NETWORK=1 MULTILANG_FORBID_PROVIDERS=1 .venv/bin/python -m pytest \
  tests/cli/test_command_registration.py tests/integration/test_phase32_dependency_guard.py \
  tests/services/test_native_content_audio.py tests/services/test_native_cloze_spans.py \
  tests/integration/test_native_application.py tests/integration/test_native_generated_edition.py \
  tests/integration/test_native_invariants.py tests/integration/test_native_source_refresh.py \
  tests/services/test_text_generation.py tests/services/test_generate_text_items.py \
  tests/services/test_regenerate_text_item.py tests/services/test_provider_response_cache.py \
  tests/services/test_assemble_export_cards.py tests/services/test_local_text_adapter.py \
  tests/test_runtime.py tests/test_runtime_templates.py --timeout=300 --tb=short -q
.venv/bin/ruff check src tests alembic/versions/20260912_20_native_architecture.py --no-cache
.venv/bin/python -m build --no-isolation
.venv/bin/mkdocs build --strict
```

## Execution record

Baseline preserved in `.multilang/verification/generation-improvements/baseline.json`.
Independent implementation/review reports live beside it. Update checkboxes only
after the corresponding verification passes. Retain source, tests and docs for
review; do not commit unrelated concurrent changes.

Completed: final integrated selection 193 passed; broad repository/domain/service
selection 417 passed; focused definition selection 123 passed. The fixture/export
rerun resolved all four failures from the broad fixture selection (8 passed).
Ruff, distribution build, wheel inventory and strict documentation build passed.
Heavy test groups ran sequentially because the workspace was shared with another
active task. Selections overlap; this is not a claim that the complete repository
suite or production providers were exercised. Details are in
`docs/generation-architecture-implementation.md`.
