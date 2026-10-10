# Candidate interfaces observed in code

Status: module interfaces observed and coder-reported; full independent final-candidate QA pending. These names supersede optional alternate API names in the preserved source reviews. Authentication/CSRF use the existing hosted owner middleware. No app code is changed by this record.

## Processor and workflow

`GET /api/processors` returns RULES AVAILABLE (Local rules, autonomous_ai_agent false, zero model usage charges) and LOCAL_MODEL UNCONFIGURED. Policy is server-owned: no external model calls, model spend cap0, training false, no messages/payments/bid submission/approval actions. Local egress none; hosted egress registered database/private documents only. Hosted infrastructure cost UNKNOWN; local cost NOT_RECORDED.

| Route | Behavior |
|---|---|
| GET/POST `/api/tenders/{tender_id}/workflows` | Scoped saved jobs/create; POST body `processor_kind:"RULES"`, required actual Idempotency-Key header |
| GET `/api/tenders/{tender_id}/workflows/{job_id}` | Actual state/progress/issues/artifacts/currency |
| POST `.../{job_id}/advance` | One bounded authenticated advance |
| POST `.../{job_id}/cancel` | Cancel and retain historical outputs |
| POST `.../{job_id}/restart` | New saved current-input run, body fixed RULES, new Idempotency-Key |
| POST `.../{job_id}/candidates/{candidate_key}/review` | `disposition:ACCEPT|REJECT`, meaningful note5–2000; source revalidation, UNKNOWN/unreviewed creation or dedup only |
| GET `.../{job_id}/receipt.json` | Actual deterministic product receipt, not Codex build-run proof |

Current contract version `tenderos_rules_review_v1`. Fixed tasks SOURCE_INSPECT, REQUIREMENT_CANDIDATES, EVIDENCE_RELEVANCE, CITATION_CHECK. Current source page quality enums TEXT_READY, NEEDS_OCR, NEEDS_MANUAL_REVIEW, EXTRACTION_FAILED, INCOMPLETE_BOUND. These persist explicit processing findings, not automated completeness approval.

Current finite limits: 20 source files/300 source pages/10 pages per batch, 1000 candidates, 128 step runs, 180000 accumulated ms, 15000ms reservation per batch, 45-second lease, 65536 bytes per page payload, 5MiB total artifacts, 20000 page characters, 4000 quote characters, 1000 existing requirements, 500 same-organization evidence records, 2MiB manifest, 5 evidence matches per target and 25 targets per batch. These are the actual current code policy rather than the design's illustrative evidence-file limits. Cooperative budgets/leases do not prove hard parser subprocess isolation.

Browser Analysis work advances sequentially while active; closing/navigating/disconnection stops future requests and saves progress. No always-on scheduler/local worker CLI is claimed shipped. Next actions cover existing source/evidence/requirement/decision conditions as well as the new clause review queue. An app-generated attempt ID is not an opaque platform Codex run ID.

## Manual diagnostic operations

Persistence: `service_intakes`, `commercial_ledger`, `diagnostic_releases`; `app/commercial.py` routes with `app/commercial_schema.py`/v4 SQL.

| Route | Current contract |
|---|---|
| GET/PUT `/api/tenders/{id}/service-intake` | scope10–6000, exclusions, unique same-tender agreed_inventory_ids, due_at timezone-aware ISO or null, quoted_fee_minor strict integer>=0 or null, currency BDT, reviewer. checklist strict booleans: intake_complete, source_scope_reviewed, evidence_gaps_reviewed, decision_limitations_reviewed. |
| GET/POST `/api/tenders/{id}/ledger` | kind RECEIPT/DIRECT_COST/REFUND/REVERSAL; positive strict integer amount_minor, BDT, reverses_entry_id or null, idempotency_key8–100, meaningful reference2–200, note. REFUND refers only to original receipt; REVERSAL original receipt/direct cost. Same-scope cumulative correction cap, no correction-of-correction. |
| GET/POST `/api/tenders/{id}/diagnostic-releases` | reviewer, delivery_note10–4000, idempotency_key; delivery_confirmed_manually strict false by default and delivery_reference. All checklist acknowledgements required. Does not attest/verify/clear eligibility; HOLD/NO_BID/unresolved permitted with explicit warnings. |
| GET `.../diagnostic-releases/{release_id}` | Immutable payload/hash, current/stale and superseded-version state |
| GET `.../diagnostic-releases/{release_id}/export.json|csv|docx` | Frozen captured snapshot; content hash and snapshot hash headers; no XLSX release format claimed |
| GET `/api/commercial/dashboard` | Counts/recorded ledger totals/assessments, positive-net paid assessments and repeat-paid organizations; unknown_costs true and explicit no-profit disclaimer |

The release's current context includes assessment, all organization evidence, service intake and ledger. Source/evidence/intake/financial changes may stale the current comparison without altering captured report bytes. An explicit manual delivery reference is an operator observation, not proof of an external send/bank action.

`contribution_after_recorded_costs_minor` is always net collected cash minus recorded direct cost, with unknown_costs true. It intentionally does not claim complete cost or audited profit. Gross receipts, refunds, receipt reversals, gross direct costs and cost reversals remain distinct. Quote/legacy pilot amount never contributes ledger cash. Repeat paid organization needs at least two distinct positive-net assessments; fully refunded orders excluded.

No source-copied prices/default SLA, automatic financial commitment, payment gateway, external report email, model call or deployed access is part of these interfaces. This is a single-owner assessment workspace, not authenticated SaaS tenant membership.
