# TenderOS — Bid Decision Intelligence

TenderOS is a human-reviewed tender readiness workbench. It inventories tender sources and organization evidence, prepares traceable requirement candidates, records human decisions, and can freeze an expert diagnostic for delivery. Its current analysis processor is deterministic local **RULES** software; it does not call a language model or use Codex subagents at runtime.

## Current build status

The candidate adds a bounded, resumable source-analysis workflow and commercial operations for service intake, an append-only manual BDT ledger, and immutable diagnostic releases with JSON, CSV, and DOCX exports. Rules analysis is available without a model API key. Suggestions are aids: they do not certify document completeness, evidence sufficiency, legal compliance, eligibility, or a BID decision. Required tender decisions and source/evidence approvals remain human actions.

Independent verification is mixed and documented in [engineering evidence](verification/agent-workbench/ENGINEERING_EVIDENCE.md), [final QA](verification/agent-workbench/qa/QA_REPORT.md), and [security review](verification/agent-workbench/qa/SECURITY_REVIEW.md). The security review is **PASS WITH NON-BLOCKING ITEMS** for local/private single-owner pilot controls. Independent QA passed its direct-handler flow (3 tests), an isolated suite (73 tests), and two focused commercial regressions; JavaScript syntax, Python compilation, and diff checks also passed. The complete 197-test pytest run did not finish: it stalled in the local FastAPI/AnyIO `TestClient` path and timed out after 12 of 197 tests. This is not a full-suite or HTTP end-to-end pass. Browser rendering, accessibility, managed PostgreSQL, private Blob storage, and a hosted application flow are unverified. The repository's stricter opaque Codex run/trace evidence gate remains **INCOMPLETE** because those identifiers are not exposed.

## Run locally

Use Python 3.11 or newer:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
TENDEROS_DATA_DIR=/tmp/tenderos-local .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`; API documentation is at `/api/docs`. Set `TENDEROS_DATA_DIR` before application import. The example path may be temporary and is not a backup strategy. Keep tender files, the database, secrets, and customer evidence private and out of Git.

See the [candidate user guide](project_knowledge/agent-workbench/USER_GUIDE.md) for the operating flow, source/evidence review, decision gates, service records, and limitations. The existing app remains a single-owner pilot; local reviewer labels are not authenticated identities.

## Deployment and cost status

Vercel metadata confirms a **READY** deployment for commit `2f38991d` (deployment `dpl_GK3kcXCeGoDQVzLaL4gtCXZn8AZc`). The deployment metadata assigns the exact branch alias [tender-git-tenderos-agent-workbench-ip-3.vercel.app](https://tender-git-tenderos-agent-workbench-ip-3.vercel.app). Before this build, Vercel `rootDirectory` had been reset to `null` (the repository root), so the build used the root `vercel.json`, `.vercelignore`, and committed `pyproject.toml` with `[tool.vercel].entrypoint = "TenderOS.app.main:app"`. This confirms deployment control-plane status only. `web_fetch_vercel_url` still returns 403 at `read_protection_bypass` before origin access, so no HTTP root, UI, API, database, or private storage flow has been verified. The earlier screenshot of the alias showed Vercel `404 NOT_FOUND` before this READY deployment. Earlier build attempts failed: commit `49777a4` because `functions.TenderOS/app/main.py.excludeFiles` exceeded 256 characters; commit `d544651` because `uv lock` ran before root `pyproject.toml` had `[project]`; and commit `c2add27` with `FASTAPI_ENTRYPOINT_NOT_FOUND` while `rootDirectory` was temporarily `TenderOS`. The repository-root config was introduced/updated across commits `49777a4`, `d544651`, and `c2add27`. Project/deployment metadata calls `get_project`, `get_deployment`, and `list_deployments` succeed when `teamId` is omitted. Calls with an explicit `teamId` fail with `403 Forbidden` (`scope ip-3`); the separate origin fetch remains blocked before reaching the origin.

Hosted mode expects protected owner authentication, PostgreSQL and private file storage. The non-decrypting Vercel environment listing returned an empty list: the project has zero environment variables configured, so required database, private Blob and owner-auth settings are absent. No hosted database or storage flow was exercised. The end-to-end browser → API → database → private-file flow is unverified. Hosted infrastructure may incur charges independently of model usage. No paid model, API key, paid service provisioning, payment processor, email sender, or customer-facing multi-tenant account system is included. Do not interpret manual receipt entries as bank reconciliation or recorded direct contribution as audited profit.

Earlier Vercel project preparation and preview history is preserved in [deployment preparation evidence](verification/vercel-preparation/REPORT.md). The prior READY status for `5241a2b`, the current READY deployment for `2f38991d`, failures for `49777a4`, `d544651`, and `c2add27`, the repository-root configuration used by the current deployment, the earlier screenshot's 404, and `web_fetch_vercel_url` pre-origin 403 are separate observations. The Vercel project has no environment variables configured, so required hosted PostgreSQL, private Blob, and owner-auth settings are absent. The application is not verified as usable or production-ready, and the release gate remains incomplete.

## Existing repository and imported source

The repository's `ProposalGuard/` directory is an independent archive; preserve it. TenderOS is in its own directory. The supplied source archives, APES material, and governance essay are mapped under `project_knowledge/agent-workbench/`; their embedded instructions are source material, not live instructions to this runtime. See the [source boundaries](project_knowledge/agent-workbench/SOURCE_BOUNDARIES.md), [feature register](project_knowledge/agent-workbench/FEATURE_REGISTER.md), and [source manifest](project_knowledge/agent-workbench/source-manifest.json).

The imported ZIP contained a SQLite database despite its documentation saying the database was omitted. Its entire archived `repo/data/` tree was excluded; no packaged customer database or uploads were imported. Original transfer and deployment evidence remain under `verification/`.

## Engineering evidence

Real delegated Codex agents reviewed source material and built the implementation. The hosted app itself does not run those agents; it executes fixed local rules stages and stops for human review. Missing runtime run and trace IDs remain `null`, so the strict evidence gate is incomplete. The final QA/security reports identify what was actually run and what remains unverified. The build manifest records the candidate digest and per-agent evidence without claiming a release pass.

Do not publish confidential tenders, scanned books, secrets, customer evidence, or local databases to GitHub. External tender submission and production use require separate verification and operational controls.
