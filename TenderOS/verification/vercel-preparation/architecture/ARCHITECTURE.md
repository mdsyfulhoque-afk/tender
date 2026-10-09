# TenderOS Vercel deployment architecture audit

## Audited state and authorization

Read-only audit of integration commit `bac1dceabf67a3e563c3f1a60f9f10369e709eb4`, using genuine delegated agent `/root/tenderos_vercel_architecture`. User explicitly requested deployment into their Vercel. This provides deployment authorization; no renewed approval is required for preparing the requested deployment. It does not provide a logged-in account, durable database, private object storage, or an authenticated customer identity system. No network calls, credentials scans, tests, app edits, or external changes were performed by this audit.

## Current code cannot be copied directly to Vercel as a durable pilot

1. **Import writes to application files.** `app/main.py:25-30` creates a package-relative data directory and private-upload directory; module import then executes the SQLite schema. A Vercel function's deployed application filesystem is not durable writable application storage. Setting `TENDEROS_DATA_DIR=/tmp/...` would make startup possible but does not solve persistence: cold starts and concurrent instances would have different databases and private files. Success from one request would not prove the next request sees its organization, tender, evidence or decision.
2. **Hosted browser writes are rejected.** `main.py:284-292` accepts Origin host only localhost/127.0.0.1. Browser fetch POST/PUT requests from the hosted origin will be 403 even if its hostname matches the deployed request. HTTP requests without Origin remain accepted; this middleware is not authentication.
3. **Data is shared and unauthenticated.** Organizations/tenders listing APIs return all records. No route authenticates a user or enforces membership/roles. Evidence is checked against the selected organization, but the caller is not authorized to that organization. Reviewer names are unverified strings.
4. **Private uploads are local files.** `main.py:480-487` writes bytes beneath `STORAGE` and records a relative path. Remote database alone would leave source documents volatile. The code has no document-download endpoint, but provenance claims depend on preserving the original document.
5. **Upload maximum needs host validation.** App accepts a 10 MiB multipart PDF and 150 pages. Serverless ingress and execution limits may be lower than this; current Vercel plan limits must be checked before selecting an upload path. Real files should use an authenticated direct-to-private-object-storage upload with explicit quota enforcement and a verified object-to-tender association, rather than assuming the current multipart endpoint fits.
6. **No deployment config exists.** Root should be `TenderOS`, not repository root containing ProposalGuard. A Python FastAPI function entrypoint is required. Dependency manifest includes test packages; production manifest should separate runtime and development dependencies and lock the versions actually verified for deployment.

## Recommended immediate implementation

Prepare a **clearly identified, read-only synthetic preview** for Vercel while account access is being established. This is a useful deployment artifact that can truthfully show the repaired assessment and export experience without accepting confidential uploads or pretending SQLite is durable. It is not a customer pilot.

- Keep local pilot behavior unchanged unless explicit deployment mode is selected.
- Separate hosted preview entrypoint/config under `TenderOS` with explicit synthetic-preview mode. Use Vercel's supported Python/FastAPI entrypoint routing after confirming current deployment tooling; route `/`, `/static/*`, `/api/*`, docs and exports to that app. Do not guess a custom Python runtime string.
- Generate deterministic synthetic data through a deployment seed step or packaged synthetic fixture. Do not copy any archived database or uploads. If copying a synthetic DB into `/tmp` on startup, make the server deny all client mutations so the copy is a cache, never represented as persistent storage. Concurrent cold starts then serve equivalent data.
- Prefer server denial of every POST/PUT/PATCH/DELETE before processing its body; permit only read-only routes, current synthetic detail and exports. Remove all customer-entry and upload UI forms and the mutating Load Demo button in this mode; show synthetic examples directly.
- Use platform deployment protection where available. A public preview may expose only predefined synthetic information, never API endpoints that accept or preserve arbitrary real tender/customer records. Platform protection availability needs inspection in the user's Vercel project; do not claim it exists before verifying.
- Health/UI must say `SYNTHETIC_PREVIEW`, `read_only=true`, `durable_storage=false`, and no external models. Replace the misleading hosted claims that documents remain local with the actual mode.
- Origin validation should compare exact configured HTTPS origins (scheme, host and normalized port) or exact request origin with strict trusted-host handling. Keep localhost development behavior explicit. Do not accept wildcard `*.vercel.app`, suffix matching, arbitrary forwarded-host headers, or requestless Origin as an identity check.
- Prevent release-mode fallback: hosted mutable pilot startup must fail if durable/authenticated storage is not configured; no silent `/tmp` fallback.
- Independent verifier should check source-preserved local regressions, preview endpoint behavior including hostile methods/origins and API routes outside UI, header behavior, synthetic exports, and function entrypoint import without writing inside deployed code. Account/API deployment smoke checks remain outstanding until Vercel is reachable.

A static preview is another valid narrow fallback, but it cannot be described as a working FastAPI assessment application. No deploy URL can be generated by local preparation.

## Durable pilot implementation choices

**Preferred full hosted product:** Vercel serves FastAPI/UI with a remote PostgreSQL database and private object storage. Add an authenticated identity and membership/role checks before enabling customer operations. Use actual configured providers rather than inventing connection strings or credentials. Database transactions must continue to preserve immutable decisions and attestation identities.

Concrete work: introduce a database adapter and migrations (SQLite SQL uses `?` placeholders, `executescript`, `lastrowid` and SQLite-specific transaction behavior); support a pooled serverless-compatible PostgreSQL driver; object-storage adapter retains SHA-256/provenance and supports restricted access; trusted authenticated principal rather than typed reviewer establishes authorization; all list/detail/create/review/decision/export endpoints filter tenant membership. Add exact origin/CSRF handling for the chosen session model. Run tests with independent DB connections and cold-start equivalents to prove state survives function instances. Backups/recovery, limits, retention and data geography must be configured, not inferred from the hosting provider.

**Alternative minimum changes to local domain core:** put the existing FastAPI application on a persistent private service with backed-up mounted SQLite/storage, authentication and tenant access enforcement, then use Vercel as the frontend/same-origin gateway. This avoids rewriting storage immediately but requires a separate persistent backend host; Vercel cannot provide a mounted durable SQLite filesystem to its serverless function. Do not forward customer data to an arbitrary newly invented service.

**Remote SQLite/libSQL:** possible as a separately scoped adapter, but not a drop-in `sqlite3.connect(DB)` path. Remote transactions, row factories, scripts, placeholders and affected-row/last-ID behavior must be explicitly tested; private PDF object storage and auth are still necessary. It is not a shortcut that validates current unchanged code.

## Account/environment dependencies

Parent reports no Vercel account credentials, project binding or CLI and network restrictions excluding Vercel endpoints. Deployment requires a Vercel account/project connection or an authorized network-capable environment; durable pilot also needs the selected database/private-storage resources. These are access prerequisites, not renewed approval gates. Prepare code, configuration, verification and a exact deployment command while obtaining that access. Do not publish a fake URL, invent project IDs or claim an external deployment was performed.

## Evidence limits

This is a source architecture audit; no Vercel build/runtime was executed. Host-specific routing, Python versions, request size, deployment protection and plan limits require verification against the connected project's current platform behavior. The agent runtime exposes canonical task identity, not a separate opaque run ID; `run_id` is recorded null rather than fabricated.
