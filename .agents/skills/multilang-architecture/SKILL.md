---
name: multilang-architecture
description: "Guide architecture changes in Multilang's native application path, including domain boundaries, transactions, jobs, providers, persistence, and exports. Use when designing or modifying cross-cutting backend architecture; not for isolated UI-only changes."
---

# Multilang Architecture

Use this skill for work that crosses the native application's domain, service,
repository, runtime, API, CLI, worker, provider, or export boundaries.

The native path evolves `src/multilang`; it does not create a second application
or replace existing exporters and jobs. Preserve existing public integrations and
change the smallest relevant boundary. Before an architectural change, read the
applicable sections of [the development stack reference](../../../docs/development-stack-reference.md)
and inspect the current implementation and installed versions.

## Boundaries and composition

Keep these dependencies directional:

| Area | Responsibility |
|---|---|
| `domain/` | Typed contracts, identities, and invariants. It must not import services or persistence. |
| `services/` | Calculation, import, validation, generation, review, and export use cases. |
| repositories | Persistence access. Native repositories leave commit ownership to the application. |
| `native_runtime.py` | Explicitly composes native services, existing `Settings`, and existing providers. |
| API, CLI, workers | Call the runtime composition; do not reconstruct dependencies independently. |

Organize new service code by responsibility:

| Package | Responsibility |
|---|---|
| `services/vocabulary/` | Lexical identity pipeline and ranking. |
| `services/content/` | Grounded definitions, quality decisions, and provider execution. |
| `services/audio/` | Audio versions, byte integrity, and synthesis fallback. |
| `services/review/` | Version review and text reports. |
| `services/exporting/` | Card projection, fields, APKG, and tabular export. |
| `cli_commands/` | Command registration grouped by responsibility. |

Keep compatibility modules for relocated services so old imports, classes, and
test seams resolve to the same Python objects. New code uses the responsibility
packages. Keep `cli.py`, `create_app`, and public integration points stable;
registrars hold command bodies. Use explicit dependencies—never execute Python
strings or copy global namespaces to install commands.

Model data by ownership:

- **Core** holds identities, revisions, forms, sources, ranking, and editions.
- **Generated** holds immutable content and audio versions.
- **User** holds owner-scoped state and minimized history.

Adaptation may change priority, module, and eligibility. It must not change a
Core GUID, rank, or content.

## Application transactions

When repositories share a SQLAlchemy `Session`, the application owns one atomic
unit of work. Use `repository_transaction(session)` or an explicit outer
`session.begin()`:

```python
with repository_transaction(session):
    job = job_repository.create_job(...)
    lexical_repository.upsert_candidates(...)
```

`repository_transaction` adopts an implicit transaction already opened by
pending writes and joins an explicit outer transaction. Nested scopes share the
same unit: catching an inner error does not make the remaining work committable,
and an inner rollback invalidates the whole unit.

Give every request and worker its own `Session`. Keep network calls and expensive
processing outside long-lived persistence transactions. Attempt logs that must
survive a business rollback use a separate session. Queue claim and heartbeat
transactions remain short.

## Extensibility, jobs, and providers

Register analyzers and importers only through `PluginRegistry`, by explicit name
and version. Registration is trusted code/configuration only: payloads must not
choose imports, execute scripts, or select endpoints. Disabled profiles fail
before generation or import. `source-evidence` consumes explicit analysis and
does not invent lemmas or senses.

The database-backed queue uses owner-scoped idempotency keys, compare-and-swap
claims, leases, heartbeats, fencing, bounded retries, and terminal states.
Delivery is at least once, so handlers must be idempotent. A failure after an
external effect can repeat a provider call; cost approval and provider limits
still apply.

Prefer the existing database for search and queue needs. Search uses
parameterized queries, normalized forms, senses, generated meanings, and
frequency filters for the active dataset. Local cache entries require bounded
size, TTL, and versioned, namespaced keys. Verify audio bytes before reusing an
asset. Do not add Redis/RQ or Meilisearch unless measurements justify them.

## Evidence, rollout, security, and observability

Local HMAC receipts bind a payload, purpose, owner, and expiration. The operator
configures the secret. A signature proves a decision's integrity and origin, not
the linguistic truth of its claims: review precedes signing. Verify bytes for
Anki decision artifacts too. A synthetic approval fixture never qualifies
production.

`ROADMAP_4_ENABLED` keeps the native path disabled by default. Legacy startup
provisions only the legacy schema; migration 20 requires the authorized
migration service. New linguistic capabilities begin disabled.

API and workers emit fixed-name structured spans, metrics, and logs with status
and duration. Do not log payloads, credentials, or stack traces containing
private input. Operators configure OpenTelemetry providers and exporters; the
instrumentation itself does not configure an external telemetry backend.

Authenticated HTTP credentials determine the actor and role—clients never supply
their own role. Preserve request limits, rate limits, ownership checks, closed
schemas, and escaping at boundaries. Deployment supplies TLS, egress control,
and secure secret storage. For API-specific changes, read [API guidance](../../../docs/api.md).
