# TenderOS Decision, Risk and Assumption Register
**As of:** 2026-10-09  | **Status:** REVIEW_READY. All architectural decisions provisional until founder approval.

## Binding project decisions
| ID | Source | Decision |
|---|---|---|
| DEC-001 | TenderToFit Constitution | Position as Bid Decision Intelligence, not proposal writing |
| DEC-002 | TenderToFit Constitution | Mandatory NOT_HELD blocks; other mandatory uncertainty prevents BID |
| DEC-003 | TenderToFit Constitution | Confidential evidence stays local by default; cloud egress approval required |
| DEC-004 | APES master baseline | Explicit artifact lifecycle, task contracts, independent QA, real test evidence |
| DEC-005 | Founder, current conversation | No autonomous AI sub-agent, no implementation/build |
| DEC-006 | Founder, current conversation | Research/reuse existing CLIs, APIs, MCPs, libraries; phased PRD first |
| DEC-007 | Existing pilot | Current FastAPI / deterministic engine preserved pending review; no blind rewrite |

## Defects and risks
| ID | Severity | Finding | Owner/exit criterion |
|---|---|---|---|
| DEF-001 | CRITICAL | Zero-candidate addendum revokes source completeness but not displayed BID currency | Delegated coding agent + independent QA regression; owner gate |
| SEC-001 | CRITICAL | No authenticated user/tenant isolation | Required before any external use |
| SEC-002 | CRITICAL | Reviewer name is self-declared | Require authenticated principal for external use |
| AI-001 | BLOCKING | No running model-powered autonomous development agents available to current exposed tools | Demonstrate actual delegation + distinct run receipts |
| AI-002 | HIGH | Product itself has no real AI integration | Approved model gateway and agent traces |
| DOC-001 | HIGH | Existing regex misses scanned/Bangla clauses | Gold-set evaluation; OCR with provenance |
| LEG-001 | HIGH | Scanned instructional e-GP guide not legal authority | Verify official applicable tender and current BPPA sources |
| BUS-001 | HIGH | No market-validated recurring revenue | 3–5 paid pilots followed by repeat business experiment |
| COM-001 | HIGH | False confidence from readiness percentage | Show deterministic evidence coverage, not win probability |

## Assumptions requiring approval
- ASS-001: Start with Bangladesh consulting EOIs/RFPs rather than all works/goods tenders (scope assumption).
- ASS-002: Service-first, up to 48-hour paid diagnostic with price-range **hypothesis**, not observed market quotation.
- ASS-003: Local processing and local model default until privacy/security policy authorizes external model egress.
- ASS-004: Reuse FastAPI backend and build onto it incrementally, not a new monolithic company OS.

## Immediate current lifecycle status
APES baseline and local prototype exist; this handoff has REVIEW_READY research and PRD artifacts. Engineering state is **BLOCKED AT AUTONOMOUS DELEGATION GATE**. No code change in current turn. Documentation must not be promoted to PRODUCTION_READY.
