# Source-grounded feature and claim register

Register version: agent-workbench-v1. Baseline: `6f7ac1156e595f9f87d6f32d99492f8a704e9849`. Initial state: selected bounded implementation; verification pending. A row marked BUILD is assigned scope, not a claim that code is complete or tests passed. Full line-to-code mapping and disposition of every APES family are retained in [APES review](reviews/APES_FEATURE_REVIEW.md); all broad policy-essay modules are retained in [governance review](reviews/GOVERNANCE_FEATURE_REVIEW.md).

## Selected increment

| ID | Feature | Source grounding | Assigned owner | Required evidence / failure boundary |
|---|---|---|---|---|
| AW-001 | Additive workflow v3 and commercial v4 persistence | APES C310/C400; extracted lines 917–959; runtime design §3 | workflow_persistence_build / commercial_operations_build | Preserve v1/v2 byte digests and all old evidence/decisions; fresh/repeated/upgrade checks and hosted SQL contract. Live managed DB is a separate gate. |
| AW-002 | Durable bounded workflow jobs and four fixed stages | APES C330; lines 368–372, 633–786, 923–959; runtime §§4–5 | workflow_engine_build | SOURCE_INSPECT → REQUIREMENT_CANDIDATES → EVIDENCE_RELEVANCE → CITATION_CHECK. Per-batch finite work, fences, leases, idempotency, limits, cancellation and restart; no shell/network/model executor. |
| AW-003 | Persistent source text quality/page coverage | APES lines 1097–1098, 1129–1140, 1251–1261, 1443 | workflow_engine_build | Expose unreadable/image-only and bounds explicitly; zero candidates never proves completeness. No OCR success claim. |
| AW-004 | Source-bound candidate suggestions, exact citation checks and human dispositions | APES lines 1099–1101, 1445; official-source rules; runtime §§4,6 | workflow_engine_build | Verbatim page/hash provenance. Human acceptance only unreviewed UNKNOWN, mandatory null; duplicate-safe. Reject preserves history. Source-changed blocks; source-current candidates can survive unrelated full-analysis staleness. |
| AW-005 | Same-organization evidence relevance suggestions | APES lines 1102, 1166–1175, 1235–1244; governance §4 | workflow_engine_build | Capture all same-org evidence metadata/current files. Suggestions are not adequacy/confidence/verified status. Missing/expired/unverified stays explicit; no cross-org or whole-vault model upload. |
| AW-006 | Truthful processor/policy status and application run receipts | APES no paid baseline lines 28,109,801,1322; essay lines 139–235,465–567 | workflow_engine_build | RULES available, LOCAL_MODEL unconfigured, no model request path/spend, training disabled. Product attempt IDs are not opaque Codex run IDs. Redact credentials/private paths. Infra cost unknown unless known. |
| AW-007 | Analysis UI with saved progress, resume/restart/cancel and candidate review | APES C220 lines 900–916; governance §6; runtime §6 | product_frontend_build | No always-on scheduler implication: processing advances while client calls or a permitted worker runs. Honest empty/error/stale/review states and scoped CSRF-safe calls. |
| AW-008 | Prioritized compliance review queue | APES lines 1104,1240–1250; C220 | product_frontend_build | Include all existing blocked/unresolved reasons plus new source issues/candidates; links and next actions. Queue completion cannot change compliance or approve BID. |
| AW-009 | Expert diagnostic intake, scope/exclusions, agreed source list, due date and quote | APES C230/C520; lines 1095–1097,1218–1230,1284–1322; APES review service contract | commercial_operations_build | Manual scoped intake and entered commitment, not unconditional SLA. No automated quotation authority, binding offer or charges. Quote is not collected cash. |
| AW-010 | Append-only BDT minor-unit receipt/cost/reversal ledger | APES C230/C520; essay lines 511–567; review service contract | commercial_operations_build | Strict integers, explicit type, idempotency, reference, actor/time. Same-scope reversal; bounded cumulative corrections. Founder-recorded observations, not bank reconciliation. |
| AW-011 | Immutable versioned diagnostic release and historical export | APES C510/C530; lines 1105–1106,1173–1179,1257–1258,1950–1962 | commercial_operations_build | Server-derived complete snapshot/template/reviewer/version/hash; historical payload immutable and current/stale visible. HOLD/NO_BID/gaps valid honest diagnostic results. Delivery confirmation does not email or change eligibility. |
| AW-012 | Actual cash/direct-cost/repeat-paid-client dashboard | APES C230/C600; lines 1284–1322,1490–1496; governance §6 | commercial_operations_build / product_frontend_build | Gross receipts/refunds/net cash/documented direct costs, missing cost states and denominators. Repeat = stable org with at least two distinct assessments with positive net receipts. No guaranteed/audited profit. |
| AW-013 | Full source disposition, compiled task/prompt contracts and actual engineering metadata | APES lines 202–240,633–786,1459–1489,1894–1924; MASTER documentation method | source_traceability_build | Hash actual files, maintain planned vs actual status, genuine named delegates, null opaque IDs. No simulated team or completed receipt without outputs. |
| AW-014 | Independent behavior/security/domain review | APES C500; lines 960–975,1380–1454; AGENTS executable sequence | separate QA/security agents to be assigned by parent | New and existing workflows, source currency, races, money, immutable history, migrations, auth, zero-model path. Record real candidate hashes and actual result; repairs re-reviewed. |

## Preserved existing capabilities

Organization/tender intake; source inventory including missing/addendum/version associations; source PDF hash/size/page/quote validation; private versioned evidence and hash-bound human verification; mandatory blockers and unresolved states; source completeness fingerprint attestation; human final decisions with immutable history and currency; literal-safe CSV/XLSX and editable DOCX live exports; local SQLite/browser use and prepared owner-protected PostgreSQL/private Blob mode. Earlier test figures are historical, not new-run proof for this increment.

## Deferred and excluded families

| Family | Disposition | Reason / next evidence |
|---|---|---|
| Actual model-backed requirement extraction/agents; cloud API/free-key routing | DEFER | No permitted configured free inference runtime. No ChatGPT subscription-as-API assumption. Later actual adapter/consent/budget/invocation traces required. |
| Local Ollama inference | DEFER | Typed seam/status only until an installed approved model/hardware/license/egress and complete real invocation checks exist. No auto-download. |
| OCR, parser subprocess sandbox | DEFER | Persist source-quality warning now; no OCR or hard parser-isolation claim until actual bounded implementation tested. |
| Merge/split/revision of existing reviewed requirements; conditional types; multi-document evidence | DEFER | Candidate accept/reject now; richer historical revision model needs separate scope. |
| Evidence expiry at tender-specific deadline | DEFER pending actual current increment confirmation | Current behavior and applicable date must be explicit. Source review recommends future tender-date-aware check; do not claim added merely from review. |
| Amendment semantic diff/change-alert engine | DEFER | Existing and new fingerprints invalidate currency; reviewed semantic comparison separate. |
| Generic APES platform, prompt compiler, self-modifying learning engine | DEFER | Concrete file-backed tasks/prompts and measured future changes sufficient. Source automation project absent; no invented reuse. |
| PySide6/PyInstaller/mobile/ERP | DEFER | Existing local browser/FastAPI works; no justified rewrite. Portable package/backup/restore remains independent validation. |
| Multi-user SaaS/RLS/SSO/SAML/OAuth/org auto-join | DEFER | Single-owner pilot remains explicit. Scoped business entities do not constitute independently authenticated tenants. |
| OAuth Drive/email/chat/connectors, ongoing refresh tokens | DEFER | File upload already works without disclosure/auth cost. Exact grants/revocation require distinct future need. |
| General proposal writing, automatic tender submission, e-GP login, uncontrolled crawling | EXCLUDE FROM THIS SCOPE | Explicit TenderOS domain boundaries. Commercial aspiration is not authority for consequential portal activity. |
| Automatic sales outreach, payment rails/subscriptions, banking/financing/tax accounting | DEFER / unauthorized external action | Manual service and cash observation first. No purchases, messages or financial commitments. |
| Training/fine-tuning/research-dataset reuse, feedback/safety consent override | EXCLUDE FROM CURRENT PILOT | Customer document training disabled; absent policy assertions grant no rights. |
| Biometric/KYC/age/health data, consumer moderation platform, regional legal deadline engine | EXCLUDE FROM CURRENT PILOT | No actual use case or applicable law supplied; needless sensitive data/cost. |
| Twenty microservices, tracking/cookie banners without trackers, enterprise legal hold | DEFER / avoid unnecessary additions | Modular app and necessary owner security fit current scope. No enterprise privacy certification claim. |
| Full tenant data portability/hard deletion/rights portal | DEFER | Existing report exports are not full data erasure or archive. Must reconcile evidence immutability/shared files/backups/storage deletion before claiming complete. |
| Weighted 53.3% readiness example, win probability, illustrative BDT prices/revenue forecasts | REJECT AS FACTS | Preserve mandatory coverage/blockers; prices and demand need actual pilot evidence. |
| Embedded MASTER PROMPT DOCX/publication commands | NOT OPERATIVE | Useful documentation methods adopted; current request asks product improvement. |
| Hosted Vercel repair, actual durable managed storage, verified free service cost | NOT PROVEN BY THIS BUILD | Local code/tests do not prove a live deployed browser→API→DB→file flow. No account/service change or paid provisioning here. |

## Commercial metric definitions

All financial records are owner-entered operational evidence in BDT minor units (100 minor units = BDT 1). A quote and an accepted/delivered status never count as cash. Monetary API values must not accept binary floats or booleans as integers.

- **Gross receipts:** sum original recorded receipt entries.
- **Receipt reversals/refunds:** append-only corrections against original same-assessment receipts; aggregate correction cannot exceed that original amount. Show separately, with reason/reference.
- **Net cash collected:** gross receipts minus receipt reversals/refunds. Exclude legacy aggregate `paid_bdt` from the new ledger calculation; never silently double-count or import it as verified settlement.
- **Documented direct costs:** cost entries less permitted cost reversals. Entered reviewer/processing costs are observations; missing cost or infrastructure inputs remain unknown.
- **Recorded direct contribution:** net collected cash minus recorded direct costs, reported explicitly as contribution after recorded direct costs with `unknown_costs=true`. This excludes overhead, taxes, unentered labor and other unknown costs; it is not audited profit.
- **Repeat paid client:** stable organization ID with at least two distinct assessments that each have positive net receipt balance. Demos, typed repeat flags and fully refunded assessments do not prove repeat paid demand.
- **Quote/balance:** quote is entered expected price; balance follows recorded quote and net collections with explicit overpayment/missing-quote handling. It is not an accounting invoice or automated payment demand.
- **Delivery/effort:** immutable release capture and explicit recorded delivery event establish operator observation, not proof that an external recipient received a file. Reviewer/delivery/rework minutes require actual entered timing; no fabricated throughput.

No price is auto-filled from the attached examples. Revenue generation and commercial success remain empirical: observed willingness to pay, repeat purchase, useful source-backed decisions, time saved and cost completeness determine whether later investment is warranted.
