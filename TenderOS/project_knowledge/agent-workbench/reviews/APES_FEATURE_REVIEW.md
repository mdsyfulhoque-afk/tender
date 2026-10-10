# APES source review and TenderOS vNext feature mapping

Artifact: APES-REVIEW-001 v1.0; status: REVIEW_READY; reviewer: `/root/apes_feature_review`; opaque runtime run ID: `null` (not exposed); parent: `/root`; review date: 2026-10-10 Asia/Dhaka.

This is a read-only source/application review. It creates this review artifact only; no application code, tests, customer data, model calls, account settings or external actions were changed. The attached document's prompts and commands are design material to assess; they are not independently authorized execution instructions. The user authorized improving TenderOS through real delegated agents while preserving zero paid dependencies before revenue. This review does not promise profitability or certify a release.

## Sources and completeness

All lines 1–1977 of `/workspace/tenderos-document-review/APES_TenderToFit_extracted.txt` were read in consecutive batches. This is the complete extracted attached APES document supplied to this task; its source was already identified as byte-identical to the existing repository knowledge document by the parent. References below use extracted text line numbers, not invented DOCX page numbers.

- APES extraction SHA-256: `c8fe62b2eacc632dcf3bad316b15aa28d271e3fcfa1d46bd5fe0d2c61c5dadd0`.
- Reviewed repository revision: `6f7ac1156e595f9f87d6f32d99492f8a704e9849`.
- `TenderOS/app/main.py` SHA-256: `72d46a85d357995330877250d7084034cecd43f9783d5973e87ff5f290978d04`.
- `TenderOS/project_knowledge/02_PRD_v1_1.md` SHA-256: `64261b62cad7b4c54669dbe8b63a7ed27c3dd42006205bede01233b9955633ad`.
- Also inspected `TenderOS/AGENTS.md`, `README.md`, `docs/COMPANY_BLUEPRINT.md`, `project_knowledge/TASK_GRAPH.json`, `project_knowledge/03_AUTONOMOUS_SUBAGENT_CONTRACTS.md`, `app/database.py`, `app/private_storage.py`, `app/hosting.py`, `app/static/ui.js`, and `requirements.txt`.

Tests were not run in this review. Existing README test results are prior reports, not newly reproduced findings.

## Product conclusion

The APES document contributes a reusable engineering control system and an offline tender decision workflow. It does not provide verified customer demand, verified competitor prices, proven success probabilities, or a validated autonomous revenue engine. The strongest commercial path in the existing PRD is a narrowly scoped expert-reviewed tender readiness diagnostic: source-backed mandatory conditions, concrete evidence gaps, prioritized next actions and editable client deliverables. Its benefit and willingness to pay remain testable hypotheses.

Use genuine development agents to build that workflow. Keep product-time model agents distinct from development-time agents. ChatGPT/Codex availability here proves an engineering environment exists; it does not provide a free inference API inside the deployed product. Do not label deterministic parsers, scripted jobs, or agent descriptions as autonomous model agents.

## Full feature and innovation mapping

| APES feature / innovation | Source lines | Existing TenderOS implementation | Missing or improvement | Priority and rationale |
|---|---:|---|---|---|
| Evidence-first knowledge classes: evidence, owner fact, assumption, decision, lesson | 202–240 | Source hashes and audit records; project knowledge contains decision/risk docs | Machine-readable evidence/assumption/decision links remain documents rather than validated live registry | P1 engineering control; preserves truthful commercial and release claims |
| Layered capability/activity/task/artifact/execution/governance/learning architecture | 149–201 | Separate engineering policy/PRD/task contracts/receipts exist | Avoid building seven new product service layers; use compact versioned JSON/Markdown artifacts | Adopt as build method now |
| State-aware lifecycle S0–S8 and gate progression | 262–296; 1419–1441 | Draft PRD has stage gates; actual main API has compliance states but no build lifecycle engine | Reconcile stale `TASK_GRAPH.json:6–17` with actual delivered work and truthful receipts; minimal engineering state register | P0 metadata accuracy, P1 automated dependency checks |
| C000 governance / artifact identity / decisions | 387–418; 605–632 | Repo knowledge/verification folders and receipts | Source-of-truth registry with IDs, versions, hashes, reviewer and supersession | P1; support agent handoff and recovery |
| C100/110/120/130 opportunity, research, alternatives and actual domain workflow | 312–332; 844–893; 1262–1283 | PRD scope and hypothesis exist; domain notes/e-GP references available | Demand and competitor claims not empirical in APES; verify official procedure version and translation before using as legal authority | Parallel research; do not block safe source-grounded pilot increments |
| C200/210/220 strategy, testable requirements and decision-centered UX | 333–347; 894–916 | PRD and UI inventory/requirements/evidence/decision/export/pilot/audit tabs | Current UI presents lists; add one visible review queue answering what blocks release and what to do next | P0 commercial pilot usability |
| C230 commercial viability / C520 productization | 348–352; 369–373; 1284–1322 | `PilotMetricsIn` and metrics route record quote, paid amount, delivery/baseline/benchmark minutes and repeat flag (`main.py:211–219,795–811`) | No delivery cost, contribution, payment-evidence reference, order linkage, aggregate management dashboard or client-ready scoped offer | P0 cost/revenue observation; no payment processor required |
| C300/310 architecture/data/provenance contracts | 353–362; 917–922; 1149–1179 | FastAPI, SQLite/Postgres adapter, inventory/evidence additive migration, private files | Keep current browser UI/local Python core rather than replacing with PySide6; additive data changes only | Retain existing work; no rewrite justified |
| C320 privacy/security/risk | 363–367; 917–922; 1435–1454 | Hosted single-owner Basic auth, HTTPS, CSRF, scoped file retrieval with hash/size checks (`hosting.py:50–121`, `main.py:222–245`) | Local names remain assertions; no multi-user identities, customer tenant system, parser sandbox, malware scan, proved backups | P0 no-egress and exact scope labeling; separate gates before multi-user exposure |
| C330 bounded AI/automation, activities not job titles | 368–372; 419–504 | Real development agents in session; product candidates remain heuristics (`main.py:813–823`) | No product model gateway/jobs/tools. Optional local model gateway only after available runtime and consent established | Optional P2; cannot be a paid dependency |
| C400/410/420 task engineering/implementation/integration | 373–384; 633–786; 923–959 | Actual code/receipts exist; static task graph is stale | Versioned allowed/forbidden path contracts and dependency-compatible work batches; independent review after each candidate | Adopt now as agent build practice |
| C500 verification with pass/fix/stop | 385–388; 960–975; 1380–1454 | Test suite and recorded independent QA reports | Current release must be re-reviewed against actual bounded increment, not declared complete from document existence | P0 required independent review |
| C510/530 docs, packaging, release/checksums/rollback | 389–397; 976–980; 1950–1962 | README/deployment docs, local run command, CSV/XLSX/DOCX exports (`main.py:955–1046`) | No immutable report release/export history, portable release bundle or proved restore path | P0 diagnostic release record; P1 local release/restore |
| C600/610 learning and governed evolution | 398–406; 981–984; 1490–1496; 1925–1949 | Pilot fields/decision risk docs | Structured measured debrief and change proposals; no self-modifying prompts from one anecdote | P1 after actual delivered assessments |
| Local project / intake / original-source inventory | 1095–1097; 1218–1230 | Organizations, tender metadata, PDFs, source inventory/addenda metadata (`main.py:149–181,534–645,874–925`) | Assessment deadline retained as date; configurable service scope and intake-complete event not tracked | P0 service intake status, if bounded |
| Text extraction + explicit scanned/corrupt/encrypted failure | 1097–1098; 1129–1140; 1251–1261; 1443 | PDF integrity/encryption/page/size checks; heuristic candidates | Scanned text-less PDF yields zero candidates rather than persistent `NEEDS_OCR`/quality state; no page coverage or extracted source-span cache | P0 source-quality states; optional local OCR later |
| Requirement correction / merge / split / reject | 1099–1101; 1445 | Manual source-linked create/review with exact quote validation (`main.py:157–170,260–282,645–672`) | No merge/split/reject or revisions; duplicates cannot be explicitly retired and rejected candidates remain review burden | P1 revision-aware correction; reject without deleting history first |
| Conditional/informational requirement, due date, evidence type | 1101; 1159–1167 | Nullable mandatory bool + requirement status/note | No structured category/conditional trigger/information type/requirement deadline | P1 after immediate diagnostic queue; do not weaken unknown classification gate |
| Evidence library, mapping, validity, missing/partial/ambiguous | 1102; 1166–1175; 1235–1244 | Private PDF versions, exact-hash human verification, same-org link/status (`main.py:285–322,673–753,852–872`) | Single evidence link per requirement; no issuer/valid-from/excerpt/relevance review history; expiry uses current date, not tender submission date | P0 evaluate expiry against applicable tender deadline; P1 multi-document support |
| Explainable readiness with mandatory blocker override | 1103; 1180–1217 | Deterministic BLOCKED/UNRESOLVED/READY + mandatory coverage (`main.py:324–441`) | APES weighted 53.3% example is illustrative. Preserve current mandatory coverage metric instead of implementing unvalidated weights | Retain; label coverage, never win probability |
| Prioritized next action / matrix / missing-evidence report | 1104; 1240–1250 | Blocker/unresolved arrays and matrix exports | Unresolved reasons are not standardized action objects; UI lacks single prioritized cross-assessment work queue | P0; reduces expert review effort and conveys value |
| Local Word/Excel editable report and export history | 1105–1106; 1173–1179; 1257–1258 | DOCX/XLSX/CSV downloads; source/evidence hashes and history included | Exports are generated from live state; no export ID, timestamp/version/template/hash/immutable payload/history or separately signed diagnostic narrative | P0 release record + diagnostic action summary; no general proposal drafting |
| Source version/addendum review and stale decision | 1153–1162; 1451 | Source inventory fingerprint, attestation event, immutable decision records and current/stale check (`main.py:388–431,754–793`) | No structured amendment diff or change-alert queue | P1 local diff; retain invalidation on all sources including zero-candidate changes |
| Offline packaging/clean-run and recovery | 1138–1148; 1261; 1449–1454; 1950–1962 | Local FastAPI/SQLite/browser run with no runtime API key | No tested portable package, backup/restore bundle or explicit release manifest | P1 actual local operability; avoids paid hosting need |
| Prompt compiler / artifact dependency engine / objective traceability checks | 1460–1485; 1894–1924 | Contracts/templates and task graph documents | No automatic compile/next task validation | P1 tiny build helper, never simulated agent launcher |
| Reuse referenced automation project | 1486–1489 | Referenced project not supplied/inspected in APES captured discussion | Adapter seam only; do not invent external orchestration integration | Defer until actual source exists |

## Recommended bounded vNext

Ship a **single-owner expert tender diagnostic workspace**, locally usable with no API key and built by genuine delegated agents. Keep final human source/evidence review and BID approval because these are current product invariants. The owner requested minimal direction for engineering execution; that does not abolish customer/reviewer approval in procurement decisions.

1. **Assessment overview and review queue.** Standardize action objects with stable reason code, severity, source/requirement/evidence link, clear next action, optional assignee/due date and resolution state. Derive current blockers and unresolved work from authoritative snapshots rather than allowing an action checkbox to clear eligibility. Prioritize missing original sources and unreadable text; unreviewed mandatory claims; missing/expired/unverified proof; source reattestation; stale decisions. Show filters and counts with truthful empty/loading/error states. Accept when every current blocking/unresolved condition has a link and next action, and action resolution cannot bypass domain gates.

2. **Source processing quality.** Persist text extraction outcome (`TEXT_READY`, `NEEDS_OCR`, `NEEDS_MANUAL_REVIEW`, `EXTRACTION_FAILED`) and page-level empty-text counts or diagnostics. Distinguish a readable PDF with zero candidate keywords from an image-only unreadable source. Preserve original/hash. Any unreadable/missing page remains visible and must not silently count as fully checked. No external OCR or model API. Local Tesseract can be optional, separately tested, and report absence rather than pretending OCR completed.

3. **Paid-diagnostic release record.** Generate report ID, snapshot fingerprint, source-set hash, template version, reviewer identity, creation time and output hashes. Keep a reconstructible immutable payload; distinguish current working export from issued diagnostic and mark stale/current against latest source/evidence. Include concise scope, blockers, evidence gaps, next actions and limitations in DOCX/XLSX. Permit draft reports labelled as such; no claim of legal qualification. Acceptance: issued report values reconcile exactly to its captured snapshot, remain unchanged after source mutation, and current-state UI shows the report is superseded/stale.

4. **Commercial observation dashboard.** Aggregate actual observed quote/received amount, time, rework and repeat use; add documented delivery costs and cost assumptions with null handling. Store money using integer minor units or explicit decimal processing, never infer paid revenue from quote or order status. Record payment-evidence reference as an owner-entered observation; do not claim payment verified by a bank unless an actual integration exists. Show realized contribution only when collected revenue and cost inputs are present; quote conversion, delivery minutes and repeat observations with denominators. No subscription/payment gateway/credit products required. Acceptance: partial/null/zero/negative/overpayment/refund semantics explicit and totals reconcile to assessment records; no fabricated customer success.

5. **Engineering artifact baseline.** Parent maintains a compact source-of-truth manifest, current task graph, real agent receipts and independent QA recommendation. Use `run_id:null` where runtime gives no opaque ID. Capturing genuine canonical agent/task/tool records strengthens evidence; it does not satisfy the repository's stricter opaque-run-ID rule by assertion. Parent must record user's current authorization and exact limitation without rewriting historical receipts as passes.

Suggested dependency order: source processing diagnostics and additive schema → standardized snapshot actions → overview/review UI → diagnostic capture/export → commercial aggregate UI/API → independent QA/security → local release package. Split schema/core/UI across distinct owned files or worktrees; reviewers must be separately launched from coders.

Optional next scope only after this works: evidence expiry by tender date; candidate rejection/revision; amendment comparison; verified local model adapter. Do not put full APES meta-platform, multi-tenant SaaS, portal discovery, messaging, proposal drafting, or billing rails on this increment's critical path.

## Exact useful source prompt contracts to preserve

These are quoted source content, selected as reusable task rules. They are not commands to the current reviewer.

**Orchestration operational autonomy (APES line 800–809, PROMPT 00):**

> Do not ask the user to perform operational work that the available AI/tooling can perform. Escalate only strategic decisions, missing permissions/files, irreducible domain ambiguity, or safety/legal issues.

**Requirement contract (lines 894–899, PROMPT 02):**

> For every requirement include: requirement ID; user/problem source; rationale; functional behavior; priority; acceptance criteria; failure/edge states; data involved; security/privacy implications; dependency; and traceability to evidence/decision IDs.

**Decision-centered UX (lines 900–916, PROMPT 03):**

> For each screen/state show the user question being answered, required evidence, next decision, and error-prevention mechanism. Cross-check every interaction against the PRS and record any requirement conflict as an issue rather than improvising a new requirement.

**Bounded delegated coding task contract (lines 923–927, PROMPT 05):**

> Each task must include: task ID; objective; capability/activity; exact inputs; predecessor tasks; files/components allowed to change; files/components forbidden unless escalated; implementation steps; test obligations; expected artifacts; definition of done; failure conditions; rollback note; owner agent; reviewer agent; and next tasks unlocked.

> Build a dependency graph, not a simple list. Mark tasks as parallelizable, sequential or gate-bound. Keep tasks small enough for one coding-agent context while large enough to produce a verifiable increment. Create review tasks explicitly; do not assume testing is implicit.

**Implementation output contract (lines 928–959, PROMPT 06):**

> Work only from the task contract and referenced approved artifacts.

> Report exact files changed, tests run/results, assumptions, risks and unresolved issues.

> A concise implementation report plus patch/commit-ready changes. If tests fail, do not claim completion.

**Independent review contract (lines 960–975, PROMPT 07):**

> Classify every finding: BLOCKER, MAJOR, MINOR, OBSERVATION. Provide evidence, affected requirement/artifact/task, corrective action and re-test instruction.

> Finish with exactly one gate recommendation: PASS, PASS WITH NON-BLOCKING ITEMS, FIX AND RE-REVIEW, or STOP/REDESIGN. Do not assign PRODUCTION_READY unless all release-critical evidence supports it.

**Productization contract (lines 976–980, PROMPT 08):**

> Do not introduce new product scope during productization. Any late feature request becomes a new decision/task unless it fixes a release blocker. Verify that the shipped product can operate without mandatory paid APIs, paid hosting or paid runtime tools.

**Learning contract (lines 981–985, PROMPT 09):**

> For each proposed APES change include: triggering evidence, affected capability/prompt/gate, expected benefit, risk of generalizing from one pilot, test for the change, and proposed APES version. Do not generalize pilot-specific behavior into APES without justification.

Use these contracts by compiling actual task inputs/paths/IDs. Merely assigning AG-00 through AG-19 persona names does not demonstrate 20 independently running agents; APES itself allows interchangeable implementations (lines 419–421), while current user's no-agent/no-build principle requires real separately delegated coding execution.

## Conflicts, precedence and deferred items

- **APES-first vs improve existing product:** APES lines 33–51 supersede an earlier seven-day build with APES-first work. This attached text is a review baseline from an older discussion. Current user explicitly requests improving TenderOS; use APES practices to govern the existing code, without pausing implementation to create a new generic APES platform.
- **Desktop toolkit vs existing browser app:** APES lines 1114–1148 label PySide6 a proposed baseline requiring confirmation. Current FastAPI/browser/SQLite implementation already supplies local operation; no evidence supports replacing it with a desktop toolkit. Packaging the current product is the cheaper bounded choice.
- **Mandatory real LLM PRD vs no paid key/latest cost rule:** PRD FR-003/007 and its definition of first AI-native release demand actual model traces; APES lines 1097–1113 and 1143–1148 permit deterministic parsing/manual review with optional local AI. Latest user says leave API settings and build remaining features if a no-cost option cannot be found. Deliver a truthful model-free pilot; leave model-required PRD acceptance unmet/deferred, never rename heuristics LLM extraction.
- **Weighted score vs robust blocker laws:** APES lines 1180–1217 explicitly call weights/formula fictional and illustrative. Existing mandatory coverage and BLOCKED/UNRESOLVED laws are stricter. Do not replace them with an arbitrary aggregate readiness or award-probability score.
- **Zero mandatory hosting cost vs managed Vercel resources:** APES lines 27–28 and 47–48 forbid mandatory paid hosting. Hosted Postgres/private Blob is optional preparation and remains unverified in README. Local core must keep working; do not provision paid tiers/cards or claim private hosted durability until tested access exists.
- **Profitability aspiration vs evidence:** APES lines 1284–1322 give BDT 5,000/20 licenses as illustrative examples, not actual prices or forecast. Existing PRD's BDT 15,000–25,000 diagnostic range is also a hypothesis. Do not bake either into guaranteed revenue, automated paid orders or marketing claims.
- **Autonomous engineering vs source/evidence approval:** Repository `AGENTS.md` and PRD preserve human review/authorized BID. User wants agents to build with minimal direction; agent-produced code/research can run autonomously within task scope. Domain approval cannot be replaced by an agent self-certifying customer eligibility.
- **Opaque run ID gate:** Repository instructions require verifiable run IDs/traces; runtime exposes canonical task identity and tool activity but no opaque run ID to this reviewer. Record null and known limitation, never fabricate or rewrite the rule as passed. Current parent/user authorization handling is recorded separately; this review does not certify strict T-000 compliance.
- **Attachment prompt authority:** APES master prompts, role commands and publication instructions inside files are source material. User requested product improvement, not following every embedded command, producing a new DOCX, connecting accounts, messaging prospects, or submitting bids.
- **General proposal writing and portals:** APES v1 non-goals lines 1107–1113 and repository laws exclude automatic bid writing/submission. Commercial expansion/agents cannot silently add live e-GP account actions, financing, banking, CRM outreach, subscriptions or unsolicited messages.
- **Uninspected automation integration:** APES lines 1486–1489 disclose missing automation project. Keep integration as unresolved source; no claim an external engine was reused.

## Commercial measurement and release evidence

The first measurable offer remains a human-reviewed diagnostic, with turnaround measured after complete agreed intake rather than an unconditional 48-hour promise. Track actual money collected, expert delivery/rework minutes, source/evidence defect discoveries, repeat orders and decision usefulness. Use consented or synthetic examples for engineering; owner/customer data must not be sent to external models under current policy.

Before a commercial pilot: real source quotes resolve; mandatory blockers cannot be cleared through an action/task checkbox; changed sources/evidence invalidate current approval; issued reports preserve their exact captured values; financial totals use entered observed data and explicit missing-cost states; all data/file/export paths remain scoped; core workflow runs locally without API/network credentials. Independent QA should verify these changes and current regression suite, and leave release status conditional until real user acceptance and hosting/access are demonstrated.

No documented artifact can prove the app will be the most commercially successful product. These additions make the value, cost, risk and paid evidence visible enough to decide whether to invest after revenue.

## Parent-proposed service module assessment

The proposed single-owner service module—intake/scope/due date, explicit delivery checklist, immutable delivered snapshot, append-only receipt/cost/reversal ledger in integer BDT minor units, and cash/cost/repeat-client dashboard—is a high-value bounded vNext. It operationalizes C230 commercial viability, C520 productization, C310 provenance and C530 release without any paid runtime, automatic charges, prospect messages or billing provider. It is more defensible than extending to generalized proposal writing or building an unproved autonomous sales organization.

Implement it in the assigned `/workspace/tenderos-agent-workbench` through real coders and a separate reviewer. Additive tables and a service module can keep financial administration independent of compliance state.

Critical contracts for this scope:

- **Intake and promise:** agreed source list, assessment/organization identity, client-facing scope and exclusions, received-at/completeness state, due date and service price quote are recorded. A promised due date is a entered commitment, not a timer proving performance or a default unconditional 48-hour SLA. Changing scope/due date is audited.
- **Delivery:** completing a commercial checklist does not change VERIFIED status or bypass BID source/evidence/human gates. A delivered diagnostic may legitimately contain HOLD or NO-BID and missing-source disclosures. Do not make all successful paid diagnostics require BID. A delivered report records exactly what was reviewed, what remained missing, and who authorized that report; an unresolved assessment cannot be labelled fully qualified.
- **Immutable capture:** report payload includes canonical source inventory/hashes, current requirements/effective evidence status, current/stale decision state, checklist, scope, reviewer and report template/version. Preserve bytes/hash or a complete deterministic reconstructible payload, not just pointers to live mutable rows. No arbitrary client snapshot supplied by API caller. A second delivery makes a new version; previous snapshots remain viewable and explicit as historical.
- **Ledger:** integer minor amounts with explicit transaction type and source/evidence reference. Distinguish quoted fee, receipt, direct cost, refund/reversal and manually claimed payment evidence. Reject bool/floating precision surprises and invalid currency/negative semantics; client decimal display cannot silently introduce rounding. Records append; corrections refer to a same-scope existing ledger item. Server records timestamp/actor. Use unique idempotency keys or equivalent duplicate protection for retries. Do not silently overwrite previous `paid_bdt` observations as payment ledger truth.
- **Refund/reversal:** define whether partial reversals are allowed and enforce that cumulative reversals do not exceed the referenced original amount. A reversal points to the same organization's same assessment transaction and does not itself become a free-standing receipt. Show gross receipts, refunds and net cash separately. Costs are observed direct costs; exclude or visibly label unentered reviewer time/overhead, taxes, receivables and profit assumptions.
- **Dashboard:** cash is summed from recorded receipts/reversals rather than quote values. Contribution uses net receipts minus documented direct cost and is labelled contribution, not audited profit. Repeat paid clients use stable organization IDs with qualifying distinct assessments and positive net collected receipts; no typed repeat flag, demos or fully refunded orders count as repeat paid demand. Show denominators and absence of data.
- **Privacy and API:** reuse exact owner auth/CSRF/scoped retrieval. Receipt reference text is an owner observation, not a bank integration. Avoid account numbers or uploaded financial proof in ordinary public logs/fixtures; test with synthetic data.
- **Acceptance:** creation/delivery does not mutate eligibility; stale approval appears stale in snapshot; history survives source/financial corrections; CSV/XLSX cells remain literal; malformed snapshot/foreign reversal/idempotent retry/partial refunds/null quote/date errors have deterministic behavior; old database migrates without erasing decisions and evidence; local and hosted SQL adapter insert/returning paths recognize additive IDs.

Source quality and a review action queue can remain a separate next increment if ownership/time makes them unsafe to combine. The service module must disclose existing unreadable/scanned source limits. Do not claim this commercial module provides model-powered analysis.

## Adopted / partial / deferred / rejected disposition register

Every APES feature family is accounted for below; detailed line-to-code evidence is in the mapping table above. “Rejected” applies to changing TenderOS scope/claims, not to claiming the source document is invalid.

| Feature family / source section | Disposition for current TenderOS work | Concrete treatment |
|---|---|---|
| Foundation, evidence classes, governance, terminology and no mandatory paid services (§§1–12) | ADOPT | Preserve source hierarchy, assumption/decision labels and zero paid dependency; genuine agents do engineering work |
| Lifecycle/dependency/artifact gates (§§13–14,18–21) | ADOPT/PARTIAL | Compact current task/artifact registers and truthful actual receipts; reconcile historic graph; stricter opaque ID proof remains unavailable |
| Opportunity/research/competitive/workflow capabilities C100/110/120/130 (§15, prompts 01/01-F) | ADOPT/PARTIAL | Reuse verified files, label user hypotheses; perform current evidence research separately; no invented pricing/demand |
| Strategy/requirements/UX C200/210/220 (prompts 02/03) | ADOPT | Define bounded service scope and observable data/security/UX acceptance before coding |
| Commercial C230/C520 (§46, prompt 08) | ADOPT | Scoped diagnostic intake/release and actual manual cash/cost evidence; prices illustrative, no automatic charging |
| Architecture/data/security C300/310/320 (prompt 04) | ADOPT/PARTIAL | Retain FastAPI/browser/local persistence, additive schema, private evidence/auth; no proof of full hosted multi-user security |
| Agent/automation C330 and activity agents (§17) | ADOPT/PARTIAL | Genuine development subagents; product model tasks remain deferred; task roles are contracts, not claims of running agents |
| Task/implementation/integration C400/410/420 (prompts 05/06) | ADOPT | Isolated worktree, bounded allowed paths, real tool outputs, downstream handoff and independent review |
| QA C500 and readiness (§§50–54, prompt 07) | ADOPT | Source-backed findings and one evidence-based gate; no synthetic production-ready declaration |
| Docs/release C510/530 (§47–49, prompt 08, Appendix O) | ADOPT/PARTIAL | Immutable diagnostic report version/hash and matching docs; portable package/restore remain next gate |
| Learning C600/610 (prompt 09, §§57–58, Appendices M/N) | ADOPT/PARTIAL | Measured feedback/debrief, versioned corrections; no unreviewed self-modifying architecture/prompts |
| Local create/import/source requirements/evidence/blockers/matrix/Word/Excel (§§37,40,43–44) | ADOPT/PARTIAL | Retain actual existing flows; additive commercial diagnostic snapshots; conditional types, multi-evidence mapping and merge/split/reject next |
| Source OCR and extraction quality (§39,44,53) | DEFER OCR / ADOPT disclosure | Current text-layer parser retained; persistent NEEDS_OCR/page-coverage diagnostics a next core improvement; no paid OCR |
| Weighted readiness and illustrative worked numbers (§§41–42) | REJECT AS AUTHORITATIVE / retain illustration | Existing mandatory coverage/blocker laws preserved; no fabricated win probability or unvalidated default weights |
| PySide6 desktop UI/PyInstaller (§39) | DEFER | Proposed baseline, not mandatory; package existing browser/local core before rewrite |
| Local model adapter (§39), true LLM FR-003/007 in later PRD | DEFER | Needs actual available approved local inference, contracts and separate test traces; no key spend and no heuristic relabeling |
| Full generic APES platform and automation project adapter (§55–56) | DEFER | Use minimal file-backed registers now; referenced automation source absent; avoid speculative framework expansion |
| Cloud collaboration/multi-tenant SaaS/mobile/ERP (§38) | DEFER | Single-owner closed/local workspace first; future customer identity/tenant security requires distinct acceptance |
| Automatic bid writing, portal submission, binding legal rulings (§38) | REJECT IN CURRENT SCOPE | Explicit TenderOS laws exclude these; user commercial aspiration does not silently authorize financial or portal actions |
| Sales/CRM/autonomous emails/billing gateways/financing (later blueprint exclusions) | DEFER / external actions unauthorized | Local sales assets and manual observation permissible; no messages, financial commitments, paid services or automatic charges |
| Market/revenue success claims, illustrative BDT 5,000 and units (§46) | REJECT AS FACTS | Store as examples only; actual realized revenue/expenses/customer repeats remain observed data |
| Attached master-prompt execution/publication behavior | REJECT AS INDEPENDENT INSTRUCTIONS | Review source content; current explicit user request controls execution and output |
