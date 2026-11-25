---
name: architecture-review
description: "Perform an evidence-based architecture review of an existing codebase. Use when asked to audit, review, assess, or improve software architecture. Read-only by default; do not modify application code."
---

# Senior Architecture Review

Conduct a senior/staff-level review of the repository that is checked out.
Identify concrete, actionable risks in design, coupling, security, reliability,
scalability, operability, and SaaS readiness where relevant.

The review is read-only by default. Do not edit application code,
configuration, migrations, tests, or documentation unless the user explicitly
requests remediation.

## Principles

- Inspect implementation, tests, configuration, migrations, and deployment
  artifacts before reaching conclusions. Never turn a generic checklist into a
  finding.
- Follow real execution paths from API, CLI, or worker entry point through
  services, domain rules, persistence, queues, and providers.
- Cite exact file paths and line ranges where possible. Explain the failure
  mechanism and practical impact.
- Separate confirmed facts, likely risks requiring runtime validation, and
  architectural gaps. State what would confirm or disprove uncertainty.
- Prioritize exploitable security issues, data loss or corruption, tenant
  isolation, concurrency, availability, core correctness, and financial
  exposure before cosmetic refactoring.
- Recommend the smallest safe correction. Do not prescribe microservices,
  Kubernetes, Redis, event sourcing, CQRS, or a rewrite without evidence that
  justifies the added complexity.
- Protect sensitive values. Report exposure locations with secrets and personal
  data redacted.

## Review workflow

### 1. Establish scope and state

- Confirm the repository root, target branch or commit, working tree state, and
  remotes when available. If no branch is specified, review the current checkout
  and state that scope.
- Do not switch branches, reset, stash, checkout, rebase, merge, or otherwise
  alter Git state.
- Identify uncommitted changes without treating them as committed
  implementation. Preserve all existing work.
- Map multiple packages or applications before narrowing the review. Record
  inaccessible files as limitations instead of guessing.

### 2. Build an architecture map

Inspect the relevant repository tree, docs and ADRs, dependency manifests,
entry points, dependency injection/composition roots, domain and application
layers, adapters and repositories, data models and migrations, queues and
workers, identity and tenancy controls, integrations, configuration, feature
flags, tests, CI, deployment artifacts, and observability configuration.

Describe concisely:

- Runtime processes and their responsibilities.
- Module dependency direction and composition roots.
- Data ownership and persistence boundaries.
- Synchronous and asynchronous execution paths.
- External systems and trust boundaries.

Compare documentation with the implementation; report material drift rather
than assuming documents are current.

### 3. Trace critical flows

Trace representative high-risk flows. Where they exist, include a normal read,
a state-changing write, a background operation, an external-provider or file
operation, and an ownership-sensitive operation. For each, follow the actual
call chain and identify validation, authentication, authorization, owner or
tenant propagation, business rules, database transactions, external effects,
timeouts, retries, cancellation, logs, metrics, and audit records.

### 4. Evaluate evidence-backed risks

Use these lenses; report an issue only when the inspected evidence supports it.

**Design and modularity:** dependency direction, framework-independent domain
rules, cohesive boundaries, duplicated business logic, circular imports, hidden
shared state, meaningful interfaces, error semantics, and clear composition.

**Data and persistence:** database-enforced invariants, foreign keys, unique
constraints, indexes, delete behavior, transaction scope, concurrency, schema
compatibility during rollout, immutable/versioned records, tenant filters,
pagination, query bounds, and N+1 behavior.

**Security and privacy:** credentials and sessions; role and object-level
authorization; tenant isolation; input validation; deserialization, injection,
SSRF, traversal and exhaustion paths; secret handling; upload/download controls;
CORS, CSRF, headers, TLS, rate limits, retention, deletion, backups, audit, and
supply-chain evidence. Inspect middleware, gateways, and infrastructure before
claiming a missing control is a vulnerability.

**Reliability and asynchronous work:** idempotency scope, at-least-once
delivery, duplicate effects, retry policy, backoff, leases, heartbeats, fencing,
stale workers, poison messages, recovery, cancellation, timeouts, outbox/inbox
behavior, shutdown, provider fallback, and consistency of task/business state.

**Performance and scalability:** blocking work in async paths, pools, resource
bounds, payloads, streaming, indexes, scans, cache lifecycle and tenancy,
filesystem assumptions, statelessness across replicas, coordination,
backpressure, queue saturation, and batch import/export behavior. Never invent
capacity estimates.

**SaaS readiness, when applicable:** organizations and memberships,
tenant-scoped authorization, lifecycle and recovery, subscriptions and quotas,
usage/cost attribution, limits, data export/deletion, audited admin access,
self-service configuration, tenant-aware observability, and incident response.
Distinguish multi-user software from commercially operable SaaS.

**Delivery and operations:** relevant unit, integration, contract, migration,
security, and concurrency tests; CI configuration versus actual run results;
reproducibility and dependency pinning; health checks, graceful shutdown,
rollback, structured logs, tracing, metrics, correlation IDs, redaction, SLOs,
alerts, and backup/restore evidence.

### 5. Validate safely

Run the narrowest relevant tests first, then broader checks when practical. Use
configured static analysis or type checks where appropriate. Inspect assertions;
test existence alone is not proof. Use isolated test data and credentials.

Never run destructive commands against production or an unknown database, run
migrations outside a disposable environment, call paid providers, or send real
customer data. Record commands, environmental constraints, and exit codes. If
execution is unavailable, label the result static analysis and provide the
commands needed to validate it. Never claim a test passed unless it passed in
the current session.

## SaaS and multi-tenant systems

Treat tenant isolation as a security boundary, not a query convention. For each
tenant-owned operation, verify server-side identity propagation and tenant scope
for reads, writes, deletes, exports, jobs, cache keys, search, analytics, and
storage. Check that relationships cannot cross tenants unintentionally, unique
constraints and idempotency keys have the correct scope, worker payloads cannot
override ownership, and support/admin access is explicit and audited. Look for
cross-tenant tests; a `tenant_id` column alone is insufficient.

## Finding format

Group findings by severity, then subsystem. Avoid duplicates caused by the same
root cause. Use this format for each finding:

**[ID] Specific title**

- **Severity:** Critical / High / Medium / Low / Informational.
- **Confidence:** Confirmed / Strong evidence / Needs runtime validation.
- **Area:** Relevant concern, such as security, tenancy, data integrity,
  reliability, performance, design, SaaS, or operations.
- **Evidence:** Exact file and line range, or symbol and observed behavior.
- **Problem:** What the implementation does now.
- **Failure mechanism:** How it fails or becomes risky, step by step.
- **Impact:** Concrete user, business, security, financial, or operational cost.
- **Recommendation:** Smallest safe architectural correction.
- **Validation:** Test or experiment that proves the fix.

Calibrate severity. Critical requires a likely severe outcome such as exploitable
cross-tenant access, remote compromise, or catastrophic loss. A missing SaaS
capability is normally a gap, not a vulnerability; a theoretical risk without a
demonstrated path needs validation.

## Close-out

Conclude with an executive maturity verdict, the five highest-impact risks, quick
wins, work required before the stated deployment target, changes not recommended
yet, an ordered test/measurement plan, and review limitations. Prefer incremental
milestones over a wholesale redesign. Write in the user's language, remain direct
and constructive, and end with the single most valuable next action.

Before delivering, verify that every finding has evidence, a mechanism and an
impact; confirmed defects are separated from risks; severity and confidence are
calibrated; tenant boundaries and transaction/external-effect paths were checked
when applicable; claims about tests/CI reflect the current session; no sensitive
values are exposed; and scope plus limitations are explicit.
