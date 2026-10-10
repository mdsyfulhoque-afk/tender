# TenderOS diagnostic workbench — candidate operation guide

Status: candidate guide reconciled to the final independently reviewed local/private build. Security review is **PASS WITH NON-BLOCKING ITEMS** for local/private single-owner pilot controls. QA is partial: direct-handler integration (3 passed), isolated suite (73 passed), and two focused commercial regressions passed, but the full suite stalled on a local HTTP test-transport issue. This is not a hosted deployment certificate. See `verification/agent-workbench/ENGINEERING_EVIDENCE.md` and the exact [QA report](../../verification/agent-workbench/qa/QA_REPORT.md).

## What you can use without a paid model

Use the single-owner workspace to collect original tender sources and private organization evidence, run local rules analysis, resolve review work, record a source-backed human BID/NO_BID/HOLD and prepare an honest expert diagnostic. The new commercial register records scope, manually observed cash/direct costs and immutable report releases. Model inference is disabled/unconfigured. No API key is required. Rules are extraction/relevance aids; they do not prove all requirements were found or a business is eligible.

The agents constructing this software are genuine delegated Codex agents. They are not a runtime API exposed to your installed app. A job labelled Local rules is software automation, not an autonomous LLM agent.

## Local startup

Follow the existing TenderOS README using Python 3.11+:

```bash
cd TenderOS
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
TENDEROS_DATA_DIR=/tmp/tenderos-local .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. Choose a private durable data directory suitable for real pilot use; `/tmp/tenderos-local` is only the README example and may be cleared by the host. Set the data directory before import. Dependency installation needs available packages; local analysis itself has no inference-provider dependency. Keep original files/database private and out of Git. Existing local reviewer names are unverified labels. Public exposure is not the local mode's intended use.

Hosted operation requires protected owner authentication, PostgreSQL and private file-store configuration. It may incur infrastructure charges even with zero model spending. Vercel metadata confirms deployment `dpl_GK3kcXCeGoDQVzLaL4gtCXZn8AZc` is **READY** for commit `2f38991d`, with the exact branch alias [tender-git-tenderos-agent-workbench-ip-3.vercel.app](https://tender-git-tenderos-agent-workbench-ip-3.vercel.app). Vercel `rootDirectory` had been reset to `null` (repository root) before this build; root `vercel.json`, `.vercelignore`, and committed `pyproject.toml` entrypoint were selected. This READY status does not verify the app response: `web_fetch_vercel_url` remains blocked with 403 at `read_protection_bypass`, before origin access. An earlier screenshot of the alias showed Vercel `404 NOT_FOUND` before this deployment. Earlier attempts failed: `49777a4` exceeded the `excludeFiles` schema limit; `d544651` ran `uv lock` before the root `[project]` table existed; `c2add27` failed with `FASTAPI_ENTRYPOINT_NOT_FOUND` while `rootDirectory` was temporarily `TenderOS`. The non-decrypting Vercel environment listing returned an empty list: zero project variables are configured, so required database, private Blob and owner-auth settings are absent. No HTTP, UI, API, database, or private-storage behavior is verified.

## 1. Agree intake and register sources

Create/select the organization and tender. Register the complete agreed original-source inventory, including notice, schedules, specifications, amendments and expected missing files. Upload available original PDFs; retain version/addendum relationships. Record service scope/exclusions, client label, received/intake status, promised due date and quoted fee if agreed. Prices in source documents are examples, not approved defaults. An entered deadline is an owner commitment, not proof of an SLA.

Missing original files and unreadable/scanned pages remain visible. Do not silently mark a zero-candidate or image-only document complete. Supply an official readable text-layer source or handle the documented manual review limitation; OCR is not implemented in this increment.

## 2. Analyze registered documents

Use the Analysis work action. The product saves a workflow job and executes fixed source inspection, requirement candidate, evidence relevance and citation-check stages in bounded advances. Show actual processor Local rules and no model usage charges. No text in a document can enable a model, change policy, run code or approve a decision.

While the interface is actively advancing the job it can continue stage batches. Closing the tab, interrupted transport or absence of an advancing client stops progress; the saved job can be reopened and continued. There is no shipped always-on scheduler. Cancel stops further publication; restart creates a new job with current files and retains prior history. Failed/stale/budget-limited runs disclose the issue and require the offered recovery path. A waiting-for-human state means suggestions are ready for review, not that you are ready to bid.

## 3. Resolve review work

Use the prioritized queue for missing source items, unreadable coverage, unreviewed clauses, mandatory blockers, missing/expired/unverified evidence, source reattestation and stale decisions. Open the source/requirement/evidence link and follow the actual next action. A checkbox or resolved task is not an eligibility approval.

Inspect each candidate's actual source, page, file hash and exact quote. Human accept creates only an unreviewed UNKNOWN requirement; existing upload candidates are deduplicated. Reject retains the candidate disposition. Classify/review the requirement in the normal human review surface, never by trusting the proposed keyword classification.

Evidence suggestions are metadata/term matches. They do not verify adequacy, legal authenticity or confidence. Confirm same-organization evidence, upload/version actual PDFs, explicitly verify the exact current file and map only justified proof. Absence of a match is unknown, not proof of NOT_HELD. Expired/missing/unverified records remain unresolved.

Changing sources/inventory/amendments can stale source proposals and require a new run. Requirement/evidence changes stale the full analysis; source-current candidates can still be individually reviewed after quote revalidation without applying stale evidence suggestions. Old artifacts remain historical.

## 4. Make the human decision

Attest complete source inventory only after actual authorized source review. Mandatory NOT_HELD blocks; mandatory UNKNOWN/PARTIAL/unverified and incomplete source inventory keep readiness unresolved. Record BID/NO_BID/HOLD through the existing human decision path when appropriate. A BID must be current against requirements/evidence/source set. Later changes make the old decision historical/stale; they do not rewrite it.

A useful paid diagnostic can honestly conclude HOLD or NO_BID and show gaps. It does not require a positive BID result. TenderOS supports decision evidence, not guaranteed award probability, legal rulings or automatic submission.

## 5. Release a diagnostic and record service observations

Review the service checklist, scope/exclusions, source inventory, current requirements/evidence and decision currency. The diagnostic release captures the server's actual assessment snapshot with reviewer/template/version/hash. The API does not trust a caller-supplied assessment payload. Each subsequent release is a new immutable version; historical exports reflect captured values rather than today's edited assessment.

Record operator delivery confirmation only for actual intended delivery. Capture/export does not secretly email a client. Mark unresolved inputs and stale approvals accurately. Current working exports and frozen issued-diagnostic exports serve different purposes; old releases stay unchanged after amendments, evidence updates or financial corrections.

Record manually observed receipts, direct costs and referenced reversals in BDT minor units. BDT 1 = 100 minor units. Use the exact supported forms/API types; no floating-point rounding assumptions. Quote is not receipt. A payment reference is your observation, not bank reconciliation. Use append-only corrections/refunds against original same-scope entries rather than overwriting history; total correction cannot exceed original allowed amount.

Read gross receipts, refunds, net collected cash and documented direct costs separately. Unknown infrastructure/labor/overhead costs remain unknown. Recorded direct contribution is not audited profit. Repeat paid demand uses positive net collections on distinct assessments for a stable organization; demos or fully refunded orders do not count. Legacy aggregate pilot amounts are not silently imported into the new cash ledger.

## 6. Costs, privacy and unresolved operation

The rules pipeline makes no model calls and does not train on customer files. Database/private-file traffic in hosted mode is infrastructure access, not model egress; cost remains unverified unless the operator establishes it. No automatic purchases, email/messages, payments, e-GP login, crawling or procurement submission are included. External model/provider settings stay disabled.

Hosted access is one configured workspace owner, not authenticated multi-user tenants. Exports are not proof of complete data erasure or rights compliance. OCR, general model inference, hard parser sandboxing, portable backup/restore validation and actual hosted browser→API→DB→private-file verification require separate evidence. The privacy essay's absent original policy does not certify legal compliance.

The [current preview alias](https://tender-git-tenderos-agent-workbench-ip-3.vercel.app) is assigned by Vercel metadata to deployment `dpl_GK3kcXCeGoDQVzLaL4gtCXZn8AZc`, marked **READY** for commit `2f38991d`. `rootDirectory` was `null` (repository root) before this build, so it used the root `vercel.json`, `.vercelignore`, and committed `pyproject.toml` entrypoint. The earlier `c2add27` deployment failed with `FASTAPI_ENTRYPOINT_NOT_FOUND` when `rootDirectory` was temporarily `TenderOS`; earlier errors were the `49777a4` `excludeFiles` limit and `d544651` missing `[project]` at `uv lock`. The READY status reports Vercel deployment state only. `web_fetch_vercel_url` still receives 403 at `read_protection_bypass` before origin access; the earlier user screenshot showed 404 before this READY deployment. There is no verification of the HTTP root, rendered UI, API, database, or private storage. `get_project`, `get_deployment`, and `list_deployments` work without explicit `teamId`; explicit team-scoped calls fail 403 in scope `ip-3`. The non-decrypting Vercel environment listing returned an empty list: zero project variables are configured, so required database, private Blob and owner-auth settings are absent. The release gate remains incomplete.

## Verification record and limits

The independent QA agent exercised a synthetic PDF through the direct registered handler flow (3 passed), including human candidate acceptance into only `UNKNOWN`/unreviewed requirements, ordinary decision gates, commercial intake/release/exports, and manual ledger corrections. A separate isolated non-HTTP pytest command passed 73 tests. Two focused commercial tests passed, including frozen snapshot drift and safe DOCX control-character handling. `node --check`, Python compilation, and `git diff --check` passed.

The full pytest run collected 197 tests and passed the first 12, then stalled at `test_blank_intake_and_quote_do_not_count_as_cash` until its 12-second timeout. A minimal synthetic FastAPI endpoint reproduced the stall through `TestClient`, `httpx.ASGITransport`, and a direct ASGI callable. This supports a local AnyIO/HTTP test-transport limitation but does not prove the app HTTP path works. The 73-test command omitted `tests/test_workflows.py` and `tests/test_commercial_operations.py`; direct handler coverage and focused regressions are not equivalent to a full HTTP suite. Chromium rendering, browser interaction/accessibility, live PostgreSQL migrations, private Blob retrieval, and hosted end-to-end behavior remain unverified.

The independent security review is **PASS WITH NON-BLOCKING ITEMS** for local/private pilot controls. It reproduced and independently rechecked fixes for aggregate receipt size, historical run visibility after evidence growth, and canonical serialized page limits. Its scope does not certify production, hosted services or the missing strict Codex evidence gate. Opaque platform run/trace IDs remain unavailable and recorded as `null`.
