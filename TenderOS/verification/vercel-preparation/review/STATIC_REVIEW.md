# Independent static review: Vercel persistent pilot

- Candidate: `c513e5af95248a11597718b950e5b4456d423d73`.
- Reviewer: `/root/tenderos_vercel_review`; opaque run ID unavailable (`null`).
- Verdict: **PASS for bounded static inspection only**. No blocking concrete defect found.
- Evidence: `static_review.json`, including 13 source hashes and public upstream snapshot hashes.

## Reviewed

Hosted mode avoids local directory/database initialization and cold-start DDL, requires managed PostgreSQL/private Blob/authentication configuration, and has no SQLite fallback. All routes share exact Host/HTTPS checks and single-owner Basic authentication. Mutations require an authenticated per-origin CSRF token; authenticated identity replaces user-supplied reviewer and audit names.

SQL remains parameter-bound. The PostgreSQL adapter returns IDs through explicit `RETURNING id`; schema types and foreign-key order align with application queries. Each route has one serializable transaction with bounded database timeouts; conflict/unavailable responses suppress provider details. Migration is explicit, transactional, advisory locked and digest marked, with no destructive operations or local data migration.

Private PDF writes follow the inspected official Blob PUT/header/response protocol, refuse redirects and reject a nonprivate response URL. Keys are randomized; private URLs/tokens are not returned to the browser. Objects remain after ambiguous database commit outcomes.

Native Python entrypoint processing maps `app/main.py` to `app.main`; the installed builder's static discovery imports the dotted module with project root on `sys.path`. A namespace package without `__init__.py` supports the current relative imports. Upload allowlist contains every runtime module and asset and excludes archives, receipts, local databases, uploads and credentials.

Five Python sources compiled in memory without executing imports, and JavaScript syntax compilation exited successfully. Seven domain/export function ASTs are identical to repaired baseline `bac1dce`, including decision currency, evidence/source invalidation, legacy handling and spreadsheet literals.

## Operating notes

- Health checks an organizations-table read and configuration shape. Actual private Blob authorization, complete migration, build routing and persistence need live verification.
- Conservatively retained private-object orphans need operator reconciliation.
- Original-PDF retrieval through the application is absent, as in the baseline. The owner needs retained originals or authorized provider retrieval when reviewing source documents.

## Limits

No unit/API/database/browser tests, application import, provider calls, customer data or credentials were used. Previous test counts remain historical. This review does not establish account connection, successful migration/deployment, production protection or persistence across function instances. Keep deployment/durability status unverified until the actual platform result and live checks exist.

The frozen checkout remained clean. Tool executions are recorded in this agent's Codex transcript; no source edits, commits or provider actions occurred.
