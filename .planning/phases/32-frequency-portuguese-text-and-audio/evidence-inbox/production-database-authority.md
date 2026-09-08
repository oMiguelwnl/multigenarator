# Production Database Gate Authority

Captured: 2026-09-08
Runtime: opencode
Authority kind: production-database-gate

The user approved continuing past the Phase 32 production database gate in the current session. This authority is narrow and can be consumed only when `MULTILANG_DATABASE_URL` is present in the process environment without reading `.env` or printing/persisting the raw locator.

```json
{
  "schema_version": "phase32-production-database-authority-v1",
  "authority_kind": "production-database-gate",
  "approval_captured": true,
  "approval_source": "current-session-user-reply",
  "target_source": "process_env:MULTILANG_DATABASE_URL",
  "allowed_powers": [
    "check-database-url-env-presence",
    "future-production-db-preflight-planning",
    "future-non-destructive-alembic-upgrade-head-planning",
    "future-korean-frequency-job-binding-planning"
  ],
  "destructive_operations_allowed": false,
  "raw_database_url_allowed_in_artifacts": false,
  "read_env_file_allowed": false,
  "database_connection_allowed_without_locator": false,
  "grants_provider_authority": false,
  "grants_azure_authority": false,
  "grants_audio_synthesis_authority": false,
  "grants_review_application_authority": false,
  "grants_export_authority": false,
  "grants_release_authority": false,
  "grants_publication_authority": false,
  "grants_delivery_authority": false,
  "grants_phase32_closure": false
}
```

## Boundary

This artifact does not prove a database target, migration state, schema readiness, job binding, provider readiness, audio readiness, review readiness, export readiness, release readiness, publication readiness, delivery, or Phase 32 closure.
