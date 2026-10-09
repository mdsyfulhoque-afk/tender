# TenderOS persistent Vercel pilot preparation

Status: **PREPARED; DEPLOYMENT BLOCKED BY WORKSPACE ACCESS**. The user explicitly authorized deployment to their Vercel account and selected a persistent pilot with managed database and private file storage. No additional deployment approval is requested.

Reviewed source candidate: `c513e5af95248a11597718b950e5b4456d423d73`, following native packaging commit `d71f807cb19114ed26ddf2127ef60c4edff9d206`, on branch `tenderos/deploy-vercel`. This branch builds on repaired integration head `bac1dceabf67a3e563c3f1a60f9f10369e709eb4`.

## Prepared implementation

- Native Vercel FastAPI entrypoint `app.main:app`, with a restricted runtime upload list and function bundle exclusions. Receipts, knowledge, tests, scripts, databases, dotenv files and private uploads are excluded from the deployment artifact.
- Hosted mode uses PostgreSQL through a bound-parameter adapter, explicit generated IDs and serializable request transactions. It preserves the local SQLite development mode. Hosted requests never initialize SQLite, use temporary files for persistent state or run startup schema DDL.
- An explicit PostgreSQL migration uses a transaction, advisory lock and schema digest. It requires an empty dedicated database and does not import a customer SQLite database.
- PDFs use a native private Vercel Blob store, with a fixed HTTPS provider endpoint, private access request, redirect refusal and verification of returned private object metadata. Object keys contain no source filename. Database commit ambiguity retains private objects for operator reconciliation.
- All hosted routes, including UI/assets/docs/health/exports, require the configured owner's Basic credentials. HTTPS and exact trusted origins are required; writes also require a token from authenticated health. Review and audit identity derives from the authenticated owner.
- Hosted PDF payload limit is 4 MiB to fit Vercel's request envelope; local mode keeps 10 MiB. The UI describes cloud storage accurately and includes its CSRF header.

This is one private owner workspace, without customer logins or a multi-tenant role system. It retains keyword PDF candidates and human source/evidence/BID review; it introduces no model calls.

## Genuine delegated work and independent review

| Canonical runtime task | Contribution | Evidence |
| --- | --- | --- |
| `/root/tenderos_vercel_architecture` | Read-only local/serverless and persistent-pilot design | [Persistent design](architecture/PERSISTENT_PILOT_DESIGN.md) |
| `/root/tenderos_vercel_packaging` | Native framework configuration and artifact boundaries | [Packaging receipt](packaging/PACKAGING_PERSISTENT_FOLLOWUP_RECEIPT.json) |
| `/root/tenderos_vercel_app` | Hosted authentication, identity, origin/CSRF, UI and upload integration | [App receipt](app/static-review.json) |
| `/root/tenderos_vercel_storage` | PostgreSQL adapter/migration and private Blob protocol | [Storage receipt](storage/storage-receipt.json) |
| `/root/tenderos_vercel_operator` | Official CLI installation and actual account/network preflight | [Operator sequence](operator/DEPLOYMENT_SEQUENCE.md) |
| `/root/tenderos_vercel_review` | Independent frozen-source static security/compatibility review | [Static review](review/STATIC_REVIEW.md) |

The independent reviewer found no concrete blocking static defect. Five Python sources compiled in memory without imports, JavaScript syntax inspection passed, and the ASTs of seven decision/evidence/export functions match the repaired baseline. Official native builder source confirms the dotted `app.main` entrypoint supports relative imports without an `__init__.py`.

**No application tests ran for this candidate. No live database, Blob authorization, Vercel build/deployment or persistence validation has completed.** Earlier passing tests under `../scoped-repairs/` describe the earlier repaired candidate, not this hosted implementation. A static PASS is not a live deployment or durability result.

Runtime identities are actual canonical task identifiers from `collaboration.spawn_agent`/`followup_task`. Receipts contain genuine tool trace IDs and available UTC observations. Separate opaque run IDs are not exposed and remain null; the historical stricter receipt gate is not asserted as passed. Only delegated coding agents modified runtime source.

## Confirmed deployment access blocker

The Vercel plugin is installed. It exposes guidance in fresh task contexts, without callable Vercel account tools. The official CLI was installed outside application source: version **63.1.0**.

Actual preflight:

- `vercel whoami --format json --non-interactive`: exit 1, `loggedIn: false`.
- This cloud environment has no Vercel token binding or linked project.
- An unauthenticated HEAD request to `https://api.vercel.com/v2/user` through the inherited proxy fails with CONNECT **403 Forbidden**. Current enforced network policy allows package-manager endpoints and excludes Vercel API/authentication hosts. No credential was sent.
- A read-only CLI integration query unexpectedly attempted its login flow and failed to reach authentication. No account login or resource operation succeeded; this is preserved in [the attempted command record](operator/categories-attempt.json).

The pending user input requests a securely configured `VERCEL_TOKEN` workspace secret and supported network access to `api.vercel.com`, or an authenticated local environment. Token values must stay out of chat/source/command logs. Authentication hosts, and later the actual database/deployment/storage hosts, also need supported access when those operations are performed. No alternative egress route was attempted.

## Execution after access is configured

Use [DEPLOY_VERCEL.md](../../DEPLOY_VERCEL.md) and the operator sequence to inspect actual owner/team/project, select an existing suitable project or create TenderOS, provision/connect verified managed PostgreSQL and a private Blob store, securely configure owner credentials/origins, apply the migration and deploy the reviewed source. Resource IDs, provider terms/prices and endpoint names must come from the actual account responses.

The CLI artifact can be staged with only the approved runtime files and project root `.`. Git deployment instead uses Root Directory `TenderOS` and may clone the private repository; `.vercelignore` cannot prevent a Git clone. The chosen deployment must use the correct actual project root.

Before reporting completion, confirm build/runtime status, owner login, authenticated routes, private Blob permissions and persistence across new instances/redeployment. Record the actual project/deployment IDs and URL. No project, managed database, Blob store or deployment has been created yet, and no live URL is claimed.

## Stored evidence

[EVIDENCE_COPY.json](EVIDENCE_COPY.json) maps byte-identical external execution reports into this archive. [Output hashes](output-hashes.json) cover stored evidence. No CLI account state, credentials, runtime databases, customer documents or npm installation cache is included.
