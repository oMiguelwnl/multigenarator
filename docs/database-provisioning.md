# Database provisioning

Alembic migrations are the single source of truth for the database schema.

## How the runtime provisions the schema

`build_runtime_service` calls `ensure_database_schema` (see
`src/multilang/db/provisioning.py`), which picks the mechanism by backend:

- **SQLite** (local development and the test suite): the schema is created in
  place with `Base.metadata.create_all` — no external setup required.
- **PostgreSQL** (production and any non-SQLite backend): the database is
  upgraded with `alembic upgrade head`. `create_all` is **not** used, so the
  migrations stay authoritative and the ORM models can never silently drift
  away from the deployed schema.

## Deploying / running against PostgreSQL

The service upgrades to the latest revision automatically on startup. To run
migrations manually (e.g. in a deploy step) point Alembic at the target
database and upgrade:

```bash
MULTILANG_DATABASE_URL="postgresql+psycopg://user:pass@host:5432/multilang" \
  alembic upgrade head
```

## Schema drift is guarded by tests

`tests/test_migration_schema_parity.py` upgrades a throwaway database with the
real migrations and asserts every ORM table **and column** has a corresponding
migration. Adding a column or table to the ORM models without a matching
migration fails these tests, so drift is caught in CI instead of at deploy time.

When you change an ORM model, add an Alembic revision in the same change:

```bash
alembic revision -m "describe the change"   # then fill in upgrade()/downgrade()
```
