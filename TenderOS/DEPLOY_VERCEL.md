# TenderOS on Vercel

## Deployment target

The user authorized a persistent pilot on their Vercel account using a managed
database and private file storage. This commit prepares packaging; it does not
implement those services or establish an account connection or deployment URL.

**The current local SQLite application cannot be deployed unchanged.** Import
creates a database and uploads inside the application package. Vercel functions
do not provide durable writable application storage. `TENDEROS_DATA_DIR=/tmp/...`
would create disposable instance state and is not configured here.

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

## Prerequisites for the persistent pilot

Before creating a usable deployment, integrate and independently verify:

1. A managed database adapter and migrations preserving state across function
   instances, immutable decisions and attestations. A URL alone does not adapt
   the current `sqlite3` calls.
2. Private PDF object storage preserving SHA-256 and provenance; database-only
   persistence leaves the current local uploads volatile.
3. Authentication and authorization on every data/document/decision/export
   endpoint. The current app has neither. Enable and verify Vercel Deployment
   Protection where available for the intended environment.
4. Exact hosted origin/CSRF handling. Current localhost-only Origin validation
   rejects hosted browser mutations with 403.
5. Uploads compatible with actual Vercel ingress/execution limits. The local
   10 MiB PDF limit does not raise the host request limit. Prefer authenticated
   private-storage direct uploads with verified ownership, size, type and hash.

Configure the implemented adapters' actual secrets in Vercel Environment
Variables; provider choices and variable names are not invented here. Keep
credentials, customer PDFs and databases out of source/deployment files. Hosted
startup must fail when persistent services or authentication are unavailable.

## File boundaries

`.vercelignore` allows CLI uploads of the current module, three static assets,
dependencies and configuration only. Add new runtime files explicitly. Knowledge,
receipts, tests, databases, uploads, logs, dotenv and Vercel local state are
excluded by default; `vercel.json` also excludes them from the function bundle.

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
2. Configure managed-service/authentication variables and protection, then
   deploy a Preview from the reviewed commit.
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

Only static configuration and source inspection were performed for this
packaging step. No application tests, Vercel build, login or deployment were run.
