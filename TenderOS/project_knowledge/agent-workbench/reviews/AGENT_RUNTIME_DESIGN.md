# TenderOS bounded workflow design

Design status: REVIEW_READY; proposed product behavior, not implemented or deployed.

Observed source commit: `6f7ac1156e595f9f87d6f32d99492f8a704e9849`.
Report author: genuinely delegated Codex subagent `/root/agent_runtime_design`, launched by `collaboration.spawn_agent`; task received from `/root`. This runtime exposes no opaque platform run ID or exported tool-trace ID: both are **null**, not fabricated. Read-only inspection used `functions.exec`/`tools.exec_command`; only this report is written. No application edits, tests, model calls, credentials, deployment, or network calls occurred.
Inspection completed: 2026-10-09 20:15 UTC / 2026-10-10 02:15 Asia/Dhaka.

## 1. Decision and scope

Ship a persistent, bounded **local rules workflow** now, because it provides useful intake, candidate extraction, evidence-relevance suggestions and citation checks without a paid inference dependency. Show actual processor type in every run. It must never masquerade as a team of autonomous AI agents. The separate agents building the repository are actual Codex subagents; the shipped runtime does not have access to these sessions. Add an optional local-inference interface with status DISABLED/UNCONFIGURED and no executable provider path until a real allowed processor is available.

The first useful product increment is:

`Source inspection → Requirement candidates → Evidence relevance suggestions → Citation check → Human review`

The durable controller determines eligible next tasks from contracts, dependencies and saved state. It does not rely on one prompt per click, an in-memory queue, `FastAPI.BackgroundTasks`, or a process that must live inside a Vercel function. An authenticated client can advance one bounded batch at a time; a local worker command can advance the same engine until a terminal/review state. Hosted operation retains jobs across cold starts, but automatic processing stops when no client/worker is advancing them. State that limit clearly; do not claim an always-on cloud agent fleet.

Job outputs are suggestions, checks and draft delivery artifacts. Only existing human routes may review/classify a requirement, verify evidence, attest the full source set, or record BID/NO_BID/HOLD. No workflow worker sends communications, charges a customer, submits a bid, logs into e-GP, crawls websites, invokes a shell, or discovers secrets.

## 2. Evidence from current source and attached documentation

- `app/main.py:95` has one transaction per route and hosted serializable PostgreSQL connections. Preserve that transaction boundary for acceptance/approval; do not hold it open while parsing PDFs or calling a future processor.
- `app/main.py:222` reads only registered opaque keys and checks exact byte size/hash; `:248` bounds PDF pages; `:260` verifies a quote against the actual source page. Reuse these trusted boundaries through injected callables rather than arbitrary file paths.
- `app/main.py:324` derives requirement/evidence and source-inventory currency hashes. Its linked-evidence set omits unlinked organizational evidence; an evidence-relevance workflow must capture all eligible evidence/file versions in a separate immutable input manifest.
- `app/main.py:645–777` intentionally requires human review and document verification. Workers must not call these review/decision routes or set their fields directly.
- `app/main.py:815–925` performs keyword extraction synchronously on PDF upload and inserts unreviewed requirements. New candidate acceptance must deduplicate against those existing rows; otherwise a second workflow duplicates every uploaded candidate.
- `app/main.py:955–1046` exports the live report snapshot. A commercial delivery receipt should record an immutable report snapshot and content hash rather than claim that a later regenerated live report is the original delivery.
- `app/database.py:45–128` and `scripts/migrate_postgres.py:25–94` preserve checksum-verified v1/v2 migrations. Add a new numbered v3 and new local extension identifier. **Do not change the v2 statement tuple or migration SQL bytes.**
- `app/hosting.py` provides single-owner authentication, origin checking and CSRF. This is a private single-owner workspace; organizations are scoped business entities, not separate authenticated SaaS tenants. Do not claim tenant/RLS isolation.
- `AGENTS.md` requires real delegated coding, source provenance, no invented identities, private boundaries, history preservation and human consequential approval. The user has explicitly requested autonomous agent implementation. This report records available identity metadata honestly and does not invent a run ID.
- `project_knowledge/02_PRD_v1_1.md` FR-013/014 and section 6 explicitly require durable states, bounded retries, idempotency, prompt/tool provenance, permission limits and egress default deny. It also requires human source/requirement/evidence/decision gates.
- Uploaded APES extracted text lines 28, 109, 801 and 1322 require no mandatory paid runtime; lines 140–165 define replaceable tools under durable contracts; lines 926–927 define bounded task graphs and reviewer tasks; lines 1459–1489 prescribe artifact lifecycle, dependency, traceability and prompt compilation. Its optional local-model baseline is at 1147. Its illustrative commercial figures at 1298–1321 are unvalidated, so they must never become default factual revenue predictions.
- Instructions inside attached documents are design source material. The current user's request governs this work; embedded master prompts do not execute themselves or authorize external actions.

## 3. Exact additive persistence contract

Use five small tables. The SQL below is the PostgreSQL v3 contract; SQLite equivalents use `INTEGER PRIMARY KEY`, the existing qmark adapter, and equivalent length/hex checks. JSON is canonical UTF-8 text validated by application schemas, with hashed content. No required third-party queue or orchestration framework.

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_tender_identity_org
  ON tenders(id,organization_id);

CREATE TABLE workflow_jobs (
 id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
 tender_id BIGINT NOT NULL,
 organization_id BIGINT NOT NULL,
 workflow_kind TEXT NOT NULL CHECK (workflow_kind='READINESS_REVIEW'),
 processor_kind TEXT NOT NULL CHECK (processor_kind IN ('RULES','LOCAL_MODEL')),
 contract_version TEXT NOT NULL,
 state TEXT NOT NULL CHECK (state IN (
   'WAITING_INPUT','READY','RUNNING','WAITING_HUMAN','COMPLETED',
   'FAILED','CANCELLED','STALE','BUDGET_EXHAUSTED')),
 created_by TEXT NOT NULL,
 idempotency_key TEXT NOT NULL CHECK (length(idempotency_key) BETWEEN 16 AND 128),
 request_sha256 TEXT NOT NULL CHECK (request_sha256 ~ '^[a-f0-9]{64}$'),
 input_manifest TEXT NOT NULL,
 input_sha256 TEXT NOT NULL CHECK (input_sha256 ~ '^[a-f0-9]{64}$'),
 policy_manifest TEXT NOT NULL,
 policy_sha256 TEXT NOT NULL CHECK (policy_sha256 ~ '^[a-f0-9]{64}$'),
 step_runs INTEGER NOT NULL DEFAULT 0 CHECK (step_runs >= 0),
 elapsed_ms BIGINT NOT NULL DEFAULT 0 CHECK (elapsed_ms >= 0),
 external_model_calls INTEGER NOT NULL DEFAULT 0 CHECK (external_model_calls=0),
 model_spend_minor BIGINT NOT NULL DEFAULT 0 CHECK (model_spend_minor=0),
 cancel_requested INTEGER NOT NULL DEFAULT 0 CHECK (cancel_requested IN (0,1)),
 revision INTEGER NOT NULL DEFAULT 0 CHECK (revision >= 0),
 restart_of_job_id BIGINT,
 last_error_code TEXT,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, completed_at TEXT,
 UNIQUE (tender_id,idempotency_key), UNIQUE (id,tender_id),
 FOREIGN KEY (tender_id,organization_id) REFERENCES tenders(id,organization_id),
 FOREIGN KEY (restart_of_job_id,tender_id) REFERENCES workflow_jobs(id,tender_id)
);

CREATE TABLE workflow_steps (
 id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
 job_id BIGINT NOT NULL REFERENCES workflow_jobs(id),
 task_kind TEXT NOT NULL CHECK (task_kind IN (
   'SOURCE_INSPECT','REQUIREMENT_CANDIDATES','EVIDENCE_RELEVANCE','CITATION_CHECK')),
 task_key TEXT NOT NULL,
 contract_version TEXT NOT NULL,
 executor_label TEXT NOT NULL,
 state TEXT NOT NULL CHECK (state IN (
   'BLOCKED','READY','RUNNING','SUCCEEDED','FAILED','CANCELLED','STALE','NEEDS_OCR')),
 predecessor_step_id BIGINT,
 cursor_json TEXT NOT NULL DEFAULT '{}',
 attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count BETWEEN 0 AND 2),
 lease_owner TEXT, lease_expires_at TEXT,
 fence INTEGER NOT NULL DEFAULT 0 CHECK (fence >= 0),
 input_sha256 TEXT NOT NULL CHECK (input_sha256 ~ '^[a-f0-9]{64}$'),
 elapsed_ms BIGINT NOT NULL DEFAULT 0 CHECK (elapsed_ms >= 0),
 last_error_code TEXT,
 started_at TEXT, completed_at TEXT,
 UNIQUE (job_id,task_key), UNIQUE (id,job_id),
 FOREIGN KEY (predecessor_step_id,job_id) REFERENCES workflow_steps(id,job_id)
);

CREATE TABLE workflow_artifacts (
 id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
 job_id BIGINT NOT NULL REFERENCES workflow_jobs(id),
 step_id BIGINT NOT NULL,
 artifact_key TEXT NOT NULL,
 artifact_kind TEXT NOT NULL CHECK (artifact_kind IN (
   'SOURCE_BATCH','REQUIREMENT_CANDIDATES','EVIDENCE_SUGGESTIONS','CITATION_CHECKS','RUN_RECEIPT')),
 schema_version TEXT NOT NULL,
 input_sha256 TEXT NOT NULL CHECK (input_sha256 ~ '^[a-f0-9]{64}$'),
 payload_json TEXT NOT NULL,
 output_sha256 TEXT NOT NULL CHECK (output_sha256 ~ '^[a-f0-9]{64}$'),
 created_at TEXT NOT NULL,
 UNIQUE (job_id,artifact_key), UNIQUE (id,job_id),
 FOREIGN KEY (step_id,job_id) REFERENCES workflow_steps(id,job_id)
);

CREATE TABLE workflow_events (
 id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
 job_id BIGINT NOT NULL REFERENCES workflow_jobs(id),
 step_id BIGINT,
 actor TEXT NOT NULL, action TEXT NOT NULL,
 event_json TEXT NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY (step_id,job_id) REFERENCES workflow_steps(id,job_id)
);

CREATE TABLE workflow_candidate_reviews (
 id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
 job_id BIGINT NOT NULL REFERENCES workflow_jobs(id),
 artifact_id BIGINT NOT NULL,
 candidate_key TEXT NOT NULL,
 disposition TEXT NOT NULL CHECK (disposition IN ('ACCEPTED','REJECTED','DUPLICATE')),
 reviewer TEXT NOT NULL, note TEXT NOT NULL,
 requirement_id BIGINT REFERENCES requirements(id),
 reviewed_at TEXT NOT NULL,
 UNIQUE (job_id,candidate_key),
 FOREIGN KEY (artifact_id,job_id) REFERENCES workflow_artifacts(id,job_id)
);
CREATE INDEX idx_workflow_jobs_tender ON workflow_jobs(tender_id,id);
CREATE INDEX idx_workflow_steps_state ON workflow_steps(job_id,state,id);
CREATE INDEX idx_workflow_events_job ON workflow_events(job_id,id);
```

Add append-only/no-delete triggers for `workflow_artifacts`, `workflow_events`, `workflow_candidate_reviews` using the v2 evidence-file trigger pattern. Jobs and steps are controller state and intentionally mutable. Freeze input/policy manifests, their hashes, contract version and identity fields after creation; guard with database trigger or exact narrow update SQL plus tests. Candidate-review table uniqueness makes double acceptance idempotent. Before linking `requirement_id`, enforce its tender equals job tender in the same transaction; a later numbered migration can add a composite FK if desired.

Migration identifier: `tenderos_bounded_workflows_v3`; new file `scripts/postgres_migrations/003_bounded_workflows.sql`. Register it under the same advisory lock in the existing migration CLI; add corresponding table names to its unversioned-table refusal. Add tables with identities to `_INSERT_ID_TABLES`. For local SQLite, preserve `_LOCAL_EXTENSION_STATEMENTS` v2 digest and add `_LOCAL_WORKFLOW_STATEMENTS` + separate `_LOCAL_WORKFLOW_ID`; call v2 then v3 in initializer. A fresh DB gets all three; a v2 DB receives v3 only; repeated runs validate each digest; v1/v2 historical rows remain untouched. Never run hosted DDL at import or request time.

An implementation may fold events into existing `audit_events` to reduce files, but must preserve append-only scoped job receipts, ordered transitions, and no confidential prompt/body in routine logs. The proposed schema is the concrete baseline, not a mandatory request to re-platform core tables.

## 4. Frozen currency and contracts

Canonical serialization must use stable ordering, `ensure_ascii=False`, explicit schema versions and stable UTC/date values. Manifest includes:

1. Tender/organization IDs, notice/source metadata, current snapshot fingerprint and source-scope fingerprint, attestation event/version.
2. Ordered source records `{id,sha256,bytes,pages}` and ordered inventory metadata/availability/version/supersession links.
3. Ordered requirements, source/page/quote/text/classification/review/status/evidence IDs/updated time; no assumed verified status.
4. **All same-organization evidence** available for matching: metadata, expiry, latest immutable file `{id,sha256,bytes}`, verified flag, verification event and note hash. Store only needed confidential content in private artifacts, not events.
5. Policy version, extractor/tokenizer/verifier versions and date at creation. On every advance/export, compare current manifest-derived dependency hashes and date-sensitive evidence currency. Addendum/upload/review/evidence replacement/expiry can mark the run STALE; prior artifacts are retained. Candidate acceptance uses the narrower source dependency defined next.

**Two explicit dependency hashes avoid self-invalidating acceptance:** `full_input_sha256` covers all manifest fields above; `source_input_sha256` covers only tender notice/source metadata, ordered source IDs/hashes/pages and ordered inventory metadata/availability/version/supersession links plus rules version. It excludes requirements, evidence and source-attestation fields because those may legitimately change when a candidate is accepted/reviewed. Store the second hash inside the frozen manifest and candidate artifact payload. SOURCE_INSPECT/REQUIREMENT_CANDIDATES/source-citation items depend on the source hash. EVIDENCE_RELEVANCE/evidence-check items/full readiness artifacts depend on the full hash.

The full job can become STALE after accepting the first candidate while the remaining source proposals are still current. The review endpoint may accept a source-current candidate from WAITING_HUMAN or STALE with a valid unchanged source check; it must compare current source dependency hash, re-read actual source quote and record that full-run analysis is stale. It creates an unreviewed requirement only. It must not apply stale evidence suggestions or change review/status/approval. A changed addendum/inventory/source context blocks source-proposal acceptance and requires restart, even if an old quote still appears. A batch review route may accept all selected candidates atomically to reduce interaction, but correctness does not depend on batching. This prevents the first accepted candidate from making all subsequent candidates unusable.

### SOURCE_INSPECT v1 / processor RULES

Input: registered source IDs and hashes from frozen manifest; 1–10 pages per advance. Permitted tools: scoped PDF reader, page text extractor, SHA-256, deterministic text-layer coverage check. Output per page `{source_id,sha256,page,text,text_sha256,character_count,coverage_status}` plus explicit unreadable/scanned issues. One artifact per page or bounded page batch. Do not truncate text silently: oversize page/artifact is an explicit INCOMPLETE_BOUND issue and downstream review remains unresolved. No OCR installation/download by surprise; missing text returns NEEDS_OCR and directs operator to supply a readable source or optional future local OCR.

### REQUIREMENT_CANDIDATES v1 / processor RULES

Input: completed source artifacts; deterministic keyword/structure patterns and their version. Output `{candidate_key,source_id,source_sha256,page,verbatim_quote,proposed_text,category_candidate,mandatory_candidate:null,uncertainty_notes,processor:'RULES'}`. Candidate key hashes `{job_input_hash,source_sha256,page,normalized_quote}`. Do not normalize away negation, numbers or conditional language. Keep normalization definition as whitespace collapse only for quote checks; casefold token search is a separate rules feature. Candidate count is not recall/completeness proof. Output unreviewed and UNKNOWN; no evidence status mutation.

### EVIDENCE_RELEVANCE v1 / processor RULES

Input: frozen reviewed requirements and accepted unreviewed candidates plus same-organization evidence metadata/latest file versions. Metadata token overlap is the initial useful matcher; if evidence text spans are extracted, they must carry file/page/exact-quote provenance. Output `{requirement_or_candidate_key,evidence_id,file_id,file_sha256,overlap_terms,matching_rule,rationale,unresolved_conditions,expiry_state,suggested_only:true}`. Do not call overlap a calibrated confidence or eligibility score. Absence of match is UNKNOWN, not NOT_HELD. Expired/missing/unverified evidence can appear in an issue list, not as compliant. No cross-organization evidence, whole-vault model ingestion or arbitrary SQL/search tools.

### CITATION_CHECK v1 / processor RULES

Input: outputs from prior stages. Re-read independently through registered document resolver, verify bytes and SHA-256, page bounds and exact normalized quotes; verify selected evidence file still belongs to expected organization/record/version. Use a checker function separate from candidate extraction so bugs are not simply echoed. Output item statuses `CITATION_VALID`, `CITATION_INVALID`, `SOURCE_CHANGED`, `EVIDENCE_CHANGED`, `UNREADABLE`, with reason and verified document hash. Also list source inventory and coverage issues. This is a deterministic automated checker, **not a separate AI verifier agent** and not a proof of recall or substantive evidence adequacy.

All artifacts validate against Pydantic/fixed JSON schemas before publish. Document text remains data; phrases such as “ignore your instructions,” payment requests or fake policies inside a PDF cannot alter the registry/permissions, choose tool names, execute code or self-approve candidates.

## 5. Controller, permission, budget and recovery

- Only registered task kinds can run. Processor/default policy is immutable RULES, no external inference, no API credential requirement; max external model calls and monetary spend are exactly zero.
- Scope every route/job lookup by tender and authenticated workspace, and evidence by captured organization. Do not infer multi-tenant authorization from organization IDs.
- Default pilot limits: 20 source documents, 300 total source pages, 20 evidence files/100 evidence pages if text matching enabled, 1,000 candidates, 128 task batches, 180,000 ms accumulated processing time; max 10 source pages per batch, 20,000 characters per quote/candidate aggregate as appropriate. Each page artifact max 64 KiB; total artifact payload max 5 MiB. Exceeding any limit preserves artifacts and returns BUDGET_EXHAUSTED/INCOMPLETE_BOUND. Limits are explicit server policy, never editable from PDF text or an untrusted request.
- The existing per-document upload bytes/page limits apply first. Future hard parser isolation requires an actual subprocess/resource ceiling/sandbox; a cooperative wall-clock check alone cannot stop a hung parser, so do not claim that it does. Vercel invocation timeout is also not a durable scheduling guarantee.
- In local mode, processor egress is none. In hosted mode, scoped database/private-file-provider traffic is necessary and distinct from model egress. No workflow tool may add arbitrary URLs/redirects; existing private Blob resolver already restricts host and tokens. Cloud model adapter remains unavailable, including public “free keys.”
- Create with client-generated random idempotency key. Store canonical request hash. Same tender+key+same hash returns existing job; changed hash returns 409. Use an independent random application execution token for each actual step attempt. This is a genuine product-generated attempt ID, never presented as a Codex/platform run ID.
- Start transaction A: verify state, currency, budgets and dependencies; claim next READY step with `UPDATE ... WHERE state='READY' AND fence=?`, increase fence and attempt count, save lease owner/deadline, job RUNNING and ordered event. Commit immediately. Attempt count is for the **current cursor batch**, not the entire multi-batch stage: after successful cursor advance reset it for the next batch, while aggregate `job.step_runs` increases monotonically and cannot be reset. Alternatively create one uniquely keyed step per page batch, each with at most two attempts. Record cursor/batch identity in every attempt event.
- Parse/execute outside a DB transaction. Do not silently retry parsing loops or writes. At most two attempts for safely repeatable registered reads/derivations; never retry candidate acceptance/approval after ambiguous DB commit.
- Publish transaction B: require exact job revision, uncancelled state, current manifest, step lease owner/fence and unexpired lease; validate all output bounds/schemas; insert unique artifact key; update cursor/budgets/step, append event, unlock dependents. A late/stale lease holder cannot publish. Uniqueness handles replay; source changes make run STALE. All artifacts+step transitions commit atomically.
- Lease expiry: advance may recover abandoned RUNNING step by incrementing fence and returning READY if attempts remain; otherwise FAILED. Record recovered attempt. A lease check by itself is insufficient; publish fencing must reject the old worker. Persist claimed batch/time budgets before computation so crashes cannot provide unlimited free attempts: reserve the per-batch allowed milliseconds at claim, reconcile to actual elapsed on successful/explicit failed publish, and charge the full reservation if abandoned. Store reservation in cursor/attempt event or an explicit column; never let unknown crash time count as zero.
- Cancellation sets CANCELLED and fences outstanding steps in one transaction; cooperative parser can finish its current read, but publish is rejected. Cancellation does not delete evidence, requirements, decisions or artifacts.
- Restart creates a **new** job with a newly captured current manifest and `restart_of_job_id`. Old failed/stale/cancelled artifacts remain historical. Never replace their hashes or relabel them successful.
- FAILED has safe enumerated errors such as DOCUMENT_MISSING, INTEGRITY_FAILED, PARSE_FAILED, OUTPUT_INVALID, COMMIT_UNCONFIRMED, ATTEMPTS_EXHAUSTED. Storage outage gives retriable 503 without DSNs/tokens/paths/raw documents; serialization conflict gives 409 and requires refresh. GET status is safe to retry; mutation response ambiguity is resolved via idempotency lookup and saved state.
- WAITING_HUMAN means automation is complete and every actionable suggestion is in the queue; it does not mean ready to bid. COMPLETED means candidate review/dispositions are recorded, including rejected/duplicate items. Source scope remains a separate human gate.

## 6. API and UI contract

API under existing security middleware:

```text
GET  /api/tenders/{tender_id}/workflows              list scoped runs
POST /api/tenders/{tender_id}/workflows              create with Idempotency-Key
GET  /api/tenders/{tender_id}/workflows/{job_id}      state, progress, artifacts/issues
POST /api/tenders/{tender_id}/workflows/{job_id}/advance  one bounded batch
POST /api/tenders/{tender_id}/workflows/{job_id}/cancel
POST /api/tenders/{tender_id}/workflows/{job_id}/restart  fresh manifest/new run
POST /api/tenders/{tender_id}/workflows/{job_id}/candidates/{key}/review
GET  /api/tenders/{tender_id}/workflows/{job_id}/receipt.json
GET  /api/processors                                RULES available, local model disabled
```

Review endpoint accepts ACCEPT/REJECT with reviewer note. ACCEPT must verify source-citation-check result and **current source dependency hash**, revalidate actual quote through existing validator, and deduplicate against existing `{tender_id,source_id,page,whitespace-normalized quote}`. Full job staleness caused by requirement/evidence changes does not forbid this narrowly safe creation from still-current source artifacts. In one transaction create a requirement with `reviewed=0`, `mandatory=NULL`, `status='UNKNOWN'`, `extraction_method='rules_workflow_v1'`, then record ACCEPTED or DUPLICATE disposition and audit. It never directly sets `VERIFIED`, accepts inferred mandatory classification or links candidate evidence as verified. Existing review/status routes perform later human approvals. Reject keeps artifact and note; do not delete the candidate.

Add an “Analysis work” tab to assessment, with one primary action “Analyze registered documents.” Show `Local rules · No model usage charges`, contract version, actual job states, reviewed/suggested distinction, source coverage issues, current vs stale inputs, evidence expiry and citation status. A collapsed run detail shows stages, attempt counts, elapsed processing, exact source/file hashes, actual receipt and processor identity. “Continue analysis,” “Cancel,” “Restart with current documents,” and the review queue resolve clear states; no fake animated team names or false completion percent.

Client may auto-advance sequentially while this tab is open, persist job IDs, show progress and reload saved state after navigation. If tab closes or transport stops, label job “Saved; resume analysis” rather than imply unattended progress. Stop auto-advance on WAITING_HUMAN, FAILED, STALE, CANCELLED or BUDGET_EXHAUSTED. Use existing CSRF wrapper, safe DOM escaping, accessible buttons/keyboard states and guarded duplicate click handlers.

## 7. Local inference extension

Ship a documented typed processor interface with capabilities, input/output schema, provenance and invocation receipt; do not auto-install/download a model or call a provider now. `RULES` is available; `LOCAL_MODEL` is unconfigured. An enabled future local Ollama adapter must require explicit administrator configuration of a fixed loopback origin/model name, availability and licensing/hardware checks, egress guard, token/time budgets and complete real invocation receipt. It may propose requirements/evidence relevance; the same citation, review and BID gates remain.

Never expose raw key values through `/api/processors`, logs or UI. An API key field is unnecessary for the current usable workflow. A future cloud option needs separate explicit processor/data authorization and affordable cost limits; a claim of “free” does not authorize transmitting company documents.

## 8. Commercial operations that help generate real receipts

Highest-value small increment after workflows is a **service-order register**, not an invented success forecast or payment processor. It organizes a paid expert-reviewed diagnostic using the existing organization's evidence and report flow:

- `service_orders(id, tender_id, organization_id, customer_label, service_name, status, currency='BDT', quoted_minor, quoted_at, due_at, accepted_at, created_by, created_at, updated_at)`. Status DRAFT/QUOTED/ACCEPTED/IN_PROGRESS/READY_TO_DELIVER/DELIVERED/CANCELLED. Store money as integer minor units; distinguish blank/unquoted from zero. Valid same-tender/org FK and explicit human transitions; automation cannot issue a binding quote.
- `service_payments(id, order_id, amount_minor>0, currency, external_reference, collected_at, recorded_by, note, created_at)`. Unique `(order_id,external_reference)` plus idempotency. These are manually recorded offline collections; no assertion of bank-verified payment unless actual reconciliation exists. Correct mistakes through append-only reversals, not deletion/overwriting. No payment gateway credentials/spend.
- `service_deliveries(id,order_id,report_format,snapshot_json,snapshot_sha256,file_sha256,template_version,decision_id,approved_by,created_at)`. Explicit human export/delivery receipt; check current report/decision policy at capture; frozen snapshot. “Delivered” records operator confirmation, does not secretly email a client. Do not claim any file was sent absent recorded operator/external evidence.

Show separately actual quoted amount, manually recorded collections, balance due, delivery status, elapsed effort, repeat paid orders and complaints/rework. Use existing `pilot_metrics` for historical work-time inputs; label current aggregates as recorded pilot observations. No profitability assertion without actual costs/review effort. Prices in attached docs/blueprint are hypotheses, not autofilled approved tariffs. Market success cannot be established by building these screens; it requires observed repeat payment/value.

These registers are practical and testable, but must not block the workflow vertical slice or expand into multi-tenant SaaS, tax accounting, public sales outreach, contracts or automatic charging.

## 9. File ownership and implementation dependency graph

1. **Persistence coder** owns `app/database.py`, `scripts/migrate_postgres.py`, new `003_bounded_workflows.sql`, and optionally `app/workflow_schema.py` for local v3 statements. Preserve v1/v2 digests. Publish schema interface to engine coder first. Must not edit `main.py` or UI.
2. **Workflow engine coder** owns new `app/workflows.py`, `app/workflow_contracts.py`, optional `app/processors.py`, optional local worker CLI. Inject database factory/document reader/current snapshot/authenticated actor so no circular import from `main.py`. Implement finite registry, manifest hashing, fenced batches, artifacts, verifier, acceptance service and receipts. No core review/decision writes except unreviewed requirement creation for human acceptance.
3. **API integration coder** owns only assigned imports/router attachment/local v3 initializer hook in `app/main.py` and new `app/workflow_routes.py`. Engine exposes router factory or dependency factory so integration is small. Coordinate explicitly; only one coder owns main.py at a time. Existing auth middleware covers every route.
4. **UI coder** owns `app/static/ui.js`, `style.css`, `index.html`; uses agreed route/result schemas, processor truth labels, progress/recovery and candidate review. May run in parallel after engine/API interface is frozen.
5. **Commercial coder**, if authorized now, owns `app/commercial.py`, `app/commercial_routes.py`, independent numbered v4 migration and assigned UI section through UI coder. Do not overlap database/main.py ownership; persistence coder registers v4. Suggest defer until workflow integration passes.
6. **Independent QA/security/domain reviewer** reads all final changes, separately runs meaningful tests and reports exact commit/hash, genuine agent metadata, null unexposed run/trace IDs and limitations. Neither coder self-approval nor deterministic product checker satisfies independent development review.

Minimal parallel batch: persistence + engine + UI; API integration after schema/engine interface; independent QA last. Save each implementation task with exact inputs, allowed/forbidden files, invariants, failure conditions and receipt. These are APES bounded tasks grounded in the user's instruction, not invented org-chart titles. Parent selected an isolated build worktree `/workspace/tenderos-agent-workbench` on `tenderos/agent-workbench` from the inspected commit; coders should target that directory, while this audit/source hash record remains tied to the original baseline.

## 10. Acceptance evidence before completion claim

Required independent checks are domain/behavior checks rather than tests mirroring helper implementations:

1. Fresh/repeated/legacy SQLite migration; explicit PostgreSQL v3 migration contract and old v1/v2 digests preserved. Live managed DB verification remains unperformed without an actual configured service.
2. Real synthetic PDF source → durable job → all four truthful rules stages → citation-valid candidate → human acceptance produces only unreviewed UNKNOWN requirement; normal human gates still work.
3. Existing upload candidates are deduplicated; same idempotency key retry returns same job; changed payload conflicts; double accept returns one requirement/review.
4. Parallel advances and expired lease publish cannot duplicate/overwrite artifacts; cancelled in-flight work cannot publish; restart retains old artifacts and freezes new sources.
5. New addendum/source/inventory changes mark source artifacts stale and block candidate acceptance. Requirement edits/evidence-file replacement/metadata change/date expiry mark full/evidence analysis stale, while a still-source-current candidate can create only an unreviewed requirement. Accept multiple same-job proposals sequentially without self-invalidating the remaining source proposals. Decisions remain historical and currency behavior stays correct.
6. Cross-tender job/artifact/source access and cross-organization evidence/reviews rejected; hosted auth/CSRF and safe receipt export enforced.
7. Scanned/unreadable/encrypted/tampered/oversize/out-of-bound PDFs and artifact/candidate/time/attempt budgets stop explicitly; no false completeness/ready claims.
8. Embedded document instructions cannot change task registry, scope, endpoint, processor, cost limit or human approval. No model/network inference call with default config.
9. Transport/commit ambiguity, outage/reload/cold-start and cancelled/restarted recovery preserve durable receipts; no silent approval retry.
10. Current end-to-end source/evidence/BID/exports tests remain passing; meaningful new workflow acceptance tests pass under independent agent review. Commercial tests, if included, separate quote from collected amount, money rounding/idempotency/reversals and immutable delivery snapshots.

A successful local rules release demonstrates usable no-paid-inference automation plus audited human decision support. It does **not** prove autonomous AI inference, always-on hosted workers, full OCR coverage, market profitability, live managed persistence, secure public SaaS, or deployment repair. Report each separately.

## Source hashes recorded at inspection

```text
app/main.py 72d46a85d357995330877250d7084034cecd43f9783d5973e87ff5f290978d04
app/database.py ba78ebd9bcf068a0ae888f0838dc01fe1302c1ac9040e41dae2f0dfcab064596
app/hosting.py ab0bf67310596abf67b8739ef4f7c5f7ac24e833638c760af1545aae6569d8a8
app/private_storage.py b3cd4bc6d0be0d6019775804e9fef4f089ca43601e62f85b3a281f9157caa379
scripts/migrate_postgres.py b292ad5dcb8791a4b2605308ba1e4e8ea32fcec12ac9032a44c7f755c558e099
scripts/postgres_schema.sql 92dab3cbda0388c278f06ca7610a0b53bde2b13edff3bed770b4f709093a268e
scripts/postgres_migrations/002_document_registry.sql 3e10701dc7ce074663fa3ab051e8ee4c3ebc9be51a0d02fb7dd4341b0d2bc5c7
AGENTS.md 1fbca1e2b3c5be11438c39aa7e4b2ab7f02554e62dfd1ed1a3f9f670cdfa3ef6
project_knowledge/02_PRD_v1_1.md 64261b62cad7b4c54669dbe8b63a7ed27c3dd42006205bede01233b9955633ad
APES_TenderToFit_extracted.txt c8fe62b2eacc632dcf3bad316b15aa28d271e3fcfa1d46bd5fe0d2c61c5dadd0
```
