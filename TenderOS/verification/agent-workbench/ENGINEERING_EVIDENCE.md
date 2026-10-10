# Engineering evidence — TenderOS agent workbench

## Candidate identity and disposition

- Baseline: `6f7ac1156e595f9f87d6f32d99492f8a704e9849`.
- Worktree: `/workspace/tenderos-agent-workbench`; branch: `tenderos/agent-workbench`.
- Candidate SHA-256 is recorded in `build-manifest.json`. It hashes every modified or untracked worktree file outside `verification/agent-workbench/`, sorted by repository-relative path, using `path + NUL + raw SHA-256(file bytes) + newline`. The excluded directory contains the evidence and hash ledgers that record the digest, avoiding a self-reference. It is a worktree snapshot, not a Git commit.
- Security disposition: **PASS WITH NON-BLOCKING ITEMS** for local/private single-owner pilot controls, scoped as documented in `qa/SECURITY_REVIEW.md`.
- QA disposition: focused and isolated checks passed; the complete pytest suite and hosted/browser flows remain unverified. Exact commands and outputs are in `qa/QA_REPORT.md`.
- Strict `AGENTS.md` runtime evidence gate: **INCOMPLETE**. Opaque platform run IDs and exported tool-trace IDs are unavailable; every unavailable value remains `null`.

## What the agents built

Genuine Codex collaboration agents reviewed the provided product and governance documents, designed the workflow, implemented application slices, repaired defects, and independently inspected the resulting code. The deployed application does **not** run those Codex agents. Its workflow is deterministic local **RULES** software, with no model/provider execution, zero configured model spend, no training, and no always-on scheduler.

The product additions include a durable, finite source-analysis workflow; source and file-version currency checks; bounded candidate, evidence-relevance, and citation artifacts; human acceptance that creates only an unreviewed `UNKNOWN` requirement; and a commercial register for scoped service intake, manually observed BDT receipts/costs and append-only corrections, frozen server-derived diagnostic releases, and JSON/CSV/DOCX exports. Original source inventory, full source review, evidence validation, attestation, and BID/NO_BID/HOLD decisions remain human-controlled.

## Delegation record

All canonical agent names below are real collaboration task identities. Opaque run IDs, exported traces, and exact launch/completion timestamps were not exposed by the runtime and are not inferred. `null` is an evidence limitation, not a successful trace.

| Canonical task | Actual outcome evidenced here |
|---|---|
| `/root/apes_feature_review` | APES source review artifact retained under `project_knowledge/agent-workbench/reviews/`. |
| `/root/governance_feature_review` | Governance/privacy source review artifact retained; the missing original privacy policy was not treated as certified. |
| `/root/agent_runtime_design` | Runtime design artifact retained; deployed processing remains fixed rules, not a Codex-agent runtime. |
| `/root/workflow_persistence_build` | Implemented additive workflow persistence; its focused schema suite was reported and independently reproduced at 57 passed. No live Postgres was used. |
| `/root/workflow_engine_build` | Hit the platform usage limit during implementation. Do not attribute a completion receipt or final test result to this task. Actual code present in the candidate was independently QA/security reviewed. |
| `/root/commercial_operations_build` | Implemented commercial operations and exporter; focused and independent integration results are recorded in QA. A full passing final `test_commercial_operations.py` run is not claimed. |
| `/root/product_frontend_build` | Implemented the front end; `node --check app/static/ui.js` passed. No browser rendering or interaction result is claimed. |
| `/root/source_traceability_build` | Built source/feature/task documentation; this record reconciles its initial pending statuses to the final reports. |
| `/root/citation_contract_repair` | Repaired the evidence-version contract mismatch; its focused contract suite passed **9 tests**. |
| `/root/receipt_budget_repair` | Implemented aggregate `RUN_RECEIPT` byte budgeting in `app/workflows.py`; the focused receipt-budget plus contract suite passed **11 tests**. A later, separate follow-up invocation failed; that does not undo or replace the completed repair and passing focused result. |
| `/root/workflow_currency_bound_fix` | Repaired canonical serialized page-size accounting; focused regression reported 2 passed. |
| `/root/final_independent_qa` | Completed the independent local QA report; results and limits are in `qa/QA_REPORT.md`. |
| `/root/independent_security_review` | Completed the separate read-only review; repaired findings were rechecked and scoped disposition is in `qa/SECURITY_REVIEW.md`. |

A prior independent full-flow QA attempt ended at a runtime usage limit. It is not counted as a pass. Some narrow repairs were independently verified in the final security report; no identity or test receipt is fabricated for an agent whose final evidence is unavailable.

## Verification actually completed

The final QA record reports:

- Direct-handler synthetic integration harness: **3 passed**. It covered the fixed RULES workflow, human acceptance into only unreviewed UNKNOWN state, ordinary domain gates, commercial intake/release/exports, and append-only ledger behavior.
- Isolated non-HTTP pytest selection: **73 passed**. It deliberately omitted `tests/test_workflows.py` and `tests/test_commercial_operations.py` because those files use the stalled HTTP test-transport path.
- Two focused commercial regressions: **2 passed**, covering repeat/digest drift and DOCX control-character rendering.
- `node --check app/static/ui.js`, Python `compileall` over `app`, `scripts`, and `tests`, and `git diff --check`: passed.
- The complete pytest attempt collected 197 tests and passed 12 before stalling at `tests/test_commercial_operations.py::test_blank_intake_and_quote_do_not_count_as_cash`; its 12-second timeout exited 124. A synthetic trivial FastAPI endpoint reproduced the stall using `TestClient`, `httpx.ASGITransport`, and a direct ASGI callable, blocking in `anyio.from_thread.portal.call`. This evidence suggests a local AnyIO/HTTP transport problem but does **not** prove the TenderOS HTTP path works.
- No Chromium/browser UI, accessibility, managed Postgres, private Blob, or deployed browser → API → database → file flow was tested. No production data, paid API, model/provider, or external service was used.

The security reviewer independently reproduced and rechecked three bounded-storage/history defects: final receipt bytes exceeding the aggregate artifact cap, evidence growth blocking access to retained historical artifacts, and serialized source-page content exceeding its byte cap. All three final repro checks passed. The reviewer found no remaining reproduced new permission, human-gate, model-spend, ledger, or injection defect within its stated scope. See the complete controls and limitations in `qa/SECURITY_REVIEW.md`.

These outcomes do not constitute a full pytest pass, hosted release approval, production security certification, or proof of customer revenue/profit.

## Deployment and spend boundary

Vercel metadata reads (`get_project`, `get_deployment`, and `list_deployments`) succeed when `teamId` is omitted. The non-decrypting Vercel environment listing returned an empty list: no project environment variables are configured, so required PostgreSQL, private Blob and owner-auth settings are absent. The previous deployment was **READY** for commit `5241a2b`. Commit `49777a4` (deployment `dpl_6cWLZ1Fx7beUeybLbMrT7vCFnxXu`) failed because `functions.TenderOS/app/main.py.excludeFiles` exceeded 256 characters. Commit `d544651` removed that setting and used the repository-root `.vercelignore` allowlist, but its build failed because root `pyproject.toml` had no `[project]` table at build time. Commit `c2add27` committed `[project]` metadata and `[tool.vercel].entrypoint = "TenderOS.app.main:app"`; its deployment `dpl_7WrL2foMKMa1asTbqmELADbNciJD` failed with `FASTAPI_ENTRYPOINT_NOT_FOUND` while `rootDirectory` was temporarily `TenderOS`. The setting has since been reset to `null` (repository root), selecting root `vercel.json`, `.vercelignore`, and `pyproject.toml`; when rootDirectory was `TenderOS`, the nested `TenderOS/vercel.json` and `TenderOS/.vercelignore` applied. No deployment has run after the reset, so the entrypoint remains unverified. The latest user-provided screenshot shows Vercel `404 NOT_FOUND`: [preview URL](https://tender-git-tenderos-agent-workbench-ip-3.vercel.app). Explicit `teamId` calls fail with `403 Forbidden` (`ip-3`); separately, `web_fetch_vercel_url` remains blocked with 403 at `read_protection_bypass`. No HTTP root, UI, API, database, or private-storage response is verified. The earlier READY deployment at `eb4280b` was integration-created. The release gate remains incomplete and no production/usable-app status is claimed.

No model API key, paid inference, database, storage, or other service was purchased or provisioned. Local deterministic rules cost no inference charge; hosted infrastructure billing is unknown and may apply independently. The deployment and commercial metrics do not establish profit or profitability.

## Related evidence

- [`build-manifest.json`](build-manifest.json): agent statuses, candidate hash, tests, and deployment limitations.
- [`output-hashes.json`](output-hashes.json): current SHA-256/byte-size inventory of evidence/document files; this file excludes itself.
- [`qa/QA_REPORT.md`](qa/QA_REPORT.md): exact final QA commands, results, warnings, and candidate-at-QA hash.
- [`qa/SECURITY_REVIEW.md`](qa/SECURITY_REVIEW.md): findings, repairs, controls, and scoped security outcome.
- [`project_knowledge/agent-workbench/USER_GUIDE.md`](../../project_knowledge/agent-workbench/USER_GUIDE.md): operator guide for the implemented local/private pilot.
