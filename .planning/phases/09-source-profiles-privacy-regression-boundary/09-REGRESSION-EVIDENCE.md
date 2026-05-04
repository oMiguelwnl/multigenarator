# Phase 09 Regression Evidence

This artifact records the runnable boundary that must stay green before v1.2 highlight ingestion/export work proceeds.

## Evidence Commands

| Command | Proves |
| --- | --- |
| `uv run pytest tests/domain/test_source_profiles.py tests/domain/test_jobs.py -q` | Source profiles are explicit; `GenerationRequest` can represent `kindle-highlights` internally while existing domain source types remain valid. |
| `uv run pytest tests/domain/test_exporting.py tests/services/test_export_anki_package.py -q` | Frequency/manual export contracts remain translation-bearing, highlight field/model selection is isolated, and mixed-source APKG export fails closed. |
| `uv run pytest tests/security/test_redaction.py -q` | SEC-01 redaction helpers cover credentials, WebDAV URLs, local raw highlight paths, book metadata, private snippets, exceptions, and gitignore protections. |
| `uv run pytest tests/integration/test_v12_existing_mode_regression_boundary.py -q` | Existing frequency and custom word-list flows still reach accepted text, fake Azure audio, APKG/CSV/TSV export, and highlight CLI gating. |
| `uv run pytest tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_frequency_e2e_export_flow.py -q` | Shipped existing-mode E2E suites remain runnable as standalone regression evidence. |
| `uv run pytest --collect-only -q` | Broad collection drift is detected before future phases rely on wider suite execution. |

## Phase 09 Verification Command

```bash
uv run pytest tests/domain/test_source_profiles.py tests/domain/test_jobs.py tests/domain/test_exporting.py tests/services/test_export_anki_package.py tests/security/test_redaction.py tests/integration/test_v12_existing_mode_regression_boundary.py tests/integration/test_custom_word_list_e2e_export_flow.py tests/integration/test_frequency_e2e_export_flow.py -q
```

## Notes

- All fixtures are synthetic and contain no real WebDAV credentials, real highlight exports, or private reading text.
- `kindle-highlights` is intentionally domain/export-representable but still rejected by the user-facing `multilang generate --source` CLI until Phase 11.
