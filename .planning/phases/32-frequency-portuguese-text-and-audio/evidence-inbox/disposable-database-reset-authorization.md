# Disposable Database Reset Authorization

target_alias=env-multilang-database-url-disposable-test
classification=disposable/test
user_choice=Wipe Current DB
destructive_reset_authorized=true
destructive_scope=public_schema_only
production_authority=false
database_drop_allowed=false
role_drop_allowed=false
non_public_schema_drop_allowed=false
backup_restore_required_for_this_rehearsal=false
plan_32_47_target_match=true
scope=Reset the public schema of the exact disposable/test target, then run Alembic current-head rehearsal only.
secret_policy=The raw MULTILANG_DATABASE_URL and target locator components are used only in-process and are not persisted.
production_boundary=A real production or important database still requires a separate plan with backup, restore, and rollback evidence.
recorded_at_utc=2026-09-08T10:16:15Z
