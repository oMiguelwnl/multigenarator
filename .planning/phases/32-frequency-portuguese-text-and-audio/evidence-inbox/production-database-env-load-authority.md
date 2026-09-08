# Production Database `.env` Load Authority

Captured: 2026-09-08
Runtime: opencode
Authority kind: env-file-load-approved

The user approved a narrow exception to load `.env` without printing secrets. This approval is limited to parsing only `MULTILANG_DATABASE_URL` for sanitized production target classification. It does not grant permission to inspect unrelated `.env` values or to persist the raw locator.

```json
{
  "schema_version": "phase32-production-database-env-load-authority-v1",
  "authority_kind": "env-file-load-approved",
  "approval_captured": true,
  "approval_source": "current-session-user-reply",
  "approved_user_text": "aprovo carregar .env sem imprimir",
  "allowed_env_keys": [
    "MULTILANG_DATABASE_URL"
  ],
  "allowed_powers": [
    "parse-env-file-database-url-in-memory",
    "compute-sanitized-database-locator-hash",
    "compare-against-prior-disposable-target-hash"
  ],
  "shell_source_env_allowed": false,
  "unrelated_env_secret_read_allowed": false,
  "raw_database_url_allowed_in_artifacts": false,
  "database_connection_allowed": false,
  "alembic_migration_allowed": false,
  "job_binding_allowed": false,
  "destructive_operations_allowed": false,
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

This artifact does not prove a production database target, migration state, schema readiness, job binding, provider readiness, audio readiness, review readiness, export readiness, release readiness, publication readiness, delivery, or Phase 32 closure.
