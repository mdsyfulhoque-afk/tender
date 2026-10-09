# Persistent TenderOS pilot on Vercel — minimum durable design

## Selected scope

The user selected a persistent pilot using a managed database and private file storage. The previous preview recommendation is superseded as the target. Build the durable adapter/auth/configuration now; deploy when the user's actual Vercel account/project and database/storage bindings are callable. User authorization persists, so these are technical access prerequisites, not renewed permission gates. No preview or temporary customer database should be substituted silently.

## Minimum architecture

Vercel Python FastAPI function + managed PostgreSQL + private S3-compatible object storage + authenticated single-owner workspace. The original SQLite/filesystem mode stays available for isolated local development; a Vercel deployment must require all durable bindings and authentication credentials and fail closed when they are absent. A single-owner workspace can hold several organization records without pretending separate customer identities are supported. Do not enable independent customer logins until real memberships/tenant authorization are implemented.

## Portable PostgreSQL adapter

The current application query subset is small: `execute(sql, params)`, cursor iteration/fetchone, `lastrowid`, commit/rollback and schema initialization. A narrow adapter preserves the deterministic domain engine with less change than an ORM rewrite.

- Use psycopg 3, dictionary rows, bounded connection/statement timeouts and the configured provider's TLS policy. Avoid logging raw connection strings, exception messages carrying credentials, or SQL parameter values.
- Preserve local `sqlite3` behavior. Choose PostgreSQL only from explicit hosted configuration; presence of Vercel runtime must forbid fallback to local SQLite. Hosted configuration validation should happen before creating any local data directories.
- Translate only the audited SQL parameter placeholder syntax. Current SQL contains parameter `?` placeholders and no question marks inside SQL literals. A placeholder conversion helper must preserve quotes or deliberately accept only the validated query subset; future arbitrary SQL must not inherit unsafe textual substitution. Parameters remain bound, not interpolated. PostgreSQL driver percent-formatting rules also need explicit coverage.
- Append `RETURNING id` only to INSERTs into a small explicit whitelist of current generated-ID tables: organizations, tenders, sources, requirements, evidence, decisions, audit_events. Capture the returned integer as cursor `lastrowid` without accidentally consuming normal SELECT rows. `pilot_metrics` has a provided tender primary key and UPSERT; do not append an imagined generated ID. Avoid LASTVAL session assumptions under connection pooling.
- Write an explicit PostgreSQL schema, not a modified SQLite script. Create organizations, tenders, sources and evidence before requirements; requirements currently references evidence created later, which SQLite accepts but PostgreSQL rejects. Use identity primary keys and real FK constraints. Preserve INTEGER 0/1 flags and nullable mandatory values; retain TEXT dates/timestamps/snapshots initially so existing JSON, hashes and strict attestation type checks stay consistent. Foreign-key IDs must use the same integer type as their referenced key. Keep amount semantics unchanged unless a separate money-type migration is requested.
- Keep `ON CONFLICT(tender_id) DO UPDATE` for metrics. SQLite PRAGMAs never reach PostgreSQL.
- Run migrations explicitly once through a bounded command with a migration version table and an advisory lock; do not run schema DDL on every Vercel cold start. An uninitialized database should fail a readiness check rather than serve an empty alternate store. Use an appropriately restricted runtime database role after schema setup.
- Define transaction boundaries clearly. Readiness/fingerprint snapshots perform multiple SELECTs and should read a consistent PostgreSQL snapshot (for example REPEATABLE READ) instead of silently mixing versions under default READ COMMITTED. Decision/source-attestation writes should lock their tender or use a tested isolation/retry approach; all mutations of requirements/source/evidence that participate in a decision must obey that approach. Retry only known rollback serialization cases, never uncertain commits blindly.
- A connection per request transaction is an acceptable initial pilot implementation when using the provider's serverless pooler and low concurrency, with no long-lived idle per-instance pool. Test real PostgreSQL behavior, rollback and multiple fresh connection instances; an adapter mock alone does not prove durable persistence.

## Private file adapter

Keep stored `sources.private_path` as an opaque object key in hosted mode. Separate LocalFileStore and PrivateObjectStore implementations behind put/get/delete, with no public URLs and no customer-supplied raw object key. For a single-owner pilot, unique keys scoped to source/tender (and explicit workspace) prevent overwrites; UUID plus SHA-256 metadata retains original provenance.

- Configure exact HTTPS endpoint, bucket, region and credentials via the platform secret store. No hardcoded provider IDs or default production bucket. Restrict SDK access to the selected bucket/key prefix. Bucket policy/access settings must prove private access; relying on an obscured key is not privacy. Encryption at rest and approved deployment geography are provider configuration, not inferred from S3 compatibility.
- Validate and extract PDF before writing. Store the immutable original bytes in the private object store, retaining SHA-256, byte count, page count and original name in PostgreSQL. In-memory parsing within a host-compatible limit avoids scratch files as a source of truth.
- Upload object, then transactionally insert source/candidates/audit. On known DB rollback, attempt orphan cleanup. On a DB commit response lost to a network fault, do not blindly delete an object that might back a committed source; resolve committed state by its unique object key or defer safe reconciliation. Object/database cross-resource consistency cannot be described as atomic.
- On object upload failure create no source/requirements. On database failure preserve the decision history and report a bounded error; cleanup failures need evidence, not swallowed claims. Add an orphan-reconciliation strategy rather than promising no possible orphans.
- Authenticated document retrieval must first resolve a source row and authorize the owner/workspace. Return bytes through protected server access or tightly scoped expiring URLs only if provider/access policy supports them. Do not make the bucket public to implement downloads. Raw paths/credentials must stay out of JSON, health and exports.
- Account for host request-size limits. Reduce server multipart PDF limit to a verified safe value initially or implement authenticated private direct-upload with size/type/hash checks and authorized completion. Existing 10 MiB limit cannot be assumed to fit Vercel. Encrypted PDF, decompression/parser resource exhaustion and scanning retention remain explicit pilot boundaries; reject unsupported input rather than treating 150 pages as a full parser-safety guarantee.

## Owner authentication and browser requests

A simple protected owner pilot can be concrete without pretending production multi-tenancy exists:

1. Configure one owner identity plus a high-entropy secret or password hash. Every product route, list/detail endpoint, source retrieval, export, docs and mutation must authenticate; health may expose only sanitized liveness. Use constant-time comparison and prevent brute-force attempts through tested rate limits or verified platform protection.
2. Browser-compatible choices are a login exchanging credentials for a Secure/HttpOnly/SameSite session, or HTTP Basic over HTTPS for a narrowly controlled pilot. Bearer tokens alone are not a complete browser product unless a secure login/session mechanism supplies fetch/export requests; avoid storing a long-lived secret in browser localStorage or URL query parameters.
3. Derive audit actor and commercial decision authority from the authenticated configured principal. Typed reviewer strings can remain explanatory display labels but must not establish identity or authorize another person. Do not claim an authenticated human signer if the app still accepts any reviewer as identity.
4. Verify exact same-origin for unsafe browser methods: scheme, host and normalized port against explicitly configured HTTPS origins. Do not allow any `.vercel.app` suffix or untrusted forwarded host. Reject cross-origin, null-origin and unsuitable scheme. Origin absence is not authentication; cookie/Basic browser mutations need a CSRF mechanism or deny missing Origin unless using an explicitly non-ambient authenticated machine API.
5. Logout/session expiry/revocation and owner secret rotation need defined behavior. Sessions must survive function instances through durable state or signed bounded-lifetime tokens, not a per-function in-memory store. Protect secrets and auth errors in logs.
6. Vercel deployment protection can supplement protection only after the actual project policy is verified. A deployment-protection prompt visible on a preview does not prove production/custom domains or bypass tokens are secure. Do not trust an arbitrary client header claiming Vercel user identity. Without independently verified protection coverage, include application authentication.

## Verification before release

Retain all existing local-mode workflow/decision/export regression tests. New independent verification should cover real PostgreSQL first-time migration and rerun, constraints and transaction rollbacks, generated IDs and dictionary row behavior, metrics UPSERT, independent cold-start processes seeing the same state, original decision history unchanged, source/evidence mutations making decisions stale, and concurrent snapshot/decision behavior.

Private-object verification should exercise provider failures and cleanup/ambiguous commit handling, authenticated retrieval and unauthorized access, key immutability, no secret URLs exposed, and DB/object SHA-256 consistency. Auth checks must cover every route family, docs/exports, same-origin writes, cross-origin/null/missing-Origin variants, sessions across processes and configured principal binding. Hosted startup with any missing auth/database/private-storage configuration must fail closed.

After a real Vercel account/project connection arrives, deploy to the user's selected project and verify health, login, organization/tender creation, PDF source persistence, source retrieval, decision gate/export, and persistence after fresh invocation. Use only synthetic data for smoke checks. Publish the real returned deployment URL and actual storage/account binding evidence with secrets redacted. Until those calls succeed, status is prepared, not deployed.

## Access status and audit limits

Parent reports the user confirmed connection, but callable tools still do not expose actual Vercel account/project access or managed storage bindings. Code preparation can proceed. Actual deployment cannot be truthfully claimed from the confirmation alone; inspect the connection/tool availability and network-capable environment before using provider identifiers. Request only the missing technical connection/binding if it remains unavailable, not repeated authorization.

This supplement is design only. No code edits, tests, network/credential scans or provider operations were performed. Genuine task identity `/root/tenderos_vercel_architecture`; separate opaque run ID is unavailable and recorded null.
