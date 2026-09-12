# HTTP API and durable jobs

Run `uv run multilang native serve --host 127.0.0.1 --port 8000` or
`uv run uvicorn multilang.api:create_app --factory --no-access-log`.
The API does not create or migrate database tables. Apply the reviewed migration
through the native migration commands before enabling v2 operations.

`MULTILANG_ROADMAP_4_ENABLED=true` (alias `ROADMAP_4_ENABLED`) enables v2 and native
execution. The default is false. `GET /health` reports process liveness without
connecting to the database. OpenAPI is available at `/openapi.json`.

## Credentials and permissions

Set `MULTILANG_NATIVE_API_CREDENTIALS` to a JSON object mapping strong random
tokens to `{"subject":"operator-id","role":"Admin"}`. Pass tokens in the
Authorization Bearer header. Keep this environment value in a secret manager;
Settings masks it and the access policy retains only token hashes. Roles and
owners never come from request payloads.

| Role | Permissions |
|---|---|
| Admin | All operations and cross-owner task status |
| Linguist | Read, import, ranking, cancel own queued tasks |
| ContentCreator | Read, content/audio generation, Anki, cancel own queued tasks |
| User | Read, Anki, cancel own queued tasks |
| Worker | Worker identity, no public data APIs |

Worker processes use trusted local configuration and the stored submitting actor.
They are operated through the CLI; there is no unauthenticated HTTP worker endpoint.
Local CLI `--actor` identifies the trusted operator and is not an HTTP credential.

Requests have a default 1 MiB byte limit before JSON parsing, bounded query/list
sizes, and 60 requests/minute per authenticated subject. Limits are configurable.
The request limiter is per process; deployments with multiple replicas must apply
a shared limit at the gateway. Bind externally only behind TLS and the deployment's
access controls. HTTP inputs reject filesystem paths, credential fields and actor
overrides. Inputs use registered asset identifiers or validated inline domain data.
Provider calls additionally require `MULTILANG_NATIVE_PROVIDER_CALLS_ENABLED=true`
and the applicable signed capabilities and provider prerequisites.

## Endpoints

| Endpoint | Result |
|---|---|
| `GET /api/v1/languages` | Existing language codes |
| `GET /api/v1/search?q=...&language=en` | Read-only frequency-mode legacy lexical projection |
| `GET /api/v1/jobs/{id}` | Admin-only legacy job counters; never private source payloads |
| `GET /api/v2/search?q=...&language=en&limit=50&min_rank=1&max_rank=1000` | Owner-aware native lexical search with optional inclusive rank bounds |
| `GET /api/v2/datasets` | Public/core dataset metadata |
| `POST /api/v2/datasets/import` | Enqueue a validated dataset import, return 202 |
| `POST /api/v2/jobs` | Enqueue `import`, `ranking`, `content`, `audio` or `anki` |
| `GET /api/v2/jobs/{id}` | Owner-scoped status/counters and result hash |
| `POST /api/v2/jobs/{id}/cancel` | Cancel queued work; running effects are not reversible |

Both POST submission endpoints require `Idempotency-Key`. Job bodies are
`{"kind":"ranking","payload":{...}}`. Payload schemas are those of the native
facade and domain contracts. Reusing a key with different input fails. Repeating
the same owner/key/input returns the same task. Responses omit payloads, source
text, paths, credentials and provider exception messages. Error codes are 401
(missing/invalid credential), 403 (permission), 404 (missing/inaccessible or v2
disabled), 413 (size), 422 (contract/prerequisite), 429 (rate), and 503 (database
unavailable or schema not provisioned).

## Queue and worker lifecycle

The SQLAlchemy `native_tasks` table stores durable tasks beside existing generation
jobs. It is not a replacement for `GenerationJob` or item-stage state. Atomic
conditional updates claim leases; heartbeats renew ownership; expired leases can
be reclaimed; fencing tokens reject stale completion. Retries use bounded backoff
and an attempt budget. Error records contain exception class names, never content.

Run `uv run multilang native worker --max-tasks 10` for a bounded batch, or append
`--loop` for a long-running worker. The default processes at most one available task.
Each handler constructs the same facade as CLI/API and uses its own transaction.
Audio, import, ranking, content and Anki handlers perform real service operations;
missing capabilities or artifacts produce failures rather than fabricated success.

Delivery is at least once. A crash after a provider effect or transaction commit
can cause a retry, so domain operations/cache keys must remain idempotent. Lease
fencing protects queue state, not external exactly-once effects. PostgreSQL is
recommended for concurrent workers. Use one worker for SQLite deployments because
long write transactions can delay heartbeat writes.

## Operator commands

Every command below follows `uv run multilang native`. Commands produce JSON on
stdout. Local JSON files are limited to 32 MiB. `--actor` identifies the trusted
local operator; the default is `local-operator` (`local-admin` for migration apply
and rollback). HTTP clients cannot invoke local path operations.

| Command | Input and behavior |
|---|---|
| `status` | Report feature/provider flags without connecting to the database |
| `search QUERY --language en --min-rank 1 --max-rank 1000` | Optional positive inclusive rank bounds and `--limit` from 1 to 100 |
| `datasets` | List shared dataset metadata |
| `import-dataset FILE` / `rank FILE` | Import or rank with the facade's JSON contracts |
| `generate-content FILE` / `generate-audio FILE` | Generate persisted versions under provider/evidence gates |
| `approve-review FILE` | Verify independently signed review evidence for a content, audio or dataset version |
| `freeze-edition FILE` / `export-anki FILE` | Freeze approved versions or export an approved edition |
| `register-profile FILE RECEIPT_ID` | Verify a local signed profile receipt and persist its immutable version |
| `import-history FILE --actor OWNER` | Read the local package `path` in the JSON request; persist only validated semantic mappings |
| `register-history-aliases FILE` | Register independently reviewed history aliases |
| `preview-legacy-aliases FILE` | Produce `{preview, confirmation_sha256}` for reviewed legacy mappings |
| `apply-legacy-aliases FILE` | Apply that reviewed object after verifying its confirmation and evidence |
| `update-learner-state FILE --actor OWNER` | Set known/reading cards, expansion or priority; revoke history; reset or delete state with `expected_revision` |
| `adaptive-queue FILE --actor OWNER` | Build an owner-scoped queue from accessible datasets and learner state |
| `enqueue KIND FILE IDEMPOTENCY_KEY` | Persist a durable task, with a bounded attempt budget |
| `job TASK_ID` | Return the current operator's task status |
| `worker --max-tasks 10` / `worker --loop` | Process queued operations through the same facade |
| `serve --host 127.0.0.1 --port 8000` | Run the HTTP adapter |

Recovery commands use the same [migration service](migration.md) and stay
available with the feature flag off, except `apply-migration`:

| Command | Behavior |
|---|---|
| `backup DESTINATION --files-manifest FILE` | Snapshot the database and optionally a JSON mapping of relative archive names to local file paths; write `DESTINATION/manifest.json` |
| `restore-backup MANIFEST TARGET_CONFIG --files-destination DIRECTORY` | Restore to a new empty database and, when present, a new separate directory for files |
| `rehearse-migration MANIFEST CLONE_PATH` | Rehearse SQLite upgrade, downgrade and legacy preservation on an isolated clone |
| `rehearse-migration MANIFEST --target-config FILE` | Use an empty PostgreSQL clone configured in JSON |
| `preview-migration MANIFEST --topology FILE --rehearsal FILE` | Print the reviewable migration preview |
| `apply-migration PREVIEW MANIFEST TOPOLOGY REHEARSAL --confirm HASH` | Apply only the exact preview with verified evidence and native mode enabled |
| `preview-legacy-adoption MANIFEST` | Check an unversioned SQLite database for exact legacy schema parity |
| `adopt-legacy-schema PREVIEW MANIFEST --confirm HASH` | Stamp that confirmed legacy schema; a new backup is required afterward |
| `preview-rollback MANIFEST MIGRATION_ID` | Check that the completed migration and original backup still permit rollback |
| `rollback-migration PREVIEW MANIFEST --confirm HASH` | Roll back only after confirming the preview; later data or schema changes block it |

`TARGET_CONFIG` is a local JSON file containing `{"database_url":"..."}`; it keeps
database credentials out of command arguments. Recovery previews print their
confirmation hash to stderr so stdout can be redirected unchanged to a JSON file.
Restore refuses to overwrite the source database or a nonempty target. PostgreSQL
backup/rehearsal requires matching `pg_dump` and `pg_restore` client tools.

Production export requires an approved frozen edition, provider outputs and signed
Anki topology evidence. Wheels include application templates and Alembic resources.
Project data and Korean evidence under `data/korean_foundations/evidence` remain
external deployment assets; supply the versioned assets and configure the existing
data/evidence paths when installing from a distribution. Operator plans and private
working files are excluded from source distributions.

## Observability

`MULTILANG_NATIVE_TELEMETRY_ENABLED=true` enables static operation spans, duration
histograms, counters and structured JSON events. The OpenTelemetry API uses the
deployment's configured SDK providers/exporters; no remote collector is selected
automatically. Logs exclude message bodies, exceptions, request paths, prompts and
credentials. Existing provider-call repositories continue to supply costs, token
counts, retry/fallback statistics and latency summaries.

References: [FastAPI security](https://fastapi.tiangolo.com/advanced/security/),
[OpenTelemetry Python instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/),
[uv and Dependabot](https://docs.astral.sh/uv/guides/integration/dependabot/).
