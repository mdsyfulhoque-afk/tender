# TenderOS on Vercel

## Deployment target

The target is a **private, single-owner pilot** on the user's Vercel account with
managed PostgreSQL and a native private Vercel Blob store. It is not a customer
or multi-tenant service. Hosted mode requires durable services and authenticated
access; local mode retains SQLite. `TENDEROS_DATA_DIR=/tmp/...` is not a hosted
storage fallback. Application packaging does not create those resources or
establish an account connection or deployment URL.

## Project settings

| Setting | Value |
| --- | --- |
| Repository | `mdsyfulhoque-afk/tender` |
| Reviewed integration branch | `tenderos/import-v1.2` |
| Root Directory | `TenderOS` |
| Framework Preset | FastAPI |
| Application entrypoint | `app/main.py`, exporting `app` (`app.main:app`) |
| Install command | Framework default; uses `requirements.txt` |
| Build command | Framework default; no custom command |
| Output directory | Framework default; no custom directory |
| Function maximum duration | 60 seconds, subject to the connected account's limits |

The native runtime discovers the entrypoint and routes `/`, `/static/*`, `/api/*`
and `/api/docs`. Confirm resolved Python/dependency versions in the actual build.

## Environment and services

Create the managed database and a **private** Vercel Blob store, then configure
these variables in the intended Preview and Production environments:

| Variable | Purpose |
| --- | --- |
| `TENDEROS_DATABASE_URL` | Managed PostgreSQL URL with `sslmode=require`, `verify-ca` or `verify-full` |
| `BLOB_READ_WRITE_TOKEN` | Token provided by the native private Vercel Blob store |
| `TENDEROS_BLOB_ACCESS` | Must be `private` |
| `TENDEROS_PILOT_USERNAME` | Operator identity: 2–100 characters, no colon or whitespace |
| `TENDEROS_PILOT_PASSWORD` | Random secret of at least 32 characters |
| `TENDEROS_APP_ORIGIN` | Exact HTTPS application origin, without a path/query |

Vercel supplies `VERCEL=1` and deployment hostname variables; local hosted-mode
verification uses `TENDEROS_HOSTED=1`. Set separate managed resources and secrets
where Preview should not share Production state. Keep secrets out of Git,
deployment files, command arguments and output. Enable Vercel Deployment
Protection where available and verify its coverage; application authentication
is also required.

`TENDEROS_DATABASE_URL` takes precedence over the optional `DATABASE_URL` alias.
Private storage defaults to `vercel_blob`; `TENDEROS_PRIVATE_STORAGE` may select
that same value explicitly. The runtime dependency manifest includes `psycopg`.

Hosted requests use single-owner HTTP Basic authentication on every route and
exact trusted origins. Authenticated `/api/health` supplies the per-origin token
required as `X-TenderOS-CSRF` on unsafe API requests; the UI handles this header.
The hosted PDF payload cap is **4 MiB**, versus **10 MiB** in
local mode; multipart overhead must also fit the actual Vercel ingress limit.
No automatic remote schema creation, local database copy or `/tmp` fallback is
permitted. Missing service/authentication configuration must fail closed.

## File boundaries

`.vercelignore` allows `app/main.py`, `app/hosting.py`, `app/database.py`,
`app/private_storage.py`, the three static assets, dependencies and configuration.
Add new runtime files explicitly. Knowledge, receipts, tests, databases, uploads,
logs, dotenv and Vercel local state are excluded by default; `vercel.json` also
excludes them from the function bundle. `scripts/migrate_postgres.py` and
`scripts/postgres_schema.sql` are operator migration tools, not runtime upload
files; execute them from the trusted source checkout before deployment.

With the managed database URL already configured securely in the operator's
environment, apply the idempotent schema migration explicitly:

```bash
cd TenderOS
python -m pip install -r requirements.txt
python scripts/migrate_postgres.py --apply
```

This uses a transaction/advisory lock and migration digest marker; function
startup never applies DDL. It does not import SQLite or customer data.

Git integration can clone the private repository for its build; a CLI ignore
file does not prevent that. Root Directory limits the application build, and
function exclusions limit its runtime bundle. To avoid sending other repository
files at all, use a reviewed staging directory with only approved runtime files
and a matching project root instead of Git import.

`.vercel/` and `.env.*` are ignored by Git. Preserve ProposalGuard outside the
TenderOS build root; never copy local account state into deployment artifacts.

## Deploy after the prerequisites are complete

1. Connect the actual account/team/project. Import the private repository with
   Root Directory `TenderOS` and the reviewed integration branch; deployment
   does not require merging the draft PR.
2. Configure the environment above and apply the managed database schema once
   from the trusted operator environment. Do not import the archived SQLite
   database or customer uploads. Deploy a Preview from the reviewed commit.
3. Check authenticated UI, static assets, health, APIs/exports, unauthorized
   requests, hosted mutations and uploads. Verify synthetic records and private
   PDFs survive new function instances and redeployment, with authorized access.
4. Promote to Production with its correctly scoped variables/protection. Record
   the actual deployment ID, commit and URL; deployment is already authorized.

For CLI, authenticate/link the actual project, run `npx vercel deploy`, then
`npx vercel deploy --prod`. Inspect its Root Directory: a Git-bound `TenderOS`
project expects a source containing that directory, so invoking inside it can
prepend `TenderOS` twice. A CLI-only staged project can use root `.`. Apply the
allowlist at the upload root and inspect the file list. Never put tokens in
commands, documentation or output.

Account access and platform reachability are deployment dependencies. Do not
report a successful deployment without the platform's actual result and URL.

## Native-runtime references

Configuration is based on the current official Vercel source inspected on
2026-10-09, at upstream commit
`c628be7835e03a965b93e9cf9e2bd5ac2acbf5eb`:

- [FastAPI framework definition](https://github.com/vercel/vercel/blob/c628be7835e03a965b93e9cf9e2bd5ac2acbf5eb/packages/frameworks/src/frameworks.ts)
- [Python entrypoint detection](https://github.com/vercel/vercel/blob/c628be7835e03a965b93e9cf9e2bd5ac2acbf5eb/packages/python/src/entrypoint.ts)
- [Python function builder](https://github.com/vercel/vercel/blob/c628be7835e03a965b93e9cf9e2bd5ac2acbf5eb/packages/python/src/index.ts)
- [Function configuration schema](https://github.com/vercel/vercel/blob/c628be7835e03a965b93e9cf9e2bd5ac2acbf5eb/packages/build-utils/src/schemas.ts)
- [FastAPI deployment documentation](https://vercel.com/docs/frameworks/backend/fastapi)

This packaging agent performed static inspection only, with no application
tests, Vercel build, login or deployment. The final frozen application and its
actual managed services require independent verification before deployment.
