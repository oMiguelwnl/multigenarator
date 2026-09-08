---
phase: 32-frequency-portuguese-text-and-audio
plan: "19"
runtime: opencode
assurance: self_checked
---

# Phase 32: Frequency, Portuguese Text, and Audio - Plan 19 Summary

**Completed**: 2026-09-06
**Tasks**: 2
**Git Actions**: None; commit not requested.
**Deviations**: The live NIKL response used `/common/download.do` with an `o_file_name` query rather than the stale `/front/etcData/etcDataFileDownload.do` fixture path; the official TXT bytes are CP949 despite a UTF-8 response header, so retrieval now preserves exact bytes and records `text_encoding=cp949`.
**Decisions Made**: No new downstream authority was granted. Retrieval remains source-access-only.
**Notes for Verification**: Plan 32-18 remains waived by owner, not passed by a full-suite claim. The quarantined TXT is exact source bytes, not transformed data.
**Notes for Next Work**: Plan 32-20 may perform read-only transformation preflight, then must stop for exact local-use/transformation/redistribution authority.

## Evidence

| Artifact | Result |
|---|---|
| `.multilang/phase32/source-quarantine/한국어 학습용 어휘 목록.txt` | `132254` bytes, SHA-256 `3b49681f05d6a7490c13da2a2847e433effdf65da409fd295792d6ee33685064`, exact CP949 source bytes. |
| `evidence-inbox/source-retrieval-result.json` | `source_id=nikl-korean-learners-vocabulary`, fixed landing URL, response-derived attachment locator, `text_encoding=cp949`. |
| `evidence-inbox/source-retrieval-validation.json` | `status=valid`, `production_asset_path_present=false`, `active_frequency_pointer_present=false`, `grants_transform_power=false`. |

## Network Control Matrix

| Control | Result |
|---|---|
| Fixed landing URL | `https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=70` only. |
| Official host | `www.korean.go.kr` only for landing and attachment. |
| Attachment derivation | Exactly one response-derived anchor labelled `한국어 학습용 어휘 목록.txt`. |
| Attachment allowlist | `/common/download.do`, `file_path=etcData`, exact `o_file_name`, UUID-like `c_file_name`. |
| Redirect handling | Redirected final response URLs reject before byte acceptance. |
| DNS control | Real CLI path requires public DNS/IP resolution before each request. |
| Credential/header control | No user URL, credential, or header override exists in the CLI. |

## Verification

- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync pytest tests/services/test_korean_frequency.py tests/cli/test_korean_source_retrieval_commands.py tests/scripts/test_build_frequency_assets.py -q` -> `25 passed`.
- `.planning/.local/phase32-py312/bin/python -c "... exact source filename/hash/encoding assertions ..."` -> passed.
- `UV_PROJECT_ENVIRONMENT=.planning/.local/phase32-py312 UV_OFFLINE=1 uv run --frozen --no-sync multilang validate-korean-source-retrieval-result --result-file .planning/phases/32-frequency-portuguese-text-and-audio/evidence-inbox/source-retrieval-result.json --source-file '.multilang/phase32/source-quarantine/한국어 학습용 어휘 목록.txt' --output .planning/phases/32-frequency-portuguese-text-and-audio/evidence-inbox/source-retrieval-validation.json` -> `retrieval_result_status=valid`.

<checks>
<executor_check>
checker: self
checker_runtime: opencode
status: passed
blocking: false
notes: Verified response-derived retrieval, exact source byte hash, CP949 schema validation, no active frequency pointer, no production asset path, and content-free validation output. No transformation, curation, provider call, database mutation, Azure call, release, publication, or Git action was performed.
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
  summary: The live NIKL attachment locator uses `/common/download.do` with exact query fields, so stale test fixtures and validators were narrowed to the current response-derived shape.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The official TXT bytes decode as CP949, so validation now accepts `utf-8` or `cp949` while preserving exact downloaded bytes.
- class: factual_discovery
  impact: recoverable
  disposition: proceeded
  summary: The CLI validation command lacked an evidence `--output`; a content-free JSON output was added for the plan artifact.
</deltas>

<judgment>
<active_constraints>
Only source-access retrieval is complete. No transformation, local-use, redistribution, repository commit, provider, Azure, production database, release, publication, or final deck authority exists from this plan.
</active_constraints>
<unresolved_uncertainty>
Official terms/attribution evidence, local-use and transformation rights, redistribution, transformed-data storage disposition, exact parser policy, curation review, provider authority, Azure authority, production database mutation, release, and publication remain unresolved.
</unresolved_uncertainty>
<decision_posture>
Proceed only to Plan 32-20's read-only preflight and human/legal checkpoint. Treat CP949 as source encoding evidence, not as permission to transcode, transform, redistribute, or commit source-derived data.
</decision_posture>
<anti_regression>
Do not replace the fixed NIKL landing URL, do not broaden attachment path/query allowlists, do not follow redirects silently, do not accept private DNS/IP resolution, do not rewrite exact source bytes during retrieval, and do not infer downstream rights from successful retrieval.
</anti_regression>
</judgment>
