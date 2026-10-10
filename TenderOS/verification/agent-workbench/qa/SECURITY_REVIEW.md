# Independent security review — TenderOS agent workbench

Gate recommendation: **PASS WITH NON-BLOCKING ITEMS** for the reviewed local/private single-owner pilot controls. All three confirmed new implementation findings were repaired by separate delegated coding agents and independently rechecked. This is not production deployment approval or a certification of the missing opaque-runtime proof gate.

## Reviewer and observed inputs

- Canonical reviewer `/root/independent_security_review`, genuinely separately delegated using `collaboration.spawn_agent`; root follow-up explicitly requested final review.
- Opaque platform run ID: `null`; exported tool trace ID: `null`; the runtime exposes neither. Actual inspected code, tool calls and reported results are the evidence. This does not certify the repository's stricter opaque-run-ID gate.
- Worktree `/workspace/tenderos-agent-workbench`, branch `tenderos/agent-workbench`, base commit `6f7ac1156e595f9f87d6f32d99492f8a704e9849`.
- Initial review began 2026-10-09T20:25:29Z; final rereview requested 2026-10-10.
- Allowed actions: read source, run requested independent synthetic/local verification, write this review. No application/test edits, commits, model/provider calls, paid services or external network calls were performed by this reviewer.

## Confirmed findings and disposition

### SEC-01 — MINOR: final receipt omitted from aggregate artifact budget

`app/workflows.py:472` checks prior plus current stage payload against max_artifact_bytes; `:489` then inserts a RUN_RECEIPT without including its bytes. Independent direct-engine reproduction with a synthetic one-page source, setting a reduced test cap equal to prior artifacts plus final citation (1,981 bytes), returned publish=true and WAITING_HUMAN while storing 5,177 payload bytes. Excess was 3,196 receipt bytes. This is a concrete advertised bound error; it does not authorize inference, alter human gates or expose another organization's evidence. Root assigned a separately delegated narrow repair. **REPAIRED / RECHECK PASS:** the same reduced-cap probe now stores exactly 1,981 bytes, returns publish=false, reports BUDGET_EXHAUSTED/ARTIFACT_LIMIT and final step FAILED, preserves the bounded citation/prior artifacts, and stores no oversized RUN_RECEIPT. The final receipt is counted before reaching the human gate.

Earlier related usage error was repaired: the frozen receipt originally used the final reserved processing time. The current implementation updates job['elapsed_ms'] after reconciliation; an independent synthetic run recorded matching frozen/live elapsed values (5 ms).

### SEC-02 — MINOR: current-input growth prevents historical run inspection/export

`app/workflows.py:64–68` limits current input record counts and raises HTTP413; currency() reuses manifest() for historical detail/list/receipt. Independent reproduction: complete one-source run, append 501 otherwise valid same-organization evidence records with unchanged sources, then detail() and receipt() both raise413. Five immutable artifacts remain stored but become unavailable to the owner through these APIs. This violates the stated retained-history behavior and prevents narrowly source-current candidate inspection after unrelated vault growth. New run/advance limits should remain enforced while historical reads disclose bounded unavailable full currency, separately check source scope, and retain downloadable frozen artifacts. **REPAIRED / RECHECK PASS:** the same actual 501-evidence probe now allows detail/list/receipt, preserves all five artifacts, marks full currency false with BOUNDED_CURRENT_INPUT and source_current=true. Source-current ACCEPT still creates only UNKNOWN/unreviewed/mandatory=NULL content. Creating a fresh over-limit run still rejects413; history availability does not enable unbounded new processing.

### SEC-03 — MINOR: raw text size failed to bound serialized page payload

On pre-repair `workflows.py` SHA256 `61f6a62af7d8349e6d898845ccb6f540de154f833fbadc0f935dc3e50e24338b`, SOURCE_INSPECT checked raw UTF-8 length plus 500 bytes rather than the actual canonical JSON page. A valid synthetic PDF produced with `synthetic_pdf(('certificate ' + '\x00' * 18000,))` is 18,628 bytes; it extracts 18,013 characters, but its JSON page record is 108,267 bytes. The code retained TEXT_READY despite the configured 65,536-byte page cap. This was independently measured using the direct engine with an actual hash-registered synthetic private PDF; no provider/model call was involved.

**REPAIRED / RECHECK PASS:** on final workflow SHA256 `b1a239494fb7b1ae9cb8fbfb706e575e30afbd778fd4f27c6c07287dd63d42d0`, `workflows.py:346` checks the canonical full page record. The exact reproducer now records INCOMPLETE_BOUND, an explicit coverage issue, the actual original character count 18,013, omitted text and its honest empty-text hash. Stored page JSON is 259 bytes. Running all remaining stages yields WAITING_HUMAN with the retained incompleteness issue and zero candidates. Registered original hash is unchanged; no requirement, decision, source attestation or evidence verification is created.

## Inspected controls

- Fixed RULES request schema and four registered tasks; no provider, arbitrary URL, shell, payment, messaging, training or model execution path in workflow/commercial modules. Policy caps model spend at zero and labels local model UNCONFIGURED. Product-generated attempt IDs are distinct from unavailable Codex runtime IDs.
- Human candidate ACCEPT rechecks current source scope and real PDF quote, deduplicates, and creates only unreviewed UNKNOWN requirements with mandatory=NULL. Worker outputs do not verify evidence, attest sources, record decisions or submit bids. Accepting a proposal may stale full analysis while other unchanged-source proposals remain reviewable.
- Every job route scopes tender/job IDs; evidence matching freezes only same-organization evidence and latest registered file identity. Citation stage independently rereads source PDFs; evidence checks explicitly state metadata version validation with content_verified=false.
- Lease/fence/revision/cancel conditions gate publish; source computation occurs outside the write transaction. Claims reserve time, crash reservations remain charged, attempts stop at two; old/cancelled workers cannot publish. Local BEGIN IMMEDIATE and hosted serializable transactions protect check/write sequences.
- Parameterized SQL only. Additive local/PostgreSQL v3/v4, original v1/v2 bytes/digests preserved, frozen workflow identities and append-only artifacts/events/reviews, same-tender predecessor/artifact/restart/review guards. Hosted startup executes no migration DDL.
- Commercial ledger accepts strict integer BDT minor units; exact idempotency, same-kind manual reference duplicate guard, same-tender original corrections, no correction of correction, and cumulative refund/reversal cap. Actual recorded receipts differ from quotes and legacy pilot totals. Unknown overhead remains explicit.
- Diagnostic capture is server-derived; payload and prior versions remain immutable; JSON hash checked on frozen detail/export. Fresh context governs current/stale labels. CSV protects formula-like dynamic text; DOCX safely renders XML-invalid text with visible substitutions while preserving frozen JSON/CSV values.
- All new routes share existing hosted owner Basic authentication, exact configured HTTPS origin and mutation CSRF middleware. New UI uses same-origin API helper/CSRF, escaped dynamic markup/textContent, fixed numeric file/report paths, and noopener for original documents. Packaging allowlist includes every new runtime module.

## Actual independent verification so far

- Persistence coder's existing schema suite was separately executed by this reviewer: 57 passed.
- Existing domain workflow suite was separately executed by this reviewer: 93 passed; one Starlette TestClient deprecation warning. These two runs precede final integrated candidate freeze and are not presented as final complete acceptance.
- Independent inline direct/API synthetic probes: source PDF with two candidate clauses including instruction-like text; all stages and valid quotes; no model enablement/action; cross-tender detail/advance rejected404; two sequential ACCEPTs produce only unreviewed UNKNOWN rows and no decisions/attestation; cancelled publish false and no artifacts; expired lease increments fence, old publish false, 30,000 ms of two abandoned reservations retained. All passed.
- Independent original reproductions initially failed SEC-01/02/03 and were sent with exact input/result evidence to the parent/coders. Re-running all three against repaired code passed as detailed above. These are independent inline synthetic probes, not fabricated test-suite counts.
- Final code inspection included repaired elapsed reconciliation, final receipt aggregate budgeting, conservative historical currency fallback and exact canonical page budgeting. No remaining reproducible new scope, human-gate, provider/spend, ledger, report injection or CSRF defect was identified in this review.
- No live managed PostgreSQL, Blob, Vercel deployment, browser accessibility/visual flow, paid inference or external account verification was performed by this reviewer. A separate final QA delegate owns final end-to-end checks.

## Practical scope limits

The reviewed app is a local/private single-owner pilot, not authenticated customer SaaS tenants. Local operator names are unauthenticated. No shipped model inference, OCR, always-on scheduler or hard parser resource sandbox exists; cooperative PDF/page/artifact limits do not prove a malicious parser cannot hang. Hosted managed resources/root-directory repair and infrastructure cost remain unverified. Reported receipts are manual observations, not bank reconciliation or evidence of guaranteed profit. Missing opaque platform IDs remain a documented engineering proof limit.

## Final reviewed candidate source hashes

```text
AGENTS.md 1fbca1e2b3c5be11438c39aa7e4b2ab7f02554e62dfd1ed1a3f9f670cdfa3ef6
app/main.py da26ba8d838ce3bd33319e1b1956bada4e067db7b445e029c9e8da1f94ff30d9
app/database.py 4d2e5d9129d89053fa02ad17aadf239d2bf515bf9b6cb519ed495624ca81a373
app/hosting.py ab0bf67310596abf67b8739ef4f7c5f7ac24e833638c760af1545aae6569d8a8
app/private_storage.py b3cd4bc6d0be0d6019775804e9fef4f089ca43601e62f85b3a281f9157caa379
app/workflows.py b1a239494fb7b1ae9cb8fbfb706e575e30afbd778fd4f27c6c07287dd63d42d0
app/workflow_contracts.py d024cd8496a951c73aa065fc9e1b8a2e80b99bf58e9a884aacd8122a5f75d7f1
app/workflow_routes.py 649c8c07a7b452cd7e84a939649e46b41d777fbbc50d0c67d100f3409117989b
app/workflow_schema.py dcf3678836a7407550b6375770d50a3ed3ba27c82e8f6c107c175daa9dfc82b7
app/commercial.py 5276c66b625560843dd0b9a6d92b139d34cc708a04557e8230e04e92d8b241ad
app/commercial_schema.py bd995bfc92e49e0d9458aeedf7389c0b4d42c69d2bd400ebba2908038d620c0a
app/static/ui.js ec7bd229b37c10dd3b4aae34c2ff20015a72b975b0b04c266c8eb64a51529df5
app/static/style.css faf399ff2edbbc3cb0d63cb3daf0ce8d5abc6af810984cf9b62e124e7e051861
app/static/index.html ee9f8dc6131412d7c0764e6676d43be02096ef20fa5cb8bf2c906594ab373615
scripts/migrate_postgres.py d53e9c42525d9fc04070e37f5ed61617018348079f8d75f25523f33c3dceb693
scripts/postgres_schema.sql 92dab3cbda0388c278f06ca7610a0b53bde2b13edff3bed770b4f709093a268e
scripts/postgres_migrations/002_document_registry.sql 3e10701dc7ce074663fa3ab051e8ee4c3ebc9be51a0d02fb7dd4341b0d2bc5c7
scripts/postgres_migrations/003_bounded_workflows.sql 9441f18c2cc69f99b9ff84c82b87a7d175a2a89d1952c64b49dc54d33f3595d9
scripts/postgres_migrations/004_commercial_operations.sql 33bdb04c5d9bb5df62169aa07eac7e9dd539b7d4241ecfa53165cbcbd66f69e7
.vercelignore 639ddf777b3f06e8121c56fcb6e9b6ee9b20fb39a45bea9fab29a0ec46f5316a
tests/conftest.py 2ec1e36f1f476a733e93d6b9a3404eaea6bd7d3d10c868f6cdc77828f68b30be
tests/test_agent_workbench_independent.py 5bca06e95af2ba4ec494517eae443fe9e85a8f43102af95868853edb3dd6ec92
tests/test_bounded_workflows_contract.py 8eac4520e738e6a25342a34251dd2fd61981414d25764a4d71b0e040fd74e44d
tests/test_commercial_operations.py dd1cded4d3556ec5ac3cbd7704fa685fb455c16d9f29692d40d45ff7291c2457
tests/test_workflow_currency_bound.py b1bdcbb29bc9a8bab922530f4afe660d83aad7a6a79cca729365c57b4997dfd7
tests/test_workflow_receipt_budget.py 13eed41b96eb7b7d63b07c6f4aacd24e4c882e29d651f988b49fa7f81bdc0610
tests/test_workflow_schema.py 18ca4650bbcd8ce24d986a679e0392fc6b4b652859fac50ef97d10bc34a88bb7
tests/test_workflows.py 81ab55fa920cadbee942120bd83c630efaeeeda5a75a7fb467ab677857fe7661
```

Review completed: 2026-10-10T08:17:41+00:00. Candidate changes after these hashes require scoped rereview; separately delegated final QA owns its own observable flow and test results.
