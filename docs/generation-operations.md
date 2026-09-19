# Generation ownership and recovery

Text generation runs one worker per job. `generate --concurrency` accepts only
`1`, and the shared service enforces the same limit before selecting candidates.
PostgreSQL permits independent jobs to run in separate processes; SQLite permits
one generation job across the database at a time.

The `generation_leases` table is introduced by Alembic revision `20260913_21`.
Normal PostgreSQL runtime provisioning targets this revision on a separate branch
from native revision `20260912_20`; both descend from `20260828_19`. It creates the
lease table without activating or provisioning native tables. Deployments that
manage migrations separately must run `alembic upgrade 20260913_21` before running
generation. SQLite creates the table through its existing local schema bootstrap.

Revision `20260914_22` merges the native and generation branches into one Alembic
head. Upgrading to this head still requires the native migration workflow's
verified backup, rehearsal and explicit authorization. Its preview binds the
contents of revisions 20, 21 and 22. Native rehearsal and confirmed rollback
return to revision 21, preserving generation leases. The merge checks native
authorization before a downgrade can remove either branch.
The service explicitly downgrades the native branch to its revision 19
branchpoint. A plain downgrade to revision 21 only splits the merge and leaves
native revision 20 active; it does not complete this rollback. This follows
[Alembic's branch traversal rules](https://alembic.sqlalchemy.org/en/latest/branches.html).

Each run acquires an atomic lease before reading its candidate batch. A heartbeat
renews ownership. Each item records an input-key hash before generation starts;
its text and job progress commit together in a short transaction that checks the
lease token. Provider telemetry and response-cache writes retain their separate
commits. An expired worker cannot overwrite a replacement worker's content.

An interruption during provider work leaves an item hash requiring explicit
recovery. Inspect it with:

```console
multilang generation-lease-status --job-id JOB_ID
```

Reconcile the provider attempt history and cached output before clearing that
reservation. The command requires the exact reported hash and an expired lease:

```console
multilang recover-generation-lease --job-id JOB_ID \
  --expected-item-sha256 ITEM_SHA256 --acknowledge-unknown-outcome
```

Recovery preserves provider history and performs no generation, retry, review, or
export. It does not grant paid-call authority. A separately authorized resumed
run can use `--missing-only` to skip already persisted text, including text still
awaiting review. Completed item commits clear their interruption markers
atomically, so those items do not require manual recovery.

These controls provide generation ownership and explicit recovery boundaries.
They do not establish production Korean deck quality, Anki playback acceptance,
or a global scheduler enforcing provider quotas across independent jobs.
